"""
Context Review API Routes

Endpoints for AI-powered codebase context analysis.
"""

import json
import logging
from datetime import datetime

from core.context_review_agent import ContextReviewAgent
from fastapi import APIRouter, HTTPException
from models.context_review import ContextReview
from pydantic import BaseModel
from repositories.context_review_repository import ContextReviewRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context-review", tags=["Context Review"])


# Pydantic models for API requests/responses
class AnalyzeRequest(BaseModel):
    """Request to analyze codebase context."""
    change_description: str
    project_path: str
    workflow_id: str | None = None
    issue_number: int | None = None


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""
    review_id: int
    status: str
    message: str


class ReviewResultResponse(BaseModel):
    """Response containing review result."""
    review_id: int
    status: str
    result: dict | None
    created_at: str


class CacheLookupRequest(BaseModel):
    """Request to check cache."""
    change_description: str
    project_path: str


class CacheLookupResponse(BaseModel):
    """Response from cache lookup."""
    cached: bool
    review_id: int | None = None
    result: dict | None = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_context(request: AnalyzeRequest):
    """
    Start context analysis for a proposed change.

    This endpoint:
    1. Creates a review record with status='analyzing'
    2. Runs AI analysis in background (synchronous for MVP)
    3. Returns review_id for polling

    Args:
        request: Analysis request with description and project path

    Returns:
        AnalyzeResponse: Review ID and status
    """
    try:
        repository = ContextReviewRepository()
        agent = ContextReviewAgent()

        # Create review record
        review = ContextReview(
            workflow_id=request.workflow_id,
            issue_number=request.issue_number,
            change_description=request.change_description,
            project_path=request.project_path,
            status="analyzing",
            analysis_timestamp=datetime.now(),
        )

        review_id = repository.create_review(review)
        logger.info(f"[API] Starting context analysis for review {review_id}")

        # Perform analysis (synchronous for MVP - should be async/background task in production)
        try:
            start_time = datetime.now()
            result = agent.analyze_context(
                request.change_description,
                request.project_path,
            )
            duration = (datetime.now() - start_time).total_seconds()

            # Update review with results
            repository.update_review_status(
                review_id,
                "complete",
                result.__dict__,
            )

            # TODO: Calculate actual API cost
            # For now, estimate based on Haiku pricing: ~$0.25 per 1M input tokens
            # Rough estimate: 2000 input tokens = $0.0005

            logger.info(f"[API] Completed analysis for review {review_id} in {duration:.2f}s")

            return AnalyzeResponse(
                review_id=review_id,
                status="complete",
                message=f"Analysis complete in {duration:.2f}s",
            )

        except Exception as e:
            # Update review as failed
            repository.update_review_status(review_id, "failed", {"error": str(e)})
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}",
            ) from e

    except Exception as e:
        logger.error(f"[ERROR] Failed to start context analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{review_id}", response_model=ReviewResultResponse)
async def get_review_result(review_id: int):
    """
    Get context analysis result by review ID.

    Args:
        review_id: Review ID to fetch

    Returns:
        ReviewResultResponse: Analysis result and status
    """
    try:
        repository = ContextReviewRepository()
        review = repository.get_review(review_id)

        if not review:
            raise HTTPException(status_code=404, detail=f"Review {review_id} not found")

        result_dict = None
        if review.result:
            try:
                result_dict = json.loads(review.result)
            except json.JSONDecodeError:
                logger.warning(f"[API] Failed to parse result JSON for review {review_id}")

        return ReviewResultResponse(
            review_id=review.id,
            status=review.status,
            result=result_dict,
            created_at=review.analysis_timestamp.isoformat() if review.analysis_timestamp else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get review {review_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{review_id}/suggestions")
async def get_review_suggestions(review_id: int):
    """
    Get integration suggestions for a review.

    Args:
        review_id: Review ID

    Returns:
        dict: List of suggestions with metadata
    """
    try:
        repository = ContextReviewRepository()
        suggestions = repository.get_suggestions(review_id)

        return {
            "review_id": review_id,
            "count": len(suggestions),
            "suggestions": [
                {
                    "id": s.id,
                    "type": s.suggestion_type,
                    "text": s.suggestion_text,
                    "confidence": s.confidence,
                    "priority": s.priority,
                    "rationale": s.rationale,
                }
                for s in suggestions
            ],
        }

    except Exception as e:
        logger.error(f"[ERROR] Failed to get suggestions for review {review_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/cache-lookup", response_model=CacheLookupResponse)
async def check_cache(request: CacheLookupRequest):
    """
    Check if similar analysis is cached.

    Args:
        request: Cache lookup request

    Returns:
        CacheLookupResponse: Whether cached and result if available
    """
    try:
        agent = ContextReviewAgent()
        cache_key = agent._generate_cache_key(
            request.change_description, request.project_path
        )

        cached_result = agent._check_cache(cache_key)

        if cached_result:
            result_dict = json.loads(cached_result)
            return CacheLookupResponse(
                cached=True,
                result=result_dict,
            )

        return CacheLookupResponse(cached=False)

    except Exception as e:
        logger.error(f"[ERROR] Cache lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def init_context_review_routes():
    """Initialize context review routes and return router."""
    return router
