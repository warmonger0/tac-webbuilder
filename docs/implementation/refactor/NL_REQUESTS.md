# Refactoring Natural Language Requests

**Purpose:** Small, focused refactoring tasks for tac-webbuilder
**Principles:** DRY, Modularity, Cost-Consciousness
**Each Request:** Single ADW workflow (~$1-3 using lightweight/haiku models)

---

## How to Use

1. Copy a request below
2. Paste into webbuilder NL request form
3. Submit to create GitHub issue
4. ADW executes automatically
5. Check off when merged
6. Move to next request

**Recommended Order:** Execute in sequence (Phase 1 → Phase 2 → Phase 3 → Phase 4)

---

# Phase 1: Utility Extraction (DRY Principles)

## ✅ Request 1.1: Extract Database Connection Utility

**Workflow:** `lightweight` (Haiku model)

```
Create a centralized database connection utility at app/server/utils/db_connection.py to eliminate duplicated sqlite3.connect() patterns across the codebase.

CONTEXT:
Currently, 7 files manually create database connections with duplicated error handling:
- server.py (4 instances: lines 596, 664, 1801, 1836)
- insights.py (1 instance: line 16)
- sql_processor.py (2 instances: lines 16, 64)

A good pattern already exists in workflow_history.py lines 182-193 using a context manager.

TASK:
Create app/server/utils/db_connection.py with a context manager that:
- Uses sqlite3.connect() with configurable db_path (default: "db/database.db")
- Sets row_factory to sqlite3.Row for dict-like access
- Automatically commits on success, rollbacks on error
- Properly closes connections in finally block
- Includes basic retry logic for SQLITE_BUSY errors (max 3 retries, 100ms delay)

Base implementation on the existing pattern from workflow_history.py:182-193.

ACCEPTANCE CRITERIA:
- Create app/server/utils/db_connection.py (~80-100 lines)
- Include get_connection() context manager
- Add docstrings explaining usage
- Create app/server/tests/utils/test_db_connection.py with tests for:
  - Successful connection and commit
  - Automatic rollback on error
  - Connection cleanup
  - Row factory configuration
- All tests pass
- No migration of existing code yet (that's a separate task)

FILES TO CREATE:
- app/server/utils/db_connection.py
- app/server/tests/utils/test_db_connection.py

ESTIMATED EFFORT: 2 hours
COMPLEXITY: Low
DRY BENEFIT: Eliminates 7 duplicate patterns (105-140 lines)
```

---

## ✅ Request 1.2: Migrate server.py to Database Connection Utility

**Workflow:** `lightweight` (Haiku model)

```
Migrate app/server/server.py to use the centralized database connection utility created in Request 1.1.

CONTEXT:
server.py has 4 manual sqlite3.connect() calls that should use the new utility:
- Line 596 (health_check function)
- Line 664 (get_system_status function)
- Line 1801 (delete_table function)
- Line 1836 (export_table function)

TASK:
Replace all 4 manual database connections with the db_connection utility.

PATTERN TO REPLACE:
OLD:
```python
conn = sqlite3.connect("db/database.db")
cursor = conn.cursor()
try:
    # operations
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

NEW:
```python
from app.server.utils.db_connection import get_connection

with get_connection() as conn:
    cursor = conn.cursor()
    # operations (no manual commit/rollback/close needed)
```

ACCEPTANCE CRITERIA:
- All 4 sqlite3.connect() calls in server.py replaced
- Import added at top of file
- All health checks still work correctly
- All table operations (delete, export) still work
- All existing tests pass
- No functional changes

FILES TO UPDATE:
- app/server/server.py (4 locations)

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low
DRY BENEFIT: Removes 4 duplicate patterns
```

---

## ✅ Request 1.3: Migrate Core Modules to Database Connection Utility

**Workflow:** `lightweight` (Haiku model)

```
Migrate insights.py and sql_processor.py to use the centralized database connection utility created in Request 1.1.

CONTEXT:
Two core modules have manual sqlite3.connect() calls:
- app/server/core/insights.py (line 16)
- app/server/core/sql_processor.py (lines 16, 64)

