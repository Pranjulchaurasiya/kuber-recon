"""
test_apex_assurance.py
======================
Unit & Resilience Tests for APEX Assurance:
  1. Contract initialization with integer paise + Route on_hold: true + TTL
  2. Delivery assertion failure -> Honest Refusal (settlement stays on_hold: true)
  3. Clean delivery verification -> Settlement release (PATCH on_hold: false)
  4. Release blocked if assertions not passed (400 Bad Request)
  5. Memory bounds enforcement (>5MB rejected with 413)
  6. Non-LLM GSTIN Mod-36 checksum mathematical correctness
"""

import pytest
from fastapi.testclient import TestClient
from kuber_recon.assurance import (
    DeterministicAssertionEngine,
    validate_gstin_checksum,
    MAX_DIRECT_PAYLOAD_BYTES,
)
from kuber_recon.server import app, idempotency_store, WebhookIdempotencyStore


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    tmp_db = tmp_path / "test_apex.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    import kuber_recon.server as srv
    srv.idempotency_store = WebhookIdempotencyStore()
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Mod-36 GSTIN Checksum Tests ────────────────────────────────────────────

def test_gstin_mod36_checksum_valid():
    # Valid Indian GSTIN format with exact Mod-36 checksum
    assert validate_gstin_checksum("27AAPCA1234F1ZV") is True
    assert validate_gstin_checksum("29BBBBB5678G2ZC") is True


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
            "seller_account_id": "acc_seller_linked_99",
            "amount_paise": 2500000,  # ₹25,000.00
            "ttl_seconds": 86400,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HELD"
    assert data["on_hold"] is True
    assert data["amount_paise"] == 2500000
    assert "₹25,000.00" in data["amount_inr"]
    assert "trf_" in data["transfer_id"]


# ── 3. Malicious / Corrupted Delivery -> Honest Refusal ───────────────────────

def test_apex_delivery_refusal_on_corrupted_gstin(client):
    # Step 1: Create contract
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_bad",
            "seller_account_id": "acc_seller_linked_99",
            "amount_paise": 2500000,
        },
    )
    contract_id = c_resp.json()["contract_id"]

    # Step 2: Deliver 10 records, but 2 have corrupted GSTINs
    records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPCA1234F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 250000}
        for i in range(8)
    ]
    # Add corrupted records
    records.append({"supplier_name": "Corrupted 1", "gstin": "27AAPCA1234F1Z9", "invoice_number": "INV-BAD1", "amount_paise": 250000})
    records.append({"supplier_name": "Corrupted 2", "gstin": "INVALID_GST", "invoice_number": "INV-BAD2", "amount_paise": 250000})

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": contract_id,
            "seller_agent_id": "agent_seller_bad",
            "payload_records": records,
        },
    )
    assert d_resp.status_code == 200
    data = d_resp.json()
    assert data["assertions_passed"] is False
    assert data["status"] == "REFUSED"
    assert data["on_hold"] is True
    assert data["failed_records"] == 2
    assert data["valid_records"] == 8
    assert "CERT:REFUSAL:APEX" in data["refusal_certificate"]

    # Step 3: Attempting release MUST be blocked with 400
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={"contract_id": contract_id, "checker_id": "cfo_test"},
    )
    assert r_resp.status_code == 400
    assert "delivery assertions have not passed" in r_resp.json()["detail"]


# ── 4. 100% Clean Delivery -> Verified Release ────────────────────────────────

def test_apex_delivery_release_on_100pct_valid(client):
    # Step 1: Create contract
    c_resp = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_007",
            "seller_agent_id": "agent_seller_good",
            "seller_account_id": "acc_seller_linked_99",
            "amount_paise": 2500000,
        },
    )
    contract_id = c_resp.json()["contract_id"]

    # Step 2: Deliver 10 clean valid records
    records = [
        {"supplier_name": f"Supplier {i}", "gstin": "27AAPCA1234F1ZV", "invoice_number": f"INV-{i}", "amount_paise": 250000}
        for i in range(10)
    ]

    d_resp = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": contract_id,
            "seller_agent_id": "agent_seller_good",
            "payload_records": records,
        },
    )
    assert d_resp.status_code == 200
    d_data = d_resp.json()
    assert d_data["assertions_passed"] is True
    assert d_data["valid_records"] == 10
    assert d_data["failed_records"] == 0

    # Step 3: Execute Release
    r_resp = client.post(
        "/api/apex/contracts/release",
        json={"contract_id": contract_id, "checker_id": "cfo_test"},
    )
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["status"] == "RELEASED"
    assert r_data["on_hold"] is False
    assert r_data["amount_paise"] == 2500000
    assert "Route Transfer hold released" in r_data["message"]


# ── 5. Memory Bounds (<5MB) Enforcement ───────────────────────────────────────

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
        },
    )
    assert resp.status_code == 413
    assert "memory bounds" in resp.json()["detail"]
