"""
Query and display pattern statistics.

Displays top patterns by occurrence count, pattern characteristics,
confidence scores, and cost analysis.

Run: cd app/server && uv run python tests/manual/query_pattern_stats.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.db_connection import get_connection

# Database path
DB_PATH = "db/workflow_history.db"


def display_top_patterns():
    """Display top 10 patterns by occurrence count."""
    print("\n" + "=" * 60)
    print("TOP 10 PATTERNS BY OCCURRENCE")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pattern_signature,
                pattern_type,
                occurrence_count,
                automation_status,
                confidence_score
            FROM operation_patterns
            ORDER BY occurrence_count DESC
            LIMIT 10
        """)

        rows = cursor.fetchall()

        if not rows:
            print("\n⚠️  No patterns found in database")
            return False

        print("\n" + "-" * 120)
        print(f"{'Pattern Signature':<45} | {'Type':<12} | {'Count':>5} | "
              f"{'Status':<18} | {'Confidence':>10}")
        print("-" * 120)

        for row in rows:
            sig, type_, count, status, confidence = row
            # Truncate long signatures
            sig_display = sig[:42] + "..." if len(sig) > 45 else sig
            confidence_display = f"{confidence:.1f}" if confidence else "N/A"
            print(f"{sig_display:<45} | {type_:<12} | {count:>5} | "
                  f"{status:<18} | {confidence_display:>10}")

        print("-" * 120)
        print(f"\nTotal patterns found: {len(rows)}")

        return True


def display_pattern_characteristics():
    """Display sample pattern characteristics."""
    print("\n" + "=" * 60)
    print("SAMPLE PATTERN CHARACTERISTICS")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pattern_signature, characteristics
            FROM operation_patterns
            WHERE characteristics IS NOT NULL
            AND characteristics != 'null'
            LIMIT 3
        """)

        rows = cursor.fetchall()

        if not rows:
            print("\n⚠️  No patterns with characteristics found")
            return

        for i, (sig, chars_json) in enumerate(rows, 1):
            print(f"\n{i}. Pattern: {sig}")
            print("   " + "-" * 57)

            try:
                chars = json.loads(chars_json)

                # Display key characteristics
                if 'keywords' in chars and chars['keywords']:
                    print(f"   Keywords: {', '.join(chars['keywords'][:5])}")

                if 'files' in chars and chars['files']:
                    files = chars['files'][:3]
                    print(f"   Files: {', '.join(files)}")

                if 'duration_range' in chars:
                    dr = chars['duration_range']
                    print(f"   Duration: {dr.get('min', 'N/A')}s - {dr.get('max', 'N/A')}s")

                if 'complexity' in chars:
                    print(f"   Complexity: {chars['complexity']}")

                if 'typical_errors' in chars and chars['typical_errors']:
                    print(f"   Typical Errors: {len(chars['typical_errors'])} recorded")

            except json.JSONDecodeError:
                print("   ⚠️  Invalid JSON in characteristics")
            except Exception as e:
                print(f"   ⚠️  Error parsing characteristics: {e}")


def display_cost_analysis():
    """Display cost analysis for top patterns."""
    print("\n" + "=" * 60)
    print("COST ANALYSIS")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pattern_signature,
                occurrence_count,
                avg_cost_with_llm,
                avg_cost_with_tool,
                potential_monthly_savings
            FROM operation_patterns
            WHERE avg_cost_with_llm IS NOT NULL
            AND avg_cost_with_llm > 0
            ORDER BY potential_monthly_savings DESC
            LIMIT 5
        """)

        rows = cursor.fetchall()

        if not rows:
            print("\n⚠️  No cost data available yet")
            return

        print("\n" + "-" * 110)
        print(f"{'Pattern':<40} | {'Count':>5} | {'Avg LLM':>10} | "
              f"{'Avg Tool':>10} | {'Monthly Savings':>15}")
        print("-" * 110)

        total_savings = 0
        for row in rows:
            sig, count, llm_cost, tool_cost, savings = row
            sig_display = sig[:37] + "..." if len(sig) > 40 else sig
            llm_display = f"${llm_cost:.4f}" if llm_cost else "N/A"
            tool_display = f"${tool_cost:.4f}" if tool_cost else "N/A"
            savings_display = f"${savings:.2f}" if savings else "N/A"

            print(f"{sig_display:<40} | {count:>5} | {llm_display:>10} | "
                  f"{tool_display:>10} | {savings_display:>15}")

            if savings:
                total_savings += savings

        print("-" * 110)
        print(f"{'Total Potential Monthly Savings':>82}: ${total_savings:>15.2f}")


def display_pattern_type_distribution():
    """Display distribution of pattern types."""
    print("\n" + "=" * 60)
    print("PATTERN TYPE DISTRIBUTION")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

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

        rows = cursor.fetchall()

        if not rows:
            print("\n⚠️  No pattern type data available")
            return

        print("\n" + "-" * 80)
        print(f"{'Type':<15} | {'Patterns':>10} | {'Occurrences':>12} | {'Avg Confidence':>15}")
        print("-" * 80)

        for row in rows:
            type_, count, occurrences, avg_conf = row
            conf_display = f"{avg_conf:.1f}" if avg_conf else "N/A"
            print(f"{type_:<15} | {count:>10} | {occurrences:>12} | {conf_display:>15}")

        print("-" * 80)


def display_automation_status():
    """Display automation status breakdown."""
    print("\n" + "=" * 60)
    print("AUTOMATION STATUS")
    print("=" * 60)

    with get_connection(db_path=DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                automation_status,
                COUNT(*) as count,
                SUM(occurrence_count) as total_occurrences
            FROM operation_patterns
            GROUP BY automation_status
            ORDER BY total_occurrences DESC
        """)

        rows = cursor.fetchall()

        if not rows:
            print("\n⚠️  No automation status data available")
            return

        print("\n" + "-" * 70)
        print(f"{'Status':<25} | {'Patterns':>10} | {'Total Occurrences':>18}")
        print("-" * 70)

        for row in rows:
            status, count, occurrences = row
            print(f"{status:<25} | {count:>10} | {occurrences:>18}")

        print("-" * 70)


def main():
    """Display comprehensive pattern statistics."""
    print("\n" + "=" * 60)
    print("PATTERN STATISTICS REPORT")
    print("=" * 60)
    print("\nDatabase: db/workflow_history.db")

    try:
        # Display various statistics
        has_patterns = display_top_patterns()

        if not has_patterns:
            print("\n💡 Tip: Run some ADW workflows first to generate patterns")
            return 0

        display_pattern_type_distribution()
        display_automation_status()
        display_pattern_characteristics()
        display_cost_analysis()

        # Final summary
        print("\n" + "=" * 60)
        print("REPORT COMPLETE")
        print("=" * 60)
        print("\n✅ Pattern statistics generated successfully")
        print("💡 Use these insights to guide automation decisions in Phase 2+")

        return 0

    except Exception as e:
        print(f"\n❌ Error generating statistics: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
