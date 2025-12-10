#!/usr/bin/env python3
"""
ROI Tracking Routes

API endpoints for pattern execution ROI tracking and analysis.

Endpoints:
- POST /api/roi-tracking/executions - Record pattern execution
- GET /api/roi-tracking/pattern/{pattern_id} - Get pattern ROI summary
- GET /api/roi-tracking/summary - Get all ROI summaries
- GET /api/roi-tracking/report/{pattern_id} - Get comprehensive ROI report
- GET /api/roi-tracking/top-performers - Get top performing patterns
- GET /api/roi-tracking/underperformers - Get underperforming patterns
"""

import logging

from core.models.workflow import (
    PatternExecution,
    PatternROISummary,
    ROIReport,
)
from fastapi import APIRouter, HTTPException, Query
from services.roi_tracking_service import ROITrackingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/roi-tracking/executions", status_code=201)
async def record_execution(execution: PatternExecution) -> dict:
    """
    Record a pattern execution instance.

    Args:
        execution: PatternExecution with metrics

    Returns:
        Success message with execution ID
    """
    try:
        service = ROITrackingService()
        execution_id = service.record_execution(execution)

        logger.info(
            f"[API] Recorded pattern execution {execution_id} for pattern {execution.pattern_id}"
        )

        return {
            "message": "Execution recorded successfully",
            "execution_id": execution_id,
            "pattern_id": execution.pattern_id,
        }

    except Exception as e:
        logger.error(f"[API] Error recording execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record execution: {str(e)}")


@router.get("/api/roi-tracking/pattern/{pattern_id}")
async def get_pattern_roi(pattern_id: str) -> PatternROISummary:
    """
    Get ROI summary for a specific pattern.

    Args:
        pattern_id: Pattern identifier

    Returns:
        PatternROISummary with aggregated metrics
    """
    try:
        service = ROITrackingService()
        summary = service.get_pattern_roi(pattern_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No ROI data found for pattern {pattern_id}"
            )

        logger.info(f"[API] Retrieved ROI summary for pattern {pattern_id}")
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error retrieving pattern ROI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pattern ROI: {str(e)}")


@router.get("/api/roi-tracking/summary")
async def get_all_roi_summaries() -> list[PatternROISummary]:
    """
    Get ROI summaries for all patterns.

    Returns:
        List of PatternROISummary objects ordered by cost savings
    """
    try:
        service = ROITrackingService()
        summaries = service.get_all_roi_summaries()

        logger.info(f"[API] Retrieved {len(summaries)} ROI summaries")
        return summaries

    except Exception as e:
        logger.error(f"[API] Error retrieving ROI summaries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ROI summaries: {str(e)}")


@router.get("/api/roi-tracking/report/{pattern_id}")
async def get_roi_report(pattern_id: str) -> ROIReport:
    """
    Generate comprehensive ROI report for a pattern.

    Args:
        pattern_id: Pattern identifier

    Returns:
        ROIReport with executions, summary, and recommendations
    """
    try:
        service = ROITrackingService()
        report = service.get_roi_report(pattern_id)

        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"No ROI report available for pattern {pattern_id}"
            )

        logger.info(
            f"[API] Generated ROI report for pattern {pattern_id}: "
            f"{report.effectiveness_rating} rating"
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error generating ROI report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate ROI report: {str(e)}")


@router.get("/api/roi-tracking/top-performers")
async def get_top_performers(limit: int = Query(10, ge=1, le=50)) -> list[PatternROISummary]:
    """
    Get top performing patterns by ROI.

    Args:
        limit: Maximum number of patterns to return (default: 10, max: 50)

    Returns:
        List of PatternROISummary objects ordered by ROI
    """
    try:
        service = ROITrackingService()
        performers = service.get_top_performers(limit=limit)

        logger.info(f"[API] Retrieved {len(performers)} top performers (limit: {limit})")
        return performers

    except Exception as e:
        logger.error(f"[API] Error retrieving top performers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top performers: {str(e)}")


@router.get("/api/roi-tracking/underperformers")
async def get_underperformers(limit: int = Query(10, ge=1, le=50)) -> list[PatternROISummary]:
    """
    Get underperforming patterns by success rate and ROI.

    Args:
        limit: Maximum number of patterns to return (default: 10, max: 50)

    Returns:
        List of PatternROISummary objects ordered by performance (worst first)
    """
    try:
        service = ROITrackingService()
        underperformers = service.get_underperformers(limit=limit)

        logger.info(f"[API] Retrieved {len(underperformers)} underperformers (limit: {limit})")
        return underperformers

    except Exception as e:
        logger.error(f"[API] Error retrieving underperformers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve underperformers: {str(e)}"
        )


@router.get("/api/roi-tracking/effectiveness/{pattern_id}")
async def get_effectiveness(pattern_id: str) -> dict:
    """
    Calculate effectiveness rating for a pattern.

    Args:
        pattern_id: Pattern identifier

    Returns:
        Dict with effectiveness rating and summary metrics
    """
    try:
        service = ROITrackingService()
        summary = service.get_pattern_roi(pattern_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No ROI data found for pattern {pattern_id}"
            )

        effectiveness = service.calculate_effectiveness(pattern_id)
        recommendation = service._generate_recommendation(effectiveness, summary)

        logger.info(
            f"[API] Calculated effectiveness for pattern {pattern_id}: {effectiveness}"
        )

        return {
            "pattern_id": pattern_id,
            "effectiveness_rating": effectiveness,
            "success_rate": summary.success_rate,
            "roi_percentage": summary.roi_percentage,
            "total_executions": summary.total_executions,
            "recommendation": recommendation,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error calculating effectiveness: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate effectiveness: {str(e)}"
        )
