import subprocess
from pathlib import Path

BASE_DIR = Path("C:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon")
WORK_DIR = BASE_DIR / "artifacts" / "video_production"
RAW_DIR = WORK_DIR / "raw"
AUDIO_DIR = WORK_DIR / "indic_gtts_audio"
SYNC_DIR = WORK_DIR / "indic_gtts_sync"
SUBTITLE_PATH = WORK_DIR / "indic_subtitles.srt"
FINAL_VIDEO_PATH = BASE_DIR / "reports" / "kuber_recon_track04_demo.mp4"

for d in [AUDIO_DIR, SYNC_DIR, FINAL_VIDEO_PATH.parent]:
    d.mkdir(parents=True, exist_ok=True)

SEGMENTS = [
    {
        "id": "seg1",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_1.wav",
        "duration": 16.0,
        "speed": 1.13,
        "sub_start": "00:00:01,000",
        "sub_end": "00:00:15,500",
        "sub_text": "Finance teams reconcile settlements manually; a wrong match is worse than an exception.\nKuberRecon matches what it can prove, refuses what it cannot, and accounts for every paise."
    },
    {
        "id": "seg2",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_2.wav",
        "duration": 20.0,
        "speed": 1.0,
        "sub_start": "00:00:17,000",
        "sub_end": "00:00:32,000",
        "sub_text": "Track 04 requires a finance-operations loop across a batch, with measured accuracy and honest unresolved exceptions.\nThis demo runs that loop on committed synthetic fixtures."
    },
    {
        "id": "seg3",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_3.wav",
        "duration": 55.0,
        "speed": 1.0,
        "sub_start": "00:00:37,500",
        "sub_end": "00:00:58,000",
        "sub_text": "Here is a non-cherry-picked synthetic batch. Exact matches are resolved in paise, while exceptions remain visible.\nZero unexplained paise means every credit is classified as reconciled or explicitly held for review."
    },
    {
        "id": "seg4",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_4.wav",
        "duration": 45.0,
        "speed": 1.0,
        "sub_start": "00:01:32,500",
        "sub_end": "00:01:58,000",
        "sub_text": "Two valid invoice subsets can equal the same bank credit. A greedy matcher might choose one and create a false match.\nKuberRecon refuses this outcome, marks it AMBIGUOUS_COLLISION, and routes it to review."
    },
    {
        "id": "seg5",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_5.wav",
        "duration": 38.0,
        "speed": 1.0,
        "sub_start": "00:02:17,500",
        "sub_end": "00:02:32,000",
        "sub_text": "Release evidence is server-controlled. A caller cannot supply a provider record in the request body.\nThis forged input is rejected (HTTP 422) before business logic can release a hold."
    },
    {
        "id": "seg6",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_6.wav",
        "duration": 45.0,
        "speed": 1.0,
        "sub_start": "00:02:56,500",
        "sub_end": "00:03:28,000",
        "sub_text": "For a valid sandbox scenario, release requires contract state, delivery assertions, Ed25519 intent, and server provider records.\nThe application moves to RELEASING and waits for final webhook processing."
    },
    {
        "id": "seg7",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_7.wav",
        "duration": 35.0,
        "speed": 1.0,
        "sub_start": "00:03:41,000",
        "sub_end": "00:04:01,000",
        "sub_text": "These fixtures are committed with fixed seeds across clean, messy, and adversarial batches.\nThe measured result is zero observed false auto-matches, with ambiguity and dense clusters quarantined."
    },
    {
        "id": "seg8",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_8.wav",
        "duration": 26.0,
        "speed": 1.0,
        "sub_start": "00:04:16,500",
        "sub_end": "00:04:41,500",
        "sub_text": "This is a sandbox-verified prototype using local SQLite WAL and a software demo signer.\nLive provider onboarding, managed key custody, and distributed infrastructure remain future work."
    },
    {
        "id": "seg9",
        "raw_src": BASE_DIR / "scratch" / "gtts_seg_9.wav",
        "duration": 14.0,
        "speed": 1.0,
        "sub_start": "00:04:42,500",
        "sub_end": "00:04:53,500",
        "sub_text": "KuberRecon does not pretend every settlement can be automated.\nIt proves when automation is justified, and makes uncertainty visible when it is not."
    },
]

def prepare_audio_and_sync():
    print("=== [1/3] Preparing Audio & Syncing Segments ===")
    concat_lines = []

    for seg in SEGMENTS:
        seg_id = seg["id"]
        raw_wav = seg["raw_src"]
        padded_wav = AUDIO_DIR / f"{seg_id}_padded.wav"
        target_dur = seg["duration"]
        speed = seg.get("speed", 1.0)

        # Build audio filter: tempo adjustment if needed, then silence padding
        if speed != 1.0:
            af_filter = f"atempo={speed:.2f},apad=whole_dur={target_dur:.2f}"
        else:
            af_filter = f"apad=whole_dur={target_dur:.2f}"

        cmd_audio = [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", af_filter,
            "-t", f"{target_dur:.2f}",
            str(padded_wav)
        ]
        res = subprocess.run(cmd_audio, capture_output=True)
        if res.returncode != 0:
            print(f"Error preparing audio {seg_id}:", res.stderr.decode(errors="replace"))
            raise RuntimeError(f"Audio prep failed for {seg_id}")

        # Find raw video segment
        raw_vids = list((RAW_DIR / seg_id).glob("*.webm"))
        if not raw_vids:
            raise FileNotFoundError(f"Missing raw video for {seg_id}")
        raw_vid = raw_vids[0]

        synced_mp4 = SYNC_DIR / f"{seg_id}.mp4"
        cmd_sync = [
            "ffmpeg", "-y",
            "-i", str(raw_vid),
            "-i", str(padded_wav),
            "-t", f"{target_dur:.2f}",
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
        res_sync = subprocess.run(cmd_sync, capture_output=True)
        if res_sync.returncode != 0:
            print(f"Error syncing {seg_id}:", res_sync.stderr.decode(errors="replace"))
            raise RuntimeError(f"Sync failed for {seg_id}")

        print(f"  Synced {seg_id}: {target_dur:.1f}s -> {synced_mp4.name}")
        concat_lines.append(f"file '{synced_mp4.resolve().as_posix()}'")

    concat_file = WORK_DIR / "indic_gtts_concat.txt"
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
    return concat_file

def generate_subtitles():
    print("=== [2/3] Writing Master SRT Subtitles ===")
    srt_entries = []
    for i, seg in enumerate(SEGMENTS):
        entry = f"{i+1}\n{seg['sub_start']} --> {seg['sub_end']}\n{seg['sub_text']}\n"
        srt_entries.append(entry)
    SUBTITLE_PATH.write_text("\n".join(srt_entries), encoding="utf-8")
    print(f"  Subtitles saved to {SUBTITLE_PATH}")

def assemble_master_with_subtitles(concat_file):
    print("=== [3/3] Concatenating & Burning Small Bottom Subtitles ===")
    temp_concat = WORK_DIR / "temp_indic_concat.mp4"

    # Step A: Concat segments
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
        print("Error concatenating:", res_c.stderr.decode(errors="replace"))
        raise RuntimeError("Concat failed")

    # Step B: Burn small non-intrusive subtitles
    # Style: FontSize=7.5 (small, clear, doesn't cover cards), MarginV=8 (rests on bottom border)
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
        raise RuntimeError("Subtitle burning failed")

    print(f"\n[SUCCESS] Master Video Created: {FINAL_VIDEO_PATH}")
    size_mb = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"Final Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    cfile = prepare_audio_and_sync()
    generate_subtitles()
    assemble_master_with_subtitles(cfile)
