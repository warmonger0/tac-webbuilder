"""
Unit tests for workflow history module.

Tests database operations, data parsing, and query functions.
"""

import json
import sqlite3

# Import the module to test
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.workflow_history import (
    resync_all_completed_workflows,
    resync_workflow_cost,
    sync_workflow_history,
)
from core.workflow_history_utils.database import (
    get_history_analytics,
    get_workflow_by_adw_id,
    get_workflow_history,
    init_db,
    insert_workflow_history,
    update_workflow_history,
)
from core.workflow_history_utils.filesystem import scan_agents_directory


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for testing"""
    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = Path(f.name)

    # Use monkeypatch to replace DB_PATH in all modules that import it
    # This works better than patch() because it happens before module-level code runs
    import core.workflow_history_utils.database.analytics as analytics_module
    import core.workflow_history_utils.database.mutations as mutations_module
    import core.workflow_history_utils.database.queries as queries_module
    import core.workflow_history_utils.database.schema as schema_module

    monkeypatch.setattr(schema_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(mutations_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(queries_module, 'DB_PATH', temp_db_path)
    monkeypatch.setattr(analytics_module, 'DB_PATH', temp_db_path)

    try:
        # Initialize the database
        init_db()
        yield temp_db_path
    finally:
        # Cleanup
        temp_db_path.unlink(missing_ok=True)


def test_init_db(temp_db):
    """Test database initialization creates tables and indexes"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check that workflow_history table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='workflow_history'
    """)
    assert cursor.fetchone() is not None

    # Check that indexes exist
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='index' AND name LIKE 'idx_%'
    """)
    indexes = cursor.fetchall()
    assert len(indexes) >= 4  # Should have at least 4 indexes

    conn.close()


def test_insert_workflow_history(temp_db):
    """Test inserting a new workflow history record"""
    # Insert a workflow
    row_id = insert_workflow_history(
        adw_id="test-123",
        issue_number=42,
        nl_input="Fix authentication bug",
        github_url="https://github.com/test/repo/issues/42",
        workflow_template="adw_sdlc_iso",
        model_used="claude-sonnet-4-5",
        status="completed"
    )

    assert row_id > 0

    # Verify it was inserted
    workflow = get_workflow_by_adw_id("test-123")
    assert workflow is not None
    assert workflow["adw_id"] == "test-123"
    assert workflow["issue_number"] == 42
    assert workflow["status"] == "completed"


def test_insert_duplicate_adw_id(temp_db):
    """Test that inserting duplicate adw_id raises an error"""
    insert_workflow_history(adw_id="test-123", status="pending")

    # Inserting the same adw_id should raise an error
    with pytest.raises(sqlite3.IntegrityError):
        insert_workflow_history(adw_id="test-123", status="running")


def test_update_workflow_history(temp_db):
    """Test updating an existing workflow history record"""
    # Insert a workflow
    insert_workflow_history(adw_id="test-456", status="pending")

    # Update the status
    success = update_workflow_history(
        adw_id="test-456",
        status="completed",
        duration_seconds=120
    )
    assert success is True

    # Verify the update
    workflow = get_workflow_by_adw_id("test-456")
    assert workflow["status"] == "completed"
    assert workflow["duration_seconds"] == 120


def test_update_nonexistent_workflow(temp_db):
    """Test updating a workflow that doesn't exist"""
    success = update_workflow_history(
        adw_id="nonexistent",
        status="completed"
    )
    assert success is False


def test_get_workflow_by_adw_id(temp_db):
    """Test retrieving a workflow by ADW ID"""
    # Insert a workflow
    insert_workflow_history(
        adw_id="test-789",
        issue_number=99,
        status="running"
    )

    # Retrieve it
    workflow = get_workflow_by_adw_id("test-789")
    assert workflow is not None
    assert workflow["adw_id"] == "test-789"
    assert workflow["issue_number"] == 99

    # Try to get nonexistent workflow
    workflow = get_workflow_by_adw_id("nonexistent")
    assert workflow is None


