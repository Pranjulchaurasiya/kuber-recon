# Official Track 04 Benchmark Results (Deterministic Frozen Suite)

Generated: `2026-09-03T21:22:46.022654+00:00`  
Git Commit: `dbbe5ab1e66fb1dbbbe5ed7f0f9b14d819351843`  
Mathematical Policy: **Exact Paise Arithmetic (Zero Floats), Dual Accounting Balance Sheet**

| Metric | Clean Batch (100) | Messy Batch (250) | Adversarial Batch (500) |
| :--- | :---: | :---: | :---: |
| **Dataset Seed** | `1001` | `2002` | `3003` |
| **Records Ingested** | **125** | **239** | **460** |
| **Bank Credits** | 21 | 35 | 74 |
| **Exact Matches** | 20 | 24 | 63 |
| **Auto-Resolved Amount** | ₹266,675.17 | ₹394,139.45 | ₹939,877.89 |
| **Ambiguous Collisions Refused** | 1 | 1 | 1 |
| **Inconclusive Quarantined (N>24)** | 0 | 0 | 1 |
| **Tier B Heuristic Holds** | 0 | 0 | 4 |
| **Tier C Malformed Exceptions** | 0 | 10 | 6 |
| **Unmatched Credits** | 0 | 0 | 0 |
| **Exception Amount** | ₹1,485.00 | ₹177,573.46 | ₹18,985.00 |
| **Unexplained Delta** | **0 paise** | **0 paise** | **0 paise** |
| **Observed False Matches** | **0** | **0** | **0** |
| **Precision** | **100.0%** | **100.0%** | **100.0%** |
| **Auto-Resolution Rate** | 95.2% | 68.6% | 85.1% |
| **p50 Latency** | 4.94 ms | 7.02 ms | 38.84 ms |
| **p95 Latency** | 24.15 ms | 8.24 ms | 40.18 ms |
| **Throughput (rec/s)** | 11408.5 rec/s | 33062.0 rec/s | 12247.3 rec/s |

### Winning Invariant Proof:
1. **Zero Unexplained Delta:** $\text{Bank Credits Total} = \text{Auto-Resolved Total} + \text{Exception Queue Total}$. Every single paisa is accounted for.
2. **Anti-Greedy Ambiguity Refusal:** Multi-solution subset sums ($|S| > 1$) are refused 100% of the time.
3. **Graceful Combinatorial Degradation:** Over-dense clusters ($N > 24$) are quarantined to the manual review queue without guessing.
