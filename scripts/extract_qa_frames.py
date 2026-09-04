import subprocess
from pathlib import Path

BASE_DIR = Path("C:/Users/pranj/Documents/Razorpay-Buildthon/kuber-recon")
VIDEO_PATH = BASE_DIR / "reports" / "kuber_recon_track04_demo.mp4"
QA_DIR = BASE_DIR / "reports" / "qa_frames"
QA_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMPS = [
    ("00:00:05.000", "01_opening_thesis.png"),
    ("00:00:25.000", "02_problem_promise.png"),
    ("00:01:05.000", "03_batch_reconciliation_result.png"),
    ("00:01:55.000", "04_ambiguity_refusal_moat.png"),
    ("00:02:35.000", "05_security_attack_matrix.png"),
    ("00:03:20.000", "06_assurance_lifecycle_evidence.png"),
    ("00:03:55.000", "07_track04_benchmark_table.png"),
    ("00:04:25.000", "08_architecture_boundary_matrix.png"),
    ("00:04:48.000", "09_closing_wrapup.png"),
]

print("=== Extracting QA Verification Frames ===")
for ts, name in TIMESTAMPS:
    out_path = QA_DIR / name
    cmd = [
        "ffmpeg", "-y",
        "-ss", ts,
        "-i", str(VIDEO_PATH),
        "-vframes", "1",
        "-q:v", "2",
        str(out_path)
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0:
        print(f"Extracted {name} at {ts} ({out_path.stat().st_size} bytes)")
    else:
        print(f"Failed {name}:", res.stderr.decode(errors="replace"))
