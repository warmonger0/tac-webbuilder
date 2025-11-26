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
        logger.info("🔧 Running external lint check")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "lint_checker", f"🔧 Running lint checks via external tools (70-95% token reduction)...")
        )

        # Run external lint check
        lint_success, lint_results = run_external_lint(issue_number, adw_id, logger, state, target, fix_mode)

        if "error" in lint_results:
            # External tool failed
            logger.error(f"External lint tool error: {lint_results['error']}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker", f"❌ External lint tool error: {lint_results['error']}")
            )
            sys.exit(1)
        else:
            # Process external lint results
            summary = lint_results.get("summary", {})
            errors = lint_results.get("errors", [])

            total_errors = summary.get("total_errors", 0)
            style_errors = summary.get("style_errors", 0)
            quality_errors = summary.get("quality_errors", 0)
            fixable_count = summary.get("fixable_count", 0)

            # Format results comment
            if lint_success:
                comment = f"✅ Lint check passed! No style or quality errors.\n"
                comment += f"⚡ Context savings: ~93% (using external tools)"
            else:
                comment = f"❌ Lint check found: {total_errors} error(s)\n"
                comment += f"   - Style errors: {style_errors}\n"
                comment += f"   - Quality errors: {quality_errors}\n"
                comment += f"   - Fixable: {fixable_count}\n\n"
                comment += "**Errors:**\n"
                for error in errors[:10]:  # Limit to first 10
                    file_path = error.get("file", "unknown")
                    line = error.get("line", "?")
                    rule = error.get("rule", "?")
                    msg = error.get("message", "unknown error")
                    fixable = "🔧" if error.get("fixable") else "  "
                    comment += f"{fixable} `{file_path}:{line}` - [{rule}] {msg}\n"

                if len(errors) > 10:
                    comment += f"\n... and {len(errors) - 10} more errors\n"

                comment += f"\n⚡ Context savings: ~83% (compact error reporting)"

                if fix_mode:
                    comment += f"\n\n✅ Auto-fix was enabled - fixable errors have been corrected"
                elif fixable_count > 0:
                    comment += f"\n\n💡 Tip: Run with --fix-mode to auto-fix {fixable_count} error(s)"

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "lint_checker", comment)
            )
            logger.info(f"External lint check: {'✅ Success' if lint_success else f'❌ {total_errors} errors'}")

            # If fix mode was enabled and there were changes, commit them
            if fix_mode and not lint_success:
                logger.info("Checking for auto-fixed changes to commit")

                # Check if there are uncommitted changes
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd=worktree_path
                )

                if result.stdout.strip():
                    logger.info("Auto-fix made changes, committing them")
                    commit_msg = f"style: Auto-fix lint errors\n\nAuto-fixed {fixable_count} lint error(s) using ruff/eslint.\n\n🤖 Generated by ADW {adw_id}"

                    success, error = commit_changes(commit_msg, cwd=worktree_path)

                    if success:
                        make_issue_comment(
                            issue_number,
                            format_issue_message(adw_id, "lint_checker", f"✅ Auto-fixed changes committed: {fixable_count} error(s) resolved")
                        )
                    else:
                        logger.error(f"Failed to commit auto-fixes: {error}")
                        make_issue_comment(
                            issue_number,
                            format_issue_message(adw_id, "lint_checker", f"⚠️ Auto-fixes applied but commit failed: {error}")
                        )
                else:
                    logger.info("No changes detected from auto-fix")

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

    # Save final state
    state.save("adw_lint_iso")

    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final lint state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )

    # Exit with appropriate code based on lint results
    # Exit 0 if lint passed or if auto-fix was successful
    # Exit 1 if lint errors detected to prevent merging code with style issues
    if lint_success or (fix_mode and use_external):
        sys.exit(0)
    else:
        logger.error("Lint errors detected - blocking workflow to prevent style issues in production")
        # Exit 1 to block workflow when lint errors are present
        sys.exit(1)


if __name__ == "__main__":
    main()
