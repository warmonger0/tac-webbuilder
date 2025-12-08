#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "psycopg2-binary",
# ]
# ///

"""
Post-Tool-Use Hook - Thin orchestrator

Executes two deterministic operations:
1. Session logging (local debugging)
2. Observability capture (pattern learning)
"""

import json
import sys
from pathlib import Path

# Add hooks_lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks_lib"))

from session_logging import log_to_session
from observability import capture_event


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # 1. Session logging (for debugging)
        log_to_session("PostToolUse", input_data)

        # 2. Observability capture (for pattern learning)
        capture_event("PostToolUse", input_data)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)


if __name__ == '__main__':
    main()