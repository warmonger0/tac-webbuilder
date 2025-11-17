# Phase 1.4: Backfill & Validation - Implementation Guide

**Parent:** Phase 1 - Pattern Detection Engine
**Depends On:** Phase 1.1, Phase 1.2, Phase 1.3
**Duration:** 1 day
**Priority:** HIGH
**Status:** Ready to implement

---

## Overview

Create tooling to backfill pattern learning with historical workflow data and validate that the entire pattern detection system is working correctly. This phase focuses on deployment, verification, and documentation.

---

## Goals

1. ✅ Backfill historical workflows to seed pattern database
2. ✅ Validate pattern detection accuracy
3. ✅ Verify database integrity and statistics
4. ✅ Create query utilities for pattern analysis
5. ✅ Document pattern detection system

---

## Implementation

### File: `scripts/backfill_pattern_learning.py`

Standalone script to analyze all historical workflows:

```python
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
```

**Make executable:**
```bash
chmod +x scripts/backfill_pattern_learning.py
```

---

### File: `scripts/analyze_patterns.py`

Query utility for pattern analysis:

```python
#!/usr/bin/env python3
"""
Analyze detected patterns and generate insights.

Usage:
    python scripts/analyze_patterns.py [command]

Commands:
    summary      Show pattern detection summary
    top          Show top patterns by occurrence
    high-value   Show patterns with highest savings potential
    recent       Show recently detected patterns
    details ID   Show detailed info for a specific pattern
"""

import sys
import sqlite3
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def show_summary():
    """Show overall pattern detection summary."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Total patterns
    cursor.execute("SELECT COUNT(*) FROM operation_patterns")
    total_patterns = cursor.fetchone()[0]

    # Total occurrences
    cursor.execute("SELECT SUM(occurrence_count) FROM operation_patterns")
    total_occurrences = cursor.fetchone()[0] or 0

    # Patterns by status
    cursor.execute("""
        SELECT automation_status, COUNT(*) as count
        FROM operation_patterns
        GROUP BY automation_status
    """)
    status_counts = dict(cursor.fetchall())

    # Total potential savings
    cursor.execute("SELECT SUM(potential_monthly_savings) FROM operation_patterns")
    total_savings = cursor.fetchone()[0] or 0

    conn.close()

    print("=" * 60)
    print("PATTERN DETECTION SUMMARY")
    print("=" * 60)
    print(f"Total Patterns:       {total_patterns}")
    print(f"Total Occurrences:    {total_occurrences}")
    print(f"Potential Savings:    ${total_savings:.2f}/month")
    print()
    print("Patterns by Status:")
    for status, count in status_counts.items():
        print(f"  {status:15} {count:3}")
    print("=" * 60)


def show_top_patterns(limit: int = 10):
    """Show top patterns by occurrence."""
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
        LIMIT ?
    """, (limit,))

    print("=" * 80)
    print(f"TOP {limit} PATTERNS BY OCCURRENCE")
    print("=" * 80)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(
            f"{i:2}. {row['pattern_signature']:30} "
            f"| Count: {row['occurrence_count']:3} "
            f"| Confidence: {row['confidence_score']:5.1f}% "
            f"| Savings: ${row['potential_monthly_savings'] or 0:6.2f}/mo"
        )

    print("=" * 80)
    conn.close()


def show_high_value_patterns(limit: int = 10):
    """Show patterns with highest savings potential."""
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
        WHERE potential_monthly_savings > 0
        ORDER BY potential_monthly_savings DESC
        LIMIT ?
    """, (limit,))

    print("=" * 80)
    print(f"TOP {limit} PATTERNS BY SAVINGS POTENTIAL")
    print("=" * 80)

    for i, row in enumerate(cursor.fetchall(), 1):
        savings_per_use = (row['avg_cost_with_llm'] or 0) * 0.95
        print(
            f"{i:2}. {row['pattern_signature']:30} "
            f"| Savings: ${row['potential_monthly_savings'] or 0:6.2f}/mo "
            f"| Count: {row['occurrence_count']:3} "
            f"| Save ${savings_per_use:.2f} per use"
        )

    print("=" * 80)
    conn.close()


def show_recent_patterns(limit: int = 10):
    """Show recently detected patterns."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pattern_signature,
            occurrence_count,
            confidence_score,
            created_at,
            automation_status
        FROM operation_patterns
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    print("=" * 80)
    print(f"RECENTLY DETECTED PATTERNS (Last {limit})")
    print("=" * 80)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(
            f"{i:2}. {row['pattern_signature']:30} "
            f"| Detected: {row['created_at'][:10]} "
            f"| Count: {row['occurrence_count']:3} "
            f"| Status: {row['automation_status']}"
        )

    print("=" * 80)
    conn.close()


def show_pattern_details(pattern_id: int):
    """Show detailed information for a specific pattern."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get pattern info
    cursor.execute("SELECT * FROM operation_patterns WHERE id = ?", (pattern_id,))
    pattern = cursor.fetchone()

    if not pattern:
        print(f"Pattern {pattern_id} not found")
        conn.close()
        return

    print("=" * 80)
    print(f"PATTERN DETAILS: {pattern['pattern_signature']}")
    print("=" * 80)
    print(f"ID:                   {pattern['id']}")
    print(f"Type:                 {pattern['pattern_type']}")
    print(f"Occurrences:          {pattern['occurrence_count']}")
    print(f"Confidence:           {pattern['confidence_score']:.1f}%")
    print(f"Status:               {pattern['automation_status']}")
    print()
    print("Cost Analysis:")
    print(f"  Avg tokens (LLM):   {pattern['avg_tokens_with_llm'] or 0:,}")
    print(f"  Avg cost (LLM):     ${pattern['avg_cost_with_llm'] or 0:.4f}")
    print(f"  Avg tokens (tool):  {pattern['avg_tokens_with_tool'] or 0:,}")
    print(f"  Avg cost (tool):    ${pattern['avg_cost_with_tool'] or 0:.4f}")
    print(f"  Monthly savings:    ${pattern['potential_monthly_savings'] or 0:.2f}")
    print()
    print("Dates:")
    print(f"  Created:            {pattern['created_at']}")
    print(f"  Last seen:          {pattern['last_seen']}")
    print()

    # Show typical characteristics
    if pattern['typical_input_pattern']:
        chars = json.loads(pattern['typical_input_pattern'])
        print("Typical Characteristics:")
        print(f"  Complexity:         {chars.get('complexity', 'unknown')}")
        print(f"  Duration:           {chars.get('duration_range', 'unknown')}")
        print(f"  Keywords:           {', '.join(chars.get('keywords', []))}")
        print()

    # Show example workflows
    cursor.execute("""
        SELECT w.workflow_id, w.adw_id, w.nl_input
        FROM pattern_occurrences po
        JOIN workflow_history w ON w.workflow_id = po.workflow_id
        WHERE po.pattern_id = ?
        LIMIT 5
    """, (pattern_id,))

    print("Example Workflows:")
    for i, row in enumerate(cursor.fetchall(), 1):
        nl_input = row['nl_input'][:60] + "..." if len(row['nl_input']) > 60 else row['nl_input']
        print(f"  {i}. {row['adw_id']}: {nl_input}")

    print("=" * 80)
    conn.close()


def main():
    if len(sys.argv) < 2:
        command = "summary"
    else:
        command = sys.argv[1]

    if command == "summary":
        show_summary()
    elif command == "top":
        show_top_patterns()
    elif command == "high-value":
        show_high_value_patterns()
    elif command == "recent":
        show_recent_patterns()
    elif command == "details":
        if len(sys.argv) < 3:
            print("Usage: analyze_patterns.py details <pattern_id>")
            sys.exit(1)
        pattern_id = int(sys.argv[2])
        show_pattern_details(pattern_id)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: summary, top, high-value, recent, details")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x scripts/analyze_patterns.py
```

