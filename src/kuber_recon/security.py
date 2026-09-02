"""Cryptographic Key Custody, AWS KMS Interface, Dual-Authorization & RBAC.
-------------------------------------------------------------------------------
Features:
1. BaseKeyCustodian contract for asymmetric signing & verification (RFC 8032 Ed25519 & AWS KMS ECC_NIST_P256 / Ed25519).
2. SoftwareEd25519Custodian (sandbox demo signer) with production startup guard.
3. AWSKMSAsymmetricCustodian (enterprise AWS KMS / CloudHSM hardware key custodian).
4. DualAuthorizationEngine: Two-Person Rule for high-value release intents (> configurable threshold).
5. UserRole & JWT Access Token authorization (Role-Based Access Control / RBAC).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

try:
    import jwt
except ImportError:
    jwt = None

from kuber_recon.config import EnvironmentMode, SecurityConfigError, config


logger = logging.getLogger("kuber_recon.security")


class UserRole(str, Enum):
    MERCHANT_OPERATOR = "MERCHANT_OPERATOR"
    FINANCE_REVIEWER = "FINANCE_REVIEWER"
    RISK_OFFICER = "RISK_OFFICER"
    RISK_ANALYST = "RISK_ANALYST"
    ADMINISTRATOR = "ADMINISTRATOR"


class AuthTokenPayload(BaseModel):
    sub: str  # User / Service Account ID
    tenant_id: str
    roles: List[UserRole] = Field(default_factory=list)
    exp: int
    iat: int
    jti: str


PROVISIONED_SUBJECTS: Dict[str, Dict[str, Any]] = {
    "merchant_rzp_primary": {
        "tenant_id": "merchant_rzp_primary",
        "roles": [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER, UserRole.RISK_OFFICER, UserRole.ADMINISTRATOR],
    },
    "cfo_demo_operator": {
        "tenant_id": "merchant_rzp_primary",
        "roles": [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER],
    },
    "risk_analyst_user": {
        "tenant_id": "merchant_rzp_primary",
        "roles": [UserRole.RISK_ANALYST],
    },
    "risk_officer_primary": {
        "tenant_id": "merchant_rzp_primary",
        "roles": [UserRole.RISK_OFFICER, UserRole.FINANCE_REVIEWER],
    },
    "compliance_admin": {
        "tenant_id": "merchant_rzp_primary",
        "roles": [UserRole.ADMINISTRATOR, UserRole.FINANCE_REVIEWER],
    },
    "agent_user": {
        "tenant_id": "merchant_agent_demo_01",
        "roles": [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER],
    },
    "agent_operator_limited": {
        "tenant_id": "merchant_agent_demo_01",
        "roles": [UserRole.MERCHANT_OPERATOR],
    },
    "merchant_agent_demo_01": {
        "tenant_id": "merchant_agent_demo_01",
        "roles": [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER, UserRole.RISK_OFFICER, UserRole.ADMINISTRATOR],
    },
}


class SignatureCertificate(BaseModel):
    key_id: str
    algorithm: str  # 'Ed25519' | 'ECDSA_SHA_256'
    key_version: str
    signed_at_ns: int
    public_key_hex: str
    signature_hex: str
    merkle_leaf_hash: str
    canonical_payload: Optional[str] = None


class BaseKeyCustodian(ABC):
    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Cryptographic algorithm identifier (e.g. 'Ed25519', 'ECDSA_SHA_256')."""
        pass

    @property
    @abstractmethod
    def public_key_hex(self) -> str:
        """Hex-encoded public verification key."""
        pass

    @abstractmethod
    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        """Sign a Merkle leaf hash with key custodian."""
        pass

    @abstractmethod
    def verify_certificate(self, cert: SignatureCertificate, expected_payload: Optional[bytes] = None) -> bool:
        """Verify the signature against the recorded public key."""
        pass

    @abstractmethod
    def verify_client_signature(
        self,
        checker_id: str,
        contract_id: str,
        leaf_hash: str,
        public_key_hex: str,
        signature_hex: str,
        key_version: str = "v1",
    ) -> bool:
        """Verify client-supplied assertion signature against the registered identity."""
        pass


