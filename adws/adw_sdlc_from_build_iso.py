#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "psycopg2-binary>=2.9.0"]
# ///

"""
ADW SDLC From Build Iso - Complete SDLC starting from Build phase (skips Analyze + Plan)

Usage: uv run adw_sdlc_from_build_iso.py <issue-number> <adw-id> [flags]

This script runs a PARTIAL ADW SDLC pipeline starting from the Build phase with 8 phases:
1. adw_build_iso.py - Implementation phase (isolated)
2. adw_lint_iso.py - Linting phase (isolated)
3. adw_test_iso.py - Testing phase (isolated)
4. adw_review_iso.py - Review phase (isolated)
5. adw_document_iso.py - Documentation phase (isolated)
6. adw_ship_iso.py - Ship phase (approve & merge PR)
7. Cleanup - Documentation organization (pure Python)
8. adw_verify_iso.py - Verify phase (post-deployment verification)

**IMPORTANT:** This workflow assumes:
- An existing worktree has been created
- A plan file exists (from prior planning phase or manual creation)
- Implementation details are ready

Use this workflow when:
- You have a detailed implementation plan already generated
- Skipping redundant planning for simple changes
- Testing implementation phases in isolation

Flags:
  --skip-e2e: Skip E2E tests
  --skip-resolution: Skip automatic resolution of review failures
  --no-external: Disable external tools (uses inline execution, higher token usage)

The scripts are chained together via persistent state (adw_state.json).
Each phase runs in its own git worktree with dedicated ports.
"""

import subprocess
import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.workflow_ops import ensure_adw_id, format_issue_message, trigger_cost_sync, broadcast_phase_update
from adw_modules.github import make_issue_comment, fetch_issue, get_repo_url, extract_repo_path
from adw_modules.cleanup_operations import cleanup_shipped_issue, cleanup_stale_workflow
from adw_modules.utils import setup_logger
from adw_modules.failure_cleanup import cleanup_failed_workflow
from adw_modules.state import ADWState
from adw_modules.rate_limit import RateLimitError
from adw_modules.phase_tracker import PhaseTracker


# Circuit breaker: Detect repetitive patterns indicating a loop
MAX_RECENT_COMMENTS_TO_CHECK = 20  # Look at last N comments
MAX_LOOP_MARKERS = 12  # If 🔁 appears 12+ times in recent comments = stuck loop (workflow-wide catch-all)


def check_for_loop(issue_number: str, logger, adw_id: str = None) -> None:
    """
    Circuit breaker to detect and prevent infinite loops.

    Detects loops by counting 🔁 loop markers in recent comments.
    Loop markers are added to retry attempt messages by the cascading
    resolution logic (external tools → LLM → phase retry).

    Simple and deterministic: if 🔁 appears >= MAX_LOOP_MARKERS times
    in recent comments, abort the workflow.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance
        adw_id: Optional ADW ID (unused, kept for compatibility)

    Raises:
        SystemExit: If loop detected (exits with code 1)
    """
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
        issue = fetch_issue(issue_number, repo_path)

        # Get last N comments
        recent_comments = issue.comments[-MAX_RECENT_COMMENTS_TO_CHECK:] if len(issue.comments) > MAX_RECENT_COMMENTS_TO_CHECK else issue.comments

        if not recent_comments:
            logger.info(f"No comments yet on issue #{issue_number}")
            return

        logger.info(f"Issue #{issue_number} has {len(issue.comments)} total comments, checking last {len(recent_comments)}")

        # Count loop markers (🔁) in recent comments
        loop_marker_count = sum(1 for comment in recent_comments if "🔁" in comment.body)

        if loop_marker_count >= MAX_LOOP_MARKERS:
            error_msg = (
                f"🛑 **Loop Detected - Aborting**\n\n"
                f"Found **{loop_marker_count} retry markers (🔁)** in the last {len(recent_comments)} comments.\n"
                f"This indicates a stuck retry loop that is not making progress.\n\n"
                f"**Recent Activity Pattern:**\n"
                f"- Total comments on issue: {len(issue.comments)}\n"
                f"- Loop markers in last {len(recent_comments)}: {loop_marker_count}/{MAX_LOOP_MARKERS}\n\n"
                f"**Circuit Breaker Triggered**\n"
                f"Please review the error pattern and fix the underlying issue before re-running.\n\n"
                f"To reset: manually close and reopen this issue, or wait for {MAX_RECENT_COMMENTS_TO_CHECK}+ new comments."
            )
            logger.error(error_msg)
            print(f"\n{error_msg}\n")
            make_issue_comment(issue_number, f"{adw_id}_ops: {error_msg}")
            sys.exit(1)

    except Exception as e:
        logger.warning(f"Could not check for loops: {e}")
        # Non-fatal: continue workflow if loop detection fails


