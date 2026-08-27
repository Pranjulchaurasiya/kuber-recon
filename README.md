# 🏛️ KuberRecon (कुबेर मिलान)

> **Track 04: AI Finance Controller · Razorpay AI Buildathon 2026**  
> **Autonomous Financial Integrity & Pre-Settlement Route Assurance Engine:** *Pre-Settlement Route Hold Gating (`on_hold: true`), Paise-Exact Combinatorial Settlement Engine (Donald Knuth DLX), Dual-Agent Delivery Assurance, Atomic CAS Hold Release & White-Box Pentest Defense.*

[![Tests Passing](https://img.shields.io/badge/pytest-51%20passed-brightgreen)](tests/)
[![Undecidable Handling](https://img.shields.io/badge/Planted%20Undecidables-4%2F4%20Isolated-blue)](tests/test_planted_undecidables.py)
[![Zero-Float Policy](https://img.shields.io/badge/AST%20Static%20Linter-Zero%20Floats%20Guarded-success)](tests/test_zero_float_policy.py)
[![Razorpay Route Integration](https://img.shields.io/badge/Razorpay%20Route-Transfer%20Hold%20Gating-gold)](src/kuber_recon/server.py)
[![Whitebox Pentest](https://img.shields.io/badge/Whitebox%20Audit-5%2F5%20Vectors%20Mitigated-purple)](tests/test_shannon_whitebox_audit.py)
[![Property Tests](https://img.shields.io/badge/Hypothesis-Invariants%20Verified-orange)](tests/test_property_based_invariants.py)

---

## 🎯 The Core Thesis: Authorisation vs. Assurance

> *"Razorpay can authorise an agent's spend. APEX proves whether the seller agent delivered before its settlement is released."*

In autonomous multi-agent commerce, payment gateways authorize spending at transaction inception ($T_0$). However, releasing settlements before cryptographic proof of delivery creates counterparty risk. **KuberRecon + APEX Assurance** provides deterministic, paise-exact settlement gating:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE APEX ASSURANCE PIPELINE                               │
├───────────────────┬───────────────────────────────┬────────────────────────────────────┤
│ 1. CONTRACT HOLD  │ 2. DETERMINISTIC VERIFICATION │ 3. ATOMIC CAS ROUTE RELEASE        │
├───────────────────┼───────────────────────────────┼────────────────────────────────────┤
│ Buyer Agent signs │ Seller delivers B2B payload.  │ Maker-Checker gate verified.       │
│ spend contract.   │ APEX runs Mod-36 GSTIN check, │ Atomic CAS: WHERE version = ?      │
│ Razorpay Route:   │ line item exactness, payload  │ Razorpay Route: on_hold -> false.  │
│ on_hold = true.   │ bounds. If corrupted -> 412.  │ 5 racing checkers -> 1 OK, 4 409s. │
└───────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          KUBERRECON + APEX TECHNICAL MATRIX                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ INGESTION LAYER ]                                                                   │
│  ├── Razorpay Webhooks (HMAC-SHA256 X-Razorpay-Signature, Event-ID Deduplication)      │
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
│  ├── Optimistic Concurrency CAS: UPDATE ... WHERE version = ? AND on_hold = 1         │
│  ├── Maker-Checker Separation of Duties: checker_id not in {buyer_id, seller_id} -> 403│
│  ├── Nodal Liveness Sweep (/sweep-expired): Force-Resolution to EXPIRED_AUTO_REFUNDED  │
│  └── Razorpay Route Adapter: Native Transfer Hold & Patch Gating                       │
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
| **5** | **Algorithmic DoS Mitigation** | Knuth DLX recursion capped at `max_nodes = 10000` & `timeout_ms = 500`. Meet-in-the-Middle bounded at N <= 24. | [`engine.py`](src/kuber_recon/engine.py) |
| **6** | **Atomic CAS Hold Release** | Optimistic locking via SQL `version = version + 1 WHERE version = ?`. Eliminates double-release lost updates. | [`test_concurrent_workers.py`](tests/test_concurrent_workers.py) |
| **7** | **Maker-Checker Separation** | Structural refusal when `checker_id == buyer_id` or `seller_id` (returns HTTP 403 Forbidden). | [`server.py`](src/kuber_recon/server.py) |
| **8** | **Nodal Liveness Sweep** | Automated TTL sweep resolving expired contracts to `EXPIRED_AUTO_REFUNDED` via CAS. | [`server.py`](src/kuber_recon/server.py) |

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

### 2. Execute Test Suite (51 / 51 Passing)
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
* Open `http://localhost:3000/apex` for the **APEX Dual-Agent Assurance Console**.

---

## 📡 API Reference

| Endpoint | Method | Purpose | Key Invariant |
|---|---|---|---|
| `/api/reconcile` | `POST` | Execute B2B batch reconciliation | Knuth DLX Exact-Cover, Ambiguous Match Isolation |
| `/api/webhooks/razorpay` | `POST` | Razorpay webhook ingestion | HMAC SHA-256 Signature Verification |
| `/api/apex/contracts/create` | `POST` | Create dual-agent assurance contract | Pre-settlement Razorpay Route `on_hold: true` |
| `/api/apex/contracts/deliver` | `POST` | Deliver B2B payload for verification | Mod-36 GSTIN checksum; returns HTTP 412 on corruption |
| `/api/apex/contracts/release` | `POST` | Release escrowed settlement hold | Maker-Checker separation + atomic CAS hold release |
| `/api/apex/contracts/sweep-expired` | `POST` | Trigger nodal escrow liveness sweep | CAS-protected auto-refund for expired holds |

---

## 🧪 Full Verified Test Suite Breakdown (51 Items)

```
tests/test_apex_assurance.py               6 passed
tests/test_chaos_suite.py                  4 passed
tests/test_concurrent_workers.py           4 passed
tests/test_digital_twin_simulation.py      3 passed
tests/test_escrow_sovereign.py             5 passed
tests/test_planted_undecidables.py         4 passed
tests/test_production_integrations.py      5 passed
tests/test_property_based_invariants.py    2 passed
tests/test_shannon_whitebox_audit.py       5 passed
tests/test_webhook_idempotency.py         11 passed
tests/test_zero_float_policy.py            1 passed
tests/test_zero_llm_in_math.py             1 passed
---------------------------------------------------
Total: 51 passed across 12 test modules
```

---

## 🏛️ Razorpay Architectural Alignment

* **Razorpay Route Settlement Gating:** Uses native Route transfer `on_hold: true` parameters, released via `PATCH /v1/transfers/{id}` (`on_hold: false`) only upon verified proof of delivery.
* **Section 194-O TDS Accounting:** Base-10 exact tax calculation with PAN-deductor validation.
* **GSTIN ISO/IEC 7064 Mod-36 Checksum:** Deterministic checksum validation rejecting corrupted invoices at the gate.
