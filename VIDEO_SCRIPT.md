# KuberRecon: Agentic Assurance & Settlement Video Script
**Target Duration:** 90 Seconds
**Core Hook:** "Agentic commerce cannot scale if agents spend money but sellers can’t prove they delivered. We fixed financial truth for agents using Razorpay Route."

---

### [0:00 - 0:10] The Hook (Talking Head / Slides)
**Speaker:**
"AI agents are authorized to spend money, but the financial rails aren't ready. If an agent buys 500 B2B leads, how does the seller prove they actually delivered before they get paid? 
Today, we are solving the Delivery-Gated Settlement problem for agentic commerce using KuberRecon and Razorpay Route."

### [0:10 - 0:25] The Setup (Screen Recording: APEX Console)
**Action:** Show the KuberRecon APEX Console. Click **"Initialize Agent Contract"**.
**Speaker:**
"When a buyer agent initiates a purchase, we immediately lock the funds using Razorpay Route. The money is secured on a 'hold' state. The seller agent knows they will get paid—but *only* if they prove delivery deterministically."

### [0:25 - 0:50] Scenario A: The Refusal (Screen Recording: Trigger Corrupted Delivery)
**Action:** Click **"Scenario A: Malicious / Corrupted Delivery"**.
**Speaker:**
"Here, the seller agent tries to submit hallucinated or corrupted data—like invalid GSTINs. Our Assertion Kernel catches it instantly. It issues an honest refusal. The Razorpay Route hold remains active, protecting the buyer's ₹25,000 from being settled to a bad actor."

### [0:50 - 1:15] Scenario B: The Release (Screen Recording: Trigger 100% Clean Delivery)
**Action:** Click **"Scenario B: 100% Verified Clean Delivery"**.
**Speaker:**
"Now, the seller agent submits the correct, 100% verified payload. The Mod-36 GSTIN checksums and contract financial totals match to the exact paise.
The authorized CFO verifier signs the canonical assertion payload using RFC 8032 Ed25519. The backend verifies the signature against pinned public keys, executes an atomic CAS state transition to RELEASING, and triggers Razorpay Route hold release."

### [1:15 - 1:30] The Finale (Screen Recording: Webhook & Close)
**Action:** Click **"Execute Settlement Release"**. Show the live logs and single authoritative webhook confirmation.
**Speaker:**
"We wait for Razorpay's exact `transfer.processed` webhook with HMAC verification to finalize the state to RELEASED. No race conditions. Zero float leakage. The seller gets paid.
We didn't just build a wrapper; we built deterministic financial truth for agentic commerce on Razorpay Route."
