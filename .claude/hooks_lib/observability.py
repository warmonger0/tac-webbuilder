"""
Observability Module - Database + WebSocket event capture

Captures structured events for pattern learning and cost optimization:
- Stores events in PostgreSQL (hook_events table)
- Optionally broadcasts to WebSocket server
- Enables pattern detection and workflow analysis

Design: Deterministic database I/O, fails gracefully
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# PostgreSQL connection parameters from environment
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
    2. ADW_ID environment variable
    3. Current working directory (if in worktree)
    """
    if "WORKFLOW_ID" in os.environ:
        return os.environ["WORKFLOW_ID"]

    if "ADW_ID" in os.environ:
        return f"wf-{os.environ['ADW_ID']}"

    # Try to detect from cwd
    cwd = Path.cwd()
    if "trees" in cwd.parts:
        try:
            trees_index = cwd.parts.index("trees")
            if len(cwd.parts) > trees_index + 1:
                adw_id = cwd.parts[trees_index + 1]
                return f"wf-{adw_id}"
        except (ValueError, IndexError):
            pass

    return None


def detect_source_app() -> str:
    """Detect source application/ADW instance."""
    workflow_id = detect_workflow_id()
    if workflow_id:
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
        return False

    try:
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

    except Exception:
        return False


def send_to_websocket(event_data: Dict) -> bool:
    """
    Send event to WebSocket server (optional).

    Args:
        event_data: Complete event data

    Returns:
        True if successful, False otherwise
    """
    try:
        import requests

        server_url = os.environ.get("OBSERVABILITY_SERVER_URL", "http://localhost:8001/api/events")
        response = requests.post(server_url, json=event_data, timeout=2)
        return response.status_code == 200

    except Exception:
        return False


def log_to_file(event_data: Dict):
    """
    Log event to local file for debugging (fallback).

    Args:
        event_data: Complete event data
    """
    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "hook_events.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(event_data) + "\n")

    except Exception:
        pass


def capture_event(event_type: str, data: Dict):
    """
    Capture event to observability system.

    This is the main entry point called by hooks.

    Args:
        event_type: Event type (PreToolUse, PostToolUse, etc.)
        data: Hook data
    """
    try:
        # Extract relevant fields
        tool_name = data.get('tool_name', 'unknown')
        session_id = data.get('session_id', 'unknown')

        # Build event payload
        if event_type == "PreToolUse":
            payload = {
                "tool_name": tool_name,
                "tool_input": data.get('tool_input', {}),
                "session_id": session_id,
                "context": {
                    "cwd": str(Path.cwd()),
                }
            }
        elif event_type == "PostToolUse":
            payload = {
                "tool_name": tool_name,
                "tool_result": data.get('tool_result', {}),
                "duration_ms": data.get('duration_ms', 0),
                "session_id": session_id,
                "success": data.get('success', True),
                "context": {
                    "cwd": str(Path.cwd()),
                }
            }
        else:
            # Generic payload
            payload = data

        # Build complete event data
        event_data = {
            "event_id": generate_event_id(),
            "event_type": event_type,
            "source_app": detect_source_app(),
            "session_id": session_id,
            "workflow_id": detect_workflow_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "tool_name": tool_name if tool_name != 'unknown' else None,
            "chat_history": None,
        }

        # Send to database
        db_success = send_to_database(event_data)

        # Optionally send to WebSocket
        send_to_websocket(event_data)

        # Always log to file as fallback
        log_to_file(event_data)

        return db_success

    except Exception:
        # Silently fail - observability should never break workflows
        return False
