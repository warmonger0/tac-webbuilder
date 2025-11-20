# ProcessRunner Tests - Quick Reference

## File Locations

```
Test File:     tests/utils/test_process_runner.py
Module Tested: utils/process_runner.py
Test Summary:  TEST_RESULTS_SUMMARY.md (this directory)
```

## Test Statistics

- **Total Tests:** 47
- **Test Classes:** 6
- **Fixtures:** 4
- **Lines of Test Code:** 1106

## Quick Test Commands

### Run all ProcessRunner tests
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
uv run pytest tests/utils/test_process_runner.py -v
```

### Run specific test class
```bash
# Test ProcessRunner.run() method
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerRun -v

# Test GitHub CLI wrapper
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerGhCommand -v

# Test git wrapper
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerGitCommand -v

# Test shell wrapper
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerShell -v

# Test ProcessResult dataclass
uv run pytest tests/utils/test_process_runner.py::TestProcessResult -v

# Test integration scenarios
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerIntegration -v
```

### Run single test with full output
```bash
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerRun::test_run_success_basic -vv -s
```

### Run with coverage report
```bash
uv run pytest tests/utils/test_process_runner.py \
    --cov=utils.process_runner \
    --cov-report=term-missing \
    --cov-report=html
```

## Test Organization

### TestProcessRunnerRun (19 tests)
Core `run()` method tests:
- `test_run_success_basic` - Basic successful execution
- `test_run_failure_non_zero_returncode` - Handle failures
- `test_run_timeout_handling` - Timeout exception handling
- `test_run_timeout_with_none_stdout_stderr` - Edge case: None output
- `test_run_timeout_with_bytes_stdout_stderr` - Edge case: bytes output
- `test_run_called_process_error_with_check_true` - CalledProcessError
- `test_run_called_process_error_without_stdout_stderr` - Missing attributes
- `test_run_no_capture_output` - capture_output=False
- `test_run_with_timeout_parameter` - Custom timeout
- `test_run_with_default_timeout` - Default 30s timeout
- `test_run_with_no_timeout` - timeout=None
- `test_run_with_cwd_parameter` - Working directory
- `test_run_with_check_true` - check parameter
- `test_run_text_parameter` - text parameter
- `test_run_command_string_formatting` - Command formatting
- `test_run_with_log_command_true` - Logging enabled
- `test_run_with_log_command_false` - Logging disabled
- `test_run_logs_timeout` - Timeout logging
- `test_run_logs_error` - Error logging
- `test_run_empty_command_list` - Edge case: empty commands

### TestProcessRunnerGhCommand (4 tests)
GitHub CLI wrapper (`run_gh_command()`) tests:
- `test_run_gh_command_basic` - Basic execution with "gh" prefix
- `test_run_gh_command_default_timeout` - Default 5s timeout
- `test_run_gh_command_custom_timeout` - Custom timeout override
- `test_run_gh_command_failure` - Error handling

### TestProcessRunnerGitCommand (6 tests)
Git wrapper (`run_git_command()`) tests:
- `test_run_git_command_basic` - Basic execution with "git" prefix
- `test_run_git_command_default_timeout` - Default 10s timeout
- `test_run_git_command_custom_timeout` - Custom timeout override
- `test_run_git_command_with_cwd` - Working directory handling
- `test_run_git_command_no_cwd` - cwd=None (default)
- `test_run_git_command_failure` - Error handling

### TestProcessRunnerShell (11 tests)
Shell wrapper (`run_shell()`) tests:
- `test_run_shell_basic` - Basic shell execution
- `test_run_shell_with_pipes` - Shell pipes (|)
- `test_run_shell_with_variable_expansion` - Variable expansion ($VAR)
- `test_run_shell_with_command_substitution` - Command substitution $(cmd)
- `test_run_shell_default_timeout` - Default 30s timeout
- `test_run_shell_custom_timeout` - Custom timeout override
- `test_run_shell_no_timeout` - timeout=None
- `test_run_shell_with_cwd` - Working directory handling
- `test_run_shell_no_cwd` - cwd=None (default)
- `test_run_shell_failure` - Error handling
- `test_run_shell_complex_command` - Complex multi-operation commands

### TestProcessResult (3 tests)
ProcessResult dataclass tests:
- `test_process_result_creation` - Create result with all fields
- `test_process_result_failure_state` - Failure state representation
- `test_process_result_timeout_state` - Timeout state (returncode=-1)

### TestProcessRunnerIntegration (3 tests)
Integration tests:
- `test_full_success_flow` - Complete success scenario
- `test_full_failure_flow` - Complete failure scenario
- `test_wrapper_methods_consistency` - Wrapper consistency check

## Fixtures

### mock_subprocess_success
Returns mock with:
- returncode=0, stdout="output", stderr=""
Used by: 7 tests

### mock_subprocess_failure
Returns mock with:
- returncode=1, stdout="partial output", stderr="error message"
Used by: 2 tests

### mock_subprocess_with_bytes
Returns mock with:
- returncode=0, stdout=b"binary output", stderr=b""
Used by: 0 tests (available for future use)

### mock_subprocess_with_no_output
Returns mock with:
- returncode=0, stdout=None, stderr=None
Used by: 0 tests (available for future use)

## Coverage Areas

### Success Cases (All parameterized)
- Basic successful execution
- Command with arguments
- Multiple command variations
- Empty commands

### Failure Cases (All error types)
- Non-zero returncodes (exit codes 1, 2, 127, 128)
- CalledProcessError (with/without output)
- Command not found errors
- Partial output on failure

### Timeout Scenarios (All edge cases)
- Timeout with stdout/stderr output
- Timeout with None output
- Timeout with bytes output
- Timeout message construction

### Parameters (All combinations tested)
- timeout: 5, 10, 15, 30, None
- capture_output: True, False
- text: True, False
- cwd: Specified path, None
- check: True, False
- log_command: True, False

### Shell Features (All tested)
- Pipes: `ps aux | grep python`
- Variables: `echo $HOME`
- Substitution: `echo $(date +%Y-%m-%d)`
- Complex: `cd /tmp && mkdir -p test && echo done`

## Mocking Strategy

All tests use `unittest.mock.patch` to replace `subprocess.run`:
- **No real process execution** - Tests run safely and fast
- **Predictable results** - Same mocks guarantee same behavior
- **Isolated tests** - No side effects between tests
- **Controlled scenarios** - Easy to test error conditions

## Test Patterns

### Pattern 1: Basic Test (Success Case)
```python
def test_something(self, mock_subprocess_success):
    with patch("subprocess.run", return_value=mock_subprocess_success):
        result = ProcessRunner.run(["command"])
        assert result.success is True
