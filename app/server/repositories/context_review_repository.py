"""Repository for context review database operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models.context_review import ContextCache, ContextReview, ContextSuggestion
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)


class ContextReviewRepository:
    """
    Repository for managing context review data.

    Provides CRUD operations for:
    - Context reviews (analysis requests and results)
    - Context suggestions (individual recommendations)
    - Context cache (optimization for repeated requests)
    """

    def __init__(self, db_path: str = "db/database.db"):
        """
        Initialize repository with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def create_review(self, review: ContextReview) -> int:
        """
        Create a new context review record.

        Args:
            review: ContextReview instance (without ID)

        Returns:
            ID of the created review

        Raises:
            Exception: If database operation fails
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO context_reviews (
                    workflow_id, issue_number, change_description,
                    project_path, analysis_timestamp, status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    review.workflow_id,
                    review.issue_number,
                    review.change_description,
                    review.project_path,
                    review.analysis_timestamp or datetime.now(),
                    review.status
                )
            )
            conn.commit()
            review_id = cursor.lastrowid
            logger.info(f"Created context review {review_id}")
            return review_id

    def get_review(self, review_id: int) -> Optional[ContextReview]:
        """
        Fetch a context review by ID.

        Args:
            review_id: ID of the review to fetch

        Returns:
            ContextReview if found, None otherwise
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM context_reviews WHERE id = ?",
                (review_id,)
            )
            row = cursor.fetchone()
            if row:
                return ContextReview.from_db_row(row)
            return None

    def update_review_status(
        self,
        review_id: int,
        status: str,
        result: Optional[dict] = None,
        duration: Optional[float] = None,
        cost: Optional[float] = None
    ) -> bool:
        """
        Update review status and optionally result data.

        Args:
            review_id: ID of the review to update
            status: New status (pending|analyzing|complete|failed)
            result: Analysis result dictionary (optional)
            duration: Analysis duration in seconds (optional)
            cost: Agent cost in USD (optional)

        Returns:
            True if updated successfully, False if review not found
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Build dynamic update based on provided parameters
            updates = ["status = ?"]
            params = [status]

            if result is not None:
                updates.append("result = ?")
                params.append(json.dumps(result))

            if duration is not None:
                updates.append("analysis_duration_seconds = ?")
                params.append(duration)

            if cost is not None:
                updates.append("agent_cost = ?")
                params.append(cost)

            params.append(review_id)

            cursor.execute(
                f"UPDATE context_reviews SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            conn.commit()

            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated review {review_id} to status: {status}")
            return updated

    def create_suggestions(
        self,
        suggestions: List[ContextSuggestion]
    ) -> List[int]:
        """
        Batch create context suggestions.

        Args:
            suggestions: List of ContextSuggestion instances

        Returns:
            List of created suggestion IDs
        """
        if not suggestions:
            return []

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            suggestion_ids = []

            for suggestion in suggestions:
                cursor.execute(
                    """
                    INSERT INTO context_suggestions (
                        review_id, suggestion_type, suggestion_text,
                        confidence, priority, rationale
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        suggestion.review_id,
                        suggestion.suggestion_type,
                        suggestion.suggestion_text,
                        suggestion.confidence,
                        suggestion.priority,
                        suggestion.rationale
                    )
                )
                suggestion_ids.append(cursor.lastrowid)

            conn.commit()
            logger.info(f"Created {len(suggestion_ids)} suggestions")
            return suggestion_ids

    def get_suggestions(self, review_id: int) -> List[ContextSuggestion]:
        """
        Fetch all suggestions for a review.

        Args:
            review_id: ID of the review

        Returns:
            List of ContextSuggestion instances (may be empty)
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM context_suggestions
                WHERE review_id = ?
                ORDER BY priority ASC, confidence DESC
                """,
                (review_id,)
            )
            rows = cursor.fetchall()
            return [ContextSuggestion.from_db_row(row) for row in rows]

    def check_cache(self, cache_key: str) -> Optional[str]:
        """
        Check if analysis is cached and return result.

        Updates access count and last_accessed timestamp.

        Args:
            cache_key: SHA256 hash of description + project path

        Returns:
            Cached analysis result JSON string if found, None otherwise
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Fetch cache entry
            cursor.execute(
                "SELECT * FROM context_cache WHERE cache_key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            cache_entry = ContextCache.from_db_row(row)

            # Update access statistics
            cursor.execute(
                """
                UPDATE context_cache
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE cache_key = ?
                """,
                (datetime.now(), cache_key)
            )
            conn.commit()

            logger.info(f"Cache hit for key {cache_key[:16]}...")
            return cache_entry.analysis_result

    def cache_result(self, cache_key: str, result: dict) -> int:
        """
        Store analysis result in cache.

        Args:
            cache_key: SHA256 hash of description + project path
            result: Analysis result dictionary

        Returns:
            ID of created cache entry
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if key already exists (shouldn't happen but handle it)
            cursor.execute(
                "SELECT id FROM context_cache WHERE cache_key = ?",
                (cache_key,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing cache entry
                cursor.execute(
                    """
                    UPDATE context_cache
                    SET analysis_result = ?,
                        created_at = ?,
                        access_count = 0,
                        last_accessed = NULL
                    WHERE cache_key = ?
                    """,
                    (json.dumps(result), datetime.now(), cache_key)
                )
                cache_id = existing[0]
            else:
                # Create new cache entry
                cursor.execute(
                    """
                    INSERT INTO context_cache (
                        cache_key, analysis_result, created_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (cache_key, json.dumps(result), datetime.now())
                )
                cache_id = cursor.lastrowid

            conn.commit()
            logger.info(f"Cached result with key {cache_key[:16]}...")
            return cache_id

    def cleanup_old_cache(self, days: int = 7) -> int:
        """
        Remove cache entries older than specified days.

        Args:
            days: Number of days to retain cache (default: 7)

        Returns:
            Number of entries deleted
        """
        cutoff = datetime.now() - timedelta(days=days)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM context_cache WHERE created_at < ?",
                (cutoff,)
            )
            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old cache entries")

            return deleted_count

    def get_review_by_workflow(
        self,
        workflow_id: str
    ) -> Optional[ContextReview]:
        """
        Fetch the most recent review for a workflow.

        Args:
            workflow_id: ADW workflow ID

        Returns:
            ContextReview if found, None otherwise
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM context_reviews
                WHERE workflow_id = ?
                ORDER BY analysis_timestamp DESC
                LIMIT 1
                """,
                (workflow_id,)
            )
            row = cursor.fetchone()
            if row:
                return ContextReview.from_db_row(row)
            return None

    def get_recent_reviews(self, limit: int = 10) -> List[ContextReview]:
        """
        Fetch recent context reviews.

        Args:
            limit: Maximum number of reviews to return (default: 10)

        Returns:
            List of ContextReview instances (most recent first)
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM context_reviews
                ORDER BY analysis_timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [ContextReview.from_db_row(row) for row in rows]
