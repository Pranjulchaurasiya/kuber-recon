import os
import sys
import time
import wave
import contextlib
import subprocess
import asyncio
from pathlib import Path
import edge_tts

BASE_DIR = Path("C:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon")
WORK_DIR = BASE_DIR / "artifacts" / "video_production"
SEG_RAW_DIR = WORK_DIR / "raw"
INDIC_AUDIO_DIR = WORK_DIR / "indic_audio"
INDIC_SYNC_DIR = WORK_DIR / "indic_synced"
FINAL_VIDEO_PATH = BASE_DIR / "reports" / "kuber_recon_track04_demo.mp4"
SUBTITLE_PATH = WORK_DIR / "master_subtitles.srt"

for d in [WORK_DIR, INDIC_AUDIO_DIR, INDIC_SYNC_DIR, FINAL_VIDEO_PATH.parent]:
    d.mkdir(parents=True, exist_ok=True)

SEGMENTS = [
    {
        "id": "seg1",
        "title": "Opening & Central Thesis",
        "duration": 16.0,
        "text": "Finance teams reconcile settlements manually, and a wrong automated match is worse than an exception. KuberRecon is a finance-control prototype that matches what it can prove, refuses what it cannot, and accounts for every paise.",
        "sub_start": "00:00:01,000",
        "sub_end": "00:00:15,000",
        "sub_text": "Finance teams reconcile settlements manually; a wrong match is worse than an exception.\nKuberRecon matches what it can prove, refuses what it cannot, and accounts for every paise."
    },
    {
        "id": "seg2",
        "title": "Problem & Promise",
        "duration": 20.0,
        "text": "Track 04 requires a finance-operations loop across a batch, with measured accuracy and honest unresolved exceptions. This demo runs that loop on committed synthetic fixtures.",
        "sub_start": "00:00:17,000",
        "sub_end": "00:00:34,000",
        "sub_text": "Track 04 requires a finance-operations loop across a batch, with measured accuracy and honest unresolved exceptions.\nThis demo runs that loop on committed synthetic fixtures."
    },
    {
        "id": "seg3",
        "title": "100+ Record Synthetic Batch",
        "duration": 55.0,
        "text": "Here is a non-cherry-picked synthetic batch. Exact matches are resolved in paise, while the exception amount remains visible. Zero unexplained paise does not mean zero exceptions; it means every credit is classified as reconciled or explicitly held for review.",
        "sub_start": "00:00:37,500",
        "sub_end": "00:00:58,000",
        "sub_text": "Here is a non-cherry-picked synthetic batch. Exact matches are resolved in paise, while exceptions remain visible.\nZero unexplained paise means every credit is classified as reconciled or explicitly held for review."
    },
    {
        "id": "seg4",
        "title": "Ambiguity Refusal: The Moat",
        "duration": 45.0,
        "text": "Two valid invoice subsets can equal the same bank credit. A greedy matcher might choose one and create a false match. KuberRecon refuses this outcome, marks it AMBIGUOUS_COLLISION, and routes it to review. That is intentional: uncertainty is not silently converted into money movement.",
        "sub_start": "00:01:32,500",
        "sub_end": "00:01:55,000",
        "sub_text": "Two valid invoice subsets can equal the same bank credit. A greedy matcher might choose one and create a false match.\nKuberRecon refuses this outcome, marks it AMBIGUOUS_COLLISION, and routes it to review."
    },
    {
        "id": "seg5",
        "title": "Security Proof & Spoof Rejection",
        "duration": 38.0,
        "text": "Release evidence is server-controlled. A caller cannot supply a provider record in the request body. This forged input is rejected before business logic can release a hold.",
        "sub_start": "00:02:17,500",
        "sub_end": "00:02:34,000",
        "sub_text": "Release evidence is server-controlled. A caller cannot supply a provider record in the request body.\nThis forged input is rejected (HTTP 422) before business logic can release a hold."
    },
    {
        "id": "seg6",
        "title": "Controlled Release Path & Sandbox Verification",
        "duration": 45.0,
        "text": "For a valid sandbox scenario, release requires the contract state, delivery assertions, Ed25519 intent verification, server-side provider-record evidence, and a compare-and-swap state transition. The application moves to RELEASING and waits for final webhook processing. The payment rails here are sandbox fixtures; the control logic is what this project demonstrates.",
        "sub_start": "00:02:56,500",
        "sub_end": "00:03:26,000",
        "sub_text": "For a valid sandbox scenario, release requires contract state, delivery assertions, Ed25519 intent, and server provider records.\nThe application moves to RELEASING and waits for final webhook processing."
    },
    {
        "id": "seg7",
        "title": "Committed Benchmark & Reproducibility",
        "duration": 35.0,
        "text": "These fixtures are committed with fixed seeds. The report shows clean, messy, and adversarial batches. The measured result is zero observed false auto-matches on this corpus, with ambiguity and dense clusters quarantined rather than guessed.",
        "sub_start": "00:03:41,000",
        "sub_end": "00:04:02,000",
        "sub_text": "These fixtures are committed with fixed seeds across clean, messy, and adversarial batches.\nThe measured result is zero observed false auto-matches, with ambiguity and dense clusters quarantined."
    },
    {
        "id": "seg8",
        "title": "Architectural Honesty & Boundary Matrix",
        "duration": 26.0,
        "text": "This is a sandbox-verified prototype. It uses local SQLite WAL and a software demo signer. Live provider onboarding, managed key custody, and distributed infrastructure are future work. The core claim is narrower and testable: deterministic reconciliation, explicit refusal, and auditable control boundaries.",
        "sub_start": "00:04:16,500",
        "sub_end": "00:04:38,500",
        "sub_text": "This is a sandbox-verified prototype using local SQLite WAL and a software demo signer.\nLive provider onboarding, managed key custody, and distributed infrastructure remain future work."
    },
    {
        "id": "seg9",
        "title": "Closing & Wrap-Up",
        "duration": 14.0,
        "text": "KuberRecon does not pretend every settlement can be automated. It proves when automation is justified, and makes uncertainty visible when it is not.",
        "sub_start": "00:04:41,500",
        "sub_end": "00:04:53,000",
        "sub_text": "KuberRecon does not pretend every settlement can be automated.\nIt proves when automation is justified, and makes uncertainty visible when it is not."
    },
]

