"""Tests for Transactional Outbox, Publisher Interface, Retries, and DLQ routing.
"""

from pathlib import Path
import tempfile
import pytest
from kuber_recon.events import (
    DeterministicFakePublisher,
    FinancialEventEnvelope,
    KafkaTopicPublisher,
    OutboxStatus,
    TransactionalOutboxDispatcher,
)


def test_outbox_successful_publisher_acknowledgement():
    """Verify that an event is marked published ONLY when publisher acknowledges success."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    publisher = DeterministicFakePublisher()

    envelope = FinancialEventEnvelope(
        event_id="evt_ack_01",
        event_type="escrow.held",
        tenant_id="tenant_alpha",
        aggregate_id="contract_101",
        correlation_id="corr_101",
        idempotency_key="idem_ack_01",
        payload={"amount_paise": 100000},
    )
    rec = dispatcher.stage_event(envelope)
    assert rec.status == OutboxStatus.PENDING
    assert rec.published is False

    # Poll and publish with active publisher
    count = dispatcher.poll_and_publish_cdc(publisher=publisher, batch_size=10)
    assert count == 1
    assert dispatcher.published_count == 1
    assert dispatcher.pending_count == 0
    assert len(publisher.published_messages) == 1
    assert publisher.published_messages[0]["key"] == "contract_101"


def test_outbox_publisher_failure_and_retry_increment():
    """Verify that if publisher fails, event remains unpublished and retry_count is incremented."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    publisher = DeterministicFakePublisher()
    publisher.should_fail = True  # Simulate broker connection failure

    envelope = FinancialEventEnvelope(
        event_id="evt_fail_01",
        event_type="escrow.held",
        tenant_id="tenant_alpha",
        aggregate_id="contract_102",
        correlation_id="corr_102",
        idempotency_key="idem_fail_01",
        payload={"amount_paise": 200000},
    )
    dispatcher.stage_event(envelope)

    # First publish attempt fails
    count = dispatcher.poll_and_publish_cdc(publisher=publisher)
    assert count == 0
    assert dispatcher.published_count == 0
    assert dispatcher.pending_count == 1

    records = dispatcher.get_tenant_events("tenant_alpha")
    assert len(records) == 1
    assert records[0].retry_count == 1
    assert records[0].last_error == "Publisher acknowledgement failed"


def test_outbox_max_retries_routes_to_dlq():
    """Verify that reaching max_retries automatically quarantines record to Dead-Letter Queue."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    publisher = DeterministicFakePublisher()
    publisher.should_fail = True

    envelope = FinancialEventEnvelope(
        event_id="evt_poison_01",
        event_type="escrow.corrupted",
        tenant_id="tenant_alpha",
        aggregate_id="contract_poison",
        correlation_id="corr_poison",
        idempotency_key="idem_poison_01",
        payload={"corrupt": True},
    )
    dispatcher.stage_event(envelope)

    # Exhaust 5 retries
    for attempt in range(5):
        dispatcher.poll_and_publish_cdc(publisher=publisher)

    assert dispatcher.pending_count == 0
    assert dispatcher.published_count == 0
    assert dispatcher.dlq_count == 1

    records = dispatcher.get_tenant_events("tenant_alpha")
    assert records[0].status == OutboxStatus.DLQ


def test_outbox_process_restart_recovery():
    """Verify that unpublished events survive process restart and publish cleanly upon restart."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_file = Path(tmpdir) / "restart_outbox.db"

        # Session 1: Stage event
        d1 = TransactionalOutboxDispatcher(db_path=db_file)
        env = FinancialEventEnvelope(
            event_id="evt_restart_01",
            event_type="escrow.held",
            tenant_id="tenant_restart",
            aggregate_id="contract_restart",
            correlation_id="corr_restart",
            idempotency_key="idem_restart",
            payload={"amount_paise": 750000},
        )
        d1.stage_event(env)
        assert d1.pending_count == 1

        # Session 2: Fresh instance (simulating process restart)
        d2 = TransactionalOutboxDispatcher(db_path=db_file)
        assert d2.pending_count == 1
        assert d2.published_count == 0

        # Publish via d2
        pub = DeterministicFakePublisher()
        count = d2.poll_and_publish_cdc(publisher=pub)
        assert count == 1
        assert d2.published_count == 1
        assert d2.pending_count == 0


def test_outbox_tenant_scoping():
    """Verify that get_tenant_events returns events strictly scoped to caller's tenant."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    env_a = FinancialEventEnvelope(
        event_id="evt_a",
        event_type="escrow.held",
        tenant_id="tenant_A",
        aggregate_id="contract_A",
        correlation_id="corr_A",
        idempotency_key="idem_A",
        payload={},
    )
    env_b = FinancialEventEnvelope(
        event_id="evt_b",
        event_type="escrow.held",
        tenant_id="tenant_B",
        aggregate_id="contract_B",
        correlation_id="corr_B",
        idempotency_key="idem_B",
        payload={},
    )
    dispatcher.stage_event(env_a)
    dispatcher.stage_event(env_b)

    events_a = dispatcher.get_tenant_events("tenant_A")
    assert len(events_a) == 1
    assert events_a[0].aggregate_id == "contract_A"

    events_b = dispatcher.get_tenant_events("tenant_B")
    assert len(events_b) == 1
    assert events_b[0].aggregate_id == "contract_B"