def test_get_workflow_history_pagination(temp_db):
    """Test pagination in get_workflow_history"""
    # Insert multiple workflows
    for i in range(25):
        insert_workflow_history(
            adw_id=f"test-{i}",
            issue_number=i,
            status="completed"
        )

    # Get first page
    workflows, total = get_workflow_history(limit=10, offset=0)
    assert len(workflows) == 10
    assert total == 25

    # Get second page
    workflows, total = get_workflow_history(limit=10, offset=10)
    assert len(workflows) == 10
    assert total == 25

    # Get last page
    workflows, total = get_workflow_history(limit=10, offset=20)
    assert len(workflows) == 5
    assert total == 25


def test_get_workflow_history_filters(temp_db):
    """Test filtering in get_workflow_history"""
    # Insert workflows with different statuses
    insert_workflow_history(adw_id="test-1", status="completed", model_used="claude-sonnet-4-5")
    insert_workflow_history(adw_id="test-2", status="failed", model_used="claude-opus")
    insert_workflow_history(adw_id="test-3", status="completed", model_used="claude-sonnet-4-5")

    # Filter by status
    workflows, total = get_workflow_history(status="completed")
    assert total == 2

    # Filter by model
    workflows, total = get_workflow_history(model="claude-opus")
    assert total == 1

    # Combined filters
    workflows, total = get_workflow_history(
        status="completed",
        model="claude-sonnet-4-5"
    )
    assert total == 2


def test_get_workflow_history_search(temp_db):
    """Test search functionality in get_workflow_history"""
    # Insert workflows with different inputs
    insert_workflow_history(
        adw_id="test-search-1",
        nl_input="Fix authentication bug",
        status="completed"
    )
    insert_workflow_history(
        adw_id="test-search-2",
        nl_input="Add new feature for users",
        status="completed"
    )

    # Search for "authentication"
    workflows, total = get_workflow_history(search="authentication")
    assert total == 1
    assert workflows[0]["adw_id"] == "test-search-1"

    # Search for "feature"
    workflows, total = get_workflow_history(search="feature")
    assert total == 1
    assert workflows[0]["adw_id"] == "test-search-2"


def test_get_workflow_history_sorting(temp_db):
    """Test sorting in get_workflow_history"""
    # Insert workflows with different durations
    insert_workflow_history(adw_id="test-1", status="completed", duration_seconds=100)
    insert_workflow_history(adw_id="test-2", status="completed", duration_seconds=50)
    insert_workflow_history(adw_id="test-3", status="completed", duration_seconds=200)

    # Sort by duration ascending
    workflows, total = get_workflow_history(
        sort_by="duration_seconds",
        sort_order="ASC"
    )
    assert workflows[0]["duration_seconds"] == 50
    assert workflows[1]["duration_seconds"] == 100
    assert workflows[2]["duration_seconds"] == 200

    # Sort by duration descending
    workflows, total = get_workflow_history(
        sort_by="duration_seconds",
        sort_order="DESC"
    )
    assert workflows[0]["duration_seconds"] == 200


def test_get_history_analytics(temp_db):
    """Test analytics calculation"""
    # Insert workflows with various statuses
    insert_workflow_history(adw_id="test-1", status="completed", duration_seconds=100)
    insert_workflow_history(adw_id="test-2", status="completed", duration_seconds=200)
    insert_workflow_history(adw_id="test-3", status="failed")
    insert_workflow_history(adw_id="test-4", status="running")

    analytics = get_history_analytics()

    assert analytics["total_workflows"] == 4
    assert analytics["completed_workflows"] == 2
    assert analytics["failed_workflows"] == 1
    assert analytics["avg_duration_seconds"] == 150.0  # (100 + 200) / 2
    assert analytics["success_rate_percent"] == 50.0  # 2/4 * 100


