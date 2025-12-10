"""
Error Analytics API Routes

Provides endpoints for error pattern analysis and debugging recommendations.

Endpoints:
- GET /api/error-analytics/summary - Error summary statistics
- GET /api/error-analytics/by-phase - Error breakdown by workflow phase
- GET /api/error-analytics/patterns - Detected error patterns
- GET /api/error-analytics/trends - Error trends over time
- GET /api/error-analytics/recommendations - Debugging recommendations
"""

import logging

from core.models.workflow import (
    DebugRecommendation,
    ErrorPattern,
    ErrorSummary,
    ErrorTrends,
    PhaseErrorBreakdown,
)
from fastapi import APIRouter, HTTPException, Query
from services.error_analytics_service import ErrorAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
error_analytics_service = ErrorAnalyticsService()


@router.get("/api/error-analytics/summary", response_model=ErrorSummary)
async def get_error_summary(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get summary statistics for workflow errors.

    Analyzes failed workflows and provides overall error statistics including
    failure rates, top error patterns, and most problematic phases.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        ErrorSummary with overall error statistics
    """
    try:
        logger.info(f"[ErrorAnalyticsRoutes] GET /summary - days={days}")

        result = error_analytics_service.get_error_summary(days=days)

        return ErrorSummary(**result)

    except Exception as e:
        logger.error(f"[ErrorAnalyticsRoutes] Error in get_error_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate error summary: {str(e)}")


@router.get("/api/error-analytics/by-phase", response_model=PhaseErrorBreakdown)
async def get_phase_errors(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get error breakdown by workflow phase.

    Analyzes errors by workflow phase (Plan, Build, Test, etc.) and calculates
    failure rates and error counts per phase.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        PhaseErrorBreakdown with error analysis by phase
    """
    try:
        logger.info(f"[ErrorAnalyticsRoutes] GET /by-phase - days={days}")

        result = error_analytics_service.analyze_by_phase(days=days)

        return PhaseErrorBreakdown(**result)

    except Exception as e:
        logger.error(f"[ErrorAnalyticsRoutes] Error in get_phase_errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze phase errors: {str(e)}")


@router.get("/api/error-analytics/patterns", response_model=list[ErrorPattern])
async def get_error_patterns(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Detect and return recurring error patterns.

    Analyzes error messages to identify common patterns (import errors, connection
    errors, timeouts, etc.) and provides debugging recommendations.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        List of ErrorPattern objects with pattern analysis
    """
    try:
        logger.info(f"[ErrorAnalyticsRoutes] GET /patterns - days={days}")

        patterns = error_analytics_service.find_error_patterns(days=days)

        return [ErrorPattern(**p) for p in patterns]

    except Exception as e:
        logger.error(f"[ErrorAnalyticsRoutes] Error in get_error_patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to detect error patterns: {str(e)}")


@router.get("/api/error-analytics/trends", response_model=ErrorTrends)
async def get_failure_trends(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get error trends over time.

    Analyzes daily error rates and identifies trends (increasing, decreasing, stable)
    in failure rates over the specified time period.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        ErrorTrends with daily error data and trend analysis
    """
    try:
        logger.info(f"[ErrorAnalyticsRoutes] GET /trends - days={days}")

        result = error_analytics_service.get_failure_trends(days=days)

        return ErrorTrends(**result)

    except Exception as e:
        logger.error(f"[ErrorAnalyticsRoutes] Error in get_failure_trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze error trends: {str(e)}")


@router.get("/api/error-analytics/recommendations", response_model=list[DebugRecommendation])
async def get_debugging_recommendations(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get debugging recommendations based on error analysis.

    Analyzes error patterns and generates actionable debugging recommendations
    prioritized by severity and frequency.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        List of DebugRecommendation objects with actionable suggestions
    """
    try:
        logger.info(f"[ErrorAnalyticsRoutes] GET /recommendations - days={days}")

        recommendations = error_analytics_service.get_debugging_recommendations(days=days)

        return [DebugRecommendation(**r) for r in recommendations]

    except Exception as e:
        logger.error(f"[ErrorAnalyticsRoutes] Error in get_debugging_recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
