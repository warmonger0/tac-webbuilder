"""
Session Logging Module - Local file logging for debugging

Logs all hook events to session-specific files for debugging and analysis.
Provides structured JSONL logs that can be reviewed later.

Design: Deterministic file I/O, always succeeds (creates dirs if needed)
"""

import json
from pathlib import Path
from typing import Dict


def ensure_session_log_dir(session_id: str) -> Path:
    """
    Ensure session log directory exists.

    Args:
        session_id: Session identifier

    Returns:
        Path to session log directory
    """
    log_dir = Path.home() / ".claude" / "sessions" / session_id
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_to_session(event_type: str, data: Dict):
    """
    Log event data to session-specific file.

    Args:
        event_type: Type of event (PreToolUse, PostToolUse, etc.)
        data: Event data to log
    """
    try:
        session_id = data.get('session_id', 'unknown')
        log_dir = ensure_session_log_dir(session_id)

        # Use snake_case filename
        filename = f"{event_type.lower().replace('tooluse', 'tool_use')}.json"
        log_path = log_dir / filename

        # Read existing data
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(data)

        # Write back
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

    except Exception:
        # Silently fail - logging should never break hooks
        pass
