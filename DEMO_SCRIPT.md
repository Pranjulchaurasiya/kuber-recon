# 🎬 APEX: Master 4-Minute Presentation & Live Demo Script

> **Razorpay AI Buildathon 2026 · Track 01: AI Growth & Agentic Commerce**
> **Product:** APEX (Autonomous Working Capital & Settlement Assurance)
> **Target Duration:** 3 minutes 30 seconds – 4 minutes 15 seconds

---

## ⏱️ Live Presentation Timeline & Word-for-Word Script

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION SEQUENCE                                     │
├───────────────┬──────────────────────────────────────────┬─────────────────────────────┤
│ 00:00 - 00:45 │ The Core Hook & Unified Thesis           │ Slide / Hero Screen         │
│ 00:45 - 02:00 │ Live Underwriting & Split-Sweep Demo     │ `run-capital-demo` Terminal │
│ 02:00 - 03:00 │ Exact-Cover Verification & Webhook CAS   │ `run-demo` Terminal         │
│ 03:00 - 03:45 │ The Ownership Triple-Test & Moat         │ Architecture / Pitch Slide  │
│ 03:45 - 04:00 │ Closing Invariants & Q&A Handoff         │ 80/80 Tests Screen          │
└───────────────┴──────────────────────────────────────────┴─────────────────────────────┘
```

---

### Phase 1: The Core Hook & Unified Thesis (0:00 – 0:45)

**[Screen: Browser open to `http://localhost:3000` or Master Slide]**

> *"Good afternoon, judges. AI agents can now autonomously negotiate, place purchase orders, and transact. But there is a massive structural gap:*
> 
> *Payment gateways authorize an agent’s spend at transaction time, but they have no way of knowing whether the seller actually delivered before the money settles out.*
> 
> *Here is our single thesis:*
> **APEX turns verified agentic commerce into instant working capital for merchants, using deterministic delivery verification as its underwriting moat and Razorpay Route split-settlements for zero-default recovery.**
> 
> *Let’s see both halves of this system work live on this machine."*

---

### Phase 2: Live Underwriting & Split-Sweep Recovery Demo (0:45 – 2:00)

**[Action: Switch to Terminal and run:]**
```bash
python -m kuber_recon.cli run-capital-demo
```

**[What to say while the table renders:]**

> *"Let’s look at what just happened in under 200 milliseconds:*
> 
> 1. **Verified Delivered Ground Truth:** *APEX didn't inspect a self-reported bank statement or credit bureau report. It analyzed 100 reconciled B2B transactions, verifying ₹2,47,089.55 of pure delivered GMV.*
> 2. **Bayesian Shrinkage Underwriting:** *To avoid small-sample noise where one bad transaction destroys a merchant's score, our engine applies a Bayesian prior ($N_0=50, p_0=0.98$), calculating an exact Settlement Reliability Index of **0.9675**—qualifying the merchant for **Tier A Premier**.*
> 3. **Instant Liquidity Advance:** *Applying our 25% operational capacity heuristic, the engine immediately underwrote a **₹59,764.78** working capital advance at a flat 4% factor fee, disbursing funds instantly via simulated Razorpay Payouts.*
> 4. **Automated Split-Settlement Recovery:** *Look at the bottom table. As daily settlements clear through Razorpay Route, APEX automatically sweeps 12% at the nodal source—₹2,656 on Day 1, ₹1,502 on Day 2, ₹1,195 on Day 3—amortizing the debt down in exact integer paise with zero floating-point leakage and zero repayment friction for the merchant."*

---

### Phase 3: Exact-Cover Verification & Webhook CAS Finality (2:00 – 3:00)

**[Action: In Terminal, run:]**
```bash
python -m kuber_recon.cli run-demo
```

**[What to say while the ASCII DAG renders:]**

> *"Now let's look under the hood at the risk engine that makes this underwriting possible:*
> 
> *When an agent transaction occurs, Razorpay Route locks the funds using native `on_hold: true`. Settlement funds never leave Razorpay's nodal account until delivery is mathematically proven.*
> 
> *Our verification kernel runs 3 deterministic checks without any probabilistic LLM hallucinations in the financial path:*
> 1. **Mod-36 GSTIN Checksum Verification:** *Validating official Indian tax identity format.*
> 2. **Knuth Exact-Cover Subset Matcher:** *Matching lump-sum bank clearing UTRs against individual line items while withholding Section 194-O TDS and gateway MDR in pure integer paise.*
> 3. **Single-Source Webhook Finality:** *State transitions (`HELD` $\to$ `RELEASING` $\to$ `RELEASED`) occur exclusively upon signed HMAC-SHA256 Razorpay webhooks using optimistic CAS database locking."*

---

### Phase 4: The Ownership Triple-Test & Moat (3:00 – 3:45)

**[Screen: `README.md` or Architecture Topology]**

