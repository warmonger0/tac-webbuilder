"""
Simple test runner for Issue #279 fixes (no pytest dependency).

Tests GitHubLabel schema validation and phase continuation logic.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "adws" / "adw_modules"))
sys.path.insert(0, str(Path(__file__).parent / "app" / "server"))

from data_types import GitHubLabel, GitHubIssue, GitHubIssueListItem
from core.phase_continuation import get_next_phase, should_continue_workflow


def test_github_label_with_all_fields():
    """Test label with all fields present."""
    label_data = {
        "id": "LA_123",
        "name": "bug",
        "color": "d73a4a",
        "description": "Bug report"
    }
    label = GitHubLabel(**label_data)
    assert label.id == "LA_123"
    assert label.name == "bug"
    print("✅ test_github_label_with_all_fields passed")


def test_github_label_without_id():
    """Test label missing id field (REST API behavior)."""
    label_data = {
        "name": "enhancement",
        "color": "a2eeef"
    }
    label = GitHubLabel(**label_data)
    assert label.id is None
    assert label.name == "enhancement"
    print("✅ test_github_label_without_id passed")


def test_github_label_without_color():
    """Test label missing color field (REST API behavior)."""
    label_data = {
        "id": "LA_456",
        "name": "documentation"
    }
    label = GitHubLabel(**label_data)
    assert label.color is None
    assert label.id == "LA_456"
    print("✅ test_github_label_without_color passed")


def test_github_label_minimal():
    """Test label with only name field."""
    label_data = {"name": "wontfix"}
    label = GitHubLabel(**label_data)
    assert label.id is None
    assert label.color is None
    assert label.name == "wontfix"
    print("✅ test_github_label_minimal passed")


def test_github_issue_with_incomplete_labels():
    """Test issue parsing with incomplete labels."""
    issue_data = {
        "number": 279,
        "title": "Test issue",
        "body": "Description",
        "state": "open",
        "author": {"login": "testuser"},
        "labels": [
            {"name": "bug", "color": "d73a4a"},  # Missing id
            {"name": "priority:high"}  # Missing id and color
        ],
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-02T00:00:00Z",
        "url": "https://github.com/test/test/issues/279"
    }

    issue = GitHubIssue(**issue_data)
    assert issue.number == 279
    assert len(issue.labels) == 2
    assert issue.labels[0].name == "bug"
    assert issue.labels[0].id is None
    assert issue.labels[1].name == "priority:high"
    assert issue.labels[1].color is None
    print("✅ test_github_issue_with_incomplete_labels passed")


def test_phase_continuation_complete_workflow():
    """Test phase sequence for complete workflow."""
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
    print("✅ test_phase_continuation_complete_workflow passed")


def test_phase_continuation_legacy_workflow():
    """Test legacy workflow phase sequence."""
    workflow = "adw_sdlc_iso"

    assert get_next_phase(workflow, "Plan") == "Build"
    assert get_next_phase(workflow, "Build") == "Test"
    assert get_next_phase(workflow, "Test") == "Review"
    assert get_next_phase(workflow, "Review") == "Document"
    assert get_next_phase(workflow, "Document") == "Ship"
    assert get_next_phase(workflow, "Ship") is None
    print("✅ test_phase_continuation_legacy_workflow passed")


def test_should_continue_completed():
    """Test auto-continue only on completed status."""
    assert should_continue_workflow("completed", "Build") is True
    assert should_continue_workflow("failed", "Build") is False
    assert should_continue_workflow("running", "Build") is False
    print("✅ test_should_continue_completed passed")


def test_should_continue_terminal_phases():
    """Test terminal phases block auto-continuation."""
    assert should_continue_workflow("completed", "Ship") is False
    assert should_continue_workflow("completed", "Verify") is False
    assert should_continue_workflow("completed", "Cleanup") is False
    print("✅ test_should_continue_terminal_phases passed")


def test_unknown_workflow():
    """Test handling of unknown workflow."""
    result = get_next_phase("adw_unknown_workflow", "Build")
    assert result is None
    print("✅ test_unknown_workflow passed")


def test_invalid_phase():
    """Test handling of invalid phase."""
    result = get_next_phase("adw_sdlc_complete_iso", "InvalidPhase")
    assert result is None
    print("✅ test_invalid_phase passed")


def main():
    """Run all tests."""
    print("=" * 70)
    print("ISSUE #279 FIX VALIDATION TESTS")
    print("=" * 70)
    print()

    tests = [
        # GitHubLabel validation tests
        ("GitHubLabel with all fields", test_github_label_with_all_fields),
        ("GitHubLabel without id", test_github_label_without_id),
        ("GitHubLabel without color", test_github_label_without_color),
        ("GitHubLabel minimal (name only)", test_github_label_minimal),
        ("GitHubIssue with incomplete labels", test_github_issue_with_incomplete_labels),

        # Phase continuation tests
        ("Phase continuation - complete workflow", test_phase_continuation_complete_workflow),
        ("Phase continuation - legacy workflow", test_phase_continuation_legacy_workflow),
        ("Should continue - completed status", test_should_continue_completed),
        ("Should continue - terminal phases", test_should_continue_terminal_phases),
        ("Unknown workflow handling", test_unknown_workflow),
        ("Invalid phase handling", test_invalid_phase),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n❌ Some tests failed!")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
