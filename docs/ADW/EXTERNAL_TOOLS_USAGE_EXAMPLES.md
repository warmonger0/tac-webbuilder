# External Tools Usage Examples

Practical examples for using ADW external testing tools to minimize context consumption.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Runner Examples](#test-runner-examples)
- [Build Checker Examples](#build-checker-examples)
- [Test Generator Examples](#test-generator-examples)
- [ADW Wrapper Examples](#adw-wrapper-examples)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Ensure you're in the project root
cd /Users/Warmonger0/tac/tac-webbuilder

# Verify adws directory exists
ls -la adws/
```

### Verify External Tools Exist

```bash
# Check tool workflow scripts
ls -la adws/adw_*_workflow.py

# Expected output:
# adw_build_workflow.py
# adw_test_workflow.py
# adw_test_gen_workflow.py

# Check ADW wrapper scripts
ls -la adws/adw_*_external.py

# Expected output:
# adw_build_external.py
# adw_test_external.py
```

## Test Runner Examples

### Example 1: Run All Python Tests

```bash
cd adws/
uv run adw_test_workflow.py --test-type=pytest
```

**Expected Output:**
```json
{
  "summary": {
    "total": 45,
    "passed": 45,
    "failed": 0,
    "duration_seconds": 8.2
  },
  "failures": [],
  "coverage": {
    "percentage": 85.3
  },
  "next_steps": []
}
```

### Example 2: Run Frontend Tests Only

```bash
cd adws/
uv run adw_test_workflow.py --test-type=vitest
```

**When Tests Fail:**
```json
{
  "summary": {
    "total": 23,
    "passed": 20,
    "failed": 3
  },
  "failures": [
    {
      "test_name": "UserForm::validates email format",
      "file": "app/client/src/components/__tests__/UserForm.test.tsx",
      "line": 42,
      "error_type": "AssertionError",
      "error_message": "Expected email validation to reject invalid format"
    },
    {
      "test_name": "Analytics::calculates score",
      "file": "app/client/src/utils/__tests__/analytics.test.ts",
      "line": 67,
      "error_type": "TypeError",
      "error_message": "Cannot read property 'reduce' of undefined"
    }
  ],
  "next_steps": [
    "Fix email validation in UserForm.test.tsx:42",
    "Fix undefined array in analytics.test.ts:67"
  ]
}
```

### Example 3: Run Tests with Coverage Threshold

```bash
cd adws/
uv run adw_test_workflow.py --test-type=all --coverage-threshold=80
```

**When Coverage is Low:**
```json
{
  "summary": {
    "total": 68,
    "passed": 68,
    "failed": 0
  },
  "coverage": {
    "percentage": 72.1,
    "missing_files": [
      "app/server/core/new_module.py",
      "app/client/src/components/NewFeature.tsx"
    ]
  },
  "next_steps": [
    "Add tests for new_module.py (currently 0% coverage)",
    "Add tests for NewFeature.tsx (currently 15% coverage)"
  ]
}
```

### Example 4: Run Tests in Specific Directory

```bash
cd adws/
uv run adw_test_workflow.py \
  --test-path=app/server/tests/test_analytics.py \
  --test-type=pytest
```

## Build Checker Examples

### Example 1: Run TypeScript Type Check

```bash
cd adws/
uv run adw_build_workflow.py --check-type=typecheck --target=frontend
```

**When Type Errors Exist:**
```json
{
  "success": false,
  "summary": {
    "total_errors": 3,
    "type_errors": 3,
    "build_errors": 0
  },
  "errors": [
    {
      "file": "app/client/src/components/RequestForm.tsx",
      "line": 142,
      "column": 23,
      "error_type": "TS2345",
      "severity": "error",
      "message": "Argument of type 'string' is not assignable to parameter of type 'number'",
      "code_snippet": "setPort('8000')"
    },
    {
      "file": "app/client/src/utils/api.ts",
      "line": 56,
      "column": 10,
      "error_type": "TS2322",
      "severity": "error",
      "message": "Type 'undefined' is not assignable to type 'string'",
      "code_snippet": "const url: string = undefined;"
    }
  ],
  "next_steps": [
    "Fix type error in RequestForm.tsx:142 - convert string to number",
    "Fix undefined assignment in api.ts:56 - provide default value"
  ]
}
```

### Example 2: Run Full Build

```bash
cd adws/
uv run adw_build_workflow.py --check-type=build --target=both
```

**Successful Build:**
```json
{
  "success": true,
  "summary": {
    "total_errors": 0,
    "type_errors": 0,
    "build_errors": 0
  },
  "errors": [],
  "next_steps": []
}
```

### Example 3: Backend Type Check Only

```bash
cd adws/
uv run adw_build_workflow.py --check-type=typecheck --target=backend
```

**When Python Type Errors Exist:**
```json
{
  "success": false,
  "summary": {
    "total_errors": 2,
    "type_errors": 2,
    "build_errors": 0
  },
  "errors": [
    {
      "file": "app/server/core/analytics.py",
      "line": 89,
      "column": 5,
      "error_type": "assignment",
      "severity": "error",
      "message": "Incompatible types in assignment (expression has type 'str', variable has type 'int')"
    }
  ]
}
```

### Example 4: Combined Type Check and Build

```bash
cd adws/
uv run adw_build_workflow.py --check-type=both --target=both
```

## Test Generator Examples

### Example 1: Generate Tests for Python Module

```bash
cd adws/
uv run adw_test_gen_workflow.py --target-path=app/server/core/analytics.py
```

**Output:**
```json
{
  "auto_generated": {
    "count": 23,
    "files": [
      "app/server/tests/test_analytics.py"
    ],
    "coverage_achieved": 78.5,
    "tests": [
      "test_calculate_score_with_valid_input",
      "test_calculate_score_with_empty_data",
      "test_calculate_score_with_negative_values",
      "test_get_workflow_stats_returns_dict",
      "..."
    ]
  },
  "needs_llm_review": [
    {
      "function": "handle_edge_case",
      "file": "app/server/core/analytics.py",
      "line": 89,
      "complexity": 15,
      "reason": "Complex async logic with external API calls and error handling",
      "context": "async def handle_edge_case(workflow_id: str) -> Optional[Dict]:\n    # 15+ decision paths\n    if not workflow_id:\n        return None\n    ...",
      "suggested_test": null
    },
    {
      "function": "calculate_weighted_score",
      "file": "app/server/core/analytics.py",
      "line": 134,
      "complexity": 12,
      "reason": "Multiple nested conditions with floating point calculations",
      "context": "def calculate_weighted_score(factors: List[Factor]) -> float:\n    # Complex weighting algorithm\n    ..."
    }
  ],
  "coverage_gap": {
    "percentage_needed": 6.5,
    "uncovered_lines": [89, 90, 91, 134, 135, 136],
    "uncovered_functions": ["handle_edge_case", "calculate_weighted_score"]
  },
  "next_steps": [
    "Review 23 auto-generated tests in test_analytics.py",
    "Manually write tests for handle_edge_case (complexity: 15)",
    "Manually write tests for calculate_weighted_score (complexity: 12)",
    "Run tests to achieve 85% coverage target"
  ]
}
```

### Example 2: Generate Tests for TypeScript Component

```bash
cd adws/
uv run adw_test_gen_workflow.py \
  --target-path=app/client/src/components/UserForm.tsx \
  --test-type=unit
```

**Output:**
```json
{
  "auto_generated": {
    "count": 12,
    "files": [
      "app/client/src/components/__tests__/UserForm.test.tsx"
    ],
    "coverage_achieved": 82.0,
    "tests": [
      "renders form with all fields",
      "validates email format on blur",
      "submits form with valid data",
      "displays error messages for invalid input",
      "..."
    ]
  },
  "needs_llm_review": [
    {
      "function": "handleComplexValidation",
      "file": "app/client/src/components/UserForm.tsx",
      "line": 67,
      "complexity": 9,
      "reason": "Async validation with debouncing and API calls"
    }
  ],
  "coverage_gap": {
    "percentage_needed": 3.0,
    "uncovered_lines": [67, 68, 69, 72]
  }
}
```

### Example 3: Generate Integration Tests

```bash
cd adws/
uv run adw_test_gen_workflow.py \
  --target-path=app/server/api/workflows.py \
  --test-type=integration \
  --coverage-goal=90
```

## ADW Wrapper Examples

### Example 1: Run Tests via External ADW

**Step 1: Create Worktree**
```bash
cd adws/
uv run adw_plan_iso.py 123

# Output shows ADW ID
# Example: Created worktree for ADW abc12345
```

**Step 2: Run External Test ADW**
```bash
uv run adw_test_external.py 123 abc12345
```

**Step 3: Check Results in State**
```bash
cat ../agents/abc12345/adw_state.json | jq '.external_test_results'
```

**Output:**
```json
{
  "success": false,
  "summary": {
    "total": 45,
    "passed": 42,
    "failed": 3
  },
  "failures": [
    {
      "test_name": "test_analytics",
      "file": "app/server/tests/test_analytics.py",
      "line": 67,
      "error": "AssertionError: Expected 0.85, got 0.72"
    }
  ],
  "next_steps": [
    "Fix assertion in test_analytics.py:67"
  ]
}
```

### Example 2: Run Build Check via External ADW

**After Creating Worktree:**
```bash
cd adws/
uv run adw_build_external.py 123 abc12345
```

**Check Build Results:**
```bash
cat ../agents/abc12345/adw_state.json | jq '.external_build_results'
```

**Output:**
```json
{
  "success": true,
  "summary": {
    "total_errors": 0,
    "type_errors": 0,
    "build_errors": 0
  },
  "errors": [],
  "next_steps": []
}
```

### Example 3: Complete Workflow with External Tools

```bash
# 1. Create worktree and plan
uv run adw_plan_iso.py 123
# Note the ADW ID (e.g., abc12345)

# 2. Implement the solution
uv run adw_build_iso.py 123 abc12345

# 3. Run tests externally
uv run adw_test_external.py 123 abc12345

# 4. Check build externally
uv run adw_build_external.py 123 abc12345

# 5. Review complete state
cat ../agents/abc12345/adw_state.json | jq .
```

## Integration Examples

### Example 1: Future Integration with --use-external Flag

**Planned Usage (Not Yet Implemented):**
```bash
# Run test ADW with external tools
uv run adw_test_iso.py 123 abc12345 --use-external

# Run build ADW with external tools
uv run adw_build_iso.py 123 abc12345 --use-external

# Run complete SDLC with external tools
uv run adw_sdlc_iso.py 123 --use-external
```

### Example 2: Manual External Tool Testing

**Test Workflow Without ADW State:**
```bash
cd adws/

# Run test workflow directly (for testing)
uv run adw_test_workflow.py \
  --test-type=pytest \
  --coverage-threshold=80 \
  --json-output

# Redirect output to file
uv run adw_test_workflow.py \
  --test-type=pytest \
  --json-output > /tmp/test_results.json

# View results
cat /tmp/test_results.json | jq .
```

### Example 3: Chaining Multiple External Tools

```bash
# 1. Run tests
uv run adw_test_external.py 123 abc12345

# 2. If tests pass, run build check
if [ $? -eq 0 ]; then
  uv run adw_build_external.py 123 abc12345
fi

# 3. Check final state
cat ../agents/abc12345/adw_state.json | jq '{
  test_results: .external_test_results.success,
  build_results: .external_build_results.success
}'
```

## Troubleshooting

### Issue: "No worktree found"

**Problem:**
```bash
uv run adw_test_external.py 123 abc12345
# Error: No worktree found at trees/abc12345
```

**Solution:**
```bash
# Create worktree first with entry point workflow
uv run adw_plan_iso.py 123

# Or check if worktree exists
git worktree list
ls -la trees/
```

### Issue: "State file not found"

**Problem:**
```bash
uv run adw_test_external.py 123 abc12345
# Error: State file not found at agents/abc12345/adw_state.json
```

**Solution:**
```bash
# Verify state file exists
ls -la agents/abc12345/

# If missing, run plan workflow first
uv run adw_plan_iso.py 123
```

### Issue: "Tests not found in worktree"

**Problem:**
```bash
uv run adw_test_external.py 123 abc12345
# Error: No tests found in app/server/tests/
```

**Solution:**
```bash
# Check worktree contents
ls -la trees/abc12345/app/server/tests/

# Ensure worktree is up to date
cd trees/abc12345
git status
git pull origin main
```

### Issue: "Tool workflow script not executable"

**Problem:**
```bash
uv run adw_test_workflow.py
# Error: Permission denied
```

**Solution:**
```bash
# Make scripts executable
chmod +x adws/adw_test_workflow.py
chmod +x adws/adw_build_workflow.py
chmod +x adws/adw_test_gen_workflow.py
```

### Issue: "JSON parsing error"

**Problem:**
```bash
cat ../agents/abc12345/adw_state.json | jq '.external_test_results'
# Error: parse error
```

**Solution:**
```bash
# Check if external tool ran successfully
echo $?  # Should be 0 or 1

# View raw state file
cat ../agents/abc12345/adw_state.json

# Validate JSON
cat ../agents/abc12345/adw_state.json | python3 -m json.tool
```

### Issue: "Coverage threshold not met"

**Problem:**
```json
{
  "coverage": {
    "percentage": 72.1,
    "threshold": 80
  },
  "next_steps": [
    "Add tests to reach 80% coverage threshold"
  ]
}
```

**Solution:**
```bash
# Generate tests for uncovered files
uv run adw_test_gen_workflow.py \
  --target-path=app/server/core/uncovered_module.py

# Re-run tests with coverage
uv run adw_test_external.py 123 abc12345
```

## Performance Comparison

### Before: Running Tests Inline (Traditional)

```bash
# Traditional approach loads all test files into context
uv run adw_test_iso.py 123 abc12345

# Context usage:
# - All test files: ~40K tokens
# - All test outputs: ~10K tokens
# - Total: ~50K tokens
# - Cost: ~$1.50 per run
```

### After: Running Tests Externally (Optimized)

```bash
# External tools approach returns only failures
uv run adw_test_external.py 123 abc12345

# Context usage:
# - Compact JSON: ~5K tokens (passing tests)
# - Compact JSON: ~8K tokens (3 failures)
# - Total: ~5-8K tokens
# - Cost: ~$0.15-0.25 per run
# - Savings: 84-90%
```

## Best Practices

1. **Always Create Worktree First**
   ```bash
   # Entry point workflows create worktrees
   uv run adw_plan_iso.py 123
   # Dependent workflows require existing worktrees
   uv run adw_test_external.py 123 abc12345
   ```

2. **Check State After External Tools**
   ```bash
   # View compact results
   cat ../agents/abc12345/adw_state.json | jq '.external_test_results'
   ```

3. **Use External Tools for CI/CD**
   ```bash
   # Fast feedback in CI pipelines
   uv run adw_test_external.py $ISSUE_NUMBER $ADW_ID
   if [ $? -ne 0 ]; then
     echo "Tests failed - check state for details"
     exit 1
   fi
   ```

4. **Combine External Tools**
   ```bash
   # Run tests and build check together
   uv run adw_test_external.py 123 abc12345 && \
   uv run adw_build_external.py 123 abc12345
   ```

5. **Monitor Token Savings**
   ```bash
   # Track actual savings in logs
   # Compare context size before/after
   ```

## Next Steps

- **Migration Guide**: See `docs/EXTERNAL_TOOLS_MIGRATION_GUIDE.md` for migrating existing workflows
- **Architecture**: See `docs/ADW_CHAINING_ARCHITECTURE.md` for design details
- **Integration**: See `docs/EXTERNAL_TOOLS_INTEGRATION_GUIDE.md` for integration strategies
- **API Reference**: See `docs/EXTERNAL_TOOL_SCHEMAS.md` for complete API specifications

---

**Document Version**: 1.0
**Last Updated**: 2025-01-16
**Status**: Production Ready
