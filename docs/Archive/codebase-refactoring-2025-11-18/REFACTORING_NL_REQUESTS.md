# Refactoring - Natural Language Requests for WebBuilder

**Purpose:** Submit these requests to the tac-webbuilder frontend to create GitHub issues that trigger ADW workflows

**Date:** 2025-11-18
**Total Requests:** 73 (organized by phase)

---

## How to Use This Document

1. **Copy a request** from below (one at a time)
2. **Paste into webbuilder frontend** NL request form
3. **Submit** - Creates GitHub issue
4. **ADW workflow executes** the task automatically
5. **Mark complete** when merged
6. **Move to next request**

---

## 🚀 Recommended Execution Order

**Start with Phase 2 (Helper Utilities) - Quick wins, no dependencies**

### Phase 2 Order:
1. Request 2.4.1 (Frontend Formatters) - Quickest win
2. Request 2.1.1 (DatabaseManager)
3. Request 2.3.1 (ProcessManager)
4. Request 2.2.1 (LLMClientManager)

Then continue with Phase 1 (Server Services extraction).

---

# Phase 2: Helper Utilities (START HERE!)

## Request 2.4.1: Create Frontend Formatters Module

```
Create a comprehensive frontend formatters utility module at app/client/src/utils/formatters.ts with 14 reusable formatting functions.

Extract and consolidate duplicate formatting logic currently scattered across WorkflowHistoryCard.tsx (lines 17-100), SimilarWorkflowsComparison.tsx, TokenBreakdownChart.tsx, CostBreakdownChart.tsx, and CostVisualization.tsx.

Functions needed:
- Date/time: formatDate(), formatDuration(), formatRelativeTime()
- Numbers: formatCost(), formatNumber(), formatPercentage(), formatTokenCount()
- Data: formatBytes(), truncateText()
- Workflow-specific: calculateBudgetDelta(), calculateCacheSavings(), getStatusColor(), getClassificationColor(), transformToPhaseCosts()

After creating formatters.ts, migrate all 5 components to use these utilities and create comprehensive tests in app/client/src/utils/__tests__/formatters.test.ts.

Acceptance Criteria:
- formatters.ts created with all 14 functions
- All 5 components migrated to use formatters
- Tests achieve >80% coverage
- No visual regressions in UI
- 50+ lines of duplicate formatting code eliminated
- All existing component tests still pass

Files to create:
- app/client/src/utils/formatters.ts
- app/client/src/utils/__tests__/formatters.test.ts

Files to update:
- app/client/src/components/WorkflowHistoryCard.tsx
- app/client/src/components/SimilarWorkflowsComparison.tsx
- app/client/src/components/TokenBreakdownChart.tsx
- app/client/src/components/CostBreakdownChart.tsx
- app/client/src/components/CostVisualization.tsx

Estimated effort: 4-5 hours
Complexity: Low
```

---

## Request 2.1.1: Create DatabaseManager Module

```
Create a centralized database connection manager at app/server/core/db_manager.py to eliminate 25+ duplicated sqlite3.connect() patterns across the codebase.

The DatabaseManager should provide:
- Context manager for automatic connection lifecycle (commit/rollback/close)
- Connection pooling for efficiency
- Automatic retry logic for SQLITE_BUSY errors
- Consistent row factory (sqlite3.Row)
- Centralized DB path configuration

Base the implementation on the good pattern from workflow_history.py line 184 (get_db_connection context manager).

Acceptance Criteria:
- DatabaseManager class created with get_connection() context manager
- Supports configurable db_path (default: "db/database.db")
- Automatic commit on success, rollback on error
- Retry logic for locked database (max 3 retries, 100ms delay)
- Connection pooling implemented
- Comprehensive tests with >80% coverage

Files to create:
- app/server/core/db_manager.py (~100 lines)
- app/server/tests/core/test_db_manager.py

Test scenarios needed:
- Successful connection and commit
- Automatic rollback on error
- Retry on SQLITE_BUSY
- Row factory configuration
- Connection cleanup

Do NOT migrate files yet - just create the manager and tests.

Estimated effort: 4-6 hours
Complexity: Low
```

---

## Request 2.1.2: Migrate server.py to DatabaseManager

