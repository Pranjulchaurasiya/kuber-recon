"""
test_apex_assurance.py
======================
Unit & Resilience Tests for APEX Assurance:
  1. Contract initialization with integer paise + Route on_hold: true + TTL + expected_record_count
  2. Delivery assertion failure -> Honest Refusal (settlement stays on_hold: true)
  3. Clean delivery verification -> Settlement release (PATCH on_hold: false)
  4. Release blocked if assertions not passed (412 Precondition Failed)
  5. Memory bounds enforcement (>5MB rejected with 413)
  6. Non-LLM GSTIN Mod-36 checksum mathematical correctness
  7. Mandatory Seller Ed25519 signature & key pinning enforcement
  8. Seller identity mismatch rejection (403 Forbidden)
  9. Enforced 500-record batch contract invariants
"""

import hashlib
import hmac
import json

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from kuber_recon.assurance import (
    validate_gstin_checksum,
)
from kuber_recon.server import WebhookIdempotencyStore, app, idempotency_store


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    tmp_db = tmp_path / "test_apex.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", False)
    srv.idempotency_store = WebhookIdempotencyStore()
    yield


@pytest.fixture
def client():
    return TestClient(app)



# ── Cryptographic Signing Helpers ─────────────────────────────────────────────

def _sign_seller_manifest(records: list, seller_agent_id: str = "agent_seller_data_01"):
    seed = hashlib.sha256(f"kuber_{seller_agent_id}_sec_key_v1".encode()).digest()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw().hex()
    canonical_bytes = json.dumps(records, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = priv.sign(canonical_bytes).hex()
    return pub, sig


def _sign_release(contract_id: str, leaf_hash: str, checker_id: str = "cfo_autonomous_verifier"):
    seed = hashlib.sha256(f"kuber_{checker_id}_sec_key_v1".encode()).digest()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw().hex()
    normalized_leaf = leaf_hash.replace("sha256:", "").strip()
    canonical = f"KEY:{checker_id}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{checker_id}|ACTION:RELEASE|VER:v1".encode()
    sig = priv.sign(canonical).hex()
    return pub, sig


# ── 1. Mod-36 GSTIN Checksum Tests ────────────────────────────────────────────

def test_gstin_mod36_checksum_valid():
    # Valid Indian GSTIN format with exact Mod-36 checksum
    assert validate_gstin_checksum("27AAPFU0939F1ZV") is True


def test_gstin_mod36_checksum_invalid():
    # Corrupted checksum character
    assert validate_gstin_checksum("27AAPCA1234F1Z9") is False
    # Wrong length / format
    assert validate_gstin_checksum("INVALID_GSTIN") is False
    assert validate_gstin_checksum("") is False


# ── 2. Contract Creation Flow ─────────────────────────────────────────────────

def test_apex_contract_creation(client):
    resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_leads_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,  # ₹25,000.00
            "expected_record_count": 500,
            "ttl_seconds": 86400,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HELD"
    assert data["on_hold"] is True
    assert data["amount_paise"] == 2500000
    assert data["expected_record_count"] == 500
    assert "₹25,000.00" in data["amount_inr"]
    assert "trf_" in data["transfer_id"]


# ── 3. Malicious / Corrupted Delivery -> Honest Refusal ───────────────────────

def test_apex_delivery_refusal_on_corrupted_gstin(client):
    # Step 1: Create contract with mandatory expected_record_count
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 10,
        },
    )
    assert c_resp.status_code == 200
    contract_id = c_resp.json()["contract_id"]

    # Step 2: Deliver 10 records, but 2 have corrupted GSTINs
    records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPFU0939F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 250000}
        for i in range(8)
    ]
    # Add corrupted records
    records.append({"supplier_name": "Corrupted 1", "gstin": "27AAPCA1234F1Z9", "invoice_number": "INV-BAD1", "amount_paise": 250000})
    records.append({"supplier_name": "Corrupted 2", "gstin": "INVALID_GST", "invoice_number": "INV-BAD2", "amount_paise": 250000})

    pub, sig = _sign_seller_manifest(records, "agent_seller_data_01")

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": contract_id,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig,
            "seller_public_key_hex": pub,
        },
    )
    assert d_resp.status_code == 412
    data = d_resp.json()
    assert data["assertions_passed"] is False
    assert data["status"] == "REFUSED"
    assert data["on_hold"] is True
    assert data["failed_records"] >= 2
    assert data["valid_records"] == 8
    assert "CERT:REFUSAL:APEX" in data["refusal_certificate"]

    # Step 3: Attempting release MUST be blocked with 412 Precondition Failed
    pub_rel, sig_rel = _sign_release(contract_id, data["manifest_sha256"])
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": contract_id,
            "checker_id": "cfo_autonomous_verifier",
            "public_key_hex": pub_rel,
            "signature_hex": sig_rel,
        },
    )
    assert r_resp.status_code == 412
    assert "delivery assertions have not passed" in r_resp.json()["detail"]


