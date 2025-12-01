"""Tests for context review repository."""

import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from migrations import init_context_review_db
from models.context_review import ContextReview, ContextSuggestion
from repositories.context_review_repository import ContextReviewRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Initialize schema
    init_context_review_db(path)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def repository(temp_db):
    """Create repository instance with temp database."""
    return ContextReviewRepository(db_path=temp_db)


class TestContextReviewRepository:
    """Test suite for ContextReviewRepository."""

    def test_create_review(self, repository):
        """Test creating a new context review."""
        review = ContextReview(
            change_description="Add user authentication",
            project_path="/path/to/project",
            status="pending"
        )

        review_id = repository.create_review(review)

        assert review_id is not None
        assert review_id > 0

    def test_get_review(self, repository):
        """Test fetching a review by ID."""
        review = ContextReview(
            change_description="Add user authentication",
            project_path="/path/to/project",
            status="pending",
            workflow_id="test-workflow-123"
        )
        review_id = repository.create_review(review)

        fetched = repository.get_review(review_id)

        assert fetched is not None
        assert fetched.id == review_id
        assert fetched.change_description == "Add user authentication"
        assert fetched.project_path == "/path/to/project"
        assert fetched.status == "pending"
        assert fetched.workflow_id == "test-workflow-123"

    def test_get_review_not_found(self, repository):
        """Test fetching non-existent review returns None."""
        fetched = repository.get_review(99999)
        assert fetched is None

    def test_update_review_status(self, repository):
        """Test updating review status."""
        review = ContextReview(
            change_description="Test",
            project_path="/test",
            status="pending"
        )
        review_id = repository.create_review(review)

        updated = repository.update_review_status(
            review_id,
            status="complete",
            duration=1.5,
            cost=0.002
        )

        assert updated is True

        fetched = repository.get_review(review_id)
        assert fetched.status == "complete"
        assert fetched.analysis_duration_seconds == 1.5
        assert fetched.agent_cost == 0.002

    def test_update_review_with_result(self, repository):
        """Test updating review with analysis result."""
        review = ContextReview(
            change_description="Test",
            project_path="/test",
            status="analyzing"
        )
        review_id = repository.create_review(review)

        result = {
            "integration_strategy": "Create new module",
            "files_to_modify": ["app.py"],
            "files_to_create": ["auth.py"],
            "risks": ["Breaking change"],
            "estimated_tokens": 1500
        }

        updated = repository.update_review_status(
            review_id,
            status="complete",
            result=result
        )

        assert updated is True

        fetched = repository.get_review(review_id)
        assert fetched.status == "complete"
        assert fetched.result is not None
        parsed_result = json.loads(fetched.result)
        assert parsed_result["integration_strategy"] == "Create new module"

    def test_update_nonexistent_review(self, repository):
        """Test updating non-existent review returns False."""
        updated = repository.update_review_status(99999, "complete")
        assert updated is False

    def test_create_suggestions(self, repository):
        """Test batch creating suggestions."""
        review = ContextReview(
            change_description="Test",
            project_path="/test",
            status="complete"
        )
        review_id = repository.create_review(review)

        suggestions = [
            ContextSuggestion(
                review_id=review_id,
                suggestion_type="file-to-modify",
                suggestion_text="app/server/models/user.py",
                confidence=0.9,
                priority=1,
                rationale="User model needs auth fields"
            ),
            ContextSuggestion(
                review_id=review_id,
                suggestion_type="file-to-create",
                suggestion_text="app/server/auth/jwt_handler.py",
                confidence=0.85,
                priority=2,
                rationale="New JWT module needed"
            )
        ]

        suggestion_ids = repository.create_suggestions(suggestions)

        assert len(suggestion_ids) == 2
        assert all(sid > 0 for sid in suggestion_ids)

    def test_create_suggestions_empty_list(self, repository):
        """Test creating suggestions with empty list returns empty list."""
        suggestion_ids = repository.create_suggestions([])
        assert suggestion_ids == []

    def test_get_suggestions(self, repository):
        """Test fetching suggestions for a review."""
        review = ContextReview(
            change_description="Test",
            project_path="/test",
            status="complete"
        )
        review_id = repository.create_review(review)

        suggestions = [
            ContextSuggestion(
                review_id=review_id,
                suggestion_type="file-to-modify",
                suggestion_text="file1.py",
                priority=2
            ),
            ContextSuggestion(
                review_id=review_id,
                suggestion_type="risk",
                suggestion_text="Breaking change",
                priority=1
            )
        ]
        repository.create_suggestions(suggestions)

        fetched = repository.get_suggestions(review_id)

        assert len(fetched) == 2
        # Should be ordered by priority ASC
        assert fetched[0].suggestion_text == "Breaking change"
        assert fetched[0].priority == 1
        assert fetched[1].suggestion_text == "file1.py"
        assert fetched[1].priority == 2

    def test_get_suggestions_empty(self, repository):
        """Test fetching suggestions for review with none returns empty list."""
        review = ContextReview(
            change_description="Test",
            project_path="/test",
            status="complete"
        )
        review_id = repository.create_review(review)

        fetched = repository.get_suggestions(review_id)
        assert fetched == []

    def test_check_cache_miss(self, repository):
        """Test cache check when no entry exists."""
        result = repository.check_cache("nonexistent-key")
        assert result is None

    def test_cache_result_and_check(self, repository):
        """Test caching result and checking for it."""
        cache_key = "test-cache-key-123"
        result = {
            "integration_strategy": "Test strategy",
            "files_to_modify": ["test.py"],
            "estimated_tokens": 1000
        }

        cache_id = repository.cache_result(cache_key, result)
        assert cache_id > 0

        cached = repository.check_cache(cache_key)
        assert cached is not None

        parsed = json.loads(cached)
        assert parsed["integration_strategy"] == "Test strategy"
        assert parsed["estimated_tokens"] == 1000

    def test_cache_result_updates_existing(self, repository):
        """Test caching with same key updates existing entry."""
        cache_key = "test-key"

        # Cache first result
        result1 = {"data": "first"}
        cache_id_1 = repository.cache_result(cache_key, result1)

        # Cache second result with same key
        result2 = {"data": "second"}
        cache_id_2 = repository.cache_result(cache_key, result2)

        # Should reuse same cache ID
        assert cache_id_1 == cache_id_2

        # Should have updated content
        cached = repository.check_cache(cache_key)
        parsed = json.loads(cached)
        assert parsed["data"] == "second"

    def test_cleanup_old_cache(self, repository):
        """Test cleaning up old cache entries."""
        # Create old cache entry (simulate by direct DB manipulation)
        import sqlite3
        old_date = datetime.now() - timedelta(days=8)

        with sqlite3.connect(repository.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO context_cache (cache_key, analysis_result, created_at)
                VALUES (?, ?, ?)
                """,
                ("old-key", '{"test": "old"}', old_date.isoformat())
            )
            conn.commit()

        # Create recent cache entry
        repository.cache_result("recent-key", {"test": "recent"})

        # Cleanup entries older than 7 days
        deleted = repository.cleanup_old_cache(days=7)

        assert deleted == 1

        # Old entry should be gone
        assert repository.check_cache("old-key") is None

        # Recent entry should remain
        assert repository.check_cache("recent-key") is not None

    def test_get_review_by_workflow(self, repository):
        """Test fetching review by workflow ID."""
        review1 = ContextReview(
            change_description="First",
            project_path="/test",
            status="complete",
            workflow_id="workflow-123"
        )
        repository.create_review(review1)

        # Create second review for same workflow (should be most recent)
        review2 = ContextReview(
            change_description="Second",
            project_path="/test",
            status="pending",
            workflow_id="workflow-123"
        )
        repository.create_review(review2)

        fetched = repository.get_review_by_workflow("workflow-123")

        assert fetched is not None
        assert fetched.change_description == "Second"

    def test_get_review_by_workflow_not_found(self, repository):
        """Test fetching review for non-existent workflow."""
        fetched = repository.get_review_by_workflow("nonexistent")
        assert fetched is None

    def test_get_recent_reviews(self, repository):
        """Test fetching recent reviews."""
        # Create 5 reviews
        for i in range(5):
            review = ContextReview(
                change_description=f"Review {i}",
                project_path="/test",
                status="complete"
            )
            repository.create_review(review)

        recent = repository.get_recent_reviews(limit=3)

        assert len(recent) == 3
        # Should be ordered by most recent first
        assert recent[0].change_description == "Review 4"
        assert recent[1].change_description == "Review 3"
        assert recent[2].change_description == "Review 2"

    def test_get_recent_reviews_empty(self, repository):
        """Test fetching recent reviews when none exist."""
        recent = repository.get_recent_reviews()
        assert recent == []
