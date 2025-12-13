"""Tests for pattern validation system."""
import uuid

import pytest
from core.pattern_validator import ValidationResult, validate_predictions


@pytest.fixture
def db_connection():
    """Get test database connection."""
    from database import get_database_adapter
    adapter = get_database_adapter()
    with adapter.get_connection() as conn:
        yield conn
        conn.rollback()  # Rollback test data


@pytest.fixture
def sample_patterns(db_connection):
    """Create sample patterns and predictions in DB."""
    cursor = db_connection.cursor()

    # Use unique suffix to avoid conflicts
    test_id = str(uuid.uuid4())[:8]

    # Pattern signatures with unique suffix
    sig1 = f'test:pytest:backend:{test_id}'
    sig2 = f'build:typecheck:backend:{test_id}'
    sig3 = f'fix:bug:{test_id}'

    # Insert test patterns
    cursor.execute("""
        INSERT INTO operation_patterns (
            pattern_signature, pattern_type, automation_status
        ) VALUES
            (%s, 'test', 'detected'),
            (%s, 'build', 'detected'),
            (%s, 'fix', 'detected')
        RETURNING id
    """, (sig1, sig2, sig3))
    pattern_ids = [row['id'] for row in cursor.fetchall()]

    # Request ID with unique suffix
    request_id = f'test-req-{test_id}'

    # Insert predictions
    cursor.execute("""
        INSERT INTO pattern_predictions (
            request_id, pattern_id, confidence_score, reasoning
        ) VALUES
            (%s, %s, 0.85, 'Test prediction 1'),
            (%s, %s, 0.75, 'Test prediction 2'),
            (%s, %s, 0.60, 'Test prediction 3')
    """, (request_id, pattern_ids[0], request_id, pattern_ids[1], request_id, pattern_ids[2]))

    db_connection.commit()

    return {
        'request_id': request_id,
        'pattern_ids': pattern_ids,
        'predicted_signatures': [sig1, sig2, sig3]
    }


def test_validate_predictions_perfect_accuracy(db_connection, sample_patterns):
    """All predictions match actual patterns - 100% accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    actual_patterns = sample_patterns['predicted_signatures']  # All match

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-001',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 3
    assert result.total_actual == 3
    assert result.correct == 3
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.accuracy == 1.0

    # Verify database updated
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 1
    """, (request_id,))
    assert cursor.fetchone()['count'] == 3


def test_validate_predictions_partial_accuracy(db_connection, sample_patterns):
    """Some predictions correct, some not - partial accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    sig1 = sample_patterns['predicted_signatures'][0]  # test:pytest:backend
    sig2 = sample_patterns['predicted_signatures'][1]  # build:typecheck:backend
    # sig3 = fix:bug (predicted but not actual - FP)

    actual_patterns = [
        sig1,  # Correct (TP)
        sig2,  # Correct (TP)
        'deploy:production'  # Not predicted (FN)
    ]

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-002',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 3
    assert result.total_actual == 3
    assert result.correct == 2  # test:pytest, build:typecheck
    assert result.false_positives == 1  # fix:bug
    assert result.false_negatives == 1  # deploy:production
    assert result.accuracy == pytest.approx(2/3, 0.01)  # 66.7%

    # Verify database
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 1
    """, (request_id,))
    assert cursor.fetchone()['count'] == 2

    cursor.execute("""
        SELECT COUNT(*) as count FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 0
    """, (request_id,))
    assert cursor.fetchone()['count'] == 1


def test_validate_predictions_no_predictions(db_connection):
    """No predictions were made - graceful handling."""
    # Act
    result = validate_predictions(
        request_id='nonexistent-req',
        workflow_id='wf-003',
        actual_patterns=['test:pytest:backend'],
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 0
    assert result.total_actual == 1
    assert result.correct == 0
    assert result.false_positives == 0
    assert result.false_negatives == 1
    assert result.accuracy == 0.0


def test_validate_predictions_updates_pattern_accuracy(db_connection, sample_patterns):
    """Validation updates operation_patterns.prediction_accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    sig1 = sample_patterns['predicted_signatures'][0]
    sig2 = sample_patterns['predicted_signatures'][1]
    actual_patterns = [sig1]  # Only first pattern is correct

    # Act
    validate_predictions(
        request_id=request_id,
        workflow_id='wf-004',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert - Check pattern accuracy was updated
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = %s
    """, (sig1,))
    accuracy = cursor.fetchone()['prediction_accuracy']
    assert accuracy == 1.0  # This pattern was predicted correctly

    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = %s
    """, (sig2,))
    accuracy = cursor.fetchone()['prediction_accuracy']
    assert accuracy == 0.0  # This pattern was predicted incorrectly


def test_validate_predictions_empty_actual(db_connection, sample_patterns):
    """Workflow completed with no detected patterns."""
    # Arrange
    request_id = sample_patterns['request_id']

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-005',
        actual_patterns=[],  # No patterns detected
        db_connection=db_connection
    )

    # Assert - All predictions are false positives
    assert result.total_predicted == 3
    assert result.total_actual == 0
    assert result.correct == 0
    assert result.false_positives == 3
    assert result.false_negatives == 0
    assert result.accuracy == 0.0


def test_validation_result_dataclass():
    """ValidationResult dataclass has correct structure."""
    result = ValidationResult(
        total_predicted=5,
        total_actual=4,
        correct=3,
        false_positives=2,
        false_negatives=1,
        accuracy=0.6,
        details={'pattern1': True, 'pattern2': False}
    )

    assert result.total_predicted == 5
    assert result.total_actual == 4
    assert result.correct == 3
    assert result.false_positives == 2
    assert result.false_negatives == 1
    assert result.accuracy == 0.6
    assert 'pattern1' in result.details
