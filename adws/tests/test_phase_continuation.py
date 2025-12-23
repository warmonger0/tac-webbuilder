"""
Regression tests for phase auto-continuation feature (Issue #279 related).

Tests the automatic workflow progression system that triggers the next phase
when a phase completes successfully.

This prevents workflow stalls and ensures proper phase sequencing.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add server modules to path
server_dir = Path(__file__).parent.parent.parent / "app" / "server"
sys.path.insert(0, str(server_dir))

from core.phase_continuation import (
    get_next_phase,
    trigger_next_phase,
    should_continue_workflow,
    WORKFLOW_PHASE_SEQUENCES,
    PHASE_TO_SCRIPT
)


class TestGetNextPhase:
    """Test phase sequence determination."""

    def test_complete_workflow_sequence(self):
        """Test adw_sdlc_complete_iso phase sequence."""
        workflow = "adw_sdlc_complete_iso"

        assert get_next_phase(workflow, "Plan") == "Validate"
        assert get_next_phase(workflow, "Validate") == "Build"
        assert get_next_phase(workflow, "Build") == "Lint"
        assert get_next_phase(workflow, "Lint") == "Test"
        assert get_next_phase(workflow, "Test") == "Review"
        assert get_next_phase(workflow, "Review") == "Document"
        assert get_next_phase(workflow, "Document") == "Ship"
        assert get_next_phase(workflow, "Ship") == "Cleanup"
        assert get_next_phase(workflow, "Cleanup") == "Verify"
        assert get_next_phase(workflow, "Verify") is None  # Last phase

    def test_zte_workflow_sequence(self):
        """Test adw_sdlc_complete_zte_iso phase sequence."""
        workflow = "adw_sdlc_complete_zte_iso"

        assert get_next_phase(workflow, "Plan") == "Validate"
        assert get_next_phase(workflow, "Validate") == "Build"
        assert get_next_phase(workflow, "Build") == "Lint"
        # ... same as complete workflow (ZTE has same phases, just auto-merges)

    def test_legacy_workflow_sequence(self):
        """Test adw_sdlc_iso (legacy) phase sequence."""
        workflow = "adw_sdlc_iso"

        # Legacy workflow skips Validate, Lint, Cleanup, Verify
        assert get_next_phase(workflow, "Plan") == "Build"
        assert get_next_phase(workflow, "Build") == "Test"
        assert get_next_phase(workflow, "Test") == "Review"
        assert get_next_phase(workflow, "Review") == "Document"
        assert get_next_phase(workflow, "Document") == "Ship"
        assert get_next_phase(workflow, "Ship") is None  # Last phase

    def test_partial_workflow_plan_build(self):
        """Test adw_plan_build_iso partial workflow."""
        workflow = "adw_plan_build_iso"

        assert get_next_phase(workflow, "Plan") == "Build"
        assert get_next_phase(workflow, "Build") is None  # Last phase

    def test_partial_workflow_plan_build_test(self):
        """Test adw_plan_build_test_iso partial workflow."""
        workflow = "adw_plan_build_test_iso"

        assert get_next_phase(workflow, "Plan") == "Build"
        assert get_next_phase(workflow, "Build") == "Test"
        assert get_next_phase(workflow, "Test") is None  # Last phase

    def test_from_build_workflow(self):
        """Test adw_sdlc_from_build_iso (starts from Build)."""
        workflow = "adw_sdlc_from_build_iso"

        # Starts from Build (no Plan phase)
        assert get_next_phase(workflow, "Build") == "Lint"
        assert get_next_phase(workflow, "Lint") == "Test"
        assert get_next_phase(workflow, "Test") == "Review"

    def test_lightweight_workflow(self):
        """Test adw_lightweight_iso (minimal workflow)."""
        workflow = "adw_lightweight_iso"

        assert get_next_phase(workflow, "Plan") == "Build"
        assert get_next_phase(workflow, "Build") == "Test"
        assert get_next_phase(workflow, "Test") is None  # Last phase

    def test_last_phase_returns_none(self):
        """Test that last phase in sequence returns None."""
        assert get_next_phase("adw_sdlc_complete_iso", "Verify") is None
        assert get_next_phase("adw_sdlc_iso", "Ship") is None
        assert get_next_phase("adw_plan_build_iso", "Build") is None

    def test_unknown_workflow(self):
        """Test handling of unknown workflow template."""
        result = get_next_phase("adw_unknown_workflow", "Plan")
        assert result is None

    def test_invalid_phase_in_workflow(self):
        """Test handling of phase not in workflow sequence."""
        # "Lint" not in legacy workflow
        result = get_next_phase("adw_sdlc_iso", "Lint")
        assert result is None

    def test_phase_not_in_any_workflow(self):
        """Test handling of completely invalid phase name."""
        result = get_next_phase("adw_sdlc_complete_iso", "InvalidPhase")
        assert result is None


class TestShouldContinueWorkflow:
    """Test workflow continuation decision logic."""

    def test_continue_on_completed_status(self):
        """Test auto-continue only on completed status."""
        assert should_continue_workflow("completed", "Build") is True
        assert should_continue_workflow("failed", "Build") is False
        assert should_continue_workflow("running", "Build") is False
        assert should_continue_workflow("pending", "Build") is False

    def test_block_terminal_phases(self):
        """Test terminal phases don't auto-continue."""
        # Ship, Verify, Cleanup should not auto-continue
        assert should_continue_workflow("completed", "Ship") is False
        assert should_continue_workflow("completed", "Verify") is False
        assert should_continue_workflow("completed", "Cleanup") is False

    def test_allow_non_terminal_phases(self):
        """Test non-terminal phases do auto-continue."""
        assert should_continue_workflow("completed", "Plan") is True
        assert should_continue_workflow("completed", "Validate") is True
        assert should_continue_workflow("completed", "Build") is True
        assert should_continue_workflow("completed", "Lint") is True
        assert should_continue_workflow("completed", "Test") is True
        assert should_continue_workflow("completed", "Review") is True
        assert should_continue_workflow("completed", "Document") is True

    def test_failed_phase_blocks_continuation(self):
        """Test failed phases block auto-continuation."""
        for phase in ["Plan", "Build", "Test", "Lint", "Review"]:
            assert should_continue_workflow("failed", phase) is False