# ── 4. 100% Clean Delivery -> Verified Release ────────────────────────────────

def test_apex_delivery_release_on_100pct_valid(client):
    # Step 1: Create contract with mandatory expected_record_count
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_good",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 10,
        },
    )
    assert c_resp.status_code == 200
    contract_id = c_resp.json()["contract_id"]

    # Step 2: Deliver 10 clean valid records matching exact contract amount ₹25,000 (250,000 paise x 10)
    records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPFU0939F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 250000}
        for i in range(10)
    ]

    pub, sig = _sign_seller_manifest(records, "agent_seller_good")

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": contract_id,
            "seller_agent_id": "agent_seller_good",
            "payload_records": records,
            "manifest_signature": sig,
            "seller_public_key_hex": pub,
        },
    )
    assert d_resp.status_code == 200
    d_data = d_resp.json()
    assert d_data["assertions_passed"] is True
    assert d_data["seller_signature_verified"] is True
    assert d_data["valid_records"] == 10
    assert d_data["failed_records"] == 0

    # Step 3: Execute Release with authenticated Ed25519 signature
    pub_rel, sig_rel = _sign_release(contract_id, d_data["manifest_sha256"])
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": contract_id,
            "checker_id": "cfo_autonomous_verifier",
            "public_key_hex": pub_rel,
            "signature_hex": sig_rel,
        },
    )
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["status"] == "RELEASING"
    assert r_data["contract_status"] == "RELEASING"
    assert r_data["signature_verified"] is True
    assert r_data["amount_paise"] == 2500000


# ── 5. Seller Security Invariant Enforcements ─────────────────────────────────

def test_apex_delivery_refused_on_missing_signature(client):
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 1,
        },
    )
    cid = c_resp.json()["contract_id"]
    records = [{"supplier_name": "S1", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 2500000}]

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            # No signature or public key provided -> Rejected with HTTP 422 Unprocessable Entity
        },
    )
    assert d_resp.status_code == 422


def test_apex_delivery_refused_on_unpinned_seller_key(client):
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 1,
        },
    )
    cid = c_resp.json()["contract_id"]
    records = [{"supplier_name": "S1", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 2500000}]

    # Valid Ed25519 key, but NOT the pinned key for agent_seller_data_01
    seed = hashlib.sha256(b"unpinned_rogue_seller_seed").digest()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw().hex()
    canonical_bytes = json.dumps(records, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = priv.sign(canonical_bytes).hex()

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig,
            "seller_public_key_hex": pub,
        },
    )
    assert d_resp.status_code == 412
    data = d_resp.json()
    assert data["assertions_passed"] is False
    assert data["seller_signature_verified"] is False
    assert any("Seller Key Pinning Violation" in v for v in data["violation_samples"])


def test_apex_delivery_rejected_on_seller_identity_mismatch(client):
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 1,
        },
    )
    cid = c_resp.json()["contract_id"]
    records = [{"supplier_name": "S1", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 2500000}]
    pub, sig = _sign_seller_manifest(records, "agent_seller_good")

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_good",  # Mismatch with contract seller_agent_id
            "payload_records": records,
            "manifest_signature": sig,
            "seller_public_key_hex": pub,
        },
    )
    assert d_resp.status_code == 403
    assert "Seller Identity Mismatch" in d_resp.json()["detail"]


# ── 6. 500-Record Batch Contract Invariant ───────────────────────────────────