---

## Testing & Validation

### Step 1: Dry Run Test

```bash
# Test backfill with first 10 workflows (dry-run)
python scripts/backfill_pattern_learning.py --dry-run --limit 10
```

**Expected output:**
```
📚 Backfilling pattern learning from: .../workflow_history.db
🔍 DRY RUN MODE - No changes will be made

Found 10 workflows to analyze

[1/10] 🔍 adw-test-123: 1 pattern(s)
[2/10] 🔍 adw-build-456: 1 pattern(s)
...
============================================================
🔍 DRY RUN COMPLETE
   Workflows processed: 10/10
   Patterns detected: 12
   Errors: 0
============================================================
```

### Step 2: Small Backfill

```bash
# Backfill first 50 workflows
python scripts/backfill_pattern_learning.py --limit 50
```

### Step 3: Full Backfill

```bash
# Backfill all historical workflows
python scripts/backfill_pattern_learning.py
```

### Step 4: Analyze Results

```bash
# Show summary
python scripts/analyze_patterns.py summary

# Show top patterns
python scripts/analyze_patterns.py top

# Show high-value patterns
python scripts/analyze_patterns.py high-value

# Show pattern details
python scripts/analyze_patterns.py details 1
```

### Step 5: Database Validation

```bash
# Verify patterns table
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) as total_patterns FROM operation_patterns;
"

# Verify occurrences table
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) as total_occurrences FROM pattern_occurrences;
"

# Check for orphaned occurrences
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*)
FROM pattern_occurrences po
LEFT JOIN operation_patterns op ON op.id = po.pattern_id
WHERE op.id IS NULL;
"
# Should return 0

# Verify statistics are populated
sqlite3 app/server/db/workflow_history.db "
SELECT
    COUNT(*) as patterns_with_stats
FROM operation_patterns
WHERE avg_tokens_with_llm > 0 AND avg_cost_with_llm > 0;
"
```

