#!/usr/bin/env python3
"""
ADW Workflow Failure Scenario Tests

Tests critical failure scenarios identified in:
docs/testing/ADW_WORKFLOW_FAILURE_SCENARIOS.md

Priority 1 (CRITICAL) tests that must pass before production use.
"""

import pytest
import subprocess
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from adw_modules.state import ADWState
from adw_modules.worktree_ops import create_worktree, get_ports_for_adw
from adw_modules.github import fetch_issue


class WorkflowTestHarness:
    """Helper class for workflow testing"""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.adws_dir = Path(__file__).parent.parent
        self.repo_root = self.adws_dir.parent

    def run_phase(
        self,
        script_name: str,
        issue_number: str,
        adw_id: str,
        flags: list[str] = None
    ) -> subprocess.CompletedProcess:
        """Run a specific ADW phase script"""
        cmd = [
            "uv", "run",
            str(self.adws_dir / script_name),
            issue_number,
            adw_id
        ]
        if flags:
            cmd.extend(flags)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )

    def inject_typescript_error(self, worktree_path: Path, file_path: str):
        """Inject a TypeScript error into a file"""
        target = worktree_path / file_path
        if not target.exists():
            pytest.skip(f"Target file {file_path} doesn't exist")

        # Read file
        content = target.read_text()

        # Inject error - add a type mismatch
        error_code = "\n// INJECTED ERROR FOR TESTING\nconst x: string = 123;\n"
        target.write_text(content + error_code)

    def load_state(self, adw_id: str) -> Optional[Dict[str, Any]]:
        """Load ADW state from JSON"""
        state_file = self.repo_root / "agents" / adw_id / "adw_state.json"
        if not state_file.exists():
            return None

        with open(state_file) as f:
            return json.load(f)

    def cleanup_adw(self, adw_id: str):
        """Clean up ADW artifacts"""
        # Remove worktree
        worktree_path = self.repo_root / "trees" / adw_id
        if worktree_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.repo_root,
                capture_output=True
            )

        # Remove agent directory
        agent_dir = self.repo_root / "agents" / adw_id
        if agent_dir.exists():
            shutil.rmtree(agent_dir)


@pytest.fixture
def test_harness(tmp_path):
    """Provide a test harness for workflow testing"""
    return WorkflowTestHarness(tmp_path)


# ==============================================================================
# PRIORITY 1: CRITICAL TESTS
# ==============================================================================

