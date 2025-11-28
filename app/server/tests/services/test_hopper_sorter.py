"""
Tests for HopperSorter - Deterministic phase selection.

Tests cover:
- Priority-based ordering
- FIFO within same priority
- Cross-parent selection
- Parallel execution support
"""

import sqlite3

import pytest
from services.hopper_sorter import HopperSorter, get_priority_name
from services.phase_queue_service import PhaseQueueService


@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database"""
    db_path = tmp_path / "test_queue.db"

    # Create schema
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE phase_queue (
            queue_id TEXT PRIMARY KEY,
            parent_issue INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            issue_number INTEGER,
            status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
            depends_on_phase INTEGER,
            phase_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            adw_id TEXT,
            pr_number INTEGER,
            priority INTEGER DEFAULT 50,
            queue_position INTEGER,
            ready_timestamp TEXT,
            started_timestamp TEXT
        )
    """)
    conn.execute("CREATE INDEX idx_phase_queue_priority ON phase_queue(priority, queue_position)")
    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def sorter(test_db):
    """Create HopperSorter instance with test database"""
    return HopperSorter(db_path=test_db)


@pytest.fixture
def queue_service(test_db):
    """Create PhaseQueueService instance with test database"""
    return PhaseQueueService(db_path=test_db)


def test_priority_ordering(test_db, sorter, queue_service):
    """Test that higher priority phases are selected first"""
    # Enqueue Phase 1s with different priorities
    queue_service.enqueue(
        parent_issue=100,
        phase_number=1,
        phase_data={"title": "Normal priority"},
        depends_on_phase=None,
    )

    queue_service.enqueue(
        parent_issue=200,
        phase_number=1,
        phase_data={"title": "Urgent priority"},
        depends_on_phase=None,
    )

    queue_service.enqueue(
        parent_issue=300,
        phase_number=1,
        phase_data={"title": "Low priority"},
        depends_on_phase=None,
    )

    # Set priorities
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET priority = 50 WHERE parent_issue = 100")
    conn.execute("UPDATE phase_queue SET priority = 10 WHERE parent_issue = 200")  # Urgent
    conn.execute("UPDATE phase_queue SET priority = 70 WHERE parent_issue = 300")
    conn.execute("UPDATE phase_queue SET status = 'ready'")  # Mark all ready
    conn.commit()
    conn.close()

    # Get next phase
    next_phase = sorter.get_next_phase_1()

    # Should be parent 200 (priority=10, highest)
    assert next_phase is not None
    assert next_phase.parent_issue == 200
    assert next_phase.priority == 10


def test_fifo_within_priority(test_db, sorter, queue_service):
    """Test FIFO ordering within same priority level"""
    # Enqueue three Phase 1s with same priority
    import time

    queue_service.enqueue(
        parent_issue=100,
        phase_number=1,
        phase_data={"title": "First"},
        depends_on_phase=None,
    )
    time.sleep(0.01)  # Ensure different queue_position

    queue_service.enqueue(
        parent_issue=200,
        phase_number=1,
        phase_data={"title": "Second"},
        depends_on_phase=None,
    )
    time.sleep(0.01)

    queue_service.enqueue(
        parent_issue=300,
        phase_number=1,
        phase_data={"title": "Third"},
        depends_on_phase=None,
    )

    # All same priority, all ready
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET priority = 50, status = 'ready'")
    conn.commit()
    conn.close()

    # Should execute in order: 100 → 200 → 300
    phase1 = sorter.get_next_phase_1()
    assert phase1.parent_issue == 100

    # Mark as running to remove from ready queue
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET status = 'running' WHERE parent_issue = 100")
    conn.commit()
    conn.close()

    phase2 = sorter.get_next_phase_1()
    assert phase2.parent_issue == 200


def test_empty_hopper(sorter):
    """Test behavior when hopper is empty"""
    next_phase = sorter.get_next_phase_1()
    assert next_phase is None


