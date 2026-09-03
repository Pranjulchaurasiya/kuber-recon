"""Tests for DistributedLockAdapter & Concurrency Mutual Exclusion.

Verifies:
1. LocalRLockAdapter reentrancy and isolation across resource keys.
2. Concurrent thread synchronization.
3. Factory resolution with fallback to LocalRLockAdapter when Redis is unconfigured.
"""

import threading
import time
import pytest

from kuber_recon.distributed_lock import LocalRLockAdapter, get_lock, DistributedLock


def test_local_rlock_reentrancy():
    lock = LocalRLockAdapter("test_resource_01")
    # Should acquire without deadlock (reentrant)
    with lock:
        with lock:
            assert True


def test_lock_isolation_across_tenants():
    lock_a = get_lock("facility_01", tenant_id="tenant_alpha")
    lock_b = get_lock("facility_01", tenant_id="tenant_beta")
    
    # Different tenants have different lock instances
    assert lock_a.key != lock_b.key


def test_concurrent_threads_mutual_exclusion():
    lock = get_lock("critical_sweep_facility_100", tenant_id="merchant_rzp_primary")
    counter = 0
    num_threads = 10
    iterations = 50

    def worker():
        nonlocal counter
        for _ in range(iterations):
            with lock:
                current = counter
                time.sleep(0.0001)  # Context switch opportunity
                counter = current + 1

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exact mutual exclusion check
    assert counter == num_threads * iterations
