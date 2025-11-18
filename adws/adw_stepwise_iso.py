#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "pyyaml"]
# ///

"""
ADW Stepwise Iso - Stepwise refinement analysis for issue decomposition

Usage:
  uv run adw_stepwise_iso.py <issue-number> [adw-id]

Workflow:
1. Fetch GitHub issue details
2. Analyze issue complexity and decomposition potential (ONE AI call)
3. Make decision: ATOMIC or DECOMPOSE
4. If DECOMPOSE:
   - Create sub-issues via GitHub API (deterministic, zero AI calls)
   - Link sub-issues to parent issue
   - Post summary comment with breakdown rationale
5. Save analysis results to state
6. Exit with status code indicating decision

This workflow uses inverted context flow:
- Single comprehensive analysis call with full issue context
- Deterministic GitHub API operations to create sub-issues
- Minimal validation for structured output

Exit codes:
  0 - ATOMIC decision (proceed with normal workflow)
  10 - DECOMPOSE decision (sub-issues created, pause for review)
  1 - Error occurred
"""

import sys
import os
import logging
import json
import subprocess
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import yaml
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
    get_github_env,
)
from adw_modules.workflow_ops import (
    format_issue_message,
    ensure_adw_id,
)
from adw_modules.utils import setup_logger, check_env_vars
from adw_modules.data_types import GitHubIssue, AgentTemplateRequest
from adw_modules.agent import execute_template


def parse_stepwise_analysis(output: str) -> Optional[Dict[str, Any]]:
    """
    Parse YAML configuration from stepwise analysis output.

    Args:
        output: Raw output from AI analysis

    Returns:
        Parsed configuration dictionary or None if parsing fails
    """
    # Extract YAML block from output
    yaml_start = None
    yaml_end = None

    lines = output.split('\n')
    for i, line in enumerate(lines):
        if '```yaml' in line.lower():
            yaml_start = i + 1
        elif yaml_start is not None and '```' in line:
            yaml_end = i
            break

    if yaml_start is None or yaml_end is None:
        return None

    yaml_content = '\n'.join(lines[yaml_start:yaml_end])

    try:
        config = yaml.safe_load(yaml_content)
        return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        return None


def validate_stepwise_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate stepwise refinement configuration.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Check required fields
    if 'decision' not in config:
        errors.append("Missing required field: decision")
    elif config['decision'] not in ['ATOMIC', 'DECOMPOSE']:
        errors.append(f"Invalid decision: {config['decision']} (must be ATOMIC or DECOMPOSE)")

    if 'reasoning' not in config:
        errors.append("Missing required field: reasoning")

    if 'confidence' not in config:
        errors.append("Missing required field: confidence")
    elif config['confidence'] not in ['high', 'medium', 'low']:
        errors.append(f"Invalid confidence: {config['confidence']}")

    # Validate sub_issues if DECOMPOSE
    if config.get('decision') == 'DECOMPOSE':
        if 'sub_issues' not in config or not config['sub_issues']:
            errors.append("DECOMPOSE decision requires non-empty sub_issues list")
        else:
            sub_issues = config['sub_issues']
            if len(sub_issues) < 2:
                errors.append("DECOMPOSE requires at least 2 sub-issues")
            elif len(sub_issues) > 5:
                errors.append("Too many sub-issues (max 5), consider reducing scope")

            # Validate each sub-issue
            for i, sub_issue in enumerate(sub_issues):
                if 'title' not in sub_issue:
                    errors.append(f"Sub-issue {i}: missing title")
                if 'body' not in sub_issue:
                    errors.append(f"Sub-issue {i}: missing body")
                if 'labels' not in sub_issue:
                    errors.append(f"Sub-issue {i}: missing labels")
                if 'depends_on' not in sub_issue:
                    errors.append(f"Sub-issue {i}: missing depends_on field")
                else:
                    # Validate dependencies
                    for dep in sub_issue['depends_on']:
                        if not isinstance(dep, int) or dep < 0 or dep >= len(sub_issues):
                            errors.append(f"Sub-issue {i}: invalid dependency index {dep}")

    return errors


