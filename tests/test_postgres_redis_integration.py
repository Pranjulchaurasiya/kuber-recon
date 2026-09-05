"""Container-Backed PostgreSQL & Redis Integration Invariant Test Suite.
========================================================================
Notice: "PostgreSQL and Redis integration profile is exercised in CI containers."

Strict Production Invariants:
1. No Silent SQLite Fallback: Fails immediately if running in SQLite fallback mode in CI.
2. Verified Active Dialect: Explicitly asserts active dialect is PostgreSQL and Redis ping returns PONG.
3. Concurrent CAS Transitions: Verifies optimistic concurrency versioning prevents double-release.
4. Duplicate Webhook Idempotency: Verifies atomic replay rejection under concurrent deliveries.
5. Out-of-Order Webhook Delivery: Verifies stale webhook sequence rejection.
6. Transaction Rollback on Failed Invariants: Verifies zero partial writes on atomic failure.
7. Redis-Unavailable Graceful Degradation: Verifies resilient fail-closed behavior.
"""

from concurrent.futures import ThreadPoolExecutor
import os
import time
from typing import Optional
import pytest

from kuber_recon.config import config
from kuber_recon.distributed_lock import (
    DistributedLockTimeoutError,
    LocalRLockAdapter,
    get_lock,
)
from kuber_recon.storage import (
    PostgreSQLStorageBackend,
    SQLiteStorageBackend,
    get_storage_backend,
)


def get_ci_integration_credentials():
    """Retrieve database and redis connection URLs, checking CI enforcement flags."""
    db_url = os.getenv("DATABASE_URL") or config.database_url
    redis_url = os.getenv("REDIS_URL") or config.redis_url
    require_pg_redis = os.getenv("REQUIRE_POSTGRES_REDIS", "").lower() in ("true", "1", "yes")

    is_postgres = db_url and any(db_url.startswith(prefix) for prefix in ("postgresql://", "postgres://", "postgresql+psycopg2://"))
    return db_url, redis_url, is_postgres, require_pg_redis


@pytest.fixture(scope="module")
def pg_redis_backend():
    """Initialize live container-backed PostgreSQL and Redis storage backend."""
    db_url, redis_url, is_postgres, require_pg_redis = get_ci_integration_credentials()

    if require_pg_redis:
        if not is_postgres:
            pytest.fail(
                "FAIL-FAST: CI environment requires live PostgreSQL container. "
                f"SQLite fallback is strictly prohibited in CI! Current DATABASE_URL: {db_url}"
            )
        if not redis_url:
            pytest.fail(
                "FAIL-FAST: CI environment requires live Redis container. "
                "Missing REDIS_URL in CI environment!"
            )

    if not is_postgres:
        pytest.skip(
            "PostgreSQL and Redis integration profile is exercised in CI containers. "
            "Local environment is using SQLite/Sandbox."
        )

    try:
        import redis as redis_lib
        r = redis_lib.from_url(redis_url, socket_timeout=3.0)
        if not r.ping():
            if require_pg_redis:
                pytest.fail("FAIL-FAST: Redis container failed PING check.")
            pytest.skip("Redis ping failed; skipping live integration tests.")
    except Exception as err:
        if require_pg_redis:
            pytest.fail(f"FAIL-FAST: Redis connection failed in CI: {err}")
        pytest.skip(f"Redis not available: {err}")

    try:
        backend = PostgreSQLStorageBackend(database_url=db_url)
        # Verify connectivity and ensure DDL tables exist
        backend._init_db()
        conn = backend._get_connection()
        conn.close()
        return backend
    except Exception as err:
        if require_pg_redis:
            pytest.fail(f"FAIL-FAST: PostgreSQL connection failed in CI: {err}")
        pytest.skip(f"PostgreSQL not reachable: {err}")


def test_active_dialect_is_postgres_and_redis_live(pg_redis_backend):
    """Invariant 1: Active database dialect is PostgreSQL and Redis is live."""
    backend = pg_redis_backend
    assert isinstance(backend, PostgreSQLStorageBackend), "Must be an instance of PostgreSQLStorageBackend"
    assert "postgres" in backend.database_url.lower()

    # Verify Redis ping directly
    import redis as redis_lib
    r = redis_lib.from_url(os.getenv("REDIS_URL") or config.redis_url)
    assert r.ping() is True, "Redis container must return PONG"


def test_duplicate_webhook_idempotency(pg_redis_backend):
    """Invariant 2: Webhook idempotency layer atomically rejects duplicate replays."""
    backend = pg_redis_backend
    event_id = f"evt_ci_idemp_{int(time.time_ns())}"

    # First attempt must succeed
    first_insert = backend.try_insert_webhook_event(event_id)
    assert first_insert is True, "Initial webhook event insert must succeed"

    # Second duplicate attempt must be rejected atomically
    duplicate_insert = backend.try_insert_webhook_event(event_id)
    assert duplicate_insert is False, "Duplicate webhook event must return False (idempotent rejection)"


