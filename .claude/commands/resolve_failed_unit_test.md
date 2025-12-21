# Resolve Failed Unit Test

Fix a specific failing unit test using the provided failure details.

## Instructions

1. **Analyze the Test Failure**
   - Review the test name, purpose, and error message from the `Test Failure Input`
   - Understand what the unit test is trying to validate
   - Identify the root cause from the error details
   - **Focus**: Unit tests validate isolated functionality (single functions, classes, or modules)

2. **Context Discovery**
   - Check recent changes: `git diff origin/main --stat --name-only`
   - If a relevant spec exists in `specs/*.md`, read it to understand requirements
   - Focus only on files that could impact this specific test
   - Read the test file itself to understand test expectations

3. **Reproduce the Failure**
   - IMPORTANT: Use the `execution_command` provided in the test data
   - Run it to see the full error output and stack trace
   - Confirm you can reproduce the exact failure
   - Understand the specific assertion or expectation that's failing

4. **Fix the Issue**
   - Make minimal, targeted changes to resolve only this test failure
   - Ensure the fix aligns with the test purpose and any spec requirements
   - Do not modify unrelated code or tests
   - **Common unit test fixes**:
     - Fix import errors or missing dependencies
     - Correct function signatures or return types
     - Fix logic errors in the implementation
     - Update mocks or fixtures
     - Fix type errors or linting issues

5. **Validate the Fix**
   - Re-run the same `execution_command` to confirm the test now passes
   - Do NOT run other tests or the full test suite
   - Focus only on fixing this specific unit test
   - Ensure no new errors were introduced

## Test Failure Input

$ARGUMENTS

## Unit Test Characteristics

Unit tests typically test:
- Individual functions or methods in isolation
- Pure logic without external dependencies
- Mocked external services or databases
- Type correctness and parameter validation
- Edge cases and error handling

Common failure patterns:
- **Import errors**: Missing dependencies, circular imports
- **Type errors**: Incorrect type hints, mismatched arguments
- **Assertion failures**: Logic bugs, incorrect return values
- **Linting/Style errors**: Code quality issues (ruff, mypy, eslint)
- **Mock failures**: Incorrect mock setup or expectations

## Report

Provide a concise summary of:
- Root cause identified
- Specific fix applied
- Confirmation that the unit test now passes
