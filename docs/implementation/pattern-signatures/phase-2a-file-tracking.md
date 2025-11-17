# Phase 2A: File Access Tracking - Implementation Guide

**Duration:** Days 1-2 (2 days)
**Dependencies:** Phase 1 complete (pattern detection working)
**Part of:** Phase 2 Context Efficiency Analysis
**Status:** Ready to implement

---

## Overview

Capture file access events during workflow execution by integrating with Claude Code hooks. This is the foundation for context efficiency analysis.

**Key Insight:** Most workflows load 100+ files but only access 20-30 files. We need to track which files are actually used to optimize future context loading.

---

## Goals

1. ✅ Capture file access events from tool usage
2. ✅ Store events in `hook_events` table
3. ✅ Link events to workflow_id
4. ✅ Support Read, Edit, Write, Grep, Glob tools
5. ✅ Enable querying by workflow or pattern

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  CLAUDE CODE WORKFLOW EXECUTING                       │
│  Tools used: Read, Edit, Write, Grep, Glob           │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  POST_TOOL_USE HOOK                                   │
│  .claude/hooks/post_tool_use.py                       │
│  • Detects tool name                                  │
│  • Extracts file paths from tool parameters           │
│  • Calls context_tracker.track_file_access()          │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT TRACKER                                      │
│  app/server/core/context_tracker.py                   │
│  • Validates event data                               │
│  • Normalizes file paths                              │
│  • Inserts into hook_events table                     │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  DATABASE: hook_events TABLE                          │
│  • session_id (workflow identifier)                   │
│  • event_type: 'FileAccess'                           │
│  • payload: {tool_name, file_path, access_type}       │
│  • created_at timestamp                               │
└──────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 2A.1: Create Context Tracker Module

**File:** `app/server/core/context_tracker.py`

**Purpose:** Core logic for tracking file access events

**Key Functions:**

```python
"""
Context tracking for workflow file access monitoring.

Captures which files are accessed during workflow execution to enable
context efficiency analysis and optimization.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ContextTracker:
    """Tracks file access during workflow execution."""

    def __init__(self, db_path: str = "app/server/db/workflow_history.db"):
        self.db_path = db_path

    def track_file_access(
        self,
        session_id: str,
        tool_name: str,
        file_path: str,
        access_type: str = "read"
    ) -> bool:
        """
        Record a file access event.

        Args:
            session_id: Claude Code session ID (workflow identifier)
            tool_name: Name of tool used (Read, Edit, Write, Grep, Glob)
            file_path: Path to file accessed
            access_type: 'read' or 'write'

        Returns:
            True if event recorded successfully

        Example:
            tracker.track_file_access(
                session_id="abc123",
                tool_name="Read",
                file_path="/app/server/routes/api.py",
                access_type="read"
            )
        """
        try:
            # Normalize file path
            normalized_path = self._normalize_path(file_path)

            # Create event payload
            payload = {
                "tool_name": tool_name,
                "file_path": normalized_path,
                "access_type": access_type,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Insert into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO hook_events (
                    session_id,
                    event_type,
                    payload,
                    created_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                session_id,
                "FileAccess",
                json.dumps(payload)
            ))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error tracking file access: {e}")
            return False

    def _normalize_path(self, file_path: str) -> str:
        """
        Normalize file path to be relative to project root.

        Converts:
            /Users/user/project/app/server/api.py → app/server/api.py
            ./app/server/api.py → app/server/api.py
        """
        # Remove leading slashes and ./
        path = file_path.lstrip('./')

        # If absolute path, try to extract relative portion
        if path.startswith('/'):
            # Look for common project directories
            for marker in ['app/', 'tests/', 'scripts/', 'adws/', 'docs/']:
                if marker in path:
                    idx = path.index(marker)
                    path = path[idx:]
                    break

        return path

    def get_files_accessed(
        self,
        session_id: str,
        tool_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get all files accessed during a workflow.

        Args:
            session_id: Workflow session ID
            tool_filter: Optional list of tool names to filter by

        Returns:
            List of file access records with metadata

        Example:
            files = tracker.get_files_accessed(
                session_id="abc123",
                tool_filter=["Read", "Edit"]
            )
            # Returns: [
            #   {
            #     "file_path": "app/server/api.py",
            #     "tool_name": "Read",
            #     "access_type": "read",
            #     "timestamp": "2025-11-17T10:30:00"
            #   },
            #   ...
            # ]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT payload, created_at
            FROM hook_events
            WHERE session_id = ?
              AND event_type = 'FileAccess'
            ORDER BY created_at
        """, (session_id,))

        results = []
        for row in cursor.fetchall():
            payload = json.loads(row[0])

            # Filter by tool if specified
            if tool_filter and payload["tool_name"] not in tool_filter:
                continue

            results.append(payload)

        conn.close()
        return results

    def get_unique_files_accessed(self, session_id: str) -> List[str]:
        """
        Get unique list of file paths accessed during workflow.

        Args:
            session_id: Workflow session ID

        Returns:
            Sorted list of unique file paths

        Example:
            files = tracker.get_unique_files_accessed("abc123")
            # Returns: [
            #   "app/server/api.py",
            #   "app/server/models.py",
            #   "tests/test_api.py"
            # ]
        """
        files = self.get_files_accessed(session_id)
        unique_paths = set(f["file_path"] for f in files)
        return sorted(unique_paths)


# Singleton instance
_tracker_instance = None

def get_tracker() -> ContextTracker:
    """Get singleton ContextTracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ContextTracker()
    return _tracker_instance
```

