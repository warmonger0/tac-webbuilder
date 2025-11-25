"""
Pattern Validator - Validates predictions against actual workflow outcomes

This module closes the loop on pattern learning by comparing predicted patterns
against actual patterns detected after workflow completion. It calculates accuracy
metrics and updates pattern confidence scores based on validation results.
"""

import logging
import sqlite3
from typing import TypedDict

logger = logging.getLogger(__name__)


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================


class ValidationResult(TypedDict):
    """Results from validating pattern predictions."""

    total_predicted: int
    total_actual: int
    correct: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    details: list[dict]


class ValidationMetrics(TypedDict):
    """Accuracy metrics for a pattern."""

    pattern_id: int
    pattern_signature: str
    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float


# ============================================================================
# CORE VALIDATION FUNCTIONS
# ============================================================================


def validate_predictions(
    workflow_id: str, actual_patterns: list[str], db_connection: sqlite3.Connection
) -> ValidationResult:
    """
    Compare predicted patterns against actual patterns from completed workflow.

    This function performs the core validation loop:
    1. Fetch all predictions for this workflow
    2. Compare predicted vs actual patterns
    3. Calculate accuracy metrics (precision, recall, F1)
    4. Update validation results in database

    Args:
        workflow_id: Workflow ID to validate predictions for
        actual_patterns: List of pattern signatures detected from completed workflow
        db_connection: Database connection

    Returns:
        ValidationResult with detailed accuracy metrics

    Example:
        >>> result = validate_predictions(
        ...     workflow_id="wf-123",
        ...     actual_patterns=["test:pytest:backend", "build:typecheck:backend"],
        ...     db_connection=conn
        ... )
        >>> result['accuracy']
        0.75  # 75% accuracy
    """
    cursor = db_connection.cursor()

    # Fetch predictions for this workflow
    cursor.execute(
        """
        SELECT pp.id, pp.pattern_id, pp.pattern_signature, pp.predicted_confidence
        FROM pattern_predictions pp
        WHERE pp.workflow_id = ?
        """,
        (workflow_id,),
    )

    predictions = cursor.fetchall()

    # Initialize result structure
    result: ValidationResult = {
        "total_predicted": len(predictions),
        "total_actual": len(actual_patterns),
        "correct": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "details": [],
    }

    # Edge case: no predictions to validate
    if not predictions:
        logger.debug(f"[Validator] No predictions found for workflow {workflow_id}")
        # Record false negatives for unpredicted actual patterns
        result["false_negatives"] = len(actual_patterns)
        return result

    # Extract predicted pattern signatures
    predicted_patterns = [p[2] for p in predictions]

    # Validate each prediction
    for pred_id, _pattern_id, pattern_sig, confidence in predictions:
        was_correct = pattern_sig in actual_patterns

        # Update prediction record with validation result
        cursor.execute(
            """
            UPDATE pattern_predictions
            SET was_correct = ?, validated_at = datetime('now')
            WHERE id = ?
            """,
            (1 if was_correct else 0, pred_id),
        )

        # Add to details
        result["details"].append(
            {
                "pattern": pattern_sig,
                "predicted_confidence": confidence,
                "was_correct": was_correct,
                "validation_type": "true_positive" if was_correct else "false_positive",
            }
        )

        if was_correct:
            result["correct"] += 1
        else:
            result["false_positives"] += 1

    # Check for false negatives (actual patterns we didn't predict)
    for actual in actual_patterns:
        if actual not in predicted_patterns:
            result["false_negatives"] += 1
            result["details"].append(
                {
                    "pattern": actual,
                    "predicted_confidence": 0.0,
                    "was_correct": False,
                    "validation_type": "false_negative",
                }
            )

    # Calculate metrics
    result["accuracy"] = _calculate_accuracy(result)
    result["precision"] = _calculate_precision(result)
    result["recall"] = _calculate_recall(result)
    result["f1_score"] = _calculate_f1_score(result["precision"], result["recall"])

    # Commit validation updates
    db_connection.commit()

    logger.info(
        f"[Validator] Workflow {workflow_id}: "
        f"Predicted {result['total_predicted']}, "
        f"Actual {result['total_actual']}, "
        f"Correct {result['correct']}, "
        f"Accuracy {result['accuracy']:.2%}"
    )

    return result


