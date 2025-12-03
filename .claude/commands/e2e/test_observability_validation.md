# E2E Test: Observability System Validation

Test the complete observability system (Panel 10) to ensure all workflow phases, task logs, and user prompts are correctly captured and displayed.

## User Story

As a developer using the observability system
I want to see loading indicators and workflow execution data in Panel 10
So that I have visibility into SDLC workflow progress and can track phase completions

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Panel 10 (Log Panel) is visible
   - Tab navigation showing: Work Logs, Task Logs, User Prompts

5. Click on "Log Panel" (Panel 10) to ensure it's in focus
6. Take a screenshot of the Log Panel initial state

### Test Work Logs Tab
7. **Verify** the "Work Logs" tab is active by default
8. **Verify** loading spinner displays with message "Loading work logs..."
9. Wait for data to load (spinner should disappear)
10. Take a screenshot of the Work Logs tab loaded state
11. **Verify** work log entries are displayed (or "No work log entries found" message appears)

### Test Task Logs Tab
12. Click on the "Task Logs" tab
13. **Verify** loading spinner displays with message "Loading task logs..."
14. Wait for data to load (spinner should disappear)
15. Take a screenshot of the Task Logs tab loaded state
16. **Verify** task log table is displayed with columns:
    - Issue #
    - ADW ID
    - Phase
    - Status
    - Duration
    - Completed At
    - Error
17. **Verify** task logs contain phase data (or "No task logs found" message appears)

### Test User Prompts Tab
18. Click on the "User Prompts" tab
19. **Verify** loading spinner displays with message "Loading user prompts..."
20. Wait for data to load (spinner should disappear)
21. Take a screenshot of the User Prompts tab loaded state
22. **Verify** user prompts are displayed with metadata:
    - Issue number and title
    - Natural language input
    - Complexity and type badges
    - Cost and token estimates
23. **Verify** user prompts contain request data (or "No user prompts found" message appears)

### Test Issue Number Filter
24. Switch back to "Task Logs" tab
25. Enter issue number "137" in the "Filter by Issue Number" field
26. **Verify** loading spinner displays again
27. Wait for filtered data to load
28. Take a screenshot of the filtered Task Logs
29. **Verify** only task logs for issue #137 are displayed

30. Switch to "User Prompts" tab
31. **Verify** only user prompts for issue #137 are displayed
32. Take a screenshot of the filtered User Prompts

### Test Loading Spinner Consistency
33. Clear the issue number filter
34. Rapidly switch between all three tabs
35. **Verify** loading spinners display consistently across all tabs
36. **Verify** no visual conflicts or duplicate spinners
37. Take a screenshot of the final state

## Success Criteria

**UI Functionality:**
- Loading spinners display correctly in all three tabs
- Loading spinners have consistent styling: centered, animated, descriptive text
- Loading spinners disappear when data is loaded
- No duplicate loading indicators or visual conflicts
- Tab switching works smoothly without errors

**Data Validation:**
- Work Logs tab displays session summaries (if data exists)
- Task Logs tab displays phase completion data with proper columns
- User Prompts tab displays request submissions with metadata
- Issue number filter works across all tabs
- Pagination controls work correctly (when applicable)

**Observability System:**
- Task logs table captures ADW phase completions
- User prompts table captures request submissions
- Phase transitions tracked with timestamps
- Duration and status data present
- Cost and token estimates captured

**Screenshots:**
- 8 screenshots taken at key points:
  1. Initial state
  2. Log Panel initial state
  3. Work Logs loaded
  4. Task Logs loaded
  5. User Prompts loaded
  6. Task Logs filtered by issue #137
  7. User Prompts filtered by issue #137
  8. Final state after tab switching
