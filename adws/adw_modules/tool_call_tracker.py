"""
ToolCallTracker - Helper for tracking tool usage in ADW workflows

Context manager that auto-captures tool execution metadata and logs to observability system.

Usage:
    with ToolCallTracker(adw_id="adw-123", issue_number=42, phase_name="Build") as tracker:
        tracker.track("npm_install", lambda: subprocess.run(["npm", "install"]))
        tracker.track("npm_build", lambda: subprocess.run(["npm", "run", "build"]))
    # Auto-calls log_task_completion() with tool_calls=[...] on context exit

Features:
- Automatic timing and duration calculation
- Success/failure detection
- Error message capture
- Parameter and result logging
- Zero-overhead on observability failures
"""

import logging
import subprocess
from datetime import datetime
from typing import Callable, Any, Optional
from contextlib import contextmanager

from adw_modules.observability import log_task_completion

logger = logging.getLogger(__name__)


class ToolCallTracker:
    """
    Context manager for tracking tool calls within ADW phases.

    Auto-captures:
    - Tool name
    - Start/end timestamps
    - Duration in milliseconds
    - Success/failure status
    - Error messages
    - Optional parameters and results

    Automatically logs to observability system on context exit.
    """

    def __init__(
        self,
        adw_id: str,
        issue_number: int,
        phase_name: str,
        phase_number: Optional[int] = None,
        workflow_template: Optional[str] = None,
    ):
        """
        Initialize tracker for a specific ADW phase.

        Args:
            adw_id: ADW workflow ID (e.g., "adw-123")
            issue_number: GitHub issue number
            phase_name: Phase name (e.g., "Build", "Test")
            phase_number: Optional phase number (1-10)
            workflow_template: Optional workflow template name
        """
        self.adw_id = adw_id
        self.issue_number = issue_number
        self.phase_name = phase_name
        self.phase_number = phase_number or self._infer_phase_number(phase_name)
        self.workflow_template = workflow_template
        self.tool_calls: list[dict] = []
        self._phase_start_time = datetime.now()

    def _infer_phase_number(self, phase_name: str) -> int:
        """Infer phase number from phase name."""
        phase_map = {
            "Plan": 1,
            "Validate": 2,
            "Build": 3,
            "Lint": 4,
            "Test": 5,
            "Review": 6,
            "Document": 7,
            "Ship": 8,
            "Cleanup": 9,
            "Verify": 10,
        }
        return phase_map.get(phase_name, 0)

    def track(
        self,
        tool_name: str,
        callable_fn: Callable[[], Any],
        parameters: Optional[dict] = None,
        capture_result: bool = False,
    ) -> Any:
        """
        Track execution of a tool/command.

        Args:
            tool_name: Name of the tool (e.g., "npm_install", "pytest", "git_commit")
            callable_fn: Function to execute (e.g., lambda: subprocess.run(...))
            parameters: Optional dict of parameters to log
            capture_result: If True, capture result in result_summary

        Returns:
            Result of callable_fn()

        Example:
            result = tracker.track(
                "pytest",
                lambda: subprocess.run(["pytest", "tests/"], capture_output=True),
                parameters={"test_path": "tests/"},
                capture_result=True
            )
        """
        started_at = datetime.now()
        success = True
        error_message = None
        result = None
        result_summary = None

        try:
            logger.debug(f"Tracking tool: {tool_name}")
            result = callable_fn()

            # Capture result summary if requested
            if capture_result:
                if isinstance(result, subprocess.CompletedProcess):
                    result_summary = f"returncode={result.returncode}"
                    if result.returncode != 0:
                        success = False
                        error_message = f"Non-zero exit code: {result.returncode}"
                        if result.stderr:
                            stderr_str = result.stderr.decode() if isinstance(result.stderr, bytes) else str(result.stderr)
                            error_message += f"\nStderr: {stderr_str[:500]}"  # Truncate to 500 chars
                else:
                    result_summary = str(result)[:200]  # Truncate to 200 chars

        except subprocess.CalledProcessError as e:
            success = False
            error_message = f"CalledProcessError: {e.returncode}"
            if e.stderr:
                stderr_str = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                error_message += f"\nStderr: {stderr_str[:500]}"
            logger.warning(f"Tool {tool_name} failed with CalledProcessError: {e}")

        except Exception as e:
            success = False
            error_message = f"{type(e).__name__}: {str(e)[:500]}"
            logger.warning(f"Tool {tool_name} failed with exception: {e}")

        finally:
            completed_at = datetime.now()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Record the tool call
            tool_call_record = {
                "tool_name": tool_name,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "duration_ms": duration_ms,
                "success": success,
                "error_message": error_message,
                "parameters": parameters or {},
                "result_summary": result_summary,
            }

            self.tool_calls.append(tool_call_record)

            logger.debug(
                f"Tool {tool_name}: {'✓' if success else '✗'} "
                f"({duration_ms}ms)"
            )

        return result

    def track_bash(
        self,
        tool_name: str,
        command: list[str] | str,
        cwd: Optional[str] = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Convenience method for tracking bash/subprocess commands.

        Args:
            tool_name: Name of the tool (e.g., "npm_install", "pytest")
            command: Command as list or string
            cwd: Working directory
            capture_output: Whether to capture stdout/stderr

        Returns:
            subprocess.CompletedProcess result

        Example:
            result = tracker.track_bash("npm_install", ["npm", "install"], cwd="/path/to/repo")
        """
        cmd_list = command if isinstance(command, list) else command.split()
        parameters = {
            "command": " ".join(cmd_list),
            "cwd": cwd or ".",
        }

        return self.track(
            tool_name=tool_name,
            callable_fn=lambda: subprocess.run(
                cmd_list,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=False,  # Don't raise on non-zero exit
            ),
            parameters=parameters,
            capture_result=True,
        )

    def get_summary(self) -> dict:
        """
        Get summary of all tracked tool calls.

        Returns:
            Dict with summary stats
        """
        total_calls = len(self.tool_calls)
        successful_calls = sum(1 for tc in self.tool_calls if tc["success"])
        failed_calls = total_calls - successful_calls
        total_duration_ms = sum(tc["duration_ms"] for tc in self.tool_calls)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "total_duration_ms": total_duration_ms,
            "tools_used": list({tc["tool_name"] for tc in self.tool_calls}),
        }

    def __enter__(self):
        """Enter context manager."""
        logger.debug(
            f"Starting tool tracking for {self.phase_name} "
            f"(ADW: {self.adw_id}, Issue: #{self.issue_number})"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - auto-log tool calls to observability system.

        Logs tool_calls to backend via log_task_completion().
        Failures in logging are non-blocking (zero-overhead guarantee).
        """
        phase_end_time = datetime.now()
        duration_seconds = (phase_end_time - self._phase_start_time).total_seconds()

        summary = self.get_summary()
        logger.debug(
            f"Tool tracking complete for {self.phase_name}: "
            f"{summary['total_calls']} calls, "
            f"{summary['successful_calls']} successful, "
            f"{summary['failed_calls']} failed, "
            f"{summary['total_duration_ms']}ms total"
        )

        # Determine phase status based on tool call results
        if exc_type is not None:
            phase_status = "failed"
            error_message = f"{exc_type.__name__}: {str(exc_val)[:500]}"
        elif summary["failed_calls"] > 0:
            phase_status = "completed"  # Completed with some failures
            error_message = None  # Individual tool errors are in tool_calls
        else:
            phase_status = "completed"
            error_message = None

        # Log to observability system
        try:
            log_task_completion(
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                phase_name=self.phase_name,
                phase_number=self.phase_number,
                phase_status=phase_status,
                log_message=f"{self.phase_name} phase tracked {summary['total_calls']} tool calls",
                workflow_template=self.workflow_template,
                error_message=error_message,
                started_at=self._phase_start_time,
                completed_at=phase_end_time,
                duration_seconds=duration_seconds,
                tool_calls=self.tool_calls,  # Pass tool calls to observability
            )
            logger.debug(f"Tool calls logged to observability system for {self.phase_name}")

        except Exception as e:
            # Zero-overhead guarantee - logging failures don't block workflow
            logger.warning(
                f"Failed to log tool calls to observability system: {e}. "
                f"Workflow continues normally."
            )

        # Don't suppress exceptions from the with block
        return False