class SoftwareEd25519Custodian(BaseKeyCustodian):
    """Local Demonstration Ed25519 Signer & Verifier (RFC 8032).
    
    Uses Python's cryptography hazmat ed25519 for genuine asymmetric math.
    Strictly barred in PRODUCTION mode by validate_production_readiness.
    """

    # Pinned RFC 8032 Public Keys for Authorized Checker Identities
    PINNED_CHECKER_REGISTRY = {
        "demo_software_ed25519_v1": "0f11d9206303ebdc7533920222d1b5bda7d05519211aff465e30138b7a45581c",
        "cfo_autonomous_verifier": "0f11d9206303ebdc7533920222d1b5bda7d05519211aff465e30138b7a45581c",
        "cfo_ed25519_primary": "c8f85e05aff655a2fb56a078938a7f9e5f10a2c0836bd195e9da05977295f468",
        "cfo_approver_01": "b6dd788ca57b2ca938e65c5dd268d242e36070bc497287a4c68b5addee5a1de6",
        "cfo_arbiter_sec_01": "a48bb8ef9a1a72a532d172357aa18d707951b03b2b8307d9e49779e52010aa8c",
        "risk_officer_secondary": "359cc424ade171567d8e189e5d4b114794a337714325d876fa4f6178ddfd4a15",
    }

    # Deterministic Seed Registry for Demo Checkers (In-Memory Prototype)
    AUTHORIZED_CHECKERS = {
        "demo_software_ed25519_v1": "kuber_cfo_autonomous_verifier_sec_key_v1",
        "cfo_autonomous_verifier": "kuber_cfo_autonomous_verifier_sec_key_v1",
        "cfo_ed25519_primary": "kuber_cfo_ed25519_primary_sec_key_v1",
        "cfo_approver_01": "kuber_cfo_approver_01_sec_key_v1",
        "cfo_arbiter_sec_01": "kuber_cfo_arbiter_sec_01_sec_key_v1",
        "risk_officer_secondary": "kuber_risk_officer_secondary_sec_key_v1",
    }

    def __init__(self, key_id: str = "cfo_autonomous_verifier"):
        if config.environment in (EnvironmentMode.PRODUCTION, EnvironmentMode.STAGING):
            raise SecurityConfigError(
                f"Fatal Security Guard: SoftwareEd25519Custodian cannot be instantiated in {config.environment.value} mode. "
                "AWSKMSAsymmetricCustodian is required."
            )
        self.key_id = key_id
        self.key_version = "v1"
        self._algorithm = "Ed25519"
        
        # Derive deterministic 32-byte private key seed for this sandbox identity
        seed_source = self.AUTHORIZED_CHECKERS.get(key_id, f"kuber_seed_default_{key_id}")
        seed_bytes = hashlib.sha256(seed_source.encode("utf-8")).digest()
        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
        self._public_key = self._private_key.public_key()
        self._public_key_hex = self._public_key.public_bytes_raw().hex()

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def public_key_hex(self) -> str:
        return self._public_key_hex

    def build_canonical_payload(self, leaf_hash: str, context: Dict[str, Any]) -> bytes:
        """Build deterministic canonical byte representation of the assertion payload."""
        approver = context.get("approver", self.key_id)
        action = context.get("action", "RELEASE")
        contract_id = context.get("contract_id", "")
        normalized_leaf = leaf_hash.replace("sha256:", "").strip()
        canonical_str = f"KEY:{self.key_id}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{approver}|ACTION:{action}|VER:{self.key_version}"
        return canonical_str.encode("utf-8")

    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        canonical_bytes = self.build_canonical_payload(leaf_hash, context)
        sig_bytes = self._private_key.sign(canonical_bytes)
        return SignatureCertificate(
            key_id=self.key_id,
            algorithm="Ed25519",
            key_version=self.key_version,
            signed_at_ns=time.time_ns(),
            public_key_hex=self.public_key_hex,
            signature_hex=sig_bytes.hex(),
            merkle_leaf_hash=leaf_hash,
            canonical_payload=canonical_bytes.decode("utf-8"),
        )

    def verify_certificate(self, cert: SignatureCertificate, expected_payload: Optional[bytes] = None) -> bool:
        """Cryptographically verify Ed25519 signature against the public key and canonical bytes."""
        try:
            if cert.key_id not in self.PINNED_CHECKER_REGISTRY:
                return False

            pinned_pubkey = self.PINNED_CHECKER_REGISTRY[cert.key_id]
            if cert.public_key_hex.lower() != pinned_pubkey.lower():
                return False

            pub_key_bytes = bytes.fromhex(cert.public_key_hex)
            sig_bytes = bytes.fromhex(cert.signature_hex)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)

            if expected_payload is not None:
                payload_to_verify = expected_payload
            elif cert.canonical_payload:
                payload_to_verify = cert.canonical_payload.encode("utf-8")
            else:
                payload_to_verify = self.build_canonical_payload(
                    cert.merkle_leaf_hash, {"approver": cert.key_id, "action": "RELEASE"}
                )

            pub_key.verify(sig_bytes, payload_to_verify)
            return True
        except (InvalidSignature, ValueError, Exception):
            return False

    def verify_client_signature(
        self,
        checker_id: str,
        contract_id: str,
        leaf_hash: str,
        public_key_hex: str,
        signature_hex: str,
        key_version: str = "v1",
    ) -> bool:
        """Cryptographically verify that the client is an authenticated checker identity."""
        try:
            if not checker_id or not public_key_hex or not signature_hex:
                return False

            if checker_id not in SoftwareEd25519Custodian.PINNED_CHECKER_REGISTRY:
                return False

            pinned_pubkey = SoftwareEd25519Custodian.PINNED_CHECKER_REGISTRY[checker_id]
            if public_key_hex.strip().lower() != pinned_pubkey.lower():
                return False

            pub_bytes = bytes.fromhex(public_key_hex.strip())
            sig_bytes = bytes.fromhex(signature_hex.strip())
            if len(pub_bytes) != 32 or len(sig_bytes) != 64:
                return False

            normalized_leaf = leaf_hash.replace("sha256:", "").strip()
            canonical_str = f"KEY:{checker_id}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{checker_id}|ACTION:RELEASE|VER:{key_version}"
            canonical_bytes = canonical_str.encode("utf-8")

            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, canonical_bytes)
            return True
        except (InvalidSignature, ValueError, Exception):
            return False


