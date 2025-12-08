"""
Tests for Cost Analytics Service

Tests cost analysis by phase, workflow type, trends, and optimization detection.

Run with:
    cd app/server
    pytest tests/services/test_cost_analytics_service.py -v
    pytest tests/services/test_cost_analytics_service.py -v -k "test_analyze_by_phase"
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from services.cost_analytics_service import CostAnalyticsService


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "%s"  # PostgreSQL placeholder
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create CostAnalyticsService with mocked adapter."""
    with patch(
        "services.cost_analytics_service.get_database_adapter",
        return_value=mock_adapter,
    ):
        return CostAnalyticsService()


@pytest.fixture
def sample_workflows():
    """Sample workflow data with cost breakdowns."""
    return [
        {
            'cost_breakdown': {
                'by_phase': {
                    'Plan': 2.0,
                    'Validate': 1.5,
                    'Build': 8.0,
                    'Lint': 1.0,
                    'Test': 5.5,
                    'Review': 2.5,
                    'Document': 1.5,
                    'Ship': 1.0,
                    'Cleanup': 0.5
                }
            },
            'actual_cost_total': 23.5
        },
        {
            'cost_breakdown': {
                'by_phase': {
                    'Plan': 1.8,
                    'Validate': 1.2,
                    'Build': 7.5,
                    'Lint': 0.9,
                    'Test': 5.0,
                    'Review': 2.2,
                    'Document': 1.3,
                    'Ship': 0.9,
                    'Cleanup': 0.4
                }
            },
            'actual_cost_total': 21.2
        },
        {
            'cost_breakdown': {
                'by_phase': {
                    'Plan': 2.2,
                    'Validate': 1.6,
                    'Build': 9.0,
                    'Lint': 1.1,
                    'Test': 6.0,
                    'Review': 2.8,
                    'Document': 1.7,
                    'Ship': 1.1,
                    'Cleanup': 0.6
                }
            },
            'actual_cost_total': 26.1
        }
    ]


class TestAnalyzeByPhase:
    """Test phase cost analysis."""

    def test_analyze_by_phase_success(self, service, sample_workflows):
        """Test successful phase cost analysis."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Return sample workflows
        mock_cursor.fetchall.return_value = sample_workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert
        assert result.workflow_count == 3
        assert result.total > 0
        assert 'Build' in result.phase_costs
        assert 'Test' in result.phase_costs
        assert result.phase_costs['Build'] > 0  # Build should have cost
        assert sum(result.phase_percentages.values()) == pytest.approx(100.0, rel=0.1)

    def test_analyze_by_phase_empty_data(self, service):
        """Test phase analysis with no workflows."""
        # Setup mock to return empty
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert
        assert result.workflow_count == 0
        assert result.total == 0.0
        assert len(result.phase_costs) == 0

    def test_analyze_by_phase_json_parsing(self, service):
        """Test parsing of JSON cost_breakdown field."""
        workflows = [
            {
                'cost_breakdown': json.dumps({
                    'by_phase': {
                        'Plan': 2.0,
                        'Build': 8.0
                    }
                }),  # String format
                'actual_cost_total': 10.0
            }
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_phase(days=30)

        # Assert
        assert result.workflow_count == 1
        assert 'Plan' in result.phase_costs
        assert 'Build' in result.phase_costs


class TestAnalyzeByWorkflowType:
    """Test workflow type cost analysis."""

    def test_analyze_by_workflow_type_success(self, service):
        """Test successful workflow type analysis."""
        workflows = [
            {
                'type': 'adw_sdlc_complete_iso',
                'total_cost': 45.0,
                'count': 3,
                'avg_cost': 15.0
            },
            {
                'type': 'adw_sdlc_complete_zte',
                'total_cost': 30.0,
                'count': 2,
                'avg_cost': 15.0
            }
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = workflows
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_workflow_type(days=30)

        # Assert
        assert len(result.by_type) == 2
        assert 'adw_sdlc_complete_iso' in result.by_type
        assert result.by_type['adw_sdlc_complete_iso'] == 45.0
        assert result.count_by_type['adw_sdlc_complete_iso'] == 3
        assert result.average_by_type['adw_sdlc_complete_iso'] == 15.0

    def test_analyze_by_workflow_type_empty(self, service):
        """Test workflow type analysis with no data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_workflow_type(days=30)

        # Assert
        assert len(result.by_type) == 0
        assert len(result.count_by_type) == 0
        assert len(result.average_by_type) == 0


