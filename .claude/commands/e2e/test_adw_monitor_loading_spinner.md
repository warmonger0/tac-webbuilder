# E2E Test: ADW Monitor Loading Spinner

Test the loading spinner functionality in the ADW Monitor Card component during data refresh operations.

## User Story

As a user monitoring ADW workflows
I want to see a loading indicator when workflow data is being refreshed
So that I know the system is actively fetching updates and the displayed information is current

## Test Steps

### Part 1: Initial State Verification

1. Navigate to the `Application URL`
2. Wait for initial page load (up to 5 seconds)
3. **Verify** the ADW Monitor Card (Panel 2) is visible
4. Take a screenshot of the initial state: "01_initial_state.png"
5. **Verify** the card header contains:
   - "Current Workflow" title
   - Debug button (⚙️)
   - ConnectionStatusIndicator component

### Part 2: Loading Spinner Detection

6. Wait for the loading spinner to appear (monitor for up to 10 seconds)
   - Use browser snapshot to detect element with class "animate-spin"
   - The spinner should appear in the header between the debug button and ConnectionStatusIndicator
7. **Verify** loading spinner is visible during data fetch
8. **Verify** spinner has the following characteristics:
   - Uses animate-spin class (rotating animation)
   - Has emerald-400 color (border-emerald-400)
   - Size is w-4 h-4 (small, non-intrusive)
   - Has glow effect: shadow-[0_0_8px_rgba(16,185,129,0.6)]
   - Has accessibility attributes: title="Refreshing workflow data", role="status", aria-label="Refreshing workflow data"
9. Take a screenshot showing the spinner during refresh: "02_spinner_active.png"

### Part 3: Spinner Disappearance

10. Wait for the loading spinner to disappear (monitor for up to 10 seconds)
11. **Verify** the spinner is no longer visible after fetch completes
12. Take a screenshot of the card after refresh completes: "03_spinner_hidden.png"
13. **Verify** no layout shift occurred (compare with initial state screenshot)

### Part 4: Multiple Refresh Cycles

14. Wait for the next polling cycle (based on polling interval)
15. **Verify** the spinner appears again during the next fetch
16. **Verify** the spinner disappears again after fetch completes
17. **Verify** spinner behavior is consistent across multiple cycles

### Part 5: Visual Inspection

18. **Verify** the spinner is positioned correctly:
    - Located in the top-right area of the card header
    - Between the debug button and ConnectionStatusIndicator
    - Aligned with other header elements
19. **Verify** the spinner does not overlap with other UI elements
20. **Verify** the spinner animation is smooth (no flickering)

## Success Criteria

- Loading spinner appears during active data fetch operations
- Spinner disappears after fetch completes (success or error)
- Spinner has correct styling (emerald color, small size, glow effect)
- Spinner has accessibility attributes for screen readers
- No layout shift when spinner appears/disappears
- Spinner positioning is correct (between debug button and ConnectionStatusIndicator)
- 3 screenshots are captured successfully
- Spinner behavior is consistent across multiple polling cycles

## Expected Behavior

### Spinner Appearance Timing
- **Active Polling (workflows running):** Spinner appears every 2 seconds during fetch
- **Idle Polling (no active workflows):** Spinner appears every 5 seconds during fetch
- **Initial Load:** Spinner should appear immediately during first fetch
- **Fetch Duration:** Typically 50-200ms depending on data size

### Spinner Styling
```html
<div
  class="w-4 h-4 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin shadow-[0_0_8px_rgba(16,185,129,0.6)]"
  title="Refreshing workflow data"
  role="status"
  aria-label="Refreshing workflow data"
/>
```

### Visual Characteristics
- **Size:** 16x16 pixels (w-4 h-4)
- **Color:** Emerald-400 (#10b981)
- **Animation:** Continuous clockwise rotation (animate-spin)
- **Glow:** Soft emerald shadow for visibility
- **Position:** Top-right header, between debug button and connection status

## Manual Verification Commands

```bash
# Start the application
./scripts/start.sh

# Navigate to the frontend
open http://localhost:5173  # macOS
# or
xdg-open http://localhost:5173  # Linux
# or visit in browser manually

# Observe the ADW Monitor Card (Panel 2)
# Watch for the small spinning circle in the top-right corner
# It should appear briefly during each polling cycle
```

## Notes

- The spinner visibility is tied to the `isFetching` state from `useReliablePolling` hook
- Spinner appears/disappears based on actual API call lifecycle (not artificial delays)
- If no workflows are running, polling interval is 5 seconds (spinner appears less frequently)
- If workflows are active, polling interval is 2 seconds (spinner appears more frequently)
- The spinner uses CSS animations (animate-spin) which are GPU-accelerated and performant
- Test should validate both the visual appearance and the timing behavior of the spinner
