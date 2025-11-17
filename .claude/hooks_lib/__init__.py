"""
Hooks Library - Modular components for Claude Code hooks

This library provides reusable, deterministic modules for all hook operations:
- safety: Block dangerous operations (rm -rf, .env access)
- session_logging: Local file logging for debugging
- observability: Database + WebSocket event capture for pattern learning
"""

from . import safety
from . import session_logging
from . import observability

__all__ = ["safety", "session_logging", "observability"]
