"""
QC Metrics Watcher Service.

Monitors file system for changes that affect QC metrics and automatically
triggers metric refresh + WebSocket broadcast.

Watches for:
- Coverage file changes (.coverage, coverage-summary.json)
- Test file changes (test_*.py, *.test.ts, *.spec.ts)
- Source code changes (*.py, *.ts, *.tsx)
- Linter execution completion
"""

import asyncio
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class QCMetricsWatcher:
    """
    Watches for file system changes that affect QC metrics.

    Automatically triggers metric refresh and WebSocket broadcast when:
    - Coverage files are updated
    - Test files are modified
    - Source code changes accumulate
    - Linting completes
    """

    def __init__(self, project_root: Path | None = None, websocket_manager=None):
        """Initialize QC metrics watcher.

        Args:
            project_root: Root directory of the project
            websocket_manager: WebSocket connection manager for broadcasts
        """
        if project_root is None:
            # Default to tac-webbuilder root
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.websocket_manager = websocket_manager
        self.is_running = False
        self.watcher_task: asyncio.Task | None = None

        # Track last modification times
        self.coverage_files_mtime: dict[str, float] = {}
        self.last_broadcast_time: float = 0
        self.min_broadcast_interval: float = 30.0  # Min 30s between broadcasts

        # Background refresh settings
        self.enable_background_refresh: bool = True
        self.background_refresh_interval: float = 300.0  # 5 minutes
        self.last_background_refresh: float = 0

        # Change accumulation for smart updates
        self.pending_changes: set[str] = set()
        self.change_accumulation_time: float = 5.0  # Wait 5s for changes to settle

        # Files to watch
        self.coverage_files = [
            self.project_root / "app" / "server" / ".coverage",
            self.project_root / "app" / "client" / "coverage" / "coverage-summary.json",
            self.project_root / "adws" / "tests" / ".coverage",
        ]

        logger.info(f"QCMetricsWatcher initialized (project_root: {self.project_root})")

    async def start(self):
        """Start the QC metrics watcher."""
        if self.is_running:
            logger.warning("[QC_WATCHER] Already running")
            return

        self.is_running = True

        # Initialize mtime tracking
        for coverage_file in self.coverage_files:
            if coverage_file.exists():
                self.coverage_files_mtime[str(coverage_file)] = coverage_file.stat().st_mtime
            else:
                self.coverage_files_mtime[str(coverage_file)] = 0

        # Start watcher task
        self.watcher_task = asyncio.create_task(self._watch_loop())
        logger.info("[QC_WATCHER] Started watching for QC metric changes")

    async def stop(self):
        """Stop the QC metrics watcher."""
        if not self.is_running:
            return

        self.is_running = False

        if self.watcher_task:
            self.watcher_task.cancel()
            try:
                await self.watcher_task
            except asyncio.CancelledError:
                pass

        logger.info("[QC_WATCHER] Stopped")

    async def _watch_loop(self):
        """Main watch loop - checks for file changes periodically."""
        try:
            while self.is_running:
                current_time = time.time()

                # Check coverage files every 10 seconds
                changed = await self._check_coverage_files()

                if changed:
                    # Add to pending changes
                    self.pending_changes.add("coverage")

                # Check if we should process pending changes
                if self.pending_changes:
                    # Wait for changes to settle before triggering refresh
                    time_since_first_change = current_time - self.last_broadcast_time
                    if time_since_first_change >= self.change_accumulation_time:
                        logger.info(f"[QC_WATCHER] Processing {len(self.pending_changes)} pending changes")
                        await self._trigger_refresh()
                        self.pending_changes.clear()

                # Background refresh (every 5 minutes)
                if self.enable_background_refresh:
                    time_since_background = current_time - self.last_background_refresh
                    if time_since_background >= self.background_refresh_interval:
                        logger.info("[QC_WATCHER] Triggering scheduled background refresh")
                        await self._trigger_refresh()
                        self.last_background_refresh = current_time

                # Sleep before next check
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.debug("[QC_WATCHER] Watch loop cancelled")
            raise
        except Exception as e:
            logger.error(f"[QC_WATCHER] Error in watch loop: {e}", exc_info=True)

    async def _check_coverage_files(self) -> bool:
        """Check if any coverage files have been modified.

        Returns:
            True if changes detected, False otherwise
        """
        changed = False

        for coverage_file in self.coverage_files:
            file_path = str(coverage_file)

            if coverage_file.exists():
                current_mtime = coverage_file.stat().st_mtime
                last_mtime = self.coverage_files_mtime.get(file_path, 0)

                if current_mtime > last_mtime:
                    logger.info(f"[QC_WATCHER] Coverage file changed: {coverage_file.name}")
                    self.coverage_files_mtime[file_path] = current_mtime
                    changed = True
            else:
                # File doesn't exist yet - check if it was just created
                if self.coverage_files_mtime.get(file_path, 0) != 0:
                    logger.info(f"[QC_WATCHER] Coverage file removed: {coverage_file.name}")
                    self.coverage_files_mtime[file_path] = 0
                    changed = True

        return changed

    async def _trigger_refresh(self):
        """Trigger QC metrics refresh and broadcast to WebSocket clients."""
        # Rate limiting: don't broadcast more than once per min_broadcast_interval
        current_time = time.time()
        time_since_last = current_time - self.last_broadcast_time

        if time_since_last < self.min_broadcast_interval:
            logger.debug(
                f"[QC_WATCHER] Skipping refresh (last broadcast {time_since_last:.1f}s ago, "
                f"min interval: {self.min_broadcast_interval}s)"
            )
            return

        logger.info("[QC_WATCHER] Triggering QC metrics refresh (parallelized)...")

        try:
            # Import here to avoid circular dependencies
            from services.qc_metrics_service import QCMetricsService

            # Compute fresh metrics using parallelized async method
            service = QCMetricsService(project_root=self.project_root)
            metrics = await service.get_all_metrics_async()

            # Update the cache in the route handler
            from routes import qc_metrics_routes
            qc_metrics_routes._qc_metrics_cache = metrics

            logger.info(
                f"[QC_WATCHER] QC metrics updated - Score: {metrics['overall_score']}/100, "
                f"Coverage: {metrics['coverage']['overall_coverage']}%"
            )

            # Broadcast to WebSocket clients
            if self.websocket_manager:
                await self._broadcast_metrics(metrics)

            self.last_broadcast_time = current_time

        except Exception as e:
            logger.error(f"[QC_WATCHER] Error refreshing metrics: {e}", exc_info=True)

    async def _broadcast_metrics(self, metrics: dict):
        """Broadcast QC metrics to all WebSocket clients.

        Args:
            metrics: QC metrics dictionary
        """
        if not self.websocket_manager:
            logger.warning("[QC_WATCHER] No WebSocket manager - cannot broadcast")
            return

        message = {
            "type": "qc_metrics_update",
            "data": metrics
        }

        try:
            # Use the connection manager's broadcast method
            await self.websocket_manager.broadcast(message)
            logger.info("[QC_WATCHER] Broadcasted QC metrics update to WebSocket clients")
        except Exception as e:
            logger.error(f"[QC_WATCHER] Error broadcasting metrics: {e}", exc_info=True)

    async def manual_refresh(self):
        """Manually trigger a refresh (bypasses rate limiting).

        Used when user clicks the Refresh button in the UI.
        """
        logger.info("[QC_WATCHER] Manual refresh triggered")

        # Temporarily reduce min interval to allow immediate refresh
        original_interval = self.min_broadcast_interval
        self.min_broadcast_interval = 0

        try:
            await self._trigger_refresh()
        finally:
            self.min_broadcast_interval = original_interval


# Singleton instance
_qc_watcher_instance: QCMetricsWatcher | None = None


def get_qc_watcher(websocket_manager=None) -> QCMetricsWatcher:
    """Get or create the singleton QC metrics watcher.

    Args:
        websocket_manager: WebSocket connection manager (only used on first call)

    Returns:
        QCMetricsWatcher instance
    """
    global _qc_watcher_instance

    if _qc_watcher_instance is None:
        _qc_watcher_instance = QCMetricsWatcher(websocket_manager=websocket_manager)

    return _qc_watcher_instance
