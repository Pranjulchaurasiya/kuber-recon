# 🚧 System Boundaries, Edge Cases & Verification Limits

> **Engineering Failure Vectors, Trade-offs & Boundary Transparency**
> *Track 01: AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026*

---

## 🔍 1. Explicit System Boundaries & Trade-Offs

| Dimension | Mechanism / Invariant | Hard Limit / Enforcement Behavior |
|---|---|---|
| **Currency Arithmetic** | Pure Base-10 Integer (Paise) | Python `Decimal` and integer paise. Prohibits IEEE-754 floats in financial paths. |
| **Ambiguous Combinations** | Bounded Subset-Sum Matcher | Emits `AmbiguousMatchError` when $>1$ valid subset covers a credit. Refuses to guess. |
| **Delivery Verification** | Deterministic Checksums | Validates 15-char GSTIN check-digit (Mod-36 custom weights) and 500-record bounds. |
| **Pre-Settlement Gating** | Razorpay Route `on_hold: true` | Payout funds remain in nodal hold until delivery assertions and maker-checker pass. |
| **Webhook Delivery Race** | Idempotent Ingestion | Atomic SQLite CAS transition on single authoritative `transfer.processed` webhook. |
| **Partial Returns** | Proportionate Escrow Shrinkage | Escrow tranche shrinks proportionately in exact base-10 paise on partial refunds. |
| **Tax Slabs** | Statutory Tax Engine | Supports 0%, 5%, 12%, 18%, 28% GST slabs and Section 194-O TDS withholding. |

---

## 🔒 2. Security Posture & Key Custody Model

