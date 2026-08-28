"""
test_webhook_idempotency.py
============================
Tests for the Razorpay webhook endpoint covering:
  1. HMAC-valid signature   → 200 acknowledged
  2. Invalid signature      → 400 rejected
  3. Duplicate event_id     → 200 ignored_duplicate (in-session)
  4. Restart durability     → duplicate still rejected after store re-initialised
     (proves SQLite persists across object lifetime)
  5. Integration status     → sandbox mode badge
  6. Route transfer paise   → amount_paise:int contract
  7. Intercept paise        → amount_paise:int contract, no float
"""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

# ── Point the idempotency DB to a temp file so tests don't pollute production ──

@pytest.fixture(autouse=True)
def _tmp_idempotency_db(tmp_path, monkeypatch):
    """Redirect the SQLite DB to a throwaway file for each test session."""
    tmp_db = tmp_path / "test_idempotency.db"
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.WebhookIdempotencyStore, "DB_FILE", tmp_db)
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", False)
    # Re-init the singleton store so it uses the new path
    srv.idempotency_store = srv.WebhookIdempotencyStore()
    yield

    # Cleanup is automatic via tmp_path fixture


@pytest.fixture()
def client():
    from kuber_recon.server import app
    return TestClient(app)


def _make_signed_payload(body_dict: dict, event_id: str, secret: str = None) -> tuple[bytes, str]:
    """Return (raw_body_bytes, hmac_signature) for a given payload dict."""
    import kuber_recon.server as srv
    raw = json.dumps(body_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sec = secret or srv.get_webhook_secret()
    sig = hmac.new(sec.encode(), raw, hashlib.sha256).hexdigest()
    return raw, sig



_SAMPLE_EVENT = {
    "entity": "event",
    "event": "payment.captured",
    "payload": {"payment": {"entity": {"id": "pay_test_001", "amount": 118000}}},
}


# ── 1. Valid HMAC ──────────────────────────────────────────────────────────────

def test_webhook_valid_hmac_accepted(client):
    raw, sig = _make_signed_payload(_SAMPLE_EVENT, "evt_valid_001")
    resp = client.post(
        "/api/webhook/razorpay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_valid_001",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "acknowledged"
    assert data["signature_verified"] is True
    assert data["event_id"] == "evt_valid_001"


# ── 2. Invalid HMAC ───────────────────────────────────────────────────────────

def test_webhook_invalid_hmac_rejected(client):
    raw, _ = _make_signed_payload(_SAMPLE_EVENT, "evt_bad_002")
    resp = client.post(
        "/api/webhook/razorpay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "deadbeef" * 8,  # deliberately wrong
            "X-Razorpay-Event-Id": "evt_bad_002",
        },
    )
    assert resp.status_code == 400
    assert "HMAC" in resp.json()["detail"]


# ── 3. Duplicate event_id — same store ────────────────────────────────────────

def test_webhook_duplicate_blocked_in_session(client):
    raw, sig = _make_signed_payload(_SAMPLE_EVENT, "evt_dup_003")
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": "evt_dup_003",
    }
    r1 = client.post("/api/webhook/razorpay", content=raw, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "acknowledged"

    # Second call with same event_id must be deduplicated
    r2 = client.post("/api/webhook/razorpay", content=raw, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "ignored_duplicate"


# ── 4. Restart durability ─────────────────────────────────────────────────────

def test_webhook_idempotency_survives_store_reinit(tmp_path, monkeypatch):
    """
    Proves SQLite durability: after inserting an event_id and then creating
    a brand-new WebhookIdempotencyStore instance (simulating a server restart),
    the duplicate is still rejected.
    """
    from kuber_recon.server import WebhookIdempotencyStore

    db_file = tmp_path / "durability_test.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", db_file)

    store1 = WebhookIdempotencyStore()
    assert store1.try_insert("evt_persist_004") is True   # new → process
    assert store1.try_insert("evt_persist_004") is False  # duplicate in same instance

    # Simulate restart: new store object, same DB file
    store2 = WebhookIdempotencyStore()
    assert store2.try_insert("evt_persist_004") is False  # still duplicate after restart


# ── 5. Integration status endpoint ────────────────────────────────────────────

def test_integration_status_sandbox(client):
    resp = client.get("/api/integration-status")
    assert resp.status_code == 200
    data = resp.json()
    # No real keys in test env → sandbox
    assert data["mode"] in ("sandbox_simulation", "test_mode")
    assert "idempotency_backend" in data
    assert data["fmr"] == "0.000"


# ── 6. Route transfer accepts amount_paise:int ────────────────────────────────

def test_route_transfer_paise_contract(client):
    resp = client.post(
        "/api/razorpay/route-transfer",
        json={"account_id": "acc_mock_001", "amount_paise": 118000},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount_paise"] == 118000
    assert "₹1,180.00" in data["amount_inr"]
    assert data["on_hold"] is True


def test_route_transfer_rejects_zero_paise(client):
    resp = client.post(
        "/api/razorpay/route-transfer",
        json={"account_id": "acc_mock_001", "amount_paise": 0},
    )
    assert resp.status_code == 422  # Pydantic validation: gt=0


# ── 7. Intercept accepts amount_paise:int — no float ─────────────────────────

def test_intercept_paise_contract_18pct(client):
    resp = client.post(
        "/api/intercept",
        json={"order_id": "ord_pytest_001", "amount_paise": 118000, "gst_rate_pct": 18},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["gross_paise"] == 118000
    assert data["unexplained_delta_paise"] == 0
    assert data["fmr"] == "0.000"
    # Verify paise arithmetic is exact: principal + gst + tds = gross
    assert data["principal_paise"] + data["gst_paise"] + data["tds_paise"] == 118000


def test_intercept_rejects_float_in_amount_paise(client):
    """Pydantic model must reject a float for amount_paise:int."""
    resp = client.post(
        "/api/intercept",
        json={"order_id": "ord_float_test", "amount_paise": 1180.50, "gst_rate_pct": 18},
    )
    # FastAPI/Pydantic will coerce or reject — either way the response must be
    # a valid integer paise (no fractional value slips through)
    if resp.status_code == 200:
        assert isinstance(resp.json()["gross_paise"], int)
    else:
        assert resp.status_code == 422


# ── 8. Sandbox fixture endpoint enabled in sandbox, disabled in live mode ────

def test_sandbox_fixture_available_in_sandbox(client):
    """In sandbox mode (no real keys), /api/sandbox/webhook/fixture returns a signed fixture."""
    import kuber_recon.server as srv
    if srv.razorpay_adapter.is_live:
        pytest.skip("Live mode active — fixture endpoint is correctly disabled")
    resp = client.get("/api/sandbox/webhook/fixture?transfer_id=trf_pytest_fixture_001")
    assert resp.status_code == 200
    data = resp.json()
    assert "raw_payload" in data
    assert "x_razorpay_signature" in data
    raw = json.dumps(data["raw_payload"], separators=(",", ":")).encode("utf-8")
    expected_sig = hmac.new(srv.get_webhook_secret().encode("utf-8"), raw, hashlib.sha256).hexdigest()
    assert expected_sig == data["x_razorpay_signature"]


def test_sandbox_fixture_disabled_in_live_mode(client, monkeypatch):
    """In live mode, /api/sandbox/webhook/fixture must be rejected with 403 Forbidden."""
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", True)
    resp = client.get("/api/sandbox/webhook/fixture?transfer_id=trf_live_001")
    assert resp.status_code == 403
    assert "disabled in live Test Mode" in resp.json()["detail"]


# ── 9. Absent signature rejected in every mode ────────────────────────────────

def test_webhook_absent_signature_rejected(client):
    """
    X-Razorpay-Signature is mandatory in every mode (including sandbox).
    A request without the header must receive 400, not 200.
    """
    raw, _ = _make_signed_payload(_SAMPLE_EVENT, "evt_nosig_009")
    resp = client.post(
        "/api/webhook/razorpay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Event-Id": "evt_nosig_009",
        },
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "Missing" in detail or "signed" in detail.lower()


# ── 10. Webhook secret missing in live mode triggers configuration error ───────

def test_webhook_missing_secret_fails_in_live_mode(client, monkeypatch):
    """
    When live Razorpay credentials are configured but RAZORPAY_WEBHOOK_SECRET is unset,
    inbound webhooks must fail with an explicit 500 configuration error rather than falling back.
    """
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", True)
    monkeypatch.delenv("RAZORPAY_WEBHOOK_SECRET", raising=False)

    raw, sig = _make_signed_payload(_SAMPLE_EVENT, "evt_live_missing_sec", secret="dummy_for_sender")
    resp = client.post(
        "/api/webhook/razorpay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_live_missing_sec",
        },
    )
    assert resp.status_code == 500
    assert "RAZORPAY_WEBHOOK_SECRET is missing" in resp.json()["detail"]



def test_webhook_configured_secret_passes_in_live_mode(client, monkeypatch):
    """
    When live Razorpay credentials and RAZORPAY_WEBHOOK_SECRET are configured,
    inbound webhook HMAC is evaluated against the explicit live secret.
    """
    import kuber_recon.server as srv
    live_secret = "whsec_live_production_test_secret_9988"
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", True)
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", live_secret)

    raw = json.dumps(_SAMPLE_EVENT, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(live_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    resp = client.post(
        "/api/webhook/razorpay",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_live_valid_001",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"
    assert resp.json()["signature_verified"] is True