TASK:
Replace all 3 manual database connections with the db_connection utility using the same pattern as Request 1.2.

ACCEPTANCE CRITERIA:
- All 3 sqlite3.connect() calls replaced
- Import statements updated
- All existing tests pass
- No functional changes
- Error handling preserved

FILES TO UPDATE:
- app/server/core/insights.py
- app/server/core/sql_processor.py

ESTIMATED EFFORT: 1 hour
COMPLEXITY: Low
DRY BENEFIT: Removes 3 duplicate patterns, completes DB utility migration
```

---

## ✅ Request 1.4: Extract LLM Client Utilities

**Workflow:** `lightweight` (Haiku model)

```
Create a centralized LLM client manager at app/server/utils/llm_clients.py to eliminate duplicated API client initialization across the codebase.

CONTEXT:
Currently, 7 functions manually initialize OpenAI/Anthropic clients with duplicated API key validation:
- llm_processor.py (4 instances: lines 20, 81, 159, 212)
- nl_processor.py (2 instances: lines 37, 104)
- api_quota.py (1 instance: line 18)

Each follows the same pattern:
```python
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")
client = Anthropic(api_key=api_key)
```

TASK:
Create app/server/utils/llm_clients.py with factory functions that:
- Provide get_anthropic_client() function
- Provide get_openai_client() function
- Validate API keys centrally
- Cache client instances (singleton pattern)
- Include clear error messages if keys missing
- Add docstrings with usage examples

IMPLEMENTATION GUIDANCE:
```python
# Module-level cached clients
_anthropic_client = None
_openai_client = None

def get_anthropic_client() -> Anthropic:
    """Get cached Anthropic client with API key validation"""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        _anthropic_client = Anthropic(api_key=api_key)
    return _anthropic_client

def get_openai_client() -> OpenAI:
    """Get cached OpenAI client with API key validation"""
    # Similar pattern
```

ACCEPTANCE CRITERIA:
- Create app/server/utils/llm_clients.py (~100 lines)
- Include get_anthropic_client() and get_openai_client()
- Implement singleton pattern (cached instances)
- Add docstrings
- Create app/server/tests/utils/test_llm_clients.py with tests for:
  - Client initialization
  - API key validation
  - Client caching (same instance returned)
  - Error handling for missing keys
- All tests pass (use mocked API keys)

FILES TO CREATE:
- app/server/utils/llm_clients.py
- app/server/tests/utils/test_llm_clients.py

ESTIMATED EFFORT: 2 hours
COMPLEXITY: Low
DRY BENEFIT: Eliminates 7 duplicate patterns (175-210 lines)
```

---

## ✅ Request 1.5: Migrate LLM Processors to Client Utilities

**Workflow:** `lightweight` (Haiku model)

```
Migrate llm_processor.py, nl_processor.py, and api_quota.py to use the centralized LLM client utilities created in Request 1.4.

CONTEXT:
Three files have 7 total manual client initializations that should use the new utility:
- llm_processor.py: 4 instances
- nl_processor.py: 2 instances
- api_quota.py: 1 instance

TASK:
Replace all manual client initializations with utility function calls.

PATTERN TO REPLACE:
OLD:
```python
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
client = Anthropic(api_key=api_key)
```

NEW:
```python
from app.server.utils.llm_clients import get_anthropic_client

client = get_anthropic_client()
```

ACCEPTANCE CRITERIA:
- All 7 client initializations replaced
- Import statements updated
- API key validation removed (handled by utility)
- All existing tests pass
- LLM calls still work correctly
- No functional changes

FILES TO UPDATE:
- app/server/core/llm_processor.py (4 replacements)
- app/server/core/nl_processor.py (2 replacements)
- app/server/core/api_quota.py (1 replacement)

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low
DRY BENEFIT: Removes 7 duplicate patterns, centralizes client management
```

---

## ✅ Request 1.6: Extract Subprocess Utilities

**Workflow:** `lightweight` (Haiku model)

```
Create a centralized subprocess management utility at app/server/utils/subprocess_utils.py to eliminate duplicated subprocess.run() patterns.