### 1. Prototype Browser Signer vs. Production Key Custody
* **Prototype Implementation:** The frontend sandbox implements client-side Ed25519 signing using the Web Crypto API to demonstrate the protocol flow (canonical manifest serialization, asymmetric signature generation, and backend public key verification).
* **Empirical Production Bundle Finding:** In the Next.js production build (`npm run build`), the CFO seed string `"kuber_cfo_autonomous_verifier_sec_key_v1"` is bundled directly into the static chunk [`frontend/.next/static/chunks/2yct_1fd1glis.js:1`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/frontend/.next/static/chunks/2yct_1fd1glis.js#L1). This confirms the known prototype boundary: client-side derived private keys are not a substitute for hardware key custody.
* **Production Architecture:**
  1. Private keys must never reside in client-side JavaScript bundles.
  2. The CFO / Arbiter signing key is stored in an **AWS KMS Asymmetric Key (ECC_NIST_P256 / Ed25519)** or **FIPS 140-2 Level 3 HSM**.
  3. The browser uses **WebAuthn / FIDO2 hardware tokens** (Touch ID, YubiKey) or authenticated OAuth2 bearer sessions to authorize the backend KMS proxy to sign the release instruction.

### 2. State Store Architecture: Prototype vs Production
* **Prototype State Store:** **SQLite with WAL Mode** (`PRAGMA busy_timeout = 5000`) and schema triggers for atomic CAS transitions and append-only audit logging. This provides zero-dependency local reproducibility for judges.
* **Production State Store:** Core ledger state requires a distributed transactional database with serializable isolation (e.g., **PostgreSQL with PgBouncer** or **Google Cloud Spanner**).

---

## ⚡ 3. Algorithmic Bounds & Performance Scope

1. **Subset-Sum Matching Bounds:**
   * For candidate invoice subsets $N \le 24$, iterative Horowitz-Sahni meet-in-the-middle hash partitioning solves in $<10\text{ms}$.
   * For dense candidate pools ($N > 24$), the candidate list is bounded to the top 24 items with strict complexity caps (`max_nodes = 10,000`, `timeout = 500ms`) to prevent combinatorial DoS.
   * If combinations cannot be uniquely resolved or multi-subset collisions occur, the engine emits `AmbiguousMatchError` (honest refusal) rather than making probabilistic guesses.

2. **Empirical Latency Scope:**
   * Reported solver execution times (4.12ms – 323.46ms across 100 to 10,000 records) represent **in-memory algorithm runtimes** on local hardware.
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

---

## 💰 5. APEX Capital: Working Capital Underwriting & Failure Recovery Bounds

### 1. Operational Heuristic Disclosures
* **25% Advance Cap Heuristic:** The maximum advance multiplier `DEFAULT_ADVANCE_RATE_HEURISTIC = Decimal("0.25")` against 30-Day Verified Delivered GMV is an operational heuristic. It ensures that at a 10%–15% daily nodal sweep rate, typical amortizations resolve in 4 to 6 weeks without impairing merchant day-to-day operating liquidity.
* **Bayesian Shrinkage Smoothing:** Small sample sizes ($N < 20$) are smoothed using a Bayesian prior ($N_0 = 50, p_0 = 0.98$), preventing single-transaction disputes from collapsing a new merchant's creditworthiness while letting mature transaction histories dominate.

### 2. Failure State Transitions & Regulatory Compliance
* **14-Day Stagnancy Queue:** If no nodal settlements occur for 14 consecutive days during an active facility, the facility transitions to `STAGNANT_RECOVERY`, halting automatic sweeps and escalating to the merchant risk remediation team.
* **30-Day FLDG Escalation:** If settlement remains frozen for 30 days, the facility transitions to `FLDG_REVIEW`.
* **RBI Digital Lending Guidelines Compliance:** In accordance with the **RBI Digital Lending Guidelines (Circular DOR.CRE.REC.66/21.07.001/2022-23, Sept 2022)** and the **June 2023 Default Loss Guarantee (DLG/FLDG) circular**, total first-loss default guarantee coverage between the platform (LSP) and regulated lending partner (RE) is hard-capped at **5% of the total outstanding portfolio**.

### 3. Concurrency Model: Process-Local RLock vs. Production Distributed Locking
* **Prototype Implementation:** `CapitalFacilityManager` synchronizes state mutations using Python reentrant locks (`threading.RLock`). This guarantees strict thread-safety, double-drawdown prevention, and zero over-recovery across concurrent threads within a single running server process.
* **Production Architecture:** In a horizontally scaled production deployment with multiple API worker nodes, state synchronization requires **distributed locking** (e.g., PostgreSQL row-level locks via `SELECT ... FOR UPDATE`, transactional Redis Redlock, or database-enforced atomic CAS constraints) to prevent cross-process race conditions.

### 4. Continuous Risk-Tier Pricing Interpolation
* **Transition Smoothing:** To eliminate pricing cliff-edges, terms are interpolated continuously across the $\text{SRI} \in [0.9300, 0.9700]$ transition band. Within this band, factor fees scale linearly from 6.0% (Tier B) down to 4.0% (Tier A), and daily sweep rates scale from 15.0% down to 12.0%.
* **Elimination of Discontinuities:** A 0.0002 SRI difference at the 0.9500 boundary results in a strictly bounded 0.179% fee delta (₹21.25 on ₹2.37L) and 2 bps sweep rate shift, preserving continuous cost progression across the full reliability spectrum.


### 5. Front-Load Default & 14-Day Silent Exposure Window
* **Exposure Lag:** If a merchant qualifies on trailing volume, draws the maximum advance, and immediately halts all transaction volume, the system maintains an active facility for **14 days** before the absence of settlement triggers automatic transition to `STAGNANT_RECOVERY` (and 30 days to `FLDG_REVIEW`).
* **Portfolio Loss Mitigation:** Individual defaults are absorbed by the merchant risk reserve up to the 5% portfolio FLDG cap under RBI Digital Lending Guidelines.

### 6. Razorpay API Gateway Connectivity & Route Verification Scope
* **Settlement Recon Read Scope:** The client adapter was verified to authenticate against `https://api.razorpay.com/v1/settlements/recon/combined` using Razorpay API credentials (`HTTP 200`).
* **Route Transfer Creation Contract:** The error response received when attempting direct balance transfers (`POST /v1/transfers`) was analyzed against Razorpay's official Route documentation: direct account transfers require an explicit account feature flag activated by Razorpay on the MID, plus onboarded linked accounts (`POST /v1/accounts`).
* **Zero-Key Sandbox Verification:** For local demonstration, testing, and unprovisioned accounts, all Route transfer creations and hold releases (`PATCH /v1/transfers/{id}`) execute against the documented Razorpay JSON contract using our deterministic zero-key simulation adapter.




