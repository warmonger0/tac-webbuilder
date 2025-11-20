# Complete Workflow Index

Quick reference index for all 67 atomic workflows across 5 phases.

## Phase 1: Extract Server Services (25 workflows)

**File:** [phases/PHASE_1_DETAILED.md](./phases/PHASE_1_DETAILED.md)

### 1.1: WebSocket Manager (3 workflows)
- **Workflow 1.1.1** - Create WebSocket Manager Module (1-2h, Low)
- **Workflow 1.1.2** - Create WebSocket Manager Tests (1-2h, Low)
- **Workflow 1.1.3** - Integrate WebSocket Manager into server.py (30min, Low)

### 1.2: Workflow Service (4 workflows)
- **Workflow 1.2.1** - Create Workflow Service Module (2-3h, Medium)
- **Workflow 1.2.2** - Create Workflow Service Tests (2-3h, Medium)
- **Workflow 1.2.3** - Integrate Workflow Service into server.py (1h, Low)
- **Workflow 1.2.4** - Update Background Watchers for Workflow Service (1h, Low)

### 1.3: Background Tasks (4 workflows)
- **Workflow 1.3.1** - Create Background Tasks Manager Module (2-3h, Medium)
- **Workflow 1.3.2** - Create Background Tasks Tests (2h, Medium)
- **Workflow 1.3.3** - Integrate Background Tasks into server.py (1h, Low)
- **Workflow 1.3.4** - Add Background Task Monitoring (1h, Low)

### 1.4: Health Service (6 workflows)
- **Workflow 1.4.1** - Create Health Service Module - Core Structure (1-2h, Low)
- **Workflow 1.4.2** - Implement Backend and Database Health Checks (1-2h, Low)
- **Workflow 1.4.3** - Implement HTTP Service Health Checks (2h, Medium)
- **Workflow 1.4.4** - Implement Cloudflare Tunnel Health Check (1h, Low)
- **Workflow 1.4.5** - Create Health Service Tests (2-3h, Medium)
- **Workflow 1.4.6** - Integrate Health Service into server.py (1h, Low)

### 1.5: Service Controller (4 workflows)
- **Workflow 1.5.1** - Create Service Controller Module (2-3h, Medium)
- **Workflow 1.5.2** - Implement Service Start/Stop Methods (2h, Medium)
- **Workflow 1.5.3** - Create Service Controller Tests (2h, Medium)
- **Workflow 1.5.4** - Integrate Service Controller into server.py (1h, Low)

### 1.6: Integration & Migration (4 workflows)
- **Workflow 1.6.1** - Create Integration Test Suite (2-3h, Medium)
- **Workflow 1.6.2** - Update server.py - Remove Extracted Code (1-2h, Low)
- **Workflow 1.6.3** - Performance Benchmarking (2h, Medium)
- **Workflow 1.6.4** - Documentation and Cleanup (1-2h, Low)

---

## Phase 2: Create Helper Utilities (12 workflows)

**File:** [phases/PHASE_2_DETAILED.md](./phases/PHASE_2_DETAILED.md)

### 2.1: DatabaseManager (4 workflows)
- **Workflow 2.1.1** - Create DatabaseManager Module (2-3h, Low)
- **Workflow 2.1.2** - Create DatabaseManager Tests (2h, Low)
- **Workflow 2.1.3** - Migrate workflow_history.py to DatabaseManager (2-3h, Medium)
- **Workflow 2.1.4** - Migrate Remaining Files to DatabaseManager (2-3h, Medium)

### 2.2: LLMClient (3 workflows)
- **Workflow 2.2.1** - Create LLMClient Module (2-3h, Medium)
- **Workflow 2.2.2** - Create LLMClient Tests (2h, Medium)
- **Workflow 2.2.3** - Migrate Files to LLMClient (1-2h, Low)

### 2.3: ProcessRunner (3 workflows)
- **Workflow 2.3.1** - Create ProcessRunner Module (2-3h, Medium)
- **Workflow 2.3.2** - Create ProcessRunner Tests (2h, Medium)
- **Workflow 2.3.3** - Migrate Files to ProcessRunner (2-3h, Medium)

