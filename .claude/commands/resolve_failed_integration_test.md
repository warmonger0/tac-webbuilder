# Resolve Failed Integration Test

Fix a specific failing integration test using the provided failure details.

## Instructions

1. **Analyze the Test Failure**
   - Review the test name, purpose, and error message from the `Test Failure Input`
   - Understand what the integration test is trying to validate
   - Identify the root cause from the error details
   - **Focus**: Integration tests validate interactions between multiple components, modules, or services

2. **Context Discovery**
   - Check recent changes: `git diff origin/main --stat --name-only`
   - If a relevant spec exists in `specs/*.md`, read it to understand requirements
   - Focus on files that impact component interactions
   - Read the test file itself to understand the integration scenario
   - Identify all components/services involved in the test

3. **Reproduce the Failure**
   - IMPORTANT: Use the `execution_command` provided in the test data
   - Run it to see the full error output and stack trace
   - Confirm you can reproduce the exact failure
   - Understand the interaction flow that's failing

4. **Fix the Issue**
   - Make targeted changes to resolve the integration failure
   - Ensure the fix aligns with the test purpose and any spec requirements
   - Consider impact on all components in the integration
   - **Common integration test fixes**:
     - Fix API contract mismatches (request/response format)
     - Correct database schema or migration issues
     - Fix service configuration or initialization order
     - Update mock services or test fixtures
     - Resolve dependency injection or wiring issues
     - Fix async/await or timing issues between components
     - Correct environment variables or configuration

5. **Validate the Fix**
   - Re-run the same `execution_command` to confirm the test now passes
   - Verify all components in the integration still work correctly
   - Do NOT run other tests or the full test suite
   - Focus only on fixing this specific integration test
   - Ensure the fix doesn't break the integration contract

## Test Failure Input

$ARGUMENTS

## Integration Test Characteristics

Integration tests typically test:
- API endpoints with real database connections
- Multi-layer interactions (routes → services → repositories → database)
- Data flow across component boundaries
- Service-to-service communication
- Caching layers and data consistency
- Transaction handling and rollback scenarios
- Authentication/authorization flows across components

Common failure patterns:
- **Contract mismatches**: API request/response format changes
- **Database issues**: Schema mismatches, missing migrations, transaction conflicts
- **Configuration errors**: Missing env vars, incorrect service URLs, port conflicts
- **Timing issues**: Race conditions, async/await problems, event ordering
- **State pollution**: Test isolation failures, shared state between tests
- **Dependency failures**: External services unavailable, mock setup incorrect
- **Data validation**: Schema validation failures, type mismatches across boundaries

## Report

Provide a concise summary of:
- Root cause identified (focus on the integration point that failed)
- Specific fix applied (which component(s) were modified)
- Confirmation that the integration test now passes
- Any side effects on related components (if applicable)
