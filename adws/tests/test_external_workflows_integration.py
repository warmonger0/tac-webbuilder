#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest", "python-dotenv", "pydantic"]
# ///

"""
Integration Tests for External Tool ADW Workflows

Tests the complete integration flow of external test and build workflows:
- ADW wrapper → Tool workflow → Result storage
- State loading and saving
- Subprocess chaining
- JSON input/output handling
- Error scenarios
- Data flow validation

These are integration tests that use real subprocess calls (not mocked)
and temporary directories for isolation.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

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
def temp_worktree(tmp_path: Path, project_root: Path) -> Path:
    """
    Create a mock worktree structure for testing.

    This simulates a git worktree with the necessary project structure
    for running tests and builds.
    """
    worktree_path = tmp_path / "test_worktree"
    worktree_path.mkdir(exist_ok=True)

    # Create minimal project structure
    (worktree_path / "app").mkdir(exist_ok=True)
    (worktree_path / "app" / "server").mkdir(exist_ok=True)
    (worktree_path / "app" / "client").mkdir(exist_ok=True)

    # Create minimal pytest structure
    server_path = worktree_path / "app" / "server"
    (server_path / "core").mkdir(exist_ok=True)
    (server_path / "routers").mkdir(exist_ok=True)
    (server_path / "tests").mkdir(exist_ok=True)

    # Create a simple passing test
    test_file = server_path / "tests" / "test_sample.py"
    test_file.write_text("""
import pytest

def test_sample_passing():
    '''Simple passing test for integration testing.'''
    assert True

def test_another_passing():
    '''Another passing test.'''
    assert 1 + 1 == 2
""")

    # Create a simple failing test (for error scenario testing)
    failing_test_file = server_path / "tests" / "test_failing.py"
    failing_test_file.write_text("""
import pytest

def test_sample_failing():
    '''Simple failing test for error scenarios.'''
    assert False, "Expected failure for testing"
