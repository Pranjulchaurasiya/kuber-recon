"""Safe Operator-Run Razorpay Wire Diagnostic Tool.
=================================================
Performs read-only API connectivity checks to the Razorpay gateway.

Safety Invariants:
1. Operator-Run Only: Strictly excluded from automated CI and test suites.
2. Default Test Mode: Requires explicit `--live` flag to use live production credentials.
3. Strict Redaction: All authorization headers, secrets, merchant IDs, and account numbers
   are irreversibly redacted before logging or returning.
4. Read-Only Verification: Calls safe read-only endpoint (GET /v1/orders?count=1).
5. Explicit Framing: Connectivity verification only; does not execute or claim live settlement.
"""

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import re
import sys
import time
from typing import Any, Dict, Optional
import urllib.error
import urllib.request

from kuber_recon.config import config


SAFE_READ_ONLY_ENDPOINT = "https://api.razorpay.com/v1/orders?count=1"
OPERATOR_NOTICE = (
    "NOTICE: Operator Wire Diagnostic performs read-only connectivity verification against "
    "the Razorpay API. It does not execute live financial settlements, transfers, or releases."
)


def redact_sensitive_string(val: Optional[str], keep_prefix: int = 4, keep_suffix: int = 4) -> str:
    """Mask secret strings keeping only safe prefix/suffix."""
    if not val:
        return "[REDACTED_EMPTY]"
    val_str = str(val).strip()
    if len(val_str) <= keep_prefix + keep_suffix:
        return "[REDACTED]"
    return f"{val_str[:keep_prefix]}...{val_str[-keep_suffix:]}"


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Redact sensitive headers such as Authorization, X-Razorpay-Signature, etc."""
    redacted = {}
    sensitive_keys = {"authorization", "x-razorpay-signature", "x-api-key", "api-key", "cookie", "x-merchant-id"}
    for k, v in headers.items():
        if k.lower() in sensitive_keys:
            redacted[k] = "[REDACTED_SECRET]"
        else:
            redacted[k] = v
    return redacted


@dataclass(frozen=True)
class WireDiagnosticResult:
    mode: str  # "test_mode" or "live"
    endpoint: str
    http_status: int
    roundtrip_latency_ms: float
    network_reachable: bool
    credentials_authenticated: bool
    verified: bool  # True ONLY if network_reachable AND credentials_authenticated (HTTP 200)
    request_id_redacted: str
    message: str
    redacted_key_id: str
    framing: str = OPERATOR_NOTICE
    timestamp: str = ""


def run_wire_diagnostic(
    is_live: bool = False,
    override_key_id: Optional[str] = None,
    override_key_secret: Optional[str] = None,
    timeout_seconds: float = 10.0,
) -> WireDiagnosticResult:
    """
    Execute safe, read-only wire diagnostic against Razorpay API.
    
    Defaults to Test Mode credentials unless is_live=True is explicitly passed.
    Distinguishes network/TLS reachability from credential authentication.
    """
    mode = "live" if is_live else "test_mode"

    # Resolve credentials based on mode
    if is_live:
        key_id = override_key_id or os.getenv("RAZORPAY_LIVE_KEY_ID") or config.razorpay_key_id
        key_secret = override_key_secret or os.getenv("RAZORPAY_LIVE_KEY_SECRET") or config.razorpay_key_secret
    else:
        key_id = override_key_id or os.getenv("RAZORPAY_TEST_KEY_ID") or os.getenv("RAZORPAY_KEY_ID") or "rzp_test_mock_operator_diag"
        key_secret = override_key_secret or os.getenv("RAZORPAY_TEST_KEY_SECRET") or os.getenv("RAZORPAY_KEY_SECRET") or "mock_secret_not_used"

    redacted_key_id = redact_sensitive_string(key_id, keep_prefix=8, keep_suffix=4)

    # Encode Basic Auth safely in-memory
    auth_pair = f"{key_id}:{key_secret}"
    auth_header = f"Basic {base64.b64encode(auth_pair.encode()).decode()}"

    req = urllib.request.Request(
        url=SAFE_READ_ONLY_ENDPOINT,
        method="GET",
        headers={
            "Authorization": auth_header,
            "User-Agent": "KuberRecon-Operator-Diagnostic/1.0",
            "Accept": "application/json",
        },
    )

    t0 = time.perf_counter()
    http_status = 0
    raw_request_id = ""
    network_reachable = False
    credentials_authenticated = False
    verified = False
    message = ""

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            http_status = response.getcode()
            raw_request_id = response.headers.get("x-razorpay-request-id", "")
            network_reachable = True
            credentials_authenticated = (http_status == 200)
            verified = credentials_authenticated
            message = f"Success: Gateway responded with HTTP {http_status} OK. Wire reachable and credentials authenticated."
    except urllib.error.HTTPError as err:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        http_status = err.code
        raw_request_id = err.headers.get("x-razorpay-request-id", "")
        network_reachable = True
        credentials_authenticated = False
        verified = False
        if http_status == 401:
            message = (
                f"Network Reachable (TLS/DNS ok), but Credentials Rejected: "
                f"Gateway returned HTTP 401 Unauthorized. Valid Razorpay credentials required to authenticate API integration."
            )
        else:
            message = f"Gateway returned HTTP {http_status}: {err.reason}"
    except (urllib.error.URLError, TimeoutError) as err:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        http_status = 0
        network_reachable = False
        credentials_authenticated = False
        verified = False
        message = f"Network Connection Failed: {err}"

    # Redact request ID if present (keep only safe prefix)
    redacted_req_id = redact_sensitive_string(raw_request_id, keep_prefix=6, keep_suffix=4) if raw_request_id else "[NOT_RETURNED]"

    return WireDiagnosticResult(
        mode=mode,
        endpoint=SAFE_READ_ONLY_ENDPOINT,
        http_status=http_status,
        roundtrip_latency_ms=round(latency_ms, 2),
        network_reachable=network_reachable,
        credentials_authenticated=credentials_authenticated,
        verified=verified,
        request_id_redacted=redacted_req_id,
        message=message,
        redacted_key_id=redacted_key_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def cli_main():
    """CLI entrypoint for safe operator wire diagnostic."""
    is_live = "--live" in sys.argv
    print("=" * 80)
    print(" [OPERATOR TOOL] RAZORPAY WIRE CONNECTIVITY DIAGNOSTIC")
    print(f" Mode: {'[LIVE PRODUCTION]' if is_live else '[TEST MODE (Default)]'}")
    print(f" Safe Endpoint: {SAFE_READ_ONLY_ENDPOINT}")
    print(f" Framing: {OPERATOR_NOTICE}")
    print("-" * 80)

    result = run_wire_diagnostic(is_live=is_live)

    print(f" Timestamp                : {result.timestamp}")
    print(f" Redacted Key ID          : {result.redacted_key_id}")
    print(f" HTTP Status Code         : {result.http_status}")
    print(f" Roundtrip Latency        : {result.roundtrip_latency_ms} ms")
    print(f" Redacted Request ID      : {result.request_id_redacted}")
    print(f" Network Reachable        : {'[PASS]' if result.network_reachable else '[FAIL]'}")
    print(f" Credentials Authenticated: {'[PASS]' if result.credentials_authenticated else '[FAIL]'}")
    print(f" Verification Status      : {'[PASS]' if result.verified else '[FAIL]'}")
    print(f" Diagnostics Message      : {result.message}")
    print("=" * 80)

    # Exit non-zero if credentials failed authentication
    sys.exit(0 if result.verified else 1)


if __name__ == "__main__":
    cli_main()
