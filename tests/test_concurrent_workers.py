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
            "seller_agent_id": "agent_seller_01",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 100000,
        },
    )
    cid = c_resp.json()["contract_id"]

    # 2. Deliver valid payload
    client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_01",
            "payload_records": [
                {"supplier_name": "S1", "gstin": "27AAPCA1234F1ZV", "invoice_number": "INV-1", "amount_paise": 100000}
            ],
        },
    )

    # 3. 5 concurrent checkers attempt release
    def try_release(checker_name: str):
        return client.post(
            "/api/apex/contracts/release",
            json={"contract_id": cid, "checker_id": checker_name},
        )

    checkers = [f"cfo_checker_{i}" for i in range(5)]
    responses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_release, c) for c in checkers]
        for f in concurrent.futures.as_completed(futures):
            responses.append(f.result())

    status_codes = [r.status_code for r in responses]
    assert status_codes.count(200) == 1, f"Expected exactly 1 200 OK, got {status_codes.count(200)}"
    assert status_codes.count(409) == 4, f"Expected 4 409 Conflicts, got {status_codes.count(409)}"


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
            "seller_agent_id": "agent_seller_colluder",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 100000,
        },
    )
    cid = c_resp.json()["contract_id"]

    # Deliver valid payload
    client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "agent_seller_colluder",
            "payload_records": [
                {"supplier_name": "S1", "gstin": "27AAPCA1234F1ZV", "invoice_number": "INV-1", "amount_paise": 100000}
            ],
        },
    )

    # Buyer attempts to approve their own purchase
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={"contract_id": cid, "checker_id": "agent_buyer_colluder"},
    )
    assert r_resp.status_code == 403
    assert "Anti-Collusion Violation" in r_resp.json()["detail"]


# ── 4. Liveness Sweep Auto-Resolution ─────────────────────────────────────────

def test_liveness_sweep_auto_resolves_expired_contract(client):
    """
    Contracts past on_hold_until TTL MUST be swept to EXPIRED_AUTO_REFUNDED.
    """
    import kuber_recon.server as srv
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_01",
            "seller_agent_id": "agent_seller_01",
            "seller_account_id": "acc_seller_01",
            "amount_paise": 50000,
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

    # Check contract is now EXPIRED_AUTO_REFUNDED
    g_resp = client.get(f"/api/apex/contracts/{cid}")
    assert g_resp.json()["status"] == "EXPIRED_AUTO_REFUNDED"
    assert g_resp.json()["on_hold"] is False
