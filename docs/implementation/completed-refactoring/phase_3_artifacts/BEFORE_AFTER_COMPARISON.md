# Before/After Code Comparison - Test Fixes

## File: tests/utils/test_process_runner.py

---

## Fix #1: test_run_timeout_handling (Line 141)

### BEFORE (Lines 152-157) - FAILING
```python
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
            timeout=5,
            stdout="partial",      # ERROR: Unexpected kwarg
            stderr="error"         # ERROR: Unexpected kwarg
        )

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.returncode == -1
            assert "timed out" in result.stderr.lower()
            assert "5" in result.stderr  # timeout value in message
            assert result.stdout == "partial"
```

### AFTER (Lines 152-167) - PASSING
```python
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
```

**Changes**:
- Removed `stdout="partial"` and `stderr="error"` from constructor
- Added 2 lines to set attributes after instantiation
- Added clarifying comment

---

## Fix #2: test_run_timeout_with_none_stdout_stderr (Line 169)

### BEFORE (Lines 177-182) - FAILING
```python
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
            timeout=5,
            stdout=None,           # ERROR: Unexpected kwarg
            stderr=None            # ERROR: Unexpected kwarg
        )

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.returncode == -1
            assert result.stdout == ""
            assert "timed out" in result.stderr.lower()
```

### AFTER (Lines 178-192) - PASSING
```python
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
```

**Changes**:
- Removed `stdout=None` and `stderr=None` from constructor
- Added 2 lines to set attributes to None after instantiation
- Added clarifying comment

---

## Fix #3: test_run_timeout_with_bytes_stdout_stderr (Line 194)

### BEFORE (Lines 200-205) - FAILING
```python
    def test_run_timeout_with_bytes_stdout_stderr(self):
        """
        Test timeout handling when TimeoutExpired has bytes stdout/stderr.

        Verifies:
        - Bytes are decoded to strings
        - Both stdout and stderr are properly converted
        """
        timeout_exception = subprocess.TimeoutExpired(
            cmd="sleep 60",
            timeout=5,
            stdout=b"partial bytes",    # ERROR: Unexpected kwarg
            stderr=b"error bytes"       # ERROR: Unexpected kwarg
        )

        with patch("subprocess.run", side_effect=timeout_exception):
            result = ProcessRunner.run(["sleep", "60"], timeout=5)

            assert result.success is False
            assert result.stdout == "partial bytes"
            assert "error bytes" in result.stderr
```

### AFTER (Lines 202-215) - PASSING
```python
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
```

**Changes**:
- Removed `stdout=b"partial bytes"` and `stderr=b"error bytes"` from constructor
- Added 2 lines to set attributes with bytes values after instantiation
- Added clarifying comment

---

## Fix #4: test_run_called_process_error_without_stdout_stderr (Line 244)

### BEFORE (Lines 250-258) - FAILING
```python
    def test_run_called_process_error_without_stdout_stderr(self):
        """
        Test CalledProcessError when stdout/stderr attributes are missing.

        Verifies:
        - Missing attributes don't cause exceptions
        - Error message fallback is used
        - Empty strings are provided for missing output
        """
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd="failing_command"
        )
        # Simulate missing stdout/stderr attributes
        if hasattr(error, 'stdout'):
            delattr(error, 'stdout')   # ERROR: Can't delete readonly attribute
        if hasattr(error, 'stderr'):
            delattr(error, 'stderr')   # ERROR: Can't delete readonly attribute

        with patch("subprocess.run", side_effect=error):
            result = ProcessRunner.run(["failing_command"], check=True)

            assert result.success is False
            assert result.returncode == 1
            assert result.stdout == ""
            assert isinstance(result.stderr, str)
```

### AFTER (Lines 253-265) - PASSING
```python
    def test_run_called_process_error_without_stdout_stderr(self):
        """
        Test CalledProcessError when stdout/stderr attributes are missing.

        Verifies:
        - Missing attributes don't cause exceptions
        - Error message fallback is used
        - Empty strings are provided for missing output
        """
        # Create a mock error that doesn't have stdout/stderr attributes
        error = MagicMock(spec=subprocess.CalledProcessError)
        error.returncode = 1
        error.args = ("failing_command",)
        # Don't include stdout/stderr in the spec so hasattr returns False

        with patch("subprocess.run", side_effect=error):
            result = ProcessRunner.run(["failing_command"], check=True)

            assert result.success is False
            assert result.returncode == 1
            assert result.stdout == ""
            assert isinstance(result.stderr, str)
```

**Changes**:
- Replaced real `subprocess.CalledProcessError` with `MagicMock(spec=subprocess.CalledProcessError)`
- Set `returncode` and `args` directly on the mock
- Removed the `delattr()` calls that were failing
- Updated comment to reflect new approach
- Removed `output` and manual `stdout`/`stderr` setting
- Added comment explaining why the attributes aren't set

---

## Summary of Changes

| Test Name | Issue | Fix Type | Lines Changed |
|-----------|-------|----------|---|
| `test_run_timeout_handling` | TimeoutExpired constructor doesn't accept stdout/stderr kwargs | Move to post-init attribute assignment | 4 lines added |
| `test_run_timeout_with_none_stdout_stderr` | Same as above | Move to post-init attribute assignment | 4 lines added |
| `test_run_timeout_with_bytes_stdout_stderr` | Same as above | Move to post-init attribute assignment | 4 lines added |
| `test_run_called_process_error_without_stdout_stderr` | Can't delete readonly attributes | Use MagicMock instead of real exception | 5 lines changed |

**Total Lines Modified**: ~17 lines across 4 test functions

**Key Concepts Applied**:
1. Exception API compatibility - respect constructor signatures
2. Attribute assignment - use post-instantiation assignment when needed
3. Mock-based testing - use mocks for edge cases with missing attributes
4. Python best practices - work with the actual API, not against it

---

## Verification Commands

```bash
# Navigate to server directory
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Run all ProcessRunner tests
uv run pytest tests/utils/test_process_runner.py -v

# Run specific test
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerRun::test_run_timeout_handling -v

# Run with coverage
uv run pytest tests/utils/test_process_runner.py --cov=utils.process_runner -v
```

Expected result: **47 passed** in all tests
