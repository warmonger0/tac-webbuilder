"""
User Prompt Repository

Handles database operations for user prompt logs.
"""

import logging
from datetime import datetime
from typing import List, Optional

from core.models.observability import (
    UserPrompt,
    UserPromptCreate,
    UserPromptFilters,
    UserPromptWithProgress,
)
from database.factory import get_database_adapter

logger = logging.getLogger(__name__)


class UserPromptRepository:
    """Repository for user prompt database operations"""

    def __init__(self):
        self.adapter = get_database_adapter()

    def create(self, prompt: UserPromptCreate) -> UserPrompt:
        """
        Create a new user prompt log entry.

        Args:
            prompt: User prompt data

        Returns:
            Created UserPrompt with ID

        Raises:
            Exception: If database operation fails
        """
        query = """
            INSERT INTO user_prompts (
                request_id, session_id, nl_input, project_path, auto_post,
                issue_title, issue_body, issue_type, complexity,
                is_multi_phase, phase_count, parent_issue_number,
                estimated_cost_usd, estimated_tokens, model_name,
                github_issue_number, github_issue_url, posted_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, captured_at
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        prompt.request_id,
                        prompt.session_id,
                        prompt.nl_input,
                        prompt.project_path,
                        prompt.auto_post,
                        prompt.issue_title,
                        prompt.issue_body,
                        prompt.issue_type,
                        prompt.complexity,
                        prompt.is_multi_phase,
                        prompt.phase_count,
                        prompt.parent_issue_number,
                        prompt.estimated_cost_usd,
                        prompt.estimated_tokens,
                        prompt.model_name,
                        prompt.github_issue_number,
                        prompt.github_issue_url,
                        prompt.posted_at,
                    ),
                )
                result = cursor.fetchone()
                conn.commit()

                prompt_id = result['id']
                created_at = result['created_at']
                captured_at = result[2]

                logger.info(f"Created user prompt log {prompt_id} for request {prompt.request_id}")

                return UserPrompt(
                    id=prompt_id,
                    request_id=prompt.request_id,
                    session_id=prompt.session_id,
                    nl_input=prompt.nl_input,
                    project_path=prompt.project_path,
                    auto_post=prompt.auto_post,
                    issue_title=prompt.issue_title,
                    issue_body=prompt.issue_body,
                    issue_type=prompt.issue_type,
                    complexity=prompt.complexity,
                    is_multi_phase=prompt.is_multi_phase,
                    phase_count=prompt.phase_count,
                    parent_issue_number=prompt.parent_issue_number,
                    estimated_cost_usd=prompt.estimated_cost_usd,
                    estimated_tokens=prompt.estimated_tokens,
                    model_name=prompt.model_name,
                    github_issue_number=prompt.github_issue_number,
                    github_issue_url=prompt.github_issue_url,
                    posted_at=prompt.posted_at,
                    created_at=created_at,
                    captured_at=captured_at,
                )
        except Exception as e:
            logger.error(f"Failed to create user prompt log: {e}")
            raise

    def get_all(self, filters: Optional[UserPromptFilters] = None) -> List[UserPrompt]:
        """
        Get all user prompts with optional filtering and pagination.

        Args:
            filters: Optional filters (session_id, issue_number, etc.)

        Returns:
            List of UserPrompt objects
        """
        if filters is None:
            filters = UserPromptFilters()

        query = """
            SELECT id, request_id, session_id, nl_input, project_path, auto_post,
                   issue_title, issue_body, issue_type, complexity,
                   is_multi_phase, phase_count, parent_issue_number,
                   estimated_cost_usd, estimated_tokens, model_name,
                   github_issue_number, github_issue_url, posted_at,
                   created_at, captured_at
            FROM user_prompts
            WHERE 1=1
        """
        params = []

        if filters.session_id:
            query += " AND session_id = %s"
            params.append(filters.session_id)

        if filters.issue_number:
            query += " AND github_issue_number = %s"
            params.append(filters.issue_number)

        if filters.issue_type:
            query += " AND issue_type = %s"
            params.append(filters.issue_type)

        if filters.is_multi_phase is not None:
            query += " AND is_multi_phase = %s"
            params.append(filters.is_multi_phase)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([filters.limit, filters.offset])

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                prompts = []
                for row in rows:
                    prompts.append(
                        UserPrompt(
                            id=row['id'],
                            request_id=row['request_id'],
                            session_id=row['session_id'],
                            nl_input=row['nl_input'],
                            project_path=row['project_path'],
                            auto_post=row['auto_post'],
                            issue_title=row['issue_title'],
                            issue_body=row['issue_body'],
                            issue_type=row['issue_type'],
                            complexity=row['complexity'],
                            is_multi_phase=row['is_multi_phase'],
                            phase_count=row['phase_count'],
                            parent_issue_number=row['parent_issue_number'],
                            estimated_cost_usd=row['estimated_cost_usd'],
                            estimated_tokens=row['estimated_tokens'],
                            model_name=row['model_name'],
                            github_issue_number=row['github_issue_number'],
                            github_issue_url=row['github_issue_url'],
                            posted_at=row['posted_at'],
                            created_at=row['created_at'],
                            captured_at=row['captured_at'],
                        )
                    )

                logger.info(f"Retrieved {len(prompts)} user prompts")
                return prompts
        except Exception as e:
            logger.error(f"Failed to get user prompts: {e}")
            raise

    def get_by_request_id(self, request_id: str) -> Optional[UserPrompt]:
        """
        Get user prompt by request ID.

        Args:
            request_id: Request ID to lookup

        Returns:
            UserPrompt if found, None otherwise
        """
        query = """
            SELECT id, request_id, session_id, nl_input, project_path, auto_post,
                   issue_title, issue_body, issue_type, complexity,
                   is_multi_phase, phase_count, parent_issue_number,
                   estimated_cost_usd, estimated_tokens, model_name,
                   github_issue_number, github_issue_url, posted_at,
                   created_at, captured_at
            FROM user_prompts
            WHERE request_id = %s
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (request_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return UserPrompt(
                    id=row['id'],
                    request_id=row['request_id'],
                    session_id=row['session_id'],
                    nl_input=row['nl_input'],
                    project_path=row['project_path'],
                    auto_post=row['auto_post'],
                    issue_title=row['issue_title'],
                    issue_body=row['issue_body'],
                    issue_type=row['issue_type'],
                    complexity=row['complexity'],
                    is_multi_phase=row['is_multi_phase'],
                    phase_count=row['phase_count'],
                    parent_issue_number=row['parent_issue_number'],
                    estimated_cost_usd=row['estimated_cost_usd'],
                    estimated_tokens=row['estimated_tokens'],
                    model_name=row['model_name'],
                    github_issue_number=row['github_issue_number'],
                    github_issue_url=row['github_issue_url'],
                    posted_at=row['posted_at'],
                    created_at=row['created_at'],
                    captured_at=row['captured_at'],
                )
        except Exception as e:
            logger.error(f"Failed to get user prompt by request_id {request_id}: {e}")
            raise

    def get_with_progress(self, filters: Optional[UserPromptFilters] = None) -> List[UserPromptWithProgress]:
        """
        Get user prompts with linked task progress.

        Args:
            filters: Optional filters

        Returns:
            List of UserPromptWithProgress objects
        """
        if filters is None:
            filters = UserPromptFilters()

        query = """
            SELECT * FROM v_user_prompts_with_progress
            WHERE 1=1
        """
        params = []

        if filters.session_id:
            query += " AND session_id = %s"
            params.append(filters.session_id)

        if filters.issue_number:
            query += " AND github_issue_number = %s"
            params.append(filters.issue_number)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([filters.limit, filters.offset])

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                prompts = []
                for row in rows:
                    prompts.append(
                        UserPromptWithProgress(
                            id=row['id'],
                            request_id=row['request_id'],
                            session_id=row['session_id'],
                            nl_input=row['nl_input'],
                            project_path=row['project_path'],
                            auto_post=row['auto_post'],
                            issue_title=row['issue_title'],
                            issue_body=row['issue_body'],
                            issue_type=row['issue_type'],
                            complexity=row['complexity'],
                            is_multi_phase=row['is_multi_phase'],
                            phase_count=row['phase_count'],
                            parent_issue_number=row['parent_issue_number'],
                            estimated_cost_usd=row['estimated_cost_usd'],
                            estimated_tokens=row['estimated_tokens'],
                            model_name=row['model_name'],
                            github_issue_number=row['github_issue_number'],
                            github_issue_url=row['github_issue_url'],
                            posted_at=row['posted_at'],
                            created_at=row['created_at'],
                            captured_at=row['captured_at'],
                            total_phases=row[21],
                            completed_phases=row[22],
                            failed_phases=row[23],
                            latest_phase=row[24],
                            last_activity=row[25],
                        )
                    )

                logger.info(f"Retrieved {len(prompts)} user prompts with progress")
                return prompts
        except Exception as e:
            logger.error(f"Failed to get user prompts with progress: {e}")
            raise

    def update_github_info(
        self, request_id: str, issue_number: int, issue_url: str, posted_at: datetime
    ) -> bool:
        """
        Update GitHub info after issue is posted.

        Args:
            request_id: Request ID
            issue_number: GitHub issue number
            issue_url: GitHub issue URL
            posted_at: Timestamp when posted

        Returns:
            True if updated, False if not found
        """
        query = """
            UPDATE user_prompts
            SET github_issue_number = %s,
                github_issue_url = %s,
                posted_at = %s
            WHERE request_id = %s
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (issue_number, issue_url, posted_at, request_id))
                conn.commit()

                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated GitHub info for request {request_id}: issue #{issue_number}")
                else:
                    logger.warning(f"Request {request_id} not found for GitHub info update")

                return updated
        except Exception as e:
            logger.error(f"Failed to update GitHub info for request {request_id}: {e}")
            raise
