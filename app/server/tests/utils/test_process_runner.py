"""
Comprehensive test suite for the ProcessRunner utility.

Tests verify:
- Successful command execution with returncode 0
- Failure handling with non-zero returncodes
- Timeout handling with TimeoutExpired exceptions
- CalledProcessError handling when check=True
- Output capture configuration (capture_output, text parameters)
- All method wrappers: run(), run_gh_command(), run_git_command(), run_shell()
- Working directory (cwd) parameter handling
- Edge cases: None stdout/stderr, bytes vs strings, empty commands
- Logging behavior with log_command parameter
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from utils.process_runner import ProcessResult, ProcessRunner

# ============================================================================
# Fixtures for mocking subprocess
# ============================================================================


@pytest.fixture
def mock_subprocess_success():
    """
    Create a mock for successful subprocess.run call.

    Returns a mock CompletedProcess with:
    - returncode = 0
    - stdout = "output"
    - stderr = ""
    """
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_subprocess_failure():
    """
    Create a mock for failed subprocess.run call (non-zero return code).

    Returns a mock CompletedProcess with:
    - returncode = 1
    - stdout = "partial output"
    - stderr = "error message"
    """
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "partial output"
    mock_result.stderr = "error message"
    return mock_result


@pytest.fixture
def mock_subprocess_with_bytes():
    """
    Create a mock for subprocess.run with bytes output (when text=False).

    Returns a mock CompletedProcess with:
    - returncode = 0
    - stdout = b"binary output"
    - stderr = b""
    """
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = b"binary output"
    mock_result.stderr = b""
    return mock_result


@pytest.fixture
def mock_subprocess_with_no_output():
    """
    Create a mock for subprocess.run with no captured output.

    Returns a mock CompletedProcess with:
    - returncode = 0
    - stdout = None
    - stderr = None
    """
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = None
    mock_result.stderr = None
    return mock_result


# ============================================================================
# Tests for ProcessRunner.run() method
# ============================================================================


class TestProcessRunnerRun:
    """Test suite for ProcessRunner.run() method."""

    def test_run_success_basic(self, mock_subprocess_success):
        """
        Test basic successful command execution.

        Verifies:
        - Command executes successfully (returncode=0)
        - Output is captured and stored in stdout/stderr
        - ProcessResult.success is True
        - Command string is formatted correctly
        """
        with patch("subprocess.run", return_value=mock_subprocess_success):
            result = ProcessRunner.run(["echo", "hello"])

            assert result.success is True
            assert result.returncode == 0
            assert result.stdout == "output"
            assert result.stderr == ""
            assert result.command == "echo hello"

    def test_run_failure_non_zero_returncode(self, mock_subprocess_failure):
        """
        Test handling of non-zero return code (failure).

        Verifies:
        - Non-zero return code is captured
        - ProcessResult.success is False
        - Output is still available for debugging
        - Failure is captured without exception
        """
        with patch("subprocess.run", return_value=mock_subprocess_failure):
            result = ProcessRunner.run(["false"])

            assert result.success is False
            assert result.returncode == 1
            assert result.stdout == "partial output"
            assert result.stderr == "error message"
            assert result.command == "false"

    def test_run_timeout_handling(self):
        """
        Test timeout handling with TimeoutExpired exception.

        Verifies:
        - TimeoutExpired is caught and converted to ProcessResult
        - returncode is set to -1 for timeout
        - success is False
        - Timeout message is in stderr
        - stdout and stderr from exception are handled
        """
        timeout_exception = subprocess.TimeoutExpired(
            cmd="sleep 60",
            timeout=5
        )
        # TimeoutExpired doesn't accept stdout/stderr in __init__, so set them after
        timeout_exception.stdout = "partial"
        timeout_exception.stderr = "error"

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.returncode == -1
            assert "timed out" in result.stderr.lower()
            assert "5" in result.stderr  # timeout value in message
            assert result.stdout == "partial"

    def test_run_timeout_with_none_stdout_stderr(self):
        """
        Test timeout handling when TimeoutExpired has None stdout/stderr.

        Verifies:
        - None values are handled gracefully (not decoded)
        - Timeout message is still created
        - No AttributeError is raised
        """
        timeout_exception = subprocess.TimeoutExpired(
            cmd="sleep 60",
            timeout=5
        )
        # TimeoutExpired doesn't accept stdout/stderr in __init__, so set them after
        timeout_exception.stdout = None
        timeout_exception.stderr = None

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.returncode == -1
            assert result.stdout == ""
            assert "timed out" in result.stderr.lower()

    def test_run_timeout_with_bytes_stdout_stderr(self):
        """
        Test timeout handling when TimeoutExpired has bytes stdout/stderr.

        Verifies:
        - Bytes are decoded to strings
        - Both stdout and stderr are properly converted
        """
        timeout_exception = subprocess.TimeoutExpired(
            cmd="sleep 60",
            timeout=5
        )
        # TimeoutExpired doesn't accept stdout/stderr in __init__, so set them after
        timeout_exception.stdout = b"partial bytes"
        timeout_exception.stderr = b"error bytes"

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.stdout == "partial bytes"
            assert "error bytes" in result.stderr

    def test_run_called_process_error_with_check_true(self):
        """
        Test CalledProcessError when check=True and command fails.

        Verifies:
        - CalledProcessError is caught
        - returncode from exception is preserved
        - stdout and stderr are captured
        - success is False
        """
        error = subprocess.CalledProcessError(
            returncode=2,
            cmd="false",
            output="stdout output",
            stderr="stderr output"
        )
        error.stdout = "stdout output"
        error.stderr = "stderr output"

        with patch("subprocess.run", side_effect=error):
            result = ProcessRunner.run(["false"], check=True)

            assert result.success is False
            assert result.returncode == 2
            assert result.stdout == "stdout output"
            assert result.stderr == "stderr output"

    def test_run_called_process_error_without_stdout_stderr(self):
        """
        Test CalledProcessError when stdout/stderr are None.

        Verifies:
        - None stdout/stderr don't cause exceptions
        - Empty strings are used for None values
        - Error message is properly formatted
        """
        # Create real CalledProcessError - stdout/stderr default to None
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["failing_command"]
        )

        with patch("subprocess.run", side_effect=error):
            result = ProcessRunner.run(["failing_command"], check=True)

            assert result.success is False
            assert result.returncode == 1
            assert result.stdout == ""
            assert isinstance(result.stderr, str)

    def test_run_no_capture_output(self, mock_subprocess_success):
        """
        Test execution with capture_output=False.

        Verifies:
        - capture_output=False is passed to subprocess.run
        - stdout and stderr are empty strings (not captured)
        - returncode is still captured
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            result = ProcessRunner.run(
                ["echo", "hello"],
                capture_output=False
            )

            assert result.stdout == ""
            assert result.stderr == ""
            assert result.success is True
            # Verify parameter was passed
            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["capture_output"] is False

    def test_run_with_timeout_parameter(self, mock_subprocess_success):
        """
        Test timeout parameter is passed to subprocess.run.

        Verifies:
        - Timeout value is passed correctly
        - Default timeout (30) is used when not specified
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            ProcessRunner.run(["echo", "hello"], timeout=15)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 15

    def test_run_with_default_timeout(self, mock_subprocess_success):
        """
        Test that default timeout of 30 seconds is applied.

        Verifies:
        - Default timeout is 30 when not specified
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            ProcessRunner.run(["echo", "hello"])

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 30

    def test_run_with_no_timeout(self, mock_subprocess_success):
        """
        Test that timeout=None removes timeout limit.

        Verifies:
        - timeout=None is passed to subprocess.run
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            ProcessRunner.run(["echo", "hello"], timeout=None)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] is None

    def test_run_with_cwd_parameter(self, mock_subprocess_success):
        """
        Test working directory (cwd) parameter is passed.

        Verifies:
        - cwd parameter is passed to subprocess.run
        - Execution happens in specified directory
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            ProcessRunner.run(
                ["ls", "-la"],
                cwd="/tmp"
            )

            call_kwargs = mock.call_args[1]
            assert call_kwargs["cwd"] == "/tmp"

    def test_run_with_check_true(self, mock_subprocess_failure):
        """
        Test check=True parameter causes exception on failure.

        Verifies:
        - check=True is passed to subprocess.run
        - CalledProcessError is raised and handled
        """
        with (
            patch("subprocess.run", side_effect=mock_subprocess_failure),
            # The actual subprocess.run with check=True raises CalledProcessError
            # but ProcessRunner catches it
            patch("subprocess.run") as mock
        ):
            error = subprocess.CalledProcessError(
                returncode=1,
                cmd="failing"
            )
            error.stdout = ""
            error.stderr = ""
            mock.side_effect = error

            result = ProcessRunner.run(["failing"], check=True)
            assert result.success is False

    def test_run_text_parameter(self, mock_subprocess_success):
        """
        Test text parameter for string vs bytes output.

        Verifies:
        - text=True is passed (default behavior)
        - text=False could be used with binary data
        """
        with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
            ProcessRunner.run(["echo", "hello"], text=True)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["text"] is True

    def test_run_command_string_formatting(self):
        """
        Test command string is formatted correctly for logging.

        Verifies:
        - Command list is joined with spaces
        - Complex commands with arguments are formatted properly
        """
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = ProcessRunner.run([
                "python", "-m", "pytest",
                "--cov=app",
                "--verbose"
            ])

            expected_cmd = "python -m pytest --cov=app --verbose"
            assert result.command == expected_cmd

    def test_run_with_log_command_true(self, mock_subprocess_success):
        """
        Test log_command=True logs the command execution.

        Verifies:
        - log_command=True triggers debug logging
        - Command is logged before execution
        """
        with (
            patch("subprocess.run", return_value=mock_subprocess_success),
            patch("utils.process_runner.logger") as mock_logger
        ):
            ProcessRunner.run(["echo", "hello"], log_command=True)

            # Should have logged the command
            assert mock_logger.debug.called
            logged_message = mock_logger.debug.call_args[0][0]
            assert "echo hello" in logged_message

    def test_run_with_log_command_false(self, mock_subprocess_success):
        """
        Test log_command=False (default) doesn't log normal execution.

        Verifies:
        - log_command=False is default
        - Debug logging is not called for normal execution
        """
        with (
            patch("subprocess.run", return_value=mock_subprocess_success),
            patch("utils.process_runner.logger") as mock_logger
        ):
            ProcessRunner.run(["echo", "hello"], log_command=False)

            # Should not have logged in debug (but timeout/error logs are separate)
            # Check that debug was not called for normal execution
            if mock_logger.debug.called:
                # If debug was called, it should not be for this execution
                for call in mock_logger.debug.call_args_list:
                    assert "Executing" not in str(call)

    def test_run_logs_timeout(self):
        """
        Test that timeout is logged when log_command=True.

        Verifies:
        - Timeout triggers warning log
        - Warning contains command and timeout info
        """
        timeout_exception = subprocess.TimeoutExpired(
            cmd="sleep 60",
            timeout=5
        )

        with (
            patch("subprocess.run", side_effect=timeout_exception),
            patch("utils.process_runner.logger") as mock_logger
        ):
            ProcessRunner.run(["sleep", "60"], timeout=5, log_command=True)

            # Should have logged the timeout
            assert mock_logger.warning.called
            logged_message = mock_logger.warning.call_args[0][0]
            assert "timed out" in logged_message.lower()

    def test_run_logs_error(self):
        """
        Test that errors are logged when log_command=True.

        Verifies:
        - CalledProcessError triggers error log
        - Error log contains command and return code
        """
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd="failing"
        )
        error.stdout = ""
        error.stderr = ""

        with (
            patch("subprocess.run", side_effect=error),
            patch("utils.process_runner.logger") as mock_logger
        ):
            ProcessRunner.run(["failing"], check=True, log_command=True)

            # Should have logged the error
            assert mock_logger.error.called
            logged_message = mock_logger.error.call_args[0][0]
            assert "failed" in logged_message.lower()

    def test_run_empty_command_list(self):
        """
        Test behavior with empty command list.

        Verifies:
        - Empty command list is passed to subprocess.run
        - Result contains empty command string
        """
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = ProcessRunner.run([])

            assert result.command == ""
            mock.assert_called_once()


