"""
E2E Tests for Multi-Phase Workflow Execution

Tests the complete flow of multi-phase workflow execution including:
- Sequential phase execution (Phase 1 → Phase 2 → Phase 3)
- Phase completion triggers next phase
- Phase failure blocks dependent phases
- Workflow history updates correctly
- WebSocket events broadcast correctly
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
def temp_phase_db():
    """Create temporary database for phase queue"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_phase_queue.db")

        # Initialize phase_queue table
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
def temp_workflow_db():
    """Create temporary database for workflow history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_workflow_history.db")

        # Initialize workflow_history table with required fields
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT UNIQUE NOT NULL,
                issue_number INTEGER,
                status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phase_number INTEGER,
                parent_workflow_id TEXT,
                is_multi_phase INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

        yield db_path


@pytest.fixture
def phase_queue_service(temp_phase_db):
    """Create PhaseQueueService with temporary database"""
    return PhaseQueueService(db_path=temp_phase_db)


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for testing broadcasts"""
    mock_manager = AsyncMock()
    mock_manager.broadcast = AsyncMock()
    return mock_manager


@pytest.fixture
def phase_coordinator(phase_queue_service, temp_workflow_db, mock_websocket_manager):
    """Create PhaseCoordinator with test dependencies"""
    coordinator = PhaseCoordinator(
        phase_queue_service=phase_queue_service,
        workflow_db_path=temp_workflow_db,
        poll_interval=0.1,  # Fast polling for tests
        websocket_manager=mock_websocket_manager
    )
    return coordinator


# ============================================================================
# Helper Functions
# ============================================================================


