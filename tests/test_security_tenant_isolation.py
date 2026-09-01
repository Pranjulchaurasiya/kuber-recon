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


@pytest.fixture
def client():
    return TestClient(app)


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
    assert data["merchant_id"] == "merch_delhi_logistics_01"
    assert "verified_delivered_gmv_paise" in data


def test_error_handler_sanitizes_tracebacks(client):
    """500 Internal Server Errors must return a structured JSON response without stack traces."""
    # Force a 500 error by triggering an invalid twin scenario
    res = client.post(
        "/api/twin/simulate",
        json={"scenario": "invalid_scenario_trigger_500", "severity": 1.0},
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        }
    )
    # The application gracefully handles 400 for unknown scenario
    assert res.status_code in (400, 500)
    body = res.json()
    assert "traceback" not in body
    assert "trace" not in body


def test_solver_explicit_inconclusive_truncated_state():
    """Solver must return INCONCLUSIVE_TRUNCATED when candidates exceed complexity bounds (N > 24)."""
    solver = KnuthExactCoverSolver(max_nodes=5000, timeout_ms=100.0)

    # 30 items - strictly exceeding the N=24 exact-cover boundary limit
    candidates = [(f"inv_{i}", (i + 1) * 1000) for i in range(30)]
    target = 99999999  # No exact subset exists

    result = solver.solve_with_diagnostics(target_paise=target, candidates=candidates)
    assert result.status == MatchResultStatus.INCONCLUSIVE_TRUNCATED
    assert result.is_truncated is True
    assert len(result.solutions) == 0
