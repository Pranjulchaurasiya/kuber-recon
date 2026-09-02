# APEX Settlement Control & KuberRecon Threat Model

## 1. Executive Summary & Security Posture
KuberRecon / APEX is an autonomous merchant reconciliation and delivery-gated settlement control system designed for the Razorpay Buildthon.

The fundamental security thesis is:
> **Zero Unverified Settlement:** No financial balance is disbursed, released, or swept based on probabilistic guesses or unverified assertions. State advances only against deterministic, base-10 paise-exact settlement truth.

---

## 2. Protected Assets & Critical Invariants

| Asset | Invariant | Protection Mechanism |
| :--- | :--- | :--- |
| **Razorpay Route Escrow Balance** | Never released prior to verified delivery manifest. | `on_hold: true` locked via Route API; released only on valid Ed25519 signature verification. |
| **Merchant Working Capital Facility** | Never double-disbursed or double-swept; balance never drops below 0 paise. | SQLite CAS versioning (`version = version + 1 WHERE version = ?`) and unique idempotency keys. |
| **Reconciliation Integrity** | Exact base-10 paise matching without IEEE-754 floating-point drift. | Integer paise arithmetic throughout; Horowitz-Sahni subset-sum solver with bounded $N \le 24$. |
| **Multi-Tenant State Isolation** | Tenant B cannot inspect, mutate, sign, or sweep Tenant A contracts/facilities. | Strict API authentication (`X-Merchant-Id`, `X-API-Key`) and mandatory SQL `tenant_id = ?` scoping. |
| **Webhook Delivery Finality** | Authoritative state transition executes exactly once per event. | Constant-time HMAC-SHA256 verification, $\pm 300\text{s}$ timestamp freshness window, SQLite idempotency store. |
| **Audit Log Immutability** | Audit logs cannot be deleted or tampered with. | SQLite engine-level append-only triggers (`abort_audit_log_update`, `abort_audit_log_delete`). |

---

## 3. Threat Actors & Threat Scenarios

```
                          [ UNTRUSTED INTERNET / CLIENTS ]
                                        │
                         [ Threat 1: Missing/Forged Auth ]
                         [ Threat 2: Stale Webhook Replay ]
                         [ Threat 3: Forged HMAC Signature ]
                                        │
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │          FastAPI Invariant Gateway        │
                  │   - Constant-time API Key Comparison      │
                  │   - ±300s Webhook Freshness Gate          │
                  │   - Constant-time HMAC-SHA256 Validator   │
                  └─────────────────────┬─────────────────────┘
                                        │
                       [ Authenticated Tenant Scope ]
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌──────────────────────────┐                             ┌──────────────────────────┐
│   Tenant A Data Plane    │   [ Threat 4: IDOR / Leak ] │   Tenant B Data Plane    │
│  - Contracts / Holds     │ ◄─────────────────────────► │  - Contracts / Holds     │
│  - Capital Facilities    │                             │  - Capital Facilities    │
└────────────┬─────────────┘                             └────────────┬─────────────┘
             │                                                        │
             └──────────────────────────┬─────────────────────────────┘
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │    Durable SQLite Single-Authoritative    │
                  │   - Optimistic Concurrency Control (CAS)  │
                  │   - Unique Idempotency Keys (Deduplication)│
                  │   - Engine-level Append-Only Triggers     │
                  └───────────────────────────────────────────┘
```

### Threat Actor Profiles:
1. **Malicious / Compromised Merchant Tenant:** Attempts to inspect other tenants' contracts (IDOR), sweep other merchants' facilities, or trigger unauthorized release holds.
2. **Rogue / Corrupted Seller Agent:** Delivers fraudulent GSTINs, malformed payload records, or mismatched amounts to extract locked escrow funds.
3. **Network / Replay Adversary:** Captures historical Razorpay webhooks or API requests and re-transmits them to trigger duplicate releases or sweeps.
4. **Complexity-DoS Attacker:** Submits thousands of ambiguous line-item candidates to force exponential search hangs ($2^N$).

---

## 4. Adversarial Attack Vectors & Deterministic Mitigations

### 4.1 Missing & Forged Tenant Authentication
*   **Attack:** Client sends mutation requests (`/api/intercept`, `/api/reconcile`, `/api/apex/contracts/*`, `/api/capital/*`) with omitted or spoofed credentials.
*   **Mitigation:** `verify_tenant_auth` dependency extracts `X-Merchant-Id` and `X-API-Key`, validates registered tenants, and executes constant-time `hmac.compare_digest`. Unauthenticated requests immediately return HTTP 401.

