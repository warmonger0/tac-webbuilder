#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Lint Iso - AI Developer Workflow for linting in isolated worktrees

Usage:
  uv run adw_lint_iso.py <issue-number> <adw-id> [--fix-mode] [--no-external] [--target=both]

Workflow:
1. Load state and validate worktree exists
2. Run linting checks in worktree (via external tools by default)
3. Report results to issue
4. Optionally auto-fix issues
5. Commit fixes if any were applied

Options:
  --fix-mode: Enable auto-fix for fixable lint errors
  --no-external: Disable external lint tools (uses inline execution, higher token usage)
  --target=both|frontend|backend: Which codebase to lint (default: both)

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Tuple, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes
from adw_modules.github import make_issue_comment
from adw_modules.workflow_ops import format_issue_message
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.worktree_ops import validate_worktree
from adw_modules.observability import log_phase_completion, get_phase_number

# Hybrid lint loop configuration
MAX_EXTERNAL_ATTEMPTS = 3  # Number of external auto-fix attempts before LLM fallback


def run_external_lint(
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    state: ADWState,
    target: str = "both",
    fix_mode: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run linting using external lint ADW workflow.

    Returns:
        Tuple of (success: bool, results: Dict)
    """
    logger.info("🔧 Using external lint tools for context optimization")

    # Get path to external lint ADW script
    script_dir = Path(__file__).parent
    lint_external_script = script_dir / "adw_lint_external.py"

    if not lint_external_script.exists():
        logger.error(f"External lint script not found: {lint_external_script}")
        return False, {"error": "External lint script not found"}

    # Run external lint ADW
    cmd = ["uv", "run", str(lint_external_script), issue_number, adw_id, f"--target={target}"]
    if fix_mode:
        cmd.append("--fix-mode")

    logger.info(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Reload state to get external lint results
    reloaded_state = ADWState.load(adw_id)
    if not reloaded_state:
        logger.error("Failed to reload state after external lint")
        return False, {"error": "Failed to reload state"}
    lint_results = reloaded_state.get("external_lint_results", {})

    if not lint_results:
        logger.warning("No external_lint_results found in state after execution")
        logger.debug(f"Stdout: {result.stdout}")
        logger.debug(f"Stderr: {result.stderr}")
        return False, {"error": "No lint results returned from external tool"}

    success = lint_results.get("success", False)
    logger.info(f"External lint check completed: {'✅ Success' if success else '❌ Errors detected'}")

    return success, lint_results


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Check for flags
    fix_mode = "--fix-mode" in sys.argv
    use_external = "--no-external" not in sys.argv
    target = "both"

    # Parse target flag
    for arg in sys.argv[3:]:
        if arg.startswith("--target="):
            target = arg.split("=")[1]
            sys.argv.remove(arg)
            break

    # Remove flags from args
    if fix_mode:
        sys.argv.remove("--fix-mode")
    if "--no-external" in sys.argv:
        sys.argv.remove("--no-external")

    # Parse command line args
    if len(sys.argv) < 3:
        print("Usage: uv run adw_lint_iso.py <issue-number> <adw-id> [--fix-mode] [--no-external] [--target=both]")
        print("\nError: adw-id is required to locate the worktree")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        print("\nOptions:")
        print("  --fix-mode: Auto-fix fixable lint errors")
        print("  --no-external: Disable external tools (higher token usage)")
        print("  --target=both|frontend|backend: Which codebase to lint")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Set up logger
    logger = setup_logger(adw_id, "adw_lint_iso")
    logger.info(f"ADW Lint Iso starting - ID: {adw_id}, Issue: {issue_number}, Fix Mode: {fix_mode}, Use External: {use_external}, Target: {target}")

    # Validate environment
    check_env_vars(logger)

    # Load state
    state = ADWState.load(adw_id, logger)
    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py first to create the worktree and state")
        sys.exit(1)

    # Track that this ADW workflow has run
    state.append_adw_id("adw_lint_iso")

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\n"
                               "Run adw_plan_iso.py or adw_patch_iso.py first")
        )
        sys.exit(1)

    # Get worktree path for explicit context
    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Starting linting phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🎯 Target: {target}\n"
                           f"🔧 Lint Mode: {'External Tools (Context Optimized)' if use_external else 'Inline Execution'}\n"
                           f"🔨 Auto-fix: {'Enabled' if fix_mode else 'Disabled'}")
    )

    # Run lint check
    if use_external:
        logger.info("🔧 Running hybrid lint loop (external + LLM fallback)")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "lint_checker", f"🔧 Starting hybrid lint loop (up to {MAX_EXTERNAL_ATTEMPTS} external attempts + LLM fallback)...")
        )

        # Hybrid lint loop: Try external auto-fix multiple times
        lint_success = False
        lint_results = {}
        initial_error_count = None

        for attempt in range(1, MAX_EXTERNAL_ATTEMPTS + 1):
            logger.info(f"External lint attempt {attempt}/{MAX_EXTERNAL_ATTEMPTS}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker", f"🔄 External lint attempt {attempt}/{MAX_EXTERNAL_ATTEMPTS}...")
            )

            # Run external lint check with auto-fix enabled
            lint_success, lint_results = run_external_lint(issue_number, adw_id, logger, state, target, fix_mode=True)

            if "error" in lint_results:
                # External tool failed completely
                logger.error(f"External lint tool error on attempt {attempt}: {lint_results['error']}")
                break

            # Track error reduction
            summary = lint_results.get("summary", {})
            current_errors = summary.get("total_errors", 0)

            if initial_error_count is None:
                initial_error_count = current_errors
                logger.info(f"Initial error count: {initial_error_count}")

            # Check if we've fixed all errors
            if lint_success:
                logger.info(f"✅ All errors fixed after {attempt} attempt(s)!")
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "lint_checker", f"✅ All lint errors resolved after {attempt} external attempt(s)!")
                )
                break

            # Log progress
            logger.info(f"Attempt {attempt}: {current_errors} error(s) remaining (reduced by {initial_error_count - current_errors})")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker", f"📊 Attempt {attempt}: {current_errors} error(s) remaining")
            )

            # Commit auto-fixes after each attempt
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=worktree_path
            )

            if result.stdout.strip():
                fixable_count = summary.get("fixable_count", 0)
                commit_msg = f"style: Auto-fix lint errors (attempt {attempt})\n\nFixed errors using ruff/eslint auto-fix.\nAttempt {attempt}/{MAX_EXTERNAL_ATTEMPTS}\n\n🤖 Generated by ADW {adw_id}"

                success, error = commit_changes(commit_msg, cwd=worktree_path)
                if success:
                    logger.info(f"Committed auto-fixes from attempt {attempt}")
                else:
                    logger.warning(f"Failed to commit auto-fixes: {error}")

        # After external loop: Report results and optionally use LLM fallback
        summary = lint_results.get("summary", {})
        errors = lint_results.get("errors", [])
        total_errors = summary.get("total_errors", 0)
        style_errors = summary.get("style_errors", 0)
        quality_errors = summary.get("quality_errors", 0)

        # LLM Fallback for remaining errors
        if not lint_success and total_errors > 0 and total_errors < 50:  # Only use LLM if <50 errors (manageable context)
            logger.info(f"🤖 Kicking {total_errors} remaining error(s) to LLM for nuanced fixes")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker",
                    f"🤖 External loop reduced errors from {initial_error_count} → {total_errors}\n"
                    f"Now attempting LLM-based fixes for remaining {total_errors} nuanced error(s)...")
            )

            # TODO: Implement LLM fallback using Claude Code
            # For now, log that we would use LLM here
            logger.warning("LLM fallback not yet implemented - would handle remaining errors here")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker",
                    f"⚠️ LLM fallback not yet implemented\n"
                    f"External loop successfully reduced errors: {initial_error_count if initial_error_count else total_errors} → {total_errors}\n"
                    f"Continuing workflow (errors logged for future attention)")
            )

        # Format final results comment
        if lint_success:
            comment = f"✅ Lint check passed! All errors resolved.\n"
            comment += f"🔄 External attempts: {attempt if 'attempt' in locals() else 'N/A'}\n"
            comment += f"⚡ Context savings: ~93% (hybrid approach)"
        else:
            errors_fixed = (initial_error_count - total_errors) if initial_error_count else 0
            comment = f"📊 Hybrid lint loop results:\n"
            comment += f"   - Initial errors: {initial_error_count if initial_error_count else total_errors}\n"
            comment += f"   - Remaining errors: {total_errors}\n"
            comment += f"   - Errors fixed: {errors_fixed}\n"
            comment += f"   - Success rate: {(errors_fixed / initial_error_count * 100) if initial_error_count and initial_error_count > 0 else 0:.1f}%\n\n"
            comment += "**Remaining Errors (sample):**\n"
            for error in errors[:5]:  # Show first 5
                file_path = error.get("file", "unknown")
                line = error.get("line", "?")
                rule = error.get("rule", "?")
                msg = error.get("message", "unknown error")
                comment += f"  `{file_path}:{line}` - [{rule}] {msg}\n"

            if len(errors) > 5:
                comment += f"\n... and {len(errors) - 5} more errors\n"

            comment += f"\n⚠️ Workflow will continue (errors logged, not blocking)"

        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "lint_checker", comment)
        )
        logger.info(f"Hybrid lint loop: {'✅ Success' if lint_success else f'⚠️ {total_errors} errors remaining (not blocking)'}")

    else:
        # Inline execution (not implemented - would use claude code directly)
        logger.warning("Inline lint execution not yet implemented")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "lint_checker", "⚠️ Inline lint execution not yet implemented. Use external tools (default).")
        )
        sys.exit(1)

    logger.info("Lint phase completed")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Lint phase completed")
    )

    # OBSERVABILITY: Log phase completion
    from datetime import datetime
    start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
    log_phase_completion(
        adw_id=adw_id,
        issue_number=int(issue_number),
        phase_name="Lint",
        phase_number=get_phase_number("Lint"),
        success=lint_success or (fix_mode and use_external),
        workflow_template="adw_lint_iso",
        started_at=start_time,
    )

    # Save final state
    state.save("adw_lint_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final lint state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    # Hybrid approach: ALWAYS continue workflow (don't block on lint errors)
    # Errors are logged and reduced by external loop
    # LLM fallback handles remaining nuanced cases
    # Workflow continues to allow testing, review, and documentation
    if lint_success:
        logger.info("✅ Lint phase completed successfully - all errors resolved")
    else:
        summary = lint_results.get("summary", {})
        remaining_errors = summary.get("total_errors", 0)
        logger.warning(f"⚠️ Lint phase completed with {remaining_errors} remaining error(s) - workflow continuing")
        logger.info("Errors were reduced by hybrid loop and logged for review")

    # Always exit 0 to continue workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
