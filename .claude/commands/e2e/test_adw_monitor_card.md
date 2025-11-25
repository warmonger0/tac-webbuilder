# E2E Test: ADW Monitor Card Frontend Component

Test the AdwMonitorCard frontend component for real-time workflow visualization and status monitoring.

## User Story

As a developer submitting ADW workflow requests
I want to see real-time status of my current workflow in the New Request tab
So that I can monitor progress, track costs, identify issues, and understand which phase the workflow is currently executing

## Test Steps

### Part 1: Initial Load and Component Visibility

1. Navigate to the Application URL (http://localhost:5173 or as configured in `.ports.env`)
2. Take a screenshot of the initial page load
3. **Verify** the page loads without errors
4. Click on the "New Request" tab
5. Take a screenshot after clicking New Request tab
6. **Verify** the AdwMonitorCard component is visible in the right column
7. **Verify** the card header displays "Current Workflow"
8. **Verify** the subtitle displays "Real-time progress"

### Part 2: Connection Status Indicator

9. **Verify** the connection status indicator is visible in the header
10. **Verify** the connection status shows one of: excellent, good, poor, or disconnected
11. Take a screenshot of the connection status indicator
12. **Verify** the indicator updates as polling occurs (observe for 15 seconds)

### Part 3: Empty State Display

13. If no workflows are active:
    - **Verify** the "No Active Workflow" message is displayed
    - **Verify** the "Queue is empty" message is displayed
    - **Verify** the empty state icon is visible
    - Take a screenshot of the empty state
    - Skip to Part 8 (Summary)

### Part 4: Workflow Status Display

14. If a workflow is active, **verify** the following information is displayed:
    - Issue number (e.g., #42) with link to GitHub
    - Workflow template badge (e.g., "plan iso", "sdlc complete iso")
    - Issue class badge (e.g., "feature", "bug")
    - Workflow status badge (RUNNING, COMPLETED, FAILED, or PAUSED)
    - Current cost display (e.g., $1.25)
    - Estimated total cost (e.g., "of $5.00")

15. Take a screenshot of the workflow header section

16. **Verify** the GitHub issue link (#XX) is clickable and points to the correct URL

17. If a PR exists:
    - **Verify** the PR number is displayed (e.g., "PR #123")
    - **Verify** the PR link is clickable
    - Take a screenshot showing both issue and PR links

### Part 5: VoltAgent-Style Phase Pipeline Visualization

18. **Verify** the central "W" hub is visible and animated
19. **Verify** lightning effects are visible around the hub
20. **Verify** floating ambient particles are present
21. Take a screenshot of the central hub animation
22. **Verify** all 9 phase nodes are displayed in a circle around the hub:
    - Plan
    - Validate
    - Build
    - Lint
    - Test
    - Review
    - Doc
    - Ship
    - Cleanup

23. For each phase node, **verify**:
    - Phase icon is visible
    - Phase label is readable
    - Connection line to center exists

24. Take a screenshot of the full pipeline visualization

### Part 6: Phase Status and Progress

25. **Verify** completed phases have:
    - Emerald green glow effect
    - Solid border
    - Phase name in emerald color

26. **Verify** the active phase has:
    - Emerald green pulsing glow
    - Animated flowing dots from center outward
    - Phase name in bold emerald color

27. **Verify** pending phases have:
    - Slate gray color
    - No glow effect
    - Phase name in gray color

28. Take a screenshot highlighting completed, active, and pending phases

29. **Verify** the phase progress counter displays correctly (e.g., "4 / 9 phases completed")

30. **Verify** the current phase name is displayed (e.g., "• Test")

### Part 7: Health Status and Metrics

31. If health status is available:
    - **Verify** health badge is displayed with one of: 🟢 HEALTH (ok), 🟡 HEALTH (warning), 🔴 HEALTH (error)
    - Take a screenshot of the health status badge
    - Hover over health badge to see warnings (if any)

32. **Verify** workflow duration is displayed (e.g., "2m 30s" or "1h 15m")

33. If errors exist:
    - **Verify** error count is displayed (e.g., "3 errors")
    - **Verify** error indicator is red
    - Take a screenshot of the error display

34. If process is active:
    - **Verify** "Process Active" indicator is displayed
    - **Verify** the indicator has a pulsing green dot
    - Take a screenshot of the process indicator

### Part 8: Real-Time Polling Behavior

35. Observe the component for 30 seconds
36. **Verify** the workflow status updates automatically (if workflow is progressing)
37. **Verify** the connection status indicator shows polling activity
38. **Verify** costs increment as workflow progresses (if workflow is active)
39. Take a screenshot after 30 seconds to show any changes

40. If a workflow completes during observation:
    - **Verify** status changes from RUNNING to COMPLETED
    - **Verify** all phases show as completed (green glow)
    - **Verify** the pulsing animation stops
    - Take a screenshot of the completed workflow state

### Part 9: Visual Design and Styling

41. **Verify** the card has:
    - Dark gradient background (slate-900 to slate-800)
    - Emerald/teal glow effects
    - Smooth animations and transitions
    - Professional typography

42. **Verify** the card fits properly in the two-column layout (next to ZteHopperQueueCard)

43. Take a screenshot of the full New Request tab showing both cards

### Part 10: Responsive Behavior

44. Resize the browser window to a narrower width
45. **Verify** the component remains usable and readable
46. **Verify** text doesn't overflow or get cut off
47. Take a screenshot at narrower width

### Part 11: Error State (if applicable)

48. If the backend API is unavailable:
    - Stop the backend server temporarily
    - Wait for polling to fail (10-30 seconds)
    - **Verify** error message is displayed: "Unable to load workflows"
    - **Verify** error details are shown
    - **Verify** retry functionality exists
    - Take a screenshot of the error state
    - Restart the backend server

## Success Criteria

- AdwMonitorCard renders in the New Request tab without errors
- Connection status indicator shows polling quality and updates
- Empty state displays correctly when no workflows exist
- Workflow information is displayed accurately (issue, status, costs, template)
- VoltAgent-style circular phase pipeline renders with animations
- Central "W" hub displays with lightning effects and particles
- All 9 phases are visible with correct icons and labels
- Phase status (pending, active, completed) is visually distinct
- Completed phases show emerald glow
- Active phase shows pulsing animation with flowing dots
- Phase progress counter displays correctly (X / 9 phases completed)
- Health status badge displays when available
- Real-time polling updates the display every 10-30 seconds
- GitHub issue and PR links work correctly
- Error count and process active indicators work
- Component styling matches VoltAgent aesthetic
- Component fits in two-column layout
- All animations are smooth and performant
- At least 10 screenshots are captured showing different states

## Manual Verification Commands

```bash
# Start the application
./scripts/start.sh

# Verify frontend is running
curl -s http://localhost:5173 | grep "Natural Language SQL Interface"

# Verify backend API is accessible
curl -s http://localhost:8000/api/adw-monitor | python3 -m json.tool

# Check for active workflows
curl -s http://localhost:8000/api/adw-monitor | jq '.summary.running'

# View health status for a workflow (replace ADW_ID)
curl -s http://localhost:8000/api/adw-health/ADW_ID | python3 -m json.tool
```

## Expected Visual States

### Empty State
- Gray empty state icon
- "No Active Workflow" message
- "Queue is empty" subtitle

### Loading State
- Spinning gradient circle
- "Loading workflows..." message

### Active Workflow State
- Issue number with GitHub link
- Status badge (RUNNING with pulsing green dot)
- Template and class badges
- Cost display ($X.XX of $Y.YY)
- Central "W" hub with lightning and particles
- 9 phase nodes in circle with correct status colors
- Active phase with pulsing animation and flowing dots
- Phase progress counter
- Health badge (if available)
- Duration display
- Process active indicator (if running)

### Completed Workflow State
- Status badge (COMPLETED with solid green dot)
- All phases show emerald glow
- No pulsing animations
- Final cost displayed

### Error State
- Red error icon
- "Unable to load workflows" message
- Error details displayed
- Retry mechanism available

## Testing Notes

- This test focuses on visual validation and real-time behavior
- Component should be tested with both active and empty workflow states
- Animations should be smooth (60 FPS) on modern browsers
- Connection quality should adapt based on polling success rate
- Component should handle rapid workflow state changes gracefully
- Screenshot all major visual states for documentation
- Test with different workflow templates (plan_iso, sdlc_complete_iso, etc.)
- Verify component performance doesn't degrade with long-running workflows

## Related Tests

- Phase 1 Backend: `.claude/commands/e2e/test_adw_monitor.md` - Tests the underlying API
- Basic Query: `.claude/commands/e2e/test_basic_query.md` - Tests core UI functionality

## Future Enhancements to Test

- User actions (view logs, cancel workflow) - when implemented
- WebSocket real-time updates - when replacing polling
- Historical workflow view - when implemented
- Performance graphs - when implemented
- Workflow control buttons (pause, resume) - when implemented
