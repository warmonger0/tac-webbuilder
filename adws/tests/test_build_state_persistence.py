#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest", "python-dotenv", "pydantic"]
# ///

"""
Comprehensive regression tests for ADW build phase state persistence.

Tests the critical bug fix: external_build_results must be properly saved
to ADW state after successful external builds.

Test coverage:
- External build results are properly saved to state
- State persistence survives across reload operations
- Both success and failure scenarios record results
- Results structure matches expected schema
- Backward compatibility with existing state files
- Both external and inline build modes
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.state import ADWState
from adw_modules.data_types import ADWStateData


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_state_directory(tmp_path: Path, project_root: Path) -> Path:
    """Create a temporary directory for state files."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


@pytest.fixture
def adw_id() -> str:
    """Sample ADW ID for testing."""
    return "test1234"


@pytest.fixture
def base_state_data() -> Dict[str, Any]:
    """Base state data for all tests."""
    return {
        "adw_id": "test1234",
        "issue_number": "42",
        "branch_name": "feature/test-build",
        "plan_file": "agents/test1234/plan.md",
        "issue_class": "/feature",
        "worktree_path": "/tmp/test_worktree",
        "backend_port": 9100,
        "frontend_port": 9200,
        "model_set": "base",
        "all_adws": ["adw_plan_iso", "adw_build_iso"],
    }


@pytest.fixture
def successful_build_results() -> Dict[str, Any]:
    """Sample successful build results."""
    return {
        "success": True,
        "summary": {
            "total_errors": 0,
            "type_errors": 0,
            "build_errors": 0,
        },
        "errors": [],
    }


@pytest.fixture
def failed_build_results() -> Dict[str, Any]:
    """Sample failed build results with errors."""
    return {
        "success": False,
        "summary": {
            "total_errors": 2,
            "type_errors": 1,
            "build_errors": 1,
        },
        "errors": [
            {
                "file": "app/server/main.py",
                "line": 42,
                "column": 15,
                "message": "Type error: Expected int, got str",
            },
            {
                "file": "app/server/utils.py",
                "line": 87,
                "column": 5,
                "message": "Undefined variable 'unknown_var'",
            },
        ],
    }


@pytest.fixture
def partial_build_results() -> Dict[str, Any]:
    """Sample build results with warnings only (no errors)."""
    return {
        "success": True,
        "summary": {
            "total_errors": 0,
            "type_errors": 0,
            "build_errors": 0,
            "warnings": 3,
        },
        "errors": [],
    }


# ============================================================================
# Unit Tests: State Save and Load
# ============================================================================


