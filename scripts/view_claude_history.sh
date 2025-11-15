#!/bin/bash

# View Claude Code conversation history across all sessions
# Usage: ./view_claude_history.sh [search_term]

CLAUDE_DIR="$HOME/.claude/projects/-Users-Warmonger0-tac-tac-webbuilder"

echo "🔍 Claude Code Conversation History Viewer"
echo "==========================================="
echo ""

if [ -n "$1" ]; then
    echo "Searching for: '$1'"
    echo ""
fi

python3 << PYEOF
import json
import os
import sys
from datetime import datetime

project_dir = "$CLAUDE_DIR"
search_term = sys.argv[1].lower() if len(sys.argv) > 1 else None

# Collect all conversations
conversations = []

for filename in os.listdir(project_dir):
    if not filename.endswith('.jsonl') or filename.startswith('agent-'):
        continue

    filepath = os.path.join(project_dir, filename)
    stat = os.stat(filepath)
    mtime = datetime.fromtimestamp(stat.st_mtime)

    # Extract all user messages
    user_messages = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('type') == 'user':
                    msg = data.get('message', {}).get('content', '')
                    if isinstance(msg, str) and len(msg.strip()) > 3:
                        user_messages.append(msg)
            except:
                pass

    if not user_messages:
        continue

    # Filter by search term if provided
    if search_term:
        matched = any(search_term in msg.lower() for msg in user_messages)
        if not matched:
            continue

    conversations.append({
        'id': filename.replace('.jsonl', ''),
        'time': mtime,
        'size': stat.st_size,
        'msg_count': len(user_messages),
        'first_msg': user_messages[0],
        'all_msgs': user_messages
    })

# Sort by time (newest first)
conversations.sort(key=lambda x: x['time'], reverse=True)

# Display
for i, conv in enumerate(conversations[:50], 1):  # Show first 50
    time_str = conv['time'].strftime('%Y-%m-%d %H:%M')
    size_kb = conv['size'] // 1024

    print(f"\n{'─'*70}")
    print(f"#{i} │ {time_str} │ {conv['msg_count']} prompts │ {size_kb}KB")
    print(f"{'─'*70}")
    print(f"Session ID: {conv['id']}")
    print(f"\nFirst prompt:")
    preview = conv['first_msg'][:200]
    if len(conv['first_msg']) > 200:
        preview += "..."
    print(f"  {preview}")

    if len(conv['all_msgs']) > 1:
        print(f"\n  ... and {len(conv['all_msgs']) - 1} more prompts")

print(f"\n{'='*70}")
print(f"Total conversations: {len(conversations)}")
if search_term:
    print(f"Filtered by: '{search_term}'")
print(f"{'='*70}")
PYEOF
