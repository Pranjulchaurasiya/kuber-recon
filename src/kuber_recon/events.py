"""
Layer 2: Event Sourcing & Transactional Outbox CDC
--------------------------------------------------
Standardized Financial Event Envelope and Transactional Outbox
pattern to guarantee Zero-Loss event streaming to Kafka / Razorpay Metro.
"""

from typing import Any, Dict, List, Optional
import uuid
import time
from pydantic import BaseModel, Field


class FinancialEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # e.g. 'escrow.held', 'lineage.reconciled', 'ledger.certified'
    schema_version: str = "1.0.0"
    tenant_id: str = "tenant_rzp_live_01"
    aggregate_id: str
    occurred_at_ns: int = Field(default_factory=lambda: int(time.time_ns()))
    correlation_id: str
    causation_id: Optional[str] = None
    idempotency_key: str
    payload: Dict[str, Any]


class OutboxRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    aggregate_id: str
    payload_json: str
    created_at_ns: int = Field(default_factory=lambda: int(time.time_ns()))
    published: bool = False
    published_at_ns: Optional[int] = None


class TransactionalOutboxDispatcher:
    """Simulates durable Postgres WAL CDC Outbox dispatcher."""

    def __init__(self):
        self._outbox: List[OutboxRecord] = []
        self._event_log: List[FinancialEventEnvelope] = []

    def stage_event(self, envelope: FinancialEventEnvelope) -> OutboxRecord:
        """Stage event inside atomic database transaction."""
        record = OutboxRecord(
            event_type=envelope.event_type,
            aggregate_id=envelope.aggregate_id,
            payload_json=envelope.model_dump_json(),
        )
        self._outbox.append(record)
        return record

    def poll_and_publish_cdc(self, batch_size: int = 100) -> int:
        """CDC Debezium worker polling outbox and publishing to Kafka / Metro."""
        pending = [r for r in self._outbox if not r.published][:batch_size]
        for record in pending:
            envelope = FinancialEventEnvelope.model_validate_json(record.payload_json)
            self._event_log.append(envelope)
            record.published = True
            record.published_at_ns = int(time.time_ns())
        return len(pending)

    @property
    def published_count(self) -> int:
        return len(self._event_log)
