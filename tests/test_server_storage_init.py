"""Tests for Server Storage Initialization, Scheme Enforcement, and Health Reporting.
"""

import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from kuber_recon.config import AppConfig, EnvironmentMode, SecurityConfigError
from kuber_recon.server import WebhookIdempotencyStore, app
from kuber_recon.storage import PostgreSQLStorageBackend, SQLiteStorageBackend, get_storage_backend


def test_server_uses_configured_database_url(tmp_path):
    """Verify that WebhookIdempotencyStore initializes using the configured database_url."""
    db_file = tmp_path / "custom_test.db"
    db_url = f"sqlite:///{db_file}"
    store = WebhookIdempotencyStore(database_url=db_url)
    assert isinstance(store.backend, SQLiteStorageBackend)
    assert str(store.backend.db_path) == str(db_file)


def test_production_never_uses_db_file():
    """Verify that PRODUCTION environment strictly refuses SQLite and filesystem paths."""
    with pytest.raises(SecurityConfigError) as exc_info:
        get_storage_backend(
            database_url=str(WebhookIdempotencyStore.DB_FILE),
            env=EnvironmentMode.PRODUCTION,
        )
    assert "PRODUCTION" in str(exc_info.value)
    assert "strictly prohibited" in str(exc_info.value) or "valid PostgreSQL scheme" in str(exc_info.value)


def test_staging_rejects_sqlite():
    """Verify that STAGING environment strictly rejects sqlite URLs."""
    with pytest.raises(SecurityConfigError) as exc_info:
        get_storage_backend(
            database_url="sqlite:///test_staging.db",
            env=EnvironmentMode.STAGING,
        )
    assert "STAGING" in str(exc_info.value)


def test_invalid_postgres_url_fails_closed():
    """Verify that invalid schemes or non-PostgreSQL URLs fail closed in STAGING and PRODUCTION."""
    for invalid_url in [
        "/var/run/postgresql/data.db",
        "mysql://user:pass@localhost/db",
        "C:\\Users\\db.sqlite",
        "",
    ]:
        with pytest.raises(SecurityConfigError):
            get_storage_backend(database_url=invalid_url, env=EnvironmentMode.PRODUCTION)

        with pytest.raises(SecurityConfigError):
            get_storage_backend(database_url=invalid_url, env=EnvironmentMode.STAGING)


def test_health_reports_actual_backend():
    """Verify that /health and /api/health report the exact active backend and status."""
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "storage_backend" in data
        assert data["storage_backend"] in ("SQLite WAL", "PostgreSQL/Aurora")
        assert data["storage_status"] in ("connected", "ok", "healthy")

        resp_api = client.get("/api/health")
        assert resp_api.status_code == 200
        data_api = resp_api.json()
        assert data_api["storage_backend"] == data["storage_backend"]
