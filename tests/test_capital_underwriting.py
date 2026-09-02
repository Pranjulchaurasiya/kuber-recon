"""Tests for APEX Capital: Autonomous Verified-Revenue Underwriting & Split-Settlement Recovery."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest

from kuber_recon.capital import (
    CapitalUnderwriter,
    CapitalUnderwritingConfig,
    CapitalFacilityManager,
    FacilityStatus,
)
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.engine import ReconciliationEngine
from kuber_recon.types import ReconciledSettlementBlock, InvoiceRecord, EvidenceTier, SettlementStatus


@pytest.fixture
def underwriter():
    return CapitalUnderwriter()


@pytest.fixture
def facility_manager():
    return CapitalFacilityManager()


def test_bayesian_sri_shrinkage_small_vs_large_sample(underwriter):
    """Test that Bayesian prior protects small sample size from extreme volatility."""
    # Merchant with 10 records, 9 matches, 0 disputes (90% empirical)
    sri_small = underwriter.compute_sri(total_records=10, matched_records=9, disputed_records=0)
    # Effective rate: (9 + 50*0.98) / (10 + 50) = (9 + 49) / 60 = 58 / 60 = 0.9667
    assert sri_small == Decimal("0.9667")
    
    # Merchant with 1000 records, 900 matches, 0 disputes (90% empirical)
    sri_large = underwriter.compute_sri(total_records=1000, matched_records=900, disputed_records=0)
    # Effective rate: (900 + 49) / 1050 = 949 / 1050 = 0.9038
    assert sri_large == Decimal("0.9038")

    # Merchant with disputes receives weighted penalty
    sri_disputed = underwriter.compute_sri(total_records=100, matched_records=95, disputed_records=5)
    # (95 + 49 - 10) / 150 = 134 / 150 = 0.8933
    assert sri_disputed == Decimal("0.8933")


def test_capital_underwriting_and_offer_generation(underwriter):
    """Test offer generation from verified synthetic reconciliation blocks."""
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=100)
    
    engine = ReconciliationEngine()
    blocks, _ = engine.reconcile_batch(bank_credits, invoices)
    
    offer = underwriter.generate_offer(
        merchant_id="merch_delhi_logistics_01",
        reconciled_blocks=blocks,
        invoices=invoices,
    )
    
    assert offer.merchant_id == "merch_delhi_logistics_01"
    assert offer.verified_delivered_gmv_paise > 0
    assert offer.settlement_reliability_index >= Decimal("0.95")
    assert offer.risk_tier == "TIER_A_PREMIER"
    assert Decimal("0.1200") <= offer.sweep_rate <= Decimal("0.1500")
    assert offer.offered_principal_paise > 0
    assert offer.total_repayment_paise == offer.offered_principal_paise + offer.factor_fee_paise


def test_split_settlement_repayment_amortization_exact_paise(underwriter, facility_manager):
    """Test 1-click advance disbursement and 3-stage settlement split-sweep to zero balance."""
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=100)
    
    engine = ReconciliationEngine()
    blocks, _ = engine.reconcile_batch(bank_credits, invoices)
    
    # Generate offer for a specific Rs 50,000 advance
    target_advance_paise = 5000000  # Rs 50,000
    offer = underwriter.generate_offer(
        merchant_id="merch_tech_solutions",
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=target_advance_paise,
    )
    
    facility = facility_manager.disburse_advance(offer, tenant_id="merch_tech_solutions")
    assert facility.status == FacilityStatus.ACTIVE
    assert facility.principal_paise == 5000000
    assert facility.factor_fee_paise == offer.factor_fee_paise
    assert facility.total_repayment_paise == offer.total_repayment_paise
    assert facility.remaining_balance_paise == offer.total_repayment_paise

    # Simulate Day 1 settlement of Rs 20,000
    dummy_block_1 = ReconciledSettlementBlock(
        settlement_id="setl_001",
        utr_number="HDFCN001",
        lump_sum_paise=2000000,
        gross_gmv_paise=2000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["INV-01"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash1",
    )
    from decimal import ROUND_FLOOR
    expected_day1_sweep = int((Decimal("2000000") * facility.sweep_rate).to_integral_value(rounding=ROUND_FLOOR))
    fac, ev1 = facility_manager.process_settlement_sweep(facility.facility_id, dummy_block_1, tenant_id="merch_tech_solutions")
    assert fac.status == FacilityStatus.AMORTIZING
    assert ev1.sweep_deduction_paise == expected_day1_sweep
    assert ev1.net_merchant_payout_paise == 2000000 - expected_day1_sweep
    assert fac.remaining_balance_paise == offer.total_repayment_paise - expected_day1_sweep

    # Simulate Day 2 massive settlement of Rs 500,000 (overshoots remaining balance)
    dummy_block_2 = ReconciledSettlementBlock(
        settlement_id="setl_002",
        utr_number="HDFCN002",
        lump_sum_paise=50000000,
        gross_gmv_paise=50000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["INV-02"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash2",
    )
    remaining_before_day2 = fac.remaining_balance_paise
    fac, ev2 = facility_manager.process_settlement_sweep(facility.facility_id, dummy_block_2, tenant_id="merch_tech_solutions")
    
    # Sweep cannot over-deduct: capped precisely at remaining balance
    assert ev2.sweep_deduction_paise == remaining_before_day2
    assert ev2.net_merchant_payout_paise == 50000000 - remaining_before_day2
    assert fac.remaining_balance_paise == 0
    assert fac.status == FacilityStatus.REPAID
    
    # Conservation of Money Proof: Total deductions == Total Repayment
    total_deducted = ev1.sweep_deduction_paise + ev2.sweep_deduction_paise
    assert total_deducted == facility.total_repayment_paise


def test_stagnancy_and_fldg_failure_state_transitions(underwriter, facility_manager):
    """Test 14-day stagnancy and 30-day FLDG review failure transitions."""
    generator = ChaosDataGenerator(seed=42)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=100)
    engine = ReconciliationEngine()
    blocks, _ = engine.reconcile_batch(bank_credits, invoices)
    
    offer = underwriter.generate_offer("merch_dormant", blocks, invoices, requested_advance_paise=1000000)
    facility = facility_manager.disburse_advance(offer, tenant_id="merch_dormant")
    
    t0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    facility_manager.update_last_settlement_time(facility.facility_id, "merch_dormant", t0)
    
    # Check at Day 5: Active
    fac = facility_manager.evaluate_stagnancy(facility.facility_id, tenant_id="merch_dormant", current_time=t0 + timedelta(days=5))
    assert fac.status == FacilityStatus.ACTIVE
    
    # Check at Day 15: STAGNANT_RECOVERY
    fac = facility_manager.evaluate_stagnancy(facility.facility_id, tenant_id="merch_dormant", current_time=t0 + timedelta(days=15))
    assert fac.status == FacilityStatus.STAGNANT_RECOVERY
    
    # Check at Day 31: FLDG_REVIEW (capped at 5% portfolio FLDG under RBI norms)
    fac = facility_manager.evaluate_stagnancy(facility.facility_id, tenant_id="merch_dormant", current_time=t0 + timedelta(days=31))
    assert fac.status == FacilityStatus.FLDG_REVIEW


def test_tier_boundary_pricing_smooth_continuity(underwriter):
    """Test that fee rates and sweep rates change smoothly without cliff-edge jumps across the entire SRI spectrum."""
    # Test step-by-step across 0.9000 to 1.0000 in 0.001 increments
    sri_steps = [Decimal(str(i / 1000)).quantize(Decimal("0.001")) for i in range(900, 1001)]
    
    # Mock data setup
    inv = InvoiceRecord(
        invoice_id="INV-SMOOTH-01",
        order_id="order_smooth_01",
        payment_id="pay_smooth_01",
        supplier_gstin="29ABCDE1234F1Z5",
        amount_in_paise=10000000,  # Rs 100,000
        captured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    block = ReconciledSettlementBlock(
        settlement_id="setl_smooth",
        utr_number="HDFCSMOOTH",
        lump_sum_paise=10000000,
        gross_gmv_paise=10000000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=[inv.invoice_id],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash",
    )

    prev_fee_rate = None
    prev_sweep_rate = None

    for sri_val in sri_steps:
        # Patch compute_sri temporarily to test raw underwriting term transitions
        original_compute_sri = underwriter.compute_sri
        underwriter.compute_sri = lambda *args, **kwargs: sri_val
        try:
            offer = underwriter.generate_offer("merch_test_smooth", [block], [inv])
        finally:
            underwriter.compute_sri = original_compute_sri

        if prev_fee_rate is not None:
            fee_diff = abs(offer.factor_fee_paise - prev_fee_rate)
            # For a 0.001 delta on Rs 25,000 capacity, max fee difference must be <= Rs 25 (0.10% bound)
            assert fee_diff <= 2500, f"Fee jump {fee_diff} paise too large at SRI {sri_val}"
            
            sweep_diff = abs(offer.sweep_rate - prev_sweep_rate)
            # Sweep rate delta for 0.001 SRI step must be <= 0.0010 (10 bps)
            assert sweep_diff <= Decimal("0.0010"), f"Sweep jump {sweep_diff} too large at SRI {sri_val}"

        prev_fee_rate = offer.factor_fee_paise
        prev_sweep_rate = offer.sweep_rate