class TestAnalyzeByTimePeriod:
    """Test time series analysis."""

    def test_analyze_by_time_period_success(self, service):
        """Test successful time series analysis."""
        # Generate daily costs for last 10 days
        daily_data = []
        for i in range(10):
            date = (datetime.now() - timedelta(days=9-i)).date()
            daily_data.append({
                'date': date,
                'daily_cost': 10.0 + i,  # Increasing trend
                'workflow_count': 2
            })

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = daily_data
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_time_period(period='day', days=10)

        # Assert
        assert len(result.daily_costs) == 10
        assert result.total_cost > 0
        assert result.average_daily_cost > 0
        assert result.trend_direction in ['increasing', 'decreasing', 'stable']
        assert len(result.moving_average) == 10

    def test_analyze_by_time_period_calculates_trend(self, service):
        """Test trend calculation."""
        # Generate increasing cost trend
        daily_data = []
        for i in range(14):
            date = (datetime.now() - timedelta(days=13-i)).date()
            daily_data.append({
                'date': date,
                'daily_cost': 10.0 + (i * 2),  # Clear increasing trend
                'workflow_count': 2
            })

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = daily_data
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            result = service.analyze_by_time_period(period='day', days=14)

        # Assert
        assert result.trend_direction == 'increasing'
        assert result.percentage_change > 10  # Should show significant increase


class TestOptimizationOpportunities:
    """Test optimization opportunity detection."""

    def test_detect_phase_anomalies(self, service):
        """Test detection of high-cost phases."""
        # Create phase breakdown with Build phase abnormally high
        from services.cost_analytics_service import PhaseBreakdown

        phase_breakdown = PhaseBreakdown(
            phase_costs={
                'Plan': 2.0,
                'Build': 50.0,  # Abnormally high (should be ~25%)
                'Test': 10.0,
                'Review': 3.0
            },
            phase_percentages={
                'Plan': 3.1,
                'Build': 76.9,  # 76.9% (expected: 25%)
                'Test': 15.4,
                'Review': 4.6
            },
            phase_counts={
                'Plan': 5,
                'Build': 5,
                'Test': 5,
                'Review': 5
            },
            total=65.0,
            average_per_workflow=13.0,
            workflow_count=5
        )

        # Call internal method
        opportunities = service._detect_phase_anomalies(phase_breakdown)

        # Assert
        assert len(opportunities) > 0
        # Find Build phase opportunity
        build_opp = [o for o in opportunities if 'Build' in o.description]
        assert len(build_opp) > 0
        assert build_opp[0].category == 'phase'
        assert build_opp[0].priority in ['high', 'medium']

    def test_detect_workflow_inefficiencies(self, service):
        """Test detection of inefficient workflow types."""
        from services.cost_analytics_service import WorkflowBreakdown

        workflow_breakdown = WorkflowBreakdown(
            by_type={
                'normal_workflow': 30.0,
                'expensive_workflow': 100.0  # More than 50% above average
            },
            count_by_type={
                'normal_workflow': 3,
                'expensive_workflow': 3
            },
            average_by_type={
                'normal_workflow': 10.0,
                'expensive_workflow': 33.33  # Much higher than avg (21.67)
            }
        )

        # Call internal method
        opportunities = service._detect_workflow_inefficiencies(workflow_breakdown)

        # Assert
        assert len(opportunities) > 0
        assert opportunities[0].category == 'workflow_type'

    def test_get_optimization_opportunities_integration(self, service, sample_workflows):
        """Test complete optimization opportunity detection."""
        # Mock all necessary database calls
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Setup responses for different queries
        def fetchall_side_effect(*args, **kwargs):
            # First call: phase analysis
            if not hasattr(fetchall_side_effect, 'call_count'):
                fetchall_side_effect.call_count = 0
            fetchall_side_effect.call_count += 1

            if fetchall_side_effect.call_count == 1:
                return sample_workflows
            elif fetchall_side_effect.call_count == 2:
                # Workflow type analysis
                return [
                    {'type': 'test_workflow', 'total_cost': 70.8, 'count': 3, 'avg_cost': 23.6}
                ]
            else:
                return []

        def fetchone_side_effect(*args, **kwargs):
            if not hasattr(fetchone_side_effect, 'call_count'):
                fetchone_side_effect.call_count = 0
            fetchone_side_effect.call_count += 1

            if fetchone_side_effect.call_count == 1:
                # Statistics query
                return {'avg_cost': 23.6, 'stddev_cost': 2.5}
            else:
                # Outlier count query
                return {'outlier_count': 0, 'outlier_total_cost': 0}

        mock_cursor.fetchall.side_effect = fetchall_side_effect
        mock_cursor.fetchone.side_effect = fetchone_side_effect
        mock_conn.cursor.return_value = mock_cursor

        with patch(
            "services.cost_analytics_service.get_database_adapter",
        ) as mock_get_adapter:
            mock_adapter_inst = MagicMock()
            mock_adapter_inst.get_connection.return_value.__enter__.return_value = mock_conn
            mock_get_adapter.return_value = mock_adapter_inst

            # Execute
            opportunities = service.get_optimization_opportunities(days=30)

        # Assert
        assert isinstance(opportunities, list)
        # Should be sorted by estimated savings
        if len(opportunities) > 1:
            for i in range(len(opportunities) - 1):
                assert opportunities[i].estimated_savings >= opportunities[i+1].estimated_savings


