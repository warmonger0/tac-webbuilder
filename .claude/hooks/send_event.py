#!/usr/bin/env python3
"""
Send Event Utility - Universal event dispatcher for Claude Code hooks

This utility is called by all hook scripts to send structured event data
to the observability system (database + optional WebSocket server).

Usage:
    python send_event.py --type PreToolUse --payload '{...}' [--add-chat] [--summarize]

Arguments:
    --type: Event type (PreToolUse, PostToolUse, UserPromptSubmit, etc.)
    --payload: JSON payload
    --add-chat: Include chat history in event
    --summarize: Generate AI summary of event
    --workflow-id: Override workflow ID detection
    --source-app: Override source app detection
"""

import argparse
import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# PostgreSQL connection parameters from environment
# These should match the values in app/server/.env
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "tac_webbuilder"),
    "user": os.getenv("POSTGRES_USER", "tac_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "changeme"),
}


def generate_event_id() -> str:
    """Generate unique event ID."""
    timestamp = datetime.utcnow().isoformat()
    random_data = os.urandom(8).hex()
    return f"evt-{hashlib.md5(f'{timestamp}{random_data}'.encode()).hexdigest()[:16]}"


def detect_workflow_id() -> Optional[str]:
    """
    Detect current workflow ID from environment or context.

    Checks:
    1. WORKFLOW_ID environment variable
    2. ADW_ID environment variable (for ADW workflows)
    3. Parent process name/cwd
    """
    # Check environment variables
    if "WORKFLOW_ID" in os.environ:
        return os.environ["WORKFLOW_ID"]

    if "ADW_ID" in os.environ:
        return f"wf-{os.environ['ADW_ID']}"

    # Try to detect from current working directory
    cwd = Path.cwd()
    if "trees" in cwd.parts:
        # We're in a worktree, extract ADW ID
        try:
            trees_index = cwd.parts.index("trees")
            if len(cwd.parts) > trees_index + 1:
                adw_id = cwd.parts[trees_index + 1]
                return f"wf-{adw_id}"
        except (ValueError, IndexError):
            pass

    return None


def detect_source_app() -> str:
    """
    Detect source application/ADW instance.

    Returns:
        Source identifier like 'main_adw', 'test_adw', 'build_adw'
    """
    workflow_id = detect_workflow_id()

    if workflow_id:
        # Try to determine ADW type from workflow_id or context
        # For now, just return a generic identifier
        return f"adw_{workflow_id}"

    return "unknown"


def send_to_database(event_data: Dict) -> bool:
    """
    Send event to PostgreSQL database.

    Args:
        event_data: Complete event data

    Returns:
        True if successful, False otherwise
    """
    if not POSTGRES_AVAILABLE:
        print("Warning: psycopg2 not available, skipping database logging", file=sys.stderr)
        return False

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hook_events (
                event_id, event_type, source_app, session_id, workflow_id,
                timestamp, payload, tool_name, chat_history, processed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event_data["event_id"],
            event_data["event_type"],
            event_data["source_app"],
            event_data.get("session_id"),
            event_data.get("workflow_id"),
            event_data["timestamp"],
            json.dumps(event_data["payload"]),
            event_data.get("tool_name"),
            json.dumps(event_data.get("chat_history")) if event_data.get("chat_history") else None,
            0  # not processed yet
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Error sending event to database: {e}", file=sys.stderr)
        return False


def send_to_websocket(event_data: Dict) -> bool:
    """
    Send event to WebSocket server (if running).

    Args:
        event_data: Complete event data

    Returns:
        True if successful, False otherwise
    """
    try:
        import requests

        # Try to send to WebSocket server
        # (This would be implemented if you set up the observability server)
        server_url = os.environ.get("OBSERVABILITY_SERVER_URL", "http://localhost:8001/api/events")

        response = requests.post(
            server_url,
            json=event_data,
            timeout=2  # Quick timeout to not block hooks
        )

        return response.status_code == 200

    except Exception:
        # WebSocket server not running or not available
        # This is okay - we still have database logging
        return False


def log_to_file(event_data: Dict):
    """
    Log event to local file for debugging.

    Args:
        event_data: Complete event data
    """
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "hook_events.jsonl"

    with open(log_file, "a") as f:
        f.write(json.dumps(event_data) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Send hook event to observability system")
    parser.add_argument("--type", required=True, help="Event type")
    parser.add_argument("--payload", required=True, help="JSON payload")
    parser.add_argument("--add-chat", action="store_true", help="Include chat history")
    parser.add_argument("--summarize", action="store_true", help="Generate AI summary")
    parser.add_argument("--workflow-id", help="Override workflow ID")
    parser.add_argument("--source-app", help="Override source app")
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--tool-name", help="Tool name (for tool-related events)")

    args = parser.parse_args()

    # Parse payload
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON payload: {e}", file=sys.stderr)
        return 1

    # Build event data
    event_data = {
        "event_id": generate_event_id(),
        "event_type": args.type,
        "source_app": args.source_app or detect_source_app(),
        "session_id": args.session_id,
        "workflow_id": args.workflow_id or detect_workflow_id(),
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
        "tool_name": args.tool_name,
        "chat_history": None,  # TODO: Implement if --add-chat is set
    }

    # Send to database
    db_success = send_to_database(event_data)

    # Attempt to send to WebSocket (optional)
    send_to_websocket(event_data)

    # Always log to file for debugging
    log_to_file(event_data)

    if db_success:
        print(f"✅ Event logged: {event_data['event_id']}", file=sys.stderr)
        return 0
    else:
        print(f"⚠️  Event logged to file only: {event_data['event_id']}", file=sys.stderr)
        return 0  # Still return success - file logging worked


if __name__ == "__main__":
    sys.exit(main())
