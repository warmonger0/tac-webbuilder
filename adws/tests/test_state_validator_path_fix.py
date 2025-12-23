"""
Regression test for Issue #279: StateValidator path mismatch bug.

Tests that StateValidator loads state from the CORRECT location (agents/)
instead of the WRONG location (trees/).

This bug caused phase validation failures even when phases completed successfully.
"""

import tempfile
from pathlib import Path
import json
import sys
import os

# Add adws modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.state import ADWState
from adw_modules.utils import setup_logger
from utils.state_validator import StateValidator


def test_validator_loads_from_agents_not_trees():
    """
    CRITICAL TEST: StateValidator must load from agents/, not trees/.

    This test verifies the fix for Issue #279 where StateValidator was reading
    from trees/{adw_id}/adw_state.json instead of agents/{adw_id}/adw_state.json.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-279-fix"
        issue_number = 279

        # Setup directory structure
        agents_dir = project_root / "agents" / adw_id
        trees_dir = project_root / "trees" / adw_id
        agents_dir.mkdir(parents=True)
        trees_dir.mkdir(parents=True)

        # Save CORRECT state to agents/ (where ADWState.save() puts it)
        correct_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 10, "passed": 10, "failed": 0},
                "failures": []
            },
            "external_build_results": {
                "success": True,
                "summary": {"total_errors": 0},
                "errors": []
            },
            "external_lint_results": {
                "success": True,
                "summary": {"total_errors": 0},
                "errors": []
            }
        }

        agents_state_file = agents_dir / "adw_state.json"
        with open(agents_state_file, 'w') as f:
            json.dump(correct_state, f)

        # Save STALE state to trees/ (old/wrong location - BUG was reading from here)
        stale_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            # NO external_*_results (stale/old state)
        }

        trees_state_file = trees_dir / "adw_state.json"
        with open(trees_state_file, 'w') as f:
            json.dump(stale_state, f)

        # Change working directory to simulate real environment
        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # TEST 1: Test phase validation
            validator_test = StateValidator(phase='test')
            result_test = validator_test.validate_outputs(issue_number)

            assert result_test.is_valid, \
                f"Test validation should PASS (reading from agents/). Errors: {result_test.errors}"

            # If this fails, StateValidator is still reading from trees/ (stale state)
            print("✅ TEST PHASE: StateValidator correctly reads from agents/ directory")

            # TEST 2: Build phase validation
            validator_build = StateValidator(phase='build')
            result_build = validator_build.validate_outputs(issue_number)

            assert result_build.is_valid, \
                f"Build validation should PASS (reading from agents/). Errors: {result_build.errors}"

            print("✅ BUILD PHASE: StateValidator correctly reads from agents/ directory")

            # TEST 3: Lint phase validation
            validator_lint = StateValidator(phase='lint')
            result_lint = validator_lint.validate_outputs(issue_number)

            assert result_lint.is_valid, \
                f"Lint validation should PASS (reading from agents/). Errors: {result_lint.errors}"

            print("✅ LINT PHASE: StateValidator correctly reads from agents/ directory")

        finally:
            os.chdir(old_cwd)


def test_validator_falls_back_to_trees_if_agents_missing():
    """
    Test that StateValidator gracefully falls back to trees/ if agents/ doesn't exist.

    This ensures backward compatibility with legacy deployments.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-fallback"
        issue_number = 280

        # Only create trees/ directory (no agents/ - simulating legacy deployment)
        trees_dir = project_root / "trees" / adw_id
        trees_dir.mkdir(parents=True)

        # Save state to trees/ only
        state_data = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 5, "passed": 5, "failed": 0}
            }
        }

        trees_state_file = trees_dir / "adw_state.json"
        with open(trees_state_file, 'w') as f:
            json.dump(state_data, f)

        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            validator = StateValidator(phase='test')
            result = validator.validate_outputs(issue_number)

            # Should still pass (fallback to trees/ works)
            assert result.is_valid, \
                f"Fallback validation should PASS. Errors: {result.errors}"

            # Should have warning about legacy location
            assert any("legacy" in w.lower() for w in result.warnings), \
                "Should warn about loading from legacy location"

            print("✅ FALLBACK: StateValidator correctly falls back to trees/ when agents/ missing")

        finally:
            os.chdir(old_cwd)


