"""
Workflow Service - Handles workflow and routes data operations

This service is responsible for:
- Scanning and reading workflow data from the agents directory
- Discovering and introspecting API routes
- Providing workflow history data with caching
- Running background sync worker for workflow history
"""

import json
import logging
import os
import threading
import time

from core.data_models import (
    CostPrediction,
    Route,
    TrendDataPoint,
    Workflow,
    WorkflowCatalogResponse,
    WorkflowHistoryAnalytics,
    WorkflowHistoryFilters,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowTemplate,
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
        enable_background_sync: bool = True,
    ):
        """
        Initialize the WorkflowService

        Args:
            agents_dir: Path to agents directory (default: ../../agents from server location)
            sync_cache_seconds: Seconds to cache sync results (default: 10)
            github_repo: GitHub repository in format "owner/repo" (default: from env)
            enable_background_sync: Enable background sync worker (default: True)
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
        self._background_sync_enabled = enable_background_sync
        self._background_sync_thread = None
        self._stop_background_sync = threading.Event()

        # Start background sync worker if enabled
        if self._background_sync_enabled:
            self._start_background_sync()

    def _start_background_sync(self):
        """Start background sync worker thread."""
        logger.info("[WORKFLOW_SERVICE] Starting background sync worker")
        self._background_sync_thread = threading.Thread(
            target=self._background_sync_worker,
            daemon=True,
            name="workflow-sync-worker"
        )
        self._background_sync_thread.start()

    def _background_sync_worker(self):
        """Background worker that periodically syncs workflow history."""
        logger.info(
            f"[WORKFLOW_SERVICE] Background sync worker started "
            f"(interval: {self.sync_cache_seconds}s)"
        )

        # Perform initial sync on startup to warm cache
        try:
            logger.info("[WORKFLOW_SERVICE] Performing initial sync...")
            synced_count = sync_workflow_history()
            self._last_sync_time = time.time()
            logger.info(
                f"[WORKFLOW_SERVICE] Initial sync complete: {synced_count} workflows"
            )
        except Exception as e:
            logger.error(f"[WORKFLOW_SERVICE] Initial sync failed: {e}")

        # Main sync loop
        while not self._stop_background_sync.is_set():
            try:
                # Wait for sync interval or stop signal
                if self._stop_background_sync.wait(timeout=self.sync_cache_seconds):
                    break  # Stop signal received

                # Perform sync
                logger.debug("[WORKFLOW_SERVICE] Background sync triggered")
                synced_count = sync_workflow_history()
                self._last_sync_time = time.time()

                if synced_count > 0:
                    logger.info(
                        f"[WORKFLOW_SERVICE] Background sync: {synced_count} workflows updated"
                    )
                else:
                    logger.debug("[WORKFLOW_SERVICE] Background sync: no changes")

            except Exception as e:
                logger.error(f"[WORKFLOW_SERVICE] Background sync error: {e}")
                # Continue running despite errors

        logger.info("[WORKFLOW_SERVICE] Background sync worker stopped")

    def stop_background_sync(self):
        """Stop the background sync worker (for graceful shutdown)."""
        if self._background_sync_enabled and self._background_sync_thread:
            logger.info("[WORKFLOW_SERVICE] Stopping background sync worker...")
            self._stop_background_sync.set()
            self._background_sync_thread.join(timeout=5)
            logger.info("[WORKFLOW_SERVICE] Background sync worker stopped")

    def get_workflows(self) -> list[Workflow]:
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

    def get_routes(self, app) -> list[Route]:
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
    ) -> tuple[WorkflowHistoryResponse, bool]:
        """
        Get workflow history data with caching

        With background sync enabled, this method instantly returns cached data.
        The background worker keeps the cache fresh automatically.

        Without background sync, falls back to the old behavior of syncing on-demand.

        Returns:
            tuple: (WorkflowHistoryResponse, did_sync: bool)
                did_sync is always False with background sync (sync happens independently)
        """
        did_sync = False

        try:
            # With background sync, we always use cached data (no blocking sync)
            if self._background_sync_enabled:
                current_time = time.time()
                logger.debug(
                    f"[WORKFLOW_SERVICE] Using cached data from background worker "
                    f"(last sync {current_time - self._last_sync_time:.1f}s ago)"
                )
            else:
                # Fallback: manual sync if background worker disabled
                current_time = time.time()
                if current_time - self._last_sync_time >= self.sync_cache_seconds:
                    logger.debug(
                        f"[WORKFLOW_SERVICE] Cache expired, syncing workflow history "
                        f"(last sync {current_time - self._last_sync_time:.1f}s ago)"
                    )
                    synced_count = sync_workflow_history()
                    self._last_sync_time = current_time
                    did_sync = synced_count > 0
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

    def predict_workflow_cost(
        self,
        classification: str,
        complexity: str,
        model: str
    ) -> CostPrediction:
        """
        Predict workflow cost based on historical data.

        Args:
            classification: Workflow template/classification
            complexity: Complexity level
            model: Model being used

        Returns:
            CostPrediction with predicted cost, confidence, and statistics
        """
        # Fetch similar historical workflows
        workflows, _ = get_workflow_history(
            limit=1000,
            offset=0,
            template=classification,
            model=model
        )

        # Filter by complexity if specified
        if complexity:
            workflows = [
                w for w in workflows
                if w.get("complexity_actual") == complexity or w.get("complexity_estimated") == complexity
            ]

        # Extract costs
        costs = [
            w["actual_cost_total"]
            for w in workflows
            if w.get("actual_cost_total") and w["actual_cost_total"] > 0
        ]

        if not costs:
            # No historical data, return conservative estimate
            return CostPrediction(
                predicted_cost=0.05,
                confidence=0.0,
                sample_size=0,
                min_cost=0.0,
                max_cost=0.0,
                avg_cost=0.0
            )

        # Calculate statistics
        avg_cost = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)

        # Confidence based on sample size (diminishing returns)
        confidence = min(100.0, (len(costs) / 10) * 100)

        return CostPrediction(
            predicted_cost=round(avg_cost, 4),
            confidence=round(confidence, 2),
            sample_size=len(costs),
            min_cost=round(min_cost, 4),
            max_cost=round(max_cost, 4),
            avg_cost=round(avg_cost, 4)
        )

    def get_workflow_catalog(self) -> WorkflowCatalogResponse:
        """Get catalog of available ADW workflow templates"""
        workflows = [
            WorkflowTemplate(
                name="adw_lightweight_iso",
                display_name="Lightweight Workflow",
                phases=["Plan (minimal)", "Build", "Ship"],
                purpose="Optimized for simple UI changes, docs updates, and single-file modifications. Skips extensive testing and review.",
                cost_range="$0.20 - $0.50",
                best_for=["UI-only changes", "Documentation updates", "Simple bug fixes", "Single-file modifications"]
            ),
            WorkflowTemplate(
                name="adw_sdlc_iso",
                display_name="Full SDLC Workflow",
                phases=["Plan", "Build", "Test", "Review", "Document", "Ship"],
                purpose="Complete software development lifecycle for standard features and improvements.",
                cost_range="$3 - $5",
                best_for=["Standard features", "Multi-file changes", "Features requiring validation", "General improvements"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_test_iso",
                display_name="Plan-Build-Test Workflow",
                phases=["Plan", "Build", "Test"],
                purpose="Focused on implementation and testing without full documentation phase. Good for bugs and medium complexity features.",
                cost_range="$3 - $5",
                best_for=["Bug fixes requiring testing", "Medium complexity features", "Changes needing validation"]
            ),
            WorkflowTemplate(
                name="adw_plan_iso",
                display_name="Planning Only",
                phases=["Plan"],
                purpose="Generate implementation plan without executing. Useful for proposal review or complex planning.",
                cost_range="$0.50 - $1",
                best_for=["Architecture planning", "Proposal generation", "Complex feature scoping"]
            ),
            WorkflowTemplate(
                name="adw_ship_iso",
                display_name="Ship Only",
                phases=["Ship"],
                purpose="Create PR and merge existing branch work. Use after manual development.",
                cost_range="$0.30 - $0.50",
                best_for=["Shipping manual changes", "Creating PR for existing work", "Final merge step"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_iso",
                display_name="Plan-Build",
                phases=["Plan", "Build"],
                purpose="Quick implementation without testing or documentation. Use when you'll test manually.",
                cost_range="$2 - $3",
                best_for=["Prototypes", "Quick implementations", "Manual testing workflows"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_test_review_iso",
                display_name="Plan-Build-Test-Review",
                phases=["Plan", "Build", "Test", "Review"],
                purpose="Comprehensive workflow with code review but no documentation phase.",
                cost_range="$4 - $6",
                best_for=["High-quality implementations", "Critical features", "Production code requiring review"]
            ),
        ]

        return WorkflowCatalogResponse(workflows=workflows, total=len(workflows))
