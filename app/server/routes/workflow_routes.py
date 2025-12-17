"""
Workflow management and analytics endpoints.
"""
import json
import logging
import traceback
from contextlib import suppress
from typing import Literal

from core.cost_tracker import read_cost_history
from core.data_models import (
    CostPrediction,
    CostResponse,
    ResyncResponse,
    RoutesResponse,
    Workflow,
    WorkflowAnalyticsDetail,
    WorkflowCatalogResponse,
    WorkflowHistoryAnalytics,
    WorkflowHistoryFilters,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowTrends,
)
from core.workflow_history import (
    get_workflow_by_adw_id,
    resync_all_completed_workflows,
    resync_workflow_cost,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Request/Response models for phase updates
class PhaseUpdateRequest(BaseModel):
    """Request model for phase update events."""
    adw_id: str
    current_phase: str
    status: str = "running"  # running, completed, failed
    metadata: dict | None = None  # Optional metadata (cost, errors, etc.)


class PhaseUpdateResponse(BaseModel):
    """Response model for phase update events."""
    success: bool
    message: str
    broadcasted: bool  # Whether WebSocket broadcast succeeded

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["Workflows"])


# Endpoint handlers - extracted for testability and to reduce complexity


async def _get_workflows_handler(workflow_service) -> list[Workflow]:
    """Handler for getting all active workflows."""
    workflows = workflow_service.get_workflows()
    logger.debug(f"[SUCCESS] Retrieved {len(workflows)} active workflows")
    return workflows


async def _get_routes_handler(get_routes_data_func) -> RoutesResponse:
    """Handler for getting all registered routes."""
    route_list = get_routes_data_func()
    response = RoutesResponse(routes=route_list, total=len(route_list))
    logger.debug(f"[SUCCESS] Retrieved {len(route_list)} routes")
    return response


async def _get_workflow_costs_handler(adw_id: str) -> CostResponse:
    """Handler for getting workflow cost data."""
    logger.info(f"[REQUEST] Fetching cost data for ADW ID: {adw_id}")
    try:
        cost_data = read_cost_history(adw_id)
        logger.info(f"[SUCCESS] Retrieved cost data for ADW ID: {adw_id}, total cost: ${cost_data.total_cost:.4f}")
        return CostResponse(cost_data=cost_data)
    except FileNotFoundError as e:
        logger.warning(f"[WARNING] Cost data not found for ADW ID: {adw_id}: {str(e)}")
        return CostResponse(error=f"Cost data not found for workflow {adw_id}")
    except ValueError as e:
        logger.warning(f"[WARNING] Invalid cost data for ADW ID: {adw_id}: {str(e)}")
        return CostResponse(error=f"Invalid cost data for workflow {adw_id}")


async def _get_workflow_history_handler(filters: WorkflowHistoryFilters, get_workflow_history_data_func) -> WorkflowHistoryResponse:
    """Handler for getting workflow history."""
    history_data, _ = get_workflow_history_data_func(filters)
    logger.debug(f"[SUCCESS] Retrieved {len(history_data.workflows)} workflow history items (total: {history_data.total_count})")
    return history_data


async def _resync_workflow_history_handler(adw_id: str | None, force: bool) -> ResyncResponse:
    """Handler for workflow history resync endpoint."""
    logger.info(f"[RESYNC] Starting resync: adw_id={adw_id}, force={force}")

    if adw_id:
        # Resync single workflow
        result = resync_workflow_cost(adw_id, force=force)

        if result["success"]:
            response = ResyncResponse(
                resynced_count=1 if result["cost_updated"] else 0,
                workflows=[{
                    "adw_id": result["adw_id"],
                    "cost_updated": result["cost_updated"]
                }],
                errors=[],
                message=f"Successfully resynced workflow {adw_id}"
            )
            logger.info(f"[RESYNC] Single workflow resync completed: {adw_id}")
            return response
        else:
            # Return error response
            response = ResyncResponse(
                resynced_count=0,
                workflows=[],
                errors=[result["error"]],
                message=f"Failed to resync workflow {adw_id}"
            )
            logger.error(f"[RESYNC] Failed to resync {adw_id}: {result['error']}")
            return response
    else:
        # Resync all completed workflows
        resynced_count, workflows, errors = resync_all_completed_workflows(force=force)

        response = ResyncResponse(
            resynced_count=resynced_count,
            workflows=workflows,
            errors=errors,
            message=f"Bulk resync completed: {resynced_count} workflows updated, {len(errors)} errors"
        )
        logger.info(f"[RESYNC] Bulk resync completed: {resynced_count} updated, {len(errors)} errors")
        return response


