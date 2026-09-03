"""End-to-End Tests for Strict Narration Release Guards and Server-Side 5-Point Provider Join.
================================================================================================
Verifies that:
1. Tier C (malformed narration) fails closed at release transition (HTTP 412).
2. Tier B (non-authoritative missing aggregator token) fails closed at release transition (HTTP 412).
3. Tier A (valid clean UTR) alone with ZERO provider records in server-side store fails closed (HTTP 412).
4. Tier A with MULTIPLE ambiguous server-side provider records fails closed (HTTP 412).
5. Tier A with mismatched amount or account ID fails closed via 5-point join (HTTP 412).
6. Tier A with valid server-side 5-point join successfully triggers contract release (HTTP 200).
7. Dedicated /auto-release-from-narration endpoint enforces server-side join without client records.
8. Attacker exploit attempting to pass forged client-controlled `provider_records` is rejected (HTTP 422/412) and funds remain held.
9. Narration memos without extractable statement dates are refused for automated release (HTTP 412).
10. Rail-specific date variance limits (e.g. RTGS 1 day limit) are dynamically enforced against server records.
"""

from datetime import date, timedelta
import hashlib
import json
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from kuber_recon.narration_parser import NarrationEvidenceTier
from kuber_recon.server import WebhookIdempotencyStore, app
import kuber_recon.server as srv


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    tmp_db = tmp_path / "test_narration_guard.db"
    monkeypatch.setattr(WebhookIdempotencyStore, "DB_FILE", tmp_db)
    monkeypatch.setattr(srv.razorpay_adapter, "is_live", False)
    srv.idempotency_store = WebhookIdempotencyStore()
    yield


@pytest.fixture
def client():
    return TestClient(
        app,
        headers={
            "X-Merchant-Id": "merchant_rzp_primary",
            "X-API-Key": "kuber_sandbox_key_primary_2026",
        },
    )


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


def _setup_verified_contract(client: TestClient, contract_amount_paise: int = 2500000) -> dict:
    """Helper: Creates a contract, delivers verified records, and returns release signature."""
    seller_id = "agent_seller_data_01"
    res_create = client.post(
        "/api/apex/contracts/create",
        json={
            "buyer_agent_id": "agent_buyer_procurement_01",
            "seller_agent_id": seller_id,
            "seller_account_id": "acc_mock_seller_001",
            "amount_paise": contract_amount_paise,
            "expected_record_count": 2,
            "ttl_seconds": 86400,
        },
    )
    assert res_create.status_code == 200, res_create.text
    contract_id = res_create.json()["contract_id"]

    half_paise = contract_amount_paise // 2
    rem_paise = contract_amount_paise - half_paise
    payload_records = [
        {
            "supplier_name": "Supplier Alpha",
            "gstin": "27AAPFU0939F1ZV",
            "invoice_number": "INV-G-001",
            "amount_paise": half_paise,
        },
        {
            "supplier_name": "Supplier Beta",
            "gstin": "27AAPFU0939F1ZV",
            "invoice_number": "INV-G-002",
            "amount_paise": rem_paise,
        },
    ]
    pub, sig = _sign_seller_manifest(payload_records, seller_id)

    res_deliver = client.post(
        "/api/apex/contracts/deliver",
        json={
            "contract_id": contract_id,
            "seller_agent_id": seller_id,
            "payload_records": payload_records,
            "manifest_signature": sig,
            "seller_public_key_hex": pub,
        },
    )
    assert res_deliver.status_code == 200, res_deliver.text
    assert res_deliver.json()["assertions_passed"] is True
    proof_hash = res_deliver.json()["manifest_sha256"]

    chk_pub, chk_sig = _sign_release(contract_id, proof_hash)

    return {
        "contract_id": contract_id,
        "amount_paise": contract_amount_paise,
        "checker_id": "cfo_autonomous_verifier",
        "public_key_hex": chk_pub,
        "signature_hex": chk_sig,
        "seller_account_id": "acc_mock_seller_001",
    }


def test_tier_c_malformed_narration_refused_at_release(client):
    """Invariant: Tier C malformed bank clearing memos cannot trigger release."""
    c_info = _setup_verified_contract(client)

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": "DISTRICT COOP BANK CLG REF 9901 INVALID MEMO",
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "TIER_C_EXCEPTION" in res.json()["detail"]


def test_tier_b_missing_aggregator_token_refused_at_release(client):
    """Invariant: Tier B heuristic narrations lacking aggregator authorization cannot trigger release."""
    c_info = _setup_verified_contract(client)

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": "NEFT-SBIN008827163541-DIRECT*DEP-MISC",
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "TIER_B_HEURISTIC" in res.json()["detail"]