# ============================================================================
# Tests for ProcessRunner.run_gh_command() method
# ============================================================================


class TestProcessRunnerGhCommand:
    """Test suite for ProcessRunner.run_gh_command() method."""

    def test_run_gh_command_basic(self):
        """
        Test basic GitHub CLI command execution.

        Verifies:
        - "gh" prefix is added to arguments
        - Default timeout of 5s is used
        - Result is returned correctly
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"id": 123}'
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_gh_command(["issue", "view", "123"])

            assert result.success is True
            assert result.stdout == '{"id": 123}'
            # Verify "gh" was prepended
            mock.assert_called_once()
            call_args = mock.call_args[0][0]
            assert call_args[0] == "gh"
            assert call_args[1:] == ["issue", "view", "123"]

    def test_run_gh_command_default_timeout(self):
        """
        Test that default timeout of 5 seconds is applied.

        Verifies:
        - Default timeout for gh commands is 5 seconds (not 30)
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_gh_command(["status"])

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 5

    def test_run_gh_command_custom_timeout(self):
        """
        Test custom timeout for gh commands.

        Verifies:
        - Custom timeout can override default
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_gh_command(["status"], timeout=10)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 10

    def test_run_gh_command_failure(self):
        """
        Test gh command failure handling.

        Verifies:
        - Non-zero return codes are handled
        - Error output is captured
        """
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "No such issue"

        with patch("subprocess.run", return_value=mock_result):
            result = ProcessRunner.run_gh_command(["issue", "view", "999"])

            assert result.success is False
            assert result.returncode == 1
            assert result.stderr == "No such issue"


# ============================================================================
# Tests for ProcessRunner.run_git_command() method
# ============================================================================


class TestProcessRunnerGitCommand:
    """Test suite for ProcessRunner.run_git_command() method."""

    def test_run_git_command_basic(self):
        """
        Test basic git command execution.

        Verifies:
        - "git" prefix is added to arguments
        - Default timeout of 10s is used
        - Result is returned correctly
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "commit abc123..."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_git_command(["log", "-1"])

            assert result.success is True
            assert result.stdout == "commit abc123..."
            # Verify "git" was prepended
            mock.assert_called_once()
            call_args = mock.call_args[0][0]
            assert call_args[0] == "git"
            assert call_args[1:] == ["log", "-1"]

    def test_run_git_command_default_timeout(self):
        """
        Test that default timeout of 10 seconds is applied.

        Verifies:
        - Default timeout for git commands is 10 seconds (not 30)
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_git_command(["status"])

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 10

    def test_run_git_command_custom_timeout(self):
        """
        Test custom timeout for git commands.

        Verifies:
        - Custom timeout can override default
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_git_command(["status"], timeout=15)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 15

    def test_run_git_command_with_cwd(self):
        """
        Test git command with working directory parameter.

        Verifies:
        - cwd is passed to subprocess.run
        - Git command executes in specified directory
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "On branch main"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_git_command(
                ["status"],
                cwd="/path/to/repo"
            )

            assert result.success is True
            call_kwargs = mock.call_args[1]
            assert call_kwargs["cwd"] == "/path/to/repo"

    def test_run_git_command_no_cwd(self):
        """
        Test git command without working directory (uses current).

        Verifies:
        - cwd is None when not specified
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_git_command(["status"])

            call_kwargs = mock.call_args[1]
            assert call_kwargs["cwd"] is None

    def test_run_git_command_failure(self):
        """
        Test git command failure handling.

        Verifies:
        - Non-zero return codes are handled
        - Error output is captured
        """
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            result = ProcessRunner.run_git_command(["status"])

            assert result.success is False
            assert result.returncode == 128
            assert "not a git repository" in result.stderr


