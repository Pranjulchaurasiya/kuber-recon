# KuberRecon — Track 04 Demo Video QA Report

**Product:** KuberRecon (Autonomous AI Finance Controller & Settlement Assurance)  
**Track:** Razorpay AI Buildathon 2026 · Track 04 (AI Finance Controller)  
**Video File:** [`reports/kuber_recon_track04_demo.mp4`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/reports/kuber_recon_track04_demo.mp4)  
**Generated At:** 2026-09-04 03:47:50 UTC+05:30  

---

## 1. Executive Summary & Thesis Statement

> **Master Thesis:**  
> *"KuberRecon is a sandbox-verified Track 04 finance-control prototype. It reconciles synthetic multi-source batches with paise-exact arithmetic, refuses ambiguous matches, accounts for every paise as reconciled or exception-held, and demonstrates server-side release controls. Live Razorpay provider onboarding and production infrastructure remain future work."*

The produced demo video delivers a strict, non-promotional, evidence-backed proof of a complete finance-operations control loop across a 100+ record synthetic batch on a live running application (`http://localhost:3000` & `http://127.0.0.1:8000`), with visible metrics, ambiguity refusal, security attack vector defense, and a sandbox-controlled contract release lifecycle.

---

## 2. Video Technical Specifications

| Specification | Target / Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Duration** | 4:40 – 5:00 (280s – 300s) | **00:04:54.04 (294.04s)** | **PASS** |
| **Resolution** | 1920×1080 (Full HD, 16:9) | **1920×1080 [SAR 1:1, DAR 16:9]** | **PASS** |
| **Frame Rate** | 30 fps minimum | **30.00 fps progressive** | **PASS** |
| **Video Codec** | H.264 (AVC) | **h264 (High) (avc1), yuv420p, 960 kb/s** | **PASS** |
| **Audio Voice Track** | Indic English Voice / Intelligible | **Indian English Neural Voice (en-IN), AAC mono 24000 Hz, 56 kb/s** | **PASS** |
| **Subtitles** | Small, non-intrusive bottom text | **Burnt-in Libass Subtitles (FontSize=7.5, MarginV=8, bottom-center)** | **PASS** |
| **File Size** | Restrained (< 100 MB) | **35.85 MB (37,594,972 bytes)** | **PASS** |
| **Container** | MP4 | **ISO/IEC 14496-14 (isom/iso2/avc1/mp41)** | **PASS** |

---

## 3. Storyboard & Timestamp Alignment

| Timeline | Scene / Segment | Route / Visual Surface | Measured Duration | Visual Proof & Actions |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 – 0:16** | **Segment 1: Opening & Central Thesis** | `http://localhost:3000` | 16.00s | Hero overview, lower-third title card, persistent `SANDBOX / SYNTHETIC FIXTURES` badge. Indic speech introduces thesis; small subtitle appears at bottom border. |
| **0:16 – 0:36** | **Segment 2: Problem & Promise** | `http://localhost:3000/console` | 20.00s | Multi-source settlement radar, gross verified GMV, active escrow holds, 0 unexplained paise drift. Subtitle clarifies Track 04 synthetic fixture scope. |
| **0:36 – 1:31** | **Segment 3: 100+ Record Synthetic Batch** | `http://localhost:3000/console` (Judge Tab) | 55.00s | Clicks `Run Test` on Card 1 (`1. Clustered MITM Batch (100 Txns)`). Live API resolves 125 records: 20 matches, 1 exception (₹1,485.00), **0 unexplained delta**, **0 false matches**. Subtitles sit safely below cards. |
| **1:31 – 2:16** | **Segment 4: Ambiguity Refusal (Moat)** | `http://localhost:3000/console` (Judge Tab) | 45.00s | Clicks `Run Test` on Card 2 (`2. Multi-Cluster Ambiguity Refusal`). Panel renders 2 valid candidate subsets for ₹1,00,000 credit; halts with `AmbiguousMatchError`; 100% quarantined to review. |
| **2:16 – 2:54** | **Segment 5: Security Proof & Spoof Rejection** | `http://localhost:3000/console` (Security Tab) | 38.00s | Executes `2. Forged Merchant API Key` (HTTP 401) and `6. Tampered Webhook HMAC` (HTTP 400). Proves client-supplied `provider_records` rejection (HTTP 422) with contract hold intact. |
| **2:54 – 3:39** | **Segment 6: Controlled Release Path** | `http://localhost:3000/console` (Assurance Tab) | 45.00s | Clicks `🚀 Run Automated Golden Flow`. Observes 6-stage lifecycle (`HELD` -> `VERIFYING` -> `RELEASING` -> `RELEASED`). Opens `Decision Evidence` drawer showing SHA-256 and Ed25519 signature. |
| **3:39 – 4:14** | **Segment 7: Committed Benchmark & Reproducibility** | `scratch/viewer_benchmark.html` | 35.00s | Displays committed Track 04 evaluation benchmark table: Clean (100), Messy (250), Adversarial (500). 0 observed false matches across all 3 batches. Subtitles rest under summary table. |
| **4:14 – 4:40** | **Segment 8: Architectural Honesty & Limits** | `scratch/viewer_architecture.html` | 26.00s | Displays 3-Tier Architecture Boundary Matrix: Core Kernel (Software), Sandbox Prototype (SQLite WAL), Production Infrastructure (Future Work). Subtitle rests below Directives card. |
| **4:40 – 4:54** | **Segment 9: Closing & Wrap-Up** | `http://localhost:3000` | 14.04s | Final system wrap-up, lower-third title card, and clean fade to black at 4:54. |

