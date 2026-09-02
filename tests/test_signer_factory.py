"""Tests for Signer Factory enforcement, algorithm reporting, and fail-closed KMS behaviors.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from kuber_recon.config import AppConfig, EnvironmentMode, SecurityConfigError
from kuber_recon.security import (
    AWSKMSAsymmetricCustodian,
    DualAuthorizationEngine,
    SoftwareEd25519Custodian,
    get_key_custodian,
)
from kuber_recon.server import app


class MockKMSClient:
    def __init__(self):
        self.public_key_bytes = b"k" * 32
        self.signatures = {}
        self.simulate_timeout = False
        self.simulate_malformed = False

    def sign(self, KeyId, Message, MessageType, SigningAlgorithm):
        if self.simulate_timeout:
            raise TimeoutError("AWS KMS Request timed out after 5000ms")
        if self.simulate_malformed:
            return {"InvalidKey": b""}  # missing 'Signature'
        sig = b"sig_" + Message[:28]
        self.signatures[sig] = Message
        return {"Signature": sig}

    def get_public_key(self, KeyId):
        if self.simulate_malformed:
            return {}  # missing 'PublicKey'
        return {"PublicKey": self.public_key_bytes}

    def verify(self, KeyId, Message, MessageType, Signature, SigningAlgorithm):
        if self.simulate_timeout:
            raise TimeoutError("AWS KMS Verify timed out")
        if self.simulate_malformed:
            return {}  # missing SignatureValid
        return {"SignatureValid": self.signatures.get(Signature) == Message}


def test_sandbox_selects_ed25519():
    """Verify that SANDBOX_DEMO environment selects SoftwareEd25519Custodian."""
    custodian = get_key_custodian(env=EnvironmentMode.SANDBOX_DEMO)
    assert isinstance(custodian, SoftwareEd25519Custodian)
    assert custodian.algorithm == "Ed25519"


def test_staging_selects_kms():
    """Verify that STAGING requires AWS KMS or an injected KMS test double."""
    mock_client = MockKMSClient()
    custodian = get_key_custodian(
        env=EnvironmentMode.STAGING,
        kms_client=mock_client,
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/staging-key",
    )
    assert isinstance(custodian, AWSKMSAsymmetricCustodian)
    assert custodian.algorithm == "ECDSA_SHA_256"

    # STAGING without KMS raises SecurityConfigError
    with patch("kuber_recon.security.config.use_aws_kms", False):
        with pytest.raises(SecurityConfigError) as exc:
            get_key_custodian(env=EnvironmentMode.STAGING)
        assert "STAGING" in str(exc.value)


def test_production_selects_kms():
    """Verify that PRODUCTION selects AWSKMSAsymmetricCustodian when configured."""
    mock_client = MockKMSClient()
    custodian = get_key_custodian(
        env=EnvironmentMode.PRODUCTION,
        kms_client=mock_client,
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/prod-key",
    )
    assert isinstance(custodian, AWSKMSAsymmetricCustodian)
    assert custodian.algorithm == "ECDSA_SHA_256"


def test_production_rejects_software_signer():
    """Verify that PRODUCTION strictly refuses SoftwareEd25519Custodian."""
    with pytest.raises(SecurityConfigError) as exc:
        get_key_custodian(env=EnvironmentMode.PRODUCTION)
    assert "PRODUCTION" in str(exc.value)
    assert "prohibited" in str(exc.value)

    # Direct instantiation in PRODUCTION also raises SecurityConfigError
    with patch("kuber_recon.security.config.environment", EnvironmentMode.PRODUCTION):
        with pytest.raises(SecurityConfigError):
            SoftwareEd25519Custodian()


def test_release_uses_factory_signer():
    """Verify that DualAuthorizationEngine release checks default to the factory signer."""
    engine = DualAuthorizationEngine()
    assert engine.custodian is not None
    assert engine.custodian.algorithm in ("Ed25519", "ECDSA_SHA_256")


def test_public_key_endpoint_reports_active_algorithm():
    """Verify that /api/apex/signer/public-key returns the active custodian algorithm."""
    with TestClient(app) as client:
        resp = client.get("/api/apex/signer/public-key")
        assert resp.status_code == 200
        data = resp.json()
        assert "algorithm" in data
        assert data["algorithm"] in ("Ed25519", "ECDSA_SHA_256")
        assert "public_key_hex" in data


def test_kms_timeout_fails_closed():
    """Verify that KMS timeouts fail closed during signing and verification."""
    mock_client = MockKMSClient()
    mock_client.simulate_timeout = True
    custodian = AWSKMSAsymmetricCustodian(
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/timeout-key",
        kms_client=mock_client,
    )
    # Sign fails closed with TimeoutError
    with pytest.raises(TimeoutError):
        custodian.sign_merkle_leaf("sha256:leaf_timeout", {"action": "RELEASE"})

    # Verify fails closed by returning False
    cert = MagicMock()
    cert.canonical_payload = "test"
    cert.signature_hex = "abcd"
    assert custodian.verify_certificate(cert) is False


def test_kms_malformed_response_fails_closed():
    """Verify that malformed KMS responses fail closed."""
    mock_client = MockKMSClient()
    mock_client.simulate_malformed = True
    custodian = AWSKMSAsymmetricCustodian(
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/malformed-key",
        kms_client=mock_client,
    )
    with pytest.raises(KeyError):
        custodian.sign_merkle_leaf("sha256:leaf_malformed", {"action": "RELEASE"})

    cert = MagicMock()
    cert.canonical_payload = "test"
    cert.signature_hex = "abcd"
    assert custodian.verify_certificate(cert) is False
