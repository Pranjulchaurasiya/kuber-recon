# KuberRecon Winning Benchmark & Final Goal Specification

> **Benchmark North Star**: Prove one complete finance-ops control loop over a non-cherry-picked batch, with exact accounting, measured accuracy, visible exceptions, and safe action boundaries.
> **Track Reference**: [Razorpay Buildathon Track 04](https://razorpay.com/buildathon/) — 50+ record synthetic batch, measured match rate, unresolved exceptions, throughput, and honest accuracy (not one impressive transaction).

---

## 1. Target System Design

```text
Bank statements / Razorpay events / invoices
  │
  ▼
Ingestion + normalization (schema validation, paise conversion, narration parser, source provenance)
  │
  ▼
Evidence classification and matching
  Tier A candidate → provider-record verification
  Tier B heuristic → hold/manual review
  Tier C malformed → exception/manual review
  │
  ▼
Deterministic reconciliation kernel
  exact paise arithmetic + bounded solver
  exact / ambiguous / inconclusive / unmatched
  │
  ┌─────────────────────────────────┴─────────────────────────────────┐
  ▼                                                                   ▼
Reconciled settlement                                           Exception queue
  immutable audit record                                          reason + evidence + owner
  │                                                                   │
  ▼                                                                   ▼
Controlled action                                               Read-only CFO explanation
  release / hold only after policy checks                         no LLM control authority
  │
  ▼
Provider confirmation + webhook finality
  idempotency + out-of-order event handling
```

### The Key Invariant:
**No client input, narration string, LLM output, heuristic, or UI state may independently release money.**
Only a server-side contract, a verified provider event/record, exact paise checks, authorization, and CAS state transition together can do that.

---

## 2. Functional Scope to Demonstrate

Freeze the product around these six functions:

1. **Ingest**:
   - Accept invoices, bank credits and Razorpay settlement/transfer events.
   - Validate schema, tenant ownership, source provenance and paise-exact amounts.
2. **Normalize**:
   - Extract UTR/settlement IDs, bank profile, dates and rail information.
   - Unknown narrations must not be guessed.
3. **Reconcile**:
   - For every bank credit, produce exactly one outcome:
     - `EXACT_MATCH`
     - `AMBIGUOUS_COLLISION`
     - `INCONCLUSIVE_TRUNCATED`
     - `TIER_B_HOLD`
     - `TIER_C_EXCEPTION`
     - `UNMATCHED`
4. **Account**:
   - Every paise must be in one of two buckets:
     $$\text{bank credit total} = \text{reconciled settlement total} + \text{explicit exception total} + \text{approved adjustment total}$$
   - "Zero unexplained delta" is valid only if exceptions remain visible as a separate amount.
5. **Control**:
   - Release only after server-side authorization, cryptographic intent, provider-record verification and state-machine validation. Otherwise hold and route to review.
6. **Explain**:
   - The CFO copilot may explain evidence, tax calculation, hold reason and cash position.
   - It must remain read-only; no LLM may mutate ledger or payment state.

---

## 3. The Benchmark Suite: Deterministic Datasets

Use three deterministic datasets committed to the repository with fixed seeds:

| Dataset | Minimum Size | What it Proves |
| :--- | :---: | :--- |
| **Clean batch** | 100 records | Straight reconciliation and throughput |
| **Messy batch** | 250 records | Narration variation, missing fields, date variance and partial evidence |
| **Adversarial batch** | 500–1,000 records | Duplicate events, ambiguous subsets, oversized clusters, cross-tenant attempts and out-of-order webhooks |

### Mandatory Benchmark Output (JSON & Human-Readable Table):
- `records_ingested`
- `bank_credits`
- `exact_matches`
- `auto_resolved_amount_paise`
- `ambiguous_refused`
- `inconclusive_quarantined`
- `tier_b_holds`
- `tier_c_exceptions`
- `unmatched_credits`
- `exception_amount_paise`
- `unexplained_delta_paise`
- `observed_false_matches`
- `precision`
- `auto_resolution_rate`
- `p50_latency_ms`
- `p95_latency_ms`
- `throughput_records_per_second`
- `dataset_seed`
- `git_commit`

---

## 4. Winning-Level Acceptance Criteria

| Area | Bare Pass | Strong Finalist Target |
| :--- | :--- | :--- |
| **Batch proof** | 50+ records | 500+ adversarial records plus 100-record demo |
| **Accuracy** | Match rate reported | 0 observed false auto-matches on named corpus |
| **Exceptions** | A list exists | Every unresolved amount has a reason, owner and paise total |
| **Accounting** | Numbers look plausible | `unexplained_delta_paise = 0`, with exceptions separately shown |
| **Ambiguity** | Basic error | Refuse all multi-solution matches |
| **Complexity** | Works on happy path | $N > 24$ becomes `INCONCLUSIVE_TRUNCATED`, never a partial guess |
| **Tenant safety** | Headers exist | Cross-tenant read, mutate, sweep and release tests all fail closed |
| **Webhooks** | HMAC check | HMAC, idempotency, out-of-order handling, safe retry/DLQ |
| **Provider evidence** | Mock record | Server-side persisted provider record; no request-body provider data |
| **Demo** | Dashboard | One 5-minute reproducible walkthrough with a failure case |
| **Claims** | "0 FMR" | "0 observed false matches on this named synthetic corpus" |
| **Test evidence** | Test count | Clean checkout command, exact result, benchmark artifacts committed |

---

## 5. Performance Targets

- **100-record batch**: p95 under 1 second
- **500-record batch**: p95 under 3 seconds
- **1,000-record batch**: p95 under 5 seconds
- **Exact arithmetic**: 0 paise unexplained delta
- **False auto-matches**: 0 observed on the committed adversarial corpus
- **Every ambiguity/overflow**: 100% refused or quarantined
- **Duplicate webhook**: exactly once
- **CAS release race**: exactly one winner
- **Cross-tenant access**: 0 successful attacks in the defined test matrix

---

## 6. Security Benchmark Matrix (14 Mandatory Checks)

1. [x] Missing auth rejected
2. [x] Forged API key rejected
3. [x] Cross-tenant contract read rejected
4. [x] Cross-tenant release rejected
5. [x] Cross-tenant capital/sweep rejected
6. [x] Forged webhook rejected
7. [x] Duplicate webhook idempotent
8. [x] Out-of-order webhook cannot regress state
9. [x] Client-supplied provider record rejected
10. [x] Zero provider match refuses release
11. [x] Multiple provider matches refuse release
12. [x] Tier B/Tier C narration refuses auto-release
13. [x] Invalid/missing narration date refuses auto-release
14. [x] CAS race produces exactly one release transition

---

## 7. What Judges Should See in Five Minutes

1. **Problem (20 seconds)**: *"Finance teams lose time and money matching settlements manually; guessing creates false matches."*
2. **100-record batch (60 seconds)**: Run reconciliation. Show exact matches, total value, exceptions and zero unexplained delta.
3. **Ambiguity refusal (45 seconds)**: Show two valid subsets. KuberRecon refuses rather than choosing.
4. **Narration spoof attempt (45 seconds)**: Submit forged/malformed narration or client provider record. Show rejection and unchanged hold.
5. **Controlled release (45 seconds)**: Show server-side provider-record join, authorization, cryptographic intent and state transition.
6. **Evidence (45 seconds)**: Show benchmark JSON, test command, fixed seed and exception ledger.
7. **Honest boundary (20 seconds)**: *"Razorpay rails, KMS and distributed deployment are sandbox-shaped here; the deterministic control kernel is real."*

---

## 8. Submission Stop Condition

Stop adding features when all are true:
- [ ] One 100-record demo works every time.
- [ ] One 500+ adversarial benchmark is committed and reproducible.
- [ ] No P0/P1 security finding remains.
- [ ] Provider evidence is genuinely server-side.
- [ ] Exceptions are visible and monetarily accounted for.
- [ ] Test suite, benchmark, build and Judge Mode pass from a clean checkout.
- [ ] README has no unqualified "guarantee," "production-ready," "live settlement," or global FMR claim.
- [ ] Demo video follows the exact scenario above.
