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
        nl_input_raw = row['nl_input']
        if nl_input_raw and len(nl_input_raw) > 60:
            nl_input = nl_input_raw[:60] + "..."
        elif nl_input_raw:
            nl_input = nl_input_raw
        else:
            nl_input = "(no input recorded)"
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