class TestHelperMethods:
    """Test helper methods."""

    def test_calculate_moving_average(self, service):
        """Test moving average calculation."""
        values = [10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0, 18.0, 17.0, 19.0]

        moving_avg = service._calculate_moving_average(values, window=7)

        assert len(moving_avg) == len(values)
        # Last value should be average of last 7 values
        expected_last = sum(values[-7:]) / 7
        assert moving_avg[-1] == pytest.approx(expected_last, rel=0.01)

    def test_calculate_moving_average_short_series(self, service):
        """Test moving average with short series."""
        values = [10.0, 12.0, 11.0]

        moving_avg = service._calculate_moving_average(values, window=7)

        # Should return same length, using available data
        assert len(moving_avg) == len(values)

    def test_calculate_trend_increasing(self, service):
        """Test trend detection for increasing costs."""
        from services.cost_analytics_service import TimeSeriesDataPoint

        # Generate increasing trend
        daily_costs = [
            TimeSeriesDataPoint(date=f"2025-12-{i:02d}", cost=10.0 + i, workflow_count=2)
            for i in range(1, 15)
        ]

        trend, percentage = service._calculate_trend(daily_costs)

        assert trend == 'increasing'
        assert percentage > 0

    def test_calculate_trend_decreasing(self, service):
        """Test trend detection for decreasing costs."""
        from services.cost_analytics_service import TimeSeriesDataPoint

        # Generate decreasing trend
        daily_costs = [
            TimeSeriesDataPoint(date=f"2025-12-{i:02d}", cost=20.0 - i, workflow_count=2)
            for i in range(1, 15)
        ]

        trend, percentage = service._calculate_trend(daily_costs)

        assert trend == 'decreasing'
        assert percentage < 0

    def test_calculate_trend_stable(self, service):
        """Test trend detection for stable costs."""
        from services.cost_analytics_service import TimeSeriesDataPoint

        # Generate stable trend
        daily_costs = [
            TimeSeriesDataPoint(date=f"2025-12-{i:02d}", cost=15.0, workflow_count=2)
            for i in range(1, 15)
        ]

        trend, percentage = service._calculate_trend(daily_costs)

        assert trend == 'stable'
        assert abs(percentage) < 5

    def test_resolve_date_range(self, service):
        """Test date range resolution."""
        start, end = service._resolve_date_range(None, None, 30)

        assert start is not None
        assert end is not None
        # Start should be 30 days before end
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        diff = (end_dt - start_dt).days
        assert 29 <= diff <= 31  # Account for timezone differences

    def test_get_phase_recommendation(self, service):
        """Test phase-specific recommendations."""
        recommendation = service._get_phase_recommendation('build')

        assert 'external tool' in recommendation.lower() or 'ruff' in recommendation.lower()

        recommendation = service._get_phase_recommendation('test')
        assert 'cach' in recommendation.lower() or 'pytest' in recommendation.lower()
