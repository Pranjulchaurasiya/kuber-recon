"""Tests for Key Custodian Factory, environment mapping, and AWS KMS test doubles.
"""

import time
import pytest
from kuber_recon.config import EnvironmentMode, SecurityConfigError
from kuber_recon.security import (
    AWSKMSAsymmetricCustodian,
    BaseKeyCustodian,
    SoftwareEd25519Custodian,
    get_key_custodian,
)


def test_key_custodian_factory_sandbox_defaults_to_ed25519():
    """Verify that SANDBOX_DEMO defaults to SoftwareEd25519Custodian."""
    custodian = get_key_custodian(env=EnvironmentMode.SANDBOX_DEMO)
    assert isinstance(custodian, SoftwareEd25519Custodian)
    assert custodian.key_id == "cfo_autonomous_verifier"


def test_key_custodian_factory_production_fails_closed_without_kms():
    """Verify that PRODUCTION fails closed if AWS KMS is not enabled."""
    with pytest.raises(SecurityConfigError, match="Software key custody is prohibited in PRODUCTION"):
        get_key_custodian(env=EnvironmentMode.PRODUCTION)


def test_key_custodian_factory_production_selects_kms():
    """Verify that PRODUCTION selects AWSKMSAsymmetricCustodian when KMS key ARN is supplied."""
    class DummyClient:
        pass

    custodian = get_key_custodian(
        env=EnvironmentMode.PRODUCTION,
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/test-prod-key",
        kms_client=DummyClient(),
    )
    assert isinstance(custodian, AWSKMSAsymmetricCustodian)
    assert custodian.key_arn == "arn:aws:kms:ap-south-1:123456789012:key/test-prod-key"


def test_kms_mock_signing_verification_and_failures():
    """Verify mock KMS client handling of sign, verify, malformed response, timeout, and errors."""
    
    class AdvancedMockKMSClient:
        def __init__(self):
            self.public_key_bytes = b"0" * 32
            self.signatures = {}
            self.simulate_timeout = False
            self.simulate_malformed = False
            self.simulate_error = False

        def sign(self, KeyId, Message, MessageType, SigningAlgorithm):
            if self.simulate_timeout:
                raise TimeoutError("AWS KMS Request timed out after 5000ms")
            if self.simulate_error:
                raise RuntimeError("AccessDeniedException: The ciphertext refers to a customer master key that does not exist")
            if self.simulate_malformed:
                return {}  # Missing 'Signature'
            import hashlib
            sig = hashlib.sha256(Message + b":kms_ecdsa_sha256").digest()
            self.signatures[sig] = Message
            return {"Signature": sig}

        def get_public_key(self, KeyId):
            return {"PublicKey": self.public_key_bytes}

        def verify(self, KeyId, Message, MessageType, Signature, SigningAlgorithm):
            if self.simulate_error:
                raise RuntimeError("KMS internal service failure")
            expected = self.signatures.get(Signature)
            return {"SignatureValid": expected == Message}

    mock_client = AdvancedMockKMSClient()
    custodian = AWSKMSAsymmetricCustodian(
        key_arn="arn:aws:kms:ap-south-1:123456789012:key/mock-fips-key",
        kms_client=mock_client,
    )

    context = {"approver": "cfo_risk_officer", "action": "RELEASE", "contract_id": "cnt_kms_test_99"}
    
    # 1. Normal Sign & Verify
    cert = custodian.sign_merkle_leaf("sha256:leaf_valid_123", context)
    assert cert.algorithm == "ECDSA_SHA_256"
    assert len(cert.signature_hex) > 0
    assert custodian.verify_certificate(cert) is True

    # 2. Malformed Response Handling
    mock_client.simulate_malformed = True
    with pytest.raises(KeyError):
        custodian.sign_merkle_leaf("sha256:leaf_malformed", context)
    mock_client.simulate_malformed = False

    # 3. Timeout Handling
    mock_client.simulate_timeout = True
    with pytest.raises(TimeoutError, match="timed out"):
        custodian.sign_merkle_leaf("sha256:leaf_timeout", context)
    mock_client.simulate_timeout = False

    # 4. KMS AccessDenied Exception
    mock_client.simulate_error = True
    with pytest.raises(RuntimeError, match="AccessDeniedException"):
        custodian.sign_merkle_leaf("sha256:leaf_error", context)
    # Verification failure on error returns False
    assert custodian.verify_certificate(cert) is False