```
Migrate app/server/server.py to use the DatabaseManager created in Request 2.1.1.

Replace 4 manual sqlite3.connect() calls with DatabaseManager.get_connection():
- Line 596 (in health_check function)
- Line 664 (in get_system_status function)
- Line 1801 (in delete_table function)
- Line 1836 (in export_table function)

Pattern to replace:
OLD:
```python
conn = sqlite3.connect("db/database.db")
cursor = conn.cursor()
try:
    # ... operations ...
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
finally:
    conn.close()
```

NEW:
```python
from core.db_manager import DatabaseManager
db = DatabaseManager()

with db.get_connection() as conn:
    cursor = conn.cursor()
    # ... operations ...
```

Acceptance Criteria:
- All 4 sqlite3.connect() calls in server.py replaced
- Import DatabaseManager added at top of file
- All functionality unchanged (health checks, table operations work)
- All existing tests pass
- No performance degradation

Files to update:
- app/server/server.py (4 locations)

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 2.1.3: Migrate Core Modules to DatabaseManager

```
Migrate file_processor.py, sql_processor.py, and insights.py to use DatabaseManager.

Files and locations:
1. app/server/core/file_processor.py - 3 occurrences (lines 57, 129, 289)
2. app/server/core/sql_processor.py - 2 occurrences (lines 16, 64)
3. app/server/core/insights.py - 1 occurrence (line 16)

Total: 6 manual sqlite3.connect() calls to replace with DatabaseManager pattern.

Acceptance Criteria:
- All 6 sqlite3.connect() calls replaced with DatabaseManager
- Import statements updated
- All existing tests pass
- No functional changes
- Error handling preserved

Files to update:
- app/server/core/file_processor.py
- app/server/core/sql_processor.py
- app/server/core/insights.py

Note: workflow_history.py and adw_lock.py already have good context managers, so they can be migrated later if needed.

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 2.1.4: DatabaseManager Integration Tests

```
Create comprehensive integration tests for DatabaseManager usage across all migrated files.

Test scenarios:
1. Connection pooling works across multiple requests
2. Retry logic handles database locks correctly
3. Rollback works when exceptions occur
4. Row factory provides dict-like access
5. No connection leaks (all connections properly closed)
6. Performance benchmarks (should be same or better than manual connections)

Acceptance Criteria:
- Integration test suite created
- Tests cover all migrated modules (server.py, file_processor.py, sql_processor.py, insights.py)
- Test database locks and retries
- Test concurrent connections
- All tests pass
- Coverage >80% for DatabaseManager

Files to create:
- app/server/tests/integration/test_db_manager_integration.py

Estimated effort: 2 hours
Complexity: Medium
```

---

## Request 2.3.1: Create ProcessManager Module

```
Create a centralized subprocess management utility at app/server/core/process_manager.py to eliminate 12+ duplicated subprocess.run() and subprocess.Popen() patterns in server.py.

The ProcessManager should provide:
- check_process_running(pattern: str) -> bool - Consolidates 3 "ps aux" grep patterns
- github_api_call(endpoint: str, method: str = "GET") -> dict - Consolidates 4 "gh api" calls
- start_background_service(cmd: list, cwd: str = None) -> subprocess.Popen - Standardizes background service starts
- Centralized timeout configuration
- Standardized error handling and logging
- Output parsing utilities

Current duplicate patterns in server.py:
- subprocess.run(["ps", "aux"], ...) - Lines 725-730, 946-950, 1097-1102 (3×)
- subprocess.run(["gh", "api", ...], timeout=5) - Lines 756-761, 985-990, 1125-1130, 1149-1154 (4×)
- subprocess.Popen(..., stdout=DEVNULL, stderr=DEVNULL) - Lines 879-885, 936-941 (2×)

Acceptance Criteria:
- ProcessManager class created with 3 main utility methods
- Standardized timeout handling (configurable, default 5s)
- Proper error handling and logging
- Output parsing for JSON responses
- Process cleanup utilities
- Comprehensive tests with mocked subprocess calls >80% coverage

Files to create:
- app/server/core/process_manager.py (~150 lines)
- app/server/tests/core/test_process_manager.py

Test with mocked subprocess to avoid actual process execution.

Estimated effort: 3-4 hours
Complexity: Medium
```

---

## Request 2.3.2: Migrate server.py to ProcessManager

