# Task: Implement Verify Phase for ADW Workflows

## Context
I'm working on the tac-webbuilder project. Currently, the ADW workflow has 9 phases (Plan → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup). Features are shipped and cleaned up, but there's no automated verification that deployed features are actually working. This session implements a 10th phase (Verify) that runs after Cleanup to check backend/frontend logs, run smoke tests, and create follow-up issues if problems are detected.

## Objective
Create a Verify phase that:
- Checks backend logs for errors in 5-minute window after ship
- Checks frontend console for errors and warnings
- Runs smoke tests for critical paths (API health, UI rendering)
- Auto-creates GitHub follow-up issues if verification fails
- Integrates with full SDLC workflow as 10th phase

## Background Information
- **Current Workflow:** 9 phases ending with Cleanup
- **Gap:** No post-deployment verification (issues discovered hours/days later)
- **Solution:** Add Verify phase after Cleanup to catch issues immediately

- **Architecture Decision (from Session 1):**
  - **Option B Selected:** Separate phase after Cleanup
  - **Workflow:** Build → Lint → Test → Review → Ship → Cleanup → **Verify**
  - **Error Handling:** Don't revert shipped code, create new GitHub issue instead
  - **Timing:** Run 5 minutes after Ship phase completes

- **Verification Types:**
  1. **Backend Log Checking:** Scan logs for exceptions, stack traces, 500 errors
  2. **Frontend Console Errors:** Detect console.error, console.warn, React errors
  3. **Smoke Tests:** Critical path verification (API endpoints, UI components)
  4. **Follow-up Issue Creation:** Auto-create GitHub issue with error context

- **Files to Create:**
  - `adws/adw_verify_iso.py` (~400-500 lines) - Main verify phase workflow
  - `adws/tests/test_verify_phase.py` (~200 lines) - Comprehensive tests

- **Files to Modify:**
  - `adws/adw_sdlc_complete_iso.py` - Add Verify phase to workflow chain
  - `adws/README.md` - Document 10th phase

---

## Step-by-Step Instructions

### Step 1: Understand Current Workflow Structure (20 min)

Read the existing workflow to understand integration points:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
```

**Read these files:**
1. `adw_sdlc_complete_iso.py` - Full 9-phase workflow orchestration
2. `adw_ship_iso.py` - Ship phase (understand what happens before Verify)
3. `adw_cleanup_operations.py` - Cleanup phase (Verify runs after this)
4. Look for state file structure and how phases pass data

**Document:**
- How phases are chained together
- State file location and format
- How to access ADW metadata (adw_id, issue_number, ports, worktree path)
- Error handling patterns in existing phases
- GitHub API integration patterns (for issue creation)

### Step 2: Create Verify Phase Module (90-120 min)

Create new file: `adws/adw_verify_iso.py`

```python
#!/usr/bin/env python3
"""
Verify Phase for ADW Workflows

Runs post-deployment verification after Cleanup phase to ensure shipped features
are working correctly. Checks logs, runs smoke tests, and creates follow-up issues
if problems are detected.

Architecture:
- Phase 10 in SDLC workflow (after Cleanup)
- Runs 5 minutes after Ship phase completes
- Non-blocking: Issues are created, but workflow doesn't fail
- Error handling: Don't revert code, create GitHub issue instead

Usage:
    python adw_verify_iso.py <issue_number>
"""

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.github_helpers import (
    create_github_issue,
    add_comment_to_issue,
    get_issue_details
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


def load_adw_state(issue_number: int) -> Dict:
    """Load ADW state file for the workflow."""
    state_file = Path(f"../agents/adw-{issue_number}/state.json")

    if not state_file.exists():
        logger.error(f"State file not found: {state_file}")
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file, 'r') as f:
        return json.load(f)


