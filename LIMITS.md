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

### 1. Hardware Security Module (HSM) Custody & Private Key Boundary
- **Current Demo Implementation:** The frontend sandbox imports a sample RFC 8410 PKCS#8 Ed25519 key derived from a demo seed (`kuber_cfo_autonomous_verifier_sec_key_v1`) to demonstrate client-side RFC 8032 Ed25519 asymmetric signing, canonical payload serialization, and public key pinning without requiring physical YubiKeys or cloud KMS setup during evaluation.
- **Threat Vector (Client-Side Key Extraction):** Any private key seed shipped in client-side JavaScript can be inspected and extracted by reverse-engineering the frontend bundle.
- **Production Architecture:** In live production deployments:
  1. Private keys **must never reside in or be derivable from client-side bundles**.
  2. The CFO / Arbiter signing key is isolated in an **AWS KMS Asymmetric Signing Key (ECC_NIST_P256 / Ed25519)** or **FIPS 140-2 Level 3 CloudHSM**.
  3. The browser uses **WebAuthn / FIDO2 hardware tokens** (Touch ID, YubiKey) or authenticated OAuth2/mTLS bearer tokens to send an authorized release instruction to the backend, which proxies the signing request to KMS.

### 2. Asynchronous Razorpay Test Mode Webhooks
- **Current Implementation:** The `/api/webhook/razorpay` endpoint serves as the single source of truth for finalizing `RELEASING` to `RELEASED`, verifying valid HMAC signatures against the webhook secret.
- **Production Requirement:** Webhooks in production must strictly validate `X-Razorpay-Signature` HMACs and reject unsigned payloads.

### 3. Idempotency TTL and Manual Refund Reconciliation
- **Current Implementation:** A background sweep identifies expired locks and transitions them to `EXPIRED_HOLD`.
- **Production Requirement:** Auto-refunds on timeouts are risky in B2B commerce. `EXPIRED_HOLD` must queue into a manual dispute resolution dashboard for a human controller or arbitration script to process.

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
