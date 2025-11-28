"""
Unit tests for workflow_history_utils.database module.

Tests all database CRUD operations for workflow history tracking.
Covers edge cases including:
- Schema initialization and migrations
- Insert operations with various field combinations
- Update operations (single record and bulk by issue)
- Query operations with filtering, sorting, and pagination
- Analytics aggregation
- JSON serialization/deserialization
- Error handling and validation
- SQL injection prevention
"""

import json
import logging
import sqlite3
from unittest.mock import MagicMock, Mock, patch

import pytest
from core.workflow_history_utils.database import (
    DB_PATH,
    get_history_analytics,
    get_workflow_by_adw_id,
    get_workflow_history,
    init_db,
    insert_workflow_history,
    update_workflow_history,
    update_workflow_history_by_issue,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_db_connection():
    """
    Create a mock database connection with cursor.

    Returns a mock connection with configured cursor for testing
    database operations without actual database access.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)

    return mock_conn, mock_cursor


@pytest.fixture
def mock_get_db_connection(mock_db_connection):
    """
    Patch _db_adapter.get_connection to return mock connection.

    Automatically patches the database connection function
    for all tests in the module.

    NOTE: Updated in Phase 2 to patch the correct function after database
    module refactoring. Now patches _db_adapter.get_connection() instead
    of the non-existent get_db_connection().
    """
    mock_conn, mock_cursor = mock_db_connection

    # Mock PRAGMA table_info to return all database columns
    # This is needed because insert_workflow_history checks existing columns
    # Create mock Row objects that support dict-like access
    pragma_columns = [
        "id", "adw_id", "issue_number", "nl_input", "github_url", "gh_issue_state",
        "workflow_template", "model_used", "status", "start_time", "end_time",
        "duration_seconds", "error_message", "phase_count", "current_phase",
        "success_rate", "retry_count", "worktree_path", "backend_port", "frontend_port",
        "concurrent_workflows", "input_tokens", "output_tokens", "cached_tokens",
        "cache_hit_tokens", "cache_miss_tokens", "total_tokens", "cache_efficiency_percent",
        "estimated_cost_total", "actual_cost_total", "estimated_cost_per_step",
        "actual_cost_per_step", "cost_per_token", "structured_input", "cost_breakdown",
        "token_breakdown", "worktree_reused", "steps_completed", "steps_total",
        # Analytics fields - actual database column names
        "hour_of_day", "day_of_week", "nl_input_clarity_score", "cost_efficiency_score",
        "performance_score", "quality_score", "scoring_version", "anomaly_flags",
        "optimization_recommendations",
        # Additional fields for analytics
        "phase_durations", "idle_time_seconds", "bottleneck_phase",
        "error_category", "retry_reasons", "error_phase_distribution",
        "recovery_time_seconds", "complexity_estimated", "complexity_actual",
        "created_at", "updated_at"
    ]
    mock_pragma_rows = [{"name": col} for col in pragma_columns]

    # Set up execute side effect to configure what fetchall returns
    # This handles both PRAGMA table_info and phantom records queries
    def execute_side_effect(query, *args):
        # If it's a PRAGMA query, set fetchall to return columns
        if isinstance(query, str) and 'PRAGMA' in query.upper():
            mock_cursor.fetchall.return_value = mock_pragma_rows
        else:
            # For other queries (like phantom records), return empty list
            mock_cursor.fetchall.return_value = []
        # Don't call original - just return None (execute doesn't return anything)
        return None

    mock_cursor.execute.side_effect = execute_side_effect

    # Patch the correct target after database module refactoring
    with patch('core.workflow_history_utils.database.schema._db_adapter.get_connection') as mock_get_conn:
        mock_get_conn.return_value = mock_conn
        yield mock_get_conn, mock_conn, mock_cursor


# ============================================================================
# Test init_db() - Schema Creation and Migrations
# ============================================================================


class TestInitDB:
    """Tests for init_db() function."""

    def test_creates_db_directory(self, mock_get_db_connection):
        """Test that init_db creates the database directory if it doesn't exist."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        with patch('core.workflow_history_utils.database.DB_PATH') as mock_db_path:
            mock_parent = Mock()
            mock_db_path.parent = mock_parent

            init_db()

            # Verify directory creation was called
            mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_creates_workflow_history_table(self, mock_get_db_connection, caplog):
        """Test that init_db creates the workflow_history table."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        with caplog.at_level(logging.INFO):
            init_db()

        # Verify CREATE TABLE was called
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        assert any("CREATE TABLE IF NOT EXISTS workflow_history" in call for call in execute_calls)

        # Verify logging
        assert any("Workflow history database initialized" in record.message for record in caplog.records)

    def test_creates_indexes(self, mock_get_db_connection):
        """Test that init_db creates all required indexes."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        init_db()

        # Verify index creation
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]

        # Check for all expected indexes
        expected_indexes = [
            "idx_adw_id",
            "idx_status",
            "idx_created_at",
            "idx_issue_number",
            "idx_model_used",
            "idx_workflow_template"
        ]

        for index_name in expected_indexes:
            assert any(index_name in call for call in execute_calls), f"Index {index_name} not created"

    def test_migration_adds_gh_issue_state_column(self, mock_get_db_connection):
        """Test migration adds gh_issue_state column if it doesn't exist."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Simulate column doesn't exist (raise OperationalError)
        mock_cursor.execute.side_effect = [
            None,  # CREATE TABLE
            None, None, None, None, None, None,  # CREATE INDEX calls
            sqlite3.OperationalError("no such column: gh_issue_state"),  # SELECT check
            None,  # ALTER TABLE (add column)
        ]

        init_db()

        # Verify ALTER TABLE was called
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        assert any("ALTER TABLE workflow_history ADD COLUMN gh_issue_state" in call for call in execute_calls)
        # Verify commit was called after ALTER TABLE
        mock_conn.commit.assert_called()

    def test_migration_skips_if_column_exists(self, mock_get_db_connection):
        """Test migration is skipped if gh_issue_state column already exists."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Simulate column exists (no error)
        init_db()

        # Verify ALTER TABLE was not called
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        assert not any("ALTER TABLE" in call for call in execute_calls)

    def test_safe_to_call_multiple_times(self, mock_get_db_connection):
        """Test that init_db can be called multiple times safely."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Call init_db multiple times
        init_db()
        init_db()
        init_db()

        # Verify it doesn't raise errors and uses IF NOT EXISTS
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        assert any("IF NOT EXISTS" in call for call in execute_calls)


# ============================================================================
# Test insert_workflow_history() - Record Insertion
# ============================================================================


class TestInsertWorkflowHistory:
    """Tests for insert_workflow_history() function."""

    def test_insert_minimal_required_fields(self, mock_get_db_connection, caplog):
        """Test inserting workflow with only required field (adw_id)."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 123

        with caplog.at_level(logging.INFO):
            row_id = insert_workflow_history(adw_id="test-001")

        assert row_id == 123

        # Verify execute was called (PRAGMA + INSERT)
        assert mock_cursor.execute.call_count == 2

        # Get the INSERT call (second call)
        insert_call = mock_cursor.execute.call_args_list[1]
        query, values = insert_call[0]

        assert "INSERT INTO workflow_history" in query
        assert "adw_id" in query
        assert "test-001" in values
        assert "pending" in values  # Default status

        # Verify logging
        assert any("Inserted workflow history for ADW test-001" in record.message for record in caplog.records)

    def test_insert_with_all_core_fields(self, mock_get_db_connection):
        """Test inserting workflow with all core fields populated."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 456

        row_id = insert_workflow_history(
            adw_id="test-002",
            issue_number=42,
            nl_input="Fix authentication bug",
            github_url="https://github.com/test/repo/issues/42",
            workflow_template="adw_sdlc_iso",
            model_used="claude-sonnet-4-5",
            status="running"
        )

        assert row_id == 456

        # Get the INSERT call (second call after PRAGMA)
        insert_call = mock_cursor.execute.call_args_list[1]
        query, values = insert_call[0]

        assert "test-002" in values
        assert 42 in values
        assert "Fix authentication bug" in values
        assert "https://github.com/test/repo/issues/42" in values
        assert "adw_sdlc_iso" in values
        assert "claude-sonnet-4-5" in values
        assert "running" in values

    def test_insert_with_optional_kwargs(self, mock_get_db_connection):
        """Test inserting workflow with optional kwargs fields."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 789

        row_id = insert_workflow_history(
            adw_id="test-003",
            status="completed",
            start_time="2025-11-20T10:00:00",
            end_time="2025-11-20T10:15:00",
            duration_seconds=900,
            input_tokens=5000,
            output_tokens=2000,
            total_tokens=7000,
            actual_cost_total=0.35,
            worktree_path="/path/to/worktree",
            backend_port=8000,
            frontend_port=3000
        )

        assert row_id == 789

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify optional fields are included
        assert 900 in values  # duration_seconds
        assert 5000 in values  # input_tokens
        assert 0.35 in values  # actual_cost_total
        assert "/path/to/worktree" in values
        assert 8000 in values
        assert 3000 in values

    def test_insert_with_json_fields_dict(self, mock_get_db_connection):
        """Test inserting workflow with JSON fields as dictionaries."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 111

        cost_breakdown = {"phase_1": 0.10, "phase_2": 0.15, "phase_3": 0.10}
        token_breakdown = {"input": 5000, "output": 2000}
        anomaly_flags = [{"type": "high_cost", "severity": "warning"}]

        row_id = insert_workflow_history(
            adw_id="test-004",
            status="completed",
            cost_breakdown=cost_breakdown,
            token_breakdown=token_breakdown,
            anomaly_flags=anomaly_flags
        )

        assert row_id == 111

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify JSON fields are serialized
        assert json.dumps(cost_breakdown) in values
        assert json.dumps(token_breakdown) in values
        assert json.dumps(anomaly_flags) in values

    def test_insert_with_json_fields_already_string(self, mock_get_db_connection):
        """Test inserting workflow with JSON fields already as strings."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 222

        cost_breakdown_str = '{"phase_1": 0.10}'

        row_id = insert_workflow_history(
            adw_id="test-005",
            status="completed",
            cost_breakdown=cost_breakdown_str
        )

        assert row_id == 222

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify string is passed as-is
        assert cost_breakdown_str in values

    def test_insert_with_analytics_scoring_fields(self, mock_get_db_connection):
        """Test inserting workflow with Phase 3A/3B analytics and scoring fields."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 333

        row_id = insert_workflow_history(
            adw_id="test-006",
            status="completed",
            hour_of_day=14,
            day_of_week=2,
            nl_input_clarity_score=0.85,
            cost_efficiency_score=0.75,
            performance_score=0.90,
            quality_score=0.88,
            scoring_version="1.0"
        )

        assert row_id == 333

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert 14 in values  # hour_of_day
        assert 2 in values   # day_of_week
        assert 0.85 in values  # nl_input_clarity_score
        assert 0.75 in values  # cost_efficiency_score
        assert 0.90 in values  # performance_score
        assert 0.88 in values  # quality_score
        assert "1.0" in values  # scoring_version

    def test_insert_with_phase_3d_insights_fields(self, mock_get_db_connection):
        """Test inserting workflow with Phase 3D insights and recommendations."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 444

        optimization_recommendations = [
            "Consider caching intermediate results",
            "Optimize token usage in phase 2"
        ]

        row_id = insert_workflow_history(
            adw_id="test-007",
            status="completed",
            optimization_recommendations=optimization_recommendations
        )

        assert row_id == 444

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert json.dumps(optimization_recommendations) in values

    def test_insert_duplicate_adw_id_raises_integrity_error(self, mock_get_db_connection):
        """Test that inserting duplicate adw_id raises IntegrityError."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Simulate UNIQUE constraint violation
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: workflow_history.adw_id")

        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
            insert_workflow_history(adw_id="duplicate-001")

    def test_insert_with_gh_issue_state(self, mock_get_db_connection):
        """Test inserting workflow with GitHub issue state."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 555

        row_id = insert_workflow_history(
            adw_id="test-008",
            status="completed",
            gh_issue_state="closed"
        )

        assert row_id == 555

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert "closed" in values

    def test_insert_with_created_at_override(self, mock_get_db_connection):
        """Test inserting workflow with custom created_at timestamp."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 666

        custom_timestamp = "2025-01-01T00:00:00"

        row_id = insert_workflow_history(
            adw_id="test-009",
            status="pending",
            created_at=custom_timestamp
        )

        assert row_id == 666

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert custom_timestamp in values


# ============================================================================
# Test update_workflow_history_by_issue() - Bulk Update by Issue
# ============================================================================


class TestUpdateWorkflowHistoryByIssue:
    """Tests for update_workflow_history_by_issue() function."""

    def test_update_single_field_by_issue(self, mock_get_db_connection, caplog):
        """Test updating a single field for all workflows with given issue number."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 2  # Simulate 2 records updated

        with caplog.at_level(logging.INFO):
            updated_count = update_workflow_history_by_issue(
                issue_number=42,
                gh_issue_state="closed"
            )

        assert updated_count == 2

        query, values = mock_cursor.execute.call_args[0]

        assert "UPDATE workflow_history" in query
        assert "gh_issue_state = ?" in query
        assert "WHERE issue_number = ?" in query
        assert "updated_at = CURRENT_TIMESTAMP" in query

        assert "closed" in values
        assert 42 in values

        # Verify logging
        assert any("Updated 2 workflow(s) for issue #42" in record.message for record in caplog.records)

    def test_update_multiple_fields_by_issue(self, mock_get_db_connection):
        """Test updating multiple fields for all workflows with given issue number."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 3

        updated_count = update_workflow_history_by_issue(
            issue_number=99,
            gh_issue_state="open",
            status="failed",
            error_message="GitHub API rate limit exceeded"
        )

        assert updated_count == 3

        query, values = mock_cursor.execute.call_args[0]

        assert "gh_issue_state = ?" in query
        assert "status = ?" in query
        assert "error_message = ?" in query

        assert "open" in values
        assert "failed" in values
        assert "GitHub API rate limit exceeded" in values
        assert 99 in values

    def test_update_no_fields_provided(self, mock_get_db_connection, caplog):
        """Test that updating with no fields returns 0 and logs warning."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        with caplog.at_level(logging.WARNING):
            updated_count = update_workflow_history_by_issue(issue_number=42)

        assert updated_count == 0

        # Verify no database operation was performed
        mock_cursor.execute.assert_not_called()

        # Verify warning logged
        assert any("No fields provided to update" in record.message for record in caplog.records)

    def test_update_issue_not_found(self, mock_get_db_connection, caplog):
        """Test updating non-existent issue number logs warning."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 0  # No records updated

        with caplog.at_level(logging.WARNING):
            updated_count = update_workflow_history_by_issue(
                issue_number=9999,
                gh_issue_state="closed"
            )

        assert updated_count == 0

        # Verify warning logged
        assert any("No workflows found for issue #9999" in record.message for record in caplog.records)

    def test_update_by_issue_sets_updated_at(self, mock_get_db_connection):
        """Test that update_workflow_history_by_issue always updates updated_at timestamp."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        update_workflow_history_by_issue(
            issue_number=42,
            gh_issue_state="closed"
        )

        query = mock_cursor.execute.call_args[0][0]

        # Verify updated_at is always included
        assert "updated_at = CURRENT_TIMESTAMP" in query


