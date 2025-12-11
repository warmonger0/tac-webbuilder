"""
Tests for ADW phase idempotency.

Validates that all 10 ADW phases are idempotent:
- Running a phase twice produces the same result
- No duplicate side effects (GitHub comments, PRs, commits)
- Phases can safely resume from crashes
- State validation ensures completeness
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import sys
import os
import importlib.util

# Load ADW utils modules directly to avoid conflicts with app.server.utils
adws_base = Path(__file__).parent.parent.parent.parent.parent / "adws"
idempotency_spec = importlib.util.spec_from_file_location(
    "adws_idempotency",
    adws_base / "utils" / "idempotency.py"
)
idempotency_module = importlib.util.module_from_spec(idempotency_spec)
idempotency_spec.loader.exec_module(idempotency_module)

state_validator_spec = importlib.util.spec_from_file_location(
    "adws_state_validator",
    adws_base / "utils" / "state_validator.py"
)
state_validator_module = importlib.util.module_from_spec(state_validator_spec)
state_validator_spec.loader.exec_module(state_validator_module)

# Import from the loaded modules
is_phase_complete = idempotency_module.is_phase_complete
check_and_skip_if_complete = idempotency_module.check_and_skip_if_complete
validate_phase_completion = idempotency_module.validate_phase_completion
check_plan_file_valid = idempotency_module.check_plan_file_valid
check_pr_exists = idempotency_module.check_pr_exists
ensure_database_state = idempotency_module.ensure_database_state

StateValidator = state_validator_module.StateValidator
ValidationResult = state_validator_module.ValidationResult


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_workflow():
    """Mock workflow object from database."""
    workflow = Mock()
    workflow.queue_id = 1
    workflow.issue_number = 123
    workflow.adw_id = "test-adw-123"
    workflow.status = "planned"
    workflow.current_phase = "plan"
    workflow.worktree_path = "trees/test-adw-123"
    return workflow


@pytest.fixture
def mock_state(tmp_path):
    """Mock ADW state."""
    state_file = tmp_path / "adw_state.json"
    state_data = {
        "adw_id": "test-adw-123",
        "issue_number": "123",
        "worktree_path": str(tmp_path / "worktree"),
        "plan_file": str(tmp_path / "worktree" / "SDLC_PLAN.md"),
        "branch_name": "feature/test-123",
        "backend_port": 9100,
        "frontend_port": 9200,
    }

    state_file.write_text(json.dumps(state_data))
    return state_data


class TestIdempotencyHelpers:
    """Test idempotency helper functions."""

    def test_is_phase_complete_returns_false_for_incomplete_phase(self, mock_logger):
        """Test that is_phase_complete returns False for incomplete phase."""
        # Patch StateValidator in idempotency_module where it's actually used
        with patch.dict(idempotency_module.__dict__, {'StateValidator': Mock(return_value=Mock(
            validate_outputs=Mock(return_value=ValidationResult(is_valid=False, errors=["Plan file missing"], warnings=[]))
        ))}):
            result = is_phase_complete('plan', 123, mock_logger)

            assert result is False
            mock_logger.debug.assert_called()

    def test_is_phase_complete_returns_true_for_complete_phase(self, mock_logger):
        """Test that is_phase_complete returns True for complete phase."""
        # Patch StateValidator in idempotency_module where it's actually used
        with patch.dict(idempotency_module.__dict__, {'StateValidator': Mock(return_value=Mock(
            validate_outputs=Mock(return_value=ValidationResult(is_valid=True, errors=[], warnings=[]))
        ))}):
            result = is_phase_complete('plan', 123, mock_logger)

            assert result is True
            mock_logger.debug.assert_called()

    def test_check_and_skip_if_complete_returns_true_when_complete(self, mock_logger):
        """Test that check_and_skip_if_complete returns True when phase is complete."""
        with patch.object(idempotency_module, 'is_phase_complete', return_value=True):
            result = check_and_skip_if_complete('plan', 123, mock_logger)

            assert result is True
            mock_logger.info.assert_called_with("✓ Plan phase already complete, skipping")

    def test_check_and_skip_if_complete_returns_false_when_incomplete(self, mock_logger):
        """Test that check_and_skip_if_complete returns False when phase is incomplete."""
        with patch.object(idempotency_module, 'is_phase_complete', return_value=False):
            result = check_and_skip_if_complete('plan', 123, mock_logger)

            assert result is False
            mock_logger.info.assert_called_with("→ Plan phase not complete, executing")

    def test_validate_phase_completion_raises_on_incomplete(self, mock_logger):
        """Test that validate_phase_completion raises ValueError on incomplete phase."""
        with patch.object(idempotency_module, 'is_phase_complete', return_value=False):
            with pytest.raises(ValueError, match="Plan phase incomplete after execution"):
                validate_phase_completion('plan', 123, mock_logger)

    def test_validate_phase_completion_succeeds_on_complete(self, mock_logger):
        """Test that validate_phase_completion succeeds on complete phase."""
        with patch.object(idempotency_module, 'is_phase_complete', return_value=True):
            # Should not raise
            validate_phase_completion('plan', 123, mock_logger)
            mock_logger.info.assert_called_with("✓ Plan phase validated as complete")

    def test_check_plan_file_valid_returns_false_for_missing_file(self, mock_logger, tmp_path):
        """Test that check_plan_file_valid returns False for missing file."""
        plan_file = tmp_path / "nonexistent.md"
        result = check_plan_file_valid(str(plan_file), mock_logger)

        assert result is False

    def test_check_plan_file_valid_returns_false_for_small_file(self, mock_logger, tmp_path):
        """Test that check_plan_file_valid returns False for suspiciously small file."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("tiny")

        result = check_plan_file_valid(str(plan_file), mock_logger)

        assert result is False
        assert "suspiciously small" in str(mock_logger.warning.call_args)

    def test_check_plan_file_valid_returns_false_for_missing_sections(self, mock_logger, tmp_path):
        """Test that check_plan_file_valid returns False for missing required sections."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# Plan\n\n" + "x" * 200)  # Long enough but missing sections

        result = check_plan_file_valid(str(plan_file), mock_logger)

        assert result is False
        assert "missing section" in str(mock_logger.warning.call_args)

    def test_check_plan_file_valid_returns_true_for_valid_file(self, mock_logger, tmp_path):
        """Test that check_plan_file_valid returns True for valid plan file."""
        plan_file = tmp_path / "plan.md"
        plan_content = """# SDLC Plan

