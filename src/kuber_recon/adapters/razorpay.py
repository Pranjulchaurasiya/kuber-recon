"""Razorpay Gateway & Route Test Double Adapter.
------------------------------------------------
STATUS NOTICE:
Local In-Memory / Test-Double Adapter conforming to Razorpay Route REST API.
Production deployment requires active live Razorpay Route gateway credentials.
"""

from typing import Any, Dict, List, Optional
from kuber_recon.client import RazorpayClientAdapter


class FakeRazorpayRouteAdapter:
    """In-memory deterministic test double for Razorpay Route escrow and settlements."""

    def __init__(self):
        self.transfers: Dict[str, Dict[str, Any]] = {}
        self.is_live = False

    def create_transfer(
        self,
        account_id: str,
        amount_paise: int,
        currency: str = "INR",
        on_hold: bool = True,
        on_hold_until: Optional[int] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        transfer_id = f"trf_fake_{account_id[-6:]}_{len(self.transfers) + 1:03d}"
        res = {
            "id": transfer_id,
            "entity": "transfer",
            "account": account_id,
            "amount": amount_paise,
            "currency": currency,
            "on_hold": on_hold,
            "status": "pending" if on_hold else "processed",
            "notes": notes or {},
            "mode": "sandbox_simulation",
        }
        if on_hold_until:
            res["on_hold_until"] = on_hold_until
        self.transfers[transfer_id] = res
        return res

    def modify_transfer_hold(self, transfer_id: str, on_hold: bool = False) -> Dict[str, Any]:
        if transfer_id not in self.transfers:
            self.transfers[transfer_id] = {
                "id": transfer_id,
                "entity": "transfer",
                "on_hold": on_hold,
                "status": "processed" if not on_hold else "pending",
                "mode": "sandbox_simulation",
            }
        else:
            self.transfers[transfer_id]["on_hold"] = on_hold
            self.transfers[transfer_id]["status"] = "processed" if not on_hold else "pending"
        return self.transfers[transfer_id]

    def fetch_settlement_recon(self, year: int, month: int, day: int) -> List[Dict[str, Any]]:
        return []
