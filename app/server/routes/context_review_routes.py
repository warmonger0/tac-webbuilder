"""API routes for context review operations."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.context_review_service import ContextReviewService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["context-review"])

# Service instance (will be set by init function)
_service: Optional[ContextReviewService] = None


def init_context_review_routes(service: Optional[ContextReviewService] = None):
    """
    Initialize context review routes with service dependency.

    Args:
        service: ContextReviewService instance (or creates default)
    """
    global _service
    _service = service or ContextReviewService()
    logger.info("Context review routes initialized")


def get_service() -> ContextReviewService:
    """Get service instance (ensures initialized)."""
    if _service is None:
        raise RuntimeError(
            "Context review routes not initialized. "
            "Call init_context_review_routes() first."
        )
    return _service


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for starting context analysis."""
    change_description: str = Field(
        ...,
        description="Description of the proposed change",
        min_length=10,
        max_length=5000
    )
    project_path: str = Field(
        ...,
        description="Path to the project directory",
        min_length=1
    )
    workflow_id: Optional[str] = Field(
        None,
        description="Optional ADW workflow ID"
    )
    issue_number: Optional[int] = Field(
        None,
        description="Optional GitHub issue number"
    )


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint."""
    review_id: int = Field(..., description="ID of the created review")
    status: str = Field(..., description="Current status (pending|analyzing|complete)")


class ReviewResponse(BaseModel):
    """Response model for review result."""
    review: dict = Field(..., description="Review metadata and result")
    suggestions: list[dict] = Field(..., description="List of suggestions")


class SuggestionsResponse(BaseModel):
    """Response model for suggestions only."""
    suggestions: list[dict] = Field(..., description="List of suggestions")


class CacheLookupRequest(BaseModel):
    """Request model for cache lookup."""
    change_description: str = Field(..., min_length=10, max_length=5000)
    project_path: str = Field(..., min_length=1)


class CacheLookupResponse(BaseModel):
    """Response model for cache lookup."""
    cached: bool = Field(..., description="Whether analysis is cached")
    review_id: Optional[int] = Field(None, description="Review ID if cached")
    result: Optional[dict] = Field(None, description="Cached result if available")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/context-review/analyze", response_model=AnalyzeResponse)
async def analyze_context(request: AnalyzeRequest):
    """
    Start a context analysis for a proposed change.

    This endpoint creates a review record and triggers async analysis using
    Claude API. The analysis identifies relevant files, generates integration
    strategy, assesses risks, and optimizes context for token efficiency.

    Returns immediately with review_id for tracking. Poll GET /{review_id}
    to check completion status.

    **Cost:** ~$0.0006-0.0009 per request (using Claude 3.5 Haiku)
    **Duration:** ~15-30 seconds typical
    **Caching:** Results cached for 7 days to save costs

    Args:
        request: AnalyzeRequest with change_description and project_path

    Returns:
        AnalyzeResponse with review_id and initial status

    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 500: Analysis initialization failed
    """
    try:
        service = get_service()

        review_id = await service.start_analysis(
            change_description=request.change_description,
            project_path=request.project_path,
            workflow_id=request.workflow_id,
            issue_number=request.issue_number
        )

        # Fetch review to get current status
        review_data = await service.get_review_result(review_id)
        if not review_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve created review"
            )

        status = review_data["review"]["status"]

        return AnalyzeResponse(
            review_id=review_id,
            status=status
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/context-review/{review_id}", response_model=ReviewResponse)
async def get_review_result(review_id: int):
    """
    Fetch context review result by ID.

    Returns review metadata and all suggestions. Use this endpoint to check
    if analysis is complete and retrieve results.

    **Status Values:**
    - `pending`: Analysis queued but not started
    - `analyzing`: Claude API call in progress
    - `complete`: Analysis finished, results available
    - `failed`: Analysis encountered an error

    Args:
        review_id: ID of the review to fetch

    Returns:
        ReviewResponse with review data and suggestions

    Raises:
        HTTPException 404: Review not found
        HTTPException 500: Database error
    """
    try:
        service = get_service()

        result = await service.get_review_result(review_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Review {review_id} not found"
            )

        return ReviewResponse(
            review=result["review"],
            suggestions=result["suggestions"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review {review_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch review: {str(e)}"
        )


@router.get("/context-review/{review_id}/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(review_id: int):
    """
    Fetch suggestions for a review.

    Returns only the suggestions list (without full review metadata).
    Useful for lightweight polling.

    **Suggestion Types:**
    - `file-to-modify`: Existing file that needs changes
    - `file-to-create`: New file to be created
    - `reference`: File to reference for patterns/examples
    - `risk`: Potential risk or concern
    - `strategy`: Overall integration approach

    Args:
        review_id: ID of the review

    Returns:
        SuggestionsResponse with suggestions list

    Raises:
        HTTPException 404: Review not found
        HTTPException 500: Database error
    """
    try:
        service = get_service()

        result = await service.get_review_result(review_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Review {review_id} not found"
            )

        return SuggestionsResponse(
            suggestions=result["suggestions"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching suggestions for review {review_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch suggestions: {str(e)}"
        )


@router.post("/context-review/cache-lookup", response_model=CacheLookupResponse)
async def check_cache(request: CacheLookupRequest):
    """
    Check if analysis is cached for a description.

    Use this before calling /analyze to show instant results for repeated
    requests. Cache entries are valid for 7 days.

    **Cache Hit Benefits:**
    - Instant results (<100ms)
    - No API cost ($0.00 vs ~$0.0007)
    - Consistent results

    Args:
        request: CacheLookupRequest with change_description and project_path

    Returns:
        CacheLookupResponse indicating if cached and result data

    Raises:
        HTTPException 400: Invalid request
        HTTPException 500: Cache lookup failed
    """
    try:
        service = get_service()

        cache_result = await service.check_cache_for_description(
            description=request.change_description,
            project_path=request.project_path
        )

        response = CacheLookupResponse(
            cached=cache_result["cached"]
        )

        if cache_result["cached"]:
            response.result = cache_result["result"]

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache lookup failed: {str(e)}"
        )


# Health check endpoint for context review feature
@router.get("/context-review/health")
async def health_check():
    """
    Health check for context review feature.

    Verifies:
    - Service is initialized
    - Anthropic API key is configured
    - Database is accessible

    Returns:
        Health status dictionary
    """
    try:
        service = get_service()

        # Check if agent has API key
        has_api_key = bool(service.agent.api_key)

        # Try a simple database operation
        try:
            service.repository.get_recent_reviews(limit=1)
            db_accessible = True
        except Exception:
            db_accessible = False

        return {
            "status": "healthy" if (has_api_key and db_accessible) else "degraded",
            "service_initialized": True,
            "anthropic_api_key_configured": has_api_key,
            "database_accessible": db_accessible
        }

    except RuntimeError:
        return {
            "status": "unhealthy",
            "service_initialized": False,
            "error": "Service not initialized"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
