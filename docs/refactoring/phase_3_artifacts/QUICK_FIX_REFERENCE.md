# Quick Fix Reference Card

## File Location
`/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/utils/test_process_runner.py`

---

## The 4 Fixes at a Glance

### Fix 1: Line 141-167 | test_run_timeout_handling
**Error**: `TypeError: __init__() got unexpected keyword argument 'stdout'`
```python
# BEFORE (WRONG):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5, stdout="partial", stderr="error")

# AFTER (CORRECT):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5)
timeout_exception.stdout = "partial"
timeout_exception.stderr = "error"
```

---

### Fix 2: Line 169-192 | test_run_timeout_with_none_stdout_stderr
**Error**: `TypeError: __init__() got unexpected keyword argument 'stdout'`
```python
# BEFORE (WRONG):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5, stdout=None, stderr=None)

# AFTER (CORRECT):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5)
timeout_exception.stdout = None
timeout_exception.stderr = None
```

---

### Fix 3: Line 194-215 | test_run_timeout_with_bytes_stdout_stderr
**Error**: `TypeError: __init__() got unexpected keyword argument 'stdout'`
```python
# BEFORE (WRONG):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5, stdout=b"partial bytes", stderr=b"error bytes")

# AFTER (CORRECT):
timeout_exception = subprocess.TimeoutExpired(cmd="sleep 60", timeout=5)
timeout_exception.stdout = b"partial bytes"
timeout_exception.stderr = b"error bytes"
```

---

### Fix 4: Line 244-265 | test_run_called_process_error_without_stdout_stderr
**Error**: `AttributeError: can't delete readonly attribute 'stdout'`
```python
# BEFORE (WRONG):
error = subprocess.CalledProcessError(returncode=1, cmd="failing_command")
if hasattr(error, 'stdout'):
    delattr(error, 'stdout')  # ERROR!
if hasattr(error, 'stderr'):
    delattr(error, 'stderr')  # ERROR!

# AFTER (CORRECT):
error = MagicMock(spec=subprocess.CalledProcessError)
error.returncode = 1
error.args = ("failing_command",)
# stdout/stderr never set, so hasattr returns False
```

---

## Test Command
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
uv run pytest tests/utils/test_process_runner.py -v
```

## Expected Result
```
47 passed
```

---

## Key Lessons

| Scenario | Solution |
|----------|----------|
| Exception won't accept kwarg | Check `__init__` signature, set as attribute after creation |
| Can't delete readonly attribute | Use `MagicMock(spec=ExceptionClass)` instead |
| Need missing attribute behavior | Don't set it on MagicMock - `hasattr()` returns False |
| Exception attributes vary | Test all variations: None, bytes, strings |

---

## Files Changed
- `tests/utils/test_process_runner.py` - 4 tests fixed (17 lines modified)

## Related Files (Reference Only)
- `utils/process_runner.py` - The code being tested
- `TEST_FIXES_SUMMARY.md` - Full overview
- `FIXES_DETAILED.md` - Detailed explanations
- `BEFORE_AFTER_COMPARISON.md` - Complete code comparison
- `TESTING_GUIDE.md` - Comprehensive guide

---

## Summary
All 4 tests fixed by:
1. Using post-instantiation attribute assignment for TimeoutExpired
2. Using MagicMock for missing attribute scenarios
3. Respecting actual Python API limitations
4. Adding clarifying comments

**Status: COMPLETE - All 47 tests passing**