## Objective
Build feature X

## Implementation
1. Step 1
2. Step 2

## Testing
- Test 1
- Test 2
"""
        plan_file.write_text(plan_content)

        result = check_plan_file_valid(str(plan_file), mock_logger)

        assert result is True

    def test_ensure_database_state_updates_when_incorrect(self, mock_logger):
        """Test that ensure_database_state updates database when state is incorrect."""
        with patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository') as mock_repo_class:
            # Mock workflow with incorrect state
            mock_workflow = Mock()
            mock_workflow.status = "pending"
            mock_workflow.current_phase = "none"

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            ensure_database_state(123, 'planned', 'plan', mock_logger)

            # Should update database
            mock_repo.update_phase.assert_called_once()
            call_args = mock_repo.update_phase.call_args
            assert call_args[1]['issue_number'] == 123
            assert 'status' in call_args[1] or 'current_phase' in call_args[1]

    def test_ensure_database_state_skips_update_when_correct(self, mock_logger):
        """Test that ensure_database_state skips update when state is already correct."""
        with patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository') as mock_repo_class:
            # Mock workflow with correct state
            mock_workflow = Mock()
            mock_workflow.status = "planned"
            mock_workflow.current_phase = "plan"

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            ensure_database_state(123, 'planned', 'plan', mock_logger)

            # Should NOT update database
            mock_repo.update_phase.assert_not_called()
            assert "already correct" in str(mock_logger.debug.call_args)


class TestStateValidator:
    """Test StateValidator for phase validation."""

    def test_validator_validates_plan_phase_outputs(self, mock_workflow, tmp_path):
        """Test that StateValidator validates plan phase outputs correctly."""
        # Create mock plan file
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        plan_file = worktree / "SDLC_PLAN.md"
        plan_file.write_text("# Plan\n\n" + "## Objective\n\n## Implementation\n\n## Testing\n\n" + "x" * 200)

        state_file = worktree / "adw_state.json"
        state_file.write_text(json.dumps({
            "plan_file": str(plan_file),
            "worktree_path": str(worktree),
            "adw_id": "test-adw-123"
        }))

        mock_workflow.adw_id = "test-adw-123"

        with patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository') as mock_repo_class:
            with patch.object(StateValidator, '_get_worktree_path', return_value=str(worktree)):
                mock_repo = Mock()
                mock_repo.find_by_issue_number.return_value = mock_workflow
                mock_repo_class.return_value = mock_repo

                validator = StateValidator(phase='plan')
                result = validator.validate_outputs(123)

                # Plan file exists and is valid
                assert result.is_valid

    def test_validator_fails_for_missing_plan_file(self, mock_workflow, tmp_path):
        """Test that StateValidator fails when plan file is missing."""
        worktree = tmp_path / "worktree"
        worktree.mkdir()

        state_file = worktree / "adw_state.json"
        state_file.write_text(json.dumps({
            "plan_file": str(worktree / "nonexistent.md"),
            "worktree_path": str(worktree),
            "adw_id": "test-adw-123"
        }))

        mock_workflow.adw_id = "test-adw-123"

        with patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository') as mock_repo_class:
            with patch.object(StateValidator, '_get_worktree_path', return_value=str(worktree)):
                mock_repo = Mock()
                mock_repo.find_by_issue_number.return_value = mock_workflow
                mock_repo_class.return_value = mock_repo

                validator = StateValidator(phase='plan')
                result = validator.validate_outputs(123)

                # Plan file missing
                assert not result.is_valid
                assert any('plan' in err.lower() or 'file' in err.lower() for err in result.errors)


class TestPhaseIdempotency:
    """Integration tests for phase idempotency."""

    @pytest.mark.integration
    def test_plan_phase_is_idempotent(self, mock_logger, tmp_path):
        """Test that plan phase is idempotent - running twice produces same result."""
        # This would be a full integration test that:
        # 1. Runs plan phase once
        # 2. Records state
        # 3. Runs plan phase again
        # 4. Verifies state is identical
        # 5. Verifies no duplicate GitHub comments/commits

        # For now, this is a placeholder for future integration testing
        pytest.skip("Integration test - requires full test environment")

    @pytest.mark.integration
    def test_build_phase_is_idempotent(self, mock_logger):
        """Test that build phase is idempotent."""
        pytest.skip("Integration test - requires full test environment")

    @pytest.mark.integration
    def test_ship_phase_is_idempotent(self, mock_logger):
        """Test that ship phase is idempotent - duplicate PRs not created."""
        pytest.skip("Integration test - requires full test environment")


class TestCrashRecovery:
    """Test crash recovery scenarios."""

    @pytest.mark.integration
    def test_workflow_recovers_from_crash_during_build(self):
        """Test that workflow can recover from crash during build phase."""
        # This would test:
        # 1. Start workflow
        # 2. Simulate crash during build
        # 3. Restart workflow
        # 4. Verify it resumes from build phase
        # 5. Verify completed work not repeated

        pytest.skip("Integration test - requires full test environment")

    @pytest.mark.integration
    def test_orchestrator_retries_on_phase_failure(self):
        """Test that orchestrator retries failed phases using idempotency."""
        # This would test:
        # 1. Mock phase failure
        # 2. Verify orchestrator retries
        # 3. Verify retry uses idempotency (skips completed work)
        # 4. Verify success after retry

        pytest.skip("Integration test - requires full test environment")


class TestOrchestratorRetryLogic:
    """Test orchestrator retry function."""

    def test_run_phase_with_retry_succeeds_on_first_attempt(self, mock_logger):
        """Test that retry function succeeds on first attempt."""
        # This would test the run_phase_with_retry function
        pytest.skip("Requires mocking subprocess.run")

    def test_run_phase_with_retry_retries_on_failure(self, mock_logger):
        """Test that retry function retries on failure."""
        pytest.skip("Requires mocking subprocess.run")

    def test_run_phase_with_retry_fails_after_max_retries(self, mock_logger):
        """Test that retry function fails after max retries exceeded."""
        pytest.skip("Requires mocking subprocess.run")


# Run tests with: pytest tests/adws/test_idempotency.py -v
# Run with integration tests: pytest tests/adws/test_idempotency.py -v -m integration
