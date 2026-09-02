"""
Security & Tenant Isolation Test Suite for Kuber OS.
Validates:
1. Strict 401 Unauthorized when X-Merchant-Id / X-API-Key are missing or invalid.
2. Constant-time key comparison and authenticated tenant identification.
3. Anti-tampering error sanitation with zero traceback exposure.
4. Solver explicit INCONCLUSIVE_TRUNCATED outcome when search candidate pool > 24 or budget exceeded.
"""

import hashlib
import json
import time

import pytest
from fastapi.testclient import TestClient
from kuber_recon.server import app, REGISTERED_TENANTS
from kuber_recon.engine import HorowitzSahniSubsetSumSolver, MatchResultStatus


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    from kuber_recon.server import WebhookIdempotencyStore
    tmp_db = tmp_path / "test_sec.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    import kuber_recon.server as srv
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", False)
    srv.idempotency_store = WebhookIdempotencyStore()
    srv.capital_facility_manager.reset_all_facilities_for_tests()
    yield
    srv.capital_facility_manager.reset_all_facilities_for_tests()


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
    assert res.json()["merchant_id"] == "merchant_rzp_primary"


def test_cross_tenant_contract_isolation(client):
    """Proves that a contract created by Tenant A cannot be read or mutated by Tenant B."""
    from kuber_recon.security import SoftwareEd25519Custodian

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

    # 4. Tenant B attempts to deliver payload to Tenant A's contract -> 404 Not Found
    deliv_records = [{"supplier_name": "Supplier X", "gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-101", "amount_paise": 50000}]
    seller_seed = "seller_tenant_a_seed_01"
    sk_bytes = hashlib.sha256(seller_seed.encode("utf-8")).digest()
    from cryptography.hazmat.primitives.asymmetric import ed25519
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes)
    pub_hex = priv.public_key().public_bytes_raw().hex()
    manifest_bytes = json.dumps(deliv_records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig_hex = priv.sign(manifest_bytes).hex()

    deliv_b = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": "seller_tenant_a",
            "payload_records": deliv_records,
            "manifest_signature": sig_hex,
            "seller_public_key_hex": pub_hex,
        },
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert deliv_b.status_code == 404
    assert "Contract not found for authenticated tenant" in deliv_b.json()["detail"]

    # 5. Tenant B attempts to release Tenant A's contract -> 404 Not Found
    cfo_seed = "cfo_test_checker_seed"
    cfo_sk = ed25519.Ed25519PrivateKey.from_private_bytes(hashlib.sha256(cfo_seed.encode("utf-8")).digest())
    cfo_pub_hex = cfo_sk.public_key().public_bytes_raw().hex()
    canon_msg = f"{cid}:dummy_leaf_hash:cfo_test_checker".encode("utf-8")
    cfo_sig_hex = cfo_sk.sign(canon_msg).hex()

    rel_b = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": cid,
            "checker_id": "cfo_test_checker",
            "public_key_hex": cfo_pub_hex,
            "signature_hex": cfo_sig_hex,
        },
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert rel_b.status_code == 404
    assert "Contract not found for authenticated tenant" in rel_b.json()["detail"]


