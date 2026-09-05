"""Quick verification script for Sarvam AI Text-to-Speech API."""
import os
import requests
import base64
from pathlib import Path

# Load key from local .env
ROOT_DIR = Path(__file__).resolve().parent.parent
key = os.environ.get("SARVAM_API_KEY")
if not key:
    for env_path in [ROOT_DIR / ".env", ROOT_DIR.parent / ".env"]:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("SARVAM_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if key:
            break

if not key:
    raise ValueError("SARVAM_API_KEY not found in .env or environment")

print("Testing Sarvam AI key:", f"{key[:8]}...{key[-4:] if len(key) > 12 else ''}")

url = "https://api.sarvam.ai/text-to-speech"
headers = {
    "api-subscription-key": key,
    "Content-Type": "application/json"
}
payload = {
    "inputs": ["Kuber OS is an autonomous AI finance controller and settlement assurance platform for Razorpay Route."],
    "target_language_code": "en-IN",
    "speaker": "advait",
    "pace": 1.0,
    "speech_sample_rate": 22050,
    "enable_preprocessing": True,
    "model": "bulbul:v3"
}

resp = requests.post(url, headers=headers, json=payload, timeout=30)
print("Status:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    raw = base64.b64decode(data["audios"][0])
    out_path = ROOT_DIR / "scratch" / "sarvam_advait_test.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    print("SUCCESS! Generated Sarvam AI audio with Advait voice! Size:", len(raw))
else:
    print("Error:", resp.text)