class TestBuildStateDataSave:
    """Test saving external_build_results to state."""

    def test_save_successful_build_results(self, adw_id, base_state_data, successful_build_results, tmp_path, monkeypatch):
        """Test saving successful build results to state."""
        # Setup
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("HOME", str(tmp_path))

        # Mock get_state_path to use tmp_path
        with patch.object(ADWState, 'get_state_path', return_value=str(agents_dir / adw_id / "adw_state.json")):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=successful_build_results)

            # Save state
            state.save(workflow_step="adw_build_external")

            # Verify file was created
            state_file = agents_dir / adw_id / "adw_state.json"
            assert state_file.exists(), "State file should be created"

            # Load and verify contents
            with open(state_file, "r") as f:
                saved_data = json.load(f)

            assert "external_build_results" in saved_data, "external_build_results should be in saved state"
            assert saved_data["external_build_results"]["success"] is True
            assert saved_data["external_build_results"]["summary"]["total_errors"] == 0

    def test_save_failed_build_results(self, adw_id, base_state_data, failed_build_results, tmp_path):
        """Test saving failed build results with errors."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(ADWState, 'get_state_path', return_value=str(agents_dir / adw_id / "adw_state.json")):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=failed_build_results)

            # Save state
            state.save(workflow_step="adw_build_external")

            # Load and verify
            state_file = agents_dir / adw_id / "adw_state.json"
            with open(state_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["external_build_results"]["success"] is False
            assert saved_data["external_build_results"]["summary"]["total_errors"] == 2
            assert len(saved_data["external_build_results"]["errors"]) == 2

    def test_save_partial_build_results_with_warnings(self, adw_id, base_state_data, partial_build_results, tmp_path):
        """Test saving build results with warnings but no errors."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(ADWState, 'get_state_path', return_value=str(agents_dir / adw_id / "adw_state.json")):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=partial_build_results)

            state.save(workflow_step="adw_build_external")

            state_file = agents_dir / adw_id / "adw_state.json"
            with open(state_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["external_build_results"]["success"] is True
            assert saved_data["external_build_results"]["summary"].get("warnings") == 3


class TestBuildStateDataLoad:
    """Test loading external_build_results from state."""

    def test_load_state_with_build_results(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test loading state that contains external_build_results."""
        # Create state file with build results
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        state_data = base_state_data.copy()
        state_data["external_build_results"] = successful_build_results

        state_file = adw_dir / "adw_state.json"
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)

        # Load state using mocked path
        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            loaded_state = ADWState.load(adw_id)

            assert loaded_state is not None, "State should be loaded successfully"
            assert "external_build_results" in loaded_state.data
            assert loaded_state.get("external_build_results")["success"] is True
            assert loaded_state.get("external_build_results")["summary"]["total_errors"] == 0

    def test_load_state_without_build_results(self, adw_id, base_state_data, tmp_path):
        """Test loading state that does not have external_build_results (legacy state)."""
        # Create legacy state file without build results
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        state_file = adw_dir / "adw_state.json"
        with open(state_file, "w") as f:
            json.dump(base_state_data, f, indent=2)

        # Load state
        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            loaded_state = ADWState.load(adw_id)

            assert loaded_state is not None
            assert loaded_state.get("external_build_results") is None
            assert loaded_state.get("adw_id") == adw_id

    def test_load_nonexistent_state_returns_none(self, adw_id, tmp_path):
        """Test that loading nonexistent state returns None."""
        nonexistent_file = tmp_path / "agents" / adw_id / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(nonexistent_file)):
            loaded_state = ADWState.load(adw_id)
            assert loaded_state is None


# ============================================================================
# Integration Tests: State Persistence Across Reload
# ============================================================================


class TestStatePersistenceAcrossReload:
    """Test that state persists correctly across save and reload cycles."""

    def test_build_results_survive_reload_cycle(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test that build results persist when state is reloaded."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # First: Create and save state with build results
            state1 = ADWState(adw_id)
            state1.data.update(base_state_data)
            state1.update(external_build_results=successful_build_results)
            state1.save(workflow_step="adw_build_external")

            # Second: Reload state
            state2 = ADWState.load(adw_id)

            # Verify build results are present after reload
            assert state2 is not None
            assert state2.get("external_build_results") == successful_build_results
            assert state2.get("external_build_results")["success"] is True

    def test_build_results_preserved_when_updating_other_fields(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test that build results are preserved when other state fields are updated."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Create and save initial state with build results
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=successful_build_results)
            state.save()

            # Reload and update unrelated field
            state = ADWState.load(adw_id)
            state.update(all_adws=["adw_plan_iso", "adw_build_iso", "adw_test_iso"])
            state.save()

            # Reload again and verify build results still present
            state = ADWState.load(adw_id)
            assert state.get("external_build_results") == successful_build_results

    def test_multiple_state_changes_with_build_results(self, adw_id, base_state_data, failed_build_results, successful_build_results, tmp_path):
        """Test state transitions: initial build failure, then fix and success."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # First build attempt: failed
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=failed_build_results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results")["success"] is False
            assert loaded.get("external_build_results")["summary"]["total_errors"] == 2

            # After fix: successful build
            state = ADWState.load(adw_id)
            state.update(external_build_results=successful_build_results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results")["success"] is True
            assert loaded.get("external_build_results")["summary"]["total_errors"] == 0


# ============================================================================
# Tests: Results Schema Validation
# ============================================================================


class TestBuildResultsSchemaValidation:
    """Test that build results match expected schema."""

    def test_successful_results_have_required_fields(self, successful_build_results):
        """Test that successful build results have all required fields."""
        assert "success" in successful_build_results
        assert "summary" in successful_build_results
        assert "errors" in successful_build_results

        assert successful_build_results["success"] is True
        assert isinstance(successful_build_results["summary"], dict)
        assert isinstance(successful_build_results["errors"], list)

    def test_summary_has_required_error_counts(self, successful_build_results, failed_build_results):
        """Test that summary contains required error counts."""
        for results in [successful_build_results, failed_build_results]:
            summary = results["summary"]
            assert "total_errors" in summary
            assert "type_errors" in summary
            assert "build_errors" in summary

            assert isinstance(summary["total_errors"], int)
            assert isinstance(summary["type_errors"], int)
            assert isinstance(summary["build_errors"], int)

    def test_error_objects_have_required_fields(self, failed_build_results):
        """Test that error objects in errors array have required fields."""
        for error in failed_build_results["errors"]:
            assert "file" in error, "Error must have 'file' field"
            assert "line" in error, "Error must have 'line' field"
            assert "message" in error, "Error must have 'message' field"

            assert isinstance(error["file"], str)
            assert isinstance(error["line"], int)
            assert isinstance(error["message"], str)

    @pytest.mark.parametrize("field_name", ["column"])
    def test_error_column_field_optional(self, field_name):
        """Test that optional error fields like 'column' can be present."""
        error_with_column = {
            "file": "test.py",
            "line": 10,
            "column": 5,
            "message": "Error message",
        }
        assert field_name in error_with_column
        assert isinstance(error_with_column[field_name], int)

    def test_error_counts_are_nonnegative(self, successful_build_results, failed_build_results, partial_build_results):
        """Test that all error counts are non-negative integers."""
        for results in [successful_build_results, failed_build_results, partial_build_results]:
            summary = results["summary"]
            for count_field in ["total_errors", "type_errors", "build_errors"]:
                assert summary[count_field] >= 0


# ============================================================================
# Tests: External vs Inline Build Modes
# ============================================================================


class TestBuildModeVariations:
    """Test both external and inline build modes."""

    def test_external_build_mode_saves_results(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test external build mode (use_external=True) saves results correctly."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Simulate external build workflow
            state = ADWState(adw_id)
            state.data.update(base_state_data)

            # External build completed and returned results
            state.update(external_build_results=successful_build_results)
            state.save(workflow_step="adw_build_external")

            # Verify results were saved
            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results") is not None
            assert loaded.get("external_build_results")["success"] is True

    def test_inline_build_mode_without_external_results(self, adw_id, base_state_data, tmp_path):
        """Test inline build mode (use_external=False) without external_build_results."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Simulate inline build workflow (no external_build_results saved)
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.save(workflow_step="adw_build_iso")

            # Verify state saved without external_build_results
            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results") is None

    def test_switching_from_inline_to_external_mode(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test workflow that initially runs inline, then switches to external mode."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # First: Inline mode (no external results)
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.save(workflow_step="adw_build_iso")

            # Verify no external results
            state = ADWState.load(adw_id)
            assert state.get("external_build_results") is None

            # Second: Switch to external mode
            state.update(external_build_results=successful_build_results)
            state.save(workflow_step="adw_build_external")

            # Verify external results now present
            state = ADWState.load(adw_id)
            assert state.get("external_build_results") is not None


# ============================================================================
# Tests: Backward Compatibility
# ============================================================================


class TestBackwardCompatibility:
    """Test backward compatibility with existing state files."""

    def test_load_legacy_state_without_external_build_results(self, adw_id, tmp_path):
        """Test loading state file created before external_build_results feature."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        # Create legacy state file (no external_build_results)
        legacy_state = {
            "adw_id": adw_id,
            "issue_number": "42",
            "branch_name": "feature/test",
            "plan_file": "agents/test1234/plan.md",
            "issue_class": "/feature",
            "worktree_path": "/tmp/test_worktree",
            "backend_port": 9100,
            "frontend_port": 9200,
            "model_set": "base",
            "all_adws": ["adw_plan_iso"],
        }

        state_file = adw_dir / "adw_state.json"
        with open(state_file, "w") as f:
            json.dump(legacy_state, f, indent=2)

        # Load legacy state
        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState.load(adw_id)

            assert state is not None
            assert state.get("external_build_results") is None
            assert state.get("adw_id") == adw_id
            assert state.get("issue_number") == "42"

    def test_add_external_build_results_to_legacy_state(self, adw_id, successful_build_results, tmp_path):
        """Test adding external_build_results to a legacy state file."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        # Create legacy state
        legacy_state = {
            "adw_id": adw_id,
            "issue_number": "42",
            "branch_name": "feature/test",
            "plan_file": "agents/test1234/plan.md",
        }

        state_file = adw_dir / "adw_state.json"
        with open(state_file, "w") as f:
            json.dump(legacy_state, f, indent=2)

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Load legacy state
            state = ADWState.load(adw_id)
            assert state.get("external_build_results") is None

            # Add build results
            state.update(external_build_results=successful_build_results)
            state.save()

            # Verify results were added
            state = ADWState.load(adw_id)
            assert state.get("external_build_results") is not None
            assert state.get("external_build_results")["success"] is True

    def test_state_with_partial_external_results(self, adw_id, tmp_path):
        """Test loading state with only some external result fields."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        # Create state with partial external_build_results
        partial_state = {
            "adw_id": adw_id,
            "issue_number": "42",
            "external_build_results": {
                "success": True,
                # Missing summary and errors fields
            },
        }

        state_file = adw_dir / "adw_state.json"
        with open(state_file, "w") as f:
            json.dump(partial_state, f, indent=2)

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Should still load (additionalProperties: true in schema)
            state = ADWState.load(adw_id)
            assert state is not None
            assert "external_build_results" in state.data


# ============================================================================
# Tests: Validation Error Scenarios
# ============================================================================


class TestValidationErrorScenarios:
    """Test validation and error handling."""

    def test_invalid_build_results_structure(self, adw_id, base_state_data, tmp_path):
        """Test handling of invalid build results structure."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        # State can accept any structure (permissive), but we test graceful handling
        invalid_results = {
            "success": True,
            # Missing required fields
        }

        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=invalid_results)

            # State allows it (permissive)
            state.save()

            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results") == invalid_results

    def test_error_with_missing_optional_column_field(self, adw_id, base_state_data, tmp_path):
        """Test error object without optional 'column' field."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "success": False,
            "summary": {"total_errors": 1, "type_errors": 1, "build_errors": 0},
            "errors": [
                {
                    "file": "test.py",
                    "line": 42,
                    "message": "Type error",
                    # column intentionally omitted
                }
            ],
        }

        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert len(loaded.get("external_build_results")["errors"]) == 1
            assert "column" not in loaded.get("external_build_results")["errors"][0]

    def test_cannot_save_forbidden_status_field(self, adw_id, base_state_data):
        """Test that forbidden 'status' field cannot be saved to state."""
        state = ADWState(adw_id)
        state.data.update(base_state_data)

        # Attempt to update with forbidden field
        with pytest.raises(ValueError, match="Cannot update 'status' in state file"):
            state.update(status="building")

    def test_cannot_save_forbidden_current_phase_field(self, adw_id, base_state_data):
        """Test that forbidden 'current_phase' field cannot be saved to state."""
        state = ADWState(adw_id)
        state.data.update(base_state_data)

        with pytest.raises(ValueError, match="Cannot update 'current_phase' in state file"):
            state.update(current_phase="build")


# ============================================================================
# Tests: Concurrent Access Patterns
# ============================================================================


class TestConcurrentStateAccess:
    """Test state behavior with concurrent-like access patterns."""

    def test_sequential_state_modifications(self, adw_id, base_state_data, successful_build_results, failed_build_results, tmp_path):
        """Test sequential modifications to state maintain integrity."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Sequence 1: Set build results
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=successful_build_results)
            state.save()

            # Sequence 2: Modify and re-save
            state = ADWState.load(adw_id)
            state.update(all_adws=["adw_plan_iso", "adw_build_iso", "adw_test_iso"])
            state.save()

            # Sequence 3: Replace build results
            state = ADWState.load(adw_id)
            state.update(external_build_results=failed_build_results)
            state.save()

            # Verify final state
            state = ADWState.load(adw_id)
            assert state.get("external_build_results")["success"] is False
            assert len(state.get("all_adws")) == 3

    def test_state_integrity_after_multiple_cycles(self, adw_id, base_state_data, successful_build_results, tmp_path):
        """Test state integrity after many save/load cycles."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            # Initial state
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=successful_build_results)
            state.save()

            # Run 10 cycles of load/save
            for i in range(10):
                state = ADWState.load(adw_id)
                state.update(all_adws=state.get("all_adws", []) + [f"adw_phase_{i}"])
                state.save()

            # Verify data integrity
            final_state = ADWState.load(adw_id)
            assert final_state.get("external_build_results") == successful_build_results
            assert adw_id in final_state.get("all_adws")
            assert len(final_state.get("all_adws")) >= 3  # Original + cycles


# ============================================================================
# Tests: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_errors_list_with_failed_build(self, adw_id, base_state_data, tmp_path):
        """Test failed build with empty errors list (edge case)."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        # Failed build but no errors reported (unusual but possible)
        results = {
            "success": False,
            "summary": {"total_errors": 1, "type_errors": 1, "build_errors": 0},
            "errors": [],  # Empty errors list
        }

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert loaded.get("external_build_results")["success"] is False
            assert len(loaded.get("external_build_results")["errors"]) == 0

    def test_very_large_error_list(self, adw_id, base_state_data, tmp_path):
        """Test build results with very large number of errors."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        # Create results with 100 errors
        errors = [
            {
                "file": f"file_{i}.py",
                "line": i * 10,
                "column": 5,
                "message": f"Error message {i}",
            }
            for i in range(100)
        ]

        results = {
            "success": False,
            "summary": {"total_errors": 100, "type_errors": 50, "build_errors": 50},
            "errors": errors,
        }

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert len(loaded.get("external_build_results")["errors"]) == 100

    def test_special_characters_in_error_messages(self, adw_id, base_state_data, tmp_path):
        """Test error messages with special characters."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        results = {
            "success": False,
            "summary": {"total_errors": 1, "type_errors": 1, "build_errors": 0},
            "errors": [
                {
                    "file": "test.py",
                    "line": 42,
                    "message": "Error: Expected 'string', got \"number\" (UTF-8: é à ñ 中文)",
                }
            ],
        }

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=results)
            state.save()

            loaded = ADWState.load(adw_id)
            assert "UTF-8" in loaded.get("external_build_results")["errors"][0]["message"]

    def test_absolute_vs_relative_file_paths_in_errors(self, adw_id, base_state_data, tmp_path):
        """Test handling both absolute and relative file paths in errors."""
        agents_dir = tmp_path / "agents"
        adw_dir = agents_dir / adw_id
        adw_dir.mkdir(parents=True, exist_ok=True)
        state_file = adw_dir / "adw_state.json"

        results = {
            "success": False,
            "summary": {"total_errors": 2, "type_errors": 2, "build_errors": 0},
            "errors": [
                {
                    "file": "app/server/main.py",  # Relative
                    "line": 10,
                    "message": "Error 1",
                },
                {
                    "file": "/absolute/path/to/file.py",  # Absolute
                    "line": 20,
                    "message": "Error 2",
                },
            ],
        }

        with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
            state = ADWState(adw_id)
            state.data.update(base_state_data)
            state.update(external_build_results=results)
            state.save()

            loaded = ADWState.load(adw_id)
            errors = loaded.get("external_build_results")["errors"]
            assert errors[0]["file"] == "app/server/main.py"
            assert errors[1]["file"] == "/absolute/path/to/file.py"


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.parametrize(
    "num_errors,expect_success",
    [
        (0, True),  # No errors = success
        (1, False),  # 1 error = failure
        (5, False),  # Multiple errors = failure
        (100, False),  # Many errors = failure
    ],
)
def test_success_field_matches_error_count(adw_id, base_state_data, tmp_path, num_errors, expect_success):
    """Parametrized test: success flag should match error count."""
    agents_dir = tmp_path / "agents"
    adw_dir = agents_dir / adw_id
    adw_dir.mkdir(parents=True, exist_ok=True)
    state_file = adw_dir / "adw_state.json"

    errors = [
        {
            "file": f"file_{i}.py",
            "line": i,
            "message": f"Error {i}",
        }
        for i in range(num_errors)
    ]

    results = {
        "success": expect_success,
        "summary": {"total_errors": num_errors, "type_errors": 0, "build_errors": num_errors},
        "errors": errors,
    }

    with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
        state = ADWState(adw_id)
        state.data.update(base_state_data)
        state.update(external_build_results=results)
        state.save()

        loaded = ADWState.load(adw_id)
        assert loaded.get("external_build_results")["success"] == expect_success
        assert len(loaded.get("external_build_results")["errors"]) == num_errors


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("adw_id", "test1234"),
        ("issue_number", "42"),
        ("branch_name", "feature/test"),
        ("worktree_path", "/tmp/test"),
    ],
)
def test_core_state_fields_preserved_with_build_results(adw_id, field_name, field_value, tmp_path):
    """Parametrized test: core state fields preserved when saving build results."""
    agents_dir = tmp_path / "agents"
    adw_dir = agents_dir / adw_id
    adw_dir.mkdir(parents=True, exist_ok=True)
    state_file = adw_dir / "adw_state.json"

    state_data = {
        "adw_id": adw_id,
        "issue_number": "42",
        "branch_name": "feature/test",
        "worktree_path": "/tmp/test",
        field_name: field_value,
    }

    results = {
        "success": True,
        "summary": {"total_errors": 0, "type_errors": 0, "build_errors": 0},
        "errors": [],
    }

    with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
        state = ADWState(adw_id)
        state.data.update(state_data)
        state.update(external_build_results=results)
        state.save()

        loaded = ADWState.load(adw_id)
        assert loaded.get(field_name) == field_value
        assert loaded.get("external_build_results") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
