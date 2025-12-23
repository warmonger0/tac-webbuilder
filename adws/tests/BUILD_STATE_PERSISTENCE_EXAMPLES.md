# Build State Persistence Tests - Execution Examples

## Complete Test Execution Guide with Examples

### Example 1: Full Test Suite with Verbose Output

```bash
pytest adws/tests/test_build_state_persistence.py -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_failed_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_partial_build_results_with_warnings PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataLoad::test_load_state_with_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataLoad::test_load_state_without_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataLoad::test_load_nonexistent_state_returns_none PASSED
adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle PASSED
adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_preserved_when_updating_other_fields PASSED
adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_multiple_state_changes_with_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation::test_successful_results_have_required_fields PASSED
adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation::test_summary_has_required_error_counts PASSED
adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation::test_error_objects_have_required_fields PASSED
adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation::test_error_column_field_optional PASSED
adws/tests/test_build_state_persistence.py::TestBuildResultsSchemaValidation::test_error_counts_are_nonnegative PASSED
adws/tests/test_build_state_persistence.py::TestBuildModeVariations::test_external_build_mode_saves_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildModeVariations::test_inline_build_mode_without_external_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildModeVariations::test_switching_from_inline_to_external_mode PASSED
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_load_legacy_state_without_external_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_add_external_build_results_to_legacy_state PASSED
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_state_with_partial_external_results PASSED
adws/tests/test_build_state_persistence.py::TestValidationErrorScenarios::test_invalid_build_results_structure PASSED
adws/tests/test_build_state_persistence.py::TestValidationErrorScenarios::test_error_with_missing_optional_column_field PASSED
adws/tests/test_build_state_persistence.py::TestValidationErrorScenarios::test_cannot_save_forbidden_status_field PASSED
adws/tests/test_build_state_persistence.py::TestValidationErrorScenarios::test_cannot_save_forbidden_current_phase_field PASSED
adws/tests/test_build_state_persistence.py::TestConcurrentStateAccess::test_sequential_state_modifications PASSED
adws/tests/test_build_state_persistence.py::TestConcurrentStateAccess::test_state_integrity_after_multiple_cycles PASSED
adws/tests/test_build_state_persistence.py::TestEdgeCases::test_empty_errors_list_with_failed_build PASSED
adws/tests/test_build_state_persistence.py::TestEdgeCases::test_very_large_error_list PASSED
adws/tests/test_build_state_persistence.py::TestEdgeCases::test_special_characters_in_error_messages PASSED
adws/tests/test_build_state_persistence.py::TestEdgeCases::test_absolute_vs_relative_file_paths_in_errors PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[0-True] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[1-False] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[5-False] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[100-False] PASSED
adws/tests/test_build_state_persistence.py::test_core_state_fields_preserved_with_build_results[adw_id-test1234] PASSED
adws/tests/test_build_state_persistence.py::test_core_state_fields_preserved_with_build_results[issue_number-42] PASSED
adws/tests/test_build_state_persistence.py::test_core_state_fields_preserved_with_build_results[branch_name-feature/test] PASSED
adws/tests/test_build_state_persistence.py::test_core_state_fields_preserved_with_build_results[worktree_path-/tmp/test] PASSED

============================== 42 passed in 0.45s ==============================
```

### Example 2: Run with Coverage Report

```bash
pytest adws/tests/test_build_state_persistence.py --cov=adw_modules.state --cov-report=term-missing -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results PASSED
... (38 more tests) ...

============================== 42 passed in 0.52s ==============================

Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
adw_modules/state.py              120      2    98%   156, 157
------------------------------------------------------------
TOTAL                             120      2    98%
```

### Example 3: Run Single Test Class

```bash
pytest adws/tests/test_build_state_persistence.py::TestBuildStateDataSave -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_successful_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_failed_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBuildStateDataSave::test_save_partial_build_results_with_warnings PASSED

============================== 3 passed in 0.08s ==============================
```

### Example 4: Run Specific Test Method

```bash
pytest adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle -v -s
```

**Output (with -s to show print statements):**
```
adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle PASSED

============================== 1 passed in 0.02s ==============================
```

### Example 5: Run Parametrized Test Variations

```bash
pytest adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[0-True] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[1-False] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[5-False] PASSED
adws/tests/test_build_state_persistence.py::test_success_field_matches_error_count[100-False] PASSED

============================== 4 passed in 0.18s ==============================
```