def create_workflow_entry(
    workflow_db_path: str,
    issue_number: int,
    status: str = "running",
    error_message: str | None = None,
    phase_number: int | None = None,
    is_multi_phase: bool = True
):
    """
    Helper to create workflow_history entry.

    Args:
        workflow_db_path: Path to workflow database
        issue_number: GitHub issue number
        status: Workflow status (pending, running, completed, failed)
        error_message: Error message for failed workflows
        phase_number: Phase number (for multi-phase workflows)
        is_multi_phase: Whether this is a multi-phase workflow
    """
    conn = sqlite3.connect(workflow_db_path)
    conn.execute(
        """
        INSERT INTO workflow_history (
            workflow_id, issue_number, status, error_message,
            phase_number, is_multi_phase, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"wf-{issue_number}",
            issue_number,
            status,
            error_message,
            phase_number,
            1 if is_multi_phase else 0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def update_workflow_status(
    workflow_db_path: str,
    issue_number: int,
    status: str,
    error_message: str | None = None
):
    """
    Helper to update workflow status.

    Args:
        workflow_db_path: Path to workflow database
        issue_number: GitHub issue number
        status: New status
        error_message: Error message (for failed status)
    """
    conn = sqlite3.connect(workflow_db_path)
    conn.execute(
        """
        UPDATE workflow_history
        SET status = ?, error_message = ?, updated_at = ?
        WHERE issue_number = ?
        """,
        (status, error_message, datetime.now().isoformat(), issue_number),
    )
    conn.commit()
    conn.close()


def get_phase_status(phase_queue_service: PhaseQueueService, queue_id: str) -> str:
    """Get current status of a phase"""
    items = phase_queue_service.get_all_queued()
    for item in items:
        if item.queue_id == queue_id:
            return item.status
    return None


# ============================================================================
# E2E Tests
# ============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMultiPhaseExecution:
    """E2E tests for multi-phase workflow execution"""

    async def test_sequential_execution_success(
        self,
        phase_queue_service,
        phase_coordinator,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test successful sequential execution of 3 phases.

        Flow:
        1. Enqueue 3 phases for parent issue #100
        2. Phase 1 starts (status=running)
        3. Phase 1 completes → Phase 2 becomes ready
        4. Phase 2 starts (status=running)
        5. Phase 2 completes → Phase 3 becomes ready
        6. Phase 3 starts (status=running)
        7. Phase 3 completes → All phases done
        """
        parent_issue = 100

        # Step 1: Enqueue 3 phases
        phase1_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=1,
            phase_data={"title": "Phase 1: Setup", "content": "Setup database"},
            depends_on_phase=None,
        )

        phase2_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=2,
            phase_data={"title": "Phase 2: API", "content": "Create API"},
            depends_on_phase=1,
        )

        phase3_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=3,
            phase_data={"title": "Phase 3: Tests", "content": "Add tests"},
            depends_on_phase=2,
        )

        # Verify initial states
        assert get_phase_status(phase_queue_service, phase1_queue_id) == "ready"
        assert get_phase_status(phase_queue_service, phase2_queue_id) == "queued"
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "queued"

        # Step 2: Phase 1 starts - assign issue number and mark running
        phase_queue_service.update_issue_number(phase1_queue_id, 101)
        phase_queue_service.update_status(phase1_queue_id, "running")
        create_workflow_entry(temp_workflow_db, 101, status="running", phase_number=1)

        # Step 3: Phase 1 completes
        update_workflow_status(temp_workflow_db, 101, "completed")
        await phase_coordinator._check_workflow_completions()

        # Verify Phase 1 completed and Phase 2 ready
        assert get_phase_status(phase_queue_service, phase1_queue_id) == "completed"
        assert get_phase_status(phase_queue_service, phase2_queue_id) == "ready"
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "queued"

        # Verify WebSocket broadcast for Phase 1 completion
        mock_websocket_manager.broadcast.assert_called()
        broadcast_args = mock_websocket_manager.broadcast.call_args_list[-1][0][0]
        assert broadcast_args["type"] == "queue_update"
        assert broadcast_args["queue_id"] == phase1_queue_id
        assert broadcast_args["status"] == "completed"
        assert broadcast_args["parent_issue"] == parent_issue

        # Step 4: Phase 2 starts
        phase_queue_service.update_issue_number(phase2_queue_id, 102)
        phase_queue_service.update_status(phase2_queue_id, "running")
        create_workflow_entry(temp_workflow_db, 102, status="running", phase_number=2)

        # Step 5: Phase 2 completes
        update_workflow_status(temp_workflow_db, 102, "completed")
        await phase_coordinator._check_workflow_completions()

        # Verify Phase 2 completed and Phase 3 ready
        assert get_phase_status(phase_queue_service, phase2_queue_id) == "completed"
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "ready"

        # Step 6: Phase 3 starts
        phase_queue_service.update_issue_number(phase3_queue_id, 103)
        phase_queue_service.update_status(phase3_queue_id, "running")
        create_workflow_entry(temp_workflow_db, 103, status="running", phase_number=3)

        # Step 7: Phase 3 completes
        update_workflow_status(temp_workflow_db, 103, "completed")
        await phase_coordinator._check_workflow_completions()

        # Verify all phases completed
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "completed"

        # Verify total broadcast count (3 completions)
        assert mock_websocket_manager.broadcast.call_count >= 3

    async def test_failure_blocks_dependents(
        self,
        phase_queue_service,
        phase_coordinator,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test that phase failure blocks all dependent phases.

        Flow:
        1. Enqueue 3 phases for parent issue #200
        2. Phase 1 starts
        3. Phase 1 fails → Phase 2 and 3 become blocked
        """
        parent_issue = 200
        error_message = "Database connection failed"

        # Step 1: Enqueue 3 phases
        phase1_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=1,
            phase_data={"title": "Phase 1: Setup", "content": "Setup database"},
            depends_on_phase=None,
        )

        phase2_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=2,
            phase_data={"title": "Phase 2: API", "content": "Create API"},
            depends_on_phase=1,
        )

        phase3_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=3,
            phase_data={"title": "Phase 3: Tests", "content": "Add tests"},
            depends_on_phase=2,
        )

        # Step 2: Phase 1 starts
        phase_queue_service.update_issue_number(phase1_queue_id, 201)
        phase_queue_service.update_status(phase1_queue_id, "running")
        create_workflow_entry(temp_workflow_db, 201, status="running", phase_number=1)

        # Verify initial states
        assert get_phase_status(phase_queue_service, phase1_queue_id) == "running"
        assert get_phase_status(phase_queue_service, phase2_queue_id) == "queued"
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "queued"

        # Step 3: Phase 1 fails
        update_workflow_status(temp_workflow_db, 201, "failed", error_message)
        await phase_coordinator._check_workflow_completions()

        # Verify Phase 1 failed and Phase 2+3 blocked
        assert get_phase_status(phase_queue_service, phase1_queue_id) == "failed"
        assert get_phase_status(phase_queue_service, phase2_queue_id) == "blocked"
        assert get_phase_status(phase_queue_service, phase3_queue_id) == "blocked"

        # Verify error messages
        items = phase_queue_service.get_all_queued()
        phase1 = next(item for item in items if item.queue_id == phase1_queue_id)
        phase2 = next(item for item in items if item.queue_id == phase2_queue_id)
        phase3 = next(item for item in items if item.queue_id == phase3_queue_id)

        assert phase1.error_message == error_message
        assert "Phase 1 failed" in phase2.error_message
        assert "Phase 1 failed" in phase3.error_message

        # Verify WebSocket broadcasts (failed + 2 blocked)
        assert mock_websocket_manager.broadcast.call_count >= 3

        # Check failed broadcast
        failed_broadcast = None
        for call in mock_websocket_manager.broadcast.call_args_list:
            event = call[0][0]
            if event["queue_id"] == phase1_queue_id:
                failed_broadcast = event
                break

        assert failed_broadcast is not None
        assert failed_broadcast["status"] == "failed"

    async def test_phase_coordinator_polling(
        self,
        phase_queue_service,
        phase_coordinator,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test PhaseCoordinator polling detects completions automatically.

        Flow:
        1. Start PhaseCoordinator background task
        2. Enqueue Phase 1 and start it
        3. Mark workflow completed
        4. Wait for polling to detect completion
        5. Verify Phase 2 becomes ready
        """
        parent_issue = 300

        # Step 1: Start coordinator
        await phase_coordinator.start()

        try:
            # Step 2: Enqueue 2 phases
            phase1_queue_id = phase_queue_service.enqueue(
                parent_issue=parent_issue,
                phase_number=1,
                phase_data={"title": "Phase 1: Setup", "content": "Setup"},
                depends_on_phase=None,
            )

            phase2_queue_id = phase_queue_service.enqueue(
                parent_issue=parent_issue,
                phase_number=2,
                phase_data={"title": "Phase 2: Build", "content": "Build"},
                depends_on_phase=1,
            )

            # Phase 1 starts
            phase_queue_service.update_issue_number(phase1_queue_id, 301)
            phase_queue_service.update_status(phase1_queue_id, "running")
            create_workflow_entry(temp_workflow_db, 301, status="running", phase_number=1)

            # Step 3: Mark workflow completed
            update_workflow_status(temp_workflow_db, 301, "completed")

            # Step 4: Wait for polling (poll_interval=0.1s, wait 0.5s to be safe)
            await asyncio.sleep(0.5)

            # Step 5: Verify Phase 1 completed and Phase 2 ready
            assert get_phase_status(phase_queue_service, phase1_queue_id) == "completed"
            assert get_phase_status(phase_queue_service, phase2_queue_id) == "ready"

            # Verify broadcast called
            assert mock_websocket_manager.broadcast.call_count > 0

        finally:
            # Stop coordinator
            await phase_coordinator.stop()

    async def test_concurrent_phase_monitoring(
        self,
        phase_queue_service,
        phase_coordinator,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test monitoring multiple phases from different parent issues concurrently.

        Flow:
        1. Enqueue phases for two different parent issues (400, 500)
        2. Start Phase 1 for both parents
        3. Complete both phases
        4. Verify both Phase 2s become ready
        """
        parent_issue_1 = 400
        parent_issue_2 = 500

        # Enqueue phases for parent 1
        p1_phase1_id = phase_queue_service.enqueue(
            parent_issue=parent_issue_1,
            phase_number=1,
            phase_data={"title": "Parent 1 - Phase 1", "content": "Setup"},
            depends_on_phase=None,
        )

        p1_phase2_id = phase_queue_service.enqueue(
            parent_issue=parent_issue_1,
            phase_number=2,
            phase_data={"title": "Parent 1 - Phase 2", "content": "Build"},
            depends_on_phase=1,
        )

        # Enqueue phases for parent 2
        p2_phase1_id = phase_queue_service.enqueue(
            parent_issue=parent_issue_2,
            phase_number=1,
            phase_data={"title": "Parent 2 - Phase 1", "content": "Setup"},
            depends_on_phase=None,
        )

        p2_phase2_id = phase_queue_service.enqueue(
            parent_issue=parent_issue_2,
            phase_number=2,
            phase_data={"title": "Parent 2 - Phase 2", "content": "Build"},
            depends_on_phase=1,
        )

        # Start both Phase 1s
        phase_queue_service.update_issue_number(p1_phase1_id, 401)
        phase_queue_service.update_status(p1_phase1_id, "running")
        create_workflow_entry(temp_workflow_db, 401, status="running", phase_number=1)

        phase_queue_service.update_issue_number(p2_phase1_id, 501)
        phase_queue_service.update_status(p2_phase1_id, "running")
        create_workflow_entry(temp_workflow_db, 501, status="running", phase_number=1)

        # Complete both workflows
        update_workflow_status(temp_workflow_db, 401, "completed")
        update_workflow_status(temp_workflow_db, 501, "completed")

        # Run coordinator check
        await phase_coordinator._check_workflow_completions()

        # Verify both Phase 1s completed and Phase 2s ready
        assert get_phase_status(phase_queue_service, p1_phase1_id) == "completed"
        assert get_phase_status(phase_queue_service, p1_phase2_id) == "ready"
        assert get_phase_status(phase_queue_service, p2_phase1_id) == "completed"
        assert get_phase_status(phase_queue_service, p2_phase2_id) == "ready"

        # Verify broadcasts for both completions
        assert mock_websocket_manager.broadcast.call_count >= 2

    async def test_workflow_not_found_graceful_handling(
        self,
        phase_queue_service,
        phase_coordinator,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test graceful handling when workflow not found in workflow_history.

        This can happen if:
        - Workflow hasn't started yet
        - Workflow entry hasn't been created
        - Database sync issues
        """
        parent_issue = 600

        # Enqueue phase
        phase1_queue_id = phase_queue_service.enqueue(
            parent_issue=parent_issue,
            phase_number=1,
            phase_data={"title": "Phase 1", "content": "Setup"},
            depends_on_phase=None,
        )

        # Mark running but DON'T create workflow entry
        phase_queue_service.update_issue_number(phase1_queue_id, 601)
        phase_queue_service.update_status(phase1_queue_id, "running")

        # Run coordinator check - should not crash
        await phase_coordinator._check_workflow_completions()

        # Verify phase still running (no change)
        assert get_phase_status(phase_queue_service, phase1_queue_id) == "running"

        # No broadcasts should occur
        assert mock_websocket_manager.broadcast.call_count == 0

    async def test_error_in_polling_loop_does_not_crash(
        self,
        phase_queue_service,
        temp_workflow_db,
        mock_websocket_manager
    ):
        """
        Test that errors in polling loop are caught and logged without crashing.
        """
        # Create coordinator with invalid workflow DB path to trigger errors
        bad_coordinator = PhaseCoordinator(
            phase_queue_service=phase_queue_service,
            workflow_db_path="/nonexistent/path/to/db.db",
            poll_interval=0.1,
            websocket_manager=mock_websocket_manager
        )

        await bad_coordinator.start()

        try:
            # Let it run for a bit - should log errors but not crash
            await asyncio.sleep(0.3)

            # Coordinator should still be running
            assert bad_coordinator._is_running is True

        finally:
            await bad_coordinator.stop()
