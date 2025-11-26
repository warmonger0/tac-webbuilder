"""
Unit tests for workflow_history.models module.

Tests type definitions, enums, and dataclasses.
"""

from core.workflow_history_utils.models import (
    BOTTLENECK_THRESHOLD,
    DEFAULT_SCORING_VERSION,
    ComplexityLevel,
    ErrorCategory,
    WorkflowFilter,
    WorkflowStatus,
)


class TestWorkflowStatus:
    """Tests for WorkflowStatus enum."""

    def test_all_statuses_defined(self):
        """Verify all expected workflow statuses are defined."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

    def test_status_count(self):
        """Verify we have exactly 4 workflow statuses."""
        assert len(WorkflowStatus) == 4


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_defined(self):
        """Verify all expected error categories are defined."""
        assert ErrorCategory.SYNTAX_ERROR.value == "syntax_error"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.API_QUOTA.value == "api_quota"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.UNKNOWN.value == "unknown"

    def test_category_count(self):
        """Verify we have exactly 5 error categories."""
        assert len(ErrorCategory) == 5


class TestComplexityLevel:
    """Tests for ComplexityLevel enum."""

    def test_all_levels_defined(self):
        """Verify all expected complexity levels are defined."""
        assert ComplexityLevel.LOW.value == "low"
        assert ComplexityLevel.MEDIUM.value == "medium"
        assert ComplexityLevel.HIGH.value == "high"

    def test_level_count(self):
        """Verify we have exactly 3 complexity levels."""
        assert len(ComplexityLevel) == 3


class TestWorkflowFilter:
    """Tests for WorkflowFilter dataclass."""

    def test_default_values(self):
        """Verify all fields default to None."""
        filter_obj = WorkflowFilter()
        assert filter_obj.issue_number is None
        assert filter_obj.status is None
        assert filter_obj.start_date is None
        assert filter_obj.end_date is None
        assert filter_obj.model is None
        assert filter_obj.template is None
        assert filter_obj.search is None

    def test_partial_initialization(self):
        """Verify partial initialization works correctly."""
        filter_obj = WorkflowFilter(
            issue_number=123,
            status=WorkflowStatus.COMPLETED
        )
        assert filter_obj.issue_number == 123
        assert filter_obj.status == WorkflowStatus.COMPLETED
        assert filter_obj.start_date is None

    def test_full_initialization(self):
        """Verify full initialization works correctly."""
        filter_obj = WorkflowFilter(
            issue_number=456,
            status=WorkflowStatus.RUNNING,
            start_date="2024-01-01",
            end_date="2024-01-31",
            model="claude-sonnet-4-5",
            template="sdlc",
            search="test query"
        )
        assert filter_obj.issue_number == 456
        assert filter_obj.status == WorkflowStatus.RUNNING
        assert filter_obj.start_date == "2024-01-01"
        assert filter_obj.end_date == "2024-01-31"
        assert filter_obj.model == "claude-sonnet-4-5"
        assert filter_obj.template == "sdlc"
        assert filter_obj.search == "test query"


class TestConstants:
    """Tests for module constants."""

    def test_default_scoring_version(self):
        """Verify default scoring version is set correctly."""
        assert DEFAULT_SCORING_VERSION == "1.0"

    def test_bottleneck_threshold(self):
        """Verify bottleneck threshold is 30%."""
        assert BOTTLENECK_THRESHOLD == 0.30

    def test_complexity_thresholds(self):
        """Verify complexity threshold constants."""
        from core.workflow_history_utils.models import (
            HIGH_COMPLEXITY_DURATION,
            HIGH_COMPLEXITY_STEPS,
            LOW_COMPLEXITY_DURATION,
            LOW_COMPLEXITY_STEPS,
        )
        assert LOW_COMPLEXITY_STEPS == 5
        assert LOW_COMPLEXITY_DURATION == 60
        assert HIGH_COMPLEXITY_STEPS == 15
        assert HIGH_COMPLEXITY_DURATION == 300
