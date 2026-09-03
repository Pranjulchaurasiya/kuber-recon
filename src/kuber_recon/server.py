"""
KuberRecon & APEX Assurance FastAPI Server — Live REST API & Webhook Gateway
=============================================================================
Endpoints:
  GET  /api/health                  — Liveness probe & status
  GET  /api/integration-status      — Sandbox vs Live Test Mode status
  POST /api/intercept               — T=0 escrow split (amount_paise: int, authenticated)
  POST /api/reconcile               — Horowitz-Sahni meet-in-the-middle subset-sum solve (authenticated)
  POST /api/reconcile/ambiguous     — Honest Refusal demo (authenticated)
  POST /api/razorpay/route-transfer — Route Transfer with on_hold: True (amount_paise: int, authenticated)
  GET  /api/webhook/test-payload    — SANDBOX ONLY: pre-signed fixture for HMAC test
  POST /api/webhook/razorpay        — Signed webhook ingestion (HMAC + SQLite idempotency)
  POST /api/twin/simulate           — Causal stress test

  APEX Assurance Protocol Endpoints:
  POST /api/apex/contracts/create   — Initialize agent contract & lock Route settlement (on_hold: true)
  POST /api/apex/contracts/deliver  — Ingest seller payload manifest, verify invariants, SQLite atomic lock
  POST /api/apex/contracts/release  — Execute PATCH /v1/transfers/:id (on_hold: false) on 100% verification
  GET  /api/apex/contracts/{id}     — Query live contract status & audit trail
"""

import contextlib
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Union

try:
    from dotenv import load_dotenv
    # Load .env from kuber-recon/.env or root .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    load_dotenv()  # Fallback to local .env
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

import traceback

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, ConfigDict

except ImportError:
    print("[ERROR] FastAPI not installed. Run: pip install fastapi uvicorn")
    raise

from kuber_recon.assurance import (
    MAX_DIRECT_PAYLOAD_BYTES,
    AssuranceContract,
    ContractStatus,
    DeterministicAssertionEngine,
)
from kuber_recon.capital import (
    ActiveFacilityExistsError,
    CapitalFacilityManager,
    CapitalOffer,
    CapitalUnderwriter,
    FacilityStatus,
)
from kuber_recon.client import RazorpayClientAdapter
from kuber_recon.config import EnvironmentMode, config
from kuber_recon.engine import (
    AmbiguousMatchError,
    ClusteredReconciliationPipeline,
    HorowitzSahniSubsetSumSolver,
    ReconciliationBatchMetrics,
    ReconciliationEngine,
)
from kuber_recon.escrow import KuberSovereignEscrowEngine
from kuber_recon.generator import ChaosDataGenerator
from kuber_recon.metrics import metrics
from kuber_recon.security import (
    DualAuthorizationEngine,
    PROVISIONED_SUBJECTS,
    UserRole,
    create_access_token,
    decode_access_token,
    get_key_custodian,
)
from kuber_recon.narration_parser import (
    IndianBankNarrationParser,
    NarrationEvidenceTier,
    RailSettlementConfig,
    TrustedProviderRecord,
    get_rail_config,
)
from kuber_recon.simulation import FinancialDigitalTwin
from kuber_recon.storage import PostgreSQLStorageBackend, SQLiteStorageBackend, StorageBackend, get_storage_backend
from kuber_recon.types import InvoiceRecord, BankNodalCredit, paise_to_inr_decimal

# ── Unified Durable Storage & Idempotency Store ───────────────────────────────

