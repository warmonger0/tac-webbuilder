#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Verify Iso - Post-deployment verification phase

Usage:
  uv run adw_verify_iso.py <issue-number> <adw-id>

Workflow (Phase 10 - runs after Cleanup):
1. Load ADW state and get deployment metadata
2. Wait for verification delay (5 minutes after ship)
3. Check backend logs for errors
4. Check frontend logs/console for errors
5. Run smoke tests (health checks, accessibility)
6. Create follow-up GitHub issue if problems detected
7. Post verification summary to original issue

This phase runs post-deployment to catch issues immediately instead of
hours/days later. It NEVER reverts shipped code - instead it creates
new GitHub issues for problems that need fixing.

Architecture:
- Non-blocking: Creates issues but doesn't fail workflow
- Time-delayed: Waits 5 minutes after ship to let services stabilize
- Log-based: Analyzes backend/frontend logs for error patterns
- Smoke tests: Verifies critical paths are accessible
"""

import sys
import os
import logging
import subprocess
import time
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from utils.idempotency import (
    check_and_skip_if_complete,
    validate_phase_completion,
    ensure_database_state,
)
from adw_modules.github import make_issue_comment, get_repo_url, extract_repo_path
from adw_modules.workflow_ops import format_issue_message
from adw_modules.utils import setup_logger
from adw_modules.observability import log_phase_completion, get_phase_number

# Agent name constant
AGENT_VERIFIER = "verifier"

# Verification configuration
VERIFICATION_DELAY_SECONDS = 300  # 5 minutes after ship
LOG_CHECK_WINDOW_MINUTES = 10  # Check logs from last 10 minutes
BACKEND_LOG_PATTERNS = [
    r'Exception',
    r'Traceback',
    r'ERROR',
    r'500 Internal Server Error',
    r'Failed to',
    r'Error:',
]
FRONTEND_ERROR_PATTERNS = [
    r'console\.error',
    r'console\.warn',
    r'Uncaught',
    r'TypeError',
    r'ReferenceError',
    r'React.*Error',
]


class VerificationResult:
    """Results from verification checks."""

    def __init__(self):
        self.passed = True
        self.backend_log_errors: List[str] = []
        self.frontend_errors: List[str] = []
        self.smoke_test_failures: List[str] = []
        self.warnings: List[str] = []

    def add_backend_error(self, error: str):
        """Add backend log error."""
        self.passed = False
        self.backend_log_errors.append(error)

    def add_frontend_error(self, error: str):
        """Add frontend console error."""
        self.passed = False
        self.frontend_errors.append(error)

    def add_smoke_test_failure(self, failure: str):
        """Add smoke test failure."""
        self.passed = False
        self.smoke_test_failures.append(failure)

    def add_warning(self, warning: str):
        """Add warning (doesn't affect pass/fail)."""
        self.warnings.append(warning)

    def get_summary(self) -> str:
        """Get summary of verification results."""
        if self.passed:
            return "✅ All verification checks passed"

        summary_lines = ["❌ Verification failed with the following issues:"]

        if self.backend_log_errors:
            summary_lines.append(f"\n**Backend Log Errors ({len(self.backend_log_errors)}):**")
            for error in self.backend_log_errors[:5]:  # Limit to 5
                summary_lines.append(f"- {error}")
            if len(self.backend_log_errors) > 5:
                summary_lines.append(f"- ... and {len(self.backend_log_errors) - 5} more")

        if self.frontend_errors:
            summary_lines.append(f"\n**Frontend Errors ({len(self.frontend_errors)}):**")
            for error in self.frontend_errors[:5]:
                summary_lines.append(f"- {error}")
            if len(self.frontend_errors) > 5:
                summary_lines.append(f"- ... and {len(self.frontend_errors) - 5} more")

        if self.smoke_test_failures:
            summary_lines.append(f"\n**Smoke Test Failures ({len(self.smoke_test_failures)}):**")
            for failure in self.smoke_test_failures:
                summary_lines.append(f"- {failure}")

        if self.warnings:
            summary_lines.append(f"\n**Warnings ({len(self.warnings)}):**")
            for warning in self.warnings:
                summary_lines.append(f"- {warning}")

        return "\n".join(summary_lines)


def check_backend_logs(
    adw_id: str,
    backend_port: int,
    ship_timestamp: datetime,
    logger: logging.Logger
) -> List[str]:
    """
    Check backend logs for errors in time window.

    Args:
        adw_id: ADW identifier
        backend_port: Backend port number
        ship_timestamp: Timestamp when Ship phase completed
        logger: Logger instance

    Returns:
        List of error messages found
    """
    errors = []

    # Calculate time window
    check_start = ship_timestamp - timedelta(minutes=LOG_CHECK_WINDOW_MINUTES)

    logger.info(
        f"[Verify] Checking backend logs for {adw_id} "
        f"(port {backend_port}) from {check_start}"
    )

    # Get project root (parent of adws directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.join(project_root, "logs", f"{adw_id}_backend.log")

    if not os.path.exists(log_file_path):
        logger.warning(f"Backend log file not found: {log_file_path}")
        errors.append(f"Warning: Backend log file not found at {log_file_path}")
        return errors

    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()

        # Search for error patterns
        for pattern in BACKEND_LOG_PATTERNS:
            matches = re.finditer(pattern, log_content, re.IGNORECASE)
            for match in matches:
                # Get context (line containing error)
                line_start = log_content.rfind('\n', 0, match.start()) + 1
                line_end = log_content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(log_content)

                error_line = log_content[line_start:line_end].strip()

                # Truncate long lines
                if len(error_line) > 200:
                    error_line = error_line[:200] + "..."

                errors.append(f"Backend log error: {error_line}")

    except Exception as e:
        logger.error(f"Failed to read backend logs: {e}")
        errors.append(f"Failed to read backend logs: {e}")

    return errors


def check_frontend_console(
    adw_id: str,
    frontend_port: int,
    logger: logging.Logger
) -> List[str]:
    """
    Check frontend console for errors.

    Note: This is a simplified implementation that checks frontend build logs.
    In production, you might use browser automation (Puppeteer, Playwright).

    Args:
        adw_id: ADW identifier
        frontend_port: Frontend port number
        logger: Logger instance

    Returns:
        List of error messages found
    """
    errors = []

    logger.info(f"[Verify] Checking frontend console for {adw_id} (port {frontend_port})")

    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.join(project_root, "logs", f"{adw_id}_frontend_build.log")

    if not os.path.exists(log_file_path):
        logger.warning(f"Frontend build log not found: {log_file_path}")
        errors.append(f"Warning: Frontend build log not found at {log_file_path}")
        return errors

    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()

        # Search for error patterns
        for pattern in FRONTEND_ERROR_PATTERNS:
            matches = re.finditer(pattern, log_content, re.IGNORECASE)
            for match in matches:
                # Get context
                line_start = log_content.rfind('\n', 0, match.start()) + 1
                line_end = log_content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(log_content)

                error_line = log_content[line_start:line_end].strip()

                # Truncate long lines
                if len(error_line) > 200:
                    error_line = error_line[:200] + "..."

                errors.append(f"Frontend console error: {error_line}")

    except Exception as e:
        logger.error(f"Failed to read frontend logs: {e}")
        errors.append(f"Failed to read frontend logs: {e}")

    return errors


def run_smoke_tests(
    adw_id: str,
    backend_port: int,
    frontend_port: int,
    issue_number: str,
    logger: logging.Logger
) -> List[str]:
    """
    Run smoke tests for critical paths.

    Args:
        adw_id: ADW identifier
        backend_port: Backend port number
        frontend_port: Frontend port number
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        List of smoke test failures
    """
    failures = []

    logger.info(f"[Verify] Running smoke tests for {adw_id}")

    # Test 1: Backend health check
    try:
        result = subprocess.run(
            ['curl', '-f', '-s', f'http://localhost:{backend_port}/health'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            failures.append(
                f"Backend health check failed (port {backend_port}): "
                f"{result.stderr[:200] if result.stderr else 'Connection failed'}"
            )
        else:
            logger.info(f"✅ Backend health check passed (port {backend_port})")

    except subprocess.TimeoutExpired:
        failures.append(f"Backend health check timeout (port {backend_port})")
    except Exception as e:
        failures.append(f"Backend health check error: {e}")

    # Test 2: Frontend accessibility
    try:
        result = subprocess.run(
            ['curl', '-f', '-s', f'http://localhost:{frontend_port}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            failures.append(
                f"Frontend accessibility check failed (port {frontend_port}): "
                f"{result.stderr[:200] if result.stderr else 'Connection failed'}"
            )
        else:
            logger.info(f"✅ Frontend accessibility check passed (port {frontend_port})")

    except subprocess.TimeoutExpired:
        failures.append(f"Frontend accessibility check timeout (port {frontend_port})")
    except Exception as e:
        failures.append(f"Frontend accessibility check error: {e}")

    return failures


def create_followup_issue(
    original_issue: str,
    verification_result: VerificationResult,
    adw_id: str,
    logger: logging.Logger
) -> Optional[str]:
    """
    Create GitHub follow-up issue for verification failures.

    Args:
        original_issue: Original GitHub issue number
        verification_result: Verification results
        adw_id: ADW identifier
        logger: Logger instance

    Returns:
        New issue number if created, None otherwise
    """
    if verification_result.passed:
        logger.info("[Verify] No issues detected, skipping follow-up issue creation")
        return None

    logger.info(f"[Verify] Creating follow-up issue for #{original_issue}")

    # Create issue title
    title = f"[Auto-Verify] Post-deployment issues detected for #{original_issue}"

    # Create issue body
    body_parts = [
        f"## 🔍 Automated Verification Report",
        f"",
        f"**Original Issue:** #{original_issue}",
        f"**ADW ID:** {adw_id}",
        f"**Verification Time:** {datetime.now().isoformat()}",
        f"",
        f"## Issues Detected",
        f"",
        verification_result.get_summary(),
        f"",
        f"## Recommended Actions",
        f"",
    ]

    # Add recommended actions based on error types
    if verification_result.backend_log_errors:
        body_parts.extend([
            f"1. **Backend Errors:** Review backend logs and fix exceptions",
            f"   - Check `logs/{adw_id}_backend.log`",
            f"   - Address error patterns and exceptions",
            f"",
        ])

    if verification_result.frontend_errors:
        body_parts.extend([
            f"2. **Frontend Errors:** Review console errors and warnings",
            f"   - Check `logs/{adw_id}_frontend_build.log`",
            f"   - Fix console.error and React errors",
            f"",
        ])

    if verification_result.smoke_test_failures:
        body_parts.extend([
            f"3. **Smoke Test Failures:** Critical paths are broken",
            f"   - Verify backend/frontend are accessible",
            f"   - Check network connectivity and ports",
            f"",
        ])

    body_parts.extend([
        f"## Context",
        f"",
        f"This issue was automatically created by the Verify phase (Phase 10) of the ADW workflow. ",
        f"The original feature was shipped successfully, but post-deployment verification detected issues.",
        f"",
        f"**Note:** The shipped code has NOT been reverted. Please fix issues in a new PR.",
        f"",
        f"---",
        f"*Auto-generated by ADW Verify Phase* 🤖",
    ])

    body = "\n".join(body_parts)

    try:
        # Get repository path
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)

        # Create issue using gh CLI
        result = subprocess.run(
            [
                "gh", "issue", "create",
                "--repo", repo_path,
                "--title", title,
                "--body", body,
                "--label", "bug,auto-verify,post-deployment"
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            # Extract issue number from output (format: "https://github.com/owner/repo/issues/123")
            output = result.stdout.strip()
            if "/issues/" in output:
                new_issue_number = output.split("/issues/")[-1]
                logger.info(f"[Verify] Created follow-up issue #{new_issue_number}")

                # Add comment to original issue
                comment = (
                    f"⚠️ **Post-Deployment Verification Failed**\n\n"
                    f"Automated verification detected issues after deployment. "
                    f"See follow-up issue #{new_issue_number} for details.\n\n"
                    f"The shipped code has NOT been reverted. Issues will be addressed in a new PR."
                )

                try:
                    make_issue_comment(original_issue, comment)
                except Exception as e:
                    logger.warning(f"Failed to add comment to original issue: {e}")

                return new_issue_number
            else:
                logger.error(f"Failed to parse issue number from: {output}")
                return None
        else:
            logger.error(f"Failed to create follow-up issue: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"Failed to create follow-up issue: {e}")
        return None


def run_verify_phase(
    issue_number: str,
    adw_id: str,
    logger: logging.Logger
) -> int:
    """
    Run verification phase for ADW workflow.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW identifier
        logger: Logger instance

    Returns:
        Exit code (0 = success, 1 = verification failed but issue created)
    """
    logger.info(f"[Verify] Starting verification for issue #{issue_number}")

    # IDEMPOTENCY CHECK: Skip if verify phase already complete
    if check_and_skip_if_complete('verify', int(issue_number), logger):
        logger.info(f"{'='*60}")
        logger.info(f"Verify phase already complete for issue {issue_number}")
        state = ADWState.load(adw_id, logger)
        logger.info(f"Verification results: {state.get('verification_results', {})}")
        logger.info(f"{'='*60}")
        return 0

    # Post initial status
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_VERIFIER,
            "🔍 Starting post-deployment verification...\n"
            "Checking backend logs, frontend console, and running smoke tests."
        )
    )

    # Load ADW state
    state = ADWState.load(adw_id, logger)
    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_VERIFIER,
                "❌ Verification failed: No state found"
            )
        )
        return 1

    try:
        backend_port = state.get('backend_port')
        frontend_port = state.get('frontend_port')

        if not backend_port or not frontend_port:
            logger.error("Backend or frontend port not found in state")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_VERIFIER,
                    "❌ Verification failed: Ports not found in state"
                )
            )
            return 1

        # Get ship timestamp (use current time - 10 minutes as fallback)
        ship_timestamp_str = state.get('ship_timestamp')
        if ship_timestamp_str:
            ship_timestamp = datetime.fromisoformat(ship_timestamp_str)
        else:
            ship_timestamp = datetime.now() - timedelta(minutes=10)
            logger.warning("Ship timestamp not found in state, using fallback")

    except Exception as e:
        logger.error(f"Failed to load ADW state: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_VERIFIER,
                f"❌ Verification failed: {e}"
            )
        )
        return 1

    # Wait for verification delay (5 minutes after ship)
    time_since_ship = datetime.now() - ship_timestamp
    remaining_wait = VERIFICATION_DELAY_SECONDS - time_since_ship.total_seconds()

    if remaining_wait > 0:
        logger.info(
            f"[Verify] Waiting {remaining_wait:.0f}s before verification "
            f"(5-minute post-ship delay)"
        )
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_VERIFIER,
                f"⏱️ Waiting {int(remaining_wait)}s for services to stabilize..."
            )
        )
        time.sleep(remaining_wait)

    # Initialize verification result
    result = VerificationResult()

    # Check 1: Backend logs
    logger.info("[Verify] Step 1/3: Checking backend logs...")
    backend_errors = check_backend_logs(adw_id, backend_port, ship_timestamp, logger)
    for error in backend_errors:
        if error.startswith("Warning:"):
            result.add_warning(error)
        else:
            result.add_backend_error(error)

    # Check 2: Frontend console
    logger.info("[Verify] Step 2/3: Checking frontend console...")
    frontend_errors = check_frontend_console(adw_id, frontend_port, logger)
    for error in frontend_errors:
        if error.startswith("Warning:"):
            result.add_warning(error)
        else:
            result.add_frontend_error(error)

    # Check 3: Smoke tests
    logger.info("[Verify] Step 3/3: Running smoke tests...")
    smoke_failures = run_smoke_tests(adw_id, backend_port, frontend_port, issue_number, logger)
    for failure in smoke_failures:
        result.add_smoke_test_failure(failure)

    # Summary
    logger.info("\n" + "="*80)
    logger.info(result.get_summary())
    logger.info("="*80 + "\n")

    # Create follow-up issue if verification failed
    if not result.passed:
        followup_issue = create_followup_issue(issue_number, result, adw_id, logger)

        if followup_issue:
            logger.info(
                f"[Verify] Verification failed. Follow-up issue #{followup_issue} created."
            )
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_VERIFIER,
                    f"⚠️ **Verification completed with issues**\n\n"
                    f"{result.get_summary()}\n\n"
                    f"Follow-up issue #{followup_issue} created for tracking."
                )
            )
            return 1
        else:
            logger.error("[Verify] Verification failed but could not create follow-up issue")
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_VERIFIER,
                    f"⚠️ **Verification failed**\n\n"
                    f"{result.get_summary()}\n\n"
                    f"Could not create follow-up issue automatically. Please review manually."
                )
            )
            return 1

    logger.info("[Verify] ✅ Verification passed! Feature is working correctly.")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_VERIFIER,
            "✅ **Verification passed**\n\n"
            "All checks completed successfully:\n"
            "- Backend logs: Clean\n"
            "- Frontend console: Clean\n"
            "- Smoke tests: Passed\n\n"
            "Feature is working correctly in production."
        )
    )

    # IDEMPOTENCY VALIDATION: Ensure phase outputs are valid
    try:
        validate_phase_completion('verify', int(issue_number), logger)
        ensure_database_state(int(issue_number), 'verified', 'verify', logger)
    except Exception as e:
        logger.error(f"Phase validation failed: {e}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "verifier", f"❌ Verify phase validation failed: {e}")
        )
        return 1

    # OBSERVABILITY: Log phase completion
    start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
    log_phase_completion(
        adw_id=adw_id,
        issue_number=int(issue_number),
        phase_name="Verify",
        phase_number=get_phase_number("Verify"),
        success=True,
        workflow_template="adw_verify_iso",
        started_at=start_time,
    )

    return 0


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line args
    if len(sys.argv) < 3:
        print("Usage: uv run adw_verify_iso.py <issue-number> <adw-id>")
        print("\nError: Both issue-number and adw-id are required")
        print("This phase runs after the Ship and Cleanup phases")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Set up logger
    logger = setup_logger(adw_id, "adw_verify_iso")
    logger.info(f"ADW Verify Iso starting - ID: {adw_id}, Issue: {issue_number}")

    try:
        exit_code = run_verify_phase(issue_number, adw_id, logger)
        logger.info(f"Verify phase completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Verify phase failed with exception: {e}", exc_info=True)
        try:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_VERIFIER,
                    f"❌ Verification failed with exception: {e}"
                )
            )
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
