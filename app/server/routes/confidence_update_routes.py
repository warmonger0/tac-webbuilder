#!/usr/bin/env python3
"""
Confidence Update Routes

API endpoints for automatic confidence score updates based on ROI performance.

Endpoints:
- POST /api/confidence/update/{pattern_id} - Update single pattern confidence
- POST /api/confidence/update-all - Update all patterns with ROI data
- GET /api/confidence/history/{pattern_id} - Get confidence change history
- GET /api/confidence/recommendations - Get status change recommendations
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from services.confidence_update_service import ConfidenceUpdateService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/confidence/update/{pattern_id}")
async def update_pattern_confidence(
    pattern_id: str,
    dry_run: bool = Query(False, description="Calculate but don't persist changes")
) -> dict:
    """
    Update confidence score for a single pattern based on ROI data.

    Args:
        pattern_id: Pattern identifier to update
        dry_run: If True, calculate but don't persist changes

    Returns:
        Confidence update details with old and new scores
    """
    try:
        service = ConfidenceUpdateService()
        update = service.update_pattern_confidence(pattern_id, dry_run=dry_run)

        if not update:
            raise HTTPException(
                status_code=404,
                detail=f"No ROI data found for pattern {pattern_id} or pattern does not exist"
            )

        logger.info(
            f"[API] Updated confidence for pattern {pattern_id}: "
            f"{update.old_confidence:.3f} -> {update.new_confidence:.3f}"
        )

        return {
            "message": "Confidence updated successfully" if not dry_run else "Dry run completed",
            "pattern_id": pattern_id,
            "old_confidence": update.old_confidence,
            "new_confidence": update.new_confidence,
            "change": update.new_confidence - update.old_confidence,
            "adjustment_reason": update.adjustment_reason,
            "roi_data": update.roi_data,
            "dry_run": dry_run
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error updating confidence: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update confidence: {str(e)}")


@router.post("/api/confidence/update-all")
async def update_all_patterns(
    dry_run: bool = Query(False, description="Calculate but don't persist changes")
) -> dict:
    """
    Update confidence scores for all patterns with ROI data.

    Args:
        dry_run: If True, calculate but don't persist changes

    Returns:
        Summary of confidence updates across all patterns
    """
    try:
        service = ConfidenceUpdateService()
        changes = service.update_all_patterns(dry_run=dry_run)

        # Calculate statistics
        total_patterns = len(changes)
        if total_patterns > 0:
            increased = sum(1 for c in changes.values() if c > 0)
            decreased = sum(1 for c in changes.values() if c < 0)
            unchanged = sum(1 for c in changes.values() if c == 0)
            avg_change = sum(changes.values()) / total_patterns
            max_increase = max(changes.values()) if changes else 0
            max_decrease = min(changes.values()) if changes else 0
        else:
            increased = decreased = unchanged = 0
            avg_change = max_increase = max_decrease = 0.0

        logger.info(
            f"[API] Updated confidence for {total_patterns} patterns: "
            f"+{increased}, -{decreased}, ={unchanged}, avg change: {avg_change:+.3f}"
        )

        return {
            "message": "Confidence updates completed" if not dry_run else "Dry run completed",
            "total_patterns": total_patterns,
            "increased": increased,
            "decreased": decreased,
            "unchanged": unchanged,
            "average_change": avg_change,
            "max_increase": max_increase,
            "max_decrease": max_decrease,
            "changes": changes,
            "dry_run": dry_run
        }

    except Exception as e:
        logger.error(f"[API] Error updating all patterns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update patterns: {str(e)}")


@router.get("/api/confidence/history/{pattern_id}")
async def get_confidence_history(
    pattern_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return")
) -> list[dict]:
    """
    Get confidence change history for a pattern.

    Args:
        pattern_id: Pattern identifier
        limit: Maximum number of records to return (1-500)

    Returns:
        List of confidence updates ordered by date (newest first)
    """
    try:
        service = ConfidenceUpdateService()
        history = service.get_confidence_history(pattern_id, limit=limit)

        logger.info(
            f"[API] Retrieved {len(history)} confidence history records for pattern {pattern_id}"
        )

        # Convert to dict for JSON response
        return [
            {
                "id": update.id,
                "pattern_id": update.pattern_id,
                "old_confidence": update.old_confidence,
                "new_confidence": update.new_confidence,
                "change": update.new_confidence - update.old_confidence,
                "adjustment_reason": update.adjustment_reason,
                "roi_data": update.roi_data,
                "updated_by": update.updated_by,
                "updated_at": update.updated_at
            }
            for update in history
        ]

    except Exception as e:
        logger.error(f"[API] Error fetching confidence history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/api/confidence/recommendations")
async def get_status_change_recommendations() -> dict:
    """
    Get recommendations for pattern status changes based on performance.

    Returns:
        Categorized recommendations with severity levels
    """
    try:
        service = ConfidenceUpdateService()
        recommendations = service.recommend_status_changes()

        # Group by severity
        high_severity = [r for r in recommendations if r.severity == 'high']
        medium_severity = [r for r in recommendations if r.severity == 'medium']
        low_severity = [r for r in recommendations if r.severity == 'low']

        logger.info(
            f"[API] Generated {len(recommendations)} recommendations: "
            f"{len(high_severity)} high, {len(medium_severity)} medium, {len(low_severity)} low"
        )

        # Convert to dict for JSON response
        return {
            "total_recommendations": len(recommendations),
            "high_severity": [
                {
                    "pattern_id": r.pattern_id,
                    "current_status": r.current_status,
                    "recommended_status": r.recommended_status,
                    "reason": r.reason,
                    "confidence_score": r.confidence_score,
                    "roi_percentage": r.roi_percentage
                }
                for r in high_severity
            ],
            "medium_severity": [
                {
                    "pattern_id": r.pattern_id,
                    "current_status": r.current_status,
                    "recommended_status": r.recommended_status,
                    "reason": r.reason,
                    "confidence_score": r.confidence_score,
                    "roi_percentage": r.roi_percentage
                }
                for r in medium_severity
            ],
            "low_severity": [
                {
                    "pattern_id": r.pattern_id,
                    "current_status": r.current_status,
                    "recommended_status": r.recommended_status,
                    "reason": r.reason,
                    "confidence_score": r.confidence_score,
                    "roi_percentage": r.roi_percentage
                }
                for r in low_severity
            ]
        }

    except Exception as e:
        logger.error(f"[API] Error generating recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
