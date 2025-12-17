"""
State validation middleware for ADW phases.

Validates phase inputs BEFORE execution (fail fast) and outputs AFTER
execution (ensure completeness) using contracts from docs/adw/phase-contracts.md
and SSoT rules from docs/adw/state-management-ssot.md.

Usage:
    validator = StateValidator(phase='test')

    # Before phase execution
    result = validator.validate_inputs(issue_number)
    if not result.is_valid:
        raise ValueError(f"Invalid inputs: {result.errors}")

    # After phase execution
    result = validator.validate_outputs(issue_number)
    if not result.is_valid:
        raise ValueError(f"Incomplete outputs: {result.errors}")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@dataclass
class ValidationResult:
    """Result of state validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self):
        return self.is_valid


class StateValidator:
    """Validates ADW phase inputs and outputs."""

    # Phase contracts (from docs/adw/phase-contracts.md)
    PHASE_CONTRACTS = {
        'plan': {
            'requires': ['github_issue', 'github_token', 'database_connection'],
            'produces': ['SDLC_PLAN.md', 'adw_state.json', 'phase_queue_record']
        },
        'validate': {
            'requires': ['SDLC_PLAN.md', 'adw_state.json', 'phase_queue_record'],
            'produces': ['validated_plan', 'baseline_errors']
        },
        'build': {
            'requires': ['SDLC_PLAN.md', 'worktree', 'adw_state.json'],
            'produces': ['code_changes', 'modified_files']
        },
        'lint': {
            'requires': ['source_files', 'worktree'],
            'produces': ['lint_pass_or_fail', 'lint_report']
        },
        'test': {
            'requires': ['source_files', 'test_files', 'worktree'],
            'produces': ['test_pass_or_fail', 'test_report']
        },
        'review': {
            'requires': ['code_changes', 'worktree'],
            'produces': ['review_comments', 'review_status']
        },
        'document': {
            'requires': ['code_changes', 'worktree'],
            'produces': ['updated_docs', 'documentation_changes']
        },
        'ship': {
            'requires': ['all_phases_passed', 'worktree', 'clean_tests'],
            'produces': ['pull_request', 'pr_url']
        },
        'cleanup': {
            'requires': ['pr_created_or_closed', 'worktree_path'],
            'produces': ['worktree_removed', 'cleanup_complete']
        },
        'verify': {
            'requires': ['pr_merged', 'issue_number'],
            'produces': ['verification_report', 'verification_status']
        }
    }

    def __init__(self, phase: str):
        """Initialize validator for specific phase.

        Args:
            phase: Phase name (plan, validate, build, etc.)
        """
        if phase not in self.PHASE_CONTRACTS:
            raise ValueError(f"Unknown phase: {phase}")
        self.phase = phase
        self.contract = self.PHASE_CONTRACTS[phase]

    def validate_inputs(self, issue_number: int) -> ValidationResult:
        """Validate phase inputs before execution.

        Args:
            issue_number: GitHub issue number

        Returns:
            ValidationResult with is_valid and any errors/warnings
        """
        errors = []
        warnings = []

        # Get workflow state from database (SSoT for coordination)
        try:
            # Set up database imports using helper function
            from adw_modules.utils import setup_database_imports
            setup_database_imports()

            from repositories.phase_queue_repository import PhaseQueueRepository
            repo = PhaseQueueRepository()
            # Get all phases for this issue (feature_id == issue_number in ADW context)
            workflows = repo.get_all_by_feature_id(issue_number)

            if not workflows:
                errors.append(f"Workflow not found for issue {issue_number}")
                return ValidationResult(False, errors, warnings)

            # Use the first workflow (there should only be one per issue)
            workflow = workflows[0]
        except Exception as e:
            errors.append(f"Failed to query database: {str(e)}")
            return ValidationResult(False, errors, warnings)

        # Get execution metadata from file (SSoT for metadata)
        state = {}
        worktree_path = None

        if workflow and workflow.adw_id:
            worktree_path = self._get_worktree_path(workflow.adw_id)
            if worktree_path:
                state_file = Path(worktree_path) / 'adw_state.json'
                if state_file.exists():
                    try:
                        with open(state_file) as f:
                            state = json.load(f)
                    except Exception as e:
                        warnings.append(f"Failed to load state file: {str(e)}")

        # Validate phase-specific requirements
        validation_method = getattr(self, f'_validate_{self.phase}_inputs', None)
        if validation_method:
            phase_errors = validation_method(workflow, state, worktree_path)
            errors.extend(phase_errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_outputs(self, issue_number: int) -> ValidationResult:
        """Validate phase outputs after execution.

        Args:
            issue_number: GitHub issue number

        Returns:
            ValidationResult with is_valid and any errors/warnings
        """
        errors = []
        warnings = []

        # Get workflow state
        try:
            # Set up database imports using helper function
            from adw_modules.utils import setup_database_imports
            setup_database_imports()

            from repositories.phase_queue_repository import PhaseQueueRepository
            repo = PhaseQueueRepository()
            # Get all phases for this issue (feature_id == issue_number in ADW context)
            workflows = repo.get_all_by_feature_id(issue_number)

            if not workflows:
                # No database record - this is a standalone ADW run
                # Fall back to file-based validation without database SSoT
                warnings.append(f"No database record for issue {issue_number} - using file-based validation (standalone mode)")
                workflow = None
            else:
                # Use the first workflow (there should only be one per issue)
                workflow = workflows[0]
        except Exception as e:
            # Database query failed - fall back to file-based validation
            warnings.append(f"Database query failed: {str(e)} - using file-based validation")
            workflow = None

        # Get execution metadata
        state = {}
        worktree_path = None
        adw_id = None

        # Initialize logger for debug output
        import logging
        logger = logging.getLogger(__name__)

        if workflow and workflow.adw_id:
            adw_id = workflow.adw_id
            logger.debug(f"[validate_outputs] Found workflow in DB with adw_id={adw_id}")
            worktree_path = self._get_worktree_path(adw_id)
            logger.debug(f"[validate_outputs] _get_worktree_path returned: {worktree_path}")

            # If worktree not found, database may have stale/wrong adw_id
            # Fall back to searching agents/ directories by issue_number
            if not worktree_path:
                warnings.append(f"Worktree not found for DB adw_id={adw_id}, searching by issue_number")
                workflow = None  # Trigger fallback search

        if not workflow or not worktree_path:
            # No database record OR worktree not found - try to find by searching agent directories
            # Get project root (this file is at project_root/adws/utils/state_validator.py)
            project_root = Path(__file__).parent.parent.parent
            agents_dir = project_root / 'agents'
            if agents_dir.exists():
                # Find most recent agent directory for this issue
                for agent_dir in sorted(agents_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                    if agent_dir.is_dir():
                        state_file = agent_dir / 'adw_state.json'
                        if state_file.exists():
                            try:
                                with open(state_file) as f:
                                    temp_state = json.load(f)
                                    if str(temp_state.get('issue_number')) == str(issue_number):
                                        adw_id = temp_state.get('adw_id')
                                        worktree_path = temp_state.get('worktree_path')
                                        state = temp_state
                                        warnings.append(f"Found worktree via file search: {adw_id}")
                                        break
                            except Exception:
                                continue

        if worktree_path and not state:
            state_file = Path(worktree_path) / 'adw_state.json'
            if state_file.exists():
                try:
                    with open(state_file) as f:
                        state = json.load(f)
                except Exception as e:
                    warnings.append(f"Failed to load state file: {str(e)}")

        # Validate phase-specific outputs
        validation_method = getattr(self, f'_validate_{self.phase}_outputs', None)
        if validation_method:
            phase_errors = validation_method(workflow, state, worktree_path)
            errors.extend(phase_errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Phase-specific input validators

    def _validate_plan_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate plan phase inputs."""
        errors = []

        # GitHub token must be available
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            errors.append("GITHUB_TOKEN environment variable not set")

        # Database connection verified by workflow existence (already checked)
        # GitHub issue existence verified by workflow creation

        return errors

    def _validate_validate_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate validate phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path - run Plan phase first")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Check for plan file
        plan_file = state.get('plan_file')
        if not plan_file:
            errors.append("No plan_file in state - run Plan phase first")
        elif not Path(plan_file).exists():
            errors.append(f"Plan file not found: {plan_file}")

        # Check for state file
        state_file = worktree / 'adw_state.json'
        if not state_file.exists():
            errors.append("adw_state.json not found in worktree")

        return errors

    def _validate_build_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate build phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path - run Plan phase first")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Must have plan file
        plan_file = state.get('plan_file')
        if not plan_file:
            errors.append("No plan_file in state - run Plan phase first")
        elif not Path(plan_file).exists():
            errors.append(f"Plan file not found: {plan_file}")

        # Must have branch name
        branch_name = state.get('branch_name')
        if not branch_name:
            errors.append("No branch_name in state - run Plan phase first")

        return errors

    def _validate_lint_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate lint phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path in state")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Check for source files (backend or frontend)
        backend_src = worktree / 'app' / 'server'
        frontend_src = worktree / 'app' / 'client' / 'src'

        has_backend = backend_src.exists() and any(backend_src.glob('**/*.py'))
        has_frontend = frontend_src.exists() and any(frontend_src.glob('**/*.{ts,tsx,js,jsx}'))

        if not has_backend and not has_frontend:
            errors.append("No source files found in worktree (checked app/server and app/client/src)")

        return errors

    def _validate_test_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate test phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path in state")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")
            return errors

        # Must have test files
        backend_tests = worktree / 'app' / 'server' / 'tests'
        frontend_tests = worktree / 'app' / 'client' / 'src' / '__tests__'

        has_backend_tests = backend_tests.exists() and any(backend_tests.glob('**/*.py'))
        has_frontend_tests = frontend_tests.exists() and any(frontend_tests.glob('**/*.{test.ts,test.tsx,spec.ts,spec.tsx}'))

        if not has_backend_tests and not has_frontend_tests:
            errors.append("No test files found (checked app/server/tests and app/client/src/__tests__)")

        return errors

    def _validate_review_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate review phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path in state")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Must have spec file for review
        plan_file = state.get('plan_file')
        if not plan_file:
            errors.append("No plan_file in state - needed for review")
        elif not Path(plan_file).exists():
            errors.append(f"Plan file not found: {plan_file}")

        # Must have ports for application startup
        backend_port = state.get('backend_port')
        frontend_port = state.get('frontend_port')

        if not backend_port:
            errors.append("No backend_port in state")
        if not frontend_port:
            errors.append("No frontend_port in state")

        return errors

    def _validate_document_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate document phase inputs."""
        errors = []

        if not worktree_path:
            errors.append("No worktree_path in state")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not found: {worktree_path}")

        # Must have spec file
        plan_file = state.get('plan_file')
        if not plan_file:
            errors.append("No plan_file in state")
        elif not Path(plan_file).exists():
            errors.append(f"Plan file not found: {plan_file}")

        return errors

    def _validate_ship_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate ship phase inputs."""
        errors = []

        # Must have all required state fields
        required_fields = ['adw_id', 'branch_name', 'plan_file', 'issue_class',
                          'worktree_path', 'backend_port', 'frontend_port']

        missing_fields = []
        for field in required_fields:
            if not state.get(field):
                missing_fields.append(field)

        if missing_fields:
            errors.append(f"Missing required state fields for Ship: {', '.join(missing_fields)}")

        # Worktree must exist
        if worktree_path and not Path(worktree_path).exists():
            errors.append(f"Worktree not found: {worktree_path}")

        return errors

    def _validate_cleanup_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate cleanup phase inputs."""
        errors = []

        # Cleanup phase is best-effort, so inputs are optional
        # Just warn if worktree doesn't exist
        if worktree_path and not Path(worktree_path).exists():
            # This is a warning, not an error, since cleanup is best-effort
            pass

        return errors

    def _validate_verify_inputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate verify phase inputs."""
        errors = []

        # Must have ports for smoke tests
        backend_port = state.get('backend_port')
        frontend_port = state.get('frontend_port')

        if not backend_port:
            errors.append("No backend_port in state - needed for smoke tests")
        if not frontend_port:
            errors.append("No frontend_port in state - needed for smoke tests")

        return errors

    # Phase-specific output validators

    def _validate_plan_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate plan phase outputs."""
        errors = []

        if not worktree_path:
            errors.append("Plan phase must set worktree_path")
            return errors

        worktree = Path(worktree_path)
        if not worktree.exists():
            errors.append(f"Worktree not created: {worktree_path}")
            return errors

        # Must have plan file (check various possible locations)
        plan_file = state.get('plan_file')
        if not plan_file:
            errors.append("Plan phase did not set plan_file in state")
        elif not Path(plan_file).exists():
            # Check if it's in specs directory
            specs_dir = worktree / 'specs'
            if specs_dir.exists():
                plan_files = list(specs_dir.glob('**/issue-*.md'))
                if not plan_files:
                    errors.append(f"Plan file not found at {plan_file} and no plan files in specs/")
            else:
                errors.append(f"Plan file not found: {plan_file}")
        elif Path(plan_file).stat().st_size < 100:
            errors.append(f"Plan file is suspiciously small (< 100 bytes): {plan_file}")

        # Must have adw_state.json (check both locations)
        # Primary location: agents/{adw_id}/adw_state.json (where ADWState saves)
        # Fallback location: trees/{adw_id}/adw_state.json (legacy)
        state_file_worktree = worktree / 'adw_state.json'

        # Check for adw_id to locate state file in agents directory
        adw_id_from_state = state.get('adw_id') if state else None
        state_file_agents = None
        if adw_id_from_state:
            # Get project root (worktree is at project_root/trees/{adw_id})
            project_root = worktree.parent.parent
            state_file_agents = project_root / 'agents' / adw_id_from_state / 'adw_state.json'

        if not state_file_worktree.exists() and not (state_file_agents and state_file_agents.exists()):
            errors.append("adw_state.json not found in worktree or agents directory")

        # Database check (skip for standalone runs without database records)
        if workflow and not workflow.adw_id:
            errors.append("Workflow adw_id not set in database")
        elif not workflow:
            # Standalone mode - verify we have minimum required data in state
            if not state.get('adw_id'):
                errors.append("No adw_id in state (required for standalone runs)")

        return errors

    def _validate_validate_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate validate phase outputs."""
        errors = []

        # Should have baseline_errors recorded
        baseline_errors = state.get('baseline_errors')
        if not baseline_errors:
            errors.append("Validate phase did not record baseline_errors")

        return errors

    def _validate_build_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate build phase outputs."""
        errors = []

        # Should have build results
        build_results = state.get('external_build_results')
        if not build_results:
            errors.append("Build phase did not record external_build_results")

        return errors

    def _validate_lint_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate lint phase outputs."""
        errors = []

        # Should have lint results
        lint_results = state.get('external_lint_results')
        if not lint_results:
            errors.append("Lint phase did not record external_lint_results")

        return errors

    def _validate_test_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate test phase outputs."""
        errors = []

        # Should have test results
        test_results = state.get('external_test_results')
        if not test_results:
            errors.append("Test phase did not record external_test_results")

        return errors

    def _validate_review_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate review phase outputs."""
        errors = []

        # Review results should be recorded (either in state or in GitHub comments)
        # This is less strict since review results might be posted to GitHub

        return errors

    def _validate_document_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate document phase outputs."""
        errors = []

        # Documentation should be created in app_docs/
        if worktree_path:
            docs_dir = Path(worktree_path) / 'app_docs'
            if docs_dir.exists():
                doc_files = list(docs_dir.glob('**/*.md'))
                if not doc_files:
                    errors.append("No documentation files created in app_docs/")
            # If no app_docs, it might mean no changes were made (which is OK)

        return errors

    def _validate_ship_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate ship phase outputs."""
        errors = []

        # Ship completion should be recorded
        ship_timestamp = state.get('ship_timestamp')
        if not ship_timestamp:
            errors.append("Ship phase did not record ship_timestamp")

        return errors

    def _validate_cleanup_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate cleanup phase outputs."""
        errors = []

        # Cleanup is best-effort, so no strict validation
        # Just check that worktree is removed (if it was supposed to be)

        return errors

    def _validate_verify_outputs(self, workflow: Any, state: dict, worktree_path: Optional[str]) -> List[str]:
        """Validate verify phase outputs."""
        errors = []

        # Verification results should be recorded
        verification_results = state.get('verification_results')
        if not verification_results:
            # This is just a warning - verify might not store results in state
            pass

        return errors

    def _get_worktree_path(self, adw_id: str) -> Optional[str]:
        """Get worktree path for ADW.

        Args:
            adw_id: ADW identifier (e.g., "77c90e61")

        Returns:
            Absolute path to worktree or None if not found
        """
        # Get project root (this file is at project_root/adws/utils/state_validator.py)
        project_root = Path(__file__).parent.parent.parent

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[_get_worktree_path] adw_id={adw_id}, project_root={project_root}")

        # Try multiple possible locations (use absolute paths)
        possible_paths = [
            project_root / "trees" / adw_id,
            project_root / "trees" / f"adw-{adw_id}",
        ]

        logger.debug(f"[_get_worktree_path] Checking paths: {[str(p) for p in possible_paths]}")

        for path in possible_paths:
            logger.debug(f"[_get_worktree_path] Checking {path}: exists={path.exists()}")
            if path.exists():
                result = str(path.absolute())
                logger.debug(f"[_get_worktree_path] Found worktree: {result}")
                return result

        logger.debug(f"[_get_worktree_path] No worktree found for {adw_id}")
        return None
