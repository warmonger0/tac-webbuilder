# Task: Comprehensive Lint Error Cleanup

## Context
Working on tac-webbuilder project. Recently auto-fixed 293 lint errors, but **150 errors remain** that require manual fixes. These are inherited from the main branch and need to be addressed before proceeding with new feature development.

## Objective
Fix all remaining 150 lint errors to achieve a clean linting baseline for the codebase.

## Current State
- **Total Errors:** 150
- **Auto-fixable:** 0 (already applied)
- **Unsafe fixes available:** 45 (use `--unsafe-fixes` flag)
- **Location:** `app/server/` directory

## Error Breakdown by Type

### 1. B904 - Exception Chaining (42 errors) - HIGHEST PRIORITY
**Issue:** Exceptions raised within `except` blocks should use proper chaining

**Current Pattern:**
```python
try:
    risky_operation()
except Exception as e:
    raise Exception(f"Error: {str(e)}")  # ❌ Loses original traceback
```

**Correct Pattern:**
```python
try:
    risky_operation()
except Exception as e:
    raise Exception(f"Error: {str(e)}") from e  # ✅ Preserves traceback
    # OR
    raise Exception(f"Error: {str(e)}") from None  # If intentionally suppressing
```

**Files affected (sample):**
- `core/file_processor.py` (multiple instances)
- `utils/llm_client.py`
- Others (check with ruff)

### 2. F841 - Unused Variables (20 errors)
**Issue:** Variables assigned but never used

**Examples:**
```python
adapter = get_adapter()  # ❌ Never used
```

**Fix:** Either use the variable or remove the assignment

### 3. PT011 - pytest.raises Too Broad (17 errors)
**Issue:** `pytest.raises(Exception)` is too generic

**Current:**
```python
with pytest.raises(Exception):  # ❌ Too broad
    risky_function()
```

**Fix:**
```python
with pytest.raises(ValueError, match="specific error message"):  # ✅ Specific
    risky_function()
```

### 4. SIM117 - Nested with Statements (17 errors)
**Issue:** Multiple nested `with` statements should be combined

**Current:**
```python
with context1():
    with context2():  # ❌ Nested
        do_work()
```

**Fix:**
```python
with context1(), context2():  # ✅ Combined
    do_work()
```

### 5. UP038 - isinstance with Tuple (11 errors)
**Issue:** Use modern union syntax for isinstance

**Current:**
```python
isinstance(obj, (str, int))  # ❌ Old style
```

**Fix:**
```python
isinstance(obj, str | int)  # ✅ Modern Python 3.10+
```

### 6. C901 - Complexity Too High (10 errors)
**Issue:** Functions exceed complexity threshold (16 > 15)

**Fix:** Refactor complex functions by:
- Extracting helper functions
- Simplifying conditional logic
- Using early returns
- Breaking into smaller methods

**Files affected:**
- `core/project_detector.py::detect_backend`

### 7. PT018 - Complex Assertions (7 errors)
**Issue:** Assertions should be broken down

**Current:**
```python
assert result.status == 200 and result.data == expected and result.valid  # ❌
```

**Fix:**
```python
assert result.status == 200
assert result.data == expected
assert result.valid
```

### 8. SIM105 - Use contextlib.suppress (7 errors)
**Issue:** Empty except blocks should use contextlib.suppress

**Current:**
```python
try:
    risky_operation()
except SomeError:
    pass  # ❌
```

**Fix:**
```python
from contextlib import suppress

with suppress(SomeError):  # ✅
    risky_operation()
```

### 9. Other Errors (~19 errors)
Various other issues including:
- RET505: Unnecessary elif after return
- B006: Mutable default arguments
- PLR0912: Too many branches
- And others

## Step-by-Step Instructions

### Step 1: Analyze Current Errors
```bash
cd app/server
uv run ruff check . --output-format=grouped > lint_errors.txt
cat lint_errors.txt
```

Review the full list of errors grouped by type.

### Step 2: Fix B904 Errors (Exception Chaining) - Top Priority
```bash
# Find all B904 errors
uv run ruff check . --select B904

# For each file, add proper exception chaining
# Use 'from e' to preserve traceback
# Use 'from None' to intentionally suppress original exception
```

**Example Fix Session:**
```python
# Before (core/file_processor.py:102)
except Exception as e:
    raise Exception(f"Error processing file: {str(e)}")

# After
except Exception as e:
    raise Exception(f"Error processing file: {str(e)}") from e
```

### Step 3: Fix F841 Errors (Unused Variables)
```bash
uv run ruff check . --select F841

# For each unused variable:
# - Remove if truly not needed
# - Prefix with _ if intentionally unused (e.g., _adapter)
# - Actually use the variable if it should be used
```

### Step 4: Fix PT011 Errors (Pytest Assertions)
```bash
uv run ruff check . --select PT011

# Update test files to use specific exceptions
# Add match parameter for expected error messages
```

### Step 5: Fix SIM117 Errors (Nested With)
```bash
uv run ruff check . --select SIM117

# Combine nested with statements into single line
```

### Step 6: Fix UP038 Errors (isinstance)
```bash
uv run ruff check . --select UP038

# Replace (Type1, Type2) with Type1 | Type2
```