CONTEXT:
Currently, 13+ locations manually execute subprocesses with duplicated error handling:
- server.py (12 instances)
- github_poster.py (3 instances)
- pattern_matcher.py (1 instance)

Common patterns:
1. subprocess.run() with capture_output, text=True, error handling
2. subprocess.Popen() for background services with DEVNULL
3. GitHub CLI (gh) commands with JSON parsing

TASK:
Create app/server/utils/subprocess_utils.py with utility functions:
- run_command(cmd, timeout=30, cwd=None) - standard subprocess execution
- run_gh_command(cmd) - GitHub CLI wrapper with error handling
- start_background_service(cmd, cwd=None) - Popen wrapper for background processes

Each function should:
- Handle subprocess.CalledProcessError
- Handle subprocess.TimeoutExpired
- Return structured results (success, stdout, stderr, returncode)
- Include comprehensive error messages

IMPLEMENTATION GUIDANCE:
```python
from dataclasses import dataclass
import subprocess

@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False

def run_command(cmd: list[str], timeout: int = 30, cwd: str = None) -> CommandResult:
    """Execute command with standard error handling"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            cwd=cwd
        )
        return CommandResult(
            success=True,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=0
        )
    except subprocess.CalledProcessError as e:
        return CommandResult(
            success=False,
            stdout=e.stdout,
            stderr=e.stderr,
            returncode=e.returncode
        )
    except subprocess.TimeoutExpired as e:
        return CommandResult(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            returncode=-1,
            timed_out=True
        )
```

ACCEPTANCE CRITERIA:
- Create app/server/utils/subprocess_utils.py (~150 lines)
- Include run_command(), run_gh_command(), start_background_service()
- Use CommandResult dataclass for structured returns
- Add comprehensive docstrings
- Create app/server/tests/utils/test_subprocess_utils.py with tests for:
  - Successful command execution
  - Failed command handling
  - Timeout handling
  - Background service starting
- All tests pass

FILES TO CREATE:
- app/server/utils/subprocess_utils.py
- app/server/tests/utils/test_subprocess_utils.py

ESTIMATED EFFORT: 2.5 hours
COMPLEXITY: Medium
DRY BENEFIT: Eliminates 13+ duplicate patterns (195+ lines)
```

---

## ✅ Request 1.7: Extract Frontend Formatters

**Workflow:** `lightweight` (Haiku model)

```
Create a centralized frontend formatters utility at app/client/src/utils/formatters.ts to eliminate duplicated formatting functions across components.

CONTEXT:
Six formatting functions are duplicated across multiple components:
- formatDate: 3 variations in HistoryView, WorkflowHistoryCard, RoutesView
- formatDuration: 5 duplicates in WorkflowHistoryCard, SimilarWorkflowsComparison, HistoryAnalytics, PhaseDurationChart
- formatCost: 4 duplicates in WorkflowHistoryCard, SimilarWorkflowsComparison
- formatNumber: 2 duplicates

Total: 36 uses of formatting functions that should be centralized.

TASK:
Create app/client/src/utils/formatters.ts with standardized formatting functions:
- formatDate(timestamp?: string): string - Format ISO timestamp to localized string
- formatDuration(seconds?: number, format?: 'simple' | 'full'): string - Format seconds to human-readable duration
- formatCost(cost?: number): string - Format cost to $X.XXXX format
- formatNumber(num: number): string - Format number with thousand separators
- formatTimestamp(date: Date | null): string - Format Date object to localized string

Each function should:
- Handle null/undefined inputs gracefully
- Return consistent formatting
- Include JSDoc documentation

