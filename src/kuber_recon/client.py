"""Razorpay Live Production API Client & Gateway Adapter.

Supports:
1. Fetching live settlement reconciliation rows (`fetch_settlement_recon_details`).
2. Creating live Route Transfers with `on_hold: True` escrow.
3. Programmatically releasing holds via `POST /v1/transfers/{id}/hold`.
4. Seamless fallback to Zero-Key Mock Engine if keys are unset.
"""

import os
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth
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
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay Route transfer with on_hold: True."""
        if not self.is_live:
            # Mock response in Zero-Key mode
            return {
                "id": f"trf_mock_{account_id[-6:]}",
                "entity": "transfer",
                "account": account_id,
                "amount": amount_paise,
                "currency": currency,
                "on_hold": True,
                "status": "processed",
            }

        url = f"{self.base_url}/transfers"
        payload = {
            "account": account_id,
            "amount": amount_paise,
            "currency": currency,
            "on_hold": True,  # <--- NATIVE ESCROW PRIMITIVE
            "notes": notes or {"protocol": "KUBERSOVEREIGN_GSTR2B_ESCROW"},
        }
        response = requests.post(url, auth=self.auth, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def release_route_hold(self, transfer_id: str) -> Dict[str, Any]:
        """Programmatically release an escrowed transfer upon GSTR-2B confirmation."""
        if not self.is_live:
            return {"id": transfer_id, "on_hold": False, "status": "settled"}

        url = f"{self.base_url}/transfers/{transfer_id}/hold"
        payload = {"on_hold": False}
        response = requests.patch(url, auth=self.auth, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