def _calculate_accuracy(result: ValidationResult) -> float:
    """
    Calculate overall accuracy: correct / total.

    Args:
        result: Validation result dictionary

    Returns:
        Accuracy score from 0.0 to 1.0
    """
    total = result["total_predicted"]
    if total == 0:
        return 0.0
    return result["correct"] / total


def _calculate_precision(result: ValidationResult) -> float:
    """
    Calculate precision: true_positives / (true_positives + false_positives).

    Precision measures "when we predict a pattern, how often are we correct?"

    Args:
        result: Validation result dictionary

    Returns:
        Precision score from 0.0 to 1.0
    """
    true_positives = result["correct"]
    false_positives = result["false_positives"]

    denominator = true_positives + false_positives
    if denominator == 0:
        return 0.0

    return true_positives / denominator


def _calculate_recall(result: ValidationResult) -> float:
    """
    Calculate recall: true_positives / (true_positives + false_negatives).

    Recall measures "of all actual patterns, how many did we predict?"

    Args:
        result: Validation result dictionary

    Returns:
        Recall score from 0.0 to 1.0
    """
    true_positives = result["correct"]
    false_negatives = result["false_negatives"]

    denominator = true_positives + false_negatives
    if denominator == 0:
        return 0.0

    return true_positives / denominator


