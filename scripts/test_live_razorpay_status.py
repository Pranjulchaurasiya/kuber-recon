"""
Razorpay Sandbox API Diagnostic Probe.
=====================================
Hard-fails defensively if any live key (non 'rzp_test_') is detected.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID", "")
key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

if not key_id or not key_id.startswith("rzp_test_"):
    raise SystemExit(
        "SAFETY ERROR: Only Razorpay test keys ('rzp_test_...') are permitted for automated probes. "
        f"Found key ID: {key_id[:8]}..."
    )

print(f"Verified Safe Sandbox Key Prefix: {key_id[:8]}... (Test Mode)")

# GET test-mode probe
url = "https://api.razorpay.com/v1/settlements/recon/combined"
params = {"year": 2026, "month": 8, "day": 1}

try:
    resp = requests.get(url, auth=HTTPBasicAuth(key_id, key_secret), params=params, timeout=5)
    print(f"HTTP Status: {resp.status_code}")
    print(f"Response Body: {resp.text[:500]}")
except Exception as e:
    print(f"Probe Result: {e}")
