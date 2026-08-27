"""
Layer 5: Enterprise Governance, Multi-Tenancy & Maker-Checker Policies
----------------------------------------------------------------------
Enforces multi-tenant isolation and strict dual-control Maker-Checker
policies to prevent single-actor financial manipulation.
"""

from typing import Optional, Set
from pydantic import BaseModel, Field


class UserIdentity(BaseModel):
    user_id: str
    email: str
    tenant_id: str
    roles: Set[str]  # e.g. {'treasury_analyst', 'cfo', 'risk_admin'}


class MakerCheckerAuthorizationPolicy:
    """Enforces dual-control separation of duty on all financial mutations."""

    @staticmethod
    def validate_action_execution(
        proposer: UserIdentity,
        approver: UserIdentity,
        amount_paise: int,
        spend_cap_paise: int = 20000,
    ) -> bool:
        # Rule 1: Multi-tenant boundary check
        if proposer.tenant_id != approver.tenant_id:
            raise PermissionError(f"Cross-tenant approval denied: {proposer.tenant_id} != {approver.tenant_id}")

        # Rule 2: Anti-Self-Approval (Strict Maker-Checker)
        if proposer.user_id == approver.user_id:
            raise PermissionError("Violation of Maker-Checker policy: Proposer cannot approve their own action.")

        # Rule 3: CFO role check on Approver
        if "cfo" not in approver.roles and "treasury_admin" not in approver.roles:
            raise PermissionError(f"Approver {approver.user_id} lacks CFO / Treasury Admin role.")

        # Rule 4: Hard statutory spend cap bound
        if amount_paise > spend_cap_paise:
            raise ValueError(f"Amount {amount_paise} paise exceeds spend cap of {spend_cap_paise} paise.")

        return True
