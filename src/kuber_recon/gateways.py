"""
Layer 1: External Statutory & Banking Gateways
---------------------------------------------
Standardized, production-grade interface adapters for:
1. GSTN / Authorized GSP (ClearTax / Iris) for GSTR-2B sync.
2. NIC e-Invoice IRP Gateway for IRN generation and verification.
3. Bank Host-to-Host (H2H) SFTP & ISO 20022 (pain.001 / camt.053).
4. NSDL TRACES TDS Gateway for Challan 281 & Form 26Q.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
import hashlib
import time
from pydantic import BaseModel, Field


class GSTR2BRecord(BaseModel):
    gstin_supplier: str
    supplier_name: str
    invoice_number: str
    invoice_date: str
    taxable_value_paise: int
    igst_paise: int = 0
    cgst_paise: int = 0
    sgst_paise: int = 0
    itc_eligibility: bool = True
    gstr1_filing_date: Optional[str] = None


class IRNResponse(BaseModel):
    irn: str
    signed_qr_code: str
    signed_invoice_json: str
    ack_number: str
    ack_date: str
    status: str = "ACT"  # Active


class ISO20022PaymentInstruction(BaseModel):
    message_id: str
    instruction_id: str
    end_to_end_id: str
    debtor_account: str
    creditor_account: str
    creditor_ifsc: str
    amount_paise: int
    currency: str = "INR"
    remittance_info: str


class BaseGSTNGateway(ABC):
    @abstractmethod
    def fetch_gstr2b(self, recipient_gstin: str, return_period: str) -> List[GSTR2BRecord]:
        """Fetch GSTR-2B inward supplies for a tax period (e.g. '082026')."""
        pass

    @abstractmethod
    def verify_supplier_filing_status(self, supplier_gstin: str, return_period: str) -> bool:
        """Check if vendor filed GSTR-1 for Section 16(2)(aa) compliance."""
        pass


class BaseIRPGateway(ABC):
    @abstractmethod
    def generate_irn(self, invoice_payload: Dict) -> IRNResponse:
        """Submit invoice to IRP and obtain 64-character SHA256 IRN."""
        pass

    @abstractmethod
    def verify_irn(self, irn: str) -> bool:
        """Verify whether an IRN is valid and active on the NIC portal."""
        pass


class BaseBankH2HGateway(ABC):
    @abstractmethod
    def initiate_payout_pain001(self, instruction: ISO20022PaymentInstruction) -> str:
        """Submit pain.001 XML payment order to Core Banking SFTP/API."""
        pass

    @abstractmethod
    def parse_bank_statement_camt053(self, statement_xml: str) -> List[Dict]:
        """Parse camt.053 end-of-day bank statement into reconciled UTR records."""
        pass


class SandboxGSTNGateway(BaseGSTNGateway):
    """Deterministic Sandbox Gateway for GSTR-2B synchronization."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "SANDBOX_GSP_KEY"

    def fetch_gstr2b(self, recipient_gstin: str, return_period: str) -> List[GSTR2BRecord]:
        return [
            GSTR2BRecord(
                gstin_supplier="27AAPCA1234F1Z5",
                supplier_name="Meridian Retail Pvt Ltd",
                invoice_number="INV-2291",
                invoice_date="2026-08-10",
                taxable_value_paise=10000000,
                igst_paise=1800000,
                itc_eligibility=True,
                gstr1_filing_date="2026-08-11",
            ),
            GSTR2BRecord(
                gstin_supplier="29BBBBB5678G2Z1",
                supplier_name="Nova Logistics LLP",
                invoice_number="INV-2292",
                invoice_date="2026-08-12",
                taxable_value_paise=4000000,
                cgst_paise=360000,
                sgst_paise=360000,
                itc_eligibility=True,
                gstr1_filing_date="2026-08-13",
            ),
        ]

    def verify_supplier_filing_status(self, supplier_gstin: str, return_period: str) -> bool:
        # Defaults if vendor GSTIN ends with 'X'
        return not supplier_gstin.endswith("X")


class SandboxIRPGateway(BaseIRPGateway):
    """Deterministic NIC e-Invoice IRP Gateway."""

    def generate_irn(self, invoice_payload: Dict) -> IRNResponse:
        inv_key = f"{invoice_payload.get('supplier_gstin')}:{invoice_payload.get('doc_num')}:{invoice_payload.get('doc_date')}"
        irn_hash = hashlib.sha256(inv_key.encode("utf-8")).hexdigest()
        return IRNResponse(
            irn=irn_hash,
            signed_qr_code=f"QR_{irn_hash[:16]}",
            signed_invoice_json=f'{{"irn":"{irn_hash}","status":"ACT"}}',
            ack_number=str(int(time.time())),
            ack_date="2026-08-27 10:00:00",
            status="ACT",
        )

    def verify_irn(self, irn: str) -> bool:
        return len(irn) == 64
