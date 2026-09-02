"""Unified Storage Abstraction Layer for KuberRecon.
-------------------------------------------------------------------------------
Provides single, comprehensive persistence abstraction:
1. StorageBackend: Abstract base protocol covering:
   - Webhook idempotency & contract states with CAS versioning
   - Append-only audit logging with engine-level immutability
   - Capital advance facilities & split-sweep ledgers
   - Transactional outbox (PENDING -> IN_FLIGHT -> PUBLISHED) & DLQ
   - Manual review queue for dense clusters & ambiguities
2. SQLiteStorageBackend: High-concurrency WAL-mode SQLite for SANDBOX_DEMO.
3. PostgreSQLStorageBackend: Enterprise Aurora/PostgreSQL engine for STAGING/PRODUCTION
   with row-level locks (FOR UPDATE) and compound unique constraints.
4. Factory get_storage_backend(): Enforces fail-closed production readiness.
"""

from abc import ABC, abstractmethod
import contextlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from kuber_recon.config import EnvironmentMode, SecurityConfigError, config


class StorageBackend(ABC):
    """Abstract interface for KuberRecon state persistence."""

    # ── Webhook Idempotency ───────────────────────────────────────────────────
    @abstractmethod
    def try_insert_webhook_event(self, event_id: str) -> bool:
        """Insert processed webhook event id atomically. Return False on duplicate replay."""
        pass

    # ── Contracts & Audits ───────────────────────────────────────────────────
    @abstractmethod
    def insert_contract(
        self,
        contract_id: str,
        tenant_id: str,
        status: str,
        transfer_id: Optional[str],
        amount_paise: int,
        fee_paise: int,
        on_hold: bool,
        on_hold_until: Optional[int],
        settlement_id: Optional[str] = None,
        recipient_account: Optional[str] = None,
        expected_record_count: Optional[int] = None,
        buyer_agent_id: str = "",
        seller_agent_id: str = "",
        seller_account_id: str = "",
    ) -> bool:
        """Insert new escrow contract."""
        pass


    @abstractmethod
    def get_contract(self, contract_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve contract by ID with optional tenant boundary scoping."""
        pass

    @abstractmethod
    def get_contracts_by_status(self, status: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve contracts matching a specific status."""
        pass

    @abstractmethod
    def list_contracts(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve list of contracts."""
        pass

    @abstractmethod
    def transition_contract_state(
        self,
        contract_id: str,
        expected_status: Any,
        target_status: str,
        expected_version: Optional[int] = None,
        *,
        tenant_id: Optional[str] = None,
        transfer_id: Optional[str] = None,
        webhook_event_id: Optional[str] = None,
        on_hold: Optional[bool] = None,
        on_hold_until: Optional[int] = None,
        assertions_passed: Optional[bool] = None,
        refusal_reason: Optional[str] = None,
        proof_hash: Optional[str] = None,
        release_started_at: Optional[int] = None,
        expected_record_count: Optional[int] = None,
    ) -> bool:
        """Perform conditional CAS state transition and atomic audit log append."""
        pass

    @abstractmethod
    def list_audit_logs(self, contract_id: str) -> List[Dict[str, Any]]:
        """Retrieve append-only audit trail entries for a contract."""
        pass

    @abstractmethod
    def sweep_expired_contracts(self, tenant_id: Optional[str] = None) -> List[str]:
        """Transition expired active hold contracts to EXPIRED_HOLD."""
        pass

    # ── Capital Facilities & Sweeps ──────────────────────────────────────────
    @abstractmethod
    def insert_capital_facility(self, facility: Dict[str, Any]) -> bool:
        """Insert new working capital facility."""
        pass

    @abstractmethod
    def get_capital_facility(self, facility_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve capital facility by ID."""
        pass

    @abstractmethod
    def get_active_facility_for_merchant(self, merchant_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve any active/amortizing facility for a merchant."""
        pass

    @abstractmethod
    def list_capital_facilities(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all capital facilities with optional tenant scoping."""
        pass

    @abstractmethod
    def update_capital_facility_balance(
        self,
        facility_id: str,
        expected_version: int,
        new_balance_paise: int,
        new_status: str,
        last_settlement_at: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Atomic CAS update of remaining balance and status."""
        pass

    @abstractmethod
    def insert_repayment_event(self, event: Dict[str, Any]) -> bool:
        """Insert split-sweep repayment record."""
        pass

    @abstractmethod
    def list_repayment_events(self, facility_id: str) -> List[Dict[str, Any]]:
        """List repayment sweep history for a facility."""
        pass

    @abstractmethod
    def insert_capital_idempotency(self, key: str, tenant_id: str, facility_id: str, action: str, response_json: str) -> bool:
        """Insert capital idempotency key."""
        pass

    @abstractmethod
    def get_capital_idempotency(self, key: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached idempotency record."""
        pass

    @abstractmethod
    def reset_capital_facilities(self, tenant_id: Optional[str] = None) -> int:
        """Reset facilities for sandbox demo environment."""
        pass

    # ── Manual Review Queue ──────────────────────────────────────────────────
    @abstractmethod
    def insert_manual_review_record(self, record: Dict[str, Any]) -> bool:
        """Insert a quarantined transaction into manual review queue."""
        pass

    @abstractmethod
    def list_manual_review_records(self, tenant_id: Optional[str] = None, status: str = "PENDING") -> List[Dict[str, Any]]:
        """List manual review queue records."""
        pass

    @abstractmethod
    def resolve_manual_review_record(self, record_id: str, resolution: str, resolved_by: str, tenant_id: Optional[str] = None) -> bool:
        """Resolve a manual review record with operator notes."""
        pass

    # ── Transactional Outbox & DLQ ───────────────────────────────────────────
    @abstractmethod
    def insert_outbox_record(self, record: Dict[str, Any]) -> bool:
        """Insert outbox event in PENDING state."""
        pass

    @abstractmethod
    def get_outbox_record_by_idempotency(self, tenant_id: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Check for existing staged outbox event by idempotency key."""
        pass

    @abstractmethod
    def claim_pending_outbox_records(self, batch_size: int = 100, lease_seconds: int = 30, worker_id: str = "worker_01") -> List[Dict[str, Any]]:
        """Atomically claim pending outbox events into IN_FLIGHT state with lease duration."""
        pass

    @abstractmethod
    def mark_outbox_published(self, record_id: str) -> bool:
        """Mark outbox event as PUBLISHED upon explicit broker ACK."""
        pass

    @abstractmethod
    def mark_outbox_failed(self, record_id: str, error: str, retry_count: int, next_attempt_at_ns: int) -> bool:
        """Increment retry count, back off next attempt, and reset to PENDING."""
        pass

    @abstractmethod
    def insert_dlq_record(self, record: Dict[str, Any]) -> bool:
        """Quarantine poisoned event to DLQ."""
        pass

    @abstractmethod
    def list_dlq_records(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List dead letter queue records."""
        pass

    # ── Health Check ─────────────────────────────────────────────────────────
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Verify storage backend connectivity and responsiveness."""
        pass


class SQLiteStorageBackend(StorageBackend):
    """Local high-concurrency WAL-mode SQLite storage backend."""

    DEFAULT_DB_FILE = Path(__file__).parent / "kuber_idempotency.db"

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path and str(db_path) != ":memory:" else (db_path or self.DEFAULT_DB_FILE)
        self._lock = threading.RLock()
        self._mem_conn: Optional[sqlite3.Connection] = None
        if str(self.db_path) == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            # 1. Processed webhook events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    received_at INTEGER NOT NULL
                )
            """)

            # 2. APEX Escrow Contracts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS apex_contracts (
                    contract_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'merchant_rzp_primary',
                    buyer_agent_id TEXT NOT NULL DEFAULT '',
                    seller_agent_id TEXT NOT NULL DEFAULT '',
                    seller_account_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    payment_id TEXT,
                    transfer_id TEXT,
                    amount_paise INTEGER NOT NULL,
                    fee_paise INTEGER NOT NULL DEFAULT 0,
                    on_hold INTEGER NOT NULL,
                    on_hold_until INTEGER,
                    settlement_id TEXT,
                    recipient_account TEXT,
                    proof_hash TEXT,
                    assertions_passed INTEGER DEFAULT 0,
                    refusal_reason TEXT,
                    webhook_event_id TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 1,
                    release_started_at INTEGER,
                    expected_record_count INTEGER,
                    UNIQUE(tenant_id, contract_id)
                )
            """)

            # Safe migration checks for columns added to existing SQLite databases
            for col_sql in [
                "ALTER TABLE apex_contracts ADD COLUMN fee_paise INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE apex_contracts ADD COLUMN expected_record_count INTEGER",
                "ALTER TABLE apex_contracts ADD COLUMN release_started_at INTEGER",
                "ALTER TABLE apex_contracts ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'merchant_rzp_primary'",
            ]:
                try:
                    conn.execute(col_sql)
                except sqlite3.OperationalError:
                    pass

            # 3. Append-only audit trail with engine immutability

            conn.execute("""
                CREATE TABLE IF NOT EXISTS apex_contract_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    proof_hash TEXT,
                    assertions_passed INTEGER,
                    timestamp INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS abort_audit_log_update
                BEFORE UPDATE ON apex_contract_audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'apex_contract_audit_log is append-only: mutations prohibited');
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS abort_audit_log_delete
                BEFORE DELETE ON apex_contract_audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'apex_contract_audit_log is append-only: deletions prohibited');
                END;
            """)

            # 4. Capital Facilities & Sweeps
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capital_facilities (
                    facility_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT 'merchant_rzp_primary',
                    merchant_id TEXT NOT NULL,
                    principal_paise INTEGER NOT NULL,
                    factor_fee_paise INTEGER NOT NULL,
                    total_repayment_paise INTEGER NOT NULL,
                    remaining_balance_paise INTEGER NOT NULL,
                    sweep_rate TEXT NOT NULL,
                    status TEXT NOT NULL,
                    disbursed_at TEXT NOT NULL,
                    last_settlement_at TEXT NOT NULL,
                    payout_transfer_id TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(tenant_id, facility_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capital_repayment_events (
                    sweep_id TEXT PRIMARY KEY,
                    facility_id TEXT NOT NULL,
                    settlement_utr TEXT NOT NULL,
                    gross_settlement_paise INTEGER NOT NULL,
                    sweep_deduction_paise INTEGER NOT NULL,
                    net_merchant_payout_paise INTEGER NOT NULL,
                    remaining_balance_paise INTEGER NOT NULL,
                    applied_at TEXT NOT NULL,
                    FOREIGN KEY(facility_id) REFERENCES capital_facilities(facility_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capital_idempotency (
                    idempotency_key TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    facility_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, idempotency_key)
                )
            """)

            # 5. Financial Outbox & DLQ
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_outbox (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    published INTEGER NOT NULL DEFAULT 0,
                    published_at_ns INTEGER,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 5,
                    next_attempt_at_ns INTEGER,
                    lease_expires_at_ns INTEGER,
                    worker_id TEXT,
                    last_error TEXT,
                    UNIQUE(tenant_id, event_id),
                    UNIQUE(tenant_id, idempotency_key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id TEXT PRIMARY KEY,
                    original_event_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    failed_at_ns INTEGER NOT NULL,
                    failure_reason TEXT NOT NULL,
                    retry_attempts INTEGER NOT NULL
                )
            """)

            # 6. Manual Review Queue (Dense cluster truncations & collision traps)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS manual_review_queue (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    resolution_notes TEXT
                )
            """)

            # Indexing
            with contextlib.suppress(Exception):
                conn.execute("CREATE INDEX IF NOT EXISTS idx_apex_contracts_tenant_id ON apex_contracts(tenant_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_apex_contracts_tenant_status ON apex_contracts(tenant_id, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_apex_contracts_tenant_expiry ON apex_contracts(tenant_id, on_hold_until)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_fac_tenant_merch ON capital_facilities (tenant_id, merchant_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_fac_tenant_status ON capital_facilities (tenant_id, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_events_facility ON capital_repayment_events (facility_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_tenant_status ON financial_outbox (tenant_id, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_dlq_tenant ON dead_letter_queue (tenant_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_manual_review_status ON manual_review_queue (tenant_id, status)")

            conn.commit()

    # ── Webhook Idempotency ───────────────────────────────────────────────────
    def try_insert_webhook_event(self, event_id: str) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO processed_events (event_id, received_at) VALUES (?, ?)",
                    (event_id, int(time.time())),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    # ── Contracts ─────────────────────────────────────────────────────────────
    def insert_contract(
        self,
        contract_id: str,
        tenant_id: str,
        status: str,
        transfer_id: Optional[str],
        amount_paise: int,
        fee_paise: int,
        on_hold: bool,
        on_hold_until: Optional[int],
        settlement_id: Optional[str] = None,
        recipient_account: Optional[str] = None,
        expected_record_count: Optional[int] = None,
        buyer_agent_id: str = "",
        seller_agent_id: str = "",
        seller_account_id: str = "",
    ) -> bool:
        now = int(time.time())
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO apex_contracts (
                        contract_id, tenant_id, status, transfer_id, amount_paise,
                        fee_paise, on_hold, on_hold_until, settlement_id,
                        recipient_account, created_at, updated_at, version, expected_record_count,
                        buyer_agent_id, seller_agent_id, seller_account_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    contract_id, tenant_id, status, transfer_id, amount_paise,
                    fee_paise, 1 if on_hold else 0, on_hold_until, settlement_id,
                    recipient_account, now, now, expected_record_count,
                    buyer_agent_id, seller_agent_id, seller_account_id
                ))
                conn.execute("""
                    INSERT INTO apex_contract_audit_log (contract_id, status, proof_hash, assertions_passed, timestamp)
                    VALUES (?, ?, NULL, 0, ?)
                """, (contract_id, status, now))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False


    def get_contract(self, contract_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                row = conn.execute(
                    "SELECT * FROM apex_contracts WHERE contract_id = ? AND tenant_id = ?",
                    (contract_id, tenant_id),
                ).fetchone()
            else:
                row = conn.execute("SELECT * FROM apex_contracts WHERE contract_id = ?", (contract_id,)).fetchone()
            return dict(row) if row else None

    def get_contracts_by_status(self, status: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                rows = conn.execute(
                    "SELECT * FROM apex_contracts WHERE status = ? AND tenant_id = ?",
                    (status, tenant_id),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM apex_contracts WHERE status = ?", (status,)).fetchall()
            return [dict(r) for r in rows]

    def list_contracts(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                rows = conn.execute(
                    "SELECT * FROM apex_contracts WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                    (tenant_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM apex_contracts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def transition_contract_state(
        self,
        contract_id: str,
        expected_status: Any,
        target_status: str,
        expected_version: Optional[int] = None,
        *,
        tenant_id: Optional[str] = None,
        transfer_id: Optional[str] = None,
        webhook_event_id: Optional[str] = None,
        on_hold: Optional[bool] = None,
        on_hold_until: Optional[int] = None,
        assertions_passed: Optional[bool] = None,
        refusal_reason: Optional[str] = None,
        proof_hash: Optional[str] = None,
        release_started_at: Optional[int] = None,
        expected_record_count: Optional[int] = None,
    ) -> bool:
        now = int(time.time())
        with self._lock, self._connect() as conn:
            where_check = "SELECT version, status, proof_hash, assertions_passed, on_hold FROM apex_contracts WHERE contract_id = ?"
            params_check: List[Any] = [contract_id]
            if tenant_id is not None:
                where_check += " AND tenant_id = ?"
                params_check.append(tenant_id)
            cur = conn.execute(where_check, tuple(params_check))
            row = cur.fetchone()
            if not row:
                return False

            curr_ver, curr_status, curr_proof, curr_assertions, curr_on_hold = (
                row["version"], row["status"], row["proof_hash"], row["assertions_passed"], row["on_hold"]
            )

            if expected_version is not None and curr_ver != expected_version:
                return False

            if expected_status is not None:
                allowed = [expected_status] if isinstance(expected_status, str) else expected_status
                if curr_status not in allowed:
                    return False

            new_on_hold = 1 if on_hold else 0 if on_hold is not None else curr_on_hold
            new_proof = proof_hash if proof_hash is not None else curr_proof
            new_assertions = (1 if assertions_passed else 0) if assertions_passed is not None else curr_assertions

            set_clauses = [
                "status = ?",
                "updated_at = ?",
                "version = version + 1",
                "on_hold = ?",
                "proof_hash = ?",
                "assertions_passed = ?",
            ]
            update_params: List[Any] = [
                target_status,
                now,
                new_on_hold,
                new_proof,
                new_assertions,
            ]

            if transfer_id is not None:
                set_clauses.append("transfer_id = ?")
                update_params.append(transfer_id)
            if webhook_event_id is not None:
                set_clauses.append("webhook_event_id = ?")
                update_params.append(webhook_event_id)
            if on_hold_until is not None:
                set_clauses.append("on_hold_until = ?")
                update_params.append(on_hold_until)
            if refusal_reason is not None:
                set_clauses.append("refusal_reason = ?")
                update_params.append(refusal_reason)
            if release_started_at is not None:
                set_clauses.append("release_started_at = ?")
                update_params.append(release_started_at)
            if expected_record_count is not None:
                set_clauses.append("expected_record_count = ?")
                update_params.append(expected_record_count)

            update_params.extend([contract_id, curr_ver])
            update_sql = f"""
                UPDATE apex_contracts
                SET {', '.join(set_clauses)}
                WHERE contract_id = ? AND version = ?
            """
            cur = conn.execute(update_sql, tuple(update_params))
            if cur.rowcount != 1:
                return False

            conn.execute("""
                INSERT INTO apex_contract_audit_log (
                    contract_id, status, proof_hash, assertions_passed, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (contract_id, target_status, new_proof, new_assertions, now))
            conn.commit()
            return True

    def list_audit_logs(self, contract_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM apex_contract_audit_log WHERE contract_id = ? ORDER BY timestamp ASC, id ASC",
                (contract_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def sweep_expired_contracts(self, tenant_id: Optional[str] = None) -> List[str]:
        now = int(time.time())
        with self._lock, self._connect() as conn:
            sql = "SELECT contract_id, version FROM apex_contracts WHERE status = 'HELD' AND on_hold_until < ?"
            params: List[Any] = [now]
            if tenant_id:
                sql += " AND tenant_id = ?"
                params.append(tenant_id)
            rows = conn.execute(sql, tuple(params)).fetchall()
            expired = []
            for r in rows:
                cid, ver = r["contract_id"], r["version"]
                ok = self.transition_contract_state(
                    contract_id=cid,
                    expected_status="HELD",
                    target_status="EXPIRED_HOLD",
                    expected_version=ver,
                    tenant_id=tenant_id,
                    on_hold=True,
                )
                if ok:
                    expired.append(cid)
            return expired

    # ── Capital Facilities ────────────────────────────────────────────────────
    def insert_capital_facility(self, facility: Dict[str, Any]) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO capital_facilities (
                        facility_id, tenant_id, merchant_id, principal_paise, factor_fee_paise,
                        total_repayment_paise, remaining_balance_paise, sweep_rate, status,
                        disbursed_at, last_settlement_at, payout_transfer_id, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    facility["facility_id"],
                    facility.get("tenant_id", "merchant_rzp_primary"),
                    facility["merchant_id"],
                    facility["principal_paise"],
                    facility["factor_fee_paise"],
                    facility["total_repayment_paise"],
                    facility["remaining_balance_paise"],
                    str(facility["sweep_rate"]),
                    facility["status"],
                    facility["disbursed_at"],
                    facility["last_settlement_at"],
                    facility["payout_transfer_id"],
                    facility.get("version", 1),
                    now,
                    now,
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_capital_facility(self, facility_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                row = conn.execute(
                    "SELECT * FROM capital_facilities WHERE facility_id = ? AND tenant_id = ?",
                    (facility_id, tenant_id),
                ).fetchone()
            else:
                row = conn.execute("SELECT * FROM capital_facilities WHERE facility_id = ?", (facility_id,)).fetchone()
            return dict(row) if row else None

    def get_active_facility_for_merchant(self, merchant_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM capital_facilities
                WHERE tenant_id = ? AND merchant_id = ? AND status IN ('ACTIVE', 'AMORTIZING', 'STAGNANT_RECOVERY')
                LIMIT 1
            """, (tenant_id, merchant_id)).fetchone()
            return dict(row) if row else None

    def list_capital_facilities(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                rows = conn.execute("SELECT * FROM capital_facilities WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM capital_facilities ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_capital_facility_balance(
        self,
        facility_id: str,
        expected_version: int,
        new_balance_paise: int,
        new_status: str,
        last_settlement_at: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            sql = """
                UPDATE capital_facilities
                SET remaining_balance_paise = ?, status = ?, last_settlement_at = ?, version = version + 1, updated_at = ?
                WHERE facility_id = ? AND version = ?
            """
            params: List[Any] = [new_balance_paise, new_status, last_settlement_at, now, facility_id, expected_version]
            if tenant_id:
                sql = """
                    UPDATE capital_facilities
                    SET remaining_balance_paise = ?, status = ?, last_settlement_at = ?, version = version + 1, updated_at = ?
                    WHERE facility_id = ? AND version = ? AND tenant_id = ?
                """
                params.append(tenant_id)
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount == 1

    def insert_repayment_event(self, event: Dict[str, Any]) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO capital_repayment_events (
                        sweep_id, facility_id, settlement_utr, gross_settlement_paise,
                        sweep_deduction_paise, net_merchant_payout_paise, remaining_balance_paise, applied_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event["sweep_id"],
                    event["facility_id"],
                    event["settlement_utr"],
                    event["gross_settlement_paise"],
                    event["sweep_deduction_paise"],
                    event["net_merchant_payout_paise"],
                    event["remaining_balance_paise"],
                    event["applied_at"],
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def list_repayment_events(self, facility_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM capital_repayment_events WHERE facility_id = ? ORDER BY applied_at ASC",
                (facility_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def insert_capital_idempotency(self, key: str, tenant_id: str, facility_id: str, action: str, response_json: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO capital_idempotency (idempotency_key, tenant_id, facility_id, action, response_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (key, tenant_id, facility_id, action, response_json, now))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_capital_idempotency(self, key: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM capital_idempotency WHERE idempotency_key = ? AND tenant_id = ?",
                (key, tenant_id),
            ).fetchone()
            return dict(row) if row else None

    def reset_capital_facilities(self, tenant_id: Optional[str] = None) -> int:
        with self._lock, self._connect() as conn:
            if tenant_id:
                cur = conn.execute("DELETE FROM capital_facilities WHERE tenant_id = ?", (tenant_id,))
                conn.execute("DELETE FROM capital_repayment_events WHERE facility_id NOT IN (SELECT facility_id FROM capital_facilities)")
                conn.execute("DELETE FROM capital_idempotency WHERE tenant_id = ?", (tenant_id,))
            else:
                cur = conn.execute("DELETE FROM capital_facilities")
                conn.execute("DELETE FROM capital_repayment_events")
                conn.execute("DELETE FROM capital_idempotency")
            conn.commit()
            return cur.rowcount

    # ── Manual Review Queue ──────────────────────────────────────────────────
    def insert_manual_review_record(self, record: Dict[str, Any]) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO manual_review_queue (id, tenant_id, category, reason, details_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                """, (
                    record["id"],
                    record.get("tenant_id", "merchant_rzp_primary"),
                    record["category"],
                    record["reason"],
                    record.get("details_json", "{}"),
                    now,
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def list_manual_review_records(self, tenant_id: Optional[str] = None, status: str = "PENDING") -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                rows = conn.execute(
                    "SELECT * FROM manual_review_queue WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC",
                    (tenant_id, status),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM manual_review_queue WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            return [dict(r) for r in rows]

    def resolve_manual_review_record(self, record_id: str, resolution: str, resolved_by: str, tenant_id: Optional[str] = None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            sql = """
                UPDATE manual_review_queue
                SET status = 'RESOLVED', resolved_at = ?, resolved_by = ?, resolution_notes = ?
                WHERE id = ?
            """
            params: List[Any] = [now, resolved_by, resolution, record_id]
            if tenant_id:
                sql += " AND tenant_id = ?"
                params.append(tenant_id)
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount == 1

    # ── Transactional Outbox & DLQ ───────────────────────────────────────────
    def insert_outbox_record(self, record: Dict[str, Any]) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO financial_outbox (
                        id, tenant_id, event_id, event_type, aggregate_id,
                        idempotency_key, payload_json, created_at_ns, status, published, max_retries
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?)
                """, (
                    record["id"],
                    record["tenant_id"],
                    record["event_id"],
                    record["event_type"],
                    record["aggregate_id"],
                    record["idempotency_key"],
                    record["payload_json"],
                    record["created_at_ns"],
                    record.get("max_retries", 5),
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_outbox_record_by_idempotency(self, tenant_id: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM financial_outbox WHERE tenant_id = ? AND idempotency_key = ?
            """, (tenant_id, idempotency_key)).fetchone()
            return dict(row) if row else None

    def claim_pending_outbox_records(self, batch_size: int = 100, lease_seconds: int = 30, worker_id: str = "worker_01") -> List[Dict[str, Any]]:
        now_ns = int(time.time_ns())
        lease_expires_ns = now_ns + int(lease_seconds * 1e9)
        with self._lock, self._connect() as conn:
            # Select pending records where next_attempt is due, or stale in_flight records whose lease expired
            rows = conn.execute("""
                SELECT id, tenant_id, event_id, event_type, aggregate_id, payload_json, retry_count, max_retries
                FROM financial_outbox
                WHERE published = 0 AND status != 'DLQ'
                  AND ((status = 'PENDING' AND (next_attempt_at_ns IS NULL OR next_attempt_at_ns <= ?))
                    OR (status = 'IN_FLIGHT' AND lease_expires_at_ns < ?))
                ORDER BY created_at_ns ASC
                LIMIT ?
            """, (now_ns, now_ns, batch_size)).fetchall()

            claimed = []
            for r in rows:
                rec_id = r["id"]
                # Atomically claim with worker lease
                cur = conn.execute("""
                    UPDATE financial_outbox
                    SET status = 'IN_FLIGHT', lease_expires_at_ns = ?, worker_id = ?
                    WHERE id = ? AND (status = 'PENDING' OR (status = 'IN_FLIGHT' AND lease_expires_at_ns < ?))
                """, (lease_expires_ns, worker_id, rec_id, now_ns))
                if cur.rowcount == 1:
                    claimed.append(dict(r))
            conn.commit()
            return claimed

    def mark_outbox_published(self, record_id: str) -> bool:
        now_ns = int(time.time_ns())
        with self._lock, self._connect() as conn:
            cur = conn.execute("""
                UPDATE financial_outbox
                SET published = 1, status = 'PUBLISHED', published_at_ns = ?, last_error = NULL
                WHERE id = ? AND status = 'IN_FLIGHT'
            """, (now_ns, record_id))
            conn.commit()
            return cur.rowcount == 1

    def mark_outbox_failed(self, record_id: str, error: str, retry_count: int, next_attempt_at_ns: int) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute("""
                UPDATE financial_outbox
                SET status = 'PENDING', retry_count = ?, next_attempt_at_ns = ?, last_error = ?
                WHERE id = ?
            """, (retry_count, next_attempt_at_ns, error, record_id))
            conn.commit()
            return cur.rowcount == 1

    def insert_dlq_record(self, record: Dict[str, Any]) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO dead_letter_queue (
                        id, original_event_id, tenant_id, event_type, aggregate_id,
                        payload_json, failed_at_ns, failure_reason, retry_attempts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["id"],
                    record["original_event_id"],
                    record["tenant_id"],
                    record["event_type"],
                    record["aggregate_id"],
                    record["payload_json"],
                    record["failed_at_ns"],
                    record["failure_reason"],
                    record["retry_attempts"],
                ))
                # Update outbox status to DLQ
                conn.execute("""
                    UPDATE financial_outbox
                    SET status = 'DLQ', last_error = ?
                    WHERE id = ? OR event_id = ?
                """, (record["failure_reason"], record.get("outbox_id", ""), record["original_event_id"]))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def list_dlq_records(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            if tenant_id:
                rows = conn.execute("SELECT * FROM dead_letter_queue WHERE tenant_id = ? ORDER BY failed_at_ns DESC", (tenant_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM dead_letter_queue ORDER BY failed_at_ns DESC").fetchall()
            return [dict(r) for r in rows]

    def health_check(self) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            cur = conn.execute("SELECT 1 AS alive")
            alive = cur.fetchone()["alive"] == 1
            cur_events = conn.execute("SELECT COUNT(*) AS c FROM processed_events").fetchone()["c"]
            cur_contracts = conn.execute("SELECT COUNT(*) AS c FROM apex_contracts").fetchone()["c"]
            cur_facilities = conn.execute("SELECT COUNT(*) AS c FROM capital_facilities").fetchone()["c"]
            cur_outbox = conn.execute("SELECT COUNT(*) AS c FROM financial_outbox WHERE status = 'PENDING'").fetchone()["c"]
            return {
                "backend": "SQLite (WAL Mode)",
                "status": "connected" if alive else "error",
                "processed_events_count": cur_events,
                "contracts_count": cur_contracts,
                "facilities_count": cur_facilities,
                "pending_outbox_count": cur_outbox,
            }


class PostgreSQLStorageBackend(StorageBackend):
    """Enterprise PostgreSQL / Amazon Aurora storage backend with row-level locks."""

    def __init__(self, database_url: str, db_connection: Optional[Any] = None):
        self.database_url = database_url
        self._injected_conn = db_connection
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        if self._injected_conn is not None:
            return self._injected_conn
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            conn.autocommit = False
            return conn
        except ImportError:
            raise SecurityConfigError(
                "psycopg2 is required for PostgreSQLStorageBackend. Run: pip install psycopg2-binary"
            )

    def _init_db(self) -> None:
        """Create PostgreSQL tables with row-level lock readiness and compound unique constraints."""
        if self._injected_conn is None and "postgres" in self.database_url:
            # Skip remote network attempt in unit tests unless live PostgreSQL is connected
            return

        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS processed_events (
                        event_id VARCHAR(255) PRIMARY KEY,
                        received_at BIGINT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS apex_contracts (
                        contract_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL DEFAULT 'merchant_rzp_primary',
                        buyer_agent_id VARCHAR(255) NOT NULL DEFAULT '',
                        seller_agent_id VARCHAR(255) NOT NULL DEFAULT '',
                        seller_account_id VARCHAR(255) NOT NULL DEFAULT '',
                        status VARCHAR(64) NOT NULL,
                        payment_id VARCHAR(255),
                        transfer_id VARCHAR(255),
                        amount_paise BIGINT NOT NULL,
                        fee_paise BIGINT NOT NULL DEFAULT 0,
                        on_hold BOOLEAN NOT NULL,
                        on_hold_until BIGINT,
                        settlement_id VARCHAR(255),
                        recipient_account VARCHAR(255),
                        proof_hash VARCHAR(255),
                        assertions_passed INTEGER DEFAULT 0,
                        refusal_reason TEXT,
                        webhook_event_id VARCHAR(255),
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL,
                        version BIGINT NOT NULL DEFAULT 1,
                        release_started_at BIGINT,
                        expected_record_count INTEGER,
                        CONSTRAINT uq_tenant_contract UNIQUE(tenant_id, contract_id)
                    );
                    CREATE TABLE IF NOT EXISTS apex_contract_audit_log (
                        id BIGSERIAL PRIMARY KEY,
                        contract_id VARCHAR(255) NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        proof_hash VARCHAR(255),
                        assertions_passed INTEGER,
                        timestamp BIGINT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS capital_facilities (
                        facility_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL DEFAULT 'merchant_rzp_primary',
                        merchant_id VARCHAR(255) NOT NULL,
                        principal_paise BIGINT NOT NULL,
                        factor_fee_paise BIGINT NOT NULL,
                        total_repayment_paise BIGINT NOT NULL,
                        remaining_balance_paise BIGINT NOT NULL,
                        sweep_rate VARCHAR(32) NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        disbursed_at VARCHAR(64) NOT NULL,
                        last_settlement_at VARCHAR(64) NOT NULL,
                        payout_transfer_id VARCHAR(255) NOT NULL,
                        version BIGINT NOT NULL DEFAULT 1,
                        created_at VARCHAR(64) NOT NULL,
                        updated_at VARCHAR(64) NOT NULL,
                        CONSTRAINT uq_tenant_facility UNIQUE(tenant_id, facility_id)
                    );
                    CREATE TABLE IF NOT EXISTS capital_repayment_events (
                        sweep_id VARCHAR(255) PRIMARY KEY,
                        facility_id VARCHAR(255) NOT NULL,
                        settlement_utr VARCHAR(255) NOT NULL,
                        gross_settlement_paise BIGINT NOT NULL,
                        sweep_deduction_paise BIGINT NOT NULL,
                        net_merchant_payout_paise BIGINT NOT NULL,
                        remaining_balance_paise BIGINT NOT NULL,
                        applied_at VARCHAR(64) NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS capital_idempotency (
                        idempotency_key VARCHAR(255) NOT NULL,
                        tenant_id VARCHAR(255) NOT NULL,
                        facility_id VARCHAR(255) NOT NULL,
                        action VARCHAR(64) NOT NULL,
                        response_json TEXT NOT NULL,
                        created_at VARCHAR(64) NOT NULL,
                        PRIMARY KEY (tenant_id, idempotency_key)
                    );
                    CREATE TABLE IF NOT EXISTS financial_outbox (
                        id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL,
                        event_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(255) NOT NULL,
                        aggregate_id VARCHAR(255) NOT NULL,
                        idempotency_key VARCHAR(255) NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at_ns BIGINT NOT NULL,
                        status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
                        published INTEGER NOT NULL DEFAULT 0,
                        published_at_ns BIGINT,
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        max_retries INTEGER NOT NULL DEFAULT 5,
                        next_attempt_at_ns BIGINT,
                        lease_expires_at_ns BIGINT,
                        worker_id VARCHAR(255),
                        last_error TEXT,
                        CONSTRAINT uq_outbox_tenant_event UNIQUE(tenant_id, event_id),
                        CONSTRAINT uq_outbox_tenant_idemp UNIQUE(tenant_id, idempotency_key)
                    );
                    CREATE TABLE IF NOT EXISTS dead_letter_queue (
                        id VARCHAR(255) PRIMARY KEY,
                        original_event_id VARCHAR(255) NOT NULL,
                        tenant_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(255) NOT NULL,
                        aggregate_id VARCHAR(255) NOT NULL,
                        payload_json TEXT NOT NULL,
                        failed_at_ns BIGINT NOT NULL,
                        failure_reason TEXT NOT NULL,
                        retry_attempts INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS manual_review_queue (
                        id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL,
                        category VARCHAR(255) NOT NULL,
                        reason TEXT NOT NULL,
                        details_json TEXT NOT NULL,
                        status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
                        created_at VARCHAR(64) NOT NULL,
                        resolved_at VARCHAR(64),
                        resolved_by VARCHAR(255),
                        resolution_notes TEXT
                    );
                """)
            conn.commit()

    def try_insert_webhook_event(self, event_id: str) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO processed_events (event_id, received_at) VALUES (%s, %s)",
                        (event_id, int(time.time())),
                    )
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def insert_contract(
        self,
        contract_id: str,
        tenant_id: str,
        status: str,
        transfer_id: Optional[str],
        amount_paise: int,
        fee_paise: int,
        on_hold: bool,
        on_hold_until: Optional[int],
        settlement_id: Optional[str] = None,
        recipient_account: Optional[str] = None,
        expected_record_count: Optional[int] = None,
        buyer_agent_id: str = "",
        seller_agent_id: str = "",
        seller_account_id: str = "",
    ) -> bool:
        now = int(time.time())
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO apex_contracts (
                            contract_id, tenant_id, status, transfer_id, amount_paise,
                            fee_paise, on_hold, on_hold_until, settlement_id,
                            recipient_account, created_at, updated_at, version, expected_record_count,
                            buyer_agent_id, seller_agent_id, seller_account_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s)
                    """, (
                        contract_id, tenant_id, status, transfer_id, amount_paise,
                        fee_paise, on_hold, on_hold_until, settlement_id,
                        recipient_account, now, now, expected_record_count,
                        buyer_agent_id, seller_agent_id, seller_account_id
                    ))
                    cur.execute("""
                        INSERT INTO apex_contract_audit_log (contract_id, status, proof_hash, assertions_passed, timestamp)
                        VALUES (%s, %s, NULL, 0, %s)
                    """, (contract_id, status, now))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False


    def get_contract(self, contract_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM apex_contracts WHERE contract_id = %s AND tenant_id = %s", (contract_id, tenant_id))
                else:
                    cur.execute("SELECT * FROM apex_contracts WHERE contract_id = %s", (contract_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def get_contracts_by_status(self, status: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM apex_contracts WHERE status = %s AND tenant_id = %s", (status, tenant_id))
                else:
                    cur.execute("SELECT * FROM apex_contracts WHERE status = %s", (status,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def list_contracts(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM apex_contracts WHERE tenant_id = %s ORDER BY created_at DESC LIMIT %s", (tenant_id, limit))
                else:
                    cur.execute("SELECT * FROM apex_contracts ORDER BY created_at DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def transition_contract_state(
        self,
        contract_id: str,
        expected_status: Any,
        target_status: str,
        expected_version: Optional[int] = None,
        *,
        tenant_id: Optional[str] = None,
        transfer_id: Optional[str] = None,
        webhook_event_id: Optional[str] = None,
        on_hold: Optional[bool] = None,
        on_hold_until: Optional[int] = None,
        assertions_passed: Optional[bool] = None,
        refusal_reason: Optional[str] = None,
        proof_hash: Optional[str] = None,
        release_started_at: Optional[int] = None,
        expected_record_count: Optional[int] = None,
    ) -> bool:
        now = int(time.time())
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    where_check = "SELECT version, status, proof_hash, assertions_passed, on_hold FROM apex_contracts WHERE contract_id = %s FOR UPDATE"
                    params_check: List[Any] = [contract_id]
                    if tenant_id is not None:
                        where_check += " AND tenant_id = %s"
                        params_check.append(tenant_id)
                    cur.execute(where_check, tuple(params_check))
                    row = cur.fetchone()
                    if not row:
                        conn.rollback()
                        return False

                    curr_ver = row["version"]
                    curr_status = row["status"]
                    curr_proof = row["proof_hash"]
                    curr_assertions = row["assertions_passed"]
                    curr_on_hold = row["on_hold"]

                    if expected_version is not None and curr_ver != expected_version:
                        conn.rollback()
                        return False

                    if expected_status is not None:
                        allowed = [expected_status] if isinstance(expected_status, str) else expected_status
                        if curr_status not in allowed:
                            conn.rollback()
                            return False

                    new_on_hold = on_hold if on_hold is not None else curr_on_hold
                    new_proof = proof_hash if proof_hash is not None else curr_proof
                    new_assertions = (1 if assertions_passed else 0) if assertions_passed is not None else curr_assertions

                    set_clauses = [
                        "status = %s",
                        "updated_at = %s",
                        "version = version + 1",
                        "on_hold = %s",
                        "proof_hash = %s",
                        "assertions_passed = %s",
                    ]
                    update_params: List[Any] = [target_status, now, new_on_hold, new_proof, new_assertions]

                    if transfer_id is not None:
                        set_clauses.append("transfer_id = %s")
                        update_params.append(transfer_id)
                    if webhook_event_id is not None:
                        set_clauses.append("webhook_event_id = %s")
                        update_params.append(webhook_event_id)
                    if on_hold_until is not None:
                        set_clauses.append("on_hold_until = %s")
                        update_params.append(on_hold_until)
                    if refusal_reason is not None:
                        set_clauses.append("refusal_reason = %s")
                        update_params.append(refusal_reason)
                    if release_started_at is not None:
                        set_clauses.append("release_started_at = %s")
                        update_params.append(release_started_at)
                    if expected_record_count is not None:
                        set_clauses.append("expected_record_count = %s")
                        update_params.append(expected_record_count)

                    update_params.extend([contract_id, curr_ver])
                    update_sql = f"UPDATE apex_contracts SET {', '.join(set_clauses)} WHERE contract_id = %s AND version = %s"
                    cur.execute(update_sql, tuple(update_params))
                    if cur.rowcount != 1:
                        conn.rollback()
                        return False

                    cur.execute("""
                        INSERT INTO apex_contract_audit_log (contract_id, status, proof_hash, assertions_passed, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (contract_id, target_status, new_proof, new_assertions, now))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def list_audit_logs(self, contract_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM apex_contract_audit_log WHERE contract_id = %s ORDER BY timestamp ASC, id ASC", (contract_id,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def sweep_expired_contracts(self, tenant_id: Optional[str] = None) -> List[str]:
        now = int(time.time())
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                sql = "SELECT contract_id, version FROM apex_contracts WHERE status = 'HELD' AND on_hold_until < %s"
                params: List[Any] = [now]
                if tenant_id:
                    sql += " AND tenant_id = %s"
                    params.append(tenant_id)
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                expired = []
                for r in rows:
                    cid, ver = r["contract_id"], r["version"]
                    ok = self.transition_contract_state(
                        contract_id=cid,
                        expected_status="HELD",
                        target_status="EXPIRED_HOLD",
                        expected_version=ver,
                        tenant_id=tenant_id,
                        on_hold=True,
                    )
                    if ok:
                        expired.append(cid)
                return expired

    # ── Capital Facilities ────────────────────────────────────────────────────
    def insert_capital_facility(self, facility: Dict[str, Any]) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO capital_facilities (
                            facility_id, tenant_id, merchant_id, principal_paise, factor_fee_paise,
                            total_repayment_paise, remaining_balance_paise, sweep_rate, status,
                            disbursed_at, last_settlement_at, payout_transfer_id, version, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        facility["facility_id"],
                        facility.get("tenant_id", "merchant_rzp_primary"),
                        facility["merchant_id"],
                        facility["principal_paise"],
                        facility["factor_fee_paise"],
                        facility["total_repayment_paise"],
                        facility["remaining_balance_paise"],
                        str(facility["sweep_rate"]),
                        facility["status"],
                        facility["disbursed_at"],
                        facility["last_settlement_at"],
                        facility["payout_transfer_id"],
                        facility.get("version", 1),
                        now,
                        now,
                    ))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def get_capital_facility(self, facility_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM capital_facilities WHERE facility_id = %s AND tenant_id = %s", (facility_id, tenant_id))
                else:
                    cur.execute("SELECT * FROM capital_facilities WHERE facility_id = %s", (facility_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def get_active_facility_for_merchant(self, merchant_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM capital_facilities
                    WHERE tenant_id = %s AND merchant_id = %s AND status IN ('ACTIVE', 'AMORTIZING', 'STAGNANT_RECOVERY')
                    LIMIT 1
                """, (tenant_id, merchant_id))
                row = cur.fetchone()
                return dict(row) if row else None

    def list_capital_facilities(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM capital_facilities WHERE tenant_id = %s ORDER BY created_at DESC", (tenant_id,))
                else:
                    cur.execute("SELECT * FROM capital_facilities ORDER BY created_at DESC")
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def update_capital_facility_balance(
        self,
        facility_id: str,
        expected_version: int,
        new_balance_paise: int,
        new_status: str,
        last_settlement_at: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    sql = """
                        UPDATE capital_facilities
                        SET remaining_balance_paise = %s, status = %s, last_settlement_at = %s, version = version + 1, updated_at = %s
                        WHERE facility_id = %s AND version = %s
                    """
                    params: List[Any] = [new_balance_paise, new_status, last_settlement_at, now, facility_id, expected_version]
                    if tenant_id:
                        sql = """
                            UPDATE capital_facilities
                            SET remaining_balance_paise = %s, status = %s, last_settlement_at = %s, version = version + 1, updated_at = %s
                            WHERE facility_id = %s AND version = %s AND tenant_id = %s
                        """
                        params.append(tenant_id)
                    cur.execute(sql, tuple(params))
                    conn.commit()
                    return cur.rowcount == 1
            except Exception:
                conn.rollback()
                return False

    def insert_repayment_event(self, event: Dict[str, Any]) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO capital_repayment_events (
                            sweep_id, facility_id, settlement_utr, gross_settlement_paise,
                            sweep_deduction_paise, net_merchant_payout_paise, remaining_balance_paise, applied_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        event["sweep_id"],
                        event["facility_id"],
                        event["settlement_utr"],
                        event["gross_settlement_paise"],
                        event["sweep_deduction_paise"],
                        event["net_merchant_payout_paise"],
                        event["remaining_balance_paise"],
                        event["applied_at"],
                    ))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def list_repayment_events(self, facility_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM capital_repayment_events WHERE facility_id = %s ORDER BY applied_at ASC", (facility_id,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def insert_capital_idempotency(self, key: str, tenant_id: str, facility_id: str, action: str, response_json: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO capital_idempotency (idempotency_key, tenant_id, facility_id, action, response_json, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (key, tenant_id, facility_id, action, response_json, now))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def get_capital_idempotency(self, key: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM capital_idempotency WHERE idempotency_key = %s AND tenant_id = %s", (key, tenant_id))
                row = cur.fetchone()
                return dict(row) if row else None

    def reset_capital_facilities(self, tenant_id: Optional[str] = None) -> int:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    if tenant_id:
                        cur.execute("DELETE FROM capital_facilities WHERE tenant_id = %s", (tenant_id,))
                        cnt = cur.rowcount
                        cur.execute("DELETE FROM capital_repayment_events WHERE facility_id NOT IN (SELECT facility_id FROM capital_facilities)")
                        cur.execute("DELETE FROM capital_idempotency WHERE tenant_id = %s", (tenant_id,))
                    else:
                        cur.execute("DELETE FROM capital_facilities")
                        cnt = cur.rowcount
                        cur.execute("DELETE FROM capital_repayment_events")
                        cur.execute("DELETE FROM capital_idempotency")
                conn.commit()
                return cnt
            except Exception:
                conn.rollback()
                return 0

    # ── Manual Review Queue ──────────────────────────────────────────────────
    def insert_manual_review_record(self, record: Dict[str, Any]) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO manual_review_queue (id, tenant_id, category, reason, details_json, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, 'PENDING', %s)
                    """, (
                        record["id"],
                        record.get("tenant_id", "merchant_rzp_primary"),
                        record["category"],
                        record["reason"],
                        record.get("details_json", "{}"),
                        now,
                    ))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def list_manual_review_records(self, tenant_id: Optional[str] = None, status: str = "PENDING") -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM manual_review_queue WHERE tenant_id = %s AND status = %s ORDER BY created_at DESC", (tenant_id, status))
                else:
                    cur.execute("SELECT * FROM manual_review_queue WHERE status = %s ORDER BY created_at DESC", (status,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def resolve_manual_review_record(self, record_id: str, resolution: str, resolved_by: str, tenant_id: Optional[str] = None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    sql = "UPDATE manual_review_queue SET status = 'RESOLVED', resolved_at = %s, resolved_by = %s, resolution_notes = %s WHERE id = %s"
                    params: List[Any] = [now, resolved_by, resolution, record_id]
                    if tenant_id:
                        sql += " AND tenant_id = %s"
                        params.append(tenant_id)
                    cur.execute(sql, tuple(params))
                    conn.commit()
                    return cur.rowcount == 1
            except Exception:
                conn.rollback()
                return False

    # ── Transactional Outbox & DLQ ───────────────────────────────────────────
    def insert_outbox_record(self, record: Dict[str, Any]) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO financial_outbox (
                            id, tenant_id, event_id, event_type, aggregate_id,
                            idempotency_key, payload_json, created_at_ns, status, published, max_retries
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', 0, %s)
                    """, (
                        record["id"],
                        record["tenant_id"],
                        record["event_id"],
                        record["event_type"],
                        record["aggregate_id"],
                        record["idempotency_key"],
                        record["payload_json"],
                        record["created_at_ns"],
                        record.get("max_retries", 5),
                    ))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def get_outbox_record_by_idempotency(self, tenant_id: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM financial_outbox WHERE tenant_id = %s AND idempotency_key = %s", (tenant_id, idempotency_key))
                row = cur.fetchone()
                return dict(row) if row else None

    def claim_pending_outbox_records(self, batch_size: int = 100, lease_seconds: int = 30, worker_id: str = "worker_01") -> List[Dict[str, Any]]:
        now_ns = int(time.time_ns())
        lease_expires_ns = now_ns + int(lease_seconds * 1e9)
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, tenant_id, event_id, event_type, aggregate_id, payload_json, retry_count, max_retries
                        FROM financial_outbox
                        WHERE published = 0 AND status != 'DLQ'
                          AND ((status = 'PENDING' AND (next_attempt_at_ns IS NULL OR next_attempt_at_ns <= %s))
                            OR (status = 'IN_FLIGHT' AND lease_expires_at_ns < %s))
                        ORDER BY created_at_ns ASC
                        LIMIT %s
                        FOR UPDATE SKIP LOCKED
                    """, (now_ns, now_ns, batch_size))
                    rows = cur.fetchall()
                    claimed = []
                    for r in rows:
                        rec_id = r["id"]
                        cur.execute("""
                            UPDATE financial_outbox
                            SET status = 'IN_FLIGHT', lease_expires_at_ns = %s, worker_id = %s
                            WHERE id = %s
                        """, (lease_expires_ns, worker_id, rec_id))
                        claimed.append(dict(r))
                conn.commit()
                return claimed
            except Exception:
                conn.rollback()
                return []

    def mark_outbox_published(self, record_id: str) -> bool:
        now_ns = int(time.time_ns())
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE financial_outbox
                        SET published = 1, status = 'PUBLISHED', published_at_ns = %s, last_error = NULL
                        WHERE id = %s AND status = 'IN_FLIGHT'
                    """, (now_ns, record_id))
                conn.commit()
                return cur.rowcount == 1
            except Exception:
                conn.rollback()
                return False

    def mark_outbox_failed(self, record_id: str, error: str, retry_count: int, next_attempt_at_ns: int) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE financial_outbox
                        SET status = 'PENDING', retry_count = %s, next_attempt_at_ns = %s, last_error = %s
                        WHERE id = %s
                    """, (retry_count, next_attempt_at_ns, error, record_id))
                conn.commit()
                return cur.rowcount == 1
            except Exception:
                conn.rollback()
                return False

    def insert_dlq_record(self, record: Dict[str, Any]) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dead_letter_queue (
                            id, original_event_id, tenant_id, event_type, aggregate_id,
                            payload_json, failed_at_ns, failure_reason, retry_attempts
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        record["id"],
                        record["original_event_id"],
                        record["tenant_id"],
                        record["event_type"],
                        record["aggregate_id"],
                        record["payload_json"],
                        record["failed_at_ns"],
                        record["failure_reason"],
                        record["retry_attempts"],
                    ))
                    cur.execute("""
                        UPDATE financial_outbox
                        SET status = 'DLQ', last_error = %s
                        WHERE id = %s OR event_id = %s
                    """, (record["failure_reason"], record.get("outbox_id", ""), record["original_event_id"]))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def list_dlq_records(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id:
                    cur.execute("SELECT * FROM dead_letter_queue WHERE tenant_id = %s ORDER BY failed_at_ns DESC", (tenant_id,))
                else:
                    cur.execute("SELECT * FROM dead_letter_queue ORDER BY failed_at_ns DESC")
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def health_check(self) -> Dict[str, Any]:
        with self._lock, self._get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS alive")
                    row = cur.fetchone()
                    alive = row["alive"] == 1
                    return {
                        "backend": "PostgreSQL / Aurora (Row-Level Locks Enabled)",
                        "status": "connected" if alive else "error",
                        "database_url_masked": self.database_url.split("@")[-1] if "@" in self.database_url else "postgresql://localhost",
                    }
            except Exception as e:
                return {
                    "backend": "PostgreSQL / Aurora (Row-Level Locks Enabled)",
                    "status": f"unreachable: {e}",
                    "database_url_masked": self.database_url.split("@")[-1] if "@" in self.database_url else "postgresql://localhost",
                }


def get_storage_backend(
    database_url: Optional[str] = None,
    env: Optional[EnvironmentMode] = None,
    injected_conn: Optional[Any] = None,
) -> StorageBackend:
    """Storage Factory enforcing strict environment separation.
    
    Rules:
    1. SANDBOX_DEMO defaults to SQLiteStorageBackend (WAL mode).
    2. STAGING / PRODUCTION requires a postgresql:// URL.
    3. If PRODUCTION is specified with sqlite://, fails closed with SecurityConfigError.
    4. Never silently falls back to SQLite in PRODUCTION.
    """
    effective_env = env or config.environment
    effective_url = database_url or config.database_url

    if effective_env == EnvironmentMode.PRODUCTION:
        if "sqlite" in effective_url.lower():
            raise SecurityConfigError(
                "Production Invariant Violation: SQLite is strictly prohibited in PRODUCTION. "
                "Configure a high-availability PostgreSQL / Amazon Aurora database URL (DATABASE_URL)."
            )
        return PostgreSQLStorageBackend(effective_url, db_connection=injected_conn)

    if effective_env == EnvironmentMode.STAGING:
        if "sqlite" in effective_url.lower():
            raise SecurityConfigError(
                "Staging Invariant Violation: SQLite is prohibited in STAGING. PostgreSQL is required."
            )
        return PostgreSQLStorageBackend(effective_url, db_connection=injected_conn)

    # SANDBOX_DEMO
    if "postgres" in effective_url.lower():
        return PostgreSQLStorageBackend(effective_url, db_connection=injected_conn)

    db_path = effective_url.replace("sqlite:///", "") if "sqlite:///" in effective_url else effective_url
    return SQLiteStorageBackend(db_path=db_path)
