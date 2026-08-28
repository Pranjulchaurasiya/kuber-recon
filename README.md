# 🏛️ KuberRecon (कुबेर मिलान)

> **Track 01: AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026**  
> **Delivery-Gated Seller Settlement for Agentic Commerce:** *Pre-Settlement Route Hold Gating (`on_hold: true`), Ed25519 Auth, Atomic CAS Hold Release, Single Authoritative Webhook.*

[![Tests Passing](https://img.shields.io/badge/pytest-54%20passed-brightgreen)](tests/)
[![Undecidable Handling](https://img.shields.io/badge/Planted%20Undecidables-4%2F4%20Isolated-blue)](tests/test_planted_undecidables.py)
[![Zero-Float Policy](https://img.shields.io/badge/AST%20Static%20Linter-Zero%20Floats%20Guarded-success)](tests/test_zero_float_policy.py)
[![Razorpay Route Integration](https://img.shields.io/badge/Razorpay%20Route-Transfer%20Hold%20Gating-gold)](src/kuber_recon/server.py)
[![Whitebox Pentest](https://img.shields.io/badge/Whitebox%20Audit-5%2F5%20Vectors%20Mitigated-purple)](tests/test_shannon_whitebox_audit.py)
[![Property Tests](https://img.shields.io/badge/Hypothesis-Invariants%20Verified-orange)](tests/test_property_based_invariants.py)

[ 🚀 Quickstart ](#-quickstart--local-reproduction) • [ 🏗️ Architecture ](#️-system-architecture) • [ 🛡️ Invariants ](#️-8-verified-engineering-invariants) • [ 🧪 54/54 Tests ](#-full-verified-test-suite-breakdown-54-items) • [ 📡 API Reference ](#-api-reference)

---

## 💬 Real-World CFO & Controller Queries

| Real-World Query | System Resolution | Invariant Enforced |
|---|---|---|
| *"Why was Route contract #CN_7781 held on Razorpay?"* | **Gated on `on_hold: true`** until Mod-36 GSTIN & 500-record delivery verified. | Dual-Agent Pre-Settlement Assurance |
| *"Show Section 194-O TDS & MDR deduction for HDFC settlement #SETTLE_9981."* | Computes **paise-exact 1% TDS, 1.85% MDR, 18% GST** with zero float drift. | Base-10 Integer Paise Math Kernel |
| *"List all ambiguous bank credits in the 10,000 transaction batch."* | **4/4 Planted Undecidables** isolated to Exception Drawer without guessing. | Zero False Match Rate ($FMR = 0.000$) |

---

## 🎯 The Core Thesis: Authorisation vs. Assurance

> *"Razorpay can authorise an agent's spend. KuberRecon proves whether the seller agent delivered before its settlement is released."*

In autonomous multi-agent commerce, payment gateways authorize spending at transaction inception ($T_0$). However, releasing settlements before cryptographic proof of delivery creates counterparty risk. **KuberRecon** provides deterministic, paise-exact settlement gating and multi-source reconciliation:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         THE KUBERRECON ASSURANCE PIPELINE                              │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ 1. CONTRACT HOLD  │ 2. DETERMINISTIC VERIFICATION │ 3. ATOMIC CAS ROUTE RELEASE        │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ Buyer Agent signs │ Seller delivers B2B payload.  │ Maker-Checker gate & Ed25519 Auth. │
│ spend contract.   │ KuberRecon runs Mod-36 GSTIN  │ Atomic CAS transitions to RELEASING│
│ Razorpay Route:   │ check, line item exactness.   │ Razorpay Route: on_hold -> false.  │
│ on_hold = true.   │ If corrupted -> Refused.      │ Webhook `transfer.processed` seals │
│ (500-item lock)   │ Payload hashed & Ed25519 signed.│ the state to RELEASED.           │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             KUBERRECON TECHNICAL MATRIX                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ INGESTION LAYER ]                                                                   │
│  ├── Razorpay Webhooks (HMAC-SHA256 X-Razorpay-Signature, Full 64-Hex Digest Idempotency)│
│  ├── Multi-Bank MT940 / CSV Parsers (HDFC, ICICI, SBI Nodal Feeds)                     │
│  └── GSTN GSTR-2B ITC Ingestion Pipeline                                               │
│                                                                                        │
│  [ FINANCIAL MATH KERNEL (ZERO-LLM DETERMINISTIC CORE) ]                               │
│  ├── Combinatorial Exact-Cover Engine:                                                 │
│  │   ├── Horowitz-Sahni Meet-in-the-Middle Partitioning for N <= 24 items              │
│  │   └── Donald Knuth Algorithm X / Dancing Links (DLX) with complexity bounds         │
│  │       (max_nodes = 10000, timeout_ms = 500 integer cap against algorithmic DoS)   │
│  ├── Temporal Time-Window Indexing (T +/- (1 + Holidays))                              │
│  ├── Indian Tax Engine (Sec 194-O TDS, MDR, 18% GST) -- Paise-Exact Decimal            │
│  └── GSTIN Mod-36 (ISO/IEC 7064) Algorithmic Checksum Engine                           │
│                                                                                        │
│  [ CONCURRENCY & SETTLEMENT ESCROW LAYER ]                                             │
│  ├── SQLite WAL Concurrency: PRAGMA busy_timeout = 5000                                │
│  ├── Dual-Party RFC 8032 Ed25519 Signatures (Pinned Seller Key + CFO Maker/Checker)   │
│  ├── Optimistic Concurrency CAS: State transitions HELD -> RELEASING -> RELEASED       │
│  ├── Nodal Liveness Sweep (/sweep-expired): Resolves expired to EXPIRED_HOLD           │
│  └── Single Authoritative Webhook (/api/webhook/razorpay) for Finalization             │
│                                                                                        │
│  [ SECURITY AUDIT & VERIFICATION HARNESS ]                                             │
│  ├── AST Static Import Linter: Scans 6 financial files, failing on any LLM imports    │
│  ├── Whitebox Pentest Suite: 5 Exploit Vectors (BOLA, Spends, TOCTOU, Escrow, CAS)     │
│  ├── Hypothesis Property Invariants: Randomized trials verifying Delta = 0 paise       │
│  └── Planted Undecidable Corpus: 4/4 adversarial undecidables isolated to exception    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 8 Verified Engineering Invariants

| # | Verified Invariant | Implementation Mechanism | Test File Proof |
|---|---|---|---|
| **1** | **Paise-Exact Zero-Float Policy** | Python `Decimal` + integer paise throughout. Floats strictly prohibited in monetary paths. | [`test_zero_float_policy.py`](tests/test_zero_float_policy.py) |
| **2** | **Zero-LLM in Financial Math** | AST static import linter scanning `engine.py`, `tax.py`, `actions.py`, `types.py`, `assurance.py`, `escrow.py`. | [`test_zero_llm_in_math.py`](tests/test_zero_llm_in_math.py) |
| **3** | **Conservation of Money** | Hypothesis property testing: `Gross = Principal + GST` and `Net_Payout = Gross - TDS_194O - MDR - GST_on_MDR`, Delta = 0 paise. | [`test_property_based_invariants.py`](tests/test_property_based_invariants.py) |
| **4** | **Planted Undecidable Isolation** | Multi-subset collisions and rounding anomalies trigger `AmbiguousMatchError` -> Routed to Exception Drawer. | [`test_planted_undecidables.py`](tests/test_planted_undecidables.py) |
| **5** | **Cryptographic Agent Auth & Key Pinning** | Dual-party RFC 8032 Ed25519 signing. Seller manifest signed with pinned key; release signed by independent CFO checker. | [`security.py`](src/kuber_recon/security.py) & [`assurance.py`](src/kuber_recon/assurance.py) |
| **6** | **Atomic CAS Hold Release** | Optimistic locking via SQL `version = version + 1 WHERE version = ?`. Eliminates double-release lost updates. | [`test_concurrent_workers.py`](tests/test_concurrent_workers.py) |
| **7** | **Single Webhook Truth** | `/api/webhook/razorpay` strictly finalizes `RELEASING` -> `RELEASED` via `transfer.processed`. | [`server.py`](src/kuber_recon/server.py) |
| **8** | **Nodal Liveness Sweep** | Automated TTL sweep resolving expired contracts to manual refund review `EXPIRED_HOLD`. | [`server.py`](src/kuber_recon/server.py) |

---

## 🚀 Quickstart & Local Reproduction

### 1. Installation
```bash
git clone https://github.com/Pranjulchaurasiya/kuber-recon.git
cd kuber-recon
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -e .
```

### 2. Execute Test Suite (54 / 54 Passing)
```bash
python -m pytest -p no:deepeval -p no:langsmith -v
```

### 3. Run Backend API Server (FastAPI on Port 8000)
```bash
python src/kuber_recon/server.py
```
* Interactive Swagger Docs: `http://localhost:8000/docs`
* Health Endpoint: `http://localhost:8000/api/health`

### 4. Run Frontend Console (Next.js 14 on Port 3000)
```bash
cd frontend
npm install
npm run dev
```
* Open `http://localhost:3000` for the Reconciliation Dashboard.
* Open `http://localhost:3000/apex` for the **KuberRecon Assurance Console**.

---

## 📡 API Reference

| Endpoint | Method | Purpose | Key Invariant |
|---|---|---|---|
| `/api/reconcile` | `POST` | Execute B2B batch reconciliation | Knuth DLX Exact-Cover, Ambiguous Match Isolation |
| `/api/webhook/razorpay` | `POST` | Razorpay webhook ingestion | Single authoritative source for `transfer.processed` |
| `/api/apex/contracts/create` | `POST` | Create dual-agent assurance contract | Pre-settlement Razorpay Route `on_hold: true` + 500-record invariant |
| `/api/apex/contracts/deliver` | `POST` | Deliver B2B payload for verification | Mandatory Seller Ed25519 signature + Pinned Key verification |
| `/api/apex/contracts/release` | `POST` | Release escrowed settlement hold | Ed25519 verification + CAS transition to `RELEASING` |
| `/api/apex/contracts/sweep-expired` | `POST` | Trigger nodal escrow liveness sweep | CAS-protected transition to `EXPIRED_HOLD` |

---

## 🧪 Full Verified Test Suite Breakdown (54 Items)

```
tests/test_apex_assurance.py              10 passed
tests/test_chaos_suite.py                  4 passed
tests/test_concurrent_workers.py           4 passed
tests/test_digital_twin_simulation.py      3 passed
tests/test_escrow_sovereign.py             5 passed
tests/test_planted_undecidables.py         4 passed
tests/test_production_integrations.py      5 passed
tests/test_property_based_invariants.py    2 passed
tests/test_shannon_whitebox_audit.py       5 passed
tests/test_webhook_idempotency.py         10 passed
tests/test_zero_float_policy.py            1 passed
tests/test_zero_llm_in_math.py             1 passed
---------------------------------------------------
Total: 54 passed across 12 test modules
```

---

## 🏛️ Razorpay Architectural Alignment

* **Razorpay Route Settlement Gating:** Uses native Route transfer `on_hold: true` parameters, released via `PATCH /v1/transfers/{id}` (`on_hold: false`) only upon verified proof of delivery.
* **Section 194-O TDS Accounting:** Base-10 exact tax calculation with PAN-deductor validation.
* **GSTIN ISO/IEC 7064 Mod-36 Checksum:** Deterministic checksum validation rejecting corrupted invoices at the gate.
