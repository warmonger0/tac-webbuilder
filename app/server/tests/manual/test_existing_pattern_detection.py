#!/usr/bin/env python3
"""
Test Pattern Detection on Existing Completed Workflows

This script:
1. Fetches a completed workflow from database
2. Runs pattern detection on it
3. Persists patterns to database
4. Verifies patterns were saved correctly

Run from app/server/ directory:
    cd app/server && uv run python tests/manual/test_existing_pattern_detection.py
"""

import sqlite3
import sys
from pathlib import Path

# Add app/server to Python path so we can import core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern_detector import detect_patterns_in_workflow, extract_pattern_characteristics
from core.pattern_persistence import record_pattern_occurrence


def main():
    print("=" * 80)
    print("PHASE 1: Verify Post-Workflow Pattern Collection")
    print("=" * 80)
    print()

    # Connect to database
    # Path: tests/manual/script.py -> tests/manual -> tests -> server -> db/database.db
    db_path = Path(__file__).parent.parent.parent / "db" / "database.db"
    print(f"📂 Connecting to database: {db_path}")

    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()

    # Fetch one completed workflow
    print("\n🔍 Fetching completed workflow from database...")
    cursor.execute("""
        SELECT *
        FROM workflow_history
        WHERE status = 'completed'
          AND nl_input IS NOT NULL
        ORDER BY end_time DESC
        LIMIT 1
    """)

    workflow_row = cursor.fetchone()

    if not workflow_row:
        print("❌ No completed workflows found with nl_input")
        conn.close()
        return 1

    # Convert Row to dictionary
    workflow = dict(workflow_row)

    print("✅ Found workflow:")
    print(f"   - Workflow ID: {workflow.get('workflow_id', 'N/A')}")
    print(f"   - ADW ID: {workflow.get('adw_id', 'N/A')}")
    print(f"   - NL Input: {workflow.get('nl_input', 'N/A')[:80]}...")
    print(f"   - Status: {workflow.get('status', 'N/A')}")
    print(f"   - Duration: {workflow.get('duration_seconds', 'N/A')}s")
    print()

    # Detect patterns
    print("🔬 Detecting patterns in workflow...")
    patterns = detect_patterns_in_workflow(workflow)

    print(f"\n✅ Detected {len(patterns)} pattern(s):")
    for i, pattern in enumerate(patterns, 1):
        print(f"   {i}. {pattern}")

    if not patterns:
        print("⚠️  No patterns detected. This workflow may not match any known patterns.")
        conn.close()
        return 0

    print()

    # Extract characteristics
    characteristics = extract_pattern_characteristics(workflow)
    print("📊 Pattern Characteristics:")
    print(f"   - Input Length: {characteristics.get('input_length', 0)} chars")
    print(f"   - Keywords: {', '.join(characteristics.get('keywords', []))}")
    print(f"   - Files Mentioned: {', '.join(characteristics.get('files_mentioned', []))}")
    print(f"   - Duration Range: {characteristics.get('duration_range', 'N/A')}")
    print(f"   - Complexity: {characteristics.get('complexity', 'N/A')}")
    print(f"   - Error Count: {characteristics.get('error_count', 0)}")
    print()

    # Record patterns in database
    print("💾 Persisting patterns to database...")
    for pattern in patterns:
        pattern_id, is_new = record_pattern_occurrence(pattern, workflow, conn)

        if pattern_id:
            status = "🆕 NEW" if is_new else "♻️  EXISTING"
            print(f"   [{status}] Pattern ID: {pattern_id} - {pattern}")
        else:
            print(f"   ❌ Failed to record pattern: {pattern}")

    print()

    # Verify patterns exist in database
    print("🔍 Verifying patterns in database...")
    cursor.execute("""
        SELECT
            p.id,
            p.pattern_signature,
            p.pattern_type,
            p.occurrence_count,
            p.confidence_score,
            p.automation_status,
            p.first_detected,
            p.last_seen
        FROM operation_patterns p
        WHERE p.pattern_signature IN ({})
    """.format(','.join('?' * len(patterns))), patterns)

    db_patterns = cursor.fetchall()

    print(f"\n✅ Found {len(db_patterns)} pattern(s) in database:")
    for row in db_patterns:
        p = dict(row)
        print(f"\n   Pattern ID: {p['id']}")
        print(f"   Signature: {p['pattern_signature']}")
        print(f"   Type: {p['pattern_type']}")
        print(f"   Occurrence Count: {p['occurrence_count']}")
        print(f"   Confidence Score: {p['confidence_score']:.1f}%")
        print(f"   Automation Status: {p['automation_status']}")
        print(f"   First Detected: {p['first_detected']}")
        print(f"   Last Seen: {p['last_seen']}")

    # Check pattern occurrences
    print("\n🔗 Checking pattern_occurrences links...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM pattern_occurrences
        WHERE workflow_id = ?
    """, (workflow.get('workflow_id'),))

    occurrence_count = cursor.fetchone()[0]
    print(f"   ✅ Found {occurrence_count} pattern occurrence(s) linked to this workflow")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ PHASE 1 VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Run this script on all 43 completed workflows")
    print("  2. Query pattern statistics using query_pattern_stats.py")
    print("  3. Document findings in docs/pattern_recognition/PHASE_1_VERIFICATION.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