def test_apex_500_record_contract_enforcement(client):
    # Contract stipulates exactly 500 records totaling ₹25,000.00 (2,500,000 paise)
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 500,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Delivery of only 5 records (even if money matches) MUST be refused due to record count invariant (412)
    partial_records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPFU0939F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 500000}
        for i in range(5)
    ]
    pub_p, sig_p = _sign_seller_manifest(partial_records, "agent_seller_data_01")
    d_partial = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": partial_records,
            "manifest_signature": sig_p,
            "seller_public_key_hex": pub_p,
        },
    )
    assert d_partial.status_code == 412
    assert d_partial.json()["assertions_passed"] is False
    assert any("Contract Record Count Mismatch" in v for v in d_partial.json()["violation_samples"])

    # Full 500-record delivery matching exact count and amount
    full_records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPFU0939F1ZV", "invoice_number": f"INV-{i:05d}", "amount_paise": 5000}
        for i in range(500)
    ]
    pub_f, sig_f = _sign_seller_manifest(full_records, "agent_seller_data_01")
    d_full = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": full_records,
            "manifest_signature": sig_f,
            "seller_public_key_hex": pub_f,
        },
    )
    assert d_full.status_code == 200
    data = d_full.json()
    assert data["assertions_passed"] is True
    assert data["valid_records"] == 500
    assert data["total_delivered_paise"] == 2500000
    assert data["seller_signature_verified"] is True


# ── 7. Memory Bounds (<5MB) Enforcement ───────────────────────────────────────

def test_apex_payload_exceeding_bounds_rejected(client):
    large_records = [
        {"supplier_name": "A" * 10000, "gstin": "27AAPCA1234F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 100}
        for i in range(600)
    ]

    resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": "apex_cnt_large",
            "seller_agent_id": "agent_seller_large",
            "payload_records": large_records,
            "manifest_signature": "a" * 128,
            "seller_public_key_hex": "b" * 64,
        },
    )
    assert resp.status_code == 413
    assert "memory bounds" in resp.json()["detail"]


# ── 8. SQLite Engine-Level Append-Only Trigger Verification ────────────────────

def test_audit_log_database_triggers_prevent_tampering():
    import sqlite3

    import pytest

    from kuber_recon.server import WebhookIdempotencyStore

    store = WebhookIdempotencyStore()
    with store._lock, store._connect() as conn:
        conn.execute(
            "INSERT INTO apex_contract_audit_log (contract_id, status, proof_hash, assertions_passed, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("cnt_trigger_test_001", "HELD", "proof_hash_initial", 0, 1000),
        )
        cur = conn.execute("SELECT id FROM apex_contract_audit_log WHERE contract_id = 'cnt_trigger_test_001'")
        row = cur.fetchone()
        assert row is not None
        row_id = row[0]

        # 1. Direct UPDATE must be aborted by SQLite trigger
        with pytest.raises(sqlite3.DatabaseError, match="apex_contract_audit_log is append-only"):
            conn.execute("UPDATE apex_contract_audit_log SET status = 'TAMPERED' WHERE id = ?", (row_id,))

        # 2. Direct DELETE must be aborted by SQLite trigger
        with pytest.raises(sqlite3.DatabaseError, match="apex_contract_audit_log is append-only"):
            conn.execute("DELETE FROM apex_contract_audit_log WHERE id = ?", (row_id,))


# ── 9. Contract Status Polling & Authoritative Webhook Lifecycle ───────────────