**Testing:**

```python
# test_context_tracker.py
import pytest
from app.server.core.context_tracker import ContextTracker

def test_track_file_access():
    tracker = ContextTracker(db_path=":memory:")

    # Create test table
    # (Assume hook_events table exists)

    success = tracker.track_file_access(
        session_id="test123",
        tool_name="Read",
        file_path="/Users/user/project/app/server/api.py",
        access_type="read"
    )

    assert success is True

    # Verify stored
    files = tracker.get_unique_files_accessed("test123")
    assert "app/server/api.py" in files

def test_path_normalization():
    tracker = ContextTracker()

    # Test various path formats
    assert tracker._normalize_path("./app/server/api.py") == "app/server/api.py"
    assert tracker._normalize_path("/abs/path/app/server/api.py") == "app/server/api.py"
```

---

### Step 2A.2: Hook Integration

**File:** `.claude/hooks/post_tool_use.py`

**Purpose:** Intercept tool usage and call context tracker

```python
"""
Post-tool-use hook for tracking file access during workflows.

This hook fires after every tool invocation in Claude Code,
allowing us to capture file access patterns for context optimization.
"""

import json
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app" / "server"))

from core.context_tracker import get_tracker


def extract_file_paths(tool_name: str, parameters: dict) -> list[str]:
    """
    Extract file paths from tool parameters.

    Different tools store file paths in different parameter names:
    - Read: 'file_path'
    - Edit: 'file_path'
    - Write: 'file_path'
    - Grep: 'path' (optional, defaults to cwd)
    - Glob: 'path' (optional, defaults to cwd)
    """
    paths = []

    if tool_name in ["Read", "Edit", "Write"]:
        if "file_path" in parameters:
            paths.append(parameters["file_path"])

    elif tool_name in ["Grep", "Glob"]:
        if "path" in parameters:
            paths.append(parameters["path"])

    return paths


def determine_access_type(tool_name: str) -> str:
    """Determine if tool is reading or writing."""
    if tool_name in ["Read", "Grep", "Glob"]:
        return "read"
    elif tool_name in ["Edit", "Write"]:
        return "write"
    else:
        return "unknown"


def hook(data: dict) -> dict:
    """
    Post-tool-use hook entry point.

    Args:
        data: Hook data from Claude Code
            {
                "session_id": "abc123",
                "tool_name": "Read",
                "parameters": {"file_path": "/path/to/file.py"},
                "result": {...}
            }

    Returns:
        Unmodified data (hooks are read-only)
    """
    try:
        tool_name = data.get("tool_name")

        # Only track file operation tools
        if tool_name not in ["Read", "Edit", "Write", "Grep", "Glob"]:
            return data

        session_id = data.get("session_id")
        parameters = data.get("parameters", {})

        if not session_id:
            return data

        # Extract file paths
        file_paths = extract_file_paths(tool_name, parameters)

        if not file_paths:
            return data

        # Track each file access
        tracker = get_tracker()
        access_type = determine_access_type(tool_name)

        for file_path in file_paths:
            tracker.track_file_access(
                session_id=session_id,
                tool_name=tool_name,
                file_path=file_path,
                access_type=access_type
            )

    except Exception as e:
        # Don't break workflow on tracking errors
        print(f"[ContextTracker] Error in post_tool_use hook: {e}", file=sys.stderr)

    # Always return data unmodified
    return data


# Hook configuration
if __name__ == "__main__":
    # Test hook locally
    test_data = {
        "session_id": "test123",
        "tool_name": "Read",
        "parameters": {"file_path": "app/server/api.py"}
    }
    result = hook(test_data)
    print(f"Hook result: {result}")
```

