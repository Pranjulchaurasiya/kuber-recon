"""Tests for RBAC authorization, provisioned subject identity registry, token lifecycle, and role guards.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from kuber_recon.security import UserRole, create_access_token
from kuber_recon.server import app

CLIENT_HEADERS_OPERATOR = {
    "X-Merchant-Id": "merchant_rzp_primary",
    "X-API-Key": "kuber_sandbox_key_primary_2026",
}


def _get_auth_header(sub: str, tenant_id: str, roles: list[UserRole], delta: timedelta = timedelta(minutes=15)) -> dict[str, str]:
    token = create_access_token(
        subject=sub,
        tenant_id=tenant_id,
        roles=roles,
        expires_delta=delta,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Merchant-Id": tenant_id,
    }


def test_unprovisioned_subject_rejected():
    """Verify that attempting to mint a token for an unknown subject returns HTTP 403."""
    with TestClient(app) as client:
        resp = client.post(
            "/api/auth/token",
            json={
                "subject": "unknown_hacker_actor",
                "tenant_id": "merchant_rzp_primary",
                "roles": ["MERCHANT_OPERATOR"],
            },
            headers=CLIENT_HEADERS_OPERATOR,
        )
        assert resp.status_code == 403
        assert "not provisioned" in resp.json()["detail"]


def test_cross_tenant_token_rejected():
    """Verify that attempting to mint a token across tenants returns HTTP 403."""
    with TestClient(app) as client:
        resp = client.post(
            "/api/auth/token",
            json={
                "subject": "cfo_demo_operator",
                "tenant_id": "merchant_agent_demo_01",
                "roles": ["MERCHANT_OPERATOR"],
            },
            headers=CLIENT_HEADERS_OPERATOR,
        )
        assert resp.status_code == 403
        assert "cannot mint tokens for tenant" in resp.json()["detail"]


def test_privilege_escalation_rejected():
    """Verify that requesting a role not assigned in the subject's provisioned registry returns HTTP 403."""
    with TestClient(app) as client:
        resp = client.post(
            "/api/auth/token",
            json={
                "subject": "cfo_demo_operator",  # Provisioned for MERCHANT_OPERATOR, FINANCE_REVIEWER
                "tenant_id": "merchant_rzp_primary",
                "roles": ["ADMINISTRATOR"],  # Escalation attempt
            },
            headers=CLIENT_HEADERS_OPERATOR,
        )
        assert resp.status_code == 403
        assert "Role Escalation Denied" in resp.json()["detail"]


def test_missing_role_returns_403():
    """Verify that calling a protected route without the required role returns HTTP 403."""
    headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.MERCHANT_OPERATOR])
    with TestClient(app) as client:
        resp = client.post(
            "/api/capital/reset",
            headers=headers,
        )
        assert resp.status_code == 403
        assert "Access Denied" in resp.json()["detail"]


def test_expired_token_rejected():
    """Verify that an expired token fails authentication with HTTP 401."""
    expired_headers = _get_auth_header(
        "compliance_admin",
        "merchant_rzp_primary",
        [UserRole.ADMINISTRATOR],
        delta=timedelta(seconds=-10),  # expired 10s ago
    )
    with TestClient(app) as client:
        resp = client.post("/api/capital/reset", headers=expired_headers)
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()


def test_admin_only_reset():
    """Verify that /api/capital/reset strictly permits ADMINISTRATOR and denies other roles."""
    operator_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER])
    admin_headers = _get_auth_header("compliance_admin", "merchant_rzp_primary", [UserRole.ADMINISTRATOR])

    with TestClient(app) as client:
        # Non-admin denied
        resp_denied = client.post("/api/capital/reset", headers=operator_headers)
        assert resp_denied.status_code == 403

        # Admin permitted
        resp_ok = client.post("/api/capital/reset", headers=admin_headers)
        assert resp_ok.status_code == 200
        assert resp_ok.json()["status"] == "RESET_SUCCESS"


def test_finance_only_release():
    """Verify that /api/apex/contracts/release allows FINANCE_REVIEWER / ADMINISTRATOR and denies others."""
    operator_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.MERCHANT_OPERATOR])
    finance_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.FINANCE_REVIEWER])
    release_body = {
        "contract_id": "cnt_test_missing",
        "checker_id": "cfo_demo_operator",
        "public_key_hex": "00" * 32,
        "signature_hex": "00" * 64,
    }

    with TestClient(app) as client:
        resp_denied = client.post(
            "/api/apex/contracts/release",
            json=release_body,
            headers=operator_headers,
        )
        assert resp_denied.status_code == 403

        resp_allowed = client.post(
            "/api/apex/contracts/release",
            json=release_body,
            headers=finance_headers,
        )
        # 404 because contract doesn't exist, which proves it passed the 403 RBAC authorization guard!
        assert resp_allowed.status_code == 404


def test_risk_or_finance_drawdown():
    """Verify that /api/capital/drawdown allows RISK_ANALYST, FINANCE_REVIEWER, or ADMINISTRATOR, but denies MERCHANT_OPERATOR."""
    operator_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.MERCHANT_OPERATOR])
    analyst_headers = _get_auth_header("risk_analyst_user", "merchant_rzp_primary", [UserRole.RISK_ANALYST])

    with TestClient(app) as client:
        resp_denied = client.post(
            "/api/capital/drawdown",
            json={"requested_amount_paise": 1000000},
            headers=operator_headers,
        )
        assert resp_denied.status_code == 403

        resp_allowed = client.post(
            "/api/capital/drawdown",
            json={"requested_amount_paise": 1000000},
            headers=analyst_headers,
        )
        # Advance underwritten and disbursed successfully
        assert resp_allowed.status_code == 200
        assert resp_allowed.json()["status"] == "DISBURSED"


def test_manual_review_role_guard():
    """Verify that /api/reconcile/manual-review/resolve requires FINANCE_REVIEWER or ADMINISTRATOR."""
    operator_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.MERCHANT_OPERATOR])
    finance_headers = _get_auth_header("cfo_demo_operator", "merchant_rzp_primary", [UserRole.FINANCE_REVIEWER])

    with TestClient(app) as client:
        resp_denied = client.post(
            "/api/reconcile/manual-review/resolve",
            json={"item_id": "mr_item_missing", "resolution": "DISMISSED"},
            headers=operator_headers,
        )
        assert resp_denied.status_code == 403

        resp_allowed = client.post(
            "/api/reconcile/manual-review/resolve",
            json={"item_id": "mr_item_missing", "resolution": "DISMISSED"},
            headers=finance_headers,
        )
        # 404 because item doesn't exist, proving it passed the RBAC role guard!
        assert resp_allowed.status_code == 404
