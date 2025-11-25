#!/usr/bin/env python3
"""
Batch Process Pattern Detection on All Completed Workflows

This script:
1. Fetches all completed workflows with nl_input
2. Runs pattern detection on each one
3. Persists patterns to database
4. Reports statistics

Run from app/server/ directory:
    cd app/server && uv run python tests/manual/batch_process_patterns.py
"""

import sys
import sqlite3
from pathlib import Path

# Add app/server to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern_persistence import batch_process_workflows


def main():
    print("=" * 80)
    print("BATCH PATTERN DETECTION - ALL COMPLETED WORKFLOWS")
    print("=" * 80)
    print()

    # Connect to database
    db_path = Path(__file__).parent.parent.parent / "db" / "database.db"
    print(f"📂 Connecting to database: {db_path}")

    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all completed workflows with nl_input
    print("\n🔍 Fetching completed workflows with nl_input...")
    cursor.execute("""
        SELECT *
        FROM workflow_history
        WHERE status = 'completed'
          AND nl_input IS NOT NULL
        ORDER BY end_time DESC
    """)

    workflows = [dict(row) for row in cursor.fetchall()]

    print(f"✅ Found {len(workflows)} workflow(s) to process")

    if not workflows:
        print("⚠️  No workflows to process")
        conn.close()
        return 0

    print()
    print("-" * 80)

    # Display workflow summary
    print("\nWorkflows to Process:")
    for i, wf in enumerate(workflows, 1):
        print(f"   {i}. ADW: {wf.get('adw_id', 'N/A')[:20]:<20} | "
              f"NL: {wf.get('nl_input', 'N/A')[:40]}... | "
              f"Duration: {wf.get('duration_seconds', 0)}s")

    print()
    print("-" * 80)
    print()

    # Batch process all workflows
    print("🔬 Processing workflows for patterns...")
    print()

    result = batch_process_workflows(workflows, conn)

    # Display results
    print("\n" + "=" * 80)
    print("📊 BATCH PROCESSING RESULTS")
    print("=" * 80)
    print()
    print(f"   Total Workflows: {result['total_workflows']}")
    print(f"   Successfully Processed: {result['processed']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Total Patterns Detected: {result['total_patterns']}")
    print(f"   New Patterns Discovered: {result['new_patterns']}")

    # Query final pattern statistics
    print("\n" + "=" * 80)
    print("📈 PATTERN STATISTICS AFTER BATCH PROCESSING")
    print("=" * 80)

    cursor.execute("""
        SELECT
            pattern_signature,
            pattern_type,
            occurrence_count,
            confidence_score,
            automation_status
        FROM operation_patterns
        ORDER BY occurrence_count DESC
    """)

    patterns = cursor.fetchall()

    print(f"\nTotal Unique Patterns: {len(patterns)}")
    print()

    if patterns:
        print(f"{'Pattern':<40} {'Type':<10} {'Count':<8} {'Confidence':<12}")
        print("-" * 75)

        for row in patterns:
            print(f"{row['pattern_signature']:<40} "
                  f"{row['pattern_type']:<10} "
                  f"{row['occurrence_count']:<8} "
                  f"{row['confidence_score']:<11.1f}%")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("  1. Run query_pattern_stats.py to see detailed statistics")
    print("  2. Document findings in docs/pattern_recognition/PHASE_1_VERIFICATION.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
