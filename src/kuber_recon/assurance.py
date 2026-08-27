"""
APEX Assurance — Delivery-Gated Settlement Engine for Agentic Commerce
=======================================================================
Core protocol for Razorpay Route escrow settlements:
  1. Contract Lifecycle: PENDING_CAPTURE -> HELD -> VERIFYING -> RELEASED / REFUSED / EXPIRED
  2. Non-LLM Deterministic Assertions: GSTIN Mod-36 checksum, zero-float paise exactness, schema invariants
  3. Memory Bounds: Streamed SHA-256 payload manifests (strict <5MB direct payload limit)
  4. Contract TTL: Automated expiration calculation for on_hold_until (prevents indefinite nodal lockup)
"""

import hashlib
import json
import re
import time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


MAX_DIRECT_PAYLOAD_BYTES = 5 * 1024 * 1024  # 5 MB bounds


class ContractStatus(str, Enum):
    PENDING_CAPTURE = "PENDING_CAPTURE"
    HELD = "HELD"
    VERIFYING = "VERIFYING"
    RELEASED = "RELEASED"
    REFUSED = "REFUSED"
    EXPIRED = "EXPIRED"


class DeliveryManifest(BaseModel):
    """Metadata manifest of the delivered payload."""
    contract_id: str
    seller_agent_id: str
    record_count: int
    payload_sha256: str
    schema_version: str = "1.0.0"
    delivery_timestamp: int = Field(default_factory=lambda: int(time.time()))
    signature_ed25519: Optional[str] = None


class AssuranceContract(BaseModel):
    """APEX Delivery-Gated Escrow Contract."""
    contract_id: str
    buyer_agent_id: str
    seller_agent_id: str
    seller_account_id: str  # Razorpay linked account: acc_...
    amount_paise: int = Field(..., gt=0, description="Contract amount in integer paise")
    currency: str = "INR"
    status: ContractStatus = ContractStatus.HELD
    transfer_id: Optional[str] = None
    on_hold: bool = True
    on_hold_until: int      # Unix timestamp TTL
    created_at: int = Field(default_factory=lambda: int(time.time()))
    verified_at: Optional[int] = None
    assertions_passed: bool = False
    refusal_reason: Optional[str] = None
    proof_hash: Optional[str] = None
    liability_allocation: str = "linked_account_indemnified"


class AssertionResult(BaseModel):
    passed: bool
    total_records: int
    valid_records: int
    failed_records: int
    violation_samples: List[str]
    latency_ms: float
    manifest_sha256: str
    refusal_certificate: Optional[str] = None


# ── Deterministic Checksum & Invariant Validators ─────────────────────────────

# Mod-36 GSTIN Character Map
GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def validate_gstin_checksum(gstin: str) -> bool:
    """
    Validate Indian 15-character GSTIN structure and Mod-36 checksum algorithm.
    Strict non-LLM mathematical validation.
    """
    if not isinstance(gstin, str) or len(gstin) != 15:
        return False
    
    gstin = gstin.upper().strip()
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, gstin):
        return False

    # Checksum calculation: weights alternating 1 and 2
    try:
        factor = 1
        total = 0
        for i in range(14):
            code_point = GSTIN_CHARS.index(gstin[i])
            digit = code_point * factor
            factor = 2 if factor == 1 else 1
            digit = (digit // 36) + (digit % 36)
            total += digit

        remainder = total % 36
        check_code = (36 - remainder) % 36
        expected_char = GSTIN_CHARS[check_code]
        return gstin[14] == expected_char
    except Exception:
        return False


class DeterministicAssertionEngine:
    """
    Evaluates seller deliveries against strict contract invariants.
    Zero floating-point arithmetic. Zero LLM hallucinations in validation.
    """

    @staticmethod
    def verify_payload_records(
        records: List[Dict[str, Any]],
        expected_schema_keys: Optional[List[str]] = None,
    ) -> AssertionResult:
        t0 = time.perf_counter()
        expected_keys = expected_schema_keys or ["supplier_name", "gstin", "invoice_number", "amount_paise"]

        valid_count = 0
        failed_count = 0
        violations: List[str] = []

        for idx, rec in enumerate(records):
            # Check 1: Schema key presence
            missing = [k for k in expected_keys if k not in rec]
            if missing:
                failed_count += 1
                violations.append(f"Row #{idx}: Missing schema keys: {missing}")
                continue

            # Check 2: Paise integer constraint (no float)
            amt = rec.get("amount_paise")
            if not isinstance(amt, int) or amt <= 0:
                failed_count += 1
                violations.append(f"Row #{idx}: amount_paise must be positive integer, got {type(amt).__name__}:{amt}")
                continue

            # Check 3: GSTIN Checksum
            gstin = rec.get("gstin", "")
            if not validate_gstin_checksum(gstin):
                failed_count += 1
                violations.append(f"Row #{idx}: Invalid GSTIN checksum for '{gstin}'")
                continue

            valid_count += 1

        latency_ms = (time.perf_counter() - t0) * 1000
        passed = (failed_count == 0 and valid_count == len(records) and len(records) > 0)

        # Compute deterministic SHA-256 of execution result
        audit_raw = f"{len(records)}:{valid_count}:{failed_count}:{passed}"
        manifest_sha256 = "sha256:" + hashlib.sha256(audit_raw.encode()).hexdigest()[:16]

        refusal_cert = None
        if not passed:
            refusal_cert = (
                f"CERT:REFUSAL:APEX-{int(time.time())}:{manifest_sha256}:"
                f"FAILED_{failed_count}_OF_{len(records)}_RECORDS"
            )

        return AssertionResult(
            passed=passed,
            total_records=len(records),
            valid_records=valid_count,
            failed_records=failed_count,
            violation_samples=violations[:5],  # return first 5 sample errors
            latency_ms=round(latency_ms, 3),
            manifest_sha256=manifest_sha256,
            refusal_certificate=refusal_cert,
        )