### 2.4: Frontend Formatters (2 workflows)
- **Workflow 2.4.1** - Create Frontend Formatters Module (2h, Low)
- **Workflow 2.4.2** - Migrate Components to Use Formatters and Create Tests (2-3h, Medium)

---

## Phase 3: Split Large Core Modules (15 workflows)

**File:** [phases/PHASE_3_DETAILED.md](./phases/PHASE_3_DETAILED.md)

### 3A: workflow_history.py Split (8 workflows)
- **Workflow 3A.1** - Create Directory Structure and Base Infrastructure (1-2h, Low)
- **Workflow 3A.2** - Extract database.py Module (2-3h, Medium)
- **Workflow 3A.3** - Extract scanner.py Module (2h, Low)
- **Workflow 3A.4** - Extract enrichment.py Module (2-3h, Medium)
- **Workflow 3A.5** - Extract analytics.py Module (2h, Low)
- **Workflow 3A.6** - Extract similarity.py Module (2h, Medium)
- **Workflow 3A.7** - Extract resync.py Module (2h, Low)
- **Workflow 3A.8** - Create sync.py Orchestration and Integration Tests (3h, Medium)

### 3B: workflow_analytics.py Split (7 workflows)
- **Workflow 3B.1** - Create Directory Structure and Base Scorer Class (2h, Medium)
- **Workflow 3B.2** - Extract clarity_score.py (1.5h, Low)
- **Workflow 3B.3** - Extract cost_efficiency_score.py (2h, Medium)
- **Workflow 3B.4** - Extract performance_score.py and quality_score.py (2h, Medium)
- **Workflow 3B.5** - Extract similarity.py and anomalies.py (2h, Medium)
- **Workflow 3B.6** - Extract recommendations.py and Helper Modules (2h, Medium)
- **Workflow 3B.7** - Integration Tests and Cleanup (2h, Medium)

---

## Phase 4: Frontend Component Refactoring (16 workflows)

**File:** [phases/PHASE_4_DETAILED.md](./phases/PHASE_4_DETAILED.md)

### 4.1: WorkflowHistoryCard Split (12 workflows)
- **Workflow 4.1.1** - Extract Utility Functions (1-2h, Low)
- **Workflow 4.1.2** - Create Component Directory Structure (30min, Low)
- **Workflow 4.1.3** - Extract CostEconomicsSection Component (2h, Medium)
- **Workflow 4.1.4** - Extract TokenAnalysisSection Component (2h, Medium)
- **Workflow 4.1.5** - Extract PerformanceAnalysisSection Component (1h, Low)
- **Workflow 4.1.6** - Extract ErrorAnalysisSection Component (1h, Low)
- **Workflow 4.1.7** - Extract ResourceUsageSection Component (1h, Low)
- **Workflow 4.1.8** - Extract WorkflowJourneySection Component (1.5h, Low)
- **Workflow 4.1.9** - Extract EfficiencyScoresSection Component (1.5h, Low)
- **Workflow 4.1.10** - Extract InsightsSection Component (2h, Medium)
- **Workflow 4.1.11** - Update Main WorkflowHistoryCard Component (2h, Medium)
- **Workflow 4.1.12** - Create Component Tests and Integration Tests (3h, Medium)

### 4.2: WebSocket Hooks Consolidation (4 workflows)
- **Workflow 4.2.1** - Create Generic useWebSocket Hook (2-3h, Medium)
- **Workflow 4.2.2** - Migrate useWorkflowsWebSocket (1h, Low)
- **Workflow 4.2.3** - Migrate Remaining WebSocket Hooks (1-2h, Low)
- **Workflow 4.2.4** - Create Tests and Integration Tests (2h, Medium)

---

## Phase 5: Fix Import Structure (5 workflows)

**File:** [phases/PHASE_5_DETAILED.md](./phases/PHASE_5_DETAILED.md)