### Step 6: Test Sync Integration

```bash
# Run sync to ensure pattern learning works automatically
cd app/server
python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Synced {synced} workflows with pattern learning')
"
```

---

## Success Criteria

- [ ] ✅ **Backfill script works** - No errors on full backfill
- [ ] ✅ **Patterns created** - At least 5 distinct patterns in database
- [ ] ✅ **Statistics calculated** - avg_tokens, avg_cost, confidence_score populated
- [ ] ✅ **No orphaned records** - All pattern_occurrences link to valid patterns
- [ ] ✅ **Analysis tools work** - All analyze_patterns.py commands succeed
- [ ] ✅ **Sync integration works** - New workflows automatically processed
- [ ] ✅ **Performance acceptable** - Backfill completes in reasonable time

---

## Deliverables

1. ✅ `scripts/backfill_pattern_learning.py` (~150 lines)
2. ✅ `scripts/analyze_patterns.py` (~300 lines)
3. ✅ Validation test results
4. ✅ Updated documentation

**Total Lines of Code:** ~450 lines

---

## Expected Results

After completing backfill, you should see:

**Pattern Categories:**
- `test:*` - Testing operations (pytest, vitest, etc.)
- `build:*` - Build operations (typecheck, compile, bundle)
- `format:*` - Formatting operations (prettier, black, eslint)
- `git:*` - Git operations (diff, status, log)
- `deps:*` - Dependency operations (npm, pip updates)

**Confidence Scores:**
- 0-30% - New patterns (1-2 occurrences)
- 30-60% - Emerging patterns (3-9 occurrences)
- 60-100% - Established patterns (10+ occurrences)

**Potential Savings:**
- High-frequency patterns = higher savings
- Based on 95% token reduction (Phase 3E results)

---

## Next Steps

After completing Phase 1.4:

1. Review top patterns for accuracy
2. Monitor pattern detection for 1 week
3. Adjust signature detection heuristics if needed
4. Document any edge cases discovered
5. **Proceed to Phase 2: Context Efficiency Analysis**

---

## Troubleshooting

**Issue:** Backfill runs but creates no patterns
- Check that workflows have `nl_input` populated
- Verify pattern signature keywords match your workflows
- Run with `--dry-run --limit 10` and inspect output

**Issue:** High error rate during backfill
- Check database schema matches expectations
- Verify JSON parsing for cost_breakdown fields
- Review error messages for specific issues

**Issue:** Statistics not calculated
- Ensure workflows have `total_tokens` and `actual_cost_total`
- Check that occurrence_count is incrementing correctly
- Verify update_pattern_statistics is being called

**Issue:** Sync integration not detecting patterns
- Verify import path in workflow_history.py
- Check that pattern learning phase is executing
- Review logs for errors during sync

---

## Documentation Updates

After completing Phase 1:

1. Update main README with pattern detection overview
2. Add examples of detected patterns
3. Document how to analyze patterns
4. Create troubleshooting guide for common issues
