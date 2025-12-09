# E2E Test: Similar Workflows Component Memory Leak Prevention

Test that the SimilarWorkflowsComparison component properly cleans up AbortController when unmounting, preventing memory leaks and console warnings.

## User Story

As a developer
I want the SimilarWorkflowsComparison component to clean up properly on unmount
So that no memory leaks or console warnings occur when navigating away

## Test Steps

1. Navigate to the `Application URL` (e.g., http://localhost:5173)
2. Take a screenshot of the initial state
3. **Verify** the application loads successfully with no console errors
4. Navigate to a page that includes the SimilarWorkflowsComparison component
   - This could be a workflow history detail page or similar workflows comparison view
5. **Verify** the component starts loading (shows "Loading similar workflows..." text or spinner)
6. Take a screenshot showing the loading state
7. **Immediately** navigate away from the page before the fetch completes
   - Use browser back button or navigate to home page
   - Timing is critical: navigate within 100-200ms of component render
8. **Verify** no console warnings appear, specifically:
   - No "Warning: Can't perform a React state update on an unmounted component"
   - No unhandled promise rejections
   - No AbortError messages in console
9. Check browser console for any errors or warnings
10. Take a screenshot of the browser console (should be clean)
11. Navigate back to the page with SimilarWorkflowsComparison component
12. **Verify** the component loads successfully on second visit
13. Allow the fetch to complete this time
14. **Verify** workflows are displayed correctly
15. Take a screenshot of the successfully loaded component

## Success Criteria

- Component loads and shows loading state
- Rapid navigation away does NOT trigger console warnings
- No "unmounted component" warnings in console
- No unhandled promise rejections
- Component works correctly on subsequent visits
- Browser console remains clean throughout the test
- All screenshots show expected UI states

## Technical Notes

- This test validates the AbortController cleanup pattern
- The fetch request should be aborted when component unmounts
- AbortError should be handled gracefully (no error UI shown)
- State updates should not occur after component unmounts
- Test should be run multiple times to ensure consistent behavior
- Consider using browser DevTools Performance Monitor to check for memory leaks

## Performance Validation

Optional: Use browser DevTools to validate memory profile:
1. Open Chrome DevTools -> Performance tab
2. Start recording
3. Navigate to component page
4. Navigate away quickly (before fetch completes)
5. Repeat 10 times
6. Stop recording
7. **Verify** no memory growth over time
8. **Verify** AbortController instances are garbage collected
