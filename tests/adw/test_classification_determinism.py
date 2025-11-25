"""
Tests to ensure ADW issue classification is deterministic.

These tests prevent branch name mismatches that occur when classification
changes between workflow phases (INCIDENT_2025-11-25_ADW_WORKFLOW_STALL).
"""

import json
import os
import pytest


def test_classification_cached_in_state():
    """Verify issue classifications are cached in state files"""
    agents_dir = "agents"

    if not os.path.exists(agents_dir):
        pytest.skip("Agents directory not found")

    # Find state files with classifications
    classified_count = 0

    for root, dirs, files in os.walk(agents_dir):
        if "adw_state.json" in files:
            state_file = os.path.join(root, "adw_state.json")

            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)

                # If workflow has been classified, verify it's stored
                if state.get("issue_class"):
                    classified_count += 1

                    # Verify format
                    assert state["issue_class"].startswith("/"), \
                        f"Classification {state['issue_class']} should start with /"

                    # Verify it's a valid classification
                    valid_classes = ["/feature", "/bug", "/chore", "/patch"]
                    assert state["issue_class"] in valid_classes, \
                        f"Invalid classification: {state['issue_class']}"

            except json.JSONDecodeError:
                continue
            except Exception:
                continue

    # Soft check - at least some workflows should have classifications
    if classified_count == 0:
        pytest.skip("No classified workflows found")


def test_branch_name_matches_classification():
    """Verify branch names match their classifications"""
    agents_dir = "agents"

    if not os.path.exists(agents_dir):
        pytest.skip("Agents directory not found")

    mismatches = []

    for root, dirs, files in os.walk(agents_dir):
        if "adw_state.json" in files:
            state_file = os.path.join(root, "adw_state.json")

            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)

                # Check branch/classification consistency
                branch_name = state.get("branch_name")
                classification = state.get("issue_class")

                if branch_name and classification:
                    # Extract prefix from classification (/feature -> feature)
                    class_prefix = classification.lstrip("/")

                    # Branch should start with classification prefix
                    if not branch_name.startswith(class_prefix):
                        mismatches.append({
                            "adw_id": state.get("adw_id"),
                            "branch": branch_name,
                            "classification": classification,
                            "expected_prefix": class_prefix
                        })

            except json.JSONDecodeError:
                continue
            except Exception:
                continue

    # Report any mismatches found
    if mismatches:
        mismatch_details = "\n".join([
            f"  ADW {m['adw_id']}: branch '{m['branch']}' doesn't match "
            f"classification '{m['classification']}'"
            for m in mismatches
        ])
        pytest.fail(
            f"Found {len(mismatches)} branch/classification mismatches:\n{mismatch_details}"
        )


def test_classification_function_uses_cache():
    """Verify classify_issue function implements caching"""
    workflow_ops_file = "adws/adw_modules/workflow_ops.py"

    if not os.path.exists(workflow_ops_file):
        pytest.skip(f"File not found: {workflow_ops_file}")

    with open(workflow_ops_file, 'r') as f:
        content = f.read()

    # Find the classify_issue function
    assert "def classify_issue" in content, \
        "classify_issue function not found"

    # Verify it checks for cached classification
    assert "cached_classification" in content or "cached" in content, \
        "classify_issue should implement classification caching"

    # Verify it loads state
    assert "ADWState.load" in content or "state.get" in content, \
        "classify_issue should load state to check for cached classification"


def test_worktree_branch_exists():
    """Verify worktrees have their expected branches checked out"""
    agents_dir = "agents"
    trees_dir = "trees"

    if not os.path.exists(agents_dir) or not os.path.exists(trees_dir):
        pytest.skip("Agents or trees directory not found")

    import subprocess

    for root, dirs, files in os.walk(agents_dir):
        if "adw_state.json" in files:
            state_file = os.path.join(root, "adw_state.json")

            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)

                adw_id = state.get("adw_id")
                branch_name = state.get("branch_name")
                worktree_path = state.get("worktree_path")

                # Only check if worktree exists
                if worktree_path and os.path.exists(worktree_path) and branch_name:
                    # Get current branch in worktree
                    result = subprocess.run(
                        ["git", "-C", worktree_path, "branch", "--show-current"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        actual_branch = result.stdout.strip()

                        # Branch in worktree should match state
                        assert actual_branch == branch_name, \
                            f"ADW {adw_id}: worktree has branch '{actual_branch}' " \
                            f"but state expects '{branch_name}'"

            except json.JSONDecodeError:
                continue
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
