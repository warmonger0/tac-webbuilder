# E2E Test: Workflow History Panel

Test the workflow history panel displays correctly with real-time WebSocket updates, filtering, sorting, and cost visualization.

## User Story

As a developer using the ADW system
I want to view comprehensive history and analytics for all workflow executions
So that I can monitor active workflows, analyze costs, optimize workflow selection, and identify performance bottlenecks

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial page state
3. **Verify** the page title is "Natural Language SQL Interface"

4. Click on the "History" tab
5. **Verify** the "Workflow History" page title is displayed
6. **Verify** the WebSocket connection status indicator shows "Connected" (green dot)
7. Take a screenshot of the History tab initial state

8. **Verify** the "Workflow History Summary" section is displayed
9. **Verify** summary metrics are visible:
   - Total Workflows count
   - Average Cost
   - Average Duration
   - Success Rate
10. Take a screenshot of the summary panel

11. **Verify** the filter controls are displayed with:
    - Sort By dropdown (Date, Duration, Status)
    - Order dropdown (Ascending, Descending)
    - Status filter (All, In Progress, Completed, Failed)
    - Model Set filter (All, Base, Heavy)
    - Search input field
    - Clear Filters button
12. Take a screenshot of the filter controls

13. Test sorting functionality:
    - Select "Duration" from Sort By dropdown
    - **Verify** workflows are re-ordered by duration
    - Take a screenshot showing sorted results

14. Test status filtering:
    - Select "Completed" from Status filter dropdown
    - **Verify** only completed workflows are shown
    - Take a screenshot showing filtered results

15. Test search functionality:
    - Enter a workflow ADW ID in the search field
    - **Verify** search results update to show matching workflows
    - Take a screenshot showing search results

16. Click "Clear Filters" button
17. **Verify** all filters are reset to defaults
18. **Verify** all workflows are displayed again

19. **Verify** workflow history cards are displayed with:
    - ADW ID and status badge
    - Issue number link (if available)
    - Workflow template and model set badges
    - Started/completed timestamps
    - Duration metric
    - Total cost (if cost data available)
    - Concurrent workflows count
20. Take a screenshot of a workflow card (collapsed state)

21. Click "Show Details" button on a workflow card
22. **Verify** expanded details are shown:
    - Original user request text
    - Resource information (worktree path, ports, GitHub URL)
    - Token statistics
    - Cache efficiency metrics
23. Take a screenshot of the expanded workflow card

24. **Verify** cost visualization section is displayed (if cost data available)
25. **Verify** the "In Progress" indicator with animated pulse is shown for active workflows

26. Test empty state:
    - Apply filters that return no results
    - **Verify** empty state message is displayed: "No workflow history found"
    - **Verify** helpful message suggests adjusting filters
27. Take a screenshot of the empty state

28. Clear filters to restore all workflows
29. **Verify** WebSocket connection indicator remains "Connected"
30. **Verify** "Last updated" timestamp is displayed and updates

31. Take a final screenshot of the complete workflow history view

## Success Criteria

- History tab loads without errors
- WebSocket connection establishes successfully (green indicator)
- Summary panel displays aggregate metrics correctly
- Filter controls are fully functional:
  - Sort by date, duration, and status works
  - Status, model, and template filters work
  - Search by ADW ID, issue number, or user input works
  - Clear filters button resets all filters
- Workflow cards display complete metadata:
  - Status badges (in_progress, completed, failed)
  - Timestamps, duration, and cost information
  - Template and model indicators
- Expandable details section works:
  - Shows/hides on button click
  - Displays user input, resource info, and token stats
- Cost visualization integrates correctly when data available
- "In Progress" indicator shows for active workflows
- Empty state displays when no results match filters
- Real-time updates work (connection indicator, last updated timestamp)
- Layout is responsive and follows existing design patterns
- At least 8 screenshots are captured documenting functionality