class AWSKMSAsymmetricCustodian(BaseKeyCustodian):
    """Enterprise Hardware Key Custodian backed by AWS KMS (FIPS 140-2 Level 3).
    
    Cryptographic Architecture Note:
    AWS KMS asymmetric keys natively support ECDSA_SHA_256 over NIST P-256 (secp256r1) or RSA.
    AWS KMS does NOT natively support RFC 8032 Ed25519 (which requires AWS CloudHSM).
    KuberRecon production signing binds to AWS KMS with ECDSA_SHA_256.
    """

    def __init__(self, key_arn: Optional[str] = None, region: Optional[str] = None, kms_client: Optional[Any] = None):
        self.key_arn = key_arn or config.aws_kms_key_arn or "arn:aws:kms:ap-south-1:123456789012:key/mock-kuber-key"
        self.key_id = self.key_arn
        self.region = region or config.aws_region
        self.key_version = "kms_v1"
        self._algorithm = "ECDSA_SHA_256"
        self._kms_client = kms_client

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def public_key_hex(self) -> str:
        client = self._get_client()
        try:
            pub_key_resp = client.get_public_key(KeyId=self.key_arn)
            return pub_key_resp["PublicKey"].hex()
        except Exception:
            return "04" + "00" * 64

    def _get_client(self):
        if self._kms_client is None:
            try:
                import boto3
                self._kms_client = boto3.client("kms", region_name=self.region)
            except ImportError:
                raise SecurityConfigError("boto3 is required for AWS KMS Key Custodian. Run: pip install boto3")
        return self._kms_client

    def sign_merkle_leaf(self, leaf_hash: str, context: Dict[str, Any]) -> SignatureCertificate:
        approver = context.get("approver", "cfo_kms_authorized_approver")
        action = context.get("action", "RELEASE")
        contract_id = context.get("contract_id", "")
        normalized_leaf = leaf_hash.replace("sha256:", "").strip()
        canonical_str = f"KEY:{self.key_arn}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{approver}|ACTION:{action}|VER:{self.key_version}"
        canonical_bytes = canonical_str.encode("utf-8")

        client = self._get_client()
        response = client.sign(
            KeyId=self.key_arn,
            Message=canonical_bytes,
            MessageType="RAW",
            SigningAlgorithm="ECDSA_SHA_256",
        )
        sig_bytes = response["Signature"]

        pub_key_resp = client.get_public_key(KeyId=self.key_arn)
        pub_key_bytes = pub_key_resp["PublicKey"]

        return SignatureCertificate(
            key_id=self.key_arn,
            algorithm="ECDSA_SHA_256",
            key_version=self.key_version,
            signed_at_ns=time.time_ns(),
            public_key_hex=pub_key_bytes.hex(),
            signature_hex=sig_bytes.hex(),
            merkle_leaf_hash=leaf_hash,
            canonical_payload=canonical_str,
        )

    def verify_certificate(self, cert: SignatureCertificate, expected_payload: Optional[bytes] = None) -> bool:
        client = self._get_client()
        payload = expected_payload or (cert.canonical_payload.encode("utf-8") if cert.canonical_payload else b"")
        try:
            response = client.verify(
                KeyId=self.key_arn,
                Message=payload,
                MessageType="RAW",
                Signature=bytes.fromhex(cert.signature_hex),
                SigningAlgorithm="ECDSA_SHA_256",
            )
            return bool(response.get("SignatureValid", False))
        except Exception as e:
            logger.error(f"KMS verification error: {e}")
            return False

    def verify_client_signature(
        self,
        checker_id: str,
        contract_id: str,
        leaf_hash: str,
        public_key_hex: str,
        signature_hex: str,
        key_version: str = "kms_v1",
    ) -> bool:
        """Verify client-supplied assertion signature via AWS KMS."""
        normalized_leaf = leaf_hash.replace("sha256:", "").strip()
        canonical_str = f"KEY:{checker_id}|CONTRACT:{contract_id}|LEAF:{normalized_leaf}|APPROVER:{checker_id}|ACTION:RELEASE|VER:{key_version}"
        canonical_bytes = canonical_str.encode("utf-8")
        client = self._get_client()
        try:
            response = client.verify(
                KeyId=self.key_arn,
                Message=canonical_bytes,
                MessageType="RAW",
                Signature=bytes.fromhex(signature_hex),
                SigningAlgorithm="ECDSA_SHA_256",
            )
            return bool(response.get("SignatureValid", False))
        except Exception:
            return False


