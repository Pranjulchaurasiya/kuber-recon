"""
Verify Complete Finance-Ops Control Loop via Signed Webhook Ingestion & 5-Point Provider Join
==============================================================================================
Validates the complete control loop:
1. Contract Creation (`POST /api/apex/contracts/create`)
2. Supplier Manifest Delivery & Cryptographic Assertion (`POST /api/apex/contracts/deliver`)
3. Forged Client-Supplied Provider Records Injection Attempt (`POST /api/apex/contracts/release`)
   -> Strictly rejected with HTTP 422 (Pydantic extra='forbid')
4. Missing Provider Record Guard (`POST /api/apex/contracts/release`)
   -> Strictly rejected with HTTP 412 (Zero matched provider records)
5. Webhook Ingestion with Valid HMAC-SHA256 Signature (`POST /api/webhook/razorpay`)
   -> Verifies HMAC signature, timestamp freshness, and saves server-side provider record
6. Authoritative Contract Release Join (`POST /api/apex/contracts/release`)
   -> 5-point join against the webhook-persisted provider event succeeds and transitions contract
"""

from datetime import date, datetime, timezone
import hashlib
import hmac
import json
import os
import sys
import time
from cryptography.hazmat.primitives.asymmetric import ed25519
import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.getenv("KUBER_API_BASE_URL", "http://127.0.0.1:8000")
MERCHANT_ID = os.getenv("KUBER_MERCHANT_ID", "merchant_rzp_primary")
API_KEY = os.getenv("KUBER_SANDBOX_KEY", "kuber_sandbox_key_primary_2026")
WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_sandbox_demo_only_2026")

