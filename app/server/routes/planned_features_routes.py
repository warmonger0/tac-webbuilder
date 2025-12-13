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
- POST   /api/planned-features/{id}/start-automation - Start event-driven phase automation
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

from core.models import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from fastapi import APIRouter, HTTPException, Query
from models.phase_queue_item import PhaseQueueItem
from repositories.phase_queue_repository import PhaseQueueRepository
from services.planned_features_service import PlannedFeaturesService

# Add scripts directory to path for PhaseAnalyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

try:
    from plan_phases import PhaseAnalyzer
except ImportError:
    PhaseAnalyzer = None  # Handle gracefully if script not available

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/planned-features", tags=["planned-features"])


@router.get("/", response_model=list[PlannedFeature])
async def get_planned_features(
    status: str | None = Query(
        None, description="Filter by status: planned, in_progress, completed, cancelled"
    ),
    item_type: str | None = Query(
        None, description="Filter by type: session, feature, bug, enhancement"
    ),
    priority: str | None = Query(
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


@router.post("/{feature_id}/start-automation")
async def start_automation(feature_id: int):
    """
    Start event-driven phase automation for a planned feature.

    This endpoint:
    1. Analyzes the feature to determine optimal phase breakdown
    2. Creates phase queue items with dependencies
    3. Triggers the PhaseCoordinator via event-driven architecture

    Path parameters:
    - feature_id: Feature ID from planned_features table

    Returns:
        Summary of phases created with queue IDs

    Raises:
        404: Feature not found
        400: PhaseAnalyzer not available or feature analysis failed
        500: Phase creation failed
    """
    try:
        # Check if PhaseAnalyzer is available
        if PhaseAnalyzer is None:
            logger.error(
                f"[POST /api/planned-features/{feature_id}/start-automation] PhaseAnalyzer not available"
            )
            raise HTTPException(
                status_code=400,
                detail="PhaseAnalyzer not available. Check scripts/plan_phases.py is accessible."
            )

        # Verify feature exists
        service = PlannedFeaturesService()
        feature = service.get_by_id(feature_id)
        if not feature:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/start-automation] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        # Analyze feature and generate phase breakdown
        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Analyzing feature..."
        )
        analyzer = PhaseAnalyzer()
        phases = analyzer.analyze_feature(feature_id)

        if not phases:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/start-automation] No phases generated"
            )
            raise HTTPException(
                status_code=400,
                detail="Feature analysis did not produce any phases"
            )

        # Create phase queue items
        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Creating {len(phases)} phase queue items..."
        )
        repository = PhaseQueueRepository()
        created_phases = []

        for phase in phases:
            # Generate unique queue_id
            queue_id = f"{feature_id}_{phase.phase_number}_{uuid.uuid4().hex[:8]}"

            # Determine initial status: 'ready' if no dependencies, else 'queued'
            initial_status = 'ready' if not phase.depends_on else 'queued'

            # Convert depends_on from List[Tuple[int, int]] to List[int] (just phase numbers)
            # Note: In the new architecture, we track phase_number dependencies within the same feature
            depends_on_phase_numbers = [dep_phase_num for _, dep_phase_num in phase.depends_on]

            # Create phase data with detailed information
            phase_data = {
                "title": phase.title,
                "description": phase.description,
                "estimated_hours": phase.estimated_hours,
                "files_to_modify": phase.files_to_modify,
                "total_phases": phase.total_phases,
                "prompt_filename": phase.filename,
            }

            # Create PhaseQueueItem
            queue_item = PhaseQueueItem(
                queue_id=queue_id,
                feature_id=feature_id,
                phase_number=phase.phase_number,
                status=initial_status,
                depends_on_phases=depends_on_phase_numbers,
                phase_data=phase_data,
                priority=50,  # Normal priority
            )

            # Insert into database
            created_item = repository.create(queue_item)
            created_phases.append({
                "queue_id": created_item.queue_id,
                "phase_number": phase.phase_number,
                "title": phase.title,
                "status": initial_status,
                "depends_on_phases": depends_on_phase_numbers,
                "estimated_hours": phase.estimated_hours,
            })

            logger.info(
                f"[POST /api/planned-features/{feature_id}/start-automation] Created phase {phase.phase_number}/{phase.total_phases}: {queue_id}"
            )

        # Update feature status to 'in_progress'
        service.update(feature_id, PlannedFeatureUpdate(status='in_progress'))

        # Return summary
        summary = {
            "feature_id": feature_id,
            "feature_title": feature.title,
            "total_phases": len(phases),
            "phases_created": created_phases,
            "ready_phases": sum(1 for p in created_phases if p["status"] == "ready"),
            "queued_phases": sum(1 for p in created_phases if p["status"] == "queued"),
            "message": f"Successfully created {len(phases)} phases. PhaseCoordinator will automatically launch ready phases.",
        }

        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Automation started successfully"
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[POST /api/planned-features/{feature_id}/start-automation] Error: {e}"
        )
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
