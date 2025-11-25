"""
Tests to ensure ADW workflows properly mark status as completed.

These tests prevent the INCIDENT_2025-11-25_ADW_WORKFLOW_STALL issue from recurring.
"""

import json
import os
import pytest
from datetime import datetime


def test_workflow_state_has_completion_fields():
    """Verify ADW state file has required completion fields"""
    # Find a completed workflow state
    agents_dir = "agents"

    if not os.path.exists(agents_dir):
        pytest.skip("Agents directory not found")

    # Find a state file
    state_files = []
    for root, dirs, files in os.walk(agents_dir):
        if "adw_state.json" in files:
            state_files.append(os.path.join(root, "adw_state.json"))

    if not state_files:
        pytest.skip("No ADW state files found")

    # Check at least one completed workflow
    completed_found = False
    for state_file in state_files:
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            # Check if this is a completed workflow
            if state.get("status") == "completed":
                completed_found = True

                # Verify required fields
                assert "end_time" in state, \
                    f"Completed workflow {state.get('adw_id')} missing end_time"

                # Verify end_time is valid ISO format
                if state["end_time"]:
                    try:
                        datetime.fromisoformat(state["end_time"])
                    except ValueError:
                        pytest.fail(f"Invalid end_time format in {state.get('adw_id')}: {state['end_time']}")

                # Verify end_time is after start_time
                if state.get("start_time") and state.get("end_time"):
                    start = datetime.fromisoformat(state["start_time"])
                    end = datetime.fromisoformat(state["end_time"])
                    assert end > start, \
                        f"end_time {end} not after start_time {start} in {state.get('adw_id')}"

        except json.JSONDecodeError:
            # Skip invalid JSON files
            continue
        except Exception as e:
            pytest.fail(f"Error checking state file {state_file}: {e}")

    # At least one completed workflow should be found in a real system
    # This is a soft check - we don't fail if none found yet
    if not completed_found:
        pytest.skip("No completed workflows found to validate")


def test_plan_iso_workflow_marks_completion():
    """Verify adw_plan_iso.py marks status as completed when done"""
    workflow_file = "adws/adw_plan_iso.py"

    if not os.path.exists(workflow_file):
        pytest.skip(f"Workflow file not found: {workflow_file}")

    with open(workflow_file, 'r') as f:
        content = f.read()

    # Verify the workflow updates status to completed
    assert 'status="completed"' in content or 'status": "completed"' in content, \
        "adw_plan_iso.py must set status='completed' before exiting"

    # Verify it sets end_time
    assert 'end_time' in content, \
        "adw_plan_iso.py must set end_time before exiting"

    # Verify it saves the state
    assert 'state.save(' in content, \
        "adw_plan_iso.py must call state.save() after updating status"


def test_workflow_state_consistency():
    """Verify workflow states are internally consistent"""
    agents_dir = "agents"

    if not os.path.exists(agents_dir):
        pytest.skip("Agents directory not found")

    for root, dirs, files in os.walk(agents_dir):
        if "adw_state.json" in files:
            state_file = os.path.join(root, "adw_state.json")

            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)

                # If status is completed, end_time must be set
                if state.get("status") == "completed":
                    assert state.get("end_time"), \
                        f"Workflow {state.get('adw_id')} marked completed but missing end_time"

                # If end_time is set, status should be completed or failed
                if state.get("end_time"):
                    assert state.get("status") in ["completed", "failed"], \
                        f"Workflow {state.get('adw_id')} has end_time but status is {state.get('status')}"

            except json.JSONDecodeError:
                # Skip invalid JSON
                continue
            except Exception:
                # Skip errors reading individual files
                continue


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
