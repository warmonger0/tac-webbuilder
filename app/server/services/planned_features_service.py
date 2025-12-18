#!/usr/bin/env python3
"""
Planned Features Service

Business logic for managing planned features, sessions, bugs, and enhancements.

Responsibilities:
- CRUD operations for planned features
- Filtering and search
- Status tracking with automatic timestamp management
- Statistics and analytics
- Hierarchical feature management
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from core.models import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from database import get_database_adapter

logger = logging.getLogger(__name__)


class PlannedFeaturesService:
    """Service for managing planned features and sessions."""

    def __init__(self):
        """Initialize PlannedFeaturesService with database adapter."""
        self.adapter = get_database_adapter()
        logger.info("[INIT] PlannedFeaturesService initialized")

    def get_all(
        self,
        status: str | None = None,
        item_type: str | None = None,
        priority: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PlannedFeature]:
        """
        Get all planned features with optional filtering and pagination.

        Args:
            status: Filter by status ('planned', 'in_progress', 'completed', 'cancelled')
            item_type: Filter by type ('session', 'feature', 'bug', 'enhancement')
            priority: Filter by priority ('high', 'medium', 'low')
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            List of PlannedFeature objects ordered by priority and status
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM planned_features WHERE 1=1"
            params = []

            if status:
                query += f" AND status = {self.adapter.placeholder()}"
                params.append(status)
            if item_type:
                query += f" AND item_type = {self.adapter.placeholder()}"
                params.append(item_type)
            if priority:
                query += f" AND priority = {self.adapter.placeholder()}"
                params.append(priority)

            # Sort by created_at in database for initial ordering
            # Then apply custom sorting in Python (faster for small result sets)
            query += " ORDER BY created_at DESC"
            query += f" LIMIT {self.adapter.placeholder()} OFFSET {self.adapter.placeholder()}"
            params.append(limit)
            params.append(offset)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            features = [self._row_to_model(row) for row in rows]

            # Sort in Python (faster for small result sets than complex CASE statements)
            # Order by: status (in_progress → planned → completed → cancelled)
            #          priority (high → medium → low)
            #          created_at (newest first)
            from datetime import datetime

            status_order = {'in_progress': 1, 'planned': 2, 'completed': 3, 'cancelled': 4}
            priority_order = {'high': 1, 'medium': 2, 'low': 3}

            features.sort(key=lambda f: (
                status_order.get(f.status, 5),
                priority_order.get(f.priority, 4),
                # Parse ISO string and negate timestamp for DESC order
                -(datetime.fromisoformat(f.created_at).timestamp() if f.created_at else 0)
            ))
            logger.info(
                f"[{self.__class__.__name__}] Retrieved {len(features)} planned features (offset: {offset})"
            )
            return features

    def get_by_id(self, feature_id: int) -> PlannedFeature | None:
        """
        Get single planned feature by ID.

        Args:
            feature_id: Feature ID to fetch

        Returns:
            PlannedFeature object if found, None otherwise
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM planned_features WHERE id = {self.adapter.placeholder()}",
                (feature_id,),
            )
            row = cursor.fetchone()

            if row:
                logger.info(
                    f"[{self.__class__.__name__}] Found feature {feature_id}"
                )
                return self._row_to_model(row)
            else:
                logger.warning(
                    f"[{self.__class__.__name__}] Feature {feature_id} not found"
                )
                return None

    def get_by_session(self, session_number: int) -> PlannedFeature | None:
        """
        Get planned feature by session number.

        Args:
            session_number: Session number to search for

        Returns:
            PlannedFeature object if found, None otherwise
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM planned_features WHERE session_number = {self.adapter.placeholder()}",
                (session_number,),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

    def create(self, feature_data: PlannedFeatureCreate) -> PlannedFeature:
        """
        Create new planned feature.

        Args:
            feature_data: PlannedFeatureCreate model with feature details

        Returns:
            Created PlannedFeature object with assigned ID

        Raises:
            ValueError: If feature data is invalid
        """
        # Serialize tags to JSON
        tags_json = json.dumps(feature_data.tags)

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Build insert query with placeholders
            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                INSERT INTO planned_features
                    (item_type, title, description, status, priority,
                     estimated_hours, session_number, github_issue_number,
                     parent_id, tags)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            """,
                (
                    feature_data.item_type,
                    feature_data.title,
                    feature_data.description,
                    feature_data.status,
                    feature_data.priority,
                    feature_data.estimated_hours,
                    feature_data.session_number,
                    feature_data.github_issue_number,
                    feature_data.parent_id,
                    tags_json,
                ),
            )

            result = cursor.fetchone()
            # Handle both dict-like (PostgreSQL RealDictCursor) and tuple-like cursors
            if result:
                feature_id = result.get("id") if hasattr(result, "get") else result[0]
            else:
                feature_id = None
            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Created feature {feature_id}: {feature_data.title}"
            )

        # Fetch and return the created feature
        return self.get_by_id(feature_id)

    def update(
        self, feature_id: int, update_data: PlannedFeatureUpdate
    ) -> PlannedFeature:
        """
        Update existing planned feature.

        Auto-updates timestamps:
        - started_at: Set when status changes to 'in_progress' (if not already set)
        - completed_at: Set when status changes to 'completed' or 'cancelled' (if not already set)

        Args:
            feature_id: ID of feature to update
            update_data: PlannedFeatureUpdate model with fields to update

        Returns:
            Updated PlannedFeature object

        Raises:
            ValueError: If feature not found
        """
        # Get existing feature
        existing = self.get_by_id(feature_id)
        if not existing:
            raise ValueError(f"Feature {feature_id} not found")

        # Build dynamic SET clause
        set_clauses = []
        params = []

        if update_data.title is not None:
            set_clauses.append(f"title = {self.adapter.placeholder()}")
            params.append(update_data.title)
        if update_data.description is not None:
            set_clauses.append(f"description = {self.adapter.placeholder()}")
            params.append(update_data.description)
        if update_data.status is not None:
            set_clauses.append(f"status = {self.adapter.placeholder()}")
            params.append(update_data.status)

            # Auto-set timestamps on status change
            if update_data.status == "in_progress" and not existing.started_at:
                set_clauses.append(f"started_at = {self.adapter.now_function()}")
            elif update_data.status in [
                "completed",
                "cancelled",
            ] and not existing.completed_at:
                set_clauses.append(f"completed_at = {self.adapter.now_function()}")

        if update_data.priority is not None:
            set_clauses.append(f"priority = {self.adapter.placeholder()}")
            params.append(update_data.priority)
        if update_data.estimated_hours is not None:
            set_clauses.append(f"estimated_hours = {self.adapter.placeholder()}")
            params.append(update_data.estimated_hours)
        if update_data.actual_hours is not None:
            set_clauses.append(f"actual_hours = {self.adapter.placeholder()}")
            params.append(update_data.actual_hours)
        if update_data.github_issue_number is not None:
            set_clauses.append(f"github_issue_number = {self.adapter.placeholder()}")
            params.append(update_data.github_issue_number)
        if update_data.tags is not None:
            set_clauses.append(f"tags = {self.adapter.placeholder()}")
            params.append(json.dumps(update_data.tags))
        if update_data.completion_notes is not None:
            set_clauses.append(f"completion_notes = {self.adapter.placeholder()}")
            params.append(update_data.completion_notes)

        if not set_clauses:
            logger.info(
                f"[{self.__class__.__name__}] No changes for feature {feature_id}"
            )
            return existing  # No changes

        params.append(feature_id)
        query = f"UPDATE planned_features SET {', '.join(set_clauses)} WHERE id = {self.adapter.placeholder()}"

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            conn.commit()

        logger.info(f"[{self.__class__.__name__}] Updated feature {feature_id}")

        # Trigger post-session hook if session completed
        if (
            update_data.status == "completed"
            and existing.session_number
            and existing.item_type == "session"
        ):
            self._trigger_post_session_hook(existing.session_number)

        return self.get_by_id(feature_id)

    def delete(self, feature_id: int) -> bool:
        """
        Delete planned feature (soft delete via status='cancelled').

        Args:
            feature_id: ID of feature to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If feature not found
        """
        update_data = PlannedFeatureUpdate(status="cancelled")
        self.update(feature_id, update_data)
        logger.info(f"[{self.__class__.__name__}] Soft deleted feature {feature_id}")
        return True

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about planned features.

        Returns:
            Dictionary with statistics:
            - by_status: Count of features by status
            - by_priority: Count of features by priority
            - by_type: Count of features by item_type
            - total_estimated_hours: Sum of estimated hours
            - total_actual_hours: Sum of actual hours
            - completion_rate: Percentage of completed vs total features
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Counts by status
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM planned_features
                GROUP BY status
            """
            )
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Counts by priority
            cursor.execute(
                """
                SELECT priority, COUNT(*) as count
                FROM planned_features
                WHERE priority IS NOT NULL
                GROUP BY priority
            """
            )
            by_priority = {row["priority"]: row["count"] for row in cursor.fetchall()}

            # Counts by type
            cursor.execute(
                """
                SELECT item_type, COUNT(*) as count
                FROM planned_features
                GROUP BY item_type
            """
            )
            by_type = {row["item_type"]: row["count"] for row in cursor.fetchall()}

            # Hours summary
            cursor.execute(
                """
                SELECT
                    SUM(estimated_hours) as total_estimated,
                    SUM(actual_hours) as total_actual
                FROM planned_features
            """
            )
            hours = cursor.fetchone()

            # Completion rate (only for completed/cancelled items)
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed') * 100.0 /
                    NULLIF(COUNT(*) FILTER (WHERE status IN ('completed', 'cancelled', 'in_progress', 'planned')), 0) as completion_rate
                FROM planned_features
            """
            )
            completion_result = cursor.fetchone()
            completion_rate = completion_result["completion_rate"] if completion_result and completion_result.get("completion_rate") else 0.0

            stats = {
                "by_status": by_status,
                "by_priority": by_priority,
                "by_type": by_type,
                "total_estimated_hours": float(hours["total_estimated"]) if hours and hours.get("total_estimated") else 0.0,
                "total_actual_hours": float(hours["total_actual"]) if hours and hours.get("total_actual") else 0.0,
                "completion_rate": float(completion_rate),
            }

            logger.info(
                f"[{self.__class__.__name__}] Generated statistics: {stats}"
            )
            return stats

    def get_recent_completions(self, days: int = 30) -> list[PlannedFeature]:
        """
        Get recently completed features.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            List of completed PlannedFeature objects ordered by completion date (newest first)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                SELECT * FROM planned_features
                WHERE status = 'completed'
                  AND completed_at >= {self.adapter.now_function()} - INTERVAL '{placeholder} days'
                ORDER BY completed_at DESC
            """,
                (days,),
            )
            rows = cursor.fetchall()

            features = [self._row_to_model(row) for row in rows]
            logger.info(
                f"[{self.__class__.__name__}] Found {len(features)} recent completions"
            )
            return features

    def _trigger_post_session_hook(self, session_number: int):
        """
        Trigger post-session hook to archive session documentation.

        Args:
            session_number: Session number that was just completed
        """
        try:
            # Get project root (3 levels up from this file: server/services -> server -> app -> root)
            project_root = Path(__file__).parent.parent.parent.parent
            hook_path = project_root / "scripts" / "post_session_hook.sh"

            if not hook_path.exists():
                logger.warning(
                    f"[{self.__class__.__name__}] Post-session hook not found at {hook_path}"
                )
                return

            logger.info(
                f"[{self.__class__.__name__}] Triggering post-session hook for session {session_number}"
            )

            # Run hook in background (non-blocking)
            subprocess.Popen(
                [str(hook_path), str(session_number)],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            logger.info(
                f"[{self.__class__.__name__}] Post-session hook triggered successfully"
            )

        except Exception as e:
            # Don't fail the update if hook fails
            logger.error(
                f"[{self.__class__.__name__}] Error triggering post-session hook: {e}"
            )

    def _row_to_model(self, row) -> PlannedFeature:
        """
        Convert database row to Pydantic model.

        Args:
            row: Database row (dict-like object)

        Returns:
            PlannedFeature object
        """
        data = dict(row)

        # Parse JSON tags (handle both JSONB from PostgreSQL and JSON string)
        if data.get("tags"):
            if isinstance(data["tags"], str):
                # JSON string (should not happen with JSONB, but handle it)
                try:
                    data["tags"] = json.loads(data["tags"])
                except (json.JSONDecodeError, TypeError):
                    data["tags"] = []
            elif isinstance(data["tags"], list):
                # Already a list (JSONB)
                pass
            else:
                data["tags"] = []
        else:
            data["tags"] = []

        # Convert datetime objects to ISO format strings
        for field in ["created_at", "updated_at", "started_at", "completed_at"]:
            if data.get(field) and hasattr(data[field], "isoformat"):
                data[field] = data[field].isoformat()

        return PlannedFeature(**data)
