"""
Git operations endpoints for frontend UI.
"""
from __future__ import annotations

import logging
import subprocess

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Git"])


class GitStatusFile(BaseModel):
    """A file in git status."""
    path: str
    status: str  # 'modified', 'added', 'deleted', 'untracked'


class GitStatusResponse(BaseModel):
    """Git status response."""
    branch: str
    ahead: int
    behind: int
    staged: list[GitStatusFile]
    unstaged: list[GitStatusFile]
    untracked: list[GitStatusFile]
    clean: bool


class GitCommitRequest(BaseModel):
    """Git commit request."""
    message: str
    files: list[str] = []  # Empty list means commit all changes


class GitCommitResponse(BaseModel):
    """Git commit response."""
    success: bool
    commit_hash: str | None
    message: str
    files_committed: int


@router.get("/git/status", response_model=GitStatusResponse)
async def get_git_status() -> GitStatusResponse:
    """
    Get current git repository status.

    Returns:
        GitStatusResponse with current branch, staged/unstaged files, etc.
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        branch = branch_result.stdout.strip()

        # Get ahead/behind count
        ahead = 0
        behind = 0
        try:
            ahead_behind_result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if ahead_behind_result.returncode == 0:
                parts = ahead_behind_result.stdout.strip().split()
                if len(parts) == 2:
                    behind = int(parts[0])
                    ahead = int(parts[1])
        except Exception as e:
            logger.warning(f"Could not get ahead/behind count: {e}")

        # Get status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        staged: list[GitStatusFile] = []
        unstaged: list[GitStatusFile] = []
        untracked: list[GitStatusFile] = []

        for line in status_result.stdout.splitlines():
            if len(line) < 4:
                continue

            index_status = line[0]
            work_tree_status = line[1]
            file_path = line[3:].strip()

            # Staged changes (index)
            if index_status in ['M', 'A', 'D', 'R', 'C']:
                status_map = {'M': 'modified', 'A': 'added', 'D': 'deleted', 'R': 'renamed', 'C': 'copied'}
                staged.append(GitStatusFile(
                    path=file_path,
                    status=status_map.get(index_status, 'modified')
                ))

            # Unstaged changes (working tree)
            if work_tree_status in ['M', 'D']:
                status_map = {'M': 'modified', 'D': 'deleted'}
                unstaged.append(GitStatusFile(
                    path=file_path,
                    status=status_map.get(work_tree_status, 'modified')
                ))

            # Untracked files
            if index_status == '?' and work_tree_status == '?':
                untracked.append(GitStatusFile(
                    path=file_path,
                    status='untracked'
                ))

        clean = len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0

        return GitStatusResponse(
            branch=branch,
            ahead=ahead,
            behind=behind,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
            clean=clean
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"Git status command failed: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error getting git status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/commit", response_model=GitCommitResponse)
async def commit_changes(request: GitCommitRequest) -> GitCommitResponse:
    """
    Commit changes to git repository.

    Args:
        request: GitCommitRequest with commit message and optional file list

    Returns:
        GitCommitResponse with success status and commit details
    """
    try:
        # Stage files
        if request.files:
            # Stage specific files
            for file_path in request.files:
                add_result = subprocess.run(
                    ["git", "add", file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
        else:
            # Stage all changes
            add_result = subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                check=True
            )

        # Create commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", request.message],
            capture_output=True,
            text=True,
            check=True
        )

        # Get the commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = hash_result.stdout.strip()

        # Count files committed
        files_result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        files_committed = len(files_result.stdout.splitlines())

        logger.info(f"[GIT] Created commit {commit_hash[:7]} with {files_committed} files")

        return GitCommitResponse(
            success=True,
            commit_hash=commit_hash,
            message=f"Successfully created commit {commit_hash[:7]}",
            files_committed=files_committed
        )

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logger.error(f"Git commit failed: {error_msg}")

        # Check if there are no changes to commit
        if "nothing to commit" in error_msg.lower():
            return GitCommitResponse(
                success=False,
                commit_hash=None,
                message="No changes to commit",
                files_committed=0
            )

        raise HTTPException(status_code=400, detail=f"Git commit failed: {error_msg}")
    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
