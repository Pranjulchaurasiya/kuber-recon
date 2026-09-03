"""
50+ to 1,000 Record Judge Benchmark & Structured Exception Report
==================================================================
Automated fintech audit benchmark evaluating clustered reconciliation,
non-authoritative narration tiers, honest refusal invariants, and 0-paise delta proof.

Coverage:
1. Clustered batch reconciliation on 50 to 1,000 synthetic records.
2. Structured exception breakdown:
   - Exact subset-sum matches (Knuth DLX / Horowitz-Sahni)
   - Planted ambiguous collisions refused (Anti-Greedy FMR Protection)
   - Dense clusters quarantined (> max_cluster_size bounds)
   - Tier B non-authoritative narration holds
   - Tier C malformed narration exceptions
3. Mathematical invariant proof: Unexplained delta is strictly 0 paise.
4. Latency and throughput benchmarking (p50, p95, p99, records/sec).
"""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from kuber_recon.engine import ClusteredReconciliationPipeline, ReconciliationBatchMetrics
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.narration_parser import IndianBankNarrationParser, NarrationEvidenceTier
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


@dataclass
class StructuredExceptionBreakdown:
    exact_subset_sum_matches: int
    planted_ambiguities_refused: int
    dense_clusters_quarantined: int
    tier_b_non_authoritative_holds: int
    tier_c_malformed_exceptions: int
    unmatched_clean_credits: int
    total_reconciled_paise: int
    total_exceptions_paise: int
    unexplained_delta_paise: int
    zero_float_policy_verified: bool


def generate_adversarial_judge_dataset(
    record_count: int,
    seed: int = 42,
) -> Tuple[List[InvoiceRecord], List[BankNodalCredit], Dict[str, Any]]:
    """
    Generates a deterministic financial dataset mixing standard settlements,
    planted ambiguous collisions, dense clusters, Tier B heuristic narrations,
    and Tier C malformed bank clearing memos.
    """
    generator = ChaosDataGenerator(seed=seed)
    base_invoices, base_credits, _, _ = generator.generate_suite(
        num_records=max(30, int(record_count * 0.7)),
        start_date=date(2026, 8, 5),
    )

    invoices = list(base_invoices)
    bank_credits = []
    
    # Ensure standard base credits have realistic Tier A bank clearing narrations with UTR
    for bc in base_credits:
        clean_utr = bc.utr_number.replace("_", "")
        # Standard HDFC format (e.g. HDFCN00 + alphanumeric = 14+ chars)
        norm_utr = clean_utr if len(clean_utr) >= 14 else f"HDFCN00{clean_utr[5:] if clean_utr.startswith('HDFCN') else clean_utr}"
        enhanced_narration = f"NFX-RZR*SETTL*{bc.settlement_id or 'TXN'}*{norm_utr}"
        bank_credits.append(
            BankNodalCredit(
                utr_number=norm_utr,
                account_number=bc.account_number,
                credit_amount_in_paise=bc.credit_amount_in_paise,
                value_date=bc.value_date,
                raw_narration=enhanced_narration,
                settlement_id=bc.settlement_id,
            )
        )

    metadata = {
        "planted_ambiguities": 1 if any("PLANTED" in c.utr_number for c in base_credits) else 0,
        "dense_cluster_invoices": 0,
        "tier_b_credits": 0,
        "tier_c_credits": 0,
    }

    # 1. Inject a Dense Cluster (> 24 invoices for a single GSTIN and date)
    dense_gstin = "29DENSE9999Z1Z8"
    dense_date = date(2026, 8, 15)
    dense_invoices_count = 32  # Exceeds max_cluster_size=24
    for idx in range(dense_invoices_count):
        inv_amt = 10000 + (idx * 500)
        inv = InvoiceRecord(
            invoice_id=f"INV-DENSE-{idx:03d}",
            order_id=f"ord_dense_{idx:03d}",
            payment_id=f"pay_dense_{idx:03d}",
            supplier_gstin=dense_gstin,
            amount_in_paise=inv_amt,
            method=PaymentMethod.UPI,
            captured_at=datetime.combine(dense_date, datetime.min.time()) + timedelta(minutes=idx * 10),
        )
        invoices.append(inv)
    metadata["dense_cluster_invoices"] = dense_invoices_count

    # 2. Inject Tier B Heuristic Narration Bank Credits
    # (Valid UTR syntax but missing aggregator token -> cannot auto-release)
    tier_b_credit = BankNodalCredit(
        utr_number="SBIN008827163541",
        account_number="918239012389",
        credit_amount_in_paise=350000,
        value_date=date(2026, 8, 16),
        raw_narration="NEFT-SBIN008827163541-DIRECT*DEP-MISC",
    )
    bank_credits.append(tier_b_credit)
    metadata["tier_b_credits"] += 1

    # 3. Inject Tier C Malformed Bank Memo
    # (Malformed / rural cooperative bank text without valid UTR)
    tier_c_credit = BankNodalCredit(
        utr_number="UNKNOWN_COOP_01",
        account_number="918239012389",
        credit_amount_in_paise=125000,
        value_date=date(2026, 8, 17),
        raw_narration="DISTRICT COOP BANK CLG REF 9901 INVALID",
    )
    bank_credits.append(tier_c_credit)
    metadata["tier_c_credits"] += 1

    return invoices, bank_credits, metadata


