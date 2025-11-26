"""
Tests for PhaseQueueService

Tests phase queue management, dependency tracking, and sequential execution coordination.
"""

import os
import tempfile

import pytest
from services.phase_queue_service import PhaseQueueService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_phase_queue.db")

        # Initialize database with schema
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS phase_queue (
              queue_id TEXT PRIMARY KEY,
              parent_issue INTEGER NOT NULL,
              phase_number INTEGER NOT NULL,
              issue_number INTEGER,
              status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
              depends_on_phase INTEGER,
              phase_data TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              error_message TEXT
            )
        """)
        conn.commit()
        conn.close()

        yield db_path


@pytest.fixture
def service(temp_db):
    """Create PhaseQueueService instance with temporary database"""
    return PhaseQueueService(db_path=temp_db)


def test_enqueue_single_phase(service):
    """Test enqueueing a single phase"""
    phase_data = {
        "title": "Phase 1: Foundation",
        "content": "Build the foundation",
        "externalDocs": ["ARCHITECTURE.md"]
    }

    queue_id = service.enqueue(
        parent_issue=123,
        phase_number=1,
        phase_data=phase_data,
        depends_on_phase=None
    )

    assert queue_id is not None
    assert len(queue_id) > 0

    # Verify phase is in queue with 'ready' status (Phase 1 is ready immediately)
    items = service.get_queue_by_parent(123)
    assert len(items) == 1
    assert items[0].phase_number == 1
    assert items[0].status == "ready"
    assert items[0].phase_data["title"] == "Phase 1: Foundation"


def test_enqueue_multiple_phases(service):
    """Test enqueueing multiple phases with dependencies"""
    parent_issue = 456

    # Enqueue Phase 1
    service.enqueue(
        parent_issue=parent_issue,
        phase_number=1,
        phase_data={"title": "Phase 1", "content": "First phase"},
        depends_on_phase=None
    )

    # Enqueue Phase 2
    service.enqueue(
        parent_issue=parent_issue,
        phase_number=2,
        phase_data={"title": "Phase 2", "content": "Second phase"},
        depends_on_phase=1
    )

    # Enqueue Phase 3
    service.enqueue(
        parent_issue=parent_issue,
        phase_number=3,
        phase_data={"title": "Phase 3", "content": "Third phase"},
        depends_on_phase=2
    )

    # Verify all phases are in queue
    items = service.get_queue_by_parent(parent_issue)
    assert len(items) == 3

    # Phase 1 should be ready
    assert items[0].status == "ready"

    # Phase 2 and 3 should be queued
    assert items[1].status == "queued"
    assert items[2].status == "queued"


def test_mark_phase_complete_triggers_next(service):
    """Test that completing a phase marks the next phase as ready"""
    parent_issue = 789

    # Enqueue 3 phases
    queue_id_1 = service.enqueue(parent_issue, 1, {"title": "P1", "content": "..."}, None)
    queue_id_2 = service.enqueue(parent_issue, 2, {"title": "P2", "content": "..."}, 1)
    service.enqueue(parent_issue, 3, {"title": "P3", "content": "..."}, 2)

    # Initially: Phase 1 ready, Phase 2 and 3 queued
    items = service.get_queue_by_parent(parent_issue)
    assert items[0].status == "ready"
    assert items[1].status == "queued"
    assert items[2].status == "queued"

    # Mark Phase 1 complete
    service.mark_phase_complete(queue_id_1)

    # Now: Phase 1 completed, Phase 2 ready, Phase 3 queued
    items = service.get_queue_by_parent(parent_issue)
    assert items[0].status == "completed"
    assert items[1].status == "ready"
    assert items[2].status == "queued"

    # Mark Phase 2 complete
    service.mark_phase_complete(queue_id_2)

    # Now: Phase 1 and 2 completed, Phase 3 ready
    items = service.get_queue_by_parent(parent_issue)
    assert items[0].status == "completed"
    assert items[1].status == "completed"
    assert items[2].status == "ready"


def test_mark_phase_failed_blocks_dependents(service):
    """Test that failing a phase blocks all dependent phases"""
    parent_issue = 999

    # Enqueue 3 phases
    queue_id_1 = service.enqueue(parent_issue, 1, {"title": "P1", "content": "..."}, None)
    service.enqueue(parent_issue, 2, {"title": "P2", "content": "..."}, 1)
    service.enqueue(parent_issue, 3, {"title": "P3", "content": "..."}, 2)

    # Mark Phase 1 as failed
    blocked_ids = service.mark_phase_failed(queue_id_1, "Tests failed")

    # Should block Phase 2 and 3
    assert len(blocked_ids) == 2

    # Verify statuses
    items = service.get_queue_by_parent(parent_issue)
    assert items[0].status == "failed"
    assert items[1].status == "blocked"
    assert items[2].status == "blocked"
    assert "Phase 1 failed" in items[1].error_message


def test_get_next_ready(service):
    """Test finding the next ready phase"""
    # Enqueue phases for multiple parent issues
    service.enqueue(100, 1, {"title": "P1", "content": "..."}, None)
    service.enqueue(100, 2, {"title": "P2", "content": "..."}, 1)
    service.enqueue(200, 1, {"title": "P1", "content": "..."}, None)

    # Should return first ready phase (Phase 1 of issue 100)
    next_ready = service.get_next_ready()
    assert next_ready is not None
    assert next_ready.parent_issue == 100
    assert next_ready.phase_number == 1
    assert next_ready.status == "ready"


def test_update_issue_number(service):
    """Test updating issue number after GitHub issue creation"""
    queue_id = service.enqueue(
        111, 1, {"title": "P1", "content": "..."}, None
    )

    # Initially no issue number
    items = service.get_queue_by_parent(111)
    assert items[0].issue_number is None

    # Update issue number
    success = service.update_issue_number(queue_id, 555)
    assert success

    # Verify updated
    items = service.get_queue_by_parent(111)
    assert items[0].issue_number == 555


def test_update_status(service):
    """Test updating phase status"""
    queue_id = service.enqueue(
        222, 1, {"title": "P1", "content": "..."}, None
    )

    # Change to running
    success = service.update_status(queue_id, "running")
    assert success

    items = service.get_queue_by_parent(222)
    assert items[0].status == "running"


def test_dequeue(service):
    """Test removing phase from queue"""
    queue_id = service.enqueue(
        333, 1, {"title": "P1", "content": "..."}, None
    )

    # Verify in queue
    items = service.get_queue_by_parent(333)
    assert len(items) == 1

    # Dequeue
    success = service.dequeue(queue_id)
    assert success

    # Verify removed
    items = service.get_queue_by_parent(333)
    assert len(items) == 0


def test_mark_phase_blocked(service):
    """Test manually blocking a phase"""
    queue_id = service.enqueue(
        444, 2, {"title": "P2", "content": "..."}, 1
    )

    # Block phase
    success = service.mark_phase_blocked(queue_id, "Manual block for testing")
    assert success

    # Verify blocked
    items = service.get_queue_by_parent(444)
    assert items[0].status == "blocked"
    assert "Manual block" in items[0].error_message


def test_get_all_queued(service):
    """Test retrieving all phases across all parent issues"""
    service.enqueue(100, 1, {"title": "P1", "content": "..."}, None)
    service.enqueue(100, 2, {"title": "P2", "content": "..."}, 1)
    service.enqueue(200, 1, {"title": "P1", "content": "..."}, None)

    all_items = service.get_all_queued()
    assert len(all_items) == 3

    # Should be ordered by parent issue and phase number
    assert all_items[0].parent_issue == 100
    assert all_items[0].phase_number == 1
    assert all_items[1].parent_issue == 100
    assert all_items[1].phase_number == 2
    assert all_items[2].parent_issue == 200
    assert all_items[2].phase_number == 1


def test_invalid_status_raises_error(service):
    """Test that invalid status raises ValueError"""
    queue_id = service.enqueue(
        555, 1, {"title": "P1", "content": "..."}, None
    )

    with pytest.raises(ValueError, match="Invalid status"):
        service.update_status(queue_id, "invalid_status")
