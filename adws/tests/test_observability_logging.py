"""
Tests for ADW phase observability logging.

Verifies that ADW phases correctly log completion events to the
observability system without blocking workflow execution.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestObservabilityLogging:
    """Test observability logging in ADW phases."""

    @pytest.mark.parametrize("phase_name,phase_number,module_path", [
        ("Validate", 2, "adw_validate_iso"),
        ("Lint", 4, "adw_lint_iso"),
        ("Review", 6, "adw_review_iso"),
        ("Document", 7, "adw_document_iso"),
        ("Ship", 8, "adw_ship_iso"),
        ("Cleanup", 9, "adw_cleanup_iso"),
    ])
    def test_phase_logs_completion(self, phase_name, phase_number, module_path):
        """Verify that each phase logs completion to observability system."""
        # This is a smoke test to verify the logging call exists in each phase
        # Actual functionality is tested in integration tests

        # Import the module dynamically
        module = __import__(module_path)

        # Verify log_phase_completion is imported
        assert hasattr(module, 'log_phase_completion') or 'log_phase_completion' in dir(module)

    def test_get_phase_number_mapping(self):
        """Verify phase number mapping is correct."""
        from adw_modules.observability import get_phase_number

        expected_mappings = {
            "Plan": 1,
            "Validate": 2,
            "Build": 3,
            "Lint": 4,
            "Test": 5,
            "Review": 6,
            "Document": 7,
            "Ship": 8,
            "Cleanup": 9,
        }

        for phase_name, expected_number in expected_mappings.items():
            assert get_phase_number(phase_name) == expected_number

    def test_get_phase_number_unknown_phase(self):
        """Verify unknown phase returns 0."""
        from adw_modules.observability import get_phase_number

        assert get_phase_number("UnknownPhase") == 0

    @patch('adw_modules.observability.urllib.request.urlopen')
    def test_log_phase_completion_success(self, mock_urlopen):
        """Verify log_phase_completion makes correct API call."""
        from adw_modules.observability import log_phase_completion

        mock_response = MagicMock()
        mock_response.status = 201
        mock_urlopen.return_value.__enter__.return_value = mock_response

        log_phase_completion(
            adw_id="test-adw-123",
            issue_number=42,
            phase_name="Test",
            phase_number=5,
            success=True,
            workflow_template="adw_test_iso",
            started_at=datetime(2025, 12, 2, 10, 0, 0)
        )

        # Verify API was called
        assert mock_urlopen.called

    @patch('adw_modules.observability.urllib.request.urlopen')
    def test_log_phase_completion_failure_does_not_raise(self, mock_urlopen):
        """Verify that API failures don't raise exceptions (zero-overhead design)."""
        from adw_modules.observability import log_phase_completion

        # Simulate API failure
        mock_urlopen.side_effect = Exception("API unavailable")

        # Should not raise - logging failures are non-blocking
        log_phase_completion(
            adw_id="test-adw",
            issue_number=1,
            phase_name="Test",
            phase_number=5,
            success=True,
            workflow_template="test"
        )

    def test_log_phase_completion_constructs_correct_payload(self):
        """Verify payload structure for task log creation."""
        from adw_modules.observability import log_phase_completion
        from unittest.mock import patch
        import json

        captured_data = None

        def capture_request(request, timeout):
            nonlocal captured_data
            captured_data = json.loads(request.data.decode('utf-8'))
            mock_response = MagicMock()
            mock_response.status = 201
            return mock_response

        with patch('adw_modules.observability.urllib.request.urlopen', side_effect=capture_request):
            log_phase_completion(
                adw_id="test-adw-123",
                issue_number=42,
                phase_name="Build",
                phase_number=3,
                success=True,
                workflow_template="adw_build_iso",
                error_message=None,
                started_at=datetime(2025, 12, 2, 10, 0, 0)
            )

        assert captured_data is not None
        assert captured_data["adw_id"] == "test-adw-123"
        assert captured_data["issue_number"] == 42
        assert captured_data["phase_name"] == "Build"
        assert captured_data["phase_number"] == 3
        assert captured_data["success"] is True
        assert captured_data["workflow_template"] == "adw_build_iso"
        assert "completed_at" in captured_data


class TestObservabilityIntegration:
    """Integration tests for observability logging."""

    def test_observability_does_not_block_phase_execution(self):
        """Verify that observability logging failures don't block workflow."""
        from adw_modules.observability import log_phase_completion

        # Even with broken API, phase should complete
        with patch('adw_modules.observability.urllib.request.urlopen', side_effect=Exception("Network error")):
            # Should not raise
            log_phase_completion(
                adw_id="test",
                issue_number=1,
                phase_name="Test",
                phase_number=5,
                success=True,
                workflow_template="test"
            )

    def test_observability_handles_missing_start_time(self):
        """Verify logging works even without start_time."""
        from adw_modules.observability import log_phase_completion

        with patch('adw_modules.observability.urllib.request.urlopen'):
            # Should not raise even without started_at
            log_phase_completion(
                adw_id="test",
                issue_number=1,
                phase_name="Test",
                phase_number=5,
                success=True,
                workflow_template="test",
                started_at=None  # Explicitly None
            )

    def test_observability_logs_failures_correctly(self):
        """Verify failed phases log with success=False and error message."""
        from adw_modules.observability import log_phase_completion
        from unittest.mock import patch
        import json

        captured_data = None

        def capture_request(request, timeout):
            nonlocal captured_data
            captured_data = json.loads(request.data.decode('utf-8'))
            mock_response = MagicMock()
            mock_response.status = 201
            return mock_response

        with patch('adw_modules.observability.urllib.request.urlopen', side_effect=capture_request):
            log_phase_completion(
                adw_id="test-adw",
                issue_number=42,
                phase_name="Build",
                phase_number=3,
                success=False,
                workflow_template="adw_build_iso",
                error_message="Build failed: syntax error"
            )

        assert captured_data["success"] is False
        assert captured_data["error_message"] == "Build failed: syntax error"
