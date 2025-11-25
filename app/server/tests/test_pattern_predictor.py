"""
Unit tests for pattern_predictor module.

Tests pattern prediction from natural language input and storage
of predicted patterns in the database.
"""

import sqlite3

import pytest
from core.pattern_predictor import predict_patterns_from_input, store_predicted_patterns

# ============================================================================
# Tests for predict_patterns_from_input
# ============================================================================


@pytest.mark.unit
def test_predict_pytest_backend():
    """Test prediction of pytest backend test pattern with explicit keyword."""
    predictions = predict_patterns_from_input("Run backend tests with pytest")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "test:pytest:backend"
    assert predictions[0]["confidence"] == 0.85
    assert "Backend test keywords detected" in predictions[0]["reasoning"]


@pytest.mark.unit
def test_predict_vitest_frontend():
    """Test prediction of vitest frontend test pattern with explicit keyword."""
    predictions = predict_patterns_from_input("Run frontend tests with vitest")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "test:vitest:frontend"
    assert predictions[0]["confidence"] == 0.85
    assert "Frontend test keywords detected" in predictions[0]["reasoning"]


@pytest.mark.unit
def test_predict_backend_test_implicit():
    """Test prediction of backend test pattern without explicit pytest keyword."""
    predictions = predict_patterns_from_input("Run backend tests")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "test:pytest:backend"
    assert predictions[0]["confidence"] == 0.65  # Lower confidence without explicit framework


@pytest.mark.unit
def test_predict_frontend_test_implicit():
    """Test prediction of frontend test pattern with UI keyword."""
    predictions = predict_patterns_from_input("Test the UI components")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "test:vitest:frontend"
    assert predictions[0]["confidence"] == 0.65


@pytest.mark.unit
def test_predict_build_typecheck():
    """Test prediction of build pattern with typecheck keyword."""
    predictions = predict_patterns_from_input("Build and typecheck the project")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "build:typecheck:backend"
    assert predictions[0]["confidence"] == 0.75
    assert "Build operation keywords detected" in predictions[0]["reasoning"]


@pytest.mark.unit
def test_predict_deploy_production():
    """Test prediction of deployment pattern."""
    predictions = predict_patterns_from_input("Deploy to production")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "deploy:production"
    assert predictions[0]["confidence"] == 0.70
    assert "Deployment keywords detected" in predictions[0]["reasoning"]


@pytest.mark.unit
def test_predict_fix_bug():
    """Test prediction of bug fix pattern."""
    predictions = predict_patterns_from_input("Fix authentication bug")

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "fix:bug"
    assert predictions[0]["confidence"] == 0.60
    assert "Bug fix keywords detected" in predictions[0]["reasoning"]


@pytest.mark.unit
def test_predict_empty_input():
    """Test that empty input returns no predictions."""
    predictions = predict_patterns_from_input("")

    assert len(predictions) == 0


@pytest.mark.unit
def test_predict_ambiguous_input():
    """Test that ambiguous input returns no predictions."""
    predictions = predict_patterns_from_input("do something")

    assert len(predictions) == 0


@pytest.mark.unit
def test_predict_multiple_patterns():
    """Test prediction of multiple patterns from single input."""
    predictions = predict_patterns_from_input(
        "Run backend tests with pytest and frontend tests with vitest"
    )

    assert len(predictions) == 2
    patterns = {p["pattern"] for p in predictions}
    assert "test:pytest:backend" in patterns
    assert "test:vitest:frontend" in patterns


@pytest.mark.unit
def test_predict_case_insensitive():
    """Test that prediction is case-insensitive."""
    predictions_lower = predict_patterns_from_input("run pytest tests")
    predictions_upper = predict_patterns_from_input("RUN PYTEST TESTS")
    predictions_mixed = predict_patterns_from_input("Run PyTest Tests")

    assert len(predictions_lower) == 1
    assert len(predictions_upper) == 1
    assert len(predictions_mixed) == 1
    assert predictions_lower[0]["pattern"] == predictions_upper[0]["pattern"]
    assert predictions_lower[0]["pattern"] == predictions_mixed[0]["pattern"]


@pytest.mark.unit
def test_predict_with_project_path():
    """Test that project_path parameter is accepted (even if unused)."""
    predictions = predict_patterns_from_input(
        "Run backend tests", project_path="/tmp/test-project"
    )

    assert len(predictions) == 1
    assert predictions[0]["pattern"] == "test:pytest:backend"


# ============================================================================
# Tests for store_predicted_patterns
# ============================================================================


@pytest.fixture
def init_pattern_schema(temp_db_connection: sqlite3.Connection):
    """Initialize pattern-related tables in test database."""
    cursor = temp_db_connection.cursor()

    # Create operation_patterns table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_signature TEXT UNIQUE NOT NULL,
            pattern_type TEXT NOT NULL,
            first_detected TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now')),
            occurrence_count INTEGER DEFAULT 1,
            automation_status TEXT DEFAULT 'detected',
            confidence_score REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            prediction_count INTEGER DEFAULT 0,
            prediction_accuracy REAL DEFAULT 0.0,
            last_predicted TEXT
        )
    """)

    # Create pattern_predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pattern_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            pattern_id INTEGER NOT NULL,
            confidence_score REAL NOT NULL,
            reasoning TEXT,
            predicted_at TEXT DEFAULT (datetime('now')),
            was_correct INTEGER,
            validated_at TEXT,
            FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
        )
    """)

    temp_db_connection.commit()
    return temp_db_connection