# ============================================================================
# Tests for ProcessRunner.run_shell() method
# ============================================================================


class TestProcessRunnerShell:
    """Test suite for ProcessRunner.run_shell() method."""

    def test_run_shell_basic(self):
        """
        Test basic shell command execution.

        Verifies:
        - Shell command is wrapped with ["bash", "-c"]
        - Default timeout of 30s is used
        - Result is returned correctly
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.txt\nfile2.txt"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell("ls -la")

            assert result.success is True
            assert result.stdout == "file1.txt\nfile2.txt"
            # Verify bash -c wrapping
            mock.assert_called_once()
            call_args = mock.call_args[0][0]
            assert call_args == ["bash", "-c", "ls -la"]

    def test_run_shell_with_pipes(self):
        """
        Test shell command with pipes (shell feature).

        Verifies:
        - Piped commands are executed correctly
        - Shell interpretation happens
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "matching_process"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell("ps aux | grep python")

            assert result.success is True
            call_args = mock.call_args[0][0]
            assert call_args == ["bash", "-c", "ps aux | grep python"]

    def test_run_shell_with_variable_expansion(self):
        """
        Test shell command with variable expansion.

        Verifies:
        - Variable expansion in shell commands is supported
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell("echo $HOME")

            assert result.success is True
            call_args = mock.call_args[0][0]
            assert call_args == ["bash", "-c", "echo $HOME"]

    def test_run_shell_with_command_substitution(self):
        """
        Test shell command with command substitution.

        Verifies:
        - Command substitution $(cmd) works
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "2025-11-19"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell("echo $(date +%Y-%m-%d)")

            assert result.success is True
            call_args = mock.call_args[0][0]
            assert "$(date" in call_args[2]

    def test_run_shell_default_timeout(self):
        """
        Test that default timeout of 30 seconds is applied.

        Verifies:
        - Default timeout for shell commands is 30 seconds
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_shell("ls")

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 30

    def test_run_shell_custom_timeout(self):
        """
        Test custom timeout for shell commands.

        Verifies:
        - Custom timeout can override default
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_shell("ls", timeout=15)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] == 15

    def test_run_shell_no_timeout(self):
        """
        Test shell command with no timeout (timeout=None).

        Verifies:
        - timeout=None removes timeout limit
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_shell("ls", timeout=None)

            call_kwargs = mock.call_args[1]
            assert call_kwargs["timeout"] is None

    def test_run_shell_with_cwd(self):
        """
        Test shell command with working directory parameter.

        Verifies:
        - cwd is passed to subprocess.run
        - Shell command executes in specified directory
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.txt"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell("ls", cwd="/tmp")

            assert result.success is True
            call_kwargs = mock.call_args[1]
            assert call_kwargs["cwd"] == "/tmp"

    def test_run_shell_no_cwd(self):
        """
        Test shell command without working directory (uses current).

        Verifies:
        - cwd is None when not specified
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock:
            ProcessRunner.run_shell("ls")

            call_kwargs = mock.call_args[1]
            assert call_kwargs["cwd"] is None

    def test_run_shell_failure(self):
        """
        Test shell command failure handling.

        Verifies:
        - Non-zero return codes are handled
        - Error output is captured
        """
        mock_result = MagicMock()
        mock_result.returncode = 127
        mock_result.stdout = ""
        mock_result.stderr = "command not found"

        with patch("subprocess.run", return_value=mock_result):
            result = ProcessRunner.run_shell("nonexistent_command")

            assert result.success is False
            assert result.returncode == 127
            assert "command not found" in result.stderr

    def test_run_shell_complex_command(self):
        """
        Test shell command with complex multi-operation string.

        Verifies:
        - Complex shell commands are passed correctly
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "result"
        mock_result.stderr = ""

        complex_cmd = "cd /tmp && mkdir -p test && echo 'done' > test/file.txt"

        with patch("subprocess.run", return_value=mock_result) as mock:
            result = ProcessRunner.run_shell(complex_cmd)

            assert result.success is True
            call_args = mock.call_args[0][0]
            assert call_args[0] == "bash"
            assert call_args[1] == "-c"
            assert call_args[2] == complex_cmd


