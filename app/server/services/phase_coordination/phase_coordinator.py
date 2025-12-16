"""
PhaseCoordinator Service

Event-driven service that coordinates parallel execution of multi-phase workflows.

Responsibilities:
- Handle workflow completion events from WebSocket broadcasts
- Resolve phase dependencies and find newly ready phases
- Enforce concurrency limits (max 3 ADWs running concurrently)
- Create isolated GitHub issues (no parent dependencies)
- Launch ADWs in parallel when ready
- Broadcast WebSocket events for real-time updates
- Post GitHub comments on phase transitions
"""

import asyncio
import contextlib
import json
import logging
from datetime import datetime

from services.phase_queue_service import PhaseQueueService

from .phase_github_notifier import PhaseGitHubNotifier
from .workflow_completion_detector import WorkflowCompletionDetector

logger = logging.getLogger(__name__)


class PhaseCoordinator:
    """
    Coordinates parallel execution of multi-phase workflows (event-driven).

    Handles workflow completion events, resolves dependencies,
    and launches up to 3 ADWs concurrently.
    """

    def __init__(
        self,
        phase_queue_service: PhaseQueueService,
        max_concurrent_adws: int = 3,
        websocket_manager = None,
        github_poster = None
    ):
        """
        Initialize PhaseCoordinator.

        Args:
            phase_queue_service: PhaseQueueService instance
            max_concurrent_adws: Maximum concurrent ADWs (default: 3)
            websocket_manager: WebSocket manager for real-time updates (optional)
            github_poster: GitHubPoster for just-in-time issue creation (optional)

        Note:
            Database type (SQLite/PostgreSQL) is determined by DB_TYPE environment variable.
        """
        self.phase_queue_service = phase_queue_service
        self.max_concurrent_adws = max_concurrent_adws
        self.websocket_manager = websocket_manager
        self.github_poster = github_poster
        self._is_running = False
        self._task: asyncio.Task | None = None

        # Initialize helper components (use database factory)
        self.detector = WorkflowCompletionDetector()
        self.notifier = PhaseGitHubNotifier(phase_queue_service)

        logger.info(
            f"[INIT] PhaseCoordinator initialized "
            f"(max_concurrent_adws={max_concurrent_adws}, event-driven mode)"
        )

    async def start(self):
        """Start the coordinator (event-driven mode, no polling)"""
        if self._is_running:
            logger.warning("[WARNING] PhaseCoordinator already running")
            return

        self._is_running = True
        logger.info("[START] PhaseCoordinator started (event-driven mode)")

        # Perform initial scan for ready phases on startup
        logger.info("[STARTUP] Performing initial scan for ready phases...")
        ready_phases = self.phase_queue_service.repository.find_ready_phases()

        if ready_phases:
            logger.info(f"[STARTUP] Found {len(ready_phases)} ready phase(s) to process")
            for phase in ready_phases:
                logger.info(
                    f"[STARTUP] Processing ready phase: queue_id={phase.queue_id}, "
                    f"feature_id={phase.feature_id}, phase={phase.phase_number}"
                )
                await self._launch_phase(phase.to_dict())
        else:
            logger.info("[STARTUP] No ready phases found")

    async def stop(self):
        """Stop the coordinator"""
        if not self._is_running:
            return

        self._is_running = False
        logger.info("[STOP] PhaseCoordinator stopped")

    async def handle_workflow_completion(self, event_data: dict):
        """
        Handle workflow completion event (main entry point).

        Called by WebSocket manager when workflow_completed event is broadcast.

        Args:
            event_data: {
                "queue_id": "1",
                "feature_id": 104,
                "phase_number": 1,
                "status": "completed" or "failed",
                "adw_id": "adw-abc123",
                "timestamp": "2025-12-13T10:30:00"
            }
        """
        try:
            queue_id = event_data.get("queue_id")
            feature_id = event_data.get("feature_id")
            phase_number = event_data.get("phase_number")
            status = event_data.get("status")
            adw_id = event_data.get("adw_id")

            logger.info(
                f"[EVENT] Workflow completion event received: "
                f"queue_id={queue_id}, feature_id={feature_id}, "
                f"phase={phase_number}, status={status}"
            )

            # Find newly ready phases (dependency resolution)
            ready_phases = self._find_newly_ready_phases(feature_id)

            if not ready_phases:
                logger.info(
                    f"[EVENT] No newly ready phases for feature #{feature_id}"
                )
                return

            # Get current running count (across ALL features)
            running_count = self._get_running_count()
            available_slots = max(0, self.max_concurrent_adws - running_count)

            logger.info(
                f"[EVENT] Found {len(ready_phases)} ready phases. "
                f"Running: {running_count}/{self.max_concurrent_adws}, "
                f"Available slots: {available_slots}"
            )

            # Launch phases in parallel (up to available slots)
            launched = 0
            for phase_row in ready_phases[:available_slots]:
                try:
                    await self._launch_phase(phase_row)
                    launched += 1
                except Exception as e:
                    logger.error(
                        f"[ERROR] Failed to launch phase {phase_row['phase_number']}: {e}"
                    )

            if launched > 0:
                logger.info(
                    f"[EVENT] Successfully launched {launched} phase(s) in parallel"
                )

            # Log queued phases (if any)
            queued_count = len(ready_phases) - launched
            if queued_count > 0:
                logger.info(
                    f"[EVENT] {queued_count} ready phase(s) queued "
                    f"(concurrency limit reached)"
                )

        except Exception as e:
            logger.error(f"[ERROR] handle_workflow_completion failed: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")

    def _find_newly_ready_phases(self, feature_id: int) -> list[dict]:
        """
        Find all phases that are now ready to execute.

        A phase is ready when:
        1. status = 'queued'
        2. ALL phases in depends_on_phases are 'completed'
        3. No concurrency check (handled by caller)

        Args:
            feature_id: Feature ID to check

        Returns:
            List of phase rows with queue_id, phase_number, depends_on_phases, phase_data
        """
        with self.phase_queue_service.repository.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all queued phases for this feature
            cursor.execute(
                """
                SELECT queue_id, phase_number, depends_on_phases, phase_data
                FROM phase_queue
                WHERE feature_id = %s AND status = 'queued'
                """,
                (feature_id,)
            )
            queued_phases = cursor.fetchall()

            ready_phases = []
            for phase in queued_phases:
                dependencies_json = phase["depends_on_phases"]

                # Parse dependencies (JSONB → Python list)
                if dependencies_json is None or dependencies_json == '[]':
                    dependencies = []
                else:
                    try:
                        if isinstance(dependencies_json, str):
                            dependencies = json.loads(dependencies_json)
                        elif isinstance(dependencies_json, list):
                            dependencies = dependencies_json
                        else:
                            dependencies = []
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"[WARN] Failed to parse depends_on_phases for "
                            f"phase {phase['phase_number']}: {dependencies_json}"
                        )
                        dependencies = []

                # No dependencies → always ready
                if not dependencies:
                    logger.debug(
                        f"[READY] Phase {phase['phase_number']} has no dependencies → READY"
                    )
                    ready_phases.append(phase)
                    continue

                # Check if ALL dependencies are completed
                all_complete = True
                for dep_phase_num in dependencies:
                    cursor.execute(
                        """
                        SELECT status FROM phase_queue
                        WHERE feature_id = %s AND phase_number = %s
                        """,
                        (feature_id, dep_phase_num)
                    )
                    dep_row = cursor.fetchone()

                    # Dependency not found OR not completed → block
                    if not dep_row or dep_row["status"] != "completed":
                        all_complete = False
                        logger.debug(
                            f"[BLOCKED] Phase {phase['phase_number']} waiting for "
                            f"Phase {dep_phase_num} (status: {dep_row['status'] if dep_row else 'NOT_FOUND'})"
                        )
                        break

                if all_complete:
                    logger.debug(
                        f"[READY] Phase {phase['phase_number']} dependencies met → READY"
                    )
                    ready_phases.append(phase)

            return ready_phases

    def _get_running_count(self) -> int:
        """
        Get count of currently running phases (across ALL features).

        Returns:
            Number of phases with status='running'
        """
        with self.phase_queue_service.repository.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM phase_queue
                WHERE status = 'running'
                """
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    async def _launch_phase(self, phase_row: dict):
        """
        Launch a single phase: create isolated issue + start ADW.

        Args:
            phase_row: Database row with queue_id, phase_number, depends_on_phases, phase_data
        """
        queue_id = phase_row["queue_id"]
        phase_number = phase_row["phase_number"]
        phase_data_json = phase_row["phase_data"]

        # Parse phase_data
        if isinstance(phase_data_json, str):
            phase_data = json.loads(phase_data_json)
        elif isinstance(phase_data_json, dict):
            phase_data = phase_data_json
        else:
            logger.error(f"[ERROR] Invalid phase_data type: {type(phase_data_json)}")
            return

        logger.info(f"[LAUNCH] Launching Phase {phase_number} (queue_id={queue_id})")

        # 1. Create isolated GitHub issue (if not exists)
        issue_number = await self._create_isolated_issue(phase_row)
        if not issue_number:
            logger.error(f"[ERROR] Failed to create issue for Phase {phase_number}")
            return

        # 2. Start ADW workflow
        await self._auto_start_phase(queue_id, issue_number, phase_data)

    async def _create_isolated_issue(self, phase_row: dict) -> int | None:
        """
        Create isolated GitHub issue (NO parent).

        Args:
            phase_row: Database row with queue_id, phase_number, phase_data

        Returns:
            Issue number if created, None if failed
        """
        if not self.github_poster:
            logger.warning("[WARN] github_poster not configured, cannot create issue")
            return None

        try:
            queue_id = phase_row["queue_id"]
            phase_number = phase_row["phase_number"]

            # Parse phase_data
            phase_data_json = phase_row["phase_data"]
            if isinstance(phase_data_json, str):
                phase_data = json.loads(phase_data_json)
            elif isinstance(phase_data_json, dict):
                phase_data = phase_data_json
            else:
                logger.error(f"[ERROR] Invalid phase_data type: {type(phase_data_json)}")
                return None

            # Get feature info
            feature_id = self._get_feature_id_for_queue(queue_id)
            if not feature_id:
                logger.error(f"[ERROR] Failed to get feature_id for queue_id={queue_id}")
                return None

            feature_title = self._get_feature_title(feature_id)
            total_phases = phase_data.get("total_phases", "?")
            phase_title = phase_data.get("title", f"Phase {phase_number}")
            prompt_content = phase_data.get("content", "")
            external_docs = phase_data.get("externalDocs", [])

            # Build issue body (isolated, no parent reference)
            issue_title = f"{phase_title}"
            issue_body = f"""# {phase_title}

