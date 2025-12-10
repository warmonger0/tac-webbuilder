"""
Latency Analytics API Routes

Provides endpoints for workflow performance analysis and bottleneck identification.

Endpoints:
- GET /api/latency-analytics/summary - Overall latency summary
- GET /api/latency-analytics/by-phase - Latency breakdown by workflow phase
- GET /api/latency-analytics/bottlenecks - Performance bottleneck detection
- GET /api/latency-analytics/trends - Latency trends over time
- GET /api/latency-analytics/recommendations - Optimization recommendations
"""

import logging

from core.models.workflow import (
    BottleneckResponse,
    LatencySummaryResponse,
    OptimizationRecommendationResponse,
    PhaseLatencyBreakdownResponse,
    TrendDataResponse,
)
from fastapi import APIRouter, HTTPException, Query
from services.latency_analytics_service import LatencyAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
latency_analytics_service = LatencyAnalyticsService()


@router.get("/api/latency-analytics/summary", response_model=LatencySummaryResponse)
async def get_latency_summary(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get overall latency summary statistics.

    Analyzes workflow execution times and returns percentiles (p50, p95, p99),
    average duration, and identifies the slowest phase.

    Args:
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
        days: Number of days to look back (default: 30)

    Returns:
        LatencySummaryResponse with overall latency statistics
    """
    try:
        logger.info(
            f"[LatencyAnalyticsRoutes] GET /summary - "
            f"start_date={start_date}, end_date={end_date}, days={days}"
        )

        result = latency_analytics_service.get_latency_summary(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        return LatencySummaryResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"[LatencyAnalyticsRoutes] Error in get_latency_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get latency summary: {str(e)}")


@router.get("/api/latency-analytics/by-phase", response_model=PhaseLatencyBreakdownResponse)
async def get_phase_latencies(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get latency breakdown by workflow phase.

    Analyzes execution times for each phase (Plan, Build, Test, etc.) and
    returns percentiles (p50, p95, p99), averages, min, max, and standard deviation.

    Args:
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
        days: Number of days to look back (default: 30)

    Returns:
        PhaseLatencyBreakdownResponse with latency statistics per phase
    """
    try:
        logger.info(
            f"[LatencyAnalyticsRoutes] GET /by-phase - "
            f"start_date={start_date}, end_date={end_date}, days={days}"
        )

        result = latency_analytics_service.analyze_by_phase(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        return PhaseLatencyBreakdownResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"[LatencyAnalyticsRoutes] Error in get_phase_latencies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze phase latencies: {str(e)}")


@router.get("/api/latency-analytics/bottlenecks", response_model=list[BottleneckResponse])
async def get_bottlenecks(
    threshold: int = Query(300, description="Bottleneck threshold in seconds (default: 300)"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Identify performance bottlenecks.

    Detects phases that consistently exceed the latency threshold and provides
    recommendations for optimization.

    Args:
        threshold: Threshold in seconds for bottleneck detection (default: 300s = 5min)
        days: Number of days to analyze (default: 30)

    Returns:
        List of BottleneckResponse objects, sorted by severity (p95 latency)
    """
    try:
        logger.info(
            f"[LatencyAnalyticsRoutes] GET /bottlenecks - "
            f"threshold={threshold}, days={days}"
        )

        bottlenecks = latency_analytics_service.find_bottlenecks(
            threshold_seconds=threshold,
            days=days
        )

        return [BottleneckResponse(**b.to_dict()) for b in bottlenecks]

    except Exception as e:
        logger.error(f"[LatencyAnalyticsRoutes] Error in get_bottlenecks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find bottlenecks: {str(e)}")


@router.get("/api/latency-analytics/trends", response_model=TrendDataResponse)
async def get_latency_trends(
    period: str = Query('day', description="Time period (day, week) - currently only 'day' supported"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Analyze latency trends over time.

    Provides daily latency data, 7-day moving average, trend direction
    (increasing/decreasing/stable), and percentage change.

    Args:
        period: Time period for grouping ('day', 'week') - currently only 'day' supported
        days: Number of days to look back (default: 30)

    Returns:
        TrendDataResponse with time series latency data and trend analysis
    """
    try:
        logger.info(
            f"[LatencyAnalyticsRoutes] GET /trends - "
            f"period={period}, days={days}"
        )

        result = latency_analytics_service.get_latency_trends(
            period=period,
            days=days
        )

        return TrendDataResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"[LatencyAnalyticsRoutes] Error in get_latency_trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze latency trends: {str(e)}")


@router.get("/api/latency-analytics/recommendations", response_model=list[OptimizationRecommendationResponse])
async def get_optimization_recommendations(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get optimization recommendations for improving workflow latency.

    Analyzes latency patterns and provides actionable recommendations
    for reducing execution times in the slowest phases.

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        List of OptimizationRecommendationResponse objects with specific actions
    """
    try:
        logger.info(
            f"[LatencyAnalyticsRoutes] GET /recommendations - days={days}"
        )

        recommendations = latency_analytics_service.get_optimization_recommendations(
            days=days
        )

        return [OptimizationRecommendationResponse(**r.to_dict()) for r in recommendations]

    except Exception as e:
        logger.error(f"[LatencyAnalyticsRoutes] Error in get_optimization_recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