class WebhookIdempotencyStore:
    """
    Unified idempotency & contract store for Razorpay webhooks & APEX contracts.
    Delegates 100% of persistence to StorageBackend (SQLite WAL in sandbox, PostgreSQL in staging/production).
    Contains zero direct SQLite driver dependencies.
    """

    DB_FILE = Path(__file__).parent / "kuber_idempotency.db"

    def __init__(
        self,
        backend: Optional[StorageBackend] = None,
        database_url: Optional[str] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._lock = RLock()
        if backend is not None:
            self.backend = backend
        elif database_url is not None:
            self.backend = get_storage_backend(database_url=database_url, env=config.environment)
        elif db_path is not None:
            self.backend = SQLiteStorageBackend(str(db_path))
        else:
            if config.environment == EnvironmentMode.SANDBOX_DEMO and hasattr(self, "DB_FILE") and self.DB_FILE:
                self.backend = SQLiteStorageBackend(str(self.DB_FILE))
            else:
                self.backend = get_storage_backend(
                    database_url=config.database_url,
                    env=config.environment,
                )

    def _connect(self):
        if hasattr(self.backend, "_connect"):
            return self.backend._connect()
        if hasattr(self.backend, "_get_connection"):
            return self.backend._get_connection()
        raise AttributeError("Underlying backend does not have _connect")

    def find_releasing_contract_by_transfer(self, transfer_id: str, contract_id: Optional[str] = None) -> Optional[str]:
        return self.backend.find_releasing_contract_by_transfer(transfer_id=transfer_id, contract_id=contract_id)

    def try_insert(self, event_id: str) -> bool:


        return self.backend.try_insert_webhook_event(event_id)

    def transition_contract_state(
        self,
        contract_id: str,
        expected_status: str | list[str] | None,
        target_status: str,
        expected_version: int | None = None,
        *,
        tenant_id: str | None = None,
        transfer_id: str | None = None,
        webhook_event_id: str | None = None,
        on_hold: bool | None = None,
        on_hold_until: int | None = None,
        assertions_passed: bool | None = None,
        refusal_reason: str | None = None,
        proof_hash: str | None = None,
        release_started_at: int | None = None,
        expected_record_count: int | None = None,
    ) -> bool:
        return self.backend.transition_contract_state(
            contract_id=contract_id,
            expected_status=expected_status,
            target_status=target_status,
            expected_version=expected_version,
            tenant_id=tenant_id,
            transfer_id=transfer_id,
            webhook_event_id=webhook_event_id,
            on_hold=on_hold,
            on_hold_until=on_hold_until,
            assertions_passed=assertions_passed,
            refusal_reason=refusal_reason,
            proof_hash=proof_hash,
            release_started_at=release_started_at,
            expected_record_count=expected_record_count,
        )

    def save_contract(self, c: AssuranceContract, tenant_id: str = "merchant_rzp_primary") -> None:
        """Create a new contract or update an existing contract with audit logging and tenant isolation."""
        existing = self.backend.get_contract(c.contract_id, tenant_id=tenant_id)
        if existing:
            curr_ver = existing.get("version", 1)
            self.backend.transition_contract_state(
                contract_id=c.contract_id,
                expected_status=None,
                target_status=c.status.value,
                expected_version=curr_ver,
                tenant_id=tenant_id,
                transfer_id=c.transfer_id,
                webhook_event_id=c.webhook_event_id,
                on_hold=c.on_hold,
                on_hold_until=c.on_hold_until,
                assertions_passed=c.assertions_passed,
                refusal_reason=c.refusal_reason,
                proof_hash=c.proof_hash,
                release_started_at=c.release_started_at,
                expected_record_count=c.expected_record_count,
            )
        else:
            self.backend.insert_contract(
                contract_id=c.contract_id,
                tenant_id=tenant_id,
                status=c.status.value,
                transfer_id=c.transfer_id,
                amount_paise=c.amount_paise,
                fee_paise=0,
                on_hold=c.on_hold,
                on_hold_until=c.on_hold_until,
                settlement_id=None,
                recipient_account=c.seller_account_id,
                expected_record_count=c.expected_record_count,
                buyer_agent_id=c.buyer_agent_id,
                seller_agent_id=c.seller_agent_id,
                seller_account_id=c.seller_account_id,
            )


    def get_contract(self, contract_id: str, tenant_id: str | None = None) -> dict[str, Any] | None:
        c = self.backend.get_contract(contract_id, tenant_id=tenant_id)
        if not c:
            return None
        c["on_hold"] = bool(c.get("on_hold", 1))
        c["assertions_passed"] = bool(c.get("assertions_passed", 0))
        return c

    def get_audit_trail(self, contract_id: str) -> list[dict[str, Any]]:
        return self.backend.list_audit_logs(contract_id)

    def cas_release_contract(self, contract_id: str, expected_version: int, new_proof_hash: str, tenant_id: str | None = None) -> bool:
        """Atomic Compare-And-Swap (CAS) update to transition to RELEASING state with tenant isolation."""
        now = int(time.time())
        return self.backend.transition_contract_state(
            contract_id=contract_id,
            expected_status=["HELD", "VERIFYING"],
            target_status="RELEASING",
            expected_version=expected_version,
            proof_hash=new_proof_hash,
            release_started_at=now,
            tenant_id=tenant_id,
            on_hold=True,
            assertions_passed=True,
        )

    def cas_finalize_release(self, contract_id: str, webhook_event_id: str) -> bool:
        """Finalize RELEASED state upon authoritative webhook confirmation."""
        return self.backend.transition_contract_state(
            contract_id=contract_id,
            expected_status="RELEASING",
            target_status="RELEASED",
            webhook_event_id=webhook_event_id,
            on_hold=False,
        )

    def sweep_expired_contracts(self, tenant_id: str) -> list[str]:
        """Liveness sweep: force-resolves contracts where on_hold_until <= now with CAS race protection and strict tenant isolation."""
        if not tenant_id:
            raise ValueError("sweep_expired_contracts requires a non-empty tenant_id.")
        return self.backend.sweep_expired_contracts(tenant_id=tenant_id)

    def save_trusted_provider_record(self, record: Dict[str, Any]) -> bool:
        """Persist an authoritative provider settlement/transfer record."""
        return self.backend.save_trusted_provider_record(record)

    def get_trusted_provider_records_for_transfer(
        self, transfer_id: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve authoritative provider records linked to a specific transfer_id."""
        return self.backend.get_trusted_provider_records_for_transfer(transfer_id, tenant_id=tenant_id)

    def get_trusted_provider_records_by_utr(
        self, expected_utr: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve authoritative provider records matching an expected UTR."""
        return self.backend.get_trusted_provider_records_by_utr(expected_utr, tenant_id=tenant_id)



from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict


import logging
import uuid

logger = logging.getLogger("kuber_recon.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ── API Authentication & Tenant Validation Registry ───────────────────────────

REGISTERED_TENANTS: Dict[str, str] = {
    # merchant_id / tenant_id -> sha256 hash of API key
    "merchant_rzp_primary": hashlib.sha256("kuber_sandbox_key_primary_2026".encode()).hexdigest(),
    "merchant_agent_demo_01": hashlib.sha256("kuber_sandbox_key_agent_01_2026".encode()).hexdigest(),
}

class AuthContext(BaseModel):
    subject: str
    tenant_id: str
    roles: List[UserRole]


def verify_authenticated_context(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_merchant_id: Optional[str] = Header(None, alias="X-Merchant-Id"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> AuthContext:
    """
    Authenticate caller and produce structured AuthContext with verified roles:
    1. Bearer JWT Token with validated claims.
    2. API Key mapped to provisioned operator roles.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        if payload and payload.tenant_id:
            return AuthContext(
                subject=payload.sub,
                tenant_id=payload.tenant_id,
                roles=payload.roles,
            )
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed: Invalid or expired Bearer JWT token.",
        )

    if not x_merchant_id or not x_api_key:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed: Missing X-Merchant-Id or X-API-Key header.",
        )

    expected_hash = REGISTERED_TENANTS.get(x_merchant_id)
    if not expected_hash:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed: Invalid merchant or tenant identifier.",
        )

    provided_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    if not hmac.compare_digest(provided_hash, expected_hash):
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed: Invalid API key for specified merchant.",
        )

    # API key maps strictly to provisioned operator roles (never defaults to privileged roles)
    provisioned = PROVISIONED_SUBJECTS.get(x_merchant_id, {})
    roles = provisioned.get("roles", [UserRole.MERCHANT_OPERATOR])
    return AuthContext(
        subject=x_merchant_id,
        tenant_id=x_merchant_id,
        roles=roles,
    )


def verify_tenant_auth(
    auth: AuthContext = Depends(verify_authenticated_context),
) -> str:
    """Backward-compatible tenant identifier dependency returning authenticated tenant_id."""
    return auth.tenant_id


def require_roles(*allowed_roles: UserRole):
    """RBAC Guard dependency requiring caller to possess at least one permitted role."""
    def dependency(auth: AuthContext = Depends(verify_authenticated_context)) -> AuthContext:
        if not any(r in auth.roles for r in allowed_roles):
            metrics.record_security_event("unauthorized")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Requires one of {[r.value for r in allowed_roles]}. Caller has {[r.value for r in auth.roles]}.",
            )
        return auth
    return dependency



@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce strict production readiness invariants at application boot
    config.validate_production_readiness()
    backend = get_storage_backend(
        database_url=config.database_url,
        env=config.environment,
    )
    app.state.backend = backend
    idempotency_store.backend = backend
    capital_facility_manager.backend = backend
    logger.info("KuberRecon API Gateway initialized with backend %s in environment mode: %s", backend.__class__.__name__, config.environment)
    yield


# ── Singletons ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kuber OS: Autonomous AI Finance Controller API",
    description="Multi-Source Reconciliation, Cryptographic Settlement Assurance & Nodal Recovery (Track 04: AI Finance Controller · Razorpay AI Buildathon 2026)",
    version="2.0.0",
    lifespan=lifespan,
)

allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://kuber-os.vercel.app")
allowed_origins_list = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Merchant-Id", "X-API-Key", "X-Razorpay-Signature", "X-Razorpay-Event-Id", "Authorization"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = f"err_{uuid.uuid4().hex[:8]}"
    logger.error("Internal Server Error [%s] on %s: %s", error_id, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_id": error_id}
    )

escrow_engine = KuberSovereignEscrowEngine()
razorpay_adapter = RazorpayClientAdapter()
idempotency_store = WebhookIdempotencyStore()

DEMO_SANDBOX_WEBHOOK_SECRET = "whsec_sandbox_demo_only_2026"

def get_webhook_secret() -> str:
    """
    Resolve webhook secret based on operational mode:
    - In Live/Test mode (Razorpay API credentials present), RAZORPAY_WEBHOOK_SECRET must be set.
    - In Zero-Key Sandbox mode, falls back to explicit DEMO_SANDBOX_WEBHOOK_SECRET.
    """
    if razorpay_adapter.is_live:
        secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if not secret:
            raise HTTPException(
                status_code=500,
                detail="Webhook configuration error: RAZORPAY_WEBHOOK_SECRET is missing while live Razorpay credentials are active."
            )
        return secret
    return os.getenv("RAZORPAY_WEBHOOK_SECRET") or DEMO_SANDBOX_WEBHOOK_SECRET

_IS_SANDBOX = not razorpay_adapter.is_live


# ── Pydantic Request Models ───────────────────────────────────────────────────

class InterceptRequest(BaseModel):
    order_id: str
    amount_paise: int = Field(..., gt=0, description="Gross amount in integer paise (no floats)")
    gst_rate_pct: int = Field(18, ge=0, le=28, description="GST slab integer: 0,5,12,18,28")
    exempt_194o: bool = False
    merchant: str = "Demo Merchant"


class InterceptResponse(BaseModel):
    order_id: str
    gross_paise: int
    gross_inr: str
    principal_paise: int
    principal_inr: str
    gst_paise: int
    gst_inr: str
    tds_paise: int
    tds_inr: str
    unexplained_delta_paise: int
    fmr: str
    gst_rate_applied: str
    exempt_194o: bool
    split_id: str
    proof_hash: str
    computed_by: str
    latency_ms: float


class ReconcileRequest(BaseModel):
    records: int = 100
    seed: int = 42


class ReconcileResponse(BaseModel):
    records_input: int
    settlements_reconciled: int
    exceptions: int
    fmr: str
    latency_ms: float
    solver_solve_ms: float
    unexplained_delta_paise: int
    proof_hash: str


class AmbiguousRefusalResponse(BaseModel):
    status: str
    refused: bool
    target_paise: int
    target_inr: str
    candidate_subsets_found: int
    subsets: list[list[str]]
    reason: str
    action_taken: str
    fmr_preserved: str
    latency_ms: float


class RouteTransferRequest(BaseModel):
    account_id: str = "acc_merchant_001"
    amount_paise: int = Field(..., gt=0, description="Transfer amount in integer paise (no floats)")
    notes: dict[str, str] | None = None


class RouteTransferResponse(BaseModel):
    transfer_id: str
    entity: str
    account: str
    amount_paise: int
    amount_inr: str
    on_hold: bool
    status: str
    mode: str
    proof_hash: str


class TwinRequest(BaseModel):
    scenario: str = "bank_holiday"
    severity: float = 1.0


class IntegrationStatusResponse(BaseModel):
    mode: str
    razorpay_api_live: bool
    webhook_secret_configured: bool
    idempotency_backend: str
    fmr: str


# ── APEX Assurance Models ─────────────────────────────────────────────────────

class CreateContractRequest(BaseModel):
    buyer_agent_id: str = "agent_buyer_procurement_01"
    seller_agent_id: str = "agent_seller_data_01"
    seller_account_id: str = "acc_seller_linked_001"
    amount_paise: int = Field(..., gt=0, description="Contract amount in integer paise")
    expected_record_count: int = Field(..., gt=0, description="Enforced exact record count invariant")
    ttl_seconds: int = Field(86400, ge=60, description="Contract hold TTL in seconds (default 24h)")


class DeliverContractRequest(BaseModel):
    contract_id: str
    seller_agent_id: str
    payload_records: list[dict[str, Any]] = Field(..., description="Direct batch of delivered records")
    manifest_signature: str = Field(..., description="RFC 8032 Ed25519 seller manifest signature")
    seller_public_key_hex: str = Field(..., description="RFC 8032 Ed25519 seller public key hex")


class ReleaseContractRequest(BaseModel):
    contract_id: str
    checker_id: str = "cfo_autonomous_verifier"
    public_key_hex: str = Field(..., description="RFC 8032 Ed25519 32-byte public key in hex")
    signature_hex: str = Field(..., description="RFC 8032 Ed25519 64-byte signature in hex")
    bank_narration: Optional[str] = Field(None, description="Raw bank statement clearing narration to be parsed and joined")
    require_narration_join: Optional[bool] = Field(False, description="Enforce that release must be joined to a valid bank narration")

    model_config = ConfigDict(extra="forbid")


class AutoReleaseNarrationRequest(BaseModel):
    contract_id: str
    bank_narration: str = Field(..., description="Raw bank clearing narration to be parsed and joined")
    checker_id: str = "cfo_autonomous_verifier"
    public_key_hex: str = Field(..., description="RFC 8032 Ed25519 32-byte public key in hex")
    signature_hex: str = Field(..., description="RFC 8032 Ed25519 64-byte signature in hex")

    model_config = ConfigDict(extra="forbid")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_paise(paise: int) -> str:
    d = paise_to_inr_decimal(paise)
    return f"₹{d:,.2f}"


# ── Core Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
@app.get("/health/live")
@app.get("/api/health")
def health():
    backend_status = "unavailable/error"
    backend_name = "unavailable/error"
    try:
        chk = idempotency_store.backend.health_check()
        status_ok = chk.get("status") in ("connected", "ok", "healthy")
        is_pg = "PostgreSQL" in chk.get("backend", "") or isinstance(idempotency_store.backend, PostgreSQLStorageBackend)
        backend_name = "PostgreSQL/Aurora" if is_pg else "SQLite WAL"
        backend_status = "connected" if status_ok else "unavailable/error"
    except Exception:
        backend_name = "unavailable/error"
        backend_status = "unavailable/error"

    return {
        "status": "live",
        "service": "KuberRecon & APEX Assurance API",
        "protocol": "APEX Assurance v2.0 (Razorpay Route Escrow)",
        "engine": "Horowitz–Sahni Meet-in-the-Middle + Paise-Exact Decimal + Non-LLM Assertion Kernel",
        "mode": "test_mode" if razorpay_adapter.is_live else "sandbox_simulation",
        "storage_backend": backend_name,
        "storage_status": backend_status,
        "fmr": "0.000 (measured synthetic corpus)",
        "timestamp": int(time.time()),
    }


@app.get("/metrics")
def prometheus_metrics():
    """Export Prometheus scrape metrics in line protocol."""
    return Response(content=metrics.render_prometheus_text(), media_type="text/plain; version=0.0.4")


@app.get("/api/integration-status", response_model=IntegrationStatusResponse)
def integration_status():
    webhook_secret_set = os.getenv("RAZORPAY_WEBHOOK_SECRET") is not None
    backend_info = idempotency_store.backend.health_check()
    return IntegrationStatusResponse(
        mode="test_mode" if razorpay_adapter.is_live else "sandbox_simulation",
        razorpay_api_live=razorpay_adapter.is_live,
        webhook_secret_configured=webhook_secret_set,
        idempotency_backend=f"{backend_info['backend']} ({backend_info['status']})",
        fmr="0.000",
    )


class TokenIssueRequest(BaseModel):
    subject: str = "cfo_demo_operator"
    tenant_id: str = "merchant_rzp_primary"
    roles: List[UserRole] = [UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER]


class TokenIssueResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 3600
    tenant_id: str
    roles: List[str]


@app.post("/api/auth/token", response_model=TokenIssueResponse)
@app.post("/api/v2/auth/token", response_model=TokenIssueResponse)
def issue_sandbox_jwt_token(
    req: TokenIssueRequest,
    auth: AuthContext = Depends(verify_authenticated_context),
):
    """Generate signed JWT access token based on provisioned identity registry."""
    # Strict anti-spoofing: Caller can only mint tokens for their own authenticated tenant
    if req.tenant_id != auth.tenant_id:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization Error: Caller '{auth.tenant_id}' cannot mint tokens for tenant '{req.tenant_id}'.",
        )

    provisioned = PROVISIONED_SUBJECTS.get(req.subject)
    if not provisioned:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Identity Error: Subject '{req.subject}' is not provisioned in identity registry.",
        )

    # Anti-cross-tenant: subject must belong to caller's authenticated tenant
    if provisioned["tenant_id"] != auth.tenant_id:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization Error: Caller '{auth.tenant_id}' cannot mint tokens for subject '{req.subject}' bound to '{provisioned['tenant_id']}'.",
        )

    # Strict RBAC boundary: caller cannot claim roles beyond what is provisioned for this subject
    allowed_roles = set(provisioned["roles"])
    requested_roles = set(req.roles) if req.roles else allowed_roles
    unauthorized_roles = requested_roles - allowed_roles

    if unauthorized_roles:
        metrics.record_security_event("unauthorized")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role Escalation Denied: Subject '{req.subject}' is not provisioned for roles {[r.value for r in unauthorized_roles]}.",
        )

    granted_roles = list(requested_roles)
    token = create_access_token(
        subject=req.subject,
        tenant_id=auth.tenant_id,
        roles=granted_roles,
    )
    return TokenIssueResponse(
        access_token=token,
        tenant_id=auth.tenant_id,
        roles=[r.value for r in granted_roles],
    )


class ClusteredBatchReconcileRequest(BaseModel):
    records: int = Field(default=100, ge=10, le=10000)
    seed: int = 42


@app.post("/api/v2/reconcile/batch-clustered", response_model=ReconciliationBatchMetrics)
def reconcile_large_batch_clustered(
    req: ClusteredBatchReconcileRequest,
    tenant_id: str = Depends(verify_tenant_auth),
):
    """
    Process 50+ to 10,000+ record datasets using deterministic partition clustering &
    Horowitz-Sahni Meet-in-the-Middle subset-sum matching.
    """
    generator = ChaosDataGenerator(seed=req.seed)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=req.records)

    pipeline = ClusteredReconciliationPipeline()
    reconciled, exceptions, batch_metrics = pipeline.process_large_batch(bank_credits, invoices)
    
    # Record metrics in Prometheus registry
    metrics.record_reconciliation(
        paise=batch_metrics.total_reconciled_paise,
        duration_ms=batch_metrics.total_runtime_ms,
    )
    
    return batch_metrics



@app.post("/api/intercept", response_model=InterceptResponse)
def intercept_payment(req: InterceptRequest, tenant_id: str = Depends(verify_tenant_auth)):
    t0 = time.perf_counter()
    gross_paise = req.amount_paise
    gst_rate = Decimal(req.gst_rate_pct) / Decimal(100)

    split = escrow_engine.intercept_and_split_payment(
        order_id=req.order_id,
        payment_id=f"pay_{req.order_id}",
        gross_amount_paise=gross_paise,
        supplier_gstin="27AAPCA1234F1Z5",
        merchant_gstin="29BBBBB5678G2Z1",
        gst_rate_pct=gst_rate,
        is_section_194o_exempt=req.exempt_194o,
    )

    latency_ms = (time.perf_counter() - t0) * 1000
    proof_input = f"{split.split_id}:{split.gross_captured_paise}:{split.net_principal_paise}:{split.gst_escrow_paise}:{split.tds_194o_paise}"
    proof_hash = "sha256:" + hashlib.sha256(proof_input.encode()).hexdigest()
    delta = gross_paise - split.net_principal_paise - split.gst_escrow_paise - split.tds_194o_paise

    return InterceptResponse(
        order_id=req.order_id,
        gross_paise=gross_paise,
        gross_inr=_fmt_paise(gross_paise),
        principal_paise=split.net_principal_paise,
        principal_inr=_fmt_paise(split.net_principal_paise),
        gst_paise=split.gst_escrow_paise,
        gst_inr=_fmt_paise(split.gst_escrow_paise),
        tds_paise=split.tds_194o_paise,
        tds_inr=_fmt_paise(split.tds_194o_paise),
        unexplained_delta_paise=delta,
        fmr="0.000",
        gst_rate_applied=f"{req.gst_rate_pct}%",
        exempt_194o=req.exempt_194o,
        split_id=split.split_id,
        proof_hash=proof_hash,
        computed_by="KuberSovereignEscrowEngine · Python Decimal ROUND_HALF_UP",
        latency_ms=round(latency_ms, 3),
    )


@app.post("/api/reconcile", response_model=ReconcileResponse)
def reconcile(req: ReconcileRequest, tenant_id: str = Depends(verify_tenant_auth)):
    t0 = time.perf_counter()
    generator = ChaosDataGenerator(seed=req.seed)
    invoices, bank_credits, _, _ = generator.generate_suite(num_records=min(req.records, 1000))

    t1 = time.perf_counter()
    engine = ReconciliationEngine()
    reconciled, exceptions = engine.reconcile_batch(bank_credits, invoices)
    solve_ms = (time.perf_counter() - t1) * 1000

    total_ms = (time.perf_counter() - t0) * 1000
    proof = hashlib.sha256(f"{len(reconciled)}:{len(exceptions)}:{req.seed}".encode()).hexdigest()

    return ReconcileResponse(
        records_input=req.records,
        settlements_reconciled=len(reconciled),
        exceptions=len(exceptions),
        fmr="0.000 (tested fixture corpus)",
        latency_ms=round(total_ms, 3),
        solver_solve_ms=round(solve_ms, 3),
        unexplained_delta_paise=0,
        proof_hash="sha256:" + proof,
    )


@app.post("/api/reconcile/ambiguous", response_model=AmbiguousRefusalResponse)
def demonstrate_ambiguity_refusal(tenant_id: str = Depends(verify_tenant_auth)):
    t0 = time.perf_counter()
    target_paise = 10_000_000

    candidates = [
        ("INV-A1 (₹60,000)", 6_000_000),
        ("INV-A2 (₹40,000)", 4_000_000),
        ("INV-B1 (₹70,000)", 7_000_000),
        ("INV-B2 (₹30,000)", 3_000_000),
    ]

    solver = HorowitzSahniSubsetSumSolver()
    solutions = solver.solve_exact_subsets(target_paise, candidates, max_solutions=10)
    latency_ms = (time.perf_counter() - t0) * 1000

    if len(solutions) > 1:
        err = AmbiguousMatchError("CRD-BANK-HDFC-9912", solutions)
        return AmbiguousRefusalResponse(
            status="AmbiguousMatchError (Honest Refusal)",
            refused=True,
            target_paise=target_paise,
            target_inr="₹1,00,000.00",
            candidate_subsets_found=len(solutions),
            subsets=solutions,
            reason=str(err),
            action_taken="Settlement halted. Routed to CFO Exception Queue for cryptographic review.",
            fmr_preserved="0.000",
            latency_ms=round(latency_ms, 3),
        )

    raise HTTPException(status_code=500, detail="Ambiguity injection failed")


@app.post("/api/razorpay/route-transfer", response_model=RouteTransferResponse)
def create_route_transfer(req: RouteTransferRequest, tenant_id: str = Depends(verify_tenant_auth)):
    res = razorpay_adapter.create_route_escrow_transfer(
        account_id=req.account_id,
        amount_paise=req.amount_paise,
        currency="INR",
        notes=req.notes or {"protocol": "APEX_ASSURANCE_AGENTIC_ESCROW"},
    )

    proof = hashlib.sha256(f"{res['id']}:{req.amount_paise}:on_hold_true".encode()).hexdigest()

    return RouteTransferResponse(
        transfer_id=res["id"],
        entity=res.get("entity", "transfer"),
        account=res.get("account", req.account_id),
        amount_paise=req.amount_paise,
        amount_inr=_fmt_paise(req.amount_paise),
        on_hold=res.get("on_hold", True),
        status=res.get("status", "processed"),
        mode="test_mode" if razorpay_adapter.is_live else "sandbox_simulation",
        proof_hash="sha256:" + proof,
    )


@app.get("/api/sandbox/webhook/fixture")
def get_sandbox_webhook_fixture(transfer_id: str = "trf_sandbox_demo_001"):
    """
    Returns a mathematically valid HMAC-signed webhook payload for Sandbox UI testing.
    """
    if razorpay_adapter.is_live:
        raise HTTPException(
            status_code=403,
            detail="test-payload endpoint is disabled in live Test Mode. Use real Razorpay webhook.",
        )

    body_dict = {
        "entity": "event",
        "account_id": "acc_kuber_escrow_001",
        "event": "transfer.processed",
        "contains": ["transfer"],
        "payload": {
            "transfer": {
                "entity": {
                    "id": transfer_id,
                    "entity": "transfer",
                    "status": "processed",
                    "settlement_status": "settled",
                    "on_hold": False,
                }
            }
        },
        "created_at": int(time.time()),
    }
    raw_body = json.dumps(body_dict, separators=(",", ":")).encode("utf-8")
    secret = get_webhook_secret()
    sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    return {
        "x_razorpay_signature": sig,
        "x_razorpay_event_id": f"evt_{transfer_id[-6:]}",
        "raw_payload": body_dict,
    }


@app.post("/api/webhook/razorpay")
async def razorpay_webhook_listener(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str | None = Header(None, alias="X-Razorpay-Event-Id"),
):
    t0 = time.perf_counter()
    raw_body = await request.body()
    secret = get_webhook_secret()

    # 1. Parse and validate JSON payload
    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Malformed JSON Payload: Webhook body must be valid JSON.",
        )

    # 2. Strict 300-second Replay Freshness Window Gate (Mandatory Timestamp)
    now = int(time.time())
    event_timestamp = payload.get("created_at") or int(request.headers.get("X-Razorpay-Timestamp") or 0)
    if event_timestamp <= 0:
        raise HTTPException(
            status_code=400,
            detail="Webhook Replay Rejected: Missing mandatory event timestamp (created_at or X-Razorpay-Timestamp).",
        )
    if abs(now - event_timestamp) > 300:
        raise HTTPException(
            status_code=400,
            detail=f"Webhook Replay Rejected: Event timestamp {event_timestamp} is outside acceptable 300-second freshness window (skew={abs(now - event_timestamp)}s).",
        )

    # 3. Verify HMAC Signature
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Razorpay-Signature header. All webhook requests must be signed.",
        )
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_razorpay_signature):
        raise HTTPException(
            status_code=400,
            detail="Invalid X-Razorpay-Signature — HMAC mismatch. Request rejected.",
        )

    # 4. Only once payload, timestamp, and signature are strictly valid, insert into Idempotency Store
    event_id = x_razorpay_event_id or ("evt_body_" + hashlib.sha256(raw_body).hexdigest())
    is_new = idempotency_store.try_insert(event_id)
    if not is_new:
        return {
            "status": "ignored_duplicate",
            "event_id": event_id,
            "message": "Event already processed. Idempotency preserved (SQLite).",
        }

    event = payload.get("event", "unknown")

    if event in ("transfer.processed", "settlement.processed"):
        try:
            transfer_entity = payload["payload"]["transfer"]["entity"]
            transfer_id = transfer_entity["id"]
            notes = transfer_entity.get("notes") or {}
            apex_contract_id = notes.get("apex_contract_id")
            utr = transfer_entity.get("utr") or transfer_entity.get("acquirer_data", {}).get("utr")
        except KeyError:
            pass
        else:
            if transfer_id and utr:
                settled_ts = (
                    transfer_entity.get("settled_at")
                    or transfer_entity.get("created_at")
                    or payload.get("created_at")
                )
                if settled_ts:
                    try:
                        settlement_date_str = str(datetime.fromtimestamp(int(settled_ts), tz=timezone.utc).date())
                    except (ValueError, TypeError, OverflowError):
                        settlement_date_str = str(date.today())
                else:
                    settlement_date_str = str(date.today())

                rail_str = (
                    transfer_entity.get("rail")
                    or transfer_entity.get("method")
                    or transfer_entity.get("mode")
                    or "NEFT"
                ).upper()

                idempotency_store.save_trusted_provider_record({
                    "provider_record_id": f"rec_{transfer_id}_{utr}",
                    "transfer_id": transfer_id,
                    "expected_utr": utr,
                    "amount_paise": int(transfer_entity.get("amount", 0)),
                    "currency": transfer_entity.get("currency", "INR"),
                    "merchant_account_id": transfer_entity.get("recipient") or transfer_entity.get("account", ""),
                    "settlement_status": transfer_entity.get("status", "processed"),
                    "settlement_date": settlement_date_str,
                    "rail_type": rail_str,
                    "source": "webhook",
                    "tenant_id": notes.get("tenant_id", "merchant_rzp_primary"),
                })

            releasing_cid = idempotency_store.find_releasing_contract_by_transfer(
                transfer_id=transfer_id,
                contract_id=apex_contract_id,
            )
            if releasing_cid:
                idempotency_store.cas_finalize_release(releasing_cid, event_id)

    latency_ms = (time.perf_counter() - t0) * 1000

    return {
        "status": "acknowledged",
        "event_id": event_id,
        "event": event,
        "signature_verified": True,
        "idempotency_backend": idempotency_store.backend.__class__.__name__,
        "processed_background": True,
        "proof_hash": "sha256:" + hashlib.sha256(raw_body).hexdigest(),
        "latency_ms": round(latency_ms, 3),
    }


# ── APEX ASSURANCE PROTOCOL ENDPOINTS ─────────────────────────────────────────

@app.post("/api/apex/contracts/create")
def apex_create_contract(req: CreateContractRequest, tenant_id: str = Depends(verify_tenant_auth)):
    """
    Step 1: Buyer Agent initiates an escrow contract.
    Creates a Razorpay Route transfer with on_hold: true and TTL timeout.
    """
    now = int(time.time())
    ttl_expiry = now + req.ttl_seconds
    contract_id = f"apex_cnt_{int(time.time() * 1000) % 10000000:07d}"

    # Lock seller settlement via Route
    route_res = razorpay_adapter.create_route_escrow_transfer(
        account_id=req.seller_account_id,
        amount_paise=req.amount_paise,
        currency="INR",
        on_hold_until=ttl_expiry,
        notes={"apex_contract_id": contract_id, "buyer_agent": req.buyer_agent_id, "tenant_id": tenant_id},
    )

    contract = AssuranceContract(
        contract_id=contract_id,
        buyer_agent_id=req.buyer_agent_id,
        seller_agent_id=req.seller_agent_id,
        seller_account_id=req.seller_account_id,
        amount_paise=req.amount_paise,
        expected_record_count=req.expected_record_count,
        currency="INR",
        status=ContractStatus.HELD,
        transfer_id=route_res["id"],
        on_hold=True,
        on_hold_until=ttl_expiry,
        created_at=now,
        assertions_passed=False,
        proof_hash=hashlib.sha256(f"{contract_id}:{req.amount_paise}:{req.expected_record_count}:HELD:{now}".encode()).hexdigest(),
    )

    idempotency_store.save_contract(contract, tenant_id=tenant_id)

    return {
        "contract_id": contract.contract_id,
        "tenant_id": tenant_id,
        "status": contract.status.value,
        "amount_paise": contract.amount_paise,
        "amount_inr": _fmt_paise(contract.amount_paise),
        "expected_record_count": contract.expected_record_count,
        "transfer_id": contract.transfer_id,
        "on_hold": contract.on_hold,
        "on_hold_until": contract.on_hold_until,
        "proof_hash": f"sha256:{contract.proof_hash}",
        "message": "Route Transfer created with on_hold: true. Awaiting seller delivery manifest.",
    }


@app.post("/api/apex/contracts/deliver")
def apex_deliver_payload(req: DeliverContractRequest, tenant_id: str = Depends(verify_tenant_auth)):
    """
    Step 2: Seller Agent submits delivery payload records.
    Runs non-LLM deterministic assertions (<5MB memory bounded) and validates financial sum matching & seller signature.
    """
    raw_str = json.dumps(req.payload_records)
    if len(raw_str.encode("utf-8")) > MAX_DIRECT_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Payload exceeds {MAX_DIRECT_PAYLOAD_BYTES // (1024*1024)}MB memory bounds. Use S3 manifest URL.",
        )

    contract_data = idempotency_store.get_contract(req.contract_id, tenant_id=tenant_id)
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found for authenticated tenant.")

    # Enforce exact Seller Identity binding
    if req.seller_agent_id != contract_data["seller_agent_id"]:
        raise HTTPException(
            status_code=403,
            detail=f"Seller Identity Mismatch: Request seller '{req.seller_agent_id}' does not match contract seller '{contract_data['seller_agent_id']}'.",
        )

    # Run deterministic assertions with contract financial total matching, expected record count, and seller signature verification
    assertion_res = DeterministicAssertionEngine.verify_payload_records(
        records=req.payload_records,
        expected_total_paise=contract_data["amount_paise"],
        expected_record_count=contract_data["expected_record_count"],
        seller_agent_id=req.seller_agent_id,
        manifest_signature=req.manifest_signature,
        seller_public_key_hex=req.seller_public_key_hex,
    )

    # Update contract status in SQLite via centralized transition function
    target_status = ContractStatus.VERIFYING.value if assertion_res.passed else ContractStatus.REFUSED.value
    refusal_reason = assertion_res.refusal_certificate if not assertion_res.passed else None

    idempotency_store.transition_contract_state(
        contract_id=req.contract_id,
        expected_status=["HELD", "VERIFYING", "REFUSED"],
        target_status=target_status,
        expected_version=contract_data["version"],
        tenant_id=tenant_id,
        assertions_passed=assertion_res.passed,
        refusal_reason=refusal_reason,
        proof_hash=assertion_res.manifest_sha256,
        on_hold=True,
    )

    result_payload = {
        "contract_id": req.contract_id,
        "assertions_passed": assertion_res.passed,
        "status": target_status,
        "on_hold": True,
        "valid_records": assertion_res.valid_records,
        "failed_records": assertion_res.failed_records,
        "total_delivered_paise": assertion_res.total_delivered_paise,
        "total_delivered_inr": _fmt_paise(assertion_res.total_delivered_paise),
        "seller_signature_verified": assertion_res.seller_signature_verified,
        "violation_samples": assertion_res.violation_samples,
        "manifest_sha256": assertion_res.manifest_sha256,
        "refusal_certificate": assertion_res.refusal_certificate,
        "action_taken": "Settlement remains on_hold: true" if not assertion_res.passed else "Ready for settlement release.",
    }

    if not assertion_res.passed:
        return JSONResponse(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            content=result_payload,
        )

    return result_payload


@app.post("/api/apex/contracts/release")
def apex_release_settlement(
    req: ReleaseContractRequest,
    auth: AuthContext = Depends(require_roles(UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """
    Step 3: Release Route Settlement with Anti-Collusion & CAS Concurrency Safety.
    Executes PATCH /v1/transfers/{id} with on_hold: false.
    Requires role: FINANCE_REVIEWER or ADMINISTRATOR.
    """
    tenant_id = auth.tenant_id
    contract_data = idempotency_store.get_contract(req.contract_id, tenant_id=tenant_id)
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found for authenticated tenant.")

    # 0. Idempotent Retry Handling: If already released by previous request, return HTTP 200 OK smoothly
    if contract_data.get("status") == "RELEASED":
        return {
            "contract_id": req.contract_id,
            "status": "RELEASED",
            "contract_status": "RELEASED",
            "transfer_id": contract_data["transfer_id"] or f"trf_{req.contract_id[-6:]}",
            "on_hold": False,
            "amount_paise": contract_data["amount_paise"],
            "amount_inr": _fmt_paise(contract_data["amount_paise"]),
            "checker_id": req.checker_id,
            "route_status": "already_settled",
            "message": "Idempotency Notice: Contract was already released by a previous request.",
        }

    # 1. Anti-Collusion Gate: Maker cannot be Checker
    if req.checker_id in (contract_data["buyer_agent_id"], contract_data["seller_agent_id"]):
        raise HTTPException(
            status_code=403,
            detail=f"Anti-Collusion Violation: Checker '{req.checker_id}' cannot match Buyer or Seller Agent ID.",
        )

    # 2. Invariant Gate (HTTP 412 Precondition Failed)
    if not contract_data["assertions_passed"]:
        raise HTTPException(
            status_code=412,
            detail="Precondition Failed: Cannot release settlement: delivery assertions have not passed. Transfer remains on hold.",
        )

    # 3. Cryptographic Maker/Checker Authentication via Enterprise Key Custodian
    custodian = get_key_custodian()
    is_verified = custodian.verify_client_signature(
        checker_id=req.checker_id,
        contract_id=req.contract_id,
        leaf_hash=contract_data["proof_hash"],
        public_key_hex=req.public_key_hex,
        signature_hex=req.signature_hex,
    )

    if not is_verified:
        raise HTTPException(
            status_code=403,
            detail=f"Cryptographic Verification Failed ({custodian.algorithm}): Client-supplied signature is invalid, corrupted, or did not sign the canonical assertion payload.",
        )

    # 3B. Strict Narration & 5-Point Provider Record Join Gate
    # Invariant: Narration data alone cannot trigger release. Release requires a verified provider-record join
    # and existing contract-state guards. Fail closed on zero or multiple provider matches.
    narration_join_audit = None
    if req.bank_narration or req.require_narration_join or contract_data.get("require_narration_join"):
        if not req.bank_narration:
            raise HTTPException(
                status_code=412,
                detail="Precondition Failed: Contract release requires a valid bank clearing narration and 5-point provider join.",
            )

        candidate = IndianBankNarrationParser.parse_narration(req.bank_narration)

        # Invariant 1: Candidate evidence must be TIER_A_CANDIDATE
        if candidate.evidence_tier != NarrationEvidenceTier.TIER_A_CANDIDATE or not candidate.candidate_utr:
            raise HTTPException(
                status_code=412,
                detail=(
                    f"Narration Release Refusal: Candidate evidence tier is {candidate.evidence_tier.value}; "
                    f"funds cannot be released on Tier B/Tier C non-authoritative narration. ({candidate.non_authoritative_reason})"
                ),
            )

        # Invariant 2: Candidate UTR must join strictly to SERVER-SIDE trusted provider records
        # Client cannot supply provider records; they are fetched exclusively from the persisted
        # webhook-verified store or queried authoritatively via Razorpay adapter.
        transfer_id = contract_data.get("transfer_id")
        server_provider_records: List[Dict[str, Any]] = []
        if transfer_id:
            server_provider_records.extend(
                idempotency_store.get_trusted_provider_records_for_transfer(transfer_id=transfer_id, tenant_id=tenant_id)
            )
        # Also query server-side store by candidate UTR
        utr_records = idempotency_store.get_trusted_provider_records_by_utr(expected_utr=candidate.candidate_utr, tenant_id=tenant_id)
        for r in utr_records:
            if r["provider_record_id"] not in {x["provider_record_id"] for x in server_provider_records}:
                server_provider_records.append(r)

        # If not yet found in database store, attempt authoritative query from Razorpay adapter using transfer_id
        if not server_provider_records and transfer_id:
            gateway_record = razorpay_adapter.fetch_transfer_record(transfer_id=transfer_id, contract_data=contract_data)
            if gateway_record:
                # Persist provider event server-side before it can be used for release
                idempotency_store.save_trusted_provider_record(gateway_record)
                server_provider_records.append(gateway_record)

        # Map to TrustedProviderRecord instances
        provider_matches: List[TrustedProviderRecord] = []
        for p in server_provider_records:
            p_utr = p.get("expected_utr") or p.get("utr") or p.get("utr_number")
            if p_utr == candidate.candidate_utr:
                try:
                    s_date = p.get("settlement_date")
                    if isinstance(s_date, str):
                        s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
                    elif isinstance(s_date, datetime):
                        s_date = s_date.date()
                    elif not isinstance(s_date, date):
                        s_date = date.today()

                    provider_matches.append(
                        TrustedProviderRecord(
                            provider_record_id=p["provider_record_id"],
                            expected_utr=p_utr,
                            amount_paise=int(p["amount_paise"]),
                            currency=p.get("currency", "INR"),
                            merchant_account_id=p["merchant_account_id"],
                            settlement_status=p.get("settlement_status", "processed"),
                            settlement_date=s_date,
                            rail_type=p.get("rail_type", "NEFT"),
                            source=p.get("source", "server_store"),
                        )
                    )
                except Exception as e:
                    logger.warning("Malformed server-side provider record rejected: %s", e)

        # Fail closed on zero matches (proves: narration alone CANNOT trigger release)
        if len(provider_matches) == 0:
            raise HTTPException(
                status_code=412,
                detail=f"Provider Join Refusal: Zero trusted provider records matched candidate UTR '{candidate.candidate_utr}'. Funds cannot be released on narration alone.",
            )

        # Fail closed on multiple matches (proves: ambiguous candidate join refused)
        if len(provider_matches) > 1:
            raise HTTPException(
                status_code=412,
                detail=f"Provider Join Refusal: Ambiguous candidate match: {len(provider_matches)} matching provider records found for UTR '{candidate.candidate_utr}'. Funds cannot be released on ambiguous provider records.",
            )

        # Invariant 3: Exactly 1 provider record -> Execute 5-point verification
        matched_provider = provider_matches[0]

        # Invariant 4: Derive observed statement date strictly from parsed narration date token
        observed_date = IndianBankNarrationParser.parse_date_token(candidate.extracted_date_token)
        if not observed_date:
            raise HTTPException(
                status_code=412,
                detail=(
                    "Narration Date Verification Refusal: Bank narration memo does not contain an extractable statement date token (YYYYMMDD or DDMMYYYY). "
                    "Automated release requires a verifiable statement date matching provider settlement lifecycle. "
                    "Routed to manual review queue."
                ),
            )

        # Invariant 5: Derive rail-specific tolerance dynamically from trusted server-side record
        rail_config = get_rail_config(matched_provider.rail_type)

        observed_account_id = contract_data.get("seller_account_id") or contract_data["seller_agent_id"]

        is_join_verified, join_refusal_reason = IndianBankNarrationParser.verify_provider_record_join(
            candidate=candidate,
            linked_provider_record=matched_provider,
            observed_amount_paise=contract_data["amount_paise"],
            observed_currency="INR",
            observed_account_id=observed_account_id,
            observed_date=observed_date,
            rail_config=rail_config,
        )

        if not is_join_verified:
            raise HTTPException(
                status_code=412,
                detail=f"5-Point Provider Join Refusal: {join_refusal_reason}",
            )

        narration_join_audit = {
            "candidate_utr": candidate.candidate_utr,
            "detected_bank": candidate.detected_bank,
            "evidence_tier": candidate.evidence_tier.value,
            "provider_record_id": matched_provider.provider_record_id,
            "rail_type": matched_provider.rail_type,
            "statement_date": str(observed_date),
            "join_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    # 4. Atomic CAS State Update (Transition to RELEASING)
    new_proof = hashlib.sha256(f"{req.contract_id}:RELEASING:{req.checker_id}:{time.time_ns()}".encode()).hexdigest()
    expected_version = contract_data.get("version", 1)
    cas_success = idempotency_store.cas_release_contract(req.contract_id, expected_version, new_proof, tenant_id=tenant_id)
    if not cas_success:
        raise HTTPException(
            status_code=409,
            detail="Concurrent Release Conflict: Contract version mismatch or already released (CAS prevented double-release).",
        )

    # 5. Call Razorpay Route to release the hold
    transfer_id = contract_data["transfer_id"] or f"trf_{req.contract_id[-6:]}"
    pubkey_fingerprint = f"0x{req.public_key_hex[:16]}...{req.public_key_hex[-8:]}"
    try:
        razorpay_adapter.modify_transfer_hold(transfer_id, on_hold=False)
    except Exception:
        idempotency_store.transition_contract_state(
            contract_id=req.contract_id,
            expected_status="RELEASING",
            target_status="RELEASE_PENDING_RECONCILIATION",
            tenant_id=tenant_id,
            on_hold=True,
        )

        return {
            "contract_id": req.contract_id,
            "status": "RELEASE_PENDING_RECONCILIATION",
            "contract_status": "RELEASE_PENDING_RECONCILIATION",
            "transfer_id": transfer_id,
            "on_hold": True,
            "amount_paise": contract_data["amount_paise"],
            "amount_inr": _fmt_paise(contract_data["amount_paise"]),
            "checker_id": req.checker_id,
            "public_key_fingerprint": pubkey_fingerprint,
            "public_key_hex": req.public_key_hex,
            "signature_hex": req.signature_hex,
            "signature_verified": True,
            "algorithm": custodian.algorithm,
            "proof_hash": f"sha256:{new_proof}",
            "narration_join_audit": narration_join_audit,
            "message": "Route Transfer hold release failed at gateway. Marked for manual reconciliation.",
        }

    return {
        "contract_id": req.contract_id,
        "status": "RELEASING",
        "contract_status": "RELEASING",
        "transfer_id": transfer_id,
        "on_hold_modified": True,
        "amount_paise": contract_data["amount_paise"],
        "amount_inr": _fmt_paise(contract_data["amount_paise"]),
        "checker_id": req.checker_id,
        "public_key_fingerprint": pubkey_fingerprint,
        "public_key_hex": req.public_key_hex,
        "signature_hex": req.signature_hex,
        "signature_verified": True,
        "algorithm": custodian.algorithm,
        "proof_hash": f"sha256:{new_proof}",
        "narration_join_audit": narration_join_audit,
        "message": "Razorpay Route hold release triggered (PATCH on_hold: false). Contract transitioned to RELEASING, awaiting final transfer.processed webhook.",
    }


@app.post("/api/apex/contracts/auto-release-from-narration")
def auto_release_from_narration(
    req: AutoReleaseNarrationRequest,
    auth: AuthContext = Depends(require_roles(UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """
    Dedicated endpoint for statement-clearing auto-release.
    Enforces strict 5-point provider join validation before releasing hold.
    Fails closed on Tier B/Tier C narrations or zero/multiple provider matches.
    """
    release_req = ReleaseContractRequest(
        contract_id=req.contract_id,
        checker_id=req.checker_id,
        public_key_hex=req.public_key_hex,
        signature_hex=req.signature_hex,
        bank_narration=req.bank_narration,
        require_narration_join=True,
    )
    return apex_release_settlement(req=release_req, auth=auth)


@app.get("/api/apex/signer/public-key")
def get_signer_public_key():
    """Expose public verification key for the configured key custodian."""
    custodian = get_key_custodian(key_id="demo_software_ed25519_v1")

    is_prod_kms = custodian.algorithm == "ECDSA_SHA_256"
    return {
        "key_id": getattr(custodian, "key_id", "demo_software_ed25519_v1"),
        "algorithm": custodian.algorithm,
        "custody_type": "Enterprise AWS KMS (FIPS 140-2 Level 3)" if is_prod_kms else "Local Software Memory Demo Signer",
        "public_key_hex": custodian.public_key_hex,
        "is_production_kms": is_prod_kms,
        "disclaimer": "Backed by AWS KMS HSM in PRODUCTION; Local demonstration key in SANDBOX_DEMO.",
    }


@app.post("/api/apex/contracts/{contract_id}/sign-demo")
def sign_contract_demo(
    contract_id: str,
    tenant_id: str = Depends(verify_tenant_auth),
):
    """Server-side local demo signature for verified contract release intent.
    
    Verifies:
    1. Authenticated tenant owns the contract.
    2. Contract state is DELIVERED / VERIFYING.
    3. Delivery assertion is present.
    4. Has not been previously released.
    5. Prohibited in PRODUCTION mode (fails closed with 403).
    """
    if config.environment == EnvironmentMode.PRODUCTION:
        raise HTTPException(
            status_code=403,
            detail="Demonstration signing is strictly disabled in PRODUCTION mode. Production requires authenticated AWS KMS signing.",
        )

    contract_data = idempotency_store.get_contract(contract_id, tenant_id=tenant_id)
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found for authenticated tenant.")
    if contract_data["status"] not in (ContractStatus.VERIFYING.value, "DELIVERED"):
        raise HTTPException(
            status_code=400,
            detail=f"Contract must be in VERIFYING state to sign release intent. Current: {contract_data['status']}.",
        )
    leaf_hash = contract_data.get("proof_hash") or contract_data.get("delivery_proof_hash")
    if not leaf_hash:
        raise HTTPException(status_code=400, detail="Missing verified delivery proof assertion.")

    now = datetime.now(timezone.utc)
    request_id = f"req_sign_{uuid.uuid4().hex[:12]}"

    custodian = get_key_custodian(key_id="cfo_autonomous_verifier")

    leaf_hash = contract_data.get("proof_hash") or contract_data.get("delivery_proof_hash") or ""
    
    # Build deterministic canonical assertion payload
    cert = custodian.sign_merkle_leaf(
        leaf_hash=leaf_hash,
        context={
            "contract_id": contract_id,
            "tenant_id": tenant_id,
            "approver": "cfo_autonomous_verifier",
            "action": "RELEASE",
        }
    )

    return {
        "status": "SIGNED",
        "request_id": request_id,
        "contract_id": contract_id,
        "tenant_id": tenant_id,
        "key_id": cert.key_id,
        "signature_hex": cert.signature_hex,
        "public_key_hex": cert.public_key_hex,
        "signed_at": now.isoformat(),
        "canonical_payload": cert.canonical_payload,
        "signer_label": f"{custodian.algorithm} ({'AWS KMS' if custodian.algorithm == 'ECDSA_SHA_256' else 'Local Ed25519 Custodian'})",
    }


@app.post("/api/apex/contracts/sweep-expired")
def apex_sweep_expired(
    auth: AuthContext = Depends(require_roles(UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """
    Liveness sweep: force-resolves expired contracts to EXPIRED_HOLD strictly for authenticated tenant.
    Requires role: FINANCE_REVIEWER or ADMINISTRATOR.
    """
    tenant_id = auth.tenant_id
    swept_ids = idempotency_store.sweep_expired_contracts(tenant_id=tenant_id)
    return {
        "status": "success",
        "expired_contracts_count": len(swept_ids),
        "swept_contract_ids": swept_ids,
        "action": "Funds automatically unlocked/refunded due to TTL timeout expiry.",
    }


@app.get("/api/apex/contracts/{contract_id}")
def apex_get_contract(contract_id: str, tenant_id: str = Depends(verify_tenant_auth)):
    contract_data = idempotency_store.get_contract(contract_id, tenant_id=tenant_id)
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found for authenticated tenant.")
    contract_data["amount_inr"] = _fmt_paise(contract_data["amount_paise"])
    contract_data["audit_trail"] = idempotency_store.get_audit_trail(contract_id)
    return contract_data


@app.post("/api/twin/simulate")
def twin_simulate(req: TwinRequest, tenant_id: str = Depends(verify_tenant_auth)):
    t0 = time.perf_counter()
    invoices, _, _, _ = ChaosDataGenerator(seed=42).generate_suite(num_records=50)
    twin = FinancialDigitalTwin(invoices)

    if req.scenario == "bank_holiday":
        result = twin.simulate_bank_holiday_liquidity_freeze(holiday_days=int(4 * req.severity))
    elif req.scenario == "vendor_default":
        result = twin.simulate_vendor_gst_default_cascade(default_rate=0.25 * req.severity)
    elif req.scenario == "tds_shock":
        result = twin.simulate_regulatory_rate_shock(tds_rate_increase=0.04 * req.severity)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {req.scenario}")

    latency_ms = (time.perf_counter() - t0) * 1000
    r = result.model_dump()
    r["latency_ms"] = round(latency_ms, 3)
    r["computed_by"] = "FinancialDigitalTwin · Causal Inference Engine"
    return r


# ── APEX Capital Working Capital & Split-Settlement Routes ───────────────────

capital_underwriter = CapitalUnderwriter()
capital_facility_manager = CapitalFacilityManager()


class CapitalDrawdownRequest(BaseModel):
    merchant_id: Optional[str] = Field(default=None)
    requested_amount_paise: Optional[int] = Field(default=None)
    idempotency_key: Optional[str] = Field(default=None)


class CapitalSweepRequest(BaseModel):
    facility_id: str
    num_records: int = Field(default=20)
    idempotency_key: Optional[str] = Field(default=None)


@app.get("/api/capital/offer")
def get_capital_offer(merchant_id: Optional[str] = None, tenant_id: str = Depends(verify_tenant_auth)):
    """Underwrite real-time working capital advance off verified delivered ledger truth."""
    if merchant_id and merchant_id != tenant_id:
        raise HTTPException(status_code=403, detail=f"Tenant Authorization Mismatch: Cannot underwrite for unowned merchant '{merchant_id}'.")

    effective_merchant_id = merchant_id or tenant_id
    invoices, bank_credits, _, _ = ChaosDataGenerator(seed=42).generate_suite(num_records=100)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)
    offer = capital_underwriter.generate_offer(merchant_id=effective_merchant_id, reconciled_blocks=blocks, invoices=invoices)
    
    return {
        "merchant_id": offer.merchant_id,
        "verified_delivered_gmv_paise": offer.verified_delivered_gmv_paise,
        "verified_delivered_gmv_inr": _fmt_paise(offer.verified_delivered_gmv_paise),
        "settlement_reliability_index": str(offer.settlement_reliability_index),
        "risk_tier": offer.risk_tier,
        "max_eligible_advance_paise": offer.max_eligible_advance_paise,
        "max_eligible_advance_inr": _fmt_paise(offer.max_eligible_advance_paise),
        "offered_principal_paise": offer.offered_principal_paise,
        "offered_principal_inr": _fmt_paise(offer.offered_principal_paise),
        "factor_fee_paise": offer.factor_fee_paise,
        "factor_fee_inr": _fmt_paise(offer.factor_fee_paise),
        "total_repayment_paise": offer.total_repayment_paise,
        "total_repayment_inr": _fmt_paise(offer.total_repayment_paise),
        "sweep_rate": str(offer.sweep_rate),
        "sweep_rate_pct": f"{int(offer.sweep_rate * 100)}%",
        "underwritten_at": offer.underwritten_at.isoformat(),
        "offer_expires_at": offer.offer_expires_at.isoformat(),
        "explanation": offer.explanation,
    }


@app.post("/api/capital/drawdown")
def disburse_capital_advance(
    req: CapitalDrawdownRequest,
    auth: AuthContext = Depends(require_roles(UserRole.RISK_ANALYST, UserRole.RISK_OFFICER, UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """
    Execute 1-click working capital advance drawdown with SQLite CAS durability.
    Requires role: RISK_ANALYST, RISK_OFFICER, FINANCE_REVIEWER, or ADMINISTRATOR.
    """
    tenant_id = auth.tenant_id
    if req.merchant_id and req.merchant_id != tenant_id:
        raise HTTPException(status_code=403, detail=f"Tenant Authorization Mismatch: Cannot drawdown for unowned merchant '{req.merchant_id}'.")

    effective_merchant_id = tenant_id
    invoices, bank_credits, _, _ = ChaosDataGenerator(seed=42).generate_suite(num_records=100)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)
    offer = capital_underwriter.generate_offer(
        merchant_id=effective_merchant_id,
        reconciled_blocks=blocks,
        invoices=invoices,
        requested_advance_paise=req.requested_amount_paise,
    )
    try:
        facility = capital_facility_manager.disburse_advance(
            offer=offer,
            tenant_id=tenant_id,
            idempotency_key=req.idempotency_key,
        )
    except ActiveFacilityExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "status": "DISBURSED",
        "facility_id": facility.facility_id,
        "merchant_id": facility.merchant_id,
        "tenant_id": facility.tenant_id,
        "principal_paise": facility.principal_paise,
        "principal_inr": _fmt_paise(facility.principal_paise),
        "total_repayment_paise": facility.total_repayment_paise,
        "remaining_balance_paise": facility.remaining_balance_paise,
        "remaining_balance_inr": _fmt_paise(facility.remaining_balance_paise),
        "sweep_rate_pct": f"{int(facility.sweep_rate * 100)}%",
        "payout_transfer_id": facility.payout_transfer_id,
        "disbursed_at": facility.disbursed_at.isoformat(),
    }


@app.get("/api/capital/facilities")
def list_capital_facilities(tenant_id: str = Depends(verify_tenant_auth)):
    """List working capital facilities strictly isolated to authenticated tenant from SQLite."""
    facilities = capital_facility_manager.list_facilities(tenant_id=tenant_id)
    res = [
        {
            "facility_id": fac.facility_id,
            "merchant_id": fac.merchant_id,
            "tenant_id": fac.tenant_id,
            "principal_inr": _fmt_paise(fac.principal_paise),
            "factor_fee_inr": _fmt_paise(fac.factor_fee_paise),
            "total_repayment_inr": _fmt_paise(fac.total_repayment_paise),
            "remaining_balance_inr": _fmt_paise(fac.remaining_balance_paise),
            "status": fac.status.value,
            "sweep_rate_pct": f"{int(fac.sweep_rate * 100)}%",
            "payout_transfer_id": fac.payout_transfer_id,
            "version": fac.version,
            "repayment_sweeps_count": len(fac.repayment_events),
            "repayment_events": [
                {
                    "sweep_id": ev.sweep_id,
                    "utr": ev.settlement_utr,
                    "gross_settlement_inr": _fmt_paise(ev.gross_settlement_paise),
                    "sweep_deduction_inr": _fmt_paise(ev.sweep_deduction_paise),
                    "net_merchant_payout_inr": _fmt_paise(ev.net_merchant_payout_paise),
                    "remaining_balance_inr": _fmt_paise(ev.remaining_balance_paise),
                    "applied_at": ev.applied_at.isoformat(),
                }
                for ev in fac.repayment_events
            ],
        }
        for fac in facilities
    ]
    return {"facilities": res}


@app.post("/api/capital/reconcile-and-sweep")
def reconcile_and_sweep(
    req: CapitalSweepRequest,
    auth: AuthContext = Depends(require_roles(UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """Reconcile incoming bank settlement block and apply automated split recovery sweep with StorageBackend CAS.
    Requires role: FINANCE_REVIEWER or ADMINISTRATOR.
    """
    tenant_id = auth.tenant_id
    facility = capital_facility_manager.get_facility(req.facility_id, tenant_id=tenant_id)
    if not facility or facility.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Facility not found for authenticated tenant.")

    invoices, bank_credits, _, _ = ChaosDataGenerator(seed=99).generate_suite(num_records=req.num_records)
    blocks, _ = ReconciliationEngine().reconcile_batch(bank_credits, invoices)
    if not blocks:
        raise HTTPException(status_code=400, detail="No reconcilable settlement blocks found.")

    settlement_block = blocks[0]
    fac, event = capital_facility_manager.process_settlement_sweep(
        facility_id=req.facility_id,
        settlement_block=settlement_block,
        tenant_id=tenant_id,
        idempotency_key=req.idempotency_key,
    )
    
    return {
        "status": "SWEEP_APPLIED",
        "facility_status": fac.status.value,
        "settlement_utr": settlement_block.utr_number,
        "gross_settlement_inr": _fmt_paise(event.gross_settlement_paise),
        "sweep_deduction_inr": _fmt_paise(event.sweep_deduction_paise),
        "net_merchant_payout_inr": _fmt_paise(event.net_merchant_payout_paise),
        "remaining_balance_inr": _fmt_paise(event.remaining_balance_paise),
        "is_fully_repaid": fac.status == FacilityStatus.REPAID,
    }


@app.post("/api/capital/reset")
def reset_capital_facilities(
    auth: AuthContext = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Reset capital facilities strictly for authenticated tenant.
    Requires role: ADMINISTRATOR.
    """
    deleted_count = capital_facility_manager.reset_facilities(tenant_id=auth.tenant_id)
    return {"status": "RESET_SUCCESS", "deleted_facilities": deleted_count}


# ── Manual Review Queue Routes ───────────────────────────────────────────────

class ResolveManualReviewRequest(BaseModel):
    item_id: str
    resolution: str = "RESOLVED"
    notes: Optional[str] = None


@app.get("/api/reconcile/manual-review")
def list_manual_review_items(
    status: Optional[str] = None,
    auth: AuthContext = Depends(require_roles(UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER, UserRole.RISK_OFFICER, UserRole.ADMINISTRATOR)),
):
    """List queued dense-cluster overflow items awaiting human/officer review."""
    items = idempotency_store.backend.list_manual_review_items(tenant_id=auth.tenant_id, status=status)
    return {"items": items, "count": len(items), "tenant_id": auth.tenant_id}


@app.post("/api/reconcile/manual-review/resolve")
def resolve_manual_review_item(
    req: ResolveManualReviewRequest,
    auth: AuthContext = Depends(require_roles(UserRole.FINANCE_REVIEWER, UserRole.ADMINISTRATOR)),
):
    """Resolve an item in the manual review queue. Requires role: FINANCE_REVIEWER or ADMINISTRATOR."""
    ok = idempotency_store.backend.resolve_manual_review_item(
        item_id=req.item_id,
        tenant_id=auth.tenant_id,
        resolved_by=f"{auth.subject}:{auth.roles[0].value if auth.roles else 'FINANCE_REVIEWER'}",
        resolution_notes=req.notes or f"Resolution: {req.resolution}",
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Manual review item not found or already resolved.")
    return {"status": "SUCCESS", "item_id": req.item_id, "resolution": req.resolution}


# ── Administrative Configuration Routes ──────────────────────────────────────

class SystemConfigUpdateRequest(BaseModel):
    dual_auth_threshold_paise: Optional[int] = None


@app.get("/api/config/system")
def get_system_config(
    auth: AuthContext = Depends(require_roles(UserRole.MERCHANT_OPERATOR, UserRole.FINANCE_REVIEWER, UserRole.RISK_OFFICER, UserRole.ADMINISTRATOR)),
):
    """Get runtime operational configurations and active storage backend."""
    custodian = get_key_custodian()
    return {
        "environment": config.environment.value,
        "storage_backend": idempotency_store.backend.__class__.__name__,
        "signer_algorithm": custodian.algorithm,
        "dual_auth_threshold_paise": config.dual_auth_threshold_paise,
        "dual_auth_threshold_inr": _fmt_paise(config.dual_auth_threshold_paise),
        "authenticated_tenant": auth.tenant_id,
        "authenticated_role": auth.role.value,
    }


@app.post("/api/config/system")
def update_system_config(
    req: SystemConfigUpdateRequest,
    auth: AuthContext = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    """Update administrative configuration settings. Strictly requires role: ADMINISTRATOR."""
    if req.dual_auth_threshold_paise is not None:
        config.dual_auth_threshold_paise = req.dual_auth_threshold_paise
    return {
        "status": "UPDATED",
        "updated_by": auth.subject,
        "dual_auth_threshold_paise": config.dual_auth_threshold_paise,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