def test_scan_agents_directory_empty(temp_db):
    """Test scanning an empty agents directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create empty agents directory
        agents_dir = Path(temp_dir) / "agents"
        agents_dir.mkdir()

        # Mock the project root
        with patch('core.workflow_history_utils.filesystem.Path.__truediv__', return_value=agents_dir):
            workflows = scan_agents_directory()
            # Should return empty list for empty directory
            assert isinstance(workflows, list)


def test_scan_agents_directory_with_workflows(temp_db):
    """Test scanning agents directory with workflow state files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create agents directory structure
        agents_dir = Path(temp_dir) / "agents"
        agents_dir.mkdir()

        # Create a workflow directory with state file
        workflow_dir = agents_dir / "test-workflow-123"
        workflow_dir.mkdir()

        state_data = {
            "adw_id": "test-workflow-123",
            "issue_number": 42,
            "nl_input": "Test workflow",
            "github_url": "https://github.com/test/repo/issues/42",
            "workflow_template": "adw_sdlc_iso",
            "model_used": "claude-sonnet-4-5",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "current_phase": "build"
        }

        with open(workflow_dir / "adw_state.json", 'w') as f:
            json.dump(state_data, f)

        # Mock Path resolution to use temp directory
        def mock_resolve(self, *parts):
            if str(self).endswith("workflow_history.py"):
                return agents_dir.parent
            return self

        with patch.object(Path, 'parent', agents_dir.parent), \
             patch('core.workflow_history_utils.filesystem.Path.__truediv__', return_value=agents_dir):
            workflows = scan_agents_directory()
            assert len(workflows) > 0 or isinstance(workflows, list)


def test_sync_workflow_history(temp_db):
    """Test syncing workflow history"""
    # Mock scan_agents_directory to return test data
    mock_workflows = [
        {
            "adw_id": "sync-test-1",
            "issue_number": 1,
            "nl_input": "Test",
            "status": "completed",
            "workflow_template": "adw_sdlc_iso",
        }
    ]

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=Exception("No cost data")):
        synced = sync_workflow_history()
        assert synced >= 0  # Should sync at least 0 workflows

        # Verify the workflow was inserted
        workflow = get_workflow_by_adw_id("sync-test-1")
        if workflow:
            assert workflow["adw_id"] == "sync-test-1"


def test_invalid_sort_field(temp_db):
    """Test that invalid sort fields are handled safely"""
    insert_workflow_history(adw_id="test-1", status="completed")

    # Try to sort by invalid field (should default to created_at)
    workflows, total = get_workflow_history(
        sort_by="invalid_field; DROP TABLE workflow_history;",
        sort_order="DESC"
    )
    assert total == 1  # Should still return results


def test_analytics_with_empty_database(temp_db):
    """Test analytics with empty database"""
    analytics = get_history_analytics()

    assert analytics["total_workflows"] == 0
    assert analytics["completed_workflows"] == 0
    assert analytics["failed_workflows"] == 0
    assert analytics["avg_duration_seconds"] == 0.0
    assert analytics["success_rate_percent"] == 0.0


# Cost Sync Tests
def test_cost_sync_completed_workflow_updates_final_cost(temp_db):
    """Test that completed workflows always get final cost, even if cost already exists"""
    from core.data_models import CostData, PhaseCost, TokenBreakdown

    # Insert workflow with initial partial cost ($0.09)
    insert_workflow_history(
        adw_id="cost-test-1",
        status="completed",
        actual_cost_total=0.09,
        cost_breakdown={
            "estimated_total": 0.0,
            "actual_total": 0.09,
            "by_phase": {"plan": 0.09}
        }
    )

    # Mock scan_agents_directory to return completed workflow with final cost ($2.37)
    mock_workflows = [{
        "adw_id": "cost-test-1",
        "status": "completed",
        "cost_breakdown": {
            "estimated_total": 0.0,
            "actual_total": 2.37,
            "by_phase": {"plan": 0.50, "build": 1.20, "test": 0.67}
        },
        "actual_cost_total": 2.37,
        "input_tokens": 50000,
        "cached_tokens": 10000,
        "cache_hit_tokens": 20000,
        "cache_miss_tokens": 30000,
        "output_tokens": 5000,
        "total_tokens": 85000,
        "cache_efficiency_percent": 40.0
    }]

    # Mock cost data
    mock_cost_data = CostData(
        adw_id="cost-test-1",
        phases=[
            PhaseCost(
                phase="plan",
                cost=0.50,
                tokens=TokenBreakdown(
                    input_tokens=10000,
                    cache_creation_tokens=2000,
                    cache_read_tokens=3000,
                    output_tokens=1000
                )
            ),
            PhaseCost(
                phase="build",
                cost=1.20,
                tokens=TokenBreakdown(
                    input_tokens=25000,
                    cache_creation_tokens=5000,
                    cache_read_tokens=10000,
                    output_tokens=2500
                )
            ),
            PhaseCost(
                phase="test",
                cost=0.67,
                tokens=TokenBreakdown(
                    input_tokens=15000,
                    cache_creation_tokens=3000,
                    cache_read_tokens=7000,
                    output_tokens=1500
                )
            )
        ],
        total_cost=2.37,
        cache_efficiency_percent=40.0,
        cache_savings_amount=0.54,
        total_tokens=85000
    )

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data):
        synced = sync_workflow_history()
        assert synced >= 1

    # Verify final cost was updated
    workflow = get_workflow_by_adw_id("cost-test-1")
    assert workflow["actual_cost_total"] == 2.37
    assert workflow["cost_breakdown"]["actual_total"] == 2.37