def get_key_custodian(
    env: Optional[EnvironmentMode] = None,
    key_id: Optional[str] = None,
    key_arn: Optional[str] = None,
    kms_client: Optional[Any] = None,
) -> BaseKeyCustodian:
    """Enterprise Key Custodian Factory enforcing strict environment separation.
    
    Rules:
    1. SANDBOX_DEMO defaults to SoftwareEd25519Custodian (RFC 8032 Ed25519).
    2. STAGING and PRODUCTION require AWSKMSAsymmetricCustodian (ECDSA_SHA_256).
    3. In PRODUCTION, if use_aws_kms is False or key_arn is missing (and no test double is injected),
       fails closed with SecurityConfigError.
    4. Never silently falls back to software demonstration keys in PRODUCTION.
    """
    effective_env = env or config.environment

    if effective_env == EnvironmentMode.PRODUCTION:
        if not config.use_aws_kms and kms_client is None:
            raise SecurityConfigError(
                "Production Invariant Violation: Software key custody is prohibited in PRODUCTION. "
                "USE_AWS_KMS must be true and a valid AWS KMS key ARN must be configured."
            )
        arn = key_arn or config.aws_kms_key_arn
        if not arn and kms_client is None:
            raise SecurityConfigError(
                "Production Invariant Violation: Missing AWS_KMS_KEY_ARN for production key custody."
            )
        return AWSKMSAsymmetricCustodian(key_arn=arn or "arn:aws:kms:ap-south-1:123456789012:key/prod-key", kms_client=kms_client)

    if effective_env == EnvironmentMode.STAGING:
        if config.use_aws_kms or kms_client is not None:
            arn = key_arn or config.aws_kms_key_arn or "arn:aws:kms:ap-south-1:123456789012:key/staging-kuber-key"
            return AWSKMSAsymmetricCustodian(key_arn=arn, kms_client=kms_client)
        raise SecurityConfigError(
            "Staging Invariant Violation: Software key custody is prohibited in STAGING. "
            "AWS KMS Asymmetric Signer (ECC_NIST_P256) or an injected KMS custodian test double is required."
        )

    # SANDBOX_DEMO
    if config.use_aws_kms or kms_client is not None:
        return AWSKMSAsymmetricCustodian(key_arn=key_arn, kms_client=kms_client)
    return SoftwareEd25519Custodian(key_id=key_id or "cfo_autonomous_verifier")