### 4.2 Cross-Tenant IDOR & Resource Leakage
*   **Attack:** Authenticated Tenant B (`merchant_agent_demo_01`) queries contract ID or capital facility owned by Tenant A (`merchant_rzp_primary`).
*   **Mitigation:** All database queries require compound predicates `WHERE contract_id = ? AND tenant_id = ?` and `WHERE facility_id = ? AND tenant_id = ?`. Queries for unowned resources return HTTP 404/403. Tenant B liveness sweeps only evaluate Tenant B expired holds.

### 4.3 Webhook Replay & Timestamp Drift
*   **Attack:** Replaying legitimate past Razorpay webhooks to re-trigger settlement lifecycle transitions.
*   **Mitigation:** 
    1. Mandatory `created_at` timestamp parsed from JSON body or `X-Razorpay-Timestamp` header.
    2. Strict validation $|T_{\text{now}} - T_{\text{event}}| \le 300\text{s}$. Expired or future-skewed timestamps return HTTP 400 without touching the database.
    3. Atomic SQLite insertion into `processed_events (event_id PRIMARY KEY)`. Replays return HTTP 200 with `status: "ignored_duplicate"` and zero side-effects.

### 4.4 Forged Webhook HMAC Signature
*   **Attack:** Injecting arbitrary `transfer.processed` events with forged payload content.
*   **Mitigation:** Constant-time `hmac.compare_digest(hmac.new(secret, raw_body, sha256).hexdigest(), x_razorpay_signature)`. Invalid signatures return HTTP 400.

### 4.5 Double-Drawdown & Double-Sweep Races
*   **Attack:** Rapid concurrent HTTP POST requests to draw down capital or deduct settlement sweeps.
*   **Mitigation:**
    1. Client-supplied `idempotency_key` stored in `capital_idempotency` table.
    2. Optimistic Concurrency Control (CAS) on `capital_facilities`:
       ```sql
       UPDATE capital_facilities
       SET remaining_balance_paise = remaining_balance_paise - ?, version = version + 1
       WHERE facility_id = ? AND tenant_id = ? AND version = ?
       ```
    3. Zero IEEE-754 floats: All deductions calculated in integer paise.

### 4.6 Ambiguous Reconciliation & Combinatorial DoS
*   **Attack:** Submitting bank nodal credits that match multiple distinct invoice subsets, or submitting $N > 24$ candidates to hang the server.
*   **Mitigation:**
    1. Horowitz-Sahni meet-in-the-middle subset-sum algorithm bounded at $O(2^{N/2})$.
    2. Hard cap $N \le 24$, max node budget, and 500ms timeout. Exceeding bounds immediately returns `INCONCLUSIVE_TRUNCATED` status.
    3. Multiple valid subsets return `MatchResultStatus.AMBIGUOUS_COLLISION` and emit a structured Refusal Certificate rather than guessing.

---

## 5. Demonstration vs Production Key Custody Boundaries

| Dimension | Buildthon Prototype Implementation | Production Enterprise Target |
| :--- | :--- | :--- |
| **Signing Engine** | Server-side `SoftwareEd25519Custodian` (Zero browser private-key exposure). | AWS CloudHSM / AWS KMS (`ECC_NIST_P256` or `ED25519`) with strict IAM policies. |
| **Approver Verification** | Pinned checker public key registry with server-side signing endpoint. | FIDO2 / WebAuthn hardware security keys (YubiKey) with cryptographic biometric assertions. |
| **Data Persistence** | SQLite in WAL mode with CAS versioning & append-only triggers. | PostgreSQL 16 with Row-Level Security (RLS) & distributed Raft consensus (e.g. AWS Aurora). |
| **Secret Management** | Local environment variables & HMAC key derivation. | AWS Secrets Manager / HashiCorp Vault with automated rotation. |

---

## 6. Verification & Automated Attack Harness

The threat model mitigations are continuously verified via two independent automated harnesses:

1. **Full Pytest Security Suite:**
   ```powershell
   python -m pytest tests/test_security_tenant_isolation.py tests/test_capital_durability.py -v
   ```
2. **Standalone One-Command Judge Audit Harness:**
   ```powershell
   python -m kuber_recon.judge_demo
   ```
   *Executes complete settlement lifecycle and proves all 10 adversarial attack vectors are blocked with 100% invariant passes.*
