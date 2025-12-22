"""
Integration test for external build/lint/test results persistence fix.

Tests that external_build_results, external_lint_results, and external_test_results
are properly saved to state and persist across parent workflow saves.

This test verifies the fix for the bug where external subprocess results were
being overwritten when the parent workflow saved state.
"""
import json
import tempfile
from pathlib import Path
import sys
import os

# Add adws modules to path
adws_dir = Path(__file__).parent.parent
sys.path.insert(0, str(adws_dir))
sys.path.insert(0, str(adws_dir / "adw_modules"))

from state import ADWState
from utils import setup_logger


def test_external_build_results_persist_after_parent_save():
    """Test that external_build_results survives parent state.save() calls."""

    with tempfile.TemporaryDirectory() as tmpdir:
        adw_id = "test_build_persist"
        logger = setup_logger(adw_id, "test")

        # Create initial state
        state = ADWState(adw_id)
        state.data["issue_number"] = "123"
        state.data["worktree_path"] = f"{tmpdir}/test"
        state.save("initial")

        # Simulate external build saving results
        external_build_results = {
            "success": True,
            "summary": {
                "total_errors": 0,
                "type_errors": 0,
                "build_errors": 0,
                "warnings": 0,
                "duration_seconds": 1.5
            },
            "errors": [],
            "next_steps": []
        }

        # External subprocess saves results (simulating adw_build_external.py)
        state.data["external_build_results"] = external_build_results
        state.save("external_build")

        # Reload state (simulating parent process checking results)
        reloaded_state = ADWState.load(adw_id)
        assert reloaded_state is not None, "State should load successfully"
        assert reloaded_state.get("external_build_results") is not None, "external_build_results should exist"

        # CRITICAL TEST: Simulate parent workflow saving state again
        # This is where the bug occurred - parent would overwrite external results
        reloaded_state.data["some_other_field"] = "test_value"
        reloaded_state.save("parent_workflow")

        # Verify external_build_results still exists after parent save
        final_state = ADWState.load(adw_id)
        assert final_state is not None, "Final state should load"
        assert final_state.get("external_build_results") is not None, \
            "external_build_results should persist after parent save"
        assert final_state.get("external_build_results")["success"] is True, \
            "external_build_results data should be intact"

        print("✅ Test passed: external_build_results persists after parent save")


def test_external_lint_results_persist():
    """Test that external_lint_results survives parent state.save() calls."""

    with tempfile.TemporaryDirectory() as tmpdir:
        adw_id = "test_lint_persist"
        logger = setup_logger(adw_id, "test")

        state = ADWState(adw_id)
        state.data["issue_number"] = "124"
        state.save("initial")

        external_lint_results = {
            "success": False,
            "summary": {"total_errors": 5},
            "errors": [{"file": "test.py", "line": 10, "message": "lint error"}]
        }

        state.data["external_lint_results"] = external_lint_results
        state.save("external_lint")

        reloaded = ADWState.load(adw_id)
        reloaded.data["another_field"] = "value"
        reloaded.save("parent")

        final = ADWState.load(adw_id)
        assert final.get("external_lint_results") is not None, \
            "external_lint_results should persist"
        assert final.get("external_lint_results")["success"] is False

        print("✅ Test passed: external_lint_results persists after parent save")


def test_external_test_results_persist():
    """Test that external_test_results survives parent state.save() calls."""

    with tempfile.TemporaryDirectory() as tmpdir:
        adw_id = "test_test_persist"
        logger = setup_logger(adw_id, "test")

        state = ADWState(adw_id)
        state.data["issue_number"] = "125"
        state.save("initial")

        external_test_results = {
            "success": True,
            "summary": {"total": 10, "passed": 10, "failed": 0},
            "failures": []
        }

        state.data["external_test_results"] = external_test_results
        state.save("external_test")

        reloaded = ADWState.load(adw_id)
        reloaded.data["test_field"] = "test"
        reloaded.save("parent")

        final = ADWState.load(adw_id)
        assert final.get("external_test_results") is not None, \
            "external_test_results should persist"
        assert final.get("external_test_results")["summary"]["total"] == 10

        print("✅ Test passed: external_test_results persists after parent save")


if __name__ == "__main__":
    print("Running external results persistence tests...\n")

    try:
        test_external_build_results_persist_after_parent_save()
        test_external_lint_results_persist()
        test_external_test_results_persist()

        print("\n✅ All tests passed! External results persistence is working correctly.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
