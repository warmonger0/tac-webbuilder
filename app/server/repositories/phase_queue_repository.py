"""
PhaseQueueRepository

Handles all database operations for the phase queue.
Separates database access from business logic (Repository Pattern).
"""

import json
import logging
import traceback
from datetime import datetime

from database import get_database_adapter
from database.sqlite_adapter import SQLiteAdapter
from models.phase_queue_item import PhaseQueueItem

logger = logging.getLogger(__name__)


class PhaseQueueRepository:
    """Repository for phase queue database operations"""

    def __init__(self, db_path: str | None = None):
        """
        Initialize repository.

        Args:
            db_path: Optional path to SQLite database. If provided, uses SQLiteAdapter with this path.
                    Otherwise uses database adapter from factory (SQLite or PostgreSQL based on DB_TYPE env var).
        """
        if db_path:
            self.adapter = SQLiteAdapter(db_path=db_path)
        else:
            self.adapter = get_database_adapter()

    def create(self, item: PhaseQueueItem) -> PhaseQueueItem:
        """
        Create a new phase queue item.

        Automatically sets:
        - queue_position (based on ROWID for FIFO ordering)
        - priority (from item, default 50)
        - ready_timestamp (if status is 'ready')

        Args:
            item: PhaseQueueItem to create

        Returns:
            Created PhaseQueueItem with queue_id populated

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.adapter.get_connection() as conn:
                # Get next queue_position (max + 1)
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(MAX(queue_position), 0) + 1 AS next_pos FROM phase_queue")
                row = cursor.fetchone()
                # Handle both tuple (SQLite) and dict-like (PostgreSQL) row formats
                next_position = row['next_pos'] if isinstance(row, dict) else row[0]

                ph = self.adapter.placeholder()

                # Serialize depends_on_phases as JSON
                depends_on_phases_json = json.dumps(item.depends_on_phases)

                cursor.execute(
                    f"""
                    INSERT INTO phase_queue (
                        queue_id, feature_id, phase_number, issue_number, status, current_phase,
                        depends_on_phases, phase_data, created_at, updated_at,
                        priority, queue_position, ready_timestamp, adw_id
                    )
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    """,
                    (
                        item.queue_id,
                        item.feature_id,
                        item.phase_number,
                        item.issue_number,
                        item.status,
                        getattr(item, 'current_phase', 'init'),
                        depends_on_phases_json,
                        json.dumps(item.phase_data),
                        item.created_at,
                        item.updated_at,
                        getattr(item, 'priority', 50),  # Default to normal priority
                        next_position,
                        item.created_at if item.status == 'ready' else None,
                        item.adw_id,
                    ),
                )
                return item
        except Exception as e:
            logger.error(f"[ERROR] Failed to create phase: {str(e)}")
            logger.error(f"[ERROR] Exception type: {type(e).__name__}")
            logger.error(f"[ERROR] Exception repr: {repr(e)}")
            logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise

    def get_by_id(self, queue_id: str) -> PhaseQueueItem | None:
        """
        Get phase queue item by queue_id.

        Args:
            queue_id: Primary key to search for

        Returns:
            PhaseQueueItem if found, None otherwise
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT * FROM phase_queue WHERE queue_id = {ph}",
                    (queue_id,)
                )
                row = cursor.fetchone()

            return PhaseQueueItem.from_db_row(row) if row else None

        except Exception as e:
            logger.error(f"[ERROR] Failed to get phase by ID: {str(e)}")
            raise

    def find_by_adw_id(self, adw_id: str) -> PhaseQueueItem | None:
        """
        Find phase queue item by ADW ID.

        Args:
            adw_id: ADW workflow identifier

        Returns:
            PhaseQueueItem if found, None otherwise
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT * FROM phase_queue WHERE adw_id = {ph} LIMIT 1",
                    (adw_id,)
                )
                row = cursor.fetchone()

            return PhaseQueueItem.from_db_row(row) if row else None

        except Exception as e:
            logger.error(f"[ERROR] Failed to find phase by ADW ID: {str(e)}")
            raise

    def get_all_by_feature_id(self, feature_id: int, limit: int = 100) -> list[PhaseQueueItem]:
        """
        Get all phases for a feature.

        Args:
            feature_id: Feature ID to filter by (from planned_features table)
            limit: Maximum records to return

        Returns:
            List of matching phase queue items ordered by phase number
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT * FROM phase_queue
                    WHERE feature_id = {ph}
                    ORDER BY phase_number ASC
                    LIMIT {ph}
                    """,
                    (feature_id, limit)
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to get phases by feature_id: {str(e)}")
            raise

    def find_phases_depending_on(self, feature_id: int, phase_number: int) -> list[PhaseQueueItem]:
        """
        Find all phases that depend on a specific phase number.

        This is optimized for finding the next phases in a workflow sequence
        instead of fetching all phases and looping (N+1 pattern).

        Note: depends_on_phases is a JSONB array, so we need to check if
        phase_number exists in that array.

        Args:
            feature_id: Feature ID to filter by
            phase_number: Phase number that target phases depend on

        Returns:
            List of PhaseQueueItems that depend on the specified phase
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()

                # Query depends on database type (PostgreSQL vs SQLite)
                db_type = self.adapter.db_type if hasattr(self.adapter, 'db_type') else 'sqlite'

                if db_type == 'postgresql':
                    # PostgreSQL: Use JSONB contains operator
                    cursor.execute(
                        f"""
                        SELECT * FROM phase_queue
                        WHERE feature_id = {ph}
                        AND depends_on_phases @> {ph}::jsonb
                        """,
                        (feature_id, json.dumps([phase_number]))
                    )
                else:
                    # SQLite: Parse JSON and check array contains
                    cursor.execute(
                        f"""
                        SELECT * FROM phase_queue
                        WHERE feature_id = {ph}
                        """,
                        (feature_id,)
                    )
                    # Filter in Python for SQLite (less efficient but works)
                    rows = cursor.fetchall()
                    filtered_rows = []
                    for row in rows:
                        depends_on_phases_raw = row.get("depends_on_phases", "[]")
                        depends_on_phases = json.loads(depends_on_phases_raw) if isinstance(depends_on_phases_raw, str) else depends_on_phases_raw
                        if phase_number in depends_on_phases:
                            filtered_rows.append(row)
                    return [PhaseQueueItem.from_db_row(row) for row in filtered_rows]

                rows = cursor.fetchall()
                return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to find phases depending on phase: {str(e)}")
            raise

    def find_ready_phases(self) -> list[PhaseQueueItem]:
        """
        Find all phases that are ready for execution.

        Returns:
            List of PhaseQueueItems with status='ready' and no issue_number
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE status = 'ready' AND issue_number IS NULL
                    ORDER BY feature_id ASC, phase_number ASC
                    """
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to find ready phases: {str(e)}")
            raise

    def get_all(self, limit: int = 100, offset: int = 0) -> list[PhaseQueueItem]:
        """
        Get all phase queue items with pagination.

        Args:
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of phase queue items ordered by feature_id and phase number
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()
                cursor.execute(
                    f"""
                    SELECT * FROM phase_queue
                    ORDER BY feature_id ASC, phase_number ASC
                    LIMIT {ph} OFFSET {ph}
                    """,
                    (limit, offset)
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to get all phases: {str(e)}")
            raise

    def update_status(self, queue_id: str, status: str, adw_id: str | None = None) -> bool:
        """
        Update phase status and optionally set ADW ID.

        Also sets timestamps:
        - ready_timestamp when transitioning to 'ready'
        - started_timestamp when transitioning to 'running'

        Args:
            queue_id: Queue ID to update
            status: New status
            adw_id: Optional ADW ID to associate with the phase

        Returns:
            True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                now_fn = self.adapter.now_function()

                # Build dynamic SQL based on status transitions
                updates = [f"status = {ph}", f"updated_at = {ph}"]
                params = [status, datetime.now().isoformat()]

                if adw_id is not None:
                    updates.append(f"adw_id = {ph}")
                    params.append(adw_id)

                if status == "ready":
                    updates.append(f"ready_timestamp = {now_fn}")
                elif status == "running":
                    updates.append(f"started_timestamp = {now_fn}")

                params.append(queue_id)

                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE phase_queue
                    SET {', '.join(updates)}
                    WHERE queue_id = {ph}
                    """,
                    tuple(params),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update status: {str(e)}")
            raise

    def update_phase(self, queue_id: str, current_phase: str, status: str) -> bool:
        """
        Update current phase and status (SSoT coordination state).

        Args:
            queue_id: Queue ID to update
            current_phase: New phase name (e.g., 'plan', 'test', 'ship')
            status: New status (e.g., 'running', 'completed', 'failed')

        Returns:
            True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()

                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE phase_queue
                    SET current_phase = {ph},
                        status = {ph},
                        updated_at = {ph}
                    WHERE queue_id = {ph}
                    """,
                    (current_phase, status, datetime.now().isoformat(), queue_id),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update phase: {str(e)}")
            raise

    def update_issue_number(self, queue_id: str, issue_number: int) -> bool:
        """
        Update GitHub issue number for a phase.

        Args:
            queue_id: Queue ID to update
            issue_number: GitHub issue number

        Returns:
            True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE phase_queue
                    SET issue_number = {ph}, updated_at = {ph}
                    WHERE queue_id = {ph}
                    """,
                    (issue_number, datetime.now().isoformat(), queue_id),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update issue number: {str(e)}")
            raise

    def update_error_message(self, queue_id: str, error_message: str) -> bool:
        """
        Update error message for a phase.

        Args:
            queue_id: Queue ID to update
            error_message: Error message

        Returns:
            True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE phase_queue
                    SET error_message = {ph}, updated_at = {ph}
                    WHERE queue_id = {ph}
                    """,
                    (error_message, datetime.now().isoformat(), queue_id),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update error message: {str(e)}")
            raise

    def delete(self, queue_id: str) -> bool:
        """
        Delete phase queue item by queue_id.

        Args:
            queue_id: Primary key of item to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM phase_queue WHERE queue_id = {ph}",
                    (queue_id,)
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to delete phase: {str(e)}")
            raise

    def get_config_value(self, config_key: str) -> str | None:
        """
        Get a configuration value from queue_config table.

        Args:
            config_key: Configuration key to retrieve

        Returns:
            Configuration value or None if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT config_value FROM queue_config WHERE config_key = {ph}",
                    (config_key,)
                )
                row = cursor.fetchone()
                # Handle both tuple (SQLite) and dict (PostgreSQL RealDictCursor) formats
                if row:
                    return row["config_value"] if isinstance(row, dict) else row[0]
                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to get config value: {str(e)}")
            raise

    def set_config_value(self, config_key: str, config_value: str) -> None:
        """
        Set a configuration value in queue_config table.

        Args:
            config_key: Configuration key to set
            config_value: Value to set

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    INSERT INTO queue_config (config_key, config_value, updated_at)
                    VALUES ({ph}, {ph}, {ph})
                    ON CONFLICT(config_key) DO UPDATE SET
                        config_value = excluded.config_value,
                        updated_at = excluded.updated_at
                    """,
                    (config_key, config_value, datetime.now().isoformat()),
                )

        except Exception as e:
            logger.error(f"[ERROR] Failed to set config value: {str(e)}")
            raise

    def try_acquire_workflow_lock(self, feature_id: int, adw_id: str) -> bool:
        """
        Try to acquire exclusive workflow lock for a feature.

        Prevents multiple concurrent workflows on the same issue by checking
        for existing active workflows before allowing a new one to start.

        Args:
            feature_id: GitHub issue number to lock
            adw_id: ADW workflow ID requesting the lock

        Returns:
            True if lock acquired (safe to proceed), False if another workflow is active

        Note:
            This is a "soft lock" - it checks state but doesn't create a database lock.
            The actual lock is enforced by creating a phase_queue entry with status 'running'.
        """
        try:
            logger.info(f"Attempting to acquire workflow lock for feature {feature_id} (ADW: {adw_id})")

            # Get all workflows for this feature
            existing_workflows = self.get_all_by_feature_id(feature_id)

            # =============================================================================
            # SCHEMA CONSTRAINT: phase_queue.status
            # =============================================================================
            # ALLOWED: 'queued', 'ready', 'running', 'completed', 'blocked', 'failed'
            # FORBIDDEN: 'pending', 'planned', 'building', 'linting', 'testing', etc.
            # NOTE: Phase names (building/linting/etc) are stored in phase_data, NOT status!
            # =============================================================================
            # Check for active workflows (not completed, failed, or blocked)
            active_statuses = ["queued", "ready", "running"]

            active_workflows = [
                w for w in existing_workflows
                if w.status in active_statuses and w.adw_id != adw_id
            ]

            if active_workflows:
                active = active_workflows[0]
                logger.warning(
                    f"Workflow lock denied: Feature {feature_id} already has active workflow "
                    f"(ADW: {active.adw_id}, Phase: {active.phase_name}, Status: {active.status})"
                )
                return False

            logger.info(f"Workflow lock acquired for feature {feature_id} (ADW: {adw_id})")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to check workflow lock: {str(e)}")
            # On error, allow workflow to proceed (fail-open for safety)
            logger.warning("Workflow lock check failed, allowing workflow to proceed")
            return True

    def release_workflow_lock(self, feature_id: int, adw_id: str) -> None:
        """
        Release workflow lock for a feature.

        Note: In practice, the lock is released by updating phase_queue status
        to a terminal state (completed, failed, cancelled). This method is
        provided for explicit lock management if needed.

        Args:
            feature_id: GitHub issue number to unlock
            adw_id: ADW workflow ID releasing the lock
        """
        try:
            logger.info(f"Releasing workflow lock for feature {feature_id} (ADW: {adw_id})")

            # Get workflows for this ADW
            workflows = self.get_all_by_feature_id(feature_id)
            adw_workflows = [w for w in workflows if w.adw_id == adw_id]

            if not adw_workflows:
                logger.warning(f"No workflows found for ADW {adw_id} on feature {feature_id}")
                return

            # Update all this ADW's workflows to completed/failed
            # (This is normally done by phase completion, but we provide explicit release)
            for workflow in adw_workflows:
                if workflow.status not in ["completed", "failed", "cancelled"]:
                    logger.info(f"Setting workflow {workflow.queue_id} to completed state for lock release")
                    self.update_status(str(workflow.queue_id), "completed")

            logger.info(f"Workflow lock released for feature {feature_id} (ADW: {adw_id})")

        except Exception as e:
            logger.error(f"[ERROR] Failed to release workflow lock: {str(e)}")
            # Don't raise - lock release failure shouldn't block workflow
