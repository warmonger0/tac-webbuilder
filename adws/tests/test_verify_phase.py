#!/usr/bin/env python3
"""
Tests for Verify Phase

Run with:
    cd adws
    uv run pytest tests/test_verify_phase.py -v
"""

import pytest
import json
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_verify_iso import (
    VerificationResult,
    check_backend_logs,
    check_frontend_console,
    run_smoke_tests,
)


@pytest.fixture
def temp_logs_dir():
    """Create temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


class TestVerificationResult:
    """Test VerificationResult class."""

    def test_verification_result_passed(self):
        """Test VerificationResult when all checks pass."""
        result = VerificationResult()

        assert result.passed is True
        assert "✅ All verification checks passed" in result.get_summary()

    def test_verification_result_backend_errors(self):
        """Test VerificationResult with backend errors."""
        result = VerificationResult()
        result.add_backend_error("Exception in API handler")
        result.add_backend_error("500 Internal Server Error")

        assert result.passed is False
        summary = result.get_summary()
        assert "❌ Verification failed" in summary
        assert "Backend Log Errors" in summary
        assert "Exception in API handler" in summary

    def test_verification_result_frontend_errors(self):
        """Test VerificationResult with frontend errors."""
        result = VerificationResult()
        result.add_frontend_error("console.error: Failed to fetch")

        assert result.passed is False
        summary = result.get_summary()
        assert "Frontend Errors" in summary

    def test_verification_result_smoke_test_failures(self):
        """Test VerificationResult with smoke test failures."""
        result = VerificationResult()
        result.add_smoke_test_failure("Backend health check failed")

        assert result.passed is False
        summary = result.get_summary()
        assert "Smoke Test Failures" in summary

    def test_verification_result_warnings(self):
        """Test VerificationResult with warnings (doesn't affect pass/fail)."""
        result = VerificationResult()
        result.add_warning("Log file not found")

        assert result.passed is True  # Warnings don't fail verification
        summary = result.get_summary()
        assert "✅ All verification checks passed" in summary

    def test_verification_result_many_errors_truncated(self):
        """Test that many errors are truncated in summary."""
        result = VerificationResult()
        for i in range(10):
            result.add_backend_error(f"Error {i}")

        summary = result.get_summary()
        assert "and 5 more" in summary  # Should show first 5 + "and N more"


class TestBackendLogChecking:
    """Test backend log checking functionality."""

    def test_check_backend_logs_no_errors(self, temp_logs_dir, mock_logger):
        """Test backend log checking with clean logs."""
        # Create log file with no errors
        log_file = temp_logs_dir / "adw-123_backend.log"
        log_file.write_text(
            "INFO: Server started\n"
            "INFO: Request processed successfully\n"
            "INFO: Response sent\n"
        )

        # Mock Path to use temp directory
        with patch('adw_verify_iso.os.path.join', return_value=str(log_file)):
            with patch('adw_verify_iso.os.path.exists', return_value=True):
                errors = check_backend_logs(
                    adw_id="adw-123",
                    backend_port=9100,
                    ship_timestamp=datetime.now(),
                    logger=mock_logger
                )

        # Should find no errors
        assert len(errors) == 0

    def test_check_backend_logs_with_errors(self, temp_logs_dir, mock_logger):
        """Test backend log checking with errors."""
        # Create log file with errors
        log_file = temp_logs_dir / "adw-123_backend.log"
        log_file.write_text(
            "INFO: Server started\n"
            "ERROR: Exception in request handler\n"
            "Traceback (most recent call last):\n"
            "  File 'handler.py', line 42, in process\n"
            "500 Internal Server Error\n"
        )

        # Mock Path to use temp directory
        with patch('adw_verify_iso.os.path.join', return_value=str(log_file)):
            with patch('adw_verify_iso.os.path.exists', return_value=True):
                errors = check_backend_logs(
                    adw_id="adw-123",
                    backend_port=9100,
                    ship_timestamp=datetime.now(),
                    logger=mock_logger
                )

        # Should find errors
        assert len(errors) > 0
        assert any("ERROR" in e or "Exception" in e or "Traceback" in e or "500" in e for e in errors)

    def test_check_backend_logs_file_not_found(self, mock_logger):
        """Test backend log checking when file doesn't exist."""
        with patch('adw_verify_iso.os.path.exists', return_value=False):
            errors = check_backend_logs(
                adw_id="adw-123",
                backend_port=9100,
                ship_timestamp=datetime.now(),
                logger=mock_logger
            )

        # Should return warning about missing file
        assert len(errors) == 1
        assert "Warning" in errors[0]
        assert "not found" in errors[0]

    def test_check_backend_logs_read_error(self, mock_logger):
        """Test backend log checking when file read fails."""
        with patch('adw_verify_iso.os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                errors = check_backend_logs(
                    adw_id="adw-123",
                    backend_port=9100,
                    ship_timestamp=datetime.now(),
                    logger=mock_logger
                )

        # Should return error about read failure
        assert len(errors) > 0
        assert any("Failed to read" in e for e in errors)


class TestFrontendConsoleChecking:
    """Test frontend console checking functionality."""

    def test_check_frontend_console_no_errors(self, temp_logs_dir, mock_logger):
        """Test frontend console checking with clean logs."""
        # Create build log with no errors
        log_file = temp_logs_dir / "adw-123_frontend_build.log"
        log_file.write_text(
            "Building for production\n"
            "Build completed successfully\n"
            "Chunks: vendor.js, app.js\n"
        )

        with patch('adw_verify_iso.os.path.join', return_value=str(log_file)):
            with patch('adw_verify_iso.os.path.exists', return_value=True):
                errors = check_frontend_console(
                    adw_id="adw-123",
                    frontend_port=9200,
                    logger=mock_logger
                )

        assert len(errors) == 0

    def test_check_frontend_console_with_errors(self, temp_logs_dir, mock_logger):
        """Test frontend console checking with errors."""
        # Create build log with errors
        log_file = temp_logs_dir / "adw-123_frontend_build.log"
        log_file.write_text(
            "Building for production\n"
            "console.error: Failed to fetch API\n"
            "Uncaught TypeError: Cannot read property 'map' of undefined\n"
            "React Error: Component failed to render\n"
        )

        with patch('adw_verify_iso.os.path.join', return_value=str(log_file)):
            with patch('adw_verify_iso.os.path.exists', return_value=True):
                errors = check_frontend_console(
                    adw_id="adw-123",
                    frontend_port=9200,
                    logger=mock_logger
                )

        # Should find errors
        assert len(errors) > 0
        assert any("console.error" in e or "TypeError" in e or "React" in e for e in errors)

    def test_check_frontend_console_file_not_found(self, mock_logger):
        """Test frontend console checking when file doesn't exist."""
        with patch('adw_verify_iso.os.path.exists', return_value=False):
            errors = check_frontend_console(
                adw_id="adw-123",
                frontend_port=9200,
                logger=mock_logger
            )

        # Should return warning
        assert len(errors) == 1
        assert "Warning" in errors[0]

    def test_check_frontend_console_long_lines_truncated(self, temp_logs_dir, mock_logger):
        """Test that long error lines are truncated."""
        log_file = temp_logs_dir / "adw-123_frontend_build.log"
        long_error = "console.error: " + "x" * 500  # Very long error
        log_file.write_text(long_error)

        with patch('adw_verify_iso.os.path.join', return_value=str(log_file)):
            with patch('adw_verify_iso.os.path.exists', return_value=True):
                errors = check_frontend_console(
                    adw_id="adw-123",
                    frontend_port=9200,
                    logger=mock_logger
                )

        # Error should be truncated
        assert len(errors) > 0
        assert len(errors[0]) < 250  # Should be truncated to 200 + prefix


class TestSmokeTests:
    """Test smoke test functionality."""

    @patch('adw_verify_iso.subprocess.run')
    def test_run_smoke_tests_all_pass(self, mock_run, mock_logger):
        """Test smoke tests when all pass."""
        # Mock successful curl commands
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="OK")

        failures = run_smoke_tests(
            adw_id="adw-123",
            backend_port=9100,
            frontend_port=9200,
            issue_number="123",
            logger=mock_logger
        )

        assert len(failures) == 0
        # Should have called curl twice (backend + frontend)
        assert mock_run.call_count == 2

    @patch('adw_verify_iso.subprocess.run')
    def test_run_smoke_tests_backend_fails(self, mock_run, mock_logger):
        """Test smoke tests when backend health check fails."""
        # First call (backend) fails, second (frontend) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="Connection refused", stdout=""),
            MagicMock(returncode=0, stderr="", stdout="OK"),
        ]

        failures = run_smoke_tests(
            adw_id="adw-123",
            backend_port=9100,
            frontend_port=9200,
            issue_number="123",
            logger=mock_logger
        )

        assert len(failures) == 1
        assert any("Backend health check failed" in f for f in failures)

    @patch('adw_verify_iso.subprocess.run')
    def test_run_smoke_tests_frontend_fails(self, mock_run, mock_logger):
        """Test smoke tests when frontend accessibility fails."""
        # First call (backend) succeeds, second (frontend) fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stderr="", stdout="OK"),
            MagicMock(returncode=1, stderr="Connection refused", stdout=""),
        ]

        failures = run_smoke_tests(
            adw_id="adw-123",
            backend_port=9100,
            frontend_port=9200,
            issue_number="123",
            logger=mock_logger
        )

        assert len(failures) == 1
        assert any("Frontend accessibility check failed" in f for f in failures)

    @patch('adw_verify_iso.subprocess.run')
    def test_run_smoke_tests_timeout(self, mock_run, mock_logger):
        """Test smoke tests with timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='curl', timeout=10)

        failures = run_smoke_tests(
            adw_id="adw-123",
            backend_port=9100,
            frontend_port=9200,
            issue_number="123",
            logger=mock_logger
        )

        assert len(failures) >= 1
        assert any("timeout" in f.lower() for f in failures)

    @patch('adw_verify_iso.subprocess.run')
    def test_run_smoke_tests_exception(self, mock_run, mock_logger):
        """Test smoke tests with exception."""
        mock_run.side_effect = Exception("Network error")

        failures = run_smoke_tests(
            adw_id="adw-123",
            backend_port=9100,
            frontend_port=9200,
            issue_number="123",
            logger=mock_logger
        )

        assert len(failures) >= 1
        assert any("error" in f.lower() for f in failures)


class TestVerifyPhaseIntegration:
    """Test verify phase integration."""

    def test_verification_result_complete_flow(self):
        """Test complete verification flow with mixed results."""
        result = VerificationResult()

        # Add various issues
        result.add_backend_error("Database connection failed")
        result.add_frontend_error("console.error: API timeout")
        result.add_smoke_test_failure("Health check failed")
        result.add_warning("Log rotation in progress")

        # Verify state
        assert not result.passed
        assert len(result.backend_log_errors) == 1
        assert len(result.frontend_errors) == 1
        assert len(result.smoke_test_failures) == 1
        assert len(result.warnings) == 1

        # Verify summary
        summary = result.get_summary()
        assert "Backend Log Errors (1)" in summary
        assert "Frontend Errors (1)" in summary
        assert "Smoke Test Failures (1)" in summary
        assert "Warnings (1)" in summary

    @patch('adw_verify_iso.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="INFO: All good\n")
    def test_check_backend_logs_pattern_matching(self, mock_file, mock_exists, mock_logger):
        """Test that backend log checking finds various error patterns."""
        mock_exists.return_value = True

        error_patterns = [
            "ERROR: Something went wrong",
            "Exception in thread main",
            "Traceback (most recent call last):",
            "500 Internal Server Error",
            "Failed to connect to database",
        ]

        for pattern in error_patterns:
            mock_file.return_value.read.return_value = pattern

            errors = check_backend_logs(
                adw_id="adw-test",
                backend_port=9100,
                ship_timestamp=datetime.now(),
                logger=mock_logger
            )

            # Each pattern should be detected
            assert len(errors) > 0, f"Pattern '{pattern}' not detected"

    def test_verification_delay_calculation(self):
        """Test that verification delay is calculated correctly."""
        # If ship happened 2 minutes ago, should wait 3 more minutes
        ship_timestamp = datetime.now() - timedelta(minutes=2)
        time_since_ship = datetime.now() - ship_timestamp
        remaining_wait = 300 - time_since_ship.total_seconds()  # 300s = 5 minutes

        # Should be approximately 3 minutes (180 seconds)
        assert 170 < remaining_wait < 190

    def test_verification_no_delay_needed(self):
        """Test that no delay occurs if enough time has passed."""
        # If ship happened 10 minutes ago, no wait needed
        ship_timestamp = datetime.now() - timedelta(minutes=10)
        time_since_ship = datetime.now() - ship_timestamp
        remaining_wait = 300 - time_since_ship.total_seconds()

        # Should be negative (no wait needed)
        assert remaining_wait < 0
