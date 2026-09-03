"""Tests for High-Frequency UPI Identical-Amount Multi-Set Pre-Solver.

Verifies:
1. Solving hundreds of identical SKU prices (e.g. Rs 499) without combinatorial explosion.
2. Multi-class bounded integer knapsack solving (e.g., Rs 499 and Rs 999 items).
3. Ambiguity collision detection when multiple distinct allocations sum to target.
4. No-match handling on non-matching targets.
"""

from datetime import datetime, timezone
import pytest

from kuber_recon.types import InvoiceRecord, MatchResultStatus
from kuber_recon.upi_presolver import UPIIdenticalAmountPreSolver


def _make_invoice(inv_id: str, amount_paise: int) -> InvoiceRecord:
    return InvoiceRecord(
        invoice_id=inv_id,
        order_id=f"order_{inv_id}",
        payment_id=f"pay_{inv_id}",
        amount_in_paise=amount_paise,
        supplier_gstin="27AAPFU0939F1ZV",
        captured_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc),
        tds_194o_rate_basis="PAN_VERIFIED_1PCT",
    )


def test_single_class_identical_amounts_solve():
    solver = UPIIdenticalAmountPreSolver()

    # 100 identical invoices of Rs 499 (49,900 paise)
    invoices = [_make_invoice(f"INV-499-{i:03d}", 49900) for i in range(100)]
    
    # Target: exactly 42 orders = 42 * 49,900 = 2,095,800 paise
    target_paise = 42 * 49900
    res = solver.solve_exact(target_paise, invoices)

    assert res.status == MatchResultStatus.EXACT_MATCH
    assert len(res.solutions) == 1
    assert len(res.solutions[0]) == 42
    # Verify deterministic selection of the first 42 invoices sorted by ID
    assert res.solutions[0][0] == "INV-499-000"
    assert res.solutions[0][-1] == "INV-499-041"


def test_multi_class_bounded_knapsack_solve():
    solver = UPIIdenticalAmountPreSolver()

    # 50 items of Rs 499 (49,900 paise) and 30 items of Rs 999 (99,900 paise)
    invoices_499 = [_make_invoice(f"INV-499-{i:03d}", 49900) for i in range(50)]
    invoices_999 = [_make_invoice(f"INV-999-{i:03d}", 99900) for i in range(30)]
    invoices = invoices_499 + invoices_999

    # Target: exactly 5 items of 999 + 10 items of 499
    # 5 * 99900 = 499,500
    # 10 * 49900 = 499,000
    # Total = 998,500 paise
    target_paise = (5 * 99900) + (10 * 49900)
    res = solver.solve_exact(target_paise, invoices)

    assert res.status == MatchResultStatus.EXACT_MATCH
    assert len(res.solutions) == 1
    matched = res.solutions[0]
    assert len(matched) == 15
    matched_499 = [m for m in matched if "INV-499" in m]
    matched_999 = [m for m in matched if "INV-999" in m]
    assert len(matched_499) == 10
    assert len(matched_999) == 5


def test_ambiguous_collision_refusal():
    solver = UPIIdenticalAmountPreSolver()

    # Invoices where 2 * Rs 500 == 1 * Rs 1,000
    invoices = [
        _make_invoice("INV-500-1", 50000),
        _make_invoice("INV-500-2", 50000),
        _make_invoice("INV-1000-1", 100000),
    ]

    # Target: Rs 1,000 (100,000 paise)
    # Candidate 1: INV-1000-1
    # Candidate 2: INV-500-1 + INV-500-2
    res = solver.solve_exact(100000, invoices)

    assert res.status == MatchResultStatus.AMBIGUOUS_COLLISION
    assert len(res.solutions) == 2


def test_no_match_returns_cleanly():
    solver = UPIIdenticalAmountPreSolver()
    invoices = [_make_invoice(f"INV-499-{i:03d}", 49900) for i in range(5)]

    # Target not reachable by any combination of 49,900
    res = solver.solve_exact(123456, invoices)
    assert res.status == MatchResultStatus.NO_MATCH
    assert len(res.solutions) == 0
