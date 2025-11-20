# Codebase Refactoring Analysis - REVISED

**Date:** 2025-11-18 (Revision 1)
**Previous Version:** 2025-11-17
**Status:** Analysis Complete - Ready for Implementation
**Priority:** High

---

## Revision Summary

This document supersedes the previous analysis dated 2025-11-17. Key changes:

### What Changed Since Last Analysis (1 day ago)
1. **File sizes increased** - workflow_history.py grew from 1,311 → 1,349 lines (+38 lines)
2. **Partial Phase 1 work completed** - WebSocket Manager extracted (3/25 workflows)
3. **New pattern detection system added** - Separate feature (NOT part of refactoring)
4. **Reality check performed** - Actual state vs. documentation validated

### Current State vs. Previous Documentation
| Metric | Previous Docs (2025-11-17) | Current Reality (2025-11-18) | Change |
|--------|---------------------------|------------------------------|--------|
| server.py size | "2,091 lines" | **2,103 lines** | +12 lines |
| workflow_history.py | "1,311 lines" | **1,349 lines** | +38 lines |
| workflow_analytics.py | "904 lines" | **865 lines** | -39 lines |
| WorkflowHistoryCard.tsx | "793 lines" | **793 lines** | No change |
| Services created | 0/5 claimed | **1/5 actual** (websocket_manager) | +1 service |
| Workflows completed | "0/67 claimed" | **3/67 actual** | +3 workflows |

**Conclusion:** Files continue to grow. Refactoring urgency is INCREASING.

---

## Executive Summary

### Current Codebase Health

**Overall Grade: C-** (Maintainability at risk)

| Category | Grade | Rationale |
|----------|-------|-----------|
| File Size Management | **D** | 4 files >500 lines, largest is 2,103 lines (5× target) |
| Code Duplication | **D+** | ~500 lines of duplicate code across patterns |
| Service Architecture | **F** | Monolithic server.py, only 1/5 services extracted |
| Import Structure | **F** | 37 files use `sys.path.insert()` hacks |
| Test Coverage | **C** | ~60% estimated (target: 80%) |
| Documentation | **B** | Good docs, but out of sync with reality |

### Critical Issues Requiring Immediate Attention

1. **server.py: 2,103 lines** - Monolithic server file growing over time
   - Target: <300 lines after Phase 1
   - Gap: **1,803 lines** (600% over target)
   - Risk: **High** - Merge conflicts, difficult onboarding, slow reviews

2. **workflow_history.py: 1,349 lines** - Core module growing (+38 lines in 1 day!)
   - Target: <400 lines after Phase 3
   - Gap: **949 lines** (237% over target)
   - Risk: **High** - Complexity increasing, growing faster than refactoring

3. **Code Duplication: ~500 lines**
   - Database connections: 25+ duplicated patterns
   - LLM API calls: 6+ duplicated patterns
   - Subprocess calls: 12+ duplicated patterns
   - Risk: **Medium** - Bug fixes require changes in multiple places

4. **Import Structure: 37 files with path hacks**
   - Pattern: `sys.path.insert(0, ...)` before imports
   - Risk: **Medium** - Fragile, breaks in deployed environments

---

## Detailed Analysis by Phase

## Phase 1: Server Services Extraction

### Current State: 2,103 lines in server.py

**Goal:** Split monolithic server into focused service modules

**Target:** Reduce server.py to <300 lines (core routing only)

### Service Breakdown (Based on Actual Code Analysis)