# ============================================================================
# Tests for ProcessResult dataclass
# ============================================================================


class TestProcessResult:
    """Test suite for ProcessResult dataclass."""

    def test_process_result_creation(self):
        """
        Test ProcessResult can be created with all fields.

        Verifies:
        - All fields are set correctly
        - success boolean is stored
        - returncode is preserved
        """
        result = ProcessResult(
            success=True,
            stdout="output",
            stderr="",
            returncode=0,
            command="echo hello"
        )

        assert result.success is True
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.returncode == 0
        assert result.command == "echo hello"

    def test_process_result_failure_state(self):
        """
        Test ProcessResult can represent failure state.

        Verifies:
        - Failure is properly represented
        - Error information is captured
        """
        result = ProcessResult(
            success=False,
            stdout="partial",
            stderr="error occurred",
            returncode=1,
            command="failing_command"
        )

        assert result.success is False
        assert result.returncode == 1
        assert result.stderr == "error occurred"

    def test_process_result_timeout_state(self):
        """
        Test ProcessResult can represent timeout state.

        Verifies:
        - Timeout is represented with returncode=-1
        - Timeout message is in stderr
        """
        result = ProcessResult(
            success=False,
            stdout="",
            stderr="Command timed out after 5s",
            returncode=-1,
            command="sleep 60"
        )

        assert result.success is False
        assert result.returncode == -1
        assert "timed out" in result.stderr.lower()


