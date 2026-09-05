"""
Sarvam AI Voice Briefing Generator (Bulbul v3 · Advait)
Synthesizes the executive audio walkthrough for Kuber OS using Sarvam AI's
Indic neural TTS engine with Advait voice.
"""

import os
import io
import wave
import base64
import requests
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_AUDIO_DIR = ROOT_DIR / "frontend" / "public" / "audio"
FRONTEND_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 1. Resolve API Key from local .env or fallback
def get_sarvam_key() -> str:
    env_files = [ROOT_DIR / ".env", ROOT_DIR.parent / ".env"]
    for env_file in env_files:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("SARVAM_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    key = os.environ.get("SARVAM_API_KEY", "")
    if not key:
        raise ValueError("SARVAM_API_KEY must be set in .env or environment")
    return key

API_KEY = get_sarvam_key()
API_URL = "https://api.sarvam.ai/text-to-speech"

# 2. Executive Script (split into <= 500 character chunks for Sarvam API compliance)
CHUNKS = [
    (
        "Welcome to Kuber OS, the autonomous AI finance controller and settlement assurance "
        "platform built for the Razorpay AI Buildathon 2026. Today, autonomous AI buyer agents "
        "can transact instantly, but they settle blindly. Traditional payment rails disburse "
        "funds before verifying if delivery occurred or if seller GSTIN is legitimate."
    ),
    (
        "Kuber OS solves this. We gate Razorpay Route pre-settlement behind cryptographic delivery "
        "proofs, Horowitz-Sahni meet-in-the-middle subset-sum matching, and statutory GSTIN "
        "Mod-36 checksums, ensuring zero false matches on tested fixtures and zero float rounding errors."
    ),
    (
        "Once verified, Kuber OS converts merchant revenue into instant working capital, "
        "and automatically recovers advances through a twelve percent nodal settlement sweep at "
        "the source. Click Launch Console to explore the live autonomous settlement radar."
    ),
]

def generate_voice_briefing():
    print(f"=== Synthesizing Kuber OS Briefing via Sarvam AI (Advait · Bulbul v3) ===")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:] if len(API_KEY) > 12 else ''}")
    
    headers = {
        "api-subscription-key": API_KEY,
        "Content-Type": "application/json"
    }

    # Verify each chunk is <= 500 characters
    for i, chunk in enumerate(CHUNKS, 1):
        print(f"  Chunk {i} length: {len(chunk)} characters")
        assert len(chunk) <= 500, f"Chunk {i} exceeds Sarvam AI 500 character limit"

    payload = {
        "inputs": CHUNKS,
        "target_language_code": "en-IN",
        "speaker": "advait",
        "pace": 1.05,
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": "bulbul:v3"
    }

    print("Sending synthesis request to Sarvam AI...")
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    
    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam AI API failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    audios = data.get("audios", [])
    if not audios:
        raise ValueError("No audio segments returned from Sarvam AI")

    print(f"Received {len(audios)} audio segments. Concatenating into single WAV...")

    # Decode each base64 audio segment into BytesIO
    wav_streams = [io.BytesIO(base64.b64decode(a)) for a in audios]
    combined_io = io.BytesIO()

    # Read params from the first chunk and extract audio frames
    with wave.open(wav_streams[0], "rb") as first_wav:
        params = first_wav.getparams()
        frames = [first_wav.readframes(first_wav.getnframes())]

    # Append subsequent frames
    for ws in wav_streams[1:]:
        with wave.open(ws, "rb") as w:
            frames.append(w.readframes(w.getnframes()))

    # Write combined frames
    with wave.open(combined_io, "wb") as out_wav:
        out_wav.setparams(params)
        for f in frames:
            out_wav.writeframes(f)

    final_wav_bytes = combined_io.getvalue()
    
    # Calculate duration
    total_frames = sum(len(f) // (params.nchannels * params.sampwidth) for f in frames)
    duration_sec = total_frames / params.framerate
    
    print(f"Audio synthesized successfully:")
    print(f"  Sample Rate: {params.framerate} Hz")
    print(f"  Channels: {params.nchannels}")
    print(f"  Total Duration: {duration_sec:.2f} seconds")
    print(f"  File Size: {len(final_wav_bytes):,} bytes ({len(final_wav_bytes)/(1024*1024):.2f} MB)")

    # Save to primary and legacy paths
    kuber_path = FRONTEND_AUDIO_DIR / "kuber_executive_briefing.wav"
    apex_path = FRONTEND_AUDIO_DIR / "apex_executive_briefing.wav"

    kuber_path.write_bytes(final_wav_bytes)
    apex_path.write_bytes(final_wav_bytes)

    print(f"  Saved to: {kuber_path}")
    print(f"  Saved to: {apex_path}")
    print("=== Complete! ===")

if __name__ == "__main__":
    generate_voice_briefing()
