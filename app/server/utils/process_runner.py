"""
Standardized subprocess execution with consistent error handling.

Eliminates duplication of:
- subprocess.run() patterns
- Timeout handling
- Error message formatting
- Output capture
- Common command wrappers (gh, git, bash)

This utility consolidates ~120 lines of duplicated subprocess code across
service_controller.py, health_service.py, github_poster.py, and workflow_history.py.
"""

import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of process execution with consistent structure."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    command: str


class ProcessRunner:
    """
    Wrapper for subprocess execution with consistent error handling.

    All methods return ProcessResult with:
    - success: True if returncode == 0
    - stdout: Standard output (empty string if not captured)
    - stderr: Standard error (empty string if not captured)
    - returncode: Process exit code (-1 for timeout)
    - command: Command string for logging/debugging
    """

    @staticmethod
    def run(
        command: list[str],
        timeout: float | None = 30,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        cwd: str | None = None,
        log_command: bool = False
    ) -> ProcessResult:
        """
        Execute command with consistent timeout and error handling.

        Args:
            command: Command and arguments as list
            timeout: Timeout in seconds (None for no timeout)
            check: Raise CalledProcessError on non-zero return code
            capture_output: Capture stdout/stderr
            text: Decode output as text
            cwd: Working directory for command execution
            log_command: Log command execution for debugging

        Returns:
            ProcessResult with command output and status

        Example:
            >>> result = ProcessRunner.run(["echo", "hello"])
            >>> print(result.stdout)
            hello
            >>> print(result.success)
            True
        """
        cmd_str = " ".join(command)

        if log_command:
            logger.debug(f"Executing: {cmd_str}")

        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=check,
                cwd=cwd,
                env=os.environ.copy()
            )
            return ProcessResult(
                success=result.returncode == 0,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                returncode=result.returncode,
                command=cmd_str
            )
        except subprocess.TimeoutExpired as e:
            # Handle timeout - stdout/stderr may be None or bytes
            stdout_str = ""
            stderr_str = f"Command timed out after {timeout}s"

            if e.stdout:
                stdout_str = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
            if e.stderr:
                stderr_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
                stderr_str = f"{stderr_str}\n{stderr_msg}"

            if log_command:
                logger.warning(f"Command timed out: {cmd_str}")

            return ProcessResult(
                success=False,
                stdout=stdout_str,
                stderr=stderr_str,
                returncode=-1,
                command=cmd_str
            )
        except subprocess.CalledProcessError as e:
            # Handle non-zero exit code when check=True
            stdout_str = e.stdout if hasattr(e, 'stdout') and e.stdout else ""
            stderr_str = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)

            if log_command:
                logger.error(f"Command failed with code {e.returncode}: {cmd_str}")

            return ProcessResult(
                success=False,
                stdout=stdout_str,
                stderr=stderr_str,
                returncode=e.returncode,
                command=cmd_str
            )

    @staticmethod
    def run_gh_command(args: list[str], timeout: float = 5) -> ProcessResult:
        """
        Run GitHub CLI command with consistent timeout.

        Args:
            args: GitHub CLI arguments (without 'gh' prefix)
            timeout: Timeout in seconds (default: 5s for gh commands)

        Returns:
            ProcessResult with gh command output

        Example:
            >>> result = ProcessRunner.run_gh_command(["issue", "view", "123"])
            >>> if result.success:
            ...     print(result.stdout)
        """
        return ProcessRunner.run(["gh"] + args, timeout=timeout)

    @staticmethod
    def run_git_command(
        args: list[str],
        cwd: str | None = None,
        timeout: float = 10
    ) -> ProcessResult:
        """
        Run git command with optional working directory.

        Args:
            args: Git arguments (without 'git' prefix)
            cwd: Working directory for git command
            timeout: Timeout in seconds (default: 10s for git commands)

        Returns:
            ProcessResult with git command output

        Example:
            >>> result = ProcessRunner.run_git_command(
            ...     ["status", "--short"],
            ...     cwd="/path/to/repo"
            ... )
        """
        return ProcessRunner.run(["git"] + args, timeout=timeout, cwd=cwd)

    @staticmethod
    def run_shell(
        shell_command: str,
        timeout: float | None = 30,
        cwd: str | None = None
    ) -> ProcessResult:
        """
        Run shell command via bash -c for complex commands with pipes/expansion.

        Use this for commands that need shell features like:
        - Pipes: "ps aux | grep cloudflared"
        - Variable expansion: "cd $DIR && python script.py"
        - Command substitution: "echo $(date)"

        Args:
            shell_command: Shell command as string
            timeout: Timeout in seconds
            cwd: Working directory

        Returns:
            ProcessResult with shell command output

        Example:
            >>> result = ProcessRunner.run_shell(
            ...     "cd /tmp && ls -la | grep test",
            ...     timeout=5
            ... )
        """
        return ProcessRunner.run(
            ["bash", "-c", shell_command],
            timeout=timeout,
            cwd=cwd
        )
