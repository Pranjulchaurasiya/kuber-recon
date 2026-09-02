"""Operational Configuration & Environment Separation Architecture.

Enforces strict boundaries between:
- SANDBOX_DEMO (zero-key local development & test suite)
- STAGING (pre-production deployment with PostgreSQL, Redis, and real APIs)
- PRODUCTION (hardened operational service with KMS/HSM, Aurora Multi-AZ, and strict IAM)
"""

from enum import Enum
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class EnvironmentMode(str, Enum):
    SANDBOX_DEMO = "SANDBOX_DEMO"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class SecurityConfigError(Exception):
    """Raised when a production security invariant or configuration requirement is violated."""
    pass


class AppConfig(BaseModel):
    """Authoritative service configuration with production readiness assertions."""

    environment: EnvironmentMode = Field(
        default_factory=lambda: EnvironmentMode(
            os.getenv("KUBER_ENV", EnvironmentMode.SANDBOX_DEMO.value)
        )
    )

    # Database connection string
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{Path(__file__).parent / 'kuber_idempotency.db'}"
        )
    )

    # Redis URL for distributed locking (Redlock) and caching
    redis_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("REDIS_URL", None)
    )

    # Razorpay API Credentials
    razorpay_key_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("RAZORPAY_KEY_ID", None)
    )
    razorpay_key_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("RAZORPAY_KEY_SECRET", None)
    )
    razorpay_webhook_secret: str = Field(
        default_factory=lambda: os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_sandbox_demo_only_2026")
    )

    # Key Custody & Signing Configuration
    use_aws_kms: bool = Field(
        default_factory=lambda: os.getenv("USE_AWS_KMS", "false").lower() in ("true", "1", "yes")
    )
    aws_kms_key_arn: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_KMS_KEY_ARN", None)
    )
    aws_region: str = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "ap-south-1")
    )

    # Two-Person / Dual-Authorization Threshold (in paise: default ₹1,00,000 = 10,000,000 paise)
    dual_auth_threshold_paise: int = Field(
        default_factory=lambda: int(os.getenv("DUAL_AUTH_THRESHOLD_PAISE", "10000000"))
    )

    # JWT Authentication Configuration
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "kuber_jwt_signing_secret_dev_sandbox_2026")
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # CORS Allowed Origins
    cors_allowed_origins: List[str] = Field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv(
                "CORS_ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,https://kuber-os.vercel.app"
            ).split(",")
            if o.strip()
        ]
    )

    # Rate Limiting (Requests per minute per tenant)
    rate_limit_per_minute: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "600"))
    )

    def validate_production_readiness(self) -> None:
        """Enforces non-negotiable production boundaries.
        
        Production startup fails immediately if any local simulation primitive is active.
        """
        if self.environment in (EnvironmentMode.PRODUCTION, EnvironmentMode.STAGING):
            env_name = self.environment.value
            url_str = str(self.database_url or "")
            if "sqlite" in url_str.lower():
                raise SecurityConfigError(
                    f"{env_name} Invariant Violation: SQLite is strictly prohibited in {env_name}. "
                    "Configure a high-availability PostgreSQL / Amazon Aurora database URL (DATABASE_URL)."
                )
            if not self.database_url or not (
                url_str.startswith("postgresql") or url_str.startswith("postgres")
            ):
                raise SecurityConfigError(
                    f"{env_name} Invariant Violation: DATABASE_URL must contain a valid PostgreSQL scheme ('postgresql://' or 'postgres://'). "
                    f"SQLite and filesystem paths are strictly prohibited in {env_name}."
                )

        if self.environment == EnvironmentMode.PRODUCTION:

            # 2. Prohibit Software Key Custody in Production
            if not self.use_aws_kms or not self.aws_kms_key_arn:
                raise SecurityConfigError(
                    "Production Invariant Violation: Software demonstration key custody is prohibited in PRODUCTION. "
                    "USE_AWS_KMS must be true and AWS_KMS_KEY_ARN must be specified."
                )

            # 3. Prohibit Default / Sandbox Webhook Secrets
            if self.razorpay_webhook_secret == "whsec_sandbox_demo_only_2026":
                raise SecurityConfigError(
                    "Production Invariant Violation: Default sandbox webhook secret detected in PRODUCTION. "
                    "Set RAZORPAY_WEBHOOK_SECRET from AWS Secrets Manager."
                )

            # 4. Enforce Live Razorpay API Keys
            if not self.razorpay_key_id or not self.razorpay_key_secret:
                raise SecurityConfigError(
                    "Production Invariant Violation: Missing live Razorpay API credentials in PRODUCTION. "
                    "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are required."
                )

            # 5. Prohibit Default JWT Secret
            if "sandbox" in self.jwt_secret_key.lower() or "dev" in self.jwt_secret_key.lower():
                raise SecurityConfigError(
                    "Production Invariant Violation: Insecure JWT secret detected in PRODUCTION. "
                    "JWT_SECRET_KEY must be a cryptographically random secret provisioned via KMS/Secrets Manager."
                )


# Global Config Singleton
config = AppConfig()
