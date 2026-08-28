# 🚧 System Boundaries, Edge Cases & Verification Limits

> **Engineering Failure Vectors, Trade-offs & Boundary Transparency**
> *Track 01: AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026*

---

## 🔍 1. Explicit System Boundaries & Trade-Offs

| Dimension | Mechanism / Invariant | Hard Limit / Enforcement Behavior |
|---|---|---|
| **Currency Arithmetic** | Pure Base-10 Integer (Paise) | Python `Decimal` and integer paise. Prohibits IEEE-754 floats in financial paths. |
| **Ambiguous Combinations** | Exact-Cover Subset Matcher | Emits `AmbiguousMatchError` when $>1$ valid subset covers a credit. Refuses to guess. |
| **Delivery Verification** | Deterministic Checksums | Validates 15-char GSTIN check-digit (Mod-36 custom weights) and 500-record bounds. |
| **Pre-Settlement Gating** | Razorpay Route `on_hold: true` | Payout funds remain in nodal hold until delivery assertions and maker-checker pass. |
| **Webhook Delivery Race** | Idempotent Ingestion | Atomic SQLite CAS transition on single authoritative `transfer.processed` webhook. |
| **Partial Returns** | Proportionate Escrow Shrinkage | Escrow tranche shrinks proportionately in exact base-10 paise on partial refunds. |
| **Tax Slabs** | Statutory Tax Engine | Supports 0%, 5%, 12%, 18%, 28% GST slabs and Section 194-O TDS withholding. |

---

## 🔒 2. Security Posture & Key Custody Model

### 1. Prototype Browser Signer vs. Production Key Custody
* **Prototype Implementation:** The frontend sandbox implements client-side Ed25519 signing using Web Crypto API to demonstrate the protocol flow (canonical manifest serialization, asymmetric signature generation, and backend public key verification).
* **Known Boundary:** In a frontend prototype, client-side derived private keys are not a substitute for hardware key custody.
* **Production Architecture:**
  1. Private keys must never reside in client-side JavaScript bundles.
  2. The CFO / Arbiter signing key is stored in an **AWS KMS Asymmetric Key (ECC_NIST_P256 / Ed25519)** or **FIPS 140-2 Level 3 HSM**.
  3. The browser uses **WebAuthn / FIDO2 hardware tokens** (Touch ID, YubiKey) or authenticated OAuth2 bearer sessions to authorize the backend KMS proxy to sign the release instruction.

### 2. State Store Architecture: Prototype vs Production
* **Prototype State Store:** **SQLite with WAL Mode** (`PRAGMA busy_timeout = 5000`) and schema triggers for atomic CAS transitions and append-only audit logging. This provides zero-dependency local reproducibility for judges.
* **Production State Store:** Core ledger state requires a distributed transactional database with serializable isolation (e.g., **PostgreSQL with PgBouncer** or **Google Cloud Spanner**).

---

## ⚡ 3. Algorithmic Bounds & Performance Scope

1. **Exact-Cover Matching Bounds:**
   * For candidate invoice subsets $N \le 24$, Horowitz-Sahni meet-in-the-middle hash partitioning solves in $<10\text{ms}$.
   * For larger sparse matrices ($N > 24$), the Dancing Links (DLX) exact-cover solver runs with a complexity cap (`max_nodes = 10,000`, `timeout = 500ms`) to protect against algorithmic DoS.
   * If combinations exceed $2^{24}$ states, the engine emits `CombinatorialThresholdExceeded` and routes to human exception review rather than stalling.

2. **Empirical Latency Scope:**
   * Reported solver execution times (1.82ms – 42.80ms) represent **in-memory algorithm runtimes** on local hardware.
   * End-to-end settlement lifecycle latency is governed by network transit, Razorpay Route API round-trips, and inbound webhook delivery times.

3. **False Match Rate (FMR) Scope:**
   * The measured metric $FMR = 0.000$ reflects behavior on our **adversarial test corpus of planted ambiguous subset traps**, where the algorithm consistently raised `AmbiguousMatchError` rather than making probabilistic guesses.

---

## 🏢 4. Strategic Value for Razorpay

### What Problem Does This Solve That Razorpay Doesn't Already Cover?
* **Post-Settlement Disputes vs. Pre-Settlement Gating:**
  * Razorpay's standard dispute/refund tooling operates **after** funds have settled to the seller's account. Recovering funds post-settlement is slow, operationally expensive, and creates merchant default risk.
  * APEX provides **pre-settlement verification**: by utilizing Razorpay Route's native `on_hold: true` flag, settlement funds never leave the nodal account until deterministic delivery proof is validated.
* **Product Form Factor:**
  * **Razorpay Assurance Hooks / Route Conditional Settlement SDK**: An extension to Route where platform merchants can configure automated verification rules (manifest checksums, schema assertions, dual-party signatures) before triggering `PATCH /v1/transfers/{id} on_hold: false`.
