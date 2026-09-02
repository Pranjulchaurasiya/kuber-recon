"""Production Observability & Metrics Export Kernel.

Provides Prometheus-compatible metric counters, histograms, and structured JSON logs.
"""

from dataclasses import dataclass, field
import json
import logging
from threading import RLock
import time
from typing import Any, Dict


logger = logging.getLogger("kuber_recon.observability")


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON for log aggregators (ELK, CloudWatch, Datadog)."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "latency_ms": getattr(record, "latency_ms", None),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


@dataclass
class PrometheusMetricsRegistry:
    """Thread-safe in-memory metrics registry formatted for Prometheus scraping (/metrics)."""

    _lock: RLock = field(default_factory=RLock)
    
    # Request counters
    http_requests_total: Dict[str, int] = field(default_factory=dict)
    
    # Financial metrics
    paise_reconciled_total: int = 0
    paise_settled_swept_total: int = 0
    
    # Solver telemetry
    solver_invocations_total: int = 0
    solver_duration_seconds_total: float = 0.0
    
    # Security metrics
    unauthorized_requests_total: int = 0
    stale_webhooks_rejected_total: int = 0
    duplicate_webhooks_ignored_total: int = 0
    cas_concurrency_conflicts_total: int = 0

    def record_http_request(self, method: str, path: str, status_code: int) -> None:
        key = f'{method}_{path}_{status_code}'
        with self._lock:
            self.http_requests_total[key] = self.http_requests_total.get(key, 0) + 1

    def record_reconciliation(self, paise: int, duration_ms: float) -> None:
        with self._lock:
            self.paise_reconciled_total += paise
            self.solver_invocations_total += 1
            self.solver_duration_seconds_total += duration_ms / 1000.0

    def record_sweep(self, paise: int) -> None:
        with self._lock:
            self.paise_settled_swept_total += paise

    def record_security_event(self, event_type: str) -> None:
        with self._lock:
            if event_type == "unauthorized":
                self.unauthorized_requests_total += 1
            elif event_type == "stale_webhook":
                self.stale_webhooks_rejected_total += 1
            elif event_type == "duplicate_webhook":
                self.duplicate_webhooks_ignored_total += 1
            elif event_type == "cas_conflict":
                self.cas_concurrency_conflicts_total += 1

    def render_prometheus_text(self) -> str:
        """Render metrics in standard Prometheus line protocol."""
        lines = [
            "# HELP kuber_http_requests_total Total HTTP requests partitioned by method, path, status",
            "# TYPE kuber_http_requests_total counter",
        ]
        with self._lock:
            for key, count in sorted(self.http_requests_total.items()):
                parts = key.split("_")
                method, path, status = parts[0], parts[1], parts[2]
                lines.append(f'kuber_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

            lines.extend([
                "# HELP kuber_paise_reconciled_total Total paise reconciled by Horowitz-Sahni engine",
                "# TYPE kuber_paise_reconciled_total counter",
                f"kuber_paise_reconciled_total {self.paise_reconciled_total}",
                "",
                "# HELP kuber_paise_settled_swept_total Total paise recovered via nodal split-sweeps",
                "# TYPE kuber_paise_settled_swept_total counter",
                f"kuber_paise_settled_swept_total {self.paise_settled_swept_total}",
                "",
                "# HELP kuber_solver_invocations_total Total subset-sum solver runs",
                "# TYPE kuber_solver_invocations_total counter",
                f"kuber_solver_invocations_total {self.solver_invocations_total}",
                "",
                "# HELP kuber_solver_duration_seconds_total Total cumulative solve duration in seconds",
                "# TYPE kuber_solver_duration_seconds_total counter",
                f"kuber_solver_duration_seconds_total {self.solver_duration_seconds_total:.6f}",
                "",
                "# HELP kuber_security_events_total Invariant and security defense blocks",
                "# TYPE kuber_security_events_total counter",
                f'kuber_security_events_total{{type="unauthorized"}} {self.unauthorized_requests_total}',
                f'kuber_security_events_total{{type="stale_webhook"}} {self.stale_webhooks_rejected_total}',
                f'kuber_security_events_total{{type="duplicate_webhook"}} {self.duplicate_webhooks_ignored_total}',
                f'kuber_security_events_total{{type="cas_conflict"}} {self.cas_concurrency_conflicts_total}',
            ])
        return "\n".join(lines) + "\n"


# Global Metrics Singleton
metrics = PrometheusMetricsRegistry()