IMPLEMENTATION GUIDANCE:
```typescript
/**
 * Format an ISO timestamp to a localized date string
 * @param timestamp - ISO 8601 timestamp string
 * @returns Formatted date string or 'N/A' if invalid
 */
export function formatDate(timestamp?: string): string {
  if (!timestamp) return 'N/A';
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format seconds to human-readable duration
 * @param seconds - Duration in seconds
 * @param format - 'simple' (e.g., "5m") or 'full' (e.g., "5m 30s")
 * @returns Formatted duration string
 */
export function formatDuration(
  seconds?: number,
  format: 'simple' | 'full' = 'full'
): string {
  if (seconds === undefined || seconds === null) return 'N/A';

  if (format === 'simple') {
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  }

  // Full format
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Format cost to currency string
 * @param cost - Cost amount
 * @returns Formatted cost string (e.g., "$1.2345")
 */
export function formatCost(cost?: number): string {
  if (cost === undefined || cost === null) return 'N/A';
  return `$${cost.toFixed(4)}`;
}
```

ACCEPTANCE CRITERIA:
- Create app/client/src/utils/formatters.ts (~150 lines)
- Include all 5 formatting functions
- Add JSDoc documentation for each
- Handle null/undefined gracefully
- Create app/client/src/utils/__tests__/formatters.test.ts with tests for:
  - Each formatter with valid input
  - Null/undefined handling
  - Edge cases (0, negative numbers, very large numbers)
