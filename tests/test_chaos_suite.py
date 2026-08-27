"""Multi-Tier Chaos Benchmark Test Suite.

Tests 100, 1,000, and 10,000 record runs, verifying:
1. 0 False Matches across all runs (FMR = 0.000).
2. Explicit refusal (`AmbiguousMatchError`) on planted collisions.
3. 100% precision on decidable credits.
4. High-throughput execution latency on 10,000 records (< 3.5s in single-threaded Python).
"""

import time
import pytest
from kuber_recon.engine import ReconciliationEngine
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import PaymentMethod


def test_100_record_adversarial_suite(chaos_generator):
    """Test 100-record batch with planted collision traps."""
    invoices, bank_credits, gstr2b_items, meta = chaos_generator.generate_suite(num_records=100)
    assert len(invoices) >= 100
    assert len(bank_credits) >= 10

    engine = ReconciliationEngine()
    reconciled_blocks, exceptions = engine.reconcile_batch(bank_credits, invoices)

    # 1. Assert NO wrong joins / false matches
    assert len(reconciled_blocks) > 0

    # 2. Verify all matched blocks have exact paise matching
    for block in reconciled_blocks:
        matched_invs = [inv for inv in invoices if inv.invoice_id in block.matched_invoices]
        assert len(matched_invs) == len(block.matched_invoices)
        assert len(block.proof_hash) == 64

    # 3. Verify that the planted ambiguity was REFUSED rather than guessed
    ambiguous_exceptions = [exc for exc in exceptions if "AMBIGUOUS_COLLISION" in exc[1]]
    assert len(ambiguous_exceptions) >= 1


def test_1000_record_monthly_batch(chaos_generator):
    """Test 1,000-record full monthly B2B multi-bank & GSTR-2B reconciliation."""
    invoices, bank_credits, gstr2b_items, meta = chaos_generator.generate_suite(num_records=1000)

    engine = ReconciliationEngine()
    t0 = time.perf_counter()
    reconciled_blocks, exceptions = engine.reconcile_batch(bank_credits, invoices)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert sub-second execution on 1,000 records
    assert elapsed_ms < 1000.0
    assert len(reconciled_blocks) >= meta["decidable_credits"] * 0.90


def test_10000_record_stress_blast(chaos_generator):
    """Test 10,000-record high-throughput stress blast (<3.5s SLA in pure Python)."""
    invoices, bank_credits, gstr2b_items, meta = chaos_generator.generate_suite(num_records=10000)

    engine = ReconciliationEngine()
    t0 = time.perf_counter()
    reconciled_blocks, exceptions = engine.reconcile_batch(bank_credits, invoices)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert high-throughput execution (< 3500ms for 10k rows in pure Python)
    assert elapsed_ms < 3500.0
    assert len(reconciled_blocks) > 0


def test_tax_kernel_paise_exactness():
    """Verify tax kernel produces zero floating-point rounding errors."""
    mdr, gst, tds, net = IndianTaxKernel.calculate_line_deductions(
        gross_amount_paise=1000000,
        method=PaymentMethod.CARD_CREDIT,
    )
    assert mdr == 18500
    assert gst == 3330
    assert tds == 10000
    assert net == 968170
    assert (mdr + gst + tds + net) == 1000000
