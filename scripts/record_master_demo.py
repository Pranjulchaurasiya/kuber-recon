import os
import sys
import time
import wave
import contextlib
import subprocess
from pathlib import Path
import pyttsx3
from playwright.sync_api import sync_playwright

BASE_DIR = Path("C:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon")
WORK_DIR = BASE_DIR / "artifacts" / "video_production"
SEG_RAW_DIR = WORK_DIR / "raw"
SEG_AUDIO_DIR = WORK_DIR / "audio"
SEG_SYNC_DIR = WORK_DIR / "synced"
FINAL_VIDEO_PATH = BASE_DIR / "reports" / "kuber_recon_track04_demo.mp4"

for d in [WORK_DIR, SEG_RAW_DIR, SEG_AUDIO_DIR, SEG_SYNC_DIR, FINAL_VIDEO_PATH.parent]:
    d.mkdir(parents=True, exist_ok=True)

# Segment Plan
# Total duration: 16 + 20 + 55 + 45 + 38 + 45 + 35 + 26 + 14 = 294s (4:54)
SEGMENTS = [
    {
        "id": "seg1",
        "title": "Opening & Central Thesis",
        "duration": 16.0,
        "text": "Finance teams reconcile settlements manually, and a wrong automated match is worse than an exception. KuberRecon is a finance-control prototype that matches what it can prove, refuses what it cannot, and accounts for every paise.",
        "url": "http://localhost:3000",
        "has_lower_third": True,
    },
    {
        "id": "seg2",
        "title": "Problem & Promise",
        "duration": 20.0,
        "text": "Track 04 requires a finance-operations loop across a batch, with measured accuracy and honest unresolved exceptions. This demo runs that loop on committed synthetic fixtures.",
        "url": "http://localhost:3000/console",
        "has_lower_third": False,
    },
    {
        "id": "seg3",
        "title": "100+ Record Synthetic Batch",
        "duration": 55.0,
        "text": "Here is a non-cherry-picked synthetic batch. Exact matches are resolved in paise, while the exception amount remains visible. Zero unexplained paise does not mean zero exceptions; it means every credit is classified as reconciled or explicitly held for review.",
        "url": "http://localhost:3000/console",
        "has_lower_third": False,
    },
    {
        "id": "seg4",
        "title": "Ambiguity Refusal: The Moat",
        "duration": 45.0,
        "text": "Two valid invoice subsets can equal the same bank credit. A greedy matcher might choose one and create a false match. KuberRecon refuses this outcome, marks it AMBIGUOUS_COLLISION, and routes it to review. That is intentional: uncertainty is not silently converted into money movement.",
        "url": "http://localhost:3000/console",
        "has_lower_third": False,
    },
    {
        "id": "seg5",
        "title": "Security Proof & Spoof Rejection",
        "duration": 38.0,
        "text": "Release evidence is server-controlled. A caller cannot supply a provider record in the request body. This forged input is rejected before business logic can release a hold.",
        "url": "http://localhost:3000/console",
        "has_lower_third": False,
    },
    {
        "id": "seg6",
        "title": "Controlled Release Path & Sandbox Verification",
        "duration": 45.0,
        "text": "For a valid sandbox scenario, release requires the contract state, delivery assertions, Ed25519 intent verification, server-side provider-record evidence, and a compare-and-swap state transition. The application moves to RELEASING and waits for final webhook processing. The payment rails here are sandbox fixtures; the control logic is what this project demonstrates.",
        "url": "http://localhost:3000/console",
        "has_lower_third": False,
    },
    {
        "id": "seg7",
        "title": "Committed Benchmark & Reproducibility",
        "duration": 35.0,
        "text": "These fixtures are committed with fixed seeds. The report shows clean, messy, and adversarial batches. The measured result is zero observed false auto-matches on this corpus, with ambiguity and dense clusters quarantined rather than guessed.",
        "url": (BASE_DIR / "scratch" / "viewer_benchmark.html").as_uri(),
        "has_lower_third": False,
    },
    {
        "id": "seg8",
        "title": "Architectural Honesty & Boundary Matrix",
        "duration": 26.0,
        "text": "This is a sandbox-verified prototype. It uses local SQLite WAL and a software demo signer. Live provider onboarding, managed key custody, and distributed infrastructure are future work. The core claim is narrower and testable: deterministic reconciliation, explicit refusal, and auditable control boundaries.",
        "url": (BASE_DIR / "scratch" / "viewer_architecture.html").as_uri(),
        "has_lower_third": False,
    },
    {
        "id": "seg9",
        "title": "Closing & Wrap-Up",
        "duration": 14.0,
        "text": "KuberRecon does not pretend every settlement can be automated. It proves when automation is justified, and makes uncertainty visible when it is not.",
        "url": "http://localhost:3000",
        "has_lower_third": True,
    },
]

