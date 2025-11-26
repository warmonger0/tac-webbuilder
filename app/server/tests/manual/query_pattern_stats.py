#!/usr/bin/env python3
"""
Query Pattern Statistics

This script queries the database for pattern statistics to understand:
1. How many patterns have been detected
2. Pattern distribution by type
3. Occurrence counts
4. Confidence scores
5. Potential automation candidates

Run from app/server/ directory:
    cd app/server && uv run python tests/manual/query_pattern_stats.py
"""

import sys
import sqlite3
from pathlib import Path


def main():
    print("=" * 80)
    print("PATTERN RECOGNITION STATISTICS")
    print("=" * 80)
    print()

    # Connect to database
    db_path = Path(__file__).parent.parent.parent / "db" / "database.db"
    print(f"📂 Database: {db_path}")

    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Overall statistics
    print("\n" + "=" * 80)
    print("📊 OVERALL STATISTICS")
    print("=" * 80)

    # Total workflows
    cursor.execute("SELECT COUNT(*) as count FROM workflow_history")
    total_workflows = cursor.fetchone()[0]
    print(f"\nTotal Workflows: {total_workflows}")

    # Completed workflows
    cursor.execute("SELECT COUNT(*) as count FROM workflow_history WHERE status = 'completed'")
    completed_workflows = cursor.fetchone()[0]
    print(f"Completed Workflows: {completed_workflows}")

    # Workflows with nl_input
    cursor.execute("SELECT COUNT(*) as count FROM workflow_history WHERE nl_input IS NOT NULL")
    workflows_with_input = cursor.fetchone()[0]
    print(f"Workflows with NL Input: {workflows_with_input}")

    # Total patterns detected
    cursor.execute("SELECT COUNT(*) as count FROM operation_patterns")
    total_patterns = cursor.fetchone()[0]
    print(f"\nTotal Patterns Detected: {total_patterns}")

    # Total pattern occurrences
    cursor.execute("SELECT COUNT(*) as count FROM pattern_occurrences")
    total_occurrences = cursor.fetchone()[0]
    print(f"Total Pattern Occurrences: {total_occurrences}")

    if total_patterns == 0:
        print("\n⚠️  No patterns detected yet. Run pattern detection on completed workflows first.")
        conn.close()
        return 0

    # Pattern breakdown by type
    print("\n" + "=" * 80)
    print("📈 PATTERNS BY TYPE")
    print("=" * 80)

    cursor.execute("""
        SELECT
            pattern_type,
            COUNT(*) as count,
            SUM(occurrence_count) as total_occurrences,
            AVG(confidence_score) as avg_confidence
        FROM operation_patterns
        GROUP BY pattern_type
        ORDER BY total_occurrences DESC
    """)

    print(f"\n{'Type':<15} {'Patterns':<10} {'Occurrences':<15} {'Avg Confidence':<15}")
    print("-" * 60)

    for row in cursor.fetchall():
        print(f"{row['pattern_type']:<15} {row['count']:<10} {row['total_occurrences']:<15} {row['avg_confidence']:.1f}%")

    # Top patterns by occurrence
    print("\n" + "=" * 80)
    print("🔥 TOP PATTERNS (By Occurrence Count)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            id,
            pattern_signature,
            pattern_type,
            occurrence_count,
            confidence_score,
            automation_status,
            avg_cost_with_llm,
            potential_monthly_savings,
            first_detected,
            last_seen
        FROM operation_patterns
        ORDER BY occurrence_count DESC
        LIMIT 10
    """)

    for row in cursor.fetchall():
        print(f"\n   Pattern: {row['pattern_signature']}")
        print(f"   Type: {row['pattern_type']}")
        print(f"   Occurrences: {row['occurrence_count']}")
        print(f"   Confidence: {row['confidence_score']:.1f}%")
        print(f"   Automation Status: {row['automation_status']}")
        if row['avg_cost_with_llm'] and row['avg_cost_with_llm'] > 0:
            print(f"   Avg Cost (LLM): ${row['avg_cost_with_llm']:.4f}")
        if row['potential_monthly_savings'] and row['potential_monthly_savings'] > 0:
            print(f"   Potential Monthly Savings: ${row['potential_monthly_savings']:.2f}")
        print(f"   First Detected: {row['first_detected']}")
        print(f"   Last Seen: {row['last_seen']}")

    # High-value automation candidates
    print("\n" + "=" * 80)
    print("💰 HIGH-VALUE AUTOMATION CANDIDATES")
    print("=" * 80)

    cursor.execute("""
        SELECT
            pattern_signature,
            pattern_type,
            occurrence_count,
            confidence_score,
            potential_monthly_savings,
            automation_status
        FROM operation_patterns
        WHERE confidence_score >= 50
          AND occurrence_count >= 2
        ORDER BY potential_monthly_savings DESC
        LIMIT 5
    """)

    candidates = cursor.fetchall()

    if not candidates:
        print("\n⚠️  No high-value candidates yet (need confidence >= 50% and occurrence >= 2)")
    else:
        print(f"\n{'Pattern':<30} {'Occurrences':<12} {'Confidence':<12} {'Monthly Savings':<15}")
        print("-" * 75)

        for row in candidates:
            savings = row['potential_monthly_savings'] if row['potential_monthly_savings'] else 0.0
            print(f"{row['pattern_signature']:<30} {row['occurrence_count']:<12} {row['confidence_score']:<11.1f}% ${savings:<14.2f}")

    # Pattern occurrences details
    print("\n" + "=" * 80)
    print("🔗 PATTERN OCCURRENCES")
    print("=" * 80)

    cursor.execute("""
        SELECT
            p.pattern_signature,
            COUNT(po.id) as occurrence_count,
            AVG(po.similarity_score) as avg_similarity
        FROM operation_patterns p
        LEFT JOIN pattern_occurrences po ON p.id = po.pattern_id
        GROUP BY p.id, p.pattern_signature
        ORDER BY occurrence_count DESC
    """)

    print(f"\n{'Pattern':<40} {'Occurrences':<15} {'Avg Similarity':<15}")
    print("-" * 70)

    for row in cursor.fetchall():
        print(f"{row['pattern_signature']:<40} {row['occurrence_count']:<15} {row['avg_similarity']:.1f}%")

    # Recent pattern activity
    print("\n" + "=" * 80)
    print("⏰ RECENT PATTERN ACTIVITY (Last 7 Days)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            p.pattern_signature,
            COUNT(po.id) as recent_occurrences,
            MAX(po.detected_at) as last_occurrence
        FROM operation_patterns p
        LEFT JOIN pattern_occurrences po ON p.id = po.pattern_id
        WHERE po.detected_at >= datetime('now', '-7 days')
        GROUP BY p.id, p.pattern_signature
        ORDER BY recent_occurrences DESC
    """)

    recent = cursor.fetchall()

    if not recent:
        print("\n⚠️  No pattern activity in the last 7 days")
    else:
        print(f"\n{'Pattern':<40} {'Recent Count':<15} {'Last Occurrence':<20}")
        print("-" * 75)

        for row in recent:
            print(f"{row['pattern_signature']:<40} {row['recent_occurrences']:<15} {row['last_occurrence']:<20}")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ QUERY COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
