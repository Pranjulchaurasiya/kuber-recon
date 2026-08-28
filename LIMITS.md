# 🚧 System Boundaries, Edge Cases & Mathematical Limits

> **Engineering Failure Vectors & Boundary Transparency**  
> *Track 04: AI Finance Controller · Razorpay AI Buildathon 2026*

---

## 🔍 Explicit System Boundaries & Non-Negotiables

| Dimension | Boundary / Invariant | Hard Limit / Enforcement Behavior |
|---|---|---|
| **Currency Representation** | Pure Base-10 Integer Paise | `.semgrep/math_guard.yaml` AST rule fails builds on `float()`. |
| **Ambiguous Combinations** | Donald Knuth Exact-Cover | Emits `AmbiguousMatchError` when $|\text{Covers}| > 1$. Never guesses. |
| **Single-Transaction AI Cap** | Self-Healing Payout Limit | Hard non-AI cap: ₹200.00 max auto-adjustment; ₹1,000.00/day. |
| **Payee Account Authorization** | Beneficiary Whitelist | Payout drafts ONLY target pre-registered KYC bank accounts. |
| **Webhook Delivery Race** | Idempotent Ingestion | Atomic deduplication on `sha256(order_id:payment_id)`. |
| **Partial Customer Returns** | Proportionate Escrow Shrink | Escrow tranche shrinks proportionately in exact base-10 paise. |
| **Statutory Tax Slabs** | HSN/SAC Dynamic Slabs | Supports 0%, 5%, 12%, 18%, 28% GST brackets dynamically. |
| **Micro-Merchant Exemption** | CBDT Section 194-O Bypass | Verified individuals $<₹5\text{ Lakhs}$ with PAN marked 0% TDS. |

---

## 🔒 Security & Finality Constraints

### 1. Hardware Security Module (HSM) Custody
- **Current Implementation:** Backend simulates hardware-backed HSM responses by constructing in-memory Ed25519 key pairs.
- **Production Requirement:** Requires integration with AWS KMS, Google Cloud KMS, or a dedicated Hardware Security Module to securely sign invariants.

### 2. Asynchronous Razorpay Test Mode Webhooks
- **Current Implementation:** The `/api/webhook/razorpay` endpoint serves as the single source of truth for finalizing `RELEASING` to `RELEASED`.
- **Production Requirement:** Webhooks in production must strictly validate `X-Razorpay-Signature` HMACs.

### 3. Idempotency TTL and Manual Refund Reconciliation
- **Current Implementation:** A background sweep identifies expired locks and transitions them to `EXPIRED_HOLD`.
- **Production Requirement:** Auto-refunds on timeouts are risky in B2B. `EXPIRED_HOLD` must queue into a manual dispute resolution dashboard for a human controller or arbitration script to process.

---

## ⚡ Mathematical & Combinatorial Thresholds

1. **Donald Knuth Algorithm X Dense Tail ($N > 36$):**
   * When $N \le 36$ candidate invoices exist in a $T \pm 2$ day window, the Knuth DLX solver runs in $<15\text{ms}$.
   * For dense tails ($N > 36$), Horowitz-Sahni meet-in-the-middle hash partitioning reduces search space to $O(2^{N/2})$.
   * If candidate combinations exceed $2^{24}$ states, the engine emits `CombinatorialThresholdExceeded` and flags the batch for tiered human review rather than timing out.

2. **GSTR-2B 14th-of-Month Auto-Population Lag:**
   * Under CGST Rule 60(7), GSTR-2B is auto-generated on the 14th of the succeeding month.
   * `KuberSovereign` holds the 18% GST tranche on hold (`on_hold: true`) throughout this window, guaranteeing that merchant working capital is protected until government confirmation.

3. **Floating-Point Drift Elimination:**
   * Standard IEEE-754 arithmetic leaks up to 14 paise per ₹1,00,000 across multi-tier aggregations.
   * Dual-accumulator rounding tracks line-item vs. aggregate GST, balancing sub-rupee rounding variances into a Martin Fowler double-entry `RoundingVarianceAccount`.