---

## 4. Ground-Truth Data & Invariant Verification

### A. Test Suite Preflight
- **Command:** `python -m pytest tests/test_narration_release_guard_e2e.py -v`
- **Result:** **11 passed in 9.34s (100%)**
- **Full Invariant Suite:** **275 passed (0 failures)**

### B. Project Evaluation Benchmark (Aligned to Track 04)
- **Command:** `python scripts/run_track04_evaluation_benchmark.py`
- **Result:**
  * **Clean Batch (Seed 1001, Target 100):** Ingested 125, Credits 21, Matches 20, Auto-Resolved ₹2,66,675.17, Exceptions ₹1,485.00, **0 unexplained paise**, **0 observed false matches**, Throughput 7,503 rec/s.
  * **Messy Batch (Seed 2002, Target 250):** Ingested 239, Credits 35, Matches 24, Auto-Resolved ₹3,94,139.45, Exceptions ₹1,77,573.46, **0 unexplained paise**, **0 observed false matches**, Throughput 29,020 rec/s.
  * **Adversarial Batch (Seed 3003, Target 500):** Ingested 460, Credits 74, Matches 63, Auto-Resolved ₹9,39,877.89, Exceptions ₹18,985.00, **0 unexplained paise**, **0 observed false matches**, Throughput 12,410 rec/s.

### C. Live Signed Webhook Provenance & Release Gate
- **Command:** `python scripts/verify_live_control_loop.py`
- **Result:** **6/6 Verification Steps Passed**
  1. Contract created (`apex_cnt_1668979`, ₹25,000.00).
  2. Seller Ed25519 payload delivered and verified.
  3. Client `provider_records` exploit attempt rejected with **HTTP 422**.
  4. Missing server provider record fails closed with **HTTP 412**.
  5. Authentic HMAC-SHA256 signed webhook ingested with fresh timestamp (`signature_verified: True`).
  6. 5-point provider join release verified (`status: RELEASING`, statement date parsed from payload).

---

## 5. Cursor & Visual Subtitle Presentation QA

- **Cursor Type:** White pointer with `#0F172A` outline (`26px`, ~130% standard scale) with CSS cubic easeInOut transitions.
- **Click Indicator:** Single cyan ripple (`28px -> 42px`, `0.35s` fade-out). No click ripples exceed 0.4s.
- **Pointer Parking:** Moves smoothly and parks at `(1860, y)` on the right margin, ensuring zero text or metric obstruction.
- **Subtitle Layout & Positioning:**
  * **Font Size:** `FontSize=7.5` (compact, high-clarity typography).
  * **Color & Style:** Pure white text (`#FFFFFF`) with thin black outline (`Outline=0.8`, `Shadow=0.5`).
  * **Placement:** Bottom center with `MarginV=8` — rests directly against the bottom edge bezel.
  * **Content Protection:** Subtitles sit completely below interactive cards, data tables, telemetry logs, and metric badges. Zero card or data obstruction verified across all 9 segments.
- **Frame-by-Frame QA Inspection:**
  Extracted and visually reviewed frames in `reports/qa_frames_subtitled/` across all 9 scenes (`01_opening_thesis.png` through `09_closing_wrapup.png`). All 9 frames show zero overlap with interactive elements or tabular financial metrics.

---

## 6. Truth Boundaries & Compliance Audit

| Requirement / Boundary | Verification Finding |
| :--- | :--- |
| **No Forbidden Terms** | Searched narration and visual cards: zero occurrences of "production-ready", "bank-grade", "official Razorpay benchmark", "guaranteed zero false matches", "100% secure". |
| **Calibrated Phrasing Used** | Confirmed presence of: *"0 observed false auto-matches on the committed synthetic corpus; ambiguity is refused."* and *"0 unexplained paise within the corpus accounting model, including explicitly classified exceptions."* |
| **Sandbox Transparency** | Persistent badge visible across entire video: `SANDBOX / SYNTHETIC FIXTURES`. Header labels: `Storage: SQLite (WAL Mode)` and `Mode: SANDBOX_SIMULATION`. |
| **Privacy & Credential Hygiene** | Zero real credentials, absolute file paths, or private secrets exposed. Merchant ID displayed as `merchant_rzp_primary`. |

---

## 7. Final Artifacts

1. **Master Demo MP4 (Indic Voice + Small Bottom Subtitles):**  
   [`reports/kuber_recon_track04_demo.mp4`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/reports/kuber_recon_track04_demo.mp4)  
   *(1920×1080 · 30 fps · 04:54.04 · 35.85 MB)*
2. **Subtitled QA Inspection Frames:**  
   [`reports/qa_frames_subtitled/`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/reports/qa_frames_subtitled/)
3. **Master Subtitle Track (SRT):**  
   [`artifacts/video_production/indic_subtitles.srt`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/artifacts/video_production/indic_subtitles.srt)
4. **Track 04 Evaluation Benchmark Report:**  
   [`reports/track04_evaluation_benchmark.md`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/reports/track04_evaluation_benchmark.md)
5. **Video Assembly & Subtitle Production Script:**  
   [`scripts/build_indic_subtitled_video.py`](file:///c:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon/scripts/build_indic_subtitled_video.py)
