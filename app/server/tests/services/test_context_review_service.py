"""Tests for context review service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context_review_agent import ContextReviewResult
from models.context_review import ContextReview
from services.context_review_service import ContextReviewService


@pytest.fixture
def mock_repository():
    """Mock context review repository."""
    return MagicMock()


@pytest.fixture
def mock_agent():
    """Mock context review agent."""
    agent = MagicMock()
    agent.generate_cache_key = MagicMock(return_value="test-cache-key-123")
    return agent


@pytest.fixture
def service(mock_repository, mock_agent):
    """Create service with mocked dependencies."""
    return ContextReviewService(
        repository=mock_repository,
        agent=mock_agent
    )


class TestContextReviewService:
    """Test suite for ContextReviewService."""

    @pytest.mark.asyncio
    async def test_start_analysis_creates_review(self, service, mock_repository):
        """Test that start_analysis creates a review record."""
        mock_repository.check_cache.return_value = None
        mock_repository.create_review.return_value = 123

        # Mock agent analysis
        service.agent.analyze_context = AsyncMock(return_value=ContextReviewResult(
            integration_strategy="Test strategy",
            files_to_modify=["app.py"],
            files_to_create=["new.py"],
            reference_files=[],
            risks=[],
            optimized_context={"must_read": [], "optional": [], "skip": []},
            estimated_tokens=1000
        ))

        review_id = await service.start_analysis(
            "Test description",
            "/test/project"
        )

        assert review_id == 123
        mock_repository.create_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_analysis_with_cache_hit(self, service, mock_repository):
        """Test that cached results are used when available."""
        cached_result = json.dumps({
            "integration_strategy": "Cached strategy",
            "files_to_modify": ["cached.py"],
            "files_to_create": [],
            "reference_files": [],
            "risks": [],
            "optimized_context": {"must_read": [], "optional": [], "skip": []},
            "estimated_tokens": 500
        })

        mock_repository.check_cache.return_value = cached_result
        mock_repository.create_review.return_value = 456

        review_id = await service.start_analysis(
            "Test description",
            "/test/project"
        )

        assert review_id == 456

        # Should not call agent.analyze_context
        service.agent.analyze_context.assert_not_called()

        # Should create review with cached result
        call_args = mock_repository.create_review.call_args[0][0]
        assert call_args.status == "complete"
        assert call_args.result == cached_result

    @pytest.mark.asyncio
    async def test_run_analysis_updates_status(self, service, mock_repository):
        """Test that analysis updates review status correctly."""
        service.agent.analyze_context = AsyncMock(return_value=ContextReviewResult(
            integration_strategy="Test",
            files_to_modify=[],
            files_to_create=[],
            reference_files=[],
            risks=[],
            optimized_context={"must_read": [], "optional": [], "skip": []},
            estimated_tokens=1000
        ))

        await service._run_analysis(1, "Test desc", "/test/path")

        # Should update to analyzing, then complete
        calls = mock_repository.update_review_status.call_args_list
        assert len(calls) == 2

        # First call: analyzing
        assert calls[0][0][0] == 1  # review_id
        assert calls[0][0][1] == "analyzing"  # status

        # Second call: complete
        assert calls[1][0][0] == 1
        assert calls[1][0][1] == "complete"

    @pytest.mark.asyncio
    async def test_run_analysis_handles_failure(self, service, mock_repository):
        """Test that analysis failures update status to failed."""
        service.agent.analyze_context = AsyncMock(
            side_effect=Exception("Analysis failed")
        )

        with pytest.raises(Exception, match="Analysis failed"):
            await service._run_analysis(1, "Test desc", "/test/path")

        # Should update status to failed
        calls = mock_repository.update_review_status.call_args_list
        assert any(call[0][1] == "failed" for call in calls)

    @pytest.mark.asyncio
    async def test_run_analysis_caches_result(self, service, mock_repository):
        """Test that successful analysis caches result."""
        service.agent.analyze_context = AsyncMock(return_value=ContextReviewResult(
            integration_strategy="Test",
            files_to_modify=[],
            files_to_create=[],
            reference_files=[],
            risks=[],
            optimized_context={"must_read": [], "optional": [], "skip": []},
            estimated_tokens=1000
        ))

        await service._run_analysis(1, "Test desc", "/test/path")

        # Should cache the result
        mock_repository.cache_result.assert_called_once()
        cache_key = service.agent.generate_cache_key("Test desc", "/test/path")
        assert mock_repository.cache_result.call_args[0][0] == cache_key

    @pytest.mark.asyncio
    async def test_create_suggestions_from_result(self, service, mock_repository):
        """Test creating suggestion records from analysis result."""
        result = {
            "integration_strategy": "Test strategy",
            "files_to_modify": ["app.py", "config.py"],
            "files_to_create": ["new.py"],
            "reference_files": ["example.py"],
            "risks": ["Breaking change"]
        }

        await service._create_suggestions_from_result(123, result)

        # Should create suggestions
        mock_repository.create_suggestions.assert_called_once()
        suggestions = mock_repository.create_suggestions.call_args[0][0]

        # Should have 5 suggestions (2 modify + 1 create + 1 reference + 1 risk + 1 strategy)
        assert len(suggestions) == 6

        # Check types
        types = [s.suggestion_type for s in suggestions]
        assert "file-to-modify" in types
        assert "file-to-create" in types
        assert "reference" in types
        assert "risk" in types
        assert "strategy" in types

    @pytest.mark.asyncio
    async def test_create_suggestions_empty_result(self, service, mock_repository):
        """Test creating suggestions from empty result."""
        result = {}

        await service._create_suggestions_from_result(123, result)

        # Should still create suggestions (for strategy if present)
        # In this case, no strategy so should create empty list
        mock_repository.create_suggestions.assert_called_once()
        suggestions = mock_repository.create_suggestions.call_args[0][0]
        assert len(suggestions) == 0

    def test_estimate_cost(self, service):
        """Test token cost estimation."""
        # Test with 1000 tokens
        cost = service._estimate_cost(1000)

        # Should be positive
        assert cost > 0

        # Should be reasonable (rough check)
        assert cost < 0.01  # Less than 1 cent for 1000 tokens

        # More tokens = higher cost
        cost_2000 = service._estimate_cost(2000)
        assert cost_2000 > cost

    def test_estimate_cost_zero_tokens(self, service):
        """Test cost estimation with zero tokens."""
        cost = service._estimate_cost(0)
        assert cost == 0

    @pytest.mark.asyncio
    async def test_get_review_result(self, service, mock_repository):
        """Test fetching review with suggestions."""
        mock_review = MagicMock()
        mock_review.to_dict.return_value = {
            "id": 123,
            "status": "complete",
            "result": {"strategy": "test"}
        }

        mock_suggestions = [
            MagicMock(to_dict=MagicMock(return_value={"id": 1, "type": "file-to-modify"})),
            MagicMock(to_dict=MagicMock(return_value={"id": 2, "type": "risk"}))
        ]

        mock_repository.get_review.return_value = mock_review
        mock_repository.get_suggestions.return_value = mock_suggestions

        result = await service.get_review_result(123)

        assert result is not None
        assert "review" in result
        assert "suggestions" in result
        assert len(result["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_get_review_result_not_found(self, service, mock_repository):
        """Test fetching non-existent review."""
        mock_repository.get_review.return_value = None

        result = await service.get_review_result(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_cache_for_description_hit(self, service, mock_repository):
        """Test cache check with cache hit."""
        cached_result = json.dumps({
            "integration_strategy": "Cached",
            "estimated_tokens": 500
        })

        mock_repository.check_cache.return_value = cached_result

        result = await service.check_cache_for_description(
            "Test desc",
            "/test/path"
        )

        assert result["cached"] is True
        assert "result" in result
        assert result["result"]["integration_strategy"] == "Cached"

    @pytest.mark.asyncio
    async def test_check_cache_for_description_miss(self, service, mock_repository):
        """Test cache check with cache miss."""
        mock_repository.check_cache.return_value = None

        result = await service.check_cache_for_description(
            "Test desc",
            "/test/path"
        )

        assert result["cached"] is False
        assert "result" not in result

    def test_calculate_token_savings(self, service):
        """Test token savings calculation."""
        optimized_context = {
            "must_read": ["file1.py", "file2.py"],
            "optional": ["file3.py", "file4.py"],
            "skip": ["file5.py", "file6.py", "file7.py"]
        }

        savings = service.calculate_token_savings(optimized_context)

        assert "before_tokens" in savings
        assert "after_tokens" in savings
        assert "savings_tokens" in savings
        assert "savings_percent" in savings

        # Should show savings
        assert savings["savings_tokens"] > 0
        assert savings["savings_percent"] > 0

        # File counts
        assert savings["files_must_read"] == 2
        assert savings["files_optional"] == 4
        assert savings["files_skip"] == 3

    def test_calculate_token_savings_empty_context(self, service):
        """Test token savings with empty context."""
        optimized_context = {
            "must_read": [],
            "optional": [],
            "skip": []
        }

        savings = service.calculate_token_savings(optimized_context)

        assert savings["before_tokens"] == 0
        assert savings["after_tokens"] == 0
        assert savings["savings_tokens"] == 0
        assert savings["savings_percent"] == 0

    def test_calculate_token_savings_no_optimization(self, service):
        """Test token savings when no files are skipped."""
        optimized_context = {
            "must_read": ["file1.py", "file2.py"],
            "optional": [],
            "skip": []
        }

        savings = service.calculate_token_savings(optimized_context)

        # Should still calculate correctly
        assert savings["before_tokens"] > 0
        assert savings["after_tokens"] > 0

    @pytest.mark.asyncio
    async def test_start_analysis_with_workflow_id(self, service, mock_repository):
        """Test starting analysis with workflow ID."""
        mock_repository.check_cache.return_value = None
        mock_repository.create_review.return_value = 789

        service.agent.analyze_context = AsyncMock(return_value=ContextReviewResult(
            integration_strategy="Test",
            files_to_modify=[],
            files_to_create=[],
            reference_files=[],
            risks=[],
            optimized_context={"must_read": [], "optional": [], "skip": []},
            estimated_tokens=1000
        ))

        review_id = await service.start_analysis(
            "Test desc",
            "/test/path",
            workflow_id="workflow-abc-123",
            issue_number=42
        )

        assert review_id == 789

        # Should pass workflow_id and issue_number to review
        call_args = mock_repository.create_review.call_args[0][0]
        assert call_args.workflow_id == "workflow-abc-123"
        assert call_args.issue_number == 42
