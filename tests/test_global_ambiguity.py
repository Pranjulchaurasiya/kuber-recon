"""Adversarial Global Multi-Cluster Ambiguity & Anti-Greedy Reconciliation Tests.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
from kuber_recon.engine import ClusteredReconciliationPipeline
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod


def test_global_cross_cluster_ambiguity_collision_refusal():
    """Verify that if two distinct clusters (Supplier A and Supplier B) both offer a valid
    exact subset-sum cover for a bank credit, the pipeline refuses both with AMBIGUOUS_COLLISION
    instead of greedily consuming the first alphabetical cluster."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)

    # Supplier A: ₹1,000 invoice (net ₹978.76)
    inv_a = InvoiceRecord(
        invoice_id="INV_A_AMBIG",
        order_id="ord_a",
        payment_id="pay_a",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    # Supplier B: ₹1,000 invoice (net ₹978.76)
    inv_b = InvoiceRecord(
        invoice_id="INV_B_AMBIG",
        order_id="ord_b",
        payment_id="pay_b",
        amount_in_paise=100000,
        supplier_gstin="29BBBBB2222B2Z2",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )

    _, _, _, net_paise = IndianTaxKernel.calculate_line_deductions(100000, PaymentMethod.UPI)
    
    # Ambiguous lump sum credit that could match either Supplier A or Supplier B
    credit = BankNodalCredit(
        utr_number="UTR_GLOBAL_AMBIG_COLLISION",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_paise,
        value_date=t0.date(),
        raw_narration="NFX-RZR*AMBIGUOUS*COLLISION",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit], [inv_a, inv_b])

    # Invariant: 0 Reconciled blocks (Refusal over false join)
    assert len(reconciled) == 0
    assert metrics.exact_reconciled_blocks == 0
    assert metrics.ambiguous_refusal_exceptions == 1
    assert metrics.false_matches_observed == 0

    # Verify exception reason details the cross-cluster collision
    collision_ex = [ex for _, ex in exceptions if "AMBIGUOUS_COLLISION" in ex]
    assert len(collision_ex) == 1
    assert "2 distinct clusters" in collision_ex[0]


def test_cross_date_cluster_collision_refusal():
    """Verify that identical amounts across two different capture dates colliding on a credit are refused."""
    t_day1 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    t_day2 = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)

    inv_day1 = InvoiceRecord(
        invoice_id="INV_DAY_1",
        order_id="ord_d1",
        payment_id="pay_d1",
        amount_in_paise=200000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t_day1,
    )
    inv_day2 = InvoiceRecord(
        invoice_id="INV_DAY_2",
        order_id="ord_d2",
        payment_id="pay_d2",
        amount_in_paise=200000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t_day2,
    )

    _, _, _, net_paise = IndianTaxKernel.calculate_line_deductions(200000, PaymentMethod.UPI)
    credit = BankNodalCredit(
        utr_number="UTR_CROSS_DATE_COLLISION",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_paise,
        value_date=date(2026, 3, 11),
        raw_narration="NFX-RZR*DATE*COLLISION",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit], [inv_day1, inv_day2])

    assert len(reconciled) == 0
    assert metrics.ambiguous_refusal_exceptions == 1
    assert metrics.false_matches_observed == 0


def test_clustered_reconciliation_deterministic_repeatability():
    """Verify that running the exact same batch 3 times yields identical results."""
    from kuber_recon.generator import ChaosDataGenerator
    generator = ChaosDataGenerator(seed=777)
    invoices, credits, _, _ = generator.generate_suite(num_records=75)

    pipeline = ClusteredReconciliationPipeline()
    r1, e1, m1 = pipeline.process_large_batch(credits, invoices)
    r2, e2, m2 = pipeline.process_large_batch(credits, invoices)

    assert m1.exact_reconciled_blocks == m2.exact_reconciled_blocks
    assert m1.ambiguous_refusal_exceptions == m2.ambiguous_refusal_exceptions
    assert m1.false_matches_observed == m2.false_matches_observed == 0
    assert [b.proof_hash for b in r1] == [b.proof_hash for b in r2]
