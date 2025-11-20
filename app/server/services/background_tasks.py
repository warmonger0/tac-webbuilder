"""
Background Task Manager - Manages background watching tasks

This service is responsible for:
- Watching workflows directory for changes
- Watching routes for changes
- Watching workflow history for changes
- Broadcasting updates via WebSocket
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from core.data_models import WorkflowHistoryFilters

if TYPE_CHECKING:
    from services.websocket_manager import ConnectionManager
    from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for watching and broadcasting changes"""

    def __init__(
        self,
        websocket_manager: "ConnectionManager",
        workflow_service: "WorkflowService",
        workflow_watch_interval: float = 10.0,
        routes_watch_interval: float = 10.0,
        history_watch_interval: float = 10.0,
    ):
        """
        Initialize the BackgroundTaskManager

        Args:
            websocket_manager: WebSocket connection manager for broadcasting
            workflow_service: Workflow service for data operations
            workflow_watch_interval: Seconds between workflow checks (default: 10)
            routes_watch_interval: Seconds between routes checks (default: 10)
            history_watch_interval: Seconds between history checks (default: 10)
        """
        self.websocket_manager = websocket_manager
        self.workflow_service = workflow_service
        self.workflow_watch_interval = workflow_watch_interval
        self.routes_watch_interval = routes_watch_interval
        self.history_watch_interval = history_watch_interval

        # Task references for cleanup
        self._tasks: list[asyncio.Task] = []

        # App reference (will be set when starting routes watcher)
        self._app = None

    def set_app(self, app):
        """
        Set the FastAPI app instance for route introspection

        Args:
            app: FastAPI application instance
        """
        self._app = app

    async def start_all(self) -> list[asyncio.Task]:
        """
        Start all background tasks

        Returns:
            List of task references for external management
        """
        logger.info("[BACKGROUND_TASKS] Starting all background watchers...")

        # Create tasks
        self._tasks = [
            asyncio.create_task(self.watch_workflows()),
            asyncio.create_task(self.watch_routes()),
            asyncio.create_task(self.watch_workflow_history()),
        ]

        logger.info(
            f"[BACKGROUND_TASKS] Started {len(self._tasks)} background watchers"
        )
        return self._tasks

    async def stop_all(self) -> None:
        """Stop all background tasks"""
        logger.info("[BACKGROUND_TASKS] Stopping all background watchers...")

        for task in self._tasks:
            task.cancel()

        # Wait for all tasks to be cancelled
        await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("[BACKGROUND_TASKS] All background watchers stopped")

    async def watch_workflows(self) -> None:
        """
        Background task to watch for workflow changes and broadcast updates

        This watcher:
        - Checks every workflow_watch_interval seconds
        - Only broadcasts if there are active WebSocket connections
        - Only broadcasts if workflow state has changed
        - Handles errors gracefully with backoff
        """
        try:
            while True:
                try:
                    # Only do work if there are active connections
                    if len(self.websocket_manager.active_connections) > 0:
                        workflows = self.workflow_service.get_workflows()

                        # Convert to JSON for comparison
                        current_state = json.dumps(
                            [w.model_dump() for w in workflows], sort_keys=True
                        )

                        # Only broadcast if state changed
                        if current_state != self.websocket_manager.last_workflow_state:
                            self.websocket_manager.last_workflow_state = current_state
                            await self.websocket_manager.broadcast(
                                {
                                    "type": "workflows_update",
                                    "data": [w.model_dump() for w in workflows],
                                }
                            )
                            logger.info(
                                f"[BACKGROUND_TASKS] Broadcasted workflow update to "
                                f"{len(self.websocket_manager.active_connections)} clients"
                            )

                    await asyncio.sleep(self.workflow_watch_interval)

                except Exception as e:
                    logger.error(f"[BACKGROUND_TASKS] Error in workflow watcher: {e}")
                    await asyncio.sleep(5)  # Back off on error

        except asyncio.CancelledError:
            logger.info("[BACKGROUND_TASKS] Workflow watcher cancelled")
            raise  # Re-raise to properly handle cancellation

    async def watch_routes(self) -> None:
        """
        Background task to watch for route changes and broadcast updates

        This watcher:
        - Checks every routes_watch_interval seconds
        - Only broadcasts if there are active WebSocket connections
        - Only broadcasts if routes state has changed
        - Requires app instance to be set via set_app()
        """
        try:
            while True:
                try:
                    # Only do work if there are active connections
                    if len(self.websocket_manager.active_connections) > 0:
                        if self._app is None:
                            logger.warning(
                                "[BACKGROUND_TASKS] App not set for routes watcher, skipping..."
                            )
                            await asyncio.sleep(self.routes_watch_interval)
                            continue

                        routes = self.workflow_service.get_routes(self._app)

                        # Convert to JSON for comparison
                        current_state = json.dumps(
                            [r.model_dump() for r in routes], sort_keys=True
                        )

                        # Only broadcast if state changed
                        if current_state != self.websocket_manager.last_routes_state:
                            self.websocket_manager.last_routes_state = current_state
                            await self.websocket_manager.broadcast(
                                {
                                    "type": "routes_update",
                                    "data": [r.model_dump() for r in routes],
                                }
                            )
                            logger.info(
                                f"[BACKGROUND_TASKS] Broadcasted routes update to "
                                f"{len(self.websocket_manager.active_connections)} clients"
                            )

                    await asyncio.sleep(self.routes_watch_interval)

                except Exception as e:
                    logger.error(f"[BACKGROUND_TASKS] Error in routes watcher: {e}")
                    await asyncio.sleep(5)  # Back off on error

        except asyncio.CancelledError:
            logger.info("[BACKGROUND_TASKS] Routes watcher cancelled")
            raise  # Re-raise to properly handle cancellation

    async def watch_workflow_history(self) -> None:
        """
        Background task to watch for workflow history changes and broadcast updates

        This watcher:
        - Checks every history_watch_interval seconds
        - Only broadcasts if there are active WebSocket connections
        - Uses workflow_service caching to avoid redundant syncs
        - Only broadcasts if sync actually found changes
        """
        try:
            while True:
                try:
                    # Only do work if there are active connections
                    if len(self.websocket_manager.active_connections) > 0:
                        # Get latest workflow history - did_sync tells us if anything changed
                        history_data, did_sync = (
                            self.workflow_service.get_workflow_history_with_cache(
                                WorkflowHistoryFilters(limit=50, offset=0)
                            )
                        )

                        # Only broadcast if sync found actual changes
                        if did_sync:
                            await self.websocket_manager.broadcast(
                                {
                                    "type": "workflow_history_update",
                                    "data": history_data.model_dump(),
                                }
                            )
                            logger.info(
                                f"[BACKGROUND_TASKS] Broadcasted workflow history update to "
                                f"{len(self.websocket_manager.active_connections)} clients"
                            )

                    await asyncio.sleep(self.history_watch_interval)

                except Exception as e:
                    logger.error(
                        f"[BACKGROUND_TASKS] Error in workflow history watcher: {e}"
                    )
                    await asyncio.sleep(5)  # Back off on error

        except asyncio.CancelledError:
            logger.info("[BACKGROUND_TASKS] Workflow history watcher cancelled")
            raise  # Re-raise to properly handle cancellation
