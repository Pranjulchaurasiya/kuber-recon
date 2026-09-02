"""Production Architecture, Security Invariants & Observability Test Suite.
"""

from decimal import Decimal
import os
from pathlib import Path
import tempfile
import pytest
from starlette.testclient import TestClient
from kuber_recon.config import AppConfig, EnvironmentMode, SecurityConfigError, config
from kuber_recon.events import FinancialEventEnvelope, TransactionalOutboxDispatcher
from kuber_recon.metrics import PrometheusMetricsRegistry
from kuber_recon.security import (
    AWSKMSAsymmetricCustodian,
    DualAuthorizationEngine,
    SoftwareEd25519Custodian,
    UserRole,
    create_access_token,
    decode_access_token,
)
from kuber_recon.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_production_config_validation_fails_on_insecure_primitives():
    """Verify that AppConfig fails closed if production mode has local simulations."""
    # 1. SQLite in Production must fail
    cfg = AppConfig(
        environment=EnvironmentMode.PRODUCTION,
        database_url="sqlite:///kuber.db",
        use_aws_kms=True,
        aws_kms_key_arn="arn:aws:kms:ap-south-1:123456789012:key/test",
        razorpay_key_id="rzp_live_123",
        razorpay_key_secret="secret_123",
        razorpay_webhook_secret="whsec_live_real_123",
        jwt_secret_key="prod_random_key_secure_123",
    )
    with pytest.raises(SecurityConfigError, match="SQLite is strictly prohibited in PRODUCTION"):
        cfg.validate_production_readiness()

    # 2. Software Key Signer in Production must fail
    cfg_no_kms = AppConfig(
        environment=EnvironmentMode.PRODUCTION,
        database_url="postgresql+psycopg2://user:pass@aurora-cluster.internal:5432/kuber",
        use_aws_kms=False,
        razorpay_key_id="rzp_live_123",
        razorpay_key_secret="secret_123",
        razorpay_webhook_secret="whsec_live_real_123",
        jwt_secret_key="prod_random_key_secure_123",
    )
    with pytest.raises(SecurityConfigError, match="Software demonstration key custody is prohibited in PRODUCTION"):
        cfg_no_kms.validate_production_readiness()


def test_dual_authorization_maker_checker_rule():
    """Verify Two-Person Rule for high-value releases above threshold."""
    dual_engine = DualAuthorizationEngine(threshold_paise=10000000)  # ₹1,00,000 threshold

    # Low value release (₹50,000 = 5,000,000 paise): Single signature suffices
    assert not dual_engine.is_dual_auth_required(5000000)
    
    # High value release (₹1,50,000 = 15,000,000 paise): Dual signatures required
    assert dual_engine.is_dual_auth_required(15000000)

    # Primary Maker
    custodian_maker = SoftwareEd25519Custodian(key_id="cfo_autonomous_verifier")
    context_maker = {"approver": "cfo_autonomous_verifier", "action": "RELEASE", "contract_id": "apex_dual_01"}
    cert_maker = custodian_maker.sign_merkle_leaf("sha256:leaf_abc", context_maker)

    primary_dict = {
        "checker_id": "cfo_autonomous_verifier",
        "public_key_hex": cert_maker.public_key_hex,
        "signature_hex": cert_maker.signature_hex,
    }

    # If dual auth is required and no secondary cert provided -> Reject
    assert not dual_engine.verify_dual_authorization(
        amount_paise=15000000,
        contract_id="apex_dual_01",
        leaf_hash="sha256:leaf_abc",
        primary_cert=primary_dict,
        secondary_cert=None,
    )

    # Secondary Checker
    custodian_checker = SoftwareEd25519Custodian(key_id="cfo_ed25519_primary")
    context_checker = {"approver": "cfo_ed25519_primary", "action": "RELEASE", "contract_id": "apex_dual_01"}
    cert_checker = custodian_checker.sign_merkle_leaf("sha256:leaf_abc", context_checker)

    secondary_dict = {
        "checker_id": "cfo_ed25519_primary",
        "public_key_hex": cert_checker.public_key_hex,
        "signature_hex": cert_checker.signature_hex,
    }

    # Valid Maker + Checker dual authorization -> Pass
    assert dual_engine.verify_dual_authorization(
        amount_paise=15000000,
        contract_id="apex_dual_01",
        leaf_hash="sha256:leaf_abc",
        primary_cert=primary_dict,
        secondary_cert=secondary_dict,
    )

    # Collusion attempt (Maker tries to sign as Checker with same identity) -> Reject
    assert not dual_engine.verify_dual_authorization(
        amount_paise=15000000,
        contract_id="apex_dual_01",
        leaf_hash="sha256:leaf_abc",
        primary_cert=primary_dict,
        secondary_cert=primary_dict,
    )


def test_jwt_rbac_token_issuance_and_claims():
    """Verify JWT access token generation and claims decoding."""
    token = create_access_token(
        subject="risk_officer_01",
        tenant_id="merchant_rzp_primary",
        roles=[UserRole.RISK_OFFICER, UserRole.FINANCE_REVIEWER],
    )
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.sub == "risk_officer_01"
    assert payload.tenant_id == "merchant_rzp_primary"
    assert UserRole.RISK_OFFICER in payload.roles
    assert UserRole.FINANCE_REVIEWER in payload.roles


