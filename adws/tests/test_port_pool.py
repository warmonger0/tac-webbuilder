#!/usr/bin/env python3
"""
Tests for Port Pool Management

Run with:
    cd adws
    pytest tests/test_port_pool.py -v
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.port_pool import PortPool, get_port_pool


@pytest.fixture
def temp_persistence_dir():
    """Create temporary directory for persistence file."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def port_pool(temp_persistence_dir):
    """Create PortPool instance with temporary persistence."""
    with patch.object(PortPool, 'PERSISTENCE_FILE', temp_persistence_dir / "port_allocations.json"):
        pool = PortPool()
        yield pool


def test_basic_reservation(port_pool):
    """Test basic port reservation."""
    backend, frontend = port_pool.reserve("adw-test1")

    assert backend >= 9100
    assert backend <= 9199
    assert frontend >= 9200
    assert frontend <= 9299
    assert frontend - backend == 100  # Offset of 100


def test_idempotent_reservation(port_pool):
    """Test that reserving same ADW returns same ports."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    backend2, frontend2 = port_pool.reserve("adw-test1")

    assert backend1 == backend2
    assert frontend1 == frontend2


def test_unique_allocations(port_pool):
    """Test that different ADWs get different ports."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    backend2, frontend2 = port_pool.reserve("adw-test2")

    assert backend1 != backend2
    assert frontend1 != frontend2


def test_release(port_pool):
    """Test port release."""
    backend, frontend = port_pool.reserve("adw-test1")

    # Should return True when releasing existing allocation
    assert port_pool.release("adw-test1") is True

    # Should return False when releasing non-existent allocation
    assert port_pool.release("adw-test1") is False


def test_reuse_after_release(port_pool):
    """Test that released ports can be reused."""
    backend1, frontend1 = port_pool.reserve("adw-test1")
    port_pool.release("adw-test1")

    backend2, frontend2 = port_pool.reserve("adw-test2")

    # Should reuse the released slot (first available)
    assert backend2 == backend1
    assert frontend2 == frontend1


def test_get_allocation(port_pool):
    """Test getting current allocation."""
    backend, frontend = port_pool.reserve("adw-test1")

    allocation = port_pool.get_allocation("adw-test1")
    assert allocation == (backend, frontend)

    # Non-existent should return None
    assert port_pool.get_allocation("adw-nonexistent") is None


def test_pool_status(port_pool):
    """Test pool status reporting."""
    status = port_pool.get_pool_status()

    assert status["allocated"] == 0
    assert status["available"] == 100
    assert status["total"] == 100
    assert status["utilization_percent"] == 0.0

    # Allocate some
    port_pool.reserve("adw-test1")
    port_pool.reserve("adw-test2")

    status = port_pool.get_pool_status()
    assert status["allocated"] == 2
    assert status["available"] == 98
    assert status["utilization_percent"] == 2.0


def test_pool_exhaustion(port_pool):
    """Test that pool correctly reports exhaustion."""
    # Allocate all 100 slots
    for i in range(100):
        port_pool.reserve(f"adw-test{i}")

    # 101st should raise RuntimeError
    with pytest.raises(RuntimeError, match="Port pool exhausted"):
        port_pool.reserve("adw-test-overflow")


def test_persistence_save(port_pool, temp_persistence_dir):
    """Test that allocations are persisted to file."""
    port_pool.reserve("adw-test1")
    port_pool.reserve("adw-test2")

    persistence_file = temp_persistence_dir / "port_allocations.json"
    assert persistence_file.exists()

    with open(persistence_file, 'r') as f:
        data = json.load(f)

    assert "adw-test1" in data
    assert "adw-test2" in data
    assert data["adw-test1"]["backend"] >= 9100
    assert "allocated_at" in data["adw-test1"]


def test_persistence_load(temp_persistence_dir):
    """Test that allocations are loaded from file on init."""
    persistence_file = temp_persistence_dir / "port_allocations.json"

    # Create persistence file manually
    allocations = {
        "adw-existing": {
            "backend": 9105,
            "frontend": 9205,
            "allocated_at": datetime.now().isoformat()
        }
    }

    persistence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(persistence_file, 'w') as f:
        json.dump(allocations, f)

    # Create new pool - should load existing allocations
    with patch.object(PortPool, 'PERSISTENCE_FILE', persistence_file):
        pool = PortPool()

    allocation = pool.get_allocation("adw-existing")
    assert allocation == (9105, 9205)


def test_cleanup_stale(port_pool):
    """Test cleanup of stale allocations."""
    # Allocate some ports
    port_pool.reserve("adw-fresh")
    port_pool.reserve("adw-stale")

    # Manually set allocated_at for stale one
    old_time = datetime.now() - timedelta(hours=25)
    port_pool._allocations["adw-stale"]["allocated_at"] = old_time.isoformat()

    # Cleanup stale (>24 hours)
    removed = port_pool.cleanup_stale(max_age_hours=24)

    assert removed == 1
    assert port_pool.get_allocation("adw-fresh") is not None
    assert port_pool.get_allocation("adw-stale") is None


def test_singleton_pattern():
    """Test that get_port_pool returns same instance."""
    pool1 = get_port_pool()
    pool2 = get_port_pool()

    assert pool1 is pool2


def test_thread_safety():
    """Test thread-safe concurrent operations."""
    import threading

    pool = PortPool()
    results = {}
    errors = []

    def reserve_port(adw_id):
        try:
            backend, frontend = pool.reserve(adw_id)
            results[adw_id] = (backend, frontend)
        except Exception as e:
            errors.append((adw_id, e))

    # Start 20 threads reserving ports
    threads = []
    for i in range(20):
        t = threading.Thread(target=reserve_port, args=(f"adw-thread{i}",))
        threads.append(t)
        t.start()

    # Wait for all
    for t in threads:
        t.join()

    # Should have no errors
    assert len(errors) == 0

    # Should have 20 unique allocations
    assert len(results) == 20

    # All should be unique
    backends = [b for b, f in results.values()]
    assert len(backends) == len(set(backends))  # No duplicates