JS_INJECTION = """
(() => {
  // 1. Persistent Sandbox Badge
  if (!document.getElementById('sandbox-fixtures-badge')) {
    const badge = document.createElement('div');
    badge.id = 'sandbox-fixtures-badge';
    badge.style.cssText = 'position:fixed;top:18px;right:24px;z-index:999998;display:flex;align-items:center;gap:8px;background:rgba(15,23,42,0.88);backdrop-filter:blur(10px);border:1px solid rgba(245,158,11,0.6);border-radius:9999px;padding:6px 15px;font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px;font-weight:700;color:#F59E0B;letter-spacing:0.06em;box-shadow:0 6px 16px rgba(0,0,0,0.4);pointer-events:none;';
    badge.innerHTML = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#F59E0B;box-shadow:0 0 8px #F59E0B;"></span> SANDBOX / SYNTHETIC FIXTURES';
    document.documentElement.appendChild(badge);
  }

  // 2. Custom Smooth Cursor Pointer
  if (!document.getElementById('demo-mouse-pointer')) {
    const cursor = document.createElement('div');
    cursor.id = 'demo-mouse-pointer';
    cursor.style.cssText = 'position:fixed;top:0;left:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;transition:transform 0.08s ease-out;transform:translate(960px,540px);';
    cursor.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter:drop-shadow(0 2px 5px rgba(0,0,0,0.5));"><path d="M4 2L18 12.5L11.5 14L8 21.5L4 2Z" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.8" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(cursor);

    window.__moveDemoCursor = (x, y) => {
      cursor.style.transform = `translate(${x}px, ${y}px)`;
    };

    window.__clickDemoCursor = (x, y) => {
      cursor.style.transform = `translate(${x}px, ${y}px)`;
      const ripple = document.createElement('div');
      ripple.style.cssText = `position:fixed;top:${y - 14}px;left:${x - 14}px;width:28px;height:28px;border-radius:50%;border:2px solid #38BDF8;background:rgba(56,189,248,0.3);z-index:2147483646;pointer-events:none;animation:demoClickAnim 0.35s ease-out forwards;`;
      document.documentElement.appendChild(ripple);
      setTimeout(() => ripple.remove(), 380);
    };

    const style = document.createElement('style');
    style.textContent = '@keyframes demoClickAnim { 0% { transform: scale(0.4); opacity: 1; } 100% { transform: scale(1.6); opacity: 0; } }';
    document.head.appendChild(style);
  }
})();
"""

LOWER_THIRD_JS = """
(() => {
  if (!document.getElementById('lower-third-banner')) {
    const banner = document.createElement('div');
    banner.id = 'lower-third-banner';
    banner.style.cssText = 'position:fixed;bottom:32px;left:36px;z-index:999998;background:rgba(10,15,30,0.92);backdrop-filter:blur(14px);border-left:4px solid #EAB308;border-top:1px solid rgba(255,255,255,0.1);border-right:1px solid rgba(255,255,255,0.1);border-bottom:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:14px 22px;font-family:system-ui,-apple-system,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,0.5);pointer-events:none;';
    banner.innerHTML = '<div style="font-size:16px;font-weight:800;color:#FFFFFF;letter-spacing:-0.02em;">KuberRecon — AI Finance Controller</div><div style="font-size:12px;font-weight:500;color:#94A3B8;margin-top:2px;">Track 04: AI Finance Controller · Razorpay AI Buildathon 2026</div>';
    document.documentElement.appendChild(banner);
  }
})();
"""

