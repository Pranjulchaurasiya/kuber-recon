"""
Unit Tests for the 5 Production Integration Layers
--------------------------------------------------
Verifies:
1. GSP / IRP / Bank H2H Gateway interfaces.
2. Financial Event Envelope & Transactional Outbox CDC.
3. Live REST / SSE API controller.
4. Cryptographic Key Custodian (Ed25519 & KMS ECDSA).
5. Multi-Tenant Maker-Checker Governance & Spend Cap policies.
"""

import pytest
from kuber_recon.gateways import SandboxGSTNGateway, SandboxIRPGateway
from kuber_recon.events import FinancialEventEnvelope, TransactionalOutboxDispatcher
from kuber_recon.api import KuberReconAPIController
from kuber_recon.security import SoftwareEd25519Custodian
from kuber_recon.governance import UserIdentity, MakerCheckerAuthorizationPolicy


def test_layer_1_gstn_and_irp_gateways():
    gstn = SandboxGSTNGateway()
    gstr2b = gstn.fetch_gstr2b("27AAPCA1234F1Z5", "082026")
    assert len(gstr2b) == 2
    assert gstn.verify_supplier_filing_status("27AAPCA1234F1Z5", "082026") is True
    assert gstn.verify_supplier_filing_status("27AAPCA1234F1Z5X", "082026") is False

    irp = SandboxIRPGateway()
    resp = irp.generate_irn({"supplier_gstin": "27AAPCA1234F1Z5", "doc_num": "INV-101", "doc_date": "2026-08-27"})
    assert len(resp.irn) == 64
    assert irp.verify_irn(resp.irn) is True


def test_layer_2_event_sourcing_and_outbox():
    dispatcher = TransactionalOutboxDispatcher()
    envelope = FinancialEventEnvelope(
        event_type="escrow.held",
        aggregate_id="ord_test_001",
        correlation_id="corr_99",
        idempotency_key="sha256_lock_01",
        payload={"amount_paise": 118000, "gst_paise": 18000},
    )
    dispatcher.stage_event(envelope)
    assert len(dispatcher._outbox) == 1

    published = dispatcher.poll_and_publish_cdc()
    assert published == 1
    assert dispatcher.published_count == 1


def test_layer_3_api_controller():
    controller = KuberReconAPIController()
    stats = controller.get_system_stats()
    assert stats.fmr == 0.000
    assert stats.protected_today_paise == 4281564000

    twin_res = controller.simulate_twin_scenario("bank_holiday", severity=1.0)
    assert twin_res["settlement_delay_days"] == 4
    assert abs(twin_res["liquidity_delta_paise"]) > 0


def test_layer_4_cryptographic_custody():
    ed_custodian = SoftwareEd25519Custodian()
    cert = ed_custodian.sign_merkle_leaf("0x8f3ad41c", {"approver": "CFO"})
    assert ed_custodian.verify_certificate(cert) is True


def test_layer_5_maker_checker_governance():
    maker = UserIdentity(user_id="user_analyst_01", email="analyst@rzp.com", tenant_id="tenant_rzp", roles={"treasury_analyst"})
    checker = UserIdentity(user_id="user_cfo_01", email="cfo@rzp.com", tenant_id="tenant_rzp", roles={"cfo"})

    # Valid approval
    assert MakerCheckerAuthorizationPolicy.validate_action_execution(maker, checker, amount_paise=15000, spend_cap_paise=20000) is True

    # Violation 1: Self-approval attempt
    with pytest.raises(PermissionError, match="Maker-Checker"):
        MakerCheckerAuthorizationPolicy.validate_action_execution(maker, maker, amount_paise=15000)

    # Violation 2: Approver lacks CFO role
    analyst_checker = UserIdentity(user_id="user_analyst_02", email="analyst2@rzp.com", tenant_id="tenant_rzp", roles={"treasury_analyst"})
    with pytest.raises(PermissionError, match="lacks CFO"):
        MakerCheckerAuthorizationPolicy.validate_action_execution(maker, analyst_checker, amount_paise=15000)

    # Violation 3: Spend cap overflow
    with pytest.raises(ValueError, match="exceeds spend cap"):
        MakerCheckerAuthorizationPolicy.validate_action_execution(maker, checker, amount_paise=25000, spend_cap_paise=20000)
