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
        }

    @classmethod
    def from_db_row(cls, row) -> "PhaseQueueItem":
        """Create PhaseQueueItem from database row"""
        phase_data = json.loads(row["phase_data"]) if row["phase_data"] else {}
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
        )