def check_backend_logs(
    adw_id: str,
    backend_port: int,
    ship_timestamp: datetime
) -> List[str]:
    """
    Check backend logs for errors in time window.

    Args:
        adw_id: ADW identifier
        backend_port: Backend port number
        ship_timestamp: Timestamp when Ship phase completed

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

    # Check backend log file (adjust path based on your logging setup)
    log_file = Path(f"../logs/{adw_id}_backend.log")

    if not log_file.exists():
        logger.warning(f"Backend log file not found: {log_file}")
        return [f"Warning: Backend log file not found at {log_file}"]

    try:
        with open(log_file, 'r') as f:
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

                # Check if error is within time window (basic timestamp check)
                # You may need to parse actual timestamps from logs
                errors.append(f"Backend log error: {error_line[:200]}")

    except Exception as e:
        logger.error(f"Failed to read backend logs: {e}")
        errors.append(f"Failed to read backend logs: {e}")

    return errors


def check_frontend_console(
    adw_id: str,
    frontend_port: int
) -> List[str]:
    """
    Check frontend console for errors.

    Note: This is a simplified implementation. In production, you might:
    - Use browser automation (Puppeteer, Playwright)
    - Check frontend build logs
    - Parse frontend server logs

    Args:
        adw_id: ADW identifier
        frontend_port: Frontend port number

    Returns:
        List of error messages found
    """
    errors = []

    logger.info(f"[Verify] Checking frontend console for {adw_id} (port {frontend_port})")

    # Check frontend build logs
    build_log = Path(f"../logs/{adw_id}_frontend_build.log")

    if not build_log.exists():
        logger.warning(f"Frontend build log not found: {build_log}")
        return [f"Warning: Frontend build log not found at {build_log}"]

    try:
        with open(build_log, 'r') as f:
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
                errors.append(f"Frontend console error: {error_line[:200]}")

    except Exception as e:
        logger.error(f"Failed to read frontend logs: {e}")
        errors.append(f"Failed to read frontend logs: {e}")

    return errors


def run_smoke_tests(
    adw_id: str,
    backend_port: int,
    frontend_port: int,
    issue_number: int
) -> List[str]:
    """
    Run smoke tests for critical paths.

    Args:
        adw_id: ADW identifier
        backend_port: Backend port number
        frontend_port: Frontend port number
        issue_number: GitHub issue number

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
                f"{result.stderr[:200]}"
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
                f"{result.stderr[:200]}"
            )
        else:
            logger.info(f"✅ Frontend accessibility check passed (port {frontend_port})")

    except subprocess.TimeoutExpired:
        failures.append(f"Frontend accessibility check timeout (port {frontend_port})")
    except Exception as e:
        failures.append(f"Frontend accessibility check error: {e}")

    # Test 3: Check if issue-specific endpoints work (if applicable)
    # This would require parsing the issue to understand what endpoints were added
    # For now, skip

    return failures


