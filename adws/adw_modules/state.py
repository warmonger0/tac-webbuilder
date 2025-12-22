"""State management for ADW composable architecture.

Provides persistent state management via file storage and
transient state passing between scripts via stdin/stdout.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from adw_modules.data_types import ADWStateData


class ADWState:
    """Container for ADW workflow state with file persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        """Initialize ADWState with a required ADW ID.
        
        Args:
            adw_id: The ADW ID for this state (required)
        """
        if not adw_id:
            raise ValueError("adw_id is required for ADWState")
        
        self.adw_id = adw_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"adw_id": self.adw_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs):
        """Update state with new key-value pairs.

        IMPORTANT: Does NOT accept 'status' or 'current_phase' - these are coordination
        state fields that belong in the database. Use PhaseQueueRepository for those.
        See docs/adw/state-management-ssot.md for complete SSoT rules.
        """
        # Core execution metadata fields (NOT coordination state)
        core_fields = {
            "adw_id", "issue_number", "branch_name", "plan_file", "issue_class",
            "worktree_path", "backend_port", "frontend_port", "model_set", "all_adws",
            "estimated_cost_total", "estimated_cost_breakdown",
            # Workflow context metadata
            "workflow_template", "model_used", "start_time", "end_time", "nl_input", "github_url",
            # Phase output metadata
            "baseline_errors", "external_build_results", "external_lint_results",
            "external_test_results", "review_results", "integration_checklist",
            "integration_checklist_markdown",
            # Multi-stage analysis results (Phase 1 extensions)
            "component_analysis", "dry_findings", "context_analysis", "multi_stage_metadata"
        }

        # Validate no forbidden fields (SSoT enforcement)
        forbidden_fields = {"status", "current_phase"}
        for key in kwargs:
            if key in forbidden_fields:
                raise ValueError(
                    f"Cannot update '{key}' in state file. Database is SSoT for coordination state. "
                    f"Use PhaseQueueRepository.update_status() instead. "
                    f"See docs/adw/state-management-ssot.md"
                )

        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_adw_id(self, adw_id: str):
        """Append an ADW ID to the all_adws list if not already present."""
        all_adws = self.data.get("all_adws", [])
        if adw_id not in all_adws:
            all_adws.append(adw_id)
            self.data["all_adws"] = all_adws

    def get_working_directory(self) -> str:
        """Get the working directory for this ADW instance.
        
        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path
        
        # Return main repo path (parent of adws directory)
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def get_state_path(self) -> str:
        """Get path to state file."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.adw_id, self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{adw_id}/adw_state.json.

        IMPORTANT: Does NOT save 'status' or 'current_phase' - these belong in database.
        See docs/adw/state-management-ssot.md for complete SSoT rules.
        """
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Validate no forbidden fields before saving (SSoT enforcement)
        forbidden_fields = {"status", "current_phase"}
        found_forbidden = [f for f in forbidden_fields if f in self.data]
        if found_forbidden:
            raise ValueError(
                f"Cannot save state with forbidden fields: {found_forbidden}. "
                f"These are coordination state fields that belong in database. "
                f"Use PhaseQueueRepository for status/current_phase. "
                f"See docs/adw/state-management-ssot.md"
            )

        # Create ADWStateData for validation of core execution metadata fields
        state_data = ADWStateData(
            adw_id=self.data.get("adw_id"),
            issue_number=self.data.get("issue_number"),
            branch_name=self.data.get("branch_name"),
            plan_file=self.data.get("plan_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            backend_port=self.data.get("backend_port"),
            frontend_port=self.data.get("frontend_port"),
            model_set=self.data.get("model_set", "base"),
            all_adws=self.data.get("all_adws", []),
            estimated_cost_total=self.data.get("estimated_cost_total"),
            estimated_cost_breakdown=self.data.get("estimated_cost_breakdown"),
            # Workflow context metadata (NOT coordination state)
            workflow_template=self.data.get("workflow_template"),
            model_used=self.data.get("model_used"),
            start_time=self.data.get("start_time"),
            nl_input=self.data.get("nl_input"),
            github_url=self.data.get("github_url"),
            # Multi-stage analysis results (Phase 1 extensions)
            component_analysis=self.data.get("component_analysis"),
            dry_findings=self.data.get("dry_findings"),
            context_analysis=self.data.get("context_analysis"),
            multi_stage_metadata=self.data.get("multi_stage_metadata"),
        )

        # Start with validated core fields
        save_data = state_data.model_dump()

        # Add extra fields (like external_build_results, external_test_results, etc.)
        core_field_names = set(state_data.model_fields.keys())
        for key, value in self.data.items():
            if key not in core_field_names:
                # Double-check no forbidden fields slip through
                if key in forbidden_fields:
                    continue  # Skip forbidden fields silently
                save_data[key] = value

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(save_data, f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, adw_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["ADWState"]:
        """Load state from file if it exists."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        state_path = os.path.join(project_root, "agents", adw_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate core fields with ADWStateData
            # This will raise an error if core fields are invalid
            state_data = ADWStateData(**{k: v for k, v in data.items() if k in ADWStateData.model_fields})

            # Create ADWState instance
            state = cls(state_data.adw_id)
            # Use full data to preserve extra fields (like external_build_results)
            state.data = data

            if logger:
                logger.info(f"🔍 Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(data, indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["ADWState"]:
        """Read state from stdin if available (for piped input).

        Returns None if no piped input is available (stdin is a tty).
        """
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            adw_id = data.get("adw_id")
            if not adw_id:
                return None  # No valid state without adw_id
            state = cls(adw_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "adw_id": self.data.get("adw_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "plan_file": self.data.get("plan_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "backend_port": self.data.get("backend_port"),
            "frontend_port": self.data.get("frontend_port"),
            "all_adws": self.data.get("all_adws", []),
        }
        print(json.dumps(output_data, indent=2))