class TestTriggerNextPhase:
    """Test next phase triggering mechanism."""

    @patch('core.phase_continuation.subprocess.Popen')
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_trigger_next_phase_success(self, mock_exists, mock_popen):
        """Test successful next phase trigger."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = trigger_next_phase(
            adw_id="test-adw-123",
            issue_number="279",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Build"
        )

        assert result is True
        mock_popen.assert_called_once()

        # Verify command structure
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "uv"
        assert cmd[1] == "run"
        assert "adw_lint_iso.py" in cmd[2]  # Next phase after Build is Lint
        assert cmd[3] == "279"  # Issue number
        assert cmd[4] == "test-adw-123"  # ADW ID

    @patch('core.phase_continuation.subprocess.Popen')
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_trigger_with_workflow_flags(self, mock_exists, mock_popen):
        """Test workflow flags are passed to next phase."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        workflow_flags = {
            "skip_e2e": True,
            "skip_resolution": True,
            "no_external": False
        }

        result = trigger_next_phase(
            adw_id="test-adw-124",
            issue_number="280",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Test",
            workflow_flags=workflow_flags
        )

        assert result is True

        # Verify flags in command
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "--skip-e2e" in cmd
        assert "--skip-resolution" in cmd
        assert "--no-external" not in cmd  # False, so not included

    @patch('core.phase_continuation.subprocess.Popen')
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_cleanup_phase_skipped(self, mock_exists, mock_popen):
        """Test Cleanup phase not auto-triggered (handled by orchestrator)."""
        result = trigger_next_phase(
            adw_id="test-adw-125",
            issue_number="281",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Ship"  # Next phase would be Cleanup
        )

        # Should return False (Cleanup skipped)
        assert result is False
        mock_popen.assert_not_called()

    @patch('core.phase_continuation.subprocess.Popen')
    def test_script_not_found(self, mock_popen):
        """Test handling when phase script doesn't exist."""
        # Don't patch Path.exists, let it check real filesystem
        result = trigger_next_phase(
            adw_id="test-adw-126",
            issue_number="282",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Build",
        )

        # Should fail gracefully (script might not exist in test environment)
        # The function should return False, not raise exception

    @patch('core.phase_continuation.subprocess.Popen', side_effect=Exception("Launch failed"))
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_subprocess_launch_failure(self, mock_exists, mock_popen):
        """Test handling of subprocess launch failure."""
        result = trigger_next_phase(
            adw_id="test-adw-127",
            issue_number="283",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Build"
        )

        assert result is False  # Should return False on exception

    def test_last_phase_no_trigger(self):
        """Test last phase doesn't trigger (no next phase)."""
        result = trigger_next_phase(
            adw_id="test-adw-128",
            issue_number="284",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Verify"  # Last phase
        )

        assert result is False

    def test_unknown_workflow_no_trigger(self):
        """Test unknown workflow doesn't trigger."""
        result = trigger_next_phase(
            adw_id="test-adw-129",
            issue_number="285",
            workflow_template="adw_unknown_workflow",
            current_phase="Build"
        )

        assert result is False


