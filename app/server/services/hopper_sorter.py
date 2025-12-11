"""
HopperSorter - Deterministic phase selection for the queue.

Implements "belt feed" logic to pick the next phase(s) to execute.
Supports both sequential (one at a time) and parallel (multiple parents) execution.

Key Features:
- Deterministic ordering: priority → queue_position → parent_issue
- Parent grouping: Can run phases from different parents in parallel
- FIFO within priority: Fair ordering for same-priority phases
- Index-optimized queries: Fast even with large queues
"""

import logging

from database import get_database_adapter
from database.sqlite_adapter import SQLiteAdapter
from models.phase_queue_item import PhaseQueueItem

logger = logging.getLogger(__name__)


class HopperSorter:
    """
    Sorts and selects next phase(s) from hopper queue.

    Provides deterministic, priority-based selection of ready phases.
    """

    # Priority levels (lower number = higher priority)
    PRIORITY_URGENT = 10
    PRIORITY_HIGH = 20
    PRIORITY_NORMAL = 50  # Default
    PRIORITY_LOW = 70
    PRIORITY_BACKGROUND = 90

    def __init__(self, db_path: str | None = None):
        """
        Initialize HopperSorter.

        Args:
            db_path: Optional path to SQLite database. If provided, uses SQLiteAdapter with this path.
                    Otherwise uses database adapter from factory (SQLite or PostgreSQL based on DB_TYPE env var).
        """
        if db_path:
            self.adapter = SQLiteAdapter(db_path=db_path)
            logger.info(f"[INIT] HopperSorter initialized with SQLite database: {db_path}")
        else:
            self.adapter = get_database_adapter()
            logger.info("[INIT] HopperSorter initialized")

    def get_next_phase_1(self) -> PhaseQueueItem | None:
        """
        Get the next Phase 1 to start from the hopper (deterministic).

        This is the "belt feed" function that picks which parent issue
        should have its Phase 1 executed next.

        Ordering:
        1. Priority (urgent before normal before low)
        2. Queue position (FIFO within same priority)
        3. Parent issue (tiebreaker for simultaneous enqueues)

        Returns:
            Next Phase 1 to start, or None if none ready

        Example:
            >>> sorter = HopperSorter()
            >>> next_phase = sorter.get_next_phase_1()
            >>> if next_phase:
            ...     print(f"Start parent #{next_phase.parent_issue}")
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE status = 'ready'
                      AND phase_number = 1
                      AND issue_number IS NULL
                    ORDER BY
                      priority ASC,         -- Lower priority number = higher urgency
                      queue_position ASC,   -- FIFO within same priority
                      parent_issue ASC      -- Tiebreaker
                    LIMIT 1
                    """,
                )
                row = cursor.fetchone()

            if row:
                phase = PhaseQueueItem.from_db_row(row)
                logger.info(
                    f"[SORTER] Next Phase 1: parent #{phase.parent_issue} "
                    f"(priority={phase.priority}, position={phase.queue_position})"
                )
                return phase
            else:
                logger.debug("[SORTER] No ready Phase 1 in hopper")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to get next Phase 1: {str(e)}")
            raise

    def get_next_phases_parallel(self, max_parallel: int = 5) -> list[PhaseQueueItem]:
        """
        Get multiple Phase 1s that can run in parallel.

        Returns up to max_parallel Phase 1s from DIFFERENT parent issues,
        allowing concurrent workflow execution across different features.

        Ordering:
        1. Priority (higher priority phases first)
        2. Queue position (FIFO within priority)

        Args:
            max_parallel: Maximum number of parallel workflows to start

        Returns:
            List of Phase 1 items to start (from different parents)

        Example:
            >>> sorter = HopperSorter()
            >>> phases = sorter.get_next_phases_parallel(max_parallel=3)
            >>> for phase in phases:
            ...     launch_workflow(phase)  # Start 3 workflows in parallel
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE status = 'ready'
                      AND phase_number = 1
                      AND issue_number IS NULL
                    ORDER BY
                      priority ASC,
                      queue_position ASC,
                      parent_issue ASC
                    LIMIT ?
                    """,
                    (max_parallel,)
                )
                rows = cursor.fetchall()

            phases = [PhaseQueueItem.from_db_row(row) for row in rows]

            if phases:
                parent_list = ", ".join(f"#{p.parent_issue}" for p in phases)
                logger.info(
                    f"[SORTER] Next {len(phases)} Phase 1s for parallel execution: {parent_list}"
                )
            else:
                logger.debug("[SORTER] No ready Phase 1s for parallel execution")

            return phases

        except Exception as e:
            logger.error(f"[ERROR] Failed to get parallel Phase 1s: {str(e)}")
            raise

    def get_running_parent_count(self) -> int:
        """
        Get count of parent issues that currently have running phases.

        Useful for limiting parallel execution based on system capacity.

        Returns:
            Number of distinct parent issues with running phases
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT parent_issue)
                    FROM phase_queue
                    WHERE status = 'running'
                    """
                )
                count = cursor.fetchone()[0]

            logger.debug(f"[SORTER] Currently {count} parent(s) running")
            return count

        except Exception as e:
            logger.error(f"[ERROR] Failed to get running parent count: {str(e)}")
            return 0

    def can_start_more_parents(self, max_concurrent: int = 5) -> bool:
        """
        Check if we can start more parent workflows based on concurrency limit.

        Args:
            max_concurrent: Maximum number of concurrent parent workflows

        Returns:
            True if we can start more parents, False otherwise
        """
        running = self.get_running_parent_count()
        can_start = running < max_concurrent

        logger.debug(
            f"[SORTER] Concurrency check: {running}/{max_concurrent} parents running "
            f"→ {'Can' if can_start else 'Cannot'} start more"
        )

        return can_start

    def get_priority_stats(self) -> dict:
        """
        Get statistics about phases by priority level.

        Returns:
            Dict with counts per priority level and overall stats

        Example:
            >>> sorter = HopperSorter()
            >>> stats = sorter.get_priority_stats()
            >>> print(f"Urgent phases: {stats['by_priority'][10]}")
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                      priority,
                      COUNT(*) as count,
                      SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) as ready_count
                    FROM phase_queue
                    WHERE phase_number = 1
                    GROUP BY priority
                    ORDER BY priority ASC
                    """
                )
                rows = cursor.fetchall()

            stats = {
                "by_priority": {},
                "total_phase_1s": 0,
                "ready_phase_1s": 0
            }

            for row in rows:
                priority, count, ready_count = row
                stats["by_priority"][priority] = {
                    "total": count,
                    "ready": ready_count
                }
                stats["total_phase_1s"] += count
                stats["ready_phase_1s"] += ready_count

            logger.debug(f"[SORTER] Priority stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"[ERROR] Failed to get priority stats: {str(e)}")
            return {"by_priority": {}, "total_phase_1s": 0, "ready_phase_1s": 0}


def get_priority_name(priority: int) -> str:
    """
    Get human-readable priority name.

    Args:
        priority: Priority value (10-90)

    Returns:
        Priority name (e.g., "urgent", "normal")
    """
    if priority <= 10:
        return "urgent"
    elif priority <= 20:
        return "high"
    elif priority <= 50:
        return "normal"
    elif priority <= 70:
        return "low"
    else:
        return "background"
