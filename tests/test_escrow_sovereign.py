"""Pytest Suite for Hardened KuberSovereign Pre-Settlement Route Escrow."""

from decimal import Decimal
import pytest
from kuber_recon.escrow import EscrowStatus, KuberSovereignEscrowEngine
from kuber_recon.types import PaymentMethod


@pytest.fixture
def sovereign_engine():
    return KuberSovereignEscrowEngine()


def test_escrow_split_standard_18(sovereign_engine):
    """Test standard 18% B2B GST payment capture."""
    gross_paise = 11800000  # ₹1,18,000.00

    split = sovereign_engine.intercept_and_split_payment(
        order_id="order_sov_001",
        payment_id="pay_sov_001",
        gross_amount_paise=gross_paise,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
        gst_rate_pct=Decimal("0.18"),
    )

    assert split.gross_captured_paise == 11800000
    assert split.gst_escrow_paise == 1800000  # ₹18,000 held in escrow
    assert split.tds_194o_paise == 118000  # 1% TDS = ₹1,180
    assert split.escrow_status == EscrowStatus.ON_HOLD


def test_escrow_dynamic_slabs_5_and_28(sovereign_engine):
    """Test dynamic statutory slabs (5% apparel & 28% luxury)."""
    # 5% slab on ₹1,05,000 gross (₹1,00,000 principal + ₹5,000 GST)
    split_5 = sovereign_engine.intercept_and_split_payment(
        order_id="order_apparel_01",
        payment_id="pay_apparel_01",
        gross_amount_paise=10500000,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
        gst_rate_pct=Decimal("0.05"),
    )
    assert split_5.gst_escrow_paise == 500000  # ₹5,000 GST

    # 28% slab on ₹1,28,000 gross (₹1,00,000 principal + ₹28,000 GST)
    split_28 = sovereign_engine.intercept_and_split_payment(
        order_id="order_luxury_01",
        payment_id="pay_luxury_01",
        gross_amount_paise=12800000,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
        gst_rate_pct=Decimal("0.28"),
    )
    assert split_28.gst_escrow_paise == 2800000  # ₹28,000 GST


def test_escrow_webhook_idempotency_replay(sovereign_engine):
    """Test concurrent or duplicate webhook delivery is deduplicated without mutation."""
    split1 = sovereign_engine.intercept_and_split_payment(
        order_id="order_idem_01",
        payment_id="pay_idem_01",
        gross_amount_paise=11800000,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
    )

    # Replay identical webhook
    split2 = sovereign_engine.intercept_and_split_payment(
        order_id="order_idem_01",
        payment_id="pay_idem_01",
        gross_amount_paise=11800000,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
    )

    assert split1.split_id == split2.split_id
    assert len(sovereign_engine.escrows) == 1  # Exactly 1 record in memory


def test_escrow_partial_refund_proportionate_shrinkage(sovereign_engine):
    """Test customer partial refund on Day 5 shrinks escrow proportionately."""
    split = sovereign_engine.intercept_and_split_payment(
        order_id="order_partial_01",
        payment_id="pay_partial_01",
        gross_amount_paise=11800000,  # ₹1,18,000 total (₹18,000 GST)
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
    )

    # Customer returns 50% of the goods (₹59,000 refund)
    res = sovereign_engine.apply_partial_refund(
        split_id=split.split_id,
        refund_amount_paise=5900000,  # 50% refund
    )

    assert res["status"] == "PARTIAL_REFUND_APPLIED"
    assert res["gst_escrow_reduced_by_paise"] == 900000  # ₹9,000 GST refunded
    assert split.gst_escrow_paise == 900000  # ₹9,000 GST remains
    assert split.escrow_status == EscrowStatus.PARTIALLY_REFUNDED


def test_escrow_section_194o_exemption_bypass(sovereign_engine):
    """Test micro-merchant statutory exemption bypass under Section 194-O."""
    split = sovereign_engine.intercept_and_split_payment(
        order_id="order_exempt_01",
        payment_id="pay_exempt_01",
        gross_amount_paise=11800000,
        supplier_gstin="29ABCDE1234F1Z5",
        merchant_gstin="27XYZAB9876C1Z2",
        is_section_194o_exempt=True,
    )

    assert split.tds_194o_paise == 0  # 0% TDS withheld
    assert split.is_section_194o_exempt is True