HEADERS = {
    "X-Merchant-Id": MERCHANT_ID,
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


def main():
    print("=" * 80)
    print(" [FINANCE-OPS VERIFICATION] End-to-End Signed Webhook Provenance & Release Gate")
    print("=" * 80)

    # 1. Create Contract
    amount_paise = 2_500_000
    create_res = requests.post(f"{BASE_URL}/api/apex/contracts/create", headers=HEADERS, json={
        "buyer_agent_id": "buyer_procure_agent_01",
        "seller_agent_id": "agent_seller_data_01",
        "seller_account_id": "acc_mock_seller_001",
        "amount_paise": amount_paise,
        "expected_record_count": 2,
        "ttl_seconds": 86400,
    })
    assert create_res.status_code == 200, f"Contract creation failed: {create_res.text}"
    contract_id = create_res.json()["contract_id"]
    print(f"\n1. Contract Created: {contract_id} (Amount: Rs {amount_paise/100:,.2f})")

    # 2. Deliver Manifest Signed with Seller Ed25519 Key
    seller_seed = hashlib.sha256(b"kuber_agent_seller_data_01_sec_key_v1").digest()
    seller_priv = ed25519.Ed25519PrivateKey.from_private_bytes(seller_seed)
    seller_pub = seller_priv.public_key().public_bytes_raw().hex()

    payload = [
        {"supplier_name": "Alpha Parts Ltd", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-001", "amount_paise": 1_250_000},
        {"supplier_name": "Beta Steel Ltd", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-002", "amount_paise": 1_250_000},
    ]
    canon_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    manifest_sig = seller_priv.sign(canon_bytes).hex()

    deliver_res = requests.post(f"{BASE_URL}/api/apex/contracts/deliver", headers=HEADERS, json={
        "contract_id": contract_id,
        "seller_agent_id": "agent_seller_data_01",
        "payload_records": payload,
        "manifest_signature": manifest_sig,
        "seller_public_key_hex": seller_pub,
    })
    assert deliver_res.status_code == 200, f"Payload delivery failed: {deliver_res.text}"
    deliver_json = deliver_res.json()
    leaf_hash = deliver_json["manifest_sha256"]
    print(f"2. Payload Delivered. Assertions Passed: {deliver_json['assertions_passed']}")

    # Prepare Checker Authorization Signature
    chk_seed = hashlib.sha256(b"kuber_cfo_autonomous_verifier_sec_key_v1").digest()
    chk_priv = ed25519.Ed25519PrivateKey.from_private_bytes(chk_seed)
    chk_pub = chk_priv.public_key().public_bytes_raw().hex()
    norm_leaf = leaf_hash.replace("sha256:", "").strip()
    intent = f"KEY:cfo_autonomous_verifier|CONTRACT:{contract_id}|LEAF:{norm_leaf}|APPROVER:cfo_autonomous_verifier|ACTION:RELEASE|VER:v1".encode()
    chk_sig = chk_priv.sign(intent).hex()

    # 3. Exploit Test: Injection of Client-Supplied Provider Records in Release Request Body
    test_utr = "HDFCN008822441"
    exploit_res = requests.post(f"{BASE_URL}/api/apex/contracts/release", headers=HEADERS, json={
        "contract_id": contract_id,
        "checker_id": "cfo_autonomous_verifier",
        "public_key_hex": chk_pub,
        "signature_hex": chk_sig,
        "bank_narration": f"NFX-RZR*SETTL*ST9901*{test_utr}*20260904",
        "require_narration_join": True,
        "provider_records": [{
            "expected_utr": test_utr,
            "amount_paise": amount_paise,
            "currency": "INR",
            "merchant_account_id": "acc_mock_seller_001",
            "settlement_status": "processed",
            "settlement_date": "2026-09-04",
        }],
    })
    print(f"3. Exploit Injection Attempt Status: {exploit_res.status_code}")
    assert exploit_res.status_code == 422, "Pydantic extra='forbid' must reject client-supplied provider_records with 422!"

    # 4. Zero Provider Records Match Guard
    refusal_res = requests.post(f"{BASE_URL}/api/apex/contracts/release", headers=HEADERS, json={
        "contract_id": contract_id,
        "checker_id": "cfo_autonomous_verifier",
        "public_key_hex": chk_pub,
        "signature_hex": chk_sig,
        "bank_narration": f"NFX-RZR*SETTL*ST9901*{test_utr}*20260904",
        "require_narration_join": True,
    })
    print(f"4. Missing Provider Record Guard: {refusal_res.status_code} ({refusal_res.json().get('detail')[:55]}...)")
    assert refusal_res.status_code == 412, "Release must fail-closed with 412 when no trusted server record exists!"

    # 5. Ingest Real Signed Razorpay Webhook Event (HMAC-SHA256 Provenance)
    now_ts = int(time.time())
    settlement_utr = f"HDFCN00{int(time.time()) % 1000000:06d}X"
    transfer_id = f"trf_hook_{contract_id[-8:]}"

    webhook_payload = {
        "entity": "event",
        "account_id": "acc_rzp_platform_001",
        "event": "transfer.processed",
        "created_at": now_ts,
        "payload": {
            "transfer": {
                "entity": {
                    "id": transfer_id,
                    "entity": "transfer",
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "processed",
                    "settled_at": now_ts,
                    "recipient": "acc_mock_seller_001",
                    "utr": settlement_utr,
                    "rail": "NEFT",
                    "notes": {
                        "apex_contract_id": contract_id,
                        "tenant_id": MERCHANT_ID,
                    },
                }
            }
        },
    }

    raw_webhook_body = json.dumps(webhook_payload, separators=(",", ":")).encode("utf-8")
    webhook_signature = hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_webhook_body, hashlib.sha256).hexdigest()

    hook_headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": webhook_signature,
        "X-Razorpay-Timestamp": str(now_ts),
        "X-Razorpay-Event-Id": f"evt_{transfer_id}",
    }

    hook_res = requests.post(f"{BASE_URL}/api/webhook/razorpay", data=raw_webhook_body, headers=hook_headers)
    assert hook_res.status_code == 200, f"Webhook failed: {hook_res.text}"
    hook_data = hook_res.json()
    print(f"5. Signed Webhook Ingested: status={hook_data['status']}, event_id={hook_data['event_id']}, hmac_verified={hook_data['signature_verified']}")

    # 6. Execute Release with Narration Memo Matching Webhook Record
    today_memo_str = datetime.fromtimestamp(now_ts, tz=timezone.utc).strftime("%Y%m%d")
    clearing_narration = f"NFX-RZR*SETTL*ST9901*{settlement_utr}*{today_memo_str}"

    release_res = requests.post(f"{BASE_URL}/api/apex/contracts/release", headers=HEADERS, json={
        "contract_id": contract_id,
        "checker_id": "cfo_autonomous_verifier",
        "public_key_hex": chk_pub,
        "signature_hex": chk_sig,
        "bank_narration": clearing_narration,
        "require_narration_join": True,
    })
    assert release_res.status_code == 200, f"Release failed: {release_res.text}"
    release_data = release_res.json()
    print(f"6. Release Transition: status={release_data['status']}")
    print(f"   Join Verified: {release_data['narration_join_audit']['join_verified']}")
    print(f"   Provider Record ID: {release_data['narration_join_audit']['provider_record_id']}")
    print(f"   Rail Type: {release_data['narration_join_audit']['rail_type']}")
    print(f"   Statement Date: {release_data['narration_join_audit']['statement_date']}")

    print("\n" + "=" * 80)
    print(" [SUCCESS] Complete Finance-Ops Control Loop Verified via Live Signed Webhook!")
    print("=" * 80)


if __name__ == "__main__":
    main()
