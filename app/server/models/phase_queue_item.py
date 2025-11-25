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
        parent_issue: int,
        phase_number: int,
        issue_number: int | None = None,
        status: str = "queued",
        depends_on_phase: int | None = None,
        phase_data: dict[str, Any] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        error_message: str | None = None,
        adw_id: str | None = None,
        pr_number: int | None = None,
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

    def to_dict(self) -> dict[str, Any]:
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
        }

    @classmethod
    def from_db_row(cls, row) -> "PhaseQueueItem":
        """Create PhaseQueueItem from database row"""
        phase_data = json.loads(row["phase_data"]) if row["phase_data"] else {}

        # Safely access adw_id and pr_number (may not exist in older database schemas)
        try:
            adw_id = row["adw_id"]
        except (KeyError, IndexError):
            adw_id = None

        try:
            pr_number = row["pr_number"]
        except (KeyError, IndexError):
            pr_number = None

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
            adw_id=adw_id,
            pr_number=pr_number,
        )