def test_validator_fails_when_state_missing_from_both_locations():
    """
    Test that validation fails correctly when state is missing from both locations.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-missing"
        issue_number = 281

        # Create directories but NO state files
        agents_dir = project_root / "agents" / adw_id
        trees_dir = project_root / "trees" / adw_id
        agents_dir.mkdir(parents=True)
        trees_dir.mkdir(parents=True)

        # Create minimal state without external_test_results
        minimal_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            # NO external_test_results
        }

        # Save to agents/ (correct location but incomplete)
        agents_state_file = agents_dir / "adw_state.json"
        with open(agents_state_file, 'w') as f:
            json.dump(minimal_state, f)

        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            validator = StateValidator(phase='test')
            result = validator.validate_outputs(issue_number)

            # Should FAIL (no external_test_results)
            assert not result.is_valid, \
                "Validation should FAIL when external_test_results missing"

            assert "Test phase did not record external_test_results" in result.errors, \
                f"Should have specific error message. Errors: {result.errors}"

            print("✅ VALIDATION: Correctly fails when test results missing")

        finally:
            os.chdir(old_cwd)


def test_validator_prefers_agents_over_trees():
    """
    Test that when state exists in BOTH locations, agents/ is preferred.

    This ensures the fix prioritizes the correct location.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-priority"
        issue_number = 282

        agents_dir = project_root / "agents" / adw_id
        trees_dir = project_root / "trees" / adw_id
        agents_dir.mkdir(parents=True)
        trees_dir.mkdir(parents=True)

        # Save DIFFERENT states to each location
        agents_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 100, "passed": 100, "failed": 0},  # Different data
                "from_location": "agents"  # Marker
            }
        }

        trees_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "external_test_results": {
                "success": True,
                "summary": {"total": 50, "passed": 50, "failed": 0},  # Different data
                "from_location": "trees"  # Marker
            }
        }

        with open(agents_dir / "adw_state.json", 'w') as f:
            json.dump(agents_state, f)

        with open(trees_dir / "adw_state.json", 'w') as f:
            json.dump(trees_state, f)

        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # Load state using ADWState (should load from agents/)
            logger = setup_logger(adw_id, "test")
            state_obj = ADWState.load(adw_id, logger)

            assert state_obj is not None, "State should load"
            assert state_obj.data.get("external_test_results", {}).get("from_location") == "agents", \
                "Should load from agents/ directory, not trees/"

            print("✅ PRIORITY: StateValidator prefers agents/ over trees/")

        finally:
            os.chdir(old_cwd)


def test_all_phases_validate_with_correct_state():
    """
    Test that ALL phases validate correctly when reading from agents/.

    This is the comprehensive test ensuring the bug is fixed for all phases.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        adw_id = "test-all-phases"
        issue_number = 283

        agents_dir = project_root / "agents" / adw_id
        trees_dir = project_root / "trees" / adw_id
        agents_dir.mkdir(parents=True)
        trees_dir.mkdir(parents=True)

        # Create comprehensive state with ALL phase results
        comprehensive_state = {
            "adw_id": adw_id,
            "issue_number": issue_number,
            "worktree_path": str(trees_dir),
            "plan_file": "/fake/plan.md",
            "branch_name": "test-branch",
            "issue_class": "/feature",
            "backend_port": 8000,
            "frontend_port": 5173,
            "baseline_errors": {"errors": []},
            "external_build_results": {
                "success": True,
                "summary": {"total_errors": 0},
                "errors": []
            },
            "external_lint_results": {
                "success": True,
                "summary": {"total_errors": 0},
                "errors": []
            },
            "external_test_results": {
                "success": True,
                "summary": {"total": 20, "passed": 20, "failed": 0},
                "failures": []
            },
            "ship_timestamp": "2025-12-22T00:00:00Z"
        }

        # Save ONLY to agents/ (correct location)
        with open(agents_dir / "adw_state.json", 'w') as f:
            json.dump(comprehensive_state, f)

        # Create empty state in trees/ (stale/wrong location)
        with open(trees_dir / "adw_state.json", 'w') as f:
            json.dump({"adw_id": adw_id, "issue_number": issue_number}, f)

        old_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # Test all phases
            phases_to_test = ['build', 'lint', 'test']

            for phase in phases_to_test:
                validator = StateValidator(phase=phase)
                result = validator.validate_outputs(issue_number)

                assert result.is_valid, \
                    f"{phase.upper()} phase validation should PASS. Errors: {result.errors}"

                print(f"✅ {phase.upper()} PHASE: Validation passed")

        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    print("=" * 70)
    print("STATE VALIDATOR PATH FIX REGRESSION TESTS (Issue #279)")
    print("=" * 70)
    print()

    tests = [
        ("StateValidator loads from agents/ not trees/", test_validator_loads_from_agents_not_trees),
        ("Fallback to trees/ when agents/ missing", test_validator_falls_back_to_trees_if_agents_missing),
        ("Validation fails when state incomplete", test_validator_fails_when_state_missing_from_both_locations),
        ("agents/ preferred over trees/", test_validator_prefers_agents_over_trees),
        ("All phases validate with correct state", test_all_phases_validate_with_correct_state),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! StateValidator path fix verified.")
        sys.exit(0)
