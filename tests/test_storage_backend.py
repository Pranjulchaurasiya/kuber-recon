"""Tests for StorageBackend abstraction, factory selection, and fail-closed security.
"""

from pathlib import Path
import tempfile
import pytest
from kuber_recon.config import EnvironmentMode, SecurityConfigError
from kuber_recon.storage import (
    PostgreSQLStorageBackend,
    SQLiteStorageBackend,
    get_storage_backend,
)


def test_storage_factory_selects_sqlite_in_sandbox():
    """Verify that SANDBOX_DEMO defaults to SQLiteStorageBackend with WAL mode."""
    backend = get_storage_backend(
        database_url="sqlite:///:memory:",
        env=EnvironmentMode.SANDBOX_DEMO,
    )
    assert isinstance(backend, SQLiteStorageBackend)
    health = backend.health_check()
    assert health["backend"] == "SQLite (WAL Mode)"
    assert health["status"] == "connected"


def test_storage_factory_prohibits_sqlite_in_production():
    """Verify that PRODUCTION fails closed if SQLite is configured."""
    with pytest.raises(SecurityConfigError, match="SQLite is strictly prohibited in PRODUCTION"):
        get_storage_backend(
            database_url="sqlite:///kuber_prod.db",
            env=EnvironmentMode.PRODUCTION,
        )


def test_storage_factory_prohibits_sqlite_in_staging():
    """Verify that STAGING fails closed if SQLite is configured."""
    with pytest.raises(SecurityConfigError, match="SQLite is prohibited in STAGING"):
        get_storage_backend(
            database_url="sqlite:///kuber_staging.db",
            env=EnvironmentMode.STAGING,
        )


def test_storage_factory_selects_postgresql_in_production():
    """Verify that PRODUCTION selects PostgreSQLStorageBackend when postgresql:// is provided."""
    backend = get_storage_backend(
        database_url="postgresql+psycopg2://user:pass@aurora-cluster.internal:5432/kuber_prod",
        env=EnvironmentMode.PRODUCTION,
    )
    assert isinstance(backend, PostgreSQLStorageBackend)


def test_sqlite_storage_backend_contract_cas_lifecycle():
    """Verify atomic CAS state transitions, version increments, and audit log appending."""
    backend = SQLiteStorageBackend(db_path=":memory:")

    # 1. Insert contract
    success = backend.insert_contract(
        contract_id="cnt_test_001",
        tenant_id="tenant_alpha",
        status="HELD",
        transfer_id="trf_test_001",
        amount_paise=500000,
        fee_paise=10000,
        on_hold=True,
        on_hold_until=int(1780000000),
    )
    assert success is True

    # Duplicate contract insertion returns False
    dup = backend.insert_contract(
        contract_id="cnt_test_001",
        tenant_id="tenant_alpha",
        status="HELD",
        transfer_id="trf_test_001",
        amount_paise=500000,
        fee_paise=10000,
        on_hold=True,
        on_hold_until=None,
    )
    assert dup is False

    # 2. Transition state with valid expected_status and version
    trans_ok = backend.transition_contract_state(
        contract_id="cnt_test_001",
        expected_status="HELD",
        target_status="VERIFYING",
        expected_version=1,
        tenant_id="tenant_alpha",
        proof_hash="sha256:proof_abc",
        assertions_passed=True,
    )
    assert trans_ok is True

    contract = backend.get_contract("cnt_test_001", tenant_id="tenant_alpha")
    assert contract is not None
    assert contract["status"] == "VERIFYING"
    assert contract["version"] == 2
    assert contract["proof_hash"] == "sha256:proof_abc"

    # 3. Cross-tenant isolation
    wrong_tenant = backend.get_contract("cnt_test_001", tenant_id="tenant_beta")
    assert wrong_tenant is None

    # Stale version transition must fail
    trans_stale = backend.transition_contract_state(
        contract_id="cnt_test_001",
        expected_status="VERIFYING",
        target_status="RELEASED",
        expected_version=1,  # Version is already 2!
        tenant_id="tenant_alpha",
    )
    assert trans_stale is False

    # Audit log verification
    logs = backend.list_audit_logs("cnt_test_001")
    assert len(logs) == 2
    assert logs[0]["status"] == "HELD"
    assert logs[1]["status"] == "VERIFYING"


def test_sqlite_storage_webhook_deduplication():
    """Verify single authoritative webhook event idempotency."""
    backend = SQLiteStorageBackend(db_path=":memory:")
    assert backend.try_insert_webhook_event("evt_first_time") is True
    # Duplicate insertion returns False
    assert backend.try_insert_webhook_event("evt_first_time") is False
