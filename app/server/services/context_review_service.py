"""Service layer for context review operations."""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from core.context_review_agent import ContextReviewAgent, ContextReviewResult
from models.context_review import ContextReview, ContextSuggestion
from repositories.context_review_repository import ContextReviewRepository

logger = logging.getLogger(__name__)


class ContextReviewService:
    """
    Service layer for context review operations.

    Orchestrates:
    - Review creation
    - Agent analysis execution
    - Result caching
    - Suggestion persistence
    """

    def __init__(
        self,
        repository: Optional[ContextReviewRepository] = None,
        agent: Optional[ContextReviewAgent] = None
    ):
        """
        Initialize service with dependencies.

        Args:
            repository: Context review repository (or creates default)
            agent: Context review agent (or creates default)
        """
        self.repository = repository or ContextReviewRepository()
        self.agent = agent or ContextReviewAgent()

    async def start_analysis(
        self,
        change_description: str,
        project_path: str,
        workflow_id: Optional[str] = None,
        issue_number: Optional[int] = None
    ) -> int:
        """
        Start a context analysis.

        Creates review record and executes analysis asynchronously.

        Args:
            change_description: User's description of proposed change
            project_path: Path to project directory
            workflow_id: Optional ADW workflow ID
            issue_number: Optional GitHub issue number

        Returns:
            Review ID for tracking

        Raises:
            Exception: If analysis fails
        """
        logger.info("Starting context analysis")

        # Check cache first
        cache_key = self.agent.generate_cache_key(
            change_description,
            project_path
        )
        cached_result = self.repository.check_cache(cache_key)

        if cached_result:
            logger.info("Using cached analysis result")
            # Create review record with cached result
            review = ContextReview(
                change_description=change_description,
                project_path=project_path,
                workflow_id=workflow_id,
                issue_number=issue_number,
                status="complete",
                result=cached_result
            )
            review_id = self.repository.create_review(review)

            # Parse cached result and create suggestions
            result_dict = json.loads(cached_result)
            await self._create_suggestions_from_result(
                review_id,
                result_dict
            )

            return review_id

        # Create review record
        review = ContextReview(
            change_description=change_description,
            project_path=project_path,
            workflow_id=workflow_id,
            issue_number=issue_number,
            status="pending"
        )
        review_id = self.repository.create_review(review)

        # Run analysis
        await self._run_analysis(review_id, change_description, project_path)

        return review_id

    async def _run_analysis(
        self,
        review_id: int,
        description: str,
        project_path: str
    ) -> None:
        """
        Execute agent analysis and update review.

        Args:
            review_id: ID of the review being analyzed
            description: Change description
            project_path: Project path

        Raises:
            Exception: If analysis fails
        """
        start_time = time.time()

        try:
            # Update status to analyzing
            self.repository.update_review_status(review_id, "analyzing")

            # Run agent analysis
            result = await self.agent.analyze_context(
                description,
                project_path
            )

            # Calculate duration and cost
            duration = time.time() - start_time
            cost = self._estimate_cost(result.estimated_tokens)

            # Convert result to dictionary
            result_dict = {
                "integration_strategy": result.integration_strategy,
                "files_to_modify": result.files_to_modify,
                "files_to_create": result.files_to_create,
                "reference_files": result.reference_files,
                "risks": result.risks,
                "optimized_context": result.optimized_context,
                "estimated_tokens": result.estimated_tokens
            }

            # Update review with results
            self.repository.update_review_status(
                review_id,
                status="complete",
                result=result_dict,
                duration=duration,
                cost=cost
            )

            # Create suggestions
            await self._create_suggestions_from_result(review_id, result_dict)

            # Cache result
            cache_key = self.agent.generate_cache_key(description, project_path)
            self.repository.cache_result(cache_key, result_dict)

            logger.info(
                f"Analysis complete for review {review_id} "
                f"({duration:.2f}s, ${cost:.4f})"
            )

        except Exception as e:
            # Update status to failed
            self.repository.update_review_status(review_id, "failed")
            logger.error(f"Analysis failed for review {review_id}: {e}")
            raise

    async def _create_suggestions_from_result(
        self,
        review_id: int,
        result: Dict
    ) -> None:
        """
        Create suggestion records from analysis result.

        Args:
            review_id: Review ID
            result: Analysis result dictionary
        """
        suggestions = []

        # Files to modify
        for i, file_path in enumerate(result.get("files_to_modify", [])):
            suggestions.append(ContextSuggestion(
                review_id=review_id,
                suggestion_type="file-to-modify",
                suggestion_text=file_path,
                confidence=0.9,
                priority=i + 1,
                rationale="Existing file requiring modifications"
            ))

        # Files to create
        for i, file_path in enumerate(result.get("files_to_create", [])):
            suggestions.append(ContextSuggestion(
                review_id=review_id,
                suggestion_type="file-to-create",
                suggestion_text=file_path,
                confidence=0.85,
                priority=i + 1,
                rationale="New file to be created"
            ))

        # Reference files
        for i, file_path in enumerate(result.get("reference_files", [])):
            suggestions.append(ContextSuggestion(
                review_id=review_id,
                suggestion_type="reference",
                suggestion_text=file_path,
                confidence=0.8,
                priority=i + 1,
                rationale="Reference file for patterns/examples"
            ))

        # Risks
        for i, risk in enumerate(result.get("risks", [])):
            suggestions.append(ContextSuggestion(
                review_id=review_id,
                suggestion_type="risk",
                suggestion_text=risk,
                confidence=0.75,
                priority=i + 1,
                rationale="Potential risk identified"
            ))

        # Strategy as a suggestion
        strategy = result.get("integration_strategy", "")
        if strategy:
            suggestions.append(ContextSuggestion(
                review_id=review_id,
                suggestion_type="strategy",
                suggestion_text=strategy,
                confidence=1.0,
                priority=0,
                rationale="Overall integration approach"
            ))

        # Persist suggestions
        if suggestions:
            self.repository.create_suggestions(suggestions)

    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate API cost based on token count.

        Uses Claude 3.5 Haiku pricing.

        Args:
            tokens: Estimated token count

        Returns:
            Cost in USD
        """
        # Haiku pricing: $0.25 per 1M input tokens, $1.25 per 1M output tokens
        # Estimate: 70% input, 30% output
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)

        input_cost = (input_tokens / 1_000_000) * 0.25
        output_cost = (output_tokens / 1_000_000) * 1.25

        return input_cost + output_cost

    async def get_review_result(
        self,
        review_id: int
    ) -> Optional[Dict]:
        """
        Fetch review result with suggestions.

        Args:
            review_id: Review ID

        Returns:
            Dictionary with review data and suggestions, or None if not found
        """
        review = self.repository.get_review(review_id)
        if not review:
            return None

        suggestions = self.repository.get_suggestions(review_id)

        return {
            "review": review.to_dict(),
            "suggestions": [s.to_dict() for s in suggestions]
        }

    async def check_cache_for_description(
        self,
        description: str,
        project_path: str
    ) -> Optional[Dict]:
        """
        Check if analysis is cached for description.

        Args:
            description: Change description
            project_path: Project path

        Returns:
            Dictionary with cached result if found, None otherwise
        """
        cache_key = self.agent.generate_cache_key(description, project_path)
        cached_result = self.repository.check_cache(cache_key)

        if cached_result:
            result_dict = json.loads(cached_result)
            return {
                "cached": True,
                "result": result_dict
            }

        return {"cached": False}

    def calculate_token_savings(
        self,
        optimized_context: Dict[str, List[str]]
    ) -> Dict:
        """
        Calculate token savings from context optimization.

        Args:
            optimized_context: Categorized files (must_read, optional, skip)

        Returns:
            Dictionary with before/after token estimates and savings
        """
        must_read = len(optimized_context.get("must_read", []))
        optional = len(optimized_context.get("optional", []))
        skip = len(optimized_context.get("skip", []))

        # Estimate tokens per file (average)
        tokens_per_file = 500

        total_files = must_read + optional + skip
        before_tokens = total_files * tokens_per_file
        after_tokens = must_read * tokens_per_file + optional * tokens_per_file * 0.5

        savings_tokens = before_tokens - after_tokens
        savings_percent = (savings_tokens / before_tokens * 100) if before_tokens > 0 else 0

        return {
            "before_tokens": before_tokens,
            "after_tokens": int(after_tokens),
            "savings_tokens": int(savings_tokens),
            "savings_percent": round(savings_percent, 1),
            "files_must_read": must_read,
            "files_optional": optional,
            "files_skip": skip
        }
