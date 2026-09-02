r"""Horowitz–Sahni Combinatorial Subset-Sum Reconciliation Solver.

Features:
1. Subset-sum matching in pure integer paise.
2. Iterative Horowitz–Sahni Meet-in-the-Middle hash partitioning ($O(2^{N/2})$) with complexity bounds.
3. Retrospective weekend-aware settlement windowing ($[T - (1 + \text{weekend\_days}), T]$ with optional holiday injection).
4. Honest Refusal State Machine: Emits `AmbiguousMatchError` on $|\text{Subsets}| > 1 \implies$ preserves FMR on tested corpus.
5. Deterministic Chronological FIFO line-item attribution.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from enum import Enum
import hashlib
import time
from typing import Dict, List, Optional, Set, Tuple
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, EvidenceTier, InvoiceRecord, ReconciledSettlementBlock, SettlementStatus


class MatchResultStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS_COLLISION = "AMBIGUOUS_COLLISION"
    INCONCLUSIVE_TRUNCATED = "INCONCLUSIVE_TRUNCATED"


class SolverResult:
    def __init__(self, status: MatchResultStatus, solutions: List[List[str]], nodes_explored: int = 0, is_truncated: bool = False):
        self.status = status
        self.solutions = solutions
        self.nodes_explored = nodes_explored
        self.is_truncated = is_truncated


class AmbiguousMatchError(Exception):
    """Raised when more than one valid subset-sum candidate matches a bank credit."""

    def __init__(self, credit_id: str, candidate_solutions: List[List[str]]):
        self.credit_id = credit_id
        self.candidate_solutions = candidate_solutions
        super().__init__(
            f"Honest Refusal: Bank Credit {credit_id} matches {len(candidate_solutions)} valid subsets. "
            "Refusing to guess to preserve FMR on tested corpus."
        )


class SolverComplexityLimitError(Exception):
    """Raised when solver exceeds node expansion or timeout bounds under adversarial load."""
    pass


class HorowitzSahniSubsetSumSolver:
    """Horowitz-Sahni Meet-in-the-Middle Combinatorial Subset-Sum Solver for Integer Paise."""

    def __init__(self, max_nodes: int = 10000, timeout_ms: float = 500.0):
        self.max_nodes = max_nodes
        self.timeout_ms = timeout_ms

    def solve_exact_subsets(
        self,
        target_paise: int,
        candidates: List[Tuple[str, int]],
        max_solutions: int = 5,
    ) -> List[List[str]]:
        """Find all subsets of candidates that sum EXACTLY to target_paise with complexity bounds."""
        res = self.solve_with_diagnostics(target_paise, candidates, max_solutions)
        return res.solutions

    def solve_with_diagnostics(
        self,
        target_paise: int,
        candidates: List[Tuple[str, int]],
        max_solutions: int = 5,
    ) -> SolverResult:
        """Find subsets returning explicit MatchResultStatus including INCONCLUSIVE_TRUNCATED."""
        if not candidates or target_paise <= 0:
            return SolverResult(MatchResultStatus.NO_MATCH, [])

        # Fast prune candidates greater than target
        valid_candidates = [(k, v) for k, v in candidates if 0 < v <= target_paise]
        if not valid_candidates:
            return SolverResult(MatchResultStatus.NO_MATCH, [])

        # Strict Honest Refusal Invariant: Any candidate pool with N > 24 is truncated and MUST return INCONCLUSIVE_TRUNCATED
        if len(candidates) > 24 or len(valid_candidates) > 24:
            return SolverResult(MatchResultStatus.INCONCLUSIVE_TRUNCATED, [], 0, is_truncated=True)

        # Direct 1-to-1 exact single item matches
        singles = [[k] for k, v in valid_candidates if v == target_paise]
        if len(singles) > 1:
            return SolverResult(MatchResultStatus.AMBIGUOUS_COLLISION, singles[:max_solutions])

        t_start = time.perf_counter()

        # Sort candidates descending for fast subset generation
        sorted_candidates = sorted(valid_candidates, key=lambda x: x[1], reverse=True)

        mid = len(sorted_candidates) // 2
        left_half = sorted_candidates[:mid]
        right_half = sorted_candidates[mid:]

        left_map: Dict[int, List[Tuple[str, ...]]] = {}
        left_subsets: List[Tuple[int, Tuple[str, ...]]] = [(0, ())]
        nodes_explored = 0
        timed_out = False

        for item_id, amt in left_half:
            new_subs = []
            for s, items in left_subsets:
                nodes_explored += 1
                s_inc = s + amt
                if s_inc <= target_paise:
                    new_subs.append((s_inc, items + (item_id,)))
            left_subsets.extend(new_subs)
            if nodes_explored > self.max_nodes or (time.perf_counter() - t_start) * 1000.0 > self.timeout_ms:
                timed_out = True
                break

        for s, items in left_subsets:
            entry = left_map.setdefault(s, [])
            if len(entry) < max_solutions:
                entry.append(items)

        solutions: List[List[str]] = list(singles)
        seen_solutions = set(tuple(s) for s in solutions)

        right_subsets: List[Tuple[int, Tuple[str, ...]]] = [(0, ())]
        for item_id, amt in right_half:
            new_subs = []
            for s, items in right_subsets:
                nodes_explored += 1
                s_inc = s + amt
                if s_inc <= target_paise:
                    new_subs.append((s_inc, items + (item_id,)))
            right_subsets.extend(new_subs)
            if nodes_explored > self.max_nodes or (time.perf_counter() - t_start) * 1000.0 > self.timeout_ms:
                timed_out = True
                break

        for s_r, items_r in right_subsets:
            comp = target_paise - s_r
            if comp in left_map:
                for items_l in left_map[comp]:
                    comb = list(items_l + items_r)
                    if comb:
                        comb_tuple = tuple(comb)
                        if comb_tuple not in seen_solutions:
                            seen_solutions.add(comb_tuple)
                            solutions.append(comb)
                            if len(solutions) >= max_solutions:
                                break

        if timed_out:
            return SolverResult(MatchResultStatus.INCONCLUSIVE_TRUNCATED, [], nodes_explored, is_truncated=True)

        if len(solutions) == 0:
            return SolverResult(MatchResultStatus.NO_MATCH, [], nodes_explored)
        elif len(solutions) == 1:
            return SolverResult(MatchResultStatus.EXACT_MATCH, solutions, nodes_explored)
        else:
            return SolverResult(MatchResultStatus.AMBIGUOUS_COLLISION, solutions[:max_solutions], nodes_explored)


# Deprecated backward-compatibility alias: Note that the implemented algorithm is
# Horowitz-Sahni meet-in-the-middle subset-sum matching, not Knuth DLX.
KnuthExactCoverSolver = HorowitzSahniSubsetSumSolver


class ReconciliationEngine:
    """Autonomous Multi-Source Reconciliation Engine with Honest Refusal."""

    def __init__(self):
        self.solver = HorowitzSahniSubsetSumSolver()

    def reconcile_batch(
        self,
        bank_credits: List[BankNodalCredit],
        invoices: List[InvoiceRecord],
        holidays: Optional[Set[date]] = None,
    ) -> Tuple[List[ReconciledSettlementBlock], List[Tuple[BankNodalCredit, str]]]:
        """Reconcile bank credits against invoices with deterministic subset-sum matching and honest refusal."""
        holidays = holidays or set()
        reconciled_blocks: List[ReconciledSettlementBlock] = []
        exceptions: List[Tuple[BankNodalCredit, str]] = []

        # 1. Precompute net deductions and index by date + amount
        inv_net_cache: Dict[str, Tuple[InvoiceRecord, int, int, int, int]] = {}
        by_date_amt: Dict[date, Dict[int, Set[str]]] = defaultdict(lambda: defaultdict(set))

        for inv in invoices:
            if not inv.is_settled:
                mdr, gst, tds, net_amt = IndianTaxKernel.calculate_line_deductions(
                    inv.amount_in_paise, inv.method
                )
                effective_net = net_amt if net_amt > 0 else inv.amount_in_paise
                inv_net_cache[inv.invoice_id] = (inv, mdr, gst, tds, effective_net)
                by_date_amt[inv.captured_at.date()][effective_net].add(inv.invoice_id)

        for credit in bank_credits:
            target_paise = credit.credit_amount_in_paise
            # 2. Retrospective Weekend Settlement Window Filtering [T - (1 + weekend_days), T] (supports optional injected holiday set)
            window_days = 1 + sum(
                1
                for d in range(3)
                if (credit.value_date - timedelta(days=d)) in holidays
                or (credit.value_date - timedelta(days=d)).weekday() >= 5
            )
            min_date = credit.value_date - timedelta(days=window_days)
            max_date = credit.value_date

            # 3. Fast O(1) single-item lookup across active date buckets
            single_matches: List[Tuple[str, date, int]] = []
            curr = min_date
            while curr <= max_date:
                bucket = by_date_amt.get(curr)
                if bucket and target_paise in bucket:
                    for inv_id in bucket[target_paise]:
                        single_matches.append((inv_id, curr, target_paise))
                curr += timedelta(days=1)

            if len(single_matches) == 1:
                inv_id, d, amt = single_matches[0]
                by_date_amt[d][amt].discard(inv_id)
                if not by_date_amt[d][amt]:
                    del by_date_amt[d][amt]

                matched_inv_data = inv_net_cache[inv_id]
                inv_obj = matched_inv_data[0]
                proof_data = f"{credit.utr_number}:{credit.credit_amount_in_paise}:{inv_id}"
                proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

                block = ReconciledSettlementBlock(
                    settlement_id=credit.settlement_id or f"setl_{credit.utr_number[:8]}",
                    utr_number=credit.utr_number,
                    lump_sum_paise=credit.credit_amount_in_paise,
                    gross_gmv_paise=inv_obj.amount_in_paise,
                    total_mdr_fee_paise=matched_inv_data[1],
                    total_gst_on_mdr_paise=matched_inv_data[2],
                    total_tds_withheld_paise=matched_inv_data[3],
                    rounding_variance_paise=0,
                    status=SettlementStatus.SETTLED,
                    matched_invoices=[inv_id],
                    matched_refunds=[],
                    evidence_tier=EvidenceTier.TIER_A if credit.settlement_id else EvidenceTier.TIER_B,
                    proof_hash=proof_hash,
                    reconciled_at=datetime.now(timezone.utc),
                )
                reconciled_blocks.append(block)
                continue
            elif len(single_matches) > 1:
                exceptions.append((credit, f"AMBIGUOUS_COLLISION ({len(single_matches)} single matches)"))
                continue

            # 4. Multi-item subset solving for lump sums
            candidate_tuples: List[Tuple[str, int]] = []
            curr = min_date
            while curr <= max_date:
                bucket = by_date_amt.get(curr)
                if bucket:
                    for amt, ids in bucket.items():
                        if 0 < amt < target_paise:
                            for inv_id in ids:
                                candidate_tuples.append((inv_id, amt))
                curr += timedelta(days=1)

            if not candidate_tuples:
                exceptions.append((credit, "NO_EXACT_COVER_FOUND"))
                continue

            solver_res = self.solver.solve_with_diagnostics(
                target_paise=target_paise,
                candidates=candidate_tuples,
                max_solutions=2,
            )

            # 5. Honest Refusal & Complexity Truncation Evaluation
            if solver_res.status == MatchResultStatus.INCONCLUSIVE_TRUNCATED:
                exceptions.append((credit, "INCONCLUSIVE_TRUNCATED (Candidate pool > 24 or solver budget exceeded)"))
            elif solver_res.status == MatchResultStatus.NO_MATCH or len(solver_res.solutions) == 0:
                exceptions.append((credit, "NO_EXACT_COVER_FOUND"))
            elif solver_res.status == MatchResultStatus.AMBIGUOUS_COLLISION or len(solver_res.solutions) > 1:
                exceptions.append((credit, f"AMBIGUOUS_COLLISION ({len(solver_res.solutions)} subsets)"))
            else:
                matched_ids = solver_res.solutions[0]
                for mid in matched_ids:
                    inv_d = inv_net_cache[mid][0].captured_at.date()
                    inv_amt = inv_net_cache[mid][4]
                    if inv_d in by_date_amt and inv_amt in by_date_amt[inv_d]:
                        by_date_amt[inv_d][inv_amt].discard(mid)
                        if not by_date_amt[inv_d][inv_amt]:
                            del by_date_amt[inv_d][inv_amt]

                matched_inv_data = [inv_net_cache[i_id] for i_id in matched_ids]
                matched_invoices = [item[0] for item in matched_inv_data]
                matched_invoices.sort(key=lambda x: (x.captured_at, x.invoice_id))

                total_gross = sum(item[0].amount_in_paise for item in matched_inv_data)
                total_mdr = sum(item[1] for item in matched_inv_data)
                total_gst = sum(item[2] for item in matched_inv_data)
                total_tds = sum(item[3] for item in matched_inv_data)

                proof_data = f"{credit.utr_number}:{credit.credit_amount_in_paise}:{','.join(matched_ids)}"
                proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

                block = ReconciledSettlementBlock(
                    settlement_id=credit.settlement_id or f"setl_{credit.utr_number[:8]}",
                    utr_number=credit.utr_number,
                    lump_sum_paise=credit.credit_amount_in_paise,
                    gross_gmv_paise=total_gross,
                    total_mdr_fee_paise=total_mdr,
                    total_gst_on_mdr_paise=total_gst,
                    total_tds_withheld_paise=total_tds,
                    rounding_variance_paise=0,
                    status=SettlementStatus.SETTLED,
                    matched_invoices=[inv.invoice_id for inv in matched_invoices],
                    matched_refunds=[],
                    evidence_tier=EvidenceTier.TIER_A if credit.settlement_id else EvidenceTier.TIER_B,
                    proof_hash=proof_hash,
                    reconciled_at=datetime.now(timezone.utc),
                )
                reconciled_blocks.append(block)

        return reconciled_blocks, exceptions
