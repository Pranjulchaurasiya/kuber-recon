"""Pytest Suite for Causal Financial Digital Twin Simulation."""

from decimal import Decimal
import pytest
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.simulation import FinancialDigitalTwin


@pytest.fixture
def digital_twin_fixture():
    generator = ChaosDataGenerator(seed=42)
    invoices, _, _, _ = generator.generate_suite(num_records=100)
    return FinancialDigitalTwin(invoices=invoices)


def test_simulate_bank_holiday_liquidity_freeze(digital_twin_fixture):
    """Test 4-day festive bank holiday freeze simulation."""
    res = digital_twin_fixture.simulate_bank_holiday_liquidity_freeze(holiday_days=4)

    assert res.settlement_delay_days == 4
    assert res.liquidity_delta_paise < 0
    assert "Razorpay On-Demand Instant Settlement" in res.recommended_hedging_action
    assert len(res.proof_manifest_hash) == 64


def test_simulate_vendor_gst_default_cascade(digital_twin_fixture):
    """Test simulating 25% vendor GSTR-1 default cascade."""
    res = digital_twin_fixture.simulate_vendor_gst_default_cascade(
        defaulting_vendor_gstin="29ABCDE1234F1Z5",
        vendor_gmv_share_pct=Decimal("0.25"),
    )

    assert res.tax_at_risk_paise > 0
    assert res.simulated_net_settlement_paise < res.baseline_net_settlement_paise
    assert "KuberSovereign Escrow" in res.recommended_hedging_action


def test_simulate_regulatory_tds_hike_206ab(digital_twin_fixture):
    """Test simulating CBDT Section 206AB 5% higher TDS enforcement."""
    res = digital_twin_fixture.simulate_regulatory_tds_hike_206ab(non_filer_ratio=Decimal("0.30"))

    assert res.tax_at_risk_paise > 0
    assert res.simulated_net_settlement_paise < res.baseline_net_settlement_paise
    assert "higher tax deductions" in res.recommended_hedging_action
