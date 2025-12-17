"""
PhaseQueueItem Model

Represents a single phase in the multi-phase workflow queue.
"""

import json
from datetime import datetime
from typing import Any


class PhaseQueueItem:
    """Represents a single phase in the queue"""

    def __init__(
        self,
        queue_id: str,
        feature_id: int,
        phase_number: int,
        issue_number: int | None = None,
        status: str = "queued",
        current_phase: str = "init",
        depends_on_phases: list[int] | None = None,
        phase_data: dict[str, Any] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        error_message: str | None = None,
        adw_id: str | None = None,
        pr_number: int | None = None,
        priority: int = 50,
        queue_position: int | None = None,
        ready_timestamp: str | None = None,
        started_timestamp: str | None = None,
    ):
        self.queue_id = queue_id
        self.feature_id = feature_id
        self.phase_number = phase_number
        self.issue_number = issue_number
        self.status = status
        self.current_phase = current_phase
        self.depends_on_phases = depends_on_phases or []
        self.phase_data = phase_data or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.error_message = error_message
        self.adw_id = adw_id
        self.pr_number = pr_number
        self.priority = priority
        self.queue_position = queue_position
        self.ready_timestamp = ready_timestamp
        self.started_timestamp = started_timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        # Helper to convert datetime to ISO string
        def to_iso(value):
            if value is None:
                return None
            return value.isoformat() if isinstance(value, datetime) else value

        return {
            "queue_id": self.queue_id,
            "feature_id": self.feature_id,
            "phase_number": self.phase_number,
            "issue_number": self.issue_number,
            "status": self.status,
            "current_phase": self.current_phase,
            "depends_on_phases": self.depends_on_phases,
            "phase_data": self.phase_data,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
            "error_message": self.error_message,
            "adw_id": self.adw_id,
            "pr_number": self.pr_number,
            "priority": self.priority,
            "queue_position": self.queue_position,
            "ready_timestamp": to_iso(self.ready_timestamp),
            "started_timestamp": to_iso(self.started_timestamp),
        }

    @classmethod
    def from_db_row(cls, row) -> "PhaseQueueItem":
        """Create PhaseQueueItem from database row"""
        # Handle both string (SQLite) and dict (PostgreSQL RealDictCursor) formats
        if row["phase_data"]:
            phase_data = json.loads(row["phase_data"]) if isinstance(row["phase_data"], str) else row["phase_data"]
        else:
            phase_data = {}

        # Handle depends_on_phases (JSONB in PostgreSQL, TEXT in SQLite)
        depends_on_phases_raw = row.get("depends_on_phases")
        if depends_on_phases_raw:
            if isinstance(depends_on_phases_raw, str):
                depends_on_phases = json.loads(depends_on_phases_raw)
            elif isinstance(depends_on_phases_raw, list):
                depends_on_phases = depends_on_phases_raw
            else:
                depends_on_phases = []
        else:
            depends_on_phases = []

        # Safely access optional fields (may not exist in older database schemas)
        def safe_get(key, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default

        return cls(
            queue_id=row["queue_id"],
            feature_id=row["feature_id"],
            phase_number=row["phase_number"],
            issue_number=row["issue_number"],
            status=row["status"],
            current_phase=safe_get("current_phase", "init"),
            depends_on_phases=depends_on_phases,
            phase_data=phase_data,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
            adw_id=safe_get("adw_id"),
            pr_number=safe_get("pr_number"),
            priority=safe_get("priority", 50),
            queue_position=safe_get("queue_position"),
            ready_timestamp=safe_get("ready_timestamp"),
            started_timestamp=safe_get("started_timestamp"),
        )