def test_apex_contract_lifecycle_polling_to_released(client):
    # 1. Create Contract
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_99",
            "amount_paise": 2500000,
            "expected_record_count": 500,
            "ttl_seconds": 86400,
        },
    )
    assert c_resp.status_code == 200
    cid = c_resp.json()["contract_id"]
    trf_id = c_resp.json()["transfer_id"]

    # Poll status -> HELD
    p1 = client.get(f"/api/apex/contracts/{cid}")
    assert p1.status_code == 200
    assert p1.json()["status"] == "HELD"

    # 2. Deliver Valid 500 Records
    clean_records = [
        {"supplier_name": "Supplier A", "gstin": "27AAPFU0939F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 5000}
        for i in range(500)
    ]
    pub_k, sig_k = _sign_seller_manifest(clean_records, "agent_seller_data_01")
    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": clean_records,
            "manifest_signature": sig_k,
            "seller_public_key_hex": pub_k,
        },
    )
    assert d_resp.status_code == 200
    assert d_resp.json()["assertions_passed"] is True

    # 3. Release Hold (Sign with CFO key)
    leaf_hash = d_resp.json()["manifest_sha256"].replace("sha256:", "")
    cfo_pub, cfo_sig = _sign_release(cid, leaf_hash, "cfo_autonomous_verifier")

    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": cid,
            "checker_id": "cfo_autonomous_verifier",
            "public_key_hex": cfo_pub,
            "signature_hex": cfo_sig,
        },
    )
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "RELEASING"

    # Poll status -> RELEASING
    p2 = client.get(f"/api/apex/contracts/{cid}")
    assert p2.status_code == 200
    assert p2.json()["status"] == "RELEASING"

    # 4. Ingest Authoritative transfer.processed Webhook
    from kuber_recon.server import get_webhook_secret
    wh_payload = {
        "entity": "event",
        "account_id": "acc_mock_seller_99",
        "event": "transfer.processed",
        "contains": ["transfer"],
        "payload": {
            "transfer": {
                "entity": {
                    "id": trf_id,
                    "entity": "transfer",
                    "amount": 2500000,
                    "currency": "INR",
                    "status": "processed",
                    "notes": {"contract_id": cid},
                }
            }
        },
    }
    raw_bytes = json.dumps(wh_payload).encode("utf-8")
    sig = hmac.new(get_webhook_secret().encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    wh_resp = client.post(
        "/api/webhook/razorpay",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": f"evt_lifecycle_{cid}",
        },
    )
    assert wh_resp.status_code == 200

    # 5. Authoritative Polling confirms RELEASED and complete Audit Trail
    p3 = client.get(f"/api/apex/contracts/{cid}")
    assert p3.status_code == 200
    res_data = p3.json()
    assert res_data["status"] == "RELEASED"
    assert res_data["webhook_event_id"] == f"evt_lifecycle_{cid}"
    assert "audit_trail" in res_data
    statuses = [entry["status"] for entry in res_data["audit_trail"]]
    assert statuses == ["HELD", "VERIFYING", "RELEASING", "RELEASED"]


# ── 15. Complete Immutable Audit Coverage Across All State Transitions ────────

def test_audit_trail_recorded_on_refusal(client):
    """Proves that contract creation and refusal each append an audit log row."""
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_001",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_001",
            "amount_paise": 5000,
            "expected_record_count": 1,
            "ttl_seconds": 3600,
        },
    )
    cid = c_resp.json()["contract_id"]

    bad_records = [{"supplier_name": "Bad", "gstin": "INVALID", "invoice_number": "INV-1", "amount_paise": 5000}]
    pub_k, sig_k = _sign_seller_manifest(bad_records, "agent_seller_data_01")
    client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": bad_records,
            "manifest_signature": sig_k,
            "seller_public_key_hex": pub_k,
        },
    )

    p = client.get(f"/api/apex/contracts/{cid}")
    assert p.status_code == 200
    trail = p.json()["audit_trail"]
    statuses = [entry["status"] for entry in trail]
    assert statuses == ["HELD", "REFUSED"]


def test_audit_trail_recorded_on_expired_sweep(client):
    """Proves that liveness sweep forces EXPIRED_HOLD and appends an audit log entry."""
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_002",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_002",
            "amount_paise": 5000,
            "expected_record_count": 1,
            "ttl_seconds": 60,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Manually backdate on_hold_until in DB
    with idempotency_store._lock, idempotency_store._connect() as conn:
        conn.execute("UPDATE apex_contracts SET on_hold_until = 0 WHERE contract_id = ?", (cid,))

    sweep_resp = client.post("/api/apex/contracts/sweep-expired")
    assert sweep_resp.status_code == 200
    assert cid in sweep_resp.json()["swept_contract_ids"]

    p = client.get(f"/api/apex/contracts/{cid}")
    trail = p.json()["audit_trail"]
    statuses = [entry["status"] for entry in trail]
    assert statuses == ["HELD", "EXPIRED_HOLD"]


