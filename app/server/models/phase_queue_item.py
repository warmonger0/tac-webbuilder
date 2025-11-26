"""
PhaseQueueItem Model

Represents a single phase in the multi-phase workflow queue.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class PhaseQueueItem:
    """Represents a single phase in the queue"""

    def __init__(
        self,
        queue_id: str,
        parent_issue: int,
        phase_number: int,
        issue_number: Optional[int] = None,
        status: str = "queued",
        depends_on_phase: Optional[int] = None,
        phase_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        error_message: Optional[str] = None,
        adw_id: Optional[str] = None,
        pr_number: Optional[int] = None,
        priority: int = 50,
        queue_position: Optional[int] = None,
        ready_timestamp: Optional[str] = None,
        started_timestamp: Optional[str] = None,
    ):
        self.queue_id = queue_id
        self.parent_issue = parent_issue
        self.phase_number = phase_number
        self.issue_number = issue_number
        self.status = status
        self.depends_on_phase = depends_on_phase
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "queue_id": self.queue_id,
            "parent_issue": self.parent_issue,
            "phase_number": self.phase_number,
            "issue_number": self.issue_number,
            "status": self.status,
            "depends_on_phase": self.depends_on_phase,
            "phase_data": self.phase_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
            "adw_id": self.adw_id,
            "pr_number": self.pr_number,
            "priority": self.priority,
            "queue_position": self.queue_position,
            "ready_timestamp": self.ready_timestamp,
            "started_timestamp": self.started_timestamp,
        }

    @classmethod
    def from_db_row(cls, row) -> "PhaseQueueItem":
        """Create PhaseQueueItem from database row"""
        phase_data = json.loads(row["phase_data"]) if row["phase_data"] else {}

        # Safely access optional fields (may not exist in older database schemas)
        def safe_get(key, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default

        return cls(
            queue_id=row["queue_id"],
            parent_issue=row["parent_issue"],
            phase_number=row["phase_number"],
            issue_number=row["issue_number"],
            status=row["status"],
            depends_on_phase=row["depends_on_phase"],
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
