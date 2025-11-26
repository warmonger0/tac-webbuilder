"""
Issue Completion Routes

Handles automatic completion of issues:
- Marks queue phases as completed
- Closes GitHub issues
- Links commits to issues
"""

import logging
import subprocess
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.phase_queue_service import PhaseQueueService
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/issue", tags=["issue-completion"])

# Initialize services
phase_queue_service = PhaseQueueService()


class IssueCompletionRequest(BaseModel):
    issue_number: int = Field(..., description="GitHub issue number")
    phase_number: Optional[int] = Field(None, description="Phase number (if multi-phase)")
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    close_message: Optional[str] = Field(None, description="Custom close message")


class IssueCompletionResponse(BaseModel):
    success: bool
    queue_updated: bool
    issue_closed: bool
    message: str


@router.post("/{issue_number}/complete", response_model=IssueCompletionResponse)
async def complete_issue(issue_number: int, request: IssueCompletionRequest) -> IssueCompletionResponse:
    """
    Complete an issue by:
    1. Marking all queue phases for the issue as completed
    2. Closing the GitHub issue with a completion message

    Args:
        issue_number: GitHub issue number
        request: Completion details (phase_number, commit_sha, etc.)

    Returns:
        IssueCompletionResponse with status of each operation
    """
    queue_updated = False
    issue_closed = False
    messages = []

    try:
        # Step 1: Mark queue phases as completed
        db_conn = get_connection()
        cursor = db_conn.cursor()

        # Find all queue entries for this issue
        if request.phase_number:
            cursor.execute(
                """
                SELECT queue_id, phase_number, status
                FROM phase_queue
                WHERE parent_issue = ? AND phase_number = ?
                """,
                (issue_number, request.phase_number)
            )
        else:
            cursor.execute(
                """
                SELECT queue_id, phase_number, status
                FROM phase_queue
                WHERE parent_issue = ?
                """,
                (issue_number,)
            )

        queue_entries = cursor.fetchall()

        if queue_entries:
            for queue_id, phase_num, status in queue_entries:
                if status != 'completed':
                    cursor.execute(
                        """
                        UPDATE phase_queue
                        SET status = 'completed',
                            updated_at = datetime('now')
                        WHERE queue_id = ?
                        """,
                        (queue_id,)
                    )
                    logger.info(f"[COMPLETION] Marked queue entry {queue_id} (issue #{issue_number} phase {phase_num}) as completed")

            db_conn.commit()
            queue_updated = True
            messages.append(f"Updated {len(queue_entries)} queue entries")
        else:
            messages.append(f"No queue entries found for issue #{issue_number}")

        db_conn.close()

        # Step 2: Close GitHub issue
        try:
            close_msg = request.close_message or "✅ Completed and merged"
            if request.commit_sha:
                close_msg += f"\n\nCommit: {request.commit_sha}"

            # Use gh CLI to close the issue
            subprocess.run(
                [
                    "gh", "issue", "close", str(issue_number),
                    "--repo", "warmonger0/tac-webbuilder",
                    "--comment", close_msg
                ],
                capture_output=True,
                text=True,
                check=True
            )

            issue_closed = True
            messages.append(f"Closed GitHub issue #{issue_number}")
            logger.info(f"[COMPLETION] Closed GitHub issue #{issue_number}")

        except subprocess.CalledProcessError as e:
            logger.error(f"[COMPLETION] Failed to close GitHub issue #{issue_number}: {e.stderr}")
            messages.append(f"Failed to close GitHub issue: {e.stderr}")

        except Exception as e:
            logger.error(f"[COMPLETION] Error closing GitHub issue #{issue_number}: {str(e)}")
            messages.append(f"Error closing GitHub issue: {str(e)}")

        return IssueCompletionResponse(
            success=queue_updated or issue_closed,
            queue_updated=queue_updated,
            issue_closed=issue_closed,
            message="; ".join(messages)
        )

    except Exception as e:
        logger.error(f"[COMPLETION] Error completing issue #{issue_number}: {str(e)}")
        raise HTTPException(500, f"Error completing issue: {str(e)}")


@router.post("/complete-from-commit", response_model=dict)
async def complete_from_commit(commit_message: str) -> dict:
    """
    Extract issue numbers from commit message and complete them.

    Looks for patterns like:
    - "Issue #123"
    - "Fixes #123"
    - "Closes #123"
    - "(Issue #123)"

    Args:
        commit_message: Git commit message

    Returns:
        Dict with completion results for each issue found
    """
    import re

    # Extract issue numbers from commit message
    patterns = [
        r'Issue #(\d+)',
        r'Fixes #(\d+)',
        r'Closes #(\d+)',
        r'\(Issue #(\d+)\)',
        r'feat:.*#(\d+)',
        r'fix:.*#(\d+)'
    ]

    issue_numbers = set()
    for pattern in patterns:
        matches = re.findall(pattern, commit_message, re.IGNORECASE)
        issue_numbers.update(int(num) for num in matches)

    if not issue_numbers:
        return {
            "found_issues": [],
            "message": "No issue numbers found in commit message"
        }

    results = {}
    for issue_num in issue_numbers:
        try:
            result = await complete_issue(
                issue_num,
                IssueCompletionRequest(
                    issue_number=issue_num,
                    close_message=f"✅ Completed via commit\n\n{commit_message[:200]}"
                )
            )
            results[issue_num] = result.dict()
        except Exception as e:
            results[issue_num] = {"error": str(e)}

    return {
        "found_issues": list(issue_numbers),
        "results": results
    }
