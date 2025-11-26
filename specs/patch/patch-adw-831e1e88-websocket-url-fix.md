# Patch: Fix WebSocket URL to Use Vite Proxy

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #1: WebSocket connection fails because the URL is hardcoded to ws://localhost:8000/ws/adw-monitor in AdwMonitorCard.tsx:21, but the backend is running on port 9111. The frontend cannot connect to the WebSocket, preventing all real-time updates from working. Resolution: Change line 21 in app/client/src/components/AdwMonitorCard.tsx from \`const wsUrl = \`${wsProtocol}//${window.location.hostname}:8000/ws/adw-monitor\`;\` to use a relative path that goes through the Vite proxy: \`const wsUrl = \`/ws/adw-monitor\`;\` or construct it properly to use the proxy. Severity: blocker`

## Issue Summary
**Original Spec:** /Users/Warmonger0/tac/tac-webbuilder/trees/adw-831e1e88/specs/issue-110-adw-adw-831e1e88-sdlc_planner-phase-3-polish-integration.md

**Issue:** The WebSocket connection URL in AdwMonitorCard.tsx:21 is hardcoded to `ws://localhost:8000/ws/adw-monitor`, but the backend server runs on port 9111 (as specified in .adw-context.json). The Vite dev server has a proxy configured to forward `/ws` requests to the backend, but the hardcoded URL bypasses this proxy entirely, causing connection failures.

**Solution:** Change line 21 to use a relative WebSocket URL `/ws/adw-monitor` instead of constructing an absolute URL with protocol and port. This allows the connection to go through Vite's proxy configuration, which properly routes to the backend on port 9111.

## Files to Modify

- `app/client/src/components/AdwMonitorCard.tsx` - Update WebSocket URL construction (lines 19-21)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update WebSocket URL in AdwMonitorCard
- Remove the `wsProtocol` variable (line 20) as it's no longer needed
- Replace the absolute WebSocket URL construction with a relative path
- Change line 21 from: `const wsUrl = \`${wsProtocol}//${window.location.hostname}:8000/ws/adw-monitor\`;`
- To: `const wsUrl = '/ws/adw-monitor';`
- This allows the WebSocket connection to go through Vite's proxy configuration, which routes `/ws` requests to the backend server on the correct port

### Step 2: Verify the fix
- Ensure the WebSocket connection now uses the relative path
- The connection will be handled by Vite's proxy: `/ws` → `ws://localhost:9111/ws` (from vite.config.ts)
- Remove any references to the old `wsProtocol` variable

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Type Check**: `cd app/client && bun tsc --noEmit` - Verify no TypeScript errors
2. **Lint Check**: `cd app/client && bun run lint` - Verify code quality standards
3. **Unit Tests**: `cd app/client && bun run test` - Verify no test failures
4. **Build Test**: `cd app/client && bun run build` - Verify production build succeeds
5. **Backend Tests**: `cd app/server && uv run pytest` - Verify no backend regressions
6. **Manual Verification**: Start the application and verify WebSocket connection indicator shows "Connected" status in the ADW Monitor Card

## Patch Scope
**Lines of code to change:** 2 (remove line 20, modify line 21)
**Risk level:** low
**Testing required:** Type checking, unit tests, manual verification of WebSocket connection in browser DevTools Network tab