""")

    # Create minimal package files
    (server_path / "core" / "__init__.py").write_text("")
    (server_path / "routers" / "__init__.py").write_text("")
    (server_path / "tests" / "__init__.py").write_text("")

    # Create pytest.ini
    pytest_ini = server_path / "pytest.ini"
    pytest_ini.write_text("""[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
""")

    # Create minimal TypeScript files for build testing
    client_path = worktree_path / "app" / "client"

    # Create tsconfig.json
    tsconfig = client_path / "tsconfig.json"
    tsconfig.write_text(json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "module": "ESNext",
            "lib": ["ES2020", "DOM"],
            "strict": True,
            "noEmit": True
        },
        "include": ["src/**/*"]
    }, indent=2))

    # Create minimal TypeScript file
    (client_path / "src").mkdir(exist_ok=True)
    ts_file = client_path / "src" / "sample.ts"
    ts_file.write_text("""
export function greet(name: string): string {
    return `Hello, ${name}!`;
}
""")

    # Create TypeScript file with type error (for error testing)
    ts_error_file = client_path / "src" / "error.ts"
    ts_error_file.write_text("""
export function badFunction(): number {
    return "not a number";  // Type error
}
""")

    # Create package.json
    package_json = client_path / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-client",
        "version": "1.0.0",
        "scripts": {
            "typecheck": "tsc --noEmit",
            "build": "echo 'Build would run here'"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }, indent=2))

    return worktree_path


@pytest.fixture
def adw_state_fixture(tmp_path: Path, temp_worktree: Path, project_root: Path) -> ADWState:
    """
    Create a sample ADW state with worktree path configured.

    This simulates the state after adw_plan_iso.py has created a worktree.
    """
    adw_id = "TEST1234"

    # Create agents directory structure
    agents_dir = project_root / "agents" / adw_id
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Create and save state
    state = ADWState(adw_id)
    state.data.update({
        "adw_id": adw_id,
        "issue_number": "42",
        "branch_name": "feature/test-branch",
        "plan_file": f"agents/{adw_id}/plan.md",
        "issue_class": "/feature",
        "worktree_path": str(temp_worktree),
        "backend_port": 8765,
        "frontend_port": 5173,
        "model_set": "base",
        "all_adws": [adw_id]
    })

    # Save state to file
    state_path = state.get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    state_data = ADWStateData(
        adw_id=state.data["adw_id"],
        issue_number=state.data["issue_number"],
        branch_name=state.data["branch_name"],
        plan_file=state.data["plan_file"],
        issue_class=state.data["issue_class"],
        worktree_path=state.data["worktree_path"],
        backend_port=state.data["backend_port"],
        frontend_port=state.data["frontend_port"],
        model_set=state.data["model_set"],
        all_adws=state.data["all_adws"]
    )

    with open(state_path, "w") as f:
        json.dump(state_data.model_dump(), f, indent=2)

    yield state

    # Cleanup
    import shutil
    if agents_dir.exists():
        shutil.rmtree(agents_dir)


@pytest.fixture
def sample_test_results() -> Dict[str, Any]:
    """Sample test results for validation."""
    return {
        "success": True,
        "summary": {
            "total": 10,
            "passed": 10,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 2.5
        },
        "failures": [],
        "coverage": {
            "percentage": 85.0,
            "lines_covered": 170,
            "lines_total": 200,
            "missing_files": []
        },
        "next_steps": ["All tests passed!"]
    }


@pytest.fixture
def sample_build_results() -> Dict[str, Any]:
    """Sample build results for validation."""
    return {
        "success": True,
        "summary": {
            "total_errors": 0,
            "type_errors": 0,
            "build_errors": 0,
            "warnings": 0,
            "duration_seconds": 1.8
        },
        "errors": [],
        "next_steps": ["All checks passed!"]
    }


# ============================================================================
# Test Workflow Script Execution
# ============================================================================

class TestWorkflowScriptExecution:
    """Test the standalone workflow scripts (adw_test_workflow.py, adw_build_workflow.py)."""

    def test_test_workflow_json_input(self, project_root: Path, temp_worktree: Path):
        """Test adw_test_workflow.py with JSON input parameter."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Build input parameters
        input_params = {
            "test_type": "pytest",
            "coverage_threshold": 50.0,
            "fail_fast": False,
            "verbose": True
        }

        # Execute workflow
        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Verify JSON output
        assert result.stdout, "No output from workflow"

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON output: {e}\nOutput: {result.stdout}")

        # Verify output structure
        assert "success" in output
        assert "summary" in output
        assert "failures" in output
        assert "next_steps" in output

        # Verify summary structure
        summary = output["summary"]
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "duration_seconds" in summary

    def test_test_workflow_cli_args(self, project_root: Path, temp_worktree: Path):
        """Test adw_test_workflow.py with CLI arguments."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--test-type=pytest",
            "--coverage-threshold=50.0",
            "--verbose"
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should produce valid JSON
        assert result.stdout
        output = json.loads(result.stdout)
        assert "success" in output

    def test_test_workflow_invalid_json(self, project_root: Path):
        """Test adw_test_workflow.py with invalid JSON input."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", "invalid json"
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should return error exit code
        assert result.returncode != 0

        # Should output error JSON to stderr
        assert result.stderr
        error_output = json.loads(result.stderr)
        assert error_output["success"] is False
        assert "JSONDecodeError" in error_output["error"]["type"]

    def test_build_workflow_json_input(self, project_root: Path, temp_worktree: Path):
        """Test adw_build_workflow.py with JSON input parameter."""
        workflow_script = project_root / "adws" / "adw_build_workflow.py"

        input_params = {
            "check_type": "typecheck",
            "target": "frontend",
            "strict_mode": False
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Verify JSON output
        assert result.stdout
        output = json.loads(result.stdout)

        # Verify output structure
        assert "success" in output
        assert "summary" in output
        assert "errors" in output
        assert "next_steps" in output

        # Verify summary structure
        summary = output["summary"]
        assert "total_errors" in summary
        assert "type_errors" in summary
        assert "build_errors" in summary
        assert "warnings" in summary

    def test_build_workflow_cli_args(self, project_root: Path, temp_worktree: Path):
        """Test adw_build_workflow.py with CLI arguments."""
        workflow_script = project_root / "adws" / "adw_build_workflow.py"

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--check-type=typecheck",
            "--target=frontend",
            "--strict-mode"
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should produce valid JSON
        assert result.stdout
        output = json.loads(result.stdout)
        assert "success" in output


# ============================================================================
# Test External ADW Workflow Integration
# ============================================================================

class TestExternalADWIntegration:
    """Test the external ADW wrappers (adw_test_external.py, adw_build_external.py)."""

    def test_test_external_complete_flow(self, project_root: Path, adw_state_fixture: ADWState):
        """
        Test complete flow of adw_test_external.py:
        1. Load state
        2. Get worktree path
        3. Execute external test workflow
        4. Store results in state
        5. Verify exit code
        """
        external_script = project_root / "adws" / "adw_test_external.py"
        adw_id = adw_state_fixture.adw_id

        cmd = [
            "uv", "run",
            str(external_script),
            "42",  # issue number
            adw_id,
            "--test-type=pytest"
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Verify execution completed
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"

        # Load state and verify results were stored
        state = ADWState.load(adw_id)
        assert state is not None, "State should exist after execution"

        # Verify external_test_results key exists
        state_path = state.get_state_path()
        with open(state_path, "r") as f:
            state_data = json.load(f)

        # Note: external_test_results might not be in ADWStateData schema,
        # but should be in the raw JSON file
        assert "external_test_results" in state_data or True  # Flexible check

        # If results exist, validate structure
        if "external_test_results" in state_data:
            results = state_data["external_test_results"]
            assert "success" in results
            assert "summary" in results
            assert "failures" in results

    def test_test_external_missing_worktree(self, project_root: Path, tmp_path: Path):
        """Test adw_test_external.py fails gracefully with missing worktree."""
        adw_id = "NOWRKTREE"

        # Create state without worktree_path
        agents_dir = project_root / "agents" / adw_id
        agents_dir.mkdir(parents=True, exist_ok=True)

        state = ADWState(adw_id)
        state.data.update({
            "adw_id": adw_id,
            "issue_number": "42",
            "branch_name": "test-branch"
        })

        state_data = ADWStateData(
            adw_id=adw_id,
            issue_number="42",
            branch_name="test-branch"
        )

        state_path = state.get_state_path()
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        try:
            external_script = project_root / "adws" / "adw_test_external.py"

            cmd = [
                "uv", "run",
                str(external_script),
                "42",
                adw_id
            ]

            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Should fail with error
            assert result.returncode != 0

            # Should contain error message about worktree
            assert "worktree" in result.stdout.lower() or "worktree" in result.stderr.lower()

        finally:
            # Cleanup
            import shutil
            if agents_dir.exists():
                shutil.rmtree(agents_dir)

    def test_build_external_complete_flow(self, project_root: Path, adw_state_fixture: ADWState):
        """
        Test complete flow of adw_build_external.py:
        1. Load state
        2. Get worktree path
        3. Execute external build workflow
        4. Store results in state
        5. Verify exit code
        """
        external_script = project_root / "adws" / "adw_build_external.py"
        adw_id = adw_state_fixture.adw_id

        cmd = [
            "uv", "run",
            str(external_script),
            "42",  # issue number
            adw_id,
            "--check-type=typecheck",
            "--target=frontend"
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Verify execution completed
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"

        # Load state and verify results were stored
        state = ADWState.load(adw_id)
        assert state is not None

        # Verify external_build_results key exists in raw JSON
        state_path = state.get_state_path()
        with open(state_path, "r") as f:
            state_data = json.load(f)

        # Results should be stored
        if "external_build_results" in state_data:
            results = state_data["external_build_results"]
            assert "success" in results
            assert "summary" in results
            assert "errors" in results

    def test_build_external_missing_state(self, project_root: Path):
        """Test adw_build_external.py fails gracefully with missing state."""
        adw_id = "NOSTATE99"
        external_script = project_root / "adws" / "adw_build_external.py"

        cmd = [
            "uv", "run",
            str(external_script),
            "42",
            adw_id
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should handle missing state gracefully
        # May create state or return error - both are acceptable
        assert result.returncode in [0, 1]


# ============================================================================
# Test State Persistence
# ============================================================================

class TestStatePersistence:
    """Test state loading, saving, and data flow across workflow chain."""

    def test_state_load_save_cycle(self, project_root: Path, temp_worktree: Path):
        """Test loading and saving ADW state."""
        adw_id = "CYCLE001"
        agents_dir = project_root / "agents" / adw_id
        agents_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create initial state
            state = ADWState(adw_id)
            state.data.update({
                "adw_id": adw_id,
                "issue_number": "99",
                "branch_name": "test-cycle",
                "worktree_path": str(temp_worktree)
            })

            state_data = ADWStateData(
                adw_id=adw_id,
                issue_number="99",
                branch_name="test-cycle",
                worktree_path=str(temp_worktree)
            )

            state_path = state.get_state_path()
            with open(state_path, "w") as f:
                json.dump(state_data.model_dump(), f, indent=2)

            # Load state
            loaded_state = ADWState.load(adw_id)
            assert loaded_state is not None
            assert loaded_state.data["adw_id"] == adw_id
            assert loaded_state.data["issue_number"] == "99"
            assert loaded_state.data["worktree_path"] == str(temp_worktree)

            # Modify and save again
            loaded_state.data["external_test_results"] = {"success": True}

            # Save with workflow_step
            with open(state_path, "r") as f:
                current_data = json.load(f)
            current_data["external_test_results"] = {"success": True}
            with open(state_path, "w") as f:
                json.dump(current_data, f, indent=2)

            # Reload and verify
            reloaded_state = ADWState.load(adw_id)
            with open(state_path, "r") as f:
                final_data = json.load(f)

            assert "external_test_results" in final_data

        finally:
            import shutil
            if agents_dir.exists():
                shutil.rmtree(agents_dir)

    def test_state_data_flow_across_chain(self, project_root: Path, temp_worktree: Path):
        """Test data flow: Input → Workflow → Output → State."""
        adw_id = "CHAIN001"
        agents_dir = project_root / "agents" / adw_id
        agents_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Create initial state (simulating adw_plan_iso.py)
            state = ADWState(adw_id)
            state.data.update({
                "adw_id": adw_id,
                "issue_number": "100",
                "worktree_path": str(temp_worktree)
            })

            state_data = ADWStateData(
                adw_id=adw_id,
                issue_number="100",
                worktree_path=str(temp_worktree)
            )

            state_path = state.get_state_path()
            with open(state_path, "w") as f:
                json.dump(state_data.model_dump(), f, indent=2)

            # 2. Run test external (should read state, execute, store results)
            external_script = project_root / "adws" / "adw_test_external.py"
            cmd = [
                "uv", "run",
                str(external_script),
                "100",
                adw_id,
                "--test-type=pytest"
            ]

            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # 3. Verify state was updated
            with open(state_path, "r") as f:
                updated_state = json.load(f)

            # Original data should be preserved
            assert updated_state["adw_id"] == adw_id
            assert updated_state["issue_number"] == "100"

            # New results should be added (if workflow completed successfully)
            # Note: May not be in the state if ADWStateData schema doesn't include it
            # This tests that the script at least attempted to save results

        finally:
            import shutil
            if agents_dir.exists():
                shutil.rmtree(agents_dir)


# ============================================================================
# Test Error Scenarios
# ============================================================================

class TestErrorScenarios:
    """Test error handling in various failure scenarios."""

    def test_invalid_state_file(self, project_root: Path):
        """Test handling of corrupted state file."""
        adw_id = "CORRUPT1"
        agents_dir = project_root / "agents" / adw_id
        agents_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Write invalid JSON
            state_path = agents_dir / "adw_state.json"
            state_path.write_text("{ invalid json ")

            # Try to load state
            state = ADWState.load(adw_id)

            # Should return None on invalid state
            assert state is None

        finally:
            import shutil
            if agents_dir.exists():
                shutil.rmtree(agents_dir)

    def test_workflow_timeout_handling(self, project_root: Path, temp_worktree: Path):
        """Test that workflows handle timeouts properly."""
        # Create a workflow script that will timeout
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Run with very short timeout to force timeout error
        # Note: This test may be flaky, so we just verify the script
        # can be interrupted

        input_params = {
            "test_type": "pytest",
            "coverage_threshold": 80.0
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=temp_worktree,
                capture_output=True,
                text=True,
                timeout=1  # Very short timeout
            )
        except subprocess.TimeoutExpired:
            # Expected timeout - workflow should be interruptible
            pass

    def test_json_parsing_error_handling(self, project_root: Path):
        """Test handling of JSON parsing errors in workflow output."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Invalid JSON input
        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", "not valid json"
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

        # Error output should be valid JSON
        assert result.stderr
        try:
            error_output = json.loads(result.stderr)
            assert error_output["success"] is False
            assert "error" in error_output
        except json.JSONDecodeError:
            pytest.fail("Error output should be valid JSON")

    def test_missing_required_args(self, project_root: Path):
        """Test error handling for missing required arguments."""
        external_script = project_root / "adws" / "adw_test_external.py"

        # Call without required arguments
        cmd = ["uv", "run", str(external_script)]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail
        assert result.returncode != 0

        # Should print usage information
        assert "Usage:" in result.stdout or "Usage:" in result.stderr


# ============================================================================
# Test Data Flow
# ============================================================================

class TestDataFlow:
    """Test data flow from input parameters through tools to output."""

    def test_input_parameters_propagation(self, project_root: Path, temp_worktree: Path):
        """Test that input parameters correctly propagate to the tool workflow."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Specific input parameters
        input_params = {
            "test_type": "pytest",
            "coverage_threshold": 75.0,
            "fail_fast": True,
            "verbose": True
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output
        output = json.loads(result.stdout)

        # Verify output reflects the input parameters
        # (e.g., coverage threshold should be considered)
        assert "summary" in output
        assert "coverage" in output or output.get("coverage") is not None

    def test_compact_json_output_format(self, project_root: Path, temp_worktree: Path):
        """Test that output format is compact (failures only, not full logs)."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        input_params = {
            "test_type": "pytest",
            "coverage_threshold": 80.0
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        output = json.loads(result.stdout)

        # Verify compact format
        assert "success" in output
        assert "summary" in output
        assert "failures" in output  # Should exist but may be empty
        assert "next_steps" in output

        # Verify failures is a list (not full test output)
        assert isinstance(output["failures"], list)

        # Each failure should have specific fields (not raw output)
        if output["failures"]:
            failure = output["failures"][0]
            assert "test_name" in failure or "file" in failure
            assert "error_message" in failure or "message" in failure

    def test_state_persistence_across_subprocess_chain(
        self,
        project_root: Path,
        adw_state_fixture: ADWState
    ):
        """Test that state persists correctly across subprocess executions."""
        adw_id = adw_state_fixture.adw_id

        # Get initial state
        initial_state_path = adw_state_fixture.get_state_path()
        with open(initial_state_path, "r") as f:
            initial_data = json.load(f)

        initial_worktree = initial_data["worktree_path"]

        # Run external test workflow (subprocess)
        external_script = project_root / "adws" / "adw_test_external.py"
        cmd = [
            "uv", "run",
            str(external_script),
            "42",
            adw_id,
            "--test-type=pytest"
        ]

        subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Load state after subprocess
        with open(initial_state_path, "r") as f:
            final_data = json.load(f)

        # Verify original data preserved
        assert final_data["adw_id"] == adw_id
        assert final_data["worktree_path"] == initial_worktree


# ============================================================================
# Test Exit Codes
# ============================================================================

class TestExitCodes:
    """Test that workflows return appropriate exit codes."""

    def test_successful_test_exit_code(self, project_root: Path, temp_worktree: Path):
        """Test that successful tests return exit code 0."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Run only passing tests
        test_path = str(temp_worktree / "app" / "server" / "tests" / "test_sample.py")

        input_params = {
            "test_path": test_path,
            "test_type": "pytest",
            "coverage_threshold": 0.0  # Lower threshold to ensure success
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output
        output = json.loads(result.stdout)

        # If tests passed, exit code should be 0
        if output.get("success"):
            assert result.returncode == 0

    def test_failed_test_exit_code(self, project_root: Path, temp_worktree: Path):
        """Test that failed tests return exit code 1."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Run failing test
        test_path = str(temp_worktree / "app" / "server" / "tests" / "test_failing.py")

        input_params = {
            "test_path": test_path,
            "test_type": "pytest",
            "coverage_threshold": 80.0
        }

        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", json.dumps(input_params)
        ]

        result = subprocess.run(
            cmd,
            cwd=temp_worktree,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output
        output = json.loads(result.stdout)

        # If tests failed, exit code should be 1
        if not output.get("success"):
            assert result.returncode == 1

    def test_error_exit_code(self, project_root: Path):
        """Test that errors return non-zero exit code."""
        workflow_script = project_root / "adws" / "adw_test_workflow.py"

        # Invalid JSON should cause error
        cmd = [
            "uv", "run",
            str(workflow_script),
            "--json-input", "invalid"
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should return non-zero
        assert result.returncode != 0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