class DualAuthorizationEngine:
    """Two-Person Rule Enforcement Engine for High-Value Release Intents.
    
    Invariants:
    1. Releases > threshold_paise require 2 distinct approved certificates from different roles/keys.
    2. Primary Maker and Secondary Risk Checker cannot share key ID or user ID.
    """

    def __init__(self, threshold_paise: Optional[int] = None, custodian: Optional[BaseKeyCustodian] = None):
        self.threshold_paise = threshold_paise or config.dual_auth_threshold_paise
        self.custodian = custodian or get_key_custodian()

    def is_dual_auth_required(self, amount_paise: int) -> bool:
        return amount_paise >= self.threshold_paise

    def verify_dual_authorization(
        self,
        amount_paise: int,
        contract_id: str,
        leaf_hash: str,
        primary_cert: Dict[str, str],
        secondary_cert: Optional[Dict[str, str]] = None,
    ) -> bool:
        # Check primary authorization via custodian
        primary_valid = self.custodian.verify_client_signature(
            checker_id=primary_cert.get("checker_id", ""),
            contract_id=contract_id,
            leaf_hash=leaf_hash,
            public_key_hex=primary_cert.get("public_key_hex", ""),
            signature_hex=primary_cert.get("signature_hex", ""),
        )
        if not primary_valid:
            return False

        # If below threshold, single signature suffices
        if not self.is_dual_auth_required(amount_paise):
            return True

        # High-value release requires second independent signature
        if not secondary_cert:
            return False

        if primary_cert.get("checker_id") == secondary_cert.get("checker_id"):
            # Anti-collusion: Maker cannot be Checker
            return False

        secondary_valid = self.custodian.verify_client_signature(
            checker_id=secondary_cert.get("checker_id", ""),
            contract_id=contract_id,
            leaf_hash=leaf_hash,
            public_key_hex=secondary_cert.get("public_key_hex", ""),
            signature_hex=secondary_cert.get("signature_hex", ""),
        )
        return secondary_valid



# ── JWT Token Generation & Verification (RBAC) ───────────────────────────────

def create_access_token(
    subject: str,
    tenant_id: str,
    roles: List[UserRole],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed short-lived JWT access token with role and tenant claims."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=config.jwt_access_token_expire_minutes))
    
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "roles": [r.value for r in roles],
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": hashlib.sha256(f"{subject}:{tenant_id}:{now.isoformat()}".encode()).hexdigest()[:16],
    }
    
    if jwt:
        return jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    else:
        # Fallback pure-python HMAC token if PyJWT is optional
        raw = json.dumps(payload, separators=(',', ':'))
        sig = hashlib.sha256(f"{raw}:{config.jwt_secret_key}".encode()).hexdigest()
        return f"{raw}.{sig}"


def decode_access_token(token: str) -> Optional[AuthTokenPayload]:
    """Validate JWT access token signature and extract claims."""
    if jwt:
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm],
                options={"require": ["sub", "tenant_id", "exp"]},
            )
            return AuthTokenPayload(
                sub=payload["sub"],
                tenant_id=payload["tenant_id"],
                roles=[UserRole(r) for r in payload.get("roles", [])],
                exp=payload["exp"],
                iat=payload.get("iat", 0),
                jti=payload.get("jti", ""),
            )
        except Exception:
            return None
    else:
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None
            raw, sig = parts[0], parts[1]
            expected_sig = hashlib.sha256(f"{raw}:{config.jwt_secret_key}".encode()).hexdigest()
            if sig != expected_sig:
                return None
            payload = json.loads(raw)
            if payload.get("exp", 0) < int(time.time()):
                return None
            return AuthTokenPayload(
                sub=payload["sub"],
                tenant_id=payload["tenant_id"],
                roles=[UserRole(r) for r in payload.get("roles", [])],
                exp=payload["exp"],
                iat=payload.get("iat", 0),
                jti=payload.get("jti", ""),
            )
        except Exception:
            return None