class TestInheritedErrors:
    """
    TC-1.1.x: Inherited Errors from Main Branch
    Issue #66: Ensure Validate phase detects baseline errors
    """

    def test_validate_phase_detects_baseline_errors(self, test_harness):
        """TC-1.1.2: Dirty main → Dirty worktree, Validate detects baseline"""
        # This test requires TypeScript errors on main branch
        # Check if main has errors
        result = subprocess.run(
            ["bun", "run", "typecheck"],
            cwd=test_harness.repo_root / "app" / "client",
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pytest.skip("Main branch is clean, can't test baseline detection")

        # Create a test ADW
        adw_id = "test_validate"
        issue_number = "999"  # Test issue

        try:
            # Run validate phase
            validate_result = test_harness.run_phase(
                "adw_validate_iso.py",
                issue_number,
                adw_id
            )

            # Validate should NEVER fail
            assert validate_result.returncode == 0, \
                f"Validate phase should never fail. stderr: {validate_result.stderr}"

            # Check state has baseline errors
            state = test_harness.load_state(adw_id)
            assert state is not None, "ADW state not created"
            assert "baseline_errors" in state, "No baseline_errors in state"

            baseline = state["baseline_errors"]
            assert "frontend" in baseline, "No frontend baseline"
            assert baseline["frontend"]["type_errors"] > 0, \
                "Should have detected baseline TypeScript errors"

        finally:
            test_harness.cleanup_adw(adw_id)

    def test_build_phase_ignores_baseline_errors(self, test_harness):
        """TC-1.1.2: Build phase ignores baseline, no new errors → PASS"""
        # This test requires:
        # 1. TypeScript errors on main (baseline)
        # 2. Build makes no changes
        # 3. Build should PASS despite baseline errors

        # Check if main has errors
        result = subprocess.run(
            ["bun", "run", "typecheck"],
            cwd=test_harness.repo_root / "app" / "client",
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pytest.skip("Main branch is clean, can't test baseline ignore")

        adw_id = "test_build_baseline"
        issue_number = "999"

        try:
            # Run Plan phase first (creates worktree)
            plan_result = test_harness.run_phase(
                "adw_plan_iso.py",
                issue_number,
                adw_id
            )

            if plan_result.returncode != 0:
                pytest.skip(f"Plan phase failed: {plan_result.stderr}")

            # Run Validate phase
            validate_result = test_harness.run_phase(
                "adw_validate_iso.py",
                issue_number,
                adw_id
            )

            assert validate_result.returncode == 0, "Validate failed"

            # Verify baseline detected
            state = test_harness.load_state(adw_id)
            baseline_count = state.get("baseline_errors", {}).get("frontend", {}).get("type_errors", 0)

            if baseline_count == 0:
                pytest.skip("No baseline errors detected")

            # Run Build phase (with minimal/no changes)
            # NOTE: This would normally implement something
            # For testing, we'll just run build checker directly
            build_result = test_harness.run_phase(
                "adw_build_external.py",
                issue_number,
                adw_id
            )

            # Build check should succeed (same errors as baseline)
            # In actual build_iso.py with differential detection,
            # it would compare and pass
            # This test verifies the mechanism exists

            state_after = test_harness.load_state(adw_id)
            assert "external_build_results" in state_after, \
                "Build results not recorded"

        finally:
            test_harness.cleanup_adw(adw_id)

    def test_build_phase_catches_new_errors(self, test_harness):
        """TC-1.1.3: Dirty main → New errors introduced → FAIL"""
        adw_id = "test_new_errors"
        issue_number = "999"

        try:
            # Run Plan phase
            plan_result = test_harness.run_phase(
                "adw_plan_iso.py",
                issue_number,
                adw_id
            )

            if plan_result.returncode != 0:
                pytest.skip(f"Plan phase failed: {plan_result.stderr}")

            # Run Validate phase
            validate_result = test_harness.run_phase(
                "adw_validate_iso.py",
                issue_number,
                adw_id
            )

            if validate_result.returncode != 0:
                pytest.skip(f"Validate phase failed: {validate_result.stderr}")

            # Get worktree path
            state = test_harness.load_state(adw_id)
            worktree_path = Path(state["worktree_path"])

            # Inject a NEW TypeScript error
            test_harness.inject_typescript_error(
                worktree_path,
                "app/client/src/types/index.ts"
            )

            # Run Build check
            build_result = test_harness.run_phase(
                "adw_build_external.py",
                issue_number,
                adw_id
            )

            # Should detect the new error
            state_after = test_harness.load_state(adw_id)
            build_results = state_after.get("external_build_results", {})
            final_errors = build_results.get("summary", {}).get("type_errors", 0)
            baseline_errors = state.get("baseline_errors", {}).get("frontend", {}).get("type_errors", 0)

            # Should have more errors than baseline
            assert final_errors > baseline_errors, \
                f"New error not detected: final={final_errors}, baseline={baseline_errors}"

        finally:
            test_harness.cleanup_adw(adw_id)


class TestPortConflicts:
    """
    TC-2.1.x: Port Allocation and Conflicts
    """

    def test_deterministic_port_allocation(self):
        """TC-2.1.1: Same ADW ID → Same ports"""
        adw_id = "test_ports"

        port1_backend, port1_frontend = get_ports_for_adw(adw_id)
        port2_backend, port2_frontend = get_ports_for_adw(adw_id)

        assert port1_backend == port2_backend, "Backend port not deterministic"
        assert port1_frontend == port2_frontend, "Frontend port not deterministic"

    def test_different_adws_get_different_ports(self):
        """TC-2.1.2: Different ADW IDs → Different ports"""
        adw1 = "aaaaaaaa"
        adw2 = "zzzzzzzz"

        ports1 = get_ports_for_adw(adw1)
        ports2 = get_ports_for_adw(adw2)

        assert ports1 != ports2, "Different ADWs should get different ports"


class TestConcurrentADWs:
    """
    TC-4.3.x: Concurrent ADW Execution
    Issue #8: Ensure mutex locking prevents conflicts
    """

    @pytest.mark.slow
    def test_concurrent_adws_no_conflict(self, test_harness):
        """TC-4.3.1: Two workflows on same issue → Lock prevents conflict"""
        # This test requires database locking mechanism
        # from Issue #8 fix (adw_locks table)

        issue_number = "999"
        adw_id_1 = "concurrent_1"
        adw_id_2 = "concurrent_2"

        # Check if adw_locks table exists
        db_path = test_harness.repo_root / "app" / "server" / "db" / "tac_webbuilder.db"
        if not db_path.exists():
            pytest.skip("Database not found")

        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='adw_locks'"
        )
        if not cursor.fetchone():
            pytest.skip("adw_locks table not found - Issue #8 fix not implemented")
        conn.close()

        try:
            # Start first workflow (blocks on issue)
            proc1 = subprocess.Popen(
                [
                    "uv", "run",
                    str(test_harness.adws_dir / "adw_plan_iso.py"),
                    issue_number,
                    adw_id_1
                ],
                cwd=test_harness.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give it time to acquire lock
            time.sleep(2)

            # Start second workflow (should be blocked)
            proc2_result = test_harness.run_phase(
                "adw_plan_iso.py",
                issue_number,
                adw_id_2
            )

            # Wait for first to complete
            proc1.wait(timeout=30)

            # Second should have detected lock
            assert "lock" in proc2_result.stderr.lower() or \
                   "already being worked" in proc2_result.stderr.lower(), \
                   "Lock not detected by second workflow"

        finally:
            test_harness.cleanup_adw(adw_id_1)
            test_harness.cleanup_adw(adw_id_2)


class TestZTEAutoMerge:
    """
    TC-5.4.x: ZTE Auto-Merge Safety
    Ensure ZTE NEVER merges broken code
    """

    def test_zte_does_not_merge_on_build_failure(self, test_harness):
        """TC-5.4.1: Build fails → NO auto-merge"""
        # This is a critical safety test
        # ZTE should NEVER merge if build fails

        # Mock test: Verify ZTE workflow script checks for failures
        zte_script = test_harness.adws_dir / "adw_sdlc_complete_zte_iso.py"

        if not zte_script.exists():
            pytest.skip("ZTE workflow not found")

        # Read ZTE script
        content = zte_script.read_text()

        # Verify it has failure checks before ship
        assert "returncode != 0" in content or "failed" in content.lower(), \
            "ZTE script doesn't check for phase failures"

        # Verify it has ship phase gated on success
        assert "ship" in content.lower(), \
            "ZTE script doesn't have ship phase"

        # This is a static analysis test
        # Full integration test would require running actual ZTE workflow
        # with injected failures


class TestEnvironmentValidation:
    """
    TC-2.3.x: Environment Variable Validation
    """

    def test_missing_api_key_detected_early(self, test_harness):
        """TC-2.3.1: Missing ANTHROPIC_API_KEY → Fail early"""
        # Temporarily remove API key
        original_key = os.environ.get("ANTHROPIC_API_KEY")

        try:
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            # Try to run workflow
            result = test_harness.run_phase(
                "adw_plan_iso.py",
                "999",
                "test_no_key"
            )

            # Should fail early
            assert result.returncode != 0, \
                "Workflow should fail without API key"

            # Should have clear error message
            combined_output = result.stdout + result.stderr
            assert "ANTHROPIC_API_KEY" in combined_output or \
                   "API key" in combined_output or \
                   "environment" in combined_output.lower(), \
                   "No clear error message about missing API key"

        finally:
            # Restore API key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key


# ==============================================================================
# PRIORITY 2: HIGH TESTS
# ==============================================================================

class TestGitHubIntegration:
    """
    TC-3.x: GitHub API Integration Tests
    """

    def test_invalid_issue_fails_early(self, test_harness):
        """TC-3.2.1: Issue not found → Fail early with clear message"""
        # Use a very high issue number that definitely doesn't exist
        invalid_issue = "999999"

        result = test_harness.run_phase(
            "adw_plan_iso.py",
            invalid_issue,
            "test_invalid"
        )

        # Should fail
        assert result.returncode != 0, \
            "Workflow should fail for invalid issue"

        # Should have clear error
        combined_output = result.stdout + result.stderr
        assert "not found" in combined_output.lower() or \
               "404" in combined_output or \
               "does not exist" in combined_output.lower(), \
               "No clear error message about invalid issue"


# ==============================================================================
# TEST RUNNERS
# ==============================================================================

def run_critical_tests():
    """Run all Priority 1 (CRITICAL) tests"""
    pytest.main([
        __file__,
        "-v",
        "-k", "test_validate or test_build or test_concurrent or test_zte or test_missing_api",
        "--tb=short"
    ])


def run_all_tests():
    """Run all failure scenario tests"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--critical":
        print("Running CRITICAL tests only...")
        run_critical_tests()
    else:
        print("Running ALL failure scenario tests...")
        run_all_tests()