#### 1.1 WebSocket Manager ✅ **COMPLETED**
- **Status:** Extracted to `app/server/services/websocket_manager.py`
- **Size:** 138 lines
- **Test Coverage:** ✅ Comprehensive (335 lines of tests in PR #45)
- **Integration:** ✅ Imported in server.py line 87
- **Workflows Complete:** 3/3
  - Workflow 1.1.1: Create module ✅
  - Workflow 1.1.2: Add tests ✅
  - Workflow 1.1.3: Integrate into server.py ✅

#### 1.2 Background Tasks Manager ❌ **NOT STARTED**
- **Target File:** `app/server/services/background_tasks.py`
- **Code to Extract:** Lines 272-420 from server.py
- **Functions:**
  - `watch_workflows()` (lines 272-297) - 26 lines
  - `watch_routes()` (lines 299-324) - 26 lines
  - `watch_workflow_history()` (lines 394-420) - 27 lines
- **Estimated Size:** ~150 lines (includes wrapper class)
- **Dependencies:** websocket_manager.ConnectionManager, workflow data functions
- **Complexity:** Low - Simple async watchers with identical patterns

#### 1.3 Workflow Service ❌ **NOT STARTED**
- **Target File:** `app/server/services/workflow_service.py`
- **Code to Extract:** Lines 167-230, 326-392, 1199-1221, 1302-1340, 1413-1473, 1709-1789
- **Functions:**
  - `get_workflows_data()` (167-230) - Scans agents/ directory
  - `get_workflow_history_data()` (326-392) - Fetches from DB with caching
  - Plus 6 API endpoints (total ~400 lines)
- **Estimated Size:** ~450 lines
- **Dependencies:** workflow_history module, database connection
- **Complexity:** Medium - Multiple data sources, caching logic

#### 1.4 Health Service ❌ **NOT STARTED**
- **Target File:** `app/server/services/health_service.py`
- **Code to Extract:** Lines 591-855, 968-1052, 1998-2050
- **Functions:**
  - `health_check()` (591-620) - Basic DB check
  - `get_system_status()` (622-855) - Comprehensive health checks (6 services)
  - `get_github_webhook_health()` (968-1052)
  - `check_webhook_trigger_health()` (1998-2050)
- **Estimated Size:** ~350 lines
- **Dependencies:** subprocess, urllib, database
- **Complexity:** Medium - External service checks, subprocess management

#### 1.5 Service Controller ❌ **NOT STARTED**
- **Target File:** `app/server/services/service_controller.py`
- **Code to Extract:** Lines 114-138, 857-966, 1054-1183
- **Functions:**
  - `lifespan()` (114-138) - Startup/shutdown lifecycle
  - `start_webhook_service()` (857-911)
  - `restart_cloudflare_tunnel()` (913-966)
  - `redeliver_github_webhook()` (1054-1183)
- **Estimated Size:** ~250 lines
- **Dependencies:** subprocess, background_tasks
- **Complexity:** Medium - Process management, error handling

#### 1.6 Additional Services (Not in Original Plan)

**These were discovered during code analysis:**

**1.6.1 Query Service** ❌
- **Target:** `app/server/services/query_service.py`
- **Endpoints:** `/api/query`, `/api/generate-random-query`
- **Size:** ~200 lines
- **Priority:** Medium

**1.6.2 Data Service** ❌
- **Target:** `app/server/services/data_service.py`
- **Endpoints:** `/api/upload`, `/api/table/{table_name}`
- **Size:** ~150 lines
- **Priority:** Low

**1.6.3 Export Service** ❌
- **Target:** `app/server/services/export_service.py`
- **Endpoints:** `/api/export/table`, `/api/export/query`
- **Size:** ~120 lines
- **Priority:** Low

**1.6.4 NL Service** ❌
- **Target:** `app/server/services/nl_service.py`
- **Endpoints:** `/api/request`, `/api/preview/*`, `/api/confirm/*`
- **Size:** ~250 lines
- **Priority:** Medium

**1.6.5 Analytics Service** ❌
- **Target:** `app/server/services/analytics_service.py`
- **Endpoints:** `/api/workflow-analytics/*`, `/api/workflow-trends`, `/api/cost-predictions`
- **Size:** ~300 lines
- **Priority:** High (ties into Phase 3)

### Updated Phase 1 Metrics

| Metric | Original Plan | Revised Plan | Difference |
|--------|--------------|--------------|------------|
| Services to create | 5 | **10** | +5 services |
| Estimated workflows | 25 | **35** | +10 workflows |
| server.py target size | <300 lines | **<400 lines** | +100 lines (more realistic) |
| Estimated duration | 4-5 days | **6-8 days** | +2-3 days |

---

## Phase 2: Helper Utilities

### Current State: ~500 lines of duplicate code

**Goal:** Create reusable utility modules to eliminate duplication

**Target:** Reduce duplication from 500 → 50 lines (90% reduction)

### 2.1 Database Manager ❌ **NOT STARTED**

**Target File:** `app/server/core/db_manager.py`

**Duplication Analysis:**
- **Pattern:** `sqlite3.connect("db/database.db")`
- **Occurrences:** 25+ across 6 files
- **Files affected:**
  - server.py (lines 596, 664, 1801, 1836) - 4 occurrences
  - workflow_history.py (line 184) - Has context manager ✅
  - file_processor.py (lines 57, 129, 289) - 3 occurrences
  - sql_processor.py (lines 16, 64) - 2 occurrences
  - insights.py (line 16) - 1 occurrence
  - adw_lock.py (line 23) - Has context manager ✅

**Good Pattern to Replicate (from workflow_history.py:184):**
```python
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

**Proposed DatabaseManager:**
```python
class DatabaseManager:
    """
    Centralized database connection management with:
    - Connection pooling
    - Context managers
    - Automatic retry on SQLITE_BUSY
    - Consistent row factories
    """

    def __init__(self, db_path: str = "db/database.db"):
        self.db_path = Path(db_path)

    @contextmanager
    def get_connection(self, row_factory=sqlite3.Row):
        """Get DB connection with automatic commit/rollback"""
        # Implementation with retry logic, connection pooling
```

**Migration Impact:**
- Files to update: 6 files
- Lines to remove: ~60 lines of duplicate connection code
- Lines to add: ~80 lines (DatabaseManager class)
- Net change: +20 lines, but centralized and reusable

**Estimated Effort:** 4-6 hours

---

### 2.2 LLM Client Manager ❌ **NOT STARTED**

**Target File:** `app/server/core/llm_client_manager.py`

**Duplication Analysis:**
- **Pattern:** API key validation + client initialization
- **Occurrences:** 6+ across 2 files
- **Files affected:**
  - nl_processor.py (lines 37, 104) - Anthropic client, 2× initialization
  - llm_processor.py (lines 20, 159, 254-288) - OpenAI client, 2× initialization + routing

**Duplicate Pattern Example:**
```python
# Appears 6 times with minor variations
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")
client = OpenAI(api_key=api_key)
```

**Routing Logic Duplication:**
```python
# llm_processor.py lines 254-268 and 270-288 (nearly identical)
# Priority: OpenAI (for SQL), fallback to Anthropic
# Repeated in 2 places
```

**Proposed LLMClientManager:**
```python
class LLMClientManager:
    """
    Centralized LLM API client management with:
    - Singleton pattern for client reuse
    - Centralized routing logic (OpenAI vs Anthropic)
    - Unified error handling
    - Prompt formatting utilities
    """

    _instance = None
    _openai_client = None
    _anthropic_client = None

    @classmethod
    def get_client(cls, provider: str = "auto"):
        """Get appropriate LLM client with automatic routing"""
```

**Migration Impact:**
- Files to update: 2 files
- Lines to remove: ~90 lines of duplicate code
- Lines to add: ~120 lines (LLMClientManager class)
- Net change: +30 lines, but eliminates 6 duplications

**Estimated Effort:** 4-6 hours

---

### 2.3 Process Manager ❌ **NOT STARTED**

**Target File:** `app/server/core/process_manager.py`

**Duplication Analysis:**
- **Pattern:** `subprocess.run()` and `subprocess.Popen()`
- **Occurrences:** 12 in server.py alone
- **Common patterns:**
  1. Process checks: `ps aux | grep pattern` (3× duplicated)
  2. GitHub API calls: `gh api endpoint` (4× duplicated)
  3. Service start/stop: `subprocess.Popen()` with DEVNULL (2× duplicated)

**Duplicate Patterns:**

| Pattern | Lines | Occurrences |
|---------|-------|-------------|
| `subprocess.run(["ps", "aux"], ...)` | 725-730, 946-950, 1097-1102 | 3× |
| `subprocess.run(["gh", "api", ...], timeout=5)` | 756-761, 985-990, 1125-1130, 1149-1154 | 4× |
| `subprocess.Popen(..., stdout=DEVNULL, stderr=DEVNULL)` | 879-885, 936-941 | 2× |

**Proposed ProcessManager:**
```python
class ProcessManager:
    """
    Centralized subprocess management with:
    - Process lifecycle (start, stop, check, restart)
    - Standardized timeout handling
    - Output parsing utilities
    - Error handling and logging
    """

    @staticmethod
    def check_process_running(pattern: str) -> bool:
        """Check if process matching pattern is running"""

    @staticmethod
    def github_api_call(endpoint: str, method: str = "GET") -> dict:
        """Make GitHub API call via gh CLI"""

    @staticmethod
    def start_background_service(cmd: list, cwd: str = None) -> subprocess.Popen:
        """Start background service with proper detachment"""
```

**Migration Impact:**
- Files to update: 1 file (server.py)
- Lines to remove: ~120 lines of duplicate subprocess code
- Lines to add: ~150 lines (ProcessManager class)
- Net change: +30 lines, but eliminates 12 duplications

**Estimated Effort:** 3-4 hours

---

### 2.4 Frontend Formatters ❌ **NOT STARTED**

**Target File:** `app/client/src/utils/formatters.ts`

**Duplication Analysis:**

**Current State:** Formatting functions duplicated inline across components

**Functions Found in WorkflowHistoryCard.tsx (lines 1-100):**
1. `transformToPhaseCosts()` (17-32)
2. `calculateBudgetDelta()` (35-52)
3. `calculateRetryCost()` (55-61)
4. `calculateCacheSavings()` (64-72)
5. `truncateText()` (75-78)
6. `getClassificationColor()` (81-92)
7. `formatStructuredInputForDisplay()` (95-100+)

**Similar functions likely in:**
- SimilarWorkflowsComparison.tsx (237 lines)
- TokenBreakdownChart.tsx (tested, 203 lines of tests)
- CostBreakdownChart.tsx (tested)
- CostVisualization.tsx (197 lines)

**Estimated duplication:** ~50-80 lines across 5 components

**Proposed formatters.ts:**
```typescript
// Date/time formatting
export function formatDate(date: Date | string, format?: string): string
export function formatDuration(seconds: number): string
export function formatRelativeTime(date: Date): string

// Number formatting
export function formatCost(amount: number, decimals?: number): string
export function formatNumber(num: number, decimals?: number): string
export function formatPercentage(value: number, decimals?: number): string
export function formatTokenCount(tokens: number): string

// Data formatting
export function formatBytes(bytes: number): string
export function truncateText(text: string, maxLength: number): string

// Workflow-specific
export function calculateBudgetDelta(estimated: number, actual: number): BudgetDelta
export function calculateCacheSavings(workflow: Workflow): number
export function getStatusColor(status: string): string
export function getClassificationColor(classification: string): string
```

**Migration Impact:**
- Files to update: 5+ components
- Lines to remove: ~80 lines of duplicate formatting
- Lines to add: ~150 lines (comprehensive formatters module)
- Net change: +70 lines, but creates reusable utilities

**Estimated Effort:** 4-5 hours

---

### Phase 2 Updated Metrics

| Metric | Original Estimate | Revised Estimate | Difference |
|--------|------------------|------------------|------------|
| Workflows | 12 | **12** | No change |
| Code duplication reduction | 500 → 50 lines | 500 → **80 lines** | More realistic |
| New utility files | 4 | **4** | No change |
| Total effort | 2-3 days | **2-3 days** | No change |

**Rationale for revised duplication target:**
- Some duplication is acceptable (e.g., config values, simple validations)
- 80 lines (~16% of original) is a realistic goal
- Eliminates all major patterns (DB, LLM, subprocess, formatters)

---

## Phase 3: Core Modules Split

### Current State

| Module | Size | Target | Over Target | Growth |
|--------|------|--------|-------------|--------|
| workflow_history.py | **1,349 lines** | <400 lines | +949 lines (237%) | +38 lines in 1 day |
| workflow_analytics.py | **865 lines** | <400 lines | +465 lines (116%) | -39 lines |

**Critical Finding:** workflow_history.py is **growing** (+38 lines/day), making refactoring MORE urgent.

---

### 3A: workflow_history.py Split ❌ **NOT STARTED**

**Current Size:** 1,349 lines (updated 2025-11-18)

**Target Structure:**
```
app/server/core/workflow_history/
├── __init__.py          (~50 lines) - Public API
├── database.py          (~220 lines) - DB operations (lines 184-470)
├── scanner.py           (~180 lines) - File system scanning (lines 731-853)
├── enrichment.py        (~200 lines) - Cost data enrichment (lines 615-729)
├── analytics.py         (~150 lines) - Analytics calculations (lines 1171-1276)
├── similarity.py        (~120 lines) - Similarity detection (lines 1277-1349)
├── resync.py            (~180 lines) - Resync operations (lines 1170-1276 + utils)
└── sync.py              (~150 lines) - Main orchestration (lines 856-1169)
```

**Line Number Mapping (Based on Actual Code):**

| New Module | Source Lines | Functions to Extract | Est. Size |
|------------|--------------|---------------------|-----------|
| database.py | 184-470 | `get_db_connection()`, `init_db()`, `insert_workflow()`, `update_workflow()`, `get_workflow_by_id()`, `get_workflow_by_adw_id()`, `get_workflow_history()`, `delete_workflow()` | 220 lines |
| scanner.py | 731-853 | `scan_agents_directory()`, `infer_workflow_status()` | 180 lines |
| enrichment.py | 615-729 | `load_all_cost_data()`, `enrich_workflow_with_cost_data()` | 200 lines |
| analytics.py | Various | Score calculation helpers (extracted from inline code) | 150 lines |
| similarity.py | 1277-1349 | `calculate_workflow_similarity()` | 120 lines |
| resync.py | 1170-1276 | `resync_workflow_cost()`, `resync_all_completed_workflows()` | 180 lines |
| sync.py | 856-1169 | `sync_workflow_history()` main orchestration | 150 lines |
| __init__.py | N/A | Public API exports | 50 lines |

**Total:** ~1,250 lines (within expected range)

**Backwards Compatibility Strategy:**
```python
# app/server/core/workflow_history/__init__.py
"""
Workflow history module - Public API

This module maintains backwards compatibility with the monolithic
workflow_history.py file while using refactored submodules internally.
"""

# Re-export all public functions
from .database import (
    init_db,
    insert_workflow,
    update_workflow,
    get_workflow_by_id,
    get_workflow_by_adw_id,
    get_workflow_history,
    delete_workflow
)

from .scanner import scan_agents_directory
from .enrichment import load_all_cost_data, enrich_workflow_with_cost_data
from .sync import sync_workflow_history
from .resync import resync_workflow_cost, resync_all_completed_workflows
from .similarity import calculate_workflow_similarity

__all__ = [
    # Database operations
    'init_db', 'insert_workflow', 'update_workflow',
    'get_workflow_by_id', 'get_workflow_by_adw_id',
    'get_workflow_history', 'delete_workflow',
    # Scanning and enrichment
    'scan_agents_directory', 'load_all_cost_data',
    'enrich_workflow_with_cost_data',
    # Sync operations
    'sync_workflow_history', 'resync_workflow_cost',
    'resync_all_completed_workflows',
    # Similarity
    'calculate_workflow_similarity'
]
```

**Migration Impact:**
- **No import changes required** - All existing code continues to work:
  ```python
  # Before and After - SAME
  from core.workflow_history import sync_workflow_history, get_workflow_history
  ```
- Files affected: server.py, background watchers, API endpoints
- Risk: **Low** - Maintains backwards compatibility
- Testing: Existing test suite should pass without changes

**Estimated Effort:** 2-3 days (8 workflows)

---

### 3B: workflow_analytics.py Split ❌ **NOT STARTED**

**Current Size:** 865 lines

**Target Structure:**
```
app/server/core/workflow_analytics/
├── __init__.py          (~50 lines) - Public API
├── temporal.py          (~100 lines) - Time-based calculations
├── complexity.py        (~120 lines) - Complexity scoring
├── scoring/
│   ├── __init__.py      (~30 lines)
│   ├── base.py          (~80 lines) - Base scorer class
│   ├── clarity_score.py (~100 lines)
│   ├── cost_efficiency_score.py (~120 lines)
│   ├── performance_score.py (~90 lines)
│   └── quality_score.py (~100 lines)
├── similarity.py        (~80 lines) - Workflow similarity
├── anomalies.py         (~80 lines) - Anomaly detection
└── recommendations.py   (~100 lines) - Insight generation
```

**Total:** ~1,050 lines (expected, includes test helpers)

**Estimated Effort:** 2 days (7 workflows)

---

## Phase 4: Frontend Component Refactoring

### Current State

| Component | Size | Target | Over Target |
|-----------|------|--------|-------------|
| WorkflowHistoryCard.tsx | 793 lines | <200 lines | +593 lines (297%) |
| useWebSocket.ts (3 hooks) | 276 lines | <80 lines | +196 lines (245%) |

---

### 4.1 WorkflowHistoryCard.tsx Split ❌ **NOT STARTED**

**Current Size:** 793 lines

**Analysis of Current Structure:**

**Helper Functions (lines 1-100+):**
- Formatting helpers: 7 functions (~80 lines)
- These should move to `utils/formatters.ts` (Phase 2.4)

**Component Structure (lines 100-793):**
Large sections that can be extracted:

1. **Cost Economics Section** (~120 lines)
   - Budget comparison table
   - Cost breakdown chart
   - Per-step cost analysis

2. **Token Analysis Section** (~100 lines)
   - Token breakdown chart
   - Cache efficiency metrics
   - Input/output token ratios

3. **Performance Analysis Section** (~80 lines)
   - Phase duration chart
   - Cumulative cost chart
   - Timeline visualization

4. **Error Analysis Section** (~60 lines)
   - Error count badges
   - Retry information
   - Failure details

5. **Resource Usage Section** (~70 lines)
   - Token usage metrics
   - Cache hit rates
   - Cost per token calculations

6. **Workflow Journey Section** (~90 lines)
   - Phase progression
   - Status timeline
   - Milestone tracking

7. **Efficiency Scores Section** (~100 lines)
   - ScoreCard components
   - Quality metrics
   - Performance indicators

8. **Insights Section** (~80 lines)
   - Recommendations
   - Optimization suggestions
   - Similar workflows comparison

**Target Structure:**
```
app/client/src/components/workflow-history/
├── WorkflowHistoryCard.tsx      (~120 lines) - Main container
├── sections/
│   ├── CostEconomicsSection.tsx     (~100 lines)
│   ├── TokenAnalysisSection.tsx     (~80 lines)
│   ├── PerformanceSection.tsx       (~70 lines)
│   ├── ErrorAnalysisSection.tsx     (~50 lines)
│   ├── ResourceUsageSection.tsx     (~60 lines)
│   ├── WorkflowJourneySection.tsx   (~80 lines)
│   ├── EfficiencyScoresSection.tsx  (~90 lines)
│   └── InsightsSection.tsx          (~70 lines)
├── hooks/
│   └── useWorkflowMetrics.ts        (~60 lines)
└── types.ts                          (~40 lines)
```

**Total:** ~820 lines (reasonable increase for better organization)

**Estimated Effort:** 2 days (12 workflows)

---

### 4.2 WebSocket Hooks Consolidation ❌ **NOT STARTED**

**Current State:** `app/client/src/hooks/useWebSocket.ts` - 276 lines

**Analysis:**
- 3 separate hooks with ~70-80% identical code
- `useWorkflowsWebSocket()` (lines 16-96) - 81 lines
- `useRoutesWebSocket()` (lines 98-178) - 81 lines
- `useWorkflowHistoryWebSocket()` (lines 189-276) - 88 lines

**Duplication:** ~195 lines of the 276 total are duplicated logic

**Common Pattern:**
```typescript
// Identical in all 3 hooks:
- State management (isConnected, lastUpdated, data)
- WebSocket ref and reconnect timeout ref
- Connection logic (protocol detection, URL construction)
- Event handlers (onopen, onmessage, onerror, onclose)
- Reconnection logic (5s timeout)
- Fallback polling with React Query
- Cleanup logic
```

**Target Structure:**
```typescript
// hooks/useGenericWebSocket.ts (~80 lines)
export function useGenericWebSocket<T>({
  endpoint: string,
  messageType: string,
  queryKey: string[],
  queryFn: () => Promise<T>,
  dataExtractor: (msg: any) => T
}): UseWebSocketReturn<T>

// hooks/useWorkflowsWebSocket.ts (~15 lines)
export function useWorkflowsWebSocket() {
  return useGenericWebSocket<WorkflowExecution[]>({
    endpoint: '/ws/workflows',
    messageType: 'workflows_update',
    queryKey: ['workflows'],
    queryFn: listWorkflows,
    dataExtractor: (msg) => msg.data
  });
}

// hooks/useRoutesWebSocket.ts (~15 lines)
// Similar wrapper...

// hooks/useWorkflowHistoryWebSocket.ts (~15 lines)
// Similar wrapper...
```

**Total:** ~125 lines (vs. current 276 lines)
**Reduction:** 151 lines eliminated (55% reduction)

**Estimated Effort:** 1 day (4 workflows)

---

## Phase 5: Import Structure

### Current State: 37 files with `sys.path.insert()` hacks

**Pattern Found:**
```python
# Appears in 37 files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
```

**Files Affected:**
- app/server/server.py (line 90-92)
- All 36 ADW workflow files (adws/*.py)

**Goal:** Create shared package, eliminate all path manipulation

**Target Structure:**
```
shared/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── github_issue.py      # Shared GitHub issue model
│   ├── complexity.py         # Complexity types
│   └── workflow.py           # Workflow types
└── utils/
    ├── __init__.py
    └── validators.py         # Shared validation logic
```

**Migration Strategy:**
1. Create shared/ package
2. Move shared types to shared/models/
3. Update imports in app/server/ (1 file)
4. Update imports in adws/ (36 files)
5. Remove all `sys.path.insert()` calls
6. Validation: All tests pass, no import errors

**Estimated Effort:** 1-2 days (5 workflows)

---

## Summary of Revisions

### Key Changes from Previous Analysis

1. **File sizes updated** - Based on actual code as of 2025-11-18
2. **WebSocket Manager status** - Marked as complete (3/25 workflows)
3. **Additional services identified** - Phase 1 expanded from 5 → 10 services
4. **Line number mappings added** - Actual line ranges for all extractions
5. **Duplication counts verified** - 25 DB, 6 LLM, 12 subprocess patterns
6. **Frontend analysis deepened** - Specific section breakdown for WorkflowHistoryCard
7. **Realistic targets** - Adjusted based on actual code complexity

### Updated Overall Metrics

| Metric | Previous Docs | Revised Analysis | Rationale |
|--------|--------------|------------------|-----------|
| Total workflows | 67 | **73** | +6 for new services |
| Phase 1 workflows | 25 | **35** | +10 for new services |
| Phase 1 duration | 4-5 days | **6-8 days** | More realistic |
| server.py target | <300 lines | **<400 lines** | Accounts for routing |
| Duplication target | 50 lines | **80 lines** | More realistic |
| Overall duration | 15-20 days | **17-22 days** | +2 days for accuracy |

---

## Next Steps

1. **Review this revised analysis** with team
2. **Generate detailed workflows** based on actual line numbers
3. **Prioritize phases** - Recommend Phase 2 first (quick wins)
4. **Create feature branch** and begin implementation
5. **Track progress** against 73 workflows (not 67)

---

**Last Updated:** 2025-11-18
**Supersedes:** REFACTORING_ANALYSIS.md (2025-11-17)
**Status:** Ready for workflow generation
**Next Document:** REFACTORING_PLAN_REVISED.md