def test_parallel_execution(test_db, sorter, queue_service):
    """Test getting multiple phases for parallel execution"""
    # Create 5 ready Phase 1s
    for i in range(1, 6):
        queue_service.enqueue(
            parent_issue=100 + i,
            phase_number=1,
            phase_data={"title": f"Parent {100+i}"},
            depends_on_phase=None,
        )

    # Mark all ready
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET status = 'ready'")
    conn.commit()
    conn.close()

    # Get up to 3 for parallel execution
    phases = sorter.get_next_phases_parallel(max_parallel=3)

    assert len(phases) == 3
    assert all(p.phase_number == 1 for p in phases)
    assert all(p.status == "ready" for p in phases)


def test_running_parent_count(test_db, sorter, queue_service):
    """Test counting running parents"""
    # Create phases for 3 parents
    for parent in [100, 200, 300]:
        queue_service.enqueue(
            parent_issue=parent,
            phase_number=1,
            phase_data={"title": f"Parent {parent}"},
            depends_on_phase=None,
        )

    # Mark 2 as running
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET status = 'running' WHERE parent_issue IN (100, 200)")
    conn.commit()
    conn.close()

    count = sorter.get_running_parent_count()
    assert count == 2


def test_can_start_more_parents(test_db, sorter, queue_service):
    """Test concurrency limit checking"""
    # Create 3 running parents
    for parent in [100, 200, 300]:
        queue_service.enqueue(
            parent_issue=parent,
            phase_number=1,
            phase_data={"title": f"Parent {parent}"},
            depends_on_phase=None,
        )

    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET status = 'running'")
    conn.commit()
    conn.close()

    # With limit of 5, should be able to start more
    assert sorter.can_start_more_parents(max_concurrent=5) is True

    # With limit of 3, should not be able to start more
    assert sorter.can_start_more_parents(max_concurrent=3) is False


def test_priority_stats(test_db, sorter, queue_service):
    """Test priority statistics"""
    # Create phases with different priorities
    queue_service.enqueue(
        parent_issue=100,
        phase_number=1,
        phase_data={"title": "Urgent"},
        depends_on_phase=None,
    )
    queue_service.enqueue(
        parent_issue=200,
        phase_number=1,
        phase_data={"title": "Normal"},
        depends_on_phase=None,
    )

    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET priority = 10, status = 'ready' WHERE parent_issue = 100")
    conn.execute("UPDATE phase_queue SET priority = 50, status = 'queued' WHERE parent_issue = 200")
    conn.commit()
    conn.close()

    stats = sorter.get_priority_stats()

    assert stats["total_phase_1s"] == 2
    assert stats["ready_phase_1s"] == 1
    assert 10 in stats["by_priority"]
    assert stats["by_priority"][10]["ready"] == 1


def test_get_priority_name():
    """Test priority name helper"""
    assert get_priority_name(10) == "urgent"
    assert get_priority_name(20) == "high"
    assert get_priority_name(50) == "normal"
    assert get_priority_name(70) == "low"
    assert get_priority_name(90) == "background"


def test_deterministic_tiebreaker(test_db, sorter, queue_service):
    """Test that parent_issue is used as tiebreaker"""
    # Create two phases with same priority and queue_position

    queue_service.enqueue(
        parent_issue=200,
        phase_number=1,
        phase_data={"title": "Higher parent number"},
        depends_on_phase=None,
    )

    queue_service.enqueue(
        parent_issue=100,
        phase_number=1,
        phase_data={"title": "Lower parent number"},
        depends_on_phase=None,
    )

    # Set same priority and position
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE phase_queue SET priority = 50, queue_position = 1, status = 'ready'")
    conn.commit()
    conn.close()

    next_phase = sorter.get_next_phase_1()

    # Should pick lower parent_issue number as tiebreaker
    assert next_phase.parent_issue == 100
