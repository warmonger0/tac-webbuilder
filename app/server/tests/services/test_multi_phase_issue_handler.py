"""
Tests for MultiPhaseIssueHandler

Tests multi-phase issue creation, pattern passing, and queue integration.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest
from core.data_models import Phase, SubmitRequestData
from services.multi_phase_issue_handler import MultiPhaseIssueHandler
from services.phase_queue_service import PhaseQueueService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_multi_phase.db")

        # Initialize database with schema
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS phase_queue (
              queue_id TEXT PRIMARY KEY,
              parent_issue INTEGER NOT NULL,
              phase_number INTEGER NOT NULL,
              issue_number INTEGER,
              status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
              depends_on_phase INTEGER,
              phase_data TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              error_message TEXT,
              adw_id TEXT,
              pr_number INTEGER,
              priority INTEGER DEFAULT 50,
              queue_position INTEGER,
              ready_timestamp TEXT,
              started_timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

        yield db_path


@pytest.fixture
def queue_service(temp_db):
    """Create PhaseQueueService instance"""
    return PhaseQueueService(db_path=temp_db)


@pytest.fixture
def mock_github_poster():
    """Create mock GitHub poster"""
    poster = MagicMock()
    poster.post_issue = MagicMock(return_value=12345)  # Mock issue number
    return poster


@pytest.fixture
def handler(mock_github_poster, queue_service):
    """Create MultiPhaseIssueHandler instance"""
    return MultiPhaseIssueHandler(
        github_poster=mock_github_poster,
        phase_queue_service=queue_service
    )


@pytest.mark.asyncio
async def test_multi_phase_without_patterns(handler, queue_service):
    """Test multi-phase request without predicted patterns"""
    request = SubmitRequestData(
        nl_input="Multi-phase workflow",
        phases=[
            Phase(number=1, title="Phase 1", content="First phase"),
            Phase(number=2, title="Phase 2", content="Second phase"),
            Phase(number=3, title="Phase 3", content="Third phase")
        ],
        auto_post=False
    )

    response = await handler.handle_multi_phase_request(request)

    # Verify response
    assert response.is_multi_phase is True
    assert len(response.child_issues) == 3

    # Verify phases in queue
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 3

    # Verify no patterns stored
    for phase in phases:
        assert 'predicted_patterns' not in phase.phase_data


@pytest.mark.asyncio
async def test_multi_phase_with_patterns(handler, queue_service):
    """Test patterns passed correctly through multi-phase flow"""
    request = SubmitRequestData(
        nl_input="Run tests and build",
        phases=[
            Phase(number=1, title="Phase 1", content="Run backend tests"),
            Phase(number=2, title="Phase 2", content="Build frontend")
        ],
        auto_post=False
    )

    # Predicted patterns from pattern predictor
    predicted_patterns = [
        {"pattern": "test:pytest:backend", "confidence": 0.95, "reasoning": "pytest keyword"},
        {"pattern": "build:npm:frontend", "confidence": 0.90, "reasoning": "build + frontend"}
    ]

    response = await handler.handle_multi_phase_request(request, predicted_patterns)

    # Verify response
    assert response.is_multi_phase is True
    assert len(response.child_issues) == 2

    # Verify patterns in queue
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 2

    # Both phases should have patterns
    expected_pattern_strings = ["test:pytest:backend", "build:npm:frontend"]
    for phase in phases:
        assert 'predicted_patterns' in phase.phase_data
        assert phase.phase_data['predicted_patterns'] == expected_pattern_strings


@pytest.mark.asyncio
async def test_multi_phase_patterns_extracted_from_dict(handler, queue_service):
    """Test that patterns are correctly extracted from prediction dicts"""
    request = SubmitRequestData(
        nl_input="Deploy application",
        phases=[
            Phase(number=1, title="Phase 1", content="Deploy to staging"),
            Phase(number=2, title="Phase 2", content="Verify deployment")
        ],
        auto_post=False
    )

    # Full prediction format with metadata
    predicted_patterns = [
        {
            "pattern": "deploy:staging",
            "confidence": 0.88,
            "reasoning": "staging keyword detected"
        }
    ]

    response = await handler.handle_multi_phase_request(request, predicted_patterns)

    # Verify only pattern strings stored (not full dict)
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 2
    assert phases[0].phase_data['predicted_patterns'] == ["deploy:staging"]
    assert phases[1].phase_data['predicted_patterns'] == ["deploy:staging"]


@pytest.mark.asyncio
async def test_multi_phase_with_empty_patterns(handler, queue_service):
    """Test multi-phase with empty patterns list"""
    request = SubmitRequestData(
        nl_input="Update docs",
        phases=[
            Phase(number=1, title="Phase 1", content="Update documentation"),
            Phase(number=2, title="Phase 2", content="Review documentation")
        ],
        auto_post=False
    )

    # Empty patterns list
    predicted_patterns = []

    response = await handler.handle_multi_phase_request(request, predicted_patterns)

    # Verify no patterns stored when empty
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 2
    assert 'predicted_patterns' not in phases[0].phase_data
    assert 'predicted_patterns' not in phases[1].phase_data


@pytest.mark.asyncio
async def test_multi_phase_patterns_persist_through_phases(handler, queue_service):
    """Test that all phases get the same pattern predictions"""
    request = SubmitRequestData(
        nl_input="Full workflow",
        phases=[
            Phase(number=1, title="Phase 1", content="Setup"),
            Phase(number=2, title="Phase 2", content="Execute"),
            Phase(number=3, title="Phase 3", content="Cleanup")
        ],
        auto_post=False
    )

    predicted_patterns = [
        {"pattern": "workflow:multi", "confidence": 0.85, "reasoning": "multi-phase detected"}
    ]

    response = await handler.handle_multi_phase_request(request, predicted_patterns)

    # All phases should have the same patterns
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 3

    for phase in phases:
        assert 'predicted_patterns' in phase.phase_data
        assert phase.phase_data['predicted_patterns'] == ["workflow:multi"]


@pytest.mark.asyncio
async def test_multi_phase_patterns_none_handling(handler, queue_service):
    """Test that None patterns handled gracefully"""
    request = SubmitRequestData(
        nl_input="Basic request",
        phases=[
            Phase(number=1, title="Phase 1", content="Do work"),
            Phase(number=2, title="Phase 2", content="Verify work")
        ],
        auto_post=False
    )

    # Explicitly pass None
    response = await handler.handle_multi_phase_request(request, predicted_patterns=None)

    # Should work without errors
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 2
    assert 'predicted_patterns' not in phases[0].phase_data
    assert 'predicted_patterns' not in phases[1].phase_data


@pytest.mark.asyncio
async def test_multi_phase_backward_compatibility(handler, queue_service):
    """Test backward compatibility - handler works without patterns parameter"""
    request = SubmitRequestData(
        nl_input="Legacy request",
        phases=[
            Phase(number=1, title="Phase 1", content="Legacy work"),
            Phase(number=2, title="Phase 2", content="Verify legacy work")
        ],
        auto_post=False
    )

    # Call without predicted_patterns parameter (uses default None)
    response = await handler.handle_multi_phase_request(request)

    # Should work normally
    phases = queue_service.get_queue_by_parent(0)
    assert len(phases) == 2
    assert response.is_multi_phase is True