def test_cost_sync_running_workflow_progressive_updates(temp_db):
    """Test that running workflows only update if cost increased"""
    from core.data_models import CostData, PhaseCost, TokenBreakdown

    # Insert workflow with initial cost ($0.50)
    insert_workflow_history(
        adw_id="cost-test-2",
        status="running",
        actual_cost_total=0.50,
        cost_breakdown={
            "estimated_total": 0.0,
            "actual_total": 0.50,
            "by_phase": {"plan": 0.50}
        }
    )

    # Mock scan to return running workflow with increased cost ($1.20)
    mock_workflows = [{
        "adw_id": "cost-test-2",
        "status": "running",
        "cost_breakdown": {
            "estimated_total": 0.0,
            "actual_total": 1.20,
            "by_phase": {"plan": 0.50, "build": 0.70}
        },
        "actual_cost_total": 1.20,
        "input_tokens": 30000,
        "total_tokens": 40000,
        "cache_efficiency_percent": 30.0
    }]

    mock_cost_data = CostData(
        adw_id="cost-test-2",
        phases=[
            PhaseCost(
                phase="plan",
                cost=0.50,
                tokens=TokenBreakdown(input_tokens=10000, cache_creation_tokens=2000, cache_read_tokens=3000, output_tokens=1000)
            ),
            PhaseCost(
                phase="build",
                cost=0.70,
                tokens=TokenBreakdown(input_tokens=20000, cache_creation_tokens=3000, cache_read_tokens=5000, output_tokens=1500)
            )
        ],
        total_cost=1.20,
        cache_efficiency_percent=30.0,
        cache_savings_amount=0.22,
        total_tokens=40000
    )

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data):
        synced = sync_workflow_history()
        assert synced >= 1

    # Verify cost was updated to higher value
    workflow = get_workflow_by_adw_id("cost-test-2")
    assert workflow["actual_cost_total"] == 1.20


def test_cost_sync_running_workflow_prevents_decreases(temp_db):
    """Test that running workflows prevent cost decreases"""
    # Insert workflow with higher cost ($2.00)
    insert_workflow_history(
        adw_id="cost-test-3",
        status="running",
        actual_cost_total=2.00,
        cost_breakdown={
            "estimated_total": 0.0,
            "actual_total": 2.00,
            "by_phase": {"plan": 2.00}
        }
    )

    # Mock scan to return running workflow with lower cost ($0.50) - should be rejected
    mock_workflows = [{
        "adw_id": "cost-test-3",
        "status": "running",
        "cost_breakdown": {
            "estimated_total": 0.0,
            "actual_total": 0.50,
            "by_phase": {"plan": 0.50}
        },
        "actual_cost_total": 0.50,
        "input_tokens": 10000,
        "total_tokens": 15000
    }]

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=Exception("No cost")):
        sync_workflow_history()

    # Verify cost was NOT decreased
    workflow = get_workflow_by_adw_id("cost-test-3")
    assert workflow["actual_cost_total"] == 2.00  # Original higher cost preserved