def generate_audios():
    print("=== [1/4] Generating Synchronized Narration Audio ===")
    engine = pyttsx3.init()
    engine.setProperty('rate', 160) # Natural measured pace
    
    for seg in SEGMENTS:
        seg_id = seg["id"]
        raw_wav = SEG_AUDIO_DIR / f"{seg_id}_raw.wav"
        pad_wav = SEG_AUDIO_DIR / f"{seg_id}_padded.wav"
        target_dur = seg["duration"]

        # Generate raw speech
        engine.save_to_file(seg["text"], str(raw_wav))
        engine.runAndWait()

        # Measure speech duration
        with contextlib.closing(wave.open(str(raw_wav), 'r')) as f:
            dur = f.getnframes() / float(f.getframerate())

        print(f"  {seg_id:5} | Target: {target_dur:4.1f}s | Raw Speech: {dur:4.1f}s")
        
        # Pad with silence using ffmpeg to exact target duration
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", f"apad=whole_dur={target_dur:.2f}",
            "-t", f"{target_dur:.2f}",
            str(pad_wav)
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            print(f"Error padding audio {seg_id}:", res.stderr.decode(errors='replace'))
            sys.exit(1)

def smooth_move(page, start_x, start_y, target_x, target_y, duration_s=1.0, steps=25):
    for i in range(steps):
        t = (i + 1) / steps
        # Smooth cubic easeInOut
        ease = t * t * (3 - 2 * t)
        curr_x = int(start_x + (target_x - start_x) * ease)
        curr_y = int(start_y + (target_y - start_y) * ease)
        page.evaluate(f"window.__moveDemoCursor({curr_x}, {curr_y})")
        time.sleep(duration_s / steps)

def smooth_click(page, x, y):
    page.evaluate(f"window.__clickDemoCursor({x}, {y})")
    time.sleep(0.35)

def park_pointer(page, x=1860, y=450):
    page.evaluate(f"window.__moveDemoCursor({x}, {y})")