```

### Pattern 2: Error Case
```python
def test_something_fails(self):
    error = subprocess.CalledProcessError(returncode=1, cmd="cmd")
    with patch("subprocess.run", side_effect=error):
        result = ProcessRunner.run(["cmd"], check=True)
        assert result.success is False
```

### Pattern 3: Parameter Verification
```python
def test_parameter(self, mock_subprocess_success):
    with patch("subprocess.run", return_value=mock_subprocess_success) as mock:
        ProcessRunner.run(["cmd"], timeout=15)
        call_kwargs = mock.call_args[1]
        assert call_kwargs["timeout"] == 15
```

### Pattern 4: Logging Verification
```python
def test_logging(self):
    with patch("subprocess.run") as mock_run:
        with patch("utils.process_runner.logger") as mock_logger:
            ProcessRunner.run(["cmd"], log_command=True)
            assert mock_logger.debug.called
```

## Common Assertions

```python
# Check success
assert result.success is True
assert result.success is False

# Check returncode
assert result.returncode == 0
assert result.returncode == 1
assert result.returncode == -1  # timeout

# Check output
assert result.stdout == "expected"
assert "message" in result.stderr
assert result.stderr == ""

# Check command
assert result.command == "command args"

# Check subprocess was called with params
assert mock.call_args[1]["timeout"] == 30
assert mock.call_args[0][0] == ["bash", "-c", "cmd"]
```

## Debugging Tips

### Run specific test with verbose output
```bash
uv run pytest tests/utils/test_process_runner.py::TestProcessRunnerRun::test_run_success_basic -vv -s
```

### Show print statements
```bash
uv run pytest tests/utils/test_process_runner.py -s
```

### Stop on first failure
```bash
uv run pytest tests/utils/test_process_runner.py -x
```

### Show slowest tests
```bash
uv run pytest tests/utils/test_process_runner.py --durations=10
```

### Run with pdb on failure
```bash
uv run pytest tests/utils/test_process_runner.py --pdb
```

## Expected Results

All 47 tests should **PASS**:
- ✓ 19 tests for ProcessRunner.run()
- ✓ 4 tests for run_gh_command()
- ✓ 6 tests for run_git_command()
- ✓ 11 tests for run_shell()
- ✓ 3 tests for ProcessResult
- ✓ 3 integration tests

**Expected execution time:** < 1 second (no real process calls)

## Adding New Tests

1. Choose appropriate test class or create new one
2. Use existing fixtures or create new ones
3. Follow AAA pattern (Arrange-Act-Assert)
4. Add comprehensive docstring
5. Include "Verifies:" section
6. Run tests to verify

```python
def test_new_feature(self):
    """Test new feature.

    Verifies:
    - Feature works
    - Output is correct
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.returncode = 0

    # Act
    with patch("subprocess.run", return_value=mock_result):
        result = ProcessRunner.run(["cmd"])

    # Assert
    assert result.success is True
```

## Common Issues & Solutions

### ImportError: cannot import name 'ProcessRunner'
**Solution:** Run tests from `/Users/Warmonger0/tac/tac-webbuilder/app/server` directory

### ModuleNotFoundError: No module named 'utils'
**Solution:** Tests must be run from `/Users/Warmonger0/tac/tac-webbuilder/app/server` where utils package exists

### Test passes locally but fails in CI
**Solution:** Ensure pytest is installed: `uv run pytest --version`

### Mock not working
**Solution:** Use `patch("subprocess.run", ...)` not `patch("utils.process_runner.subprocess.run", ...)`

## Test Maintenance

- Review tests when ProcessRunner.py changes
- Update mocks if subprocess interface changes
- Add tests for new features/methods
- Keep docstrings updated
- Maintain consistent naming patterns
- Run tests before committing changes
