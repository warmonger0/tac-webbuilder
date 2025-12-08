#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "psycopg2-binary",
# ]
# ///

"""
Pre-Tool-Use Hook - Thin orchestrator

Executes three deterministic operations:
1. Safety checks (may block dangerous operations)
2. Session logging (local debugging)
3. Observability capture (pattern learning)
"""

import json
import sys
from pathlib import Path

# Add hooks_lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks_lib"))

from safety import check_and_block
from session_logging import log_to_session
from observability import capture_event


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # 1. Safety checks (may exit with code 2 to block)
        check_and_block(input_data)

        # 2. Session logging (for debugging)
        log_to_session("PreToolUse", input_data)

        # 3. Observability capture (for pattern learning)
        capture_event("PreToolUse", input_data)

        sys.exit(0)

    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()