"""
Unit tests for workflow_history.metrics module.

Tests metric calculation functions.
"""

from core.workflow_history_utils.metrics import (
    calculate_phase_metrics,
    categorize_error,
    estimate_complexity,
)
from core.data_models import CostData, PhaseCost, TokenBreakdown


class TestCalculatePhaseMetrics:
    """Tests for calculate_phase_metrics function."""

    def test_empty_cost_data(self):
        """Test with None or empty cost data."""
        result = calculate_phase_metrics(None)
        assert result["phase_durations"] is None
        assert result["bottleneck_phase"] is None
        assert result["idle_time_seconds"] is None

    def test_cost_data_without_phases(self):
        """Test with cost data that has no phases."""
        cost_data = CostData(
            adw_id="test-123",
            total_cost=1.0,
            cache_efficiency_percent=50.0,
            cache_savings_amount=0.5,
            total_tokens=1000,
            phases=[]
        )
        result = calculate_phase_metrics(cost_data)
        assert result["phase_durations"] is None
        assert result["bottleneck_phase"] is None
        assert result["idle_time_seconds"] is None

    def test_single_phase_with_timestamp(self):
        """Test with single phase - should return None (need at least 2 phases)."""
        phase = PhaseCost(
            phase="plan",
            cost=0.5,
            tokens=TokenBreakdown(
                input_tokens=100,
                output_tokens=50,
                cache_creation_tokens=10,
                cache_read_tokens=5
            ),
            timestamp="2024-01-01T10:00:00Z"
        )
        cost_data = CostData(
            adw_id="test-123",
            total_cost=0.5,
            cache_efficiency_percent=0.0,
            cache_savings_amount=0.0,
            total_tokens=165,
            phases=[phase]
        )
        result = calculate_phase_metrics(cost_data)
        assert result["phase_durations"] is None
        assert result["bottleneck_phase"] is None
        assert result["idle_time_seconds"] is None

    def test_two_phases_with_timestamps(self):
        """Test with two phases - should calculate duration."""
        phases = [
            PhaseCost(
                phase="plan",
                cost=0.3,
                tokens=TokenBreakdown(
                    input_tokens=100,
                    output_tokens=50,
                    cache_creation_tokens=10,
                    cache_read_tokens=5
                ),
                timestamp="2024-01-01T10:00:00Z"
            ),
            PhaseCost(
                phase="build",
                cost=0.7,
                tokens=TokenBreakdown(
                    input_tokens=200,
                    output_tokens=100,
                    cache_creation_tokens=20,
                    cache_read_tokens=10
                ),
                timestamp="2024-01-01T10:05:00Z"
            ),
        ]
        cost_data = CostData(
            adw_id="test-123",
            total_cost=1.0,
            cache_efficiency_percent=0.0,
            cache_savings_amount=0.0,
            total_tokens=495,
            phases=phases
        )
        result = calculate_phase_metrics(cost_data)
        assert result["phase_durations"] is not None
        assert result["phase_durations"]["plan"] == 300  # 5 minutes
        assert result["bottleneck_phase"] == "plan"  # 100% of time
        assert result["idle_time_seconds"] == 0

    def test_multiple_phases_with_bottleneck(self):
        """Test with multiple phases where one is a bottleneck (>30% of time)."""
        phases = [
            PhaseCost(
                phase="plan",
                cost=0.1,
                tokens=TokenBreakdown(
                    input_tokens=100,
                    output_tokens=50,
                    cache_creation_tokens=10,
                    cache_read_tokens=5
                ),
                timestamp="2024-01-01T10:00:00Z"
            ),
            PhaseCost(
                phase="build",
                cost=0.5,
                tokens=TokenBreakdown(
                    input_tokens=500,
                    output_tokens=250,
                    cache_creation_tokens=50,
                    cache_read_tokens=25
                ),
                timestamp="2024-01-01T10:01:00Z"  # 1 minute after plan
            ),
            PhaseCost(
                phase="test",
                cost=0.4,
                tokens=TokenBreakdown(
                    input_tokens=400,
                    output_tokens=200,
                    cache_creation_tokens=40,
                    cache_read_tokens=20
                ),
                timestamp="2024-01-01T10:06:00Z"  # 5 minutes after build
            ),
        ]
        cost_data = CostData(
            adw_id="test-123",
            total_cost=1.0,
            cache_efficiency_percent=0.0,
            cache_savings_amount=0.0,
            total_tokens=1650,
            phases=phases
        )
        result = calculate_phase_metrics(cost_data)
        assert result["phase_durations"] is not None
        assert result["phase_durations"]["plan"] == 60  # 1 minute
        assert result["phase_durations"]["build"] == 300  # 5 minutes
        # build is 300s out of 360s total = 83% (>30% threshold)
        assert result["bottleneck_phase"] == "build"
        assert result["idle_time_seconds"] == 0

    def test_phases_without_timestamps(self):
        """Test with phases that have no timestamps."""
        phases = [
            PhaseCost(
                phase="plan",
                cost=0.5,
                tokens=TokenBreakdown(
                    input_tokens=100,
                    output_tokens=50,
                    cache_creation_tokens=10,
                    cache_read_tokens=5
                ),
                timestamp=None
            ),
            PhaseCost(
                phase="build",
                cost=0.5,
                tokens=TokenBreakdown(
                    input_tokens=100,
                    output_tokens=50,
                    cache_creation_tokens=10,
                    cache_read_tokens=5
                ),
                timestamp=None
            ),
        ]
        cost_data = CostData(
            adw_id="test-123",
            total_cost=1.0,
            cache_efficiency_percent=0.0,
            cache_savings_amount=0.0,
            total_tokens=330,
            phases=phases
        )
        result = calculate_phase_metrics(cost_data)
        assert result["phase_durations"] is None
        assert result["bottleneck_phase"] is None
        assert result["idle_time_seconds"] is None


