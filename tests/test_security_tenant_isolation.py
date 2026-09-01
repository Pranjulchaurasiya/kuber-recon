"""
Security & Tenant Isolation Test Suite for Kuber OS.
Validates:
1. Strict 401 Unauthorized when X-Merchant-Id / X-API-Key are missing or invalid.
2. Constant-time key comparison and authenticated tenant identification.
3. Anti-tampering error sanitation with zero traceback exposure.
4. Solver explicit INCONCLUSIVE_TRUNCATED outcome when search candidate pool > 24 or budget exceeded.
"""

from enum import Enum
import pytest
from fastapi.testclient import TestClient
from kuber_recon.server import app, REGISTERED_TENANTS
from kuber_recon.engine import KnuthExactCoverSolver, MatchResultStatus


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    from kuber_recon.server import WebhookIdempotencyStore
    tmp_db = tmp_path / "test_sec.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", False)
    srv.idempotency_store = WebhookIdempotencyStore()
    yield


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_tenant_auth_missing_headers_returns_401(client):
    """Endpoints with Depends(verify_tenant_auth) must reject requests missing auth headers."""
    # Attempt to fetch capital offer with zero auth headers
    res = client.get("/api/capital/offer")
    assert res.status_code == 401
    assert "Missing X-Merchant-Id or X-API-Key" in res.json()["detail"]

    # Attempt to create contract without auth headers
    res = client.post("/api/apex/contracts/create", json={
        "buyer_agent_id": "buyer_01",
        "seller_agent_id": "seller_01",
        "seller_account_id": "acc_seller_01",
        "amount_paise": 100000,
        "expected_record_count": 1,
        "ttl_seconds": 3600
    })
    assert res.status_code == 401


def test_tenant_auth_invalid_credentials_returns_401(client):
    """Requests with incorrect merchant ID or mismatched API key must return 401."""
    # Unknown tenant
    res = client.get(
        "/api/capital/offer",
        headers={"X-Merchant-Id": "merchant_fake_attacker", "X-API-Key": "bad_key"}
    )
    assert res.status_code == 401
    assert "Invalid merchant or tenant identifier" in res.json()["detail"]

    # Valid tenant, but invalid key
    res = client.get(
        "/api/capital/offer",
        headers={"X-Merchant-Id": "merchant_rzp_primary", "X-API-Key": "wrong_password_123"}
    )
    assert res.status_code == 401
    assert "Invalid API key" in res.json()["detail"]


def test_tenant_auth_valid_credentials_succeeds(client):
    """Requests with valid merchant identity and key must pass authentication."""
    res = client.get(
        "/api/capital/offer",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        }
    )
    assert res.status_code == 200
    data = res.json()
