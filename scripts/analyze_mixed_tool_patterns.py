#!/usr/bin/env python3
"""
Analyze mixed-tool sequences to understand orchestration patterns.

Even without error→fix→retry, there may be other deterministic patterns:
- Read → Edit → Write (file transformation)
- Grep → Read → Edit (search and modify)
- Bash → Read → Bash (command → inspect → verify)
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
import json

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def extract_tool_sequences(events):
    """Extract tool call sequences from hook events."""
    sequences = defaultdict(list)

    for event in events:
        session_id = event['session_id'] or event['workflow_id'] or 'unknown'
        tool_name = event['tool_name']
        event_type = event['event_type']

        if tool_name and event_type == 'PostToolUse':  # Only completed tool calls
            try:
                payload = json.loads(event['payload']) if event['payload'] else {}
            except:
                payload = {}

            sequences[session_id].append({
                'tool': tool_name,
                'timestamp': event['timestamp'],
                'payload': payload
            })

    return sequences


def find_common_mixed_patterns(sequences, min_length=3, max_length=6, min_occurrences=10):
    """Find common mixed-tool sequences (at least 2 different tools)."""
    pattern_list = []

    for session_id, events in sequences.items():
        # Extract subsequences
        for i in range(len(events)):
            for length in range(min_length, min(max_length + 1, len(events) - i + 1)):
                window = events[i:i+length]
                tools = tuple([e['tool'] for e in window])

                # Filter: Must have at least 2 different tools
                if len(set(tools)) >= 2:
                    # Filter: No more than 2 consecutive same tools
                    valid = True
                    for j in range(len(tools) - 2):
                        if tools[j] == tools[j+1] == tools[j+2]:
                            valid = False
                            break

                    if valid:
                        pattern_list.append((tools, session_id))

    # Count occurrences
    pattern_counts = Counter([p[0] for p in pattern_list])

    # Filter by min_occurrences and return
    common = []
    for pattern, count in pattern_counts.items():
        if count >= min_occurrences:
            # Find example sessions
            examples = list(set([s for p, s in pattern_list if p == pattern]))[:3]
            common.append((pattern, count, examples))

    # Sort by frequency
    common.sort(key=lambda x: x[1], reverse=True)

    return common


def categorize_pattern(pattern_tuple):
    """Categorize pattern by type of orchestration."""
    tools = set(pattern_tuple)
    sequence = ' → '.join(pattern_tuple)

    # File manipulation patterns
    if 'Read' in tools and 'Edit' in tools:
        if 'Grep' in tools:
            return 'search_modify', 'Search → Modify', sequence
        elif 'Bash' in tools:
            return 'inspect_modify_verify', 'Inspect → Modify → Verify', sequence
        else:
            return 'read_modify', 'Read → Modify', sequence

    # Verification patterns
    if 'Bash' in tools and 'Read' in tools:
        return 'command_inspect', 'Command → Inspect', sequence

    # Data gathering patterns
    if pattern_tuple.count('Read') >= 2 and len(set(pattern_tuple)) >= 2:
        return 'multi_read', 'Multi-file Read', sequence

    # Planning/writing patterns
    if 'TodoWrite' in tools:
        return 'planning', 'Planning/Tracking', sequence

    return 'other', 'Other', sequence


def main():
    print("🔍 Mixed-Tool Pattern Analysis")
    print("=" * 80)
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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
        WHERE event_type = 'PostToolUse'
        AND tool_name IS NOT NULL
        ORDER BY timestamp ASC
    """)

    events = [dict(row) for row in cursor.fetchall()]
    print(f"   Loaded {len(events):,} completed tool calls")
    print()

    print("🔄 Extracting tool sequences...")
    sequences = extract_tool_sequences(events)
    print(f"   Found {len(sequences):,} unique sessions")
    print()

    print("🔎 Finding common mixed-tool patterns (min 10 occurrences)...")
    patterns = find_common_mixed_patterns(sequences, min_length=3, max_length=5, min_occurrences=10)
    print(f"   Found {len(patterns):,} common mixed-tool patterns")
    print()

    # Categorize patterns
    categorized = defaultdict(list)
    for pattern, count, examples in patterns:
        category, category_name, sequence = categorize_pattern(pattern)
        categorized[category].append((pattern, count, examples, sequence))

    # Display by category
    print("=" * 80)
    print("MIXED-TOOL ORCHESTRATION PATTERNS")
    print("=" * 80)
    print()

    for category in ['search_modify', 'read_modify', 'inspect_modify_verify', 'command_inspect', 'planning', 'multi_read', 'other']:
        if category not in categorized:
            continue

        category_patterns = categorized[category]
        category_total = sum([p[1] for p in category_patterns])

        # Get category name from first pattern
        _, category_name, _ = categorize_pattern(category_patterns[0][0])

        print(f"📂 {category_name.upper()}")
        print(f"   Total patterns in category: {len(category_patterns)}")
        print(f"   Total occurrences: {category_total:,}")
        print()

        # Show top 5 patterns in this category
        for i, (pattern, count, examples, sequence) in enumerate(category_patterns[:5], 1):
            print(f"   {i}. {sequence}")
            print(f"      Occurrences: {count:,}")
            print(f"      Example sessions: {', '.join(examples[:2])}")

            # Estimate if this could be a pattern worth automating
            if count >= 50:
                print(f"      💡 HIGH FREQUENCY - Consider reviewing for automation")

            print()

        if len(category_patterns) > 5:
            print(f"   ... and {len(category_patterns) - 5} more patterns in this category")
            print()

    print("=" * 80)
    print()

    # Summary
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total unique mixed-tool patterns (10+ occurrences): {len(patterns)}")
    print(f"Categories identified: {len(categorized)}")
    print()

    # Find highest frequency patterns
    top_10 = patterns[:10]
    high_freq = [p for p in patterns if p[1] >= 50]

    if high_freq:
        print(f"🔥 HIGH FREQUENCY PATTERNS (50+ occurrences): {len(high_freq)}")
        print()
        for pattern, count, examples in high_freq[:10]:
            print(f"   {' → '.join(pattern)}")
            print(f"   Occurrences: {count:,}")
            print()

    print("💡 ANALYSIS:")
    print()
    print("These patterns represent how the LLM orchestrates tools during workflows.")
    print("Most are:")
    print("  • Normal workflow progression (Read → Edit → Verify)")
    print("  • Context gathering (multiple Reads)")
    print("  • Planning and tracking (TodoWrite sequences)")
    print()
    print("For patterns to be worth automating, they must be:")
    print("  ✓ Deterministic (same input → same output)")
    print("  ✓ High frequency (50+ occurrences)")
    print("  ✓ Wasteful (LLM could be replaced by a function)")
    print()

    if not high_freq:
        print("✅ CONCLUSION: No high-frequency deterministic patterns found.")
        print("   This indicates the ADW workflows are already efficient.")
    else:
        print("⚠️  NEXT STEP: Review high-frequency patterns above.")
        print("   Manually inspect example sessions to determine if automation is possible.")

    print()
    conn.close()


if __name__ == "__main__":
    main()