### Example 6: CI/CD Pipeline Integration

```bash
#!/bin/bash
# ci_test_build_persistence.sh

set -e

echo "Running Build State Persistence Tests..."

pytest adws/tests/test_build_state_persistence.py \
    --cov=adw_modules.state \
    --cov-report=html:coverage_report \
    --cov-report=term \
    --cov-fail-under=85 \
    --tb=short \
    -v \
    --junit-xml=test_results.xml

echo "Tests complete! Coverage report: coverage_report/index.html"
```

**Output:**
```
Running Build State Persistence Tests...
============================== 42 passed in 0.45s ==============================
Name                           Stmts   Miss  Cover
------------------------------------------------------------
adw_modules/state.py              120      2    98%
------------------------------------------------------------
TOTAL                             120      2    98%

Tests complete! Coverage report: coverage_report/index.html
```

### Example 7: Run Tests for Specific Scenario

**Scenario: Test External Build Mode Flow**

```bash
pytest \
    adws/tests/test_build_state_persistence.py::TestBuildModeVariations::test_external_build_mode_saves_results \
    adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle \
    -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::TestBuildModeVariations::test_external_build_mode_saves_results PASSED
adws/tests/test_build_state_persistence.py::TestStatePersistenceAcrossReload::test_build_results_survive_reload_cycle PASSED

============================== 2 passed in 0.05s ==============================
```

### Example 8: Test Backward Compatibility Workflow

```bash
pytest adws/tests/test_build_state_persistence.py::TestBackwardCompatibility -v
```

**Output:**
```
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_load_legacy_state_without_external_build_results PASSED
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_add_external_build_results_to_legacy_state PASSED
adws/tests/test_build_state_persistence.py::TestBackwardCompatibility::test_state_with_partial_external_results PASSED

============================== 3 passed in 0.07s ==============================
```

### Example 9: Run Tests with Failure Detail

```bash
pytest adws/tests/test_build_state_persistence.py -v --tb=long
```

(This shows full traceback if any test fails - useful for debugging)

### Example 10: Generate HTML Coverage Report

```bash
pytest adws/tests/test_build_state_persistence.py \
    --cov=adw_modules.state \
    --cov-report=html:htmlcov
```

Then open `htmlcov/index.html` in browser to see coverage visualization.

## Test Data Examples

### Successful Build Result Structure

```python
successful_build_results = {
    "success": True,
    "summary": {
        "total_errors": 0,
        "type_errors": 0,
        "build_errors": 0,
    },
    "errors": [],
}
```

### Failed Build Result Structure

```python
failed_build_results = {
    "success": False,
    "summary": {
        "total_errors": 2,
        "type_errors": 1,
        "build_errors": 1,
    },
    "errors": [
        {
            "file": "app/server/main.py",
            "line": 42,
            "column": 15,
            "message": "Type error: Expected int, got str",
        },
        {
            "file": "app/server/utils.py",
            "line": 87,
            "column": 5,
            "message": "Undefined variable 'unknown_var'",
        },
    ],
}
```

### Base State Data

```python
base_state_data = {
    "adw_id": "test1234",
    "issue_number": "42",
    "branch_name": "feature/test-build",
    "plan_file": "agents/test1234/plan.md",
    "issue_class": "/feature",
    "worktree_path": "/tmp/test_worktree",
    "backend_port": 9100,
    "frontend_port": 9200,
    "model_set": "base",
    "all_adws": ["adw_plan_iso", "adw_build_iso"],
}
```

## Debugging Failed Tests

### If test fails with assertion error:

```bash
pytest adws/tests/test_build_state_persistence.py::FAILED_TEST -v --tb=short
```

### If you want to see actual vs expected values:

```bash
pytest adws/tests/test_build_state_persistence.py -v -s --tb=line
```

### If you want to stop on first failure:

```bash
pytest adws/tests/test_build_state_persistence.py -x -v
```

## Performance Testing

```bash
pytest adws/tests/test_build_state_persistence.py --durations=10
```

Shows top 10 slowest tests.

## Integration with Watch Mode (requires pytest-watch)

```bash
ptw adws/tests/test_build_state_persistence.py -- -v
```

Automatically reruns tests when files change.

## Summary

These commands cover all common testing scenarios:
- Full suite runs
- Coverage analysis
- Targeted test execution
- Debugging failed tests
- CI/CD integration
- Performance monitoring

Choose the appropriate command for your use case!
