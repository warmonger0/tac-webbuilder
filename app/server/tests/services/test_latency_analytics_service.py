"""
Tests for Latency Analytics Service

Tests latency analysis by phase, bottleneck detection, trends, and optimization recommendations.

Run with:
    cd app/server
    pytest tests/services/test_latency_analytics_service.py -v
    pytest tests/services/test_latency_analytics_service.py -v -k "test_get_latency_summary"
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from services.latency_analytics_service import LatencyAnalyticsService


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "%s"  # PostgreSQL placeholder
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create LatencyAnalyticsService with mocked adapter."""
    with patch(
        "services.latency_analytics_service.get_database_adapter",
        return_value=mock_adapter,
    ):
        return LatencyAnalyticsService()


@pytest.fixture
def sample_workflows():
    """Sample workflow data with duration and phase_durations."""
    return [
        {
            'duration_seconds': 420,
            'phase_durations': {
                'Plan': 30,
                'Validate': 20,
                'Build': 120,
                'Lint': 15,
                'Test': 180,
                'Review': 35,
                'Document': 15,
                'Ship': 5
            }
        },
        {
            'duration_seconds': 380,
            'phase_durations': {
                'Plan': 25,
                'Validate': 18,
                'Build': 110,
                'Lint': 12,
                'Test': 165,
                'Review': 30,
                'Document': 12,
                'Ship': 4
            }
        },
        {
            'duration_seconds': 510,
            'phase_durations': {
                'Plan': 35,
                'Validate': 25,
                'Build': 140,
                'Lint': 18,
                'Test': 210,
                'Review': 45,
                'Document': 20,
                'Ship': 7
            }
        }
    ]


class TestGetLatencySummary:
    """Test overall latency summary statistics."""

    def test_get_latency_summary_success(self, service, sample_workflows):
        """Test successful latency summary calculation."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.get_latency_summary(days=30)

        # Assert
        assert result.total_workflows == 3
        assert result.average_duration_seconds == pytest.approx(436.67, rel=0.01)
        assert result.p50_duration == 420  # Median of [380, 420, 510]
        assert result.slowest_phase == 'Test'  # Test has highest average
        assert result.slowest_phase_avg > 0

    def test_get_latency_summary_empty_data(self, service):
        """Test summary with no completed workflows."""
        # Setup mock to return empty
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.get_latency_summary(days=30)

        # Assert
        assert result.total_workflows == 0
        assert result.average_duration_seconds == 0.0
        assert result.p50_duration == 0.0

    def test_get_latency_summary_json_parsing(self, service):
        """Test parsing of JSON phase_durations field."""
        workflows = [
            {
                'duration_seconds': 420,
                'phase_durations': json.dumps({'Plan': 30, 'Test': 180})
            }
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.get_latency_summary(days=30)

        # Assert
        assert result.total_workflows == 1
        assert result.slowest_phase in ['Plan', 'Test']


class TestAnalyzeByPhase:
    """Test phase latency breakdown."""

    def test_analyze_by_phase_success(self, service, sample_workflows):
        """Test successful phase latency analysis."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert
        assert len(result.phase_latencies) > 0
        assert 'Test' in result.phase_latencies
        assert 'Build' in result.phase_latencies

        # Check Test phase stats (highest latency)
        test_stats = result.phase_latencies['Test']
        assert test_stats.sample_count == 3
        assert test_stats.average == pytest.approx(185.0, rel=0.01)  # (180+165+210)/3
        assert test_stats.min == 165
        assert test_stats.max == 210

    def test_analyze_by_phase_percentiles(self, service, sample_workflows):
        """Test percentile calculations in phase analysis."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert - Test phase should have valid percentiles
        test_stats = result.phase_latencies['Test']
        assert test_stats.p50 > 0  # Median
        assert test_stats.p95 >= test_stats.p50  # p95 >= median
        assert test_stats.p99 >= test_stats.p95  # p99 >= p95

    def test_analyze_by_phase_empty_data(self, service):
        """Test phase analysis with no workflows."""
        # Setup mock to return empty
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert
        assert len(result.phase_latencies) == 0
        assert result.total_duration_avg == 0.0


class TestFindBottlenecks:
    """Test bottleneck detection."""

    def test_find_bottlenecks_detected(self, service, sample_workflows):
        """Test bottleneck detection when phases exceed threshold."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute with low threshold (50s) to trigger bottlenecks
            bottlenecks = service.find_bottlenecks(threshold_seconds=50, days=30)

        # Assert - Test and Build should be bottlenecks (both > 50s)
        assert len(bottlenecks) > 0
        bottleneck_phases = [b.phase for b in bottlenecks]
        assert 'Test' in bottleneck_phases or 'Build' in bottleneck_phases

        # Check bottleneck structure
        if bottlenecks:
            first_bottleneck = bottlenecks[0]
            assert first_bottleneck.p95_latency > 50
            assert first_bottleneck.threshold == 50.0
            assert first_bottleneck.recommendation is not None
            assert first_bottleneck.estimated_speedup is not None

    def test_find_bottlenecks_none_detected(self, service, sample_workflows):
        """Test bottleneck detection when no phases exceed threshold."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute with high threshold (1000s) - no bottlenecks expected
            bottlenecks = service.find_bottlenecks(threshold_seconds=1000, days=30)

        # Assert
        assert len(bottlenecks) == 0

    def test_find_bottlenecks_sorted_by_severity(self, service, sample_workflows):
        """Test that bottlenecks are sorted by p95 latency (highest first)."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute with threshold that captures multiple bottlenecks
            bottlenecks = service.find_bottlenecks(threshold_seconds=50, days=30)

        # Assert - bottlenecks should be sorted by p95 (descending)
        if len(bottlenecks) > 1:
            for i in range(len(bottlenecks) - 1):
                assert bottlenecks[i].p95_latency >= bottlenecks[i + 1].p95_latency