def test_durable_sqlite_outbox_and_dlq_restart():
    """Verify SQLite WAL outbox persistence, restart survival, idempotency, and DLQ quarantine."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_file = Path(tmpdir) / "test_outbox.db"
        
        # 1. First Dispatcher instance stages events
        dispatcher1 = TransactionalOutboxDispatcher(db_path=db_file)
        env1 = FinancialEventEnvelope(
            event_id="evt_001",
            event_type="escrow.held",
            tenant_id="tenant_01",
            aggregate_id="contract_100",
            correlation_id="corr_100",
            idempotency_key="idem_100",
            payload={"amount_paise": 500000},
        )
        rec1 = dispatcher1.stage_event(env1)
        assert not rec1.published
        assert dispatcher1.pending_count == 1
        assert dispatcher1.published_count == 0

        # Duplicate staging with same idempotency key returns existing record without duplicating
        rec1_dup = dispatcher1.stage_event(env1)
        assert rec1_dup.id == rec1.id
        assert dispatcher1.pending_count == 1

        # 2. Simulate Process Restart by instantiating new Dispatcher pointing to same DB
        dispatcher2 = TransactionalOutboxDispatcher(db_path=db_file)
        assert dispatcher2.pending_count == 1
        assert dispatcher2.published_count == 0

        # CDC Polling publishes the pending event
        published = dispatcher2.poll_and_publish_cdc(batch_size=10)
        assert published == 1
        assert dispatcher2.published_count == 1
        assert dispatcher2.pending_count == 0

        # 3. Stage poison pill and quarantine to DLQ
        env_poison = FinancialEventEnvelope(
            event_id="evt_poison",
            event_type="escrow.corrupt",
            tenant_id="tenant_01",
            aggregate_id="contract_poison",
            correlation_id="corr_poison",
            idempotency_key="idem_poison",
            payload={"corrupt": True},
        )
        rec_poison = dispatcher2.stage_event(env_poison)
        dlq_rec = dispatcher2.route_to_dlq(rec_poison.id, reason="Corrupted statutory tax jurisdiction")
        assert dlq_rec is not None
        assert dlq_rec.failure_reason == "Corrupted statutory tax jurisdiction"
        assert dispatcher2.dlq_count == 1


def test_mock_aws_kms_signing_and_verification():
    """Verify AWSKMSAsymmetricCustodian with a mock KMS client test double."""
    class MockKMSClient:
        def __init__(self):
            self.public_key_bytes = b"0" * 32
            self.signatures = {}

        def sign(self, KeyId, Message, MessageType, SigningAlgorithm):
            import hashlib
            sig = hashlib.sha256(Message + b":kms_mock_sig").digest()
            self.signatures[sig] = Message
            return {"Signature": sig}

        def get_public_key(self, KeyId):
            return {"PublicKey": self.public_key_bytes}

        def verify(self, KeyId, Message, MessageType, Signature, SigningAlgorithm):
            expected = self.signatures.get(Signature)
            return {"SignatureValid": expected == Message}

    mock_client = MockKMSClient()
    kms_custodian = AWSKMSAsymmetricCustodian(
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/test-prod-key",
        region="ap-south-1",
        kms_client=mock_client,
    )

    context = {"approver": "cfo_kms_approver", "action": "RELEASE", "contract_id": "cnt_kms_01"}
    cert = kms_custodian.sign_merkle_leaf("sha256:leaf_kms_123", context)

    assert cert.algorithm == "ECDSA_SHA_256"
    assert len(cert.signature_hex) > 0
    assert cert.key_id == "arn:aws:kms:ap-south-1:123456789012:key/test-prod-key"

    # Verify certificate against mock KMS
    assert kms_custodian.verify_certificate(cert)


def test_secured_jwt_token_endpoint(client):
    """Verify that POST /api/v2/auth/token enforces authentication and prohibits cross-tenant spoofing."""
    # 1. Unauthenticated request -> HTTP 401
    resp_unauth = client.post("/api/v2/auth/token", json={
        "subject": "attacker",
        "tenant_id": "merchant_rzp_primary",
        "roles": ["ADMINISTRATOR"],
    })
    assert resp_unauth.status_code == 401

    # 2. Authenticated as merchant_agent_demo_01, but trying to mint for merchant_rzp_primary -> HTTP 403
    resp_cross = client.post(
        "/api/v2/auth/token",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
        json={
            "subject": "agent_user",
            "tenant_id": "merchant_rzp_primary",
            "roles": ["MERCHANT_OPERATOR"],
        },
    )
    assert resp_cross.status_code == 403

    # 3. Authenticated for self tenant with valid roles -> HTTP 200
    resp_valid = client.post(
        "/api/v2/auth/token",
        headers={
            "X-Merchant-Id": "merchant_agent_demo_01",
            "X-API-Key": "kuber_sandbox_key_agent_01_2026",
        },
        json={
            "subject": "agent_user",
            "tenant_id": "merchant_agent_demo_01",
            "roles": ["MERCHANT_OPERATOR", "FINANCE_REVIEWER"],
        },
    )
    assert resp_valid.status_code == 200
    data = resp_valid.json()
    assert "access_token" in data
    assert data["tenant_id"] == "merchant_agent_demo_01"


def test_health_endpoints_dual_support(client):
    """Verify both /health and /api/health respond with 200 for Docker/K8s probes."""
    resp1 = client.get("/api/health")
    resp2 = client.get("/health")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["status"] == "live"
    assert resp2.json()["status"] == "live"


def test_prometheus_metrics_export():
    """Verify Prometheus registry renders valid metric lines."""
    reg = PrometheusMetricsRegistry()
    reg.record_http_request("POST", "/api/intercept", 200)
    reg.record_reconciliation(paise=150000, duration_ms=4.5)
    reg.record_sweep(paise=18000)
    reg.record_security_event("unauthorized")

    output = reg.render_prometheus_text()
    assert "kuber_http_requests_total" in output
    assert "kuber_paise_reconciled_total 150000" in output
    assert "kuber_paise_settled_swept_total 18000" in output
    assert 'kuber_security_events_total{type="unauthorized"} 1' in output
