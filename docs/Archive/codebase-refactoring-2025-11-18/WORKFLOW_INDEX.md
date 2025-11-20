# Complete Workflow Index - REVISED

**Date:** 2025-11-18 (Revision 1)
**Supersedes:** WORKFLOW_INDEX.md (2025-11-17)
**Total Workflows:** 73 (was 67)
**Progress:** 3/73 complete (4.1%)

---

## Quick Navigation

| Phase | Workflows | Status | Duration | Priority |
|-------|-----------|--------|----------|----------|
| [Phase 1: Server Services](#phase-1-server-services-extraction) | 35 (was 25) | 3/35 (8.6%) | 6-8 days | High |
| [Phase 2: Helper Utilities](#phase-2-helper-utilities) | 12 | 0/12 (0%) | 2-3 days | **CRITICAL - Start here!** |
| [Phase 3: Core Modules](#phase-3-core-modules-split) | 15 | 0/15 (0%) | 4-5 days | High |
| [Phase 4: Frontend](#phase-4-frontend-refactoring) | 16 | 0/16 (0%) | 3-4 days | High |
| [Phase 5: Imports](#phase-5-import-structure) | 5 | 0/5 (0%) | 1-2 days | Medium |
| **TOTAL** | **73** | **3/73 (4.1%)** | **17-22 days** | - |

---

## Phase 1: Server Services Extraction (35 workflows)

**File:** `app/server/server.py` (2,103 lines)
**Target:** Reduce to <400 lines by creating 10 service modules
**Status:** 3/35 complete (8.6%)
**Duration:** 6-8 days

---

### 1.1: WebSocket Manager ✅ **COMPLETED** (3 workflows)

- **✅ Workflow 1.1.1** - Create WebSocket Manager Module (1-2h, Low)
  - File: `app/server/services/websocket_manager.py` (138 lines)
  - Extract: ConnectionManager class from server.py
  - Status: **COMPLETE** - Module exists

- **✅ Workflow 1.1.2** - Create WebSocket Manager Tests (1-2h, Low)
  - File: `app/server/tests/services/test_websocket_manager.py` (335 lines)
  - Status: **COMPLETE** - Comprehensive tests added in PR #45

- **✅ Workflow 1.1.3** - Integrate WebSocket Manager into server.py (30min, Low)
  - Update: server.py line 87 imports from services.websocket_manager
  - Status: **COMPLETE** - Integrated and tested

---

### 1.2: Background Tasks Manager ❌ **NOT STARTED** (4 workflows)

- **❌ Workflow 1.2.1** - Create Background Tasks Module (2-3h, Medium)
  - File: `app/server/services/background_tasks.py` (~150 lines)
  - Extract from server.py:
    - `watch_workflows()` (lines 272-297)
    - `watch_routes()` (lines 299-324)
    - `watch_workflow_history()` (lines 394-420)
  - Create BackgroundTaskManager class wrapping all 3 watchers

- **❌ Workflow 1.2.2** - Create Background Tasks Tests (2-3h, Medium)
  - File: `app/server/tests/services/test_background_tasks.py`
  - Test each watcher independently
  - Test manager lifecycle (start_all, stop_all)

- **❌ Workflow 1.2.3** - Integrate Background Tasks into server.py (1h, Low)
  - Update: server.py lines 114-138 (lifespan function)
  - Replace inline task creation with BackgroundTaskManager

- **❌ Workflow 1.2.4** - Performance Testing for Background Tasks (1h, Low)
  - Verify no memory leaks in long-running watchers
  - Benchmark broadcast performance

---

### 1.3: Workflow Service ❌ **NOT STARTED** (5 workflows)

- **❌ Workflow 1.3.1** - Create Workflow Service Module - Core Functions (2-3h, Medium)
  - File: `app/server/services/workflow_service.py` (~450 lines)
  - Extract from server.py:
    - `get_workflows_data()` (lines 167-230)
    - `get_workflow_history_data()` (lines 326-392)
  - Create WorkflowService class

- **❌ Workflow 1.3.2** - Add Workflow Service API Endpoints (2h, Medium)
  - Extract endpoints:
    - GET `/api/workflows` (lines 1709-1719)
    - GET `/api/workflows/{adw_id}/costs` (lines 1199-1221)
    - GET `/api/workflow-catalog` (lines 1721-1789)
    - POST `/api/workflows/batch` (lines 1413-1473)

- **❌ Workflow 1.3.3** - Add Workflow History Endpoints (2h, Medium)
  - Extract endpoints:
    - GET `/api/workflow-history` (lines 1302-1340)
    - POST `/api/workflow-history/resync` (lines 1342-1411)

- **❌ Workflow 1.3.4** - Create Workflow Service Tests (2-3h, Medium)
  - File: `app/server/tests/services/test_workflow_service.py`
  - Test data fetching, caching, filtering, pagination

- **❌ Workflow 1.3.5** - Integrate Workflow Service into server.py (1h, Low)
  - Update server.py to import and use WorkflowService
  - Remove extracted code
  - Verify all endpoints work

---

### 1.4: Health Service ❌ **NOT STARTED** (6 workflows)

- **❌ Workflow 1.4.1** - Create Health Service Module - Core Structure (1-2h, Low)
  - File: `app/server/services/health_service.py` (~350 lines)
  - Create HealthService class skeleton

- **❌ Workflow 1.4.2** - Implement Backend and Database Health Checks (1-2h, Low)
  - Extract from server.py:
    - `health_check()` (lines 591-620)
    - Database connectivity check from `get_system_status()` (lines 622-695)

- **❌ Workflow 1.4.3** - Implement Service Health Checks (2h, Medium)
  - Extract from server.py lines 697-855:
    - Webhook service check
    - GitHub webhook check
    - Frontend check

- **❌ Workflow 1.4.4** - Implement Cloudflare Tunnel Health Check (1h, Low)
  - Extract from server.py lines 725-730, 946-950, 1097-1102
  - Consolidate `ps aux` grep logic

- **❌ Workflow 1.4.5** - Create Health Service Tests (2-3h, Medium)
  - File: `app/server/tests/services/test_health_service.py`
  - Mock external services (subprocess, HTTP calls)
  - Test each health check independently

- **❌ Workflow 1.4.6** - Integrate Health Service into server.py (1h, Low)
  - Update endpoints:
    - GET `/api/health` (line 591)
    - GET `/api/system-status` (line 622)
    - GET `/api/services/github-webhook/health` (line 968)

---

### 1.5: Service Controller ❌ **NOT STARTED** (5 workflows)

- **❌ Workflow 1.5.1** - Create Service Controller Module (2-3h, Medium)
  - File: `app/server/services/service_controller.py` (~250 lines)
  - Extract from server.py:
    - `lifespan()` context manager (lines 114-138)
    - Startup/shutdown logic

- **❌ Workflow 1.5.2** - Add Webhook Service Management (2h, Medium)
  - Extract from server.py:
    - `start_webhook_service()` (lines 857-911)
    - Webhook health check logic (lines 862-866, 1998-2050)

- **❌ Workflow 1.5.3** - Add Cloudflare Tunnel Management (2h, Medium)
  - Extract from server.py:
    - `restart_cloudflare_tunnel()` (lines 913-966)
    - Tunnel process checks (lines 725-730, 926-929)

- **❌ Workflow 1.5.4** - Add GitHub Webhook Redelivery (1-2h, Low)
  - Extract from server.py:
    - `redeliver_github_webhook()` (lines 1054-1183)

- **❌ Workflow 1.5.5** - Create Service Controller Tests and Integration (2-3h, Medium)
  - File: `app/server/tests/services/test_service_controller.py`
  - Mock subprocess calls
  - Test start/stop/restart logic
  - Integrate into server.py

---

### 1.6: Query Service ❌ **NOT STARTED** (3 workflows)

- **❌ Workflow 1.6.1** - Create Query Service Module (2h, Medium)
  - File: `app/server/services/query_service.py` (~200 lines)
  - Extract endpoints:
    - POST `/api/query` (lines 463-500)
    - GET `/api/generate-random-query` (lines 563-589)

- **❌ Workflow 1.6.2** - Create Query Service Tests (2h, Medium)
  - File: `app/server/tests/services/test_query_service.py`
  - Test NL query processing, SQL generation

- **❌ Workflow 1.6.3** - Integrate Query Service (1h, Low)
  - Update server.py imports and endpoints

---

### 1.7: Data Service ❌ **NOT STARTED** (3 workflows)

- **❌ Workflow 1.7.1** - Create Data Service Module (1-2h, Low)
  - File: `app/server/services/data_service.py` (~150 lines)
  - Extract endpoints:
    - POST `/api/upload` (lines 422-461)
    - DELETE `/api/table/{table_name}` (lines 1791-1826)

- **❌ Workflow 1.7.2** - Create Data Service Tests (2h, Medium)
  - File: `app/server/tests/services/test_data_service.py`
  - Test file uploads, table deletion, validation

- **❌ Workflow 1.7.3** - Integrate Data Service (1h, Low)
  - Update server.py

---

### 1.8: Export Service ❌ **NOT STARTED** (3 workflows)

- **❌ Workflow 1.8.1** - Create Export Service Module (1-2h, Low)
  - File: `app/server/services/export_service.py` (~120 lines)
  - Extract endpoints:
    - POST `/api/export/table` (lines 1828-1860)
    - POST `/api/export/query` (lines 1862-1881)

- **❌ Workflow 1.8.2** - Create Export Service Tests (1-2h, Low)
  - File: `app/server/tests/services/test_export_service.py`

- **❌ Workflow 1.8.3** - Integrate Export Service (30min, Low)

---

### 1.9: NL Service ❌ **NOT STARTED** (3 workflows)

- **❌ Workflow 1.9.1** - Create NL Service Module (2-3h, Medium)
  - File: `app/server/services/nl_service.py` (~250 lines)
  - Extract endpoints:
    - POST `/api/request` (lines 1883-1957)
    - GET `/api/preview/{request_id}` (lines 1959-1975)
    - GET `/api/preview/{request_id}/cost` (lines 1977-1996)
    - POST `/api/confirm/{request_id}` (lines 2052-2103)

- **❌ Workflow 1.9.2** - Create NL Service Tests (2h, Medium)
  - File: `app/server/tests/services/test_nl_service.py`

- **❌ Workflow 1.9.3** - Integrate NL Service (1h, Low)

---

### 1.10: Analytics Service ❌ **NOT STARTED** (3 workflows)

- **❌ Workflow 1.10.1** - Create Analytics Service Module (2-3h, Medium)
  - File: `app/server/services/analytics_service.py` (~300 lines)
  - Extract endpoints:
    - GET `/api/workflow-analytics/{adw_id}` (lines 1475-1522)
    - GET `/api/workflow-trends` (lines 1524-1640)
    - GET `/api/cost-predictions` (lines 1642-1707)

- **❌ Workflow 1.10.2** - Create Analytics Service Tests (2-3h, Medium)
  - File: `app/server/tests/services/test_analytics_service.py`

- **❌ Workflow 1.10.3** - Integrate Analytics Service (1h, Low)

---

## Phase 2: Helper Utilities (12 workflows) ⭐ **START HERE!**

**Goal:** Eliminate ~420 lines of code duplication
**Status:** 0/12 complete (0%)
**Duration:** 2-3 days
**Priority:** **CRITICAL**

---

### 2.1: DatabaseManager (4 workflows)

- **❌ Workflow 2.1.1** - Create DatabaseManager Module (2-3h, Low)
  - File: `app/server/core/db_manager.py` (~100 lines)
  - Based on good pattern from workflow_history.py:184
  - Features: Context manager, connection pooling, retry logic

- **❌ Workflow 2.1.2** - Create DatabaseManager Tests (2h, Low)
  - File: `app/server/tests/core/test_db_manager.py`
  - Test: Context manager, rollback on error, row factory, retries

- **❌ Workflow 2.1.3** - Migrate server.py to DatabaseManager (2-3h, Medium)
  - Update 4 occurrences (lines 596, 664, 1801, 1836)
  - Eliminates manual connection management

- **❌ Workflow 2.1.4** - Migrate Remaining Files to DatabaseManager (2-3h, Medium)
  - file_processor.py (3 occurrences: lines 57, 129, 289)
  - sql_processor.py (2 occurrences: lines 16, 64)
  - insights.py (1 occurrence: line 16)
  - Total: Eliminate 25+ duplicated connection patterns

---

### 2.2: LLMClientManager (3 workflows)

- **❌ Workflow 2.2.1** - Create LLMClientManager Module (2-3h, Medium)
  - File: `app/server/core/llm_client_manager.py` (~120 lines)
  - Features: Singleton clients, routing logic, error handling

- **❌ Workflow 2.2.2** - Create LLMClientManager Tests (2h, Medium)
  - File: `app/server/tests/core/test_llm_client_manager.py`
  - Mock API calls, test routing logic

- **❌ Workflow 2.2.3** - Migrate Files to LLMClientManager (1-2h, Low)
  - nl_processor.py (2 occurrences: lines 37, 104)
  - llm_processor.py (3 occurrences: lines 20, 159, 254-288)
  - Total: Eliminate 6+ duplicated client initializations

---

### 2.3: ProcessManager (3 workflows)

- **❌ Workflow 2.3.1** - Create ProcessManager Module (2-3h, Medium)
  - File: `app/server/core/process_manager.py` (~150 lines)
  - Utilities:
    - `check_process_running(pattern)` - Consolidates 3 `ps aux` calls
    - `github_api_call(endpoint, method)` - Consolidates 4 `gh api` calls
    - `start_background_service(cmd, cwd)` - Consolidates 2 Popen patterns

- **❌ Workflow 2.3.2** - Create ProcessManager Tests (2h, Medium)
  - File: `app/server/tests/core/test_process_manager.py`
  - Mock subprocess calls

- **❌ Workflow 2.3.3** - Migrate server.py to ProcessManager (2-3h, Medium)
  - Update 12 subprocess calls
  - Lines: 725-730, 756-761, 862-866, 879-885, 926-929, 936-941, 946-950, 985-990, 1084-1092, 1097-1102, 1125-1130, 1149-1154

---

### 2.4: Frontend Formatters ⭐ **QUICKEST WIN** (2 workflows)

- **❌ Workflow 2.4.1** - Create Frontend Formatters Module (2h, Low)
  - File: `app/client/src/utils/formatters.ts` (~150 lines)
  - Functions:
    - Date/time: `formatDate()`, `formatDuration()`, `formatRelativeTime()`
    - Numbers: `formatCost()`, `formatNumber()`, `formatPercentage()`, `formatTokenCount()`
    - Data: `formatBytes()`, `truncateText()`
    - Workflow: `calculateBudgetDelta()`, `calculateCacheSavings()`, `getStatusColor()`, `getClassificationColor()`

- **❌ Workflow 2.4.2** - Migrate Components and Create Tests (2-3h, Medium)
  - Migrate:
    - WorkflowHistoryCard.tsx (lines 17-100)
    - SimilarWorkflowsComparison.tsx
    - TokenBreakdownChart.tsx
    - CostBreakdownChart.tsx
    - CostVisualization.tsx
  - File: `app/client/src/utils/__tests__/formatters.test.ts`
  - Total: Eliminate 50+ lines of inline formatting

---

## Phase 3: Core Modules Split (15 workflows)

**Goal:** Split 2 large modules into focused submodules
**Status:** 0/15 complete (0%)
**Duration:** 4-5 days

---

### 3A: workflow_history.py Split (8 workflows)

**Current:** 1,349 lines | **Target:** 8 modules of ~150-220 lines each

- **❌ Workflow 3A.1** - Create Directory Structure and Base Infrastructure (1-2h, Low)
  - Create: `app/server/core/workflow_history/` directory
  - Create: `__init__.py` with public API exports (~50 lines)
  - Ensures backwards compatibility

- **❌ Workflow 3A.2** - Extract database.py Module (2-3h, Medium)
  - File: `app/server/core/workflow_history/database.py` (~220 lines)
  - Extract from lines 184-470:
    - `get_db_connection()` context manager
    - `init_db()`, `insert_workflow()`, `update_workflow()`
    - `get_workflow_by_id()`, `get_workflow_by_adw_id()`
    - `get_workflow_history()`, `delete_workflow()`

- **❌ Workflow 3A.3** - Extract scanner.py Module (2h, Low)
  - File: `app/server/core/workflow_history/scanner.py` (~180 lines)
  - Extract from lines 731-853:
    - `scan_agents_directory()` - Scans agents/ for state files
    - `infer_workflow_status()` - Determines status from artifacts

- **❌ Workflow 3A.4** - Extract enrichment.py Module (2-3h, Medium)
  - File: `app/server/core/workflow_history/enrichment.py` (~200 lines)
  - Extract from lines 615-729:
    - `load_all_cost_data()` - Loads conversation_log.json files
    - `enrich_workflow_with_cost_data()` - Enriches workflow metadata

- **❌ Workflow 3A.5** - Extract analytics.py Module (2h, Low)
  - File: `app/server/core/workflow_history/analytics.py` (~150 lines)
  - Extract analytics helper functions (currently inline in sync process)

- **❌ Workflow 3A.6** - Extract similarity.py Module (2h, Medium)
  - File: `app/server/core/workflow_history/similarity.py` (~120 lines)
  - Extract from lines 1277-1349:
    - `calculate_workflow_similarity()` - Similarity scoring

- **❌ Workflow 3A.7** - Extract resync.py Module (2h, Low)
  - File: `app/server/core/workflow_history/resync.py` (~180 lines)
  - Extract from lines 1170-1276:
    - `resync_workflow_cost()` - Single workflow resync
    - `resync_all_completed_workflows()` - Batch resync

- **❌ Workflow 3A.8** - Create sync.py Orchestration and Integration Tests (3h, Medium)
  - File: `app/server/core/workflow_history/sync.py` (~150 lines)
  - Extract from lines 856-1169:
    - `sync_workflow_history()` - Main orchestration
  - File: `app/server/tests/test_workflow_history_integration.py`
  - Test: Complete sync process, verify backwards compatibility

---

### 3B: workflow_analytics.py Split (7 workflows)

**Current:** 865 lines | **Target:** 9 modules of ~80-120 lines each

- **❌ Workflow 3B.1** - Create Directory Structure and Base Scorer Class (2h, Medium)
  - Create: `app/server/core/workflow_analytics/` directory
  - Create: `scoring/base.py` with BaseScorer abstract class

- **❌ Workflow 3B.2** - Extract clarity_score.py (1.5h, Low)
  - File: `app/server/core/workflow_analytics/scoring/clarity_score.py` (~100 lines)

- **❌ Workflow 3B.3** - Extract cost_efficiency_score.py (2h, Medium)
  - File: `app/server/core/workflow_analytics/scoring/cost_efficiency_score.py` (~120 lines)

- **❌ Workflow 3B.4** - Extract performance_score.py and quality_score.py (2h, Medium)
  - Files: performance_score.py (~90 lines), quality_score.py (~100 lines)

- **❌ Workflow 3B.5** - Extract similarity.py and anomalies.py (2h, Medium)
  - Files: similarity.py (~80 lines), anomalies.py (~80 lines)

- **❌ Workflow 3B.6** - Extract recommendations.py and Helper Modules (2h, Medium)
  - Files: recommendations.py (~100 lines), temporal.py (~100 lines), complexity.py (~120 lines)

- **❌ Workflow 3B.7** - Integration Tests and Cleanup (2h, Medium)
  - File: `__init__.py` with public API
  - Tests: Verify backwards compatibility
  - Remove original workflow_analytics.py

---

## Phase 4: Frontend Component Refactoring (16 workflows)

**Goal:** Split large components, consolidate hooks
**Status:** 0/16 complete (0%)
**Duration:** 3-4 days

---

### 4.1: WorkflowHistoryCard Split (12 workflows)

**Current:** 793 lines | **Target:** 9 components of ~50-120 lines each

- **❌ Workflow 4.1.1** - Extract Utility Functions (1-2h, Low)
  - Move lines 17-100 to `utils/workflowHelpers.ts`
  - Or migrate to formatters.ts (if Phase 2.4 done first)

- **❌ Workflow 4.1.2** - Create Component Directory Structure (30min, Low)
  - Create: `app/client/src/components/workflow-history/` directory
  - Create: `sections/` subdirectory

- **❌ Workflow 4.1.3** - Extract CostEconomicsSection Component (2h, Medium)
  - File: `sections/CostEconomicsSection.tsx` (~100 lines)
  - Budget comparison, cost breakdown chart, per-step analysis

- **❌ Workflow 4.1.4** - Extract TokenAnalysisSection Component (2h, Medium)
  - File: `sections/TokenAnalysisSection.tsx` (~80 lines)
  - Token breakdown chart, cache efficiency

- **❌ Workflow 4.1.5** - Extract PerformanceAnalysisSection Component (1h, Low)
  - File: `sections/PerformanceSection.tsx` (~70 lines)
  - Phase duration chart, timeline

- **❌ Workflow 4.1.6** - Extract ErrorAnalysisSection Component (1h, Low)
  - File: `sections/ErrorAnalysisSection.tsx` (~50 lines)
  - Error count, retry info

- **❌ Workflow 4.1.7** - Extract ResourceUsageSection Component (1h, Low)
  - File: `sections/ResourceUsageSection.tsx` (~60 lines)
  - Token usage, cache metrics

- **❌ Workflow 4.1.8** - Extract WorkflowJourneySection Component (1.5h, Low)
  - File: `sections/WorkflowJourneySection.tsx` (~80 lines)
  - Phase progression, status timeline

- **❌ Workflow 4.1.9** - Extract EfficiencyScoresSection Component (1.5h, Low)
  - File: `sections/EfficiencyScoresSection.tsx` (~90 lines)
  - ScoreCard components, quality metrics

- **❌ Workflow 4.1.10** - Extract InsightsSection Component (2h, Medium)
  - File: `sections/InsightsSection.tsx` (~70 lines)
  - Recommendations, similar workflows

- **❌ Workflow 4.1.11** - Update Main WorkflowHistoryCard Component (2h, Medium)
  - File: `workflow-history/WorkflowHistoryCard.tsx` (~120 lines)
  - Import all section components, compose layout

- **❌ Workflow 4.1.12** - Create Component Tests and Integration Tests (3h, Medium)
  - Files: `__tests__/` for each section component
  - Integration test: Main card with all sections

---

### 4.2: WebSocket Hooks Consolidation (4 workflows)

**Current:** 276 lines (3 hooks) | **Target:** 125 lines (1 generic + 3 wrappers)

- **❌ Workflow 4.2.1** - Create Generic useWebSocket Hook (2-3h, Medium)
  - File: `app/client/src/hooks/useGenericWebSocket.ts` (~80 lines)
  - Generic implementation with:
    - Connection management
    - Reconnection logic (5s timeout)
    - Fallback polling with React Query
    - Type-safe message handling

- **❌ Workflow 4.2.2** - Migrate useWorkflowsWebSocket (1h, Low)
  - File: `hooks/useWorkflowsWebSocket.ts` (~15 lines)
  - Wrapper around useGenericWebSocket

- **❌ Workflow 4.2.3** - Migrate Remaining WebSocket Hooks (1-2h, Low)
  - Files: useRoutesWebSocket.ts, useWorkflowHistoryWebSocket.ts
  - Each ~15 lines

- **❌ Workflow 4.2.4** - Create Tests and Integration Tests (2h, Medium)
  - File: `hooks/__tests__/useGenericWebSocket.test.ts`
  - Test: Connection, reconnection, polling fallback
  - Integration: Verify all 3 hooks work

---

## Phase 5: Fix Import Structure (5 workflows)

**Goal:** Eliminate 37 `sys.path.insert()` hacks
**Status:** 0/5 complete (0%)
**Duration:** 1-2 days

---

- **❌ Workflow 5.1** - Create Shared Package Structure (30min, Low)
  - Create: `shared/` directory at project root
  - Create: `shared/models/`, `shared/utils/` subdirectories
  - Create: `__init__.py` files

- **❌ Workflow 5.2** - Move Shared Types to shared/models/ (1-2h, Medium)
  - Move: GitHub issue types to `shared/models/github_issue.py`
  - Move: Complexity types to `shared/models/complexity.py`
  - Move: Workflow types to `shared/models/workflow.py`

- **❌ Workflow 5.3** - Update app/server/ Imports (1-2h, Medium)
  - Update: server.py (1 file)
  - Remove: `sys.path.insert()` line 90-92
  - Update: Import from `shared.models.complexity` instead

- **❌ Workflow 5.4** - Update adws/ Imports (1-2h, Medium)
  - Update: All 36 ADW workflow files
  - Remove: `sys.path.insert()` calls
  - Update: Imports from shared package

- **❌ Workflow 5.5** - Validation and Cleanup (1-2h, Low)
  - Run: All tests to verify imports work
  - Search: No remaining `sys.path.insert()` calls
  - Verify: Deployed environments work (not just local)

---

## Progress Tracking

### Overall Progress: 3/73 Workflows (4.1%)

```
Phase 1: [███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 3/35 (8.6%)
Phase 2: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/12 (0%)
Phase 3: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/15 (0%)
Phase 4: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/16 (0%)
Phase 5: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/5  (0%)
---------------------------------------------------------
Total:   [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 3/73 (4.1%)
```

### Completed Workflows ✅
1. ✅ **1.1.1** - WebSocket Manager Module
2. ✅ **1.1.2** - WebSocket Manager Tests
3. ✅ **1.1.3** - WebSocket Manager Integration

### In Progress
- None currently

### Next Up (Recommended Order)
1. ⭐ **2.4.1** - Frontend Formatters (Quickest win, visible impact)
2. **2.1.1** - DatabaseManager (Highest impact, 25+ duplications)
3. **2.3.1** - ProcessManager (12+ duplications)
4. **2.2.1** - LLMClientManager (6+ duplications)

---

## How to Use This Index

### To Execute a Workflow:

1. **Find the workflow** in this index (e.g., "Workflow 2.4.1")
2. **Read the details** above (file path, line numbers, what to extract)
3. **Create feature branch** (if not already created)
   ```bash
   git checkout -b refactor/workflow-2.4.1-formatters
   ```
4. **Execute the workflow tasks** (see detailed phase docs for step-by-step)
5. **Run tests** to verify
6. **Mark as complete** in this index (change ❌ to ✅)
7. **Commit** with descriptive message
   ```bash
   git commit -m "refactor: Complete Workflow 2.4.1 - Create frontend formatters

   - Created app/client/src/utils/formatters.ts with 14 functions
   - Eliminated 50+ lines of inline formatting duplication
   - Added comprehensive tests (formatters.test.ts)
   - All existing tests still pass

   Workflow 2.4.1 complete (1/73)"
   ```
8. **Move to next workflow**

### Workflow Naming Convention:
- **X.Y.Z** format where:
  - **X** = Phase number (1-5)
  - **Y** = Service/component number within phase
  - **Z** = Workflow step within service
- **3A/3B** = workflow_history split / workflow_analytics split

### Time Estimates:
- **30min - 1h** = Quick task (setup, integration)
- **1-2h** = Standard workflow (module creation)
- **2-3h** = Complex workflow (comprehensive tests, migrations)

### Complexity Levels:
- **Low** - Straightforward extraction/integration, clear patterns
- **Medium** - Requires careful testing, migration, or coordination
- **High** - Complex logic, risky changes, multiple dependencies

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-17 | 1.0 | Original index created (67 workflows) |
| 2025-11-18 | 2.0 | **REVISED:** Added 6 workflows for new services, updated all line numbers, validated against actual code |

---

**Last Updated:** 2025-11-18
**Supersedes:** WORKFLOW_INDEX.md (2025-11-17)
**Related Documents:**
- [REFACTORING_ANALYSIS_REVISED.md](./REFACTORING_ANALYSIS_REVISED.md) - Detailed analysis with code evidence
- [README_REVISED.md](./README_REVISED.md) - Implementation strategy and timeline
- Individual phase files (to be created with detailed task breakdowns)