def record_segments():
    print("\n=== [2/4] Recording 1080p Browser Segments with Custom Cursor ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for seg in SEGMENTS:
            seg_id = seg["id"]
            raw_video_dir = SEG_RAW_DIR / seg_id
            raw_video_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n>> Recording {seg_id}: '{seg['title']}' ({seg['duration']}s)...")
            
            ctx = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(raw_video_dir),
                record_video_size={"width": 1920, "height": 1080},
            )
            page = ctx.new_page()
            page.goto(seg["url"], wait_until="networkidle")
            page.wait_for_timeout(1000)

            # Inject cursor and badges
            page.evaluate(JS_INJECTION)
            if seg["has_lower_third"]:
                page.evaluate(LOWER_THIRD_JS)

            t_start = time.time()

            if seg_id == "seg1":
                # Opening: Move smoothly across title and CTA, then park pointer
                smooth_move(page, 960, 540, 800, 360, duration_s=2.5)
                time.sleep(1.0)
                smooth_move(page, 800, 360, 960, 620, duration_s=2.5)
                time.sleep(1.5)
                smooth_move(page, 960, 620, 1860, 300, duration_s=2.0)
                park_pointer(page, 1860, 300)

            elif seg_id == "seg2":
                # Problem & Promise: Move over KPI cards on /console
                smooth_move(page, 960, 540, 320, 150, duration_s=2.0)
                time.sleep(1.5)
                smooth_move(page, 320, 150, 680, 150, duration_s=2.0)
                time.sleep(1.5)
                smooth_move(page, 680, 150, 1050, 150, duration_s=2.0)
                time.sleep(1.5)
                smooth_move(page, 1050, 150, 1860, 400, duration_s=2.0)
                park_pointer(page, 1860, 400)

            elif seg_id == "seg3":
                # 100+ Record Synthetic Batch: Click Run Test on Card 1
                smooth_move(page, 960, 540, 960, 350, duration_s=2.0)
                time.sleep(1.0)
                # Find the button on Card 1 (first Run Test button)
                run_btn = page.locator("button:has-text('Run Test')").first
                box = run_btn.bounding_box()
                if box:
                    btn_x = int(box["x"] + box["width"] / 2)
                    btn_y = int(box["y"] + box["height"] / 2)
                    smooth_move(page, 960, 350, btn_x, btn_y, duration_s=2.0)
                    smooth_click(page, btn_x, btn_y)
                    run_btn.click()
                    time.sleep(2.5) # Wait for batch response to render
                    # Move pointer over the results table
                    smooth_move(page, btn_x, btn_y, 400, 520, duration_s=2.5)
                    time.sleep(2.0)
                    smooth_move(page, 400, 520, 750, 520, duration_s=2.5)
                    time.sleep(2.0)
                    smooth_move(page, 750, 520, 1100, 520, duration_s=2.5)
                    time.sleep(2.0)
                    smooth_move(page, 1100, 520, 1860, 480, duration_s=2.0)
                    park_pointer(page, 1860, 480)

            elif seg_id == "seg4":
                # Ambiguity Refusal: Scroll to Card 2 and run test
                page.mouse.wheel(0, 350)
                time.sleep(1.0)
                page.evaluate(JS_INJECTION) # ensure cursor tracks
                # Card 2 Run Test button (second button)
                run_btns = page.locator("button:has-text('Run Test')")
                if run_btns.count() >= 2:
                    btn2 = run_btns.nth(1)
                    box = btn2.bounding_box()
                    if box:
                        btn_x = int(box["x"] + box["width"] / 2)
                        btn_y = int(box["y"] + box["height"] / 2)
                        smooth_move(page, 960, 350, btn_x, btn_y, duration_s=2.0)
                        smooth_click(page, btn_x, btn_y)
                        btn2.click()
                        time.sleep(2.0)
                        # Move over collision result
                        smooth_move(page, btn_x, btn_y, 500, btn_y + 120, duration_s=2.0)
                        time.sleep(2.0)
                        smooth_move(page, 500, btn_y + 120, 900, btn_y + 120, duration_s=2.0)
                        time.sleep(2.0)
                        smooth_move(page, 900, btn_y + 120, 1860, 520, duration_s=2.0)
                        park_pointer(page, 1860, 520)

            elif seg_id == "seg5":
                # Security Proof Matrix: Switch to Security tab and run attacks
                sec_tab = page.locator("button:has-text('Security Proof & Attack Matrix')")
                box = sec_tab.bounding_box()
                if box:
                    tab_x = int(box["x"] + box["width"] / 2)
                    tab_y = int(box["y"] + box["height"] / 2)
                    smooth_move(page, 960, 540, tab_x, tab_y, duration_s=2.0)
                    smooth_click(page, tab_x, tab_y)
                    sec_tab.click()
                    time.sleep(1.5)
                    page.evaluate(JS_INJECTION)
                    # Run Attack 2 (Forged Key)
                    run_btns = page.locator("button:has-text('Run Test')")
                    if run_btns.count() >= 2:
                        btn2 = run_btns.nth(1)
                        b2_box = btn2.bounding_box()
                        if b2_box:
                            x2 = int(b2_box["x"] + b2_box["width"] / 2)
                            y2 = int(b2_box["y"] + b2_box["height"] / 2)
                            smooth_move(page, tab_x, tab_y, x2, y2, duration_s=2.0)
                            smooth_click(page, x2, y2)
                            btn2.click()
                            time.sleep(2.0)
                    # Move pointer to highlight 422 / 401 refusal
                    smooth_move(page, 500, 400, 1860, 480, duration_s=2.0)
                    park_pointer(page, 1860, 480)

            elif seg_id == "seg6":
                # Assurance Lifecycle: Switch to Assurance tab and run Golden Flow
                ass_tab = page.locator("button:has-text('Assurance Lifecycle')")
                box = ass_tab.bounding_box()
                if box:
                    tab_x = int(box["x"] + box["width"] / 2)
                    tab_y = int(box["y"] + box["height"] / 2)
                    smooth_move(page, 960, 540, tab_x, tab_y, duration_s=2.0)
                    smooth_click(page, tab_x, tab_y)
                    ass_tab.click()
                    time.sleep(1.5)
                    page.evaluate(JS_INJECTION)
                    # Click Run Automated Golden Flow
                    gf_btn = page.locator("button:has-text('Run Automated Golden Flow')")
                    gbox = gf_btn.bounding_box()
                    if gbox:
                        gx = int(gbox["x"] + gbox["width"] / 2)
                        gy = int(gbox["y"] + gbox["height"] / 2)
                        smooth_move(page, tab_x, tab_y, gx, gy, duration_s=2.0)
                        smooth_click(page, gx, gy)
                        gf_btn.click()
                        time.sleep(5.0) # Wait for golden flow stages (HELD -> VERIFYING -> RELEASING -> RELEASED)
                    # Open Decision Evidence drawer
                    ev_btn = page.locator("button:has-text('Decision Evidence')")
                    ebox = ev_btn.bounding_box()
                    if ebox:
                        ex = int(ebox["x"] + ebox["width"] / 2)
                        ey = int(ebox["y"] + ebox["height"] / 2)
                        smooth_move(page, 960, 400, ex, ey, duration_s=2.0)
                        smooth_click(page, ex, ey)
                        ev_btn.click()
                        time.sleep(3.0)
                    smooth_move(page, 1000, 500, 1860, 500, duration_s=2.0)
                    park_pointer(page, 1860, 500)

            elif seg_id == "seg7":
                # Benchmark Viewer: Inspect the 3 batch comparison table
                smooth_move(page, 960, 540, 500, 240, duration_s=2.5)
                time.sleep(2.0)
                smooth_move(page, 500, 240, 800, 240, duration_s=2.0)
                time.sleep(2.0)
                smooth_move(page, 800, 240, 1100, 240, duration_s=2.0)
                time.sleep(2.0)
                smooth_move(page, 1100, 240, 600, 480, duration_s=2.5)
                time.sleep(2.5)
                smooth_move(page, 600, 480, 1860, 400, duration_s=2.0)
                park_pointer(page, 1860, 400)

            elif seg_id == "seg8":
                # Architecture Viewer: Inspect 3-tier boundary matrix
                smooth_move(page, 960, 540, 500, 360, duration_s=2.5)
                time.sleep(2.0)
                smooth_move(page, 500, 360, 800, 480, duration_s=2.5)
                time.sleep(2.5)
                smooth_move(page, 800, 480, 1860, 400, duration_s=2.0)
                park_pointer(page, 1860, 400)

            elif seg_id == "seg9":
                # Closing Hero: Clean overview
                smooth_move(page, 960, 540, 960, 400, duration_s=2.5)
                time.sleep(2.0)
                smooth_move(page, 960, 400, 1860, 300, duration_s=2.0)
                park_pointer(page, 1860, 300)

            # Wait out remaining segment duration
            elapsed = time.time() - t_start
            rem = seg["duration"] - elapsed
            if rem > 0:
                time.sleep(rem)

            ctx.close()

        browser.close()