def create_github_issue(
    title: str,
    body: str,
    labels: List[str],
    repo_path: str,
    logger: logging.Logger
) -> Optional[str]:
    """
    Create a GitHub issue using gh CLI.

    Returns issue number if successful, None otherwise.
    """
    # Build command
    cmd = [
        "gh", "issue", "create",
        "-R", repo_path,
        "--title", title,
        "--body", body,
    ]

    # Add labels
    for label in labels:
        cmd.extend(["--label", label])

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        logger.info(f"Creating issue: {title}")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            # Extract issue number from URL (last part of output)
            issue_url = result.stdout.strip()
            issue_number = issue_url.split('/')[-1]
            logger.info(f"Created issue #{issue_number}: {issue_url}")
            return issue_number
        else:
            logger.error(f"Failed to create issue: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        return None


def create_sub_issues(
    parent_issue_number: str,
    sub_issues_config: List[Dict[str, Any]],
    repo_path: str,
    logger: logging.Logger
) -> List[str]:
    """
    Create sub-issues from configuration.

    Returns list of created sub-issue numbers.
    """
    created_issues = []
    issue_map = {}  # Index -> issue number

    for i, sub_issue in enumerate(sub_issues_config):
        title = sub_issue['title']
        body = sub_issue['body']
        labels = sub_issue['labels']
        depends_on = sub_issue.get('depends_on', [])

        # Add parent reference to body
        enhanced_body = f"{body}\n\n---\n**Parent Issue:** #{parent_issue_number}"

        # Add dependency references
        if depends_on:
            dep_refs = [f"#{issue_map[dep]}" for dep in depends_on if dep in issue_map]
            if dep_refs:
                enhanced_body += f"\n**Depends on:** {', '.join(dep_refs)}"

        # Create issue
        issue_number = create_github_issue(
            title=title,
            body=enhanced_body,
            labels=labels,
            repo_path=repo_path,
            logger=logger
        )

        if issue_number:
            created_issues.append(issue_number)
            issue_map[i] = issue_number
        else:
            logger.warning(f"Failed to create sub-issue {i}: {title}")

    return created_issues


def run_stepwise_analysis(
    issue: GitHubIssue,
    adw_id: str,
    logger: logging.Logger,
    repo_path: str
) -> Optional[Dict[str, Any]]:
    """
    Run stepwise refinement analysis with single AI call.

    Returns parsed configuration or None if failed.
    """
    logger.info("="*60)
    logger.info("STEPWISE REFINEMENT ANALYSIS")
    logger.info("="*60)

    # Minimal issue JSON (only what's needed for analysis)
    minimal_issue_json = issue.model_dump_json(
        by_alias=True,
        include={"number", "title", "body", "labels"}
    )

    # Single comprehensive analysis call
    analysis_request = AgentTemplateRequest(
        agent_name="stepwise_analyzer",
        slash_command="/stepwise_analysis",
        args=[str(issue.number), minimal_issue_json],
        adw_id=adw_id,
        working_dir=repo_path
    )

    logger.info("Invoking stepwise analyzer...")
    analysis_response = execute_template(analysis_request)

    if not analysis_response.success:
        logger.error(f"Analysis failed: {analysis_response.output}")
        return None

    # Parse YAML configuration from response
    logger.info("Parsing analysis configuration...")
    config = parse_stepwise_analysis(analysis_response.output)

    if not config:
        logger.error("Failed to parse analysis configuration")
        return None

    # Validate configuration
    errors = validate_stepwise_config(config)
    if errors:
        error_msg = "Analysis validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        return None

    logger.info("Analysis complete!")
    logger.info(f"  Decision: {config['decision']}")
    logger.info(f"  Confidence: {config['confidence']}")
    logger.info(f"  Reasoning: {config['reasoning'][:100]}...")

    if config['decision'] == 'DECOMPOSE':
        logger.info(f"  Sub-issues to create: {len(config['sub_issues'])}")

    return config


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 2:
        print("Usage: uv run adw_stepwise_iso.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(adw_id, "adw_stepwise_iso") if adw_id else None
    adw_id = ensure_adw_id(issue_number, adw_id, temp_logger)

    # Load the state
    state = ADWState.load(adw_id, temp_logger)

    # Ensure state has the adw_id field
    if not state.get("adw_id"):
        state.update(adw_id=adw_id)

    # Track that this ADW workflow has run
    state.append_adw_id("adw_stepwise_iso")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_stepwise_iso")
    logger.info(f"ADW Stepwise Iso starting - ID: {adw_id}, Issue: {issue_number}")

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
        format_issue_message(adw_id, "ops", "🔍 Starting stepwise refinement analysis")
    )

    # ========================================
    # STAGE 1: ANALYSIS (ONE AI CALL)
    # ========================================
    try:
        config = run_stepwise_analysis(issue, adw_id, logger, repo_path)

        if not config:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ Stepwise analysis failed - see logs")
            )
            sys.exit(1)

        # Save analysis to state
        state.update(
            stepwise_decision=config['decision'],
            stepwise_confidence=config['confidence'],
            stepwise_reasoning=config['reasoning']
        )
        state.save("adw_stepwise_iso")

        # Post analysis summary
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "stepwise_analyzer",
                f"✅ **Analysis Complete**\n\n"
                f"**Decision:** `{config['decision']}`\n"
                f"**Confidence:** `{config['confidence']}`\n\n"
                f"**Reasoning:**\n{config['reasoning']}"
            )
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Analysis failed: {e}")
        )
        sys.exit(1)

    # ========================================
    # STAGE 2: EXECUTION (ZERO AI CALLS)
    # ========================================
    if config['decision'] == 'ATOMIC':
        logger.info("Decision: ATOMIC - Issue is ready for implementation")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops",
                "✅ **Issue is ATOMIC** - Ready for implementation\n\n"
                "Recommended workflow: `adw_sdlc_complete_iso` or `adw_lightweight_iso`"
            )
        )
        # Exit with success code 0 (proceed with normal workflow)
        sys.exit(0)

    elif config['decision'] == 'DECOMPOSE':
        logger.info("Decision: DECOMPOSE - Creating sub-issues")

        # Create sub-issues deterministically (zero AI calls)
        logger.info("Creating sub-issues via GitHub API...")
        sub_issues = create_sub_issues(
            parent_issue_number=issue_number,
            sub_issues_config=config['sub_issues'],
            repo_path=repo_path,
            logger=logger
        )

        if not sub_issues:
            logger.error("Failed to create any sub-issues")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ Failed to create sub-issues")
            )
            sys.exit(1)

        # Save sub-issue numbers to state
        state.update(sub_issue_numbers=sub_issues)
        state.save("adw_stepwise_iso")

        # Post summary with sub-issues
        sub_issue_list = "\n".join([f"- #{num}" for num in sub_issues])
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops",
                f"✅ **Issue Decomposed** - Created {len(sub_issues)} sub-issues\n\n"
                f"**Sub-issues:**\n{sub_issue_list}\n\n"
                f"**Next Steps:**\n"
                f"1. Review sub-issues for accuracy\n"
                f"2. Run workflow on each sub-issue independently\n"
                f"3. Close parent issue when all sub-issues are complete\n\n"
                f"**Recommended workflow per sub-issue:** `adw_sdlc_complete_iso`"
            )
        )

        logger.info(f"Successfully created {len(sub_issues)} sub-issues")
        logger.info("Stepwise refinement complete - DECOMPOSE decision")

        # Exit with code 10 to indicate decomposition (pause for review)
        sys.exit(10)


if __name__ == "__main__":
    main()