def create_followup_issue(
    original_issue: int,
    verification_result: VerificationResult,
    adw_id: str
) -> Optional[int]:
    """
    Create GitHub follow-up issue for verification failures.

    Args:
        original_issue: Original GitHub issue number
        verification_result: Verification results
        adw_id: ADW identifier

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
        ])

    if verification_result.frontend_errors:
        body_parts.extend([
            f"2. **Frontend Errors:** Review console errors and warnings",
            f"   - Check `logs/{adw_id}_frontend_build.log`",
            f"   - Fix console.error and React errors",
        ])

    if verification_result.smoke_test_failures:
        body_parts.extend([
            f"3. **Smoke Test Failures:** Critical paths are broken",
            f"   - Verify backend/frontend are accessible",
            f"   - Check network connectivity and ports",
        ])

    body_parts.extend([
        f"",
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
        # Create issue (this assumes github_helpers module exists)
        new_issue_number = create_github_issue(
            title=title,
            body=body,
            labels=["bug", "auto-verify", "post-deployment"]
        )

        logger.info(f"[Verify] Created follow-up issue #{new_issue_number}")

        # Add comment to original issue
        comment = (
            f"⚠️ **Post-Deployment Verification Failed**\n\n"
            f"Automated verification detected issues after deployment. "
            f"See follow-up issue #{new_issue_number} for details.\n\n"
            f"The shipped code has NOT been reverted. Issues will be addressed in a new PR."
        )
        add_comment_to_issue(original_issue, comment)

        return new_issue_number

    except Exception as e:
        logger.error(f"Failed to create follow-up issue: {e}")
        return None


def run_verify_phase(issue_number: int) -> int:
    """
    Run verification phase for ADW workflow.

    Args:
        issue_number: GitHub issue number

    Returns:
        Exit code (0 = success, 1 = verification failed but issue created)
    """
    logger.info(f"[Verify] Starting verification for issue #{issue_number}")

    # Load ADW state
    try:
        state = load_adw_state(issue_number)
        adw_id = state.get('adw_id', f'adw-{issue_number}')
        backend_port = state.get('backend_port')
        frontend_port = state.get('frontend_port')
        ship_timestamp_str = state.get('ship_timestamp')

        if not backend_port or not frontend_port:
            logger.error("Backend or frontend port not found in state")
            return 1

        # Parse ship timestamp
        if ship_timestamp_str:
            ship_timestamp = datetime.fromisoformat(ship_timestamp_str)
        else:
            # Fallback: use current time - 10 minutes
            ship_timestamp = datetime.now() - timedelta(minutes=10)
            logger.warning("Ship timestamp not found in state, using fallback")

    except Exception as e:
        logger.error(f"Failed to load ADW state: {e}")
        return 1

    # Wait for verification delay (5 minutes after ship)
    time_since_ship = datetime.now() - ship_timestamp
    remaining_wait = VERIFICATION_DELAY_SECONDS - time_since_ship.total_seconds()

    if remaining_wait > 0:
        logger.info(
            f"[Verify] Waiting {remaining_wait:.0f}s before verification "
            f"(5-minute post-ship delay)"
        )
        time.sleep(remaining_wait)

    # Initialize verification result
    result = VerificationResult()

    # Check 1: Backend logs
    logger.info("[Verify] Step 1/3: Checking backend logs...")
    backend_errors = check_backend_logs(adw_id, backend_port, ship_timestamp)
    for error in backend_errors:
        result.add_backend_error(error)

    # Check 2: Frontend console
    logger.info("[Verify] Step 2/3: Checking frontend console...")
    frontend_errors = check_frontend_console(adw_id, frontend_port)
    for error in frontend_errors:
        result.add_frontend_error(error)

    # Check 3: Smoke tests
    logger.info("[Verify] Step 3/3: Running smoke tests...")
    smoke_failures = run_smoke_tests(adw_id, backend_port, frontend_port, issue_number)
    for failure in smoke_failures:
        result.add_smoke_test_failure(failure)

    # Summary
    logger.info("\n" + "="*80)
    logger.info(result.get_summary())
    logger.info("="*80 + "\n")

    # Create follow-up issue if verification failed
    if not result.passed:
        followup_issue = create_followup_issue(issue_number, result, adw_id)

        if followup_issue:
            logger.info(
                f"[Verify] Verification failed. Follow-up issue #{followup_issue} created."
            )
            return 1
        else:
            logger.error("[Verify] Verification failed but could not create follow-up issue")
            return 1

    logger.info("[Verify] ✅ Verification passed! Feature is working correctly.")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run Verify phase for ADW workflow'
    )
    parser.add_argument(
        'issue_number',
        type=int,
        help='GitHub issue number'
    )

    args = parser.parse_args()

    try:
        exit_code = run_verify_phase(args.issue_number)
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Verify phase failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### Step 3: Create Tests for Verify Phase (60 min)

Create new file: `adws/tests/test_verify_phase.py`

```python
#!/usr/bin/env python3
"""
Tests for Verify Phase

Run with:
    cd adws
    uv run pytest tests/test_verify_phase.py -v
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_verify_iso import (
    VerificationResult,
    check_backend_logs,
    check_frontend_console,
    run_smoke_tests,
    load_adw_state,
)


@pytest.fixture
def temp_logs_dir():
    """Create temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_agents_dir():
    """Create temporary directory for agent state files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_verification_result_passed():
    """Test VerificationResult when all checks pass."""
    result = VerificationResult()

    assert result.passed is True
    assert "✅ All verification checks passed" in result.get_summary()


def test_verification_result_backend_errors():
    """Test VerificationResult with backend errors."""
    result = VerificationResult()
    result.add_backend_error("Exception in API handler")
    result.add_backend_error("500 Internal Server Error")

    assert result.passed is False
    summary = result.get_summary()
    assert "❌ Verification failed" in summary
    assert "Backend Log Errors" in summary
    assert "Exception in API handler" in summary


def test_verification_result_frontend_errors():
    """Test VerificationResult with frontend errors."""
    result = VerificationResult()
    result.add_frontend_error("console.error: Failed to fetch")

    assert result.passed is False
    summary = result.get_summary()
    assert "Frontend Errors" in summary


def test_verification_result_smoke_test_failures():
    """Test VerificationResult with smoke test failures."""
    result = VerificationResult()
    result.add_smoke_test_failure("Backend health check failed")

    assert result.passed is False
    summary = result.get_summary()
    assert "Smoke Test Failures" in summary


