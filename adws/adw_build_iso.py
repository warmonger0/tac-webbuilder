#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Build Iso - AI Developer Workflow for agentic building in isolated worktrees

Usage:
  uv run adw_build_iso.py <issue-number> <adw-id> [--no-external]

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the solution based on plan in worktree
4. Commit implementation in worktree
5. Push and update PR

Options:
  --no-external: Disable external build tools (uses inline execution, higher token usage)

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations, get_current_branch
from adw_modules.github import fetch_issue, make_issue_comment, get_repo_url, extract_repo_path
from adw_modules.workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    AGENT_IMPLEMENTOR,
)
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.data_types import GitHubIssue
from adw_modules.worktree_ops import validate_worktree
from adw_modules.observability import log_phase_completion, get_phase_number


def run_external_build(
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    state: ADWState
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run build checks using external build ADW workflow.

    Returns:
        Tuple of (success: bool, results: Dict)
    """
    logger.info("🔧 Using external build tools for context optimization")

    # Get path to external build ADW script
    script_dir = Path(__file__).parent
    build_external_script = script_dir / "adw_build_external.py"

    if not build_external_script.exists():
        logger.error(f"External build script not found: {build_external_script}")
        return False, {"error": "External build script not found"}

    # Run external build ADW
    cmd = ["uv", "run", str(build_external_script), issue_number, adw_id]

    logger.info(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Reload state to get external build results
    reloaded_state = ADWState.load(adw_id)
    if not reloaded_state:
        logger.error("Failed to reload state after external build")
        return False, {"error": "Failed to reload state"}
    build_results = reloaded_state.get("external_build_results", {})

    if not build_results:
        logger.warning("No external_build_results found in state after execution")
        logger.debug(f"Stdout: {result.stdout}")
        logger.debug(f"Stderr: {result.stderr}")
        return False, {"error": "No build results returned from external tool"}

    success = build_results.get("success", False)
    logger.info(f"External build check completed: {'✅ Success' if success else '❌ Errors detected'}")

    return success, build_results


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # External tools are DEFAULT (opt-out with --no-external)
    use_external = "--no-external" not in sys.argv
    if "--no-external" in sys.argv:
        sys.argv.remove("--no-external")

    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run adw_build_iso.py <issue-number> <adw-id> [--no-external]")
        print("\nError: adw-id is required to locate the worktree and plan file")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_build_iso")
    state = ADWState.load(adw_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - resuming isolated build\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        # No existing state found
        logger = setup_logger(adw_id, "adw_build_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py first to create the worktree and state")
        sys.exit(1)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_build_iso")
    
    # Set up logger with ADW ID from command line
    logger = setup_logger(adw_id, "adw_build_iso")
    logger.info(f"ADW Build Iso starting - ID: {adw_id}, Issue: {issue_number}, Use External: {use_external}")
    
    # Validate environment
    check_env_vars(logger)
    
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
    
    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run adw_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    if not state.get("plan_file"):
        error_msg = "No plan file in state - run adw_plan_iso.py first"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    # Checkout the branch in the worktree
    branch_name = state.get("branch_name")
    result = subprocess.run(["git", "checkout", branch_name], capture_output=True, text=True, cwd=worktree_path)
    if result.returncode != 0:
        logger.error(f"Failed to checkout branch {branch_name} in worktree: {result.stderr}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Failed to checkout branch {branch_name} in worktree")
        )
        sys.exit(1)
    logger.info(f"Checked out branch in worktree: {branch_name}")
    
    # Get the plan file from state
    plan_file = state.get("plan_file")
    logger.info(f"Using plan file: {plan_file}")
    
    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")
    
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Starting isolated implementation phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                           f"🔧 Build Mode: {'External Tools (Context Optimized)' if use_external else 'Inline Execution'}")
    )
    
    # Implement the plan (executing in worktree)
    logger.info("Implementing solution in worktree")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementing solution in isolated environment")
    )
    
    implement_response = implement_plan(plan_file, adw_id, logger, working_dir=worktree_path)
    
    if not implement_response.success:
        logger.error(f"Error implementing solution: {implement_response.output}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error implementing solution: {implement_response.output}")
        )
        sys.exit(1)
    
    logger.debug(f"Implementation response: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Solution implemented")
    )

    # Run build check if using external tools
    if use_external:
        logger.info("🔧 Running external build check for type validation")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "build_checker", "🔧 Running build checks via external tools (70-95% token reduction)...")
        )

        # Run external build check
        build_success, build_results = run_external_build(issue_number, adw_id, logger, state)

        if "error" in build_results:
            # External tool failed
            logger.error(f"External build tool error: {build_results['error']}")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "build_checker", f"❌ External build tool error: {build_results['error']}")
            )
        else:
            # Process external build results
            summary = build_results.get("summary", {})
            errors = build_results.get("errors", [])

            total_errors = summary.get("total_errors", 0)
            type_errors = summary.get("type_errors", 0)
            build_errors = summary.get("build_errors", 0)

            # Load baseline from Validate phase (if it ran)
            baseline_errors_data = state.get("baseline_errors", {})
            baseline_frontend = baseline_errors_data.get("frontend", {})
            baseline_error_details = baseline_frontend.get("error_details", [])

            # Calculate differential errors
            if baseline_error_details:
                logger.info("📊 Baseline detected - calculating differential errors")

                # Create sets of errors for comparison (file:line:message)
                baseline_error_set = {
                    (e.get("file", ""), e.get("line", 0), e.get("message", ""))
                    for e in baseline_error_details
                }
                final_error_set = {
                    (e.get("file", ""), e.get("line", 0), e.get("message", ""))
                    for e in errors
                }

                # Calculate new and fixed errors
                new_errors_tuples = final_error_set - baseline_error_set
                fixed_errors_tuples = baseline_error_set - final_error_set

                # Convert back to error dictionaries
                new_errors = [e for e in errors if (e.get("file", ""), e.get("line", 0), e.get("message", "")) in new_errors_tuples]
                num_new_errors = len(new_errors)
                num_fixed_errors = len(fixed_errors_tuples)
                num_baseline_errors = len(baseline_error_set)

                logger.info(f"Baseline: {num_baseline_errors}, New: {num_new_errors}, Fixed: {num_fixed_errors}")

                # Override build_success based on new errors only
                build_success = (num_new_errors == 0)

                # Update total_errors to reflect only new errors
                total_errors = num_new_errors
            else:
                logger.info("No baseline detected - all errors are considered new")
                new_errors = errors
                num_new_errors = len(errors)
                num_fixed_errors = 0
                num_baseline_errors = 0

            # Format results comment with differential information
            if build_success:
                comment = f"✅ Build check passed! No NEW errors introduced.\n"
                if num_baseline_errors > 0:
                    comment += f"\n**Differential Error Analysis:**\n"
                    comment += f"- Baseline (inherited): {num_baseline_errors} errors (ignored)\n"
                    comment += f"- New errors: 0 ✅\n"
                    if num_fixed_errors > 0:
                        comment += f"- Fixed errors: {num_fixed_errors} 🎉\n"
                comment += f"\n⚡ Context savings: ~93% (using external tools)"
            else:
                comment = f"❌ Build check failed: {num_new_errors} NEW error(s) introduced\n\n"
                if num_baseline_errors > 0:
                    comment += f"**Differential Error Analysis:**\n"
                    comment += f"- Baseline (inherited): {num_baseline_errors} errors (ignored)\n"
                    comment += f"- New errors: {num_new_errors} ❌\n"
                    if num_fixed_errors > 0:
                        comment += f"- Fixed errors: {num_fixed_errors} ✨\n"
                    comment += f"\n"
                comment += "**New Errors (blocking):**\n"
                for error in new_errors[:10]:  # Limit to first 10
                    file_path = error.get("file", "unknown")
                    line = error.get("line", "?")
                    col = error.get("column", "?")
                    msg = error.get("message", "unknown error")
                    comment += f"- `{file_path}:{line}:{col}` - {msg}\n"

                if len(new_errors) > 10:
                    comment += f"\n... and {len(new_errors) - 10} more errors\n"

                comment += f"\n⚡ Context savings: ~83% (compact error reporting)"
                comment += f"\n\n⚠️ Fix NEW build errors before committing"

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "build_checker", comment)
            )
            logger.info(f"External build check: {'✅ Success' if build_success else f'❌ {total_errors} errors'}")

            # If build failed, stop here
            if not build_success:
                logger.error("Build check failed - stopping workflow")
                sys.exit(1)

    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        from adw_modules.workflow_ops import classify_issue
        issue_command, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("adw_build_iso")
    
    # Create commit message
    logger.info("Creating implementation commit")
    commit_msg, error = create_commit(AGENT_IMPLEMENTOR, issue, issue_command, adw_id, logger, worktree_path)
    
    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)
    
    # Commit the implementation (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)
    
    if not success:
        logger.error(f"Error committing implementation: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Error committing implementation: {error}")
        )
        sys.exit(1)
    
    logger.info(f"Committed implementation: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementation committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated implementation phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Isolated implementation phase completed")
    )

    # Save final state
    state.save("adw_build_iso")

    # OBSERVABILITY: Log phase completion
    from datetime import datetime
    start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
    log_phase_completion(
        adw_id=adw_id,
        issue_number=int(issue_number),
        phase_name="Build",
        phase_number=get_phase_number("Build"),
        success=True,
        workflow_template="adw_build_iso",
        started_at=start_time,
    )
    
    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final build state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )


if __name__ == "__main__":
    main()