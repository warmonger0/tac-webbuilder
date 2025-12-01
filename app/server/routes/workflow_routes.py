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

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["Workflows"])


def init_workflow_routes(workflow_service, get_routes_data_func, get_workflow_history_data_func):
    """
    Initialize workflow routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.get("/workflows", response_model=list[Workflow])
    async def get_workflows() -> list[Workflow]:
        """Get all active ADW workflows (REST endpoint for fallback)"""
        try:
            workflows = workflow_service.get_workflows()
            logger.debug(f"[SUCCESS] Retrieved {len(workflows)} active workflows")
            return workflows
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflows: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return []

    @router.get("/routes", response_model=RoutesResponse)
    async def get_routes() -> RoutesResponse:
        """Get all registered FastAPI routes (REST endpoint for fallback)"""
        try:
            route_list = get_routes_data_func()
            response = RoutesResponse(routes=route_list, total=len(route_list))
            logger.debug(f"[SUCCESS] Retrieved {len(route_list)} routes")
            return response
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve routes: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            # Return empty routes list on error
            return RoutesResponse(routes=[], total=0)

    @router.get("/workflows/{adw_id}/costs", response_model=CostResponse)
    async def get_workflow_costs(adw_id: str) -> CostResponse:
        """
        Get cost data for a specific ADW workflow.

        Returns cost breakdown by phase, cache efficiency metrics,
        and token usage statistics.
        """
        try:
            logger.info(f"[REQUEST] Fetching cost data for ADW ID: {adw_id}")
            cost_data = read_cost_history(adw_id)
            logger.info(f"[SUCCESS] Retrieved cost data for ADW ID: {adw_id}, total cost: ${cost_data.total_cost:.4f}")
            return CostResponse(cost_data=cost_data)
        except FileNotFoundError as e:
            logger.warning(f"[WARNING] Cost data not found for ADW ID: {adw_id}: {str(e)}")
            return CostResponse(error=f"Cost data not found for workflow {adw_id}")
        except ValueError as e:
            logger.warning(f"[WARNING] Invalid cost data for ADW ID: {adw_id}: {str(e)}")
            return CostResponse(error=f"Invalid cost data for workflow {adw_id}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve cost data for ADW ID: {adw_id}: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return CostResponse(error=f"Failed to retrieve cost data: {str(e)}")

    @router.get("/workflow-history", response_model=WorkflowHistoryResponse)
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
        """Get workflow history with filtering, sorting, and pagination (REST endpoint for fallback)"""
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
            history_data, _ = get_workflow_history_data_func(filters)
            logger.debug(f"[SUCCESS] Retrieved {len(history_data.workflows)} workflow history items (total: {history_data.total_count})")
            return history_data
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow history: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            # Return empty response on error
            return WorkflowHistoryResponse(
                workflows=[],
                total_count=0,
                analytics=WorkflowHistoryAnalytics()
            )

    @router.post("/workflow-history/resync", response_model=ResyncResponse)
    async def resync_workflow_history(
        adw_id: str | None = None,
        force: bool = False
    ) -> ResyncResponse:
        """
        Manually resync workflow history cost data from source files.

        Query Parameters:
        - adw_id: Optional ADW ID to resync single workflow
        - force: If true, clears existing cost data before resync

        Returns:
        - resynced_count: Number of workflows resynced
        - workflows: List of resynced workflow summaries
        - errors: List of error messages encountered
        """
        try:
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

        except Exception as e:
            logger.error(f"[RESYNC] Unexpected error: {str(e)}")
            logger.error(f"[RESYNC] Full traceback:\n{traceback.format_exc()}")
            return ResyncResponse(
                resynced_count=0,
                workflows=[],
                errors=[f"Unexpected error: {str(e)}"],
                message="Resync failed"
            )

    @router.post("/workflows/batch", response_model=list[WorkflowHistoryItem])
    async def get_workflows_batch(workflow_ids: list[str]) -> list[WorkflowHistoryItem]:
        """
        Fetch multiple workflows by ADW IDs in a single request.

        This endpoint is optimized for Phase 3E's similar workflows feature,
        allowing the frontend to fetch multiple workflows efficiently instead
        of making N separate requests.

        Args:
            workflow_ids: List of ADW IDs to fetch (max 20)

        Returns:
            List of workflow history items

        Raises:
            HTTPException 400: If more than 20 workflow IDs requested
            HTTPException 500: If database error occurs

        Example:
            POST /api/workflows/batch
            Body: ["adw-abc123", "adw-def456", "adw-ghi789"]
            Returns: [{ workflow data }, { workflow data }, ...]
        """
        try:
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
                        try:
                            workflow["similar_workflow_ids"] = json.loads(workflow["similar_workflow_ids"])
                        except (json.JSONDecodeError, TypeError):
                            workflow["similar_workflow_ids"] = []

                    workflows.append(WorkflowHistoryItem(**workflow))

            logger.info(f"[BATCH] Fetched {len(workflows)}/{len(workflow_ids)} workflows")
            return workflows

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[BATCH] Error fetching workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.get("/workflow-analytics/{adw_id}", response_model=WorkflowAnalyticsDetail)
    async def get_workflow_analytics(adw_id: str) -> WorkflowAnalyticsDetail:
        """Get advanced analytics for a specific workflow"""
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve analytics for {adw_id}: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}") from e

    @router.get("/workflow-trends", response_model=WorkflowTrends)
    async def get_workflow_trends(days: int = 30, group_by: str = "day") -> WorkflowTrends:
        """Get trend data over time - delegates to WorkflowService"""
        try:
            trends = workflow_service.get_workflow_trends(days=days, group_by=group_by)
            logger.info(f"[SUCCESS] Retrieved workflow trends for {days} days grouped by {group_by}")
            return trends
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow trends: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}") from e

    @router.get("/cost-predictions", response_model=CostPrediction)
    async def predict_workflow_cost(classification: str, complexity: str, model: str) -> CostPrediction:
        """Predict workflow cost - delegates to WorkflowService"""
        try:
            prediction = workflow_service.predict_workflow_cost(
                classification=classification,
                complexity=complexity,
                model=model
            )
            logger.info(f"[SUCCESS] Generated cost prediction for {classification}/{complexity}/{model}: ${prediction.predicted_cost:.4f}")
            return prediction
        except Exception as e:
            logger.error(f"[ERROR] Failed to predict workflow cost: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to predict cost: {str(e)}") from e

    @router.get("/workflow-catalog", response_model=WorkflowCatalogResponse)
    async def get_workflow_catalog() -> WorkflowCatalogResponse:
        """Get workflow catalog - delegates to WorkflowService"""
        try:
            catalog = workflow_service.get_workflow_catalog()
            logger.info(f"[SUCCESS] Retrieved {catalog.total} workflow templates")
            return catalog
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrieve workflow catalog: {str(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            return WorkflowCatalogResponse(workflows=[], total=0)
