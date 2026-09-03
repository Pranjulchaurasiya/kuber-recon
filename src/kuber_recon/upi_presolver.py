"""High-Frequency UPI Identical-Amount Multi-Set Pre-Solver.

Solves bounded integer knapsack problems for D2C merchants with hundreds or thousands of
identical transaction amounts (e.g., Rs 499, Rs 999) without combinatorial explosion
or cluster size truncation.

Paise-Exact Rule: Pure integer arithmetic; zero IEEE 754 float operations.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from kuber_recon.types import InvoiceRecord, MatchResultStatus, SolverResult


@dataclass(frozen=True)
class PriceClass:
    """Represents an aggregated pool of invoices sharing the exact same amount."""
    amount_paise: int
    invoices: Tuple[InvoiceRecord, ...]
    
    @property
    def count(self) -> int:
        return len(self.invoices)
    
    @property
    def total_paise(self) -> int:
        return self.amount_paise * self.count


class UPIIdenticalAmountPreSolver:
    """
    Bounded multi-set pre-solver for high-frequency identical amount transactions.
    
    Transforms O(2^N) combinatorial subsets of identical amounts into bounded integer
    knapsack combinations O(Products of Counts), enabling thousands of identical UPI
    transactions to reconcile in sub-millisecond time.
    """

    def __init__(self, max_solutions: int = 5):
        self.max_solutions = max_solutions

    def group_invoices(self, invoices: Sequence[InvoiceRecord]) -> List[PriceClass]:
        """Group invoices by exact amount_paise sorted deterministically."""
        groups: Dict[int, List[InvoiceRecord]] = defaultdict(list)
        for inv in invoices:
            groups[inv.amount_in_paise].append(inv)
            
        classes: List[PriceClass] = []
        for amt in sorted(groups.keys(), reverse=True):
            # Sort individual invoices deterministically by invoice_id
            sorted_invs = tuple(sorted(groups[amt], key=lambda x: x.invoice_id))
            classes.append(PriceClass(amount_paise=amt, invoices=sorted_invs))
        return classes

    def solve_exact(
        self,
        target_paise: int,
        invoices: Sequence[InvoiceRecord],
    ) -> SolverResult:
        """
        Attempts to solve the exact multi-set cover for target_paise.
        
        Returns:
            SolverResult with status:
            - EXACT_MATCH: Exactly one unique allocation of invoices matches target_paise.
            - AMBIGUOUS_COLLISION: Multiple distinct combinations sum to target_paise.
            - NO_MATCH: No combination sums to target_paise.
        """
        if not invoices or target_paise <= 0:
            return SolverResult(MatchResultStatus.NO_MATCH, [])

        classes = self.group_invoices(invoices)
        
        # Fast prune: if single price class and perfectly divisible
        if len(classes) == 1:
            pc = classes[0]
            if target_paise % pc.amount_paise == 0:
                needed = target_paise // pc.amount_paise
                if 0 < needed <= pc.count:
                    matched_ids = [inv.invoice_id for inv in pc.invoices[:needed]]
                    return SolverResult(MatchResultStatus.EXACT_MATCH, [matched_ids], nodes_explored=1)
                else:
                    return SolverResult(MatchResultStatus.NO_MATCH, [], nodes_explored=1)
            else:
                return SolverResult(MatchResultStatus.NO_MATCH, [], nodes_explored=1)

        # Multi-class bounded knapsack search
        solutions: List[List[str]] = []
        nodes_explored = 0

        def search(class_idx: int, rem_target: int, current_selection: List[Tuple[PriceClass, int]]):
            nonlocal nodes_explored
            nodes_explored += 1
            
            if rem_target == 0:
                # Found valid configuration
                selected_ids: List[str] = []
                for pc, count in current_selection:
                    for inv in pc.invoices[:count]:
                        selected_ids.append(inv.invoice_id)
                solutions.append(selected_ids)
                return
                
            if class_idx >= len(classes) or rem_target < 0:
                return
                
            pc = classes[class_idx]
            max_take = min(pc.count, rem_target // pc.amount_paise)
            
            # Prune if remaining maximum capacity cannot reach rem_target
            max_remaining_capacity = sum(
                c.amount_paise * c.count for c in classes[class_idx:]
            )
            if max_remaining_capacity < rem_target:
                return

            for take in range(max_take, -1, -1):
                if len(solutions) >= self.max_solutions:
                    break
                current_selection.append((pc, take))
                search(class_idx + 1, rem_target - (take * pc.amount_paise), current_selection)
                current_selection.pop()

        search(0, target_paise, [])

        if not solutions:
            return SolverResult(MatchResultStatus.NO_MATCH, [], nodes_explored=nodes_explored)
        elif len(solutions) == 1:
            return SolverResult(MatchResultStatus.EXACT_MATCH, solutions, nodes_explored=nodes_explored)
        else:
            return SolverResult(MatchResultStatus.AMBIGUOUS_COLLISION, solutions[:self.max_solutions], nodes_explored=nodes_explored)