- **Workflow 5.1** - Create Shared Package Structure (30min, Low)
- **Workflow 5.2** - Move Shared Types to shared/models/ (1-2h, Medium)
- **Workflow 5.3** - Update app/server/ Imports (1-2h, Medium)
- **Workflow 5.4** - Update adws/ Imports (1-2h, Medium)
- **Workflow 5.5** - Validation and Cleanup (1-2h, Low)

---

## How to Use This Index

### To Execute a Workflow:

1. **Find the workflow** in this index
2. **Open the detailed phase file** linked above
3. **Navigate to the workflow section** (use search or line numbers)
4. **Read the complete workflow** (tasks, code, tests, verification)
5. **Execute tasks sequentially**
6. **Check acceptance criteria**
7. **Run verification commands**
8. **Commit and move to next workflow**

### Workflow Naming Convention:

- **X.Y.Z** format where:
  - **X** = Phase number (1-5)
  - **Y** = Component number within phase
  - **Z** = Workflow number within component

- **3A/3B** format for Phase 3:
  - **3A** = workflow_history.py split
  - **3B** = workflow_analytics.py split

### Time Estimates:

Each workflow lists estimated time:
- **30min - 1h** = Quick task (extraction, integration)
- **1-2h** = Standard workflow (module creation + basic tests)
- **2-3h** = Complex workflow (comprehensive tests, migrations)

### Complexity Levels:

- **Low** - Straightforward extraction/integration
- **Medium** - Requires careful testing or migration
- **High** - Complex logic or risky changes

---

## Progress Tracking

Use this as a checklist:

### Phase 1 (25 workflows)
- [ ] 1.1.1 - [ ] 1.1.2 - [ ] 1.1.3
- [ ] 1.2.1 - [ ] 1.2.2 - [ ] 1.2.3 - [ ] 1.2.4
- [ ] 1.3.1 - [ ] 1.3.2 - [ ] 1.3.3 - [ ] 1.3.4
- [ ] 1.4.1 - [ ] 1.4.2 - [ ] 1.4.3 - [ ] 1.4.4 - [ ] 1.4.5 - [ ] 1.4.6
- [ ] 1.5.1 - [ ] 1.5.2 - [ ] 1.5.3 - [ ] 1.5.4
- [ ] 1.6.1 - [ ] 1.6.2 - [ ] 1.6.3 - [ ] 1.6.4

### Phase 2 (12 workflows)
- [ ] 2.1.1 - [ ] 2.1.2 - [ ] 2.1.3 - [ ] 2.1.4
- [ ] 2.2.1 - [ ] 2.2.2 - [ ] 2.2.3
- [ ] 2.3.1 - [ ] 2.3.2 - [ ] 2.3.3
- [ ] 2.4.1 - [ ] 2.4.2

### Phase 3 (15 workflows)
- [ ] 3A.1 - [ ] 3A.2 - [ ] 3A.3 - [ ] 3A.4 - [ ] 3A.5 - [ ] 3A.6 - [ ] 3A.7 - [ ] 3A.8
- [ ] 3B.1 - [ ] 3B.2 - [ ] 3B.3 - [ ] 3B.4 - [ ] 3B.5 - [ ] 3B.6 - [ ] 3B.7

### Phase 4 (16 workflows)
- [ ] 4.1.1 - [ ] 4.1.2 - [ ] 4.1.3 - [ ] 4.1.4 - [ ] 4.1.5 - [ ] 4.1.6
- [ ] 4.1.7 - [ ] 4.1.8 - [ ] 4.1.9 - [ ] 4.1.10 - [ ] 4.1.11 - [ ] 4.1.12
- [ ] 4.2.1 - [ ] 4.2.2 - [ ] 4.2.3 - [ ] 4.2.4

### Phase 5 (5 workflows)
- [ ] 5.1 - [ ] 5.2 - [ ] 5.3 - [ ] 5.4 - [ ] 5.5

**Total:** 0/67 workflows completed (0%)

---

**Last Updated:** 2025-11-17
**Related Documents:**
- [IMPLEMENTATION_ORCHESTRATION.md](./IMPLEMENTATION_ORCHESTRATION.md) - Master execution guide
- [phases/README.md](./phases/README.md) - Phase overview
- Individual phase files listed above
