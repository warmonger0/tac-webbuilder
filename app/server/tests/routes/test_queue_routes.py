"""
Tests for queue routes validation.

Tests the EnqueueRequest model validators to ensure data integrity
and prevent invalid data from entering the phase queue.
"""
import pytest
from pydantic import ValidationError
from routes.queue_routes import EnqueueRequest


def test_enqueue_request_valid():
    """Test valid EnqueueRequest."""
    request = EnqueueRequest(
        parent_issue=114,
        phase_number=2,
        phase_data={
            "workflow_type": "adw_sdlc_complete_iso",
            "adw_id": "adw_12345"
        }
    )
    assert request.parent_issue == 114
    assert request.phase_number == 2
    assert request.phase_data["workflow_type"] == "adw_sdlc_complete_iso"
    assert request.phase_data["adw_id"] == "adw_12345"


def test_enqueue_request_hopper_workflow():
    """Test hopper workflow with parent_issue=0."""
    request = EnqueueRequest(
        parent_issue=0,  # Valid for hopper workflows
        phase_number=1,
        phase_data={
            "workflow_type": "adw_lightweight_iso",
            "adw_id": "hopper_001"
        }
    )
    assert request.parent_issue == 0


def test_enqueue_request_with_optional_fields():
    """Test request with optional fields in phase_data."""
    request = EnqueueRequest(
        parent_issue=114,
        phase_number=1,
        phase_data={
            "workflow_type": "adw_sdlc_complete_iso",
            "adw_id": "adw_12345",
            "model": "sonnet",
            "skip_e2e": True,
            "fix_mode": False
        }
    )
    assert request.phase_data["model"] == "sonnet"
    assert request.phase_data["skip_e2e"] is True


def test_enqueue_request_with_dependencies():
    """Test request with valid depends_on_phase."""
    request = EnqueueRequest(
        parent_issue=114,
        phase_number=3,
        depends_on_phase=2,
        phase_data={
            "workflow_type": "adw_sdlc_complete_iso",
            "adw_id": "adw_12345"
        }
    )
    assert request.depends_on_phase == 2
    assert request.phase_number == 3


def test_enqueue_request_negative_parent_issue():
    """Test that negative parent_issue is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=-1,
            phase_number=1,
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "parent_issue" in str(exc_info.value)
    assert "greater than or equal to 0" in str(exc_info.value).lower()


def test_enqueue_request_zero_phase_number():
    """Test that phase_number < 1 is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=0,  # Invalid
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "phase_number" in str(exc_info.value)
    assert "greater than or equal to 1" in str(exc_info.value).lower()


def test_enqueue_request_phase_number_too_high():
    """Test that phase_number > 20 is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=21,  # Invalid
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "phase_number" in str(exc_info.value)
    assert "less than or equal to 20" in str(exc_info.value).lower()


def test_enqueue_request_missing_workflow_type():
    """Test that missing workflow_type is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "adw_id": "adw_12345"
                # Missing workflow_type
            }
        )
    assert "workflow_type" in str(exc_info.value)
    assert "missing required fields" in str(exc_info.value).lower()


def test_enqueue_request_missing_adw_id():
    """Test that missing adw_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso"
                # Missing adw_id
            }
        )
    assert "adw_id" in str(exc_info.value)
    assert "missing required fields" in str(exc_info.value).lower()


def test_enqueue_request_empty_phase_data():
    """Test that empty phase_data is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={}  # Empty
        )
    assert "phase_data" in str(exc_info.value)
    assert "missing required fields" in str(exc_info.value).lower()


def test_enqueue_request_empty_workflow_type():
    """Test that empty workflow_type string is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "workflow_type": "   ",  # Empty after strip
                "adw_id": "adw_12345"
            }
        )
    assert "workflow_type" in str(exc_info.value)
    assert "cannot be empty" in str(exc_info.value).lower()


def test_enqueue_request_empty_adw_id():
    """Test that empty adw_id string is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "   "  # Empty after strip
            }
        )
    assert "adw_id" in str(exc_info.value)
    assert "cannot be empty" in str(exc_info.value).lower()


def test_enqueue_request_non_string_workflow_type():
    """Test that non-string workflow_type is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "workflow_type": 123,  # Not a string
                "adw_id": "adw_12345"
            }
        )
    assert "workflow_type" in str(exc_info.value)
    assert "must be a string" in str(exc_info.value).lower()


def test_enqueue_request_non_string_adw_id():
    """Test that non-string adw_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=1,
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": 12345  # Not a string
            }
        )
    assert "adw_id" in str(exc_info.value)
    assert "must be a string" in str(exc_info.value).lower()


def test_enqueue_request_invalid_depends_on_equal():
    """Test that depends_on_phase == phase_number is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=2,
            depends_on_phase=2,  # Must be < phase_number
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "depends_on_phase" in str(exc_info.value)
    assert "must be less than phase_number" in str(exc_info.value).lower()


def test_enqueue_request_invalid_depends_on_greater():
    """Test that depends_on_phase > phase_number is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=2,
            depends_on_phase=3,  # Must be < phase_number
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "depends_on_phase" in str(exc_info.value)
    assert "must be less than phase_number" in str(exc_info.value).lower()


def test_enqueue_request_depends_on_zero():
    """Test that depends_on_phase = 0 is rejected (must be >= 1)."""
    with pytest.raises(ValidationError) as exc_info:
        EnqueueRequest(
            parent_issue=114,
            phase_number=2,
            depends_on_phase=0,  # Invalid, must be >= 1
            phase_data={
                "workflow_type": "adw_sdlc_complete_iso",
                "adw_id": "adw_12345"
            }
        )
    assert "depends_on_phase" in str(exc_info.value)
    assert "greater than or equal to 1" in str(exc_info.value).lower()


def test_enqueue_request_boundary_values():
    """Test boundary values for all fields."""
    # Minimum valid values
    request = EnqueueRequest(
        parent_issue=0,
        phase_number=1,
        depends_on_phase=None,
        phase_data={
            "workflow_type": "a",
            "adw_id": "b"
        }
    )
    assert request.parent_issue == 0
    assert request.phase_number == 1

    # Maximum valid values
    request = EnqueueRequest(
        parent_issue=999999,
        phase_number=20,
        depends_on_phase=19,
        phase_data={
            "workflow_type": "adw_sdlc_complete_iso",
            "adw_id": "adw_12345"
        }
    )
    assert request.parent_issue == 999999
    assert request.phase_number == 20
    assert request.depends_on_phase == 19
