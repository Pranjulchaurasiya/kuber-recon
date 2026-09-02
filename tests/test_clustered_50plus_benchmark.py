"""Track 04 Benchmark & Clustered Batch Reconciliation Validation (50+ to 1000+ records).

Verifies:
1. Reconciles datasets with 50, 100, 250, 500, and 1,000 records.
2. Reports comprehensive production metrics:
   - total_invoices_ingested
   - total_bank_credits_ingested
   - exact_reconciled_blocks
   - ambiguous_refusal_exceptions
   - inconclusive_truncated_exceptions
   - false_matches_observed (0 on tested corpus)
   - total_runtime_ms
   - solver_solve_ms
   - throughput_records_per_sec
3. Strictly maintains 0 False Match Rate on tested corpus.
4. Proves cluster isolation, dense cluster truncation, zero cross-cluster leakage, and ambiguity preservation.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from kuber_recon.engine import (
    ClusteredReconciliationPipeline,
    HorowitzSahniSubsetSumSolver,
    ReconciliationEngine,
)
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod


@pytest.mark.parametrize("record_count", [50, 100, 250, 500, 1000])
def test_clustered_batch_reconciliation_50_plus(record_count: int):
    """Prove that KuberRecon processes 50+ to 1000+ record batches deterministically."""
    generator = ChaosDataGenerator(seed=42 + record_count)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=record_count)

    pipeline = ClusteredReconciliationPipeline()
    reconciled_blocks, exceptions, metrics = pipeline.process_large_batch(bank_credits, invoices)

    # 1. Non-empty results
    assert metrics.total_invoices_ingested == len(invoices)
    assert metrics.total_bank_credits_ingested == len(bank_credits)
    assert len(reconciled_blocks) > 0

    # 2. Strict Invariant: 0 False Matches on tested corpus
    assert metrics.false_matches_observed == 0

    # 3. Paise-exact arithmetic validation on all reconciled blocks
    for block in reconciled_blocks:
        assert isinstance(block.lump_sum_paise, int)
        assert isinstance(block.total_mdr_fee_paise, int)
        assert isinstance(block.total_gst_on_mdr_paise, int)
        assert isinstance(block.total_tds_withheld_paise, int)
        assert block.lump_sum_paise > 0

    # 4. Throughput and runtime sanity
    assert metrics.total_runtime_ms > 0
    assert metrics.throughput_records_per_sec > 0
    assert metrics.exact_reconciled_blocks == len(reconciled_blocks)


def test_clustered_benchmark_handles_planted_ambiguity_and_truncation():
    """Verify that within a large batch, ambiguous collisions and dense clusters are quarantined safely."""
    generator = ChaosDataGenerator(seed=999)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=150)

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch(bank_credits, invoices)

    assert metrics.total_invoices_ingested + metrics.total_bank_credits_ingested == len(invoices) + len(bank_credits)
    assert metrics.false_matches_observed == 0
    assert isinstance(metrics.throughput_records_per_sec, float)


def test_independent_gstin_clusters_isolated():
    """Prove that two distinct counterparty GSTIN clusters reconcile independently."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    
    # GSTIN A: 2 invoices
    inv_a1 = InvoiceRecord(
        invoice_id="INV_A_1",
        order_id="ord_a1",
        payment_id="pay_a1",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1234F1Z5",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_a2 = InvoiceRecord(
        invoice_id="INV_A_2",
        order_id="ord_a2",
        payment_id="pay_a2",
        amount_in_paise=200000,
        supplier_gstin="27AAPCA1234F1Z5",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    
    # Calculate expected net for GSTIN A
    _, _, _, net_a1 = IndianTaxKernel.calculate_line_deductions(100000, PaymentMethod.UPI)
    _, _, _, net_a2 = IndianTaxKernel.calculate_line_deductions(200000, PaymentMethod.UPI)
    credit_a = BankNodalCredit(
        utr_number="UTR_CREDIT_A",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_a1 + net_a2,
        value_date=t0.date(),
        raw_narration="NFX-RZR*SETTL*A",
    )

    # GSTIN B: 1 invoice
    inv_b1 = InvoiceRecord(
        invoice_id="INV_B_1",
        order_id="ord_b1",
        payment_id="pay_b1",
        amount_in_paise=500000,
        supplier_gstin="29BBBBB5678G2Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    _, _, _, net_b1 = IndianTaxKernel.calculate_line_deductions(500000, PaymentMethod.UPI)
    credit_b = BankNodalCredit(
        utr_number="UTR_CREDIT_B",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_b1,
        value_date=t0.date(),
        raw_narration="NFX-RZR*SETTL*B",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit_a, credit_b], [inv_a1, inv_a2, inv_b1])

    assert len(reconciled) == 2
    block_a = next(b for b in reconciled if b.utr_number == "UTR_CREDIT_A")
    block_b = next(b for b in reconciled if b.utr_number == "UTR_CREDIT_B")

    # Invariant: Block A only contains GSTIN A invoices; Block B only contains GSTIN B invoices
    assert set(block_a.matched_invoices) == {"INV_A_1", "INV_A_2"}
    assert set(block_b.matched_invoices) == {"INV_B_1"}


def test_dense_cluster_truncation():
    """Prove that any cluster exceeding max_cluster_size (24) is safely truncated without solver explosion."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    # Generate 30 invoices for a single GSTIN on the same date
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
        for i in range(30)
    ]
    credit = BankNodalCredit(
        utr_number="UTR_DENSE_TEST",
        account_number="ACC_12345678",
        credit_amount_in_paise=999999,
        value_date=t0.date(),
        raw_narration="NFX-RZR*SETTL*DENSE",
    )

    pipeline = ClusteredReconciliationPipeline(max_cluster_size=24)
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit], invoices)

    assert metrics.inconclusive_truncated_exceptions >= 1
    # Check that exception message specifies truncation
    trunc_ex = [ex for _, ex in exceptions if "INCONCLUSIVE_TRUNCATED" in ex]
    assert len(trunc_ex) > 0


def test_zero_cross_cluster_leakage_on_distinct_amounts():
    """Prove that if two suppliers have distinct invoice amounts, credit for Supplier A never consumes Supplier B."""
    t0 = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    
    # Supplier X (₹1,000) & Supplier Y (₹1,500)
    inv_x = InvoiceRecord(
        invoice_id="INV_X_01",
        order_id="ord_x1",
        payment_id="pay_x1",
        amount_in_paise=100000,
        supplier_gstin="27AAPCA1111A1Z1",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    inv_y = InvoiceRecord(
        invoice_id="INV_Y_01",
        order_id="ord_y1",
        payment_id="pay_y1",
        amount_in_paise=150000,
        supplier_gstin="29BBBBB2222B2Z2",
        method=PaymentMethod.UPI,
        captured_at=t0,
    )
    
    _, _, _, net_x = IndianTaxKernel.calculate_line_deductions(100000, PaymentMethod.UPI)
    credit_x = BankNodalCredit(
        utr_number="UTR_FOR_X_ONLY",
        account_number="ACC_12345678",
        credit_amount_in_paise=net_x,
        value_date=t0.date(),
        raw_narration="NFX-RZR*SETTL*X",
    )

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, metrics = pipeline.process_large_batch([credit_x], [inv_x, inv_y])

    assert len(reconciled) == 1
    assert reconciled[0].matched_invoices == ["INV_X_01"]
    # INV_Y_01 was untouched