class TestCategorizeError:
    """Tests for categorize_error function."""

    def test_empty_error_message(self):
        """Test with empty or None error message."""
        assert categorize_error("") == "unknown"
        assert categorize_error(None) == "unknown"

    def test_syntax_errors(self):
        """Test syntax error detection."""
        assert categorize_error("SyntaxError: invalid syntax") == "syntax_error"
        assert categorize_error("IndentationError: unexpected indent") == "syntax_error"
        assert categorize_error("Parse error at line 42") == "syntax_error"
        assert categorize_error("Invalid syntax in file.py") == "syntax_error"

    def test_timeout_errors(self):
        """Test timeout error detection."""
        assert categorize_error("TimeoutError: operation timed out") == "timeout"
        assert categorize_error("Connection timeout after 30s") == "timeout"
        assert categorize_error("Request timed out") == "timeout"
        assert categorize_error("Deadline exceeded") == "timeout"

    def test_api_quota_errors(self):
        """Test API quota/rate limit error detection."""
        assert categorize_error("API quota exceeded") == "api_quota"
        assert categorize_error("Rate limit error: too many requests") == "api_quota"
        assert categorize_error("HTTP 429: Too Many Requests") == "api_quota"
        assert categorize_error("Rate_limit_error in API call") == "api_quota"

    def test_validation_errors(self):
        """Test validation error detection."""
        assert categorize_error("ValidationError: invalid input") == "validation"
        assert categorize_error("Schema validation failed") == "validation"
        assert categorize_error("Invalid data format") == "validation"
        assert categorize_error("Schema error in config") == "validation"

    def test_unknown_errors(self):
        """Test unknown/uncategorized errors."""
        assert categorize_error("Something went wrong") == "unknown"
        assert categorize_error("Unexpected error occurred") == "unknown"
        assert categorize_error("File not found") == "unknown"

    def test_case_insensitivity(self):
        """Test that categorization is case-insensitive."""
        assert categorize_error("SYNTAXERROR: INVALID SYNTAX") == "syntax_error"
        assert categorize_error("timeout ERROR") == "timeout"
        assert categorize_error("QUOTA EXCEEDED") == "api_quota"


class TestEstimateComplexity:
    """Tests for estimate_complexity function."""

    def test_low_complexity_by_steps(self):
        """Test low complexity determined by few steps."""
        assert estimate_complexity(steps_total=3, duration_seconds=300) == "low"
        assert estimate_complexity(steps_total=5, duration_seconds=500) == "low"

    def test_low_complexity_by_duration(self):
        """Test low complexity determined by short duration."""
        assert estimate_complexity(steps_total=10, duration_seconds=30) == "low"
        assert estimate_complexity(steps_total=20, duration_seconds=59) == "low"

    def test_high_complexity_by_steps(self):
        """Test high complexity determined by many steps."""
        assert estimate_complexity(steps_total=16, duration_seconds=100) == "high"
        assert estimate_complexity(steps_total=20, duration_seconds=200) == "high"

    def test_high_complexity_by_duration(self):
        """Test high complexity determined by long duration."""
        assert estimate_complexity(steps_total=10, duration_seconds=301) == "high"
        assert estimate_complexity(steps_total=8, duration_seconds=500) == "high"

    def test_medium_complexity(self):
        """Test medium complexity for intermediate values."""
        assert estimate_complexity(steps_total=8, duration_seconds=150) == "medium"
        assert estimate_complexity(steps_total=10, duration_seconds=200) == "medium"
        assert estimate_complexity(steps_total=12, duration_seconds=250) == "medium"

    def test_boundary_values(self):
        """Test boundary values for complexity thresholds."""
        # Low boundary (5 steps, 60 seconds)
        assert estimate_complexity(steps_total=5, duration_seconds=300) == "low"
        assert estimate_complexity(steps_total=6, duration_seconds=60) == "medium"
        assert estimate_complexity(steps_total=10, duration_seconds=60) == "medium"

        # High boundary (15 steps, 300 seconds)
        assert estimate_complexity(steps_total=15, duration_seconds=100) == "medium"
        assert estimate_complexity(steps_total=16, duration_seconds=100) == "high"
        assert estimate_complexity(steps_total=10, duration_seconds=300) == "medium"
        assert estimate_complexity(steps_total=10, duration_seconds=301) == "high"
