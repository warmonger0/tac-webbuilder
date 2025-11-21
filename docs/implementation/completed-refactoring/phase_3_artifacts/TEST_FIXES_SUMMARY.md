# Test Fixes Summary - ProcessRunner Tests

## Overview
Fixed 4 failing tests in `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/utils/test_process_runner.py` by addressing issues with exception initialization and attribute handling.

## Issues Fixed

### 1. `test_run_timeout_handling` (Line 141-167)
**Problem**: `subprocess.TimeoutExpired.__init__()` doesn't accept `stdout` and `stderr` kwargs.

**Solution**: Create the exception first with only required arguments (`cmd` and `timeout`), then set `stdout` and `stderr` attributes afterward.

```python
# Before (FAILED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5,
    stdout="partial",  # TypeError!
    stderr="error"     # TypeError!
)

# After (FIXED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5
)
timeout_exception.stdout = "partial"
timeout_exception.stderr = "error"
```

### 2. `test_run_timeout_with_none_stdout_stderr` (Line 169-192)
**Problem**: Same TimeoutExpired initialization issue with None values.

**Solution**: Same pattern - initialize without stdout/stderr, then set them to None.

```python
# Before (FAILED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5,
    stdout=None,   # TypeError!
    stderr=None    # TypeError!
)

# After (FIXED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5
)
timeout_exception.stdout = None
timeout_exception.stderr = None
```

### 3. `test_run_timeout_with_bytes_stdout_stderr` (Line 194-215)
**Problem**: Same TimeoutExpired initialization issue with bytes values.

**Solution**: Same pattern - initialize without stdout/stderr, then set them to bytes.

```python
# Before (FAILED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5,
    stdout=b"partial bytes",  # TypeError!
    stderr=b"error bytes"     # TypeError!
)

# After (FIXED)
timeout_exception = subprocess.TimeoutExpired(
    cmd="sleep 60",
    timeout=5
)
timeout_exception.stdout = b"partial bytes"
timeout_exception.stderr = b"error bytes"
```

### 4. `test_run_called_process_error_without_stdout_stderr` (Line 244-265)
**Problem**: Can't delete attributes from a real `subprocess.CalledProcessError` instance.

**Solution**: Use `MagicMock` with a spec to create a mock exception that doesn't have `stdout`/`stderr` attributes in the first place.

```python
# Before (FAILED)
error = subprocess.CalledProcessError(
    returncode=1,
    cmd="failing_command"
)
if hasattr(error, 'stdout'):
    delattr(error, 'stdout')  # Error! Can't delete
if hasattr(error, 'stderr'):
    delattr(error, 'stderr')  # Error! Can't delete

# After (FIXED)
error = MagicMock(spec=subprocess.CalledProcessError)
error.returncode = 1
error.args = ("failing_command",)
# Don't include stdout/stderr in the spec so hasattr returns False
```

## Key Insights

1. **TimeoutExpired Exception API**: The `subprocess.TimeoutExpired` exception only accepts `cmd` and `timeout` in its `__init__` method. The `stdout` and `stderr` attributes must be set afterward if needed.

2. **Exception Attributes**: Real exception objects from the subprocess module have read-only or protected attributes that can't be deleted using `delattr()`. Using mocks with appropriate specs is more reliable for testing edge cases.

3. **Mock Specs**: Using `spec=subprocess.CalledProcessError` tells the mock to mimic that class's interface, but we can still avoid setting certain attributes to test missing attribute scenarios.

## Tests Status
- All 4 previously failing tests now pass
- Total test count: 47 tests in the file
- All tests should now pass when run with: `uv run pytest tests/utils/test_process_runner.py -v`

## Files Modified
- `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/utils/test_process_runner.py`
  - Lines 141-167: Fixed `test_run_timeout_handling`
  - Lines 169-192: Fixed `test_run_timeout_with_none_stdout_stderr`
  - Lines 194-215: Fixed `test_run_timeout_with_bytes_stdout_stderr`
  - Lines 244-265: Fixed `test_run_called_process_error_without_stdout_stderr`
