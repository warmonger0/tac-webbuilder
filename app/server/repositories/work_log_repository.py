"""
Work Log Repository

Handles database operations for work log entries.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from core.models.work_log import WorkLogEntry, WorkLogEntryCreate
from database.factory import get_database_adapter

logger = logging.getLogger(__name__)


class WorkLogRepository:
    """Repository for work log database operations"""

    def __init__(self):
        self.adapter = get_database_adapter()

    def create_entry(self, entry: WorkLogEntryCreate) -> WorkLogEntry:
        """
        Create a new work log entry.

        Args:
            entry: Work log entry data

        Returns:
            Created WorkLogEntry with ID

        Raises:
            ValueError: If summary exceeds 280 characters
            Exception: If database operation fails
        """
        if len(entry.summary) > 280:
            raise ValueError("Summary must be at most 280 characters")

        ph = self.adapter.placeholder()
        db_type = self.adapter.get_db_type()

        # SQLite doesn't support RETURNING clause
        if db_type == "sqlite":
            query = f"""
                INSERT INTO work_log (session_id, summary, chat_file_link, issue_number, workflow_id, tags, timestamp)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
            """
        else:
            query = f"""
                INSERT INTO work_log (session_id, summary, chat_file_link, issue_number, workflow_id, tags, timestamp)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                RETURNING id, timestamp, created_at
            """

        tags_json = json.dumps(entry.tags) if entry.tags else "[]"

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        entry.session_id,
                        entry.summary,
                        entry.chat_file_link,
                        entry.issue_number,
                        entry.workflow_id,
                        tags_json,
                    ),
                )
                conn.commit()

                if db_type == "sqlite":
                    # SQLite: Use lastrowid and fetch the created row
                    entry_id = cursor.lastrowid
                    cursor.execute(
                        f"SELECT id, timestamp, created_at FROM work_log WHERE id = {ph}",
                        (entry_id,)
                    )
                    result = cursor.fetchone()
                    timestamp = result[1]
                    created_at = result[2]
                else:
                    # PostgreSQL: Use RETURNING clause
                    result = cursor.fetchone()
                    entry_id = result[0]
                    timestamp = result[1]
                    created_at = result[2]

                logger.info(f"Created work log entry {entry_id} for session {entry.session_id}")

                return WorkLogEntry(
                    id=entry_id,
                    timestamp=timestamp,
                    session_id=entry.session_id,
                    summary=entry.summary,
                    chat_file_link=entry.chat_file_link,
                    issue_number=entry.issue_number,
                    workflow_id=entry.workflow_id,
                    tags=entry.tags,
                    created_at=created_at,
                )
        except Exception as e:
            logger.error(f"Failed to create work log entry: {e}")
            raise

    def get_all(self, limit: int = 50, offset: int = 0) -> List[WorkLogEntry]:
        """
        Get all work log entries with pagination.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of WorkLogEntry objects
        """
        ph = self.adapter.placeholder()
        query = f"""
            SELECT id, timestamp, session_id, summary, chat_file_link, issue_number, workflow_id, tags, created_at
            FROM work_log
            ORDER BY timestamp DESC
            LIMIT {ph} OFFSET {ph}
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()

                entries = []
                for row in rows:
                    tags = json.loads(row[7]) if row[7] else []
                    entries.append(
                        WorkLogEntry(
                            id=row[0],
                            timestamp=row[1],
                            session_id=row[2],
                            summary=row[3],
                            chat_file_link=row[4],
                            issue_number=row[5],
                            workflow_id=row[6],
                            tags=tags,
                            created_at=row[8],
                        )
                    )

                logger.info(f"Retrieved {len(entries)} work log entries (limit={limit}, offset={offset})")
                return entries
        except Exception as e:
            logger.error(f"Failed to get work log entries: {e}")
            raise

    def get_by_session(self, session_id: str) -> List[WorkLogEntry]:
        """
        Get all work log entries for a specific session.

        Args:
            session_id: Session ID to filter by

        Returns:
            List of WorkLogEntry objects for the session
        """
        ph = self.adapter.placeholder()
        query = f"""
            SELECT id, timestamp, session_id, summary, chat_file_link, issue_number, workflow_id, tags, created_at
            FROM work_log
            WHERE session_id = {ph}
            ORDER BY timestamp DESC
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (session_id,))
                rows = cursor.fetchall()

                entries = []
                for row in rows:
                    tags = json.loads(row[7]) if row[7] else []
                    entries.append(
                        WorkLogEntry(
                            id=row[0],
                            timestamp=row[1],
                            session_id=row[2],
                            summary=row[3],
                            chat_file_link=row[4],
                            issue_number=row[5],
                            workflow_id=row[6],
                            tags=tags,
                            created_at=row[8],
                        )
                    )

                logger.info(f"Retrieved {len(entries)} work log entries for session {session_id}")
                return entries
        except Exception as e:
            logger.error(f"Failed to get work log entries for session {session_id}: {e}")
            raise

    def get_count(self) -> int:
        """Get total count of work log entries"""
        query = "SELECT COUNT(*) AS count FROM work_log"

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                # Access by column name since Row objects don't support integer indexing
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Failed to get work log count: {e}")
            raise

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete a work log entry.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If database operation fails
        """
        ph = self.adapter.placeholder()
        query = f"DELETE FROM work_log WHERE id = {ph}"

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (entry_id,))
                conn.commit()

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted work log entry {entry_id}")
                else:
                    logger.warning(f"Work log entry {entry_id} not found for deletion")

                return deleted
        except Exception as e:
            logger.error(f"Failed to delete work log entry {entry_id}: {e}")
            raise
