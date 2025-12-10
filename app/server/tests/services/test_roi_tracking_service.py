"""
Tests for ROI Tracking Service

Tests pattern execution tracking, ROI calculation, effectiveness rating, and reporting.

Run with:
    cd app/server
    pytest tests/services/test_roi_tracking_service.py -v
    pytest tests/services/test_roi_tracking_service.py -v -k "test_record_execution"
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from core.models.workflow import PatternExecution
from services.roi_tracking_service import ROITrackingService


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "%s"  # PostgreSQL placeholder
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create ROITrackingService with mocked adapter."""
    with patch(
        "services.roi_tracking_service.get_database_adapter",
        return_value=mock_adapter,
    ):
        return ROITrackingService()


@pytest.fixture
def sample_execution():
    """Sample pattern execution."""
    return PatternExecution(
        pattern_id="test-retry-automation",
        workflow_id=123,
        execution_time_seconds=45.2,
        estimated_time_seconds=60.0,
        actual_cost=0.012,
        estimated_cost=0.015,
        success=True,
        error_message=None,
        executed_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def sample_roi_summary():
    """Sample ROI summary data."""
    return {
        'pattern_id': 'test-retry-automation',
        'total_executions': 150,
        'successful_executions': 148,
        'success_rate': 0.987,
        'total_time_saved_seconds': 3450.0,
        'total_cost_saved_usd': 425.50,
        'average_time_saved_seconds': 23.0,
        'average_cost_saved_usd': 2.84,
        'roi_percentage': 312.0,
        'last_updated': datetime.utcnow()
    }


def test_record_execution(service, mock_adapter, sample_execution):
    """Test recording a pattern execution."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {'id': 1}
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Mock update_roi_summary to avoid additional queries
    with patch.object(service, 'update_roi_summary'):
        # Execute
        execution_id = service.record_execution(sample_execution)

        # Verify
        assert execution_id == 1
        assert mock_cursor.execute.called
        assert mock_conn.commit.called

        # Check SQL was called with correct data
        execute_call = mock_cursor.execute.call_args
        sql = execute_call[0][0]
        params = execute_call[0][1]

        assert "INSERT INTO pattern_executions" in sql
        assert params[0] == "test-retry-automation"  # pattern_id
        assert params[1] == 123  # workflow_id
        assert params[2] == 45.2  # execution_time_seconds
        assert params[3] == 60.0  # estimated_time_seconds
        assert params[4] == 0.012  # actual_cost
        assert params[5] == 0.015  # estimated_cost
        assert params[6] is True  # success


def test_update_roi_summary(service, mock_adapter):
    """Test ROI summary calculation."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock aggregate query results
    mock_cursor.fetchone.return_value = {
        'total_executions': 150,
        'successful_executions': 148,
        'total_time_saved': 3450.0,
        'total_cost_saved': 425.50,
        'total_investment': 2220.0,
    }

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    service.update_roi_summary("test-retry-automation")

    # Verify
    assert mock_cursor.execute.call_count == 2  # SELECT + UPSERT
    assert mock_conn.commit.called

    # Check UPSERT SQL
    upsert_call = mock_cursor.execute.call_args_list[1]
    sql = upsert_call[0][0]
    params = upsert_call[0][1]

    assert "INSERT INTO pattern_roi_summary" in sql
    assert "ON CONFLICT" in sql
    assert params[0] == "test-retry-automation"  # pattern_id
    assert params[1] == 150  # total_executions
    assert params[2] == 148  # successful_executions
    assert abs(params[3] - 0.987) < 0.001  # success_rate
    assert params[4] == 3450.0  # total_time_saved
    assert params[5] == 425.50  # total_cost_saved


def test_get_pattern_roi(service, mock_adapter, sample_roi_summary):
    """Test retrieving pattern ROI summary."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = sample_roi_summary
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    summary = service.get_pattern_roi("test-retry-automation")

    # Verify
    assert summary is not None
    assert summary.pattern_id == "test-retry-automation"
    assert summary.total_executions == 150
    assert summary.successful_executions == 148
    assert abs(summary.success_rate - 0.987) < 0.001
    assert summary.total_cost_saved_usd == 425.50
    assert summary.roi_percentage == 312.0


def test_get_pattern_roi_not_found(service, mock_adapter):
    """Test retrieving ROI for non-existent pattern."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    summary = service.get_pattern_roi("non-existent-pattern")

    # Verify
    assert summary is None


def test_get_all_roi_summaries(service, mock_adapter):
    """Test retrieving all ROI summaries."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            'pattern_id': 'pattern-1',
            'total_executions': 100,
            'successful_executions': 95,
            'success_rate': 0.95,
            'total_time_saved_seconds': 2000.0,
            'total_cost_saved_usd': 250.0,
            'average_time_saved_seconds': 20.0,
            'average_cost_saved_usd': 2.5,
            'roi_percentage': 200.0,
            'last_updated': datetime.utcnow()
        },
        {
            'pattern_id': 'pattern-2',
            'total_executions': 50,
            'successful_executions': 48,
            'success_rate': 0.96,
            'total_time_saved_seconds': 1000.0,
            'total_cost_saved_usd': 120.0,
            'average_time_saved_seconds': 20.0,
            'average_cost_saved_usd': 2.4,
            'roi_percentage': 150.0,
            'last_updated': datetime.utcnow()
        }
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    summaries = service.get_all_roi_summaries()

    # Verify
    assert len(summaries) == 2
    assert summaries[0].pattern_id == 'pattern-1'
    assert summaries[1].pattern_id == 'pattern-2'
    assert summaries[0].total_executions == 100
    assert summaries[1].total_executions == 50


def test_calculate_effectiveness_excellent(service, mock_adapter):
    """Test effectiveness calculation for excellent pattern."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        'pattern_id': 'excellent-pattern',
        'total_executions': 100,
        'successful_executions': 98,
        'success_rate': 0.98,
        'total_time_saved_seconds': 2000.0,
        'total_cost_saved_usd': 300.0,
        'average_time_saved_seconds': 20.0,
        'average_cost_saved_usd': 3.0,
        'roi_percentage': 250.0,
        'last_updated': datetime.utcnow()
    }
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    effectiveness = service.calculate_effectiveness("excellent-pattern")

    # Verify
    assert effectiveness == "excellent"


