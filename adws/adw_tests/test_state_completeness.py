#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///

"""
Regression test for ADW state file completeness.

Ensures that all required fields for workflow history database sync
are present in adw_state.json files.

This test prevents the bug where workflow history panel was empty because
state files were missing required sync fields.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.state import ADWState
from adw_modules.data_types import ADWStateData


# Required fields for workflow history database sync
REQUIRED_SYNC_FIELDS = {
    "status",           # pending, running, completed, failed
    "workflow_template", # e.g., "adw_sdlc_complete_zte_iso"
    "model_used",       # e.g., "sonnet", "haiku", "opus"
    "start_time",       # ISO format timestamp
    "nl_input",         # Natural language input from user
    "github_url",       # GitHub issue URL
}


def test_adw_state_data_schema():
    """Test that ADWStateData schema includes all required sync fields."""
    print("Testing ADWStateData schema...")

    schema_fields = set(ADWStateData.model_fields.keys())

    missing_fields = REQUIRED_SYNC_FIELDS - schema_fields
    if missing_fields:
        raise AssertionError(
            f"ADWStateData schema missing required sync fields: {missing_fields}"
        )

    print(f"✅ ADWStateData schema has all {len(REQUIRED_SYNC_FIELDS)} required sync fields")


def test_adw_state_update_allows_sync_fields():
    """Test that ADWState.update() accepts all required sync fields."""
    print("\nTesting ADWState.update() accepts sync fields...")

    state = ADWState("test-adw-id")

    # Try to update with all required sync fields
    test_data = {
        "status": "running",
        "workflow_template": "adw_sdlc_complete_zte_iso",
        "model_used": "sonnet",
        "start_time": "2025-11-20T18:00:00",
        "nl_input": "Test input for regression",
        "github_url": "https://github.com/test/repo/issues/1",
    }

    state.update(**test_data)

    # Verify all fields were saved
    for field, expected_value in test_data.items():
        actual_value = state.get(field)
        if actual_value != expected_value:
            raise AssertionError(
                f"Field '{field}' not updated correctly. "
                f"Expected: {expected_value}, Got: {actual_value}"
            )

    print(f"✅ ADWState.update() accepts all {len(test_data)} sync fields")


def test_state_file_persistence():
    """Test that sync fields persist when saved to file."""
    print("\nTesting sync fields persist to file...")

    # Create test state directory
    test_adw_id = "test-state-regression"
    project_root = Path(__file__).parent.parent.parent
    test_state_dir = project_root / "agents" / test_adw_id
    test_state_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create state with all required fields
        state = ADWState(test_adw_id)
        state.update(
            issue_number="999",
            status="running",
            workflow_template="adw_test_iso",
            model_used="sonnet",
            start_time="2025-11-20T18:00:00",
            nl_input="Test regression for state completeness",
            github_url="https://github.com/test/repo/issues/999",
        )
        state.save("test_state_completeness")

        # Load state from file
        state_file = test_state_dir / "adw_state.json"
        if not state_file.exists():
            raise AssertionError(f"State file not created: {state_file}")

        with open(state_file) as f:
            saved_data = json.load(f)

        # Verify all sync fields are in the saved file
        missing = REQUIRED_SYNC_FIELDS - set(saved_data.keys())
        if missing:
            raise AssertionError(
                f"Saved state file missing required sync fields: {missing}\n"
                f"File contents: {json.dumps(saved_data, indent=2)}"
            )

        # Verify field values
        expected_values = {
            "status": "running",
            "workflow_template": "adw_test_iso",
            "model_used": "sonnet",
            "start_time": "2025-11-20T18:00:00",
            "nl_input": "Test regression for state completeness",
            "github_url": "https://github.com/test/repo/issues/999",
        }

        for field, expected_value in expected_values.items():
            actual_value = saved_data.get(field)
            if actual_value != expected_value:
                raise AssertionError(
                    f"Field '{field}' not persisted correctly. "
                    f"Expected: {expected_value}, Got: {actual_value}"
                )

        print(f"✅ All {len(REQUIRED_SYNC_FIELDS)} sync fields persisted to file")

    finally:
        # Cleanup test state directory
        import shutil
        if test_state_dir.exists():
            shutil.rmtree(test_state_dir)
            print(f"✅ Cleaned up test state directory")


def test_state_roundtrip():
    """Test that state can be saved and loaded without losing sync fields."""
    print("\nTesting state save/load roundtrip...")

    test_adw_id = "test-roundtrip-regression"
    project_root = Path(__file__).parent.parent.parent
    test_state_dir = project_root / "agents" / test_adw_id
    test_state_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create and save state
        original_state = ADWState(test_adw_id)
        original_data = {
            "issue_number": "888",
            "status": "completed",
            "workflow_template": "adw_plan_iso",
            "model_used": "haiku",
            "start_time": "2025-11-20T17:00:00",
            "nl_input": "Roundtrip test for state persistence",
            "github_url": "https://github.com/test/repo/issues/888",
        }
        original_state.update(**original_data)
        original_state.save("test_roundtrip")

        # Load state
        loaded_state = ADWState.load(test_adw_id)
        if not loaded_state:
            raise AssertionError("Failed to load state from file")

        # Verify all sync fields survived roundtrip
        for field, expected_value in original_data.items():
            actual_value = loaded_state.get(field)
            if actual_value != expected_value:
                raise AssertionError(
                    f"Roundtrip failed for field '{field}'. "
                    f"Expected: {expected_value}, Got: {actual_value}"
                )

        print(f"✅ State roundtrip preserved all {len(original_data)} fields")

    finally:
        # Cleanup
        import shutil
        if test_state_dir.exists():
            shutil.rmtree(test_state_dir)
            print(f"✅ Cleaned up roundtrip test directory")


def main():
    """Run all regression tests for state file completeness."""
    print("=" * 60)
    print("ADW State File Completeness Regression Tests")
    print("=" * 60)

    tests = [
        test_adw_state_data_schema,
        test_adw_state_update_allows_sync_fields,
        test_state_file_persistence,
        test_state_roundtrip,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\n⚠️  Some tests failed - state file may not have all required fields!")
        return 1
    else:
        print("\n✅ All tests passed - state file has all required sync fields!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