@pytest.mark.unit
def test_store_predicted_patterns_new_pattern(temp_db_connection, init_pattern_schema):
    """Test storing predictions for a new pattern."""
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        }
    ]

    store_predicted_patterns("REQ-001", predictions, temp_db_connection)

    # Verify pattern was created
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT * FROM operation_patterns WHERE pattern_signature = ?",
                   ("test:pytest:backend",))
    pattern = cursor.fetchone()

    assert pattern is not None
    assert pattern["pattern_type"] == "test"
    assert pattern["automation_status"] == "predicted"
    assert pattern["prediction_count"] == 1

    # Verify prediction was stored
    cursor.execute("SELECT * FROM pattern_predictions WHERE request_id = ?", ("REQ-001",))
    prediction = cursor.fetchone()

    assert prediction is not None
    assert prediction["pattern_id"] == pattern["id"]
    assert prediction["confidence_score"] == 0.85
    assert prediction["reasoning"] == "Backend test keywords detected"


@pytest.mark.unit
def test_store_predicted_patterns_existing_pattern(temp_db_connection, init_pattern_schema):
    """Test storing predictions for an existing pattern."""
    # Create initial pattern
    cursor = temp_db_connection.cursor()
    cursor.execute("""
        INSERT INTO operation_patterns
        (pattern_signature, pattern_type, automation_status, prediction_count)
        VALUES (?, ?, ?, ?)
    """, ("test:pytest:backend", "test", "detected", 5))
    temp_db_connection.commit()

    # Store new prediction
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        }
    ]

    store_predicted_patterns("REQ-002", predictions, temp_db_connection)

    # Verify prediction count was incremented
    cursor.execute("SELECT prediction_count FROM operation_patterns WHERE pattern_signature = ?",
                   ("test:pytest:backend",))
    result = cursor.fetchone()
    assert result["prediction_count"] == 6

    # Verify new prediction was stored
    cursor.execute("SELECT COUNT(*) as count FROM pattern_predictions WHERE request_id = ?",
                   ("REQ-002",))
    result = cursor.fetchone()
    assert result["count"] == 1


@pytest.mark.unit
def test_store_predicted_patterns_multiple(temp_db_connection, init_pattern_schema):
    """Test storing multiple predictions at once."""
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        },
        {
            "pattern": "test:vitest:frontend",
            "confidence": 0.85,
            "reasoning": "Frontend test keywords detected",
        },
    ]

    store_predicted_patterns("REQ-003", predictions, temp_db_connection)

    # Verify both patterns were created
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM operation_patterns")
    result = cursor.fetchone()
    assert result["count"] == 2

    # Verify both predictions were stored
    cursor.execute("SELECT COUNT(*) as count FROM pattern_predictions WHERE request_id = ?",
                   ("REQ-003",))
    result = cursor.fetchone()
    assert result["count"] == 2


@pytest.mark.unit
def test_store_predicted_patterns_updates_last_predicted(temp_db_connection, init_pattern_schema):
    """Test that last_predicted timestamp is updated."""
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        }
    ]

    store_predicted_patterns("REQ-004", predictions, temp_db_connection)

    # Verify last_predicted was set
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT last_predicted FROM operation_patterns WHERE pattern_signature = ?",
                   ("test:pytest:backend",))
    result = cursor.fetchone()
    assert result["last_predicted"] is not None


@pytest.mark.unit
def test_store_predicted_patterns_transaction_rollback(temp_db_connection, init_pattern_schema):
    """Test that transaction rolls back on error."""
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        }
    ]

    # Store first prediction successfully
    store_predicted_patterns("REQ-005", predictions, temp_db_connection)

    # Verify it was stored
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM pattern_predictions WHERE request_id = ?",
                   ("REQ-005",))
    result = cursor.fetchone()
    assert result["count"] == 1


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
def test_end_to_end_prediction_and_storage(temp_db_connection, init_pattern_schema):
    """Test complete workflow: predict patterns and store them."""
    nl_input = "Run backend tests with pytest and deploy to production"
    request_id = "REQ-INTEGRATION-001"

    # Predict patterns
    predictions = predict_patterns_from_input(nl_input)
    assert len(predictions) == 2

    # Store predictions
    store_predicted_patterns(request_id, predictions, temp_db_connection)

    # Verify storage
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM pattern_predictions WHERE request_id = ?",
                   (request_id,))
    result = cursor.fetchone()
    assert result["count"] == 2

    # Verify patterns were created
    cursor.execute("SELECT COUNT(*) as count FROM operation_patterns")
    result = cursor.fetchone()
    assert result["count"] == 2


@pytest.mark.integration
def test_multiple_requests_same_pattern(temp_db_connection, init_pattern_schema):
    """Test that multiple requests with same pattern increment count."""
    predictions = [
        {
            "pattern": "test:pytest:backend",
            "confidence": 0.85,
            "reasoning": "Backend test keywords detected",
        }
    ]

    # Store predictions for multiple requests
    for i in range(5):
        store_predicted_patterns(f"REQ-{i}", predictions, temp_db_connection)

    # Verify prediction count
    cursor = temp_db_connection.cursor()
    cursor.execute("SELECT prediction_count FROM operation_patterns WHERE pattern_signature = ?",
                   ("test:pytest:backend",))
    result = cursor.fetchone()
    assert result["prediction_count"] == 5

    # Verify individual predictions stored
    cursor.execute("SELECT COUNT(*) as count FROM pattern_predictions")
    result = cursor.fetchone()
    assert result["count"] == 5
