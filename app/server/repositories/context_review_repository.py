"""
Context Review Repository

Handles all database operations for the context review system.
"""

import json
import logging
from datetime import datetime

from database import get_database_adapter
from models.context_review import ContextReview, ContextSuggestion

logger = logging.getLogger(__name__)


class ContextReviewRepository:
    """Repository for context review database operations"""

    def __init__(self):
        """Initialize repository with database adapter."""
        self.adapter = get_database_adapter()

    def create_review(self, review: ContextReview) -> int:
        """
        Create a new context review record.

        Args:
            review: ContextReview object to insert

        Returns:
            int: ID of the created review

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()
                db_type = self.adapter.get_db_type()

                # PostgreSQL requires RETURNING clause to get inserted ID
                # Note: PostgreSQL adapter uses RealDictCursor, so rows are dicts
                if db_type == "postgresql":
                    cursor.execute(
                        f"""
                        INSERT INTO context_reviews (
                            workflow_id, issue_number, change_description, project_path,
                            analysis_timestamp, analysis_duration_seconds, agent_cost,
                            status, result
                        )
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        RETURNING id
                        """,
                        (
                            review.workflow_id,
                            review.issue_number,
                            review.change_description,
                            review.project_path,
                            review.analysis_timestamp or datetime.now(),
                            review.analysis_duration_seconds,
                            review.agent_cost,
                            review.status,
                            review.result,
                        ),
                    )
                    result = cursor.fetchone()
                    review_id = result["id"]  # Use column name for RealDictCursor
                else:  # SQLite
                    cursor.execute(
                        f"""
                        INSERT INTO context_reviews (
                            workflow_id, issue_number, change_description, project_path,
                            analysis_timestamp, analysis_duration_seconds, agent_cost,
                            status, result
                        )
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        """,
                        (
                            review.workflow_id,
                            review.issue_number,
                            review.change_description,
                            review.project_path,
                            review.analysis_timestamp or datetime.now(),
                            review.analysis_duration_seconds,
                            review.agent_cost,
                            review.status,
                            review.result,
                        ),
                    )
                    review_id = cursor.lastrowid

                logger.info(f"[DB] Created context review {review_id}")
                return review_id

        except Exception as e:
            logger.error(f"[ERROR] Failed to create context review: {e}")
            logger.error(f"[ERROR] Exception type: {type(e)}")
            logger.error(f"[ERROR] Exception args: {e.args}")
            import traceback
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            raise

    def get_review(self, review_id: int) -> ContextReview | None:
        """
        Get a context review by ID.

        Args:
            review_id: Review ID to fetch

        Returns:
            ContextReview object or None if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()

                cursor.execute(
                    f"SELECT * FROM context_reviews WHERE id = {ph}",
                    (review_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                return ContextReview(
                    id=row["id"] if "id" in row else row[0],
                    workflow_id=row["workflow_id"] if "workflow_id" in row else row[1],
                    issue_number=row["issue_number"] if "issue_number" in row else row[2],
                    change_description=row["change_description"] if "change_description" in row else row[3],
                    project_path=row["project_path"] if "project_path" in row else row[4],
                    analysis_timestamp=row["analysis_timestamp"] if "analysis_timestamp" in row else row[5],
                    analysis_duration_seconds=row["analysis_duration_seconds"] if "analysis_duration_seconds" in row else row[6],
                    agent_cost=row["agent_cost"] if "agent_cost" in row else row[7],
                    status=row["status"] if "status" in row else row[8],
                    result=row["result"] if "result" in row else row[9],
                )

        except Exception as e:
            logger.error(f"[ERROR] Failed to get context review {review_id}: {e}")
            raise

    def update_review_status(
        self, review_id: int, status: str, result: dict | None = None
    ) -> bool:
        """
        Update review status and optionally set result.

        Args:
            review_id: Review ID to update
            status: New status value
            result: Optional analysis result dict

        Returns:
            bool: True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()

                result_json = json.dumps(result) if result else None

                cursor.execute(
                    f"""
                    UPDATE context_reviews
                    SET status = {ph}, result = {ph}
                    WHERE id = {ph}
                    """,
                    (status, result_json, review_id),
                )

                success = cursor.rowcount > 0
                if success:
                    logger.info(f"[DB] Updated context review {review_id} to status: {status}")
                return success

        except Exception as e:
            logger.error(f"[ERROR] Failed to update review {review_id}: {e}")
            raise

    def create_suggestions(self, suggestions: list[ContextSuggestion]) -> list[int]:
        """
        Create multiple context suggestions.

        Args:
            suggestions: List of ContextSuggestion objects

        Returns:
            list[int]: List of created suggestion IDs
        """
        suggestion_ids = []

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()
                db_type = self.adapter.get_db_type()

                for suggestion in suggestions:
                    # PostgreSQL requires RETURNING clause to get inserted ID
                    # Note: PostgreSQL adapter uses RealDictCursor, so rows are dicts
                    if db_type == "postgresql":
                        cursor.execute(
                            f"""
                            INSERT INTO context_suggestions (
                                review_id, suggestion_type, suggestion_text,
                                confidence, priority, rationale
                            )
                            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                            RETURNING id
                            """,
                            (
                                suggestion.review_id,
                                suggestion.suggestion_type,
                                suggestion.suggestion_text,
                                suggestion.confidence,
                                suggestion.priority,
                                suggestion.rationale,
                            ),
                        )
                        result = cursor.fetchone()
                        suggestion_id = result["id"]  # Use column name for RealDictCursor
                    else:  # SQLite
                        cursor.execute(
                            f"""
                            INSERT INTO context_suggestions (
                                review_id, suggestion_type, suggestion_text,
                                confidence, priority, rationale
                            )
                            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                            """,
                            (
                                suggestion.review_id,
                                suggestion.suggestion_type,
                                suggestion.suggestion_text,
                                suggestion.confidence,
                                suggestion.priority,
                                suggestion.rationale,
                            ),
                        )
                        suggestion_id = cursor.lastrowid

                    suggestion_ids.append(suggestion_id)

                logger.info(f"[DB] Created {len(suggestion_ids)} suggestions")
                return suggestion_ids

        except Exception as e:
            logger.error(f"[ERROR] Failed to create suggestions: {e}")
            raise

    def get_suggestions(self, review_id: int) -> list[ContextSuggestion]:
        """
        Get all suggestions for a review.

        Args:
            review_id: Review ID

        Returns:
            list[ContextSuggestion]: List of suggestions
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()

                cursor.execute(
                    f"""
                    SELECT * FROM context_suggestions
                    WHERE review_id = {ph}
                    ORDER BY priority ASC
                    """,
                    (review_id,),
                )
                rows = cursor.fetchall()

                suggestions = []
                for row in rows:
                    suggestions.append(
                        ContextSuggestion(
                            id=row["id"] if "id" in row else row[0],
                            review_id=row["review_id"] if "review_id" in row else row[1],
                            suggestion_type=row["suggestion_type"] if "suggestion_type" in row else row[2],
                            suggestion_text=row["suggestion_text"] if "suggestion_text" in row else row[3],
                            confidence=row["confidence"] if "confidence" in row else row[4],
                            priority=row["priority"] if "priority" in row else row[5],
                            rationale=row["rationale"] if "rationale" in row else row[6],
                        )
                    )

                return suggestions

        except Exception as e:
            logger.error(f"[ERROR] Failed to get suggestions for review {review_id}: {e}")
            raise

    def check_cache(self, cache_key: str) -> str | None:
        """
        Check if analysis result is cached.

        Args:
            cache_key: SHA-256 hash of analysis request

        Returns:
            str | None: Cached analysis result JSON or None
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()

                cursor.execute(
                    f"""
                    SELECT analysis_result FROM context_cache
                    WHERE cache_key = {ph}
                    """,
                    (cache_key,),
                )
                row = cursor.fetchone()

                if row:
                    # Update access count and timestamp
                    cursor.execute(
                        f"""
                        UPDATE context_cache
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE cache_key = {ph}
                        """,
                        (cache_key,),
                    )
                    logger.info(f"[DB] Cache hit for key: {cache_key[:16]}...")
                    return row[0] if isinstance(row, tuple) else row["analysis_result"]

                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to check cache: {e}")
            raise

    def cache_result(self, cache_key: str, result: str) -> int:
        """
        Cache an analysis result.

        Args:
            cache_key: SHA-256 hash of analysis request
            result: Analysis result JSON string

        Returns:
            int: Cache entry ID
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                ph = self.adapter.placeholder()

                # Use UPSERT to handle duplicates
                if self.adapter.get_db_type() == "postgresql":
                    cursor.execute(
                        f"""
                        INSERT INTO context_cache (cache_key, analysis_result)
                        VALUES ({ph}, {ph})
                        ON CONFLICT (cache_key) DO UPDATE
                        SET analysis_result = EXCLUDED.analysis_result,
                            access_count = context_cache.access_count + 1,
                            last_accessed = NOW()
                        RETURNING id
                        """,
                        (cache_key, result),
                    )
                    row = cursor.fetchone()
                    cache_id = row["id"]  # Use column name for RealDictCursor
                else:  # SQLite
                    cursor.execute(
                        f"""
                        INSERT INTO context_cache (cache_key, analysis_result)
                        VALUES ({ph}, {ph})
                        ON CONFLICT(cache_key) DO UPDATE SET
                            analysis_result = excluded.analysis_result,
                            access_count = context_cache.access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        """,
                        (cache_key, result),
                    )
                    cache_id = cursor.lastrowid

                logger.info(f"[DB] Cached result with key: {cache_key[:16]}...")
                return cache_id

        except Exception as e:
            logger.error(f"[ERROR] Failed to cache result: {e}")
            raise
