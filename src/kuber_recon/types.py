"""Core Base-10 Integer-Paise Types and Pydantic Schemas.

Enforces zero IEEE-754 floats across all currency values and mirrors official
Razorpay Go MCP `fetch_settlement_recon_details` contracts.
"""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, PlainSerializer, field_validator


def paise_to_inr_decimal(paise: int) -> Decimal:
    """Convert integer paise to base-10 INR Decimal."""
    return (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def inr_to_paise(inr_amount: Decimal | str | int) -> int:
    """Convert INR amount strictly to integer paise."""
    if isinstance(inr_amount, float):
        raise TypeError("IEEE-754 floats are barred on currency fields. Use str or Decimal.")
    d = Decimal(str(inr_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int((d * Decimal(100)).to_integral_value(rounding=ROUND_HALF_UP))


class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD_CREDIT = "card_credit"
    CARD_DEBIT = "card_debit"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class SettlementStatus(str, Enum):
    SETTLED = "settled"
    PARTIALLY_SETTLED = "partially_settled"
    HELD_AMBIGUOUS = "held_ambiguous"
    HELD_DISPUTED = "held_disputed"
    UNMATCHED = "unmatched"


class EvidenceTier(str, Enum):
    TIER_A = "tier_a_machine_fact"  # Exact UTR / Settlement ID (Immutable)
    TIER_B = "tier_b_prefix_heuristic"  # Exact amount + prefix match
    TIER_C = "tier_c_soft_entity"  # Fuzzy vendor name / unverified memo


class MatchResultStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS_COLLISION = "AMBIGUOUS_COLLISION"
    INCONCLUSIVE_TRUNCATED = "INCONCLUSIVE_TRUNCATED"


class SolverResult:
    def __init__(self, status: MatchResultStatus, solutions: List[List[str]], nodes_explored: int = 0, is_truncated: bool = False):
        self.status = status
        self.solutions = solutions
        self.nodes_explored = nodes_explored
        self.is_truncated = is_truncated


class InvoiceRecord(BaseModel):
    """Internal Merchant Invoice / Order Record."""

    invoice_id: str = Field(..., description="Unique merchant invoice identifier")
    order_id: str = Field(..., description="Razorpay order_id")
    payment_id: str = Field(..., description="Razorpay payment_id (e.g. pay_xxx)")
    customer_gstin: Optional[str] = Field(None, description="Customer GSTIN if B2B")
    supplier_gstin: str = Field(..., description="Merchant supplier GSTIN")
    amount_in_paise: int = Field(..., ge=0, description="Gross invoice amount in integer paise")
    method: PaymentMethod = Field(default=PaymentMethod.UPI)
    captured_at: datetime = Field(..., description="Timestamp payment was captured")
    is_settled: bool = Field(default=False)
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID owning this invoice")


class RazorpaySettlementItem(BaseModel):
    """Mirror of official Razorpay Go MCP `fetch_settlement_recon_details` row."""

    entity_id: str = Field(..., description="Payment ID or Refund ID")
    type: str = Field(..., description="payment | refund | transfer | adjustment")
    debit_in_paise: int = Field(default=0, ge=0, description="Deductions/Refunds in paise")
    credit_in_paise: int = Field(default=0, ge=0, description="Gross captured in paise")
    amount_in_paise: int = Field(..., description="Net contribution in paise")
    fee_in_paise: int = Field(default=0, ge=0, description="MDR fee in paise")
    tax_in_paise: int = Field(default=0, ge=0, description="18% GST on MDR in paise")
    settlement_id: str = Field(..., description="Razorpay settlement ID (e.g. setl_xxx)")
    settled_at: datetime = Field(..., description="Settlement clearing timestamp")


class GSTR2BLineItem(BaseModel):
    """Official CBIC GSTR-2B B2B Monthly Input Tax Credit (ITC) Portal Line Item."""

    supplier_gstin: str = Field(..., description="Supplier GSTIN")
    supplier_name: str = Field(..., description="Legal Trade Name")
    invoice_number: str = Field(..., description="Tax invoice number")
    invoice_date: date = Field(..., description="Date on tax invoice")
    taxable_value_in_paise: int = Field(..., ge=0, description="Taxable fee in paise")
    cgst_in_paise: int = Field(default=0, ge=0, description="9% Central GST in paise")
    sgst_in_paise: int = Field(default=0, ge=0, description="9% State GST in paise")
    igst_in_paise: int = Field(default=0, ge=0, description="18% Integrated GST in paise")
    total_tax_in_paise: int = Field(..., ge=0, description="Total ITC claimable in paise")
    itc_available: bool = Field(default=True, description="Rule 36(4) ITC eligibility")
    hsn_sac_code: str = Field(default="997159", description="Payment gateway SAC code")


class BankNodalCredit(BaseModel):
    """Lump-Sum Credit from Bank Nodal Statement (HDFC, ICICI, Axis)."""

    utr_number: str = Field(..., description="Bank Unique Transaction Reference")
    account_number: str = Field(..., description="Merchant account credited")
    credit_amount_in_paise: int = Field(..., gt=0, description="Net lump sum in integer paise")
    value_date: date = Field(..., description="Bank clearing date")
    raw_narration: str = Field(..., description="Raw bank string (e.g. NFX-RZR*REMIT*9901)")
    settlement_id: Optional[str] = Field(None, description="Extracted Razorpay settlement ID")


class ReconciledSettlementBlock(BaseModel):
    """Final, Sealed Reconciled Settlement Manifest."""

    settlement_id: str
    utr_number: str
    lump_sum_paise: int
    gross_gmv_paise: int
    total_mdr_fee_paise: int
    total_gst_on_mdr_paise: int
    total_tds_withheld_paise: int
    rounding_variance_paise: int
    status: SettlementStatus
    matched_invoices: List[str]
    matched_refunds: List[str]
    evidence_tier: EvidenceTier
    proof_hash: str
    reconciled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
