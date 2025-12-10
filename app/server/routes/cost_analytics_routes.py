"""
Cost Analytics API Routes

Provides endpoints for cost attribution analysis and optimization recommendations.

Endpoints:
- GET /api/cost-analytics/by-phase - Cost breakdown by workflow phase
- GET /api/cost-analytics/by-workflow-type - Cost breakdown by workflow type
- GET /api/cost-analytics/trends - Cost trends over time
- GET /api/cost-analytics/optimizations - Optimization opportunities
"""

import logging

from core.models.workflow import (
    OptimizationOpportunityResponse,
    PhaseBreakdownResponse,
    TrendAnalysisResponse,
    WorkflowBreakdownResponse,
)
from fastapi import APIRouter, HTTPException, Query
from services.cost_analytics_service import CostAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
cost_analytics_service = CostAnalyticsService()


@router.get("/api/cost-analytics/by-phase", response_model=PhaseBreakdownResponse)
async def get_phase_breakdown(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get cost breakdown by workflow phase.

    Analyzes workflow costs aggregated by phase (Plan, Validate, Build, Test, etc.)
    and returns cost totals, percentages, and averages.

    Args:
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
        days: Number of days to look back (default: 30)

    Returns:
        PhaseBreakdownResponse with cost analysis by phase
    """
    try:
        logger.info(
            f"[CostAnalyticsRoutes] GET /by-phase - "
            f"start_date={start_date}, end_date={end_date}, days={days}"
        )

        result = cost_analytics_service.analyze_by_phase(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        return PhaseBreakdownResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"[CostAnalyticsRoutes] Error in get_phase_breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze phase costs: {str(e)}")


@router.get("/api/cost-analytics/by-workflow-type", response_model=WorkflowBreakdownResponse)
async def get_workflow_breakdown(
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get cost breakdown by workflow type.

    Analyzes workflow costs aggregated by workflow type/template
    and returns cost totals, counts, and averages per type.

    Args:
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
        days: Number of days to look back (default: 30)

    Returns:
        WorkflowBreakdownResponse with cost analysis by workflow type
    """
    try:
        logger.info(
            f"[CostAnalyticsRoutes] GET /by-workflow-type - "
            f"start_date={start_date}, end_date={end_date}, days={days}"
        )

        result = cost_analytics_service.analyze_by_workflow_type(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        return WorkflowBreakdownResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"[CostAnalyticsRoutes] Error in get_workflow_breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze workflow costs: {str(e)}")


@router.get("/api/cost-analytics/trends", response_model=TrendAnalysisResponse)
async def get_cost_trends(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get cost trends over time.

    Analyzes daily costs over a time period and calculates trend direction,
    moving averages, and percentage changes.

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        TrendAnalysisResponse with time series data and trend analysis
    """
    try:
        logger.info(f"[CostAnalyticsRoutes] GET /trends - days={days}")

        result = cost_analytics_service.analyze_by_time_period(
            period='day',
            days=days
        )

        # Convert result to response model format
        response_dict = result.to_dict()
        return TrendAnalysisResponse(**response_dict)

    except Exception as e:
        logger.error(f"[CostAnalyticsRoutes] Error in get_cost_trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze cost trends: {str(e)}")


@router.get("/api/cost-analytics/optimizations", response_model=list[OptimizationOpportunityResponse])
async def get_optimization_opportunities(
    days: int = Query(30, description="Number of days to analyze (default: 30)")
):
    """
    Get optimization opportunities.

    Identifies cost optimization opportunities by detecting:
    - Phases with abnormally high costs
    - Workflow types with inefficiencies
    - High-cost outlier workflows

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        List of OptimizationOpportunityResponse objects sorted by estimated savings
    """
    try:
        logger.info(f"[CostAnalyticsRoutes] GET /optimizations - days={days}")

        opportunities = cost_analytics_service.get_optimization_opportunities(days=days)

        return [
            OptimizationOpportunityResponse(**opp.to_dict())
            for opp in opportunities
        ]

    except Exception as e:
        logger.error(f"[CostAnalyticsRoutes] Error in get_optimization_opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to identify optimization opportunities: {str(e)}")