**Feature**: {feature_title} (planned_features #{feature_id})
**Phase**: {phase_number} of {total_phases}

## Description

{prompt_content}
"""

            if external_docs:
                issue_body += f"""
## Referenced Documents

{chr(10).join(f'- `{doc}`' for doc in external_docs)}
"""

            issue_body += """

---
**Tracking**: See Panel 5 for full feature progress
"""

            # Create GitHub issue (NO parent_issue parameter)
            from core.data_models import GitHubIssue

            github_issue = GitHubIssue(
                title=issue_title,
                body=issue_body,
                labels=[f"feature-{feature_id}", f"phase-{phase_number}", "multi-phase"],
                classification="feature",
                workflow="adw_sdlc_complete_iso",
                model_set="base"
            )

            issue_number = self.github_poster.post_issue(github_issue, confirm=False)
            logger.info(
                f"[CREATED] Isolated issue #{issue_number} for "
                f"Feature #{feature_id} Phase {phase_number}"
            )

            # Update phase_queue with issue number
            self.phase_queue_service.update_issue_number(queue_id, issue_number)

            return issue_number

        except Exception as e:
            logger.error(f"[ERROR] Failed to create isolated issue: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return None

    def _get_feature_id_for_queue(self, queue_id: str) -> int | None:
        """Get feature_id for a queue_id"""
        with self.phase_queue_service.repository.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT feature_id FROM phase_queue WHERE queue_id = %s",
                (queue_id,)
            )
            row = cursor.fetchone()
            return row["feature_id"] if row else None

    def _get_feature_title(self, feature_id: int) -> str:
        """Get feature title from planned_features table"""
        with self.phase_queue_service.repository.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM planned_features WHERE id = %s",
                (feature_id,)
            )
            row = cursor.fetchone()
            return row["title"] if row else f"Feature #{feature_id}"

    async def _auto_start_phase(self, queue_id: str, issue_number: int, phase_data: dict):
        """
        Start ADW workflow for a phase.

        Args:
            queue_id: Queue ID
            issue_number: GitHub issue number
            phase_data: Phase metadata dict
        """
        try:
            import os
            import subprocess
            import uuid

            from routes.queue_routes import determine_workflow_for_phase

            # Generate ADW ID
            adw_id = f"adw-{uuid.uuid4().hex[:8]}"

            # Determine workflow
            workflow, model_set = determine_workflow_for_phase(phase_data)

            # Build command
            # __file__ is in app/server/services/phase_coordination/phase_coordinator.py
            # Go up: phase_coordination -> services -> server -> app -> repo_root
            services_dir = os.path.dirname(os.path.abspath(__file__))  # services/phase_coordination
            services_parent = os.path.dirname(services_dir)  # services
            server_dir = os.path.dirname(services_parent)  # app/server
            app_dir = os.path.dirname(server_dir)  # app
            repo_root = os.path.dirname(app_dir)  # repo root

            # Validate repo_root exists
            if not os.path.exists(repo_root):
                logger.error(f"[AUTO-START] Repository root not found: {repo_root}")
                return

            adws_dir = os.path.join(repo_root, "adws")
            workflow_script = os.path.join(adws_dir, f"{workflow}.py")

            if not os.path.exists(workflow_script):
                logger.error(f"[AUTO-START] Workflow script not found: {workflow_script}")
                return

            cmd = ["uv", "run", workflow_script, str(issue_number), adw_id]

            logger.info(
                f"[AUTO-START] Launching {workflow} "
                f"(issue #{issue_number}, adw_id: {adw_id})"
            )

            # Mark phase as running BEFORE launching subprocess (prevent race condition)
            self.phase_queue_service.update_status(queue_id, "running", adw_id=adw_id)

            # Prepare environment with GitHub token
            env = os.environ.copy()
            try:
                # Get GitHub token from gh CLI
                github_token = subprocess.check_output(
                    ["gh", "auth", "token"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                env["GITHUB_TOKEN"] = github_token
                logger.info("[AUTO-START] GitHub token loaded from gh CLI")
            except (subprocess.CalledProcessError, FileNotFoundError) as token_error:
                logger.warning(
                    f"[AUTO-START] Could not get GitHub token: {token_error}. "
                    "ADW may fail authentication."
                )

            # Launch workflow in background
            try:
                subprocess.Popen(
                    cmd,
                    cwd=repo_root,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,  # Don't capture - let it go to parent logs
                    stderr=subprocess.DEVNULL,
                    env=env,  # Pass environment with GITHUB_TOKEN
                )
                logger.info(
                    f"[AUTO-START] Successfully started workflow "
                    f"(issue #{issue_number}, adw_id: {adw_id})"
                )
            except (FileNotFoundError, PermissionError, OSError) as subprocess_error:
                # Subprocess failed to launch - revert status back to queued
                logger.error(
                    f"[AUTO-START] Subprocess launch failed: "
                    f"{type(subprocess_error).__name__}: {str(subprocess_error)}"
                )
                self.phase_queue_service.update_status(queue_id, "queued", adw_id=None)

        except Exception as e:
            logger.error(f"[AUTO-START] Failed to start phase: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")

    async def _broadcast_queue_update(self, queue_id: str, status: str, feature_id: int):
        """
        Broadcast WebSocket event for queue update.

        Args:
            queue_id: Queue ID that was updated
            status: New status (completed, failed, blocked, ready, etc.)
            feature_id: Feature ID (references planned_features.id)
        """
        if not self.websocket_manager:
            return

        try:
            event = {
                "type": "queue_update",
                "queue_id": queue_id,
                "status": status,
                "feature_id": feature_id,
                "timestamp": datetime.now().isoformat()
            }

            await self.websocket_manager.broadcast(event)
            logger.debug(f"[WS] Broadcast queue_update: {queue_id} → {status}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to broadcast WebSocket event: {str(e)}")

    def mark_phase_running(self, queue_id: str):
        """
        Mark a phase as running when workflow starts.

        This should be called by the webhook trigger when starting a workflow.

        Args:
            queue_id: Queue ID to mark as running
        """
        try:
            self.phase_queue_service.update_status(queue_id, "running")
            logger.info(f"[RUNNING] Phase marked as running (queue_id: {queue_id})")
        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase as running: {str(e)}")

    def get_ready_phases(self):
        """
        Get all phases with status='ready'.

        Returns:
            List of PhaseQueueItem objects
        """
        try:
            items = self.phase_queue_service.get_all_queued()
            return [item for item in items if item.status == "ready"]
        except Exception as e:
            logger.error(f"[ERROR] Failed to get ready phases: {str(e)}")
            return []

    # Legacy wrapper methods for backwards compatibility with tests
    def _get_workflow_status(self, issue_number: int) -> str | None:
        """
        Get workflow status from workflow_history by issue number.

        Wrapper method for backwards compatibility with tests.

        Args:
            issue_number: GitHub issue number

        Returns:
            'completed', 'failed', 'running', 'pending', or None if not found
        """
        return self.detector.get_workflow_status(issue_number)

    def _get_workflow_error(self, issue_number: int) -> str | None:
        """
        Get error message from workflow_history.

        Wrapper method for backwards compatibility with tests.

        Args:
            issue_number: GitHub issue number

        Returns:
            Error message string or None
        """
        return self.detector.get_workflow_error(issue_number)