def test_verification_result_warnings():
    """Test VerificationResult with warnings (doesn't affect pass/fail)."""
    result = VerificationResult()
    result.add_warning("Log file not found")

    assert result.passed is True  # Warnings don't fail verification
    summary = result.get_summary()
    assert "✅ All verification checks passed" in summary


def test_check_backend_logs_no_errors(temp_logs_dir):
    """Test backend log checking with clean logs."""
    # Create log file with no errors
    log_file = temp_logs_dir / "adw-123_backend.log"
    log_file.write_text(
        "INFO: Server started\n"
        "INFO: Request processed successfully\n"
        "INFO: Response sent\n"
    )

    with patch('adw_verify_iso.Path') as mock_path:
        mock_path.return_value = log_file

        errors = check_backend_logs(
            adw_id="adw-123",
            backend_port=9100,
            ship_timestamp=datetime.now()
        )

    # Should find no errors
    assert len(errors) == 0 or all("Warning" in e for e in errors)


def test_check_backend_logs_with_errors(temp_logs_dir):
    """Test backend log checking with errors."""
    # Create log file with errors
    log_file = temp_logs_dir / "adw-123_backend.log"
    log_file.write_text(
        "INFO: Server started\n"
        "ERROR: Exception in request handler\n"
        "Traceback (most recent call last):\n"
        "  File 'handler.py', line 42, in process\n"
        "500 Internal Server Error\n"
    )

    with patch('adw_verify_iso.Path') as mock_path:
        mock_path.return_value = log_file

        errors = check_backend_logs(
            adw_id="adw-123",
            backend_port=9100,
            ship_timestamp=datetime.now()
        )

    # Should find errors
    assert len(errors) > 0
    assert any("ERROR" in e or "Exception" in e for e in errors)


def test_check_frontend_console_no_errors(temp_logs_dir):
    """Test frontend console checking with clean logs."""
    # Create build log with no errors
    log_file = temp_logs_dir / "adw-123_frontend_build.log"
    log_file.write_text(
        "Building for production\n"
        "Build completed successfully\n"
        "Chunks: vendor.js, app.js\n"
    )

    with patch('adw_verify_iso.Path') as mock_path:
        mock_path.return_value = log_file

        errors = check_frontend_console(
            adw_id="adw-123",
            frontend_port=9200
        )

    assert len(errors) == 0 or all("Warning" in e for e in errors)


def test_check_frontend_console_with_errors(temp_logs_dir):
    """Test frontend console checking with errors."""
    # Create build log with errors
    log_file = temp_logs_dir / "adw-123_frontend_build.log"
    log_file.write_text(
        "Building for production\n"
        "console.error: Failed to fetch API\n"
        "Uncaught TypeError: Cannot read property 'map' of undefined\n"
        "React Error: Component failed to render\n"
    )

    with patch('adw_verify_iso.Path') as mock_path:
        mock_path.return_value = log_file

        errors = check_frontend_console(
            adw_id="adw-123",
            frontend_port=9200
        )

    # Should find errors
    assert len(errors) > 0
    assert any("console.error" in e or "TypeError" in e for e in errors)


@patch('adw_verify_iso.subprocess.run')
def test_run_smoke_tests_all_pass(mock_run):
    """Test smoke tests when all pass."""
    # Mock successful curl commands
    mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="OK")

    failures = run_smoke_tests(
        adw_id="adw-123",
        backend_port=9100,
        frontend_port=9200,
        issue_number=123
    )

    assert len(failures) == 0


@patch('adw_verify_iso.subprocess.run')
def test_run_smoke_tests_backend_fails(mock_run):
    """Test smoke tests when backend health check fails."""
    # First call (backend) fails, second (frontend) succeeds
    mock_run.side_effect = [
        MagicMock(returncode=1, stderr="Connection refused", stdout=""),
        MagicMock(returncode=0, stderr="", stdout="OK"),
    ]

    failures = run_smoke_tests(
        adw_id="adw-123",
        backend_port=9100,
        frontend_port=9200,
        issue_number=123
    )

    assert len(failures) > 0
    assert any("Backend health check failed" in f for f in failures)


