"""
Tests for pattern_validator.py

Tests the pattern prediction validation system including accuracy calculations,
edge cases, and database operations.
"""

import sqlite3

import pytest
from core.pattern_validator import (
    _calculate_f1_score,
    get_validation_metrics,
    get_validation_summary,
    update_pattern_accuracy,
    validate_predictions,
)


@pytest.fixture
def test_db():
    """Create an in-memory test database with required schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create minimal schema for testing
    cursor.execute("""
        CREATE TABLE workflow_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT UNIQUE NOT NULL,
            adw_id TEXT NOT NULL,
            nl_input TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE operation_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_signature TEXT UNIQUE NOT NULL,
            pattern_type TEXT NOT NULL,
            occurrence_count INTEGER DEFAULT 1,
            confidence_score REAL DEFAULT 10.0,
            prediction_accuracy REAL DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE pattern_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            pattern_id INTEGER NOT NULL,
            pattern_signature TEXT NOT NULL,
            predicted_confidence REAL DEFAULT 0.0,
            was_correct INTEGER,
            validated_at TEXT,
            FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id),
            FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id),
            UNIQUE(workflow_id, pattern_id)
        )
    """)

    conn.commit()
    yield conn
    conn.close()


def test_validate_predictions_100_percent_accuracy(test_db):
    """Test validation with perfect prediction accuracy."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id, nl_input) VALUES (?, ?, ?)",
        ("wf-123", "adw-123", "Run backend tests"),
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up prediction
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-123", pattern_id, "test:pytest:backend", 85.0),
    )

    test_db.commit()

    # Validate predictions
    actual_patterns = ["test:pytest:backend"]
    result = validate_predictions("wf-123", actual_patterns, test_db)

    # Assertions
    assert result["total_predicted"] == 1
    assert result["total_actual"] == 1
    assert result["correct"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["accuracy"] == 1.0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1_score"] == 1.0

    # Check database was updated
    cursor.execute(
        "SELECT was_correct, validated_at FROM pattern_predictions WHERE workflow_id = ?",
        ("wf-123",),
    )
    row = cursor.fetchone()
    assert row["was_correct"] == 1
    assert row["validated_at"] is not None


def test_validate_predictions_0_percent_accuracy(test_db):
    """Test validation with no correct predictions."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-456", "adw-456")
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up prediction (wrong)
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-456", pattern_id, "test:pytest:backend", 60.0),
    )

    test_db.commit()

    # Validate with different actual pattern
    actual_patterns = ["build:typecheck:frontend"]
    result = validate_predictions("wf-456", actual_patterns, test_db)

    # Assertions
    assert result["total_predicted"] == 1
    assert result["total_actual"] == 1
    assert result["correct"] == 0
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1
    assert result["accuracy"] == 0.0


def test_validate_predictions_mixed_accuracy(test_db):
    """Test validation with some correct and some incorrect predictions."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-789", "adw-789")
    )

    # Set up patterns
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern1_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("build:typecheck:backend", "build"),
    )
    pattern2_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("format:eslint:all", "format"),
    )
    pattern3_id = cursor.lastrowid

    # Set up predictions (2 correct, 1 incorrect)
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-789", pattern1_id, "test:pytest:backend", 90.0),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-789", pattern2_id, "build:typecheck:backend", 75.0),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-789", pattern3_id, "format:eslint:all", 50.0),
    )

    test_db.commit()

    # Validate with 2 correct predictions
    actual_patterns = ["test:pytest:backend", "build:typecheck:backend"]
    result = validate_predictions("wf-789", actual_patterns, test_db)

    # Assertions
    assert result["total_predicted"] == 3
    assert result["total_actual"] == 2
    assert result["correct"] == 2
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 0
    assert result["accuracy"] == pytest.approx(2.0 / 3.0)
    assert result["precision"] == pytest.approx(2.0 / 3.0)
    assert result["recall"] == 1.0  # All actual patterns were predicted


def test_validate_predictions_no_predictions(test_db):
    """Test validation when no predictions exist."""
    cursor = test_db.cursor()

    # Set up workflow without predictions
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)",
        ("wf-empty", "adw-empty"),
    )
    test_db.commit()

    # Validate with actual patterns
    actual_patterns = ["test:pytest:backend"]
    result = validate_predictions("wf-empty", actual_patterns, test_db)

    # Assertions
    assert result["total_predicted"] == 0
    assert result["total_actual"] == 1
    assert result["correct"] == 0
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 1
    assert result["accuracy"] == 0.0


def test_validate_predictions_no_actual_patterns(test_db):
    """Test validation when no actual patterns are detected."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-999", "adw-999")
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up prediction
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-999", pattern_id, "test:pytest:backend", 70.0),
    )

    test_db.commit()

    # Validate with no actual patterns
    actual_patterns = []
    result = validate_predictions("wf-999", actual_patterns, test_db)

    # Assertions
    assert result["total_predicted"] == 1
    assert result["total_actual"] == 0
    assert result["correct"] == 0
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 0


def test_update_pattern_accuracy(test_db):
    """Test updating pattern accuracy from validation history."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-acc1", "adw-acc1")
    )
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-acc2", "adw-acc2")
    )
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-acc3", "adw-acc3")
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up validation history (2 correct, 1 incorrect)
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-acc1", pattern_id, "test:pytest:backend", 1),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-acc2", pattern_id, "test:pytest:backend", 1),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-acc3", pattern_id, "test:pytest:backend", 0),
    )

    test_db.commit()

    # Update pattern accuracy
    accuracy = update_pattern_accuracy(pattern_id, test_db)

    # Assertions
    assert accuracy == pytest.approx(2.0 / 3.0)

    # Check database was updated
    cursor.execute("SELECT prediction_accuracy FROM operation_patterns WHERE id = ?", (pattern_id,))
    row = cursor.fetchone()
    assert row["prediction_accuracy"] == pytest.approx(2.0 / 3.0)


