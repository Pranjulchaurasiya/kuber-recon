"""Test Suite: Tally Prime XML (<ENVELOPE>) Double-Entry Journal Export.
=============================================================================
Verifies:
1. Exact double-entry balancing (Debits == Credits, Delta = 0 paise).
2. Place-of-supply tax handling (CGST+SGST vs IGST).
3. Section 194-O TDS withholding integration.
4. XML structural compliance for Tally Prime voucher import.
5. Zero-Float Policy adherence (pure base-10 paise arithmetic).
6. Robustness against XML injection attacks.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import xml.etree.ElementTree as ET
import pytest

from kuber_recon.tally import (
    TallyLedgerConfig,
    _paise_to_rupee_str,
    export_tally_json_from_blocks,
    export_tally_xml,
    export_tally_xml_from_blocks,
    generate_tally_voucher_for_block,
)
from kuber_recon.types import EvidenceTier, ReconciledSettlementBlock, SettlementStatus


@pytest.fixture
def sample_reconciled_block() -> ReconciledSettlementBlock:
    """Standard balanced settlement block."""
    # Gross: 100,000 paise (Rs 1,000.00)
    # Fee: 2,000 paise (Rs 20.00)
    # GST on Fee (18%): 360 paise (Rs 3.60)
    # TDS (194-O 1%): 1,000 paise (Rs 10.00)
    # Net Bank: 100,000 - 2,000 - 360 - 1,000 = 96,640 paise (Rs 966.40)
    return ReconciledSettlementBlock(
        settlement_id="setl_test_99812",
        utr_number="HDFCN9901238471",
        lump_sum_paise=96640,
        gross_gmv_paise=100000,
        total_mdr_fee_paise=2000,
        total_gst_on_mdr_paise=360,
        total_tds_withheld_paise=1000,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["inv_001", "inv_002"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        reconciled_at=datetime(2026, 6, 12, 14, 30, 0, tzinfo=timezone.utc),
    )


def test_paise_to_rupee_conversion():
    """Verify exact rupee conversion without float precision loss."""
    assert _paise_to_rupee_str(0) == "0.00"
    assert _paise_to_rupee_str(1) == "0.01"
    assert _paise_to_rupee_str(100) == "1.00"
    assert _paise_to_rupee_str(123456) == "1234.56"
    assert _paise_to_rupee_str(-505) == "-5.05"


def test_tally_voucher_intra_state_balancing(sample_reconciled_block):
    """Verify intra-state voucher balances to exactly zero paise with CGST+SGST split."""
    voucher = generate_tally_voucher_for_block(
        sample_reconciled_block,
        is_interstate=False,
        split_gst=True,
    )

    assert voucher.is_balanced is True
    assert voucher.delta_paise == 0
    assert voucher.total_debit_paise == 100000
    assert voucher.total_credit_paise == 100000

    # Ledger breakdown checks
    entries = {e.ledger_name: e for e in voucher.entries}
    assert "HDFC Bank Current A/c" in entries
    assert entries["HDFC Bank Current A/c"].amount_paise == 96640
    assert entries["HDFC Bank Current A/c"].is_debit is True

    assert "Payment Gateway Charges" in entries
    assert entries["Payment Gateway Charges"].amount_paise == 2000

    # 360 paise split evenly into 180 + 180
    assert "Input CGST (PG Charges)" in entries
    assert entries["Input CGST (PG Charges)"].amount_paise == 180

    assert "Input SGST (PG Charges)" in entries
    assert entries["Input SGST (PG Charges)"].amount_paise == 180

    assert "TDS Receivable (Sec 194-O)" in entries
    assert entries["TDS Receivable (Sec 194-O)"].amount_paise == 1000

    assert "Razorpay Settlement Clearing A/c" in entries
    assert entries["Razorpay Settlement Clearing A/c"].amount_paise == 100000
    assert entries["Razorpay Settlement Clearing A/c"].is_debit is False


def test_tally_voucher_inter_state_balancing(sample_reconciled_block):
    """Verify inter-state voucher allocates full GST to IGST ledger."""
    voucher = generate_tally_voucher_for_block(
        sample_reconciled_block,
        is_interstate=True,
    )

    assert voucher.is_balanced is True
    assert voucher.delta_paise == 0

    entries = {e.ledger_name: e for e in voucher.entries}
    assert "Input IGST (PG Charges)" in entries
    assert entries["Input IGST (PG Charges)"].amount_paise == 360
    assert "Input CGST (PG Charges)" not in entries
    assert "Input SGST (PG Charges)" not in entries


def test_tally_xml_envelope_structure(sample_reconciled_block):
    """Verify valid XML generation conforming to Tally Prime import schema."""
    xml_output = export_tally_xml_from_blocks(
        [sample_reconciled_block],
        company_name="Acme Merchants Pvt Ltd",
    )

    # Must parse as valid XML
    root = ET.fromstring(xml_output)
    assert root.tag == "ENVELOPE"

    header = root.find("HEADER")
    assert header is not None
    assert header.find("TALLYREQUEST").text == "Import Data"

    body = root.find("BODY/IMPORTDATA")
    assert body is not None

    company = body.find("REQUESTDESC/STATICVARIABLES/SVCURRENTCOMPANY")
    assert company is not None
    assert company.text == "Acme Merchants Pvt Ltd"

    voucher = body.find("REQUESTDATA/TALLYMESSAGE/VOUCHER")
    assert voucher is not None
    assert voucher.attrib["VCHTYPE"] == "Journal"
    assert voucher.find("DATE").text == "20260612"
    assert voucher.find("REFERENCE").text == "HDFCN9901238471"

    # Verify ledger entries sum to 0.00 according to Tally amount convention
    # In Tally: debits are negative, credits are positive
    amounts = [Decimal(node.find("AMOUNT").text) for node in voucher.findall("ALLLEDGERENTRIES.LIST")]
    assert sum(amounts) == Decimal("0.00")


def test_tally_xml_escaping_security():
    """Verify special XML characters in narrations do not break XML parsing."""
    block = ReconciledSettlementBlock(
        settlement_id="setl_<evil>&'\"_99",
        utr_number="UTR & <CO> 'TEST\"",
        lump_sum_paise=10000,
        gross_gmv_paise=10000,
        total_mdr_fee_paise=0,
        total_gst_on_mdr_paise=0,
        total_tds_withheld_paise=0,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=[],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash="hash_123",
        reconciled_at=datetime.now(timezone.utc),
    )

    xml_output = export_tally_xml_from_blocks([block])
    # Must parse without ParseError
    root = ET.fromstring(xml_output)
    assert root is not None


def test_tally_json_export_structure(sample_reconciled_block):
    """Verify JSON export endpoint payload."""
    res = export_tally_json_from_blocks([sample_reconciled_block])
    assert res["status"] == "SUCCESS"
    assert res["voucher_count"] == 1
    assert res["is_all_balanced"] is True
    assert res["total_debit_paise"] == 100000
    assert res["total_credit_paise"] == 100000
    assert len(res["vouchers"][0]["entries"]) == 6


def test_tally_api_export_xml_endpoint():
    """Verify live FastAPI /api/reconcile/export/tally XML endpoint."""
    from fastapi.testclient import TestClient
    from kuber_recon.server import app

    headers = {
        "X-Merchant-Id": "merchant_rzp_primary",
        "X-API-Key": "kuber_sandbox_key_primary_2026",
    }
    client = TestClient(app)

    # Test GET XML export
    res = client.get("/api/reconcile/export/tally?records=20&seed=42&format=xml", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/xml"
    assert "attachment; filename=" in res.headers.get("content-disposition", "")
    assert "<ENVELOPE>" in res.text
    assert "<VOUCHER VCHTYPE=\"Journal\"" in res.text

    # Test POST JSON export
    res_json = client.post(
        "/api/reconcile/export/tally",
        headers=headers,
        json={"records": 10, "seed": 42, "format": "json", "is_interstate": False},
    )
    assert res_json.status_code == 200
    data = res_json.json()
    assert data["status"] == "SUCCESS"
    assert data["is_all_balanced"] is True
    assert data["voucher_count"] > 0

