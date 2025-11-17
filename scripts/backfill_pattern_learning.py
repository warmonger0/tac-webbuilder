#!/usr/bin/env python3
"""
Backfill pattern learning with historical workflow data.

This script analyzes all existing workflows in the database and
populates the operation_patterns and pattern_occurrences tables.

Usage:
    python scripts/backfill_pattern_learning.py [--dry-run] [--limit N]

Options:
    --dry-run    Show what would be done without making changes
    --limit N    Only process first N workflows (for testing)
"""

import sys
import sqlite3
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_persistence import process_and_persist_workflow


def backfill_patterns(dry_run: bool = False, limit: int = None):
    """
    Analyze all historical workflows for patterns.

    Args:
        dry_run: If True, show what would be done without persisting
        limit: Maximum number of workflows to process (None = all)
    """
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    print(f"📚 Backfilling pattern learning from: {db_path}")
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all completed/failed workflows
    query = """
        SELECT * FROM workflow_history
        WHERE status IN ('completed', 'failed')
        ORDER BY created_at ASC
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    workflows = [dict(row) for row in cursor.fetchall()]
    total = len(workflows)

    print(f"Found {total} workflows to analyze")
    print()

    patterns_detected = 0
    new_patterns = 0
    processed = 0
    errors = 0

    for i, workflow in enumerate(workflows, 1):
        # Parse JSON fields if needed
        if workflow.get('cost_breakdown') and isinstance(workflow['cost_breakdown'], str):
            import json
            try:
                workflow['cost_breakdown'] = json.loads(workflow['cost_breakdown'])
            except:
                pass

        try:
            if dry_run:
                # Just detect, don't persist
                from core.pattern_detector import process_workflow_for_patterns
                result = process_workflow_for_patterns(workflow)
                result_summary = {
                    'patterns_detected': len(result['patterns']),
                    'new_patterns': 0,  # Can't determine in dry-run
                    'pattern_ids': []
                }
            else:
                # Detect and persist
                result_summary = process_and_persist_workflow(workflow, conn)

            patterns_detected += result_summary['patterns_detected']
            new_patterns += result_summary.get('new_patterns', 0)
            processed += 1

            if result_summary['patterns_detected'] > 0:
                status = "🔍" if dry_run else "✓"
                print(
                    f"[{i}/{total}] {status} {workflow['adw_id']}: "
                    f"{result_summary['patterns_detected']} pattern(s)"
                )

        except Exception as e:
            errors += 1
            print(f"[{i}/{total}] ✗ {workflow['adw_id']}: Error: {e}")

    if not dry_run:
        conn.close()

    print()
    print("=" * 60)
    print(f"{'🔍 DRY RUN COMPLETE' if dry_run else '✅ BACKFILL COMPLETE'}")
    print(f"   Workflows processed: {processed}/{total}")
    print(f"   Patterns detected: {patterns_detected}")
    if not dry_run:
        print(f"   New patterns created: {new_patterns}")
    print(f"   Errors: {errors}")
    print("=" * 60)

    if not dry_run:
        # Show top patterns
        print()
        print("Top 10 patterns by occurrence:")
        print()

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pattern_signature,
                occurrence_count,
                confidence_score,
                avg_cost_with_llm,
                potential_monthly_savings,
                automation_status
            FROM operation_patterns
            ORDER BY occurrence_count DESC
            LIMIT 10
        """)

        for i, row in enumerate(cursor.fetchall(), 1):
            print(
                f"{i:2}. {row['pattern_signature']:30} "
                f"| Count: {row['occurrence_count']:3} "
                f"| Confidence: {row['confidence_score']:5.1f}% "
                f"| Savings: ${row['potential_monthly_savings'] or 0:6.2f}/mo "
                f"| Status: {row['automation_status']}"
            )

        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill pattern learning with historical workflow data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Only process first N workflows (for testing)"
    )

    args = parser.parse_args()
    backfill_patterns(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
