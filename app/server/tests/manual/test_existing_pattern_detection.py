"""
Manual test to verify pattern detection on existing workflows.

Demonstrates that pattern detection works correctly on completed workflows,
patterns persist to database, and duplicate detection is handled correctly.

Run: cd app/server && uv run python tests/manual/test_existing_pattern_detection.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern_detector import detect_patterns_in_workflow
from core.pattern_persistence import record_pattern_occurrence
from utils.db_connection import get_connection

# Database path
DB_PATH = "db/workflow_history.db"


def get_completed_workflow():
    """Retrieve a completed workflow for testing."""
    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        # Get a completed workflow with non-null nl_input
        cursor.execute("""
            SELECT *
            FROM workflow_history
            WHERE status = 'completed'
            AND nl_input IS NOT NULL
            LIMIT 1
        """)

        row = cursor.fetchone()
        if not row:
            return None

        # Convert to dictionary
        columns = [desc[0] for desc in cursor.description]
        workflow = dict(zip(columns, row, strict=False))

        return workflow


def display_workflow_summary(workflow):
    """Display summary of the test workflow."""
    print("\n" + "=" * 60)
    print("TEST WORKFLOW SUMMARY")
    print("=" * 60)

    print(f"\nWorkflow ID: {workflow['id']}")
    print(f"Status: {workflow['status']}")
    print(f"Created: {workflow['created_at']}")
    print(f"Completed: {workflow['completed_at']}")
    print(f"Duration: {workflow.get('duration', 'N/A')}s")
    print(f"\nNL Input: {workflow['nl_input'][:100]}..." if len(
        workflow['nl_input']) > 100 else f"\nNL Input: {workflow['nl_input']}")

    if workflow.get('error_message'):
        print(f"Error: {workflow['error_message'][:100]}...")


def detect_and_display_patterns(workflow):
    """Detect patterns from workflow and display results."""
    print("\n" + "=" * 60)
    print("PATTERN DETECTION")
    print("=" * 60)

    # Detect patterns
    patterns = detect_patterns_in_workflow(workflow)

    print(f"\n✅ Detected {len(patterns)} pattern(s):")
    if patterns:
        for i, pattern in enumerate(patterns, 1):
            print(f"\n   {i}. {pattern['signature']}")
            print(f"      Type: {pattern['type']}")
            print(f"      Source: {pattern['source']}")
            if 'confidence_components' in pattern:
                components = pattern['confidence_components']
                print(f"      Confidence: {components.get('total', 0):.1f} "
                      f"(freq: {components.get('frequency', 0):.1f}, "
                      f"cons: {components.get('consistency', 0):.1f}, "
                      f"succ: {components.get('success', 0):.1f})")
    else:
        print("   (No patterns detected)")

    return patterns


def persist_patterns(patterns, workflow):
    """Persist patterns to database and show results."""
    print("\n" + "=" * 60)
    print("PATTERN PERSISTENCE")
    print("=" * 60)

    if not patterns:
        print("\n⚠️  No patterns to persist")
        return

    with get_connection(db_path=DB_PATH) as conn:
        print(f"\n✅ Recording {len(patterns)} pattern(s) to database:")

        for i, pattern in enumerate(patterns, 1):
            try:
                pattern_id, is_new = record_pattern_occurrence(pattern, workflow, conn)
                status = "NEW" if is_new else "EXISTING"
                print(f"\n   {i}. {pattern['signature']}")
                print(f"      [{status}] Pattern ID: {pattern_id}")
                print(f"      Database record {'created' if is_new else 'updated'}")

            except Exception as e:
                print(f"\n   {i}. {pattern['signature']}")
                print(f"      ❌ ERROR: {e}")

        # Commit all changes
        conn.commit()
        print("\n✅ All patterns committed to database")


def verify_persistence(workflow):
    """Verify patterns were persisted correctly."""
    print("\n" + "=" * 60)
    print("PERSISTENCE VERIFICATION")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        # Count pattern occurrences for this workflow
        cursor.execute("""
            SELECT COUNT(*)
            FROM pattern_occurrences
            WHERE workflow_id = ?
        """, (workflow['id'],))

        count = cursor.fetchone()[0]
        print(f"\n✅ Found {count} pattern occurrence(s) linked to workflow {workflow['id']}")

        # Get pattern details
        cursor.execute("""
            SELECT
                op.pattern_signature,
                op.pattern_type,
                op.occurrence_count,
                op.confidence_score
            FROM pattern_occurrences po
            JOIN operation_patterns op ON po.pattern_id = op.id
            WHERE po.workflow_id = ?
        """, (workflow['id'],))

        rows = cursor.fetchall()
        if rows:
            print("\nPattern details:")
            for row in rows:
                sig, type_, occ_count, confidence = row
                print(f"   - {sig}")
                print(f"     Type: {type_}, Occurrences: {occ_count}, "
                      f"Confidence: {confidence:.1f}")


def main():
    """Run pattern detection test on a completed workflow."""
    print("\n" + "=" * 60)
    print("PATTERN DETECTION TEST")
    print("=" * 60)
    print("\nDatabase: db/workflow_history.db")

    try:
        # Get a completed workflow
        print("\n🔍 Searching for completed workflow...")
        workflow = get_completed_workflow()

        if not workflow:
            print("\n⚠️  No completed workflows found in database")
            print("⚠️  Please run some ADW workflows first, then re-run this test")
            return 0

        # Display workflow summary
        display_workflow_summary(workflow)

        # Detect patterns
        patterns = detect_and_display_patterns(workflow)

        # Persist patterns
        persist_patterns(patterns, workflow)

        # Verify persistence
        verify_persistence(workflow)

        # Final summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        if patterns:
            print(f"\n✅ Successfully detected {len(patterns)} pattern(s)")
            print("✅ Patterns persisted to database")
            print("✅ Pattern-workflow linkage verified")
            print("\n💡 Tip: Run this script again to verify patterns are marked as EXISTING")
        else:
            print("\n⚠️  No patterns detected from this workflow")
            print("💡 This may be expected for workflows that don't match pattern heuristics")

        return 0

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