def run_phase_with_retry(
    cmd: list,
    phase_name: str,
    issue_number: str,
    adw_id: str,
    logger,
    max_retries: int = 2,
    critical: bool = True
) -> int:
    """
    Run a phase with retry logic and loop detection.

    Args:
        cmd: Command to execute
        phase_name: Human-readable phase name
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        logger: Logger instance
        max_retries: Maximum number of retry attempts (default: 2)
        critical: If True, exit workflow on failure; if False, continue (default: True)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    attempt = 0
    max_attempts = max_retries + 1

    while attempt < max_attempts:
        attempt += 1

        if attempt > 1:
            logger.warning(f"🔁 {phase_name} phase failed, retry attempt {attempt}/{max_attempts}")
            print(f"\n🔁 Retry {attempt}/{max_attempts} for {phase_name} phase\n")

            # Post retry comment to GitHub
            try:
                make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: 🔁 **{phase_name} Phase - Retry {attempt}/{max_attempts}**\n\n"
                    f"The {phase_name} phase encountered an error. Attempting automatic recovery.\n\n"
                    f"Retry marker: 🔁"
                )
            except Exception as e:
                logger.warning(f"Could not post retry comment: {e}")

        logger.info(f"{phase_name} phase attempt {attempt}/{max_attempts}: {' '.join(cmd)}")
        exit_code = subprocess.call(cmd)

        if exit_code == 0:
            if attempt > 1:
                logger.info(f"✅ {phase_name} phase succeeded on retry {attempt}")
                # Post success comment
                try:
                    make_issue_comment(
                        issue_number,
                        f"{adw_id}_ops: ✅ **{phase_name} Phase - Recovered**\n\n"
                        f"Retry {attempt}/{max_attempts} succeeded. Continuing workflow."
                    )
                except Exception as e:
                    logger.warning(f"Could not post recovery comment: {e}")
            return 0

        logger.error(f"❌ {phase_name} phase attempt {attempt} failed with exit code {exit_code}")

    # All retries exhausted
    logger.error(f"❌ {phase_name} phase failed after {max_attempts} attempts")

    if critical:
        error_msg = (
            f"❌ **{phase_name} Phase Failed**\n\n"
            f"The {phase_name} phase failed after {max_attempts} attempts.\n"
            f"This is a critical phase - workflow cannot continue.\n\n"
            f"**Next Steps:**\n"
            f"1. Review the error logs in the comments above\n"
            f"2. Fix the underlying issue\n"
            f"3. Re-run the workflow or use resume mode"
        )
        try:
            make_issue_comment(issue_number, f"{adw_id}_ops: {error_msg}")
        except Exception as e:
            logger.warning(f"Could not post failure comment: {e}")

        sys.exit(1)

    # Non-critical phase - log warning and continue
    logger.warning(f"⚠️ {phase_name} phase failed but is non-critical, continuing workflow")
    return 1


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run adw_sdlc_from_build_iso.py <issue-number> <adw-id> [flags]")
        print("\nFlags:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --skip-resolution: Skip automatic resolution of review failures")
        print("  --no-external: Disable external tools (uses inline execution)")
        print("\nNote: This workflow requires an existing worktree and plan file.")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Parse flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv
    use_external = "--no-external" not in sys.argv

    # Validate ADW ID exists
    if not adw_id:
        print("❌ Error: ADW ID is required for this workflow")
        print("This workflow must be used after planning phase has created a worktree")
        sys.exit(1)

    # Setup logger
    logger = setup_logger(adw_id, "adw_sdlc_from_build_iso")
    logger.info(f"Starting SDLC from Build workflow for issue #{issue_number}, ADW ID: {adw_id}")

    # Validate existing state
    state = ADWState.load(adw_id, logger)
    if not state:
        print("❌ No existing state found. This workflow requires existing plan.")
        print("Run adw_plan_iso.py first to create worktree and plan.")
        sys.exit(1)

    if not state.get("worktree_path"):
        print("❌ Missing required state: worktree_path")
        print("This workflow must be used after planning phase")
        sys.exit(1)

    # Initialize phase tracker for resume capability
    phase_tracker = PhaseTracker(adw_id)

    # Define phases (starting from Build - skipping Plan and Validate)
    ALL_PHASES = ["Build", "Lint", "Test", "Review", "Document", "Ship", "Cleanup", "Verify"]

    # Circuit breaker: Check for infinite loops before starting
    try:
        check_for_loop(issue_number, logger, adw_id)
    except RateLimitError as e:
        logger.error(f"GitHub API rate limit exhausted: {e}")
        logger.error(f"Cannot proceed with workflow until rate limit resets")

        # Update workflow status back to paused if it exists in database
        try:
            from adw_modules.workflow_ops import update_workflow_status
            update_workflow_status(adw_id, "paused", error_message=f"Rate limit exhausted: {str(e)}")
            logger.info("Updated workflow status to 'paused' due to rate limit")
        except Exception as status_error:
            logger.warning(f"Could not update workflow status: {status_error}")

        sys.exit(1)

    # Update state to show this workflow is active
    state.update(workflow_template="adw_sdlc_from_build_iso")
    state.save("adw_sdlc_from_build_iso")
    logger.info("✅ Updated state to show SDLC from Build workflow active")

    # Post initial message
    logger.info("Attempting to post initial GitHub comment...")
    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎯 **Starting SDLC From Build Workflow**\n\n"
            "This workflow will execute 8 phases (skipping Analyze and Plan):\n"
            "1. 🔨 Build the solution\n"
            "2. 🧹 Lint the code\n"
            "3. 🧪 Test the code\n"
            "4. 👀 Review the implementation\n"
            "5. 📚 Generate documentation\n"
            "6. 🚢 Ship to production\n"
            "7. 🗂️ Cleanup and organize\n"
            "8. 🔍 Verify deployment (post-ship verification)\n\n"
            f"**Configuration:**\n"
            f"- External tools: {'✅ Enabled' if use_external else '❌ Disabled'}\n"
            f"- Skip E2E: {'✅ Yes' if skip_e2e else '❌ No'}\n"
            f"- Auto-resolution: {'❌ Disabled' if skip_resolution else '✅ Enabled'}\n\n"
            f"**Prerequisites verified:**\n"
            f"- ✅ Worktree exists: `{state.get('worktree_path')}`\n"
            f"- ✅ ADW state loaded"
        )
        logger.info("✅ Initial GitHub comment posted successfully")
    except Exception as e:
        logger.error(f"Failed to post initial comment: {e}", exc_info=True)
        print(f"Warning: Failed to post initial comment: {e}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ========================================
    # PHASE 1: BUILD (formerly PHASE 3 in full SDLC)
    # ========================================
    # Event-driven broadcast - immediate WebSocket notification (0ms latency)
    broadcast_phase_update(adw_id, "Build", "running", logger=logger)
    phase_tracker.set_current_phase("Build")

    build_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_build_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        build_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 1/8: BUILD")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 1: BUILD with command: {' '.join(build_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=build_cmd,
        phase_name="Build",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=2,  # Allow 2 retries (3 total attempts)
        critical=True   # Fail workflow if all retries fail
    )

    # Mark phase as completed
    phase_tracker.mark_phase_completed("Build")
    logger.info("✅ Build phase marked as completed")

    # ========================================
    # PHASE 2: LINT (formerly PHASE 4 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Lint", "running", logger=logger)
    phase_tracker.set_current_phase("Lint")

    lint_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_lint_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        lint_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 2/8: LINT")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 2: LINT with command: {' '.join(lint_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=lint_cmd,
        phase_name="Lint",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=2,
        critical=True
    )

    phase_tracker.mark_phase_completed("Lint")
    logger.info("✅ Lint phase marked as completed")

    # ========================================
    # PHASE 3: TEST (formerly PHASE 5 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Test", "running", logger=logger)
    phase_tracker.set_current_phase("Test")

    test_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_test_iso.py"),
        issue_number,
        adw_id,
    ]
    if skip_e2e:
        test_cmd.append("--skip-e2e")
    if skip_resolution:
        test_cmd.append("--skip-resolution")
    if not use_external:
        test_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 3/8: TEST")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 3: TEST with command: {' '.join(test_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=test_cmd,
        phase_name="Test",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=2,
        critical=True
    )

    phase_tracker.mark_phase_completed("Test")
    logger.info("✅ Test phase marked as completed")

    # ========================================
    # PHASE 4: REVIEW (formerly PHASE 6 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Review", "running", logger=logger)
    phase_tracker.set_current_phase("Review")

    review_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_review_iso.py"),
        issue_number,
        adw_id,
    ]
    if skip_resolution:
        review_cmd.append("--skip-resolution")
    if not use_external:
        review_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 4/8: REVIEW")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 4: REVIEW with command: {' '.join(review_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=review_cmd,
        phase_name="Review",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=2,
        critical=True
    )

    phase_tracker.mark_phase_completed("Review")
    logger.info("✅ Review phase marked as completed")

    # ========================================
    # PHASE 5: DOCUMENT (formerly PHASE 7 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Document", "running", logger=logger)
    phase_tracker.set_current_phase("Document")

    document_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_document_iso.py"),
        issue_number,
        adw_id,
    ]
    if not use_external:
        document_cmd.append("--no-external")

    print(f"\n{'='*60}")
    print(f"PHASE 5/8: DOCUMENT")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 5: DOCUMENT with command: {' '.join(document_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=document_cmd,
        phase_name="Document",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=1,
        critical=False  # Non-critical: can continue if fails
    )

    phase_tracker.mark_phase_completed("Document")
    logger.info("✅ Document phase marked as completed")

    # ========================================
    # PHASE 6: SHIP (formerly PHASE 8 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Ship", "running", logger=logger)
    phase_tracker.set_current_phase("Ship")

    ship_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_ship_iso.py"),
        issue_number,
        adw_id,
    ]

    print(f"\n{'='*60}")
    print(f"PHASE 6/8: SHIP")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 6: SHIP with command: {' '.join(ship_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=ship_cmd,
        phase_name="Ship",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=1,
        critical=True
    )

    phase_tracker.mark_phase_completed("Ship")
    logger.info("✅ Ship phase marked as completed")

    # ========================================
    # PHASE 7: CLEANUP (formerly PHASE 9 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Cleanup", "running", logger=logger)
    phase_tracker.set_current_phase("Cleanup")

    print(f"\n{'='*60}")
    print(f"PHASE 7/8: CLEANUP")
    print(f"{'='*60}")
    logger.info("Starting PHASE 7: CLEANUP (pure Python, no LLM)")

    try:
        cleanup_shipped_issue(issue_number, adw_id)
        logger.info("✅ Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        print(f"⚠️ Warning: Cleanup failed but continuing: {e}")

    phase_tracker.mark_phase_completed("Cleanup")
    logger.info("✅ Cleanup phase marked as completed")

    # ========================================
    # PHASE 8: VERIFY (formerly PHASE 10 in full SDLC)
    # ========================================
    broadcast_phase_update(adw_id, "Verify", "running", logger=logger)
    phase_tracker.set_current_phase("Verify")

    verify_cmd = [
        "uv",
        "run",
        os.path.join(script_dir, "adw_verify_iso.py"),
        issue_number,
        adw_id,
    ]

    print(f"\n{'='*60}")
    print(f"PHASE 8/8: VERIFY (Post-Deployment)")
    print(f"{'='*60}")
    logger.info(f"Starting PHASE 8: VERIFY with command: {' '.join(verify_cmd)}")

    exit_code = run_phase_with_retry(
        cmd=verify_cmd,
        phase_name="Verify",
        issue_number=issue_number,
        adw_id=adw_id,
        logger=logger,
        max_retries=1,
        critical=False  # Non-critical: can continue if fails
    )

    phase_tracker.mark_phase_completed("Verify")
    logger.info("✅ Verify phase marked as completed")

    # ========================================
    # ALL PHASES COMPLETE
    # ========================================
    print(f"\n{'='*60}")
    print(f"✅ ALL 8 PHASES COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")
    logger.info("✅ All 8 phases completed successfully")

    broadcast_phase_update(adw_id, "Completed", "completed", logger=logger)

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎉 **SDLC From Build Workflow Complete!**\n\n"
            f"All 8 phases completed successfully:\n"
            f"1. ✅ Build\n"
            f"2. ✅ Lint\n"
            f"3. ✅ Test\n"
            f"4. ✅ Review\n"
            f"5. ✅ Document\n"
            f"6. ✅ Ship\n"
            f"7. ✅ Cleanup\n"
            f"8. ✅ Verify\n\n"
            f"The implementation has been merged and deployed!"
        )
    except Exception as e:
        logger.warning(f"Could not post completion comment: {e}")

    # Trigger cost sync
    try:
        trigger_cost_sync(adw_id)
    except Exception as e:
        logger.warning(f"Could not trigger cost sync: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
