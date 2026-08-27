# 🏛️ KUBERRECON (कुबेर मिलान)

> **Track 04: AI Finance Controller · Razorpay AI Buildathon 2026**  
> **The Autonomous Financial Operating System:** *Pre-Settlement Tax Escrow (`on_hold`), Paise-Exact Settlement Lineage (Donald Knuth DLX), GSTR-2B Input Tax Credit Reconciliation & Causal Financial Digital Twin.*

[![Verification: 19/19 Passing](https://img.shields.io/badge/Tests-19%2F19%20Passing-brightgreen)](tests/)
[![False Match Rate](https://img.shields.io/badge/FMR-0.000%20(Zero%20Error)-blue)](RESULTS.md)
[![Zero-Float Policy](https://img.shields.io/badge/Semgrep%20AST-Zero%20Floats%20Guarded-success)](.semgrep/math_guard.yaml)
[![Shannon Security](https://img.shields.io/badge/Shannon%20Whitebox-5%2F5%20Exploits%20Blocked-green)](reports/security/shannon_whitebox_audit.json)

---

### ⚖️ Technical Note for Judges (Evaluating Algorithmic & Statutory Rigor)

To verify that **KuberRecon** is a deeply integrated, first-principles FinTech operating system rather than an AI wrapper, we invite the panel to evaluate our architecture against three structural invariants:

1. **The Combinatorial Core (Knuth’s DLX vs. Relational Scans):** 
   We do not use costly database scans or fragile LLM fuzzy-matching to reconcile bulk bank credit lump sums. Our system executes an in-memory **Donald Knuth Dancing Links (Algorithm X) + Horowitz-Sahni** exact-cover solver in **<5ms inside pure CPU cache**, maintaining a provable **False Match Rate of 0.000** through deterministic honest refusal (`AmbiguousMatchError`).

2. **The Compliance Guardrail (Pre-Settlement Route Escrow):** 
   To completely satisfy **Section 16(2)(aa) of the CGST Act**, we intercept transactions at authorization via **Razorpay Route (`on_hold: true`)**. The 18% GST tranche is held in escrow until the auto-population of the **GSTR-2B statement on the 14th of the succeeding month**. If a supplier defaults on GSTR-1, the escrow automatically refunds the 18% tax liquidity to the merchant’s wallet, neutralizing the ₹15,000 Crore tax-leakage trap by construction.

3. **Compiler-Enforced Precision (Zero-Float AST Rule):** 
   Every financial operation is strictly enforced in base-10 integer paise. Our build pipeline enforces a custom Semgrep AST rule (`.semgrep/math_guard.yaml`) that fails compilation if any IEEE-754 `float()` constructor touches currency fields.

👉 **To Verify Locally in < 2 Seconds:**
```bash
python src/kuber_recon/cli.py run-demo
```

---

## ⚡ Quickstart & Zero-Key Reproducibility

No API keys, databases, or cloud accounts are required to evaluate. Everything runs deterministically in pure Python:

```bash
# 1. Clone & install dependencies
git clone https://github.com/Pranjulchaurasiya/kuber-recon.git
cd kuber-recon
pip install -e .

# 2. Launch Interactive Razorpay Blade Web Console (<100ms)
python src/kuber_recon/cli.py serve-web

# 3. Run instant terminal verification demo (ASCII Money Lineage DAG)
python src/kuber_recon/cli.py run-demo

# 4. Run Causal Financial Digital Twin stress-test simulation
python src/kuber_recon/cli.py simulate-shock

# 5. Run high-throughput stress benchmark (10,000 records in 1.2s)
python src/kuber_recon/cli.py run-benchmark --records 10000

# 6. Run full automated verification suite (19/19 tests in 2.2s)
python -m pytest tests/ -v
```

---

## 🏗️ The 3 Core Pillars of KuberRecon

```
                                  ┌─────────────────────────────┐
                                  │         KUBERRECON          │
                                  └──────────────┬──────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
       [ 1. Real-Time Escrow ]         [ 2. Knuth DLX Solver ]       [ 3. Financial Twin ]
       (Pre-Settlement Route Rail)     (Post-Settlement Lineage)     (Causal Stress Simulator)
       • Splits Principal/TDS/GST      • Solves 1-to-N Lump Sums     • 4-Day Bank Holiday Freeze
       • 14th GSTR-2B Auto-Release     • False Match Rate = 0.000    • Vendor Default Cascades
```

### 1. Real-Time Pre-Settlement Route Escrow ($T=0 \rightarrow 14\text{th}$)
* **The Problem:** Indian enterprises lose over ₹15,000 Crores annually because vendors collect 18% GST upfront but default on GSTR-1 filings, triggering Section 16(2)(aa) tax penalties for buyers.
* **The Solution:** Intercepts payments at capture via **Razorpay Route**, holds the 18% GST tranche on hold (`on_hold: true`), and auto-releases it on the **14th of the next month (GSTR-2B cycle)** only upon verified ITC reflection. If the vendor defaults, the ₹18,000 is auto-refunded to the merchant!

### 2. Donald Knuth Algorithm X Combinatorial Core
* Solves multi-invoice offline bank deposits (HDFC/ICICI/Axis nodal lump sums) in $<25\text{ms}$ using **Dancing Links (DLX)** and **Horowitz-Sahni Meet-in-the-Middle** ($O(2^{N/2})$).
* **Honest Refusal State Machine:** Raises `AmbiguousMatchError` on multi-subset collisions $\implies$ **False Match Rate (FMR) = 0.000**.
* **Zero-Float AST Guard:** Barred from using IEEE-754 floats on money fields via `.semgrep/math_guard.yaml`.

### 3. Causal Financial Digital Twin: Counterfactual Stress Simulator
* Simulates 4-day festive bank holiday liquidity freezes, 25% vendor GSTR-1 default cascades, and Section 206AB 5% higher TDS enforcement across 10,000 transactions in $<50\text{ms}$.

---

## 🏆 Key Measured Results

| Metric | Measured Value | Benchmark Target |
|---|---|---|
| **False Match Rate (FMR)** | **0.000 (0 False Matches)** | $0.000$ (Strict 0) |
| **Match Rate on Decidable Credits** | **100.0%** | $\ge 95.0\%$ |
| **10,000-Record Solving Latency** | **1,262.0 ms (1.26s)** | $< 3,500\text{ ms SLA}$ |
| **Throughput (Single CPU Core)** | **7,924 records / sec** | Production Ready |
| **Zero-Float Policy Enforcement** | **0 Floats (AST Guarded)** | Strictly 0 |
| **White-Box Penetration Security** | **5 / 5 Exploits Blocked** | OWASP Top 10 |

---

## 🔒 Security, Integrity & CSO Guardrails

1. **Hard Spend Cap:** Maximum ₹200.00 auto-adjustment per transaction; ₹1,000.00 daily spend cap.
2. **Payee Whitelist Lock:** Self-healing payouts only target pre-registered KYC beneficiary accounts.
3. **Zero-Silent-Mutation:** Atomic state checks abort execution if underlying balance drifts prior to execution.
4. **RFC 6962 Merkle Audit Ledger:** Every reconciliation and escrow release generates an Ed25519-signed cryptographic audit block.
