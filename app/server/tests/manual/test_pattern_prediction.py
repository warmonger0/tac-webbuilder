"""
Manual Test Script for Pattern Prediction

Validates that pattern prediction works end-to-end:
1. Predicts patterns from various test inputs
2. Stores predictions in database
3. Verifies accuracy against expected patterns

Usage:
    cd app/server
    uv run python tests/manual/test_pattern_prediction.py
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern_predictor import predict_patterns_from_input, store_predicted_patterns

# Test cases: (input, expected_patterns)
TEST_CASES = [
    (
        "Run backend pytest tests and ensure coverage >80%",
        ["test:pytest:backend"]
    ),
    (
        "Build and typecheck the backend TypeScript code",
        ["build:typecheck:backend"]
    ),
    (
        "Fix the authentication bug in login flow",
        ["fix:bug"]
    ),
    (
        "Run frontend vitest tests for all components",
        ["test:vitest:frontend"]
    ),
    (
        "Deploy the new feature to production",
        ["deploy:production"]
    ),
    (
        "Run all tests and build the project before deploying",
        ["test:pytest:backend", "test:vitest:frontend", "build:typecheck:backend", "deploy:production"]
    ),
]


def run_prediction_test():
    """Run pattern prediction tests and verify results."""
    print("\n" + "=" * 80)
    print("Pattern Prediction Test")
    print("=" * 80 + "\n")

    db_conn = sqlite3.connect("../../workflow_history.db")
    cursor = db_conn.cursor()

    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0

    for idx, (nl_input, expected_patterns) in enumerate(TEST_CASES, 1):
        print(f"\nTest Case {idx}/{total_tests}")
        print("-" * 80)
        print(f"Input: {nl_input}")
        print(f"Expected Patterns: {expected_patterns}")

        # Predict patterns
        try:
            predictions = predict_patterns_from_input(nl_input)
            predicted_patterns = [p['pattern'] for p in predictions]

            print(f"Predicted Patterns: {predicted_patterns}")

            # Check accuracy
            correct_predictions = [p for p in predicted_patterns if p in expected_patterns]
            accuracy = len(correct_predictions) / len(expected_patterns) if expected_patterns else 0.0

            print(f"Accuracy: {accuracy * 100:.0f}% ({len(correct_predictions)}/{len(expected_patterns)} correct)")

            # Display confidence scores
            for pred in predictions:
                print(f"  - {pred['pattern']}: {pred['confidence']:.2f} confidence ({pred['reasoning']})")

            # Store predictions with test request ID
            request_id = f"test_request_{idx}"
            store_predicted_patterns(request_id, predictions, db_conn)

            # Verify database storage
            cursor.execute(
                "SELECT COUNT(*) FROM pattern_predictions WHERE request_id = ?",
                (request_id,)
            )
            stored_count = cursor.fetchone()[0]

            print(f"Database: {stored_count} predictions stored for request {request_id}")

            # Check test result
            if accuracy >= 0.8:  # 80% accuracy threshold
                print("✅ PASS")
                passed_tests += 1
            else:
                print("❌ FAIL (accuracy below 80%)")
                failed_tests += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed_tests += 1

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.0f}%)")
    print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.0f}%)")

    # Query database for all test predictions
    print("\n" + "=" * 80)
    print("Database Verification")
    print("=" * 80)

    cursor.execute(
        """
        SELECT pp.request_id, p.pattern_signature, pp.confidence_score, pp.reasoning
        FROM pattern_predictions pp
        JOIN operation_patterns p ON pp.pattern_id = p.id
        WHERE pp.request_id LIKE 'test_request_%'
        ORDER BY pp.request_id, pp.id
        """
    )

    results = cursor.fetchall()
    print(f"\nTotal predictions stored: {len(results)}")

    for request_id, pattern, confidence, reasoning in results:
        print(f"  {request_id}: {pattern} ({confidence:.2f}) - {reasoning}")

    db_conn.close()

    print("\n" + "=" * 80)
    if failed_tests == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed_tests} test(s) failed")
    print("=" * 80 + "\n")

    return failed_tests == 0


if __name__ == "__main__":
    success = run_prediction_test()
    sys.exit(0 if success else 1)