```
Migrate app/server/server.py to use ProcessManager created in Request 2.3.1.

Replace 12 subprocess calls with ProcessManager utilities:

Process checks (3×):
- Lines 725-730: Replace with ProcessManager.check_process_running("cloudflared tunnel run")
- Lines 946-950: Replace with ProcessManager.check_process_running("cloudflared tunnel run")
- Lines 1097-1102: Replace with ProcessManager.check_process_running("cloudflared tunnel run")

GitHub API calls (4×):
- Lines 756-761: Replace with ProcessManager.github_api_call(f"repos/{repo}/hooks/{webhook_id}/deliveries")
- Lines 985-990: Replace with ProcessManager.github_api_call(f"repos/{repo}/hooks/{webhook_id}/deliveries")
- Lines 1125-1130: Replace with ProcessManager.github_api_call(f"repos/{repo}/hooks/{webhook_id}/deliveries", params={"per_page": 5})
- Lines 1149-1154: Replace with ProcessManager.github_api_call(endpoint, method="POST")

Background service starts (2×):
- Lines 879-885: Replace with ProcessManager.start_background_service(["uv", "run", "adw_triggers/trigger_webhook.py"], cwd=adws_dir)
- Lines 936-941: Replace with ProcessManager.start_background_service(["cloudflared", "tunnel", "run", ...])

Other subprocess calls (3×):
- Lines 862-866: lsof check
- Lines 926-929: pkill
- Lines 1084-1092: bash command

Acceptance Criteria:
- All 12 subprocess calls replaced with ProcessManager
- Import ProcessManager added
- All health checks still work
- Service start/stop still works
- All tests pass
- Code is more readable

Files to update:
- app/server/server.py

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 2.3.3: ProcessManager Integration Tests

```
Create integration tests for ProcessManager usage in server.py.

Test scenarios:
1. Process detection works correctly
2. GitHub API calls handle errors gracefully
3. Background services start and can be stopped
4. Timeout handling works
5. Error logging is comprehensive
6. No zombie processes left behind

Acceptance Criteria:
- Integration test suite created
- Tests use real subprocess calls (not mocked) for process checks
- Tests mock GitHub API to avoid real API calls
- Tests verify process cleanup
- All tests pass

Files to create:
- app/server/tests/integration/test_process_manager_integration.py

Estimated effort: 2 hours
Complexity: Medium
```

---

## Request 2.2.1: Create LLMClientManager Module

```
Create a centralized LLM client manager at app/server/core/llm_client_manager.py to eliminate 6+ duplicated API client initializations and routing logic.

The LLMClientManager should provide:
- Singleton pattern for OpenAI and Anthropic client reuse
- Automatic routing logic (OpenAI for SQL, Anthropic for analysis)
- Centralized API key validation
- Unified error handling
- Prompt formatting utilities
- Cost tracking helpers

Current duplicate patterns:
- API key validation + client init in nl_processor.py (lines 37, 104)
- API key validation + client init in llm_processor.py (lines 20, 159)
- Routing logic duplicated in llm_processor.py (lines 254-268, 270-288)

LLMClientManager features:
- get_client(provider: str = "auto") -> OpenAI | Anthropic
- Auto-routing: "auto" picks best provider based on task
- Client caching/reuse (singleton instances)
- Centralized error messages
- format_schema_for_prompt() utility
- track_usage() for cost monitoring

Acceptance Criteria:
- LLMClientManager class created (~120 lines)
- Singleton pattern implemented for both clients
- Routing logic centralized
- API key validation centralized
- Comprehensive tests with mocked API clients >80% coverage
- No real API calls in tests

Files to create:
- app/server/core/llm_client_manager.py
- app/server/tests/core/test_llm_client_manager.py

Estimated effort: 4-6 hours
Complexity: Medium
```

---

## Request 2.2.2: Migrate NL and LLM Processors to LLMClientManager

```
Migrate nl_processor.py and llm_processor.py to use LLMClientManager created in Request 2.2.1.

Files and locations:
1. app/server/core/nl_processor.py
   - Lines 37: Replace Anthropic client init with LLMClientManager.get_client("anthropic")
   - Lines 104: Replace second Anthropic client init with LLMClientManager.get_client("anthropic")

2. app/server/core/llm_processor.py
   - Lines 20: Replace OpenAI client init with LLMClientManager.get_client("openai")
   - Lines 159: Replace second OpenAI client init with LLMClientManager.get_client("openai")
   - Lines 254-288: Replace routing logic with LLMClientManager.get_client("auto")

Total: 6 client initializations to replace.