def test_calculate_effectiveness_good(service, mock_adapter):
    """Test effectiveness calculation for good pattern."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        'pattern_id': 'good-pattern',
        'total_executions': 100,
        'successful_executions': 87,
        'success_rate': 0.87,
        'total_time_saved_seconds': 1500.0,
        'total_cost_saved_usd': 180.0,
        'average_time_saved_seconds': 15.0,
        'average_cost_saved_usd': 1.8,
        'roi_percentage': 120.0,
        'last_updated': datetime.utcnow()
    }
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    effectiveness = service.calculate_effectiveness("good-pattern")

    # Verify
    assert effectiveness == "good"


def test_calculate_effectiveness_poor(service, mock_adapter):
    """Test effectiveness calculation for poor pattern."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        'pattern_id': 'poor-pattern',
        'total_executions': 50,
        'successful_executions': 30,
        'success_rate': 0.60,
        'total_time_saved_seconds': 200.0,
        'total_cost_saved_usd': 25.0,
        'average_time_saved_seconds': 4.0,
        'average_cost_saved_usd': 0.5,
        'roi_percentage': 20.0,
        'last_updated': datetime.utcnow()
    }
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    effectiveness = service.calculate_effectiveness("poor-pattern")

    # Verify
    assert effectiveness == "poor"


def test_get_top_performers(service, mock_adapter):
    """Test retrieving top performing patterns."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            'pattern_id': 'top-pattern-1',
            'total_executions': 100,
            'successful_executions': 98,
            'success_rate': 0.98,
            'total_time_saved_seconds': 3000.0,
            'total_cost_saved_usd': 400.0,
            'average_time_saved_seconds': 30.0,
            'average_cost_saved_usd': 4.0,
            'roi_percentage': 320.0,
            'last_updated': datetime.utcnow()
        },
        {
            'pattern_id': 'top-pattern-2',
            'total_executions': 80,
            'successful_executions': 77,
            'success_rate': 0.96,
            'total_time_saved_seconds': 2400.0,
            'total_cost_saved_usd': 300.0,
            'average_time_saved_seconds': 30.0,
            'average_cost_saved_usd': 3.75,
            'roi_percentage': 280.0,
            'last_updated': datetime.utcnow()
        }
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    performers = service.get_top_performers(limit=10)

    # Verify
    assert len(performers) == 2
    assert performers[0].pattern_id == 'top-pattern-1'
    assert performers[0].roi_percentage == 320.0
    assert performers[1].pattern_id == 'top-pattern-2'
    assert performers[1].roi_percentage == 280.0


def test_get_underperformers(service, mock_adapter):
    """Test retrieving underperforming patterns."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            'pattern_id': 'poor-pattern-1',
            'total_executions': 30,
            'successful_executions': 18,
            'success_rate': 0.60,
            'total_time_saved_seconds': 100.0,
            'total_cost_saved_usd': -50.0,  # Negative ROI
            'average_time_saved_seconds': 3.33,
            'average_cost_saved_usd': -1.67,
            'roi_percentage': -25.0,
            'last_updated': datetime.utcnow()
        }
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    underperformers = service.get_underperformers(limit=10)

    # Verify
    assert len(underperformers) == 1
    assert underperformers[0].pattern_id == 'poor-pattern-1'
    assert underperformers[0].success_rate == 0.60
    assert underperformers[0].roi_percentage == -25.0
    assert underperformers[0].total_cost_saved_usd == -50.0


def test_get_roi_report(service, mock_adapter):
    """Test generating comprehensive ROI report."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock pattern details query
    def fetchone_side_effect():
        if "pattern_approvals" in mock_cursor.execute.call_args[0][0]:
            return {
                'pattern_id': 'test-pattern',
                'tool_sequence': 'test → retry → automation',
                'created_at': '2024-01-01T00:00:00Z'
            }
        else:
            # ROI summary
            return {
                'pattern_id': 'test-pattern',
                'total_executions': 50,
                'successful_executions': 48,
                'success_rate': 0.96,
                'total_time_saved_seconds': 1200.0,
                'total_cost_saved_usd': 150.0,
                'average_time_saved_seconds': 24.0,
                'average_cost_saved_usd': 3.0,
                'roi_percentage': 200.0,
                'last_updated': datetime.utcnow()
            }

    mock_cursor.fetchone.side_effect = fetchone_side_effect

    # Mock executions query
    mock_cursor.fetchall.return_value = [
        {
            'id': 1,
            'pattern_id': 'test-pattern',
            'workflow_id': 123,
            'execution_time_seconds': 45.0,
            'estimated_time_seconds': 60.0,
            'actual_cost': 0.012,
            'estimated_cost': 0.015,
            'success': True,
            'error_message': None,
            'executed_at': datetime.utcnow()
        }
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    report = service.get_roi_report("test-pattern")

    # Verify
    assert report is not None
    assert report.pattern_id == "test-pattern"
    assert report.pattern_name == "test → retry → automation"
    assert report.summary.total_executions == 50
    assert report.effectiveness_rating == "excellent"
    assert len(report.executions) == 1
    assert "Exceptional performance" in report.recommendation
