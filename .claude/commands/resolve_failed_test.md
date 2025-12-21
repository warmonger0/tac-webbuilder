# Resolve Failed Test (Router)

Route failed test to the appropriate specialized resolver based on test type.

## Instructions

This is a **router command** that detects test type and delegates to specialized resolvers.

1. **Parse Test Failure Input**
   - Read the JSON test failure data from `$ARGUMENTS`
   - Parse to understand test type and failure details

2. **Detect Test Type**

   Analyze the JSON structure and fields to determine test category:

   **E2E Test Detection** (highest priority):
   - JSON contains `test_path` field → E2E test (frontend, Playwright-based)
   - `execution_command` contains `tests/e2e/` → E2E test (backend pytest)
   - `execution_command` contains `.claude/commands/e2e/` → E2E test (command-based)

   **Integration Test Detection**:
   - `execution_command` contains `tests/integration/` → Integration test

   **Regression Test Detection**:
   - `execution_command` contains `tests/regression/` → Regression test

   **Unit Test Detection** (default):
   - `execution_command` contains `tests/core/` → Unit test
   - `execution_command` contains `tests/services/` → Unit test
   - `execution_command` contains `tests/routes/` → Unit test
   - `execution_command` contains `tests/utils/` → Unit test
   - Any other test pattern → Unit test (default fallback)

3. **Route to Specialized Resolver**

   Based on detected test type, execute the appropriate resolver:

   ```
   E2E Test → Execute `/resolve_failed_e2e_test $ARGUMENTS`
   Integration Test → Execute `/resolve_failed_integration_test $ARGUMENTS`
   Unit Test → Execute `/resolve_failed_unit_test $ARGUMENTS`
   ```

   **Note**: Regression test resolver coming soon (for now, route to unit test resolver)

4. **Pass Through Arguments**
   - Pass the EXACT same `$ARGUMENTS` (JSON test failure data) to the specialized resolver
   - Do not modify or transform the data
   - The specialized resolver will handle all fixing logic

## Test Failure Input Format

The input will be JSON in one of these formats:

**Unit/Integration Test** (TestResult):
```json
{
  "test_name": "backend_linting",
  "passed": false,
  "execution_command": "cd app/server && uv run ruff check .",
  "test_purpose": "Validates Python code quality...",
  "error": "app/server/routes/workflow_routes.py:45:1: F401 'os' imported but unused"
}
```

**E2E Test** (E2ETestResult):
```json
{
  "test_name": "Basic Query E2E Test",
  "status": "failed",
  "test_path": ".claude/commands/e2e/test_basic_query.md",
  "error": "(Step 3 ❌) Failed to find element...",
  "screenshots": ["/path/to/screenshot.png"]
}
```

## Routing Examples

**Example 1**: Backend pytest unit test
```json
{
  "execution_command": "cd app/server && uv run pytest tests/core/test_nl_processor.py"
}
```
→ Routes to `/resolve_failed_unit_test`

**Example 2**: Integration test
```json
{
  "execution_command": "cd app/server && uv run pytest tests/integration/test_workflow_integration.py"
}
```
→ Routes to `/resolve_failed_integration_test`

**Example 3**: E2E test (command-based)
```json
{
  "test_path": ".claude/commands/e2e/test_basic_query.md"
}
```
→ Routes to `/resolve_failed_e2e_test`

**Example 4**: Backend E2E test
```json
{
  "execution_command": "cd app/server && uv run pytest tests/e2e/test_api_flow.py"
}
```
→ Routes to `/resolve_failed_e2e_test`

## Report

IMPORTANT: Do NOT report routing decision. Simply execute the specialized resolver and let it handle the response. The user should not see "Routing to X" - they should only see the resolver's output.
