"""
Unit Tests for PhaseCoordinator Service

Tests the PhaseCoordinator background service including:
- Polling loop lifecycle (start/stop)
- Workflow completion detection
- Phase completion triggering next phase
- Phase failure blocking dependents
- WebSocket event broadcasting
- Error handling in polling loop
"""

import asyncio
import os
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from services.phase_coordinator import PhaseCoordinator
from services.phase_queue_service import PhaseQueueService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_workflow_db():
    """Create temporary database for workflow history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_workflow_history.db")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        # Use standard schema initialization instead of manual SQL
        from database.sqlite_adapter import SQLiteAdapter
        from core.workflow_history_utils.database import init_db
        from core.workflow_history_utils.database import schema as schema_module
        from unittest.mock import patch

        adapter = SQLiteAdapter(db_path=db_path)

        # Temporarily patch the schema module to use our test database
        original_adapter = schema_module._db_adapter
        schema_module._db_adapter = adapter

        try:
            init_db()
        finally:
            schema_module._db_adapter = original_adapter

        yield db_path


@pytest.fixture
def phase_queue_service():
    """
    Create PhaseQueueService.

    Uses PostgreSQL database with cleanup_phase_queue_data autouse fixture
    for automatic test isolation.
    """
    return PhaseQueueService()


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    mock = AsyncMock()
    mock.broadcast = AsyncMock()
    return mock


@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    from database.sqlite_adapter import SQLiteAdapter

    # Create adapter for workflow database
    workflow_adapter = SQLiteAdapter(db_path=temp_workflow_db)

    # Create coordinator (detector will use factory adapter initially)
    coordinator = PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )

    # Manually inject the workflow adapter into the detector
    # This ensures the detector queries the test workflow database
    coordinator.detector.adapter = workflow_adapter

    # DEBUG: Verify the adapter is correctly set
    print(f"\n[DEBUG FIXTURE] Created adapter with db_path: {temp_workflow_db}")
    print(f"[DEBUG FIXTURE] Detector adapter db_path: {coordinator.detector.adapter.db_path}")
    assert coordinator.detector.adapter.db_path == temp_workflow_db, \
        f"Adapter injection failed: {coordinator.detector.adapter.db_path} != {temp_workflow_db}"

    return coordinator


# ============================================================================
# Helper Functions
# ============================================================================


def add_workflow(
    workflow_db_path: str,
    issue_number: int,
    status: str = "running",
    error_message: str | None = None
):
    """Add a workflow to workflow_history"""
    conn = sqlite3.connect(workflow_db_path)
    # Set end_time only for completed/failed status (for phantom detection)
    end_time = datetime.now().isoformat() if status in ('completed', 'failed') else None
    conn.execute(
        """
        INSERT INTO workflow_history (
            adw_id, issue_number, status, error_message,
            created_at, updated_at, end_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"wf-{issue_number}",
            issue_number,
            status,
            error_message,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            end_time,
        ),
    )
    conn.commit()
    conn.close()


def get_phase_by_id(phase_queue_service: PhaseQueueService, queue_id: str):
    """Get phase by queue_id"""
    items = phase_queue_service.get_all_queued()
    for item in items:
        if item.queue_id == queue_id:
            return item
    return None


