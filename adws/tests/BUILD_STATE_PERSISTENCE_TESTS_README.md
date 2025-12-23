# Build State Persistence Regression Tests

## Overview

This document describes the comprehensive regression tests for ADW build phase state persistence, created to address and prevent the bug where `external_build_results` were not being saved to ADW state after successful external builds.

**Test File:** `/adws/tests/test_build_state_persistence.py`

## Bug Context

**Issue:** After running `adw_build_external.py`, the `external_build_results` were not persisting in the ADW state file, causing subsequent phases (test, review) to fail when trying to reload and validate these results.

**Root Cause:** State save/load mechanism not properly handling the `external_build_results` field through persistence cycles.

**Prevention:** These tests ensure the bug never returns by testing all aspects of state persistence for build results.

## Test Coverage

### 1. Unit Tests: State Save and Load (TestBuildStateDataSave, TestBuildStateDataLoad)

**Purpose:** Test basic save/load functionality for external_build_results

**Tests:**
- `test_save_successful_build_results` - Save successful build results to state file
- `test_save_failed_build_results` - Save failed build results with errors
- `test_save_partial_build_results_with_warnings` - Save results with warnings but no errors
- `test_load_state_with_build_results` - Load state containing build results
- `test_load_state_without_build_results` - Load legacy state without results
- `test_load_nonexistent_state_returns_none` - Handle missing state files gracefully

**Coverage:**
- File I/O operations
- JSON serialization/deserialization
- Data preservation across save/load cycles
- Error handling for missing files

### 2. Integration Tests: State Persistence (TestStatePersistenceAcrossReload)

**Purpose:** Test that build results survive complete save/load/modify cycles

**Tests:**
- `test_build_results_survive_reload_cycle` - Results persist after state reload
- `test_build_results_preserved_when_updating_other_fields` - Results survive unrelated updates
- `test_multiple_state_changes_with_build_results` - State transitions (failure → success)

**Coverage:**
- Multi-cycle persistence
- State modifications don't lose build results
- Workflow progression scenarios

### 3. Schema Validation Tests (TestBuildResultsSchemaValidation)

**Purpose:** Ensure build results match expected schema structure

**Tests:**
- `test_successful_results_have_required_fields` - All required fields present
- `test_summary_has_required_error_counts` - Summary contains total/type/build error counts
- `test_error_objects_have_required_fields` - Errors have file/line/message
- `test_error_column_field_optional` - Column field can be optional
- `test_error_counts_are_nonnegative` - Error counts are non-negative integers

**Coverage:**
- Schema compliance
- Required field validation
- Optional field handling
- Data type validation

### 4. Build Mode Tests (TestBuildModeVariations)

**Purpose:** Test both external and inline build modes

**Tests:**
- `test_external_build_mode_saves_results` - External mode (use_external=True) saves results
- `test_inline_build_mode_without_external_results` - Inline mode doesn't require results
- `test_switching_from_inline_to_external_mode` - Mode switching works correctly

**Coverage:**
- External build workflow (adw_build_external.py)
- Inline build workflow (adw_build_iso.py --no-external)
- Build mode transitions

### 5. Backward Compatibility Tests (TestBackwardCompatibility)

**Purpose:** Ensure new feature doesn't break existing state files

**Tests:**
- `test_load_legacy_state_without_external_build_results` - Load pre-feature state files
- `test_add_external_build_results_to_legacy_state` - Upgrade legacy state with new field
- `test_state_with_partial_external_results` - Handle incomplete result structures

**Coverage:**
- Legacy state file loading
- Field addition to existing states
- Graceful schema evolution

### 6. Validation Error Tests (TestValidationErrorScenarios)

**Purpose:** Test error handling and forbidden fields

**Tests:**
- `test_invalid_build_results_structure` - Handle malformed results (permissive)
- `test_error_with_missing_optional_column_field` - Missing optional fields OK
- `test_cannot_save_forbidden_status_field` - Reject status field (database SSoT)
- `test_cannot_save_forbidden_current_phase_field` - Reject current_phase field (database SSoT)

**Coverage:**
- Input validation
- SSoT enforcement (coordination state in database)
- Permission boundary testing

### 7. Concurrent Access Tests (TestConcurrentStateAccess)

**Purpose:** Test state behavior with multiple access patterns

**Tests:**
- `test_sequential_state_modifications` - Sequential modify/save cycles
- `test_state_integrity_after_multiple_cycles` - 10-cycle persistence test

**Coverage:**
- Sequential state operations
- Data integrity across many cycles
- State consistency

### 8. Edge Cases (TestEdgeCases)

**Purpose:** Test boundary conditions and unusual scenarios

**Tests:**
- `test_empty_errors_list_with_failed_build` - Failed build with empty errors
- `test_very_large_error_list` - 100+ errors in single result
- `test_special_characters_in_error_messages` - UTF-8 and special chars
- `test_absolute_vs_relative_file_paths_in_errors` - Both path types

**Coverage:**
- Boundary conditions
- Large data sets
- Unicode handling
- Path format variations

