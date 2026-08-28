"""Razorpay Live Production API Client & Gateway Adapter.

Supports:
1. Fetching live settlement reconciliation rows (`fetch_settlement_recon`).
2. Creating live Route Transfers with `on_hold: True` and optional `on_hold_until` TTL.
3. Modifying settlement hold status via `PATCH /v1/transfers/{id}` (`on_hold: False`).
4. Seamless fallback to Zero-Key Sandbox Engine if keys are unset.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    load_dotenv()
except ImportError:
    pass

from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod


class RazorpayClientAdapter:
    """Production Adapter for Live Razorpay API Integration."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
    ):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        self.base_url = "https://api.razorpay.com/v1"
        self.is_live = bool(self.key_id and self.key_secret)

    @property
    def auth(self) -> Optional[HTTPBasicAuth]:
        if self.is_live:
            return HTTPBasicAuth(self.key_id, self.key_secret)
        return None

    def fetch_settlement_recon(self, year: int, month: int, day: int) -> List[Dict[str, Any]]:
        """Fetch settlement reconciliation details for a specific date."""
        if not self.is_live:
            return []  # Graceful fallback to zero-key mock generator

        url = f"{self.base_url}/settlements/recon/combined"
        params = {"year": year, "month": month, "day": day}
        response = requests.get(url, auth=self.auth, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])

    def create_route_escrow_transfer(
        self,
        account_id: str,
        amount_paise: int,
        currency: str = "INR",
        on_hold_until: Optional[int] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay Route transfer with on_hold: True and optional on_hold_until TTL."""
        is_sandbox_account = (
            not self.is_live
            or os.getenv("RAZORPAY_SANDBOX", "false").lower() in ("true", "1", "yes")
            or account_id.startswith("acc_mock_")
            or account_id.startswith("acc_seller_")
            or account_id.startswith("acc_test_")
        )

        if is_sandbox_account:
            # Deterministic response in Zero-Key Sandbox mode
            res = {
                "id": f"trf_mock_{account_id[-6:]}",
                "entity": "transfer",
                "account": account_id,
                "amount": amount_paise,
                "currency": currency,
                "on_hold": True,
                "status": "processed",
                "mode": "sandbox_simulation",
            }
            if on_hold_until:
                res["on_hold_until"] = on_hold_until
            return res

        url = f"{self.base_url}/transfers"
        payload: Dict[str, Any] = {
            "account": account_id,
            "amount": amount_paise,
            "currency": currency,
            "on_hold": True,  # <--- NATIVE ESCROW PRIMITIVE
            "notes": notes or {"protocol": "APEX_ASSURANCE_AGENTIC_ESCROW"},
        }
        if on_hold_until:
            payload["on_hold_until"] = on_hold_until

        response = requests.post(url, auth=self.auth, json=payload, timeout=10)
        if response.status_code in (200, 201):
            return response.json()
        
        # In live mode, raise explicit error on Gateway API rejection
        raise RuntimeError(
            f"Razorpay Route Transfer Creation Failed (HTTP {response.status_code}): {response.text}"
        )

    def modify_transfer_hold(self, transfer_id: str, on_hold: bool = False) -> Dict[str, Any]:
        """
        Modify the settlement hold status of a transfer.
        PATCH /v1/transfers/{transfer_id} with {"on_hold": false}
        """
        is_sandbox_transfer = (
            not self.is_live
            or os.getenv("RAZORPAY_SANDBOX", "false").lower() in ("true", "1", "yes")
            or transfer_id.startswith("trf_mock_")
            or transfer_id.startswith("trf_test_")
        )

        if is_sandbox_transfer:
            return {
                "id": transfer_id,
                "entity": "transfer",
                "on_hold": on_hold,
                "status": "settled" if not on_hold else "processed",
                "mode": "sandbox_simulation",
            }

        url = f"{self.base_url}/transfers/{transfer_id}"
        payload = {"on_hold": on_hold}
        response = requests.patch(url, auth=self.auth, json=payload, timeout=10)
        if response.status_code in (200, 201):
            return response.json()

        # In live mode, raise explicit error on Gateway API rejection
        raise RuntimeError(
            f"Razorpay Route Hold Modification Failed (HTTP {response.status_code}): {response.text}"
        )

    def release_route_hold(self, transfer_id: str) -> Dict[str, Any]:
        """Legacy helper for releasing an escrowed transfer."""
        return self.modify_transfer_hold(transfer_id, on_hold=False)
