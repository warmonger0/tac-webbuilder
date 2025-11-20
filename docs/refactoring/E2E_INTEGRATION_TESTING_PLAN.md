# Task: Implement Comprehensive E2E Integration Testing

## Context
The tac-webbuilder project currently has 411 unit tests with excellent coverage, but lacks comprehensive end-to-end (E2E) integration testing for critical workflows.

## Current Testing State

### What Exists:
1. **Integration Tests (Limited)**: `tests/integration/test_server_startup.py` - Only 6 tests covering server imports, launch script consistency, and config validation
2. **API Endpoint Tests (Partial)**: `tests/test_workflow_history.py` has 5 endpoint tests but they're SKIPPED (lines 946-1049)
3. **Unit Tests**: 411 passing unit tests with mocked dependencies

### Critical Gaps:

**❌ No E2E tests for core workflows:**
- Natural language → SQL generation → execution → results
- GitHub issue creation: NL input → API → Database → GitHub API
- ADW workflow execution: trigger → isolated worktree → completion
- WebSocket real-time updates
- Frontend ↔ Backend integration
- Authentication/authorization flows

**❌ No full-stack integration tests:**
- Frontend (React/Vite) → Backend (FastAPI) → Database (SQLite)
- Real HTTP requests through the full stack
- Multiple services coordinating

**❌ No ADW workflow E2E tests:**
- `adw_sdlc_iso` - Standard SDLC workflow
- `adw_lightweight_iso` - Quick fixes
- `adw_sdlc_complete_iso` - Full workflow with testing
- Git worktree isolation validation
- Concurrent workflow execution testing

## Requirements

### 1. API Endpoint Integration Tests
Create tests using FastAPI's `TestClient` for all major endpoints:
- `/api/query` - Natural language SQL queries
- `/api/create-issue` - GitHub issue creation
- `/api/workflow-history` - Workflow CRUD operations
- `/api/system-status` - Health checks
- `/api/adw/*` - ADW workflow endpoints
- WebSocket endpoints

### 2. Full-Stack E2E Tests
Test complete user journeys:
- User submits NL query → Backend processes → Returns SQL + results
- User creates GitHub issue → ADW triggered → Workflow executes → Results returned
- Real-time workflow updates via WebSocket
- Error handling and edge cases

### 3. ADW Workflow E2E Tests
Test actual ADW execution:
- Workflow isolation in git worktrees
- Concurrent workflow execution (up to 15)
- Port allocation (9100-9114 backend, 9200-9214 frontend)
- Cost tracking and estimation
- Workflow state persistence

### 4. Database Integration Tests
Test real database operations (not mocks):
- Schema migrations
- Concurrent access
- Transaction handling
- Workflow history persistence

## Technical Specifications

**Testing Stack:**
- FastAPI `TestClient` for HTTP endpoint testing
- `pytest-asyncio` for async tests
- Real SQLite database (temporary test DBs)
- Real git operations in temporary directories
- WebSocket testing with `websockets` library

**Test Organization:**
```
tests/
├── integration/
│   ├── test_api_endpoints.py          # NEW
│   ├── test_fullstack_workflows.py    # NEW
│   ├── test_adw_execution.py          # NEW
│   ├── test_websocket_integration.py  # NEW
│   └── test_server_startup.py         # EXISTS
├── e2e/                                # NEW
│   ├── test_nl_to_sql_flow.py
│   ├── test_github_issue_flow.py
│   ├── test_adw_workflows.py
│   └── test_concurrent_workflows.py
```

**Success Criteria:**
- All major API endpoints have integration tests
- At least 3 complete E2E user journeys tested
- ADW workflows can be tested in isolation
- Tests can run in CI/CD without external dependencies
- Test suite completes in <2 minutes
- Zero false positives/flaky tests

## Existing Code References

**Files to Review:**
- `app/server/server.py` - FastAPI app definition
- `app/server/tests/test_workflow_history.py:949-1049` - Skipped endpoint tests (enable and expand these)
- `adws/` - ADW workflow implementations
- `app/server/core/` - Core business logic
- `scripts/launch.sh` - Production server startup

**Example Pattern from Codebase:**
```python
# From test_workflow_history.py (currently skipped)
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/api/resync-cost", json={...})
assert response.status_code == 200
```

## Deliverables

1. **Integration test suite** with >50 new tests covering all API endpoints
2. **E2E test suite** with >20 tests covering complete user journeys
3. **ADW workflow tests** validating isolation and concurrent execution
4. **Documentation** (`docs/TESTING_STRATEGY.md`) explaining test architecture
5. **CI/CD integration** (update test commands if needed)

## Constraints

- Use existing test infrastructure (pytest, fixtures)
- Don't modify production code unless fixing bugs
- Tests must be deterministic (no flaky tests)
- Keep test execution time reasonable (<2 min total)
- Follow existing test patterns and conventions

## Priority

**High** - Integration testing gaps pose risks for production deployments. Unit tests alone don't catch integration issues, API contract violations, or workflow coordination problems.

## Related Documents

- `docs/TEST_FAILURE_FIXES_SUMMARY.md` - Recent test fixes (2025-11-20)
- `docs/refactoring/PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md` - Phase 4 refactoring context
- `app/server/tests/integration/test_server_startup.py` - Existing integration test pattern
