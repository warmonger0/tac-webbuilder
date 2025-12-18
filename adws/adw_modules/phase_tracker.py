"""Phase completion tracking for workflow resume functionality.

This module provides utilities to track which phases have been completed
in a workflow, allowing workflows to resume from where they paused rather
than restarting from Phase 1.

The tracker stores completion data in agents/{adw_id}/completed_phases.json:
{
    "completed": ["Plan", "Validate", "Build", "Lint"],
    "current": "Test",
    "last_updated": "2025-12-18T10:30:45"
}
"""

import json
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path


COMPLETION_FILENAME = "completed_phases.json"


class PhaseTracker:
    """Tracks phase completion for workflow resume capability."""

    def __init__(self, adw_id: str):
        """Initialize PhaseTracker for an ADW workflow.

        Args:
            adw_id: The ADW ID for this workflow
        """
        if not adw_id:
            raise ValueError("adw_id is required for PhaseTracker")

        self.adw_id = adw_id
        self.completion_file = self._get_completion_file_path()

    def _get_completion_file_path(self) -> Path:
        """Get path to the completion tracking file."""
        # Get project root (parent of adws directory)
        project_root = Path(__file__).resolve().parent.parent.parent
        return project_root / "agents" / self.adw_id / COMPLETION_FILENAME

    def load_completion_data(self) -> dict:
        """Load completion data from file.

        Returns:
            Dict with 'completed' list, 'current' phase, 'last_updated' timestamp
        """
        if not self.completion_file.exists():
            return {
                "completed": [],
                "current": None,
                "last_updated": None
            }

        try:
            with open(self.completion_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, return empty state
            return {
                "completed": [],
                "current": None,
                "last_updated": None
            }

    def save_completion_data(self, data: dict) -> None:
        """Save completion data to file.

        Args:
            data: Dict with 'completed' list, 'current' phase, 'last_updated'
        """
        # Ensure parent directory exists
        self.completion_file.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        data["last_updated"] = datetime.now().isoformat()

        with open(self.completion_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_phase_completed(self, phase_name: str) -> bool:
        """Check if a phase has been completed.

        Args:
            phase_name: Name of the phase (e.g., "Plan", "Build", "Test")

        Returns:
            True if phase is marked as completed
        """
        data = self.load_completion_data()
        return phase_name in data.get("completed", [])

    def mark_phase_completed(self, phase_name: str) -> None:
        """Mark a phase as completed.

        Args:
            phase_name: Name of the phase to mark as completed
        """
        data = self.load_completion_data()

        if phase_name not in data.get("completed", []):
            if "completed" not in data:
                data["completed"] = []
            data["completed"].append(phase_name)

        # Update current phase to next (will be set by workflow)
        data["current"] = None

        self.save_completion_data(data)

    def set_current_phase(self, phase_name: str) -> None:
        """Set the currently running phase.

        Args:
            phase_name: Name of the phase currently running
        """
        data = self.load_completion_data()
        data["current"] = phase_name
        self.save_completion_data(data)

    def get_completed_phases(self) -> List[str]:
        """Get list of completed phases.

        Returns:
            List of phase names that have been completed
        """
        data = self.load_completion_data()
        return data.get("completed", [])

    def get_current_phase(self) -> Optional[str]:
        """Get the currently running phase.

        Returns:
            Name of current phase, or None if not set
        """
        data = self.load_completion_data()
        return data.get("current")

    def reset(self) -> None:
        """Reset all completion tracking (start fresh)."""
        data = {
            "completed": [],
            "current": None,
            "last_updated": None
        }
        self.save_completion_data(data)

    def get_next_phase_to_run(self, all_phases: List[str]) -> Optional[str]:
        """Determine which phase should run next based on completion state.

        Args:
            all_phases: Ordered list of all phases in the workflow

        Returns:
            Name of next phase to run, or None if all complete
        """
        completed = set(self.get_completed_phases())

        # Find first phase that hasn't been completed
        for phase in all_phases:
            if phase not in completed:
                return phase

        # All phases completed
        return None

    def should_skip_phase(self, phase_name: str, resume_mode: bool) -> bool:
        """Determine if a phase should be skipped during resume.

        Args:
            phase_name: Name of the phase to check
            resume_mode: Whether workflow is in resume mode

        Returns:
            True if phase should be skipped (already completed and resuming)
        """
        if not resume_mode:
            return False

        return self.is_phase_completed(phase_name)