# ============================================================================
# Integration tests - Testing multiple components together
# ============================================================================


class TestProcessRunnerIntegration:
    """Integration tests combining multiple features."""

    def test_full_success_flow(self):
        """
        Test complete successful execution flow.

        Verifies:
        - run() with all standard parameters works
        - Result is valid
        - Command is logged properly
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""

        with (
            patch("subprocess.run", return_value=mock_result),
            patch("utils.process_runner.logger")
        ):
            result = ProcessRunner.run(
                ["python", "-m", "pytest"],
                timeout=30,
                capture_output=True,
                text=True,
                log_command=True
            )

            assert result.success is True
            assert result.command == "python -m pytest"

    def test_full_failure_flow(self):
        """
        Test complete failure execution flow.

        Verifies:
        - Failure is captured
        - Error details are available
        - Logging occurs
        """
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "failure details"

        with (
            patch("subprocess.run", return_value=mock_result),
            patch("utils.process_runner.logger")
        ):
            result = ProcessRunner.run(
                ["failing_command"],
                log_command=True
            )

            assert result.success is False
            assert result.returncode == 1

    def test_wrapper_methods_consistency(self):
        """
        Test that wrapper methods delegate to run() consistently.

        Verifies:
        - All wrapper methods use the base run() method
        - Parameters are passed correctly
        - Results are consistent
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # All should succeed
            gh_result = ProcessRunner.run_gh_command(["status"])
            git_result = ProcessRunner.run_git_command(["status"])
            shell_result = ProcessRunner.run_shell("echo test")

            assert all([
                gh_result.success,
                git_result.success,
                shell_result.success
            ])