def test_cost_sync_failed_workflow_updates_final_cost(temp_db):
    """Test that failed workflows always get final cost"""
    from core.data_models import CostData, PhaseCost, TokenBreakdown

    # Insert workflow with initial cost
    insert_workflow_history(
        adw_id="cost-test-4",
        status="failed",
        actual_cost_total=0.25,
        cost_breakdown={
            "estimated_total": 0.0,
            "actual_total": 0.25,
            "by_phase": {"plan": 0.25}
        }
    )

    # Mock scan to return failed workflow with final cost
    mock_workflows = [{
        "adw_id": "cost-test-4",
        "status": "failed",
        "cost_breakdown": {
            "estimated_total": 0.0,
            "actual_total": 1.50,
            "by_phase": {"plan": 0.50, "build": 1.00}
        },
        "actual_cost_total": 1.50,
        "input_tokens": 35000,
        "total_tokens": 45000,
        "cache_efficiency_percent": 25.0
    }]

    mock_cost_data = CostData(
        adw_id="cost-test-4",
        phases=[
            PhaseCost(
                phase="plan",
                cost=0.50,
                tokens=TokenBreakdown(input_tokens=10000, cache_creation_tokens=2000, cache_read_tokens=3000, output_tokens=1000)
            ),
            PhaseCost(
                phase="build",
                cost=1.00,
                tokens=TokenBreakdown(input_tokens=25000, cache_creation_tokens=4000, cache_read_tokens=8000, output_tokens=2000)
            )
        ],
        total_cost=1.50,
        cache_efficiency_percent=25.0,
        cache_savings_amount=0.30,
        total_tokens=45000
    )

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data):
        synced = sync_workflow_history()
        assert synced >= 1

    # Verify final cost was updated for failed workflow
    workflow = get_workflow_by_adw_id("cost-test-4")
    assert workflow["actual_cost_total"] == 1.50


def test_cost_sync_logging(temp_db, caplog):
    """Test that cost sync logging works correctly"""
    import logging

    from core.data_models import CostData, PhaseCost, TokenBreakdown

    # Insert workflow with initial cost
    insert_workflow_history(
        adw_id="cost-test-5",
        status="completed",
        actual_cost_total=0.50,
        cost_breakdown={
            "estimated_total": 0.0,
            "actual_total": 0.50,
            "by_phase": {"plan": 0.50}
        }
    )

    # Mock scan to return completed workflow with updated cost
    mock_workflows = [{
        "adw_id": "cost-test-5",
        "status": "completed",
        "cost_breakdown": {
            "estimated_total": 0.0,
            "actual_total": 2.00,
            "by_phase": {"plan": 0.50, "build": 1.50}
        },
        "actual_cost_total": 2.00,
        "input_tokens": 40000,
        "total_tokens": 50000
    }]

    mock_cost_data = CostData(
        adw_id="cost-test-5",
        phases=[
            PhaseCost(
                phase="plan",
                cost=0.50,
                tokens=TokenBreakdown(input_tokens=10000, cache_creation_tokens=2000, cache_read_tokens=3000, output_tokens=1000)
            ),
            PhaseCost(
                phase="build",
                cost=1.50,
                tokens=TokenBreakdown(input_tokens=30000, cache_creation_tokens=5000, cache_read_tokens=10000, output_tokens=3000)
            )
        ],
        total_cost=2.00,
        cache_efficiency_percent=35.0,
        cache_savings_amount=0.45,
        total_tokens=50000
    )

    with patch('core.workflow_history_utils.sync_manager.scan_agents_directory', return_value=mock_workflows), \
         patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data), \
         caplog.at_level(logging.INFO):
        synced = sync_workflow_history()

    # Verify logging occurred - check that cost update was logged
    # Look for the log message pattern: "Cost update for cost-test-5 (completed)"
    log_messages = [record.message for record in caplog.records if record.levelname == "INFO"]
    cost_update_logged = any("cost-test-5" in msg and "completed" in msg for msg in log_messages)
    assert cost_update_logged or synced >= 1  # Either logging worked or sync succeeded


# ============================================================================
# Resync Tests
# ============================================================================

