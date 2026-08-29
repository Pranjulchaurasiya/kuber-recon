"""
Concurrency, Idempotency & Adversarial Attack Suite for APEX Capital Underwriting & Sweeps.
========================================================================================
Validates financial safety invariants:
1. Double-Drawdown Prevention: Exactly 1 concurrent drawdown succeeds per merchant.
2. Atomic Sweep Deductions: Multi-threaded incoming settlement blocks cannot over-recover.
3. Conservation of Repayment: Total deductions strictly equal total facility obligation (0 over-recovery).
4. Terminal State Protection: Sweeps on REPAID facilities raise TerminalFacilitySweepError.
5. Post-Repayment Eligibility: Merchant can draw a new advance once previous is REPAID.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from starlette.testclient import TestClient

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
from kuber_recon.server import app
from kuber_recon.types import EvidenceTier, ReconciledSettlementBlock, SettlementStatus


@pytest.fixture
def underwriter():
    return CapitalUnderwriter()


@pytest.fixture
def facility_manager():
    return CapitalFacilityManager()


def test_concurrent_double_drawdown_race_protection(underwriter, facility_manager):
    """20 threads simultaneously attempt to draw advances for the same merchant.
    
    Invariant: Exactly 1 succeeds (status=ACTIVE); 19 fail with ActiveFacilityExistsError.
    """
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=50)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)

    offer = underwriter.generate_offer(
        merchant_id="merch_concurrent_01",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=2000000,  # Rs 20,000
    )

    success_facilities = []
    rejected_count = 0

    def attempt_drawdown(idx: int):
        try:
            fac = facility_manager.disburse_advance(offer)
            return ("SUCCESS", fac)
        except ActiveFacilityExistsError:
            return ("REJECTED", None)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(attempt_drawdown, i) for i in range(20)]
        for f in futures:
            status, fac = f.result()
            if status == "SUCCESS":
                success_facilities.append(fac)
            else:
                rejected_count += 1

    # Invariant: Strictly 1 advance disbursed, 19 blocked
    assert len(success_facilities) == 1
    assert rejected_count == 19
    assert success_facilities[0].remaining_balance_paise == offer.total_repayment_paise


def test_concurrent_settlement_sweeps_zero_over_recovery(underwriter, facility_manager):
    """20 concurrent threads process settlement sweeps against a single active facility.
    
    Invariant: Total deductions strictly equal total repayment obligation; 
    remaining balance reaches strictly 0 paise without underflow.
    """
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=50)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)

    offer = underwriter.generate_offer(
        merchant_id="merch_sweep_race_02",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=3000000,  # Rs 30,000
    )
    facility = facility_manager.disburse_advance(offer)
    total_obligation_paise = facility.total_repayment_paise  # 30,000 + 4% = 31,200 (3,120,000 paise)

    deductions = []
    terminal_errors = 0

    def process_sweep(idx: int):
        # Create unique settlement block of Rs 20,000
        block = ReconciledSettlementBlock(
            settlement_id=f"setl_conc_{idx}",
            utr_number=f"HDFCRACE{idx:04d}",
            lump_sum_paise=2000000,  # Rs 20,000
            gross_gmv_paise=2000000,
            total_mdr_fee_paise=0,
            total_gst_on_mdr_paise=0,
            total_tds_withheld_paise=0,
            rounding_variance_paise=0,
            status=SettlementStatus.SETTLED,
            matched_invoices=[f"INV-{idx}"],
            matched_refunds=[],
            evidence_tier=EvidenceTier.TIER_A,
            proof_hash=f"hash_{idx}",
        )
        try:
            _, event = facility_manager.process_settlement_sweep(facility.facility_id, block)
            return ("DEDUCTED", event.sweep_deduction_paise)
        except TerminalFacilitySweepError:
            return ("TERMINAL", 0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_sweep, i) for i in range(20)]
        for f in futures:
            status, ded_paise = f.result()
            if status == "DEDUCTED":
                deductions.append(ded_paise)
            else:
                terminal_errors += 1

    # Invariant checks:
    # 1. Total deductions across all events must exactly equal total obligation
    total_recovered = sum(deductions)
    assert total_recovered == total_obligation_paise, f"Expected {total_obligation_paise}, got {total_recovered}"

    # 2. Final facility state must be REPAID with exactly 0 remaining balance
    final_fac = facility_manager.facilities[facility.facility_id]
    assert final_fac.status == FacilityStatus.REPAID
    assert final_fac.remaining_balance_paise == 0


def test_redrawdown_allowed_after_repaid(underwriter, facility_manager):
    """A merchant who completes repayment on facility #1 can immediately disburse facility #2."""
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=50)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)

    offer = underwriter.generate_offer(
        merchant_id="merch_repeat_borrower",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=2000000,  # Rs 20,000
    )
    fac1 = facility_manager.disburse_advance(offer)

    # Pay off facility #1 with a single large settlement
    large_block = ReconciledSettlementBlock(
        settlement_id="setl_large",
        utr_number="HDFCLARGE01",
        lump_sum_paise=50000000,  # Rs 500,000
        gross_gmv_paise=50000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["INV-L"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash_l",
    )
    fac1_updated, ev = facility_manager.process_settlement_sweep(fac1.facility_id, large_block)
    assert fac1_updated.status == FacilityStatus.REPAID
    assert fac1_updated.remaining_balance_paise == 0

    # Merchant immediately requests a second advance
    offer2 = underwriter.generate_offer(
        merchant_id="merch_repeat_borrower",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=2500000,  # Rs 25,000
    )
    fac2 = facility_manager.disburse_advance(offer2)
    assert fac2.facility_id != fac1.facility_id
    assert fac2.status == FacilityStatus.ACTIVE
    assert fac2.principal_paise == 2500000


def test_overshoot_sweep_capped_at_exact_remaining_balance(underwriter, facility_manager):
    """When a 12% sweep exceeds the remaining balance, the deduction is capped to the exact paise left."""
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=50)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)

    offer = underwriter.generate_offer(
        merchant_id="merch_tiny_balance",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=1000000,  # Rs 10,000
    )
    fac = facility_manager.disburse_advance(offer)

    # Artificially set remaining balance to Rs 35.50 (3550 paise)
    fac.remaining_balance_paise = 3550

    # Settlement of Rs 100,000 (12% would be Rs 12,000 = 1,200,000 paise)
    block = ReconciledSettlementBlock(
        settlement_id="setl_big",
        utr_number="HDFCBIG01",
        lump_sum_paise=10000000,  # Rs 100,000
        gross_gmv_paise=10000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["INV-B"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash_b",
    )

    fac_after, ev = facility_manager.process_settlement_sweep(fac.facility_id, block)
    assert ev.sweep_deduction_paise == 3550  # Capped at remaining balance
    assert ev.net_merchant_payout_paise == 10000000 - 3550  # Rs 99,964.50
    assert fac_after.remaining_balance_paise == 0
    assert fac_after.status == FacilityStatus.REPAID

    # Subsequent sweep on REPAID facility must raise TerminalFacilitySweepError
    with pytest.raises(TerminalFacilitySweepError):
        facility_manager.process_settlement_sweep(fac.facility_id, block)


def test_rest_api_drawdown_conflict_on_duplicate():
    """FastAPI REST endpoint returns 409 Conflict when merchant attempts second active drawdown."""
    client = TestClient(app)
    
    # 1. First drawdown succeeds
    res1 = client.post("/api/capital/drawdown", json={"merchant_id": "merch_api_dup_01", "requested_amount_paise": 2000000})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "DISBURSED"
    assert "facility_id" in data1

    # 2. Duplicate concurrent drawdown for the same merchant fails with 409 Conflict
    res2 = client.post("/api/capital/drawdown", json={"merchant_id": "merch_api_dup_01", "requested_amount_paise": 2000000})
    assert res2.status_code == 409
    assert "already has an active facility" in res2.json()["detail"]