# ============================================================================
# Test update_workflow_history() - Single Record Update
# ============================================================================


class TestUpdateWorkflowHistory:
    """Tests for update_workflow_history() function."""

    def test_update_single_field(self, mock_get_db_connection, caplog):
        """Test updating a single field for a specific workflow."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        with caplog.at_level(logging.DEBUG):
            success = update_workflow_history(
                adw_id="test-001",
                status="completed"
            )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert "UPDATE workflow_history" in query
        assert "status = ?" in query
        assert "WHERE adw_id = ?" in query
        assert "updated_at = CURRENT_TIMESTAMP" in query

        assert "completed" in values
        assert "test-001" in values

        # Verify logging
        assert any("Updated workflow history for ADW test-001" in record.message for record in caplog.records)

    def test_update_multiple_fields(self, mock_get_db_connection):
        """Test updating multiple fields for a specific workflow."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        success = update_workflow_history(
            adw_id="test-002",
            status="completed",
            end_time="2025-11-20T10:15:00",
            duration_seconds=900,
            output_tokens=2000,
            actual_cost_total=0.35
        )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]

        assert "status = ?" in query
        assert "end_time = ?" in query
        assert "duration_seconds = ?" in query
        assert "output_tokens = ?" in query
        assert "actual_cost_total = ?" in query

        assert "completed" in values
        assert "2025-11-20T10:15:00" in values
        assert 900 in values
        assert 2000 in values
        assert 0.35 in values

    def test_update_with_json_field_dict(self, mock_get_db_connection):
        """Test updating workflow with JSON field as dictionary."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        cost_breakdown = {"phase_1": 0.10, "phase_2": 0.15}

        success = update_workflow_history(
            adw_id="test-003",
            cost_breakdown=cost_breakdown
        )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify JSON is serialized
        assert json.dumps(cost_breakdown) in values

    def test_update_with_json_field_list(self, mock_get_db_connection):
        """Test updating workflow with JSON field as list."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        anomaly_flags = [
            {"type": "high_cost", "phase": "build"},
            {"type": "slow_execution", "phase": "test"}
        ]

        success = update_workflow_history(
            adw_id="test-004",
            anomaly_flags=anomaly_flags
        )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify list is serialized to JSON
        assert json.dumps(anomaly_flags) in values

    def test_update_no_fields_provided(self, mock_get_db_connection, caplog):
        """Test that updating with no fields returns False and logs warning."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        with caplog.at_level(logging.WARNING):
            success = update_workflow_history(adw_id="test-005")

        assert success is False

        # Verify no database operation was performed
        mock_cursor.execute.assert_not_called()

        # Verify warning logged
        assert any("No fields provided to update for ADW test-005" in record.message for record in caplog.records)

    def test_update_workflow_not_found(self, mock_get_db_connection, caplog):
        """Test updating non-existent workflow returns False and logs warning."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 0  # No records updated

        with caplog.at_level(logging.WARNING):
            success = update_workflow_history(
                adw_id="non-existent",
                status="completed"
            )

        assert success is False

        # Verify warning logged
        assert any("No workflow found with ADW ID non-existent" in record.message for record in caplog.records)

    def test_update_sets_updated_at(self, mock_get_db_connection):
        """Test that update_workflow_history always updates updated_at timestamp."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        update_workflow_history(
            adw_id="test-006",
            status="running"
        )

        query = mock_cursor.execute.call_args_list[1][0][0]

        # Verify updated_at is always included
        assert "updated_at = CURRENT_TIMESTAMP" in query

    def test_update_all_json_fields(self, mock_get_db_connection):
        """Test updating all JSON fields simultaneously."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        success = update_workflow_history(
            adw_id="test-007",
            structured_input={"query": "test"},
            cost_breakdown={"phase_1": 0.10},
            token_breakdown={"input": 1000},
            phase_durations={"plan": 120, "build": 300},
            retry_reasons=["timeout", "api_error"],
            error_phase_distribution={"build": 2, "test": 1},
            anomaly_flags=[{"type": "warning"}],
            optimization_recommendations=["Use cache"]
        )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify all JSON fields are in the query
        for field in ["structured_input", "cost_breakdown", "token_breakdown",
                      "phase_durations", "retry_reasons", "error_phase_distribution",
                      "anomaly_flags", "optimization_recommendations"]:
            assert f"{field} = ?" in query


