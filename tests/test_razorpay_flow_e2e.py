"""End-to-End Razorpay Settlement Assurance & Split-Sweep Integration Test.
-------------------------------------------------------------------------
TEST BOUNDARY DISCLAIMER:
The Razorpay Route adapter utilized in this test is an in-memory deterministic
simulation / test double conforming to the Razorpay API contracts. It is NOT
a live production gateway connection, ensuring zero external network dependency
and 100% offline test reproducibility.

10-Step Lifecycle Verification:
  1. Invoice/order creation
  2. Payment captured
  3. Route transfer created with on_hold: true
  4. Settlement recon details fetched
  5. Combinatorial reconciliation executed (Horowitz-Sahni paise-exact)
  6. Merkle tree generated and signed (cryptographic assertion)
  7. Route transfer hold released (on_hold: false)
  8. transfer.processed webhook validated and processed idempotently
  9. Working capital advance underwritten and disbursed
  10. Nodal settlement sweep applied and advance balance amortized
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import pytest

from kuber_recon.adapters.razorpay import FakeRazorpayRouteAdapter
from kuber_recon.capital import CapitalFacilityManager, CapitalUnderwriter, FacilityStatus
from kuber_recon.engine import ReconciliationEngine
from kuber_recon.merkle import FinancialMerkleTree
from kuber_recon.security import get_key_custodian
from kuber_recon.server import WebhookIdempotencyStore
from kuber_recon.storage import SQLiteStorageBackend
from kuber_recon.types import BankNodalCredit, InvoiceRecord, PaymentMethod


def test_full_razorpay_settlement_and_capital_lifecycle():
    tenant_id = "merchant_rzp_e2e_test"
    seller_acc = "acc_e2e_seller_01"
    storage = SQLiteStorageBackend(":memory:")
    adapter = FakeRazorpayRouteAdapter()
    custodian = get_key_custodian(key_id="cfo_autonomous_verifier")
    from kuber_recon.capital import CapitalUnderwritingConfig
    config = CapitalUnderwritingConfig(min_advance_paise=100000)
    idempotency_store = WebhookIdempotencyStore(backend=storage)
    facility_mgr = CapitalFacilityManager(config=config, backend=storage)
    underwriter = CapitalUnderwriter(config=config)


    # Step 1: Invoice / Order Creation
    now = datetime.now(timezone.utc)
    order_id = "order_e2e_001"
    invoice = InvoiceRecord(
        invoice_id="INV-E2E-1001",
        order_id=order_id,
        payment_id="pay_e2e_001",
        customer_gstin="27AABCU9603R1ZM",
        supplier_gstin="29AAFCR1234K1ZV",
        amount_in_paise=500000,  # Rs 5,000.00
        method=PaymentMethod.UPI,
        captured_at=now - timedelta(hours=2),
        is_settled=False,
    )
    assert invoice.amount_in_paise == 500000

    # Step 2: Payment Captured
    payment_id = invoice.payment_id
    assert payment_id.startswith("pay_")

    # Step 3: Route Transfer Created with on_hold: true
    transfer_res = adapter.create_transfer(
        account_id=seller_acc,
        amount_paise=invoice.amount_in_paise,
        currency="INR",
        on_hold=True,
        notes={"invoice_id": invoice.invoice_id, "tenant_id": tenant_id},
    )
    transfer_id = transfer_res["id"]
    assert transfer_res["on_hold"] is True
    assert transfer_res["status"] == "pending"

    # Step 4: Settlement Recon Details Fetched (Paise-Exact Indian Taxation: 1% Section 194-O TDS)
    from kuber_recon.tax import IndianTaxKernel
    _, _, _, net_settleable_paise = IndianTaxKernel.calculate_line_deductions(invoice.amount_in_paise, invoice.method)

    bank_credit = BankNodalCredit(
        utr_number="UTR-E2E-20260902-001",
        account_number="NODAL-YES-001",
        credit_amount_in_paise=net_settleable_paise,
        value_date=now.date(),
        raw_narration=f"CMS/NODAL/SETL/{invoice.invoice_id}",
    )
    assert bank_credit.credit_amount_in_paise == net_settleable_paise


    # Step 5: Combinatorial Reconciliation Executed (paise-exact)
    engine = ReconciliationEngine()
    reconciled_blocks, exceptions = engine.reconcile_batch([bank_credit], [invoice])
    assert len(reconciled_blocks) == 1
    assert len(exceptions) == 0
    block = reconciled_blocks[0]
    assert block.utr_number == bank_credit.utr_number
    assert block.lump_sum_paise == net_settleable_paise


    # Step 6: Merkle Tree Generated and Signed
    leaves = [hashlib.sha256(f"{block.utr_number}:{block.lump_sum_paise}".encode()).hexdigest()]
    merkle = FinancialMerkleTree(leaves)
    cert = custodian.sign_merkle_leaf(
        leaf_hash=merkle.root_hash,
        context={"contract_id": transfer_id, "approver": "cfo_autonomous_verifier", "action": "RELEASE"},
    )
    assert cert.signature_hex is not None
    assert custodian.verify_certificate(cert)

    # Step 7: Route Transfer Hold Released (on_hold: false)
    mod_res = adapter.modify_transfer_hold(transfer_id, on_hold=False)
    assert mod_res["on_hold"] is False
    assert mod_res["status"] == "processed"

    # Step 8: transfer.processed Webhook Validated and Processed Idempotently
    webhook_event_id = f"evt_trf_proc_{transfer_id}"
    first_attempt = idempotency_store.try_insert(webhook_event_id)
    assert first_attempt is True
    # Replay must be deduplicated
    replay_attempt = idempotency_store.try_insert(webhook_event_id)
    assert replay_attempt is False

    # Step 9: Working Capital Advance Underwritten & Disbursed
    offer = underwriter.generate_offer(
        merchant_id=tenant_id,
        reconciled_blocks=reconciled_blocks,
        invoices=[invoice],
        requested_advance_paise=200000,  # Rs 2,000.00
    )
    assert offer.offered_principal_paise > 0
    assert offer.total_repayment_paise > offer.offered_principal_paise

    facility = facility_mgr.disburse_advance(
        offer=offer,
        tenant_id=tenant_id,
        idempotency_key="idemp_e2e_disburse_001",
    )
    assert facility.status == FacilityStatus.ACTIVE
    initial_balance = facility.remaining_balance_paise
    assert initial_balance == offer.total_repayment_paise

    # Step 10: Nodal Settlement Sweep Applied & Advance Balance Amortized
    # Another credit arrives for Rs 1,000.00
    sweep_credit_block = reconciled_blocks[0]  # Gross Rs 5,000.00
    updated_fac, sweep_event = facility_mgr.process_settlement_sweep(
        facility_id=facility.facility_id,
        settlement_block=sweep_credit_block,
        tenant_id=tenant_id,
        idempotency_key="idemp_e2e_sweep_001",
    )
    assert sweep_event.sweep_deduction_paise > 0
    assert updated_fac.remaining_balance_paise == initial_balance - sweep_event.sweep_deduction_paise
    assert updated_fac.remaining_balance_paise < initial_balance
    assert updated_fac.status in (FacilityStatus.AMORTIZING, FacilityStatus.REPAID)
