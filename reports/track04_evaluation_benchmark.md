# Track 04 Project Evaluation Benchmark Results

Generated: `2026-09-03T21:41:13.527247+00:00`  
Git Commit: `156b0cc4404989e0fab65e951efa8d073b4e5734`  
Mathematical Policy: **Exact Base-10 Integer Paise Arithmetic (Zero Floats), Dual Accounting Balance Sheet**

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
| **p50 Latency** | 5.11 ms | 8.34 ms | 36.46 ms |
| **p95 Latency** | 39.87 ms | 9.58 ms | 39.79 ms |
| **Throughput (rec/s)** | 7503.6 rec/s | 29020.7 rec/s | 12410.4 rec/s |

### Invariant Proofs (Synthetic Corpus Evaluation):
1. **0 Unexplained Paise:** $\text{Bank Credits Total} = \text{Auto-Resolved Total} + \text{Exception Queue Total}$ (0 unexplained paise within the corpus accounting model, including explicitly classified exceptions).
2. **0 Observed False Auto-Matches:** Exact matching observed 0 false matches across tested synthetic fixtures.
3. **Ambiguity Refusal:** Multi-solution subset sums ($|S| > 1$) are refused 100% of the time.
4. **Combinatorial Degradation:** Over-dense clusters ($N > 24$) are quarantined to the review queue without guessing.
