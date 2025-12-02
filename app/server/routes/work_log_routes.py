"""
Work Log API Routes

Endpoints for creating and managing work log entries.
"""

import logging
from typing import List

from core.models.work_log import (
    WorkLogEntry,
    WorkLogEntryCreate,
    WorkLogListResponse,
)
from fastapi import APIRouter, HTTPException
from repositories.work_log_repository import WorkLogRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-log", tags=["Work Log"])


def init_work_log_routes(repository: WorkLogRepository | None = None):
    """
    Initialize work log routes with optional repository injection.

    Args:
        repository: WorkLogRepository instance (creates new if None)
    """
    repo = repository or WorkLogRepository()

    @router.post("", response_model=WorkLogEntry, status_code=201)
    async def create_work_log_entry(entry: WorkLogEntryCreate) -> WorkLogEntry:
        """
        Create a new work log entry.

        Validates that summary is at most 280 characters.
        """
        try:
            return repo.create_entry(entry)
        except ValueError as e:
            logger.warning(f"Validation error creating work log: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating work log entry: {e}")
            raise HTTPException(status_code=500, detail="Failed to create work log entry")

    @router.get("", response_model=WorkLogListResponse)
    async def get_work_log_entries(
        limit: int = 50,
        offset: int = 0,
    ) -> WorkLogListResponse:
        """
        Get all work log entries with pagination.

        Args:
            limit: Maximum number of entries to return (default: 50)
            offset: Number of entries to skip (default: 0)

        Returns:
            List of work log entries with pagination info
        """
        try:
            entries = repo.get_all(limit=limit, offset=offset)
            total = repo.get_count()

            return WorkLogListResponse(
                entries=entries,
                total=total,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            import traceback
            logger.error(f"Error retrieving work log entries: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to retrieve work log entries")

    @router.get("/session/{session_id}", response_model=List[WorkLogEntry])
    async def get_session_work_logs(session_id: str) -> List[WorkLogEntry]:
        """
        Get all work log entries for a specific session.

        Args:
            session_id: Session ID to filter by

        Returns:
            List of work log entries for the session
        """
        try:
            return repo.get_by_session(session_id)
        except Exception as e:
            logger.error(f"Error retrieving work logs for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve session work logs")

    @router.delete("/{entry_id}", status_code=204)
    async def delete_work_log_entry(entry_id: int):
        """
        Delete a work log entry.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            204 No Content on success

        Raises:
            404: If entry not found
            500: If database operation fails
        """
        try:
            deleted = repo.delete_entry(entry_id)
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Work log entry {entry_id} not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting work log entry {entry_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete work log entry")

    return router
