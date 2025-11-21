# E2E Test: Request Form State Persistence

Test form state persistence across navigation, tab switching, and page reloads in the TAC WebBuilder application.

## User Story

As a user creating a new request
I want my form input to be automatically saved as I type
So that I don't lose my work if I accidentally navigate away, reload the page, or switch tabs

## Test Steps

### Part 1: Auto-Save and Tab Navigation

1. Navigate to the `Application URL` (http://localhost:5173 or port from .ports.env)
2. Take a screenshot of the initial Request form
3. **Verify** the "Create New Request" form is present with:
   - Natural language textarea
   - Project path input field
   - Auto-post checkbox
   - Generate Issue button

4. Enter text in the natural language input field: "Build a REST API for user management with CRUD operations and authentication"
5. Enter project path: "/Users/test/projects/user-api"
6. Check the auto-post checkbox
7. Take a screenshot showing filled form fields
8. Wait 500ms for auto-save debounce to complete

9. Click the "Workflows" tab to navigate away from the Request form
10. **Verify** the page shows the Workflows view
11. Take a screenshot of the Workflows view

12. Click the "Request" tab to return to the form
13. **Verify** all form fields retained their values:
    - Natural language input contains: "Build a REST API for user management with CRUD operations and authentication"
    - Project path contains: "/Users/test/projects/user-api"
    - Auto-post checkbox is checked
14. Take a screenshot showing persistence after navigation

### Part 2: Page Reload Persistence

15. Reload the page using browser refresh (Cmd+R / Ctrl+R)
16. Wait for page to fully load
17. **Verify** all form fields still have their values:
    - Natural language input contains the same text
    - Project path contains the same path
    - Auto-post checkbox is still checked
18. Take a screenshot showing persistence after reload

### Part 3: State Clearing After Submission

19. Uncheck the auto-post checkbox (to enable manual confirmation flow)
20. Click "Generate Issue" button
21. Wait for preview and cost estimate to load
22. **Verify** the issue preview is displayed
23. Take a screenshot of the preview

24. Click "Confirm & Post" button
25. Wait for success message: "Issue #N created successfully!"
26. **Verify** the form is cleared:
    - Natural language input is empty
    - Project path may persist (optional field)
    - Auto-post checkbox is unchecked
27. Take a screenshot showing cleared form

### Part 4: Verify State Cleared After Reload

28. Reload the page again
29. **Verify** the form state remains cleared:
    - Natural language input is empty (state was cleared after submission)
    - Auto-post checkbox is unchecked
30. Take final screenshot showing empty form

## Success Criteria

- Form state is automatically saved as user types (with 300ms debounce)
- Form state persists when navigating between tabs
- Form state persists across page reloads
- Form state is cleared after successful form submission
- Cleared state persists across subsequent reloads
- No console errors or warnings during the test
- All 7+ screenshots are captured successfully

## Edge Cases to Test (Optional)

- **Multiple tabs**: Open two tabs with the form, edit in both, verify last-write-wins behavior
- **Empty form**: Verify empty form saves and restores correctly
- **Partial input**: Enter only one field and verify it persists
- **Failed submission**: Trigger a submission error and verify state is NOT cleared

## Notes

- The test assumes a working backend is available for form submission
- The test uses the local development server (not production)
- Screenshots help validate visual state and can be used for regression testing
- Auto-save debounce is 300ms, so wait at least 500ms before navigation to ensure save completes
