"""
Workflow Service - Handles workflow and routes data operations

This service is responsible for:
- Scanning and reading workflow data from the agents directory
- Discovering and introspecting API routes
- Providing workflow history data with caching
"""

import json
import logging
import os
import time
from typing import List, Tuple

from core.data_models import (
    Route,
    TrendDataPoint,
    Workflow,
    WorkflowHistoryAnalytics,
    WorkflowHistoryFilters,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowTrends,
)
from core.workflow_history import (
    get_history_analytics,
    get_workflow_history,
    sync_workflow_history,
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow and routes data"""

    def __init__(
        self,
        agents_dir: str | None = None,
        sync_cache_seconds: int = 10,
        github_repo: str | None = None,
    ):
        """
        Initialize the WorkflowService

        Args:
            agents_dir: Path to agents directory (default: ../../agents from server location)
            sync_cache_seconds: Seconds to cache sync results (default: 10)
            github_repo: GitHub repository in format "owner/repo" (default: from env)
        """
        if agents_dir is None:
            # Default to ../../agents from server location
            self.agents_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "agents"
            )
        else:
            self.agents_dir = agents_dir

        self.sync_cache_seconds = sync_cache_seconds
        self.github_repo = github_repo or os.environ.get(
            "GITHUB_REPO", "warmonger0/tac-webbuilder"
        )
        self._last_sync_time = 0

    def get_workflows(self) -> List[Workflow]:
        """
        Get all active workflows from agents directory

        Only returns workflows with valid integer issue numbers (filters out debug/test workflows).

        Returns:
            List of Workflow objects
        """
        workflows = []

        # Check if agents directory exists
        if not os.path.exists(self.agents_dir):
            logger.warning(
                f"[WORKFLOW_SERVICE] Agents directory not found: {self.agents_dir}"
            )
            return []

        # Scan for workflow directories
        for adw_id in os.listdir(self.agents_dir):
            adw_dir = os.path.join(self.agents_dir, adw_id)
            state_file = os.path.join(adw_dir, "adw_state.json")

            # Skip if not a directory or no state file
            if not os.path.isdir(adw_dir) or not os.path.exists(state_file):
                continue

            # Read state file
            try:
                with open(state_file) as f:
                    state = json.load(f)

                # Validate issue_number - must be convertible to int
                issue_num_raw = state.get("issue_number", 0)
                try:
                    issue_number = int(issue_num_raw)
                except (ValueError, TypeError):
                    # Skip workflows with invalid issue numbers (debug workflows, tests, etc.)
                    logger.debug(
                        f"[WORKFLOW_SERVICE] Skipping workflow {adw_id} with invalid issue_number: {issue_num_raw}"
                    )
                    continue

                # Determine current phase by checking which phase directories exist
                phase_order = ["plan", "build", "test", "review", "document", "ship"]
                current_phase = "plan"  # Default

                for phase in reversed(phase_order):
                    phase_dir = os.path.join(adw_dir, f"adw_{phase}_iso")
                    if os.path.exists(phase_dir):
                        current_phase = phase
                        break

                # Create GitHub URL
                github_url = f"https://github.com/{self.github_repo}/issues/{issue_number}"

                # Create workflow object
                workflow = Workflow(
                    adw_id=state["adw_id"],
                    issue_number=issue_number,
                    phase=current_phase,
                    github_url=github_url,
                )
                workflows.append(workflow)

            except Exception as e:
                logger.error(
                    f"[WORKFLOW_SERVICE] Failed to process workflow {adw_id}: {str(e)}"
                )
                continue

        return workflows

    def get_routes(self, app) -> List[Route]:
        """
        Get all API routes from the FastAPI application

        Args:
            app: FastAPI application instance

        Returns:
            List of Route objects
        """
        route_list = []

        try:
            # Introspect FastAPI routes
            for route in app.routes:
                # Filter for HTTP routes (not WebSocket, static, etc.)
                if hasattr(route, "methods") and hasattr(route, "path"):
                    # Skip internal routes
                    if (
                        route.path.startswith("/docs")
                        or route.path.startswith("/redoc")
                        or route.path.startswith("/openapi")
                    ):
                        continue

                    # Extract route information
                    for method in route.methods:
                        # Skip OPTIONS method (automatically added by CORS)
                        if method == "OPTIONS":
                            continue

                        # Extract route metadata
                        route_name = route.name if hasattr(route, "name") else None
                        summary = None
                        description = None
                        tags = []

                        # Try to extract from endpoint function
                        if hasattr(route, "endpoint") and route.endpoint:
                            summary = (
                                route.endpoint.__doc__.split("\n")[0].strip()
                                if route.endpoint.__doc__
                                else None
                            )
                            if hasattr(route, "tags"):
                                tags = route.tags or []

                        route_obj = Route(
                            path=route.path,
                            method=method,
                            name=route_name,
                            summary=summary,
                            description=description,
                            tags=tags,
                        )
                        route_list.append(route_obj)

        except Exception as e:
            logger.error(f"[WORKFLOW_SERVICE] Error getting routes: {e}")

        return route_list

    def get_workflow_history_with_cache(
        self, filters: WorkflowHistoryFilters | None = None
    ) -> Tuple[WorkflowHistoryResponse, bool]:
        """
        Get workflow history data with caching

        This method:
        1. Syncs workflow history if cache has expired
        2. Applies filters
        3. Fetches workflow history from database
        4. Fetches analytics

        Returns:
            tuple: (WorkflowHistoryResponse, did_sync: bool)
                did_sync indicates if sync found and processed changes
        """
        did_sync = False

        try:
            # Only sync if cache has expired
            current_time = time.time()
            if current_time - self._last_sync_time >= self.sync_cache_seconds:
                logger.debug(
                    f"[WORKFLOW_SERVICE] Cache expired, syncing workflow history "
                    f"(last sync {current_time - self._last_sync_time:.1f}s ago)"
                )
                synced_count = sync_workflow_history()
                self._last_sync_time = current_time
                did_sync = synced_count > 0  # Only True if actual changes found
            else:
                logger.debug(
                    f"[WORKFLOW_SERVICE] Using cached data "
                    f"(last sync {current_time - self._last_sync_time:.1f}s ago)"
                )

            # Apply filters
            filter_params = self._prepare_filter_params(filters)

            # Get workflow history
            workflows, total_count = get_workflow_history(**filter_params)

            # Get analytics
            analytics = get_history_analytics()

            # Convert database rows to Pydantic models
            workflow_items = [WorkflowHistoryItem(**workflow) for workflow in workflows]
            analytics_model = WorkflowHistoryAnalytics(**analytics)

            return (
                WorkflowHistoryResponse(
                    workflows=workflow_items,
                    total_count=total_count,
                    analytics=analytics_model,
                ),
                did_sync,
            )

        except Exception as e:
            logger.error(
                f"[WORKFLOW_SERVICE] Failed to get workflow history data: {str(e)}"
            )
            # Return empty response on error
            return (
                WorkflowHistoryResponse(
                    workflows=[],
                    total_count=0,
                    analytics=WorkflowHistoryAnalytics(),
                ),
                False,
            )

    def _prepare_filter_params(
        self, filters: WorkflowHistoryFilters | None
    ) -> dict:
        """
        Prepare filter parameters for workflow history query

        Args:
            filters: Optional filter object

        Returns:
            Dictionary of filter parameters
        """
        if filters:
            return {
                "limit": filters.limit or 20,
                "offset": filters.offset or 0,
                "status": filters.status,
                "model": filters.model,
                "template": filters.template,
                "start_date": filters.start_date,
                "end_date": filters.end_date,
                "search": filters.search,
                "sort_by": filters.sort_by or "created_at",
                "sort_order": filters.sort_order or "DESC",
            }
        else:
            return {
                "limit": 20,
                "offset": 0,
                "sort_by": "created_at",
                "sort_order": "DESC",
            }

    def get_workflow_trends(self, days: int = 30, group_by: str = "day") -> WorkflowTrends:
        """
        Get trend data over time for workflows.

        Args:
            days: Number of days to look back (default: 30)
            group_by: Grouping period - "hour", "day", or "week" (default: "day")

        Returns:
            WorkflowTrends object with cost, duration, success rate, and cache efficiency trends
        """
        from collections import defaultdict
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch workflows in date range
        workflows, _ = get_workflow_history(
            limit=10000,
            offset=0,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        # Group by time period
        cost_by_period = defaultdict(lambda: {"total": 0.0, "count": 0})
        duration_by_period = defaultdict(lambda: {"total": 0, "count": 0})
        success_by_period = defaultdict(lambda: {"success": 0, "total": 0})
        cache_by_period = defaultdict(lambda: {"total": 0.0, "count": 0})

        for workflow in workflows:
            if not workflow.get("created_at"):
                continue

            try:
                created_dt = datetime.fromisoformat(workflow["created_at"].replace("Z", "+00:00"))

                # Determine period key based on group_by
                if group_by == "hour":
                    period_key = created_dt.strftime("%Y-%m-%d %H:00")
                elif group_by == "week":
                    period_key = created_dt.strftime("%Y-W%U")
                else:  # day
                    period_key = created_dt.strftime("%Y-%m-%d")

                # Aggregate metrics
                if workflow.get("actual_cost_total"):
                    cost_by_period[period_key]["total"] += workflow["actual_cost_total"]
                    cost_by_period[period_key]["count"] += 1

                if workflow.get("duration_seconds"):
                    duration_by_period[period_key]["total"] += workflow["duration_seconds"]
                    duration_by_period[period_key]["count"] += 1

                if workflow.get("status") in ["completed", "failed"]:
                    success_by_period[period_key]["total"] += 1
                    if workflow["status"] == "completed":
                        success_by_period[period_key]["success"] += 1

                if workflow.get("cache_efficiency_percent") is not None:
                    cache_by_period[period_key]["total"] += workflow["cache_efficiency_percent"]
                    cache_by_period[period_key]["count"] += 1

            except Exception as e:
                logger.debug(f"Error processing workflow {workflow.get('adw_id')}: {e}")
                continue

        # Convert to trend data points
        cost_trend = [
            TrendDataPoint(
                timestamp=period,
                value=data["total"] / data["count"] if data["count"] > 0 else 0,
                count=data["count"]
            )
            for period, data in sorted(cost_by_period.items())
        ]

        duration_trend = [
            TrendDataPoint(
                timestamp=period,
                value=data["total"] / data["count"] if data["count"] > 0 else 0,
                count=data["count"]
            )
            for period, data in sorted(duration_by_period.items())
        ]

        success_rate_trend = [
            TrendDataPoint(
                timestamp=period,
                value=(data["success"] / data["total"] * 100) if data["total"] > 0 else 0,
                count=data["total"]
            )
            for period, data in sorted(success_by_period.items())
        ]

        cache_efficiency_trend = [
            TrendDataPoint(
                timestamp=period,
                value=data["total"] / data["count"] if data["count"] > 0 else 0,
                count=data["count"]
            )
            for period, data in sorted(cache_by_period.items())
        ]

        return WorkflowTrends(
            cost_trend=cost_trend,
            duration_trend=duration_trend,
            success_rate_trend=success_rate_trend,
            cache_efficiency_trend=cache_efficiency_trend
        )
