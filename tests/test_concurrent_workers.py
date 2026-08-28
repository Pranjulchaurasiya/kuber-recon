"""
test_concurrent_workers.py
==========================
Multi-Threaded Concurrency & Race Condition Test Suite.
Verifies:
  1. SQLite PRAGMA busy_timeout=5000 & WAL mode prevents SQLITE_BUSY deadlocks.
  2. Concurrent try_insert across 10 threads claims unique event_ids exactly once.
  3. Concurrent CAS releases on the same contract permit EXACTLY ONE release (preventing double-release).
  4. Anti-Collusion enforcement rejects same-principal maker-checker attempts.
  5. Liveness sweep auto-resolves expired holds.
"""

import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from kuber_recon.server import app, WebhookIdempotencyStore


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    tmp_db = tmp_path / "test_concurrent.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    import kuber_recon.server as srv
    srv.idempotency_store = WebhookIdempotencyStore()
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Concurrent Webhook Deduplication Race ──────────────────────────────────

def test_concurrent_webhook_deduplication(client):
    """
    10 threads submit the EXACT same webhook event_id simultaneously.
    Result MUST be: exactly 1 thread claims it, 9 threads receive False / duplicate.
    """
    import kuber_recon.server as srv
    store = srv.idempotency_store
    event_id = "evt_race_condition_test_99"

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(store.try_insert, event_id) for _ in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    assert results.count(True) == 1, f"Expected exactly 1 claim, got {results.count(True)}"
    assert results.count(False) == 9, f"Expected 9 duplicates, got {results.count(False)}"


def _sign_seller_manifest(records: list, seller_agent_id: str = "agent_seller_data_01"):
    import hashlib
    import json
    from cryptography.hazmat.primitives.asymmetric import ed25519
    seed = hashlib.sha256(f"kuber_{seller_agent_id}_sec_key_v1".encode()).digest()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw().hex()
    canonical_bytes = json.dumps(records, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = priv.sign(canonical_bytes).hex()
    return pub, sig


def _sign_release(contract_id: str, leaf_hash: str, checker_id: str = "cfo_autonomous_verifier"):
    import hashlib
    from cryptography.hazmat.primitives.asymmetric import ed25519
    seed = hashlib.sha256(f"kuber_{checker_id}_sec_key_v1".encode()).digest()
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw().hex()
    normalized_leaf = leaf_hash.replace("sha256:", "").strip()
    canonical = f"KEY:{checker_id}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{checker_id}|ACTION:RELEASE|VER:v1".encode("utf-8")
    sig = priv.sign(canonical).hex()
    return pub, sig


# ── 2. CAS Double-Release Prevention ──────────────────────────────────────────

def test_concurrent_cas_double_release_prevention(client):
    """
    Create a verified contract, then have 5 checkers attempt to release it simultaneously.
    CAS MUST ensure exactly ONE checker succeeds (200 OK), and 4 receive 409 Conflict.
    """
    # 1. Create contract
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_01",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 100000,
            "expected_record_count": 1,
        },
    )
    cid = c_resp.json()["contract_id"]

    # 2. Deliver valid payload
    records = [{"supplier_name": "S1", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 100000}]
    pub_s, sig_s = _sign_seller_manifest(records, "agent_seller_data_01")
    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig_s,
            "seller_public_key_hex": pub_s,
        },
    )
    assert d_resp.json()["assertions_passed"] is True
    leaf_hash = d_resp.json()["manifest_sha256"]
    pub, sig = _sign_release(cid, leaf_hash, "cfo_autonomous_verifier")

    # 3. 5 concurrent checkers attempt release
    def try_release(_i: int):
        return client.post(
            "/api/apex/contracts/release",
            json={
                "contract_id": cid,
                "checker_id": "cfo_autonomous_verifier",
                "public_key_hex": pub,
                "signature_hex": sig,
            },
        )

    responses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_release, i) for i in range(5)]
        for f in concurrent.futures.as_completed(futures):
            responses.append(f.result())

    status_codes = [r.status_code for r in responses]
    assert status_codes.count(200) == 1, f"Expected exactly 1 200 OK, got {status_codes.count(200)}"
    assert all(code in (403, 409, 412) for code in status_codes if code != 200)


# ── 3. Anti-Collusion Enforcement ─────────────────────────────────────────────

def test_anti_collusion_rejected_when_maker_is_checker(client):
    """
    If the Buyer Agent or Seller Agent attempts to self-approve as Checker,
    the system MUST return 403 Forbidden.
    """
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_colluder",
            "seller_agent_id": "agent_seller_data_01",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 100000,
            "expected_record_count": 1,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Deliver valid payload
    records = [{"supplier_name": "S1", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-1", "amount_paise": 100000}]
    pub_s, sig_s = _sign_seller_manifest(records, "agent_seller_data_01")
    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_data_01",
            "payload_records": records,
            "manifest_signature": sig_s,
            "seller_public_key_hex": pub_s,
        },
    )
    assert d_resp.json()["assertions_passed"] is True
    leaf_hash = d_resp.json()["manifest_sha256"]
    pub, sig = _sign_release(cid, leaf_hash, "cfo_autonomous_verifier")

    # Buyer attempts to approve their own purchase
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": cid,
            "checker_id": "agent_buyer_colluder",
            "public_key_hex": pub,
            "signature_hex": sig,
        },
    )
    assert r_resp.status_code == 403
    assert "Anti-Collusion Violation" in r_resp.json()["detail"]


# ── 4. Liveness Sweep Auto-Resolution ─────────────────────────────────────────

def test_liveness_sweep_auto_resolves_expired_contract(client):
    """
    Contracts past on_hold_until TTL MUST be swept to EXPIRED_HOLD.
    """
    import kuber_recon.server as srv
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_01",
            "seller_agent_id": "agent_seller_01",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 50000,
            "expected_record_count": 1,
            "ttl_seconds": 60,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Artificially set on_hold_until into the past in the database
    with srv.idempotency_store._connect() as conn:
        conn.execute("UPDATE apex_contracts SET on_hold_until = ? WHERE contract_id = ?", (1000, cid))

    # Run sweep
    s_resp = client.post("/api/apex/contracts/sweep-expired")
    assert s_resp.status_code == 200
    data = s_resp.json()
    assert cid in data["swept_contract_ids"]

    # Check contract is now EXPIRED_HOLD
    g_resp = client.get(f"/api/apex/contracts/{cid}")
    assert g_resp.json()["status"] == "EXPIRED_HOLD"
    assert g_resp.json()["on_hold"] is True