class TestCalculatePercentiles:
    """Test percentile calculation."""

    def test_calculate_percentiles_basic(self, service):
        """Test basic percentile calculations."""
        durations = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

        result = service.calculate_percentiles(durations)

        assert result['p50'] == pytest.approx(550, abs=50)  # Median
        assert result['p95'] == pytest.approx(950, abs=50)  # 95th percentile
        assert result['p99'] == pytest.approx(990, abs=50)  # 99th percentile
        assert result['average'] == 550  # Mean
        assert result['min'] == 100
        assert result['max'] == 1000
        assert result['std_dev'] > 0

    def test_calculate_percentiles_single_value(self, service):
        """Test percentiles with single value."""
        durations = [500]

        result = service.calculate_percentiles(durations)

        assert result['p50'] == 500
        assert result['p95'] == 500
        assert result['p99'] == 500
        assert result['average'] == 500
        assert result['std_dev'] == 0.0

    def test_calculate_percentiles_empty(self, service):
        """Test percentiles with empty list."""
        durations = []

        result = service.calculate_percentiles(durations)

        assert result['p50'] == 0.0
        assert result['p95'] == 0.0
        assert result['p99'] == 0.0
        assert result['average'] == 0.0


class TestDetectOutliers:
    """Test outlier detection."""

    def test_detect_outliers_found(self, service):
        """Test outlier detection with outliers present."""
        # Normal values around 500, with outliers at 5000 and 10000
        durations = [450, 480, 490, 500, 510, 520, 530, 5000, 10000]

        outliers = service.detect_outliers(durations, threshold_std=2.0)

        # Assert - should detect 2 outliers (5000 and 10000)
        assert len(outliers) > 0

    def test_detect_outliers_none_found(self, service):
        """Test outlier detection with no outliers."""
        # All values close together
        durations = [450, 480, 490, 500, 510, 520, 530]

        outliers = service.detect_outliers(durations, threshold_std=2.0)

        # Assert - should find no outliers
        assert len(outliers) == 0

    def test_detect_outliers_insufficient_data(self, service):
        """Test outlier detection with too few data points."""
        durations = [100, 200]  # < 3 data points

        outliers = service.detect_outliers(durations, threshold_std=2.0)

        # Assert - should return empty list
        assert len(outliers) == 0


class TestGetLatencyTrends:
    """Test latency trends over time."""

    def test_get_latency_trends_success(self, service):
        """Test successful trend analysis."""
        # Setup mock with daily data
        daily_data = [
            {'date': '2025-11-01', 'avg_duration': 400.0, 'workflow_count': 5},
            {'date': '2025-11-02', 'avg_duration': 420.0, 'workflow_count': 6},
            {'date': '2025-11-03', 'avg_duration': 410.0, 'workflow_count': 4},
            {'date': '2025-11-04', 'avg_duration': 430.0, 'workflow_count': 7},
            {'date': '2025-11-05', 'avg_duration': 440.0, 'workflow_count': 5},
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = daily_data
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.get_latency_trends(days=30)

        # Assert
        assert len(result.daily_latencies) == 5
        assert result.trend_direction in ['increasing', 'decreasing', 'stable']
        assert isinstance(result.percentage_change, float)
        assert result.average_daily_duration > 0

    def test_get_latency_trends_increasing(self, service):
        """Test trend detection for increasing latency."""
        # Setup mock with clear increasing trend (need 14+ days for week-over-week comparison)
        daily_data = []
        # First 7 days: around 300s
        for i in range(7):
            daily_data.append({'date': f'2025-11-{i+1:02d}', 'avg_duration': 300.0 + i * 5, 'workflow_count': 5})
        # Last 7 days: around 500s (much higher)
        for i in range(7):
            daily_data.append({'date': f'2025-11-{i+8:02d}', 'avg_duration': 500.0 + i * 5, 'workflow_count': 5})

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = daily_data
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.get_latency_trends(days=14)

        # Assert - should detect increasing trend
        assert result.trend_direction == 'increasing'
        assert result.percentage_change > 5  # More than 5% increase


class TestGetOptimizationRecommendations:
    """Test optimization recommendations."""

    def test_get_optimization_recommendations_success(self, service, sample_workflows):
        """Test successful recommendation generation."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            recommendations = service.get_optimization_recommendations(days=30)

        # Assert
        # Should generate recommendations for slowest phases (Test, Build)
        if recommendations:
            rec = recommendations[0]
            assert rec.target is not None
            assert rec.current_latency > 0
            assert rec.target_latency > 0
            assert rec.improvement_percentage > 0
            assert len(rec.actions) > 0

    def test_get_optimization_recommendations_empty_data(self, service):
        """Test recommendations with no data."""
        # Setup mock to return empty
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.latency_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            recommendations = service.get_optimization_recommendations(days=30)

        # Assert
        assert len(recommendations) == 0
