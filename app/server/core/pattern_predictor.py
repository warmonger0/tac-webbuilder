"""
Pattern Predictor - Predicts patterns from nl_input before workflow execution.

Differs from pattern_detector.py which analyzes completed workflows.
This module predicts patterns from user input alone.
"""
import logging
from typing import Any

from core.pattern_logging import PatternOperationContext, log_pattern_event, log_pattern_performance

logger = logging.getLogger(__name__)


@log_pattern_performance
def predict_patterns_from_input(
    nl_input: str,
    project_path: str | None = None
) -> list[dict[str, Any]]:
    """
    Predict patterns from natural language input before workflow starts.

    Args:
        nl_input: User's natural language request
        project_path: Optional project context

    Returns:
        List of predicted patterns with confidence scores

    Example:
        >>> predict_patterns_from_input("Run backend tests with pytest")
        [{'pattern': 'test:pytest:backend', 'confidence': 0.85, 'reasoning': 'explicit pytest mention'}]
    """
    with PatternOperationContext(
        "pattern_prediction",
        {"input_length": len(nl_input), "input_preview": nl_input[:100]}
    ):
        predictions = []
        nl_lower = nl_input.lower()

        # Test patterns
        test_keywords = ['test', 'pytest', 'vitest']
        if any(kw in nl_lower for kw in test_keywords):
            log_pattern_event(
                "pattern_keyword_match",
                {"pattern_type": "test", "matched_keywords": [k for k in test_keywords if k in nl_lower]}
            )

            if 'pytest' in nl_lower or 'backend' in nl_lower or 'api' in nl_lower:
                predictions.append({
                    'pattern': 'test:pytest:backend',
                    'confidence': 0.85 if 'pytest' in nl_lower else 0.65,
                    'reasoning': 'Backend test keywords detected'
                })
            if 'vitest' in nl_lower or 'frontend' in nl_lower or 'ui' in nl_lower or 'component' in nl_lower:
                predictions.append({
                    'pattern': 'test:vitest:frontend',
                    'confidence': 0.85 if 'vitest' in nl_lower else 0.65,
                    'reasoning': 'Frontend test keywords detected'
                })

        # Build patterns
        build_keywords = ['build', 'compile', 'typecheck', 'tsc']
        if any(kw in nl_lower for kw in build_keywords):
            log_pattern_event(
                "pattern_keyword_match",
                {"pattern_type": "build", "matched_keywords": [k for k in build_keywords if k in nl_lower]}
            )
            predictions.append({
                'pattern': 'build:typecheck:backend',
                'confidence': 0.75,
                'reasoning': 'Build operation keywords detected'
            })

        # Deploy patterns
        deploy_keywords = ['deploy', 'ship', 'release', 'publish']
        if any(kw in nl_lower for kw in deploy_keywords):
            log_pattern_event(
                "pattern_keyword_match",
                {"pattern_type": "deploy", "matched_keywords": [k for k in deploy_keywords if k in nl_lower]}
            )
            predictions.append({
                'pattern': 'deploy:production',
                'confidence': 0.70,
                'reasoning': 'Deployment keywords detected'
            })

        # Fix/patch patterns
        fix_keywords = ['fix', 'bug', 'patch', 'hotfix']
        if any(kw in nl_lower for kw in fix_keywords):
            log_pattern_event(
                "pattern_keyword_match",
                {"pattern_type": "fix", "matched_keywords": [k for k in fix_keywords if k in nl_lower]}
            )
            predictions.append({
                'pattern': 'fix:bug',
                'confidence': 0.60,
                'reasoning': 'Bug fix keywords detected'
            })

        # Log final predictions
        log_pattern_event(
            "predictions_generated",
            {
                "prediction_count": len(predictions),
                "patterns": [p['pattern'] for p in predictions],
                "avg_confidence": sum(p['confidence'] for p in predictions) / len(predictions) if predictions else 0.0
            }
        )

        logger.info(f"[Predictor] Predicted {len(predictions)} patterns from input")
        for pred in predictions:
            logger.debug(f"  - {pred['pattern']} (confidence: {pred['confidence']:.2f})")

        return predictions


def store_predicted_patterns(
    request_id: str,
    predictions: list[dict],
    db_connection
) -> None:
    """
    Store predicted patterns for later validation.

    Creates entries in operation_patterns with 'predicted' status.
    After workflow completes, we can compare predicted vs actual.
    """
    cursor = db_connection.cursor()

    for pred in predictions:
        # Check if pattern exists
        cursor.execute(
            "SELECT id FROM operation_patterns WHERE pattern_signature = ?",
            (pred['pattern'],)
        )
        result = cursor.fetchone()

        if result:
            pattern_id = result[0]
            # Update prediction count
            cursor.execute(
                """
                UPDATE operation_patterns
                SET prediction_count = prediction_count + 1,
                    last_predicted = datetime('now')
                WHERE id = ?
                """,
                (pattern_id,)
            )
        else:
            # Create new predicted pattern
            cursor.execute(
                """
                INSERT INTO operation_patterns (
                    pattern_signature,
                    pattern_type,
                    automation_status,
                    prediction_count,
                    last_predicted
                ) VALUES (?, ?, 'predicted', 1, datetime('now'))
                """,
                (pred['pattern'], pred['pattern'].split(':')[0])
            )
            pattern_id = cursor.lastrowid

        # Store prediction metadata
        cursor.execute(
            """
            INSERT INTO pattern_predictions (
                request_id,
                pattern_id,
                confidence_score,
                reasoning
            ) VALUES (?, ?, ?, ?)
            """,
            (request_id, pattern_id, pred['confidence'], pred['reasoning'])
        )

    db_connection.commit()
    logger.info(f"[Predictor] Stored {len(predictions)} predicted patterns for request {request_id}")