- All tests pass
- No migration of existing code yet (that's separate tasks)

FILES TO CREATE:
- app/client/src/utils/formatters.ts
- app/client/src/utils/__tests__/formatters.test.ts

ESTIMATED EFFORT: 2 hours
COMPLEXITY: Low
DRY BENEFIT: Eliminates 36 uses of duplicate formatting (30-48 lines)
```

---

# Phase 2: Backend Modularity (File Size Fixes)

## ✅ Request 2.1: Extract Workflow Watchers Service

**Workflow:** `lightweight` (Haiku model)

```
Extract background workflow watchers from server.py to a dedicated service module to improve modularity and reduce file size.

CONTEXT:
server.py (2,103 lines) violates the 800-line hard limit by 2.6×. The first step is extracting the 3 background watchers (lines 272-420) which are a self-contained responsibility.

Current watchers:
- watch_workflows() - Polls agents/ directory every 10s
- watch_routes() - Polls FastAPI routes every 10s
- watch_workflow_history() - Polls DB every 10s

All three have identical patterns and dependencies.

TASK:
Create app/server/services/watchers.py containing:
- BackgroundWatcherService class that manages all 3 watchers
- Methods: start_all(), stop_all()
- Takes ConnectionManager and WorkflowService as constructor dependencies
- Configurable watch_interval (default 10s)

Extract from server.py:
- watch_workflows() (lines 272-297)
- watch_routes() (lines 299-324)
- watch_workflow_history() (lines 394-420)
- Helper functions: get_workflows_data(), get_routes_data(), get_workflow_history_data()

IMPLEMENTATION GUIDANCE:
```python
class BackgroundWatcherService:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        workflow_service: WorkflowService,
        watch_interval: float = 10.0
    ):
        self.connection_manager = connection_manager
        self.workflow_service = workflow_service
        self.watch_interval = watch_interval
        self._tasks = []

    async def start_all(self):
        """Start all background watchers"""
        self._tasks = [
            asyncio.create_task(self._watch_workflows()),
            asyncio.create_task(self._watch_routes()),
            asyncio.create_task(self._watch_workflow_history())
        ]

    async def stop_all(self):
        """Stop all background watchers gracefully"""
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
```

ACCEPTANCE CRITERIA:
- Create app/server/services/watchers.py (~150 lines)
- BackgroundWatcherService class with start_all()/stop_all()
- All 3 watchers extracted and working
- Graceful shutdown on cancellation
- Do NOT integrate into server.py yet (that's Request 2.2)
- Create app/server/tests/services/test_watchers.py with tests
- All tests pass

FILES TO CREATE:
- app/server/services/watchers.py
- app/server/tests/services/test_watchers.py

ESTIMATED EFFORT: 2 hours
COMPLEXITY: Medium
MODULARITY BENEFIT: Separates infrastructure from routing, reduces server.py by ~150 lines
```

---

## ✅ Request 2.2: Integrate Watchers Service into server.py

**Workflow:** `lightweight` (Haiku model)

```
Integrate the BackgroundWatcherService created in Request 2.1 into server.py and remove the old inline watcher functions.

CONTEXT:
Request 2.1 created app/server/services/watchers.py with BackgroundWatcherService. Now we need to:
1. Import and use it in server.py
2. Remove the old inline watcher functions

TASK:
Update server.py to use BackgroundWatcherService:
1. Add import: `from app.server.services.watchers import BackgroundWatcherService`
2. Update lifespan() context manager (lines 114-138) to create and start/stop the service
3. Remove watch_workflows() (lines 272-297)
4. Remove watch_routes() (lines 299-324)
5. Remove watch_workflow_history() (lines 394-420)

PATTERN:
OLD lifespan():
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher_tasks = [
        asyncio.create_task(watch_workflows()),
        # ...
    ]
    yield
    for task in watcher_tasks:
        task.cancel()
```

NEW lifespan():
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher_service = BackgroundWatcherService(
        connection_manager=manager,
        # other dependencies
    )
    await watcher_service.start_all()
    yield
    await watcher_service.stop_all()
```

ACCEPTANCE CRITERIA:
- BackgroundWatcherService imported and integrated
- lifespan() uses watcher_service.start_all()/stop_all()
- All 3 inline watcher functions removed
- WebSocket broadcasts still work
- Background tasks start on server startup
- Background tasks stop gracefully on shutdown
- All existing tests pass
- Server.py reduced by ~150 lines

FILES TO UPDATE:
- app/server/server.py (integration + removals)

ESTIMATED EFFORT: 1 hour
COMPLEXITY: Low
MODULARITY BENEFIT: Cleaner server.py, watchers properly encapsulated
```

---

## ✅ Request 2.3: Extract Health Checks Service

**Workflow:** `lightweight` (Haiku model)

```
Extract system health check logic from server.py to a dedicated service module.

CONTEXT:
server.py has ~250 lines of health checking logic (lines 623-855 + 968-1052) that should be in a separate module.

Components to extract:
- get_system_status() - Main health check function
- Webhook service health checks
- Cloudflare tunnel health checks
- GitHub webhook health checks
- Service restart logic (webhook, Cloudflare)

TASK:
Create app/server/services/health_checks.py with:
- SystemHealthService class
- Methods:
  - check_all_services() - Returns health status for all services
  - check_database()
  - check_webhook_service()
  - check_cloudflare_tunnel()
  - check_github_webhook()
  - check_frontend()
  - restart_webhook_service() (from server.py lines 857-911)
  - restart_cloudflare_tunnel() (from server.py lines 913-966)

Use the subprocess_utils created in Request 1.6 for process checks.

ACCEPTANCE CRITERIA:
- Create app/server/services/health_checks.py (~300 lines)
- SystemHealthService class with all check methods
- Use subprocess_utils for process operations
- Return structured health status data
- Do NOT integrate into server.py yet (that's a separate request)
- Create app/server/tests/services/test_health_checks.py
- All tests pass (mock subprocess calls)

FILES TO CREATE:
- app/server/services/health_checks.py
- app/server/tests/services/test_health_checks.py

ESTIMATED EFFORT: 3 hours
COMPLEXITY: Medium
MODULARITY BENEFIT: Separates health concerns, reduces server.py by ~250 lines
```

---

## ✅ Request 2.4: Extract Request Processor Service

**Workflow:** `lightweight` (Haiku model)

```
Extract natural language request processing logic from server.py to a dedicated service module.

CONTEXT:
server.py has ~200 lines of NL request processing (lines 1883-2100) that should be in a separate module for better organization.

Components to extract:
- submit_nl_request() - Creates GitHub issue from NL request
- get_issue_preview() - Generates preview before posting
- get_cost_estimate() - Estimates workflow cost
- confirm_and_post_issue() - Posts issue to GitHub
- check_webhook_trigger_health() - Validates webhook service

TASK:
Create app/server/services/request_processor.py with:
- RequestProcessorService class
- Methods for all NL request operations
- Integration with GitHub poster
- Cost estimation logic
- Preview generation

ACCEPTANCE CRITERIA:
- Create app/server/services/request_processor.py (~200 lines)
- RequestProcessorService class with all methods
- Clear separation of concerns (parsing, validation, posting)
- Do NOT integrate into server.py yet
- Create app/server/tests/services/test_request_processor.py
- All tests pass

FILES TO CREATE:
- app/server/services/request_processor.py
- app/server/tests/services/test_request_processor.py

ESTIMATED EFFORT: 2.5 hours
COMPLEXITY: Medium
MODULARITY BENEFIT: Separates NL processing, reduces server.py by ~200 lines
```

---

# Phase 3: workflow_history.py Decomposition

## ✅ Request 3.1: Extract Database Layer from workflow_history

**Workflow:** `lightweight` (Haiku model)

```
Extract pure database operations from workflow_history.py to create a clean data access layer.

CONTEXT:
workflow_history.py (1,349 lines) violates the 800-line hard limit. It mixes database operations with business logic. First step: extract the database layer.

Components to extract (lines 181-476):
- get_db_connection() context manager
- init_db() - Initialize workflow history tables
- insert_workflow_history() - Insert workflow
- update_workflow_history() - Update workflow
- get_workflow_by_adw_id() - Query by ID
- get_workflow_history() - Query with filters
- delete_workflow() - Delete operation

TASK:
Create app/server/data/workflow_db.py with pure CRUD operations:
- Use the db_connection utility from Request 1.1
- No business logic (syncing, calculations, enrichment)
- Just database operations

ACCEPTANCE CRITERIA:
- Create app/server/data/workflow_db.py (~300 lines)
- All CRUD operations extracted
- Uses db_connection utility
- No business logic mixed in
- Do NOT update workflow_history.py imports yet
- Create app/server/tests/data/test_workflow_db.py
- All tests pass

FILES TO CREATE:
- app/server/data/workflow_db.py
- app/server/tests/data/test_workflow_db.py

ESTIMATED EFFORT: 2 hours
COMPLEXITY: Low (mechanical extraction)
MODULARITY BENEFIT: Clean data layer, reduces workflow_history.py by ~300 lines
```

---

## ✅ Request 3.2: Extract Workflow Sync Logic

**Workflow:** `lightweight` (Haiku model)

```
Extract workflow syncing logic from workflow_history.py to a dedicated sync module.

CONTEXT:
After Request 3.1 extracted the database layer, we need to extract the syncing logic (lines 731-1169) which is a distinct responsibility.

Components to extract:
- scan_agents_directory() - Scans agents/ for workflows
- sync_workflow_history() - Main sync orchestration
- resync_workflow_cost() - Resync single workflow
- resync_all_completed_workflows() - Batch resync
- Supporting functions: categorize_error(), estimate_complexity()

TASK:
Create app/server/core/workflow_sync.py with:
- WorkflowSyncService class
- Methods for all syncing operations
- Uses workflow_db for database operations
- Uses workflow_metrics (Request 3.3) for calculations

ACCEPTANCE CRITERIA:
- Create app/server/core/workflow_sync.py (~350 lines)
- WorkflowSyncService class
- Clear separation from database operations
- Uses workflow_db module
- Do NOT update workflow_history.py imports yet
- Create app/server/tests/core/test_workflow_sync.py
- All tests pass

FILES TO CREATE:
- app/server/core/workflow_sync.py
- app/server/tests/core/test_workflow_sync.py

ESTIMATED EFFORT: 3 hours
COMPLEXITY: Medium (complex interdependencies)
MODULARITY BENEFIT: Separates sync concern, reduces workflow_history.py by ~350 lines
```

---

## ✅ Request 3.3: Extract Workflow Metrics Calculation

**Workflow:** `lightweight` (Haiku model)

```
Extract phase metrics and calculation functions from workflow_history.py to a dedicated metrics module.

CONTEXT:
workflow_history.py has metrics calculation logic scattered throughout. Extract to a focused module for reusability.

Components to extract:
- calculate_phase_metrics() - Calculate metrics for phases
- categorize_error() - Error categorization logic
- estimate_complexity() - Complexity estimation
- Supporting calculation helpers

TASK:
Create app/server/core/workflow_metrics.py with:
- Pure calculation functions
- No database access
- No file system access
- Just business logic for metrics

ACCEPTANCE CRITERIA:
- Create app/server/core/workflow_metrics.py (~150 lines)
- All calculation functions extracted
- Pure functions (no side effects)
- Do NOT update workflow_history.py yet
- Create app/server/tests/core/test_workflow_metrics.py
- All tests pass

FILES TO CREATE:
- app/server/core/workflow_metrics.py
- app/server/tests/core/test_workflow_metrics.py

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low (pure functions)
MODULARITY BENEFIT: Reusable metrics logic, reduces workflow_history.py by ~150 lines
```

---

# Phase 4: Frontend Component Decomposition

## ✅ Request 4.1: Extract WorkflowHistoryCard Helper Functions

**Workflow:** `lightweight` (Haiku model)

```
Extract helper functions from WorkflowHistoryCard.tsx to a dedicated utilities module.

CONTEXT:
WorkflowHistoryCard.tsx (794 lines) is approaching the 800-line hard limit. First step: extract the 11 helper functions (lines 16-101) to utils/.

Helper functions to extract:
- transformToPhaseCosts()
- calculateBudgetDelta()
- calculateRetryCost()
- calculateCacheSavings()
- truncateText()
- getClassificationColor()
- formatStructuredInputForDisplay()

TASK:
Create app/client/src/utils/workflowHelpers.ts with all helper functions.

Alternatively, if formatters.ts from Request 1.7 exists, merge some helpers there:
- Date/cost/number formatting → formatters.ts
- Workflow-specific logic → workflowHelpers.ts

ACCEPTANCE CRITERIA:
- Create app/client/src/utils/workflowHelpers.ts (~100 lines)
- All helper functions extracted with TypeScript types
- JSDoc documentation for each
- Do NOT update WorkflowHistoryCard.tsx imports yet
- Create app/client/src/utils/__tests__/workflowHelpers.test.ts
- All tests pass

FILES TO CREATE:
- app/client/src/utils/workflowHelpers.ts
- app/client/src/utils/__tests__/workflowHelpers.test.ts

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low
MODULARITY BENEFIT: Reusable helpers, reduces component by ~100 lines
```

---

## ✅ Request 4.2: Extract CostAnalysisSection Component

**Workflow:** `lightweight` (Haiku model)

```
Extract the Cost Analysis section from WorkflowHistoryCard.tsx to a dedicated component.

CONTEXT:
WorkflowHistoryCard.tsx needs decomposition. Extract the cost analysis section (lines ~252-354) as the first of 8 section components.

Section includes:
- Budget delta calculation and display
- Phase cost visualization
- Budget comparison (actual vs. estimated)
- Per-step cost comparison

TASK:
Create app/client/src/components/workflow-history/sections/CostAnalysisSection.tsx.

Import and use:
- Helper functions from workflowHelpers.ts (Request 4.1)
- Formatters from formatters.ts (Request 1.7)
- CostBreakdownChart component

ACCEPTANCE CRITERIA:
- Create app/client/src/components/workflow-history/sections/CostAnalysisSection.tsx (~100 lines)
- Focused single-responsibility component
- Uses imported helpers/formatters
- TypeScript props interface defined
- Do NOT update WorkflowHistoryCard.tsx yet
- Create __tests__/CostAnalysisSection.test.tsx
- All tests pass

FILES TO CREATE:
- app/client/src/components/workflow-history/sections/CostAnalysisSection.tsx
- app/client/src/components/workflow-history/sections/__tests__/CostAnalysisSection.test.tsx

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low
MODULARITY BENEFIT: Focused component, reduces main component by ~100 lines
```

---

## ✅ Request 4.3: Extract TokenAnalysisSection Component

**Workflow:** `lightweight` (Haiku model)

```
Extract the Token Analysis section from WorkflowHistoryCard.tsx to a dedicated component.

CONTEXT:
Second of 8 section extractions. Token analysis section (lines ~356-448) handles token breakdown and cache efficiency.

Section includes:
- Token breakdown chart
- Cache efficiency display
- Cache hit/miss ratios
- Cache savings calculation

TASK:
Create app/client/src/components/workflow-history/sections/TokenAnalysisSection.tsx.

ACCEPTANCE CRITERIA:
- Create component file (~90 lines)
- Uses workflowHelpers for calculateCacheSavings()
- Uses formatters for number/cost formatting
- Includes TokenBreakdownChart component
- Do NOT update main component yet
- Create tests
- All tests pass

FILES TO CREATE:
- app/client/src/components/workflow-history/sections/TokenAnalysisSection.tsx
- app/client/src/components/workflow-history/sections/__tests__/TokenAnalysisSection.test.tsx

ESTIMATED EFFORT: 1.5 hours
COMPLEXITY: Low
```

---

## ✅ Request 4.4: Extract Remaining 6 Sections and Update Main Component

**Workflow:** `lightweight` (Haiku model)

```
Extract the remaining 6 section components from WorkflowHistoryCard.tsx and update the main component to use all extracted sections.

CONTEXT:
Requests 4.2 and 4.3 extracted CostAnalysisSection and TokenAnalysisSection. This request extracts the remaining 6 sections and updates the main component.

Sections to extract:
1. PerformanceSection (~30 lines)
2. ErrorAnalysisSection (~90 lines)
3. ResourceUsageSection (~25 lines)
4. WorkflowJourneySection (~80 lines)
5. EfficiencyScoresSection (~40 lines)
6. InsightsSection (~35 lines)

Then update WorkflowHistoryCard.tsx to:
- Import all 8 section components
- Remove old section code
- Compose sections in the render

ACCEPTANCE CRITERIA:
- Create 6 section component files
- Create test files for each
- Update app/client/src/components/workflow-history/WorkflowHistoryCard.tsx to use all sections
- Main component reduced to ~100-120 lines (just composition)
- All sections work correctly
- All tests pass
- No visual regressions

FILES TO CREATE:
- 6 section components
- 6 test files

FILES TO UPDATE:
- WorkflowHistoryCard.tsx (convert to composition)

ESTIMATED EFFORT: 4 hours
COMPLEXITY: Medium (multiple components)
MODULARITY BENEFIT: Reduces monolithic component from 794 → ~100 lines
```

---

## Progress Tracking

### Phase 1: Utility Extraction (DRY)
- [ ] 1.1 - Extract Database Connection Utility
- [ ] 1.2 - Migrate server.py to DB Utility
- [ ] 1.3 - Migrate Core Modules to DB Utility
- [ ] 1.4 - Extract LLM Client Utilities
- [ ] 1.5 - Migrate LLM Processors to Client Utilities
- [ ] 1.6 - Extract Subprocess Utilities
- [ ] 1.7 - Extract Frontend Formatters

### Phase 2: Backend Modularity
- [ ] 2.1 - Extract Workflow Watchers Service
- [ ] 2.2 - Integrate Watchers Service
- [ ] 2.3 - Extract Health Checks Service
- [ ] 2.4 - Extract Request Processor Service

### Phase 3: workflow_history Decomposition
- [ ] 3.1 - Extract Database Layer
- [ ] 3.2 - Extract Workflow Sync Logic
- [ ] 3.3 - Extract Workflow Metrics

### Phase 4: Frontend Decomposition
- [ ] 4.1 - Extract WorkflowHistoryCard Helpers
- [ ] 4.2 - Extract CostAnalysisSection
- [ ] 4.3 - Extract TokenAnalysisSection
- [ ] 4.4 - Extract Remaining Sections + Update Main Component

**Total:** 22 focused, cost-conscious refactoring tasks
**Estimated Total Cost:** $24-40 (using lightweight/haiku models)
