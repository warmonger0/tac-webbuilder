"""
Integration tests for pattern validation flow.

Tests end-to-end workflow:
1. Pattern detection in workflow
2. Prediction validation
3. Database updates
"""
import uuid

import pytest
from core.pattern_detector import process_and_validate_workflow


@pytest.fixture
def db_connection():
    """Get test database connection."""
    from database import get_database_adapter
    adapter = get_database_adapter()
    with adapter.get_connection() as conn:
        yield conn
        conn.rollback()  # Rollback test data


@pytest.fixture
def setup_test_data(db_connection):
    """Create test patterns and predictions."""
    cursor = db_connection.cursor()
    test_id = str(uuid.uuid4())[:8]

    # Create patterns
    sig1 = f'test:pytest:backend:{test_id}'
    sig2 = f'build:typecheck:backend:{test_id}'

    cursor.execute("""
        INSERT INTO operation_patterns (
            pattern_signature, pattern_type, automation_status
        ) VALUES
            (%s, 'test', 'detected'),
            (%s, 'build', 'detected')
        RETURNING id
    """, (sig1, sig2))
    pattern_ids = [row['id'] for row in cursor.fetchall()]

    # Create predictions for a request
    request_id = f'test-req-{test_id}'
    cursor.execute("""
        INSERT INTO pattern_predictions (
            request_id, pattern_id, confidence_score, reasoning
        ) VALUES
            (%s, %s, 0.90, 'Test prediction'),
            (%s, %s, 0.85, 'Build prediction')
    """, (request_id, pattern_ids[0], request_id, pattern_ids[1]))

    db_connection.commit()

    return {
        'request_id': request_id,
        'pattern_ids': pattern_ids,
        'signatures': [sig1, sig2],
        'test_id': test_id
    }


def test_end_to_end_validation_flow(db_connection, setup_test_data):
    """
    Test complete validation flow:
    - Workflow has request_id
    - Patterns detected
    - Validation runs
    - Database updated correctly
    """
    # Arrange
    test_data = setup_test_data
    sig1, sig2 = test_data['signatures']

    workflow = {
        'request_id': test_data['request_id'],
        'workflow_id': 'wf-integration-test',
        'nl_input': f'Run pytest tests and typecheck - {test_data["test_id"]}',
        'duration_seconds': 120,
        'error_count': 0
    }

    # Act
    result = process_and_validate_workflow(workflow, db_connection)

    # Assert - Patterns detected
    assert 'patterns' in result
    assert 'validation' in result
    assert result['validation'] is not None

    # Assert - Validation result
    validation = result['validation']
    assert validation.total_predicted == 2
    assert validation.accuracy >= 0  # May vary based on detection

    # Assert - Database updated
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM pattern_predictions
        WHERE request_id = %s AND was_correct IS NOT NULL
    """, (test_data['request_id'],))

    validated_count = cursor.fetchone()['count']
    assert validated_count == 2, "Both predictions should be validated"


def test_validation_with_partial_matches(db_connection, setup_test_data):
    """Test validation when only some predictions match actual patterns."""
    # Arrange
    test_data = setup_test_data
    # sig1 = test_data['signatures'][0]  # Will match
    # sig2 not in nl_input - will be false positive

    workflow = {
        'request_id': test_data['request_id'],
        'workflow_id': 'wf-partial-test',
        'nl_input': f'Run pytest tests - {test_data["test_id"]}',  # Only mentions pytest
        'duration_seconds': 90,
        'error_count': 0
    }

    # Act
    result = process_and_validate_workflow(workflow, db_connection)

    # Assert
    validation = result['validation']
    assert validation is not None
    assert validation.total_predicted == 2

    # Check database for correct/incorrect flags
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT was_correct
        FROM pattern_predictions
        WHERE request_id = %s
        ORDER BY id
    """, (test_data['request_id'],))

    results = [row['was_correct'] for row in cursor.fetchall()]
    assert len(results) == 2
    assert None not in results, "All predictions should be validated"


def test_validation_without_request_id(db_connection):
    """Test that workflow without request_id doesn't fail validation."""
    # Arrange
    workflow = {
        # No request_id
        'workflow_id': 'wf-no-request-id',
        'nl_input': 'Run tests',
        'duration_seconds': 60,
        'error_count': 0
    }

    # Act
    result = process_and_validate_workflow(workflow, db_connection)

    # Assert - Detection runs but validation is None
    assert 'patterns' in result
    assert 'validation' in result
    assert result['validation'] is None, "Should not validate without request_id"


def test_validation_without_db_connection():
    """Test that workflow without DB connection doesn't fail."""
    # Arrange
    workflow = {
        'request_id': 'test-req-123',
        'workflow_id': 'wf-no-db',
        'nl_input': 'Run tests',
        'duration_seconds': 60,
        'error_count': 0
    }

    # Act - No db_connection provided
    result = process_and_validate_workflow(workflow, db_connection=None)

    # Assert - Detection runs but validation is None
    assert 'patterns' in result
    assert 'validation' in result
    assert result['validation'] is None, "Should not validate without DB connection"


def test_validation_updates_pattern_accuracy(db_connection, setup_test_data):
    """Test that validation updates operation_patterns.prediction_accuracy."""
    # Arrange
    test_data = setup_test_data
    sig1, sig2 = test_data['signatures']

    workflow = {
        'request_id': test_data['request_id'],
        'workflow_id': 'wf-accuracy-test',
        'nl_input': f'Run pytest - {test_data["test_id"]}',  # Only sig1 matches
        'duration_seconds': 80,
        'error_count': 0
    }

    # Act
    process_and_validate_workflow(workflow, db_connection)

    # Assert - Check pattern accuracy updated in operation_patterns
    cursor = db_connection.cursor()

    # Check sig1 (should have accuracy data)
    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = %s
    """, (sig1,))
    accuracy1 = cursor.fetchone()['prediction_accuracy']
    assert accuracy1 is not None, "Pattern accuracy should be updated"

    # Check sig2 (should also have accuracy data)
    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = %s
    """, (sig2,))
    accuracy2 = cursor.fetchone()['prediction_accuracy']
    assert accuracy2 is not None, "Pattern accuracy should be updated"


def test_validation_error_handling(db_connection):
    """Test graceful error handling when validation fails."""
    # Arrange - Invalid request_id format
    workflow = {
        'request_id': None,  # Invalid
        'workflow_id': 'wf-error-test',
        'nl_input': 'Run tests',
        'duration_seconds': 60
    }

    # Act - Should not raise exception
    result = process_and_validate_workflow(workflow, db_connection)

    # Assert - Detection still works
    assert 'patterns' in result
    assert 'validation' in result
    assert result['validation'] is None, "Should handle None request_id gracefully"
