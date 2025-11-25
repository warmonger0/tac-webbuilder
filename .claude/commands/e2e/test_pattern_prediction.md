# E2E Test: Pattern Prediction (Phase 2)

Test submission-time pattern detection in the Natural Language SQL Interface application.

## User Story

As a user
I want the system to detect operation patterns from my request input
So that I get immediate feedback on what operations the system identified

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Request input textarea
   - Project path input
   - Submit button

5. Enter the project path: "/tmp/test-project"
6. Enter the natural language request: "Run backend tests with pytest and frontend tests with vitest"
7. Take a screenshot of the input state
8. Click the Submit button
9. Wait for the request to be processed
10. **Verify** success message appears
11. **Verify** success message contains "Detected patterns:"
12. **Verify** success message includes "test:pytest:backend"
13. **Verify** success message includes "test:vitest:frontend"
14. Take a screenshot of the success message
15. Clear the form

16. Enter a new request: "Deploy to production"
17. Click the Submit button
18. Wait for the request to be processed
19. **Verify** success message contains "Detected patterns:"
20. **Verify** success message includes "deploy:production"
21. Take a screenshot of the final state

## Success Criteria
- Request input accepts text
- Submit button triggers pattern prediction
- Success message displays predicted patterns
- Multiple patterns can be detected from single input
- Pattern names follow format: category:subcategory:target
- 3 screenshots are taken
- No errors appear in the console
- Request processing completes without failures

## Expected Patterns

### Test Patterns
- Input: "Run backend tests with pytest" → Pattern: "test:pytest:backend"
- Input: "Run frontend tests with vitest" → Pattern: "test:vitest:frontend"
- Input: "Test the UI components" → Pattern: "test:vitest:frontend"

### Build Patterns
- Input: "Build and typecheck" → Pattern: "build:typecheck:backend"

### Deploy Patterns
- Input: "Deploy to production" → Pattern: "deploy:production"

### Fix Patterns
- Input: "Fix authentication bug" → Pattern: "fix:bug"

## Performance Requirements
- Pattern prediction adds < 100ms to request submission time
- Request submission succeeds even if pattern prediction fails
- UI displays patterns immediately after submission
