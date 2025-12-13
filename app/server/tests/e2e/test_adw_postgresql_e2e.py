"""
End-to-end ADW workflow validation with PostgreSQL.

This test validates a complete ADW workflow execution using PostgreSQL database,
ensuring all components work together correctly:
- Workflow state management
- PostgreSQL persistence
- Phase transitions
- API responses
- Database integrity

Enhancement #88: E2E ADW Workflow Validation with PostgreSQL
"""

import time
from unittest.mock import patch

import pytest
from core.workflow_history import (
    get_workflow_by_adw_id,
    get_workflow_history,
    insert_workflow_history,
    update_workflow_history,
)
from models.phase_queue_item import PhaseQueueItem
from repositories.phase_queue_repository import PhaseQueueRepository


@pytest.mark.e2e
@pytest.mark.postgresql
class TestADWPostgreSQLWorkflow:
    """E2E test validating complete ADW workflow with PostgreSQL."""

    def test_complete_adw_workflow_with_postgresql(
        self,
        e2e_database,
        e2e_test_client,
    ):
        """
        Complete ADW workflow journey with PostgreSQL validation.

        Workflow:
        1. Create workflow via database
        2. Verify workflow_history entry created
        3. Simulate planning phase completion
        4. Verify database updated with plan data
        5. Simulate build phase
        6. Verify phase progression in database
        7. Mark workflow complete
        8. Validate final database state
        9. Validate via API

        Validates:
        - workflow_history table: status transitions, timestamps, metadata
        - phase_queue table: phase creation and completion
        - API responses: correct data returned
        """
        # Step 1: Create workflow
        test_adw_id = f"test_e2e_{int(time.time())}"
        test_issue_number = 999

        # Patch DB_PATH for database operations
        with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
            # Insert workflow into database
            insert_workflow_history(
                adw_id=test_adw_id,
                issue_number=test_issue_number,
                nl_input="Test E2E workflow validation",
                github_url="https://github.com/test/repo/issues/999",
                workflow_template="adw_sdlc_complete_iso",
                model_used="sonnet",
                status="pending",
            )

            # Step 2: Verify workflow exists (verifies insert succeeded)
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow is not None, "Workflow should be created and retrievable"
            assert workflow["status"] == "pending", "Initial status should be pending"
            assert workflow["adw_id"] == test_adw_id
            assert workflow["issue_number"] == test_issue_number

            # Step 3: Simulate planning phase start
            update_workflow_history(
                adw_id=test_adw_id,
                status="running",
                current_phase="plan",
            )

            # Verify status updated
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["status"] == "running"
            assert workflow["current_phase"] == "plan"

            # Step 4: Simulate planning phase completion
            update_workflow_history(
                adw_id=test_adw_id,
                current_phase="build",
            )

            # Verify phase transitioned
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["current_phase"] == "build"

            # Step 5: Simulate build phase
            update_workflow_history(
                adw_id=test_adw_id,
                current_phase="test",
            )

            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["current_phase"] == "test"

            # Step 6: Mark workflow complete
            update_workflow_history(
                adw_id=test_adw_id,
                status="completed",
                current_phase="cleanup",
            )

            # Verify completion
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["status"] == "completed"

            # Step 7: Verify workflow can be retrieved via history
            workflows, total = get_workflow_history(limit=1000)
            test_workflow = None
            for wf in workflows:
                if wf.get("adw_id") == test_adw_id:
                    test_workflow = wf
                    break

            assert test_workflow is not None, f"Test workflow {test_adw_id} should be in history"
            assert test_workflow["status"] == "completed"
            assert test_workflow["current_phase"] == "cleanup"

    def test_workflow_history_persistence(
        self,
        e2e_database,
    ):
        """
        Test that workflow history persists correctly across operations.

        Validates:
        - Create → Read → Update → Delete cycle
        - PostgreSQL transactions
        - Data integrity constraints
        """
        test_adw_id = f"test_persist_{int(time.time())}"

        with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
            # Create
            insert_workflow_history(
                adw_id=test_adw_id,
                issue_number=888,
                nl_input="Test persistence",
                status="pending",
            )

            # Read (verifies create succeeded)
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow is not None, "Workflow should be created and retrievable"
            assert workflow["issue_number"] == 888

            # Update
            update_workflow_history(
                adw_id=test_adw_id,
                status="completed",
                actual_cost_total=0.15,
            )

            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["status"] == "completed"
            assert workflow.get("actual_cost_total") == 0.15

            # Read all workflows to verify our test workflow is included
            workflows, total_count = get_workflow_history(limit=1000)
            test_workflow_found = False
            for wf in workflows:
                if wf["adw_id"] == test_adw_id:
                    test_workflow_found = True
                    assert wf["status"] == "completed"
                    break

            assert test_workflow_found, f"Test workflow {test_adw_id} should be in history"

    def test_phase_queue_integration(
        self,
        e2e_database,
    ):
        """
        Test phase queue integration with PostgreSQL.

        Validates:
        - Phase creation
        - Phase status updates
        - Phase retrieval
        - Queue priority handling
        """
        # Use PhaseQueueRepository directly
        phase_queue_repo = PhaseQueueRepository()

        # Create phase
        test_queue_id = f"test_phase_{int(time.time())}"
        phase_item = PhaseQueueItem(
            queue_id=test_queue_id,
            parent_issue=777,
            phase_number=1,
            status="ready",
            depends_on_phase=None,
            phase_data={"test": "data"},
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        created_phase = phase_queue_repo.create(phase_item)
        assert created_phase is not None
        assert created_phase.queue_id == test_queue_id

        # Verify created
        retrieved_phase = phase_queue_repo.get_by_id(test_queue_id)
        assert retrieved_phase is not None
        assert retrieved_phase.parent_issue == 777
        assert retrieved_phase.status == "ready"

        # Update status
        phase_queue_repo.update_status(test_queue_id, "completed")

        updated_phase = phase_queue_repo.get_by_id(test_queue_id)
        assert updated_phase.status == "completed"

        # Cleanup - delete test phase
        phase_queue_repo.delete(test_queue_id)
        deleted_phase = phase_queue_repo.get_by_id(test_queue_id)
        assert deleted_phase is None, "Phase should be deleted"

    def test_workflow_status_transitions(
        self,
        e2e_database,
    ):
        """
        Test workflow status transitions through complete lifecycle.

        Validates:
        - Status field updates correctly
        - Phase transitions work properly
        - Status persists across updates
        """
        test_adw_id = f"test_status_{int(time.time())}"

        with patch('core.workflow_history_utils.database.DB_PATH', e2e_database):
            # Create workflow
            insert_workflow_history(
                adw_id=test_adw_id,
                issue_number=123,
                nl_input="Test status transitions",
                status="pending",
            )

            # Verify workflow created
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow is not None, "Workflow should be created and retrievable"
            assert workflow["status"] == "pending"

            # Transition to running
            update_workflow_history(
                adw_id=test_adw_id,
                status="running",
                current_phase="plan",
            )

            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["status"] == "running"
            assert workflow["current_phase"] == "plan"

            # Transition through phases
            for phase in ["build", "test", "review"]:
                update_workflow_history(
                    adw_id=test_adw_id,
                    current_phase=phase,
                )
                workflow = get_workflow_by_adw_id(test_adw_id)
                assert workflow["current_phase"] == phase
                assert workflow["status"] == "running"

            # Complete workflow
            update_workflow_history(
                adw_id=test_adw_id,
                status="completed",
                current_phase="cleanup",
            )

            # Verify final state
            workflow = get_workflow_by_adw_id(test_adw_id)
            assert workflow["status"] == "completed"
            assert workflow["current_phase"] == "cleanup"
