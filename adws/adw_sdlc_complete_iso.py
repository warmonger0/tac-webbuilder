#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "psycopg2-binary>=2.9.0"]
# ///

"""
ADW SDLC Complete Iso - Complete Software Development Life Cycle with ALL phases

Usage: uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [flags]

This script runs the COMPLETE ADW SDLC pipeline in isolation with all 10 phases:
1. adw_plan_iso.py - Planning phase (isolated)
2. adw_validate_iso.py - Baseline validation phase (isolated) ✨ NEW
3. adw_build_iso.py - Implementation phase (isolated)
4. adw_lint_iso.py - Linting phase (isolated)
5. adw_test_iso.py - Testing phase (isolated)
6. adw_review_iso.py - Review phase (isolated)
7. adw_document_iso.py - Documentation phase (isolated)
8. adw_ship_iso.py - Ship phase (approve & merge PR)
9. Cleanup - Documentation organization (pure Python)
10. adw_verify_iso.py - Verify phase (post-deployment verification) ✨ NEW

This is the RECOMMENDED workflow for feature implementation. It includes all
quality gates and ships to production when all phases pass.

Flags:
  --skip-e2e: Skip E2E tests
  --skip-resolution: Skip automatic resolution of review failures
  --no-external: Disable external tools (uses inline execution, higher token usage)
  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)

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
from adw_modules.preflight_checks import run_all_preflight_checks
from adw_modules.rate_limit import RateLimitError
from adw_modules.phase_tracker import PhaseTracker

# Circuit breaker: Detect repetitive patterns indicating a loop
MAX_RECENT_COMMENTS_TO_CHECK = 15  # Look at last N comments
MAX_SAME_AGENT_REPEATS = 8  # If same agent posts 8+ times in last N comments = loop


def check_for_loop(issue_number: str, logger, adw_id: str = None) -> None:
    """
    Circuit breaker to detect and prevent infinite loops.
    Detects loops by checking for repetitive patterns in recent comments:
    - Same agent posting repeatedly (e.g., test_resolver multiple times)
    - Same phase repeating without progress

    Args:
        issue_number: GitHub issue number
        logger: Logger instance
        adw_id: Optional ADW ID to check for repetition

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

        # Count agent repetitions in recent comments
        agent_counts = {}
        adw_comment_count = 0

        for comment in recent_comments:
            body = comment.body

            # Count this ADW's comments if adw_id provided
            if adw_id and f"{adw_id}_" in body:
                adw_comment_count += 1

            # Extract agent name from comments like "[ADW-AGENTS] abc123_test_resolver_iter2_0:"
            if "[ADW-AGENTS]" in body and "_" in body:
                # Parse agent name (e.g., "test_resolver", "test_runner", "ops")
                try:
                    # Format is usually: [ADW-AGENTS] {adw_id}_{agent_name}: or {adw_id}_{agent_name}:
                    parts = body.split(":", 1)[0]  # Get everything before first colon
                    if "_" in parts:
                        # Get the last part after underscore (agent name, possibly with iteration)
                        agent_part = parts.split("_")[-1]
                        # Remove iteration numbers (e.g., iter2, iter3)
                        agent_base = agent_part.split("iter")[0].rstrip("_0123456789")

                        if agent_base:
                            agent_counts[agent_base] = agent_counts.get(agent_base, 0) + 1
                except:
                    pass

        # Check for same agent repeating too much
        for agent, count in agent_counts.items():
            if count >= MAX_SAME_AGENT_REPEATS:
                error_msg = (
                    f"🛑 **Loop Detected - Aborting**\n\n"
                    f"Agent `{agent}` has posted **{count} times** in the last {len(recent_comments)} comments.\n"
                    f"This indicates a retry loop where the same operation is repeating without progress.\n\n"
                    f"**Recent Activity Pattern:**\n"
                    f"- Total comments on issue: {len(issue.comments)}\n"
                    f"- `{agent}` repetitions in last {len(recent_comments)}: {count}\n"
                    f"- Threshold: {MAX_SAME_AGENT_REPEATS}\n\n"
                    f"**Action Required:**\n"
                    f"- Manual review and cleanup needed\n"
                    f"- Check for stuck test failures\n"
                    f"- Review error logs for root cause\n"
                    f"- Consider creating a fresh issue if problem persists"
                )
                logger.error(f"Loop detected: Agent '{agent}' posted {count} times in last {len(recent_comments)} comments")
                make_issue_comment(issue_number, error_msg)
                sys.exit(1)

        # Check if this specific ADW has too many comments recently
        if adw_id and adw_comment_count >= 20:
            error_msg = (
                f"🛑 **Loop Detected - Aborting**\n\n"
                f"ADW `{adw_id}` has posted **{adw_comment_count} times** in the last {len(recent_comments)} comments.\n"
                f"This indicates a retry loop within this workflow.\n\n"
                f"**Action Required:** Manual intervention needed."
            )
            logger.error(f"Loop detected: ADW {adw_id} posted {adw_comment_count} times in last {len(recent_comments)} comments")
            make_issue_comment(issue_number, error_msg)
            sys.exit(1)

        logger.info(f"No loop detected. Agent counts in last {len(recent_comments)} comments: {agent_counts}")

    except Exception as e:
        # Don't fail on circuit breaker errors - log and continue
        logger.warning(f"Circuit breaker check failed (continuing anyway): {e}")


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
    Run a phase with automatic retry on crash (leveraging idempotency).

    Args:
        cmd: Command to execute
        phase_name: Name of phase for logging
        issue_number: GitHub issue number
        adw_id: ADW identifier
        logger: Logger instance
        max_retries: Maximum number of retry attempts (default: 2)
        critical: If True, fail the workflow on error; if False, log warning and continue

    Returns:
        Exit code of the phase (0 = success)
    """
    logger.info(f"Running {phase_name} phase with up to {max_retries} retries")

    for attempt in range(max_retries + 1):  # +1 to include initial attempt
        try:
            logger.info(f"{'='*60}")
            if attempt == 0:
                logger.info(f"Starting {phase_name.upper()} phase (initial attempt)")
            else:
                logger.info(f"Retrying {phase_name.upper()} phase (attempt {attempt + 1}/{max_retries + 1})")
                # Post retry notification to GitHub
                try:
                    make_issue_comment(
                        issue_number,
                        format_issue_message(
                            adw_id,
                            "ops",
                            f"🔄 Retrying {phase_name} phase (attempt {attempt + 1}/{max_retries + 1}) - "
                            f"leveraging idempotency for safe retry"
                        )
                    )
                except:
                    pass

            logger.info(f"Running: {' '.join(cmd)}")
            logger.info(f"{'='*60}")

            result = subprocess.run(cmd, capture_output=False, text=True)
            exit_code = result.returncode

            logger.info(f"{phase_name} phase completed with exit code: {exit_code}")

            if exit_code == 0:
                logger.info(f"✓ {phase_name} phase succeeded")
                return 0
            else:
                logger.warning(f"✗ {phase_name} phase failed with exit code: {exit_code}")

                if attempt < max_retries:
                    logger.info(f"Will retry {phase_name} phase (idempotent)")
                else:
                    logger.error(f"{phase_name} phase failed after {max_retries + 1} attempts")

        except Exception as e:
            logger.error(f"{phase_name} phase crashed with exception: {e}", exc_info=True)

            if attempt < max_retries:
                logger.info(f"Will retry {phase_name} phase after crash (idempotent)")
            else:
                logger.error(f"{phase_name} phase crashed after {max_retries + 1} attempts")

                if critical:
                    # For critical phases, fail the workflow
                    cleanup_failed_workflow(
                        adw_id=adw_id,
                        issue_number=issue_number,
                        branch_name=None,
                        phase_name=phase_name.lower(),
                        error_details=f"Phase crashed after {max_retries + 1} attempts: {str(e)}",
                        logger=logger
                    )
                    print(f"❌ {phase_name} phase crashed: {e}")
                    sys.exit(1)
                else:
                    # For non-critical phases, log warning and continue
                    logger.warning(f"⚠️ {phase_name} phase crashed but marked as non-critical, continuing...")
                    print(f"⚠️ {phase_name} phase crashed: {e}, but continuing...")
                    return exit_code

    # If we get here, all retries failed
    if critical:
        logger.error(f"{phase_name} phase failed after all retries")
        cleanup_failed_workflow(
            adw_id=adw_id,
            issue_number=issue_number,
            branch_name=None,
            phase_name=phase_name.lower(),
            error_details=f"Phase failed after {max_retries + 1} attempts",
            logger=logger
        )
        print(f"❌ {phase_name} phase failed after all retries")
        sys.exit(1)
    else:
        logger.warning(f"⚠️ {phase_name} phase failed but marked as non-critical, continuing...")
        print(f"⚠️ {phase_name} phase failed but continuing...")
        return 1


def main():
    """Main entry point."""
    # Check for flags
    skip_e2e = "--skip-e2e" in sys.argv
    skip_resolution = "--skip-resolution" in sys.argv
    use_external = "--no-external" not in sys.argv
    use_optimized_plan = "--use-optimized-plan" in sys.argv
    clean_start = "--clean-start" in sys.argv
    resume_mode = "--resume" in sys.argv

    # Remove flags from argv
    for flag in ["--skip-e2e", "--skip-resolution", "--no-external", "--use-optimized-plan", "--clean-start", "--resume"]:
        if flag in sys.argv:
            sys.argv.remove(flag)

    if len(sys.argv) < 2:
        print("Usage: uv run adw_sdlc_complete_iso.py <issue-number> [adw-id] [flags]")
        print("\n🎯 Complete SDLC: All 10 phases for production-ready features")
        print("\nThis runs the COMPLETE isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Validate (baseline detection) ✨")
        print("  3. Build (isolated)")
        print("  4. Lint (isolated)")
        print("  5. Test (isolated)")
        print("  6. Review (isolated)")
        print("  7. Document (isolated)")
        print("  8. Ship (approve & merge PR)")
        print("  9. Cleanup (organize documentation)")
        print("  10. Verify (post-deployment verification) ✨ NEW")
        print("\nFlags:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --skip-resolution: Skip automatic resolution of review failures")
        print("  --no-external: Disable external tools (higher token usage)")
        print("  --use-optimized-plan: Use inverted context flow planner (77% cost reduction)")
        print("  --clean-start: Remove all previous state for this issue before starting")
        print("  --resume: Resume from where workflow paused (skips completed phases)")
        print("\nNote: External tools are ENABLED by default for 70-95% token reduction")
        print("      Ships to production ONLY after all phases pass")
        print("\n⚠️  --clean-start will DELETE all previous agent dirs, worktrees, and database")
        print("    entries for this issue. Use this to start completely fresh, discarding")
        print("    all previous progress. Without this flag, workflows can resume from where")
        print("    they left off (leveraging idempotency).")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Handle --clean-start flag: Remove all previous state for this issue
    if clean_start:
        print(f"\n{'='*60}")
        print(f"🧹 CLEAN START MODE - Removing all previous state for issue #{issue_number}")
        print(f"{'='*60}")

        # Set up temporary logger for cleanup
        temp_logger = setup_logger("cleanup", "stale_workflow_cleanup")

        # Run cleanup
        cleanup_result = cleanup_stale_workflow(
            issue_number=int(issue_number),
            dry_run=False,
            logger=temp_logger
        )

        print(f"\n📊 Cleanup Results:")
        print(f"  - Agent directories found: {cleanup_result['agent_dirs_found']}")
        print(f"  - Agent directories removed: {cleanup_result['agent_dirs_removed']}")
        print(f"  - Worktrees removed: {cleanup_result['worktrees_removed']}")
        print(f"  - Database entries removed: {cleanup_result['db_entries_removed']}")

        if cleanup_result['errors']:
            print(f"  ⚠️  Errors encountered: {len(cleanup_result['errors'])}")
            for error in cleanup_result['errors'][:3]:  # Show first 3 errors
                print(f"    - {error}")

        if cleanup_result['success']:
            print(f"\n✅ Cleanup completed successfully: {cleanup_result['summary']}")
        else:
            print(f"\n⚠️  Cleanup completed with errors: {cleanup_result['summary']}")
            print(f"Some errors occurred but workflow will continue with fresh state")

        print(f"{'='*60}\n")

    # PRE-FLIGHT CHECKS: Verify it's safe to start workflow
    # Skip cooldown check if using --clean-start (intentional fresh start)
    temp_logger = setup_logger("preflight", "preflight_checks")
    preflight_result = run_all_preflight_checks(
        issue_number=int(issue_number),
        skip_cooldown=clean_start,  # Skip cooldown if clean start requested
        logger=temp_logger
    )

    if not preflight_result.should_proceed:
        print(f"\n{'='*60}")
        print(f"❌ PRE-FLIGHT CHECK FAILED")
        print(f"{'='*60}")
        print(f"Reason: {preflight_result.reason}")
        print(f"\nDetails:")
        for key, value in preflight_result.details.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    - {k}: {v}")
            else:
                print(f"  {key}: {value}")
        print(f"{'='*60}\n")

        # Post to GitHub issue
        try:
            make_issue_comment(
                issue_number,
                f"🛑 **Workflow Start Prevented - Pre-flight Check Failed**\n\n"
                f"**Reason:** {preflight_result.reason}\n\n"
                f"**Details:** {json.dumps(preflight_result.details, indent=2)}\n\n"
                f"**Next Steps:**\n"
                f"- Verify the issue status and linked PRs\n"
                f"- Check if work is already complete\n"
                f"- Wait for active workflows to finish\n"
                f"- Use `--clean-start` flag to override (with caution)"
            )
        except Exception as e:
            print(f"Warning: Could not post pre-flight failure to GitHub: {e}")

        sys.exit(1)

    print(f"\n✅ Pre-flight checks passed - safe to proceed\n")

    # Ensure ADW ID exists with initialized state
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Update state to show full SDLC workflow is active
    from adw_modules.state import ADWState
    logger = setup_logger(adw_id, "adw_sdlc_complete_iso")

    # Initialize phase tracker for resume capability
    phase_tracker = PhaseTracker(adw_id)

    # Define all phases in order
    ALL_PHASES = ["Plan", "Validate", "Build", "Lint", "Test", "Review", "Document", "Ship", "Cleanup", "Verify"]

    # Handle resume mode
    if resume_mode:
        completed_phases = phase_tracker.get_completed_phases()
        next_phase = phase_tracker.get_next_phase_to_run(ALL_PHASES)

        logger.info(f"🔄 RESUME MODE ENABLED")
        logger.info(f"Completed phases: {completed_phases}")
        logger.info(f"Next phase to run: {next_phase}")

        print(f"\n{'='*60}")
        print(f"🔄 RESUME MODE")
        print(f"{'='*60}")
        print(f"Completed phases: {', '.join(completed_phases) if completed_phases else 'None'}")
        print(f"Resuming from: {next_phase if next_phase else 'All complete'}")
        print(f"{'='*60}\n")

        if not next_phase:
            print("✅ All phases already completed, nothing to resume")
            sys.exit(0)
    else:
        # Fresh start - reset phase tracker if clean_start
        if clean_start:
            phase_tracker.reset()
            logger.info("🧹 Reset phase tracker for clean start")

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

    state = ADWState.load(adw_id, logger)
    state.update(
        workflow_template="adw_sdlc_complete_iso"
        # Note: status managed by PhaseQueueRepository (database is SSoT)
    )
    state.save("adw_sdlc_complete_iso")
    logger.info("✅ Updated state to show full SDLC workflow active")

    # Post initial message
    logger.info("Attempting to post initial GitHub comment...")
    try:
        # Build status messages
        cleanup_msg = ""
        if clean_start:
            cleanup_msg = f"\n\n🧹 **Clean Start Mode**: All previous state cleared before starting"

        resume_msg = ""
        if resume_mode:
            completed = phase_tracker.get_completed_phases()
            next_phase = phase_tracker.get_next_phase_to_run(ALL_PHASES)
            resume_msg = f"\n\n🔄 **Resume Mode**: Continuing from {next_phase} (skipping {len(completed)} completed phases)"

        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎯 **{'Resuming' if resume_mode else 'Starting'} Complete SDLC Workflow**{cleanup_msg}{resume_msg}\n\n"
            "This workflow will execute ALL 10 phases:\n"
            "1. ✍️ Plan the implementation\n"
            "2. 📊 Validate baseline (detect inherited errors)\n"
            "3. 🔨 Build the solution\n"
            "4. 🧹 Lint the code\n"
            "5. 🧪 Test the code\n"
            "6. 👀 Review the implementation\n"
            "7. 📚 Generate documentation\n"
            "8. 🚢 Ship to production\n"
            "9. 🗂️ Cleanup and organize\n"
            "10. 🔍 Verify deployment (post-ship verification) ✨\n\n"
            f"**Configuration:**\n"
            f"- External tools: {'✅ Enabled' if use_external else '❌ Disabled'}\n"
            f"- Optimized planner: {'✅ Enabled' if use_optimized_plan else '❌ Disabled'}\n"
            f"- Skip E2E: {'✅ Yes' if skip_e2e else '❌ No'}\n"
            f"- Auto-resolution: {'❌ Disabled' if skip_resolution else '✅ Enabled'}\n"
            f"- Clean start: {'✅ Yes (fresh state)' if clean_start else '❌ No (can resume)'}",
        )
        logger.info("✅ Initial GitHub comment posted successfully")
    except Exception as e:
        logger.error(f"Failed to post initial comment: {e}", exc_info=True)
        print(f"Warning: Failed to post initial comment: {e}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ========================================
    # PHASE 1: PLAN
    # ========================================
    if phase_tracker.should_skip_phase("Plan", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 1/10: PLAN - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Plan phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
        broadcast_phase_update(adw_id, "Plan", "running", logger=logger)
        phase_tracker.set_current_phase("Plan")

        plan_script = "adw_plan_iso_optimized.py" if use_optimized_plan else "adw_plan_iso.py"
        plan_cmd = [
            "uv",
            "run",
            os.path.join(script_dir, plan_script),
            issue_number,
            adw_id,
        ]
        print(f"\n{'='*60}")
        print(f"PHASE 1/10: PLAN ({plan_script})")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 1: PLAN with command: {' '.join(plan_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=plan_cmd,
            phase_name="Plan",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=2,  # Allow 2 retries (3 total attempts)
            critical=True   # Fail workflow if all retries fail
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Plan")
        logger.info("✅ Plan phase marked as completed")

    # ========================================
    # PHASE 2: VALIDATE (NEW)
    # ========================================
    if phase_tracker.should_skip_phase("Validate", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 2/10: VALIDATE - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Validate phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
        broadcast_phase_update(adw_id, "Validate", "running", logger=logger)
        phase_tracker.set_current_phase("Validate")

        validate_cmd = [
            "uv",
            "run",
            os.path.join(script_dir, "adw_validate_iso.py"),
            issue_number,
            adw_id,
        ]
        print(f"\n{'='*60}")
        print(f"PHASE 2/10: VALIDATE (Baseline Error Detection)")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 2: VALIDATE with command: {' '.join(validate_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=validate_cmd,
            phase_name="Validate",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=1,  # Allow 1 retry (2 total attempts)
            critical=False  # Non-critical: can continue if fails
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Validate")
        logger.info("✅ Validate phase marked as completed")

    # ========================================
    # PHASE 3: BUILD (formerly PHASE 2)
    # ========================================
    if phase_tracker.should_skip_phase("Build", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 3/10: BUILD - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Build phase (already completed)")
    else:
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
        print(f"PHASE 3/10: BUILD")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 3: BUILD with command: {' '.join(build_cmd)}")

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
    # PHASE 4: LINT
    # ========================================
    if phase_tracker.should_skip_phase("Lint", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 4/10: LINT - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Lint phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
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
        print(f"PHASE 4/10: LINT")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 4: LINT with command: {' '.join(lint_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=lint_cmd,
            phase_name="Lint",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=2,  # Allow 2 retries (3 total attempts)
            critical=True   # Fail workflow if all retries fail
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Lint")
        logger.info("✅ Lint phase marked as completed")

    # ========================================
    # PHASE 5: TEST
    # ========================================
    if phase_tracker.should_skip_phase("Test", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 5/10: TEST - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Test phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
        broadcast_phase_update(adw_id, "Test", "running", logger=logger)
        phase_tracker.set_current_phase("Test")

        test_cmd = [
            "uv",
            "run",
            os.path.join(script_dir, "adw_test_iso.py"),
            issue_number,
            adw_id,
            "--skip-e2e",  # Always skip E2E in SDLC workflows
        ]
        if not use_external:
            test_cmd.append("--no-external")

        print(f"\n{'='*60}")
        print(f"PHASE 5/10: TEST")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 5: TEST with command: {' '.join(test_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=test_cmd,
            phase_name="Test",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=2,  # Allow 2 retries (3 total attempts)
            critical=True   # Fail workflow if all retries fail
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Test")
        logger.info("✅ Test phase marked as completed")

    # ========================================
    # PHASE 6: REVIEW
    # ========================================
    if phase_tracker.should_skip_phase("Review", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 6/10: REVIEW - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Review phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
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

        print(f"\n{'='*60}")
        print(f"PHASE 6/10: REVIEW")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 6: REVIEW with command: {' '.join(review_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=review_cmd,
            phase_name="Review",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=2,  # Allow 2 retries (3 total attempts)
            critical=True   # Fail workflow if all retries fail
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Review")
        logger.info("✅ Review phase marked as completed")

    # ========================================
    # PHASE 7: DOCUMENT
    # ========================================
    if phase_tracker.should_skip_phase("Document", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 7/10: DOCUMENT - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Document phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
        broadcast_phase_update(adw_id, "Document", "running", logger=logger)
        phase_tracker.set_current_phase("Document")

        document_cmd = [
            "uv",
            "run",
            os.path.join(script_dir, "adw_document_iso.py"),
            issue_number,
            adw_id,
        ]
        print(f"\n{'='*60}")
        print(f"PHASE 7/10: DOCUMENT")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 7: DOCUMENT with command: {' '.join(document_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=document_cmd,
            phase_name="Document",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=1,  # Allow 1 retry (2 total attempts)
            critical=False  # Non-critical: can continue if fails
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Document")
        logger.info("✅ Document phase marked as completed")

    # ========================================
    # PHASE 8: SHIP
    # ========================================
    if phase_tracker.should_skip_phase("Ship", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 8/10: SHIP - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Ship phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
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
        print(f"PHASE 8/10: SHIP")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 8: SHIP with command: {' '.join(ship_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=ship_cmd,
            phase_name="Ship",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=2,  # Allow 2 retries (3 total attempts)
            critical=True   # Fail workflow if all retries fail
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Ship")
        logger.info("✅ Ship phase marked as completed")

    # ========================================
    # PHASE 9: CLEANUP
    # ========================================
    if phase_tracker.should_skip_phase("Cleanup", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 9/10: CLEANUP - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Cleanup phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
        broadcast_phase_update(adw_id, "Cleanup", "running", logger=logger)
        phase_tracker.set_current_phase("Cleanup")

        print(f"\n{'='*60}")
        print(f"PHASE 9/10: CLEANUP")
        print(f"{'='*60}")
        print(f"Running cleanup operations directly (pure Python, no LLM)...")

        try:
            # Set up logger for cleanup
            cleanup_logger = setup_logger(adw_id, "cleanup_operations")

            # Post initial cleanup message
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "🧹 Starting cleanup (pure Python, no LLM calls)...")
            )

            # Run cleanup directly
            cleanup_result = cleanup_shipped_issue(
                issue_number=issue_number,
                adw_id=adw_id,
                skip_worktree=False,
                dry_run=False,
                logger=cleanup_logger
            )

            if cleanup_result["success"]:
                print(f"✅ Cleanup completed: {cleanup_result['summary']}")

                # Post success message
                summary_msg = f"✅ **Cleanup completed**\n\n"
                if cleanup_result["docs_moved"] > 0:
                    summary_msg += f"📁 Organized {cleanup_result['docs_moved']} documentation files\n"
                if cleanup_result["worktree_removed"]:
                    summary_msg += f"🗑️ Removed worktree and freed resources\n"
                if cleanup_result["errors"]:
                    summary_msg += f"\n⚠️ {len(cleanup_result['errors'])} warnings (non-fatal)\n"

                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "cleanup", summary_msg)
                )
            else:
                print(f"⚠️ Cleanup had errors: {cleanup_result['errors']}")
                # Cleanup failure shouldn't block SDLC completion
                print("WARNING: Cleanup had errors but SDLC is still considered successful")

                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "cleanup",
                        f"⚠️ Cleanup completed with warnings\n\n"
                        f"Errors: {', '.join(cleanup_result['errors'][:3])}"
                    )
                )
        except Exception as e:
            print(f"⚠️ Cleanup exception: {e}")
            # Cleanup failure shouldn't block SDLC completion
            print("WARNING: Cleanup failed but SDLC is still considered successful")

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Cleanup")
        logger.info("✅ Cleanup phase marked as completed")

    # ========================================
    # PHASE 10: VERIFY
    # ========================================
    if phase_tracker.should_skip_phase("Verify", resume_mode):
        print(f"\n{'='*60}")
        print(f"PHASE 10/10: VERIFY - ⏭️  SKIPPED (already completed)")
        print(f"{'='*60}")
        logger.info("Skipping Verify phase (already completed)")
    else:
        # Event-driven broadcast - immediate WebSocket notification (0ms latency)
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
        print(f"PHASE 10/10: VERIFY (Post-Deployment Verification)")
        print(f"{'='*60}")
        logger.info(f"Starting PHASE 10: VERIFY with command: {' '.join(verify_cmd)}")

        exit_code = run_phase_with_retry(
            cmd=verify_cmd,
            phase_name="Verify",
            issue_number=issue_number,
            adw_id=adw_id,
            logger=logger,
            max_retries=1,  # Allow 1 retry (2 total attempts)
            critical=False  # Non-critical: can continue if fails
        )

        # Mark phase as completed
        phase_tracker.mark_phase_completed("Verify")
        logger.info("✅ Verify phase marked as completed")

    # ========================================
    # COMPLETION
    # ========================================
    print(f"\n{'='*60}")
    print(f"🎉 COMPLETE SDLC FINISHED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"ADW ID: {adw_id}")
    print(f"All 10 phases completed successfully!")
    print(f"✅ Code has been shipped to production and verified!")

    # Record workflow end_time (status is in database)
    logger.info("Recording workflow end_time")
    state = ADWState.load(adw_id, logger)
    from datetime import datetime
    end_time = datetime.now()
    state.update(
        end_time=end_time.isoformat()
    )
    state.save("adw_sdlc_complete_iso")
    logger.info("✅ Workflow end_time recorded")

    # Trigger cost synchronization
    print(f"\n📊 Syncing workflow costs...")
    trigger_cost_sync(adw_id)

    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To manually clean up: ./scripts/purge_tree.sh {adw_id}")

    try:
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🎉 **Complete SDLC Finished!**\n\n"
            "✅ Phase 1: Plan completed\n"
            "✅ Phase 2: Validate completed ✨\n"
            "✅ Phase 3: Build completed\n"
            "✅ Phase 4: Lint completed\n"
            "✅ Phase 5: Test completed\n"
            "✅ Phase 6: Review completed\n"
            "✅ Phase 7: Documentation completed\n"
            "✅ Phase 8: Ship completed\n"
            "✅ Phase 9: Cleanup completed\n"
            "✅ Phase 10: Verify completed ✨\n\n"
            "🚢 **Code has been shipped to production and verified!**",
        )
    except:
        pass


if __name__ == "__main__":
    main()