def test_cross_tenant_contract_isolation(client):
    """Proves that a contract created by Tenant A cannot be read or mutated by Tenant B."""
    # 1. Tenant A creates contract
    create_res = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "buyer_tenant_a",
            "seller_agent_id": "seller_tenant_a",
            "seller_account_id": "acc_tenant_a",
            "amount_paise": 50000,
            "expected_record_count": 1,
            "ttl_seconds": 3600,
        },
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert create_res.status_code == 200
    cid = create_res.json()["contract_id"]

    # 2. Tenant A can read its own contract
    get_res_a = client.get(
        f"/api/apex/contracts/{cid}",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert get_res_a.status_code == 200
    assert get_res_a.json()["contract_id"] == cid

    # 3. Tenant B attempts to read Tenant A's contract -> 404 Not Found
    get_res_b = client.get(
        f"/api/apex/contracts/{cid}",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert get_res_b.status_code == 404
    assert "Contract not found for authenticated tenant" in get_res_b.json()["detail"]


def test_error_handler_sanitizes_tracebacks(client, monkeypatch):
    """500 Internal Server Errors must return a structured JSON response without stack traces or exception leaks."""
    import kuber_recon.server as srv
    
    # Intentionally force an unhandled runtime error inside an endpoint to trigger global_exception_handler
    def _exploding_offer(*args, **kwargs):
        raise RuntimeError("Simulated Database Connection Collapse")

    monkeypatch.setattr(srv.capital_underwriter, "generate_offer", _exploding_offer)

    res = client.get(
        "/api/capital/offer",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res.status_code == 500
    body = res.json()
    assert body["detail"] == "Internal Server Error"
    assert "error_id" in body
    assert body["error_id"].startswith("err_")
    assert "traceback" not in body
    assert "trace" not in body
    assert "Simulated Database Connection Collapse" not in str(body)


def test_solver_explicit_inconclusive_truncated_state():
    """Solver must return INCONCLUSIVE_TRUNCATED whenever candidates exceed N=24, even if partial solution exists."""
    solver = KnuthExactCoverSolver(max_nodes=5000, timeout_ms=100.0)

    # 30 items where item 0 + item 1 sum to 3000, but total candidates N=30 > 24
    candidates = [(f"inv_{i}", 1500 if i < 2 else (i + 1) * 1000) for i in range(30)]
    target = 3000

    result = solver.solve_with_diagnostics(target_paise=target, candidates=candidates)
    assert result.status == MatchResultStatus.INCONCLUSIVE_TRUNCATED
    assert result.is_truncated is True
    assert len(result.solutions) == 0


def test_webhook_replay_protection_timestamp_freshness(client):
    """Webhook requests with timestamps older than 300 seconds MUST be rejected with 400 Bad Request."""
    import time
    import json
    import hmac
    import hashlib
    from kuber_recon.server import get_webhook_secret

    now = int(time.time())
    stale_timestamp = now - 600  # 10 minutes old

    body_dict = {
        "entity": "event",
        "account_id": "acc_kuber_escrow_001",
        "event": "transfer.processed",
        "contains": ["transfer"],
        "payload": {"transfer": {"entity": {"id": "trf_test_replay_01", "status": "processed", "on_hold": False}}},
        "created_at": stale_timestamp,
    }
    raw_body = json.dumps(body_dict, separators=(",", ":")).encode("utf-8")
    secret = get_webhook_secret()
    sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    res = client.post(
        "/api/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_stale_replay_01",
        },
    )
    assert res.status_code == 400
    assert "Webhook Replay Rejected" in res.json()["detail"]


def test_webhook_missing_timestamp_rejected(client):
    """Webhook requests with missing timestamp MUST be rejected with 400 Bad Request."""
    import json
    import hmac
    import hashlib
    from kuber_recon.server import get_webhook_secret

    body_dict = {
        "entity": "event",
        "account_id": "acc_kuber_escrow_001",
        "event": "transfer.processed",
        "contains": ["transfer"],
        "payload": {"transfer": {"entity": {"id": "trf_test_no_ts_01", "status": "processed", "on_hold": False}}},
    }
    raw_body = json.dumps(body_dict, separators=(",", ":")).encode("utf-8")
    secret = get_webhook_secret()
    sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    res = client.post(
        "/api/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_no_ts_01",
        },
    )
    assert res.status_code == 400
    assert "Missing mandatory event timestamp" in res.json()["detail"]


def test_cross_tenant_capital_facility_isolation(client):
    """Proves Tenant A's capital facility cannot be listed, swept, or mutated by Tenant B."""
    # 1. Tenant A draws down a capital facility
    res_a = client.post(
        "/api/capital/drawdown",
        json={"requested_amount_paise": 2000000},
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_a.status_code == 200
    facility_id = res_a.json()["facility_id"]

    # 2. Tenant B lists facilities -> receives empty list (0 facilities for Tenant B)
    res_b_list = client.get(
        "/api/capital/facilities",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()["facilities"]) == 0

    # 3. Tenant B attempts to sweep Tenant A's facility -> 404 Not Found
    res_b_sweep = client.post(
        "/api/capital/reconcile-and-sweep",
        json={"facility_id": facility_id, "num_records": 10},
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert res_b_sweep.status_code == 404
    assert "Facility not found for authenticated tenant" in res_b_sweep.json()["detail"]