# ============================================================================
# Test get_workflow_by_adw_id() - Single Record Retrieval
# ============================================================================


class TestGetWorkflowByAdwId:
    """Tests for get_workflow_by_adw_id() function."""

    def test_get_existing_workflow(self, mock_get_db_connection):
        """Test retrieving an existing workflow by ADW ID."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Mock database row
        mock_row = {
            "id": 1,
            "adw_id": "test-001",
            "issue_number": 42,
            "nl_input": "Fix auth bug",
            "status": "completed",
            "start_time": "2025-11-20T10:00:00",
            "input_tokens": 5000,
            "output_tokens": 2000,
            "total_tokens": 7000,
            "actual_cost_total": 0.35,
            "structured_input": None,
            "cost_breakdown": None,
            "token_breakdown": None,
            "phase_durations": None,
            "retry_reasons": None,
            "error_phase_distribution": None,
            "anomaly_flags": None,
            "optimization_recommendations": None,
            "created_at": "2025-11-20T09:55:00"
        }

        mock_cursor.fetchone.return_value = mock_row

        result = get_workflow_by_adw_id("test-001")

        assert result is not None
        assert result["adw_id"] == "test-001"
        assert result["issue_number"] == 42
        assert result["nl_input"] == "Fix auth bug"
        assert result["status"] == "completed"
        assert result["total_tokens"] == 7000

        # Verify query
        mock_cursor.execute.assert_called_once()
        query, params = mock_cursor.execute.call_args[0]
        assert "SELECT * FROM workflow_history WHERE adw_id = ?" in query
        assert params == ("test-001",)

    def test_get_workflow_with_json_fields(self, mock_get_db_connection):
        """Test retrieving workflow with JSON fields properly parsed."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        cost_breakdown = {"phase_1": 0.10, "phase_2": 0.15}
        anomaly_flags = [{"type": "high_cost"}]

        mock_row = {
            "id": 2,
            "adw_id": "test-002",
            "status": "completed",
            "cost_breakdown": json.dumps(cost_breakdown),
            "token_breakdown": json.dumps({"input": 5000}),
            "anomaly_flags": json.dumps(anomaly_flags),
            "optimization_recommendations": json.dumps(["Use cache"]),
            "structured_input": None,
            "phase_durations": None,
            "retry_reasons": None,
            "error_phase_distribution": None,
        }

        mock_cursor.fetchone.return_value = mock_row

        result = get_workflow_by_adw_id("test-002")

        assert result is not None

        # Verify JSON fields are parsed
        assert result["cost_breakdown"] == cost_breakdown
        assert result["token_breakdown"] == {"input": 5000}
        assert result["anomaly_flags"] == anomaly_flags
        assert result["optimization_recommendations"] == ["Use cache"]

    def test_get_workflow_with_invalid_json(self, mock_get_db_connection, caplog):
        """Test retrieving workflow with invalid JSON gracefully handles error."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_row = {
            "id": 3,
            "adw_id": "test-003",
            "status": "completed",
            "cost_breakdown": "{invalid json}",  # Invalid JSON
            "token_breakdown": None,
            "structured_input": None,
            "phase_durations": None,
            "retry_reasons": None,
            "error_phase_distribution": None,
            "anomaly_flags": None,
            "optimization_recommendations": None,
        }

        mock_cursor.fetchone.return_value = mock_row

        with caplog.at_level(logging.WARNING):
            result = get_workflow_by_adw_id("test-003")

        assert result is not None
        # Invalid JSON should be set to None
        assert result["cost_breakdown"] is None

        # Verify warning logged
        assert any("Failed to parse JSON" in record.message for record in caplog.records)

    def test_get_nonexistent_workflow(self, mock_get_db_connection):
        """Test retrieving non-existent workflow returns None."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.fetchone.return_value = None

        result = get_workflow_by_adw_id("non-existent")

        assert result is None

        mock_cursor.execute.assert_called_once()

    def test_get_workflow_empty_json_fields_default_to_empty_array(self, mock_get_db_connection):
        """Test that Phase 3D JSON fields default to empty arrays when None."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_row = {
            "id": 4,
            "adw_id": "test-004",
            "status": "completed",
            "structured_input": None,
            "cost_breakdown": None,
            "token_breakdown": None,
            "phase_durations": None,
            "retry_reasons": None,
            "error_phase_distribution": None,
            "anomaly_flags": None,  # Should default to []
            "optimization_recommendations": None,  # Should default to []
        }

        mock_cursor.fetchone.return_value = mock_row

        result = get_workflow_by_adw_id("test-004")

        assert result is not None

        # Phase 3D fields should default to empty arrays
        assert result["anomaly_flags"] == []
        assert result["optimization_recommendations"] == []

        # Other JSON fields should remain None
        assert result["cost_breakdown"] is None
        assert result["token_breakdown"] is None


# ============================================================================
# Test get_workflow_history() - Complex Queries with Filtering
# ============================================================================


class TestGetWorkflowHistory:
    """Tests for get_workflow_history() function."""

    def test_get_all_workflows_default_pagination(self, mock_get_db_connection, caplog):
        """Test getting workflows with default pagination (limit=20, offset=0)."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Mock count query result
        mock_cursor.fetchone.side_effect = [
            {"total": 50},  # Total count
        ]

        # Mock paginated results
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "adw_id": "test-001",
                "status": "completed",
                "nl_input_clarity_score": None,
                "cost_efficiency_score": None,
                "performance_score": None,
                "quality_score": None,
                "estimated_cost_total": None,
                "structured_input": None,
                "cost_breakdown": None,
                "token_breakdown": None,
                "phase_durations": None,
                "retry_reasons": None,
                "error_phase_distribution": None,
                "anomaly_flags": None,
                "optimization_recommendations": None,
            }
        ]

        with caplog.at_level(logging.DEBUG):
            results, total_count = get_workflow_history()

        assert len(results) == 1
        assert total_count == 50
        assert results[0]["adw_id"] == "test-001"

        # Verify default score values are applied
        assert results[0]["nl_input_clarity_score"] == 0.0
        assert results[0]["cost_efficiency_score"] == 0.0
        assert results[0]["performance_score"] == 0.0
        assert results[0]["quality_score"] == 0.0
        assert results[0]["estimated_cost_total"] == 0.0

        # Verify logging
        assert any("Retrieved 1 workflows" in record.message for record in caplog.records)
        assert any("total: 50" in record.message for record in caplog.records)

    def test_get_workflows_with_custom_pagination(self, mock_get_db_connection):
        """Test getting workflows with custom limit and offset."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 100}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(limit=50, offset=20)

        assert total_count == 100

        # Verify LIMIT and OFFSET in query
        query = mock_cursor.execute.call_args_list[-1][0][0]
        params = mock_cursor.execute.call_args_list[-1][0][1]

        assert "LIMIT ?" in query
        assert "OFFSET ?" in query
        assert 50 in params  # limit
        assert 20 in params  # offset

    def test_filter_by_status(self, mock_get_db_connection):
        """Test filtering workflows by status."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(status="completed")

        # Verify WHERE clause
        count_query = mock_cursor.execute.call_args_list[0][0][0]
        count_params = mock_cursor.execute.call_args_list[0][0][1]

        assert "WHERE status = ?" in count_query
        assert "completed" in count_params

    def test_filter_by_model(self, mock_get_db_connection):
        """Test filtering workflows by model."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 15}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(model="claude-sonnet-4-5")

        count_query = mock_cursor.execute.call_args_list[0][0][0]
        count_params = mock_cursor.execute.call_args_list[0][0][1]

        assert "WHERE model_used = ?" in count_query
        assert "claude-sonnet-4-5" in count_params

    def test_filter_by_template(self, mock_get_db_connection):
        """Test filtering workflows by template."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 8}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(template="adw_sdlc_iso")

        count_query = mock_cursor.execute.call_args_list[0][0][0]
        count_params = mock_cursor.execute.call_args_list[0][0][1]

        assert "WHERE workflow_template = ?" in count_query
        assert "adw_sdlc_iso" in count_params

    def test_filter_by_date_range(self, mock_get_db_connection):
        """Test filtering workflows by date range."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 5}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(
            start_date="2025-11-01T00:00:00",
            end_date="2025-11-30T23:59:59"
        )

        count_query = mock_cursor.execute.call_args_list[0][0][0]
        count_params = mock_cursor.execute.call_args_list[0][0][1]

        assert "created_at >= ?" in count_query
        assert "created_at <= ?" in count_query
        assert "2025-11-01T00:00:00" in count_params
        assert "2025-11-30T23:59:59" in count_params

    def test_filter_by_search_query(self, mock_get_db_connection):
        """Test filtering workflows by search query (searches ADW ID, nl_input, github_url)."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 3}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(search="authentication")

        count_query = mock_cursor.execute.call_args_list[0][0][0]
        count_params = mock_cursor.execute.call_args_list[0][0][1]

        assert "adw_id LIKE ?" in count_query
        assert "nl_input LIKE ?" in count_query
        assert "github_url LIKE ?" in count_query
        assert "%authentication%" in count_params

    def test_filter_multiple_conditions(self, mock_get_db_connection):
        """Test combining multiple filter conditions."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 2}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(
            status="completed",
            model="claude-sonnet-4-5",
            template="adw_sdlc_iso",
            start_date="2025-11-01T00:00:00",
            search="bug"
        )

        count_query = mock_cursor.execute.call_args_list[0][0][0]

        # Verify all conditions are in WHERE clause
        assert "status = ?" in count_query
        assert "model_used = ?" in count_query
        assert "workflow_template = ?" in count_query
        assert "created_at >= ?" in count_query
        assert "adw_id LIKE ?" in count_query
        assert " AND " in count_query  # Conditions are combined with AND

    def test_sort_by_created_at_desc_default(self, mock_get_db_connection):
        """Test default sort order (created_at DESC)."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history()

        select_query = mock_cursor.execute.call_args_list[-1][0][0]

        assert "ORDER BY created_at DESC" in select_query

    def test_sort_by_custom_field_asc(self, mock_get_db_connection):
        """Test sorting by custom field in ascending order."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(
            sort_by="duration_seconds",
            sort_order="ASC"
        )

        select_query = mock_cursor.execute.call_args_list[-1][0][0]

        assert "ORDER BY duration_seconds ASC" in select_query

    def test_sort_by_invalid_field_defaults_to_created_at(self, mock_get_db_connection):
        """Test that invalid sort_by field defaults to created_at (SQL injection prevention)."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        # Try to inject SQL through sort_by
        results, total_count = get_workflow_history(
            sort_by="created_at; DROP TABLE workflow_history; --"
        )

        select_query = mock_cursor.execute.call_args_list[-1][0][0]

        # Should fall back to created_at
        assert "ORDER BY created_at" in select_query
        assert "DROP TABLE" not in select_query

    def test_sort_order_invalid_defaults_to_desc(self, mock_get_db_connection):
        """Test that invalid sort_order defaults to DESC."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        # Invalid sort order
        results, total_count = get_workflow_history(sort_order="INVALID")

        select_query = mock_cursor.execute.call_args_list[-1][0][0]

        # Should fall back to DESC
        assert "ORDER BY created_at DESC" in select_query

    def test_valid_sort_fields(self, mock_get_db_connection):
        """Test all valid sort fields are accepted."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []

        valid_fields = [
            "created_at", "updated_at", "start_time", "end_time",
            "duration_seconds", "status", "adw_id", "issue_number",
            "actual_cost_total", "total_tokens", "cache_efficiency_percent"
        ]

        for field in valid_fields:
            mock_cursor.reset_mock()
            results, total_count = get_workflow_history(sort_by=field)

            select_query = mock_cursor.execute.call_args_list[-1][0][0]
            assert f"ORDER BY {field}" in select_query

    def test_json_fields_parsed_in_results(self, mock_get_db_connection):
        """Test that JSON fields are properly parsed in result list."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 2}
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "adw_id": "test-001",
                "status": "completed",
                "cost_breakdown": json.dumps({"phase_1": 0.10}),
                "anomaly_flags": json.dumps([{"type": "warning"}]),
                "nl_input_clarity_score": 0.8,
                "cost_efficiency_score": 0.9,
                "performance_score": 0.85,
                "quality_score": 0.88,
                "estimated_cost_total": 0.5,
                "structured_input": None,
                "token_breakdown": None,
                "phase_durations": None,
                "retry_reasons": None,
                "error_phase_distribution": None,
                "optimization_recommendations": None,
            },
            {
                "id": 2,
                "adw_id": "test-002",
                "status": "running",
                "cost_breakdown": None,
                "anomaly_flags": None,  # Should default to []
                "nl_input_clarity_score": None,  # Should default to 0.0
                "cost_efficiency_score": None,
                "performance_score": None,
                "quality_score": None,
                "estimated_cost_total": None,
                "structured_input": None,
                "token_breakdown": None,
                "phase_durations": None,
                "retry_reasons": None,
                "error_phase_distribution": None,
                "optimization_recommendations": None,
            }
        ]

        results, total_count = get_workflow_history()

        assert len(results) == 2

        # First result - JSON parsed
        assert results[0]["cost_breakdown"] == {"phase_1": 0.10}
        assert results[0]["anomaly_flags"] == [{"type": "warning"}]
        assert results[0]["nl_input_clarity_score"] == 0.8

        # Second result - defaults applied
        assert results[1]["anomaly_flags"] == []
        assert results[1]["nl_input_clarity_score"] == 0.0
        assert results[1]["cost_efficiency_score"] == 0.0

    def test_empty_results(self, mock_get_db_connection):
        """Test handling of empty result set."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 0}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history()

        assert results == []
        assert total_count == 0