def test_audit_trail_recorded_on_gateway_failure(client, monkeypatch):
    """Proves that gateway exception transitions to RELEASE_PENDING_RECONCILIATION with audit logging."""
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_003",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_003",
            "amount_paise": 5000,
            "expected_record_count": 1,
            "ttl_seconds": 3600,
        },
    )
    cid = c_resp.json()["contract_id"]

    records = [{"supplier_name": "Good", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 5000}]
    pub_k, sig_k = _sign_seller_manifest(records, "agent_seller_data_01")
    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig_k,
            "seller_public_key_hex": pub_k,
        },
    )
    assert d_resp.status_code == 200

    leaf_hash = d_resp.json()["manifest_sha256"].replace("sha256:", "")
    cfo_pub, cfo_sig = _sign_release(cid, leaf_hash, "cfo_autonomous_verifier")

    # Force modify_transfer_hold to raise an exception
    import kuber_recon.server as srv
    def mock_fail(*args, **kwargs):
        raise RuntimeError("Gateway network error")
    monkeypatch.setattr(srv.razorpay_adapter, "modify_transfer_hold", mock_fail)

    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": cid,
            "checker_id": "cfo_autonomous_verifier",
            "public_key_hex": cfo_pub,
            "signature_hex": cfo_sig,
        },
    )
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "RELEASE_PENDING_RECONCILIATION"

    p = client.get(f"/api/apex/contracts/{cid}")
    trail = p.json()["audit_trail"]
    statuses = [entry["status"] for entry in trail]
    assert statuses == ["HELD", "VERIFYING", "RELEASING", "RELEASE_PENDING_RECONCILIATION"]


def test_cas_conflict_does_not_create_audit_record(client):
    """Proves that CAS version mismatches or invalid status transitions do not write orphan audit logs."""
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_cas_01",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_cas",
            "amount_paise": 5000,
            "expected_record_count": 1,
            "ttl_seconds": 3600,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Initial audit log must have exactly 1 record (HELD)
    trail_initial = idempotency_store.get_audit_trail(cid)
    assert len(trail_initial) == 1
    assert trail_initial[0]["status"] == "HELD"

    # Attempt CAS transition with incorrect expected_version (999) -> Must fail and write 0 audit records
    res_version_mismatch = idempotency_store.transition_contract_state(
        contract_id=cid,
        expected_status="HELD",
        target_status="RELEASING",
        expected_version=999,
    )
    assert res_version_mismatch is False
    assert len(idempotency_store.get_audit_trail(cid)) == 1

    # Attempt CAS transition with incorrect expected_status ("RELEASED" instead of "HELD") -> Must fail and write 0 audit records
    res_status_mismatch = idempotency_store.transition_contract_state(
        contract_id=cid,
        expected_status="RELEASED",
        target_status="RELEASING",
        expected_version=1,
    )
    assert res_status_mismatch is False
    assert len(idempotency_store.get_audit_trail(cid)) == 1


def test_webhook_mismatched_transfer_id_does_not_finalize(client):
    """Proves that a webhook with an unrelated transfer_id does not finalize a RELEASING contract."""
    # 1. Create contract
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_mismatch",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_mock_seller_mismatch",
            "amount_paise": 5000,
            "expected_record_count": 1,
            "ttl_seconds": 3600,
        },
    )
    cid = c_resp.json()["contract_id"]

    # 2. Deliver valid payload

    records = [{"supplier_name": "Good", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 5000}]
    pub_k, sig_k = _sign_seller_manifest(records, "agent_seller_data_01")
    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig_k,
            "seller_public_key_hex": pub_k,
        },
    )
    assert d_resp.status_code == 200

    # 3. Release -> RELEASING
    leaf_hash = d_resp.json()["manifest_sha256"].replace("sha256:", "")
    cfo_pub, cfo_sig = _sign_release(cid, leaf_hash, "cfo_autonomous_verifier")
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": cid,
            "checker_id": "cfo_autonomous_verifier",
            "public_key_hex": cfo_pub,
            "signature_hex": cfo_sig,
        },
    )
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "RELEASING"

    # 4. Inbound webhook with mismatched transfer_id
    from kuber_recon.server import get_webhook_secret
    mismatched_wh = {
        "entity": "event",
        "account_id": "acc_mock_seller_mismatch",
        "event": "transfer.processed",
        "contains": ["transfer"],
        "payload": {
            "transfer": {
                "entity": {
                    "id": "trf_completely_unrelated_99999",
                    "entity": "transfer",
                    "amount": 5000,
                    "currency": "INR",
                    "status": "processed",
                }
            }
        },
    }
    raw_bytes = json.dumps(mismatched_wh).encode("utf-8")
    sig = hmac.new(get_webhook_secret().encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    wh_resp = client.post(
        "/api/webhook/razorpay",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_mismatched_transfer_001",
        },
    )
    assert wh_resp.status_code == 200

    # Contract must REMAIN in RELEASING state (not RELEASED)
    p = client.get(f"/api/apex/contracts/{cid}")
    assert p.status_code == 200
    assert p.json()["status"] == "RELEASING"
    assert p.json()["on_hold"] is True
    assert p.json()["webhook_event_id"] is None





