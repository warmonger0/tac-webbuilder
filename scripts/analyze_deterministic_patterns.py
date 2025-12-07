#!/usr/bin/env python3
"""
Advanced Pattern Analysis - Find Deterministic Orchestration Sequences

This analyzer goes deeper than basic sequence counting. It:
1. Filters out same-tool repetitions (Bash→Bash not interesting)
2. Examines payloads to understand context (errors, files, commands)
3. Identifies error→fix→retry patterns
4. Groups similar patterns by their triggering context
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
import json
import re

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def extract_tool_sequence_with_context(events):
    """
    Extract tool sequences with full context (commands, files, errors).
    Filter out consecutive same-tool calls.
    """
    sequences_by_session = defaultdict(list)

    for event in events:
        session_id = event['session_id'] or event['workflow_id'] or 'unknown'
        tool_name = event['tool_name']
        event_type = event['event_type']

        if not tool_name:
            continue

        try:
            payload = json.loads(event['payload']) if event['payload'] else {}
        except:
            payload = {}

        # Extract relevant context based on tool
        context = {
            'tool': tool_name,
            'type': event_type,
            'timestamp': event['timestamp']
        }

        if tool_name == 'Bash':
            context['command'] = payload.get('command', '')
            context['description'] = payload.get('description', '')
            # PostToolUse will have results
            if event_type == 'PostToolUse':
                context['exit_code'] = payload.get('exit_code')
                context['output'] = payload.get('output', '')[:500]  # First 500 chars

        elif tool_name in ('Read', 'Edit', 'Write'):
            context['file_path'] = payload.get('file_path', '')
            if tool_name == 'Edit':
                context['old_string'] = payload.get('old_string', '')[:200]
                context['new_string'] = payload.get('new_string', '')[:200]

        elif tool_name == 'Grep':
            context['pattern'] = payload.get('pattern', '')
            context['path'] = payload.get('path', '')

        sequences_by_session[session_id].append(context)

    return sequences_by_session


def filter_mixed_tool_sequences(sequences_by_session, min_length=3, max_length=10):
    """
    Extract mixed-tool sequences (filter out Bash→Bash→Bash).
    """
    mixed_sequences = []

    for session_id, events in sequences_by_session.items():
        if len(events) < min_length:
            continue

        # Look for windows of mixed tools
        for i in range(len(events) - min_length + 1):
            for length in range(min_length, min(max_length + 1, len(events) - i + 1)):
                window = events[i:i+length]

                # Get tool sequence
                tools = [e['tool'] for e in window]

                # Filter: Must have at least 2 different tools
                if len(set(tools)) >= 2:
                    # Filter: No more than 3 consecutive same tools
                    max_consecutive = 1
                    current_consecutive = 1
                    for j in range(1, len(tools)):
                        if tools[j] == tools[j-1]:
                            current_consecutive += 1
                            max_consecutive = max(max_consecutive, current_consecutive)
                        else:
                            current_consecutive = 1

                    if max_consecutive <= 3:  # Allow up to 3 consecutive
                        mixed_sequences.append({
                            'session': session_id,
                            'tools': tuple(tools),
                            'events': window,
                            'start_idx': i
                        })

    return mixed_sequences


def identify_error_fix_patterns(mixed_sequences):
    """
    Find error→fix→retry patterns (most valuable for automation).

    Pattern: Bash(fail) → Read/Grep/Edit → Bash(success)
    """
    error_fix_patterns = []

    for seq in mixed_sequences:
        events = seq['events']
        tools = seq['tools']

        # Look for Bash → (Read/Grep/Edit)+ → Bash pattern
        if len(tools) < 3:
            continue

        # First tool is Bash (PostToolUse with error)
        if events[0]['tool'] == 'Bash' and events[0]['type'] == 'PostToolUse':
            exit_code = events[0].get('exit_code')

            # Check if it failed (non-zero exit code)
            if exit_code and exit_code != 0:
                # Middle tools are Read/Grep/Edit
                middle_tools = [e['tool'] for e in events[1:-1]]

                if all(t in ('Read', 'Grep', 'Edit', 'Write') for t in middle_tools):
                    # Last tool is Bash (PostToolUse)
                    if events[-1]['tool'] == 'Bash' and events[-1]['type'] == 'PostToolUse':
                        last_exit_code = events[-1].get('exit_code')

                        # Check if it succeeded
                        if last_exit_code == 0:
                            # This is an error→fix→retry pattern!
                            error_fix_patterns.append({
                                'session': seq['session'],
                                'pattern': seq['tools'],
                                'initial_command': events[0].get('command', ''),
                                'initial_error': events[0].get('output', '')[:300],
                                'fix_tools': middle_tools,
                                'files_modified': [e.get('file_path', '') for e in events[1:-1] if e.get('file_path')],
                                'final_command': events[-1].get('command', ''),
                                'success': True
                            })

    return error_fix_patterns


def categorize_error_patterns(error_fix_patterns):
    """
    Group error→fix patterns by error type.
    """
    categorized = defaultdict(list)

    for pattern in error_fix_patterns:
        error_output = pattern['initial_error'].lower()

        # Categorize by error type
        if 'modulenotfounderror' in error_output or 'import' in error_output:
            category = 'import_error'
        elif 'type error' in error_output or 'property' in error_output:
            category = 'type_error'
        elif 'test failed' in error_output or 'assertion' in error_output:
            category = 'test_failure'
        elif 'lint' in error_output or 'e501' in error_output or 'ruff' in error_output:
            category = 'lint_error'
        elif 'syntax' in error_output:
            category = 'syntax_error'
        elif 'pytest' in pattern['initial_command']:
            category = 'test_related'
        elif 'tsc' in pattern['initial_command'] or 'typescript' in pattern['initial_command']:
            category = 'typescript_related'
        elif 'ruff' in pattern['initial_command']:
            category = 'lint_related'
        else:
            category = 'other'

        categorized[category].append(pattern)

    return categorized


def analyze_pattern_determinism(patterns_in_category):
    """
    Determine if patterns in a category are deterministic.

    Deterministic = same command → same error type → same fix sequence
    """
    if len(patterns_in_category) < 3:
        return None  # Need at least 3 occurrences

    # Group by initial command
    by_command = defaultdict(list)
    for p in patterns_in_category:
        cmd = p['initial_command'].strip()
        by_command[cmd].append(p)

    deterministic_patterns = []

    for cmd, patterns in by_command.items():
        if len(patterns) < 3:
            continue

        # Check if fix sequence is consistent
        fix_sequences = [tuple(p['fix_tools']) for p in patterns]
        most_common_fix = Counter(fix_sequences).most_common(1)[0]

        if most_common_fix[1] >= len(patterns) * 0.7:  # 70% consistency
            deterministic_patterns.append({
                'command': cmd,
                'occurrences': len(patterns),
                'fix_sequence': most_common_fix[0],
                'consistency': most_common_fix[1] / len(patterns),
                'example_sessions': [p['session'] for p in patterns[:3]],
                'files_involved': list(set([f for p in patterns for f in p['files_modified'] if f]))
            })

    return deterministic_patterns


def main():
    print("🔬 Advanced Pattern Analysis - Finding Deterministic Orchestration Patterns")
    print("=" * 80)
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all hook events
    print("📊 Loading hook events...")
    cursor.execute("""
        SELECT
            event_id,
            event_type,
            session_id,
            workflow_id,
            timestamp,
            tool_name,
            payload
        FROM hook_events
        WHERE event_type IN ('PreToolUse', 'PostToolUse')
        ORDER BY timestamp ASC
    """)

    events = [dict(row) for row in cursor.fetchall()]
    total = len(events)
    print(f"   Loaded {total:,} hook events")
    print()

    # Extract sequences with context
    print("🔄 Extracting tool sequences with context...")
    sequences_by_session = extract_tool_sequence_with_context(events)
    print(f"   Found {len(sequences_by_session):,} unique sessions")
    print()

    # Filter for mixed-tool sequences
    print("🔍 Finding mixed-tool sequences (filtering out Bash→Bash→Bash)...")
    mixed_sequences = filter_mixed_tool_sequences(sequences_by_session, min_length=3, max_length=8)
    print(f"   Found {len(mixed_sequences):,} mixed-tool sequences")
    print()

    # Identify error→fix→retry patterns
    print("⚡ Identifying error→fix→retry patterns...")
    error_fix_patterns = identify_error_fix_patterns(mixed_sequences)
    print(f"   Found {len(error_fix_patterns):,} error→fix→retry patterns")
    print()

    if len(error_fix_patterns) == 0:
        print("❌ No error→fix→retry patterns found.")
        print()
        print("This means:")
        print("  • ADW workflows don't have many error→fix cycles")
        print("  • Tests/builds succeed on first try (good!)")
        print("  • Or errors are fixed without re-running commands")
        print()
        conn.close()
        return

    # Categorize by error type
    print("📂 Categorizing patterns by error type...")
    categorized = categorize_error_patterns(error_fix_patterns)
    print()

    # Display results
    print("=" * 80)
    print("DETERMINISTIC PATTERN ANALYSIS")
    print("=" * 80)
    print()

    total_deterministic = 0

    for category, patterns in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"📌 {category.upper().replace('_', ' ')}")
        print(f"   Total occurrences: {len(patterns)}")
        print()

        # Analyze determinism
        deterministic = analyze_pattern_determinism(patterns)

        if deterministic:
            total_deterministic += len(deterministic)

            for i, pattern in enumerate(deterministic, 1):
                print(f"   Pattern {i}:")
                print(f"      Command: {pattern['command'][:80]}")
                print(f"      Occurrences: {pattern['occurrences']}")
                print(f"      Fix sequence: {' → '.join(pattern['fix_sequence'])}")
                print(f"      Consistency: {pattern['consistency']:.0%}")
                print(f"      Files: {', '.join(pattern['files_involved'][:3])}")

                # Estimate savings
                token_savings = pattern['occurrences'] * 2000  # ~2K tokens per occurrence
                cost_savings = token_savings * 0.003 / 1000  # $3/1M tokens
                print(f"      💰 Estimated savings: {token_savings:,} tokens (${cost_savings:.2f})")
                print()
        else:
            print(f"   ⚠️  Patterns in this category are not consistent enough (< 3 occurrences or < 70% consistency)")
            print()

    print("=" * 80)
    print()

    # Summary
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total error→fix→retry patterns found: {len(error_fix_patterns)}")
    print(f"Categories identified: {len(categorized)}")
    print(f"Deterministic patterns (70%+ consistency): {total_deterministic}")
    print()

    if total_deterministic > 0:
        print("✅ RECOMMENDATION: Implement deterministic handlers for top patterns")
        print()
        print("NEXT STEPS:")
        print("1. Review pattern details above")
        print("2. For each high-value pattern:")
        print("   - Verify 70%+ consistency in actual execution")
        print("   - Design deterministic handler function")
        print("   - Estimate token/cost savings")
        print("   - Implement and test handler")
        print("3. Track savings in cost_savings_log table")
    else:
        print("✅ NO ACTION NEEDED")
        print()
        print("While error→fix→retry patterns exist, none are deterministic enough (70%+)")
        print("to warrant automation. This is actually good - it means:")
        print("  • Each error requires unique LLM reasoning")
        print("  • No repetitive waste of tokens on predictable fixes")
        print("  • Current architecture is optimal")

    print()
    conn.close()


if __name__ == "__main__":
    main()
