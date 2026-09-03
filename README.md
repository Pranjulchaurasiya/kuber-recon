# 🏛️ Kuber OS: Autonomous AI Finance Controller & Settlement Assurance

> **Track 04: AI Finance Controller · Razorpay AI Buildathon 2026**
> **Multi-Source Financial Reconciliation, Statutory Tax Assurance & Autonomous Nodal Recovery**
> *Powered by Horowitz–Sahni Meet-in-the-Middle Combinatorial Subset-Sum Matching, GSTIN Mod-36 Checksums, and Prototype Merkle Tree Audit Chains.*

[![Sarvam AI Voice](https://img.shields.io/badge/Sarvam%20AI-Indic%20Voice%20(Advait)-purple)](https://sarvam.ai)
[![Tests Passing](https://img.shields.io/badge/pytest-275%20passed%20(0%20failures)-brightgreen)](tests/)
[![Deterministic Kernel](https://img.shields.io/badge/Financial%20Kernel-Zero%20LLM%20in%20Math-blue)](tests/test_zero_llm_in_math.py)
[![Official Benchmark](https://img.shields.io/badge/Track%2004-Official%20Benchmark%20Frozen-gold)](reports/official_track04_benchmark.md)

[![Zero-Float Policy](https://img.shields.io/badge/AST%20Static%20Linter-Zero%20Floats%20Guarded-success)](tests/test_zero_float_policy.py)
[![Razorpay Route Integration](https://img.shields.io/badge/Razorpay%20Route-Transfer%20Hold%20Gating-gold)](src/kuber_recon/server.py)
[![Whitebox Audit](https://img.shields.io/badge/Whitebox%20Audit-14%2F14%20Vectors%20Mitigated-purple)](tests/test_shannon_whitebox_audit.py)
[![Security & Tenant Isolation](https://img.shields.io/badge/Tenant%20Auth-401%20Enforced%20%26%20Sanitized-purple)](tests/test_security_tenant_isolation.py)
[![Property Tests](https://img.shields.io/badge/Hypothesis-Invariants%20Verified-orange)](tests/test_property_based_invariants.py)

[ ⚡ 30s Cold Start ](#-30-second-cold-start-problem-vs-solution) • [ 🎯 Official Benchmark ](reports/official_track04_benchmark.md) • [ 🏗️ Layer Taxonomy ](#️-system-architecture--layer-taxonomy) • [ 🏢 Razorpay Value ](#-value-for-razorpay) • [ 🏗️ Architecture ](#️-system-architecture) • [ 🛡️ Invariants ](#️-key-engineering-invariants) • [ 🧪 Test Suite ](#-full-test-suite-breakdown-275-items) • [ 🚀 Quickstart ](#-quickstart--local-reproduction)

---

## ⚡ 30-Second Cold Start: Problem vs Solution

### 🚨 The Core Problem vs 🛡️ The APEX Solution

| # | 🔴 The Problem in AI Commerce | 🟢 The APEX Solution |
|---|---|---|
| **1** | **Blind Pre-Settlement Disbursals:** AI buyer agents order automatically, but legacy gateways disburse funds immediately before checking if goods actually arrived. | **Deterministic Escrow ([Razorpay Route](src/kuber_recon/server.py)):** Locks funds with `on_hold: true`. Settlement releases only after cryptographic proof of delivery. |
| **2** | **AI Hallucinations & Float Drift:** Using LLMs to verify invoices causes phantom line items and floating-point errors (`0.1 + 0.2 != 0.3`). | **Zero-LLM Math Kernel:** Uses **Horowitz–Sahni Subset-Sum algorithm** and **GSTIN Mod-36 checksums** in exact base-10 paise. 0 false matches observed on tested synthetic fixtures. |
| **3** | **Merchant Cash Crunch:** Small sellers face severe 30–45 day cash crunches while waiting for escrow and banking cycles. | **1-Click Capital + 12% Nodal Sweep:** Converts verified revenue into instant working capital, auto-recovering advances directly at the nodal gateway. |

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                HOW APEX WORKS IN 4 STEPS                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  1. AI Buyer Orders      ──▶  Razorpay Route holds merchant payout on strict hold      │
│  2. Delivery & GST Match ──▶  Horowitz–Sahni Subset-Sum & GSTIN Mod-36 Checksums       │
│  3. Escrow Releases      ──▶  Funds settle to merchant with ZERO math hallucinations   │
│  4. 1-Click Capital      ──▶  Merchant gets instant advance; repaid via 12% split-sweep│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ System Architecture & Layer Taxonomy

Kuber OS unifies three specialized engineering layers into one coherent financial operating system:

| Layer | Component | Core Technical Responsibility |
|---|---|---|
| **OS & Intelligence Layer** | **Kuber OS** | CFO AI Copilot, Multi-Source Settlement Radar, Verified-Revenue Capital Hub, and 7-Day Forecasting. |
| **Escrow Protocol Layer** | **APEX Protocol** | **A**utonomous **P**roof & **Ex**ecution engine gating Razorpay Route settlements (`on_hold: true`) behind delivery verification. |
| **Mathematical Kernel** | **KuberRecon** | **Horowitz–Sahni Subset-Sum Solver**, **Indian GSTIN Mod-36 Checksums**, **Paise-Exact Zero-Float Policy**, and **Prototype Merkle Tree Audit Chains** (0 false matches observed on verified synthetic fixtures). |

---

## 🎯 The Unified Pitch: Underwriting Ground Truth & Nodal Recovery

> *"APEX turns verified agentic commerce into instant working capital for merchants, using deterministic delivery verification as its underwriting moat and Razorpay Route split-settlements for automated recovery."*

### Why Capital + Assurance is One Coherent System:
1. **The Moat (APEX Assurance):** Banks and NBFCs cannot underwrite autonomous AI agent commerce because they lack ground truth line-item delivery logs and statutory GSTIN verification. APEX provides mathematically verifiable proof of delivery before funds settle.
2. **The Product (APEX Capital):** Armed with real-time Verified Delivered GMV (VD-GMV), Razorpay extends instant working capital advances to merchants against trailing verified revenue.
3. **The Recovery (Razorpay Route):** Because Razorpay controls the settlement stream via Route, advances are amortized automatically via 10%–15% daily split-sweeps deducted directly at the nodal source—mitigating merchant default risk through automated recovery.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE APEX PRODUCT LIFECYCLE                               │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ 1. ASSURANCE MOAT │ 2. INSTANT CAPITAL DRAWDOWN   │ 3. SOURCE-SPLIT SETTLEMENT RECOVERY│
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ Buyer/Seller agent│ Bayesian Underwriter evaluates│ Every incoming bank credit block   │
│ transactions match│ 30-Day Verified Delivered GMV │ automatically sweeps 12% at source │
│ via Subset-Sum &  │ and disburses instant liquidity│ via Razorpay Route until advance   │
│ Mod-36 GST checks.│ via Razorpay Payouts (T=0).   │ is fully amortized to ₹0.00.       │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 🏢 Value for Razorpay

| Question | Clear Answer |
|---|---|
| **What is it?** | **Razorpay Route Capital & Assurance Engine**: An autonomous underwriting and split-settlement extension converting verified platform GMV into instant working capital advances. |
| **Who is the buyer?** | B2B marketplaces, supply-chain platforms, and agentic commerce merchants processing transactions via Razorpay. |
| **Why can't banks copy it?** | **The Ownership Triple-Test**: External lenders cannot see line-item GSTIN-verified ground truth, cannot gate settlement holds in real time, and do not possess native split-settlement deduction capabilities on the nodal stream. |
| **Why not standard disputes?** | Standard dispute workflows operate **post-settlement** (asymmetric risk, recovery friction, 45-day cycle). APEX operates **pre-settlement**—funds never leave Razorpay's nodal account until delivery proof passes. |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              APEX ASSURANCE SYSTEM ARCHITECTURE                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ INGESTION & GATEWAY LAYER ]                                                         │
│  ├── Razorpay Webhook Ingestion (HMAC-SHA256 X-Razorpay-Signature verification)        │
│  ├── Razorpay Route API Adapter (POST /v1/transfers with on_hold: true, PATCH release) │
│  └── Multi-Bank Statement Parsers (HDFC, ICICI, SBI Nodal settlement feeds)            │
│                                                                                        │
│  [ DETERMINISTIC VERIFICATION KERNEL (ZERO-LLM FINANCIAL PATH) ]                      │
│  ├── Delivery Assertion Engine:                                                        │
│  │   ├── Indian GSTIN 15-char check-digit algorithm (Mod-36 with 1-2 weight factors)   │
│  │   └── Exact batch record count & line-item amount invariants                        │
│  ├── Combinatorial Subset-Sum Matcher:                                                │
│  │   ├── Iterative Horowitz-Sahni meet-in-the-middle subset-sum matcher (N <= 24)      │
│  │   └── Deterministic Subset-Sum Solver with complexity caps (max 10,000 nodes)        │
│  └── Statutory Tax Engine (Section 194-O TDS, MDR, GST on MDR) in exact base-10 paise  │
│                                                                                        │
│  [ CONCURRENCY & SETTLEMENT ESCROW LAYER ]                                             │
│  ├── SQLite WAL State Store (PRAGMA busy_timeout = 5000) for local reproducibility     │
│  ├── Optimistic Concurrency CAS: State transitions HELD -> RELEASING -> RELEASED       │
│  ├── Trigger-protected immutable audit logging                                         │
│  └── Single Authoritative Webhook (/api/webhook/razorpay) for Finalization             │
│                                                                                        │
│  [ VERIFICATION & SECURITY HARNESS ]                                                   │
│  ├── AST Static Import Linter: Scans 6 financial files, failing on any LLM imports    │
│  ├── Whitebox Pentest Suite: 5 Exploit Vectors (BOLA, spend caps, TOCTOU, Merkle)      │
│  ├── Hypothesis Property Invariants: Randomized trials verifying Delta = 0 paise       │
│  └── Planted Undecidable Corpus: Verifies refusal on ambiguous subset collisions       │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Key Engineering Invariants

| # | Invariant | Technical Mechanism | Verification Proof |
|---|---|---|---|
| **1** | **Paise-Exact Zero-Float Policy** | Python `Decimal` and integer paise. Prohibits IEEE-754 floats in financial paths. | [`test_zero_float_policy.py`](tests/test_zero_float_policy.py) |
| **2** | **Zero-LLM in Financial Math** | AST static import linter scanning all monetary calculation modules. | [`test_zero_llm_in_math.py`](tests/test_zero_llm_in_math.py) |
| **3** | **Conservation of Money** | Hypothesis property testing: `Gross = Principal + GST`, Delta = 0 paise across all tax splits. | [`test_property_based_invariants.py`](tests/test_property_based_invariants.py) |
| **4** | **Honest Refusal on Ambiguity** | When $>1$ valid subset covers a credit, raises `AmbiguousMatchError` rather than guessing. | [`test_planted_undecidables.py`](tests/test_planted_undecidables.py) |
| **5** | **Pre-Settlement Route Gating** | Native Razorpay Route `on_hold: true` locking funds until assertions pass. | [`test_apex_assurance.py`](tests/test_apex_assurance.py) |
| **6** | **Atomic CAS State Transitions** | Optimistic locking via SQL `version = version + 1 WHERE version = ?`. | [`test_concurrent_workers.py`](tests/test_concurrent_workers.py) |
| **7** | **Single Webhook Source of Truth** | `/api/webhook/razorpay` strictly finalizes `RELEASING` -> `RELEASED` via `transfer.processed`. | [`test_webhook_idempotency.py`](tests/test_webhook_idempotency.py) |

---

## 🧪 Full Test Suite Breakdown (212 Items — 100% Green)

> **Strict 3-Way Evidence Framework:**
> - `VERIFIED_TEST_CORPUS`: **212 automated tests pass in sandbox and mock environments.**
> - `SIMULATION_STRESS_TEST`: **Zero unhandled exceptions occurred in synthetic stress runs (50 to 1,000+ records).**
> - `PRODUCTION_DEFENSE`: **Production integrations fail closed on unconfigured infrastructure (AWS KMS, PostgreSQL/Aurora).**

```bash
$ python -m pytest tests/ -q
212 passed, 1 warning in 30.64s
```

```text
tests/test_apex_assurance.py              17 passed (CAS updates, trigger immutability, audit logging)
tests/test_capital_concurrency.py          5 passed (double-drawdown races, zero over-recovery, API 409)
tests/test_capital_durability.py           5 passed (process restart recovery, CAS versioning, sweep deduplication)
tests/test_capital_storage_contract.py     6 passed (unified storage backend delegation, double-drawdown, CAS)
tests/test_capital_underwriting.py          4 passed (Bayesian SRI, advance disbursement, split-sweeps, stagnancy)
tests/test_chaos_suite.py                  4 passed (adversarial batches & stress blasts)
tests/test_clustered_50plus_benchmark.py    9 passed (deterministic clustering, 50-1000 txns, truncation caps)
tests/test_concurrent_workers.py           4 passed (webhook deduplication, CAS race protection)
tests/test_digital_twin_simulation.py      3 passed (bank holiday freezes, TDS shocks)
tests/test_escrow_sovereign.py             5 passed (statutory splits & partial refunds)
tests/test_global_ambiguity.py             8 passed (cross-GSTIN & cross-date collision refusal, MR queue)
tests/test_integration_chaos.py            4 passed (20-thread webhook dedup, 5-worker CAS race, paise conservation)
tests/test_kms_custody.py                  4 passed (fail-closed KMS factory, timeout & malformed payload defense)
tests/test_outbox_claiming.py              8 passed (atomic claiming, exponential backoff, DLQ quarantine)
tests/test_outbox_publisher.py             5 passed (durable publisher boundary, retry backoff, DLQ quarantine)
tests/test_planted_undecidables.py        10 passed (9 parameterized ambiguity traps + FMR fixture verification)
tests/test_production_architecture.py      8 passed (KMS custodian, SQLite WAL outbox restart, secure JWT RBAC, /health)
tests/test_production_integrations.py      5 passed (layer 1-5 integration harnesses)
tests/test_property_based_invariants.py    2 passed (conservation of money & GSTIN fuzzing)
tests/test_rbac_authorization.py           5 passed (subject provisioning, role escalation refusal, endpoint guards)
tests/test_rbac_provisioning.py            9 passed (token issuance, RISK_ANALYST, maker-checker escalation)
tests/test_security_tenant_isolation.py    36 passed (tenant 401/403, cross-tenant scoping, webhook freshness, solver budget)
tests/test_server_storage_init.py          5 passed (explicit backend injection, zero DB_FILE coupling in prod)
tests/test_shannon_whitebox_audit.py       5 passed (BOLA, spend caps, state drift mitigation)
tests/test_signer_factory.py               8 passed (deterministic factory resolution, AWS KMS fail-closed)
tests/test_storage_backend.py              6 passed (storage factory selection, CAS updates, WAL deduplication)
tests/test_webhook_idempotency.py         14 passed (HMAC signatures, secret enforcement, replay defense)
tests/test_zero_float_policy.py            1 passed (AST scanning for float prohibition)
tests/test_zero_llm_in_math.py             1 passed (AST scanning for zero LLM imports in math)
--------------------------------------------------------------------------------------------------
Total: 212 passed, 0 skipped, 0 failed across 212 test items in 29 test modules (100% PASS)
```

---

## ⏱️ 5-Minute Judge Verification Runbook (cURL Commands)

Judges can verify all major financial invariants in real time on the running API gateway (`http://127.0.0.1:8000`):

```bash
# 1. Health & Storage Status (Reports active SQLite WAL backend & metrics)
curl -s http://127.0.0.1:8000/health

# 2. Clustered MITM Batch Reconciliation (100 Transactions, 0 paise drift)
curl -s -X POST http://127.0.0.1:8000/api/v2/reconcile/batch-clustered \
  -H "Content-Type: application/json" \
  -H "X-Merchant-Id: merchant_rzp_primary" \
  -H "X-API-Key: kuber_sandbox_key_primary_2026" \
  -d '{"records": 100, "seed": 42}'

# 3. Global Multi-Cluster Ambiguity Refusal (Proves zero false match tolerance)
curl -s -X POST http://127.0.0.1:8000/api/reconcile/ambiguous \
  -H "X-Merchant-Id: merchant_rzp_primary" \
  -H "X-API-Key: kuber_sandbox_key_primary_2026"

# 4. Create APEX Route Escrow Contract (Funds locked with on_hold: true)
curl -s -X POST http://127.0.0.1:8000/api/apex/contracts/create \
  -H "Content-Type: application/json" \
  -H "X-Merchant-Id: merchant_rzp_primary" \
  -H "X-API-Key: kuber_sandbox_key_primary_2026" \
  -d '{"buyer_agent_id":"buyer_01","seller_agent_id":"seller_01","seller_account_id":"acc_mock_01","amount_paise":50000,"expected_record_count":1,"ttl_seconds":3600}'

# 5. Dual-Authorization Anti-Collusion Guard (Buyer attempting self-release rejected)
curl -s -X POST http://127.0.0.1:8000/api/apex/contracts/release \
  -H "Content-Type: application/json" \
  -H "X-Merchant-Id: merchant_rzp_primary" \
  -H "X-API-Key: kuber_sandbox_key_primary_2026" \
  -d '{"contract_id":"apex_cnt_sample","checker_id":"buyer_01","public_key_hex":"00","signature_hex":"00"}'

# 6. Working Capital Advance Sweep (Autonomous nodal split-recovery at source)
curl -s -X POST http://127.0.0.1:8000/api/capital/reconcile-and-sweep \
  -H "X-Merchant-Id: merchant_rzp_primary" \
  -H "X-API-Key: kuber_sandbox_key_primary_2026"
```

---

## 🚀 Quickstart & Local Reproduction

### 1. Instant Capital & Settlement CLI Demos
```bash
# 1. Run Verified-Revenue Capital Underwriting & Split-Sweep Demo
python -m kuber_recon.cli run-capital-demo

# 2. Run Instant Subset-Sum Verification Demo
python -m kuber_recon.cli run-demo

# 3. Run Causal Financial Stress-Test
python -m kuber_recon.cli simulate-shock
```

### 2. Full-Stack Web Console
```bash
# Terminal 1: Backend API (port 8000)
python -m uvicorn kuber_recon.server:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend Dashboard (port 3000)
cd frontend && npm run dev
# Open http://localhost:3000
```

### 3. Run Automated Invariant Tests (275 Items)
```bash
python -m pytest -q
```

### 4. Run Official Deterministic Benchmark Suite (Track 04)
```bash
python scripts/run_official_benchmark.py
```

---

## ⚖️ 3-Tier Architecture Boundary Matrix

| Dimension | Tier 1: Fully Implemented Kernel (This Repo) | Tier 2: Sandbox / Prototype Layer | Tier 3: Planned Production Architecture |
|---|---|---|---|
| **Reconciliation Math** | Base-10 integer paise arithmetic, bounded Horowitz–Sahni subset-sum solver ($N \le 24$), explicit `INCONCLUSIVE_TRUNCATED` outcomes. | Synthetic benchmark fixture generator (11,100 cases), seeded chaos scenarios. | Distributed streaming partitions, multi-worker Kafka partition consumers. |
| **Cryptography & Keys** | RFC 8032 Ed25519 asymmetric signature generation and verification via Python `cryptography` hazmat. | Local demonstration software keys (pinned demo public keys, server-side software demo signer). | Dedicated AWS CloudHSM / AWS KMS asymmetric key custody (FIPS 140-2 Level 3). |
| **State Durability & CAS** | SQLite WAL mode with optimistic CAS version updates, triggers for update/delete prevention, tenant indexes. | Local sandbox single-node filesystem database (`kuber_idempotency.db`). | Multi-AZ AWS Aurora PostgreSQL with row-level locks (`SELECT FOR UPDATE`) and Redis Cluster. |
| **Payment Rails** | Authentic Razorpay API payload schemas and Route transfer hold/release logic. | Zero-key sandbox simulation fallback when live credentials are unprovisioned. | Live production Razorpay Route MID feature flag, linked accounts, and bank nodal routing. |
| **Capital Facilities** | Bayesian SRI credit scoring, 12% split-sweep nodal amortizations, SQLite-backed facility store with CAS versioning. | Process-local `RLock` synchronization and local SQLite facility tracking. | Distributed Redis Redlock / transactional PostgreSQL locking across multi-instance worker nodes. |
| **Audit Digest** | Prototype Merkle Tree hash chain computed over executed audit blocks. | Local tamper-evident audit digest in JSON / SQLite. | Production append-only log backed by HSM-signed checkpointing. |

---

## ⚠️ Regulatory & Statutory Disclaimer

> **IMPORTANT NOTICE:** Regulatory and statutory logic shown in this project (including Indian GST Section 16/Rule 36(4), Income Tax Act Section 194-O TDS withholdings, and RBI Digital Lending FLDG guidelines) is an algorithmic sandbox demonstration inspired by applicable RBI, CBIC, GST, FLDG, and payment-settlement concepts. It is not legal, tax, or financial advice, does not establish formal regulatory compliance, and requires independent formal legal, tax, risk, security, and compliance review before production commercial use.

---

## 🚧 Known Limitations & System Boundaries

1. **Local Software Key Custody:** Asymmetric Ed25519 keypairs are demonstration keys executed in server-side software memory (Python `cryptography` hazmat); production requires hardware KMS/CloudHSM custody.
2. **Mock / Sandbox Rails Default:** When live Razorpay API keys are absent, transfer creation and webhook processing execute against our deterministic sandbox simulation adapter.
3. **Single-Node State:** Contract state and idempotency records reside in local SQLite (WAL mode); horizontal multi-pod deployment requires distributed databases and locking.
4. **Synthetic Fixture Evaluation:** Measured 0.000 FMR is verified on the synthetic and planted adversarial fixture corpus under the $N \le 24$ complexity bound; it is not a guarantee across unstructured, arbitrary real-world bank narration strings.
5. **Bounded Solver Complexity:** Candidate pools exceeding 24 items or exceeding the node/time budget return `INCONCLUSIVE_TRUNCATED` and halt automated release.
