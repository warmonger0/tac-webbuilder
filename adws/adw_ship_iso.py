#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "requests"]
# ///

"""
ADW Ship Iso - AI Developer Workflow for shipping (merging) to main

Usage:
  uv run adw_ship_iso.py <issue-number> <adw-id>

Workflow:
1. Load state and validate worktree exists
2. Validate ALL state fields are populated (not None)
3. Find PR for the feature branch
4. Merge PR via GitHub API (gh pr merge --squash)
5. Verify merge actually landed on main (phantom merge detection)
6. Close issue with success comment
7. Post success message to issue

This workflow uses GitHub's PR merge API which automatically:
- Handles merge conflicts
- Supports squash/merge strategies
- Doesn't require clean working directory

After successful merge and verification, this workflow:
- Automatically closes the associated issue
- Posts a success comment explaining the closure

This workflow REQUIRES that all previous workflows have been run and that
every field in ADWState has a value. This is our final approval step.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.github import (
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adw_modules.workflow_ops import format_issue_message
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.worktree_ops import validate_worktree
from adw_modules.data_types import ADWStateData
from adw_modules.doc_cleanup import cleanup_adw_documentation
from adw_modules.success_operations import close_issue_on_success

# Agent name constant
AGENT_SHIPPER = "shipper"


def find_pr_for_branch(branch_name: str, repo_path: str, logger: logging.Logger) -> Optional[str]:
    """Find the PR number for a given branch.

    Args:
        branch_name: Feature branch name
        repo_path: Repository path (owner/repo)
        logger: Logger instance

    Returns:
        PR number as string, or None if not found
    """
    try:
        # Search for PR with this head branch
        result = subprocess.run(
            ["gh", "pr", "list",
             "--repo", repo_path,
             "--head", branch_name,
             "--json", "number",
             "--jq", ".[0].number"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            pr_number = result.stdout.strip()
            logger.info(f"Found PR #{pr_number} for branch {branch_name}")
            return pr_number

        logger.warning(f"No PR found for branch {branch_name}")
        return None

    except Exception as e:
        logger.error(f"Error finding PR: {e}")
        return None


def verify_merge_landed(
    pr_number: str,
    repo_path: str,
    target_branch: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Verify that PR merge actually landed commits on target branch.

    This critical verification step ensures we don't have "phantom merges"
    where GitHub reports success but commits never land on main.

    Args:
        pr_number: PR number that was merged
        repo_path: Repository path (owner/repo)
        target_branch: Target branch to verify (usually 'main')
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        logger.info(f"🔍 Verifying PR #{pr_number} landed on {target_branch}...")

        # Step 1: Get PR merge commit SHA
        result = subprocess.run(
            ["gh", "pr", "view", pr_number,
             "--repo", repo_path,
             "--json", "mergeCommit",
             "--jq", ".mergeCommit.oid"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0 or not result.stdout.strip():
            error_msg = f"Failed to get merge commit for PR #{pr_number}"
            logger.error(error_msg)
            return False, error_msg

        merge_commit_sha = result.stdout.strip()
        logger.info(f"Merge commit SHA: {merge_commit_sha}")

        # Step 2: Fetch latest from origin BEFORE verification
        # This ensures we have the latest state from remote
        logger.info(f"Fetching latest changes from origin/{target_branch}...")
        subprocess.run(["git", "fetch", "origin", target_branch], check=False)

        # Step 3: Verify commit exists on target branch
        # Use git branch --contains to check if merge commit is on target
        result = subprocess.run(
            ["git", "branch", "-r", "--contains", merge_commit_sha],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            error_msg = f"Failed to check if commit {merge_commit_sha} is on {target_branch}"
            logger.error(error_msg)
            logger.error(f"Git error: {result.stderr}")
            return False, error_msg

        branches_containing_commit = result.stdout.strip()
        expected_branch = f"origin/{target_branch}"

        if expected_branch not in branches_containing_commit:
            error_msg = (
                f"❌ PHANTOM MERGE DETECTED!\n"
                f"PR #{pr_number} reported as merged, but commit {merge_commit_sha} "
                f"not found on {target_branch}\n"
                f"Branches containing commit:\n{branches_containing_commit}"
            )
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"✅ Verified: Commit {merge_commit_sha} exists on {expected_branch}")

        # Step 4: Verify merge commit is ancestor of target branch HEAD
        result = subprocess.run(
            ["git", "log", f"origin/{target_branch}", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            latest_commit = result.stdout.strip()
            logger.info(f"Latest commit on origin/{target_branch}: {latest_commit}")

            # Verify our merge commit is reachable from HEAD of target
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", merge_commit_sha, latest_commit],
                check=False
            )

            if result.returncode == 0:
                logger.info(f"✅ Verified: {merge_commit_sha} is ancestor of {target_branch} HEAD")
            else:
                logger.warning(
                    f"Merge commit may not be direct ancestor of HEAD, "
                    f"but is present on {target_branch}"
                )

        return True, None

    except Exception as e:
        error_msg = f"Exception during merge verification: {e}"
        logger.error(error_msg)
        return False, error_msg


def merge_pr_via_github(
    pr_number: str,
    repo_path: str,
    logger: logging.Logger,
    target_branch: str = "main"
) -> Tuple[bool, Optional[str]]:
    """Merge a PR using GitHub's merge API via gh CLI.

    CRITICAL: This function now includes post-merge verification to prevent
    "phantom merges" where GitHub reports success but commits never land.

    Args:
        pr_number: PR number to merge
        repo_path: Repository path (owner/repo)
        logger: Logger instance
        target_branch: Target branch to merge into (default: 'main')

    Returns:
        Tuple of (success, error_message)
    """
    try:
        logger.info(f"Merging PR #{pr_number} using GitHub API...")

        # Use squash merge to combine commits
        result = subprocess.run(
            ["gh", "pr", "merge", pr_number,
             "--repo", repo_path,
             "--squash",
             "--delete-branch"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"✅ GitHub API reports PR #{pr_number} merged successfully")

            # CRITICAL FIX: Don't trust GitHub API - verify merge actually landed!
            logger.info("🔍 Verifying merge actually landed on target branch...")

            verify_success, verify_error = verify_merge_landed(
                pr_number, repo_path, target_branch, logger
            )

            if not verify_success:
                # Phantom merge detected!
                error_msg = (
                    f"❌ CRITICAL: Merge verification failed!\n"
                    f"GitHub API reported PR #{pr_number} as merged, "
                    f"but commits did not land on {target_branch}.\n\n"
                    f"Details: {verify_error}\n\n"
                    f"This is a PHANTOM MERGE. Do NOT close the issue.\n"
                    f"Manual investigation required."
                )
                logger.error(error_msg)
                return False, error_msg

            logger.info(f"✅ Merge verification passed - commits confirmed on {target_branch}")
            return True, None
        else:
            # Check if it's just a branch deletion error (worktree in use)
            if "cannot delete branch" in result.stderr and "used by worktree" in result.stderr:
                logger.warning("PR merged but branch deletion failed (worktree in use)")
                logger.info("Branch will be cleaned up with worktree removal")

                # Still verify the merge landed
                verify_success, verify_error = verify_merge_landed(
                    pr_number, repo_path, target_branch, logger
                )

                if not verify_success:
                    return False, verify_error

                return True, None

            error_msg = f"Failed to merge PR #{pr_number}: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

    except Exception as e:
        error_msg = f"Exception during PR merge: {e}"
        logger.error(error_msg)
        return False, error_msg


def ship_via_pr_merge(branch_name: str, repo_path: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """Ship by merging via GitHub PR.

    This is the preferred method as it:
    - Uses GitHub's merge conflict detection
    - Automatically closes linked issues
    - Handles squash/merge strategies
    - Doesn't require clean working directory

    Args:
        branch_name: Feature branch name
        repo_path: Repository path (owner/repo)
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    # Step 1: Find the PR
    pr_number = find_pr_for_branch(branch_name, repo_path, logger)

    if not pr_number:
        return False, f"No PR found for branch {branch_name}. Cannot merge via GitHub API."

    # Step 2: Merge the PR
    return merge_pr_via_github(pr_number, repo_path, logger)


