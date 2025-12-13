#!/usr/bin/env python3
"""
Pattern Prediction Accuracy Analytics

Queries prediction accuracy metrics from the pattern validation system.
Shows overall accuracy and per-pattern accuracy breakdown.

Usage:
    python scripts/analytics/query_prediction_accuracy.py
    python scripts/analytics/query_prediction_accuracy.py --report
    python scripts/analytics/query_prediction_accuracy.py --pattern "test:pytest:backend"
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from database import get_database_adapter  # noqa: E402


class PredictionAccuracyAnalyzer:
    """Analyzes pattern prediction accuracy from validation data."""

    def __init__(self):
        """Initialize analyzer with database connection."""
        self.adapter = get_database_adapter()

    def get_overall_accuracy(self) -> dict:
        """
        Calculate overall prediction accuracy across all patterns.

        Returns:
            Dict with overall metrics:
            {
                'total_predictions': int,
                'correct_predictions': int,
                'accuracy': float,
                'total_workflows_validated': int
            }
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Total predictions and correct count
            cursor.execute("""
                SELECT
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions
                FROM pattern_predictions
                WHERE was_correct IS NOT NULL
            """)
            row = cursor.fetchone()

            total = row['total_predictions'] if row['total_predictions'] else 0
            correct = row['correct_predictions'] if row['correct_predictions'] else 0
            accuracy = (correct / total * 100) if total > 0 else 0

            # Count validated workflows
            cursor.execute("""
                SELECT COUNT(DISTINCT request_id) as workflow_count
                FROM pattern_predictions
                WHERE was_correct IS NOT NULL
            """)
            workflow_count = cursor.fetchone()['workflow_count']

            return {
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy': accuracy,
                'total_workflows_validated': workflow_count
            }

    def get_pattern_accuracy_breakdown(self) -> list[dict]:
        """
        Get accuracy breakdown for each pattern.

        Returns:
            List of dicts with per-pattern metrics:
            [
                {
                    'pattern_signature': str,
                    'pattern_type': str,
                    'prediction_accuracy': float,
                    'total_predictions': int,
                    'correct_predictions': int
                },
                ...
            ]
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    op.pattern_signature,
                    op.pattern_type,
                    op.prediction_accuracy,
                    COUNT(pp.id) as total_predictions,
                    SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions
                FROM operation_patterns op
                LEFT JOIN pattern_predictions pp ON pp.pattern_id = op.id
                WHERE pp.was_correct IS NOT NULL
                GROUP BY op.id, op.pattern_signature, op.pattern_type, op.prediction_accuracy
                ORDER BY total_predictions DESC, op.prediction_accuracy DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'pattern_signature': row['pattern_signature'],
                    'pattern_type': row['pattern_type'],
                    'prediction_accuracy': row['prediction_accuracy'] or 0,
                    'total_predictions': row['total_predictions'],
                    'correct_predictions': row['correct_predictions'] or 0
                })

            return results

    def get_pattern_accuracy(self, pattern_signature: str) -> dict | None:
        """
        Get accuracy metrics for a specific pattern.

        Args:
            pattern_signature: Pattern signature to query

        Returns:
            Dict with pattern metrics or None if not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    op.pattern_signature,
                    op.pattern_type,
                    op.prediction_accuracy,
                    COUNT(pp.id) as total_predictions,
                    SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
                    op.occurrence_count,
                    op.confidence_score
                FROM operation_patterns op
                LEFT JOIN pattern_predictions pp ON pp.pattern_id = op.id
                WHERE op.pattern_signature = %s AND pp.was_correct IS NOT NULL
                GROUP BY op.id
            """, (pattern_signature,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'pattern_signature': row['pattern_signature'],
                'pattern_type': row['pattern_type'],
                'prediction_accuracy': row['prediction_accuracy'] or 0,
                'total_predictions': row['total_predictions'],
                'correct_predictions': row['correct_predictions'] or 0,
                'occurrence_count': row['occurrence_count'],
                'confidence_score': row['confidence_score']
            }

    def print_summary(self):
        """Print overall accuracy summary."""
        metrics = self.get_overall_accuracy()

        print("=" * 70)
        print("PATTERN PREDICTION ACCURACY SUMMARY")
        print("=" * 70)
        print(f"Total Predictions Made:      {metrics['total_predictions']}")
        print(f"Correct Predictions:         {metrics['correct_predictions']}")
        print(f"Overall Accuracy:            {metrics['accuracy']:.1f}%")
        print(f"Workflows Validated:         {metrics['total_workflows_validated']}")
        print("=" * 70)

    def print_detailed_report(self):
        """Print detailed accuracy report by pattern."""
        self.print_summary()
        print()

        patterns = self.get_pattern_accuracy_breakdown()

        if not patterns:
            print("No validated predictions found.")
            return

        print("=" * 90)
        print("ACCURACY BY PATTERN")
        print("=" * 90)
        print(f"{'Pattern':<35} {'Type':<12} {'Accuracy':<12} {'Predictions':<12}")
        print("-" * 90)

        for p in patterns:
            accuracy_pct = (p['correct_predictions'] / p['total_predictions'] * 100) \
                if p['total_predictions'] > 0 else 0

            print(
                f"{p['pattern_signature']:<35} "
                f"{p['pattern_type']:<12} "
                f"{accuracy_pct:>6.1f}%      "
                f"{p['correct_predictions']}/{p['total_predictions']}"
            )

        print("=" * 90)

    def print_pattern_details(self, pattern_signature: str):
        """Print detailed metrics for a specific pattern."""
        metrics = self.get_pattern_accuracy(pattern_signature)

        if not metrics:
            print(f"Pattern not found or has no validated predictions: {pattern_signature}")
            return

        accuracy_pct = (metrics['correct_predictions'] / metrics['total_predictions'] * 100) \
            if metrics['total_predictions'] > 0 else 0

        print("=" * 70)
        print(f"PATTERN: {metrics['pattern_signature']}")
        print("=" * 70)
        print(f"Type:                {metrics['pattern_type']}")
        print(f"Prediction Accuracy: {accuracy_pct:.1f}%")
        print(f"Total Predictions:   {metrics['total_predictions']}")
        print(f"Correct Predictions: {metrics['correct_predictions']}")
        print(f"Occurrence Count:    {metrics['occurrence_count']}")
        print(f"Confidence Score:    {metrics['confidence_score']:.1f}")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query pattern prediction accuracy metrics"
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Show detailed accuracy breakdown by pattern'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        help='Show detailed metrics for a specific pattern signature'
    )

    args = parser.parse_args()
    analyzer = PredictionAccuracyAnalyzer()

    if args.pattern:
        analyzer.print_pattern_details(args.pattern)
    elif args.report:
        analyzer.print_detailed_report()
    else:
        analyzer.print_summary()


if __name__ == '__main__':
    main()