def test_update_pattern_accuracy_no_history(test_db):
    """Test updating pattern accuracy when no validation history exists."""
    cursor = test_db.cursor()

    # Set up pattern without validation history
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid
    test_db.commit()

    # Update pattern accuracy
    accuracy = update_pattern_accuracy(pattern_id, test_db)

    # Assertions
    assert accuracy == 0.0


def test_get_validation_metrics(test_db):
    """Test retrieving validation metrics for a pattern."""
    cursor = test_db.cursor()

    # Set up workflows
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-m1", "adw-m1")
    )
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-m2", "adw-m2")
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up validation history
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-m1", pattern_id, "test:pytest:backend", 1),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-m2", pattern_id, "test:pytest:backend", 0),
    )

    test_db.commit()

    # Get metrics
    metrics = get_validation_metrics(pattern_id, test_db)

    # Assertions
    assert metrics is not None
    assert metrics["pattern_id"] == pattern_id
    assert metrics["pattern_signature"] == "test:pytest:backend"
    assert metrics["total_predictions"] == 2
    assert metrics["correct_predictions"] == 1
    assert metrics["incorrect_predictions"] == 1
    assert metrics["accuracy"] == 0.5


def test_get_validation_metrics_nonexistent_pattern(test_db):
    """Test retrieving metrics for a pattern that doesn't exist."""
    metrics = get_validation_metrics(99999, test_db)
    assert metrics is None


def test_get_validation_summary(test_db):
    """Test retrieving overall validation summary."""
    cursor = test_db.cursor()

    # Set up workflows
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-s1", "adw-s1")
    )
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-s2", "adw-s2")
    )

    # Set up patterns
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type, prediction_accuracy) VALUES (?, ?, ?)",
        ("test:pytest:backend", "test", 0.75),
    )
    pattern1_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type, prediction_accuracy) VALUES (?, ?, ?)",
        ("build:typecheck:backend", "build", 0.90),
    )
    pattern2_id = cursor.lastrowid

    # Set up predictions
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-s1", pattern1_id, "test:pytest:backend", 1),
    )
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, was_correct)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-s2", pattern2_id, "build:typecheck:backend", 1),
    )

    test_db.commit()

    # Get summary
    summary = get_validation_summary(test_db)

    # Assertions
    assert summary["total_patterns"] == 2
    assert summary["patterns_with_predictions"] == 2
    assert summary["total_predictions"] == 2
    assert summary["total_validations"] == 2
    assert summary["overall_accuracy"] == 1.0
    assert summary["patterns_above_70_percent"] == 2
    assert summary["patterns_above_90_percent"] == 1


def test_calculate_f1_score():
    """Test F1 score calculation."""
    # Perfect scores
    assert _calculate_f1_score(1.0, 1.0) == 1.0

    # Balanced scores
    assert _calculate_f1_score(0.5, 0.5) == 0.5

    # Imbalanced scores
    f1 = _calculate_f1_score(0.8, 0.6)
    expected = 2 * (0.8 * 0.6) / (0.8 + 0.6)
    assert f1 == pytest.approx(expected)

    # Zero scores
    assert _calculate_f1_score(0.0, 0.0) == 0.0

    # One zero score
    assert _calculate_f1_score(1.0, 0.0) == 0.0


def test_validate_predictions_with_false_negatives(test_db):
    """Test validation correctly identifies false negatives."""
    cursor = test_db.cursor()

    # Set up workflow
    cursor.execute(
        "INSERT INTO workflow_history (workflow_id, adw_id) VALUES (?, ?)", ("wf-fn", "adw-fn")
    )

    # Set up pattern
    cursor.execute(
        "INSERT INTO operation_patterns (pattern_signature, pattern_type) VALUES (?, ?)",
        ("test:pytest:backend", "test"),
    )
    pattern_id = cursor.lastrowid

    # Set up prediction (only one pattern)
    cursor.execute(
        """
        INSERT INTO pattern_predictions (workflow_id, pattern_id, pattern_signature, predicted_confidence)
        VALUES (?, ?, ?, ?)
        """,
        ("wf-fn", pattern_id, "test:pytest:backend", 80.0),
    )

    test_db.commit()

    # Validate with additional actual patterns (false negatives)
    actual_patterns = ["test:pytest:backend", "build:typecheck:backend", "format:eslint:all"]
    result = validate_predictions("wf-fn", actual_patterns, test_db)

    # Assertions
    assert result["correct"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 2
    assert result["recall"] == pytest.approx(1.0 / 3.0)

    # Check details include false negatives
    false_neg_details = [d for d in result["details"] if d["validation_type"] == "false_negative"]
    assert len(false_neg_details) == 2