@patch('adw_verify_iso.subprocess.run')
def test_run_smoke_tests_timeout(mock_run):
    """Test smoke tests with timeout."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired(cmd='curl', timeout=10)

    failures = run_smoke_tests(
        adw_id="adw-123",
        backend_port=9100,
        frontend_port=9200,
        issue_number=123
    )

    assert len(failures) > 0
    assert any("timeout" in f.lower() for f in failures)


def test_load_adw_state(temp_agents_dir):
    """Test loading ADW state file."""
    # Create state file
    state_data = {
        "adw_id": "adw-123",
        "backend_port": 9100,
        "frontend_port": 9200,
        "ship_timestamp": datetime.now().isoformat()
    }

    adw_dir = temp_agents_dir / "adw-123"
    adw_dir.mkdir(parents=True, exist_ok=True)
    state_file = adw_dir / "state.json"

    with open(state_file, 'w') as f:
        json.dump(state_data, f)

    # Mock Path to use temp directory
    with patch('adw_verify_iso.Path') as mock_path:
        mock_path.return_value = state_file

        loaded_state = load_adw_state(123)

    assert loaded_state["adw_id"] == "adw-123"
    assert loaded_state["backend_port"] == 9100
    assert loaded_state["frontend_port"] == 9200


def test_load_adw_state_not_found():
    """Test loading ADW state when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_adw_state(999)
```

### Step 4: Integrate with Full SDLC Workflow (30 min)

**Modify `adws/adw_sdlc_complete_iso.py`:**

Find the workflow orchestration section and add Verify phase:

```python
# Add import at top
from adw_verify_iso import run_verify_phase

# ... in main workflow function ...

def run_full_sdlc(issue_number, nl_input, ...):
    # ... existing phases ...

    # Phase 9: Cleanup
    logger.info("[SDLC] Phase 9/10: Cleanup")
    cleanup_result = run_cleanup_phase(issue_number)
    if cleanup_result != 0:
        logger.error("[SDLC] Cleanup phase failed")
        return 1

    # Phase 10: Verify
    logger.info("[SDLC] Phase 10/10: Verify")
    verify_result = run_verify_phase(issue_number)
    if verify_result != 0:
        logger.warning(
            "[SDLC] Verify phase detected issues. "
            "Follow-up issue created. See logs for details."
        )
        # Note: Don't fail workflow on verify failures
        # Issues are tracked via GitHub, code is already shipped

    logger.info("[SDLC] ✅ Full 10-phase SDLC workflow complete!")
    return 0
```

**Find integration point:**

```bash
# Search for where phases are called
grep -n "cleanup\|Phase 9" adw_sdlc_complete_iso.py

# Look for phase orchestration pattern
grep -A 5 "Phase [0-9]" adw_sdlc_complete_iso.py
```

### Step 5: Run Tests (15 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Run verify phase tests
uv run pytest tests/test_verify_phase.py -v

# Expected output:
# test_verification_result_passed PASSED
# test_verification_result_backend_errors PASSED
# test_verification_result_frontend_errors PASSED
# test_verification_result_smoke_test_failures PASSED
# test_verification_result_warnings PASSED
# test_check_backend_logs_no_errors PASSED
# test_check_backend_logs_with_errors PASSED
# test_check_frontend_console_no_errors PASSED
# test_check_frontend_console_with_errors PASSED
# test_run_smoke_tests_all_pass PASSED
# test_run_smoke_tests_backend_fails PASSED
# test_run_smoke_tests_timeout PASSED
# test_load_adw_state PASSED
# test_load_adw_state_not_found PASSED
# ================== 14 passed ==================
```

If tests fail:
- Check import paths
- Verify mock configurations
- Review Path patching (temp directories)
- Check subprocess mocking

### Step 6: Manual Integration Test (30 min)

Test verify phase with manual invocation:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws

# Test 1: Verify with mock state file
mkdir -p ../agents/adw-test-verify
cat > ../agents/adw-test-verify/state.json <<EOF
{
  "adw_id": "adw-test-verify",
  "backend_port": 9100,
  "frontend_port": 9200,
  "ship_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S)"
}
EOF

# Create mock log files
mkdir -p ../logs
echo "INFO: Server started" > ../logs/adw-test-verify_backend.log
echo "Build completed" > ../logs/adw-test-verify_frontend_build.log

# Run verify phase
uv run python adw_verify_iso.py 999  # Use test issue number

# Should complete without errors (logs are clean)

# Test 2: Verify with errors in logs
echo "ERROR: Exception occurred" >> ../logs/adw-test-verify_backend.log

# Run again
uv run python adw_verify_iso.py 999

# Should detect backend error

