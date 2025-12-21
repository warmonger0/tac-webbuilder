#!/usr/bin/env python3
"""
Check tool_calls data for a specific ADW workflow.

Usage:
    python scripts/check_tool_calls.py <adw_id>
"""

import sys
from pathlib import Path

# Add parent to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from database import get_database_adapter

def check_workflow_status(adw_id: str):
    """Check workflow status and tool_calls data."""
    adapter = get_database_adapter()
    ph = adapter.placeholder()  # Get correct placeholder (? or %s)
    db_type = adapter.get_db_type()

    print("=" * 80)
    print(f"WORKFLOW STATUS CHECK - ADW ID: {adw_id}")
    print(f"Database Type: {db_type}")
    print("=" * 80)

    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Check recent workflow activity
        # Use json_array_length for SQLite, jsonb_array_length for PostgreSQL
        if db_type == 'sqlite':
            query = f"""
                SELECT adw_id, phase_name, phase_status, created_at,
                       CASE
                           WHEN tool_calls IS NOT NULL THEN json_array_length(tool_calls)
                           ELSE 0
                       END as tool_count
                FROM task_logs
                WHERE adw_id = {ph}
                ORDER BY created_at DESC
                LIMIT 15;
            """
        else:
            query = f"""
                SELECT adw_id, phase_name, phase_status, created_at,
                       CASE
                           WHEN tool_calls IS NOT NULL THEN jsonb_array_length(tool_calls)
                           ELSE 0
                       END as tool_count
                FROM task_logs
                WHERE adw_id = {ph}
                ORDER BY created_at DESC
                LIMIT 15;
            """
        cursor.execute(query, (adw_id,))

        rows = cursor.fetchall()
        if not rows:
            print(f"\nNo workflow found with ID: {adw_id}")
            return

        print(f"\nRecent workflow activity (last 15 entries):")
        print("-" * 80)
        print(f"{'Phase':<15} {'Status':<12} {'Tool Calls':<12} {'Created At':<25}")
        print("-" * 80)
        for row in rows:
            print(f"{row['phase_name']:<15} {row['phase_status']:<12} {row['tool_count']:<12} {row['created_at']}")

        # Get summary by phase
        print("\n" + "=" * 80)
        print("TOOL CALLS SUMMARY BY PHASE")
        print("=" * 80)

        if db_type == 'sqlite':
            query = f"""
                SELECT phase_name,
                       COUNT(*) as total_logs,
                       SUM(CASE WHEN tool_calls IS NOT NULL THEN json_array_length(tool_calls) ELSE 0 END) as total_tool_calls,
                       COUNT(CASE WHEN tool_calls IS NOT NULL AND json_array_length(tool_calls) > 0 THEN 1 END) as logs_with_tools
                FROM task_logs
                WHERE adw_id = {ph}
                GROUP BY phase_name
                ORDER BY phase_name;
            """
        else:
            query = f"""
                SELECT phase_name,
                       COUNT(*) as total_logs,
                       SUM(CASE WHEN tool_calls IS NOT NULL THEN jsonb_array_length(tool_calls) ELSE 0 END) as total_tool_calls,
                       COUNT(CASE WHEN tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) > 0 THEN 1 END) as logs_with_tools
                FROM task_logs
                WHERE adw_id = {ph}
                GROUP BY phase_name
                ORDER BY phase_name;
            """
        cursor.execute(query, (adw_id,))

        phase_rows = cursor.fetchall()
        if phase_rows:
            print(f"{'Phase':<15} {'Total Logs':<12} {'Tool Calls':<12} {'Logs w/ Tools':<15}")
            print("-" * 80)
            for row in phase_rows:
                print(f"{row['phase_name']:<15} {row['total_logs']:<12} {row['total_tool_calls']:<12} {row['logs_with_tools']:<15}")
        else:
            print("No tool calls data found.")

        # Get sample tool call details
        print("\n" + "=" * 80)
        print("SAMPLE TOOL CALL DETAILS")
        print("=" * 80)

        if db_type == 'sqlite':
            query = f"""
                SELECT phase_name, tool_calls
                FROM task_logs
                WHERE adw_id = {ph} AND tool_calls IS NOT NULL AND json_array_length(tool_calls) > 0
                ORDER BY created_at DESC
                LIMIT 3;
            """
        else:
            query = f"""
                SELECT phase_name, tool_calls
                FROM task_logs
                WHERE adw_id = {ph} AND tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) > 0
                ORDER BY created_at DESC
                LIMIT 3;
            """
        cursor.execute(query, (adw_id,))

        sample_rows = cursor.fetchall()
        if sample_rows:
            import json
            for i, row in enumerate(sample_rows, 1):
                print(f"\nSample {i} - Phase: {row['phase_name']}")
                print("-" * 80)
                # Parse JSON if stored as string (SQLite)
                tool_calls = row['tool_calls']
                if isinstance(tool_calls, str):
                    tool_calls = json.loads(tool_calls)
                for j, tool in enumerate(tool_calls[:3], 1):  # Show first 3 tools
                    print(f"  Tool {j}:")
                    print(f"    Name: {tool.get('tool_name', 'N/A')}")
                    print(f"    Duration: {tool.get('duration_seconds', 'N/A')}s")
                    print(f"    Exit Code: {tool.get('exit_code', 'N/A')}")
                    if 'command' in tool:
                        cmd = tool['command'][:80] + "..." if len(tool['command']) > 80 else tool['command']
                        print(f"    Command: {cmd}")
                if len(tool_calls) > 3:
                    print(f"  ... and {len(tool_calls) - 3} more tools")
        else:
            print("No tool calls found.")

        # Data quality check
        print("\n" + "=" * 80)
        print("DATA QUALITY CHECK")
        print("=" * 80)

        if db_type == 'sqlite':
            # SQLite doesn't support FILTER, use CASE instead
            query = f"""
                SELECT
                    SUM(CASE WHEN tool_calls IS NULL THEN 1 ELSE 0 END) as null_tool_calls,
                    SUM(CASE WHEN tool_calls IS NOT NULL AND json_array_length(tool_calls) = 0 THEN 1 ELSE 0 END) as empty_tool_calls,
                    SUM(CASE WHEN tool_calls IS NOT NULL AND json_array_length(tool_calls) > 0 THEN 1 ELSE 0 END) as populated_tool_calls
                FROM task_logs
                WHERE adw_id = {ph};
            """
        else:
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE tool_calls IS NULL) as null_tool_calls,
                    COUNT(*) FILTER (WHERE tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) = 0) as empty_tool_calls,
                    COUNT(*) FILTER (WHERE tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) > 0) as populated_tool_calls
                FROM task_logs
                WHERE adw_id = {ph};
            """
        cursor.execute(query, (adw_id,))

        quality_row = cursor.fetchone()
        print(f"Null tool_calls:      {quality_row['null_tool_calls']}")
        print(f"Empty tool_calls:     {quality_row['empty_tool_calls']}")
        print(f"Populated tool_calls: {quality_row['populated_tool_calls']}")

        cursor.close()

    adapter.close()
    print("\n" + "=" * 80)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_tool_calls.py <adw_id>")
        sys.exit(1)

    adw_id = sys.argv[1]
    check_workflow_status(adw_id)
