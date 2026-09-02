"""Adversarial Global Multi-Cluster Ambiguity, Manual Review, and Anti-Greedy Reconciliation Tests.
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from kuber_recon.engine import ClusteredReconciliationPipeline
from kuber_recon.storage import SQLiteStorageBackend
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod


def test_global_cross_gstin_collision():
    """Verify that if two distinct clusters (Supplier A and Supplier B) both offer a valid
    exact subset-sum cover for a bank credit, the pipeline refuses both with AMBIGUOUS_COLLISION
    instead of greedily consuming the first alphabetical cluster."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)

    inv_a = InvoiceRecord(
        invoice_id="INV_A_AMBIG",
        order_id="ord_a",
        payment_id="pay_a",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
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

    collision_ex = [ex for _, ex in exceptions if "AMBIGUOUS_COLLISION" in ex]
    assert len(collision_ex) == 1
    assert "2 distinct clusters" in collision_ex[0]


def test_global_cross_date_collision():
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


def test_global_payment_method_collision():
    """Verify that identical gross amounts under different payment methods generate distinct clusters and refuse collision."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)

    inv_upi = InvoiceRecord(
        invoice_id="INV_METH_UPI",
        order_id="ord_u",
        payment_id="pay_u",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_card = InvoiceRecord(
        invoice_id="INV_METH_CARD",
        order_id="ord_c",
        payment_id="pay_c",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.CARD_CREDIT,
        captured_at=t0,
    )

    _, _, _, net_upi = IndianTaxKernel.calculate_line_deductions(100000, PaymentMethod.UPI)
    credit = BankNodalCredit(
        utr_number="UTR_METHOD_COLLISION",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_upi,
        value_date=t0.date(),
        raw_narration="NFX-RZR*METHOD*COLLISION",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit], [inv_upi, inv_card])
    # UPI matches net_upi exactly; CARD has different MDR so it won't match net_upi.
    # Therefore UPI matches cleanly without collision.
    assert len(reconciled) == 1
    assert reconciled[0].matched_invoices == ["INV_METH_UPI"]


def test_ambiguous_match_consumes_nothing():
    """Verify that when an ambiguous collision occurs, neither candidate invoice is consumed."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    inv_a = InvoiceRecord(
        invoice_id="INV_A_UNCONSUMED",
        order_id="ord_a",
        payment_id="pay_a",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_b = InvoiceRecord(
        invoice_id="INV_B_UNCONSUMED",
        order_id="ord_b",
        payment_id="pay_b",
        amount_in_paise=100000,
        supplier_gstin="29BBBBB2222B2Z2",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )

    _, _, _, net_paise = IndianTaxKernel.calculate_line_deductions(100000, PaymentMethod.UPI)
    credit_ambig = BankNodalCredit(
        utr_number="UTR_AMBIG_1",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_paise,
        value_date=t0.date(),
        raw_narration="NFX-RZR*AMBIG",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit_ambig], [inv_a, inv_b])

    assert len(reconciled) == 0
    assert metrics.ambiguous_refusal_exceptions == 1

    # Follow-up run with unambiguous credit for inv_a can still match it (not poisoned/consumed)
    reconciled_clean, _, _ = pipeline.process_large_batch([credit_ambig], [inv_a])
    assert len(reconciled_clean) == 1
    assert reconciled_clean[0].matched_invoices == ["INV_A_UNCONSUMED"]


def test_dense_cluster_creates_manual_review_record(tmp_path):
    """Verify that clusters exceeding max_cluster_size create durable manual review records in storage."""
    backend = SQLiteStorageBackend(db_path=":memory:")
    pipeline = ClusteredReconciliationPipeline(max_cluster_size=5, backend=backend)

    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    gstin = "27AAPCA9999Z1Z0"
    invoices = [
        InvoiceRecord(
            invoice_id=f"INV_DENSE_{i}",
            order_id=f"ord_dense_{i}",
            payment_id=f"pay_dense_{i}",
            amount_in_paise=10000 + i * 100,
            supplier_gstin=gstin,
            method=PaymentMethod.UPI,
            captured_at=t0,
        )
        for i in range(10)
    ]
    credit = BankNodalCredit(
        utr_number="UTR_DENSE_MANUAL_TEST",
        account_number="ACC_12345678",
        credit_amount_in_paise=999999,
        value_date=t0.date(),
        raw_narration="NFX-RZR*SETTL*DENSE",
    )

    reconciled, exceptions, metrics = pipeline.process_large_batch([credit], invoices, tenant_id="tenant_dense_audit")
    assert metrics.inconclusive_truncated_exceptions >= 1

    # Verify manual review records were persisted into storage
    mr_records = backend.list_manual_review_records(tenant_id="tenant_dense_audit")
    assert len(mr_records) >= 1
    record = mr_records[0]
    assert record["tenant_id"] == "tenant_dense_audit"
    assert record["category"] == "DENSE_CLUSTER"
    assert record["status"] == "PENDING"
    assert "Cluster exceeded max_cluster_size" in record["reason"]


def test_duplicate_invoice_ids_rejected():
    """Verify that batches containing duplicate invoice IDs are strictly rejected."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    inv1 = InvoiceRecord(
        invoice_id="INV_DUPLICATE",
        order_id="ord_1",
        payment_id="pay_1",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv2 = InvoiceRecord(
        invoice_id="INV_DUPLICATE",
        order_id="ord_2",
        payment_id="pay_2",
        amount_in_paise=150000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    pipeline = ClusteredReconciliationPipeline()
    with pytest.raises(ValueError, match="Duplicate invoice ID"):
        pipeline.process_large_batch([], [inv1, inv2])


def test_mixed_tenant_batch_rejected():
    """Verify that batches containing invoices from multiple tenants are strictly rejected."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    inv_a = InvoiceRecord(
        invoice_id="INV_TENANT_A",
        order_id="ord_a",
        payment_id="pay_a",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_b = InvoiceRecord(
        invoice_id="INV_TENANT_B",
        order_id="ord_b",
        payment_id="pay_b",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_a.tenant_id = "tenant_alpha"
    inv_b.tenant_id = "tenant_beta"

    pipeline = ClusteredReconciliationPipeline()
    with pytest.raises(ValueError, match="Cross-tenant invoice reuse violation"):
        pipeline.process_large_batch([], [inv_a, inv_b])


def test_reconciliation_is_deterministic():
    """Verify that repeated runs with identical inputs produce identical outcomes."""
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
    assert [ex[1] for ex in e1] == [ex[1] for ex in e2]