Pattern to replace:
OLD:
```python
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")
client = OpenAI(api_key=api_key)
```

NEW:
```python
from core.llm_client_manager import LLMClientManager
client = LLMClientManager.get_client("openai")
```

Acceptance Criteria:
- All 6 client initializations replaced
- Routing logic simplified
- API key validation removed (handled by manager)
- All existing tests pass
- LLM calls still work correctly
- No functional changes

Files to update:
- app/server/core/nl_processor.py
- app/server/core/llm_processor.py

Estimated effort: 1-2 hours
Complexity: Low
```

---

## Request 2.2.3: LLMClientManager Integration Tests

```
Create integration tests for LLMClientManager usage across nl_processor and llm_processor.

Test scenarios:
1. Client instances are reused (singleton pattern works)
2. Routing logic picks correct provider
3. API key validation works
4. Error handling is consistent
5. Multiple requests use same client instance (no re-initialization)
6. Cost tracking works if implemented

Acceptance Criteria:
- Integration test suite created
- Tests mock API responses (no real API calls)
- Tests verify singleton behavior
- Tests verify routing logic
- All tests pass

Files to create:
- app/server/tests/integration/test_llm_client_manager_integration.py

Estimated effort: 2 hours
Complexity: Medium
```

---

# Phase 1: Server Services Extraction

## Request 1.2.1: Create Background Tasks Manager Module

```
Create a background tasks manager service at app/server/services/background_tasks.py to extract the 3 watcher functions from server.py.

Extract from server.py:
- watch_workflows() (lines 272-297) - Watches agents/ directory, polls every 10s
- watch_routes() (lines 299-324) - Watches FastAPI routes, polls every 10s
- watch_workflow_history() (lines 394-420) - Watches workflow history DB, polls every 10s

All three functions follow identical pattern:
- while True loop with asyncio.sleep(interval)
- Check connection count before processing
- Broadcast via WebSocket manager
- Handle asyncio.CancelledError for graceful shutdown

Create BackgroundTaskManager class that:
- Wraps all 3 watcher functions
- Provides start_all() and stop_all() lifecycle methods
- Takes websocket_manager and workflow_service as dependencies
- Configurable watch_interval (default 10s, 2s for testing)
- Tracks running tasks for cleanup

Acceptance Criteria:
- BackgroundTaskManager class created (~150 lines)
- All 3 watchers extracted and wrapped
- Lifecycle management (start/stop) implemented
- Graceful shutdown on cancellation
- No WebSocket manager or workflow service logic duplicated

Files to create:
- app/server/services/background_tasks.py

Do NOT integrate into server.py yet - just create the module.

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 1.2.2: Create Background Tasks Tests

```
Create comprehensive tests for BackgroundTaskManager created in Request 1.2.1.

Test scenarios:
1. start_all() creates 3 background tasks
2. stop_all() cancels all tasks and clears task list
3. Each watcher broadcasts to WebSocket manager when data changes
4. Watchers don't broadcast when data unchanged
5. Watchers handle cancellation gracefully
6. Configurable watch_interval works
7. No memory leaks in long-running watchers (run for 30s, check memory)

Use mocked dependencies:
- Mock ConnectionManager for WebSocket broadcasts
- Mock WorkflowService for data fetching
- asyncio testing for background task lifecycle

Acceptance Criteria:
- Comprehensive test suite created
- All 3 watchers tested independently
- Lifecycle (start/stop) tested
- Memory leak test included
- Tests pass with >80% coverage
- Tests run quickly (<5s total)

Files to create:
- app/server/tests/services/test_background_tasks.py

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 1.2.3: Integrate Background Tasks into server.py

```
Integrate BackgroundTaskManager into server.py, replacing the inline watcher functions.

Current state (server.py lines 114-138):
- lifespan() context manager starts 3 tasks manually
- watch_workflows(), watch_routes(), watch_workflow_history() defined inline (lines 272-420)

New state:
- Import BackgroundTaskManager
- Create instance in lifespan startup
- Call task_manager.start_all() on startup
- Call task_manager.stop_all() on shutdown
- Remove inline watcher function definitions

Changes:
1. Add import: from services.background_tasks import BackgroundTaskManager
2. Update lifespan() to use BackgroundTaskManager
3. Remove watch_workflows() (lines 272-297)
4. Remove watch_routes() (lines 299-324)
5. Remove watch_workflow_history() (lines 394-420)

