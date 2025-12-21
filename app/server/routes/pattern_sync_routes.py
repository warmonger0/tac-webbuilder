"""
Pattern Sync API endpoints for synchronizing patterns to review queue.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.pattern_sync_service import PatternSyncService, SyncFilter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patterns/sync", tags=["Pattern Sync"])

# Initialize service
pattern_sync_service = PatternSyncService()


# Pydantic models for request/response
class SyncFilterRequest(BaseModel):
    """Filter criteria for pattern sync."""

    min_confidence: float = Field(
        0.0, ge=0.0, le=100.0, description="Minimum confidence score (0-100)"
    )
    min_occurrences: int = Field(
        1, ge=1, description="Minimum number of occurrences"
    )
    min_savings: float = Field(0.0, ge=0.0, description="Minimum monthly savings (USD)")
    max_patterns: int = Field(
        50, ge=1, le=200, description="Maximum patterns to sync"
    )
    exclude_types: list[str] | None = Field(
        None, description="Pattern types to exclude"
    )
    only_types: list[str] | None = Field(None, description="Only these pattern types")


class SyncResultResponse(BaseModel):
    """Result of a pattern sync operation."""

    total_candidates: int
    synced_count: int
    skipped_count: int
    error_count: int
    synced_pattern_ids: list[str]
    errors: list[str]
    sync_duration_ms: float


class SyncStatistics(BaseModel):
    """Statistics about sync status."""

    patterns_in_source: int
    patterns_in_review: int
    pending_sync: int
    sync_percentage: float


@router.get("/statistics", response_model=SyncStatistics)
async def get_sync_statistics():
    """
    Get statistics about pattern sync status.

    Returns:
        Current sync statistics including:
        - patterns_in_source: Patterns in operation_patterns
        - patterns_in_review: Patterns in pattern_approvals
        - pending_sync: Patterns not yet synced
        - sync_percentage: % of patterns synced
    """
    try:
        stats = pattern_sync_service.get_sync_statistics()
        return SyncStatistics(**stats)
    except Exception as e:
        logger.error(f"Error fetching sync statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=SyncResultResponse)
async def run_pattern_sync(
    filter_request: SyncFilterRequest | None = None, dry_run: bool = False
):
    """
    Run pattern sync with custom filters.

    Args:
        filter_request: Optional filter criteria (uses smart defaults if None)
        dry_run: If True, report what would be synced without syncing

    Returns:
        SyncResult with statistics and list of synced patterns

    Example:
        POST /patterns/sync/run?dry_run=true
        {
            "min_confidence": 70.0,
            "min_savings": 1000.0,
            "max_patterns": 20
        }
    """
    try:
        # Convert request to SyncFilter
        sync_filter = None
        if filter_request:
            sync_filter = SyncFilter(
                min_confidence=filter_request.min_confidence,
                min_occurrences=filter_request.min_occurrences,
                min_savings=filter_request.min_savings,
                max_patterns=filter_request.max_patterns,
                exclude_types=filter_request.exclude_types,
                only_types=filter_request.only_types,
            )

        result = pattern_sync_service.sync_patterns(
            sync_filter=sync_filter, dry_run=dry_run
        )

        return SyncResultResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error running pattern sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/high-priority", response_model=SyncResultResponse)
async def sync_high_priority_patterns(dry_run: bool = False):
    """
    Sync only high-priority patterns (high confidence + high savings).

    This is the recommended sync strategy for automated background jobs.

    Criteria:
    - Confidence >= 70%
    - Monthly savings >= $1000
    - Occurrences >= 5
    - Limit: Top 20 patterns

    Args:
        dry_run: If True, report what would be synced without syncing

    Returns:
        SyncResult with sync details
    """
    try:
        result = pattern_sync_service.sync_high_priority_patterns()
        return SyncResultResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error syncing high-priority patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/all", response_model=SyncResultResponse)
async def sync_all_patterns(dry_run: bool = False):
    """
    Sync all detected patterns regardless of confidence/savings.

    ⚠️ WARNING: This may create many low-value review items.
    Recommended to use /high-priority instead.

    Args:
        dry_run: If True, report what would be synced without syncing

    Returns:
        SyncResult with sync details
    """
    try:
        result = pattern_sync_service.sync_all_patterns()
        return SyncResultResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error syncing all patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
