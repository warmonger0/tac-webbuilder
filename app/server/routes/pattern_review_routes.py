"""
Pattern Review API endpoints for reviewing and approving automation patterns.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.pattern_review_service import PatternReviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patterns", tags=["Pattern Review"])

# Initialize service
pattern_review_service = PatternReviewService()


# Pydantic models for request/response
class PatternReviewResponse(BaseModel):
    """Pattern review item response model."""
    pattern_id: str
    tool_sequence: str
    status: str
    confidence_score: float
    occurrence_count: int
    estimated_savings_usd: float
    impact_score: float
    pattern_context: str | None = None
    example_sessions: list[str] | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    approval_notes: str | None = None
    created_at: str | None = None


class ApproveRequest(BaseModel):
    """Request to approve a pattern."""
    notes: str | None = Field(None, description="Optional approval notes")


class RejectRequest(BaseModel):
    """Request to reject a pattern."""
    reason: str = Field(..., description="Reason for rejection (required)")


class CommentRequest(BaseModel):
    """Request to add a comment to a pattern."""
    comment: str = Field(..., description="Comment text")


class ReviewStatistics(BaseModel):
    """Pattern review statistics."""
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    auto_approved: int = 0
    auto_rejected: int = 0
    total: int = 0


@router.get("/statistics", response_model=ReviewStatistics)
async def get_review_statistics():
    """
    Get pattern review statistics.

    Returns:
        Count of patterns by status
    """
    try:
        stats = pattern_review_service.get_review_statistics()

        total = sum(stats.values())

        return ReviewStatistics(
            pending=stats.get("pending", 0),
            approved=stats.get("approved", 0),
            rejected=stats.get("rejected", 0),
            auto_approved=stats.get("auto-approved", 0),
            auto_rejected=stats.get("auto-rejected", 0),
            total=total
        )
    except Exception as e:
        logger.error(f"Error fetching review statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/pending", response_model=list[PatternReviewResponse])
async def get_pending_patterns(limit: int = 20):
    """
    Get pending patterns for review, ordered by impact score.

    Args:
        limit: Maximum number of patterns to return (default: 20)

    Returns:
        List of pending patterns sorted by impact score (highest first)
    """
    try:
        patterns = pattern_review_service.get_pending_patterns(limit=limit)

        return [
            PatternReviewResponse(
                pattern_id=p.pattern_id,
                tool_sequence=p.tool_sequence,
                status=p.status,
                confidence_score=p.confidence_score,
                occurrence_count=p.occurrence_count,
                estimated_savings_usd=p.estimated_savings_usd,
                impact_score=p.impact_score,
                pattern_context=p.pattern_context,
                example_sessions=p.example_sessions,
                reviewed_by=p.reviewed_by,
                reviewed_at=p.reviewed_at,
                approval_notes=p.approval_notes,
                created_at=p.created_at
            )
            for p in patterns
        ]
    except Exception as e:
        logger.error(f"Error fetching pending patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{pattern_id}", response_model=PatternReviewResponse)
async def get_pattern_details(pattern_id: str):
    """
    Get details for a specific pattern.

    Args:
        pattern_id: Pattern identifier

    Returns:
        Pattern details
    """
    try:
        pattern = pattern_review_service.get_pattern_details(pattern_id)

        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")

        return PatternReviewResponse(
            pattern_id=pattern.pattern_id,
            tool_sequence=pattern.tool_sequence,
            status=pattern.status,
            confidence_score=pattern.confidence_score,
            occurrence_count=pattern.occurrence_count,
            estimated_savings_usd=pattern.estimated_savings_usd,
            impact_score=pattern.impact_score,
            pattern_context=pattern.pattern_context,
            example_sessions=pattern.example_sessions,
            reviewed_by=pattern.reviewed_by,
            reviewed_at=pattern.reviewed_at,
            approval_notes=pattern.approval_notes,
            created_at=pattern.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{pattern_id}/approve", response_model=PatternReviewResponse)
async def approve_pattern(pattern_id: str, request: ApproveRequest):
    """
    Approve a pattern for automation.

    Args:
        pattern_id: Pattern identifier
        request: Approval request with optional notes

    Returns:
        Updated pattern details
    """
    try:
        pattern = pattern_review_service.approve_pattern(
            pattern_id=pattern_id,
            reviewer="system",  # Auto-populated
            notes=request.notes
        )

        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")

        logger.info(f"Pattern {pattern_id} approved by system")

        return PatternReviewResponse(
            pattern_id=pattern.pattern_id,
            tool_sequence=pattern.tool_sequence,
            status=pattern.status,
            confidence_score=pattern.confidence_score,
            occurrence_count=pattern.occurrence_count,
            estimated_savings_usd=pattern.estimated_savings_usd,
            impact_score=pattern.impact_score,
            pattern_context=pattern.pattern_context,
            example_sessions=pattern.example_sessions,
            reviewed_by=pattern.reviewed_by,
            reviewed_at=pattern.reviewed_at,
            approval_notes=pattern.approval_notes,
            created_at=pattern.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{pattern_id}/reject", response_model=PatternReviewResponse)
async def reject_pattern(pattern_id: str, request: RejectRequest):
    """
    Reject a pattern from automation.

    Args:
        pattern_id: Pattern identifier
        request: Rejection request with reason

    Returns:
        Updated pattern details
    """
    try:
        pattern = pattern_review_service.reject_pattern(
            pattern_id=pattern_id,
            reviewer="system",  # Auto-populated
            reason=request.reason
        )

        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")

        logger.info(f"Pattern {pattern_id} rejected by system: {request.reason}")

        return PatternReviewResponse(
            pattern_id=pattern.pattern_id,
            tool_sequence=pattern.tool_sequence,
            status=pattern.status,
            confidence_score=pattern.confidence_score,
            occurrence_count=pattern.occurrence_count,
            estimated_savings_usd=pattern.estimated_savings_usd,
            impact_score=pattern.impact_score,
            pattern_context=pattern.pattern_context,
            example_sessions=pattern.example_sessions,
            reviewed_by=pattern.reviewed_by,
            reviewed_at=pattern.reviewed_at,
            approval_notes=pattern.approval_notes,
            created_at=pattern.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{pattern_id}/comment")
async def add_comment(pattern_id: str, request: CommentRequest):
    """
    Add a comment to a pattern (for further discussion).

    Args:
        pattern_id: Pattern identifier
        request: Comment request with comment text

    Returns:
        Success message
    """
    try:
        # Verify pattern exists
        pattern = pattern_review_service.get_pattern_details(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")

        # Add comment to review history
        from database import get_database_adapter
        adapter = get_database_adapter()

        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = adapter.placeholder()
            cursor.execute(
                f"""
                INSERT INTO pattern_review_history (pattern_id, action, reviewer, notes)
                VALUES ({placeholder}, 'commented', {placeholder}, {placeholder})
            """,
                (pattern_id, "system", request.comment)
            )
            conn.commit()

        logger.info(f"Comment added to pattern {pattern_id} by system")

        return {
            "status": "success",
            "message": f"Comment added to pattern {pattern_id}",
            "pattern_id": pattern_id,
            "reviewer": "system"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment to pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