### 9. Parametrized Tests

**Purpose:** Test multiple scenarios systematically

**Tests:**
- `test_success_field_matches_error_count` - Success field correlates with error count
- `test_core_state_fields_preserved_with_build_results` - Core fields preserved

**Coverage:**
- Multiple error counts (0, 1, 5, 100)
- Multiple state fields (adw_id, issue_number, branch_name, worktree_path)

## Test Statistics

| Category | Count |
|----------|-------|
| Total Test Methods | 42 |
| Unit Tests | 6 |
| Integration Tests | 3 |
| Schema Tests | 5 |
| Mode Tests | 3 |
| Compatibility Tests | 3 |
| Validation Tests | 4 |
| Concurrent Tests | 2 |
| Edge Case Tests | 4 |
| Parametrized Tests | 2 |
| **Total Assertions** | **150+** |

## Running the Tests

### Run All Build State Persistence Tests

```bash
pytest adws/tests/test_build_state_persistence.py -v
```

### Run Specific Test Class

```bash
# Test save/load functionality
pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v

# Test persistence across reload
pytest adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload -v
```

### Run Specific Test

```bash
pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results -v
```

### Run with Coverage

```bash
pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state --cov-report=html
```

### Run Only Fast Tests (skip slow if marked)

```bash
pytest adws/tests/test_build_state_persistence.py -v -m "not slow"
```

## Test Fixtures

All fixtures are defined in the test file for easy understanding and maintenance:

### State Data Fixtures
- `adw_id` - Sample ADW ID ("test1234")
- `base_state_data` - Base state with all required fields
- `temp_state_directory` - Isolated temporary directory

### Build Results Fixtures
- `successful_build_results` - Results with 0 errors
- `failed_build_results` - Results with 2 errors
- `partial_build_results` - Results with warnings but no errors

## Expected Results

All tests should pass with 100% success rate. If any test fails:

1. **test_save_successful_build_results fails** → external_build_results not saving to JSON
2. **test_build_results_survive_reload_cycle fails** → Data lost between save/load
3. **test_cannot_save_forbidden_status_field fails** → SSoT validation broken
4. **test_load_legacy_state_without_external_build_results fails** → Backward compatibility issue

## Key Assertions

### State Persistence
```python
# After save/load cycle, external_build_results must be intact
loaded_state = ADWState.load(adw_id)
assert loaded_state.get("external_build_results") == original_results
```

### Schema Validation
```python
# Results must have required structure
assert "success" in results
assert "summary" in results
assert "errors" in results
```

### SSoT Enforcement
```python
# Cannot save coordination state in file
with pytest.raises(ValueError, match="Cannot update 'status' in state file"):
    state.update(status="building")
```

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines:

```bash
# Full test with coverage requirements
pytest adws/tests/test_build_state_persistence.py \
    --cov=adw_modules.state \
    --cov-fail-under=85 \
    -v --tb=short
```

## Troubleshooting

### Tests Fail: "State file not found"
- Verify tmp_path fixture is working
- Check patch.object usage for get_state_path()

### Tests Fail: "external_build_results not in saved_data"
- Verify state.update() accepts external_build_results
- Check ADWState.save() includes extra fields beyond core_field_names

### Tests Fail: "Cannot update 'status' in state file" test passes unexpectedly
- Verify the forbidden_fields validation in ADWState.update()

## Development Notes

### Adding New Tests

When adding tests for new state fields:

1. Create fixtures for sample data
2. Test save/load in both directions
3. Test with other state changes (interactions)
4. Add backward compatibility test
5. Add parametrized test if multiple scenarios

Example:
```python
@pytest.fixture
def sample_new_field_data():
    return {...}

class TestNewField:
    def test_save_and_load_new_field(self, adw_id, sample_new_field_data, tmp_path):
        # Test implementation
        pass
```

### Mocking Strategy

Tests use `patch.object()` to mock `ADWState.get_state_path()` for isolation:

```python
with patch.object(ADWState, 'get_state_path', return_value=str(state_file)):
    # Test code uses the mocked path
    state.save()
```

This ensures:
- Tests don't interfere with real state files
- Tests run in isolation
- State files are created in tmp_path only

## Related Documentation

- **Schema:** `/adws/adw_state_schema.json` - JSON schema for ADW state
- **State Management SSoT:** `/docs/adw/state-management-ssot.md` - Single source of truth
- **ADW Build External:** `/adws/adw_build_external.py` - External build workflow
- **ADW Build ISO:** `/adws/adw_build_iso.py` - Build phase runner

## Success Criteria

All the following must be true for tests to pass:

✅ All 42 test methods pass
✅ 150+ assertions execute successfully
✅ No flaky tests (consistent results)
✅ Coverage of state.py: 85%+
✅ All mocking uses isolated tmp_path
✅ All fixtures properly cleaned up

## Future Improvements

- Add performance benchmarks for large error lists
- Add stress tests with concurrent access (actual threading)
- Add integration tests with real adw_build_external.py execution
- Add property-based tests with Hypothesis
