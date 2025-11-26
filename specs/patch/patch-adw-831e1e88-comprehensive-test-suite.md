# Patch: Comprehensive Test Suite for ADW Monitor Phase 3

## Metadata
adw_id: `adw-831e1e88`
review_change_request: `Issue #6: Unit and integration tests were not implemented. The spec required comprehensive test coverage including: backend WebSocket tests, frontend component tests, integration tests for full WebSocket flow, and performance tests. Test files mentioned in the documentation do not exist. Resolution: Create comprehensive test suite: 1) Create app/server/tests/services/test_websocket_adw_monitor.py for backend WebSocket tests, 2) Create app/client/src/components/__tests__/AdwMonitorCard.phase3.test.tsx for frontend tests, 3) Create app/server/tests/integration/test_adw_monitor_websocket.py for integration tests, 4) Add performance benchmarks validating <200ms API response and <50ms WebSocket latency. Severity: blocker`

## Issue Summary
**Original Spec:** specs/issue-110-adw-adw-831e1e88-sdlc_planner-phase-3-polish-integration.md
**Issue:** Test files referenced in Phase 3 documentation do not exist, resulting in zero test coverage for WebSocket functionality, frontend component integration, full WebSocket flow, and performance benchmarks.
**Solution:** Create four comprehensive test files covering backend WebSocket unit tests, frontend component tests, integration tests for the complete WebSocket flow, and performance validation benchmarks.

## Files to Modify
Use these files to implement the patch:

### New Test Files to Create
- `app/server/tests/services/test_websocket_adw_monitor.py` - Backend WebSocket unit tests
- `app/client/src/components/__tests__/AdwMonitorCard.phase3.test.tsx` - Frontend component tests
- `app/server/tests/integration/test_adw_monitor_websocket.py` - Integration tests for full WebSocket flow
- `app/server/tests/performance/test_adw_monitor_performance.py` - Performance benchmarks (new directory)

### Supporting Test Infrastructure
- `app/server/tests/conftest.py` - Add performance test fixtures if needed
- `app/client/vitest.config.ts` - Verify configuration supports WebSocket mocking

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Backend WebSocket Unit Tests
Create `app/server/tests/services/test_websocket_adw_monitor.py` with comprehensive coverage:
- Test `/ws/adw-monitor` endpoint connection/disconnection lifecycle
- Test initial state broadcast on client connection
- Test state change detection and targeted broadcast mechanism
- Test broadcast to multiple concurrent clients
- Test error handling for connection failures and malformed data
- Test cleanup of disconnected clients during broadcast
- Follow existing pattern from `test_websocket_manager.py` using pytest-asyncio and mocks
- Ensure 100% coverage of WebSocket-specific ADW monitor logic

### Step 2: Create Frontend Component Tests
Create `app/client/src/components/__tests__/AdwMonitorCard.phase3.test.tsx` with Phase 3 feature coverage:
- Test WebSocket connection initialization in AdwMonitorCard component
- Test real-time state updates via WebSocket messages
- Test fallback to polling when WebSocket connection fails
- Test connection status indicator states (connected, reconnecting, degraded)
- Test error boundary behavior for component crashes
- Test animation triggers on status changes (use jest timers)
- Test exponential backoff reconnection logic (1s, 2s, 4s, 8s, max 30s)
- Mock useReliableWebSocket hook with vitest.mock
- Follow existing test patterns from `RequestForm.test.tsx` and `WorkflowHistoryCard.test.tsx`

### Step 3: Create Integration Tests for Full WebSocket Flow
Create `app/server/tests/integration/test_adw_monitor_websocket.py` with end-to-end coverage:
- Test complete connection → state change → broadcast → client update cycle
- Test multiple concurrent client connections receiving updates
- Test WebSocket reconnection after temporary server unavailability
- Test graceful degradation to polling on persistent WebSocket failures
- Test message ordering and deduplication for rapid state changes
- Use actual WebSocket connections (not mocks) with FastAPI TestClient
- Follow pattern from `test_adw_monitor_endpoint.py` and `test_server_startup.py`
- Ensure tests validate both backend and client-side behavior

### Step 4: Create Performance Benchmarks
Create `app/server/tests/performance/test_adw_monitor_performance.py` with performance validation:
- Test API response time for `/api/adw-monitor` endpoint (<200ms target)
  - Measure over 100 consecutive requests
  - Calculate mean, median, p95, p99 response times
  - Assert p95 < 200ms
- Test WebSocket message latency (<50ms target)
  - Measure time from state change to client message receipt
  - Test with 1, 5, 10, 20 concurrent clients
  - Assert p95 latency < 50ms for all scenarios
- Test frontend render performance (<16ms target for 60fps)
  - Create benchmark measuring component re-render time
  - Test with 10, 25, 50 workflow items
  - Assert render time < 16ms for reasonable workflow counts
- Use pytest-benchmark for timing measurements
- Add performance test execution to validation commands

### Step 5: Update Test Infrastructure
Update supporting files to enable new tests:
- Add pytest-benchmark to `app/server/pyproject.toml` dev dependencies if not present
- Create `app/server/tests/performance/__init__.py` for new test directory
- Verify `app/client/vitest.config.ts` supports WebSocket mocking (likely already configured)
- Add performance test execution to `.claude/commands/test.md` validation sequence
- Document performance test expectations in test docstrings

## Validation
Execute every command to validate the patch is complete with zero regressions.

### Backend Test Validation
```bash
cd app/server && uv run pytest tests/services/test_websocket_adw_monitor.py -v
cd app/server && uv run pytest tests/integration/test_adw_monitor_websocket.py -v
cd app/server && uv run pytest tests/performance/test_adw_monitor_performance.py -v --benchmark-only
```

### Frontend Test Validation
```bash
cd app/client && bun run test AdwMonitorCard.phase3.test.tsx
```

### Full Test Suite Validation
```bash
cd app/server && uv run pytest tests/ -v --tb=short
cd app/client && bun tsc --noEmit
cd app/client && bun run build
```

### Code Quality Validation
```bash
cd app/server && uv run ruff check .
```

### Performance Benchmark Validation
```bash
# Start server in background for performance tests
cd app/server && uv run python main.py &
sleep 5

# Run performance benchmarks
cd app/server && uv run pytest tests/performance/test_adw_monitor_performance.py -v --benchmark-only

# Verify API response time < 200ms
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/adw-monitor

# Stop background server
pkill -f "python main.py"
```

## Patch Scope
**Lines of code to change:** ~800 (all new test code)
- test_websocket_adw_monitor.py: ~300 lines
- AdwMonitorCard.phase3.test.tsx: ~250 lines
- test_adw_monitor_websocket.py: ~200 lines
- test_adw_monitor_performance.py: ~150 lines

**Risk level:** low
- Only adding new test files, no production code changes
- Tests validate existing functionality
- Performance benchmarks establish baseline metrics

**Testing required:** Self-validating
- New tests validate Phase 3 functionality
- Existing test suite ensures no regressions
- Performance benchmarks confirm <200ms API and <50ms WebSocket targets