# ============================================================================
# Test get_history_analytics() - Analytics Aggregation
# ============================================================================


class TestGetHistoryAnalytics:
    """Tests for get_history_analytics() function."""

    def test_analytics_with_workflows(self, mock_get_db_connection, caplog):
        """Test calculating analytics with existing workflows."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Mock query results in order
        mock_cursor.fetchone.side_effect = [
            {"total": 100},  # Total workflows
            {"avg_duration": 450.5},  # Average duration
            {"avg_cost": 0.35, "total_cost": 35.0},  # Cost analytics
            {"avg_tokens": 5500.0, "avg_cache_efficiency": 65.5},  # Token analytics
        ]

        # Mock status counts
        mock_cursor.fetchall.side_effect = [
            [
                {"status": "completed", "count": 70},
                {"status": "failed", "count": 20},
                {"status": "running", "count": 8},
                {"status": "pending", "count": 2},
            ],
            # Mock workflows by model
            [
                {"model_used": "claude-sonnet-4-5", "count": 80},
                {"model_used": "gpt-4", "count": 20},
            ],
            # Mock workflows by template
            [
                {"workflow_template": "adw_sdlc_iso", "count": 60},
                {"workflow_template": "adw_basic", "count": 40},
            ],
        ]

        with caplog.at_level(logging.DEBUG):
            analytics = get_history_analytics()

        assert analytics["total_workflows"] == 100
        assert analytics["completed_workflows"] == 70
        assert analytics["failed_workflows"] == 20
        assert analytics["success_rate_percent"] == 70.0
        assert analytics["avg_duration_seconds"] == 450.5
        assert analytics["avg_cost"] == 0.35
        assert analytics["total_cost"] == 35.0
        assert analytics["avg_tokens"] == 5500.0
        assert analytics["avg_cache_efficiency"] == 65.5

        assert analytics["workflows_by_status"] == {
            "completed": 70,
            "failed": 20,
            "running": 8,
            "pending": 2
        }

        assert analytics["workflows_by_model"] == {
            "claude-sonnet-4-5": 80,
            "gpt-4": 20
        }

        assert analytics["workflows_by_template"] == {
            "adw_sdlc_iso": 60,
            "adw_basic": 40
        }

        # Verify logging
        assert any("Generated analytics" in record.message for record in caplog.records)

    def test_analytics_with_no_workflows(self, mock_get_db_connection):
        """Test calculating analytics with no workflows returns zeros."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Mock empty results
        mock_cursor.fetchone.side_effect = [
            {"total": 0},  # No workflows
            {"avg_duration": None},
            {"avg_cost": None, "total_cost": None},
            {"avg_tokens": None, "avg_cache_efficiency": None},
        ]

        mock_cursor.fetchall.side_effect = [
            [],  # No status counts
            [],  # No model counts
            [],  # No template counts
        ]

        analytics = get_history_analytics()

        assert analytics["total_workflows"] == 0
        assert analytics["completed_workflows"] == 0
        assert analytics["failed_workflows"] == 0
        assert analytics["success_rate_percent"] == 0.0
        assert analytics["avg_duration_seconds"] == 0.0
        assert analytics["avg_cost"] == 0.0
        assert analytics["total_cost"] == 0.0
        assert analytics["avg_tokens"] == 0.0
        assert analytics["avg_cache_efficiency"] == 0.0
        assert analytics["workflows_by_status"] == {}
        assert analytics["workflows_by_model"] == {}
        assert analytics["workflows_by_template"] == {}

    def test_analytics_success_rate_calculation(self, mock_get_db_connection):
        """Test success rate is calculated correctly."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.side_effect = [
            {"total": 200},  # Total workflows
            {"avg_duration": 300.0},
            {"avg_cost": 0.25, "total_cost": 50.0},
            {"avg_tokens": 4000.0, "avg_cache_efficiency": 50.0},
        ]

        mock_cursor.fetchall.side_effect = [
            [
                {"status": "completed", "count": 150},  # 150/200 = 75%
                {"status": "failed", "count": 50},
            ],
            [],  # Empty models
            [],  # Empty templates
        ]

        analytics = get_history_analytics()

        assert analytics["total_workflows"] == 200
        assert analytics["completed_workflows"] == 150
        assert analytics["failed_workflows"] == 50
        assert analytics["success_rate_percent"] == 75.0

    def test_analytics_only_completed_workflows_in_avg_duration(self, mock_get_db_connection):
        """Test that average duration only includes completed workflows."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.side_effect = [
            {"total": 100},
            {"avg_duration": 500.0},  # Only from completed workflows
            {"avg_cost": 0.30, "total_cost": 30.0},
            {"avg_tokens": 5000.0, "avg_cache_efficiency": 60.0},
        ]

        mock_cursor.fetchall.side_effect = [
            [{"status": "completed", "count": 50}],
            [],
            [],
        ]

        analytics = get_history_analytics()

        # Verify query filters for completed status (3rd query executed)
        # Query execution order: 1. COUNT(*) 2. GROUP BY status 3. AVG(duration) for completed
        avg_duration_query = mock_cursor.execute.call_args_list[2][0][0]
        assert "WHERE status = 'completed'" in avg_duration_query
        assert "duration_seconds IS NOT NULL" in avg_duration_query

    def test_analytics_filters_zero_costs_and_tokens(self, mock_get_db_connection):
        """Test that analytics filters out zero/null costs and tokens."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.side_effect = [
            {"total": 50},
            {"avg_duration": 400.0},
            {"avg_cost": 0.40, "total_cost": 20.0},
            {"avg_tokens": 6000.0, "avg_cache_efficiency": 70.0},
        ]

        mock_cursor.fetchall.side_effect = [
            [{"status": "completed", "count": 40}],
            [],
            [],
        ]

        analytics = get_history_analytics()

        # Verify cost query filters (6th query executed)
        # Query order: 1.COUNT 2.status 3.duration 4.model 5.template 6.cost 7.tokens
        cost_query = mock_cursor.execute.call_args_list[5][0][0]
        assert "actual_cost_total IS NOT NULL" in cost_query
        assert "actual_cost_total > 0" in cost_query

        # Verify token query filters (7th query executed)
        token_query = mock_cursor.execute.call_args_list[6][0][0]
        assert "total_tokens IS NOT NULL" in token_query
        assert "total_tokens > 0" in token_query

    def test_analytics_returns_all_required_keys(self, mock_get_db_connection):
        """Test that analytics returns all expected keys in the dictionary."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Minimal mock data
        mock_cursor.fetchone.side_effect = [
            {"total": 1},
            {"avg_duration": 100.0},
            {"avg_cost": 0.10, "total_cost": 0.10},
            {"avg_tokens": 1000.0, "avg_cache_efficiency": 50.0},
        ]

        mock_cursor.fetchall.side_effect = [
            [{"status": "completed", "count": 1}],
            [{"model_used": "test-model", "count": 1}],
            [{"workflow_template": "test-template", "count": 1}],
        ]

        analytics = get_history_analytics()

        # Verify all expected keys are present
        expected_keys = [
            "total_workflows",
            "completed_workflows",
            "failed_workflows",
            "avg_duration_seconds",
            "success_rate_percent",
            "workflows_by_model",
            "workflows_by_template",
            "workflows_by_status",
            "avg_cost",
            "total_cost",
            "avg_tokens",
            "avg_cache_efficiency",
        ]

        for key in expected_keys:
            assert key in analytics, f"Missing key: {key}"


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling across all functions."""

    def test_db_path_is_correct(self):
        """Test that DB_PATH is correctly constructed relative to module location."""
        # DB_PATH should be: core/workflow_history_utils/../../db/workflow_history.db
        # Which resolves to: app/server/db/workflow_history.db
        assert "workflow_history.db" in str(DB_PATH)
        assert DB_PATH.name == "workflow_history.db"

    def test_insert_with_empty_string_values(self, mock_get_db_connection):
        """Test inserting workflow with empty string values."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 999

        row_id = insert_workflow_history(
            adw_id="test-empty",
            nl_input="",  # Empty string
            github_url="",  # Empty string
            status="pending"
        )

        assert row_id == 999

        query, values = mock_cursor.execute.call_args_list[1][0]
        assert "" in values  # Empty strings should be preserved

    def test_update_with_none_values(self, mock_get_db_connection):
        """Test updating workflow with None values."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.rowcount = 1

        success = update_workflow_history(
            adw_id="test-none",
            error_message=None,
            end_time=None
        )

        assert success is True

        query, values = mock_cursor.execute.call_args_list[1][0]
        assert None in values  # None values should be allowed

    def test_get_workflow_history_with_zero_limit(self, mock_get_db_connection):
        """Test querying with limit=0 returns empty results."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 100}
        mock_cursor.fetchall.return_value = []

        results, total_count = get_workflow_history(limit=0)

        assert results == []
        assert total_count == 100  # Total count should still be accurate

    def test_get_workflow_history_with_large_offset(self, mock_get_db_connection):
        """Test querying with offset larger than total count."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        mock_cursor.fetchone.return_value = {"total": 10}
        mock_cursor.fetchall.return_value = []  # No results

        results, total_count = get_workflow_history(limit=20, offset=100)

        assert results == []
        assert total_count == 10

    def test_connection_error_propagates(self, mock_get_db_connection):
        """Test that database connection errors propagate correctly."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Simulate connection error
        mock_get_conn.side_effect = sqlite3.OperationalError("Unable to open database")

        with pytest.raises(sqlite3.OperationalError, match="Unable to open database"):
            init_db()

    def test_query_execution_error_propagates(self, mock_get_db_connection):
        """Test that query execution errors propagate correctly."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection

        # Simulate query error
        mock_cursor.execute.side_effect = sqlite3.OperationalError("Database is locked")

        with pytest.raises(sqlite3.OperationalError, match="Database is locked"):
            get_workflow_by_adw_id("test-001")

    def test_json_serialization_preserves_types(self, mock_get_db_connection):
        """Test that JSON serialization preserves data types correctly."""
        mock_get_conn, mock_conn, mock_cursor = mock_get_db_connection
        mock_cursor.lastrowid = 777

        complex_data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }

        row_id = insert_workflow_history(
            adw_id="test-json-types",
            status="completed",
            structured_input=complex_data
        )

        query, values = mock_cursor.execute.call_args_list[1][0]

        # Verify JSON serialization
        json_str = json.dumps(complex_data)
        assert json_str in values

        # Verify deserialization preserves types
        deserialized = json.loads(json_str)
        assert deserialized == complex_data
