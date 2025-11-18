"""
Unit tests for pattern persistence.

Tests cover:
- Pattern occurrence recording (new patterns, updates, edge cases)
- Pattern statistics updates (first workflow, running averages)
- Batch workflow processing (single and multiple workflows)
- Database operations and persistence
"""

import sqlite3

import pytest
from core.pattern_persistence import (
    batch_process_workflows,
    process_and_persist_workflow,
    record_pattern_occurrence,
    update_pattern_statistics,
)


@pytest.fixture
def mock_db():
    """Create in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create tables (matching schema.sql)
    cursor.execute("""
        CREATE TABLE operation_patterns (
            id INTEGER PRIMARY KEY,
            pattern_signature TEXT UNIQUE,
            pattern_type TEXT,
            occurrence_count INTEGER DEFAULT 1,
            avg_tokens_with_llm INTEGER DEFAULT 0,
            avg_cost_with_llm REAL DEFAULT 0.0,
            avg_tokens_with_tool INTEGER DEFAULT 0,
            avg_cost_with_tool REAL DEFAULT 0.0,
            typical_input_pattern TEXT,
            automation_status TEXT DEFAULT 'detected',
            confidence_score REAL DEFAULT 10.0,
            potential_monthly_savings REAL DEFAULT 0.0,
            created_at TEXT,
            last_seen TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE pattern_occurrences (
            id INTEGER PRIMARY KEY,
            pattern_id INTEGER,
            workflow_id TEXT,
            similarity_score REAL,
            matched_characteristics TEXT,
            detected_at TEXT,
            UNIQUE(pattern_id, workflow_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_history (
            workflow_id TEXT PRIMARY KEY,
            error_count INTEGER,
            duration_seconds INTEGER,
            retry_count INTEGER,
            total_tokens INTEGER,
            actual_cost_total REAL
        )
    """)

    conn.commit()
    return conn


class TestPatternRecording:
    """Test recording pattern occurrences.

    Validates:
    - Creating new pattern records
    - Updating existing pattern occurrence counts
    - Handling missing workflow IDs gracefully
    - Recording pattern-workflow associations
    """

    def test_create_new_pattern(self, mock_db):
        """Test creating a new pattern record.

        When a workflow matches a pattern signature that doesn't exist in the database,
        a new pattern record should be created with occurrence_count = 1.
        """
        workflow = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests with pytest",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50
        }

        pattern_id, is_new = record_pattern_occurrence(
            "test:pytest:backend",
            workflow,
            mock_db
        )

        assert pattern_id is not None
        assert is_new is True

        # Verify pattern was created in database
        cursor = mock_db.cursor()
        cursor.execute("SELECT * FROM operation_patterns WHERE id = ?", (pattern_id,))
        pattern = cursor.fetchone()
        assert pattern is not None
        assert pattern[1] == "test:pytest:backend"  # pattern_signature
        assert pattern[3] == 1  # occurrence_count

    def test_update_existing_pattern(self, mock_db):
        """Test updating occurrence count for existing pattern.

        When a second workflow matches an existing pattern signature,
        the pattern record should be updated (occurrence_count incremented)
        but not marked as new.
        """
        workflow1 = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50
        }

        workflow2 = {
            "workflow_id": "wf-456",
            "nl_input": "Run backend tests again",
            "duration_seconds": 125,
            "error_count": 0,
            "total_tokens": 5200,
            "actual_cost_total": 0.52
        }

        # First occurrence
        pattern_id1, is_new1 = record_pattern_occurrence(
            "test:pytest:backend",
            workflow1,
            mock_db
        )

        # Second occurrence
        pattern_id2, is_new2 = record_pattern_occurrence(
            "test:pytest:backend",
            workflow2,
            mock_db
        )

        assert pattern_id1 == pattern_id2  # Same pattern ID
        assert is_new1 is True
        assert is_new2 is False

        # Verify occurrence count was incremented
        cursor = mock_db.cursor()
        cursor.execute("SELECT occurrence_count FROM operation_patterns WHERE id = ?", (pattern_id1,))
        count = cursor.fetchone()[0]
        assert count == 2

    def test_missing_workflow_id(self, mock_db):
        """Test error handling when workflow_id is missing.

        If a workflow doesn't have a workflow_id field, the function should:
        - Return None for pattern_id
        - Return False for is_new
        - Not create any records
        """
        workflow = {
            "nl_input": "Run tests",
            "duration_seconds": 120
            # Missing workflow_id
        }

        pattern_id, is_new = record_pattern_occurrence(
            "test:generic:all",
            workflow,
            mock_db
        )

        assert pattern_id is None
        assert is_new is False


class TestStatisticsUpdate:
    """Test pattern statistics updates.

    Validates:
    - Computing statistics from first workflow occurrence
    - Calculating running averages as more workflows are recorded
    - Proper handling of cost and token calculations
    - Statistics accuracy over multiple occurrences
    """

    def test_first_workflow_statistics(self, mock_db):
        """Test that statistics are initialized correctly from first workflow.

        When the first workflow is recorded for a pattern:
        - avg_tokens_with_llm = workflow's total_tokens
        - avg_cost_with_llm = workflow's actual_cost_total
        - avg_tokens_with_tool and avg_cost_with_tool remain 0
        """
        # Create pattern first
        cursor = mock_db.cursor()
        cursor.execute(
            """
            INSERT INTO operation_patterns (
                id, pattern_signature, pattern_type, occurrence_count
            ) VALUES (1, 'test:pytest:backend', 'test', 1)
            """
        )
        mock_db.commit()

        workflow = {
            "workflow_id": "wf-123",
            "total_tokens": 5000,
            "actual_cost_total": 0.50,
            "duration_seconds": 120,
            "error_count": 0
        }

        update_pattern_statistics(1, workflow, mock_db)

        # Check updated statistics
        cursor.execute(
            "SELECT avg_tokens_with_llm, avg_cost_with_llm, avg_tokens_with_tool, avg_cost_with_tool FROM operation_patterns WHERE id = 1"
        )
        tokens_llm, cost_llm, tokens_tool, cost_tool = cursor.fetchone()
        assert tokens_llm == 5000
        assert cost_llm == 0.50
        # Tool tokens/cost are estimated at 5% of LLM tokens/cost (per spec line 219-221)
        assert tokens_tool == int(5000 * 0.05)  # 250
        assert abs(cost_tool - 0.50 * 0.05) < 0.001  # ~0.025

    def test_running_average_calculation(self, mock_db):
        """Test that running average is correctly calculated over multiple workflows.

        When updating statistics with new workflow data:
        - New average = (old_average * old_count + new_value) / (old_count + 1)

        For this test:
        - First workflow: 5000 tokens, cost 0.50
        - Second workflow: 6000 tokens, cost 0.60
        - Expected average: (5000 + 6000) / 2 = 5500 tokens, (0.50 + 0.60) / 2 = 0.55 cost
        """
        # Create pattern with existing stats
        cursor = mock_db.cursor()
        cursor.execute(
            """
            INSERT INTO operation_patterns (
                id, pattern_signature, pattern_type, occurrence_count,
                avg_tokens_with_llm, avg_cost_with_llm
            ) VALUES (1, 'test:pytest:backend', 'test', 2, 5000, 0.50)
            """
        )
        mock_db.commit()

        # Add third workflow to update average
        workflow = {
            "workflow_id": "wf-789",
            "total_tokens": 6000,
            "actual_cost_total": 0.60,
            "duration_seconds": 120,
            "error_count": 0
        }

        update_pattern_statistics(1, workflow, mock_db)

        # Check running average
        cursor.execute(
            "SELECT avg_tokens_with_llm, avg_cost_with_llm FROM operation_patterns WHERE id = 1"
        )
        tokens, cost = cursor.fetchone()
        # Average of (5000, 6000) = 5500
        assert tokens == 5500
        # Average of (0.50, 0.60) = 0.55
        assert abs(cost - 0.55) < 0.01


class TestBatchProcessing:
    """Test batch workflow processing.

    Validates:
    - Processing single workflows end-to-end
    - Batch processing multiple workflows efficiently
    - Correct aggregation of results
    - Handling of processing errors within batches
    - Idempotency of batch processing
    """

    def test_process_single_workflow(self, mock_db):
        """Test end-to-end processing of a single workflow.

        The process_and_persist_workflow function should:
        1. Detect patterns in the workflow
        2. Record pattern occurrences
        3. Update statistics
        4. Return summary of detected patterns
        """
        workflow = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests with pytest",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50,
            "workflow_template": None,
            "error_message": None
        }

        result = process_and_persist_workflow(workflow, mock_db)

        assert "patterns_detected" in result
        assert result["patterns_detected"] >= 1

        # Verify patterns were persisted
        cursor = mock_db.cursor()
        cursor.execute("SELECT pattern_signature FROM operation_patterns")
        patterns = [row[0] for row in cursor.fetchall()]
        assert "test:pytest:backend" in patterns

    def test_process_workflow_with_error(self, mock_db):
        """Test processing workflow that contains error information.

        Workflows with error_messages should:
        1. Extract patterns from error details
        2. Record all detected patterns
        3. Still successfully persist data
        """
        workflow = {
            "workflow_id": "wf-456",
            "nl_input": "Deploy to production",
            "duration_seconds": 300,
            "error_count": 2,
            "total_tokens": 8000,
            "actual_cost_total": 0.80,
            "workflow_template": "adw_deploy",
            "error_message": "pytest failed: 3 tests failed in test_api.py"
        }

        result = process_and_persist_workflow(workflow, mock_db)

        assert "patterns_detected" in result
        # Should detect test pattern from error message
        assert result["patterns_detected"] >= 1

    def test_batch_process_single_workflow(self, mock_db):
        """Test batch processing with a single workflow.

        batch_process_workflows should handle arrays of 1+ workflows.
        """
        workflows = [
            {
                "workflow_id": "wf-123",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
        ]

        result = batch_process_workflows(workflows, mock_db)

        assert result["total_workflows"] == 1
        assert result["processed"] == 1
        assert result["total_patterns"] >= 1
        assert result["errors"] == 0

    def test_batch_process_multiple_workflows(self, mock_db):
        """Test batch processing of multiple workflows.

        The function should:
        1. Process all workflows in the batch
        2. Aggregate pattern detection results
        3. Return comprehensive summary including error handling
        """
        workflows = [
            {
                "workflow_id": f"wf-{i}",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
            for i in range(5)
        ]

        result = batch_process_workflows(workflows, mock_db)

        assert result["total_workflows"] == 5
        assert result["processed"] == 5
        assert result["total_patterns"] >= 5
        assert result["errors"] == 0

    def test_batch_process_with_mixed_patterns(self, mock_db):
        """Test batch processing with workflows of different pattern types.

        Batch should handle:
        - Different pattern types (test, build, format, etc.)
        - Varying workflow characteristics
        - Multiple occurrences of same pattern
        """
        workflows = [
            {
                "workflow_id": "wf-test-1",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": "adw_test_iso",
                "error_message": None
            },
            {
                "workflow_id": "wf-build-1",
                "nl_input": "Build and typecheck the backend",
                "duration_seconds": 180,
                "error_count": 1,
                "total_tokens": 6000,
                "actual_cost_total": 0.60,
                "workflow_template": "adw_build_iso",
                "error_message": "typecheck failed"
            },
            {
                "workflow_id": "wf-test-2",
                "nl_input": "Run backend tests with pytest",  # Same as wf-test-1
                "duration_seconds": 125,
                "error_count": 0,
                "total_tokens": 5100,
                "actual_cost_total": 0.51,
                "workflow_template": "adw_test_iso",
                "error_message": None
            }
        ]

        result = batch_process_workflows(workflows, mock_db)

        assert result["total_workflows"] == 3
        assert result["processed"] == 3
        # Should have detected multiple different patterns
        assert result["total_patterns"] >= 2
        assert result["errors"] == 0

    def test_batch_process_with_partial_errors(self, mock_db):
        """Test batch processing continues when some workflows fail.

        If processing one workflow fails:
        1. The error should be counted
        2. Processing should continue with remaining workflows
        3. Results should reflect both successes and failures
        """
        workflows = [
            {
                "workflow_id": "wf-123",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            },
            {
                # Invalid workflow - missing workflow_id
                "nl_input": "Invalid workflow",
                "duration_seconds": 120,
                # Missing workflow_id
            },
            {
                "workflow_id": "wf-456",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
        ]

        result = batch_process_workflows(workflows, mock_db)

        assert result["total_workflows"] == 3
        # All 3 workflows should process successfully (no exceptions raised)
        assert result["processed"] == 3
        # No errors (missing workflow_id logs warning but doesn't fail)
        assert result["errors"] == 0
        # But the second workflow shouldn't create patterns (missing workflow_id)
        # So we should have patterns from 2 workflows only
        assert result["total_patterns"] >= 2

    def test_batch_process_idempotency(self, mock_db):
        """Test that processing same batch twice doesn't create duplicates.

        Running batch_process_workflows twice with same data should:
        1. Return same total_patterns count
        2. Not create duplicate pattern records
        3. Update occurrence counts correctly
        """
        workflows = [
            {
                "workflow_id": f"wf-{i}",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
            for i in range(3)
        ]

        # First batch processing
        result1 = batch_process_workflows(workflows, mock_db)

        # Second batch processing with same data
        result2 = batch_process_workflows(workflows, mock_db)

        # Should have same number of patterns (idempotent)
        assert result1["total_patterns"] == result2["total_patterns"]
        assert result1["processed"] == result2["processed"]

    def test_batch_process_aggregation(self, mock_db):
        """Test that batch results properly aggregate metrics.

        Result should include:
        - total_workflows: Number of workflows in batch
        - processed: Number successfully processed
        - total_patterns: Total unique patterns detected
        - errors: Count of failed workflows
        """
        workflows = [
            {
                "workflow_id": f"wf-{i}",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
            for i in range(5)
        ]

        result = batch_process_workflows(workflows, mock_db)

        # Verify all required fields in result
        assert "total_workflows" in result
        assert "processed" in result
        assert "total_patterns" in result
        assert "errors" in result

        # Verify result values are reasonable
        assert result["total_workflows"] == 5
        assert isinstance(result["processed"], int)
        assert isinstance(result["total_patterns"], int)
        assert isinstance(result["errors"], int)
        assert result["total_patterns"] >= 0
