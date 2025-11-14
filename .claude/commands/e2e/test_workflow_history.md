# E2E Test: Workflow History Panel with Real-time Updates

## User Story
As a developer using the ADW system, I want to view comprehensive workflow execution history with real-time updates, so that I can track costs, analyze performance, and monitor workflow status.

## Test Scenario
This test validates that the Workflow History tab displays workflow execution history correctly, shows analytics, supports filtering/sorting, and receives real-time WebSocket updates.

## Prerequisites
- Backend server running on port 8000
- Frontend running on configured port
- At least one workflow in the agents directory (or database contains test data)

## Test Steps

### 1. Navigate to History Tab
```
1. Open the application in browser
2. Click on the "History" tab in the navigation
3. Wait for page to load
```

**Expected Result:**
- History view loads without errors
- WebSocket connection indicator shows "Live updates" in green
- Analytics summary panel displays at the top

### 2. Verify Analytics Panel
```
1. Observe the Analytics Summary panel
2. Check for the following metrics:
   - Total Workflows
   - Completed workflows count
   - Failed workflows count
   - Success Rate percentage
   - Average Duration
3. Verify "By Model" breakdown shows model distribution
4. Verify "By Template" breakdown shows template distribution
```

**Expected Result:**
- All metrics display correctly with appropriate numbers
- Model and template breakdowns show tags with counts
- Visual styling matches application design (cards, colors, fonts)

### 3. Verify Workflow Cards Display
```
1. Scroll down to view workflow history cards
2. Check that each card displays:
   - ADW ID and Issue number
   - Status badge (colored: green=completed, red=failed, blue=running, gray=pending)
   - Request summary (nl_input truncated to 2 lines)
   - Duration, Model, Template, Current Phase
   - Cost data (if available): total cost, cache efficiency, cache savings
   - Error message (if workflow failed)
3. Click "Show Details" on a card
4. Verify expanded details show:
   - Worktree path
   - Backend/Frontend ports
   - Phase-by-phase cost breakdown
   - "View on GitHub" link
```

**Expected Result:**
- All workflow cards render correctly
- Status badges have appropriate colors
- Expandable details work smoothly
- Cost visualizations display correctly
- GitHub links are clickable and open in new tab

### 4. Test Search Functionality
```
1. Enter a search term in the search box (e.g., part of an ADW ID)
2. Click "Search" button or press Enter
3. Verify results are filtered
4. Clear search and verify all workflows return
```

**Expected Result:**
- Search filters workflows matching the search term
- Results update immediately after search
- Clearing search restores full list

### 5. Test Status Filter
```
1. Select "Completed" from status dropdown
2. Verify only completed workflows are shown
3. Select "Failed" from status dropdown
4. Verify only failed workflows are shown
5. Select "All Status" to reset
```

**Expected Result:**
- Filtering by status works correctly
- Cards update to show only filtered status
- Resetting shows all workflows again

### 6. Test Sorting
```
1. Select "Sort by Duration" from sort dropdown
2. Verify workflows are reordered by duration
3. Select "Sort by Status" from sort dropdown
4. Verify workflows are grouped by status
5. Select "Sort by Date" to reset to default
```

**Expected Result:**
- Sorting changes the order of workflow cards
- Duration sorting shows longest/shortest first
- Status sorting groups workflows by status
- Date sorting shows most recent first (default)

### 7. Test Real-time WebSocket Updates (Manual)
```
Note: This requires manual intervention to trigger a workflow update

1. Open browser console to see WebSocket messages
2. Observe WebSocket connection status (should show green "Live updates")
3. Manually modify a workflow state file:
   - Navigate to agents/{adw_id}/adw_state.json
   - Change status field (e.g., from "running" to "completed")
   - Save the file
4. Wait up to 5 seconds
5. Observe that the UI updates automatically without refresh
6. Check console logs for "[WS] Received workflow history update" message
```

**Expected Result:**
- WebSocket connection remains active
- UI updates automatically when workflow state changes
- No page refresh required
- Console shows WebSocket update messages
- Updated workflow card reflects new status

### 8. Test Fallback Polling (Optional)
```
1. Stop the backend server temporarily
2. Observe WebSocket connection indicator changes to "Polling"
3. Restart backend server
4. Observe WebSocket reconnects and shows "Live updates"
```

**Expected Result:**
- When WebSocket disconnects, UI falls back to polling (REST API)
- Connection indicator shows "Polling" in gray
- When backend restarts, WebSocket reconnects automatically
- No data loss or errors during disconnect/reconnect

### 9. Test Empty State
```
1. If database is empty, verify empty state displays:
   - Message: "No workflow history"
   - Subtext: "Workflow executions will appear here once they are tracked"
```

**Expected Result:**
- Empty state shows helpful message
- No errors or broken UI elements

### 10. Test Error Handling
```
1. With backend stopped, observe error handling
2. Verify error message displays clearly
3. Restart backend and verify recovery
```

**Expected Result:**
- Error messages are user-friendly
- No console errors or crashes
- System recovers gracefully when backend restarts

## Success Criteria

### UI Elements Present
- [x] Analytics summary panel with 5 key metrics
- [x] Model breakdown tags
- [x] Template breakdown tags
- [x] Search input field
- [x] Status filter dropdown
- [x] Sort dropdown
- [x] Workflow history cards
- [x] WebSocket connection indicator

### Functionality Works
- [x] Search filters workflows correctly
- [x] Status filter shows only matching workflows
- [x] Sorting reorders workflows correctly
- [x] Expandable card details work
- [x] Cost data displays (if available)
- [x] GitHub links are clickable
- [x] WebSocket receives real-time updates
- [x] Fallback polling works when WebSocket disconnected

### Data Accuracy
- [x] Analytics metrics are calculated correctly
- [x] Workflow cards show correct data
- [x] Cost information matches backend data
- [x] Status badges reflect actual workflow status
- [x] Timestamps are formatted correctly

### Visual Design
- [x] Components follow existing Tailwind CSS patterns
- [x] Colors match application theme
- [x] Hover effects work smoothly
- [x] Responsive layout works on different screen sizes
- [x] No visual glitches or layout breaks

## Known Limitations
- Real-time updates require manual file modification for testing (no automated workflow runner)
- Cost data only available for workflows with raw_output.jsonl files
- Pagination not yet implemented (shows first 50 workflows via WebSocket)

## Screenshots
Capture screenshots at key steps:
1. Analytics panel with populated data
2. Workflow cards in grid layout
3. Expanded card with full details
4. Filtered results (status filter applied)
5. WebSocket connection indicator (both states)
