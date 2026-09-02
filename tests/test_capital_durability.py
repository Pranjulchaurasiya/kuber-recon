"""
test_capital_durability.py
===========================
Rigorous durability, idempotency, process-restart recovery, and tenant-isolation
tests for APEX SQLite-backed CapitalFacilityManager.
"""

import gc
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import pytest

from kuber_recon.capital import (
    ActiveFacilityExistsError,
    CapitalFacilityManager,
    CapitalOffer,
    CapitalUnderwriter,
    FacilityStatus,
    TerminalFacilitySweepError,
)
from kuber_recon.engine import ReconciliationEngine
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.types import EvidenceTier, ReconciledSettlementBlock, SettlementStatus


def make_settlement_block(lump_sum_paise: int, utr: str = "UTR-TEST-01") -> ReconciledSettlementBlock:
    return ReconciledSettlementBlock(
        settlement_id=f"set_{utr.lower()}",
        utr_number=utr,
        lump_sum_paise=lump_sum_paise,
        gross_gmv_paise=lump_sum_paise + 5000,
        total_mdr_fee_paise=4000,
        total_gst_on_mdr_paise=720,
        total_tds_withheld_paise=280,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["inv_01", "inv_02"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash=f"sha256:mock_proof_{utr}",
    )


@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "test_capital_durability.db"
    yield db_file
    gc.collect()


@pytest.fixture
def sample_offer():
    underwriter = CapitalUnderwriter()
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=50)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)
    return underwriter.generate_offer(
        merchant_id="merch_durability_01",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=2500000,  # Rs 25,000
    )


def test_process_restart_recovery(temp_db_path, sample_offer):
    """Simulates complete process restart: facility disbursed in Process A persists in Process B."""
    # Process A
    mgr_a = CapitalFacilityManager(db_path=temp_db_path)
    fac_a = mgr_a.disburse_advance(sample_offer, tenant_id="tenant_alpha")
    assert fac_a.remaining_balance_paise == sample_offer.total_repayment_paise
    assert fac_a.status == FacilityStatus.ACTIVE
    fac_id = fac_a.facility_id

    # Process B (Simulated server restart with new manager instance on same DB)
    mgr_b = CapitalFacilityManager(db_path=temp_db_path)
    fac_b = mgr_b.get_facility(fac_id, tenant_id="tenant_alpha")
    assert fac_b is not None
    assert fac_b.facility_id == fac_id
    assert fac_b.merchant_id == "merch_durability_01"
    assert fac_b.tenant_id == "tenant_alpha"
    assert fac_b.remaining_balance_paise == sample_offer.total_repayment_paise
    assert fac_b.status == FacilityStatus.ACTIVE


def test_drawdown_idempotency(temp_db_path, sample_offer):
    """Duplicate drawdown requests with the same idempotency_key return identical state without duplicate records."""
    mgr = CapitalFacilityManager(db_path=temp_db_path)
    idemp_key = "idemp_drawdown_unique_abc_123"

    fac_first = mgr.disburse_advance(sample_offer, tenant_id="tenant_alpha", idempotency_key=idemp_key)
    fac_second = mgr.disburse_advance(sample_offer, tenant_id="tenant_alpha", idempotency_key=idemp_key)

    assert fac_first.facility_id == fac_second.facility_id
    assert fac_first.remaining_balance_paise == fac_second.remaining_balance_paise

    # Verify only 1 facility exists in DB
    facilities = mgr.list_facilities(tenant_id="tenant_alpha")
    assert len(facilities) == 1


def test_sweep_deduplication_idempotency(temp_db_path, sample_offer):
    """Duplicate sweep calls with same idempotency_key do not double-deduct from facility balance."""
    mgr = CapitalFacilityManager(db_path=temp_db_path)
    fac = mgr.disburse_advance(sample_offer, tenant_id="tenant_alpha")
    initial_balance = fac.remaining_balance_paise

    block = make_settlement_block(lump_sum_paise=1000000, utr="UTR-DURABILITY-01")  # Rs 10,000

    idemp_sweep = "idemp_swp_unique_xyz_789"
    fac_after_1, ev_1 = mgr.process_settlement_sweep(
        fac.facility_id, block, tenant_id="tenant_alpha", idempotency_key=idemp_sweep
    )
    expected_deduction = ev_1.sweep_deduction_paise
    assert fac_after_1.remaining_balance_paise == initial_balance - expected_deduction

    # Second identical sweep with same idempotency key
    fac_after_2, ev_2 = mgr.process_settlement_sweep(
        fac.facility_id, block, tenant_id="tenant_alpha", idempotency_key=idemp_sweep
    )
    assert fac_after_2.remaining_balance_paise == initial_balance - expected_deduction
    assert ev_1.sweep_id == ev_2.sweep_id


def test_cross_tenant_facility_isolation(temp_db_path, sample_offer):
    """Tenant B cannot read or sweep Tenant A's facility."""
    mgr = CapitalFacilityManager(db_path=temp_db_path)
    fac_a = mgr.disburse_advance(sample_offer, tenant_id="tenant_alpha")

    # Tenant B tries to read Tenant A's facility
    fac_b_view = mgr.get_facility(fac_a.facility_id, tenant_id="tenant_bravo")
    assert fac_b_view is None

    # Tenant B list facilities shows 0
    assert len(mgr.list_facilities(tenant_id="tenant_bravo")) == 0

    # Tenant B tries to sweep Tenant A's facility
    block = make_settlement_block(lump_sum_paise=500000, utr="UTR-CROSS-TENANT")
    with pytest.raises(KeyError):
        mgr.process_settlement_sweep(fac_a.facility_id, block, tenant_id="tenant_bravo")


def test_repaid_terminal_state_sweep_rejection(temp_db_path, sample_offer):
    """Sweeping a facility after full repayment raises TerminalFacilitySweepError."""
    mgr = CapitalFacilityManager(db_path=temp_db_path)
    fac = mgr.disburse_advance(sample_offer, tenant_id="tenant_alpha")

    # Giant settlement that repays the entire facility
    large_block = make_settlement_block(lump_sum_paise=50000000, utr="UTR-FULL-PAYOFF")
    repaid_fac, _ = mgr.process_settlement_sweep(fac.facility_id, large_block, tenant_id="tenant_alpha")
    assert repaid_fac.remaining_balance_paise == 0
    assert repaid_fac.status == FacilityStatus.REPAID

    # Subsequent sweep must fail
    with pytest.raises(TerminalFacilitySweepError):
        mgr.process_settlement_sweep(fac.facility_id, large_block, tenant_id="tenant_alpha")