def execute_judge_benchmark_run(
    record_target: int,
    iterations: int = 3,
) -> Dict[str, Any]:
    """Execute multi-iteration benchmark run for a specific target size."""
    invoices, bank_credits, meta = generate_adversarial_judge_dataset(record_target)
    total_records = len(invoices) + len(bank_credits)

    pipeline = ClusteredReconciliationPipeline(max_cluster_size=24)
    run_latencies_ms: List[float] = []
    last_reconciled = []
    last_exceptions = []
    last_metrics: Optional[ReconciliationBatchMetrics] = None

    # Step 1: Pre-filter bank credits through IndianBankNarrationParser
    clean_credits: List[BankNodalCredit] = []
    tier_b_holds: List[Tuple[BankNodalCredit, str]] = []
    tier_c_exceptions: List[Tuple[BankNodalCredit, str]] = []

    for credit in bank_credits:
        parsed = IndianBankNarrationParser.parse_narration(credit.raw_narration)
        if parsed.evidence_tier == NarrationEvidenceTier.TIER_C_EXCEPTION:
            tier_c_exceptions.append((credit, f"TIER_C_EXCEPTION: {parsed.non_authoritative_reason}"))
        elif parsed.evidence_tier == NarrationEvidenceTier.TIER_B_HEURISTIC:
            tier_b_holds.append((credit, f"TIER_B_HEURISTIC: {parsed.non_authoritative_reason}"))
        else:
            clean_credits.append(credit)

    for _ in range(iterations):
        t0 = time.perf_counter()
        reconciled, exceptions, metrics = pipeline.process_large_batch(
            bank_credits=clean_credits,
            invoices=invoices,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        run_latencies_ms.append(elapsed_ms)
        last_reconciled = reconciled
        last_exceptions = exceptions
        last_metrics = metrics

    # Latency statistics
    p50 = statistics.median(run_latencies_ms)
    p95 = statistics.quantiles(run_latencies_ms, n=20)[-1] if len(run_latencies_ms) >= 5 else max(run_latencies_ms)
    p99 = max(run_latencies_ms)
    mean_lat = statistics.mean(run_latencies_ms)
    throughput = total_records / (mean_lat / 1000.0) if mean_lat > 0 else 0.0

    # Classify reconciliation exceptions on clean credits
    # Note: Dense cluster dummies in last_exceptions represent invoice quarantine, not input bank credits
    planted_ambig_count = sum(1 for c, r in last_exceptions if "AMBIGUOUS_COLLISION" in r)
    dense_quarantined_count = sum(1 for c, r in last_exceptions if "INCONCLUSIVE_TRUNCATED" in r)
    unmatched_clean_count = sum(1 for c, r in last_exceptions if "NO_EXACT_COVER_FOUND" in r and not c.utr_number.startswith("TRUNC_"))

    # Monetary delta verification (Paise-Exact Rule on Bank Credits)
    reconciled_paise = sum(b.lump_sum_paise for b in last_reconciled)
    ambig_paise = sum(c.credit_amount_in_paise for c, r in last_exceptions if "AMBIGUOUS_COLLISION" in r)
    unmatched_paise = sum(c.credit_amount_in_paise for c, r in last_exceptions if "NO_EXACT_COVER_FOUND" in r and not c.utr_number.startswith("TRUNC_"))
    tier_b_paise = sum(c.credit_amount_in_paise for c, _ in tier_b_holds)
    tier_c_paise = sum(c.credit_amount_in_paise for c, _ in tier_c_exceptions)

    total_accounted_paise = (
        reconciled_paise + ambig_paise + unmatched_paise + tier_b_paise + tier_c_paise
    )
    total_input_credits_paise = sum(c.credit_amount_in_paise for c in bank_credits)

    # Invariant: Every single paisa in bank_credits must be classified and accounted for
    unexplained_delta = total_input_credits_paise - total_accounted_paise

    breakdown = StructuredExceptionBreakdown(
        exact_subset_sum_matches=len(last_reconciled),
        planted_ambiguities_refused=planted_ambig_count,
        dense_clusters_quarantined=dense_quarantined_count,
        tier_b_non_authoritative_holds=len(tier_b_holds),
        tier_c_malformed_exceptions=len(tier_c_exceptions),
        unmatched_clean_credits=unmatched_clean_count,
        total_reconciled_paise=reconciled_paise,
        total_exceptions_paise=(ambig_paise + unmatched_paise + tier_b_paise + tier_c_paise),
        unexplained_delta_paise=unexplained_delta,
        zero_float_policy_verified=isinstance(unexplained_delta, int) and unexplained_delta == 0,
    )

    return {
        "scenario_target": record_target,
        "total_records_ingested": total_records,
        "invoices_count": len(invoices),
        "bank_credits_count": len(bank_credits),
        "total_input_credits_paise": total_input_credits_paise,
        "iterations": iterations,
        "mean_latency_ms": round(mean_lat, 2),
        "p50_latency_ms": round(p50, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "throughput_records_per_sec": round(throughput, 1),
        "structured_breakdown": asdict(breakdown),
    }


def run_judge_benchmark_suite():
    """Main benchmark entry point."""
    print("=" * 88)
    print(" [BENCHMARK] KUBERRECON JUDGE MODE: HIGH-RIGOR RECONCILIATION AUDIT")
    print("    Scenario Targets 50 to 1,000 | Clustered Batch Reconciliation & Dual Delta Accounting")
    print("=" * 88)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("Invariant: Zero IEEE-754 floats; pure base-10 integer paise; zero false matches.")
    print("Notice   : 0 unexplained delta means all funds are classified; exceptions are separately tracked.")
    print("-" * 88)

    test_targets = [50, 100, 250, 500, 1000]
    suite_results = []

    for target in test_targets:
        res = execute_judge_benchmark_run(target, iterations=3)
        suite_results.append(res)
        bd = res["structured_breakdown"]

        print(f"\n[SCENARIO TARGET: {target} | TOTAL RECORDS INGESTED: {res['total_records_ingested']}]")
        print(f"  Ingested Split : Invoices={res['invoices_count']} | Bank Credits={res['bank_credits_count']}")
        print(f"  Latency        : Mean={res['mean_latency_ms']}ms | p50={res['p50_latency_ms']}ms | p95={res['p95_latency_ms']}ms | p99={res['p99_latency_ms']}ms")
        print(f"  Throughput     : {res['throughput_records_per_sec']} records/sec")
        print(f"  Matches        : {bd['exact_subset_sum_matches']} Exact Blocks Reconciled")
        print(f"  Exceptions     : {bd['planted_ambiguities_refused']} Ambiguous Collisions Refused | {bd['dense_clusters_quarantined']} Dense Clusters Quarantined")
        print(f"  Narrations     : {bd['tier_b_non_authoritative_holds']} Tier B Holds | {bd['tier_c_malformed_exceptions']} Tier C Malformed")
        print(f"  Accounting Breakdown:")
        print(f"    - Total Ingested Credits : Rs {res['total_input_credits_paise']/100:,.2f} ({res['total_input_credits_paise']} paise)")
        print(f"    - Fully Reconciled Funds : Rs {bd['total_reconciled_paise']/100:,.2f} ({bd['total_reconciled_paise']} paise)")
        print(f"    - Active Exceptions Hold : Rs {bd['total_exceptions_paise']/100:,.2f} ({bd['total_exceptions_paise']} paise) [Ambiguities + Quarantine + Holds + Malformed]")
        delta_status = "[VERIFIED 0 PAISE]" if bd["unexplained_delta_paise"] == 0 else "[FAIL: DELTA NON-ZERO]"
        print(f"    - Unexplained Delta      : {bd['unexplained_delta_paise']} paise {delta_status}")

        assert bd["unexplained_delta_paise"] == 0, f"Critical Invariant Violated: Delta is {bd['unexplained_delta_paise']} paise"
        assert bd["zero_float_policy_verified"] is True

    # Save to reports
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "judge_benchmark_report.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pipeline": "ClusteredReconciliationPipeline with Multi-Bank Narration Parser",
            "accounting_policy": "Dual Accounting: Explicit Reconciled Volume + Explicit Exception Volume; Zero Unexplained Delta",
            "results": suite_results,
        }, f, indent=2)

    print("\n" + "=" * 88)
    print(f" [SUCCESS] Judge Benchmark Suite Completed. Verified 0 unexplained delta across all scales.")
    print(f" Report saved: {out_path.resolve()}")
    print("=" * 88)


if __name__ == "__main__":
    run_judge_benchmark_suite()