class TestPhaseToScriptMapping:
    """Test phase name to script name mapping."""

    def test_all_phases_mapped(self):
        """Test all phases have script mappings."""
        expected_phases = [
            "Plan", "Validate", "Build", "Lint", "Test",
            "Review", "Document", "Ship", "Cleanup", "Verify"
        ]

        for phase in expected_phases:
            assert phase in PHASE_TO_SCRIPT
            assert PHASE_TO_SCRIPT[phase].endswith(".py")

    def test_script_naming_convention(self):
        """Test script names follow naming convention."""
        for phase, script in PHASE_TO_SCRIPT.items():
            # Should be adw_<phase>_iso.py
            expected = f"adw_{phase.lower()}_iso.py"
            assert script == expected


class TestWorkflowPhaseSequences:
    """Test workflow phase sequence definitions."""

    def test_all_complete_workflows_have_10_phases(self):
        """Test complete workflows have all 10 phases."""
        complete_workflows = [
            "adw_sdlc_complete_iso",
            "adw_sdlc_complete_zte_iso"
        ]

        for workflow in complete_workflows:
            assert workflow in WORKFLOW_PHASE_SEQUENCES
            assert len(WORKFLOW_PHASE_SEQUENCES[workflow]) == 10

    def test_legacy_workflows_have_6_phases(self):
        """Test legacy workflows have 6 phases."""
        legacy_workflows = [
            "adw_sdlc_iso",
            "adw_sdlc_zte_iso"
        ]

        for workflow in legacy_workflows:
            assert workflow in WORKFLOW_PHASE_SEQUENCES
            assert len(WORKFLOW_PHASE_SEQUENCES[workflow]) == 6

    def test_partial_workflows_correct_lengths(self):
        """Test partial workflows have correct phase counts."""
        assert len(WORKFLOW_PHASE_SEQUENCES["adw_plan_build_iso"]) == 2
        assert len(WORKFLOW_PHASE_SEQUENCES["adw_plan_build_test_iso"]) == 3
        assert len(WORKFLOW_PHASE_SEQUENCES["adw_plan_build_test_review_iso"]) == 4
        assert len(WORKFLOW_PHASE_SEQUENCES["adw_lightweight_iso"]) == 3

    def test_from_build_workflow_starts_with_build(self):
        """Test from-build workflow starts with Build phase."""
        workflow = WORKFLOW_PHASE_SEQUENCES["adw_sdlc_from_build_iso"]
        assert workflow[0] == "Build"
        assert "Plan" not in workflow


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_workflow_template(self):
        """Test handling of None workflow template."""
        result = get_next_phase(None, "Build")
        assert result is None

    def test_empty_workflow_template(self):
        """Test handling of empty workflow template."""
        result = get_next_phase("", "Build")
        assert result is None

    def test_none_current_phase(self):
        """Test handling of None current phase."""
        result = get_next_phase("adw_sdlc_complete_iso", None)
        assert result is None

    def test_empty_current_phase(self):
        """Test handling of empty current phase."""
        result = get_next_phase("adw_sdlc_complete_iso", "")
        assert result is None

    @patch('core.phase_continuation.subprocess.Popen')
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_trigger_with_none_flags(self, mock_exists, mock_popen):
        """Test trigger works with None workflow_flags."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = trigger_next_phase(
            adw_id="test-adw-130",
            issue_number="286",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Build",
            workflow_flags=None  # None flags
        )

        assert result is True

    @patch('core.phase_continuation.subprocess.Popen')
    @patch('core.phase_continuation.Path.exists', return_value=True)
    def test_trigger_with_empty_flags(self, mock_exists, mock_popen):
        """Test trigger works with empty workflow_flags dict."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = trigger_next_phase(
            adw_id="test-adw-131",
            issue_number="287",
            workflow_template="adw_sdlc_complete_iso",
            current_phase="Build",
            workflow_flags={}  # Empty flags
        )

        assert result is True


if __name__ == "__main__":
    """Run tests directly with pytest."""
    import subprocess as sp
    import sys

    print("Running phase auto-continuation regression tests...\n")

    # Run with pytest
    result = sp.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )

    sys.exit(result.returncode)