def _calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score: 2 * (precision * recall) / (precision + recall).

    F1 score is the harmonic mean of precision and recall.

    Args:
        precision: Precision score
        recall: Recall score

    Returns:
        F1 score from 0.0 to 1.0
    """
    denominator = precision + recall
    if denominator == 0:
        return 0.0

    return 2 * (precision * recall) / denominator


# ============================================================================
# PATTERN ACCURACY UPDATES
# ============================================================================


def update_pattern_accuracy(pattern_id: int, db_connection: sqlite3.Connection) -> float:
    """
    Recalculate prediction accuracy for a pattern based on validation history.

    This function queries all validated predictions for a pattern and calculates
    a running average of correctness.

    Args:
        pattern_id: ID of pattern to update
        db_connection: Database connection

    Returns:
        Updated accuracy score from 0.0 to 1.0
    """
    cursor = db_connection.cursor()

    # Calculate accuracy from validation history
    cursor.execute(
        """
        SELECT AVG(CAST(was_correct AS REAL))
        FROM pattern_predictions
        WHERE pattern_id = ? AND was_correct IS NOT NULL
        """,
        (pattern_id,),
    )

    row = cursor.fetchone()
    accuracy = row[0] if row and row[0] is not None else None

    if accuracy is None:
        logger.debug(f"[Validator] No validated predictions for pattern {pattern_id}")
        return 0.0

    # Update pattern record
    cursor.execute(
        """
        UPDATE operation_patterns
        SET prediction_accuracy = ?
        WHERE id = ?
        """,
        (accuracy, pattern_id),
    )

    db_connection.commit()

    logger.debug(f"[Validator] Updated pattern {pattern_id} accuracy: {accuracy:.2%}")

    return accuracy


# ============================================================================
# METRICS QUERIES
# ============================================================================


def get_validation_metrics(
    pattern_id: int, db_connection: sqlite3.Connection
) -> ValidationMetrics | None:
    """
    Get validation metrics for a specific pattern.

    Args:
        pattern_id: Pattern ID to get metrics for
        db_connection: Database connection

    Returns:
        ValidationMetrics dictionary or None if pattern not found
    """
    cursor = db_connection.cursor()

    # Get pattern info and counts
    cursor.execute(
        """
        SELECT
            p.id,
            p.pattern_signature,
            COUNT(CASE WHEN pp.was_correct IS NOT NULL THEN 1 END) as total_predictions,
            COUNT(CASE WHEN pp.was_correct = 1 THEN 1 END) as correct_predictions,
            COUNT(CASE WHEN pp.was_correct = 0 THEN 1 END) as incorrect_predictions
        FROM operation_patterns p
        LEFT JOIN pattern_predictions pp ON pp.pattern_id = p.id
        WHERE p.id = ?
        GROUP BY p.id, p.pattern_signature
        """,
        (pattern_id,),
    )

    row = cursor.fetchone()
    if not row:
        return None

    pid, pattern_sig, total, correct, incorrect = row

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0.0

    # For precision/recall/F1, we need more detailed data
    # These are aggregate metrics across all validations
    cursor.execute(
        """
        SELECT
            COUNT(CASE WHEN was_correct = 1 THEN 1 END) as true_positives,
            COUNT(CASE WHEN was_correct = 0 THEN 1 END) as false_positives
        FROM pattern_predictions
        WHERE pattern_id = ? AND was_correct IS NOT NULL
        """,
        (pattern_id,),
    )

    tp_fp_row = cursor.fetchone()
    true_positives = tp_fp_row[0] if tp_fp_row else 0
    false_positives = tp_fp_row[1] if tp_fp_row else 0

    # Calculate precision
    precision_denom = true_positives + false_positives
    precision = true_positives / precision_denom if precision_denom > 0 else 0.0

    # For recall, we'd need to know about false negatives across all workflows
    # For now, use accuracy as a proxy (conservative estimate)
    recall = accuracy

    # Calculate F1
    f1 = _calculate_f1_score(precision, recall)

    return ValidationMetrics(
        pattern_id=pid,
        pattern_signature=pattern_sig,
        total_predictions=total,
        correct_predictions=correct,
        incorrect_predictions=incorrect,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1,
    )


def get_validation_summary(db_connection: sqlite3.Connection) -> dict:
    """
    Get overall validation statistics across all patterns.

    Args:
        db_connection: Database connection

    Returns:
        Dictionary with summary statistics:
        {
            'total_patterns': 15,
            'patterns_with_predictions': 10,
            'total_predictions': 100,
            'total_validations': 85,
            'overall_accuracy': 0.75,
            'patterns_above_70_percent': 8,
            'patterns_above_90_percent': 3
        }
    """
    cursor = db_connection.cursor()

    # Overall counts
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT p.id) as total_patterns,
            COUNT(DISTINCT CASE WHEN pp.id IS NOT NULL THEN p.id END) as patterns_with_predictions,
            COUNT(pp.id) as total_predictions,
            COUNT(CASE WHEN pp.was_correct IS NOT NULL THEN 1 END) as total_validations,
            AVG(CASE WHEN pp.was_correct IS NOT NULL THEN CAST(pp.was_correct AS REAL) END) as overall_accuracy
        FROM operation_patterns p
        LEFT JOIN pattern_predictions pp ON pp.pattern_id = p.id
        """
    )

    row = cursor.fetchone()
    total_patterns, patterns_with_preds, total_preds, total_vals, overall_acc = row

    # Patterns above accuracy thresholds
    cursor.execute(
        """
        SELECT
            COUNT(CASE WHEN prediction_accuracy >= 0.70 THEN 1 END) as above_70,
            COUNT(CASE WHEN prediction_accuracy >= 0.90 THEN 1 END) as above_90
        FROM operation_patterns
        WHERE prediction_accuracy IS NOT NULL
        """
    )

    threshold_row = cursor.fetchone()
    above_70, above_90 = threshold_row if threshold_row else (0, 0)

    return {
        "total_patterns": total_patterns,
        "patterns_with_predictions": patterns_with_preds,
        "total_predictions": total_preds,
        "total_validations": total_vals,
        "overall_accuracy": overall_acc if overall_acc is not None else 0.0,
        "patterns_above_70_percent": above_70,
        "patterns_above_90_percent": above_90,
    }