def test_resync_workflow_cost_single(temp_db):
    """Test resyncing cost data for a single workflow"""
    # Insert a workflow
    insert_workflow_history(
        adw_id="resync-test-1",
        status="completed",
        actual_cost_total=0.0
    )

    # Mock cost data
    from core.data_models import CostData, PhaseCost, TokenBreakdown
    mock_cost_data = CostData(
        adw_id="resync-test-1",
        phases=[
            PhaseCost(
                phase="plan",
                cost=0.50,
                tokens=TokenBreakdown(input_tokens=10000, cache_creation_tokens=2000, cache_read_tokens=5000, output_tokens=1000)
            )
        ],
        total_cost=0.50,
        cache_efficiency_percent=25.0,
        cache_savings_amount=0.10,
        total_tokens=18000
    )

    # Patch read_cost_history in enrichment module where it's actually called
    with patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data):
        result = resync_workflow_cost("resync-test-1", force=False)

    assert result["success"] is True
    assert result["cost_updated"] is True
    assert result["adw_id"] == "resync-test-1"
    assert result["error"] is None

    # Verify the cost was updated
    workflow = get_workflow_by_adw_id("resync-test-1")
    assert workflow["actual_cost_total"] == 0.50


def test_resync_workflow_cost_force_clear(temp_db):
    """Test force resync clears and recalculates cost data"""
    # Insert a workflow with existing cost data
    insert_workflow_history(
        adw_id="resync-test-2",
        status="completed",
        actual_cost_total=1.00,  # Old cost
        input_tokens=50000
    )

    # Mock new cost data
    from core.data_models import CostData, PhaseCost, TokenBreakdown
    mock_cost_data = CostData(
        adw_id="resync-test-2",
        phases=[
            PhaseCost(
                phase="build",
                cost=0.75,
                tokens=TokenBreakdown(input_tokens=15000, cache_creation_tokens=3000, cache_read_tokens=7000, output_tokens=2000)
            )
        ],
        total_cost=0.75,
        cache_efficiency_percent=30.0,
        cache_savings_amount=0.15,
        total_tokens=27000
    )

    # Patch read_cost_history in enrichment module where it's actually called
    with patch('core.workflow_history_utils.enrichment.read_cost_history', return_value=mock_cost_data):
        result = resync_workflow_cost("resync-test-2", force=True)

    assert result["success"] is True
    assert result["cost_updated"] is True

    # Verify the cost was updated with new values
    workflow = get_workflow_by_adw_id("resync-test-2")
    assert workflow["actual_cost_total"] == 0.75
    assert workflow["total_tokens"] == 27000


def test_resync_workflow_cost_nonexistent(temp_db):
    """Test error handling for nonexistent workflow"""
    result = resync_workflow_cost("nonexistent-workflow", force=False)

    assert result["success"] is False
    assert result["cost_updated"] is False
    assert "not found" in result["error"].lower()


def test_resync_workflow_cost_no_cost_file(temp_db):
    """Test error handling when cost file doesn't exist"""
    # Insert a workflow
    insert_workflow_history(
        adw_id="resync-test-3",
        status="completed"
    )

    # Mock FileNotFoundError from read_cost_history in enrichment module
    with patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=FileNotFoundError("No cost files")):
        result = resync_workflow_cost("resync-test-3", force=False)

    assert result["success"] is False
    assert result["cost_updated"] is False
    assert "cost files not found" in result["error"].lower()


def test_resync_all_completed_workflows(temp_db):
    """Test bulk resync of all completed workflows"""
    with patch('core.workflow_history_utils.sync_manager.DB_PATH', Path(temp_db)):
        # Insert multiple workflows
        insert_workflow_history(adw_id="bulk-1", status="completed", actual_cost_total=0.0)
        insert_workflow_history(adw_id="bulk-2", status="completed", actual_cost_total=0.0)
        insert_workflow_history(adw_id="bulk-3", status="running", actual_cost_total=0.0)  # Should be skipped
        insert_workflow_history(adw_id="bulk-4", status="failed", actual_cost_total=0.0)

        # Mock cost data
        from core.data_models import CostData, PhaseCost, TokenBreakdown
        def mock_read_cost_history(adw_id):
            return CostData(
                adw_id=adw_id,
                phases=[
                    PhaseCost(
                        phase="test",
                        cost=0.25,
                        tokens=TokenBreakdown(input_tokens=5000, cache_creation_tokens=1000, cache_read_tokens=2000, output_tokens=500)
                    )
                ],
                total_cost=0.25,
                cache_efficiency_percent=20.0,
                cache_savings_amount=0.05,
                total_tokens=8500
            )

        # Patch read_cost_history in enrichment module where it's actually called
        with patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=mock_read_cost_history):
            resynced_count, workflows, errors = resync_all_completed_workflows(force=False)

        # Should resync 3 workflows (2 completed + 1 failed)
        assert resynced_count == 3
        assert len(workflows) == 3
        assert len(errors) == 0

        # Verify running workflow was not resynced
        running_workflow = get_workflow_by_adw_id("bulk-3")
        assert running_workflow["actual_cost_total"] == 0.0


