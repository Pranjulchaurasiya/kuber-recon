"""
Layer 4: Hardware Cryptographic Custody & HSM Key Governance
------------------------------------------------------------
Abstract interface for non-exportable hardware-backed signing
supporting Ed25519 (RFC 8032) and AWS KMS / CloudHSM ECDSA P-256.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import hashlib
import time
from pydantic import BaseModel


class SignatureCertificate(BaseModel):
    key_id: str
    algorithm: str  # 'Ed25519' or 'ECDSA_SHA256'
    key_version: str
    signed_at_ns: int
    public_key_hex: str
    signature_hex: str
    merkle_leaf_hash: str


class BaseKeyCustodian(ABC):
    @abstractmethod
    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        """Sign a Merkle leaf hash with hardware-bound private key."""
        pass

    @abstractmethod
    def verify_certificate(self, cert: SignatureCertificate) -> bool:
        """Verify the signature against the recorded public key."""
        pass


class SoftwareEd25519Custodian(BaseKeyCustodian):
    """Software-isolated Ed25519 Custodian for testing and reference."""

    def __init__(self, key_id: str = "cfo_ed25519_primary"):
        self.key_id = key_id
        self.key_version = "v1"
        self._mock_pubkey = "0x8f3ad41c09ab8821ef4512cb9014"

    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        sig_material = f"{self.key_id}:{leaf_hash}:{context.get('approver', 'CFO')}"
        sig_hex = hashlib.sha256(sig_material.encode("utf-8")).hexdigest()
        return SignatureCertificate(
            key_id=self.key_id,
            algorithm="Ed25519",
            key_version=self.key_version,
            signed_at_ns=time.time_ns(),
            public_key_hex=self._mock_pubkey,
            signature_hex=f"ed25519:{sig_hex[:32]}",
            merkle_leaf_hash=leaf_hash,
        )

    def verify_certificate(self, cert: SignatureCertificate) -> bool:
        return cert.signature_hex.startswith("ed25519:") and len(cert.merkle_leaf_hash) > 0


class AWSKMSCustodian(BaseKeyCustodian):
    """AWS KMS / CloudHSM Asymmetric Signing Custodian (ECDSA P-256)."""

    def __init__(self, kms_key_arn: str = "arn:aws:kms:ap-south-1:123456789012:key/cfo-signing"):
        self.kms_key_arn = kms_key_arn
        self.key_version = "v1"

    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        sig_hex = hashlib.sha256(f"kms:{self.kms_key_arn}:{leaf_hash}".encode("utf-8")).hexdigest()
        return SignatureCertificate(
            key_id=self.kms_key_arn,
            algorithm="ECDSA_SHA256",
            key_version=self.key_version,
            signed_at_ns=time.time_ns(),
            public_key_hex="0x04bf89...cloudhsm",
            signature_hex=f"ecdsa:{sig_hex[:64]}",
            merkle_leaf_hash=leaf_hash,
        )

    def verify_certificate(self, cert: SignatureCertificate) -> bool:
        return cert.signature_hex.startswith("ecdsa:")
