# E2E Test: ADW Monitor Phase 3 - Polish & Integration

Test Phase 3 enhancements: WebSocket real-time updates, animations, performance optimizations, and error handling.

## User Story

As a developer monitoring ADW workflows
I want smooth, real-time updates with visual feedback and optimized performance
So that I can efficiently track workflow progress without manual refreshes or performance degradation

## Test Steps

### Part 1: WebSocket Real-Time Updates

1. Navigate to the `Application URL`
2. Take a screenshot of the ADW Monitor card initial state
3. **Verify** the ADW Monitor card is visible on the page
4. **Verify** the WebSocket connection indicator shows "connected" or "online"
5. Open browser DevTools Network tab and filter for WebSocket connections
6. **Verify** a WebSocket connection to `/ws/adw-monitor` exists
7. **Verify** the connection status is "101 Switching Protocols" (successful upgrade)
8. Monitor the WebSocket frames for incoming messages
9. If workflows are active:
   - **Verify** real-time workflow state updates arrive via WebSocket
   - **Verify** updates occur without page refresh or polling requests
   - Take a screenshot of the WebSocket frames in DevTools
10. Record the WebSocket message latency (time from message sent to UI update)
11. **Verify** WebSocket latency is less than 50ms

### Part 2: WebSocket Reconnection Test

12. Simulate WebSocket disconnect by temporarily blocking network in DevTools
13. **Verify** the connection indicator shows "reconnecting" or "degraded" status
14. Take a screenshot of the reconnection state
15. Restore network connection
16. **Verify** WebSocket reconnects automatically with exponential backoff
17. **Verify** the connection indicator returns to "connected" status
18. **Verify** workflow updates resume after reconnection
19. Take a screenshot of the restored connection

### Part 3: Fallback to Polling

