"""
Unit tests for workflow history tracking functionality.
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import os
from datetime import datetime

# Import the workflow history module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.workflow_history import (
    init_workflow_history_db,
    record_workflow_start,
    record_workflow_complete,
    record_workflow_failed,
    get_workflow_history,
    get_workflow_history_summary,
    get_concurrent_workflow_count,
    get_db_connection,
)
from core.data_models import WorkflowHistoryFilter


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    # Create temp directory for test database
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_database.db"

    # Override the DB_PATH in the module
    import core.workflow_history as wh_module
    original_db_path = wh_module.DB_PATH
    wh_module.DB_PATH = test_db_path

    # Initialize the database
    init_workflow_history_db()

    yield test_db_path

    # Cleanup
    wh_module.DB_PATH = original_db_path
    if test_db_path.exists():
        test_db_path.unlink()
    os.rmdir(temp_dir)


def test_init_workflow_history_db(test_db):
    """Test database schema initialization"""
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()

    # Check that the table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_history'"
    )
    result = cursor.fetchone()
    assert result is not None, "workflow_history table should exist"

    # Check that indexes exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='workflow_history'"
    )
    indexes = [row[0] for row in cursor.fetchall()]
    assert "idx_adw_id" in indexes
    assert "idx_started_at" in indexes
    assert "idx_status" in indexes
    assert "idx_workflow_template" in indexes

    conn.close()


def test_record_workflow_start(test_db):
    """Test recording workflow start event"""
    adw_id = "test_adw_123"
    issue_number = 42
    workflow_template = "adw_plan_build_test_iso"
    model_set = "base"
    user_input = "Test workflow"
    github_url = "https://github.com/test/repo/issues/42"

    record_workflow_start(
        adw_id=adw_id,
        issue_number=issue_number,
        workflow_template=workflow_template,
        model_set=model_set,
        user_input=user_input,
        github_url=github_url,
        backend_port=8000,
        frontend_port=5173,
        concurrent_workflows=2,
    )

    # Verify the record was inserted
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflow_history WHERE adw_id = ?", (adw_id,))
    row = cursor.fetchone()

    assert row is not None, "Record should be inserted"
    assert row[1] == adw_id
    assert row[2] == issue_number
    assert row[3] == workflow_template
    assert row[4] == model_set
    assert row[5] == "in_progress"

    conn.close()


def test_record_workflow_complete(test_db):
    """Test recording workflow completion"""
    adw_id = "test_adw_456"

    # First record a start event
    record_workflow_start(
        adw_id=adw_id,
        workflow_template="adw_sdlc_iso",
        model_set="heavy",
    )

    # Then complete it
    record_workflow_complete(adw_id=adw_id, total_duration_seconds=120.5)

    # Verify the record was updated
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT status, total_duration_seconds, completed_at FROM workflow_history WHERE adw_id = ?", (adw_id,))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "completed"
    assert row[1] == 120.5
    assert row[2] is not None  # completed_at should be set

    conn.close()


def test_record_workflow_failed(test_db):
    """Test recording workflow failure"""
    adw_id = "test_adw_789"
    error_message = "Test error occurred"

    # First record a start event
    record_workflow_start(adw_id=adw_id)

    # Then mark as failed
    record_workflow_failed(adw_id=adw_id, error_message=error_message)

    # Verify the record was updated
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT status, error_message, completed_at FROM workflow_history WHERE adw_id = ?", (adw_id,))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "failed"
    assert row[1] == error_message
    assert row[2] is not None  # completed_at should be set

    conn.close()


def test_get_workflow_history_filtering(test_db):
    """Test filtering workflow history"""
    # Insert multiple test records
    record_workflow_start(adw_id="test_1", model_set="base", workflow_template="adw_plan_build_test_iso")
    record_workflow_complete(adw_id="test_1", total_duration_seconds=100)

    record_workflow_start(adw_id="test_2", model_set="heavy", workflow_template="adw_sdlc_iso")
    record_workflow_failed(adw_id="test_2", error_message="Error")

    record_workflow_start(adw_id="test_3", model_set="base", workflow_template="adw_plan_build_test_iso")

    # Test model filter
    filters = WorkflowHistoryFilter(model_filter="base", limit=50, offset=0)
    response = get_workflow_history(filters)
    assert response.total == 2
    assert all(item.model_set == "base" for item in response.items)

    # Test status filter
    filters = WorkflowHistoryFilter(status_filter="completed", limit=50, offset=0)
    response = get_workflow_history(filters)
    assert response.total == 1
    assert response.items[0].adw_id == "test_1"

    # Test search filter
    filters = WorkflowHistoryFilter(search_query="test_2", limit=50, offset=0)
    response = get_workflow_history(filters)
    assert response.total == 1
    assert response.items[0].adw_id == "test_2"


def test_get_workflow_history_sorting(test_db):
    """Test sorting workflow history"""
    # Insert records with different durations
    record_workflow_start(adw_id="test_a")
    record_workflow_complete(adw_id="test_a", total_duration_seconds=50)

    record_workflow_start(adw_id="test_b")
    record_workflow_complete(adw_id="test_b", total_duration_seconds=150)

    record_workflow_start(adw_id="test_c")
    record_workflow_complete(adw_id="test_c", total_duration_seconds=100)

    # Test sorting by duration ascending
    filters = WorkflowHistoryFilter(sort_by="duration", order="asc", limit=50, offset=0)
    response = get_workflow_history(filters)
    durations = [item.total_duration_seconds for item in response.items]
    assert durations == sorted(durations)

    # Test sorting by duration descending
    filters = WorkflowHistoryFilter(sort_by="duration", order="desc", limit=50, offset=0)
    response = get_workflow_history(filters)
    durations = [item.total_duration_seconds for item in response.items]
    assert durations == sorted(durations, reverse=True)


def test_get_workflow_history_pagination(test_db):
    """Test pagination of workflow history"""
    # Insert 10 records
    for i in range(10):
        record_workflow_start(adw_id=f"test_{i}")

    # Test first page
    filters = WorkflowHistoryFilter(limit=3, offset=0)
    response = get_workflow_history(filters)
    assert len(response.items) == 3
    assert response.total == 10

    # Test second page
    filters = WorkflowHistoryFilter(limit=3, offset=3)
    response = get_workflow_history(filters)
    assert len(response.items) == 3
    assert response.total == 10


def test_get_workflow_history_summary(test_db):
    """Test summary statistics calculation"""
    # Insert test records
    record_workflow_start(adw_id="summary_1", workflow_template="adw_plan_build_test_iso", model_set="base")
    record_workflow_complete(adw_id="summary_1", total_duration_seconds=100)

    record_workflow_start(adw_id="summary_2", workflow_template="adw_sdlc_iso", model_set="heavy")
    record_workflow_complete(adw_id="summary_2", total_duration_seconds=200)

    record_workflow_start(adw_id="summary_3", workflow_template="adw_plan_build_test_iso", model_set="base")
    record_workflow_failed(adw_id="summary_3", error_message="Error")

    summary = get_workflow_history_summary()

    assert summary.total_workflows == 3
    assert summary.avg_duration == 150.0  # (100 + 200) / 2 completed workflows
    assert summary.success_rate == pytest.approx(66.67, rel=0.1)  # 2 out of 3
    assert summary.workflow_counts["adw_plan_build_test_iso"] == 2
    assert summary.workflow_counts["adw_sdlc_iso"] == 1
    assert summary.model_counts["base"] == 2
    assert summary.model_counts["heavy"] == 1


def test_sql_injection_prevention(test_db):
    """Test that search queries are safe from SQL injection"""
    # Insert a normal record
    record_workflow_start(adw_id="safe_record")

    # Try SQL injection in search query
    malicious_query = "'; DROP TABLE workflow_history; --"
    filters = WorkflowHistoryFilter(search_query=malicious_query, limit=50, offset=0)

    # This should not raise an error and should not drop the table
    response = get_workflow_history(filters)

    # Verify table still exists
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM workflow_history")
    count = cursor.fetchone()[0]
    assert count == 1, "Table should still exist with one record"
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
