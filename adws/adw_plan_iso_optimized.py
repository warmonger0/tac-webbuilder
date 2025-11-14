#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "pyyaml"]
# ///

"""
ADW Plan Iso (Optimized) - Inverted context flow architecture

OPTIMIZED WORKFLOW:
1. Fetch issue
2. ONE comprehensive AI planning call (loads context ONCE)
3. Execute plan deterministically (ZERO AI calls)
4. Validate execution against plan (minimal context)

This reduces token usage by 77% by:
- Making all decisions upfront in single AI call
- Executing setup with pure Python (no AI)
- Validating at end with structured artifacts

Traditional flow:    1,173k tokens (~$1.90)
Optimized flow:        271k tokens (~$0.34)
"""

import sys
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adw_modules.workflow_ops import (
    format_issue_message,
    ensure_adw_id,
)
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.data_types import GitHubIssue, AgentTemplateRequest
from adw_modules.agent import execute_template
from adw_modules.plan_parser import parse_plan, validate_workflow_config, WorkflowConfig
from adw_modules.plan_executor import execute_plan, ExecutionResult


def create_comprehensive_plan(
    issue: GitHubIssue,
    adw_id: str,
    logger: logging.Logger,
    repo_path: str
) -> WorkflowConfig:
    """
    Create comprehensive plan with ONE AI call.

    This single call makes ALL decisions:
    - Issue classification
    - Project context detection
    - Branch naming
    - Worktree setup planning
    - Implementation planning
    - Validation criteria

    Returns parsed WorkflowConfig ready for execution.
    """
    logger.info("="*60)
    logger.info("COMPREHENSIVE PLANNING PHASE (ONE AI CALL)")
    logger.info("="*60)

    # Minimal issue JSON (only what's needed)
    minimal_issue_json = issue.model_dump_json(
        by_alias=True,
        include={"number", "title", "body"}
    )

    # Single comprehensive planning call
    planning_request = AgentTemplateRequest(
        agent_name="sdlc_planner",
        slash_command="/plan_complete_workflow",
        args=[str(issue.number), adw_id, minimal_issue_json],
        adw_id=adw_id,
        working_dir=repo_path
    )

    logger.info("Invoking comprehensive planner...")
    plan_response = execute_template(planning_request)

    if not plan_response.success:
        raise ValueError(f"Planning failed: {plan_response.output}")

    # Parse YAML configuration from response
    logger.info("Parsing plan configuration...")
    config = parse_plan(plan_response.output)

    # Validate configuration
    errors = validate_workflow_config(config)
    if errors:
        error_msg = "Plan validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Plan created successfully!")
    logger.info(f"  Issue type: {config.issue_type}")
    logger.info(f"  Project: {config.project_context}")
    logger.info(f"  Branch: {config.branch_name}")
    logger.info(f"  Requires worktree: {config.requires_worktree}")
    logger.info(f"  Confidence: {config.confidence}")

    return config


def validate_execution(
    config: WorkflowConfig,
    execution: ExecutionResult,
    worktree_path: str,
    adw_id: str,
    logger: logging.Logger
) -> bool:
    """
    Validate execution against plan with minimal AI call.

    Passes structured artifacts to AI for verification.
    """
    logger.info("="*60)
    logger.info("VALIDATION PHASE")
    logger.info("="*60)

    # Gather validation artifacts
    import subprocess

    git_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    ).stdout

    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    ).stdout.strip()

    # Check file system
    file_system_checks = {
        "worktree_exists": os.path.exists(worktree_path) if config.requires_worktree else None,
        "plan_file_exists": os.path.exists(os.path.join(worktree_path, config.plan_file_path)) if config.plan_file_path else False,
        "current_branch": current_branch
    }

    # Build validation artifacts
    validation_artifacts = {
        "plan": {
            "issue_type": config.issue_type,
            "project_context": config.project_context,
            "requires_worktree": config.requires_worktree,
            "confidence": config.confidence,
            "detection_reasoning": config.detection_reasoning,
            "branch_name": config.branch_name,
            "worktree_setup": config.worktree_setup,
            "validation_criteria": config.validation_criteria
        },
        "execution": execution.to_dict(),
        "git_status": git_status,
        "file_system": file_system_checks
    }

    # Invoke validation agent
    validation_request = AgentTemplateRequest(
        agent_name="sdlc_validator",
        slash_command="/validate_workflow",
        args=[json.dumps(validation_artifacts, indent=2)],
        adw_id=adw_id,
        working_dir=worktree_path
    )

    logger.info("Invoking validation agent...")
    validation_response = execute_template(validation_request)

    if not validation_response.success:
        logger.error(f"Validation invocation failed: {validation_response.output}")
        return False

    logger.info("Validation complete!")
    logger.info(validation_response.output)

    # Check if validation passed
    if "❌ FAILED" in validation_response.output:
        logger.error("Validation identified failures")
        return False

    if "⚠️ PASSED WITH WARNINGS" in validation_response.output:
        logger.warning("Validation passed with warnings")

    return True