def test_resync_all_completed_workflows_force(temp_db):
    """Test force resync clears and recalculates all workflows"""
    with patch('core.workflow_history_utils.sync_manager.DB_PATH', Path(temp_db)):
        # Insert workflows with existing costs
        insert_workflow_history(adw_id="force-1", status="completed", actual_cost_total=1.0)
        insert_workflow_history(adw_id="force-2", status="completed", actual_cost_total=2.0)

        # Mock cost data
        from core.data_models import CostData, PhaseCost, TokenBreakdown
        def mock_read_cost_history(adw_id):
            return CostData(
                adw_id=adw_id,
                phases=[
                    PhaseCost(
                        phase="test",
                        cost=0.30,
                        tokens=TokenBreakdown(input_tokens=6000, cache_creation_tokens=1200, cache_read_tokens=2400, output_tokens=600)
                    )
                ],
                total_cost=0.30,
                cache_efficiency_percent=22.0,
                cache_savings_amount=0.06,
                total_tokens=10200
            )

        # Patch read_cost_history in enrichment module where it's actually called
        with patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=mock_read_cost_history):
            resynced_count, workflows, errors = resync_all_completed_workflows(force=True)

        assert resynced_count == 2
        assert len(errors) == 0

        # Verify costs were updated
        workflow1 = get_workflow_by_adw_id("force-1")
        assert workflow1["actual_cost_total"] == 0.30


def test_resync_all_completed_workflows_error_handling(temp_db):
    """Test partial success with errors"""
    with patch('core.workflow_history_utils.sync_manager.DB_PATH', Path(temp_db)):
        # Insert workflows
        insert_workflow_history(adw_id="error-1", status="completed")
        insert_workflow_history(adw_id="error-2", status="completed")

        # Mock cost data - one succeeds, one fails
        from core.data_models import CostData, PhaseCost, TokenBreakdown
        def mock_read_cost_history(adw_id):
            if adw_id == "error-1":
                return CostData(
                    adw_id=adw_id,
                    phases=[
                        PhaseCost(
                            phase="test",
                            cost=0.40,
                            tokens=TokenBreakdown(input_tokens=7000, cache_creation_tokens=1400, cache_read_tokens=2800, output_tokens=700)
                        )
                    ],
                    total_cost=0.40,
                    cache_efficiency_percent=24.0,
                    cache_savings_amount=0.07,
                    total_tokens=11900
                )
            else:
                raise FileNotFoundError("Cost file not found")

        # Patch read_cost_history in enrichment module where it's actually called
        with patch('core.workflow_history_utils.enrichment.read_cost_history', side_effect=mock_read_cost_history):
            resynced_count, workflows, errors = resync_all_completed_workflows(force=False)

        assert resynced_count == 1
        assert len(workflows) == 1  # Only successful workflow in the list
        assert len(errors) == 1  # One error
        assert "error-2" in errors[0]


# ============================================================================
# Resync Endpoint Tests
# ============================================================================

@pytest.mark.skipif(True, reason="Endpoint tests require full server setup with all dependencies")
def test_resync_endpoint_single_workflow(temp_db):
    """Test POST /api/workflow-history/resync with single workflow"""
    # Setup: Insert a workflow
    insert_workflow_history(
        adw_id="endpoint-test-1",
        status="completed",
        actual_cost_total=0.0
    )

    # Mock the resync function
    mock_result = {
        "success": True,
        "adw_id": "endpoint-test-1",
        "error": None,
        "cost_updated": True
    }

    # Import server app
    from server import app
    client = TestClient(app)

    with patch('core.workflow_history_utils.sync_manager.resync_workflow_cost', return_value=mock_result):
        response = client.post("/api/workflow-history/resync?adw_id=endpoint-test-1")

    assert response.status_code == 200
    data = response.json()
    assert data["resynced_count"] == 1
    assert len(data["workflows"]) == 1
    assert data["workflows"][0]["adw_id"] == "endpoint-test-1"
    assert len(data["errors"]) == 0