# Clean up
rm -rf ../agents/adw-test-verify
rm ../logs/adw-test-verify_*
```

### Step 7: Update Documentation (20 min)

**Update `adws/README.md`:**

Add Verify phase documentation:

```markdown
## ADW Workflow Phases

The ADW workflow consists of **10 phases** for complete SDLC automation:

1. **Plan** - Generate implementation plan
2. **Validate** - Validate plan feasibility
3. **Build** - Build backend and frontend
4. **Lint** - Code quality checks
5. **Test** - Run unit and integration tests
6. **Review** - AI-assisted code review
7. **Document** - Generate documentation
8. **Ship** - Create PR and merge
9. **Cleanup** - Clean up worktree and resources
10. **Verify** - Post-deployment verification ✨ NEW

### Phase 10: Verify

The Verify phase runs after Ship and Cleanup to ensure deployed features are working correctly.

**Purpose:** Catch post-deployment issues immediately instead of hours/days later

**Timing:** Runs 5 minutes after Ship phase completes

**Checks Performed:**

1. **Backend Log Analysis**
   - Scans backend logs for exceptions, errors, stack traces
   - Checks 10-minute window from ship time
   - Pattern matching: `Exception`, `ERROR`, `500`, `Failed to`

2. **Frontend Console Errors**
   - Analyzes frontend build logs
   - Detects: `console.error`, `console.warn`, `Uncaught`, React errors
   - Identifies JavaScript exceptions

3. **Smoke Tests**
   - Backend health check (`/health` endpoint)
   - Frontend accessibility (main page load)
   - Critical path verification

**Error Handling:**

- ❌ **Verification Fails:** Auto-create GitHub follow-up issue
- ✅ **Verification Passes:** Complete workflow successfully
- ⚠️ **Important:** Shipped code is NEVER reverted (create new PR instead)

**Example Verification Report:**

```
✅ All verification checks passed

OR

❌ Verification failed with the following issues:

Backend Log Errors (2):
- Backend log error: ERROR: Exception in /api/users handler
- Backend log error: 500 Internal Server Error

Smoke Test Failures (1):
- Backend health check failed (port 9100): Connection refused

Follow-up issue #124 created automatically.
```

**Manual Verification:**

```bash
# Run verify phase manually
cd adws
uv run python adw_verify_iso.py <issue_number>

# Check verification status
echo $?  # 0 = passed, 1 = failed
```

**Configuration:**

- Verification delay: 5 minutes (300 seconds)
- Log check window: 10 minutes
- Smoke test timeout: 10 seconds per test

**Architecture Decision:**

- **Why Phase 10?** Separate phase allows verification without blocking Ship
- **Why not revert?** Code has passed Review and Test phases - issues are likely environmental
- **Why auto-issue?** Reduces time to detect problems from hours to minutes
```

---

## Success Criteria

- ✅ adw_verify_iso.py created with log checking, smoke tests, issue creation
- ✅ VerificationResult class tracks errors, warnings, and pass/fail status
- ✅ Backend log checking with pattern matching
- ✅ Frontend console error detection
- ✅ Smoke tests for backend/frontend health
- ✅ Auto-create GitHub follow-up issue on failures
- ✅ All 14 tests passing
- ✅ Integration with adw_sdlc_complete_iso.py complete (10th phase)
- ✅ Documentation updated with Verify phase details
- ✅ Manual test confirms verify phase runs correctly

---

## Files Expected to Change

**Created (2):**
- `adws/adw_verify_iso.py` (~400-500 lines)
- `adws/tests/test_verify_phase.py` (~200 lines)

**Modified (2):**
- `adws/adw_sdlc_complete_iso.py` (add Verify phase to workflow chain, ~15 lines)
- `adws/README.md` (add Verify phase documentation)

---

## Troubleshooting

### Import Errors

```bash
# If "ModuleNotFoundError: No module named 'adw_modules'"
cd adws
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run pytest tests/test_verify_phase.py -v
```

### GitHub Helpers Not Found

If `github_helpers` module doesn't exist:
- Check existing ADW files for GitHub integration patterns
- Implement create_github_issue, add_comment_to_issue functions
- Or use subprocess to call `gh` CLI

### State File Not Found

```bash
# Check state file location
find . -name "state.json" | grep agents