Acceptance Criteria:
- BackgroundTaskManager imported and integrated
- lifespan() uses task_manager.start_all() / stop_all()
- All 3 inline watcher functions removed
- WebSocket broadcasts still work
- Background tasks start on server startup
- Background tasks stop gracefully on shutdown
- All existing tests pass
- Server behavior unchanged

Files to update:
- app/server/server.py (lines 114-138, 272-420)

Estimated effort: 1 hour
Complexity: Low
```

---

## Request 1.2.4: Background Tasks Performance Tests

```
Create performance and stability tests for BackgroundTaskManager in production-like conditions.

Test scenarios:
1. Memory usage over 5 minutes of operation (should be stable)
2. CPU usage is reasonable (<5% average)
3. Broadcast latency is acceptable (<100ms)
4. Tasks recover from WebSocket connection errors
5. Tasks handle rapid data changes (stress test with 100 updates/sec)
6. No task leaks after multiple start/stop cycles

Performance benchmarks:
- Memory should not grow >10MB over 5 minutes
- CPU usage <5% average
- Broadcast latency <100ms p95
- Task cleanup completes in <1s

Acceptance Criteria:
- Performance test suite created
- Benchmarks measured and pass thresholds
- Stress tests pass
- Memory leak detection passes
- All tests pass

Files to create:
- app/server/tests/services/test_background_tasks_performance.py

Estimated effort: 1 hour
Complexity: Low
```

---

## Request 1.3.1: Create Workflow Service Module - Core Functions

```
Create a workflow service at app/server/services/workflow_service.py to centralize all workflow data operations.

Extract core data functions from server.py:
- get_workflows_data() (lines 167-230) - Scans agents/ directory, parses adw_state.json files
- get_workflow_history_data() (lines 326-392) - Fetches from DB with 10s caching

Create WorkflowService class with:
- __init__(workflows_dir: str = "agents") - Configurable workflows directory
- get_workflows() -> List[WorkflowExecution] - Scans and returns workflows
- get_workflow_by_id(adw_id: str) -> Optional[WorkflowExecution]
- get_workflow_costs(adw_id: str) -> Optional[CostData]
- get_history(limit, offset, status_filter, search_query) -> WorkflowHistoryResponse
- _cache management for get_history (10s TTL)

Dependencies:
- Uses workflow_history module for get_history()
- Parses adw_state.json files directly
- Validates issue numbers
- Determines current phase from directory structure

Acceptance Criteria:
- WorkflowService class created (~450 lines)
- Both core functions extracted and wrapped
- Caching implemented for get_history()
- All workflow parsing logic preserved
- Type hints for all methods
- Docstrings for all public methods

Files to create:
- app/server/services/workflow_service.py

Do NOT create tests or integrate yet - just the service module.

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 1.3.2: Add Workflow Service API Endpoint Methods

```
Extend WorkflowService created in Request 1.3.1 with methods for API endpoints currently in server.py.

Add these methods to WorkflowService:
1. get_workflow_catalog() - From server.py lines 1721-1789
2. get_workflows_batch(adw_ids: List[str]) - From server.py lines 1413-1473
3. get_workflow_costs_detailed(adw_id: str) - Enhanced version from lines 1199-1221

Each method should:
- Extract business logic from endpoint handlers
- Return structured data (not FastAPI responses)
- Include error handling
- Log appropriately

Acceptance Criteria:
- 3 new methods added to WorkflowService
- Business logic extracted from server.py
- Methods return data (not HTTP responses)
- Error handling included
- Type hints and docstrings added

Files to update:
- app/server/services/workflow_service.py

Estimated effort: 2 hours
Complexity: Medium
```

---

## Request 1.3.3: Add Workflow History Service Methods

```
Extend WorkflowService with workflow history-specific methods.

Add these methods to WorkflowService:
1. resync_workflow_history() - From server.py lines 1342-1411
   - Triggers full workflow history resync
   - Returns sync statistics

2. get_workflow_analytics_summary() - Helper for analytics endpoints
   - Aggregates workflow metrics
   - Provides trends and insights

Both methods should:
- Use workflow_history module internally
- Handle errors gracefully
- Return structured data
- Log operations

Acceptance Criteria:
- 2 new methods added to WorkflowService
- Resync functionality preserved
- Analytics helper implemented
- Error handling included
- Logs operations appropriately

Files to update:
- app/server/services/workflow_service.py

Estimated effort: 2 hours
Complexity: Medium
```