def sync_and_concat():
    print("\n=== [3/4] Transcoding & Synchronizing Audio/Video Segments ===")
    concat_lines = []

    for seg in SEGMENTS:
        seg_id = seg["id"]
        raw_vids = list((SEG_RAW_DIR / seg_id).glob("*.webm"))
        if not raw_vids:
            print(f"Error: No raw video found for {seg_id}!")
            sys.exit(1)
        raw_vid = raw_vids[0]
        pad_wav = SEG_AUDIO_DIR / f"{seg_id}_padded.wav"
        synced_mp4 = SEG_SYNC_DIR / f"{seg_id}.mp4"
        dur = seg["duration"]

        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_vid),
            "-i", str(pad_wav),
            "-t", f"{dur:.2f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(synced_mp4)
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            print(f"Error syncing {seg_id}:", res.stderr.decode(errors='replace'))
            sys.exit(1)

        print(f"  Synced {seg_id}: {dur}s -> {synced_mp4.name}")
        concat_lines.append(f"file '{synced_mp4.resolve().as_posix()}'")

    concat_file = WORK_DIR / "concat_list.txt"
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")

    print("\n=== [4/4] Concatenating Master 1080p MP4 Demo Video ===")
    master_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(FINAL_VIDEO_PATH)
    ]
    res = subprocess.run(master_cmd, capture_output=True)
    if res.returncode != 0:
        print("Error concatenating master video:", res.stderr.decode(errors='replace'))
        sys.exit(1)

    print(f"\n[SUCCESS] Master Video Generated: {FINAL_VIDEO_PATH}")
    file_size_mb = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    generate_audios()
    record_segments()
    sync_and_concat()