20. Disable WebSocket support (use DevTools to block ws:// connections)
21. **Verify** the application gracefully falls back to polling
22. **Verify** the connection indicator shows "degraded" or "polling" status
23. **Verify** workflow updates continue to work via HTTP polling
24. Take a screenshot showing polling fallback mode
25. Re-enable WebSocket support
26. **Verify** the application switches back to WebSocket connection

### Part 4: Animation System Validation

27. Navigate to a page with active workflows
28. **Verify** loading skeletons appear during initial data fetch
29. Take a screenshot of loading skeletons
30. Once data loads, **Verify** smooth fade-in transitions for workflow cards
31. If a workflow status changes during testing:
    - **Verify** status badge transitions smoothly (no abrupt changes)
    - **Verify** progress bar animates smoothly (interpolation, not jumps)
    - Take a screenshot of status change animation
32. **Verify** phase node transitions show visual effects (scale, glow, opacity)
33. Hover over phase nodes and **Verify** hover effects are present
34. Take a screenshot showing animation states

### Part 5: Performance Benchmarks

35. Open browser DevTools Performance tab
36. Start recording performance
37. Trigger a workflow list refresh
38. Stop recording after data loads
39. **Verify** frontend render time is less than 16ms (60fps target)
40. Take a screenshot of Performance profiler results
41. Execute API performance test:
    ```bash
    curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/adw-monitor
    ```
42. **Verify** API response time is less than 200ms (0.200s)
43. Make a second identical API call immediately after
44. **Verify** the second call uses cached data (faster response)
45. Record both response times

### Part 6: Error Handling & Recovery

46. Simulate a network timeout by slowing network in DevTools (Slow 3G)
47. **Verify** a user-friendly error message appears (not raw error text)
48. **Verify** a "Retry" button is present in the error message
49. Take a screenshot of the error state
50. Click the "Retry" button
51. **Verify** the application attempts to reconnect/refetch
52. Restore normal network speed
53. **Verify** the application recovers and displays data correctly
54. Take a screenshot of the recovered state

55. Test error boundary by triggering a component error (if possible)
56. **Verify** the error boundary catches the error gracefully
57. **Verify** a user-friendly error message is displayed
58. **Verify** the rest of the application continues to function

### Part 7: Accessibility Validation

59. Use keyboard navigation (Tab key) to navigate through workflow cards
60. **Verify** focus indicators are visible on all interactive elements
61. **Verify** phase nodes can be navigated with Tab and activated with Enter
62. Press Tab through all elements and take a screenshot showing focus states
63. **Verify** ARIA labels are present on status indicators (use DevTools Accessibility tree)
64. **Verify** progress bars have accessible labels (aria-label or aria-labelledby)
65. Take a screenshot of the Accessibility tree in DevTools

### Part 8: Responsive Design Test

66. Resize browser to mobile width (320px)
67. **Verify** ADW Monitor card adapts to mobile layout
68. **Verify** all content is readable and accessible
69. Take a screenshot of mobile view (320px width)
70. Resize to tablet width (768px)
71. **Verify** layout adjusts for tablet view
72. Take a screenshot of tablet view (768px width)
73. Resize to desktop width (1024px+)
74. **Verify** layout utilizes full width appropriately
75. Take a screenshot of desktop view

### Part 9: Data Quality & Consistency

76. If multiple workflows are present:
    - **Verify** workflows are sorted correctly (most recent first)
    - **Verify** no duplicate workflow IDs are displayed
    - **Verify** all cost values are formatted correctly (2 decimal places)
    - **Verify** all duration values are human-readable (e.g., "2h 30m")
77. **Verify** phase progress percentages are between 0-100
78. **Verify** status colors are consistent with system-wide color scheme
79. Take a screenshot showing multiple workflows

### Part 10: Concurrent Updates Test

80. If possible, trigger multiple workflow state changes in rapid succession
81. **Verify** all updates are reflected in the UI without data loss
82. **Verify** no race conditions occur (updates don't overwrite each other)
83. **Verify** UI remains responsive during rapid updates
84. Take a screenshot after rapid updates

## Success Criteria

### WebSocket Functionality
- [ ] WebSocket connection to `/ws/adw-monitor` established successfully
- [ ] Real-time workflow updates received via WebSocket (no polling)
- [ ] WebSocket message latency < 50ms
- [ ] Reconnection works with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- [ ] Graceful fallback to polling when WebSocket unavailable

### Animation Quality
- [ ] Loading skeletons display during initial fetch
- [ ] Smooth fade-in transitions for workflow cards
- [ ] Status badge changes animate smoothly (CSS transitions)
- [ ] Progress bars interpolate smoothly (no jumps)
- [ ] Phase node transitions show visual effects (scale, glow, opacity)
- [ ] Hover effects work on interactive elements

### Performance Targets
- [ ] API response time < 200ms (measured over multiple requests)
- [ ] WebSocket latency < 50ms (from server send to UI update)
- [ ] Frontend render time < 16ms (60fps for smooth animations)
- [ ] Cache improves performance (second request faster than first)

### Error Handling
- [ ] User-friendly error messages displayed (not raw errors)
- [ ] Retry button present and functional in error states
- [ ] Error boundary catches component crashes gracefully
- [ ] Application recovers from network failures automatically
- [ ] Error states don't break other functionality

### Accessibility
- [ ] Keyboard navigation works (Tab through elements, Enter to activate)
- [ ] Focus indicators visible on all interactive elements
- [ ] ARIA labels present on status indicators and progress bars
- [ ] Screen reader compatible (accessible names and roles)

### Responsive Design
- [ ] Mobile layout works correctly (320px width)
- [ ] Tablet layout works correctly (768px width)
- [ ] Desktop layout works correctly (1024px+ width)
- [ ] All content readable and accessible at all breakpoints

### Data Quality
- [ ] Workflows sorted correctly (most recent first)
- [ ] No duplicate workflow IDs displayed
- [ ] Cost values formatted correctly (2 decimal places)
- [ ] Duration values human-readable (e.g., "2h 30m")
- [ ] Phase progress percentages valid (0-100)
- [ ] Status colors consistent with system-wide scheme

## Manual Verification Commands

```bash
# Test WebSocket connection with wscat (if installed)
wscat -c ws://localhost:8000/ws/adw-monitor

# Test API performance
time curl -s http://localhost:8000/api/adw-monitor > /dev/null

# Measure response time precisely
curl -w "\\nTime Total: %{time_total}s\\nTime Connect: %{time_connect}s\\n" http://localhost:8000/api/adw-monitor

# Check WebSocket with browser DevTools
# 1. Open DevTools -> Network tab
# 2. Filter by "WS" (WebSocket)
# 3. Click on the WebSocket connection
# 4. View "Frames" to see messages

# Test with multiple concurrent requests
for i in {1..10}; do curl -s http://localhost:8000/api/adw-monitor & done; wait
```

## Expected Behavior

### WebSocket Connection Flow
1. Client connects to `/ws/adw-monitor`
2. Server sends initial workflow state
3. Server broadcasts updates when workflow states change
4. Client receives updates and re-renders UI smoothly
5. On disconnect, client attempts exponential backoff reconnection
6. On persistent failure, client falls back to polling

### Animation Timing
- **Loading skeleton**: 200-500ms shimmer animation
- **Fade-in transition**: 300ms ease-in-out
- **Status change**: 200ms color transition
- **Progress bar**: 500ms smooth interpolation
- **Phase node**: 300ms scale + glow effect

### Error Recovery Timeline
1. Error detected (network timeout, parse error, etc.)
2. User-friendly error message displayed (< 100ms)
3. Retry button shown
4. User clicks retry or auto-retry after 3 seconds
5. Exponential backoff: 1s, 2s, 4s, 8s, max 30s between attempts
6. Success: Resume normal operation
7. Persistent failure: Fall back to polling mode

## Notes

- This test builds upon the basic ADW Monitor test (test_adw_monitor.md)
- Focus on user experience: smoothness, responsiveness, error recovery
- Performance targets based on industry standards (Google Web Vitals, 60fps)
- Accessibility compliance ensures usability for all users
- WebSocket should be the primary transport, polling as fallback only
- All animations should respect user's `prefers-reduced-motion` setting
- Screenshots should capture key states: loading, active, error, recovered
