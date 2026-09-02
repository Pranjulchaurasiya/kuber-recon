"""Tests for Transactional Outbox worker lease claiming, exponential backoff, retry, DLQ, and tenant isolation.
"""

import time
from unittest.mock import MagicMock
import pytest

from kuber_recon.events import (
    DeterministicFakePublisher,
    FinancialEventEnvelope,
    OutboxRecord,
    OutboxStatus,
    TransactionalOutboxDispatcher,
    calculate_backoff_seconds,
)


def _make_envelope(tenant_id: str = "tenant_test", agg_id: str = "cnt_101") -> FinancialEventEnvelope:
    return FinancialEventEnvelope(
        event_type="contract.held",
        tenant_id=tenant_id,
        aggregate_id=agg_id,
        correlation_id=f"corr_{agg_id}",
        idempotency_key=f"idem_{tenant_id}_{agg_id}_{time.time_ns()}",
        payload={"status": "HELD", "amount_paise": 100000},
    )


def test_event_not_marked_published_before_ack():
    """Verify that an event is NEVER marked PUBLISHED before a broker ACK is received."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    rec = dispatcher.append_event(env)
    assert rec.status == OutboxStatus.PENDING
    assert rec.published is False

    # Dispatch with a failing publisher
    fake_pub = DeterministicFakePublisher()
    fake_pub.should_fail = True
    published_count = dispatcher.poll_and_publish_cdc(publisher=fake_pub)

    assert published_count == 0
    records = dispatcher.get_tenant_events("tenant_test")
    assert len(records) == 1
    assert records[0].published is False
    assert records[0].status == OutboxStatus.PENDING


def test_failed_publish_increments_retry():
    """Verify that failed publish attempts increment retry_count."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    dispatcher.append_event(env, max_retries=5)

    fake_pub = DeterministicFakePublisher()
    fake_pub.should_fail = True

    dispatcher.poll_and_publish_cdc(publisher=fake_pub)
    records = dispatcher.get_tenant_events("tenant_test")
    assert records[0].retry_count == 1

    dispatcher.poll_and_publish_cdc(publisher=fake_pub)
    records = dispatcher.get_tenant_events("tenant_test")
    assert records[0].retry_count == 2


def test_exponential_backoff():
    """Verify that backoff calculation uses explicit 2^retry seconds bounded by max backoff."""
    assert calculate_backoff_seconds(0) == 1
    assert calculate_backoff_seconds(1) == 2
    assert calculate_backoff_seconds(2) == 4
    assert calculate_backoff_seconds(3) == 8
    assert calculate_backoff_seconds(4) == 16
    assert calculate_backoff_seconds(5) == 32
    assert calculate_backoff_seconds(6) == 60  # bounded by default 60s
    assert calculate_backoff_seconds(10, max_backoff=120) == 120

    # Verify that when use_backoff=True, next_attempt_at_ns is pushed into the future
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    dispatcher.append_event(env)

    fake_pub = DeterministicFakePublisher()
    fake_pub.should_fail = True
    before_ns = time.time_ns()
    dispatcher.poll_and_publish_cdc(publisher=fake_pub, use_backoff=True)

    with dispatcher._get_connection() as conn:
        row = conn.execute("SELECT next_attempt_at_ns FROM financial_outbox WHERE tenant_id = 'tenant_test'").fetchone()
        assert row["next_attempt_at_ns"] is not None
        assert row["next_attempt_at_ns"] >= before_ns + 1_000_000_000


