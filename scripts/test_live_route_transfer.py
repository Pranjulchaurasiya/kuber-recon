"""
Razorpay Route Transfer Creation Sandbox Diagnostic Probe.
==========================================================
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

url = "https://api.razorpay.com/v1/transfers"
payload = {
    "account": "acc_sample_seller_01",
    "amount": 2500000,
    "currency": "INR",
    "on_hold": True,
    "notes": {"protocol": "APEX_ASSURANCE_AGENTIC_ESCROW"},
}

try:
    resp = requests.post(url, auth=HTTPBasicAuth(key_id, key_secret), json=payload, timeout=5)
    print(f"HTTP Status: {resp.status_code}")
    print(f"Response Body: {resp.text}")
except Exception as e:
    print(f"Request Result: {e}")