# Verify state file structure
cat agents/adw-<issue>/state.json | jq .
```

### Smoke Tests Always Fail

This usually indicates:
- Backend/frontend not running on expected ports
- Ports not accessible from verify phase
- Check if worktree processes are still running
- Verify port allocation is correct

### Log Files Not Found

If log files don't exist:
- Check logging configuration in backend/frontend
- Verify log directory path (`../logs/`)
- Create logs directory if missing: `mkdir -p logs`

### Time Window Issues

If log checking misses errors:
- Increase LOG_CHECK_WINDOW_MINUTES (default: 10)
- Verify ship_timestamp is correctly recorded
- Check datetime parsing logic

---

## Estimated Time

- Step 1 (Understand workflow): 20 min
- Step 2 (Create verify module): 90-120 min
- Step 3 (Create tests): 60 min
- Step 4 (Integration): 30 min
- Step 5 (Run tests): 15 min
- Step 6 (Manual test): 30 min
- Step 7 (Documentation): 20 min

**Total: 4-5 hours**

---

## Session Completion Instructions

When you finish this session, provide a completion summary in this **EXACT FORMAT:**

```markdown
## ✅ Session 5 Complete - Verify Phase Implementation

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 6 (Pattern Review System)

### What Was Done

1. **Verify Phase Module Created**
   - Created adws/adw_verify_iso.py (~400-500 lines)
   - VerificationResult class for tracking check results
   - Backend log checking with pattern matching
   - Frontend console error detection
   - Smoke tests (backend health, frontend accessibility)
   - Auto-create GitHub follow-up issues on failures

2. **Comprehensive Tests**
   - Created tests/test_verify_phase.py (14 tests)
   - All tests passing ✅
   - Coverage: verification result, log checking, smoke tests, state loading

3. **SDLC Integration**
   - Modified adw_sdlc_complete_iso.py to add Phase 10
   - Verify runs after Cleanup phase
   - Non-blocking: Issues created but workflow doesn't fail

4. **Documentation Updated**
   - Added Verify phase section to adws/README.md
   - Documented checks, error handling, configuration
   - Included examples and manual verification instructions

### Key Results

- ✅ 10th ADW phase implemented (Verify)
- ✅ Post-deployment verification in 5-minute window
- ✅ Backend log analysis with error pattern matching
- ✅ Frontend console error detection
- ✅ Smoke tests for critical paths
- ✅ Auto-create follow-up GitHub issues on failures
- ✅ Shipped code never reverted (new PR created instead)
- ✅ Complete workflow: Plan → ... → Ship → Cleanup → Verify

### Files Changed

**Created (2):**
- adws/adw_verify_iso.py
- adws/tests/test_verify_phase.py

**Modified (2):**
- adws/adw_sdlc_complete_iso.py
- adws/README.md

### Test Results

```
uv run pytest tests/test_verify_phase.py -v
================== 14 passed ==================
```

### Example Verification Output

Clean deployment:
```
✅ All verification checks passed
Feature is working correctly.
```

Failed verification:
```
❌ Verification failed with the following issues:
Backend Log Errors (2):
- ERROR: Exception in API handler
- 500 Internal Server Error

Follow-up issue #124 created.
```

### Next Session

Session 6: Pattern Review System (3-4 hours)
- Manual approval system for detected patterns
- CLI tool for reviewing patterns before automation
- GitHub integration for pattern approval workflow
```

---

## Next Session Prompt Instructions

After providing the completion summary above, create the prompt for **Session 6: Pattern Review System** using this template:

### Template for SESSION_6_PROMPT.md

```markdown
# Task: Implement Pattern Review System

## Context
I'm working on the tac-webbuilder project. The pattern detection system (completed in Session 1.5) identifies automation patterns from hook events. Before automatically generating workflows from these patterns, we need a manual review system to ensure pattern quality and prevent automation of incorrect patterns. This session implements a CLI-based pattern review tool.

## Objective
Create a pattern review system that:
- Displays detected patterns with context and statistics
- Allows manual approval/rejection via CLI
- Stores approval decisions in database
- Integrates with GitHub for collaboration
- Provides filtering and search capabilities

## Background Information
- **Pattern Detection:** Already implemented (Session 1.5)
- **Current Gap:** No review mechanism before automation
- **Safety Layer:** Manual approval prevents bad automation
- **Threshold:** 95% confidence + 100+ occurrences before automation eligible

[... continue with full session structure ...]
```

**Save this prompt as:** `/Users/Warmonger0/tac/tac-webbuilder/SESSION_6_PROMPT.md`

---

**Ready to copy into a new chat!**

Run `/prime` first, then paste this entire prompt.
