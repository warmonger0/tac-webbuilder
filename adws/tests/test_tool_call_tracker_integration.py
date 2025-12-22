"""
Integration test for ToolCallTracker across ADW phases.

Verifies that tool call tracking is properly integrated and working.
"""

import subprocess
import sys
from pathlib import Path

# Add adws directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.tool_call_tracker import ToolCallTracker


def test_tool_call_tracker_basic():
    """Test basic ToolCallTracker functionality."""
    with ToolCallTracker(adw_id="test-adw-123", issue_number=999, phase_name="Test") as tracker:
        # Track a simple command
        result = tracker.track_bash(
            "echo_test",
            ["echo", "Hello, ToolCallTracker!"],
            capture_output=True
        )

        assert result.returncode == 0
        assert "Hello, ToolCallTracker!" in result.stdout

        # Get summary
        summary = tracker.get_summary()
        assert summary["total_calls"] == 1
        assert summary["successful_calls"] == 1
        assert summary["failed_calls"] == 0
        assert "echo_test" in summary["tools_used"]

    print("✅ Basic ToolCallTracker test passed")


def test_tool_call_tracker_multiple_calls():
    """Test tracking multiple tool calls."""
    with ToolCallTracker(adw_id="test-adw-124", issue_number=999, phase_name="Test") as tracker:
        # Track multiple commands
        tracker.track_bash("pwd", ["pwd"])
        tracker.track_bash("ls", ["ls", "-la"])
        tracker.track_bash("echo", ["echo", "test"])

        summary = tracker.get_summary()
        assert summary["total_calls"] == 3
        assert summary["successful_calls"] == 3
        assert len(summary["tools_used"]) == 3

    print("✅ Multiple tool calls test passed")


def test_tool_call_tracker_error_handling():
    """Test tracking failed commands."""
    with ToolCallTracker(adw_id="test-adw-125", issue_number=999, phase_name="Test") as tracker:
        # Track a command that will fail (exit code 1)
        result = tracker.track_bash(
            "false_command",
            ["sh", "-c", "exit 1"],
            capture_output=True
        )

        # Should still return (not raise exception)
        assert result.returncode != 0

        summary = tracker.get_summary()
        assert summary["total_calls"] == 1
        assert summary["failed_calls"] == 1

    print("✅ Error handling test passed")


def verify_phase_integration(phase_file: str, phase_name: str):
    """Verify a phase file has proper ToolCallTracker integration."""
    phase_path = Path(__file__).parent.parent / phase_file

    if not phase_path.exists():
        print(f"⚠️  Phase file not found: {phase_file}")
        return False

    content = phase_path.read_text()

    # Check for import
    has_import = "from adw_modules.tool_call_tracker import ToolCallTracker" in content

    # Check for context manager usage
    has_context = f'phase_name="{phase_name}"' in content

    status = "✅" if (has_import and has_context) else "❌"
    print(f"{status} {phase_file}: import={has_import}, context={has_context}")

    return has_import and has_context


def test_all_phases_integration():
    """Verify all 10 phases have ToolCallTracker integration."""
    phases = [
        ("adw_plan_iso.py", "Plan"),
        ("adw_validate_iso.py", "Validate"),
        ("adw_build_iso.py", "Build"),
        ("adw_lint_iso.py", "Lint"),
        ("adw_test_iso.py", "Test"),
        ("adw_review_iso.py", "Review"),
        ("adw_document_iso.py", "Document"),
        ("adw_ship_iso.py", "Ship"),
        ("adw_cleanup_iso.py", "Cleanup"),
        ("adw_verify_iso.py", "Verify"),
    ]

    results = []
    for phase_file, phase_name in phases:
        result = verify_phase_integration(phase_file, phase_name)
        results.append((phase_file, result))

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n📊 Integration Status: {passed}/{total} phases have ToolCallTracker")

    if passed == total:
        print("✅ All phases properly integrated!")
        return True
    else:
        print("❌ Some phases missing integration")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing ToolCallTracker Integration")
    print("=" * 60)

    try:
        # Run basic functionality tests
        test_tool_call_tracker_basic()
        test_tool_call_tracker_multiple_calls()
        test_tool_call_tracker_error_handling()

        print("\n" + "=" * 60)
        print("Verifying Phase Integration")
        print("=" * 60)

        # Verify all phases are integrated
        all_integrated = test_all_phases_integration()

        if all_integrated:
            print("\n🎉 All tests passed! ToolCallTracker integration complete.")
            sys.exit(0)
        else:
            print("\n⚠️  Some phases need integration work.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
