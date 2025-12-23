# Build State Persistence Tests - Quick Start

## What are these tests?

Regression tests for the bug where `external_build_results` were not being saved to ADW state after successful external builds.

**File:** `adws/tests/test_build_state_persistence.py`

## Quick Run

```bash
# Run all tests
pytest adws/tests/test_build_state_persistence.py -v

# Run with coverage
pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state -v

# Run specific test class
pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v
```

## Test Breakdown

| Test Class | What It Tests | # Tests |
|-----------|--------------|---------|
| **TestBuildStateDataSave** | Saving build results | 3 |
| **TestBuildStateDataLoad** | Loading build results | 3 |
| **TestStatePersistenceAcrossReload** | Save/load cycles | 3 |
| **TestBuildResultsSchemaValidation** | Schema compliance | 5 |
| **TestBuildModeVariations** | External vs inline modes | 3 |
| **TestBackwardCompatibility** | Legacy state files | 3 |
| **TestValidationErrorScenarios** | Error handling | 4 |
| **TestConcurrentStateAccess** | Sequential modifications | 2 |
| **TestEdgeCases** | Boundary conditions | 4 |
| **Parametrized Tests** | Multiple scenarios | 3 |

**Total: 42 test methods, 150+ assertions**

## Common Scenarios

### Test that successful builds save correctly

```bash
pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results -v
```

### Test that build results survive state reload

```bash
pytest adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle -v
```

### Test backward compatibility with legacy state files

```bash
pytest adws/tests/test_build_state_persistence.py::TestBackwardCompatibility -v
```

### Test all schema validation

```bash
pytest adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation -v
```

## Key Test Fixtures

- **successful_build_results** - 0 errors (build passed)
- **failed_build_results** - 2 errors (build failed)
- **partial_build_results** - warnings only (build passed with warnings)
- **base_state_data** - standard ADW state fields

## Expected Output

When all tests pass:

```
test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results PASSED
test_build_state_persistence.py::TestBuildStateDataSave::test_save_failed_build_results PASSED
test_build_state_persistence.py::TestBuildStateDataSave::test_save_partial_build_results_with_warnings PASSED
...

============================== 42 passed in 0.45s ==============================
```

## Running in CI/CD

```bash
pytest adws/tests/test_build_state_persistence.py \
    --cov=adw_modules.state \
    --cov-fail-under=85 \
    --tb=short \
    -v
```

## What Tests Check

### 1. Save/Load (6 tests)
✅ Build results are saved to JSON file
✅ Build results are loaded from JSON file
✅ Both success and failure results work
✅ Missing files handled gracefully

### 2. Persistence (3 tests)
✅ Results survive reload cycle
✅ Results preserved when updating other fields
✅ State transitions (failure → success) work

### 3. Schema (5 tests)
✅ Results have required fields
✅ Summary has error counts
✅ Errors have file/line/message
✅ Error counts are non-negative
✅ Optional fields can be omitted

### 4. Build Modes (3 tests)
✅ External mode (use_external=True) saves results
✅ Inline mode (use_external=False) works without results
✅ Switching between modes works

### 5. Compatibility (3 tests)
✅ Legacy state files load correctly
✅ New results can be added to old state
✅ Partial results don't break loading

### 6. Validation (4 tests)
✅ Invalid structures handled gracefully
✅ Optional fields work
✅ Forbidden fields rejected (status, current_phase)
✅ SSoT enforcement works

### 7. Concurrent (2 tests)
✅ Sequential modifications maintain integrity
✅ Multiple save/load cycles preserve data

### 8. Edge Cases (4 tests)
✅ Empty error lists work
✅ 100+ errors handled
✅ UTF-8 and special characters work
✅ Absolute and relative paths work

### 9. Parametrized (3 tests)
✅ Success field matches error count
✅ Core state fields preserved
✅ Multiple scenarios tested

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests fail with "State file not found" | Verify pytest-tmp_path fixture, check patch.object() |
| "external_build_results not in saved_data" | Check ADWState.update() accepts the field |
| Imports fail | Verify sys.path includes parent directory |

## Integration with Workflows

These tests run as part of:
- ADW Build phase testing
- State management validation
- CI/CD pipeline quality gates
- Regression test suite

## See Also

- Full documentation: `BUILD_STATE_PERSISTENCE_TESTS_README.md`
- ADW state schema: `adws/adw_state_schema.json`
- State management docs: `docs/adw/state-management-ssot.md`
