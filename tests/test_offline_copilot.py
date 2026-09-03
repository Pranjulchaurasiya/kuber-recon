"""Unit Tests for Offline Read-Only CFO Copilot Fallback Engine.
==============================================================
Verifies:
1. Deterministic intent classification across all 5 financial query domains.
2. Presence of mandatory offline banner disclaimer on every response.
3. Pure read-only guarantee: zero ledger state mutations or database writes.
4. Integer paise exactness across tax and capital calculations.
5. Accurate Bayesian SRI formula and factor fee determination.
"""

from decimal import Decimal
import tempfile
from pathlib import Path
import pytest

from kuber_recon.capital import CapitalFacilityManager
from kuber_recon.offline_copilot import (
    CFOQueryIntent,
    OFFLINE_DISCLAIMER,
    OfflineCFOCopilot,
)
from kuber_recon.storage import SQLiteStorageBackend
from kuber_recon.types import PaymentMethod


@pytest.fixture
def copilot_env():
    """Create isolated temporary storage and facility manager for testing."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_path = temp_path / "test_offline_copilot.db"
        backend = SQLiteStorageBackend(db_path=db_path)
        facility_manager = CapitalFacilityManager(db_path=db_path, backend=backend)
        copilot = OfflineCFOCopilot(backend=backend, facility_manager=facility_manager)
        yield copilot, backend, facility_manager


def test_offline_copilot_intent_classification():
    """Verify regex intent classification across all 5 domains."""
    assert OfflineCFOCopilot.classify_intent("What is our net GST liability on MDR?") == CFOQueryIntent.GST_LIABILITY
    assert OfflineCFOCopilot.classify_intent("Show GSTR-2B ITC input tax credit status") == CFOQueryIntent.GST_LIABILITY
    assert OfflineCFOCopilot.classify_intent("Why was my contract placed on hold?") == CFOQueryIntent.HOLD_REASON
    assert OfflineCFOCopilot.classify_intent("Explain ambiguous collision refusal") == CFOQueryIntent.HOLD_REASON
    assert OfflineCFOCopilot.classify_intent("What is the merchant Bayesian SRI score and reliability?") == CFOQueryIntent.SRI_METRICS
    assert OfflineCFOCopilot.classify_intent("Calculate Section 194-O TDS withholding for non-filer 206AB") == CFOQueryIntent.TDS_194O
    assert OfflineCFOCopilot.classify_intent("What is our active working capital facility balance and split-sweep rate?") == CFOQueryIntent.CAPITAL_FACILITY
    assert OfflineCFOCopilot.classify_intent("Who won the cricket match?") == CFOQueryIntent.UNKNOWN


def test_offline_copilot_banner_disclaimer_present(copilot_env):
    """Verify that every single response contains the mandatory offline banner disclaimer."""
    copilot, _, _ = copilot_env
    queries = [
        "What is our GST liability?",
        "Why is payment held?",
        "Show SRI score",
        "Calculate 194O TDS",
        "Show capital facility balance",
        "Random query",
    ]
    for q in queries:
        resp = copilot.answer_query(q)
        assert resp.disclaimer == OFFLINE_DISCLAIMER
        assert "without an LLM" in resp.disclaimer


def test_offline_copilot_read_only_zero_ledger_mutation(copilot_env):
    """Verify that processing queries performs ZERO ledger mutations or database side-effects."""
    copilot, backend, facility_manager = copilot_env

    # 1. Seed one contract and one facility
    backend.insert_contract(
        contract_id="ct_offline_test_01",
        tenant_id="tenant_alpha",
        status="ACTIVE",
        transfer_id="trf_001",
        amount_paise=5000000,
        fee_paise=10000,
        on_hold=True,
        on_hold_until=None,
    )
    facility_dict = {
        "facility_id": "CAP-FAC-TEST01",
        "tenant_id": "tenant_alpha",
        "merchant_id": "tenant_alpha",
        "principal_paise": 2000000,
        "factor_fee_paise": 80000,
        "total_repayment_paise": 2080000,
        "remaining_balance_paise": 2080000,
        "sweep_rate": "0.12",
        "status": "ACTIVE",
        "disbursed_at": "2026-08-01T00:00:00+00:00",
        "last_settlement_at": "2026-08-01T00:00:00+00:00",
        "payout_transfer_id": "pout_test_01",
        "version": 1,
    }
    backend.insert_capital_facility(facility_dict)

    # Snapshot contract and facility state
    contracts_before = backend.list_contracts(tenant_id="tenant_alpha")
    facility_before = backend.get_active_facility_for_merchant("tenant_alpha", "tenant_alpha")

    # 2. Run queries across all 5 intents
    copilot.answer_query("Explain GST liability on credit card transactions", tenant_id="tenant_alpha")
    copilot.answer_query("Why is contract ct_offline_test_01 on hold?", tenant_id="tenant_alpha", context={"contract_id": "ct_offline_test_01"})
    copilot.answer_query("What is our Bayesian SRI reliability index?", tenant_id="tenant_alpha")
    copilot.answer_query("Check Section 194-O TDS withholding", tenant_id="tenant_alpha")
    copilot.answer_query("Show active capital facility and remaining balance", tenant_id="tenant_alpha")

    # 3. Snapshot state after all queries
    contracts_after = backend.list_contracts(tenant_id="tenant_alpha")
    facility_after = backend.get_active_facility_for_merchant("tenant_alpha", "tenant_alpha")

    # Invariant: State must be 100% identical (zero mutations)
    assert contracts_before == contracts_after
    assert facility_before == facility_after


def test_offline_copilot_gst_liability_exact_paise(copilot_env):
    """Verify GST liability intent outputs exact base-10 integer paise."""
    copilot, _, _ = copilot_env
    resp = copilot.answer_query(
        "Calculate GST on 1,00,000 GMV",
        context={"gross_gmv_paise": 10000000, "payment_method": PaymentMethod.CARD_CREDIT},
    )
    assert resp.intent == CFOQueryIntent.GST_LIABILITY
    sd = resp.structured_data
    # 1.85% of 1,00,000 = 1,850 INR = 185,000 paise
    assert sd["mdr_fee_paise"] == 185000
    # 18% GST on 1,850 = 333 INR = 33,300 paise
    assert sd["gst_on_mdr_paise"] == 33300
    assert sd["cgst_paise"] == 16650
    assert sd["sgst_paise"] == 16650
    # Zero floats
    assert isinstance(sd["gst_on_mdr_paise"], int)
    assert isinstance(sd["net_settleable_paise"], int)


def test_offline_copilot_bayesian_sri_formula(copilot_env):
    """Verify Bayesian shrinkage formula in SRI metrics."""
    copilot, _, _ = copilot_env
    # Prior weight = 50, prior rate = 0.98. Observed: 100 samples, 95 matches (0.95 rate)
    # Expected SRI = (50 * 0.98 + 100 * 0.95) / (50 + 100) = (49 + 95) / 150 = 144 / 150 = 0.96 (96%)
    resp = copilot.answer_query(
        "Show Bayesian SRI score",
        context={"sample_count": 100, "observed_matches": 95},
    )
    assert resp.intent == CFOQueryIntent.SRI_METRICS
    sd = resp.structured_data
    assert Decimal(sd["bayesian_sri_score"]) == pytest.approx(Decimal("0.96"), abs=Decimal("0.0001"))
    assert sd["risk_tier"] == "TIER_A"  # >= 0.95
    assert sd["factor_fee_rate"] == "0.04"
    assert sd["daily_sweep_rate"] == "0.12"


def test_offline_copilot_tds_194o_non_filer_distinction(copilot_env):
    """Verify Section 194-O compliant rate (1%) vs Section 206AB non-filer rate (5%)."""
    copilot, _, _ = copilot_env
    # Compliant PAN filer: 1%
    resp_compliant = copilot.answer_query(
        "Calculate 194O TDS",
        context={"gross_gmv_paise": 10000000, "is_specified_person_206ab": False},
    )
    assert resp_compliant.structured_data["tds_rate"] == "0.01"
    assert resp_compliant.structured_data["tds_withheld_paise"] == 100000

    # Non-compliant Section 206AB non-filer: 5%
    resp_non_filer = copilot.answer_query(
        "Calculate 206AB TDS for non-filer",
        context={"gross_gmv_paise": 10000000, "is_specified_person_206ab": True},
    )
    assert resp_non_filer.structured_data["tds_rate"] == "0.05"
    assert resp_non_filer.structured_data["tds_withheld_paise"] == 500000
