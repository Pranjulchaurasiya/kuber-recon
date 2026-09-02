"""Integration & Chaos Verification Suite for KuberRecon.
-------------------------------------------------------------------------------
1. Concurrent Webhook Deduplication Race Condition.
2. Concurrent CAS Release Settlement Contention.
3. Outbox Broker Disconnect, Retry Backoff, and Recovery.
4. Exact Zero-Paise Conservation Law under mixed settlement transactions.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import pytest
from kuber_recon.assurance import (
    AssuranceContract,
    ContractStatus,
)
from kuber_recon.events import (
    DeterministicFakePublisher,
    FinancialEventEnvelope,
    TransactionalOutboxDispatcher,
)
from kuber_recon.server import WebhookIdempotencyStore
from kuber_recon.storage import SQLiteStorageBackend
from kuber_recon.tax import IndianTaxKernel
from kuber_recon.types import PaymentMethod


@pytest.fixture
def isolated_store():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "chaos_isolated.db"
        backend = SQLiteStorageBackend(db_path)
        store = WebhookIdempotencyStore(backend=backend)
        yield store


def test_concurrent_webhook_deduplication_race_condition(isolated_store):
    """Chaos: 20 concurrent threads attempt to insert the same webhook event ID.
    Invariants: Exactly 1 succeeds in initial insertion; 19 report duplicate. Zero duplicate rows."""
    event_id = "evt_chaos_race_9999"

    def try_insert(worker_idx: int) -> bool:
        return isolated_store.try_insert(event_id)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(try_insert, range(20)))

    # Exactly 1 True, 19 False
    assert results.count(True) == 1
    assert results.count(False) == 19


def test_concurrent_cas_release_settlement_contention(isolated_store):
    """Chaos: Concurrent release attempts on the same held APEX contract.
    Invariant: Exactly one successful state transition occurs. Never double-released."""
    contract_id = "cnt_chaos_cas_contention_01"
    tenant_id = "merchant_rzp_primary"

    # 1. Create held contract in storage via save_contract
    contract = AssuranceContract(
        contract_id=contract_id,
        transfer_id="trf_chaos_01",
        account_id="acc_chaos_seller",
        seller_account_id="acc_chaos_seller",
        expected_record_count=100,
        on_hold_until=int(datetime.now(timezone.utc).timestamp()) + 3600,
        amount_paise=1000000,
        buyer_agent_id="buyer_chaos_agent",
        seller_agent_id="seller_chaos_agent",
        tenant_id=tenant_id,
        status=ContractStatus.HELD,
        on_hold=True,
        version=1,
    )
    isolated_store.save_contract(contract, tenant_id=tenant_id)

    # 2. Concurrently attempt transition to RELEASED
    def attempt_release(checker_id: str) -> bool:
        return isolated_store.transition_contract_state(
            contract_id=contract_id,
            expected_status=["HELD", "VERIFYING"],
            target_status="RELEASED",
            expected_version=1,
            tenant_id=tenant_id,
            assertions_passed=True,
            on_hold=False,
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(attempt_release, [f"checker_{i}" for i in range(5)]))

    # Exactly 1 worker succeeds with CAS version transition
    assert results.count(True) == 1
    assert results.count(False) == 4

    # Post-state check: contract is RELEASED at version 2
    final_contract = isolated_store.get_contract(contract_id, tenant_id=tenant_id)
    assert final_contract["status"] == "RELEASED"
    assert final_contract["version"] == 2
    assert final_contract["on_hold"] == 0


def test_outbox_broker_disconnect_and_recovery():
    """Chaos: Broker disconnects for 2 attempts, then recovers.
    Invariant: Zero messages lost, retry count tracks attempts, all published upon recovery."""
    dispatcher = TransactionalOutboxDispatcher(db_path=":memory:")
    publisher = DeterministicFakePublisher()
    publisher.attempts_before_success = 2  # Fails twice, succeeds on 3rd attempt

    env = FinancialEventEnvelope(
        event_id="evt_chaos_broker_recovery",
        event_type="settlement.reconciled",
        tenant_id="tenant_chaos",
        aggregate_id="agg_chaos_123",
        correlation_id="corr_chaos_123",
        idempotency_key="idem_chaos_broker_01",
        payload={"batch_size": 50},
    )
    dispatcher.stage_event(env)

    # Attempt 1: Broker failure
    count1 = dispatcher.poll_and_publish_cdc(publisher=publisher)
    assert count1 == 0
    assert dispatcher.published_count == 0

    # Attempt 2: Broker failure
    count2 = dispatcher.poll_and_publish_cdc(publisher=publisher)
    assert count2 == 0
    assert dispatcher.published_count == 0

    # Attempt 3: Broker recovered
    count3 = dispatcher.poll_and_publish_cdc(publisher=publisher)
    assert count3 == 1
    assert dispatcher.published_count == 1
    assert dispatcher.pending_count == 0
    assert len(publisher.published_messages) == 1


def test_exact_zero_paise_conservation_under_mixed_methods():
    """Mathematical Invariant: Across 400 mixed-method micro-transactions,
    every transaction strictly obeys Gross = Net + Fee + GST + TDS.
    Rounding variance is identically zero."""
    for amt in range(1000, 100000, 1000):
        for method in [PaymentMethod.UPI, PaymentMethod.NETBANKING, PaymentMethod.CARD_DEBIT, PaymentMethod.WALLET]:
            fee, gst, tds, net = IndianTaxKernel.calculate_line_deductions(amt, method)
            assert amt == fee + gst + tds + net, f"Conservation violation on amt={amt}, method={method}"
