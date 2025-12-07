#!/usr/bin/env python3
"""
Analyze hook events to detect repeated tool orchestration patterns.

Identifies deterministic sequences where LLM is just routing between tools
predictably, wasting tokens on orchestration that could be code.
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
import json

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def extract_tool_sequences(events):
    """
    Extract tool call sequences from hook events.

    Returns sequences grouped by session/workflow.
    """
    sequences = defaultdict(list)

    for event in events:
        session_id = event['session_id'] or event['workflow_id'] or 'unknown'
        tool_name = event['tool_name']
        event_type = event['event_type']

        if tool_name and event_type in ('PreToolUse', 'PostToolUse'):
            sequences[session_id].append({
                'tool': tool_name,
                'type': event_type,
                'timestamp': event['timestamp'],
                'payload': json.loads(event['payload']) if event['payload'] else {}
            })

    return sequences


def find_common_sequences(sequences, min_length=3, min_occurrences=5):
    """
    Find tool sequences that occur frequently.

    Args:
        sequences: Dict of session_id -> list of tool events
        min_length: Minimum sequence length to consider
        min_occurrences: Minimum times a sequence must occur

    Returns:
        List of (sequence_pattern, count, example_sessions)
    """
    # Extract tool-only sequences
    tool_patterns = []

    for session_id, events in sequences.items():
        # Get just the tool names in order
        tools = [e['tool'] for e in events]

        # Extract subsequences of various lengths
        for length in range(min_length, min(len(tools) + 1, 10)):
            for i in range(len(tools) - length + 1):
                subseq = tuple(tools[i:i+length])
                tool_patterns.append((subseq, session_id))

    # Count occurrences
    pattern_counts = Counter([p[0] for p in tool_patterns])

    # Filter by min_occurrences
    common_patterns = []
    for pattern, count in pattern_counts.items():
        if count >= min_occurrences:
            # Find example sessions
            examples = [s for p, s in tool_patterns if p == pattern][:3]
            common_patterns.append((pattern, count, examples))

    # Sort by frequency
    common_patterns.sort(key=lambda x: x[1], reverse=True)

    return common_patterns


def analyze_pattern_context(pattern_tuple, sequences, example_sessions):
    """
    Analyze context around a pattern to determine if it's deterministic.

    Returns dict with:
    - success_rate: How often does this sequence lead to success?
    - common_errors: What errors typically trigger this sequence?
    - common_files: What files are typically involved?
    """
    contexts = []

    for session_id in example_sessions:
        events = sequences[session_id]

        # Find where pattern occurs in this session
        tools = [e['tool'] for e in events]
        pattern_str = [str(t) for t in pattern_tuple]

        # Extract context (errors, file patterns, outcomes)
        context = {
            'session': session_id,
            'tools_before': [],
            'tools_after': [],
            'bash_outputs': [],
            'files_touched': []
        }

        for event in events:
            if event['tool'] == 'Bash':
                payload = event['payload']
                if 'result' in payload:
                    context['bash_outputs'].append(payload['result'])
            elif event['tool'] in ('Read', 'Edit', 'Write'):
                payload = event['payload']
                if 'file_path' in payload:
                    context['files_touched'].append(payload['file_path'])

        contexts.append(context)

    return contexts


def main():
    print("🔍 Analyzing hook events for orchestration patterns...")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all hook events
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

    print(f"📊 Total hook events: {total:,}")
    print()

    # Extract sequences
    print("🔄 Extracting tool sequences...")
    sequences = extract_tool_sequences(events)
    print(f"   Found {len(sequences):,} unique sessions")
    print()

    # Find common patterns
    print("🔎 Finding repeated patterns (min 5 occurrences, min length 3)...")
    patterns = find_common_sequences(sequences, min_length=3, min_occurrences=5)
    print(f"   Found {len(patterns):,} repeated patterns")
    print()

    # Display top patterns
    print("=" * 80)
    print("TOP 20 ORCHESTRATION PATTERNS")
    print("=" * 80)
    print()

    for i, (pattern, count, examples) in enumerate(patterns[:20], 1):
        print(f"{i:2}. Pattern (occurs {count} times):")
        print(f"    Sequence: {' → '.join(pattern)}")
        print(f"    Example sessions: {', '.join(examples[:3])}")

        # Analyze context
        contexts = analyze_pattern_context(pattern, sequences, examples[:3])

        # Try to detect what this pattern does
        tools_involved = set(pattern)

        if 'Bash' in tools_involved and any(t in tools_involved for t in ['Read', 'Edit']):
            print(f"    ⚡ Likely: Test/Build/Lint failure → fix → retry pattern")
        elif 'Grep' in tools_involved and 'Edit' in tools_involved:
            print(f"    ⚡ Likely: Search → modify pattern")
        elif pattern.count('Bash') >= 2:
            print(f"    ⚡ Likely: Command → verify → rerun pattern")

        print()

    print("=" * 80)
    print()

    # Suggest pattern candidates
    print("💡 PATTERN CANDIDATES FOR AUTOMATION:")
    print()

    high_value = [
        p for p in patterns
        if p[1] >= 10  # Occurs at least 10 times
        and len(p[0]) >= 3  # At least 3 tools
        and 'Bash' in p[0]  # Involves external command
    ]

    for pattern, count, examples in high_value[:10]:
        print(f"   🎯 {' → '.join(pattern)}")
        print(f"      Occurrences: {count}")
        print(f"      Potential savings: ~{count * 2000} tokens (est.)")
        print()

    conn.close()

    print("✅ Analysis complete!")
    print()
    print("NEXT STEPS:")
    print("1. Review pattern candidates above")
    print("2. For each high-value pattern:")
    print("   - Examine hook event details to understand context")
    print("   - Verify it's deterministic (same input → same output)")
    print("   - Estimate token savings (LLM orchestration vs direct function)")
    print("   - Create pattern definition in operation_patterns")
    print("3. Implement deterministic handlers for approved patterns")


if __name__ == "__main__":
    main()
