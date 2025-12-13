"""Pattern prediction validation system.

Compares predicted patterns against actual detected patterns
to measure prediction accuracy and close the feedback loop.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of pattern prediction validation.

    Attributes:
        total_predicted: Number of patterns predicted
        total_actual: Number of patterns actually detected
        correct: Number of correct predictions (true positives)
        false_positives: Predicted but not actual
        false_negatives: Actual but not predicted
        accuracy: Percentage correct (0.0 to 1.0)
        details: Pattern-level results {signature: was_correct}
    """
    total_predicted: int
    total_actual: int
    correct: int
    false_positives: int
    false_negatives: int
    accuracy: float
    details: dict[str, bool]


def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: list[str],
    db_connection
) -> ValidationResult:
    """Compare predicted patterns against actual patterns.

    Args:
        request_id: Request ID that triggered workflow
        workflow_id: Workflow that completed
        actual_patterns: List of pattern signatures actually detected
        db_connection: Database connection

    Returns:
        ValidationResult with accuracy metrics
    """
    cursor = db_connection.cursor()

    # 1. Fetch predictions for this request
    cursor.execute("""
        SELECT pp.id, op.pattern_signature, pp.confidence_score
        FROM pattern_predictions pp
        JOIN operation_patterns op ON pp.pattern_id = op.id
        WHERE pp.request_id = %s
    """, (request_id,))

    predictions = cursor.fetchall()

    # Handle no predictions case
    if not predictions:
        return ValidationResult(
            total_predicted=0,
            total_actual=len(actual_patterns),
            correct=0,
            false_positives=0,
            false_negatives=len(actual_patterns),
            accuracy=0.0,
            details={}
        )

    # 2. Build sets for comparison
    predicted_map = {row['pattern_signature']: row['id'] for row in predictions}  # {signature: pred_id}
    predicted_set: set[str] = set(predicted_map.keys())
    actual_set: set[str] = set(actual_patterns)

    # 3. Calculate metrics
    true_positives = predicted_set & actual_set
    false_positives = predicted_set - actual_set
    false_negatives = actual_set - predicted_set

    correct_count = len(true_positives)
    accuracy = correct_count / len(predicted_set) if predicted_set else 0.0

    # 4. Update pattern_predictions.was_correct
    details = {}
    for signature, pred_id in predicted_map.items():
        was_correct = 1 if signature in actual_set else 0
        details[signature] = bool(was_correct)

        cursor.execute("""
            UPDATE pattern_predictions
            SET was_correct = %s, validated_at = NOW()
            WHERE id = %s
        """, (was_correct, pred_id))

    # 5. Update operation_patterns.prediction_accuracy
    # Recalculate accuracy for each pattern based on all validations
    affected_patterns = predicted_set | actual_set
    for pattern_sig in affected_patterns:
        cursor.execute("""
            UPDATE operation_patterns
            SET prediction_accuracy = (
                SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
                FROM pattern_predictions
                WHERE pattern_id = operation_patterns.id
                  AND was_correct IS NOT NULL
            )
            WHERE pattern_signature = %s
        """, (pattern_sig,))

    db_connection.commit()

    # 6. Return results
    return ValidationResult(
        total_predicted=len(predicted_set),
        total_actual=len(actual_set),
        correct=correct_count,
        false_positives=len(false_positives),
        false_negatives=len(false_negatives),
        accuracy=accuracy,
        details=details
    )
