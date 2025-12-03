"""Tests for structured logging service."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from core.models.structured_logs import LogLevel, LogSource
from services.structured_logger import StructuredLogger, get_structured_logger


class TestStructuredLogger:
    """Tests for StructuredLogger service."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create a logger instance with temp directory."""
        return StructuredLogger(log_dir=temp_log_dir, enable_console=False, enable_file=True)

    def test_initialization(self, temp_log_dir):
        """Test logger initialization."""
        logger = StructuredLogger(log_dir=temp_log_dir)
        assert logger.log_dir == temp_log_dir
        assert logger.enable_file is True
        assert logger.enable_console is False
        assert temp_log_dir.exists()

    def test_log_workflow_event(self, logger, temp_log_dir):
        """Test logging a workflow event."""
        success = logger.log_workflow_event(
            adw_id="adw-test123",
            issue_number=42,
            message="Test workflow event",
            workflow_status="in_progress",
            phase_name="Plan",
            phase_number=1,
            phase_status="completed",
            tokens_used=1000,
            cost_usd=0.05,
        )

        assert success is True

        # Check log file exists
        log_file = temp_log_dir / "workflow_adw-test123.jsonl"
        assert log_file.exists()

        # Read and parse log entry
        with open(log_file, "r") as f:
            log_entry = json.loads(f.read().strip())

        assert log_entry["adw_id"] == "adw-test123"
        assert log_entry["issue_number"] == 42
        assert log_entry["message"] == "Test workflow event"
        assert log_entry["workflow_status"] == "in_progress"
        assert log_entry["phase_name"] == "Plan"
        assert log_entry["phase_number"] == 1
        assert log_entry["tokens_used"] == 1000
        assert log_entry["cost_usd"] == 0.05
        assert "event_id" in log_entry
        assert "timestamp" in log_entry

    def test_log_phase_event(self, logger, temp_log_dir):
        """Test logging a phase event."""
        started = datetime.utcnow()
        success = logger.log_phase_event(
            adw_id="adw-phase123",
            issue_number=100,
            phase_name="Build",
            phase_number=3,
            phase_status="completed",
            message="Build phase completed successfully",
            started_at=started,
            duration_seconds=45.2,
        )

        assert success is True

        # Check log file
        log_file = temp_log_dir / "workflow_adw-phase123.jsonl"
        assert log_file.exists()

        with open(log_file, "r") as f:
            log_entry = json.loads(f.read().strip())

        assert log_entry["phase_name"] == "Build"
        assert log_entry["phase_number"] == 3
        assert log_entry["phase_status"] == "completed"
        assert log_entry["duration_seconds"] == 45.2

    def test_log_system_event(self, logger, temp_log_dir):
        """Test logging a system event."""
        success = logger.log_system_event(
            component="database",
            operation="migrate",
            status="success",
            message="Database migration completed",
            duration_ms=1500.5,
        )

        assert success is True

        # System events go to general log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_log_dir / f"general_{date_str}.jsonl"
        assert log_file.exists()

        with open(log_file, "r") as f:
            log_entry = json.loads(f.read().strip())

        assert log_entry["component"] == "database"
        assert log_entry["operation"] == "migrate"
        assert log_entry["status"] == "success"
        assert log_entry["duration_ms"] == 1500.5

    def test_log_database_event(self, logger, temp_log_dir):
        """Test logging a database event."""
        success = logger.log_database_event(
            operation="select",
            table="phase_queue",
            duration_ms=5.2,
            status="success",
            message="Query executed successfully",
            rows_affected=10,
        )

        assert success is True

    def test_log_http_event(self, logger, temp_log_dir):
        """Test logging an HTTP event."""
        success = logger.log_http_event(
            method="POST",
            path="/api/v1/workflows",
            status_code=201,
            duration_ms=125.5,
            message="Workflow created",
            client_ip="192.168.1.1",
        )

        assert success is True

    def test_log_metric(self, logger, temp_log_dir):
        """Test logging a metric."""
        success = logger.log_metric(
            metric_name="workflow_duration",
            metric_value=120.5,
            metric_unit="seconds",
            message="Workflow duration recorded",
            dimensions={"workflow": "sdlc", "status": "completed"},
        )

        assert success is True

    def test_per_workflow_isolation(self, logger, temp_log_dir):
        """Test that different workflows write to separate files."""
        logger.log_workflow_event(
            adw_id="adw-workflow1",
            issue_number=1,
            message="Workflow 1 event",
            workflow_status="started",
        )

        logger.log_workflow_event(
            adw_id="adw-workflow2",
            issue_number=2,
            message="Workflow 2 event",
            workflow_status="started",
        )

        # Check separate log files exist
        log_file1 = temp_log_dir / "workflow_adw-workflow1.jsonl"
        log_file2 = temp_log_dir / "workflow_adw-workflow2.jsonl"

        assert log_file1.exists()
        assert log_file2.exists()

        # Verify contents
        with open(log_file1, "r") as f:
            entry1 = json.loads(f.read().strip())
            assert entry1["adw_id"] == "adw-workflow1"

        with open(log_file2, "r") as f:
            entry2 = json.loads(f.read().strip())
            assert entry2["adw_id"] == "adw-workflow2"

    def test_multiple_events_same_workflow(self, logger, temp_log_dir):
        """Test multiple events for same workflow append to same file."""
        adw_id = "adw-multi123"

        for i in range(3):
            logger.log_phase_event(
                adw_id=adw_id,
                issue_number=100,
                phase_name=f"Phase{i}",
                phase_number=i + 1,
                phase_status="completed",
                message=f"Phase {i} completed",
            )

        log_file = temp_log_dir / f"workflow_{adw_id}.jsonl"
        assert log_file.exists()

        # Count lines (should be 3)
        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 3

        # Verify each entry
        for i, line in enumerate(lines):
            entry = json.loads(line.strip())
            assert entry["phase_name"] == f"Phase{i}"
            assert entry["phase_number"] == i + 1

    def test_error_logging(self, logger, temp_log_dir):
        """Test logging errors."""
        success = logger.log_workflow_event(
            adw_id="adw-error123",
            issue_number=500,
            message="Workflow failed",
            workflow_status="failed",
            level=LogLevel.ERROR,
            error_message="Test execution failed",
            error_type="TestFailureError",
        )

        assert success is True

        log_file = temp_log_dir / "workflow_adw-error123.jsonl"
        with open(log_file, "r") as f:
            entry = json.loads(f.read().strip())

        assert entry["level"] == "error"
        assert entry["error_message"] == "Test execution failed"
        assert entry["error_type"] == "TestFailureError"

    def test_context_data(self, logger, temp_log_dir):
        """Test logging with additional context."""
        success = logger.log_workflow_event(
            adw_id="adw-context123",
            issue_number=200,
            message="Event with context",
            workflow_status="in_progress",
            custom_field="custom_value",
            metadata={"key": "value"},
        )

        assert success is True

        log_file = temp_log_dir / "workflow_adw-context123.jsonl"
        with open(log_file, "r") as f:
            entry = json.loads(f.read().strip())

        assert entry["context"]["custom_field"] == "custom_value"
        assert entry["context"]["metadata"] == {"key": "value"}

    def test_file_disabled(self, temp_log_dir):
        """Test logger with file output disabled."""
        logger = StructuredLogger(log_dir=temp_log_dir, enable_file=False)

        success = logger.log_system_event(
            component="test",
            operation="test",
            status="success",
            message="Test event",
        )

        # Should return True but not write file
        assert success is True

        # No log files should be created
        assert len(list(temp_log_dir.glob("*.jsonl"))) == 0

    def test_singleton_pattern(self):
        """Test get_structured_logger returns singleton."""
        logger1 = get_structured_logger()
        logger2 = get_structured_logger()

        assert logger1 is logger2