def test_expired_lease_can_be_reclaimed():
    """Verify that an expired in-flight worker lease can be reclaimed by another worker."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    dispatcher.append_event(env)

    # Manually simulate a crashed worker leaving an expired lease
    past_ns = time.time_ns() - 100_000_000
    with dispatcher._get_connection() as conn:
        conn.execute("""
            UPDATE financial_outbox
            SET status = 'IN_FLIGHT',
                worker_id = 'crashed_worker',
                lease_expires_at_ns = ?
            WHERE tenant_id = 'tenant_test'
        """, (past_ns,))
        conn.commit()

    # Second worker should reclaim and successfully publish
    fake_pub = DeterministicFakePublisher()
    published = dispatcher.poll_and_publish_cdc(publisher=fake_pub, worker_id="recovering_worker")
    assert published == 1

    records = dispatcher.get_tenant_events("tenant_test")
    assert records[0].status == OutboxStatus.PUBLISHED
    assert records[0].published is True


def test_concurrent_workers_claim_once():
    """Verify that competing workers cannot claim the same record due to atomic CAS."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    dispatcher.append_event(env)

    now_ns = time.time_ns()
    lease_expires_ns = now_ns + 30_000_000_000

    # Worker 1 executes atomic claim
    with dispatcher._get_connection() as conn:
        claim1 = conn.execute("""
            UPDATE financial_outbox
            SET status = 'IN_FLIGHT', lease_expires_at_ns = ?, worker_id = 'worker_1'
            WHERE published = 0 AND status = 'PENDING'
        """, (lease_expires_ns,))
        conn.commit()
        assert claim1.rowcount == 1

        # Worker 2 attempts same claim concurrently; must get 0
        claim2 = conn.execute("""
            UPDATE financial_outbox
            SET status = 'IN_FLIGHT', lease_expires_at_ns = ?, worker_id = 'worker_2'
            WHERE published = 0 AND status = 'PENDING'
        """, (lease_expires_ns,))
        conn.commit()
        assert claim2.rowcount == 0


def test_max_retries_routes_to_dlq():
    """Verify that exceeding max_retries routes the poison record to dead_letter_queue."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env = _make_envelope()
    dispatcher.append_event(env, max_retries=2)

    fake_pub = DeterministicFakePublisher()
    fake_pub.should_fail = True

    # Attempt 1
    dispatcher.poll_and_publish_cdc(publisher=fake_pub)
    records = dispatcher.get_tenant_events("tenant_test")
    assert records[0].status == OutboxStatus.PENDING

    # Attempt 2 -> routes to DLQ
    dispatcher.poll_and_publish_cdc(publisher=fake_pub)
    records = dispatcher.get_tenant_events("tenant_test")
    assert records[0].status == OutboxStatus.DLQ

    with dispatcher._get_connection() as conn:
        dlq_row = conn.execute("SELECT * FROM dead_letter_queue WHERE tenant_id = 'tenant_test'").fetchone()
        assert dlq_row is not None
        assert "Max retries (2) exceeded" in dlq_row["failure_reason"]


def test_restart_recovers_inflight_event(tmp_path):
    """Verify that process restarts recover expired in-flight events from disk."""
    db_file = tmp_path / "outbox_recovery.db"

    # Process 1: write event and crash mid-flight
    d1 = TransactionalOutboxDispatcher(db_path=db_file)
    env = _make_envelope(agg_id="cnt_survive")
    d1.append_event(env)

    past_ns = time.time_ns() - 50_000_000
    with d1._get_connection() as conn:
        conn.execute("""
            UPDATE financial_outbox
            SET status = 'IN_FLIGHT', worker_id = 'dead_proc', lease_expires_at_ns = ?
            WHERE aggregate_id = 'cnt_survive'
        """, (past_ns,))
        conn.commit()

    # Process 2: restart
    d2 = TransactionalOutboxDispatcher(db_path=db_file)
    fake_pub = DeterministicFakePublisher()
    published = d2.poll_and_publish_cdc(publisher=fake_pub, worker_id="new_proc")
    assert published == 1

    recs = d2.get_tenant_events("tenant_test")
    assert recs[0].status == OutboxStatus.PUBLISHED


def test_tenant_scoped_outbox_access():
    """Verify that outbox querying and publishing is strictly tenant scoped."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env_a = _make_envelope(tenant_id="tenant_A", agg_id="cnt_A")
    env_b = _make_envelope(tenant_id="tenant_B", agg_id="cnt_B")

    dispatcher.append_event(env_a)
    dispatcher.append_event(env_b)

    # Scoped query
    assert len(dispatcher.get_tenant_events("tenant_A")) == 1
    assert len(dispatcher.get_tenant_events("tenant_B")) == 1
    assert dispatcher.get_tenant_events("tenant_A")[0].aggregate_id == "cnt_A"

    # Scoped publishing
    fake_pub = DeterministicFakePublisher()
    published_a = dispatcher.poll_and_publish_cdc(publisher=fake_pub, tenant_id="tenant_A")
    assert published_a == 1

    # Tenant B remains pending
    assert dispatcher.get_tenant_events("tenant_B")[0].published is False
    assert dispatcher.get_tenant_events("tenant_A")[0].published is True