async def _get_workflow_analytics_handler(adw_id: str) -> WorkflowAnalyticsDetail:
    """Handler for getting workflow analytics."""
    workflow = get_workflow_by_adw_id(adw_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {adw_id} not found")

    # Parse JSON fields (handle both string and already-parsed data)
    similar_workflow_ids = []
    if workflow.get("similar_workflow_ids"):
        if isinstance(workflow["similar_workflow_ids"], list):
            similar_workflow_ids = workflow["similar_workflow_ids"]
        else:
            with suppress(json.JSONDecodeError, TypeError):
                similar_workflow_ids = json.loads(workflow["similar_workflow_ids"])

    anomaly_flags = []
    if workflow.get("anomaly_flags"):
        if isinstance(workflow["anomaly_flags"], list):
            anomaly_flags = workflow["anomaly_flags"]
        else:
            with suppress(json.JSONDecodeError, TypeError):
                anomaly_flags = json.loads(workflow["anomaly_flags"])

    optimization_recommendations = []
    if workflow.get("optimization_recommendations"):
        if isinstance(workflow["optimization_recommendations"], list):
            optimization_recommendations = workflow["optimization_recommendations"]
        else:
            with suppress(json.JSONDecodeError, TypeError):
                optimization_recommendations = json.loads(workflow["optimization_recommendations"])

    analytics = WorkflowAnalyticsDetail(
        adw_id=adw_id,
        cost_efficiency_score=workflow.get("cost_efficiency_score"),
        performance_score=workflow.get("performance_score"),
        quality_score=workflow.get("quality_score"),
        similar_workflow_ids=similar_workflow_ids,
        anomaly_flags=anomaly_flags,
        optimization_recommendations=optimization_recommendations,
        nl_input_clarity_score=workflow.get("nl_input_clarity_score"),
        nl_input_word_count=workflow.get("nl_input_word_count")
    )

    logger.info(f"[SUCCESS] Retrieved analytics for workflow {adw_id}")
    return analytics


async def _get_workflow_trends_handler(workflow_service, days: int, group_by: str) -> WorkflowTrends:
    """Handler for getting workflow trends."""
    trends = workflow_service.get_workflow_trends(days=days, group_by=group_by)
    logger.info(f"[SUCCESS] Retrieved workflow trends for {days} days grouped by {group_by}")
    return trends


async def _predict_workflow_cost_handler(workflow_service, classification: str, complexity: str, model: str) -> CostPrediction:
    """Handler for predicting workflow cost."""
    prediction = workflow_service.predict_workflow_cost(
        classification=classification,
        complexity=complexity,
        model=model
    )
    logger.info(f"[SUCCESS] Generated cost prediction for {classification}/{complexity}/{model}: ${prediction.predicted_cost:.4f}")
    return prediction


async def _get_workflow_catalog_handler(workflow_service) -> WorkflowCatalogResponse:
    """Handler for getting workflow catalog."""
    catalog = workflow_service.get_workflow_catalog()
    logger.info(f"[SUCCESS] Retrieved {catalog.total} workflow templates")
    return catalog


async def _update_phase_handler(request: PhaseUpdateRequest, websocket_manager) -> PhaseUpdateResponse:
    """Handler for event-driven phase update notifications from orchestrator."""
    logger.info(f"[PHASE_UPDATE] Received phase update: adw_id={request.adw_id}, phase={request.current_phase}, status={request.status}")

    try:
        # Update state file
        from adw_modules.state import ADWState
        from adw_modules.utils import setup_logger

        state_logger = setup_logger(request.adw_id, "phase_update_api")
        state = ADWState.load(request.adw_id, state_logger)

        if state:
            state.update(current_phase=request.current_phase, status=request.status)
            if request.metadata:
                state.update(**request.metadata)
            state.save("phase_update_api")
            logger.info(f"[PHASE_UPDATE] Updated state file for {request.adw_id}")
        else:
            logger.warning(f"[PHASE_UPDATE] State file not found for {request.adw_id}, skipping state update")

        # Immediately broadcast via WebSocket
        broadcasted = False
        if websocket_manager and websocket_manager.active_connections:
            try:
                # Broadcast to ADW monitor listeners
                from core.adw_monitor import aggregate_adw_monitor_data
                monitor_data = aggregate_adw_monitor_data()

                await websocket_manager.broadcast({
                    "type": "adw_monitor_update",
                    "data": monitor_data,
                })
                broadcasted = True
                logger.info(f"[PHASE_UPDATE] Broadcasted update to {len(websocket_manager.active_connections)} WebSocket clients")
            except Exception as e:
                logger.error(f"[PHASE_UPDATE] WebSocket broadcast failed: {e}")
        else:
            logger.debug("[PHASE_UPDATE] No active WebSocket connections, skipping broadcast")

        return PhaseUpdateResponse(
            success=True,
            message=f"Phase update processed for {request.adw_id}",
            broadcasted=broadcasted
        )

    except Exception as e:
        logger.error(f"[PHASE_UPDATE] Error processing phase update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _get_workflows_batch_handler(workflow_ids: list[str]) -> list[WorkflowHistoryItem]:
    """Handler for batch workflows fetch endpoint."""
    # Validate input
    if not workflow_ids:
        return []

    if len(workflow_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 workflows can be fetched at once"
        )

    # Fetch workflows
    workflows = []
    for adw_id in workflow_ids:
        workflow = get_workflow_by_adw_id(adw_id)
        if workflow:
            # Parse JSON fields if they're strings
            if isinstance(workflow.get("similar_workflow_ids"), str):
                with suppress(json.JSONDecodeError, TypeError):
                    workflow["similar_workflow_ids"] = json.loads(workflow["similar_workflow_ids"])

            if not workflow.get("similar_workflow_ids"):
                workflow["similar_workflow_ids"] = []

            workflows.append(WorkflowHistoryItem(**workflow))

    logger.info(f"[BATCH] Fetched {len(workflows)}/{len(workflow_ids)} workflows")
    return workflows


def _register_workflow_basic_queries(router_obj, workflow_service, get_routes_data_func, get_workflow_history_data_func):
    """Register basic workflow query endpoints."""

    @router_obj.get("/workflows", response_model=list[Workflow])
    async def get_workflows() -> list[Workflow]:
        """Get all active ADW workflows (REST endpoint for fallback)"""
        try:
            return await _get_workflows_handler(workflow_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflows: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return []

    @router_obj.get("/routes", response_model=RoutesResponse)
    async def get_routes() -> RoutesResponse:
        """Get all registered FastAPI routes (REST endpoint for fallback)"""
        try:
            return await _get_routes_handler(get_routes_data_func)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve routes: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return RoutesResponse(routes=[], total=0)

    @router_obj.get("/workflows/{adw_id}/costs", response_model=CostResponse)
    async def get_workflow_costs(adw_id: str) -> CostResponse:
        """Get cost data for a specific ADW workflow."""
        try:
            return await _get_workflow_costs_handler(adw_id)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve cost data for ADW ID: {adw_id}: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return CostResponse(error=f"Failed to retrieve cost data: {str(e)}")

    @router_obj.get("/workflow-history", response_model=WorkflowHistoryResponse)
    async def get_workflow_history_endpoint(
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        model: str | None = None,
        template: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: Literal["ASC", "DESC"] = "DESC"
    ) -> WorkflowHistoryResponse:
        """Get workflow history with filtering, sorting, and pagination."""
        try:
            filters = WorkflowHistoryFilters(
                limit=limit,
                offset=offset,
                status=status,
                model=model,
                template=template,
                start_date=start_date,
                end_date=end_date,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order
            )
            return await _get_workflow_history_handler(filters, get_workflow_history_data_func)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow history: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return WorkflowHistoryResponse(
                workflows=[],
                total_count=0,
                analytics=WorkflowHistoryAnalytics()
            )


def _register_workflow_analytics_queries(router_obj, workflow_service):
    """Register workflow analytics query endpoints."""

    @router_obj.get("/workflow-analytics/{adw_id}", response_model=WorkflowAnalyticsDetail)
    async def get_workflow_analytics(adw_id: str) -> WorkflowAnalyticsDetail:
        """Get advanced analytics for a specific workflow."""
        try:
            return await _get_workflow_analytics_handler(adw_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve analytics for {adw_id}: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}") from e

    @router_obj.get("/workflow-trends", response_model=WorkflowTrends)
    async def get_workflow_trends(days: int = 30, group_by: str = "day") -> WorkflowTrends:
        """Get trend data over time."""
        try:
            return await _get_workflow_trends_handler(workflow_service, days, group_by)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow trends: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}") from e

    @router_obj.get("/cost-predictions", response_model=CostPrediction)
    async def predict_workflow_cost(classification: str, complexity: str, model: str) -> CostPrediction:
        """Predict workflow cost."""
        try:
            return await _predict_workflow_cost_handler(workflow_service, classification, complexity, model)
        except Exception as e:
            logger.error(f"[ERROR] Failed to predict workflow cost: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to predict cost: {str(e)}") from e

    @router_obj.get("/workflow-catalog", response_model=WorkflowCatalogResponse)
    async def get_workflow_catalog() -> WorkflowCatalogResponse:
        """Get workflow catalog."""
        try:
            return await _get_workflow_catalog_handler(workflow_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow catalog: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return WorkflowCatalogResponse(workflows=[], total=0)


def _register_workflow_mutation_routes(router_obj, websocket_manager=None):
    """Register POST endpoints for workflow mutations."""

    @router_obj.post("/api/v1/adw-phase-update", response_model=PhaseUpdateResponse)
    async def update_adw_phase(request: PhaseUpdateRequest) -> PhaseUpdateResponse:
        """
        Event-driven phase update endpoint for ADW orchestrator.

        This endpoint receives phase transition events from the orchestrator and:
        1. Updates the state file immediately
        2. Broadcasts via WebSocket to all connected clients
        3. Provides instant frontend updates (0ms vs 500ms polling latency)
        """
        try:
            return await _update_phase_handler(request, websocket_manager)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[PHASE_UPDATE] Error processing phase update: {str(e)}")
            logger.error(f"[PHASE_UPDATE] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to process phase update: {str(e)}") from e

    @router_obj.post("/workflow-history/resync", response_model=ResyncResponse)
    async def resync_workflow_history(
        adw_id: str | None = None,
        force: bool = False
    ) -> ResyncResponse:
        """Manually resync workflow history cost data from source files."""
        try:
            return await _resync_workflow_history_handler(adw_id, force)
        except Exception as e:
            logger.error(f"[RESYNC] Unexpected error: {str(e)}")
            logger.error(f"[RESYNC] Full traceback:\n{traceback.format_exc()}")
            return ResyncResponse(
                resynced_count=0,
                workflows=[],
                errors=[f"Unexpected error: {str(e)}"],
                message="Resync failed"
            )

    @router_obj.post("/workflows/batch", response_model=list[WorkflowHistoryItem])
    async def get_workflows_batch(workflow_ids: list[str]) -> list[WorkflowHistoryItem]:
        """Fetch multiple workflows by ADW IDs in a single request."""
        try:
            return await _get_workflows_batch_handler(workflow_ids)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[BATCH] Error fetching workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e


def init_workflow_routes(workflow_service, get_routes_data_func, get_workflow_history_data_func, websocket_manager=None):
    """Initialize workflow routes with service dependencies."""
    _register_workflow_basic_queries(router, workflow_service, get_routes_data_func, get_workflow_history_data_func)
    _register_workflow_analytics_queries(router, workflow_service)
    _register_workflow_mutation_routes(router, websocket_manager)
