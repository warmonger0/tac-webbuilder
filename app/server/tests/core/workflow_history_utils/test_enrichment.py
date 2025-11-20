"""
Unit tests for workflow_history_utils.enrichment module.

Tests all enrichment functions for workflow data augmentation.
Covers edge cases including:
- Cost data enrichment from cost tracker
- Cost estimate loading from storage
- GitHub issue state fetching
- Workflow template defaults
- Error categorization
- Duration calculations
- Complexity estimation
- Temporal field extraction
- Score calculations
- Insight generation (anomalies and recommendations)
- Resync operations
- Main orchestrator workflow
"""

import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from core.workflow_history_utils.enrichment import (
    enrich_complexity,
    enrich_cost_data,
    enrich_cost_data_for_resync,
    enrich_cost_estimate,
    enrich_duration,
    enrich_error_category,
    enrich_github_state,
    enrich_insights,
    enrich_scores,
    enrich_temporal_fields,
    enrich_workflow,
    enrich_workflow_template,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow_data():
    """
    Create sample workflow data dictionary.

    Returns typical workflow data structure for testing.
    """
    return {
        "adw_id": "test-adw-123",
        "issue_number": 42,
        "status": "completed",
        "start_time": "2025-01-15T10:30:00Z",
        "nl_input": "Create a new feature",
        "steps_total": 10,
        "model_used": None,
    }


@pytest.fixture
def sample_cost_data():
    """
    Create mock CostData object with phases.

    Returns a properly structured cost data mock.
    """
    mock_cost_data = Mock()
    mock_cost_data.total_cost = 1.25
    mock_cost_data.cache_efficiency_percent = 45.5

    # Create mock phases with token data
    phase1 = Mock()
    phase1.phase = "plan"
    phase1.cost = 0.35
    phase1.model = "claude-3-5-sonnet-20241022"
    phase1.tokens = Mock()
    phase1.tokens.input_tokens = 1000
    phase1.tokens.cache_creation_tokens = 200
    phase1.tokens.cache_read_tokens = 100
    phase1.tokens.output_tokens = 500

    phase2 = Mock()
    phase2.phase = "build"
    phase2.cost = 0.90
    phase2.model = "claude-3-5-sonnet-20241022"
    phase2.tokens = Mock()
    phase2.tokens.input_tokens = 2000
    phase2.tokens.cache_creation_tokens = 300
    phase2.tokens.cache_read_tokens = 150
    phase2.tokens.output_tokens = 800

    mock_cost_data.phases = [phase1, phase2]

    return mock_cost_data


@pytest.fixture
def mock_phase_metrics():
    """
    Create mock phase metrics for performance analysis.

    Returns typical phase metrics structure.
    """
    return {
        "phase_durations": {
            "plan": 30.5,
            "build": 45.2,
            "test": 20.1
        },
        "bottleneck_phase": "build",
        "idle_time_seconds": 5.3
    }


# ============================================================================
# Test enrich_cost_data() - Cost Data from cost_tracker
# ============================================================================


class TestEnrichCostData:
    """Tests for enrich_cost_data() function."""

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_enriches_with_full_cost_data(
        self, mock_calc_metrics, mock_read_cost, sample_workflow_data, sample_cost_data, mock_phase_metrics
    ):
        """Test enrichment with complete cost data."""
        # Arrange
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = mock_phase_metrics

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["actual_cost_total"] == 1.25
        assert sample_workflow_data["input_tokens"] == 3000
        assert sample_workflow_data["cached_tokens"] == 500
        assert sample_workflow_data["cache_hit_tokens"] == 250
        assert sample_workflow_data["output_tokens"] == 1300
        assert sample_workflow_data["total_tokens"] == 5050
        assert sample_workflow_data["cache_efficiency_percent"] == 45.5
        assert sample_workflow_data["model_used"] == "claude-3-5-sonnet-20241022"

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_enriches_cost_breakdown_by_phase(
        self, mock_calc_metrics, mock_read_cost, sample_workflow_data, sample_cost_data, mock_phase_metrics
    ):
        """Test cost breakdown includes by_phase data."""
        # Arrange
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = mock_phase_metrics

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert
        assert "cost_breakdown" in sample_workflow_data
        breakdown = sample_workflow_data["cost_breakdown"]
        assert breakdown["actual_total"] == 1.25
        assert breakdown["by_phase"] == {"plan": 0.35, "build": 0.90}

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_enriches_phase_metrics(
        self, mock_calc_metrics, mock_read_cost, sample_workflow_data, sample_cost_data, mock_phase_metrics
    ):
        """Test phase metrics are added to workflow data."""
        # Arrange
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = mock_phase_metrics

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["phase_durations"] == mock_phase_metrics["phase_durations"]
        assert sample_workflow_data["bottleneck_phase"] == "build"
        assert sample_workflow_data["idle_time_seconds"] == 5.3

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_does_not_overwrite_existing_model(self, mock_read_cost, sample_workflow_data, sample_cost_data):
        """Test existing model_used is not overwritten."""
        # Arrange
        sample_workflow_data["model_used"] = "existing-model"
        mock_read_cost.return_value = sample_cost_data

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["model_used"] == "existing-model"

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_handles_missing_cost_data(self, mock_read_cost, sample_workflow_data):
        """Test graceful handling when cost data is not available."""
        # Arrange
        mock_read_cost.return_value = None

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert - workflow_data unchanged
        assert "actual_cost_total" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_handles_cost_data_without_total_cost(self, mock_read_cost, sample_workflow_data):
        """Test handling cost data object without total_cost attribute."""
        # Arrange
        mock_cost_data = Mock(spec=[])  # No attributes
        mock_read_cost.return_value = mock_cost_data

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert - workflow_data unchanged
        assert "actual_cost_total" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_handles_cost_data_with_empty_phases(self, mock_read_cost, sample_workflow_data):
        """Test handling cost data with empty phases list."""
        # Arrange
        mock_cost_data = Mock()
        mock_cost_data.total_cost = 1.0
        mock_cost_data.phases = []
        mock_read_cost.return_value = mock_cost_data

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert - cost total set but no breakdown
        assert sample_workflow_data["actual_cost_total"] == 1.0
        assert "cost_breakdown" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_handles_empty_phase_metrics(
        self, mock_calc_metrics, mock_read_cost, sample_workflow_data, sample_cost_data
    ):
        """Test handling when phase metrics calculation returns empty."""
        # Arrange
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = {"phase_durations": {}, "bottleneck_phase": None, "idle_time_seconds": 0}

        # Act
        enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert - no phase metrics added
        assert "phase_durations" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_handles_exception_gracefully(self, mock_read_cost, sample_workflow_data, caplog):
        """Test exception handling logs debug message."""
        # Arrange
        mock_read_cost.side_effect = Exception("Database error")

        # Act
        with caplog.at_level(logging.DEBUG):
            enrich_cost_data(sample_workflow_data, "test-adw-123")

        # Assert - exception caught and logged
        assert "No cost data for test-adw-123" in caplog.text


# ============================================================================
# Test enrich_cost_estimate() - Cost Estimates from Storage
# ============================================================================


class TestEnrichCostEstimate:
    """Tests for enrich_cost_estimate() function."""

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_enriches_with_cost_estimate(self, mock_get_estimate, sample_workflow_data):
        """Test enrichment with cost estimate data."""
        # Arrange
        mock_get_estimate.return_value = {
            "estimated_cost_total": 2.50,
            "estimated_cost_breakdown": {
                "plan": 0.50,
                "build": 1.00,
                "test": 0.50,
                "review": 0.25,
                "document": 0.15,
                "ship": 0.10
            }
        }

        # Act
        enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["estimated_cost_total"] == 2.50
        assert "cost_breakdown" in sample_workflow_data
        assert sample_workflow_data["cost_breakdown"]["estimated_total"] == 2.50
        assert sample_workflow_data["cost_breakdown"]["estimated_by_phase"]["plan"] == 0.50

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_creates_new_cost_breakdown(self, mock_get_estimate, sample_workflow_data):
        """Test creates new cost_breakdown structure if not present."""
        # Arrange
        mock_get_estimate.return_value = {
            "estimated_cost_total": 2.50,
            "estimated_cost_breakdown": {"plan": 0.50}
        }

        # Act
        enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert
        breakdown = sample_workflow_data["cost_breakdown"]
        assert breakdown["estimated_total"] == 2.50
        assert breakdown["actual_total"] == 0.0
        assert breakdown["by_phase"] == {}
        assert breakdown["estimated_by_phase"] == {"plan": 0.50}

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_updates_existing_cost_breakdown(self, mock_get_estimate, sample_workflow_data):
        """Test updates existing cost_breakdown with estimate data."""
        # Arrange
        sample_workflow_data["cost_breakdown"] = {
            "actual_total": 1.25,
            "by_phase": {"plan": 0.35, "build": 0.90}
        }
        mock_get_estimate.return_value = {
            "estimated_cost_total": 2.50,
            "estimated_cost_breakdown": {"plan": 0.50}
        }

        # Act
        enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert
        breakdown = sample_workflow_data["cost_breakdown"]
        assert breakdown["estimated_total"] == 2.50
        assert breakdown["actual_total"] == 1.25
        assert breakdown["estimated_by_phase"] == {"plan": 0.50}

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_handles_json_string_cost_breakdown(self, mock_get_estimate, sample_workflow_data):
        """Test handles cost_breakdown as JSON string."""
        # Arrange
        sample_workflow_data["cost_breakdown"] = json.dumps({"actual_total": 1.25})
        mock_get_estimate.return_value = {
            "estimated_cost_total": 2.50,
            "estimated_cost_breakdown": {}
        }

        # Act
        enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert
        breakdown = sample_workflow_data["cost_breakdown"]
        assert isinstance(breakdown, dict)
        assert breakdown["estimated_total"] == 2.50

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_skips_when_no_issue_number(self, mock_get_estimate):
        """Test skips enrichment when issue_number is missing."""
        # Arrange
        workflow_data = {"adw_id": "test-adw-123"}

        # Act
        enrich_cost_estimate(workflow_data, "test-adw-123")

        # Assert
        mock_get_estimate.assert_not_called()
        assert "estimated_cost_total" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_handles_missing_cost_estimate(self, mock_get_estimate, sample_workflow_data):
        """Test graceful handling when cost estimate is not found."""
        # Arrange
        mock_get_estimate.return_value = None

        # Act
        enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert - workflow_data unchanged
        assert "estimated_cost_total" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.get_cost_estimate')
    def test_handles_exception_gracefully(self, mock_get_estimate, sample_workflow_data, caplog):
        """Test exception handling logs debug message."""
        # Arrange
        mock_get_estimate.side_effect = ValueError("Invalid issue number")

        # Act
        with caplog.at_level(logging.DEBUG):
            enrich_cost_estimate(sample_workflow_data, "test-adw-123")

        # Assert - exception caught and logged
        assert "Could not load cost estimate" in caplog.text


# ============================================================================
# Test enrich_github_state() - GitHub Issue State
# ============================================================================


class TestEnrichGithubState:
    """Tests for enrich_github_state() function."""

    @patch('core.workflow_history_utils.enrichment.fetch_github_issue_state')
    def test_enriches_with_github_state(self, mock_fetch_state, sample_workflow_data):
        """Test enrichment with GitHub issue state."""
        # Arrange
        mock_fetch_state.return_value = "open"

        # Act
        enrich_github_state(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["gh_issue_state"] == "open"
        mock_fetch_state.assert_called_once_with(42)

    @patch('core.workflow_history_utils.enrichment.fetch_github_issue_state')
    def test_skips_when_no_issue_number(self, mock_fetch_state):
        """Test skips enrichment when issue_number is missing."""
        # Arrange
        workflow_data = {"adw_id": "test-adw-123"}

        # Act
        enrich_github_state(workflow_data, "test-adw-123")

        # Assert
        mock_fetch_state.assert_not_called()
        assert "gh_issue_state" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.fetch_github_issue_state')
    def test_handles_closed_state(self, mock_fetch_state, sample_workflow_data):
        """Test handling of closed GitHub issue state."""
        # Arrange
        mock_fetch_state.return_value = "closed"

        # Act
        enrich_github_state(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["gh_issue_state"] == "closed"

    @patch('core.workflow_history_utils.enrichment.fetch_github_issue_state')
    def test_handles_missing_github_state(self, mock_fetch_state, sample_workflow_data):
        """Test graceful handling when GitHub state is not available."""
        # Arrange
        mock_fetch_state.return_value = None

        # Act
        enrich_github_state(sample_workflow_data, "test-adw-123")

        # Assert - workflow_data unchanged
        assert "gh_issue_state" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.fetch_github_issue_state')
    def test_handles_exception_gracefully(self, mock_fetch_state, sample_workflow_data, caplog):
        """Test exception handling logs debug message."""
        # Arrange
        mock_fetch_state.side_effect = Exception("GitHub API error")

        # Act
        with caplog.at_level(logging.DEBUG):
            enrich_github_state(sample_workflow_data, "test-adw-123")

        # Assert - exception caught and logged
        assert "Could not fetch GitHub issue state" in caplog.text


# ============================================================================
# Test enrich_workflow_template() - Workflow Template Defaults
# ============================================================================


class TestEnrichWorkflowTemplate:
    """Tests for enrich_workflow_template() function."""

    def test_sets_default_template(self):
        """Test sets default 'sdlc' template."""
        # Arrange
        workflow_data = {}

        # Act
        enrich_workflow_template(workflow_data)

        # Assert
        assert workflow_data["workflow_template"] == "sdlc"

    def test_does_not_overwrite_existing_template(self):
        """Test does not overwrite existing workflow_template."""
        # Arrange
        workflow_data = {"workflow_template": "custom-template"}

        # Act
        enrich_workflow_template(workflow_data)

        # Assert
        assert workflow_data["workflow_template"] == "custom-template"

    def test_handles_empty_string_template(self):
        """Test overwrites empty string template."""
        # Arrange
        workflow_data = {"workflow_template": ""}

        # Act
        enrich_workflow_template(workflow_data)

        # Assert - empty string is falsy, so it gets overwritten
        assert workflow_data["workflow_template"] == "sdlc"


# ============================================================================
# Test enrich_error_category() - Error Categorization
# ============================================================================


class TestEnrichErrorCategory:
    """Tests for enrich_error_category() function."""

    @patch('core.workflow_history_utils.enrichment.categorize_error')
    def test_categorizes_error_message(self, mock_categorize):
        """Test categorization of error message."""
        # Arrange
        workflow_data = {"error_message": "Connection timeout"}
        mock_categorize.return_value = "network_error"

        # Act
        enrich_error_category(workflow_data)

        # Assert
        assert workflow_data["error_category"] == "network_error"
        mock_categorize.assert_called_once_with("Connection timeout")

    @patch('core.workflow_history_utils.enrichment.categorize_error')
    def test_skips_when_no_error_message(self, mock_categorize):
        """Test skips categorization when no error_message present."""
        # Arrange
        workflow_data = {}

        # Act
        enrich_error_category(workflow_data)

        # Assert
        mock_categorize.assert_not_called()
        assert "error_category" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.categorize_error')
    def test_handles_empty_error_message(self, mock_categorize):
        """Test skips categorization for empty error message."""
        # Arrange
        workflow_data = {"error_message": ""}

        # Act
        enrich_error_category(workflow_data)

        # Assert
        mock_categorize.assert_not_called()

    @patch('core.workflow_history_utils.enrichment.categorize_error')
    def test_handles_various_error_categories(self, mock_categorize):
        """Test handles various error categories."""
        # Arrange
        test_cases = [
            ("Validation failed", "validation_error"),
            ("File not found", "file_error"),
            ("Authentication failed", "auth_error"),
        ]

        for error_msg, expected_category in test_cases:
            workflow_data = {"error_message": error_msg}
            mock_categorize.return_value = expected_category

            # Act
            enrich_error_category(workflow_data)

            # Assert
            assert workflow_data["error_category"] == expected_category


# ============================================================================
# Test enrich_duration() - Duration Calculation
# ============================================================================


class TestEnrichDuration:
    """Tests for enrich_duration() function."""

    @patch('core.workflow_history_utils.enrichment.datetime')
    def test_calculates_duration_for_completed_workflow(self, mock_datetime, sample_workflow_data):
        """Test duration calculation for completed workflow."""
        # Arrange
        start_time = datetime(2025, 1, 15, 10, 30, 0)
        end_time = datetime(2025, 1, 15, 11, 0, 0)  # 30 minutes later
        mock_datetime.fromisoformat.return_value = start_time
        mock_datetime.now.return_value = end_time

        # Act
        duration = enrich_duration(sample_workflow_data, "test-adw-123")

        # Assert
        assert duration == 1800  # 30 minutes in seconds

    def test_returns_none_for_missing_start_time(self):
        """Test returns None when start_time is missing."""
        # Arrange
        workflow_data = {"status": "completed"}

        # Act
        duration = enrich_duration(workflow_data, "test-adw-123")

        # Assert
        assert duration is None

    def test_returns_none_for_non_completed_status(self):
        """Test returns None for non-completed workflows."""
        # Arrange
        workflow_data = {
            "start_time": "2025-01-15T10:30:00Z",
            "status": "running"
        }

        # Act
        duration = enrich_duration(workflow_data, "test-adw-123")

        # Assert
        assert duration is None

    @patch('core.workflow_history_utils.enrichment.datetime')
    def test_handles_iso_format_with_z(self, mock_datetime):
        """Test handles ISO format timestamp with Z suffix."""
        # Arrange
        workflow_data = {
            "start_time": "2025-01-15T10:30:00Z",
            "status": "completed"
        }
        start_time = datetime(2025, 1, 15, 10, 30, 0)
        mock_datetime.fromisoformat.return_value = start_time
        mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 31, 0)

        # Act
        duration = enrich_duration(workflow_data, "test-adw-123")

        # Assert
        assert duration == 60
        # Verify Z was replaced with +00:00
        mock_datetime.fromisoformat.assert_called_once_with("2025-01-15T10:30:00+00:00")

    @patch('core.workflow_history_utils.enrichment.datetime')
    def test_handles_exception_gracefully(self, mock_datetime, sample_workflow_data, caplog):
        """Test exception handling logs debug message."""
        # Arrange
        mock_datetime.fromisoformat.side_effect = ValueError("Invalid date format")

        # Act
        with caplog.at_level(logging.DEBUG):
            duration = enrich_duration(sample_workflow_data, "test-adw-123")

        # Assert
        assert duration is None
        assert "Could not calculate duration" in caplog.text


# ============================================================================
# Test enrich_complexity() - Complexity Estimation
# ============================================================================


class TestEnrichComplexity:
    """Tests for enrich_complexity() function."""

    @patch('core.workflow_history_utils.enrichment.estimate_complexity')
    def test_estimates_complexity_with_steps_and_duration(self, mock_estimate, sample_workflow_data):
        """Test complexity estimation with steps and duration."""
        # Arrange
        mock_estimate.return_value = "medium"

        # Act
        enrich_complexity(sample_workflow_data, duration_seconds=1800)

        # Assert
        assert sample_workflow_data["complexity_actual"] == "medium"
        mock_estimate.assert_called_once_with(10, 1800)

    @patch('core.workflow_history_utils.enrichment.estimate_complexity')
    def test_skips_when_no_steps_total(self, mock_estimate):
        """Test skips complexity estimation when steps_total is missing."""
        # Arrange
        workflow_data = {}

        # Act
        enrich_complexity(workflow_data, duration_seconds=1800)

        # Assert
        mock_estimate.assert_not_called()
        assert "complexity_actual" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.estimate_complexity')
    def test_skips_when_steps_total_is_zero(self, mock_estimate):
        """Test skips complexity estimation when steps_total is zero."""
        # Arrange
        workflow_data = {"steps_total": 0}

        # Act
        enrich_complexity(workflow_data, duration_seconds=1800)

        # Assert
        mock_estimate.assert_not_called()
        assert "complexity_actual" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.estimate_complexity')
    def test_skips_when_no_duration(self, mock_estimate, sample_workflow_data):
        """Test skips complexity estimation when duration is None."""
        # Act
        enrich_complexity(sample_workflow_data, duration_seconds=None)

        # Assert
        mock_estimate.assert_not_called()
        assert "complexity_actual" not in sample_workflow_data

    @patch('core.workflow_history_utils.enrichment.estimate_complexity')
    def test_handles_various_complexity_levels(self, mock_estimate):
        """Test handles various complexity levels."""
        # Arrange
        test_cases = ["low", "medium", "high", "very_high"]

        for complexity in test_cases:
            workflow_data = {"steps_total": 10}
            mock_estimate.return_value = complexity

            # Act
            enrich_complexity(workflow_data, duration_seconds=1800)

            # Assert
            assert workflow_data["complexity_actual"] == complexity


# ============================================================================
# Test enrich_temporal_fields() - Temporal Extraction
# ============================================================================


class TestEnrichTemporalFields:
    """Tests for enrich_temporal_fields() function."""

    @patch('core.workflow_history_utils.enrichment.extract_hour')
    @patch('core.workflow_history_utils.enrichment.extract_day_of_week')
    def test_extracts_temporal_fields(self, mock_day, mock_hour, sample_workflow_data):
        """Test extraction of hour and day of week."""
        # Arrange
        mock_hour.return_value = 10
        mock_day.return_value = "Tuesday"

        # Act
        enrich_temporal_fields(sample_workflow_data)

        # Assert
        assert sample_workflow_data["hour_of_day"] == 10
        assert sample_workflow_data["day_of_week"] == "Tuesday"
        mock_hour.assert_called_once_with("2025-01-15T10:30:00Z")
        mock_day.assert_called_once_with("2025-01-15T10:30:00Z")

    @patch('core.workflow_history_utils.enrichment.extract_hour')
    @patch('core.workflow_history_utils.enrichment.extract_day_of_week')
    def test_skips_when_no_start_time(self, mock_day, mock_hour):
        """Test skips extraction when start_time is missing."""
        # Arrange
        workflow_data = {}

        # Act
        enrich_temporal_fields(workflow_data)

        # Assert
        mock_hour.assert_not_called()
        mock_day.assert_not_called()
        assert "hour_of_day" not in workflow_data
        assert "day_of_week" not in workflow_data

    @patch('core.workflow_history_utils.enrichment.extract_hour')
    @patch('core.workflow_history_utils.enrichment.extract_day_of_week')
    def test_handles_empty_start_time(self, mock_day, mock_hour):
        """Test skips extraction for empty start_time."""
        # Arrange
        workflow_data = {"start_time": ""}

        # Act
        enrich_temporal_fields(workflow_data)

        # Assert
        mock_hour.assert_not_called()
        mock_day.assert_not_called()


# ============================================================================
# Test enrich_scores() - Score Calculations
# ============================================================================


class TestEnrichScores:
    """Tests for enrich_scores() function."""

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_calculates_all_scores(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data
    ):
        """Test calculation of all score metrics."""
        # Arrange
        mock_clarity.return_value = 0.85
        mock_cost_eff.return_value = 0.72
        mock_perf.return_value = 0.90
        mock_quality.return_value = 0.88

        # Act
        enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["scoring_version"] == "1.0"
        assert sample_workflow_data["nl_input_clarity_score"] == 0.85
        assert sample_workflow_data["cost_efficiency_score"] == 0.72
        assert sample_workflow_data["performance_score"] == 0.90
        assert sample_workflow_data["quality_score"] == 0.88

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_handles_clarity_score_exception(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data, caplog
    ):
        """Test handles exception in clarity score calculation."""
        # Arrange
        mock_clarity.side_effect = ValueError("Invalid data")
        mock_cost_eff.return_value = 0.72
        mock_perf.return_value = 0.90
        mock_quality.return_value = 0.88

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["nl_input_clarity_score"] == 0.0
        assert "Failed to calculate clarity score" in caplog.text
        # Other scores still calculated
        assert sample_workflow_data["cost_efficiency_score"] == 0.72

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_handles_cost_efficiency_score_exception(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data, caplog
    ):
        """Test handles exception in cost efficiency score calculation."""
        # Arrange
        mock_clarity.return_value = 0.85
        mock_cost_eff.side_effect = ZeroDivisionError("Division by zero")
        mock_perf.return_value = 0.90
        mock_quality.return_value = 0.88

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["cost_efficiency_score"] == 0.0
        assert "Failed to calculate cost efficiency score" in caplog.text

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_handles_performance_score_exception(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data, caplog
    ):
        """Test handles exception in performance score calculation."""
        # Arrange
        mock_clarity.return_value = 0.85
        mock_cost_eff.return_value = 0.72
        mock_perf.side_effect = KeyError("Missing field")
        mock_quality.return_value = 0.88

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["performance_score"] == 0.0
        assert "Failed to calculate performance score" in caplog.text

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_handles_quality_score_exception(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data, caplog
    ):
        """Test handles exception in quality score calculation."""
        # Arrange
        mock_clarity.return_value = 0.85
        mock_cost_eff.return_value = 0.72
        mock_perf.return_value = 0.90
        mock_quality.side_effect = TypeError("Invalid type")

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert
        assert sample_workflow_data["quality_score"] == 0.0
        assert "Failed to calculate quality score" in caplog.text

    @patch('core.workflow_history_utils.enrichment.calculate_quality_score')
    @patch('core.workflow_history_utils.enrichment.calculate_performance_score')
    @patch('core.workflow_history_utils.enrichment.calculate_cost_efficiency_score')
    @patch('core.workflow_history_utils.enrichment.calculate_nl_input_clarity_score')
    def test_handles_all_scores_exceptions(
        self, mock_clarity, mock_cost_eff, mock_perf, mock_quality, sample_workflow_data, caplog
    ):
        """Test handles exceptions in all score calculations."""
        # Arrange
        mock_clarity.side_effect = Exception("Error 1")
        mock_cost_eff.side_effect = Exception("Error 2")
        mock_perf.side_effect = Exception("Error 3")
        mock_quality.side_effect = Exception("Error 4")

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_scores(sample_workflow_data, "test-adw-123")

        # Assert - all scores default to 0.0
        assert sample_workflow_data["nl_input_clarity_score"] == 0.0
        assert sample_workflow_data["cost_efficiency_score"] == 0.0
        assert sample_workflow_data["performance_score"] == 0.0
        assert sample_workflow_data["quality_score"] == 0.0


# ============================================================================
# Test enrich_insights() - Anomaly Detection and Recommendations
# ============================================================================


class TestEnrichInsights:
    """Tests for enrich_insights() function."""

    @patch('core.workflow_history_utils.enrichment.generate_optimization_recommendations')
    @patch('core.workflow_history_utils.enrichment.detect_anomalies')
    def test_generates_insights(self, mock_detect, mock_recommend, sample_workflow_data):
        """Test generation of anomalies and recommendations."""
        # Arrange
        mock_detect.return_value = [
            {"type": "high_cost", "message": "Cost is 50% above average"},
            {"type": "slow_phase", "message": "Build phase took 2x longer"}
        ]
        mock_recommend.return_value = [
            {"type": "caching", "message": "Enable caching to reduce cost"},
            {"type": "optimization", "message": "Optimize build process"}
        ]
        all_workflows = [sample_workflow_data]

        # Act
        enrich_insights(sample_workflow_data, "test-adw-123", all_workflows)

        # Assert
        anomalies = json.loads(sample_workflow_data["anomaly_flags"])
        recommendations = json.loads(sample_workflow_data["optimization_recommendations"])
        assert len(anomalies) == 2
        assert "Cost is 50% above average" in anomalies
        assert len(recommendations) == 2
        assert recommendations[0]["type"] == "caching"

    @patch('core.workflow_history_utils.enrichment.generate_optimization_recommendations')
    @patch('core.workflow_history_utils.enrichment.detect_anomalies')
    def test_handles_empty_insights(self, mock_detect, mock_recommend, sample_workflow_data):
        """Test handling of empty anomalies and recommendations."""
        # Arrange
        mock_detect.return_value = []
        mock_recommend.return_value = []
        all_workflows = []

        # Act
        enrich_insights(sample_workflow_data, "test-adw-123", all_workflows)

        # Assert
        anomalies = json.loads(sample_workflow_data["anomaly_flags"])
        recommendations = json.loads(sample_workflow_data["optimization_recommendations"])
        assert anomalies == []
        assert recommendations == []

    @patch('core.workflow_history_utils.enrichment.generate_optimization_recommendations')
    @patch('core.workflow_history_utils.enrichment.detect_anomalies')
    def test_serializes_insights_to_json(self, mock_detect, mock_recommend, sample_workflow_data):
        """Test insights are serialized to JSON strings."""
        # Arrange
        mock_detect.return_value = [{"type": "test", "message": "Test anomaly"}]
        mock_recommend.return_value = [{"type": "test", "message": "Test recommendation"}]

        # Act
        enrich_insights(sample_workflow_data, "test-adw-123", [])

        # Assert
        assert isinstance(sample_workflow_data["anomaly_flags"], str)
        assert isinstance(sample_workflow_data["optimization_recommendations"], str)
        # Can parse back to list
        assert isinstance(json.loads(sample_workflow_data["anomaly_flags"]), list)
        assert isinstance(json.loads(sample_workflow_data["optimization_recommendations"]), list)

    @patch('core.workflow_history_utils.enrichment.generate_optimization_recommendations')
    @patch('core.workflow_history_utils.enrichment.detect_anomalies')
    def test_handles_exception_gracefully(self, mock_detect, mock_recommend, sample_workflow_data, caplog):
        """Test exception handling logs warning and sets empty insights."""
        # Arrange
        mock_detect.side_effect = Exception("Analysis error")

        # Act
        with caplog.at_level(logging.WARNING):
            enrich_insights(sample_workflow_data, "test-adw-123", [])

        # Assert
        assert sample_workflow_data["anomaly_flags"] == "[]"
        assert sample_workflow_data["optimization_recommendations"] == "[]"
        assert "Failed to generate insights" in caplog.text


# ============================================================================
# Test enrich_cost_data_for_resync() - Resync Cost Data
# ============================================================================


class TestEnrichCostDataForResync:
    """Tests for enrich_cost_data_for_resync() function."""

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_returns_update_dict_with_cost_data(
        self, mock_calc_metrics, mock_read_cost, sample_cost_data, mock_phase_metrics
    ):
        """Test returns update dictionary with cost data."""
        # Arrange
        existing = {"estimated_cost_total": 2.0}
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = mock_phase_metrics

        # Act
        updates = enrich_cost_data_for_resync(existing, "test-adw-123")

        # Assert
        assert updates["actual_cost_total"] == 1.25
        assert updates["input_tokens"] == 3000
        assert updates["total_tokens"] == 5050
        assert "cost_breakdown" in updates
        assert updates["cost_breakdown"]["actual_total"] == 1.25

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    @patch('core.workflow_history_utils.enrichment.calculate_phase_metrics')
    def test_includes_phase_metrics_in_updates(
        self, mock_calc_metrics, mock_read_cost, sample_cost_data, mock_phase_metrics
    ):
        """Test phase metrics are included in update dict."""
        # Arrange
        existing = {}
        mock_read_cost.return_value = sample_cost_data
        mock_calc_metrics.return_value = mock_phase_metrics

        # Act
        updates = enrich_cost_data_for_resync(existing, "test-adw-123")

        # Assert
        assert updates["phase_durations"] == mock_phase_metrics["phase_durations"]
        assert updates["bottleneck_phase"] == "build"
        assert updates["idle_time_seconds"] == 5.3

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_returns_empty_dict_when_no_cost_data(self, mock_read_cost):
        """Test returns empty dict when cost data is not available."""
        # Arrange
        existing = {}
        mock_read_cost.return_value = None

        # Act
        updates = enrich_cost_data_for_resync(existing, "test-adw-123")

        # Assert
        assert updates == {}

    @patch('core.workflow_history_utils.enrichment.read_cost_history')
    def test_uses_existing_values_in_breakdown(self, mock_read_cost, sample_cost_data):
        """Test uses existing workflow values in cost breakdown."""
        # Arrange
        existing = {
            "estimated_cost_total": 2.50,
            "estimated_cost_per_step": 0.25,
            "actual_cost_per_step": 0.15,
            "cost_per_token": 0.0001
        }
        mock_read_cost.return_value = sample_cost_data

        # Act
        updates = enrich_cost_data_for_resync(existing, "test-adw-123")

        # Assert
        breakdown = updates["cost_breakdown"]
        assert breakdown["estimated_total"] == 2.50
        assert breakdown["estimated_per_step"] == 0.25
        assert breakdown["actual_per_step"] == 0.15
        assert breakdown["cost_per_token"] == 0.0001


# ============================================================================
# Test enrich_workflow() - Main Orchestrator
# ============================================================================


class TestEnrichWorkflow:
    """Tests for enrich_workflow() main orchestrator function."""

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_calls_all_enrichment_functions_for_new_workflow(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test calls all enrichment functions for new workflow."""
        # Arrange
        mock_duration.return_value = 1800
        all_workflows = [sample_workflow_data]

        # Act
        duration = enrich_workflow(sample_workflow_data, "test-adw-123", is_new=True, all_workflows=all_workflows)

        # Assert - all functions called
        mock_cost_data.assert_called_once_with(sample_workflow_data, "test-adw-123")
        mock_cost_estimate.assert_called_once_with(sample_workflow_data, "test-adw-123")
        mock_github.assert_called_once_with(sample_workflow_data, "test-adw-123")
        mock_template.assert_called_once_with(sample_workflow_data)
        mock_error.assert_called_once_with(sample_workflow_data)
        mock_duration.assert_called_once_with(sample_workflow_data, "test-adw-123")
        mock_complexity.assert_called_once_with(sample_workflow_data, 1800)
        mock_temporal.assert_called_once_with(sample_workflow_data)
        mock_scores.assert_called_once_with(sample_workflow_data, "test-adw-123")
        mock_insights.assert_called_once_with(sample_workflow_data, "test-adw-123", all_workflows)
        assert duration == 1800

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_skips_cost_estimate_for_existing_workflow(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test skips cost estimate enrichment for existing workflows."""
        # Arrange
        mock_duration.return_value = 1800

        # Act
        enrich_workflow(sample_workflow_data, "test-adw-123", is_new=False)

        # Assert - cost estimate not called for existing workflow
        mock_cost_estimate.assert_not_called()
        # Other functions still called
        mock_cost_data.assert_called_once()
        mock_github.assert_called_once()

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_skips_insights_for_existing_workflow(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test skips insights generation for existing workflows."""
        # Arrange
        mock_duration.return_value = 1800
        all_workflows = [sample_workflow_data]

        # Act
        enrich_workflow(sample_workflow_data, "test-adw-123", is_new=False, all_workflows=all_workflows)

        # Assert - insights not called for existing workflow
        mock_insights.assert_not_called()

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_skips_insights_when_no_workflows_provided(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test skips insights when all_workflows is None."""
        # Arrange
        mock_duration.return_value = 1800

        # Act
        enrich_workflow(sample_workflow_data, "test-adw-123", is_new=True, all_workflows=None)

        # Assert - insights not called when all_workflows is None
        mock_insights.assert_not_called()

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_passes_duration_to_complexity(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test duration is passed to complexity estimation."""
        # Arrange
        mock_duration.return_value = 2400

        # Act
        enrich_workflow(sample_workflow_data, "test-adw-123", is_new=False)

        # Assert - complexity called with duration from enrich_duration
        mock_complexity.assert_called_once_with(sample_workflow_data, 2400)

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_handles_none_duration(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test handles None duration from enrich_duration."""
        # Arrange
        mock_duration.return_value = None

        # Act
        duration = enrich_workflow(sample_workflow_data, "test-adw-123", is_new=False)

        # Assert - complexity still called with None
        mock_complexity.assert_called_once_with(sample_workflow_data, None)
        assert duration is None

    @patch('core.workflow_history_utils.enrichment.enrich_insights')
    @patch('core.workflow_history_utils.enrichment.enrich_scores')
    @patch('core.workflow_history_utils.enrichment.enrich_temporal_fields')
    @patch('core.workflow_history_utils.enrichment.enrich_complexity')
    @patch('core.workflow_history_utils.enrichment.enrich_duration')
    @patch('core.workflow_history_utils.enrichment.enrich_error_category')
    @patch('core.workflow_history_utils.enrichment.enrich_workflow_template')
    @patch('core.workflow_history_utils.enrichment.enrich_github_state')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_estimate')
    @patch('core.workflow_history_utils.enrichment.enrich_cost_data')
    def test_enrichment_order_is_correct(
        self, mock_cost_data, mock_cost_estimate, mock_github, mock_template,
        mock_error, mock_duration, mock_complexity, mock_temporal, mock_scores,
        mock_insights, sample_workflow_data
    ):
        """Test enrichment functions are called in correct order."""
        # Arrange
        mock_duration.return_value = 1800
        call_order = []

        mock_cost_data.side_effect = lambda *args: call_order.append("cost_data")
        mock_cost_estimate.side_effect = lambda *args: call_order.append("cost_estimate")
        mock_github.side_effect = lambda *args: call_order.append("github")
        mock_template.side_effect = lambda *args: call_order.append("template")
        mock_error.side_effect = lambda *args: call_order.append("error")
        mock_duration.side_effect = lambda *args: (call_order.append("duration"), 1800)[1]
        mock_complexity.side_effect = lambda *args: call_order.append("complexity")
        mock_temporal.side_effect = lambda *args: call_order.append("temporal")
        mock_scores.side_effect = lambda *args: call_order.append("scores")
        mock_insights.side_effect = lambda *args: call_order.append("insights")

        # Act
        enrich_workflow(sample_workflow_data, "test-adw-123", is_new=True, all_workflows=[])

        # Assert - correct order
        expected_order = [
            "cost_data", "cost_estimate", "github", "template", "error",
            "duration", "complexity", "temporal", "scores", "insights"
        ]
        assert call_order == expected_order