def validate_state_completeness(state: ADWState, logger: logging.Logger) -> tuple[bool, list[str]]:
    """Validate that all fields in ADWState have values (not None).
    
    Returns:
        tuple of (is_valid, missing_fields)
    """
    # Get the expected fields from ADWStateData model
    expected_fields = {
        "adw_id",
        "issue_number",
        "branch_name",
        "plan_file",
        "issue_class",
        "worktree_path",
        "backend_port",
        "frontend_port",
    }
    
    missing_fields = []
    
    for field in expected_fields:
        value = state.get(field)
        if value is None:
            missing_fields.append(field)
            logger.warning(f"Missing required field: {field}")
        else:
            logger.debug(f"✓ {field}: {value}")
    
    return len(missing_fields) == 0, missing_fields


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree and state
    if len(sys.argv) < 3:
        print("Usage: uv run adw_ship_iso.py <issue-number> <adw-id>")
        print("\nError: Both issue-number and adw-id are required")
        print("Run the complete SDLC workflow before shipping")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_ship_iso")
    state = ADWState.load(adw_id, temp_logger)
    if not state:
        # No existing state found
        logger = setup_logger(adw_id, "adw_ship_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run the complete SDLC workflow before shipping")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run the complete SDLC workflow before shipping")
        sys.exit(1)
    
    # Update issue number from state if available
    issue_number = state.get("issue_number", issue_number)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_ship_iso")
    
    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_ship_iso")
    logger.info(f"ADW Ship Iso starting - ID: {adw_id}, Issue: {issue_number}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"🚢 Starting ship workflow\n"
                           f"📋 Validating state completeness...")
    )
    
    # Step 1: Validate state completeness
    logger.info("Validating state completeness...")
    is_valid, missing_fields = validate_state_completeness(state, logger)
    
    if not is_valid:
        error_msg = f"State validation failed. Missing fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ {error_msg}\n\n"
                               "Please ensure all workflows have been run:\n"
                               "- adw_plan_iso.py (creates plan_file, branch_name, issue_class)\n"
                               "- adw_build_iso.py (implements the plan)\n" 
                               "- adw_test_iso.py (runs tests)\n"
                               "- adw_review_iso.py (reviews implementation)\n"
                               "- adw_document_iso.py (generates docs)")
        )
        sys.exit(1)
    
    logger.info("✅ State validation passed - all fields have values")
    
    # Step 2: Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ Worktree validation failed: {error}")
        )
        sys.exit(1)
    
    worktree_path = state.get("worktree_path")
    logger.info(f"✅ Worktree validated at: {worktree_path}")
    
    # Step 3: Get branch name
    branch_name = state.get("branch_name")
    logger.info(f"Preparing to ship branch: {branch_name}")

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_SHIPPER, f"📋 State validation complete\n"
                           f"🔍 Preparing to ship branch: {branch_name}")
    )

    # Step 4: Get repository path
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        logger.error(f"Failed to get repository info: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER, f"❌ Failed to get repository info: {e}")
        )
        sys.exit(1)

    # Step 5: Ship via GitHub PR merge
    logger.info(f"Shipping {branch_name} via GitHub PR merge...")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_SHIPPER, f"🔀 Shipping {branch_name}...\n"
                           "Using GitHub PR merge API")
    )

    success, error = ship_via_pr_merge(branch_name, repo_path, logger)

    if not success:
        logger.error(f"Failed to ship: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_SHIPPER,
                               f"❌ ZTE Failed - Ship phase failed\n\n"
                               f"Could not automatically approve and merge the PR.\n"
                               f"Please check the ship logs and merge manually if needed.\n\n"
                               f"Error: {error}")
        )
        sys.exit(1)

    logger.info(f"✅ Successfully shipped {branch_name}")

    # Step 6: Close the issue with success comment (using modular success_operations)
    close_issue_on_success(
        adw_id=adw_id,
        issue_number=issue_number,
        branch_name=branch_name,
        agent_name=AGENT_SHIPPER,
        logger=logger
    )
    
    # Save final state
    state.save("adw_ship_iso")
    
    # Post final state summary
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final ship state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )
    
    logger.info("Ship workflow completed successfully")


if __name__ == "__main__":
    main()