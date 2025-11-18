# Individual Workflow Files

This directory contains 72 individual workflow files extracted from the 5 phase detailed plans (1 completed).

## Overview

Each workflow has been extracted into its own markdown file for easier navigation and execution. The workflows are organized by phase and numbered sequentially.

## File Naming Convention

Files follow this pattern:
```
PHASE{N}_WORKFLOW_{X.Y}_{Sanitized_Title}.md
```

Where:
- `{N}` = Phase number (1-5)
- `{X.Y}` = Workflow identifier (e.g., 1.1, 2.3, 3A.2)
- `{Sanitized_Title}` = Shortened, filesystem-safe version of the workflow title

## Workflow Distribution by Phase

### Phase 1: Extract Server Services (24 workflows remaining, 1 completed)
**Duration:** 4-5 days | **Status:** 4% Complete (1/25)

**Components:**
1. WebSocket Manager Service (2 workflows: 1.2-1.3) - ✅ 1.1 completed
2. Workflow Service (4 workflows: 2.1-2.4)
3. Background Tasks Service (4 workflows: 3.1-3.4)
4. Health Service (6 workflows: 4.1-4.6)
5. Service Controller (4 workflows: 5.1-5.4)
6. Integration & Migration (4 workflows: 6.1-6.4)

### Phase 2: Create Helper Utilities (12 workflows)
**Duration:** 2-3 days | **Status:** Not Started

**Components:**
1. DatabaseManager (4 workflows: 1.1-1.4)
2. LLMClient (3 workflows: 2.1-2.3)
3. ProcessRunner (3 workflows: 3.1-3.3)
4. Frontend Formatters (2 workflows: 4.1-4.2)

### Phase 3: Split Large Core Modules (15 workflows)
**Duration:** 6-7 days | **Status:** Not Started

**Components:**
- Part A: workflow_history Split (8 workflows: 3A.1-3A.8)
- Part B: workflow_analytics Split (7 workflows: 3B.1-3B.7)

### Phase 4: Frontend Component Refactoring (16 workflows)
**Duration:** 3-4 days | **Status:** Not Started

**Components:**
1. WorkflowHistoryCard Split (12 workflows: 1.1-1.12)
2. WebSocket Hooks Consolidation (4 workflows: 2.1-2.4)

### Phase 5: Fix Import Structure (5 workflows)
**Duration:** 1-2 days | **Status:** Not Started

**Components:**
1. Create Shared Package (1 workflow: 1.1)
2. Move Shared Types (1 workflow: 2.1)
3. Update app/server/ Imports (1 workflow: 3.1)
4. Update adws/ Imports (1 workflow: 4.1)
5. Validation and Cleanup (1 workflow: 5.1)

## Total Project Statistics

- **Total Workflows:** 73 atomic units (72 remaining, 1 completed)
- **Overall Progress:** 1.4% (1/73)
- **Total Duration:** 17-21 days
- **Total Phases:** 5
- **Priority Levels:** CRITICAL (2), HIGH (2), MEDIUM (1)

## Completed Workflows

Completed workflows are moved to the `completed/` subdirectory for reference:
- ✅ [1.1 - Create WebSocket Manager Module](completed/PHASE1_WORKFLOW_1.1_Create_WebSocket_Manager_Module.md) - Issue #37, PR #38

## Quick Navigation

### Phase 1 Workflows
- ~~1.1 - Create WebSocket Manager Module~~ ✅ Completed
- [1.2 - Create WebSocket Manager Tests](PHASE1_WORKFLOW_1.2_Create_WebSocket_Manager_Tests.md)
- [1.3 - Integrate WebSocket Manager](PHASE1_WORKFLOW_1.3_Integrate_WebSocket_Manager_into_serverpy.md)
- ... (see directory for complete list)

### Phase 2 Workflows
- [1.1 - Create DatabaseManager Module](PHASE2_WORKFLOW_1.1_Create_DatabaseManager_Module.md)
- [1.2 - Create DatabaseManager Tests](PHASE2_WORKFLOW_1.2_Create_DatabaseManager_Tests.md)
- ... (see directory for complete list)

### Phase 3 Workflows
- [3A.1 - Create Directory Structure](PHASE3_WORKFLOW_3A.1_Create_Directory_Structure_and_Base_Infrastructure.md)
- [3A.2 - Extract database.py Module](PHASE3_WORKFLOW_3A.2_Extract_databasepy_Module.md)
- ... (see directory for complete list)

### Phase 4 Workflows
- [1.1 - Extract Utility Functions](PHASE4_WORKFLOW_1.1_Extract_Utility_Functions_to_utils_Directory.md)
- [1.2 - Create Component Directory](PHASE4_WORKFLOW_1.2_Create_Component_Directory_Structure.md)
- ... (see directory for complete list)

### Phase 5 Workflows
- [1.1 - Create Shared Package](PHASE5_WORKFLOW_1.1_Create_Shared_Package_Directory_Structure.md)
- [2.1 - Move GitHubIssue Types](PHASE5_WORKFLOW_2.1_Move_GitHubIssue_and_Complexity_Types.md)
- ... (see directory for complete list)

## Workflow Structure

Each workflow file contains:

1. **Header**
   - Workflow ID and Title
   - Estimated Time
   - Complexity Level
   - Dependencies

2. **File Information**
   - Input Files (with line numbers)
   - Output Files (new/modified)

3. **Implementation Details**
   - Numbered task list
   - Code examples
   - Before/After comparisons

4. **Quality Assurance**
   - Acceptance Criteria (checkboxes)
   - Verification Commands

## Execution

Each workflow is executed via ZTE (Zero Touch Execution):

```bash
# 1. Create GitHub issue from workflow file
gh issue create --title "PHASE{N} {X.Y}: {Title}" --body "{workflow-content}"

# 2. Run ZTE pipeline
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```

ZTE runs all 8 phases automatically: Plan → Build → Lint → Test → Review → Document → Ship → Cleanup

## Generation

These files were automatically extracted from the phase detailed plans using:

```bash
python3 extract_workflows.py
```

**Generated:** 2025-11-17
**Source Files:** PHASE_1_DETAILED.md through PHASE_5_DETAILED.md
