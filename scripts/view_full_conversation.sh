#!/bin/bash

# View full conversation by session ID
# Usage: ./view_full_conversation.sh <session_id>

if [ -z "$1" ]; then
    echo "Usage: $0 <session_id>"
    echo ""
    echo "Get session IDs from view_claude_history.sh"
    exit 1
fi

SESSION_ID="$1"
CLAUDE_DIR="$HOME/.claude/projects/-Users-Warmonger0-tac-tac-webbuilder"
FILE="$CLAUDE_DIR/$SESSION_ID.jsonl"

if [ ! -f "$FILE" ]; then
    echo "Error: Session file not found: $FILE"
    exit 1
fi

echo "📖 Full Conversation: $SESSION_ID"
echo "==========================================="
echo ""

python3 << PYEOF
import json

file_path = "$FILE"

with open(file_path, 'r') as f:
    msg_num = 0
    for line in f:
        try:
            data = json.loads(line)

            if data.get('type') == 'user':
                msg_num += 1
                timestamp = data.get('timestamp', 'N/A')
                msg = data.get('message', {}).get('content', '')

                if isinstance(msg, str) and len(msg.strip()) > 3:
                    print(f"\n{'='*70}")
                    print(f"USER MESSAGE #{msg_num}")
                    print(f"Time: {timestamp}")
                    print(f"{'='*70}")
                    print(msg)
                    print("")

        except Exception as e:
            pass

print(f"\n{'='*70}")
print(f"Total user messages: {msg_num}")
print(f"{'='*70}")
PYEOF