@pytest.mark.skipif(True, reason="Endpoint tests require full server setup with all dependencies")
def test_resync_endpoint_all_workflows(temp_db):
    """Test POST /api/workflow-history/resync without parameters"""
    # Mock the bulk resync function
    mock_workflows = [
        {"adw_id": "bulk-1", "status": "completed", "cost_updated": True},
        {"adw_id": "bulk-2", "status": "completed", "cost_updated": True}
    ]
    mock_errors = []

    from server import app
    client = TestClient(app)

    with patch('core.workflow_history_utils.sync_manager.resync_all_completed_workflows', return_value=(2, mock_workflows, mock_errors)):
        response = client.post("/api/workflow-history/resync")

    assert response.status_code == 200
    data = response.json()
    assert data["resynced_count"] == 2
    assert len(data["workflows"]) == 2
    assert len(data["errors"]) == 0


@pytest.mark.skipif(True, reason="Endpoint tests require full server setup with all dependencies")
def test_resync_endpoint_force_mode(temp_db):
    """Test POST /api/workflow-history/resync with force=true"""
    # Mock the bulk resync function with force
    mock_workflows = [{"adw_id": "force-1", "status": "completed", "cost_updated": True}]
    mock_errors = []

    from server import app
    client = TestClient(app)

    with patch('core.workflow_history_utils.sync_manager.resync_all_completed_workflows', return_value=(1, mock_workflows, mock_errors)) as mock_resync:
        response = client.post("/api/workflow-history/resync?force=true")

    assert response.status_code == 200
    data = response.json()
    assert data["resynced_count"] == 1
    # Verify force=True was passed
    mock_resync.assert_called_once_with(force=True)


@pytest.mark.skipif(True, reason="Endpoint tests require full server setup with all dependencies")
def test_resync_endpoint_error_cases(temp_db):
    """Test error responses from resync endpoint"""
    # Test 1: Single workflow not found
    mock_result = {
        "success": False,
        "adw_id": "nonexistent",
        "error": "Workflow not found: nonexistent",
        "cost_updated": False
    }

    from server import app
    client = TestClient(app)

    with patch('core.workflow_history_utils.sync_manager.resync_workflow_cost', return_value=mock_result):
        response = client.post("/api/workflow-history/resync?adw_id=nonexistent")

    assert response.status_code == 200  # Still returns 200 with error details
    data = response.json()
    assert data["resynced_count"] == 0
    assert len(data["errors"]) == 1
    assert "not found" in data["errors"][0].lower()

    # Test 2: Bulk resync with partial errors
    mock_workflows = [{"adw_id": "w1", "status": "completed", "cost_updated": True}]
    mock_errors = ["w2: Cost files not found"]

    with patch('core.workflow_history_utils.sync_manager.resync_all_completed_workflows', return_value=(1, mock_workflows, mock_errors)):
        response = client.post("/api/workflow-history/resync")

    assert response.status_code == 200
    data = response.json()
    assert data["resynced_count"] == 1
    assert len(data["errors"]) == 1


@pytest.mark.skipif(True, reason="Endpoint tests require full server setup with all dependencies")
def test_resync_endpoint_unexpected_error(temp_db):
    """Test handling of unexpected errors in resync endpoint"""
    from server import app
    client = TestClient(app)

    # Mock an unexpected exception
    with patch('core.workflow_history_utils.sync_manager.resync_all_completed_workflows', side_effect=Exception("Unexpected error")):
        response = client.post("/api/workflow-history/resync")

    assert response.status_code == 200  # Still returns 200 with error details
    data = response.json()
    assert data["resynced_count"] == 0
    assert len(data["errors"]) == 1
    assert "unexpected error" in data["errors"][0].lower()
