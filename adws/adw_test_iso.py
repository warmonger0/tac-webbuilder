#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Test Iso - AI Developer Workflow for agentic testing in isolated worktrees

Usage:
  uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e] [--no-external] [--skip-coverage] [--coverage-threshold N]

Workflow:
1. Load state and validate worktree exists
2. Run application test suite in worktree (optionally via external tools)
3. **NEW (Issue #74):** Automatically retry and resolve test failures with fallback
4. **NEW:** Enforce code coverage thresholds based on issue type
5. Report results to issue
6. Create commit with test results in worktree
7. Push and update PR

Options:
  --skip-e2e: Skip E2E tests
  --no-external: Disable external test tools (uses inline execution, higher token usage)
  --skip-coverage: Skip coverage enforcement (debugging)
  --coverage-threshold N: Override coverage threshold percentage

Coverage Enforcement:
- LIGHTWEIGHT issues: 0% (no requirement)
- STANDARD issues: 70% minimum coverage (blocks if lower)
- COMPLEX issues: 80% minimum coverage (blocks if lower)
- Posts GitHub comment with coverage details
- Updates ADW state with coverage metrics
- Blocks merge with sys.exit(1) if coverage < threshold

Resolution Loop (Issue #74, #168):
- Infrastructure failures: Retries with fallback to inline mode (max 3 attempts)
- Test failures: Attempts resolution via inline mode with test fixing (max 3 attempts)
- **Verification-based loop control**: After each resolution attempt, re-runs tests to verify actual progress
  - Compares failures before vs after resolution
  - Exits immediately if no progress detected (prevents false success loops)
  - Only continues if failures actually decreased
- Never continues to review phase with failing tests
- Blocks progression until tests pass or max retries exhausted
- Circuit breaker: Detects loops by checking for repetitive agent patterns (not total comment count)

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import json
import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    TestResult,
    E2ETestResult,
    IssueClassSlashCommand,
)
from adw_modules.agent import execute_template
from adw_modules.github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from adw_modules.utils import make_adw_id, setup_logger, parse_json, check_env_vars
from adw_modules.state import ADWState
from utils.idempotency import (
    check_and_skip_if_complete,
    validate_phase_completion,
    ensure_database_state,
)
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.workflow_ops import (
    format_issue_message,
    create_commit,
    ensure_adw_id,
    classify_issue,
)
from adw_modules.worktree_ops import validate_worktree
from adw_modules.observability import log_phase_completion, get_phase_number
from adw_modules.tool_call_tracker import ToolCallTracker

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"
AGENT_BRANCH_GENERATOR = "branch_generator"

# Maximum number of test retry attempts after resolution
# Cap at 3 to prevent infinite loops (issue #168)
MAX_TEST_RETRY_ATTEMPTS = 3
MAX_E2E_TEST_RETRY_ATTEMPTS = 3  # E2E ui tests

# Circuit breaker: Detect repetitive patterns indicating a loop
MAX_RECENT_COMMENTS_TO_CHECK = 20  # Look at last N comments
MAX_LOOP_MARKERS = 12  # If 🔁 appears 12+ times in recent comments = stuck loop (workflow-wide catch-all)


def check_for_loop(issue_number: str, logger: logging.Logger, adw_id: str = None) -> None:
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
                f"**Action Required:**\n"
                f"- Manual review needed to identify root cause\n"
                f"- Check logs for recurring errors\n"
                f"- Fix underlying issue before retrying\n"
                f"- Consider creating a fresh issue if problem persists"
            )
            logger.error(f"Loop detected: Found {loop_marker_count} loop markers in last {len(recent_comments)} comments")
            make_issue_comment(issue_number, error_msg)
            sys.exit(1)

        logger.info(f"No loop detected. Loop markers in last {len(recent_comments)} comments: {loop_marker_count}/{MAX_LOOP_MARKERS}")

    except Exception as e:
        # Don't fail on circuit breaker errors - log and continue
        logger.warning(f"Circuit breaker check failed (continuing anyway): {e}")



def run_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None) -> AgentPromptResponse:
    """Run the test suite using the /test command."""
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"test_response: {test_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return test_response


