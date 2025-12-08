"""
Planned Features API Routes

RESTful API endpoints for managing planned features, sessions, bugs, and enhancements.

Endpoints:
- GET    /api/planned-features       - Get all planned features (with optional filters)
- GET    /api/planned-features/stats - Get statistics
- GET    /api/planned-features/recent-completions - Get recent completions
- GET    /api/planned-features/{id}  - Get single feature
- POST   /api/planned-features       - Create new feature
- PATCH  /api/planned-features/{id}  - Update feature
- DELETE /api/planned-features/{id}  - Delete feature (soft delete)
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.models import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from services.planned_features_service import PlannedFeaturesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/planned-features", tags=["planned-features"])


@router.get("/", response_model=List[PlannedFeature])
async def get_planned_features(
    status: Optional[str] = Query(
        None, description="Filter by status: planned, in_progress, completed, cancelled"
    ),
    item_type: Optional[str] = Query(
        None, description="Filter by type: session, feature, bug, enhancement"
    ),
    priority: Optional[str] = Query(
        None, description="Filter by priority: high, medium, low"
    ),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
):
    """
    Get all planned features with optional filtering.

    Results are ordered by:
    1. Status (in_progress, planned, completed, cancelled)
    2. Priority (high, medium, low)
    3. Creation date (newest first)

    Query parameters:
    - status: Filter by status
    - item_type: Filter by type
    - priority: Filter by priority
    - limit: Maximum results (1-1000, default: 100)

    Returns:
        List of PlannedFeature objects
    """
    try:
        service = PlannedFeaturesService()
        features = service.get_all(
            status=status, item_type=item_type, priority=priority, limit=limit
        )
        logger.info(
            f"[GET /api/planned-features] Retrieved {len(features)} features"
        )
        return features
    except Exception as e:
        logger.error(f"[GET /api/planned-features] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    Get statistics about planned features.

    Returns:
        Dictionary with:
        - by_status: Count by status
        - by_priority: Count by priority
        - by_type: Count by item type
        - total_estimated_hours: Sum of estimated hours
        - total_actual_hours: Sum of actual hours
        - completion_rate: Percentage completed
    """
    try:
        service = PlannedFeaturesService()
        stats = service.get_statistics()
        logger.info("[GET /api/planned-features/stats] Generated statistics")
        return stats
    except Exception as e:
        logger.error(f"[GET /api/planned-features/stats] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-completions")
async def get_recent_completions(
    days: int = Query(
        30, description="Number of days to look back", ge=1, le=365
    )
):
    """
    Get recently completed features.

    Query parameters:
    - days: Number of days to look back (1-365, default: 30)

    Returns:
        List of completed PlannedFeature objects ordered by completion date
    """
    try:
        service = PlannedFeaturesService()
        features = service.get_recent_completions(days=days)
        logger.info(
            f"[GET /api/planned-features/recent-completions] Found {len(features)} completions in last {days} days"
        )
        return features
    except Exception as e:
        logger.error(
            f"[GET /api/planned-features/recent-completions] Error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{feature_id}", response_model=PlannedFeature)
async def get_planned_feature(feature_id: int):
    """
    Get single planned feature by ID.

    Path parameters:
    - feature_id: Feature ID

    Returns:
        PlannedFeature object

    Raises:
        404: Feature not found
    """
    try:
        service = PlannedFeaturesService()
        feature = service.get_by_id(feature_id)

        if not feature:
            logger.warning(
                f"[GET /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        logger.info(f"[GET /api/planned-features/{feature_id}] Retrieved feature")
        return feature
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PlannedFeature, status_code=201)
async def create_planned_feature(feature_data: PlannedFeatureCreate):
    """
    Create new planned feature.

    Request body:
    - item_type: Type (session, feature, bug, enhancement)
    - title: Feature title (required)
    - description: Detailed description (optional)
    - status: Initial status (default: 'planned')
    - priority: Priority (high, medium, low)
    - estimated_hours: Estimated hours
    - session_number: Session number (for sessions)
    - github_issue_number: Related GitHub issue
    - parent_id: Parent feature ID (for hierarchical features)
    - tags: List of tags

    Returns:
        Created PlannedFeature object with assigned ID

    Raises:
        400: Invalid feature data
    """
    try:
        service = PlannedFeaturesService()
        feature = service.create(feature_data)
        logger.info(
            f"[POST /api/planned-features] Created feature {feature.id}: {feature.title}"
        )
        return feature
    except ValueError as e:
        logger.error(f"[POST /api/planned-features] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[POST /api/planned-features] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{feature_id}", response_model=PlannedFeature)
async def update_planned_feature(feature_id: int, update_data: PlannedFeatureUpdate):
    """
    Update existing planned feature.

    Path parameters:
    - feature_id: Feature ID

    Request body (all optional):
    - title: New title
    - description: New description
    - status: New status (auto-updates timestamps)
    - priority: New priority
    - estimated_hours: New estimated hours
    - actual_hours: Actual hours spent
    - github_issue_number: GitHub issue number
    - tags: List of tags
    - completion_notes: Completion notes

    Auto-timestamp behavior:
    - started_at: Set when status → 'in_progress'
    - completed_at: Set when status → 'completed' or 'cancelled'

    Returns:
        Updated PlannedFeature object

    Raises:
        404: Feature not found
        400: Invalid update data
    """
    try:
        service = PlannedFeaturesService()

        # Verify feature exists
        existing = service.get_by_id(feature_id)
        if not existing:
            logger.warning(
                f"[PATCH /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        feature = service.update(feature_id, update_data)
        logger.info(
            f"[PATCH /api/planned-features/{feature_id}] Updated feature"
        )
        return feature
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            f"[PATCH /api/planned-features/{feature_id}] Validation error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PATCH /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{feature_id}", status_code=204)
async def delete_planned_feature(feature_id: int):
    """
    Delete planned feature (soft delete via status='cancelled').

    Path parameters:
    - feature_id: Feature ID

    Returns:
        204 No Content

    Raises:
        404: Feature not found
    """
    try:
        service = PlannedFeaturesService()

        # Verify feature exists
        existing = service.get_by_id(feature_id)
        if not existing:
            logger.warning(
                f"[DELETE /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        service.delete(feature_id)
        logger.info(
            f"[DELETE /api/planned-features/{feature_id}] Soft deleted feature"
        )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