async def generate_indic_audios():
    print("=== [1/4] Synthesizing Indian English Neural Voice (en-IN-PrabhatNeural) ===")
    voice = "en-IN-PrabhatNeural"
    
    for seg in SEGMENTS:
        seg_id = seg["id"]
        raw_mp3 = INDIC_AUDIO_DIR / f"{seg_id}_raw.mp3"
        raw_wav = INDIC_AUDIO_DIR / f"{seg_id}_raw.wav"
        pad_wav = INDIC_AUDIO_DIR / f"{seg_id}_padded.wav"
        target_dur = seg["duration"]

        print(f"  Generating {seg_id}...")
        communicate = edge_tts.Communicate(seg["text"], voice, rate="+2%")
        await communicate.save(str(raw_mp3))

        # Convert to WAV
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_mp3), str(raw_wav)], capture_output=True)

        # Measure duration
        with contextlib.closing(wave.open(str(raw_wav), 'r')) as f:
            dur = f.getnframes() / float(f.getframerate())

        print(f"  {seg_id:5} | Target: {target_dur:4.1f}s | Synthesized Speech: {dur:4.1f}s")

        # Pad with silence to exact duration
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", f"apad=whole_dur={target_dur:.2f}",
            "-t", f"{target_dur:.2f}",
            str(pad_wav)
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            print(f"Error padding {seg_id}:", res.stderr.decode(errors="replace"))
            sys.exit(1)

def generate_srt():
    print("\n=== [2/4] Generating Master Subtitles (SRT) ===")
    srt_entries = []
    for i, seg in enumerate(SEGMENTS):
        entry = f"{i+1}\n{seg['sub_start']} --> {seg['sub_end']}\n{seg['sub_text']}\n"
        srt_entries.append(entry)
    
    SUBTITLE_PATH.write_text("\n".join(srt_entries), encoding="utf-8")
    print(f"  Master Subtitles written to: {SUBTITLE_PATH}")

def sync_segments():
    print("\n=== [3/4] Synchronizing Audio & Video Segments ===")
    concat_lines = []

    for seg in SEGMENTS:
        seg_id = seg["id"]
        raw_vids = list((SEG_RAW_DIR / seg_id).glob("*.webm"))
        if not raw_vids:
            print(f"Error: Missing raw video for {seg_id}")
            sys.exit(1)
        raw_vid = raw_vids[0]
        pad_wav = INDIC_AUDIO_DIR / f"{seg_id}_padded.wav"
        synced_mp4 = INDIC_SYNC_DIR / f"{seg_id}.mp4"
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
            print(f"Error syncing {seg_id}:", res.stderr.decode(errors="replace"))
            sys.exit(1)

        print(f"  Synced {seg_id}: {dur:.1f}s -> {synced_mp4.name}")
        concat_lines.append(f"file '{synced_mp4.resolve().as_posix()}'")

    concat_file = WORK_DIR / "indic_concat_list.txt"
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
    return concat_file

def assemble_master_video(concat_file):
    print("\n=== [4/4] Assembling Master Video with Small Subtitles ===")
    temp_concat = WORK_DIR / "temp_concat.mp4"

    # Step A: Concat segments without recompression
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(temp_concat)
    ]
    res_c = subprocess.run(cmd_concat, capture_output=True)
    if res_c.returncode != 0:
        print("Error concatenating segments:", res_c.stderr.decode(errors="replace"))
        sys.exit(1)

    # Step B: Burn small non-intrusive subtitles
    # Style: FontSize=7.5 (small), white with thin black outline, bottom margin MarginV=8 (never covers cards)
    sub_path_escaped = str(SUBTITLE_PATH.resolve().as_posix()).replace(":", "\\:")
    sub_filter = f"subtitles={sub_path_escaped}:force_style='FontSize=7.5,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=0.8,Shadow=0.5,MarginV=8'"

    cmd_burn = [
        "ffmpeg", "-y",
        "-i", str(temp_concat),
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "copy",
        str(FINAL_VIDEO_PATH)
    ]
    res_b = subprocess.run(cmd_burn, capture_output=True)
    if res_b.returncode != 0:
        print("Error burning subtitles:", res_b.stderr.decode(errors="replace"))
        sys.exit(1)

    print(f"\n[SUCCESS] Master Video with Indic Voice & Subtitles Created: {FINAL_VIDEO_PATH}")
    size_mb = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"File Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    asyncio.run(generate_indic_audios())
    generate_srt()
    cfile = sync_segments()
    assemble_master_video(cfile)