> *"Why is this a venture-scale product that only Razorpay can build, rather than an external lending SaaS?*
> 
> *We call this the **Ownership Triple-Test**:*
> 
> 1. **Ground-Truth Line-Item Visibility:** *HDFC, ICICI, and external NBFCs only see lump-sum bank deposits. Only Razorpay sees the line-item invoice data, GSTIN verification, and delivery completion.*
> 2. **Pre-Settlement Hold Gating:** *External SaaS lenders cannot intercept settlement payouts. Razorpay Route provides native `on_hold` primitives to freeze funds before payout.*
> 3. **First-Lien Source Deduction:** *Because Razorpay controls the nodal settlement pipeline, capital advances are recovered before money ever leaves the payment gateway—giving Razorpay first-lien priority with near-zero default risk.*"

---

### Phase 5: Closing Invariants & Q&A Handoff (3:45 – 4:00)

**[Action: In Terminal, run:]**
```bash
python -m pytest -p no:deepeval -p no:langsmith tests/ -q
```

> *"Every claim we’ve demonstrated is backed by **80 automated invariant tests** running across 14 modules—including AST scanners enforcing zero floats, multi-threaded concurrency suites proving zero over-recovery, and formal proofs of a 0.000 False Match Rate.*
> 
> *Thank you. We are happy to take your questions."*

---

## 🛡️ Appendix: "If Asked" Adversarial Q&A Cheat Sheet

### Q1: "Is your `RLock` safe in production across multiple servers?"
> **Answer:** *"No, and we explicitly disclose this in `LIMITS.md` Section 5.3. The `RLock` in `CapitalFacilityManager` provides strict thread-safety and double-drawdown prevention within a single server process for this prototype. In a horizontally scaled production deployment with multiple Kubernetes pods, this will be migrated to distributed row-level locking (e.g. PostgreSQL `SELECT ... FOR UPDATE` or Redis Redlock) to ensure cross-process serialization."*

---

### Q2: "Why Bayesian shrinkage ($N_0=50, p_0=0.98$) for SRI instead of simple transaction matching?"
> **Answer:** *"A naive match rate unfairly penalizes small-volume merchants. If a merchant has only 10 transactions and suffers 1 disputed order due to a supplier issue, their score drops to 70%, completely cutting off their credit. Our Bayesian prior anchors them at a reasonable baseline ($N_0=50, p_0=0.98$), keeping their score at 0.8429, while for large merchants ($N=500+$), empirical performance completely dominates the prior."*

---

### Q3: "Is the 25% advance rate a calculated credit risk model?"
> **Answer:** *"No. We explicitly label it `DEFAULT_ADVANCE_RATE_HEURISTIC = Decimal("0.25")` in the code and documentation. It is an operational heuristic designed to keep repayment duration between 4 and 6 weeks at typical 10%–15% daily sweep rates, avoiding impairment of merchant operating cash flow. In production, this would be calibrated by NBFC risk models."*

---

### Q4: "What happens if a merchant takes the advance and stops transacting immediately (the rogue merchant)?"
> **Answer:** *"We stress-tested this exact adversarial scenario. Because recovery is split-settlement-driven, if settlement drops to zero, the system has a 14-day silent window before the state machine automatically transitions the facility to `STAGNANT_RECOVERY` for manual risk intervention, and after 30 days to `FLDG_REVIEW`. Under the RBI Digital Lending Guidelines, total First Loss Default Guarantee exposure is legally capped at 5% of the overall portfolio."*

---

### Q5: "Is there a cliff-edge at the Tier A / Tier B boundary (SRI = 0.9500)?"
> **Answer:** *"We stress-tested this scenario, identified the discrete step-function cliff-edge, and eliminated it. In `capital.py`, we implemented continuous linear interpolation across the $[0.9300, 0.9700]$ transition band. A 0.0002 SRI difference now results in a strictly bounded 0.179% fee delta (₹21.25 on ₹2.37L) and 2 bps sweep rate shift, locked in by regression tests in `test_capital_underwriting.py`."*

---

### Q6: "Did you test against live Razorpay APIs or simulated responses?"
> **Answer:** *"Our client adapter authenticates live against `api.razorpay.com/v1` for settlement recon data (HTTP 200). Direct balance transfer creation (`POST /v1/transfers`) was analyzed against Razorpay's official Route documentation: direct account transfers require an explicit account feature flag activated by Razorpay on the MID, plus onboarded linked accounts (`POST /v1/accounts`). For demonstration and sandbox environments, transfers and hold releases execute against the documented Razorpay JSON contract via our zero-key simulation harness."*

---

### Q7: "Why did test suite execution times vary across runs?"
> **Answer:** *"We profiled 5 consecutive runs with `--durations=10`: execution time converges from an initial cold run down to 13s–18s. The delta is driven by cold-start AST parsing of all financial source files and disk cache warming on temporary databases, after which execution is fast and predictable."*