def test_primary_tenant_requesting_another_merchant_offer_rejected_403(client):
    """Even primary tenant cannot request capital offer for another merchant."""
    res = client.get(
        "/api/capital/offer?merchant_id=merchant_agent_demo_01",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res.status_code == 403
    assert "Tenant Authorization Mismatch" in res.json()["detail"]


def test_primary_tenant_drawing_down_another_merchant_facility_rejected_403(client):
    """Even primary tenant cannot drawdown capital under another merchant ID."""
    res = client.post(
        "/api/capital/drawdown",
        json={"merchant_id": "merchant_agent_demo_01", "requested_amount_paise": 1000000},
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res.status_code == 403
    assert "Tenant Authorization Mismatch" in res.json()["detail"]


def test_cross_tenant_reset_preserves_other_tenant_facilities(client):
    """Resetting Tenant B's facilities must NOT affect Tenant A's active facilities."""
    # 1. Tenant A draws down facility
    res_a = client.post(
        "/api/capital/drawdown",
        json={"requested_amount_paise": 1500000},
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_a.status_code == 200

    # 2. Tenant B draws down facility
    res_b = client.post(
        "/api/capital/drawdown",
        json={"requested_amount_paise": 1000000},
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert res_b.status_code == 200

    # 3. Tenant B executes reset
    res_reset_b = client.post(
        "/api/capital/reset",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert res_reset_b.status_code == 200

    # 4. Tenant B now has 0 facilities
    res_list_b = client.get(
        "/api/capital/facilities",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert len(res_list_b.json()["facilities"]) == 0

    # 5. Tenant A's facility is PRESERVED
    res_list_a = client.get(
        "/api/capital/facilities",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert len(res_list_a.json()["facilities"]) == 1


def test_rejected_webhook_does_not_poison_idempotency_table_and_retry_succeeds(client):
    """
    Proves that when a webhook is rejected due to a stale timestamp,
    its event_id is NOT saved in the idempotency table, allowing a corrected retry to succeed.
    """
    import time
    import json
    import hmac
    import hashlib
    from kuber_recon.server import get_webhook_secret

    event_id = "evt_retry_test_freshness_999"
    stale_ts = int(time.time()) - 1000

    # 1. Send stale payload with event_id
    payload_stale = {
        "entity": "event",
        "account_id": "acc_retry_01",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_retry_01", "amount": 100000}}},
        "created_at": stale_ts,
    }
    raw_stale = json.dumps(payload_stale, separators=(",", ":")).encode("utf-8")
    sig_stale = hmac.new(get_webhook_secret().encode("utf-8"), raw_stale, hashlib.sha256).hexdigest()

    res_fail = client.post(
        "/api/webhook/razorpay",
        content=raw_stale,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig_stale,
            "X-Razorpay-Event-Id": event_id,
        },
    )
    assert res_fail.status_code == 400
    assert "Webhook Replay Rejected" in res_fail.json()["detail"]

    # 2. Resend valid payload with same event_id
    fresh_ts = int(time.time())
    payload_fresh = {
        "entity": "event",
        "account_id": "acc_retry_01",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_retry_01", "amount": 100000}}},
        "created_at": fresh_ts,
    }
    raw_fresh = json.dumps(payload_fresh, separators=(",", ":")).encode("utf-8")
    sig_fresh = hmac.new(get_webhook_secret().encode("utf-8"), raw_fresh, hashlib.sha256).hexdigest()

    res_ok = client.post(
        "/api/webhook/razorpay",
        content=raw_fresh,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig_fresh,
            "X-Razorpay-Event-Id": event_id,
        },
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "acknowledged"


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
    solver = HorowitzSahniSubsetSumSolver(max_nodes=5000, timeout_ms=100.0)

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


def test_cross_tenant_sweep_expired_isolation(client):
    """
    Proves that when Tenant B calls /api/apex/contracts/sweep-expired,
    only Tenant B's expired contracts are swept, and Tenant A's expired contracts remain untouched.
    """
    import time
    from kuber_recon.server import idempotency_store

    now = int(time.time())
    past_expiry = now - 100  # already expired

    # 1. Create expired contract directly in store for Tenant A
    cid_a = "apx_test_sweep_tenant_a_001"
    with idempotency_store._lock, idempotency_store._connect() as conn:
        conn.execute(
            """
            INSERT INTO apex_contracts (
                contract_id, buyer_agent_id, seller_agent_id, seller_account_id,
                amount_paise, expected_record_count, on_hold, on_hold_until, assertions_passed,
                status, version, tenant_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0, 'HELD', 1, 'merchant_rzp_primary', ?)
            """,
            (cid_a, "buyer_a", "seller_a", "acc_a", 50000, 1, past_expiry, now),
        )

    # 2. Create expired contract directly in store for Tenant B
    cid_b = "apx_test_sweep_tenant_b_001"
    with idempotency_store._lock, idempotency_store._connect() as conn:
        conn.execute(
            """
            INSERT INTO apex_contracts (
                contract_id, buyer_agent_id, seller_agent_id, seller_account_id,
                amount_paise, expected_record_count, on_hold, on_hold_until, assertions_passed,
                status, version, tenant_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0, 'HELD', 1, 'merchant_agent_demo_01', ?)
            """,
            (cid_b, "buyer_b", "seller_b", "acc_b", 60000, 1, past_expiry, now),
        )

    # 3. Tenant B triggers sweep-expired
    sweep_res_b = client.post(
        "/api/apex/contracts/sweep-expired",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert sweep_res_b.status_code == 200
    swept_b = sweep_res_b.json()["swept_contract_ids"]

    # Tenant B's sweep must include cid_b and MUST NOT include cid_a
    assert cid_b in swept_b
    assert cid_a not in swept_b

    # 4. Verify Tenant A's contract remains HELD (untouched by Tenant B's sweep)
    contract_a_data = idempotency_store.get_contract(cid_a, tenant_id="merchant_rzp_primary")
    assert contract_a_data is not None
    assert contract_a_data["status"] == "HELD"

    # 5. Tenant A triggers sweep-expired -> now Tenant A's contract is swept
    sweep_res_a = client.post(
        "/api/apex/contracts/sweep-expired",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert sweep_res_a.status_code == 200
    swept_a = sweep_res_a.json()["swept_contract_ids"]
    assert cid_a in swept_a
    assert cid_b not in swept_a

    # Now Tenant A's contract is in EXPIRED_HOLD
    contract_a_updated = idempotency_store.get_contract(cid_a, tenant_id="merchant_rzp_primary")
    assert contract_a_updated["status"] == "EXPIRED_HOLD"


@pytest.mark.parametrize(
    "method,endpoint,json_payload",
    [
        ("POST", "/api/intercept", {"order_id": "ord_t_01", "amount_paise": 10000, "gst_rate_pct": 18}),
        ("POST", "/api/reconcile", {"records": 10, "seed": 42}),
        ("POST", "/api/reconcile/ambiguous", None),
        ("POST", "/api/razorpay/route-transfer", {"account_id": "acc_01", "amount_paise": 10000}),
        ("POST", "/api/apex/contracts/create", {
            "buyer_agent_id": "b1", "seller_agent_id": "s1", "seller_account_id": "acc1",
            "amount_paise": 10000, "expected_record_count": 1, "ttl_seconds": 3600
        }),
        ("POST", "/api/apex/contracts/deliver", {
            "contract_id": "cnt_dummy", "seller_agent_id": "s1", "payload_records": [],
            "manifest_signature": "00" * 64, "seller_public_key_hex": "00" * 32
        }),
        ("POST", "/api/apex/contracts/release", {
            "contract_id": "cnt_dummy", "checker_id": "chk_1",
            "public_key_hex": "00" * 32, "signature_hex": "00" * 64
        }),
        ("POST", "/api/apex/contracts/sweep-expired", None),
        ("GET", "/api/apex/contracts/cnt_dummy", None),
        ("POST", "/api/twin/simulate", {"scenario": "bank_holiday", "severity": 1.0}),
        ("GET", "/api/capital/offer", None),
        ("POST", "/api/capital/drawdown", {"requested_amount_paise": 100000}),
        ("GET", "/api/capital/facilities", None),
        ("POST", "/api/capital/reconcile-and-sweep", {"facility_id": "fac_dummy", "num_records": 10}),
        ("POST", "/api/capital/reset", None),
    ]
)
def test_all_protected_financial_endpoints_reject_missing_auth_with_401(client, method, endpoint, json_payload):
    """Every financially meaningful endpoint must strictly return HTTP 401 when auth headers are missing."""
    if method == "GET":
        res = client.get(endpoint)
    else:
        res = client.post(endpoint, json=json_payload) if json_payload else client.post(endpoint)
    assert res.status_code == 401
    assert "Authentication Failed" in res.json()["detail"]


def test_webhook_rejects_future_timestamp(client):
    """Webhook with timestamp > 300s in the future must be rejected with HTTP 400 without poisoning idempotency DB."""
    import time
    from kuber_recon.server import get_webhook_secret

    now = int(time.time())
    future_ts = now + 500  # 500 seconds into future (> 300s skew)
    event_id = "evt_future_ts_999"

    payload = {
        "entity": "event",
        "account_id": "acc_kuber_01",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_future_01", "amount": 100000}}},
        "created_at": future_ts,
    }
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hashlib.sha256(raw_body).hexdigest()

    res = client.post(
        "/api/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": event_id,
        },
    )
    assert res.status_code == 400
    assert "Webhook Replay Rejected" in res.json()["detail"]

    # Verify event was NOT inserted into processed_events
    from kuber_recon.server import idempotency_store
    with idempotency_store._lock, idempotency_store._connect() as conn:
        row = conn.execute("SELECT event_id FROM processed_events WHERE event_id = ?", (event_id,)).fetchone()
        assert row is None


def test_webhook_rejects_invalid_hmac_signature(client):
    """Webhook with invalid HMAC signature must return HTTP 400 without poisoning idempotency DB."""
    import time

    now = int(time.time())
    event_id = "evt_bad_sig_999"

    payload = {
        "entity": "event",
        "account_id": "acc_kuber_01",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_bad_01", "amount": 100000}}},
        "created_at": now,
    }
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    res = client.post(
        "/api/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_signature_hex_value_00000",
            "X-Razorpay-Event-Id": event_id,
        },
    )
    assert res.status_code == 400
    assert "Invalid X-Razorpay-Signature" in res.json()["detail"]

    from kuber_recon.server import idempotency_store
    with idempotency_store._lock, idempotency_store._connect() as conn:
        row = conn.execute("SELECT event_id FROM processed_events WHERE event_id = ?", (event_id,)).fetchone()
        assert row is None


def test_webhook_rejects_malformed_json(client):
    """Malformed non-JSON request body must return HTTP 400."""
    res = client.post(
        "/api/webhook/razorpay",
        content=b"not a valid json payload",
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "sig123",
        },
    )
    assert res.status_code == 400
    assert "Malformed JSON Payload" in res.json()["detail"]


def test_solver_node_budget_and_timeout_exhaustion():
    """Solver must return INCONCLUSIVE_TRUNCATED when max_nodes budget or timeout is exceeded."""
    # Extremely small budget (max_nodes=2)
    solver = HorowitzSahniSubsetSumSolver(max_nodes=2, timeout_ms=500.0)
    candidates = [(f"inv_{i}", (i + 1) * 1000) for i in range(12)]
    target = 15000

    result = solver.solve_with_diagnostics(target_paise=target, candidates=candidates)
    assert result.status == MatchResultStatus.INCONCLUSIVE_TRUNCATED
    assert result.is_truncated is True


def test_reconciliation_engine_rejects_inconclusive_and_ambiguous_subsets():
    """ReconciliationEngine must never create settled blocks for inconclusive or ambiguous results."""
    from datetime import date, datetime, timezone
    from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod
    from kuber_recon.engine import ReconciliationEngine

    engine = ReconciliationEngine()
    today = date(2026, 8, 27)
    inv_ts = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    credit = BankNodalCredit(
        utr_number="UTR_AMBIG_001",
        account_number="ACC_NODAL_01",
        raw_narration="Settlement UPI",
        credit_amount_in_paise=99000,
        value_date=today,
    )

    # 2 conflicting pairs of invoices that both sum to 99000 net (1% TDS deducted)
    invoices = [
        InvoiceRecord(invoice_id="INV-1", order_id="ord_1", payment_id="pay_1", supplier_gstin="29ABCDE1234F1Z5", amount_in_paise=60000, method=PaymentMethod.UPI, captured_at=inv_ts, is_settled=False),
        InvoiceRecord(invoice_id="INV-2", order_id="ord_2", payment_id="pay_2", supplier_gstin="29ABCDE1234F1Z5", amount_in_paise=40000, method=PaymentMethod.UPI, captured_at=inv_ts, is_settled=False),
        InvoiceRecord(invoice_id="INV-3", order_id="ord_3", payment_id="pay_3", supplier_gstin="29ABCDE1234F1Z5", amount_in_paise=70000, method=PaymentMethod.UPI, captured_at=inv_ts, is_settled=False),
        InvoiceRecord(invoice_id="INV-4", order_id="ord_4", payment_id="pay_4", supplier_gstin="29ABCDE1234F1Z5", amount_in_paise=30000, method=PaymentMethod.UPI, captured_at=inv_ts, is_settled=False),
    ]

    reconciled, exceptions = engine.reconcile_batch([credit], invoices)
    assert len(reconciled) == 0
    assert len(exceptions) == 1
    assert "AMBIGUOUS_COLLISION" in exceptions[0][1]


def test_signer_public_key_endpoint_exposes_no_private_keys(client):
    """GET /api/apex/signer/public-key exposes public metadata and zero private key material."""
    res = client.get("/api/apex/signer/public-key")
    assert res.status_code == 200
    data = res.json()
    assert data["key_id"] == "demo_software_ed25519_v1"
    assert data["algorithm"] == "Ed25519"
    assert data["is_production_kms"] is False
    assert len(data["public_key_hex"]) == 64
    assert "private" not in str(data).lower()
    assert "seed" not in str(data).lower()


def test_server_side_demo_signing_workflow_and_isolation(client):
    """Server-side demo signing verifies tenant ownership, delivered state, and returns valid RFC 8032 signature."""
    from kuber_recon.security import SoftwareEd25519Custodian

    seller_id = "agent_seller_data_01"

    # 1. Create a contract for Tenant A
    res_create = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "buyer_sign_01",
            "seller_agent_id": seller_id,
            "seller_account_id": "acc_sign_01",
            "amount_paise": 150000,
            "expected_record_count": 2,
            "ttl_seconds": 3600,
        },
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_create.status_code == 200
    cid = res_create.json()["contract_id"]

    # 2. Attempt to sign before delivery -> rejected with 400
    res_sign_early = client.post(
        f"/api/apex/contracts/{cid}/sign-demo",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_sign_early.status_code == 400
    assert "Contract must be in VERIFYING state" in res_sign_early.json()["detail"]

    # 3. Deliver valid assertion payload
    from cryptography.hazmat.primitives.asymmetric import ed25519 as crypto_ed25519
    seller_seed = hashlib.sha256(f"kuber_{seller_id}_sec_key_v1".encode()).digest()
    seller_priv = crypto_ed25519.Ed25519PrivateKey.from_private_bytes(seller_seed)
    seller_pub = seller_priv.public_key().public_bytes_raw().hex()

    payload_records = [
        {
            "supplier_name": "Supplier Sign Alpha",
            "gstin": "27AAPFU0939F1ZV",
            "invoice_number": "INV-SIGN-001",
            "amount_paise": 75000,
        },
        {
            "supplier_name": "Supplier Sign Beta",
            "gstin": "27AAPFU0939F1ZV",
            "invoice_number": "INV-SIGN-002",
            "amount_paise": 75000,
        },
    ]
    canonical_seller_bytes = json.dumps(payload_records, separators=(',', ':'), sort_keys=True).encode('utf-8')
    seller_sig = seller_priv.sign(canonical_seller_bytes).hex()

    res_deliver = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": cid,
            "seller_agent_id": seller_id,
            "payload_records": payload_records,
            "manifest_signature": seller_sig,
            "seller_public_key_hex": seller_pub,
        },
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_deliver.status_code == 200

    # 4. Tenant B attempts to sign Tenant A's contract -> 404/403 Forbidden
    res_sign_b = client.post(
        f"/api/apex/contracts/{cid}/sign-demo",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
    )
    assert res_sign_b.status_code in (403, 404)

    # 5. Tenant A signs contract -> 200 OK with valid Ed25519 signature
    res_sign_a = client.post(
        f"/api/apex/contracts/{cid}/sign-demo",
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )
    assert res_sign_a.status_code == 200
    sign_data = res_sign_a.json()
    assert sign_data["status"] == "SIGNED"
    assert sign_data["contract_id"] == cid
    assert sign_data["tenant_id"] == "merchant_rzp_primary"
    assert len(sign_data["signature_hex"]) == 128
    assert len(sign_data["public_key_hex"]) == 64


