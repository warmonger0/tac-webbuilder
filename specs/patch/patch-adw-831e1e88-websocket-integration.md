# Patch: Implement WebSocket Integration for Real-Time ADW Monitor Updates

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #2: Frontend WebSocket integration was not implemented. The spec required replacing useReliablePolling with useReliableWebSocket for real-time push updates. The card still uses polling-based updates as confirmed by the documentation and code review. Resolution: Implement WebSocket integration in AdwMonitorCard.tsx: 1) Replace useReliablePolling hook with useReliableWebSocket hook connecting to /ws/adw-monitor, 2) Add connection status indicator showing connected/reconnecting/degraded states, 3) Implement fallback to polling on WebSocket failure, 4) Add exponential backoff reconnection logic (1s, 2s, 4s, 8s, max 30s). Severity: blocker`

## Issue Summary
**Original Spec:** specs/issue-110-adw-adw-831e1e88-sdlc_planner-phase-3-polish-integration.md
**Issue:** AdwMonitorCard.tsx still uses useReliablePolling for data updates instead of the required useReliableWebSocket hook. The Phase 3 spec explicitly requires WebSocket integration to /ws/adw-monitor endpoint for real-time push-based updates, eliminating polling overhead and providing instant workflow state changes.
**Solution:** Replace useReliablePolling with useReliableWebSocket hook in AdwMonitorCard.tsx, connecting to /ws/adw-monitor endpoint. The existing useReliableWebSocket implementation already provides exponential backoff reconnection (1s, 2s, 4s, 8s, max 30s), automatic fallback to polling, and connection quality monitoring - exactly what the spec requires.

## Files to Modify
- `app/client/src/components/AdwMonitorCard.tsx` - Replace polling hook with WebSocket hook, update connection status display

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Replace useReliablePolling with useReliableWebSocket
- In `AdwMonitorCard.tsx`, replace the useReliablePolling import with useReliableWebSocket
- Remove the useReliablePolling hook call (lines 17-31)
- Add useReliableWebSocket hook call with:
  - `url`: Construct WebSocket URL dynamically from window.location (ws:// for http://, wss:// for https://) connecting to `/ws/adw-monitor`
  - `queryKey`: `['adw-monitor']` for React Query caching
  - `queryFn`: Use existing `getAdwMonitor` function for fallback polling
  - `onMessage`: Handler that calls setWorkflows, setSummary, and clears errors on successful message
  - `enabled`: `true` (always enabled)
  - `pollingInterval`: `10000` (10 seconds fallback polling)
  - `maxReconnectDelay`: `30000` (30 seconds maximum)
  - `maxReconnectAttempts`: `10` (matches exponential backoff spec: 1s, 2s, 4s, 8s, 16s, 30s, 30s, 30s, 30s, 30s)
- Update state variable references from `pollingState` to `connectionState`

### Step 2: Update Connection Status Indicator
- Update ConnectionStatusIndicator props to use connectionState instead of pollingState:
  - `isConnected`: Use `connectionState.isConnected`
  - `connectionQuality`: Use `connectionState.connectionQuality`
  - `lastUpdated`: Use `connectionState.lastUpdated`
  - `consecutiveErrors`: Remove (not provided by useReliableWebSocket, use `reconnectAttempts` instead)
  - `onRetry`: Remove (useReliableWebSocket handles reconnection automatically)
- Adjust ConnectionStatusIndicator to reflect WebSocket states:
  - Show "Connected" when `connectionState.isConnected === true`
  - Show "Reconnecting..." when `connectionState.reconnectAttempts > 0 && !connectionState.isConnected`
  - Show "Degraded (Polling)" when `connectionState.connectionQuality === 'poor'`
  - Show "Disconnected" when `connectionState.connectionQuality === 'disconnected'`

### Step 3: Update Loading and Connection State Logic
- Update loading state check from `!pollingState.isPolling` to check if `!connectionState.isConnected && workflows.length === 0`
- Ensure the component still displays loading state properly during initial connection
- Verify error handling remains functional with WebSocket onMessage error callback

### Step 4: Verify TypeScript Types
- Ensure AdwMonitorSummary and AdwWorkflowStatus types match the WebSocket message format
- The useReliableWebSocket hook expects messages in format: `{ workflows: AdwWorkflowStatus[], summary: AdwMonitorSummary }`
- Update onMessage handler to destructure the WebSocket message correctly

## Validation
Execute every command to validate the patch is complete with zero regressions.

### TypeScript Validation
1. `cd app/client && bun tsc --noEmit` - Verify no TypeScript errors

### Linting Validation
2. `cd app/client && bun run lint` - Verify ESLint passes

### Build Validation
3. `cd app/client && bun run build` - Verify production build succeeds

### Functional Validation (requires backend running)
4. Verify WebSocket endpoint exists: `grep -r "/ws/adw-monitor" app/server/routes/` - Should return WebSocket route definition
5. Start backend: `cd app/server && uv run python server.py` (background)
6. Start frontend: `cd app/client && bun run dev` (background)
7. Open browser to `http://localhost:9211` and verify:
   - ADW Monitor Card connects via WebSocket (check Network tab, WS filter)
   - Connection status shows "Connected" when WebSocket active
   - Workflows update in real-time without manual polling
   - Connection falls back to polling if WebSocket fails (simulate by stopping backend)
   - Reconnection occurs with exponential backoff when backend restarts
8. Browser DevTools Console verification:
   - Look for `[WS] Connected to ws://localhost:8000/ws/adw-monitor` log
   - Look for `[WS] Reconnecting to...` logs with increasing delays if disconnected
   - Verify no errors related to WebSocket message parsing
9. Stop processes

### Backend Validation
10. `cd app/server && uv run pytest tests/ -v --tb=short` - Run all backend tests to ensure no regressions

## Patch Scope
**Lines of code to change:** ~30 lines (hook replacement + status indicator updates)
**Risk level:** low (useReliableWebSocket already implements all required features - exponential backoff, polling fallback, connection monitoring)
**Testing required:** TypeScript compilation, build verification, WebSocket connection testing, fallback to polling validation, reconnection logic verification
