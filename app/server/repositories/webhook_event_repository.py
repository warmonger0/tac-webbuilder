"""Repository for webhook event deduplication."""
from typing import Optional
from datetime import datetime, timedelta
import logging

from database import get_database_adapter

logger = logging.getLogger(__name__)


class WebhookEventRepository:
    """Manages webhook event tracking for idempotency."""

    def __init__(self):
        self.adapter = get_database_adapter()

    def is_duplicate(
        self,
        webhook_id: str,
        window_seconds: int = 30
    ) -> bool:
        """Check if webhook was already processed recently.

        Args:
            webhook_id: Unique identifier for webhook event
            window_seconds: Deduplication window in seconds

        Returns:
            True if duplicate (already processed), False otherwise
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id FROM webhook_events
                WHERE webhook_id = %s
                  AND received_at > %s
                LIMIT 1
            """

            cursor.execute(query, (webhook_id, cutoff_time))
            result = cursor.fetchone()

            return result is not None

    def record_webhook(
        self,
        webhook_id: str,
        webhook_type: str,
        adw_id: Optional[str] = None,
        issue_number: Optional[int] = None
    ) -> int:
        """Record webhook event.

        Args:
            webhook_id: Unique identifier for webhook event
            webhook_type: Type of webhook ('github_issue', 'workflow_complete', etc.)
            adw_id: Associated ADW ID (if applicable)
            issue_number: Associated issue number (if applicable)

        Returns:
            Event ID (-1 if duplicate)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO webhook_events
                    (webhook_id, webhook_type, adw_id, issue_number, processed)
                VALUES (%s, %s, %s, %s, TRUE)
                ON CONFLICT (webhook_id) DO NOTHING
                RETURNING id
            """

            cursor.execute(
                query,
                (webhook_id, webhook_type, adw_id, issue_number)
            )

            result = cursor.fetchone()
            conn.commit()

            if result:
                # Handle both dict-like (PostgreSQL) and tuple (SQLite) results
                return result['id'] if isinstance(result, dict) else result[0]
            else:
                # Already exists (conflict)
                logger.debug(f"[WEBHOOK] Duplicate webhook_id: {webhook_id}")
                return -1

    def cleanup_old_events(self, days: int = 7) -> int:
        """Remove webhook events older than specified days.

        Args:
            days: Number of days to retain

        Returns:
            Number of events deleted
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = "DELETE FROM webhook_events WHERE received_at < %s"
            cursor.execute(query, (cutoff_time,))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"[WEBHOOK] Cleaned up {deleted_count} old webhook events")
            return deleted_count
