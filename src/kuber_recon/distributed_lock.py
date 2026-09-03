"""Distributed Lock Adapter for Multi-Replica API Deployments.

Provides mutual exclusion across Kubernetes replicas for critical financial mutations
(e.g., APEX Capital disbursements, split-settlement sweeps, and CAS transitions).

Architecture:
- Primary: Redis-backed distributed lock with unique random nonce and atomic Lua release.
- Fallback: Threading RLock with per-key tenant isolation when Redis is unconfigured or offline.
"""

import os
import time
import uuid
import logging
from threading import RLock
from typing import Any, Dict, Optional

logger = logging.getLogger("kuber_recon.distributed_lock")


# Lua script for safe atomic release: deletes key ONLY if token matches owner
RELEASE_LUA_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class DistributedLockTimeoutError(Exception):
    """Raised when failing to acquire distributed lock within timeout window."""
    pass


class DistributedLock:
    """Abstract interface for distributed mutual exclusion."""
    def acquire(self, timeout_sec: float = 5.0) -> bool:
        raise NotImplementedError

    def release(self) -> bool:
        raise NotImplementedError

    def __enter__(self):
        if not self.acquire():
            raise DistributedLockTimeoutError("Failed to acquire distributed lock.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class LocalRLockAdapter(DistributedLock):
    """Process-local reentrant lock adapter with per-key registry."""
    _registry: Dict[str, RLock] = {}
    _registry_guard: RLock = RLock()

    def __init__(self, key: str):
        self.key = key
        with self._registry_guard:
            if key not in self._registry:
                self._registry[key] = RLock()
            self._lock = self._registry[key]

    def acquire(self, timeout_sec: float = 5.0) -> bool:
        return self._lock.acquire(timeout=timeout_sec)

    def release(self) -> bool:
        try:
            self._lock.release()
            return True
        except RuntimeError:
            return False


class RedisDistributedLock(DistributedLock):
    """Production Redis-backed distributed lock with TTL and atomic Lua release."""

    def __init__(self, redis_client: Any, key: str, ttl_ms: int = 10000):
        self.client = redis_client
        self.key = f"kuber:lock:{key}"
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())
        self._acquired = False

    def acquire(self, timeout_sec: float = 5.0) -> bool:
        start_time = time.monotonic()
        retry_delay = 0.05  # 50ms polling delay

        while time.monotonic() - start_time < timeout_sec:
            # SET key token NX PX ttl_ms
            ok = self.client.set(self.key, self.token, nx=True, px=self.ttl_ms)
            if ok:
                self._acquired = True
                return True
            time.sleep(retry_delay)

        return False

    def release(self) -> bool:
        if not self._acquired:
            return False
        try:
            res = self.client.eval(RELEASE_LUA_SCRIPT, 1, self.key, self.token)
            self._acquired = False
            return bool(res)
        except Exception as e:
            logger.warning(f"Failed to release Redis lock on {self.key}: {e}")
            return False


_global_redis_client: Optional[Any] = None
_redis_init_attempted: bool = False


def _get_redis_client() -> Optional[Any]:
    global _global_redis_client, _redis_init_attempted
    if _redis_init_attempted:
        return _global_redis_client

    _redis_init_attempted = True
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None

    try:
        import redis
        client = redis.from_url(redis_url, socket_timeout=2.0, decode_responses=True)
        client.ping()
        _global_redis_client = client
        logger.info(f"Connected to Redis distributed lock provider: {redis_url}")
        return _global_redis_client
    except Exception as e:
        logger.warning(f"Redis configured at {redis_url} but unreachable ({e}). Falling back to LocalRLockAdapter.")
        return None


def get_lock(resource_key: str, tenant_id: str, ttl_seconds: int = 10) -> DistributedLock:
    """
    Factory resolving lock adapter based on operational environment.
    
    If REDIS_URL is accessible, returns RedisDistributedLock.
    Otherwise returns LocalRLockAdapter with per-tenant resource key isolation.
    """
    full_key = f"{tenant_id}:{resource_key}"
    client = _get_redis_client()
    if client is not None:
        return RedisDistributedLock(redis_client=client, key=full_key, ttl_ms=ttl_seconds * 1000)
    return LocalRLockAdapter(key=full_key)