---

### Step 2A.3: Enable Hook in Claude Code

**File:** `.claude/config.yaml`

Ensure hooks are enabled:

```yaml
hooks:
  post_tool_use:
    enabled: true
    script: .claude/hooks/post_tool_use.py
```

---

### Step 2A.4: Testing Strategy

**Manual Test:**

```bash
# 1. Run a simple workflow that uses file tools
cd adws/
uv run adw_test_iso.py 999

# 2. Check hook_events table for FileAccess events
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) as event_count
FROM hook_events
WHERE event_type = 'FileAccess';
"

# Expected: event_count > 0

# 3. Inspect actual events
sqlite3 app/server/db/workflow_history.db "
SELECT session_id, payload, created_at
FROM hook_events
WHERE event_type = 'FileAccess'
ORDER BY created_at DESC
LIMIT 5;
"

# Expected: See JSON payloads with file paths
```

**Unit Test:**

```bash
cd app/server
uv run pytest tests/test_context_tracker.py -v
```

---

## Database Schema Reference

The `hook_events` table already exists (from migration 004):

```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'FileAccess', 'ToolUse', etc.
    payload TEXT NOT NULL,      -- JSON blob
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hook_events_session ON hook_events(session_id);
CREATE INDEX idx_hook_events_type ON hook_events(event_type);
```

**FileAccess Payload Schema:**

```json
{
  "tool_name": "Read",
  "file_path": "app/server/api.py",
  "access_type": "read",
  "timestamp": "2025-11-17T10:30:00.123Z"
}
```

---

## Success Criteria

- [ ] ✅ `app/server/core/context_tracker.py` implemented (300 lines)
- [ ] ✅ `.claude/hooks/post_tool_use.py` implemented (100 lines)
- [ ] ✅ Hook enabled in `.claude/config.yaml`
- [ ] ✅ Unit tests passing
- [ ] ✅ Manual test shows FileAccess events in database
- [ ] ✅ Events linked to correct session_id
- [ ] ✅ File paths normalized correctly

---

## Troubleshooting

### Issue: No events captured

**Check:**
1. Hook enabled in config: `.claude/config.yaml`
2. Hook script executable: `chmod +x .claude/hooks/post_tool_use.py`
3. Database path correct in tracker
4. Workflow actually using file tools

### Issue: Duplicate events

**Expected behavior:** Same file accessed multiple times = multiple events
This is intentional for understanding access patterns.

### Issue: Path normalization not working

**Debug:**
```python
from app.server.core.context_tracker import ContextTracker
tracker = ContextTracker()
print(tracker._normalize_path("/your/problematic/path"))
```

Adjust `_normalize_path()` logic as needed.

---

## Next Steps

After Phase 2A completion:
→ **Phase 2B: Context Efficiency Analysis** (`PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`)

Phase 2B will use the file access events captured here to calculate context efficiency metrics and identify token waste.

---

## Deliverables Checklist

- [ ] `app/server/core/context_tracker.py` (300 lines)
- [ ] `.claude/hooks/post_tool_use.py` (100 lines)
- [ ] Unit tests in `tests/test_context_tracker.py`
- [ ] Hook enabled in config
- [ ] Manual test validation
- [ ] Documentation updated

**Total Lines of Code:** ~400 lines

**Estimated Time:** 2 days (8-12 hours)

---

**Status:** Ready to implement
**Next Phase:** 2B Context Efficiency Analysis
**Blocked by:** None (Phase 1 optional dependency)