---

## Request 1.3.4: Create Workflow Service Tests

```
Create comprehensive tests for WorkflowService created in Requests 1.3.1-1.3.3.

Test scenarios:
1. get_workflows() scans directory and parses state files
2. get_workflow_by_id() returns correct workflow
3. get_workflow_costs() parses conversation logs correctly
4. get_history() caching works (10s TTL)
5. get_workflow_catalog() returns all workflows
6. get_workflows_batch() handles multiple IDs
7. resync_workflow_history() triggers sync and returns stats
8. Error handling for missing files, invalid JSON, etc.

Use temporary test directories and mock data:
- Create temp agents/ directory with test workflows
- Mock workflow_history module calls
- Test with valid and invalid state files

Acceptance Criteria:
- Comprehensive test suite created
- All methods tested
- Edge cases covered (missing files, invalid JSON)
- Caching behavior verified
- Tests pass with >80% coverage

Files to create:
- app/server/tests/services/test_workflow_service.py

Estimated effort: 2-3 hours
Complexity: Medium
```

---

## Request 1.3.5: Integrate Workflow Service into server.py

```
Integrate WorkflowService into server.py, replacing inline workflow data functions and updating all related endpoints.

Steps:
1. Import WorkflowService
2. Create instance: workflow_service = WorkflowService()
3. Update get_workflows_data() calls to workflow_service.get_workflows()
4. Update get_workflow_history_data() calls to workflow_service.get_history()
5. Update endpoints to use workflow_service methods

Endpoints to update:
- GET /api/workflows (line 1709) → workflow_service.get_workflows()
- GET /api/workflows/{adw_id}/costs (line 1199) → workflow_service.get_workflow_costs()
- GET /api/workflow-catalog (line 1721) → workflow_service.get_workflow_catalog()
- POST /api/workflows/batch (line 1413) → workflow_service.get_workflows_batch()
- GET /api/workflow-history (line 1302) → workflow_service.get_history()
- POST /api/workflow-history/resync (line 1342) → workflow_service.resync_workflow_history()

Remove from server.py:
- get_workflows_data() function (lines 167-230)
- get_workflow_history_data() function (lines 326-392)

Acceptance Criteria:
- WorkflowService imported and instantiated
- All 6 endpoints updated to use workflow_service
- Inline functions removed
- All endpoints still work correctly
- Background tasks use workflow_service
- All existing tests pass

Files to update:
- app/server/server.py

Estimated effort: 1 hour
Complexity: Low
```

---

**[Continue with remaining workflows 1.4.1 through 1.10.3, Phase 3, Phase 4, and Phase 5...]**

---

## Status Tracking

Mark requests as you submit them:

### Phase 2: Helper Utilities (Recommended Start)
- [ ] 2.4.1 - Frontend Formatters
- [ ] 2.1.1 - DatabaseManager Module
- [ ] 2.1.2 - Migrate server.py to DatabaseManager
- [ ] 2.1.3 - Migrate Core Modules to DatabaseManager
- [ ] 2.1.4 - DatabaseManager Integration Tests
- [ ] 2.3.1 - ProcessManager Module
- [ ] 2.3.2 - Migrate server.py to ProcessManager
- [ ] 2.3.3 - ProcessManager Integration Tests
- [ ] 2.2.1 - LLMClientManager Module
- [ ] 2.2.2 - Migrate to LLMClientManager
- [ ] 2.2.3 - LLMClientManager Integration Tests

### Phase 1: Server Services
- [ ] 1.2.1 - Background Tasks Module
- [ ] 1.2.2 - Background Tasks Tests
- [ ] 1.2.3 - Integrate Background Tasks
- [ ] 1.2.4 - Background Tasks Performance Tests
- [ ] 1.3.1 - Workflow Service Core
- [ ] 1.3.2 - Workflow Service API Methods
- [ ] 1.3.3 - Workflow History Methods
- [ ] 1.3.4 - Workflow Service Tests
- [ ] 1.3.5 - Integrate Workflow Service

---

**Total:** 73 NL requests (showing first 19 above)

**Next:** I can create the remaining 54 requests (Health Service, Service Controller, Analytics Service, Core Module Splits, Frontend Refactoring, Import Structure) if you'd like to see them all.
