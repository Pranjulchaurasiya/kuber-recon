# KuberRecon — Presenter Demo Playbook (Self-Recording Guide)

> **Goal:** Record a winning, professional, truth-calibrated **4:30 – 4:55 minute** live screen recording for **Razorpay AI Buildathon Track 04** (AI Finance Controller).

---

## 🛠️ 1. Quick Setup & Pre-Flight (1 Minute)

### A. Confirm Both Servers are Live
Both servers are already running in the background:
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Assurance Console:** [http://localhost:3000/console](http://localhost:3000/console)
- **Backend API:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### B. Pre-Open These 4 Browser Tabs
Before starting your recording, open these 4 tabs in Chrome / Edge so you can switch between them smoothly:
1. **Tab 1:** `http://localhost:3000` (Home Landing Page)
2. **Tab 2:** `http://localhost:3000/console` (Assurance Console)
3. **Tab 3:** `file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/scratch/viewer_benchmark.html` (Benchmark Viewer)
4. **Tab 4:** `file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/scratch/viewer_architecture.html` (Architecture Matrix)

### C. Screen Recorder Settings
- **Software:** OBS Studio, Windows Game Bar (`Win + Alt + R`), or Loom.
- **Resolution:** 1080p (1920×1080), Full Screen Browser (press `F11` if you want clean borderless recording).
- **Target Time:** Between **4:30 and 4:55** (Razorpay strictly caps submissions at 5:00 max).

---

## 🗣️ 2. Scene-by-Scene Presenter Script & Click Action Guide

---

### Scene 1: Problem & Central Thesis (0:00 – 0:20 | 20s)
* **Browser Tab:** **Tab 1** (`http://localhost:3000`)
* **Mouse Action:** Start at the top hero section. Hover over the headline *"AI transactions move fast. Settlement must never be blind."*

> **What to Say:**  
> *"Hi everyone, I'm presenting KuberRecon for Razorpay AI Buildathon Track 04 — AI Finance Controller & Settlement OS.*  
> *Finance teams spend hours reconciling high-volume bank credits against invoices. But in financial systems, an incorrect automated match is far worse than an exception.*  
> *KuberRecon is built on a strict, non-negotiable principle: match what you can mathematically prove, refuse what is ambiguous, and account for every single paise."*

---

### Scene 2: Console Tour & Sandbox Boundary (0:20 – 0:40 | 20s)
* **Browser Tab:** Switch to **Tab 2** (`http://localhost:3000/console`)
* **Mouse Action:** Point cursor at the top-right badge `SANDBOX / SYNTHETIC FIXTURES`, then hover over the top metric cards (Gross Verified GMV, Active Escrow Holds).

> **What to Say:**  
> *"Here on the Assurance Console, we see our live finance-control dashboard.*  
> *Notice the persistent badge at top-right: all data demonstrated today runs on committed synthetic fixtures in sandbox simulation mode. Live Razorpay provider onboarding remains future work.*  
> *Our dual-entry engine ensures that gross settlements and escrow balances maintain zero unexplained paise drift."*

---

### Scene 3: 100+ Txn Clustered Batch Reconciliation (0:40 – 1:35 | 55s)
* **Browser Tab:** **Tab 2** (`/console`), on the **`Judge Control Panel (5 Invariants)`** tab.
* **Mouse Action:** Move pointer to **Card 1: `1. Clustered MITM Batch (100 Txns)`**. Click the **`Run Test`** button. Watch the test execute in ~100ms and display results.

> **What to Say:**  
> *"Track 04 requires proving a complete finance-operations control loop over a non-cherry-picked batch, with measured accuracy and visible exceptions.*  
> *Let's trigger Card 1: our 100+ transaction clustered batch test.*  
> *(Click Run Test)*  
> *Under the hood, our engine partitions the batch and runs our Meet-in-the-Middle subset-sum solver.*  
> *In under 100 milliseconds, it processed 125 records: 20 exact matches auto-resolved totaling ₹2.66 lakhs, with 1 held exception of ₹1,485.*  
> *Notice the accounting invariant: zero unexplained paise delta, and zero false matches on this committed corpus."*

---

### Scene 4: Ambiguity Refusal — The Moat (1:35 – 2:20 | 45s)
* **Browser Tab:** **Tab 2** (`/console`), still on **`Judge Control Panel`**.
* **Mouse Action:** Move to **Card 2: `2. Multi-Cluster Ambiguity Refusal`**. Click **`Run Test`**. Show the amber card output and the quarantined status.

> **What to Say:**  
> *"Now let's examine what happens when multiple valid invoice subsets equal the exact same bank credit — in this scenario, two different combinations equal ₹1,00,000.*  
> *(Click Run Test)*  
> *A naive or greedy matcher might pick one arbitrarily, creating a catastrophic false match and misrouting funds.*  
> *KuberRecon detects this multi-subset collision, halts with an AmbiguousMatchError, and routes both subsets to human review.*  
> *This is our defensive moat: financial uncertainty is never silently converted into automated money movement."*

---

### Scene 5: Security Proof & Spoof Rejection (2:20 – 3:00 | 40s)
* **Browser Tab:** **Tab 2** (`/console`), click the **`Security Proof & Attack Matrix (9 Vectors)`** tab.
* **Mouse Action:** Click the orange **`Run All 9 Vectors`** button (or click Card 2 `Forged API Key` and Card 6 `Tampered Webhook HMAC`). Hover over Card 2 (401) and Card 6 (400).

> **What to Say:**  
> *"Next, let's look at the security perimeter. Here we have a live 9-vector adversarial attack suite.*  
> *(Click Run All 9 Vectors)*  
> *Notice how every vector is blocked deterministically: forged merchant API keys fail with HTTP 401, and tampered webhook HMAC signatures fail with HTTP 400.*  
> *Crucially, release evidence is strictly server-controlled: if an attacker attempts to inject client-supplied provider records into the release request, our API schema rejects it with HTTP 422 before business logic can ever touch the hold."*

---

### Scene 6: Controlled Assurance Lifecycle & Evidence (3:00 – 3:45 | 45s)
* **Browser Tab:** **Tab 2** (`/console`), click the **`Assurance Lifecycle (3-Stage Demo)`** tab.
* **Mouse Action:** Click **`🚀 Run Automated Golden Flow`**. Watch the progress bar move across `HELD` -> `VERIFYING` -> `RELEASING` -> `RELEASED`. Then click the **`Decision Evidence`** drawer button to reveal the cryptographic proofs.

> **What to Say:**  
> *"Here is the contract assurance lifecycle gating merchant releases.*  
> *(Click Run Automated Golden Flow)*  
> *Watch the compare-and-swap state machine: HELD, VERIFYING, RELEASING, and RELEASED.*  
> *Let's inspect the Decision Evidence drawer.*  
> *(Open Decision Evidence)*  
> *Every state change requires immutable cryptographic proof: SHA-256 delivery assertions, Ed25519 seller signatures, and server-verified webhook provider records.*  
> *The payment rails here are sandbox fixtures; the verified state machine is what ensures zero premature releases."*

---

### Scene 7: Committed Benchmark & Reproducibility (3:45 – 4:15 | 30s)
* **Browser Tab:** Switch to **Tab 3** (`viewer_benchmark.html`).
* **Mouse Action:** Hover across the 4 top summary cards (3 Batches, 0 False Matches, 0 Paise Delta, 100% Quarantined) and scroll slightly through the table.

> **What to Say:**  
> *"Track 04 demands transparent metrics over marketing claims. Here is our project evaluation benchmark aligned to Track 04.*  
> *We evaluated 3 committed synthetic batches with fixed random seeds: Clean with 125 records, Messy with 239 records, and Adversarial with 460 records — totaling 824 records.*  
> *Across all 3 batches, the result is consistent: 0 observed false auto-matches, zero unexplained paise drift, and 100% of ambiguous collisions quarantined rather than guessed."*

---

### Scene 8: Architectural Honesty & Boundary Matrix (4:15 – 4:45 | 30s)
* **Browser Tab:** Switch to **Tab 4** (`viewer_architecture.html`).
* **Mouse Action:** Hover over the 3 tiers: Tier 1 (Green), Tier 2 (Yellow), Tier 3 (Blue).

> **What to Say:**  
> *"To maintain complete architectural honesty, we document our system boundaries across 3 distinct tiers:*  
> *Tier 1 is our Core Financial Kernel — base-10 integer paise arithmetic, Horowitz-Sahni subset-sum solver, and Ed25519 verification — fully implemented and proven across 275 automated tests.*  
> *Tier 2 is our Sandbox Prototype using local SQLite WAL and webhook simulation.*  
> *Tier 3 — live Razorpay linked account onboarding, AWS KMS key custody, and distributed locks — represents future production work."*

---

### Scene 9: Closing & Wrap-Up (4:45 – 4:55 | 10s)
* **Browser Tab:** Switch back to **Tab 1** (`http://localhost:3000`).
* **Mouse Action:** Rest cursor cleanly on the right margin.

> **What to Say:**  
> *"In summary: KuberRecon does not pretend every settlement can be automated. It proves when automation is mathematically justified, and keeps uncertainty visible when it is not.*  
> *Thank you!"*

---

## ⚠️ 3. Truth Boundaries & Vocabulary Cheatsheet

Keep this checklist in front of you while speaking to ensure 100% compliance with Track 04 judging criteria:

| ❌ NEVER SAY THIS | ✅ SAY THIS INSTEAD |
| :--- | :--- |
| "This is 100% production-ready." | *"This is a sandbox-verified Track 04 prototype."* |
| "Official Razorpay benchmark." | *"Project evaluation benchmark aligned to Track 04."* |
| "Guaranteed zero false matches everywhere." | *"0 observed false auto-matches on the committed synthetic corpus; ambiguity is refused."* |
| "Zero errors or zero unlinked transactions." | *"0 unexplained paise within the accounting model; exceptions are held for review."* |
| "Authoritative bank settlement date." | *"Sandbox event-date validation."* |
| "Connected live to real banking partners." | *"Live Razorpay linked account onboarding remains future work."* |

---

## 🚀 4. You Are Ready!
1. Pre-open the 4 tabs.
2. Start your recording.
3. Follow the 9 scenes above at a steady, confident pace.
4. Stop recording around **4:45 – 4:50**.
5. Your submission will be clear, honest, technically authoritative, and aligned with Track 04!
