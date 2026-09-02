"""Tests for Capital Facilities StorageBackend contract, durability, cross-tenant isolation, and CAS.
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from kuber_recon.capital import (
    ActiveFacilityExistsError,
    CapitalFacilityManager,
    CapitalOffer,
    FacilityStatus,
)
from kuber_recon.storage import (
    PostgreSQLStorageBackend,
    SQLiteStorageBackend,
    StorageBackend,
)
from kuber_recon.types import EvidenceTier, ReconciledSettlementBlock, SettlementStatus


def make_settlement_block(lump_sum_paise: int, utr: str = "UTR-TEST-01") -> ReconciledSettlementBlock:
    return ReconciledSettlementBlock(
        settlement_id=f"set_{utr.lower()}",
        utr_number=utr,
        lump_sum_paise=lump_sum_paise,
        gross_gmv_paise=lump_sum_paise + 5000,
        total_mdr_fee_paise=4000,
        total_gst_on_mdr_paise=720,
        total_tds_withheld_paise=280,
        rounding_variance_paise=0,
        status=SettlementStatus.SETTLED,
        matched_invoices=["inv_01"],
        matched_refunds=[],
        evidence_tier=EvidenceTier.TIER_A,
        proof_hash=f"sha256:mock_proof_{utr}",
    )


def _dummy_offer(merchant_id: str = "merch_101", principal: int = 10000000) -> CapitalOffer:
    now = datetime.now(timezone.utc)
    return CapitalOffer(
        merchant_id=merchant_id,
        verified_delivered_gmv_paise=principal * 4,
        settlement_reliability_index=Decimal("0.98"),
        risk_tier="TIER_A",
        max_eligible_advance_paise=principal * 2,
        offered_principal_paise=principal,
        factor_fee_paise=200000,
        total_repayment_paise=principal + 200000,
        sweep_rate=Decimal("0.10"),
        underwritten_at=now,
        offer_expires_at=now,
        explanation="Test offer",
    )


def test_capital_manager_uses_storage_backend():
    """Verify that CapitalFacilityManager operates directly via the injected StorageBackend."""
    mock_backend = MagicMock(spec=StorageBackend)
    mock_backend.get_capital_idempotency.return_value = None
    mock_backend.get_active_facility_for_merchant.return_value = None
    mock_backend.insert_capital_facility.return_value = True
    now_iso = datetime.now(timezone.utc).isoformat()
    mock_backend.get_capital_facility.return_value = {
        "facility_id": "CAP-FAC-TESTMOCK",
        "tenant_id": "tenant_1",
        "merchant_id": "merch_101",
        "principal_paise": 10000000,
        "factor_fee_paise": 200000,
        "total_repayment_paise": 10200000,
        "remaining_balance_paise": 10200000,
        "sweep_rate": "0.10",
        "status": FacilityStatus.ACTIVE.value,
        "disbursed_at": now_iso,
        "last_settlement_at": now_iso,
        "payout_transfer_id": "pout_mock",
        "version": 1,
    }
    mock_backend.list_repayment_events.return_value = []

    manager = CapitalFacilityManager(backend=mock_backend)
    assert manager.backend is mock_backend

    offer = _dummy_offer("merch_101")
    fac = manager.disburse_advance(offer=offer, tenant_id="tenant_1")

    assert fac.facility_id == "CAP-FAC-TESTMOCK"
    mock_backend.insert_capital_facility.assert_called_once()
    mock_backend.get_capital_facility.assert_called()


def test_capital_facility_survives_restart(tmp_path):
    """Verify that facilities and sweep events persist on disk across manager restarts."""
    db_file = tmp_path / "capital_durability.db"

    # Instance 1: Disburse advance
    backend1 = SQLiteStorageBackend(db_path=db_file)
    manager1 = CapitalFacilityManager(backend=backend1)
    offer = _dummy_offer("merch_persist")
    fac = manager1.disburse_advance(offer=offer, tenant_id="tenant_persist")
    assert fac.remaining_balance_paise == 10200000

    # Apply a sweep
    block = make_settlement_block(1964600, utr="UTR_SWEEP_PERSIST")
    fac_after, sweep_event = manager1.process_settlement_sweep(
        facility_id=fac.facility_id,
        settlement_block=block,
        tenant_id="tenant_persist",
    )
    expected_deduction = int(Decimal("1964600") * Decimal("0.10"))
    assert sweep_event.sweep_deduction_paise == expected_deduction

    # Instance 2: Simulate complete process restart
    backend2 = SQLiteStorageBackend(db_path=db_file)
    manager2 = CapitalFacilityManager(backend=backend2)
    fac_recovered = manager2.get_facility(fac.facility_id, tenant_id="tenant_persist")
    assert fac_recovered is not None
    assert fac_recovered.remaining_balance_paise == fac_after.remaining_balance_paise
    assert len(fac_recovered.repayment_events) == 1
    assert fac_recovered.repayment_events[0].settlement_utr == "UTR_SWEEP_PERSIST"


def test_postgres_capital_repository_contract():
    """Verify that PostgreSQLStorageBackend implements all 10 required capital storage methods."""
    required_methods = [
        "insert_capital_facility",
        "get_capital_facility",
        "get_active_facility_for_merchant",
        "list_capital_facilities",
        "update_capital_facility_balance",
        "insert_repayment_event",
        "list_repayment_events",
        "insert_capital_idempotency",
        "get_capital_idempotency",
        "reset_capital_facilities",
    ]
    for method_name in required_methods:
        assert hasattr(PostgreSQLStorageBackend, method_name), f"PostgreSQLStorageBackend missing {method_name}"
        assert callable(getattr(PostgreSQLStorageBackend, method_name))
        assert hasattr(SQLiteStorageBackend, method_name), f"SQLiteStorageBackend missing {method_name}"
        assert callable(getattr(SQLiteStorageBackend, method_name))


def test_cross_tenant_capital_isolation():
    """Verify strict tenant isolation across disbursements, queries, and sweeps."""
    backend = SQLiteStorageBackend(db_path=":memory:")
    manager = CapitalFacilityManager(backend=backend)

    offer_a = _dummy_offer("merch_shared", principal=5000000)
    offer_b = _dummy_offer("merch_shared", principal=8000000)

    # Same merchant ID in two distinct tenants
    fac_a = manager.disburse_advance(offer_a, tenant_id="tenant_A")
    fac_b = manager.disburse_advance(offer_b, tenant_id="tenant_B")

    # Tenant A cannot see Tenant B's facility
    assert manager.get_facility(fac_b.facility_id, tenant_id="tenant_A") is None
    assert manager.get_facility(fac_a.facility_id, tenant_id="tenant_B") is None

    # List scoping
    list_a = manager.list_facilities("tenant_A")
    assert len(list_a) == 1
    assert list_a[0].facility_id == fac_a.facility_id

    list_b = manager.list_facilities("tenant_B")
    assert len(list_b) == 1
    assert list_b[0].facility_id == fac_b.facility_id


def test_concurrent_sweep_cas():
    """Verify optimistic concurrency CAS: stale version update must fail."""
    backend = SQLiteStorageBackend(db_path=":memory:")
    manager = CapitalFacilityManager(backend=backend)

    offer = _dummy_offer("merch_cas")
    fac = manager.disburse_advance(offer, tenant_id="tenant_cas")
    assert fac.version == 1

    now_iso = datetime.now(timezone.utc).isoformat()
    # CAS update 1: Version 1 -> Version 2 succeeds
    ok1 = backend.update_capital_facility_balance(
        facility_id=fac.facility_id,
        expected_version=1,
        new_balance_paise=9000000,
        new_status="ACTIVE",
        last_settlement_at=now_iso,
        tenant_id="tenant_cas",
    )
    assert ok1 is True

    # CAS update 2 with stale version 1 must be rejected
    ok2 = backend.update_capital_facility_balance(
        facility_id=fac.facility_id,
        expected_version=1,
        new_balance_paise=8000000,
        new_status="ACTIVE",
        last_settlement_at=now_iso,
        tenant_id="tenant_cas",
    )
    assert ok2 is False


def test_duplicate_sweep_idempotency():
    """Verify duplicate sweep processing with identical idempotency key is idempotent."""
    backend = SQLiteStorageBackend(db_path=":memory:")
    manager = CapitalFacilityManager(backend=backend)

    offer = _dummy_offer("merch_idem")
    fac = manager.disburse_advance(offer, tenant_id="tenant_idem")

    block = make_settlement_block(982300, utr="UTR_SWEEP_IDEM")

    fac1, sweep1 = manager.process_settlement_sweep(
        facility_id=fac.facility_id,
        settlement_block=block,
        tenant_id="tenant_idem",
        idempotency_key="sweep_key_001",
    )
    balance_after_1 = fac1.remaining_balance_paise

    # Replay identical sweep request
    fac2, sweep2 = manager.process_settlement_sweep(
        facility_id=fac.facility_id,
        settlement_block=block,
        tenant_id="tenant_idem",
        idempotency_key="sweep_key_001",
    )
    # Zero double deduction
    assert fac2.remaining_balance_paise == balance_after_1
    assert sweep2.sweep_id == sweep1.sweep_id