def test_tier_a_alone_without_provider_match_refused(client):
    """Invariant: Narration data alone cannot trigger release when zero provider records exist server-side."""
    c_info = _setup_verified_contract(client)

    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*HDFCN009827163*{today_str}"

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "Zero trusted provider records matched candidate UTR" in res.json()["detail"]
    assert "Funds cannot be released on narration alone" in res.json()["detail"]


def test_tier_a_with_multiple_ambiguous_provider_matches_refused(client):
    """Invariant: Ambiguous join with multiple provider records matching candidate UTR fails closed."""
    c_info = _setup_verified_contract(client)

    utr = "HDFCN009827163"
    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*{utr}*{today_str}"

    # Seed 2 conflicting provider records into the server's authoritative store
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_prov_001",
        "transfer_id": "trf_prov_001",
        "expected_utr": utr,
        "amount_paise": c_info["amount_paise"],
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_prov_002",
        "transfer_id": "trf_prov_002",
        "expected_utr": utr,
        "amount_paise": c_info["amount_paise"],
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })

    # Client sends request WITHOUT any provider_records
    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "Ambiguous candidate match: 2 matching provider records found" in res.json()["detail"]


def test_tier_a_with_mismatched_amount_refused(client):
    """Invariant: 5-Point join fails if candidate contract amount does not match provider record amount."""
    c_info = _setup_verified_contract(client, contract_amount_paise=2500000)

    utr = "HDFCN009827163"
    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*{utr}*{today_str}"

    # Server store has mismatched amount (2000000 != 2500000)
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_prov_mismatch_amt",
        "transfer_id": "trf_prov_mismatch",
        "expected_utr": utr,
        "amount_paise": 2000000,
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "Amount/Currency mismatch" in res.json()["detail"]


def test_tier_a_with_mismatched_merchant_account_refused(client):
    """Invariant: 5-Point join fails if provider record merchant account does not match contract seller."""
    c_info = _setup_verified_contract(client)

    utr = "HDFCN009827163"
    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*{utr}*{today_str}"

    # Server store has wrong merchant account
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_prov_mismatch_acc",
        "transfer_id": "trf_prov_mismatch_acc",
        "expected_utr": utr,
        "amount_paise": c_info["amount_paise"],
        "currency": "INR",
        "merchant_account_id": "acc_WRONG_MERCHANT_999",
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "Merchant account ID mismatch" in res.json()["detail"]


def test_tier_a_with_valid_5_point_join_succeeds_and_releases(client):
    """Invariant: Tier A narration joined to matching server-side trusted provider record releases hold successfully."""
    c_info = _setup_verified_contract(client, contract_amount_paise=2500000)

    utr = "HDFCN009827163"
    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*{utr}*{today_str}"

    # Seed authoritative server-side provider record
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_verified_01",
        "transfer_id": "trf_hdfc_verified_01",
        "expected_utr": utr,
        "amount_paise": 2500000,
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "webhook",
        "tenant_id": "merchant_rzp_primary",
    })

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "RELEASING"
    assert data["on_hold_modified"] is True
    assert data["narration_join_audit"]["join_verified"] is True
    assert data["narration_join_audit"]["candidate_utr"] == utr
    assert data["narration_join_audit"]["evidence_tier"] == NarrationEvidenceTier.TIER_A_CANDIDATE.value
    assert data["narration_join_audit"]["rail_type"] == "NEFT"


def test_auto_release_from_narration_endpoint(client):
    """Verify dedicated statement-clearing auto-release endpoint enforces server-side 5-point join."""
    c_info = _setup_verified_contract(client, contract_amount_paise=2500000)

    utr = "HDFCN009827163"
    today_str = date.today().strftime("%Y%m%d")
    clean_tier_a = f"NFX-RZR*SETTL*ST9901*{utr}*{today_str}"

    # Seed authoritative server-side provider record
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_verified_auto_01",
        "transfer_id": "trf_hdfc_verified_auto_01",
        "expected_utr": utr,
        "amount_paise": 2500000,
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "webhook",
        "tenant_id": "merchant_rzp_primary",
    })

    # 1. Invalid attempt with Tier C narration -> Fails closed 412
    res_fail = client.post(
        "/api/apex/contracts/auto-release-from-narration",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": "INVALID RURAL MEMO",
        },
    )
    assert res_fail.status_code == 412
    assert "TIER_C_EXCEPTION" in res_fail.json()["detail"]

    # 2. Valid attempt with clean Tier A narration + server-side matching record -> Releases 200
    res_pass = client.post(
        "/api/apex/contracts/auto-release-from-narration",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": clean_tier_a,
        },
    )
    assert res_pass.status_code == 200, res_pass.text
    assert res_pass.json()["status"] == "RELEASING"
    assert res_pass.json()["narration_join_audit"]["join_verified"] is True


