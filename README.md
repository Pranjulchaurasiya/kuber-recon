# 🏛️ APEX Assurance

> **Track 01: AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026**
> **Delivery-Gated Settlement for Agentic Commerce**
> *Powered by the KuberRecon deterministic verification kernel.*

[![Tests Passing](https://img.shields.io/badge/pytest-71%20passed-brightgreen)](tests/)
[![Deterministic Kernel](https://img.shields.io/badge/Financial%20Kernel-Zero%20LLM%20in%20Math-blue)](tests/test_zero_llm_in_math.py)
[![Zero-Float Policy](https://img.shields.io/badge/AST%20Static%20Linter-Zero%20Floats%20Guarded-success)](tests/test_zero_float_policy.py)
[![Razorpay Route Integration](https://img.shields.io/badge/Razorpay%20Route-Transfer%20Hold%20Gating-gold)](src/kuber_recon/server.py)
[![Whitebox Audit](https://img.shields.io/badge/Whitebox%20Audit-5%2F5%20Vectors%20Mitigated-purple)](tests/test_shannon_whitebox_audit.py)
[![Property Tests](https://img.shields.io/badge/Hypothesis-Invariants%20Verified-orange)](tests/test_property_based_invariants.py)

[ 🚀 Quickstart ](#-quickstart--local-reproduction) • [ 🏗️ Architecture ](#️-system-architecture) • [ 🛡️ Invariants ](#️-key-engineering-invariants) • [ 🧪 Test Suite ](#-full-test-suite-breakdown-65-items) • [ 🏢 Razorpay Value ](#-value-for-razorpay)

---

## 🎯 The Core Problem: Authorization vs. Assurance

> *"Razorpay Route authorizes an agent's spend. APEX verifies whether the seller agent delivered before settlement is released."*

In autonomous agentic commerce, payment gateways authorize funds at transaction time ($T_0$). However, releasing payouts before structured proof of delivery creates counterparty risk. **APEX Assurance** uses Razorpay Route's native `on_hold: true` settlement lock and releases it only when deterministic delivery invariants pass.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          THE APEX ASSURANCE PIPELINE                                   │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ 1. ROUTE HOLD     │ 2. DETERMINISTIC VERIFICATION │ 3. ATOMIC CAS ROUTE RELEASE        │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ Buyer Agent signs │ Seller delivers B2B payload.  │ Maker-Checker gate & Ed25519 Auth. │
│ procurement intent.│ APEX runs Mod-36 GSTIN checks │ Atomic CAS transitions to RELEASING│
│ Razorpay Route:   │ and line-item bounds.         │ Razorpay Route: on_hold -> false.  │
│ on_hold = true.   │ If corrupted -> Refused.      │ Webhook `transfer.processed` seals │
│ (₹25,000 lock)    │ Valid -> Release intent signed.│ the state to RELEASED.           │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 🏢 Value for Razorpay

| Question | Clear Answer |
|---|---|
| **What is it?** | **Razorpay Route Conditional Settlement Extension**: An SDK / webhook hook allowing platforms to attach deterministic delivery verification rules before releasing Route holds. |
| **Who is the buyer?** | B2B multi-agent marketplaces, procurement platforms, automated API exchanges, and supply-chain platforms using Razorpay Route. |
| **Why not standard disputes?** | Standard dispute/chargeback workflows operate **post-settlement** (asymmetric risk, recovery friction, 45-day cycle). APEX operates **pre-settlement**—funds never leave Razorpay's nodal account until delivery proof passes. |

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
│  ├── Combinatorial Exact-Cover Matcher:                                                │
│  │   ├── Horowitz-Sahni meet-in-the-middle subset-sum partitioning for N <= 24 items   │
│  │   └── Dancing Links (DLX) exact-cover solver with complexity caps (max 10,000 nodes)│
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

## 🧪 Full Test Suite Breakdown (71 Items)

```bash
$ python -m pytest -p no:deepeval -p no:langsmith tests/ -v
```

```text
tests/test_apex_assurance.py              17 passed (CAS updates, trigger immutability, audit logging)
tests/test_chaos_suite.py                  4 passed (adversarial batches & stress blasts)
tests/test_concurrent_workers.py           4 passed (webhook deduplication, CAS race protection)
tests/test_digital_twin_simulation.py      3 passed (bank holiday freezes, TDS shocks)
tests/test_escrow_sovereign.py             5 passed (statutory splits & partial refunds)
tests/test_planted_undecidables.py        10 passed (9 parameterized ambiguity traps + FMR formal proof)
tests/test_production_integrations.py      5 passed (layer 1-5 integration harnesses)
tests/test_property_based_invariants.py    2 passed (conservation of money & GSTIN fuzzing)
tests/test_shannon_whitebox_audit.py       5 passed (BOLA, spend caps, state drift mitigation)
tests/test_webhook_idempotency.py         14 passed (HMAC signatures, secret enforcement, replay defense)
tests/test_zero_float_policy.py            1 passed (AST scanning for float prohibition)
tests/test_zero_llm_in_math.py             1 passed (AST scanning for zero LLM imports in math)
--------------------------------------------------------------------------------------------------
Total: 71 passed, 0 skipped, 0 failed across 12 test modules
```

---

## 🚀 Quickstart & Local Reproduction

### 1. Backend Service
```bash
# Python 3.11+
python -m pip install -e ".[dev]"
python -m uvicorn kuber_recon.server:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000 (Landing Page) or http://localhost:3000/apex (Assurance Console)
```

### 3. Run Automated Invariant Tests
```bash
python -m pytest -p no:deepeval -p no:langsmith tests/ -q
```