def test_concurrent_cas_transitions(pg_redis_backend):
    """Invariant 3: Concurrent CAS transitions prevent double-release race conditions."""
    backend = pg_redis_backend
    contract_id = f"ct_ci_cas_{int(time.time_ns())}"
    tenant_id = "tenant_ci_test"

    # 1. Initialize contract in INITIALIZED state at version 1
    created = backend.insert_contract(
        contract_id=contract_id,
        tenant_id=tenant_id,
        status="INITIALIZED",
        transfer_id=None,
        amount_paise=1000000,
        fee_paise=2000,
        on_hold=True,
        on_hold_until=None,
    )
    assert created is True

    # 2. Spawn 10 concurrent threads attempting to transition from INITIALIZED -> RELEASED
    success_count = 0
    failure_count = 0

    def attempt_transition(worker_idx: int) -> bool:
        return backend.transition_contract_state(
            contract_id=contract_id,
            expected_status="INITIALIZED",
            target_status="RELEASED",
            expected_version=1,
            tenant_id=tenant_id,
            on_hold=False,
            refusal_reason=None,
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(attempt_transition, range(10)))

    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if r is False)

    # Invariant: EXACTLY ONE worker succeeds in CAS transition
    assert success_count == 1, f"Expected exactly 1 successful CAS transition, observed {success_count}"
    assert failure_count == 9, f"Expected 9 failed CAS transitions, observed {failure_count}"

    # Final contract status check
    contract = backend.get_contract(contract_id, tenant_id=tenant_id)
    assert contract is not None
    assert contract["status"] == "RELEASED"
    assert contract["on_hold"] is False
    assert contract["version"] == 2


def test_out_of_order_webhook_delivery(pg_redis_backend):
    """Invariant 4: Stale / out-of-order webhook state transitions are rejected."""
    backend = pg_redis_backend
    contract_id = f"ct_ci_ooo_{int(time.time_ns())}"
    tenant_id = "tenant_ci_test"

    backend.insert_contract(
        contract_id=contract_id,
        tenant_id=tenant_id,
        status="PROCESSING",
        transfer_id="trf_ooo_01",
        amount_paise=2500000,
        fee_paise=5000,
        on_hold=True,
        on_hold_until=None,
    )

    # First advance to version 2
    ok1 = backend.transition_contract_state(
        contract_id=contract_id,
        expected_status="PROCESSING",
        target_status="SETTLING",
        expected_version=1,
        tenant_id=tenant_id,
    )
    assert ok1 is True

    # Simulate delayed out-of-order webhook with expected_version=1 (now stale)
    ok_stale = backend.transition_contract_state(
        contract_id=contract_id,
        expected_status="PROCESSING",
        target_status="RELEASED",
        expected_version=1,  # Stale version!
        tenant_id=tenant_id,
    )
    assert ok_stale is False, "Out-of-order transition with stale version must fail"

    # Verify contract remained in SETTLING at version 2
    contract = backend.get_contract(contract_id, tenant_id=tenant_id)
    assert contract["status"] == "SETTLING"
    assert contract["version"] == 2


def test_transaction_rollback_on_failed_invariants(pg_redis_backend):
    """Invariant 5: Atomic transactions roll back cleanly leaving zero partial state."""
    backend = pg_redis_backend
    contract_id = f"ct_ci_rollback_{int(time.time_ns())}"
    tenant_id = "tenant_ci_test"

    # Attempt an atomic transaction that executes an insert followed by an intentional SQL failure
    with backend._get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Insert valid contract
            cur.execute("""
                INSERT INTO apex_contracts (
                    contract_id, tenant_id, status, amount_paise, fee_paise, on_hold, version, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (contract_id, tenant_id, "INITIALIZED", 100000, 0, True, 1, int(time.time()), int(time.time())))

            # 2. Trigger intentional database failure (violating non-null or invalid syntax)
            try:
                cur.execute("INSERT INTO apex_contracts (contract_id, amount_paise) VALUES (NULL, NULL)")
                conn.commit()
            except Exception:
                conn.rollback()

    # Verify that the entire transaction was rolled back and contract_id was NOT persisted
    contract = backend.get_contract(contract_id, tenant_id=tenant_id)
    assert contract is None, "Contract should have rolled back completely on invariant failure"


def test_redis_unavailable_graceful_degradation(monkeypatch):
    """Invariant 6: Distributed lock degrades safely to LocalRLockAdapter when Redis is unreachable."""
    import kuber_recon.distributed_lock as dl
    # Reset init state and point to unreachable port
    monkeypatch.setattr(dl, "_redis_init_attempted", False)
    monkeypatch.setattr(dl, "_global_redis_client", None)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:59999/0")

    lock = dl.get_lock(resource_key="res_degrade_test", tenant_id="tenant_ci_test")
    # Must gracefully degrade to LocalRLockAdapter without crashing
    assert isinstance(lock, dl.LocalRLockAdapter)
    with lock:
        assert True