### Step 7: Fix C901 Errors (Complexity)
```bash
uv run ruff check . --select C901

# Refactor complex functions:
# - Extract helper methods
# - Use guard clauses (early returns)
# - Simplify conditional logic
# - Consider design patterns (strategy, chain of responsibility)
```

### Step 8: Fix PT018 Errors (Complex Assertions)
```bash
uv run ruff check . --select PT018

# Break down compound assertions into separate assert statements
```

### Step 9: Fix SIM105 Errors (contextlib.suppress)
```bash
uv run ruff check . --select SIM105

# Replace try-except-pass with contextlib.suppress
```

### Step 10: Fix Remaining Errors
```bash
uv run ruff check .

# Address any remaining errors one by one
```

### Step 11: Apply Unsafe Fixes (If Appropriate)
```bash
# Some fixes are considered "unsafe" by ruff
# Review these carefully before applying:
uv run ruff check . --unsafe-fixes --fix

# Only apply if you understand the implications
```

### Step 12: Verify All Tests Still Pass
```bash
cd app/server
uv run pytest -xvs

# Ensure no tests broken by lint fixes
# If tests fail, review and fix
```

### Step 13: Commit Changes
```bash
git add -A
git commit -m "$(cat <<'EOF'
fix: Resolve all 150 remaining lint errors

Comprehensive cleanup of inherited lint issues:
- B904: Added exception chaining (42 fixes)
- F841: Removed unused variables (20 fixes)
- PT011: Made pytest assertions specific (17 fixes)
- SIM117: Combined nested with statements (17 fixes)
- UP038: Modernized isinstance calls (11 fixes)
- C901: Refactored complex functions (10 fixes)
- PT018: Split complex assertions (7 fixes)
- SIM105: Used contextlib.suppress (7 fixes)
- Others: Various fixes (19 fixes)

All errors now resolved. Codebase achieves clean lint baseline.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Success Criteria

- ✅ All 150 lint errors resolved
- ✅ `uv run ruff check .` returns 0 errors
- ✅ All existing tests still pass
- ✅ No new warnings introduced
- ✅ Code remains functionally equivalent (no behavior changes)
- ✅ Changes committed with descriptive message

## Files Expected to Change

**Primary:**
- `app/server/core/file_processor.py` (many B904 fixes)
- `app/server/utils/llm_client.py` (B904 fixes)
- `app/server/benchmark_db_performance.py` (F841 fixes)
- `app/server/tests/core/test_file_processor.py` (PT011 fixes)
- `app/server/tests/integration/test_database_operations.py` (SIM117 fixes)
- `app/server/core/routes_analyzer.py` (UP038 fixes)
- `app/server/core/project_detector.py` (C901 complexity refactor)
- `app/server/tests/integration/test_file_query_pipeline.py` (PT018 fixes)
- `app/server/services/phase_coordination/phase_coordinator.py` (SIM105 fixes)

**And others** - run `uv run ruff check . --output-format=grouped` for full list

## Verification Commands

```bash
# Check error count before
uv run ruff check . | tail -1
# Should show: "Found 150 errors."

# Apply fixes (do this iteratively, not all at once)
# ... make fixes ...

# Check error count after
uv run ruff check . | tail -1
# Should show: "Found 0 errors." or "All checks passed!"

# Verify tests
uv run pytest -x
# Should show: All tests passing

# Final validation
uv run ruff check .
echo "Exit code: $?"  # Should be 0
```

## Tips for Efficient Fixing

1. **Work by error type** - Fix all B904 errors together, then F841, etc.
2. **Use search and replace** - Many fixes are repetitive
3. **Test frequently** - Run tests after each batch of fixes
4. **Review auto-fixes** - If using `--unsafe-fixes`, review changes carefully
5. **Create checkpoints** - Commit after fixing each error type
6. **Use IDE** - Many IDEs can apply ruff fixes automatically

## Common Pitfalls

❌ **Don't:**
- Apply all unsafe fixes blindly
- Change behavior while fixing lint
- Fix tests without running them
- Commit everything in one massive change

✅ **Do:**
- Fix one error type at a time
- Run tests after each batch
- Commit incremental progress
- Review each change for correctness

## Time Estimate

- **B904 (42 errors):** ~30-45 minutes (straightforward)
- **F841 (20 errors):** ~15-20 minutes (easy)
- **PT011 (17 errors):** ~20-30 minutes (requires understanding tests)
- **SIM117 (17 errors):** ~10-15 minutes (straightforward)
- **UP038 (11 errors):** ~5-10 minutes (simple)
- **C901 (10 errors):** ~60-90 minutes (complex refactoring)
- **Others (~33 errors):** ~30-45 minutes (varied)

**Total:** ~3-4 hours for comprehensive cleanup

## Next Steps

After completing this cleanup:
1. Report: "Lint cleanup complete - 150 errors resolved"
2. Push changes to main branch
3. Update any feature branches to include lint fixes
4. Resume Issue #116 workflow
5. All future workflows will start from clean baseline

---

**Ready to copy into a new clean chat!**

This comprehensive cleanup will establish a clean linting baseline for the entire codebase.
