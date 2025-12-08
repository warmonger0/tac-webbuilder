"""
Tests for Confidence Update Service

Tests confidence calculation, pattern updates, history tracking, and recommendations.

Run with:
    cd app/server
    pytest tests/services/test_confidence_update_service.py -v
    pytest tests/services/test_confidence_update_service.py -v -k "test_calculate_confidence"
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, call
import json

import pytest
from services.confidence_update_service import ConfidenceUpdateService
from core.models.workflow import PatternROISummary, ConfidenceUpdate, StatusChangeRecommendation


@pytest.fixture
def mock_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    adapter.placeholder.return_value = "%s"  # PostgreSQL placeholder
    return adapter


@pytest.fixture
def service(mock_adapter):
    """Create ConfidenceUpdateService with mocked adapter."""
    with patch(
        "services.confidence_update_service.get_database_adapter",
        return_value=mock_adapter,
    ):
        return ConfidenceUpdateService()


@pytest.fixture
def excellent_roi_summary():
    """ROI summary for excellent performer."""
    return PatternROISummary(
        pattern_id="test-excellent-pattern",
        total_executions=150,
        successful_executions=148,
        success_rate=0.987,  # 98.7% success
        total_time_saved_seconds=3450.0,
        total_cost_saved_usd=425.50,
        average_time_saved_seconds=23.0,
        average_cost_saved_usd=2.84,
        roi_percentage=312.0,  # 312% ROI
        last_updated=datetime.utcnow().isoformat()
    )


@pytest.fixture
def poor_roi_summary():
    """ROI summary for poor performer."""
    return PatternROISummary(
        pattern_id="test-poor-pattern",
        total_executions=20,
        successful_executions=12,
        success_rate=0.60,  # 60% success
        total_time_saved_seconds=100.0,
        total_cost_saved_usd=-15.0,
        average_time_saved_seconds=8.3,
        average_cost_saved_usd=-1.25,
        roi_percentage=-25.0,  # -25% ROI (negative)
        last_updated=datetime.utcnow().isoformat()
    )


def test_calculate_confidence_adjustment_excellent(service, excellent_roi_summary):
    """Test confidence calculation for excellent performer."""
    # Calculate
    new_confidence = service.calculate_confidence_adjustment(excellent_roi_summary)

    # Verify
    # Base: 0.987 (success rate)
    # ROI bonus: 312/1000 = 0.312, clamped to 0.1
    # Exec bonus: 150/1000 = 0.15, clamped to 0.05
    # Expected: 0.987 + 0.1 + 0.05 = 1.137, clamped to 1.0
    assert new_confidence == 1.0


def test_calculate_confidence_adjustment_poor(service, poor_roi_summary):
    """Test confidence calculation for poor performer with negative ROI."""
    # Calculate
    new_confidence = service.calculate_confidence_adjustment(poor_roi_summary)

    # Verify
    # Base: 0.60 (success rate)
    # ROI bonus: min(0.1, -25/1000) = -0.025 (negative ROI can reduce further)
    # Exec bonus: min(0.05, 20/1000) = 0.02
    # ROI penalty: abs(-25)/100 = 0.25 (for -25% ROI)
    # Expected: 0.60 + (-0.025) + 0.02 - 0.25 = 0.345
    assert new_confidence == pytest.approx(0.345, abs=0.01)


def test_update_pattern_confidence(service, mock_adapter, excellent_roi_summary):
    """Test updating confidence score for a single pattern."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock ROI summary query
    mock_cursor.fetchone.side_effect = [
        {
            'pattern_id': 'test-excellent-pattern',
            'total_executions': 150,
            'successful_executions': 148,
            'success_rate': 0.987,
            'total_time_saved_seconds': 3450.0,
            'total_cost_saved_usd': 425.50,
            'average_time_saved_seconds': 23.0,
            'average_cost_saved_usd': 2.84,
            'roi_percentage': 312.0,
            'last_updated': datetime.utcnow()
        },
        {'confidence_score': 0.80},  # Current confidence
        {'id': 1}  # Insert ID for confidence history
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    update = service.update_pattern_confidence('test-excellent-pattern', dry_run=False)

    # Verify
    assert update is not None
    assert update.pattern_id == 'test-excellent-pattern'
    assert update.old_confidence == 0.80
    assert update.new_confidence == 1.0  # Calculated to max
    assert update.new_confidence > update.old_confidence  # Increased
    assert mock_conn.commit.called


def test_update_pattern_confidence_dry_run(service, mock_adapter, excellent_roi_summary):
    """Test dry run mode (no database changes)."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_cursor.fetchone.side_effect = [
        {
            'pattern_id': 'test-excellent-pattern',
            'total_executions': 150,
            'successful_executions': 148,
            'success_rate': 0.987,
            'total_time_saved_seconds': 3450.0,
            'total_cost_saved_usd': 425.50,
            'average_time_saved_seconds': 23.0,
            'average_cost_saved_usd': 2.84,
            'roi_percentage': 312.0,
            'last_updated': datetime.utcnow()
        },
        {'confidence_score': 0.80}
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    update = service.update_pattern_confidence('test-excellent-pattern', dry_run=True)

    # Verify
    assert update is not None
    assert update.old_confidence == 0.80
    assert update.new_confidence == 1.0
    assert not mock_conn.commit.called  # No commit in dry run
    assert update.updated_at is None  # No timestamp in dry run


def test_get_confidence_history(service, mock_adapter):
    """Test retrieving confidence change history."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock history query results
    mock_cursor.fetchall.return_value = [
        {
            'id': 3,
            'pattern_id': 'test-pattern',
            'old_confidence': 0.85,
            'new_confidence': 0.90,
            'adjustment_reason': 'Improved performance',
            'roi_data': json.dumps({'success_rate': 0.95, 'roi_percentage': 250.0}),
            'updated_by': 'system',
            'updated_at': datetime.utcnow()
        },
        {
            'id': 2,
            'pattern_id': 'test-pattern',
            'old_confidence': 0.80,
            'new_confidence': 0.85,
            'adjustment_reason': 'Good execution history',
            'roi_data': json.dumps({'success_rate': 0.90, 'roi_percentage': 200.0}),
            'updated_by': 'system',
            'updated_at': datetime.utcnow()
        },
        {
            'id': 1,
            'pattern_id': 'test-pattern',
            'old_confidence': 0.75,
            'new_confidence': 0.80,
            'adjustment_reason': 'Initial performance data',
            'roi_data': json.dumps({'success_rate': 0.85, 'roi_percentage': 150.0}),
            'updated_by': 'system',
            'updated_at': datetime.utcnow()
        }
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    history = service.get_confidence_history('test-pattern')

    # Verify
    assert len(history) == 3
    assert history[0].old_confidence == 0.85
    assert history[0].new_confidence == 0.90
    assert history[1].old_confidence == 0.80
    assert history[2].old_confidence == 0.75
    assert all(isinstance(h, ConfidenceUpdate) for h in history)


def test_recommend_status_changes(service, mock_adapter):
    """Test status change recommendation logic."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock query results with various patterns
    mock_cursor.fetchall.return_value = [
        {
            'pattern_id': 'poor-performer',
            'status': 'approved',
            'confidence_score': 0.65,
            'success_rate': 0.60,  # Below 70%
            'roi_percentage': -10.0,  # Negative
            'total_executions': 25
        },
        {
            'pattern_id': 'excellent-pending',
            'status': 'pending',
            'confidence_score': 0.98,
            'success_rate': 0.97,  # Above 95%
            'roi_percentage': 250.0,  # Above 200%
            'total_executions': 50
        },
        {
            'pattern_id': 'borderline-approved',
            'status': 'approved',
            'confidence_score': 0.75,
            'success_rate': 0.75,  # Between 70-80%
            'roi_percentage': 40.0,  # Between 0-50%
            'total_executions': 30
        }
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Execute
    recommendations = service.recommend_status_changes()

    # Verify
    assert len(recommendations) == 3

    # Find recommendations by pattern
    poor = next(r for r in recommendations if r.pattern_id == 'poor-performer')
    excellent = next(r for r in recommendations if r.pattern_id == 'excellent-pending')
    borderline = next(r for r in recommendations if r.pattern_id == 'borderline-approved')

    # Poor performer should be recommended for rejection (high severity)
    assert poor.current_status == 'approved'
    assert poor.recommended_status == 'rejected'
    assert poor.severity == 'high'

    # Excellent pending should be recommended for auto-approval (medium severity)
    assert excellent.current_status == 'pending'
    assert excellent.recommended_status == 'auto-approved'
    assert excellent.severity == 'medium'

    # Borderline should be flagged for manual review (low severity)
    assert borderline.current_status == 'approved'
    assert borderline.recommended_status == 'manual-review'
    assert borderline.severity == 'low'


def test_update_all_patterns(service, mock_adapter):
    """Test batch update of all patterns."""
    # Setup mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Mock pattern list query
    mock_cursor.fetchall.return_value = [
        {'pattern_id': 'pattern-1'},
        {'pattern_id': 'pattern-2'},
        {'pattern_id': 'pattern-3'}
    ]

    mock_conn.cursor.return_value = mock_cursor
    mock_adapter.get_connection.return_value.__enter__.return_value = mock_conn

    # Mock update_pattern_confidence to return test data
    mock_updates = [
        ConfidenceUpdate(
            pattern_id='pattern-1',
            old_confidence=0.80,
            new_confidence=0.85,
            adjustment_reason='Improved',
            roi_data={}
        ),
        ConfidenceUpdate(
            pattern_id='pattern-2',
            old_confidence=0.90,
            new_confidence=0.88,
            adjustment_reason='Slight decline',
            roi_data={}
        ),
        ConfidenceUpdate(
            pattern_id='pattern-3',
            old_confidence=0.75,
            new_confidence=0.75,
            adjustment_reason='Unchanged',
            roi_data={}
        )
    ]

    with patch.object(service, 'update_pattern_confidence', side_effect=mock_updates):
        # Execute
        changes = service.update_all_patterns(dry_run=False)

        # Verify
        assert len(changes) == 3
        assert changes['pattern-1'] == pytest.approx(0.05, abs=0.01)  # Increased
        assert changes['pattern-2'] == pytest.approx(-0.02, abs=0.01)  # Decreased
        assert changes['pattern-3'] == 0.0  # Unchanged