def test_forged_client_provider_records_exploit_rejected(client):
    """
    SECURITY AUDIT EXPLOIT TEST:
    Attacker crafts a fabricated `provider_records` payload in the release request
    aiming to trick the 5-point join into verifying client-controlled data.
    Invariant:
    - The request MUST be rejected (HTTP 422 extra inputs forbidden or HTTP 412 provider join refusal).
    - Under NO circumstances can funds be released.
    - Contract state MUST remain HELD with on_hold == 1.
    """
    c_info = _setup_verified_contract(client, contract_amount_paise=5000000)

    fake_utr = "FAKERZP999888777"
    fake_narration = f"NFX-RZR*SETTL*ST9901*{fake_utr}*{date.today().strftime('%Y%m%d')}"

    forged_provider = {
        "expected_utr": fake_utr,
        "amount_paise": 5000000,
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "provider_transfer_id": "trf_forged_by_attacker_999",
    }

    # Attempt 1: Exploit against /api/apex/contracts/release
    res_release = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": fake_narration,
            "require_narration_join": True,
            "provider_records": [forged_provider],  # <--- Attacker injection
        },
    )
    # Pydantic ConfigDict(extra="forbid") rejects extra inputs with 422
    assert res_release.status_code in (412, 422)

    # Attempt 2: Exploit against /api/apex/contracts/auto-release-from-narration
    res_auto = client.post(
        "/api/apex/contracts/auto-release-from-narration",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": fake_narration,
            "provider_records": [forged_provider],  # <--- Attacker injection
        },
    )
    assert res_auto.status_code in (412, 422)

    # Invariant check: Assert contract was NOT released and hold remains strictly active
    contract = srv.idempotency_store.get_contract(c_info["contract_id"])
    assert contract is not None
    assert contract["status"] in ("HELD", "VERIFYING")
    assert contract["status"] != "RELEASING"
    assert contract["status"] != "RELEASED"
    assert contract["on_hold"] == 1


def test_tier_a_without_date_token_refused_for_automated_release(client):
    """Invariant: Narration memos without extractable statement date token refuse automated release."""
    c_info = _setup_verified_contract(client)

    utr = "HDFCN009827163"
    # Narration memo has UTR and aggregator tokens, but NO date token
    narration_without_date = f"NFX-RZR*SETTL*ST9901*{utr}"

    # Seed authoritative server record
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_hdfc_no_date_test",
        "transfer_id": "trf_hdfc_no_date",
        "expected_utr": utr,
        "amount_paise": c_info["amount_paise"],
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "NEFT",
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": narration_without_date,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "Narration Date Verification Refusal" in res.json()["detail"]


def test_tier_a_date_variance_exceeds_rail_tolerance_refused(client):
    """Invariant: Date variance exceeding rail-specific limits (RTGS: 1 day) fails closed."""
    c_info = _setup_verified_contract(client)

    utr = "HDFCN009827163"
    # Narration date is 5 days after settlement date
    narration_date = date.today() + timedelta(days=5)
    narration_date_str = narration_date.strftime("%Y%m%d")
    narration_with_stale_date = f"NFX-RZR*SETTL*ST9901*{utr}*{narration_date_str}"

    # Seed RTGS record with strict 1-day variance limit
    srv.idempotency_store.save_trusted_provider_record({
        "provider_record_id": "rec_rtgs_variance_test",
        "transfer_id": "trf_rtgs_variance",
        "expected_utr": utr,
        "amount_paise": c_info["amount_paise"],
        "currency": "INR",
        "merchant_account_id": c_info["seller_account_id"],
        "settlement_status": "processed",
        "settlement_date": str(date.today()),
        "rail_type": "RTGS",  # 1-day limit
        "source": "server_store",
        "tenant_id": "merchant_rzp_primary",
    })

    res = client.post(
        "/api/apex/contracts/release",
        json={
            "contract_id": c_info["contract_id"],
            "checker_id": c_info["checker_id"],
            "public_key_hex": c_info["public_key_hex"],
            "signature_hex": c_info["signature_hex"],
            "bank_narration": narration_with_stale_date,
            "require_narration_join": True,
        },
    )
    assert res.status_code == 412
    assert "5-Point Provider Join Refusal" in res.json()["detail"]
    assert "exceeds RTGS rail limit (1 days)" in res.json()["detail"]

