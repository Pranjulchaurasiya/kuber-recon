"""Tests for Provisioned Identity, JWT Token Minting, and RBAC Endpoint Protection.
"""

import pytest
from fastapi.testclient import TestClient
from kuber_recon.security import UserRole, create_access_token
from kuber_recon.server import app

client = TestClient(app)

AUTH_HEADERS_PRIMARY = {
    "X-Merchant-Id": "merchant_rzp_primary",
    "X-API-Key": "kuber_sandbox_key_primary_2026",
}

AUTH_HEADERS_PARTNER = {
    "X-Merchant-Id": "merchant_agent_demo_01",
    "X-API-Key": "kuber_sandbox_key_agent_01_2026",
}


def test_token_minting_for_provisioned_subject_success():
    """Verify that a provisioned subject can mint a valid token matching their provisioned roles."""
    resp = client.post(
        "/api/v2/auth/token",
        headers=AUTH_HEADERS_PRIMARY,
        json={
            "subject": "cfo_demo_operator",
            "tenant_id": "merchant_rzp_primary",
            "roles": ["MERCHANT_OPERATOR", "FINANCE_REVIEWER"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == "merchant_rzp_primary"
    assert "access_token" in data
    assert set(data["roles"]) == {"MERCHANT_OPERATOR", "FINANCE_REVIEWER"}


def test_token_minting_unknown_subject_rejected():
    """Verify that an unprovisioned subject is rejected with HTTP 403."""
    resp = client.post(
        "/api/v2/auth/token",
        headers=AUTH_HEADERS_PRIMARY,
        json={
            "subject": "unregistered_intruder_99",
            "tenant_id": "merchant_rzp_primary",
            "roles": ["MERCHANT_OPERATOR"],
        },
    )
    assert resp.status_code == 403
    assert "not provisioned" in resp.json()["detail"]


def test_token_minting_cross_tenant_spoofing_rejected():
    """Verify that caller cannot mint a token for a subject provisioned under another tenant."""
    resp = client.post(
        "/api/v2/auth/token",
        headers=AUTH_HEADERS_PARTNER,  # partner merchant
        json={
            "subject": "cfo_demo_operator",  # belongs to primary tenant
            "tenant_id": "merchant_agent_demo_01",
            "roles": ["MERCHANT_OPERATOR"],
        },
    )
    assert resp.status_code == 403
    assert "Authorization Error" in resp.json()["detail"]


def test_token_minting_role_escalation_rejected():
    """Verify that a subject provisioned only as MERCHANT_OPERATOR cannot request ADMINISTRATOR."""
    resp = client.post(
        "/api/v2/auth/token",
        headers=AUTH_HEADERS_PARTNER,
        json={
            "subject": "agent_operator_limited",
            "tenant_id": "merchant_agent_demo_01",
            "roles": ["ADMINISTRATOR"],  # Not provisioned for ADMIN
        },
    )
    assert resp.status_code == 403
    assert "Role Escalation Denied" in resp.json()["detail"]


def test_protected_endpoint_role_enforcement():
    """Verify that an endpoint requiring FINANCE_REVIEWER rejects a token containing only MERCHANT_OPERATOR."""
    operator_token = create_access_token(
        subject="test_operator",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.MERCHANT_OPERATOR],
    )
    headers = {"Authorization": f"Bearer {operator_token}"}

    # /api/apex/contracts/sweep-expired requires FINANCE_REVIEWER or ADMINISTRATOR
    resp = client.post("/api/apex/contracts/sweep-expired", headers=headers)
    assert resp.status_code == 403
    assert "Access Denied" in resp.json()["detail"]

    # Now with reviewer token
    reviewer_token = create_access_token(
        subject="test_reviewer",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.FINANCE_REVIEWER],
    )
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
    resp_ok = client.post("/api/apex/contracts/sweep-expired", headers=reviewer_headers)
    assert resp_ok.status_code == 200


def test_capital_drawdown_negative_authorization():
    """Verify that capital drawdown strictly rejects unauthorized roles (MERCHANT_OPERATOR -> 403)."""
    operator_token = create_access_token(
        subject="test_operator",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.MERCHANT_OPERATOR],
    )
    headers = {"Authorization": f"Bearer {operator_token}"}
    resp = client.post("/api/capital/drawdown", headers=headers, json={"requested_amount_paise": 500000})
    assert resp.status_code == 403
    assert "Access Denied" in resp.json()["detail"]


def test_capital_reset_negative_authorization():
    """Verify that capital reset rejects non-ADMINISTRATOR roles (FINANCE_REVIEWER -> 403)."""
    reviewer_token = create_access_token(
        subject="test_reviewer",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.FINANCE_REVIEWER],
    )
    headers = {"Authorization": f"Bearer {reviewer_token}"}
    resp = client.post("/api/capital/reset", headers=headers)
    assert resp.status_code == 403
    assert "Access Denied" in resp.json()["detail"]

    admin_token = create_access_token(
        subject="test_admin",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.ADMINISTRATOR],
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp_admin = client.post("/api/capital/reset", headers=admin_headers)
    assert resp_admin.status_code == 200
    assert resp_admin.json()["status"] == "RESET_SUCCESS"


def test_manual_review_resolution_negative_authorization():
    """Verify that resolving manual review queue rejects MERCHANT_OPERATOR (403)."""
    operator_token = create_access_token(
        subject="test_operator",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.MERCHANT_OPERATOR],
    )
    headers = {"Authorization": f"Bearer {operator_token}"}
    resp = client.post(
        "/api/reconcile/manual-review/resolve",
        headers=headers,
        json={"item_id": "MR-NONEXISTENT", "resolution": "RESOLVED"},
    )
    assert resp.status_code == 403
    assert "Access Denied" in resp.json()["detail"]


def test_system_config_negative_authorization():
    """Verify that system configuration POST requires ADMINISTRATOR (FINANCE_REVIEWER -> 403)."""
    reviewer_token = create_access_token(
        subject="test_reviewer",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.FINANCE_REVIEWER],
    )
    headers = {"Authorization": f"Bearer {reviewer_token}"}
    resp = client.post("/api/config/system", headers=headers, json={"dual_auth_threshold_paise": 200000000})
    assert resp.status_code == 403
    assert "Access Denied" in resp.json()["detail"]

    admin_token = create_access_token(
        subject="test_admin",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.ADMINISTRATOR],
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp_admin = client.post("/api/config/system", headers=admin_headers, json={"dual_auth_threshold_paise": 250000000})
    assert resp_admin.status_code == 200
    assert resp_admin.json()["status"] == "UPDATED"