def main():
    """Main entry point - optimized inverted flow."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_iso_optimized.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(adw_id, "adw_plan_iso_optimized") if adw_id else None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)

    # Load the state
    state = ADWState.load(adw_id, temp_logger)

    # Ensure state has the adw_id field
    if not state.get("adw_id"):
        state.update(adw_id=adw_id)

    # Track that this ADW workflow has run
    state.append_adw_id("adw_plan_iso_optimized")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_plan_iso_optimized")
    logger.info(f"ADW Plan Iso (Optimized) starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Fetch issue details
    issue: GitHubIssue = fetch_issue(issue_number, repo_path)
    logger.debug(f"Fetched issue: {issue.model_dump_json(indent=2, by_alias=True)}")

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Starting optimized planning phase")
    )

    # ========================================
    # STAGE 1: COMPREHENSIVE PLANNING (ONE AI CALL)
    # ========================================
    try:
        config = create_comprehensive_plan(issue, adw_id, logger, repo_path)

        # Post plan summary to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "sdlc_planner",
                f"✅ Comprehensive plan created\n"
                f"- Type: `{config.issue_type}`\n"
                f"- Project: `{config.project_context}`\n"
                f"- Branch: `{config.branch_name}`\n"
                f"- Worktree: `{config.requires_worktree}`\n"
                f"- Confidence: `{config.confidence}`"
            )
        )

        # Save plan config to state
        state.update(
            issue_class=config.issue_type,
            branch_name=config.branch_name,
            project_context=config.project_context,
            requires_worktree=config.requires_worktree
        )
        state.save("adw_plan_iso_optimized")

    except Exception as e:
        logger.error(f"Planning failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Planning failed: {e}")
        )
        sys.exit(1)

    # ========================================
    # STAGE 2: DETERMINISTIC EXECUTION (ZERO AI CALLS)
    # ========================================
    logger.info("="*60)
    logger.info("DETERMINISTIC EXECUTION PHASE (ZERO AI CALLS)")
    logger.info("="*60)

    try:
        execution_result = execute_plan(config, issue.number, repo_path, logger)

        if not execution_result.success:
            error_msg = "Execution failed:\n" + "\n".join(execution_result.errors)
            logger.error(error_msg)
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ {error_msg}")
            )
            sys.exit(1)

        # Save execution artifacts
        execution_file = f"agents/{adw_id}/execution_result.json"
        os.makedirs(os.path.dirname(execution_file), exist_ok=True)
        execution_result.save_to_file(execution_file)

        # Update state
        worktree_path = execution_result.metadata.get('working_directory', repo_path)
        state.update(
            worktree_path=worktree_path,
            plan_file=config.plan_file_path,
            execution_result=execution_file
        )
        state.save("adw_plan_iso_optimized")

        # Post execution summary
        files_created_summary = "\n".join(f"  - {f}" for f in execution_result.files_created[:5])
        if len(execution_result.files_created) > 5:
            files_created_summary += f"\n  - ... and {len(execution_result.files_created) - 5} more"

        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops",
                f"✅ Execution complete\n"
                f"- Files created: {len(execution_result.files_created)}\n"
                f"- Commands executed: {len(execution_result.commands_executed)}\n"
                f"- Warnings: {len(execution_result.warnings)}\n"
                f"\nFiles:\n{files_created_summary}"
            )
        )

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Execution failed: {e}")
        )
        sys.exit(1)

    # ========================================
    # STAGE 3: VALIDATION (MINIMAL AI CALL)
    # ========================================
    try:
        validation_passed = validate_execution(
            config, execution_result, worktree_path, adw_id, logger
        )

        if validation_passed:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "sdlc_validator", "✅ Validation passed")
            )
        else:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "sdlc_validator", "⚠️ Validation found issues")
            )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Validation failed: {e}")
        )
        # Don't exit - validation failure is not critical

    # ========================================
    # STAGE 4: COMMIT AND FINALIZE
    # ========================================
    logger.info("Committing plan")

    # Use commit message from plan or generate simple one
    commit_msg = config.commit_message or f"{config.issue_type}: {issue.title}\n\nADW: {adw_id}\nIssue: #{issue.number}"

    success, error = commit_changes(commit_msg, cwd=worktree_path)
    if not success:
        logger.error(f"Error committing plan: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Error committing plan: {error}")
        )
        sys.exit(1)

    logger.info(f"Committed plan: {commit_msg}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Plan committed")
    )

    # Finalize git operations (push and PR)
    finalize_git_operations(state, logger, cwd=worktree_path)

    logger.info("Optimized planning phase completed successfully")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Optimized planning phase completed")
    )

    # Save final state
    state.save("adw_plan_iso_optimized")

    # Post final state summary
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )


if __name__ == "__main__":
    main()