# ============================================================================
# Unit Tests
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestPhaseCoordinatorLifecycle:
    """Test PhaseCoordinator lifecycle management"""

    async def test_start_stops_polling_loop(self, phase_coordinator):
        """Test that start() launches the polling loop"""
        assert phase_coordinator._is_running is False
        assert phase_coordinator._task is None

        await phase_coordinator.start()

        assert phase_coordinator._is_running is True
        assert phase_coordinator._task is not None
        assert not phase_coordinator._task.done()

        # Cleanup
        await phase_coordinator.stop()

    async def test_stop_cancels_polling_loop(self, phase_coordinator):
        """Test that stop() cancels the polling loop"""
        await phase_coordinator.start()
        assert phase_coordinator._is_running is True

        await phase_coordinator.stop()

        assert phase_coordinator._is_running is False
        # Task should be cancelled
        await asyncio.sleep(0.1)  # Give it time to cancel

    async def test_start_when_already_running(self, phase_coordinator):
        """Test that starting an already running coordinator is safe"""
        await phase_coordinator.start()
        task1 = phase_coordinator._task

        # Try to start again
        await phase_coordinator.start()
        task2 = phase_coordinator._task

        # Should be the same task
        assert task1 is task2

        # Cleanup
        await phase_coordinator.stop()

    async def test_stop_when_not_running(self, phase_coordinator):
        """Test that stopping a non-running coordinator is safe"""
        assert phase_coordinator._is_running is False

        # Should not raise exception
        await phase_coordinator.stop()

        assert phase_coordinator._is_running is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowDetection:
    """Test workflow completion detection"""

    async def test_detect_completed_workflow(
        self,
        phase_coordinator,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """Test detection of completed workflow"""
        # Create phase and mark running
        queue_id = phase_queue_service.enqueue(
            parent_issue=100,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Test"},
            depends_on_phase=None,
        )
        phase_queue_service.update_issue_number(queue_id, 101)
        phase_queue_service.update_status(queue_id, "running")

        # Add completed workflow
        add_workflow(temp_workflow_db, 101, status="completed")

        # Check for completions
        await phase_coordinator._check_workflow_completions()

        # Verify phase marked complete
        phase = get_phase_by_id(phase_queue_service, queue_id)
        assert phase.status == "completed"

        # Verify WebSocket broadcast
        mock_websocket_manager.broadcast.assert_called_once()
        event = mock_websocket_manager.broadcast.call_args[0][0]
        assert event["type"] == "queue_update"
        assert event["status"] == "completed"
        assert event["queue_id"] == queue_id

    async def test_detect_failed_workflow(
        self,
        phase_coordinator,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """Test detection of failed workflow"""
        error_msg = "Test error"

        # Create phase and mark running
        queue_id = phase_queue_service.enqueue(
            parent_issue=200,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Test"},
            depends_on_phase=None,
        )
        phase_queue_service.update_issue_number(queue_id, 201)
        phase_queue_service.update_status(queue_id, "running")

        # Add failed workflow
        add_workflow(temp_workflow_db, 201, status="failed", error_message=error_msg)

        # Check for completions
        await phase_coordinator._check_workflow_completions()

        # Verify phase marked failed
        phase = get_phase_by_id(phase_queue_service, queue_id)
        assert phase.status == "failed"
        assert phase.error_message == error_msg

        # Verify WebSocket broadcast
        mock_websocket_manager.broadcast.assert_called_once()
        event = mock_websocket_manager.broadcast.call_args[0][0]
        assert event["status"] == "failed"

    async def test_ignore_non_running_phases(
        self,
        phase_coordinator,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """Test that only running phases are checked"""
        # Pause the queue to prevent auto-start of ready phases
        phase_queue_service.set_paused(True)

        # Create phase but leave it in 'ready' status
        queue_id = phase_queue_service.enqueue(
            parent_issue=300,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Test"},
            depends_on_phase=None,
        )
        phase_queue_service.update_issue_number(queue_id, 301)
        # DON'T mark as running

        # Add completed workflow
        add_workflow(temp_workflow_db, 301, status="completed")

        # Check for completions
        await phase_coordinator._check_workflow_completions()

        # Verify phase status unchanged (should stay 'ready' because queue is paused)
        phase = get_phase_by_id(phase_queue_service, queue_id)
        assert phase.status == "ready"

        # No broadcast should occur
        mock_websocket_manager.broadcast.assert_not_called()

    async def test_get_workflow_status(self, phase_coordinator, temp_workflow_db):
        """Test _get_workflow_status() helper method"""
        from datetime import datetime

        # Add workflow with end_time for completed status
        conn = sqlite3.connect(temp_workflow_db)
        conn.execute(
            """
            INSERT INTO workflow_history (
                adw_id, issue_number, status, error_message,
                created_at, updated_at, end_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "wf-401",
                401,
                "completed",
                None,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Get status
        status = phase_coordinator._get_workflow_status(401)
        assert status == "completed"

        # Non-existent workflow
        status = phase_coordinator._get_workflow_status(999)
        assert status is None

    async def test_get_workflow_error(self, phase_coordinator, temp_workflow_db):
        """Test _get_workflow_error() helper method"""
        from datetime import datetime
        error_msg = "Test error message"

        # Add failed workflow with end_time
        conn = sqlite3.connect(temp_workflow_db)
        conn.execute(
            """
            INSERT INTO workflow_history (
                adw_id, issue_number, status, error_message,
                created_at, updated_at, end_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "wf-501",
                501,
                "failed",
                error_msg,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Get error
        error = phase_coordinator._get_workflow_error(501)
        assert error == error_msg

        # Non-existent workflow
        error = phase_coordinator._get_workflow_error(999)
        assert error is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestPhaseTriggerring:
    """Test phase completion triggers next phase"""

    async def test_completion_triggers_next_phase(
        self,
        phase_coordinator,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """Test that completing Phase 1 marks Phase 2 as ready"""
        parent_issue = 600

        # Enqueue 2 phases
        phase1_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Setup"},
            depends_on_phase=None,
        )

        phase2_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=2,
            phase_data={"title": "Phase 2", "content": "Build"},
            depends_on_phase=1,
        )

        # Phase 1 runs and completes
        phase_queue_service.update_issue_number(phase1_id, 601)
        phase_queue_service.update_status(phase1_id, "running")
        add_workflow(temp_workflow_db, 601, status="completed")

        await phase_coordinator._check_workflow_completions()

        # Verify Phase 1 completed
        phase1 = get_phase_by_id(phase_queue_service, phase1_id)
        assert phase1.status == "completed"

        # Verify Phase 2 ready
        phase2 = get_phase_by_id(phase_queue_service, phase2_id)
        assert phase2.status == "ready"

    async def test_failure_blocks_all_dependents(
        self,
        phase_coordinator,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """Test that Phase 1 failure blocks Phase 2 and 3"""
        parent_issue = 700
        error_msg = "Phase 1 failed"

        # Enqueue 3 phases
        phase1_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Setup"},
            depends_on_phase=None,
        )

        phase2_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=2,
            phase_data={"title": "Phase 2", "content": "Build"},
            depends_on_phase=1,
        )

        phase3_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=3,
            phase_data={"title": "Phase 3", "content": "Test"},
            depends_on_phase=2,
        )

        # Phase 1 runs and fails
        phase_queue_service.update_issue_number(phase1_id, 701)
        phase_queue_service.update_status(phase1_id, "running")
        add_workflow(temp_workflow_db, 701, status="failed", error_message=error_msg)

        await phase_coordinator._check_workflow_completions()

        # Verify Phase 1 failed
        phase1 = get_phase_by_id(phase_queue_service, phase1_id)
        assert phase1.status == "failed"

        # Verify Phase 2 and 3 blocked
        phase2 = get_phase_by_id(phase_queue_service, phase2_id)
        phase3 = get_phase_by_id(phase_queue_service, phase3_id)
        assert phase2.status == "blocked"
        assert phase3.status == "blocked"

        # Verify broadcasts (failed + 2 blocked = 3)
        assert mock_websocket_manager.broadcast.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
class TestWebSocketBroadcasting:
    """Test WebSocket event broadcasting"""

    async def test_broadcast_queue_update_success(
        self,
        phase_coordinator,
        mock_websocket_manager
    ):
        """Test successful WebSocket broadcast"""
        queue_id = "test-queue-123"
        status = "completed"
        parent_issue = 800

        await phase_coordinator._broadcast_queue_update(queue_id, status, parent_issue)

        # Verify broadcast called with correct event
        mock_websocket_manager.broadcast.assert_called_once()
        event = mock_websocket_manager.broadcast.call_args[0][0]

        assert event["type"] == "queue_update"
        assert event["queue_id"] == queue_id
        assert event["status"] == status
        assert event["parent_issue"] == parent_issue
        assert "timestamp" in event

    async def test_broadcast_without_websocket_manager(
        self,
        phase_queue_service,
        temp_workflow_db
    ):
        """Test coordinator works without WebSocket manager"""
        # Create coordinator without WebSocket manager
        coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            poll_interval=0.1,
            websocket_manager=None
        )

        # Should not raise exception
        await coordinator._broadcast_queue_update("queue-123", "completed", 900)

    async def test_broadcast_error_handling(
        self,
        phase_coordinator,
        mock_websocket_manager
    ):
        """Test that broadcast errors are caught and logged"""
        # Make broadcast raise exception
        mock_websocket_manager.broadcast.side_effect = Exception("WebSocket error")

        # Should not raise exception
        await phase_coordinator._broadcast_queue_update("queue-123", "completed", 1000)

        # Broadcast was attempted
        mock_websocket_manager.broadcast.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in PhaseCoordinator"""

    async def test_polling_loop_continues_after_error(
        self,
        phase_coordinator,
        phase_queue_service,
        mock_websocket_manager
    ):
        """Test that errors in polling loop don't crash the coordinator"""
        await phase_coordinator.start()

        try:
            # Mock _check_workflow_completions to raise error
            original_check = phase_coordinator._check_workflow_completions
            error_count = 0

            async def mock_check_with_error():
                nonlocal error_count
                error_count += 1
                if error_count == 1:
                    raise Exception("Test error")
                # Second call succeeds
                await original_check()

            phase_coordinator._check_workflow_completions = mock_check_with_error

            # Wait for multiple poll cycles
            await asyncio.sleep(0.3)

            # Coordinator should still be running
            assert phase_coordinator._is_running is True
            assert error_count >= 2  # At least 2 polling cycles occurred

        finally:
            await phase_coordinator.stop()


@pytest.mark.unit
def test_mark_phase_running(phase_coordinator, phase_queue_service):
    """Test mark_phase_running() method"""
    # Enqueue phase
    queue_id = phase_queue_service.enqueue(
        parent_issue=1100,
        phase_number=1,
        phase_data={"title": "Phase 1", "content": "Test"},
        depends_on_phase=None,
    )

    # Initially ready
    phase = get_phase_by_id(phase_queue_service, queue_id)
    assert phase.status == "ready"

    # Mark running
    phase_coordinator.mark_phase_running(queue_id)

    # Verify status updated
    phase = get_phase_by_id(phase_queue_service, queue_id)
    assert phase.status == "running"


@pytest.mark.unit
def test_get_ready_phases(phase_coordinator, phase_queue_service):
    """Test get_ready_phases() method"""
    # Enqueue multiple phases with different statuses
    ready_id = phase_queue_service.enqueue(
        parent_issue=1200,
        phase_number=1,
        phase_data={"title": "Ready Phase", "content": "Test"},
        depends_on_phase=None,
    )

    phase_queue_service.enqueue(
        parent_issue=1200,
        phase_number=2,
        phase_data={"title": "Queued Phase", "content": "Test"},
        depends_on_phase=1,
    )

    running_id = phase_queue_service.enqueue(
        parent_issue=1300,
        phase_number=1,
        phase_data={"title": "Running Phase", "content": "Test"},
        depends_on_phase=None,
    )
    phase_queue_service.update_status(running_id, "running")

    # Get ready phases
    ready_phases = phase_coordinator.get_ready_phases()

    # Should only return the ready phase
    assert len(ready_phases) == 1
    assert ready_phases[0].queue_id == ready_id
    assert ready_phases[0].status == "ready"