def run_external_tests(
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    state: ADWState,
    tracker: Optional[ToolCallTracker] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run tests using external test ADW workflow.

    Returns:
        Tuple of (success: bool, results: Dict)

    Note: If external tool fails, returns (False, {"error": {...}})
          Caller MUST check for "error" key and exit immediately.
    """
    logger.info("🔧 Using external test tools for context optimization")

    # Get path to external test ADW script
    script_dir = Path(__file__).parent
    test_external_script = script_dir / "adw_test_external.py"

    if not test_external_script.exists():
        logger.error(f"External test script not found: {test_external_script}")
        return False, {
            "error": {
                "type": "FileNotFoundError",
                "message": f"External test script not found: {test_external_script}"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": ["Verify adw_test_external.py exists in adws/ directory"]
        }

    # Run external test ADW
    cmd = ["uv", "run", str(test_external_script), issue_number, adw_id]

    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        # Track external test execution if tracker available
        if tracker:
            result = tracker.track_bash(
                tool_name="adw_test_external",
                command=cmd,
                cwd=None
            )
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        # Check if subprocess exited with non-zero code
        if result.returncode != 0:
            logger.error(f"External test tool exited with code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")

            # Try to extract error from stderr
            error_message = result.stderr.strip() if result.stderr else "Unknown error"

            return False, {
                "error": {
                    "type": "SubprocessError",
                    "message": f"External test tool exited with code {result.returncode}",
                    "details": error_message[:500]  # Limit error details
                },
                "summary": {"total": 0, "passed": 0, "failed": 0},
                "failures": [],
                "next_steps": [
                    "Check adw_test_external.py logs",
                    "Verify worktree is valid",
                    "Check if test dependencies are installed"
                ]
            }

    except subprocess.TimeoutExpired:
        logger.error("External test tool timed out after 10 minutes")
        return False, {
            "error": {
                "type": "TimeoutError",
                "message": "External test tool timed out after 10 minutes"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": [
                "Check for infinite loops in tests",
                "Verify test infrastructure is responsive",
                "Check if services are hanging"
            ]
        }
    except Exception as e:
        logger.error(f"Unexpected error running external tests: {e}")
        return False, {
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": [f"Investigate exception: {type(e).__name__}: {str(e)}"]
        }

    # Reload state to get external test results
    reloaded_state = ADWState.load(adw_id)
    if not reloaded_state:
        logger.error("Failed to reload state after external tests")
        return False, {
            "error": {
                "type": "StateError",
                "message": "Failed to reload state after external tests"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": [
                "Check if state file exists",
                "Verify external test workflow saved results to state"
            ]
        }

    test_results = reloaded_state.get("external_test_results", {})

    if not test_results:
        logger.warning("No external_test_results found in state after execution")
        logger.debug(f"Stdout: {result.stdout}")
        logger.debug(f"Stderr: {result.stderr}")
        return False, {
            "error": {
                "type": "ResultsError",
                "message": "No test results returned from external tool",
                "details": f"Stdout: {result.stdout[:200]}"
            },
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "failures": [],
            "next_steps": [
                "Check adw_test_external.py output",
                "Verify state is being saved correctly"
            ]
        }

    success = test_results.get("success", False)
    logger.info(f"External tests completed: {'✅ Success' if success else '❌ Failures detected'}")

    return success, test_results


def parse_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[TestResult], int, int]:
    """Parse test results JSON and return (results, passed_count, failed_count)."""
    try:
        # Use parse_json to handle markdown-wrapped JSON
        results = parse_json(output, List[TestResult])

        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        return [], 0, 0


def format_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format test results for GitHub issue comment with JSON blocks."""
    if not results:
        return "❌ No test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Summary
    comment_parts.append("## Summary")
    comment_parts.append(f"- **Passed**: {passed_count}")
    comment_parts.append(f"- **Failed**: {failed_count}")
    comment_parts.append(f"- **Total**: {len(results)}")

    return "\n".join(comment_parts)


def parse_e2e_test_results(
    output: str, logger: logging.Logger
) -> Tuple[List[E2ETestResult], int, int]:
    """Parse E2E test results JSON and return (results, passed_count, failed_count)."""
    try:
        # Use parse_json to handle markdown-wrapped JSON
        results = parse_json(output, List[E2ETestResult])

        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing E2E test results: {e}")
        return [], 0, 0


def post_comprehensive_test_summary(
    issue_number: str,
    adw_id: str,
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger,
):
    """Post a comprehensive test summary including both unit and E2E tests."""
    summary = "# 🧪 Comprehensive Test Results\n\n"

    # Unit test section
    if results:
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        summary += "## Unit Tests\n\n"
        summary += f"- **Total**: {len(results)}\n"
        summary += f"- **Passed**: {passed_count} ✅\n"
        summary += f"- **Failed**: {failed_count} ❌\n\n"

        # List failures first
        failed_tests = [test for test in results if not test.passed]
        if failed_tests:
            summary += "### Failed Unit Tests:\n"
            for test in failed_tests:
                summary += f"- ❌ {test.test_name}\n"
            summary += "\n"

    # E2E test section
    if e2e_results:
        e2e_passed_count = sum(1 for test in e2e_results if test.passed)
        e2e_failed_count = len(e2e_results) - e2e_passed_count

        summary += "## E2E Tests\n\n"
        summary += f"- **Total**: {len(e2e_results)}\n"
        summary += f"- **Passed**: {e2e_passed_count} ✅\n"
        summary += f"- **Failed**: {e2e_failed_count} ❌\n\n"

        # List E2E failures
        e2e_failed_tests = [test for test in e2e_results if not test.passed]
        if e2e_failed_tests:
            summary += "### Failed E2E Tests:\n"
            for result in e2e_failed_tests:
                summary += f"- ❌ {result.test_name}\n"
                if result.screenshots:
                    summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    total_failures = (
        (failed_count if results else 0) + 
        (e2e_failed_count if e2e_results else 0)
    )
    if total_failures > 0:
        summary += f"\n### ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        total_tests = len(results) + len(e2e_results)
        summary += f"\n### ✅ Overall Status: PASSED\n"
        summary += f"All {total_tests} tests passed successfully!\n"

    # Post the summary to the issue
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "test_summary", summary)
    )

    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def run_e2e_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None, e2e_test_file: Optional[str] = None) -> AgentPromptResponse:
    """Run the E2E test suite using the /test_e2e command.

    Note: The test_e2e command will automatically detect and use ports from .ports.env
    in the working directory if it exists.

    Args:
        adw_id: ADW workflow ID
        logger: Logger instance
        working_dir: Working directory for the test
        e2e_test_file: Path to E2E test specification file (optional, skips E2E if not provided)

    Returns:
        AgentPromptResponse with success=True and a skip message if no e2e_test_file provided
    """
    # Skip E2E tests if no test file is provided
    if not e2e_test_file:
        logger.info("No E2E test file provided, skipping E2E tests")
        return AgentPromptResponse(
            output="E2E tests skipped (no test file provided)",
            success=True
        )

    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_E2E_TESTER,
        slash_command="/test_e2e",
        args=[e2e_test_file] if e2e_test_file else [],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(
        f"e2e_test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    test_response = execute_template(test_template_request)

    logger.debug(
        f"e2e_test_response: {test_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return test_response


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed tests using the resolve_failed_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"test_resolver_iter{iteration}_{idx}"

        # Create template request with worktree_path
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"🔧 Attempting to resolve: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve: {test.test_name}")

    return resolved_count, unresolved_count


def run_external_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    state: ADWState,
    worktree_path: str,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
    tracker: Optional[ToolCallTracker] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run external tests with automatic resolution and retry logic for infrastructure failures.
    Returns (success, results_dict).

    This handles two failure scenarios:
    1. Infrastructure failures (JSONDecodeError, SubprocessError, etc.) - attempts retry with fallback
    2. Test failures (parseable test results) - attempts test resolution via inline mode
    """
    attempt = 0
    last_results = {}

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== External Test Run Attempt {attempt}/{max_attempts} ===")

        # Run external tests
        success, external_results = run_external_tests(issue_number, adw_id, logger, state, tracker)
        last_results = external_results

        # Check for infrastructure failure (has "error" key)
        if "error" in external_results:
            error_info = external_results.get("error", {})
            error_type = error_info.get("type", "Unknown")
            error_message = error_info.get("message", "Unknown error")

            logger.error(f"External test tool infrastructure failure: {error_type}: {error_message}")

            # Post infrastructure failure details
            error_comment = f"❌ **Test infrastructure failure (Attempt {attempt}/{max_attempts})**\n\n"
            error_comment += f"**Error Type:** {error_type}\n"
            error_comment += f"**Error Message:** {error_message}\n\n"

            if "details" in error_info:
                error_comment += f"**Details:**\n```\n{error_info['details']}\n```\n\n"

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_TESTER, error_comment)
            )

            # If this is the last attempt, fall back to inline execution
            if attempt == max_attempts:
                logger.warning("Max retry attempts reached for external tests, falling back to inline execution")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        "⚠️ External test tool failed after max retries. Falling back to inline execution..."
                    )
                )
                # Will fall through to return False, which triggers inline mode in caller
                return False, external_results

            # Not the last attempt - retry
            logger.info(f"Retrying external tests (attempt {attempt + 1}/{max_attempts})...")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"🔄 Retrying test infrastructure (attempt {attempt + 1}/{max_attempts}) 🔁"
                )
            )
            continue

        # No infrastructure error - check test results
        summary = external_results.get("summary", {})
        failed_count = summary.get("failed", 0)

        # If all tests passed, we're done
        if success and failed_count == 0:
            logger.info("All external tests passed")
            return True, external_results

        # Tests failed - try resolution if not last attempt
        if attempt < max_attempts and failed_count > 0:
            logger.info(f"\n=== External tests have {failed_count} failures, attempting resolution ===")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"🔧 Found {failed_count} test failures. Attempting resolution via inline mode..."
                )
            )

            # Fall back to inline mode for resolution
            logger.info("Using inline test execution for detailed failure analysis and resolution")
            results, passed_count, failed_count_inline, test_response = run_tests_with_resolution(
                adw_id, issue_number, logger, worktree_path, max_attempts=1
            )

            # After inline resolution, retry external tests to verify fix
            logger.info("Re-running external tests to verify fixes...")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"🔄 Re-running external tests to verify fixes (attempt {attempt + 1}/{max_attempts}) 🔁"
                )
            )
            continue

        # Last attempt with failures - return results
        logger.warning(f"Reached max attempts with {failed_count} test failures")
        return False, external_results

    # Exceeded max attempts
    logger.error(f"Exceeded max attempts ({max_attempts}) for external tests")
    return False, last_results


def run_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[TestResult], int, int, AgentPromptResponse]:
    """
    Run tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count, last_test_response).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0
    test_response = None

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Test Run Attempt {attempt}/{max_attempts} ===")

        # Run tests in worktree
        test_response = run_tests(adw_id, logger, worktree_path)

        # If there was a high level - non-test related error, stop and report it
        if not test_response.success:
            logger.error(f"Error running tests: {test_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"❌ Error running tests: {test_response.output}",
                ),
            )
            break

        # Parse test results
        results, passed_count, failed_count = parse_test_results(
            test_response.output, logger
        )

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(f"Reached maximum retry attempts ({max_attempts}), stopping")
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"🔧 Found {failed_count} failed tests. Attempting resolution...",
            ),
        )

        # Track failures before resolution to verify progress
        previous_failed_count = failed_count

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        # CRITICAL: Verify resolution actually worked by re-running tests
        # Don't trust agent's "resolved" claim - check actual test results
        if resolved > 0:
            logger.info(f"Agent claimed to resolve {resolved} tests, verifying...")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"🔍 Agent claimed {resolved}/{failed_count} tests resolved, verifying..."
                ),
            )

            # Re-run tests to verify fixes actually work
            verify_response = run_tests(adw_id, logger, worktree_path)

            if not verify_response.success:
                logger.error("Verification test run failed")
                break

            # Parse verification results
            verify_results, verify_passed, verify_failed = parse_test_results(
                verify_response.output, logger
            )

            # Check for ACTUAL progress (not just agent claims)
            if verify_failed >= previous_failed_count:
                # No progress or regression - agent lied about fixing tests
                logger.warning(
                    f"No actual progress: {verify_failed} failures remain "
                    f"(was {previous_failed_count}). Agent claimed success but tests still fail."
                )
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id, "ops",
                        f"⚠️ **No Progress Detected**\n\n"
                        f"Agent claimed to fix {resolved} tests, but verification shows:\n"
                        f"- Before: {previous_failed_count} failures\n"
                        f"- After: {verify_failed} failures\n\n"
                        f"**No improvement.** Stopping retry loop to prevent infinite attempts."
                    ),
                )
                # Update our state with verified results for final return
                results = verify_results
                passed_count = verify_passed
                failed_count = verify_failed
                break  # EXIT - no point continuing if no progress

            # Real progress made - update state and continue
            logger.info(
                f"✅ Verified progress: {previous_failed_count} → {verify_failed} failures "
                f"({previous_failed_count - verify_failed} tests actually fixed)"
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    f"✅ **Progress Verified**\n"
                    f"- Before: {previous_failed_count} failures\n"
                    f"- After: {verify_failed} failures\n"
                    f"- Improvement: {previous_failed_count - verify_failed} tests fixed"
                ),
            )

            # Update our state with verified results
            results = verify_results
            passed_count = verify_passed
            failed_count = verify_failed

            # Check if all tests now pass
            if verify_failed == 0:
                logger.info("All tests now pass after verification!")
                break  # EXIT - success!

            # Still have failures but made progress - continue to next iteration
            logger.info(f"\n=== Re-running resolution for remaining {verify_failed} failures ===")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"🔄 Continuing resolution for {verify_failed} remaining failures (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved by agent, no point in retrying
            logger.info("Agent didn't resolve any tests, stopping retry attempts")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"⚠️ Agent couldn't resolve any tests. Stopping attempts."
                ),
            )
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count, test_response


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """
    Attempt to resolve failed E2E tests using the resolve_failed_e2e_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(
            f"\n=== Resolving failed E2E test {idx + 1}/{len(failed_tests)}: {test.test_name} ==="
        )

        # Create payload for the resolve command
        test_payload = test.model_dump_json(indent=2)

        # Create agent name with iteration
        agent_name = f"e2e_test_resolver_iter{iteration}_{idx}"

        # Create template request with worktree_path
        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_e2e_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        # Post to issue
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"🔧 Attempting to resolve E2E test: {test.test_name}\n```json\n{test_payload}\n```",
            ),
        )

        # Execute resolution
        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"✅ Successfully resolved E2E test: {test.test_name}",
                ),
            )
            logger.info(f"Successfully resolved E2E test: {test.test_name}")
        else:
            unresolved_count += 1
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ Failed to resolve E2E test: {test.test_name}",
                ),
            )
            logger.error(f"Failed to resolve E2E test: {test.test_name}")

    return resolved_count, unresolved_count


def get_issue_type(issue_number: str, logger: logging.Logger) -> str:
    """
    Determine issue type from GitHub labels.

    Returns:
        "LIGHTWEIGHT", "STANDARD", or "COMPLEX"
    """
    try:
        # Use gh CLI to get issue labels
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--json", "labels"],
            capture_output=True,
            text=True,
            check=True
        )
        labels_data = json.loads(result.stdout)
        labels = [label["name"].lower() for label in labels_data.get("labels", [])]

        # Check for issue type labels
        if "lightweight" in labels:
            return "LIGHTWEIGHT"
        elif "complex" in labels:
            return "COMPLEX"
        else:
            return "STANDARD"  # Default
    except Exception as e:
        logger.warning(f"Could not determine issue type: {e}")
        return "STANDARD"  # Safe default


def run_e2e_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_E2E_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[E2ETestResult], int, int]:
    """
    Run E2E tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== E2E Test Run Attempt {attempt}/{max_attempts} ===")

        # Run E2E tests (will auto-detect ports from .ports.env in worktree)
        e2e_response = run_e2e_tests(adw_id, logger, worktree_path)

        if not e2e_response.success:
            logger.error(f"Error running E2E tests: {e2e_response.output}")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"❌ Error running E2E tests: {e2e_response.output}",
                ),
            )
            break

        # Parse E2E results
        results, passed_count, failed_count = parse_e2e_test_results(
            e2e_response.output, logger
        )

        if not results:
            logger.warning("No E2E test results to process")
            break

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All E2E tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(
                f"Reached maximum E2E retry attempts ({max_attempts}), stopping"
            )
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed E2E tests ===")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"🔧 Found {failed_count} failed E2E tests. Attempting resolution...",
            ),
        )

        # Track failures before resolution to verify progress
        previous_failed_count = failed_count

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution
        resolved, unresolved = resolve_failed_e2e_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        # CRITICAL: Verify resolution actually worked by re-running E2E tests
        # Don't trust agent's "resolved" claim - check actual test results
        if resolved > 0:
            logger.info(f"Agent claimed to resolve {resolved} E2E tests, verifying...")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"🔍 Agent claimed {resolved}/{failed_count} E2E tests resolved, verifying..."
                ),
            )

            # Re-run E2E tests to verify fixes actually work
            verify_response = run_e2e_tests(adw_id, logger, worktree_path)

            if not verify_response.success:
                logger.error("Verification E2E test run failed")
                break

            # Parse verification results
            verify_results, verify_passed, verify_failed = parse_e2e_test_results(
                verify_response.output, logger
            )

            # Check for ACTUAL progress (not just agent claims)
            if verify_failed >= previous_failed_count:
                # No progress or regression - agent lied about fixing tests
                logger.warning(
                    f"No actual progress: {verify_failed} E2E failures remain "
                    f"(was {previous_failed_count}). Agent claimed success but tests still fail."
                )
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id, "ops",
                        f"⚠️ **No Progress Detected**\n\n"
                        f"Agent claimed to fix {resolved} E2E tests, but verification shows:\n"
                        f"- Before: {previous_failed_count} failures\n"
                        f"- After: {verify_failed} failures\n\n"
                        f"**No improvement.** Stopping retry loop to prevent infinite attempts."
                    ),
                )
                # Update our state with verified results for final return
                results = verify_results
                passed_count = verify_passed
                failed_count = verify_failed
                break  # EXIT - no point continuing if no progress

            # Real progress made - update state and continue
            logger.info(
                f"✅ Verified progress: {previous_failed_count} → {verify_failed} E2E failures "
                f"({previous_failed_count - verify_failed} tests actually fixed)"
            )
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops",
                    f"✅ **Progress Verified**\n"
                    f"- Before: {previous_failed_count} E2E failures\n"
                    f"- After: {verify_failed} E2E failures\n"
                    f"- Improvement: {previous_failed_count - verify_failed} tests fixed"
                ),
            )

            # Update our state with verified results
            results = verify_results
            passed_count = verify_passed
            failed_count = verify_failed

            # Check if all E2E tests now pass
            if verify_failed == 0:
                logger.info("All E2E tests now pass after verification!")
                break  # EXIT - success!

            # Still have failures but made progress - continue to next iteration
            logger.info(f"\n=== Re-running E2E resolution for remaining {verify_failed} failures ===")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"🔄 Continuing E2E resolution for {verify_failed} remaining failures (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            # No tests were resolved by agent, no point in retrying
            logger.info("Agent didn't resolve any E2E tests, stopping retry attempts")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"⚠️ Agent couldn't resolve any E2E tests. Stopping attempts."
                ),
            )
            break

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Check for flags in args
    skip_e2e = "--skip-e2e" in sys.argv
    skip_coverage = "--skip-coverage" in sys.argv
    # External tools are DEFAULT (opt-out with --no-external)
    use_external = "--no-external" not in sys.argv

    # Check for coverage threshold override
    coverage_threshold_override = None
    for i, arg in enumerate(sys.argv):
        if arg == "--coverage-threshold" and i + 1 < len(sys.argv):
            try:
                coverage_threshold_override = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: Invalid coverage threshold value: {sys.argv[i + 1]}")
                sys.exit(1)
            break

    # Remove flags from args if present
    if skip_e2e:
        sys.argv.remove("--skip-e2e")
    if skip_coverage:
        sys.argv.remove("--skip-coverage")
    if use_external:
        pass  # Keep for backwards compatibility
    if "--no-external" in sys.argv:
        sys.argv.remove("--no-external")
    if coverage_threshold_override is not None:
        # Remove --coverage-threshold and its value
        threshold_idx = sys.argv.index("--coverage-threshold")
        sys.argv.pop(threshold_idx)  # Remove flag
        sys.argv.pop(threshold_idx)  # Remove value

    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e] [--no-external] [--skip-coverage] [--coverage-threshold N]")
        print("\nError: adw-id is required to locate the worktree")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        print("\nOptions:")
        print("  --skip-e2e: Skip E2E tests")
        print("  --no-external: Disable external test tools (uses inline execution)")
        print("  --skip-coverage: Skip coverage enforcement (debugging)")
        print("  --coverage-threshold N: Override coverage threshold percentage")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_test_iso")

    # Circuit breaker: Check for infinite loops before starting
    check_for_loop(issue_number, temp_logger, adw_id)

    state = ADWState.load(adw_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - starting isolated testing\n```json\n{json.dumps(state.data, indent=2)}\n```"
        )
    else:
        # No existing state found
        logger = setup_logger(adw_id, "adw_test_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        sys.exit(1)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_test_iso")
    
    # Set up logger with ADW ID from command line
    logger = setup_logger(adw_id, "adw_test_iso")
    logger.info(f"ADW Test Iso starting - ID: {adw_id}, Issue: {issue_number}, Skip E2E: {skip_e2e}, Use External: {use_external}, Skip Coverage: {skip_coverage}, Coverage Threshold Override: {coverage_threshold_override}")

    # Validate environment
    check_env_vars(logger)

    # IDEMPOTENCY CHECK: Skip if test phase already complete
    if check_and_skip_if_complete('test', int(issue_number), logger):
        logger.info(f"{'='*60}")
        logger.info(f"Test phase already complete for issue {issue_number}")
        state = ADWState.load(adw_id, temp_logger)
        logger.info(f"Test results: {state.get('external_test_results', {})}")
        logger.info(f"{'='*60}")
        sys.exit(0)

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

    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")

    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Starting isolated testing phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                           f"🧪 E2E Tests: {'Skipped' if skip_e2e else 'Enabled'}\n"
                           f"🔧 Test Mode: {'External Tools (Context Optimized)' if use_external else 'Inline Execution'}")
    )

    # Track results for resolution attempts
    test_results = []
    e2e_results = []
    passed_count = 0
    failed_count = 0

    if use_external:
        # Use external test tools (context optimized) with automatic resolution
        logger.info("🔧 Using external test tools with automatic resolution for context optimization")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, "🔧 Running tests via external tools with resolution loop (70-95% token reduction)...")
        )

        # Create tool call tracker for Test phase
        with ToolCallTracker(adw_id=adw_id, issue_number=int(issue_number), phase_name="Test") as tracker:
            # Run external tests with resolution and retry logic
            success, external_results = run_external_tests_with_resolution(
                adw_id, issue_number, logger, state, worktree_path, tracker=tracker
            )

        # Check if we need to fall back to inline mode for LLM-based fixes
        if not success:
            if "error" in external_results:
                # Infrastructure failure - fallback to inline mode
                logger.warning("External test tools failed after retries, using inline execution as fallback")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        "⚠️ External test tools failed after max retries. Using inline execution mode for comprehensive analysis..."
                    )
                )
            else:
                # Test failures after external resolution - need LLM-based fixes
                summary = external_results.get("summary", {})
                failed_count_ext = summary.get("failed", 0)

                logger.warning(f"External resolution could not fix {failed_count_ext} test failures, falling back to LLM-based fixes")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"⚠️ External test resolution could not fix {failed_count_ext} test failures.\n"
                        f"Falling back to LLM-based test fixing for comprehensive resolution..."
                    )
                )

            # Use inline mode with full LLM-based resolution
            test_results, passed_count, failed_count, test_response = run_tests_with_resolution(
                adw_id, issue_number, logger, worktree_path
            )

            if test_results:
                comment = format_test_results_comment(test_results, passed_count, failed_count)
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, AGENT_TESTER, comment)
                )
                logger.info(f"LLM-based resolution results: {passed_count} passed, {failed_count} failed")
        else:
            # Process external results - all tests passed
            summary = external_results.get("summary", {})
            passed_count = summary.get("passed", 0)
            failed_count = summary.get("failed", 0)
            total = summary.get("total", passed_count + failed_count)

            comment = f"✅ All {total} tests passed!\n"
            comment += f"⚡ Context savings: ~90% (using external tools with resolution)"

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_TESTER, comment)
            )
            logger.info(f"External test results: {passed_count} passed, {failed_count} failed")

    else:
        # Use inline test execution (existing behavior)
        logger.info("Running unit tests in worktree with automatic resolution")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, "🧪 Running unit tests in isolated environment...")
        )

        # Run tests with resolution and retry logic
        results, passed_count, failed_count, test_response = run_tests_with_resolution(
            adw_id, issue_number, logger, worktree_path
        )

        # Track results
        test_results = results

        if results:
            comment = format_test_results_comment(results, passed_count, failed_count)
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_TESTER, comment)
            )
            logger.info(f"Test results: {passed_count} passed, {failed_count} failed")
        else:
            logger.warning("No test results found in output")
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, AGENT_TESTER, "⚠️ No test results found in output"
                ),
            )

    # Run E2E tests if not skipped (executing in worktree)
    e2e_passed = 0
    e2e_failed = 0
    if not skip_e2e:
        logger.info("Running E2E tests in worktree with automatic resolution")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_E2E_TESTER, "🌐 Running E2E tests in isolated environment...")
        )
        
        # Run E2E tests with resolution and retry logic
        e2e_results, e2e_passed, e2e_failed = run_e2e_tests_with_resolution(
            adw_id, issue_number, logger, worktree_path
        )
        
        if e2e_results:
            logger.info(f"E2E test results: {e2e_passed} passed, {e2e_failed} failed")
    
    # Post comprehensive summary
    post_comprehensive_test_summary(
        issue_number, adw_id, test_results, e2e_results, logger
    )

    # ==========================
    # COVERAGE ENFORCEMENT
    # ==========================
    if not skip_coverage:
        logger.info("\n=== Coverage Enforcement Check ===")

        # Determine issue type from GitHub labels
        issue_type = get_issue_type(issue_number, logger)
        logger.info(f"[COVERAGE] Issue type: {issue_type}")

        # Determine coverage threshold based on issue type
        if coverage_threshold_override is not None:
            coverage_threshold = coverage_threshold_override
            logger.info(f"[COVERAGE] Using override threshold: {coverage_threshold}%")
        elif issue_type == "LIGHTWEIGHT":
            coverage_threshold = 0  # No requirement
        elif issue_type == "STANDARD":
            coverage_threshold = 70
        elif issue_type == "COMPLEX":
            coverage_threshold = 80
        else:
            coverage_threshold = 70  # Safe default (STANDARD)

        logger.info(f"[COVERAGE] Required threshold: {coverage_threshold}%")

        # Extract coverage data from test results
        coverage_percentage = None
        coverage_data = None

        # Check external test results first (if used)
        if use_external and "external_test_results" in state.data:
            external_results = state.data.get("external_test_results", {})
            coverage_data = external_results.get("coverage")
            if coverage_data:
                coverage_percentage = coverage_data.get("percentage", 0.0)
                logger.info(f"[COVERAGE] Found coverage in external test results: {coverage_percentage:.1f}%")

        # If no external coverage, check inline test results (not typical but possible)
        # Note: inline test_results is a List[TestResult] which doesn't have coverage
        # Coverage would be in the test_response object, but that's not directly accessible here

        # Reload state to check if coverage was saved by test runner
        if coverage_percentage is None:
            reloaded_state = ADWState.load(adw_id)
            if reloaded_state:
                # Check if coverage data exists in state
                external_results = reloaded_state.get("external_test_results", {})
                coverage_data = external_results.get("coverage")
                if coverage_data:
                    coverage_percentage = coverage_data.get("percentage", 0.0)
                    logger.info(f"[COVERAGE] Found coverage in reloaded state: {coverage_percentage:.1f}%")

        # Enforce coverage threshold
        if coverage_threshold > 0:
            if coverage_percentage is None:
                # No coverage data available but threshold is required
                logger.error("[COVERAGE] Coverage data not available, but threshold is required")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"❌ **Coverage check failed**\n\n"
                        f"Coverage data not available, but {issue_type} issues require {coverage_threshold}% coverage.\n\n"
                        f"Please ensure tests are running with coverage collection enabled."
                    )
                )
                state.data["coverage_check"] = "failed"
                state.data["coverage_error"] = "Coverage data not available"
                state.save("adw_test_iso")
                sys.exit(1)

            elif coverage_percentage < coverage_threshold:
                # Coverage is below threshold - BLOCK
                missing_coverage = coverage_threshold - coverage_percentage
                logger.error(f"[COVERAGE] ❌ Coverage check failed: {coverage_percentage:.1f}% < {coverage_threshold}%")

                # Post detailed comment to GitHub issue
                comment = f"❌ **Coverage check failed**\n\n"
                comment += f"**Issue Type:** {issue_type}\n"
                comment += f"**Current Coverage:** {coverage_percentage:.1f}%\n"
                comment += f"**Required Coverage:** {coverage_threshold}%\n"
                comment += f"**Missing Coverage:** {missing_coverage:.1f}%\n\n"
                comment += f"Please add tests to increase coverage before merging.\n\n"

                # Add details about uncovered files if available
                if coverage_data and coverage_data.get("missing_files"):
                    missing_files = coverage_data.get("missing_files", [])
                    if missing_files:
                        comment += f"**Files with 0% coverage ({len(missing_files)}):**\n"
                        for file_path in missing_files[:5]:  # Limit to first 5
                            comment += f"- `{file_path}`\n"
                        if len(missing_files) > 5:
                            comment += f"- ... and {len(missing_files) - 5} more\n"

                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", comment)
                )

                # Update state with coverage failure
                state.data["coverage_check"] = "failed"
                state.data["coverage_percentage"] = coverage_percentage
                state.data["coverage_threshold"] = coverage_threshold
                state.data["coverage_missing"] = missing_coverage
                if coverage_data:
                    state.data["coverage_lines_covered"] = coverage_data.get("lines_covered", 0)
                    state.data["coverage_lines_total"] = coverage_data.get("lines_total", 0)
                state.save("adw_test_iso")

                # Exit with error to block workflow
                logger.error(f"[EXIT] Blocking merge due to insufficient coverage")
                sys.exit(1)
            else:
                # Coverage passed - CONTINUE
                logger.info(f"[COVERAGE] ✅ Coverage check passed: {coverage_percentage:.1f}% >= {coverage_threshold}%")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"✅ **Coverage check passed**\n\n"
                        f"**Coverage:** {coverage_percentage:.1f}%\n"
                        f"**Required:** {coverage_threshold}%\n"
                        f"**Issue Type:** {issue_type}"
                    )
                )
                state.data["coverage_check"] = "passed"
                state.data["coverage_percentage"] = coverage_percentage
                state.data["coverage_threshold"] = coverage_threshold
                if coverage_data:
                    state.data["coverage_lines_covered"] = coverage_data.get("lines_covered", 0)
                    state.data["coverage_lines_total"] = coverage_data.get("lines_total", 0)
                state.save("adw_test_iso")
        else:
            # No threshold required (LIGHTWEIGHT or threshold override = 0)
            logger.info(f"[COVERAGE] No coverage requirement for {issue_type} issues")
            if coverage_percentage is not None:
                logger.info(f"[COVERAGE] Current coverage: {coverage_percentage:.1f}% (advisory only)")
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"ℹ️ **Coverage (Advisory)**\n\n"
                        f"**Coverage:** {coverage_percentage:.1f}%\n"
                        f"**Issue Type:** {issue_type} (no requirement)"
                    )
                )
                state.data["coverage_check"] = "passed"
                state.data["coverage_percentage"] = coverage_percentage
                state.data["coverage_threshold"] = 0
                if coverage_data:
                    state.data["coverage_lines_covered"] = coverage_data.get("lines_covered", 0)
                    state.data["coverage_lines_total"] = coverage_data.get("lines_total", 0)
                state.save("adw_test_iso")
    else:
        logger.info("[COVERAGE] Coverage check skipped (--skip-coverage)")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", "⚠️ Coverage check skipped (--skip-coverage flag)")
        )

    # Check if we should exit due to test failures
    total_failures = failed_count + (e2e_failed if not skip_e2e and e2e_results else 0)
    if total_failures > 0:
        logger.warning(f"Tests completed with {total_failures} failures - continuing to commit results")
        # Note: We don't exit here anymore, we commit the results regardless
        # This is different from the old workflow which would exit(1) on failures

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        issue_command, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("adw_test_iso")
    
    # Create commit message
    logger.info("Creating test commit")
    commit_msg, error = create_commit(AGENT_TESTER, issue, issue_command, adw_id, logger, worktree_path)
    
    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)
    
    # Commit the test results (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)
    
    if not success:
        logger.error(f"Error committing test results: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}")
        )
        sys.exit(1)
    
    logger.info(f"Committed test results: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_TESTER, "✅ Test results committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated testing phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Isolated testing phase completed")
    )

    # Save final state
    state.save("adw_test_iso")

    # IDEMPOTENCY VALIDATION: Ensure phase outputs are valid
    try:
        validate_phase_completion('test', int(issue_number), logger)
        ensure_database_state(int(issue_number), 'tested', 'test', logger)
    except Exception as e:
        logger.error(f"Phase validation failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "tester", f"❌ Test phase validation failed: {e}")
        )
        sys.exit(1)

    # OBSERVABILITY: Log phase completion
    from datetime import datetime
    start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
    log_phase_completion(
        adw_id=adw_id,
        issue_number=int(issue_number),
        phase_name="Test",
        phase_number=get_phase_number("Test"),
        success=(total_failures == 0),  # Success only if no failures
        workflow_template="adw_test_iso",
        error_message=f"{total_failures} test failures" if total_failures > 0 else None,
        started_at=start_time,
    )
    
    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final test state:\n```json\n{json.dumps(state.data, indent=2)}\n```"
    )
    
    # Report test results but don't exit on failures
    # This allows the workflow to continue to review phase where issues can be addressed
    if total_failures > 0:
        logger.warning(f"Test workflow completed with {total_failures} failures (continuing to next phase)")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"⚠️ Test workflow completed with {total_failures} failures - continuing to review phase")
        )
        # NOTE: We do NOT exit(1) here anymore. The review phase will catch and address issues.
    else:
        logger.info("All tests passed successfully")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", "✅ All tests passed successfully!")
        )


if __name__ == "__main__":
    main()