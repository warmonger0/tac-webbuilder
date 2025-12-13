# Feature Implementation Roadmap
**Sequential Implementation via tac-webbuilder ADW Workflows**

**Status:** Ready for Execution
**Last Updated:** 2025-12-01
**Total Estimated Duration:** 12-16 weeks
**Total Estimated Cost:** $72-$156 (via ADW workflows)

---

## 🎯 Implementation Strategy

### **Sequential Execution Rules**

1. **One workflow at a time** - Submit next issue only after current one is COMPLETE
2. **Unblock before proceeding** - If workflow gets blocked, fix before moving on
3. **Each feature = 1 GitHub issue** - Submitted via tac-webbuilder UI
4. **Test before next** - Verify feature works before submitting next request
5. **Track progress** - Update completion status in this document

### **Workflow States**

- ⏳ **Pending** - Not yet submitted
- 🏗️ **In Progress** - ADW workflow running
- 🚧 **Blocked** - Workflow stuck, needs intervention
- ✅ **Complete** - Merged and tested
- ❌ **Failed** - Workflow failed, needs retry or redesign

---

## 📊 Progress Tracker

| # | Feature | Status | Issue # | PR # | Cost | Duration | Completed |
|---|---------|--------|---------|------|------|----------|-----------|
| 1.1 | UI Layout Restructuring | ⏳ Pending | - | - | - | - | - |
| 1.2 | Work Log System | ⏳ Pending | - | - | - | - | - |
| 2.1 | Plans Panel | ⏳ Pending | - | - | - | - | - |
| 2.2 | Template System | ⏳ Pending | - | - | - | - | - |
| 3.1 | Review Panel | ⏳ Pending | - | - | - | - | - |
| 3.2 | Quality Panel (Part 1) | ⏳ Pending | - | - | - | - | - |
| 3.3 | Quality Panel (Part 2) | ⏳ Pending | - | - | - | - | - |
| 4.1 | Quality Gates (Part 1) | ⏳ Pending | - | - | - | - | - |
| 4.2 | Quality Gates (Part 2) | ⏳ Pending | - | - | - | - | - |
| 4.3 | Enhanced Patterns Panel | ⏳ Pending | - | - | - | - | - |
| 5.1 | Context Review Agent | ⏳ Pending | - | - | - | - | - |

**How to Update:**
- Change status when submitting/completing
- Add GitHub issue # when created
- Add PR # when PR created
- Record cost from workflow dashboard
- Record actual duration
- Add completion date when merged

---

## 🚀 Phase 1: Foundation & Quick Wins (Week 1)

### **Checkpoint 1.0 - Before Starting**

**Pre-Flight Checks:**
- [ ] tac-webbuilder running at http://localhost:5173
- [ ] Backend server running (port 8000)
- [ ] Database accessible
- [ ] GitHub integration working
- [ ] Work Log tab empty (baseline)

---

### **Issue 1.1: UI Layout Restructuring**

**⏱️ Estimated:** 2-3 days | **💰 Estimated Cost:** $0.50-$1.50 | **Priority:** HIGH

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Fix ZTE Hopper Queue Card Layout with Equal Margins

Description:
Restructure the New Request tab layout to keep the Create New Request (CNR) card centered at a fixed width while positioning the ZTE Hopper Queue card to its right with equal margins on both sides.

Context:
- Current state: Layout uses CSS Grid (grid-cols-1 lg:grid-cols-3) in RequestFormCore.tsx
- CNR card spans 2 columns (lg:col-span-2), Hopper Queue spans 1 column (lg:col-span-1)
- Problem: Hopper Queue has different margins on each side
- Goal: CNR card stays centered with fixed width, Hopper Queue has equal margins (CNR↔Hopper == Hopper↔viewport)
- Integration: This is purely a CSS/layout change, no logic changes

Technical Specifications:
1. Change container from grid to flexbox layout
2. CNR card: fixed width = 50% of container (flex-shrink-0)
3. Hopper Queue: flexible width (flex-grow) to fill remaining space
4. Calculate margins to ensure equal spacing
5. Maintain responsive behavior at all breakpoints
6. Keep System Status row (second row) layout unchanged

Files to Modify:
- app/client/src/components/RequestFormCore.tsx (lines 59-84)
  - Change: grid grid-cols-1 lg:grid-cols-3 → flex gap-4
  - Change: lg:col-span-2 → flex-shrink-0 with calculated width
  - Change: lg:col-span-1 → flex-grow
  - Ensure items-stretch is maintained for equal heights

Acceptance Criteria:
- [ ] CNR card maintains fixed width (50% of container) at all viewport sizes
- [ ] Hopper Queue card fills remaining space
- [ ] Margin between CNR and Hopper equals margin between Hopper and viewport edge
- [ ] Layout tested at 1024px, 1440px, 1920px widths
- [ ] No visual regressions in second row (System Status + ADW Monitor)
- [ ] Mobile responsiveness maintained (stacks vertically on small screens)

Testing Requirements:
- Visual regression testing at multiple viewport widths
- Measure margins using browser dev tools to verify equality
- Test with different content heights in Hopper Queue
- Verify no layout shift when content loads

Dependencies: None

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Check "Workflows" tab for progress
- [ ] Watch ADW Monitor Card for current phase
- [ ] Note any errors in console

**2. Review PR:**
- [ ] Check files changed match specification
- [ ] Review CSS changes are minimal and correct
- [ ] No unintended side effects

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Start frontend
cd app/client && bun run dev

# Test in browser:
# - Navigate to http://localhost:5173
# - Go to "New Request" tab
# - Measure margins with dev tools (F12 → Elements → hover over elements)
# - Test at 1024px, 1440px, 1920px widths
# - Test on mobile (< 768px)
```

**4. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**5. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record GitHub issue # and PR #
- [ ] Record actual cost and duration
- [ ] Add completion date

#### **If Blocked:**

**Common Issues:**
- **TypeScript errors:** Check props passed to components
- **Layout breaks:** Verify flex properties are correct
- **Tests fail:** Update snapshots if visual changes expected

**Unblocking Steps:**
1. Check ADW workflow logs for specific error
2. If test failures: Submit refinement issue with specific fixes
3. If build failures: Check linting/TypeScript errors
4. If stuck: Create follow-up issue with detailed error description

**Do NOT proceed to Issue 1.2 until this is ✅ Complete**

---

### **Checkpoint 1.1 - Before Issue 1.2**

**Verification:**
- [ ] Issue 1.1 merged to main
- [ ] Frontend builds successfully
- [ ] Layout looks correct in browser
- [ ] No console errors
- [ ] Ready to proceed

---

### **Issue 1.2: Work Log System**

**⏱️ Estimated:** 2-3 days | **💰 Estimated Cost:** $2-$5 | **Priority:** HIGH

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Implement Work Log System for Chat Session Tracking

Description:
Create a simple logging system to track what happened in each chat session. Each entry is limited to 2 sentences (280 characters max, like Twitter) and can link to the chat file context, related GitHub issues, or workflows.

Context:
- Current state: No way to track what was done in each chat session
- Problem: Work gets lost when sidetracked, no historical record of attempts
- Goal: Quick logging system to capture session summaries
- Integration: Will be used by future Plans Panel and standalone

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_work_log.sql
```sql
CREATE TABLE work_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT NOT NULL,
  summary TEXT NOT NULL CHECK(length(summary) <= 280),
  chat_file_link TEXT,
  issue_number INTEGER,
  workflow_id TEXT,
  tags TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_work_log_session ON work_log(session_id);
CREATE INDEX idx_work_log_timestamp ON work_log(timestamp DESC);
```

BACKEND API ROUTES (app/server/routes/work_log_routes.py):
- POST /api/v1/work-log - Create new entry (validate 280 char limit)
- GET /api/v1/work-log - List entries (pagination: limit, offset)
- GET /api/v1/work-log/session/{session_id} - Get all logs for a session
- DELETE /api/v1/work-log/{id} - Delete entry

BACKEND MODELS (app/server/models/work_log.py):
```python
@dataclass
class WorkLogEntry:
    id: Optional[int]
    timestamp: datetime
    session_id: str
    summary: str  # max 280 chars
    chat_file_link: Optional[str]
    issue_number: Optional[int]
    workflow_id: Optional[str]
    tags: List[str]  # JSON array
    created_at: datetime
```

BACKEND REPOSITORY (app/server/repositories/work_log_repository.py):
- create_entry(entry: WorkLogEntry) -> int
- get_all(limit: int = 50, offset: int = 0) -> List[WorkLogEntry]
- get_by_session(session_id: str) -> List[WorkLogEntry]
- delete_entry(entry_id: int) -> bool

FRONTEND COMPONENTS:
1. WorkLogPanel.tsx - Main panel showing recent logs
   - List view with filters (date, session, tags)
   - Click to expand details
   - Pagination
   - "New Entry" button

2. WorkLogEntryForm.tsx - Form for creating entries
   - Text area with character counter (280 max)
   - Optional: chat_file_link, issue_number, workflow_id
   - Tags input (multi-select)
   - Submit button
   - Validation: Enforce 280 char limit client-side

3. WorkLogCard.tsx - Individual log entry display
   - Shows summary, timestamp, tags
   - Links to issue/workflow if present
   - Delete button

FRONTEND API CLIENT (app/client/src/api/work-log-client.ts):
- createWorkLog(entry: WorkLogEntryCreate): Promise<WorkLogEntry>
- getWorkLogs(limit?: number, offset?: number): Promise<WorkLogEntry[]>
- getSessionLogs(sessionId: string): Promise<WorkLogEntry[]>
- deleteWorkLog(id: number): Promise<void>

INTEGRATION:
- Add "Work Log" tab to App.tsx (new tab: 'work-log')
- Auto-generate session_id on App.tsx mount (store in state)
- Optional: Add "Log Work" button to RequestFormCore for quick logging

Files to Create:
Backend:
- app/server/migration/add_work_log.sql
- app/server/routes/work_log_routes.py
- app/server/repositories/work_log_repository.py
- app/server/models/work_log.py

Frontend:
- app/client/src/components/WorkLogPanel.tsx
- app/client/src/components/WorkLogEntryForm.tsx
- app/client/src/components/WorkLogCard.tsx
- app/client/src/api/work-log-client.ts

Tests:
- app/server/tests/repositories/test_work_log_repository.py
- app/server/tests/routes/test_work_log_routes.py
- app/client/src/components/__tests__/WorkLogEntryForm.test.tsx
- app/server/tests/e2e/test_work_log_flow.py

Files to Modify:
- app/server/server.py (line ~80: register work_log_routes)
- app/client/src/App.tsx (add 'work-log' tab option and WorkLogPanel)

Acceptance Criteria:
- [ ] Database schema created with migration script
- [ ] Backend API routes implemented with proper validation
- [ ] 280 character limit enforced in backend and frontend
- [ ] Repository methods with error handling
- [ ] Frontend WorkLogPanel displays entries correctly
- [ ] Frontend form validates character limit before submission
- [ ] Session ID auto-generated and persisted in session
- [ ] Tags stored as JSON array and displayed as badges
- [ ] Links to issues/workflows are clickable
- [ ] Unit tests pass for repository and routes
- [ ] Integration tests pass for API endpoints
- [ ] Frontend tests pass for form validation
- [ ] E2E test: Create entry → View entries → Filter by session → Delete entry

Testing Requirements:
Backend:
- test_work_log_repository.py: Test CRUD operations
- test_work_log_routes.py: Test API endpoints, validation, error cases
- Test 280 char limit enforcement (281 chars should fail)
- Test session filtering
- Test pagination

Frontend:
- Test character counter updates correctly
- Test form submission prevents >280 chars
- Test tag input and display
- Test entry deletion

E2E:
- Full lifecycle: Create → Read → Filter → Delete
- Test with linked issue number
- Test with linked workflow ID

Dependencies: None

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Check workflow progress (will be longer than 1.1)
- [ ] Watch for database migration success
- [ ] Monitor test execution

**2. Review PR:**
- [ ] Verify migration file is correct (no typos in SQL)
- [ ] Check API routes match specification
- [ ] Verify 280 char limit in multiple places (DB, backend, frontend)
- [ ] Check frontend components render correctly

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Run migration
cd app/server
uv run python -c "from database.connection import get_connection; get_connection()"

# Run tests
uv run pytest tests/repositories/test_work_log_repository.py -v
uv run pytest tests/routes/test_work_log_routes.py -v

# Start servers
cd app/server && uv run python server.py &
cd app/client && bun run dev

# Manual test:
# 1. Go to http://localhost:5173
# 2. Click "Work Log" tab (new tab should appear)
# 3. Click "New Entry" button
# 4. Type exactly 280 characters - should accept
# 5. Type 281 characters - should reject
# 6. Create entry with tags
# 7. Verify entry appears in list
# 8. Test filter by session
# 9. Test delete entry
```

**4. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**5. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **Migration fails:** Check SQL syntax, table already exists
- **API 500 errors:** Check repository implementation, error handling
- **Character limit not enforced:** Verify validation in both backend and frontend
- **Tests fail:** Check test data, mock implementations

**Unblocking Steps:**
1. Check migration ran successfully: `sqlite3 tac-webbuilder.db ".schema work_log"`
2. Test API manually: `curl -X POST http://localhost:8000/api/v1/work-log -d '...'`
3. Check backend logs: `tail -f app/server/logs/server.log`
4. If stuck: Create refinement issue

**Do NOT proceed to Phase 2 until this is ✅ Complete**

---

### **Checkpoint 1.2 - End of Phase 1**

**Phase 1 Complete Checklist:**
- [ ] Both issues 1.1 and 1.2 are ✅ Complete
- [ ] No open issues from Phase 1
- [ ] Work Log tab visible and functional
- [ ] Can create and view work log entries
- [ ] Database schema verified
- [ ] All tests passing

**Take a break! Test the features together before Phase 2.**

**Manual Integration Test:**
1. Go to New Request tab - verify layout is correct
2. Go to Work Log tab - create first entry about Phase 1 completion
3. Verify entry saves and displays correctly

---

## 🏗️ Phase 2: Planning & Templates (Week 2-3)

### **Checkpoint 2.0 - Before Starting**

**Prerequisites:**
- [ ] Phase 1 is ✅ Complete
- [ ] Work Log system is tested and working
- [ ] No blocking bugs from Phase 1

---

### **Issue 2.1: Plans Panel**

**⏱️ Estimated:** 5-7 days | **💰 Estimated Cost:** $3-$8 | **Priority:** HIGH

**Dependencies:** Work Log System (Issue 1.2)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Implement Plans Panel for Feature Attempt Tracking

Description:
Create a Plans Panel that tracks feature/bug/refactor attempts across multiple chat sessions. Plans persist until explicitly marked complete, preventing work loss when getting sidetracked. Uses Kanban-style board with states: Draft → In Progress → Blocked → Completed.

Context:
- Current state: No way to track multi-session attempts at features/bugs
- Problem: When sidetracked, lose context of what was being worked on
- Goal: Persistent tracking of plans with attempt history
- Integration: Links with Work Log system (each attempt = multiple log entries)

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_plans.sql
```sql
CREATE TABLE plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  plan_type TEXT NOT NULL CHECK(plan_type IN ('feature', 'bug', 'refactor', 'research', 'chore')),
  status TEXT NOT NULL CHECK(status IN ('draft', 'in_progress', 'blocked', 'completed')),
  priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  estimated_hours REAL,
  actual_hours REAL,
  blocked_reason TEXT,
  parent_plan_id INTEGER,
  FOREIGN KEY (parent_plan_id) REFERENCES plans(id)
);

CREATE TABLE plan_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_id INTEGER NOT NULL,
  attempt_number INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('in_progress', 'abandoned', 'completed')),
  notes TEXT,
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  ended_at DATETIME,
  outcome TEXT CHECK(outcome IN ('success', 'blocked', 'sidetracked', 'failed')),
  blockers TEXT,
  artifacts TEXT,
  FOREIGN KEY (plan_id) REFERENCES plans(id)
);

CREATE INDEX idx_plans_status ON plans(status);
CREATE INDEX idx_plans_priority ON plans(priority);
CREATE INDEX idx_plan_attempts_plan ON plan_attempts(plan_id);
CREATE INDEX idx_plan_attempts_session ON plan_attempts(session_id);
```

BACKEND API ROUTES (app/server/routes/plans_routes.py):
- POST /api/v1/plans - Create new plan
- GET /api/v1/plans - List all plans (filter by status, priority)
- GET /api/v1/plans/{plan_id} - Get single plan with attempts
- PUT /api/v1/plans/{plan_id} - Update plan (status, description, etc.)
- DELETE /api/v1/plans/{plan_id} - Delete plan
- POST /api/v1/plans/{plan_id}/attempts - Start new attempt
- PUT /api/v1/plans/{plan_id}/attempts/{attempt_id} - End attempt with outcome
- GET /api/v1/plans/{plan_id}/history - Get full history (all attempts + changes)

BACKEND MODELS (app/server/models/plan.py):
```python
@dataclass
class Plan:
    id: Optional[int]
    title: str
    description: Optional[str]
    plan_type: str  # 'feature', 'bug', 'refactor', 'research', 'chore'
    status: str  # 'draft', 'in_progress', 'blocked', 'completed'
    priority: str  # 'low', 'medium', 'high', 'critical'
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    blocked_reason: Optional[str]
    parent_plan_id: Optional[int]

@dataclass
class PlanAttempt:
    id: Optional[int]
    plan_id: int
    attempt_number: int
    session_id: str
    status: str  # 'in_progress', 'abandoned', 'completed'
    notes: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    outcome: Optional[str]  # 'success', 'blocked', 'sidetracked', 'failed'
    blockers: List[str]  # JSON array
    artifacts: List[str]  # JSON array: file paths, PR links
```

BACKEND REPOSITORY (app/server/repositories/plans_repository.py):
- create_plan(plan: Plan) -> int
- get_all_plans(status: Optional[str] = None) -> List[Plan]
- get_plan(plan_id: int) -> Optional[Plan]
- update_plan(plan_id: int, updates: dict) -> bool
- delete_plan(plan_id: int) -> bool
- create_attempt(attempt: PlanAttempt) -> int
- get_plan_attempts(plan_id: int) -> List[PlanAttempt]
- update_attempt(attempt_id: int, updates: dict) -> bool
- get_current_attempt(plan_id: int) -> Optional[PlanAttempt]

FRONTEND COMPONENTS:
1. PlansPanel.tsx - Main Kanban board
   - Four columns: Draft | In Progress | Blocked | Completed
   - Drag-and-drop to change status
   - Filter by type, priority
   - "New Plan" button
   - Card count per column

2. PlanCard.tsx - Individual plan card in Kanban
   - Title, type badge, priority badge
   - Attempt counter: "Attempt #3"
   - Last updated timestamp
   - Quick status indicators (blocked icon, etc.)
   - Click to open detail modal

3. PlanDetailModal.tsx - Full plan details
   - Editable title, description
   - Status, priority, type selectors
   - Estimated vs actual hours
   - Attempt timeline (vertical timeline view)
   - Notes from each attempt
   - Blockers list (if blocked)
   - Actions: "Start New Attempt", "Mark Complete", "Edit", "Delete"

4. PlanAttemptTimeline.tsx - Visual attempt history
   - Vertical timeline of all attempts
   - Each entry shows: attempt #, duration, outcome, notes
   - Color-coded by outcome (success=green, blocked=yellow, failed=red)

5. CreatePlanForm.tsx - Form for new plan
   - Title (required)
   - Description (textarea)
   - Type (dropdown)
   - Priority (dropdown)
   - Estimated hours (optional)

FRONTEND API CLIENT (app/client/src/api/plans-client.ts):
- createPlan(plan: PlanCreate): Promise<Plan>
- getPlans(status?: string): Promise<Plan[]>
- getPlan(planId: number): Promise<Plan>
- updatePlan(planId: number, updates: Partial<Plan>): Promise<Plan>
- deletePlan(planId: number): Promise<void>
- startAttempt(planId: number, sessionId: string): Promise<PlanAttempt>
- endAttempt(planId: number, attemptId: number, outcome: AttemptOutcome): Promise<void>
- getPlanHistory(planId: number): Promise<PlanHistory>

INTEGRATION:
- Add "Plans" tab to App.tsx
- Link work log entries to plan attempts (optional foreign key)
- Auto-update plan.updated_at when attempt added
- Calculate actual_hours from attempt durations

DRAG-AND-DROP LIBRARY:
- Use @dnd-kit/core for drag-and-drop (already a Vite/React standard)
- Or use react-beautiful-dnd (if preferred)

Files to Create:
Backend:
- app/server/migration/add_plans.sql
- app/server/routes/plans_routes.py
- app/server/repositories/plans_repository.py
- app/server/models/plan.py

Frontend:
- app/client/src/components/PlansPanel.tsx
- app/client/src/components/PlanCard.tsx
- app/client/src/components/PlanDetailModal.tsx
- app/client/src/components/PlanAttemptTimeline.tsx
- app/client/src/components/CreatePlanForm.tsx
- app/client/src/api/plans-client.ts

Tests:
- app/server/tests/repositories/test_plans_repository.py
- app/server/tests/routes/test_plans_routes.py
- app/client/src/components/__tests__/PlansPanel.test.tsx
- app/server/tests/e2e/test_plans_lifecycle.py

Files to Modify:
- app/server/server.py (register plans_routes)
- app/client/src/App.tsx (add 'plans' tab)
- app/server/models/work_log.py (add optional plan_attempt_id field)

Acceptance Criteria:
- [ ] Database schema created with proper constraints
- [ ] Backend CRUD operations working
- [ ] Plans can be created, listed, filtered by status
- [ ] Attempts can be started and ended with outcomes
- [ ] Frontend Kanban board displays plans in columns
- [ ] Drag-and-drop changes plan status
- [ ] Plan detail modal shows full attempt history
- [ ] Attempt timeline visually shows all attempts
- [ ] New plan form validates required fields
- [ ] Status transitions are valid (draft → in_progress, not draft → completed)
- [ ] Actual hours calculated from attempt durations
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E test: Create plan → Start attempt → Get sidetracked → Resume → Complete

Testing Requirements:
Backend:
- Test plan CRUD operations
- Test attempt lifecycle
- Test status transitions
- Test parent-child plan relationships
- Test filtering by status, priority

Frontend:
- Test Kanban drag-and-drop
- Test plan card rendering
- Test detail modal interactions
- Test form validation

E2E:
- Full plan lifecycle with multiple attempts
- Test blocked → unblocked transition
- Test attempt abandonment and resume

Dependencies:
- Work Log System (Issue 1.2) - for session tracking

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] This is a large feature - expect longer execution time
- [ ] Watch for drag-and-drop library installation
- [ ] Monitor migration and test execution

**2. Review PR:**
- [ ] Verify complex SQL schema (CHECK constraints, foreign keys)
- [ ] Check drag-and-drop implementation
- [ ] Verify attempt timeline rendering
- [ ] Check status transition logic

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Run migration
cd app/server
uv run python -c "from database.connection import get_connection; get_connection()"

# Check schema
sqlite3 tac-webbuilder.db ".schema plans"
sqlite3 tac-webbuilder.db ".schema plan_attempts"

# Run tests
uv run pytest tests/repositories/test_plans_repository.py -v
uv run pytest tests/routes/test_plans_routes.py -v
uv run pytest tests/e2e/test_plans_lifecycle.py -v

# Start servers
cd app/server && uv run python server.py &
cd app/client && bun run dev

# Manual test:
# 1. Go to "Plans" tab
# 2. Create new plan (title, description, type=feature, priority=high)
# 3. Verify plan appears in "Draft" column
# 4. Drag plan to "In Progress" column
# 5. Open plan detail modal
# 6. Click "Start New Attempt"
# 7. Verify attempt appears in timeline
# 8. End attempt with outcome="success"
# 9. Drag plan to "Completed" column
# 10. Verify completed_at is set
```

**4. Integration Test with Work Log:**
```bash
# Test Work Log → Plans integration
# 1. Go to Work Log tab
# 2. Create entry mentioning "working on Plans Panel"
# 3. Go to Plans tab
# 4. Verify session_id linkage (if implemented)
```

**5. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**6. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **Drag-and-drop not working:** Check library installation, permissions
- **Foreign key constraint fails:** Check work_log table exists
- **Status transition invalid:** Verify CHECK constraints
- **Attempt timeline not rendering:** Check data format (JSON arrays)

**Unblocking Steps:**
1. Check both migrations ran: `sqlite3 tac-webbuilder.db ".tables"`
2. Test API manually: Create plan → Start attempt → End attempt
3. Check drag-and-drop library: `cd app/client && bun list | grep dnd`
4. If stuck: Create refinement issue with specific component

**Do NOT proceed to Issue 2.2 until this is ✅ Complete**

---

### **Checkpoint 2.1 - Before Issue 2.2**

**Verification:**
- [ ] Issue 2.1 merged to main
- [ ] Plans Panel tab visible
- [ ] Can create and drag plans between columns
- [ ] Attempt timeline works
- [ ] No console errors

---

### **Issue 2.2: Template System Enhancement**

**⏱️ Estimated:** 5-7 days | **💰 Estimated Cost:** $3-$8 | **Priority:** MEDIUM

**Dependencies:** None (parallel to 2.1, but submit sequentially)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Enhanced Input Template System with Validation

Description:
Enhance the existing workflow templating system with structured input validation, auto-completion, and template selection UI. Define required/optional fields per workflow type, validate before workflow execution, and suggest missing fields based on context.

Context:
- Current state: Workflow templates exist (adw_*), user input parsed to structured inputs
- Problem: Some required inputs missing → unpredictable workflow results
- Goal: Template-based input with validation to ensure all required fields present
- Integration: Extends existing template_router.py, adds frontend template selector

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_input_templates.sql
```sql
CREATE TABLE input_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  template_schema TEXT NOT NULL,
  example_inputs TEXT,
  workflow_type TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE template_validations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  field_type TEXT NOT NULL CHECK(field_type IN ('string', 'number', 'boolean', 'array', 'object')),
  required BOOLEAN DEFAULT FALSE,
  validation_rule TEXT,
  default_value TEXT,
  help_text TEXT,
  FOREIGN KEY (template_id) REFERENCES input_templates(id)
);

CREATE INDEX idx_input_templates_name ON input_templates(name);
CREATE INDEX idx_template_validations_template ON template_validations(template_id);
```

TEMPLATE SCHEMA FORMAT (JSON):
```json
{
  "name": "feature-request",
  "description": "Template for new feature requests",
  "fields": [
    {
      "name": "feature_description",
      "type": "string",
      "required": true,
      "minLength": 20,
      "helpText": "Describe the feature in detail"
    },
    {
      "name": "acceptance_criteria",
      "type": "array",
      "required": true,
      "minItems": 1,
      "helpText": "List conditions for feature completion"
    },
    {
      "name": "project_path",
      "type": "string",
      "required": false,
      "pattern": "^/.*",
      "default": "/Users/Warmonger0/tac/tac-webbuilder",
      "helpText": "Absolute path to project"
    }
  ]
}
```

PRE-POPULATED TEMPLATES:
Create seed file: app/server/migration/seed_templates.sql
1. feature-request (maps to adw_sdlc_standard)
2. bug-fix (maps to adw_sdlc_lightweight)
3. refactor (maps to adw_sdlc_standard)
4. freeform (no validation, current behavior)

BACKEND API ROUTES (app/server/routes/template_routes.py):
- GET /api/v1/templates - List all templates
- GET /api/v1/templates/{name} - Get template schema
- POST /api/v1/templates/{name}/validate - Validate user input against template
- POST /api/v1/templates/{name}/autocomplete - Suggest missing fields

BACKEND VALIDATOR (app/server/core/template_validator.py):
```python
class TemplateValidator:
    def validate_input(self, template: InputTemplate, user_input: dict) -> ValidationResult:
        """Validate user input against template schema"""
        # Returns: {valid: bool, errors: List[Error], missing_fields: List[str]}

    def suggest_fields(self, template: InputTemplate, partial_input: dict) -> List[Suggestion]:
        """Suggest missing required fields with defaults"""

    def apply_defaults(self, template: InputTemplate, user_input: dict) -> dict:
        """Apply default values for missing optional fields"""
```

BACKEND REPOSITORY (app/server/repositories/template_repository.py):
- get_all_templates() -> List[InputTemplate]
- get_template(name: str) -> Optional[InputTemplate]
- get_validations(template_id: int) -> List[TemplateValidation]

FRONTEND COMPONENTS:
1. TemplateSelector.tsx - Dropdown in RequestFormCore
   - Dropdown with template options
   - Shows template description on hover
   - "Freeform (no template)" option
   - OnChange: Load template and show TemplateForm

2. TemplateForm.tsx - Dynamic form based on template
   - Renders form fields based on schema
   - Field types: text, textarea, number, checkbox, array (tags)
   - Shows help text on hover/below field
   - Real-time validation with inline errors
   - Required fields marked with *
   - Character/length counters where applicable

3. TemplateValidationPanel.tsx - Validation status display
   - Shows overall status: ✅ All required fields present / ⚠️ Missing fields
   - Lists missing required fields with help text
   - Shows field-level validation errors
   - "Fix Issues" suggestions

4. TemplateFieldInput.tsx - Reusable field component
   - Handles different field types (string, number, array, etc.)
   - Validation state display (valid/invalid)
   - Help text tooltip
   - Error message display

FRONTEND API CLIENT (app/client/src/api/template-client.ts):
- getTemplates(): Promise<InputTemplate[]>
- getTemplate(name: string): Promise<InputTemplate>
- validateInput(name: string, input: any): Promise<ValidationResult>
- autocompleteFields(name: string, partialInput: any): Promise<Suggestion[]>

INTEGRATION WITH RequestFormCore:
- Add template selector above current nl-input textarea
- When template selected: Show TemplateForm below selector
- When "freeform" selected: Show current textarea (no validation)
- Validation happens on form change and before submission
- Block submission if validation fails (show errors)

Files to Create:
Backend:
- app/server/migration/add_input_templates.sql
- app/server/migration/seed_templates.sql (seed with 3 templates)
- app/server/routes/template_routes.py
- app/server/core/template_validator.py
- app/server/repositories/template_repository.py
- app/server/models/template.py

Frontend:
- app/client/src/components/TemplateSelector.tsx
- app/client/src/components/TemplateForm.tsx
- app/client/src/components/TemplateValidationPanel.tsx
- app/client/src/components/TemplateFieldInput.tsx
- app/client/src/api/template-client.ts

Tests:
- app/server/tests/core/test_template_validator.py
- app/server/tests/repositories/test_template_repository.py
- app/server/tests/routes/test_template_routes.py
- app/client/src/components/__tests__/TemplateForm.test.tsx
- app/server/tests/e2e/test_template_validation.py

Files to Modify:
- app/server/server.py (register template_routes)
- app/client/src/components/RequestFormCore.tsx (add TemplateSelector above nl-input)
- app/server/core/template_router.py (integrate with new validation)

Acceptance Criteria:
- [ ] Database schema created with templates and validations tables
- [ ] Three templates pre-populated: feature-request, bug-fix, refactor
- [ ] Template validator correctly validates required fields
- [ ] Template validator correctly checks field types (string, number, array)
- [ ] Template validator applies default values
- [ ] Frontend selector displays all templates
- [ ] Frontend form dynamically renders based on template schema
- [ ] Real-time validation with inline error messages
- [ ] Required fields marked with asterisk (*)
- [ ] Help text displayed on hover or below field
- [ ] Submission blocked if validation fails
- [ ] "Freeform" option allows bypassing template validation
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E test: Select template → Fill form → Validation pass → Submit

Testing Requirements:
Backend:
- Test validator with valid inputs
- Test validator with missing required fields (should fail)
- Test validator with wrong field types (should fail)
- Test validator with minLength, maxLength, pattern constraints
- Test default value application
- Test autocomplete suggestions

Frontend:
- Test template selector renders all options
- Test form renders correctly for each field type
- Test validation error display
- Test required field indicators
- Test help text display

E2E:
- Full flow: Select template → Fill invalid data → See errors → Fix → Submit
- Test each template type (feature-request, bug-fix, refactor)
- Test freeform submission (no validation)

Dependencies: None

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Watch for migration + seed file execution
- [ ] Monitor validator implementation
- [ ] Check dynamic form rendering

**2. Review PR:**
- [ ] Verify seed data is correct (3 templates)
- [ ] Check validator logic (minLength, pattern matching)
- [ ] Review dynamic form rendering based on schema
- [ ] Verify validation blocks submission

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Run migrations + seed
cd app/server
uv run python -c "from database.connection import get_connection; get_connection()"

# Verify templates seeded
sqlite3 tac-webbuilder.db "SELECT name FROM input_templates;"
# Should show: feature-request, bug-fix, refactor, freeform

# Run tests
uv run pytest tests/core/test_template_validator.py -v
uv run pytest tests/routes/test_template_routes.py -v
uv run pytest tests/e2e/test_template_validation.py -v

# Start servers
cd app/server && uv run python server.py &
cd app/client && bun run dev

# Manual test:
# 1. Go to "New Request" tab
# 2. Above textarea, should see template selector dropdown
# 3. Select "feature-request" template
# 4. Form should dynamically render with fields:
#    - feature_description (required, minLength 20)
#    - acceptance_criteria (required, array)
#    - project_path (optional, has default)
# 5. Try submitting with empty fields - should block
# 6. Fill required fields - should allow submission
# 7. Select "Freeform" - should show regular textarea
```

**4. Integration Test:**
```bash
# Test template validation → GitHub issue creation
# 1. Select "bug-fix" template
# 2. Fill all required fields
# 3. Submit
# 4. Verify issue created with structured format
```

**5. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**6. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **Templates not showing:** Check seed file ran, query database
- **Validation not working:** Check validator logic, field types
- **Dynamic form not rendering:** Check schema parsing, React rendering
- **Default values not applied:** Check validator apply_defaults logic

**Unblocking Steps:**
1. Check migrations: `sqlite3 tac-webbuilder.db ".tables"`
2. Check seed data: `sqlite3 tac-webbuilder.db "SELECT * FROM input_templates;"`
3. Test validator manually: Write Python test script
4. Check browser console for React errors
5. If stuck: Create refinement issue

**Do NOT proceed to Phase 3 until this is ✅ Complete**

---

### **Checkpoint 2.2 - End of Phase 2**

**Phase 2 Complete Checklist:**
- [ ] Issues 2.1 and 2.2 are ✅ Complete
- [ ] Plans Panel working (Kanban board functional)
- [ ] Template selector working (shows templates)
- [ ] Template validation working (blocks invalid submissions)
- [ ] Integration between Work Log and Plans tested
- [ ] All Phase 2 tests passing

**Manual Integration Test:**
1. Go to Plans Panel → Create plan for "Implement Phase 3"
2. Go to Work Log → Create entry "Completed Phase 2"
3. Go to New Request → Select "feature-request" template
4. Fill form and submit (should validate)

---

## 🔍 Phase 3: Quality & Review (Week 4-6)

### **Checkpoint 3.0 - Before Starting**

**Prerequisites:**
- [ ] Phase 2 is ✅ Complete
- [ ] Plans Panel is functional
- [ ] Template system is validated
- [ ] No blocking bugs

**Note:** Phase 3 has larger features. Issue 3.2 (Quality Panel) will be split into 2 parts.

---

### **Issue 3.1: Review Panel**

**⏱️ Estimated:** 7-10 days | **💰 Estimated Cost:** $5-$12 | **Priority:** MEDIUM

**Dependencies:** None

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Implement Issue Review Panel with Structured Checklists

Description:
Create a Review Panel for structured review of GitHub issues before ADW execution. Includes triage workflow, readiness checklists, clarity/completeness scoring, and review history tracking. Blocks ADW workflow execution if issue not marked "ADW Ready".

Context:
- Current state: Issues submitted → ADW starts immediately
- Problem: Some issues lack clarity or required details, leading to workflow failures
- Goal: Quality gate before ADW execution with structured review process
- Integration: Checks before ADW workflow starts, history tracked in database

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_issue_reviews.sql
```sql
CREATE TABLE issue_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_number INTEGER NOT NULL,
  reviewer TEXT NOT NULL,
  review_type TEXT NOT NULL CHECK(review_type IN ('triage', 'readiness', 'quality')),
  status TEXT NOT NULL CHECK(status IN ('approved', 'needs-work', 'rejected')),
  clarity_score INTEGER CHECK(clarity_score BETWEEN 1 AND 10),
  completeness_score INTEGER CHECK(completeness_score BETWEEN 1 AND 10),
  adw_ready BOOLEAN DEFAULT FALSE,
  notes TEXT,
  checklist TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_checklists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_type TEXT NOT NULL,
  item_text TEXT NOT NULL,
  item_order INTEGER NOT NULL,
  required BOOLEAN DEFAULT TRUE,
  help_text TEXT
);

CREATE INDEX idx_issue_reviews_issue ON issue_reviews(issue_number);
CREATE INDEX idx_issue_reviews_status ON issue_reviews(status);
CREATE INDEX idx_issue_reviews_adw_ready ON issue_reviews(adw_ready);
```

PRE-POPULATED CHECKLISTS:
Create seed file: app/server/migration/seed_review_checklists.sql

Triage Checklist:
1. Issue title is descriptive and clear (required)
2. Issue type identified (bug/feature/refactor) (required)
3. Priority level assigned (required)
4. Affected components identified (optional)

ADW Readiness Checklist:
1. Acceptance criteria clearly defined (required)
2. No dependencies on external approvals (required)
3. Project path specified (required)
4. Test strategy defined (optional)
5. Estimated complexity is reasonable (required)

BACKEND API ROUTES (app/server/routes/review_routes.py):
- POST /api/v1/reviews/issues/{issue_number} - Create review
- GET /api/v1/reviews/issues/{issue_number} - Get all reviews for issue
- GET /api/v1/reviews/checklists/{review_type} - Get checklist template
- GET /api/v1/reviews/pending - Get issues awaiting review
- GET /api/v1/reviews/adw-ready - Get ADW-ready issues
- PUT /api/v1/reviews/{review_id} - Update review

BACKEND MODELS (app/server/models/review.py):
```python
@dataclass
class IssueReview:
    id: Optional[int]
    issue_number: int
    reviewer: str
    review_type: str  # 'triage', 'readiness', 'quality'
    status: str  # 'approved', 'needs-work', 'rejected'
    clarity_score: Optional[int]  # 1-10
    completeness_score: Optional[int]  # 1-10
    adw_ready: bool
    notes: Optional[str]
    checklist: List[ChecklistItem]  # JSON array
    created_at: datetime

@dataclass
class ChecklistItem:
    item_text: str
    checked: bool
    required: bool
    help_text: Optional[str]
```

BACKEND REPOSITORY (app/server/repositories/review_repository.py):
- create_review(review: IssueReview) -> int
- get_reviews_for_issue(issue_number: int) -> List[IssueReview]
- get_review(review_id: int) -> Optional[IssueReview]
- update_review(review_id: int, updates: dict) -> bool
- get_checklist_template(review_type: str) -> List[ChecklistItem]
- get_pending_reviews() -> List[int]  # Issue numbers
- is_adw_ready(issue_number: int) -> bool
- get_latest_review(issue_number: int) -> Optional[IssueReview]

FRONTEND COMPONENTS:
1. ReviewPanel.tsx - Main review interface
   - List of issues pending review (tabs: All | Needs Triage | Needs Readiness)
   - Issue cards with status indicators
   - Filter by status, reviewer
   - Click issue to open review modal
   - "Review Issue" button for each issue

2. IssueReviewModal.tsx - Review modal
   - Shows issue details (title, description, labels)
   - Review type selector (Triage | Readiness | Quality)
   - Dynamic checklist based on review type
   - Clarity score slider (1-10) with labels
   - Completeness score slider (1-10) with labels
   - Notes textarea
   - "ADW Ready" checkbox (only for readiness review)
   - Actions: Approve | Request Changes | Reject

3. ReviewChecklist.tsx - Checklist component
   - List of checklist items with checkboxes
   - Required items marked with (required)
   - Help text on hover
   - Visual indicator: All required checked = ✅

4. ReviewHistory.tsx - Review timeline for issue
   - Vertical timeline of all reviews
   - Shows: reviewer, type, status, timestamp
   - Click to expand: full checklist, scores, notes
   - Color-coded: approved=green, needs-work=yellow, rejected=red

5. ReviewStatusBadge.tsx - Status indicator
   - Visual badge showing review status
   - Icons: ✅ Approved | ⚠️ Needs Work | ❌ Rejected | ⏳ Pending
   - Tooltip with latest review details

FRONTEND API CLIENT (app/client/src/api/review-client.ts):
- createReview(issueNumber: number, review: ReviewCreate): Promise<IssueReview>
- getReviews(issueNumber: number): Promise<IssueReview[]>
- getChecklistTemplate(reviewType: string): Promise<ChecklistItem[]>
- getPendingReviews(): Promise<number[]>
- getAdwReadyIssues(): Promise<number[]>
- updateReview(reviewId: number, updates: Partial<IssueReview>): Promise<IssueReview>

INTEGRATION WITH ADW WORKFLOWS:
- Add pre-flight check in workflow_service.py:
  ```python
  def can_start_workflow(issue_number: int) -> tuple[bool, str]:
      if not review_repository.is_adw_ready(issue_number):
          latest_review = review_repository.get_latest_review(issue_number)
          return False, f"Issue not ADW ready. Latest review: {latest_review.status}"
      return True, ""
  ```
- Show review status in Workflow History
- Auto-create "pending triage" review when issue created via UI

INTEGRATION WITH UI:
- Add "Review" tab to App.tsx
- Show review status badge in Workflow History View
- Optional: Add review status in ZteHopperQueueCard

Files to Create:
Backend:
- app/server/migration/add_issue_reviews.sql
- app/server/migration/seed_review_checklists.sql
- app/server/routes/review_routes.py
- app/server/repositories/review_repository.py
- app/server/models/review.py

Frontend:
- app/client/src/components/ReviewPanel.tsx
- app/client/src/components/IssueReviewModal.tsx
- app/client/src/components/ReviewChecklist.tsx
- app/client/src/components/ReviewHistory.tsx
- app/client/src/components/ReviewStatusBadge.tsx
- app/client/src/api/review-client.ts

Tests:
- app/server/tests/repositories/test_review_repository.py
- app/server/tests/routes/test_review_routes.py
- app/client/src/components/__tests__/ReviewChecklist.test.tsx
- app/server/tests/e2e/test_review_workflow.py

Files to Modify:
- app/server/server.py (register review_routes)
- app/client/src/App.tsx (add 'review' tab)
- app/server/services/workflow_service.py (add can_start_workflow check)
- app/client/src/components/WorkflowHistoryView.tsx (show review status)

Acceptance Criteria:
- [ ] Database schema created with reviews and checklists
- [ ] Checklists pre-populated for triage and readiness review types
- [ ] Backend CRUD operations for reviews working
- [ ] Checklist templates retrievable by review type
- [ ] Frontend review modal renders with dynamic checklist
- [ ] Clarity and completeness score sliders working (1-10 range)
- [ ] ADW ready checkbox only appears for readiness reviews
- [ ] Review status badge shows correct status and color
- [ ] Review history displays all reviews in timeline format
- [ ] ADW workflow blocked if issue not ADW ready
- [ ] Error message shown explaining why workflow blocked
- [ ] Auto-create pending triage review when issue created
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E test: Create issue → Review (needs work) → Fix → Review (approve) → ADW starts

Testing Requirements:
Backend:
- Test review CRUD operations
- Test checklist template retrieval
- Test is_adw_ready check (true/false scenarios)
- Test can_start_workflow blocking logic
- Test review history retrieval

Frontend:
- Test modal renders with checklist
- Test score sliders (min 1, max 10)
- Test checklist item checking
- Test required items validation
- Test status badge rendering

E2E:
- Full review flow: Issue → Triage → Readiness → ADW blocked → Approve → ADW starts
- Test review history display
- Test review status in workflow history

Dependencies: None

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Large feature - expect 6-8 hour execution
- [ ] Watch for workflow_service.py modification
- [ ] Monitor ADW blocking logic implementation

**2. Review PR:**
- [ ] Verify pre-flight check in workflow_service.py
- [ ] Check is_adw_ready logic
- [ ] Review checklist rendering
- [ ] Verify score sliders (1-10 range)

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Run migrations + seed
cd app/server
uv run python -c "from database.connection import get_connection; get_connection()"

# Verify checklists seeded
sqlite3 tac-webbuilder.db "SELECT * FROM review_checklists ORDER BY review_type, item_order;"

# Run tests
uv run pytest tests/repositories/test_review_repository.py -v
uv run pytest tests/routes/test_review_routes.py -v
uv run pytest tests/e2e/test_review_workflow.py -v

# Start servers
cd app/server && uv run python server.py &
cd app/client && bun run dev

# Manual test - Blocking Logic:
# 1. Create a test issue via GitHub or UI
# 2. DO NOT review it (should be in pending state)
# 3. Try to start ADW workflow on that issue
# 4. EXPECT: Workflow should be BLOCKED
# 5. Error should say "Issue not ADW ready"

# Manual test - Review Flow:
# 1. Go to "Review" tab
# 2. Should see pending issue
# 3. Click "Review Issue"
# 4. Select review type: "Triage"
# 5. Check all required items
# 6. Set clarity score = 8
# 7. Set completeness score = 7
# 8. Click "Approve"
# 9. Review should save

# Manual test - Readiness:
# 1. Same issue, review type: "Readiness"
# 2. Check all required items
# 3. Check "ADW Ready" checkbox
# 4. Click "Approve"
# 5. Now try starting ADW workflow
# 6. EXPECT: Workflow should START (not blocked)
```

**4. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**5. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **ADW not blocked:** Check workflow_service.py integration, is_adw_ready logic
- **Checklist not loading:** Check seed file, check API response
- **Score sliders not working:** Check range validation (1-10)
- **Reviews not saving:** Check JSON checklist serialization

**Unblocking Steps:**
1. Test is_adw_ready manually: `curl http://localhost:8000/api/v1/reviews/adw-ready`
2. Test workflow blocking: Try starting workflow on unreviewed issue
3. Check review creation: `sqlite3 tac-webbuilder.db "SELECT * FROM issue_reviews;"`
4. If stuck: Create refinement issue

**Do NOT proceed to Issue 3.2 until this is ✅ Complete**

---

### **Checkpoint 3.1 - Before Quality Panel**

**Verification:**
- [ ] Issue 3.1 merged to main
- [ ] Review Panel tab visible
- [ ] Can review issues with checklist
- [ ] ADW workflow blocks unreviewed issues
- [ ] Review history displays correctly

**Important:** Quality Panel (Issue 3.2) is LARGE. It will be split into 2 parts:
- Part 1: Database, analyzer, backend API
- Part 2: Frontend components

---

### **Issue 3.2: Quality Panel - Part 1 (Backend)**

**⏱️ Estimated:** 5-7 days | **💰 Estimated Cost:** $5-$10 | **Priority:** HIGH

**Dependencies:** None

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Quality Panel Part 1 - Backend Infrastructure

Description:
Create backend infrastructure for code quality tracking: database schema, quality analyzer service, and API routes. Tracks file metrics (line counts, complexity), test coverage, quality thresholds, and compliance violations. Frontend components will be added in Part 2.

Context:
- Current state: No code quality tracking
- Problem: Can't monitor codebase health, compliance, or test coverage
- Goal: Automated quality scanning and metrics storage
- Integration: Part 1 = Backend only, Part 2 = Frontend

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_quality_metrics.sql
```sql
CREATE TABLE quality_scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  project_path TEXT NOT NULL,
  scan_type TEXT NOT NULL CHECK(scan_type IN ('full', 'incremental', 'targeted')),
  total_files INTEGER,
  total_lines INTEGER,
  scan_duration_seconds REAL
);

CREATE TABLE file_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT,
  line_count INTEGER,
  function_count INTEGER,
  class_count INTEGER,
  complexity_score INTEGER,
  compliant BOOLEAN DEFAULT TRUE,
  violations TEXT,
  FOREIGN KEY (scan_id) REFERENCES quality_scans(id)
);

CREATE TABLE quality_thresholds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  metric_name TEXT NOT NULL UNIQUE,
  threshold_value INTEGER NOT NULL,
  threshold_type TEXT NOT NULL CHECK(threshold_type IN ('max', 'min', 'exact')),
  severity TEXT DEFAULT 'warning' CHECK(severity IN ('info', 'warning', 'error')),
  description TEXT
);

CREATE TABLE test_coverage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  coverage_type TEXT NOT NULL CHECK(coverage_type IN ('unit', 'integration', 'e2e')),
  lines_covered INTEGER,
  lines_total INTEGER,
  coverage_percent REAL,
  missing_lines TEXT,
  FOREIGN KEY (scan_id) REFERENCES quality_scans(id)
);

CREATE INDEX idx_file_metrics_scan ON file_metrics(scan_id);
CREATE INDEX idx_file_metrics_compliant ON file_metrics(compliant);
CREATE INDEX idx_test_coverage_scan ON test_coverage(scan_id);
```

QUALITY THRESHOLDS (Pre-populate):
Create seed file: app/server/migration/seed_quality_thresholds.sql
```sql
INSERT INTO quality_thresholds (metric_name, threshold_value, threshold_type, severity, description) VALUES
  ('file_line_limit', 500, 'max', 'warning', 'Maximum lines per file'),
  ('function_line_limit', 50, 'max', 'warning', 'Maximum lines per function'),
  ('cyclomatic_complexity', 10, 'max', 'error', 'Maximum complexity score per function'),
  ('test_coverage_min', 80, 'min', 'warning', 'Minimum test coverage percentage'),
  ('documentation_coverage_min', 70, 'min', 'info', 'Minimum files with documentation');
```

BACKEND QUALITY ANALYZER:
Create file: app/server/core/quality_analyzer.py
```python
import ast
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class FileMetrics:
    file_path: str
    file_type: str
    line_count: int
    function_count: int
    class_count: int
    complexity_score: int
    compliant: bool
    violations: List[str]

class QualityAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> Dict[str, int]:
        # Load from quality_thresholds table
        pass

    def scan_codebase(self, scan_type: str = 'full') -> int:
        """
        Perform quality scan of codebase.
        Returns scan_id.

        Steps:
        1. Create quality_scans record
        2. Walk through project directory
        3. For each file: analyze_file()
        4. Store metrics in file_metrics table
        5. Return scan_id
        """
        pass

    def analyze_file(self, file_path: Path) -> FileMetrics:
        """
        Analyze single file and return metrics.

        For Python files:
        - Use ast module to parse
        - Count lines, functions, classes
        - Calculate cyclomatic complexity
        - Check against thresholds

        For TypeScript files:
        - Count lines (simple line count)
        - Pattern match for functions/classes
        - Basic complexity (future: use ts-morph)

        Returns FileMetrics with violations list
        """
        pass

    def check_compliance(self, metrics: FileMetrics) -> List[str]:
        """
        Check file metrics against thresholds.
        Returns list of violations.

        Checks:
        - Line count > file_line_limit?
        - Complexity > cyclomatic_complexity?
        - etc.
        """
        pass

    def calculate_complexity(self, tree: ast.AST) -> int:
        """
        Calculate cyclomatic complexity for Python code.

        Counts:
        - if statements
        - for/while loops
        - try/except blocks
        - and/or operators
        - Nested depth

        Returns complexity score (1-100)
        """
        pass
```

BACKEND API ROUTES (app/server/routes/quality_routes.py):
- POST /api/v1/quality/scan - Start quality scan (async job)
  - Body: { "project_path": str, "scan_type": "full" }
  - Returns: { "scan_id": int, "status": "running" }
- GET /api/v1/quality/scans/{scan_id} - Get scan results
  - Returns: { "scan": QualityScan, "metrics": List[FileMetrics] }
- GET /api/v1/quality/metrics/summary - Get latest metrics summary
  - Returns: { "total_files": int, "compliant_files": int, "violation_count": int }
- GET /api/v1/quality/violations - Get list of violations
  - Query params: severity (optional)
  - Returns: List[Violation]
- GET /api/v1/quality/thresholds - Get all thresholds
  - Returns: List[QualityThreshold]

BACKEND REPOSITORY (app/server/repositories/quality_repository.py):
- create_scan(scan: QualityScan) -> int
- get_scan(scan_id: int) -> Optional[QualityScan]
- create_file_metric(metric: FileMetrics) -> int
- get_scan_metrics(scan_id: int) -> List[FileMetrics]
- get_violations(severity: Optional[str] = None) -> List[FileMetrics]
- get_thresholds() -> Dict[str, int]
- get_latest_scan() -> Optional[QualityScan]

BACKEND MODELS (app/server/models/quality.py):
```python
@dataclass
class QualityScan:
    id: Optional[int]
    scan_timestamp: datetime
    project_path: str
    scan_type: str
    total_files: int
    total_lines: int
    scan_duration_seconds: float

@dataclass
class Violation:
    file_path: str
    violation_type: str
    severity: str
    message: str
```

Files to Create:
Backend:
- app/server/migration/add_quality_metrics.sql
- app/server/migration/seed_quality_thresholds.sql
- app/server/core/quality_analyzer.py
- app/server/routes/quality_routes.py
- app/server/repositories/quality_repository.py
- app/server/models/quality.py

Tests:
- app/server/tests/core/test_quality_analyzer.py
- app/server/tests/repositories/test_quality_repository.py
- app/server/tests/routes/test_quality_routes.py

Files to Modify:
- app/server/server.py (register quality_routes)

Acceptance Criteria:
- [ ] Database schema created with all 4 tables
- [ ] Quality thresholds seeded with 5 default values
- [ ] QualityAnalyzer can scan Python files (line count, function count, complexity)
- [ ] QualityAnalyzer can scan TypeScript files (line count, basic metrics)
- [ ] Violations detected and stored correctly
- [ ] API route: POST /scan creates scan and returns scan_id
- [ ] API route: GET /scans/{id} returns scan results
- [ ] API route: GET /violations returns list of violations
- [ ] Repository methods working with proper error handling
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Can run scan on /Users/Warmonger0/tac/tac-webbuilder and get results

Testing Requirements:
Backend:
- Test quality_analyzer on sample Python file
- Test quality_analyzer on sample TypeScript file
- Test threshold violation detection
- Test complexity calculation
- Test scan creation and retrieval
- Test violation filtering by severity

Integration:
- Test full scan workflow: POST /scan → GET /scans/{id} → verify metrics
- Test scan on actual tac-webbuilder codebase
- Verify violations detected for files >500 lines

Dependencies: None

Project Path: /Users/Warmonger0/tac/tac-webbuilder

IMPORTANT: This is Part 1 (backend only). Part 2 will add frontend components.
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Watch for ast module usage (Python builtin)
- [ ] Monitor file walking logic
- [ ] Check complexity calculation implementation

**2. Review PR:**
- [ ] Verify QualityAnalyzer logic is sound
- [ ] Check threshold checking logic
- [ ] Review scan workflow (create scan → analyze files → store metrics)
- [ ] Verify API routes work correctly

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Run migrations + seed
cd app/server
uv run python -c "from database.connection import get_connection; get_connection()"

# Verify thresholds seeded
sqlite3 tac-webbuilder.db "SELECT * FROM quality_thresholds;"

# Run tests
uv run pytest tests/core/test_quality_analyzer.py -v
uv run pytest tests/repositories/test_quality_repository.py -v
uv run pytest tests/routes/test_quality_routes.py -v

# Test analyzer manually
uv run python -c "
from core.quality_analyzer import QualityAnalyzer
analyzer = QualityAnalyzer('/Users/Warmonger0/tac/tac-webbuilder')
scan_id = analyzer.scan_codebase('full')
print(f'Scan ID: {scan_id}')
"

# Check results
sqlite3 tac-webbuilder.db "SELECT COUNT(*) FROM file_metrics;"
sqlite3 tac-webbuilder.db "SELECT file_path, compliant FROM file_metrics WHERE compliant = 0 LIMIT 10;"

# Start server and test API
cd app/server && uv run python server.py &

# Test API
curl -X POST http://localhost:8000/api/v1/quality/scan \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/Users/Warmonger0/tac/tac-webbuilder", "scan_type": "full"}'

# Get scan results (replace {scan_id} with actual ID from above)
curl http://localhost:8000/api/v1/quality/scans/{scan_id}

# Get violations
curl http://localhost:8000/api/v1/quality/violations
```

**4. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**5. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **ast parsing fails:** Check Python syntax errors in target files
- **Scan takes too long:** Implement file filtering (skip node_modules, __pycache__)
- **Complexity calculation wrong:** Review algorithm, compare with known tools
- **Too many violations:** Adjust thresholds or implement severity levels

**Unblocking Steps:**
1. Test analyzer on single file first: `analyzer.analyze_file(Path('test.py'))`
2. Check scan progress: `sqlite3 tac-webbuilder.db "SELECT COUNT(*) FROM file_metrics;"`
3. If stuck on complexity: Simplify to basic metric (just count ifs/loops)
4. If stuck: Create refinement issue

**Do NOT proceed to Issue 3.3 until this is ✅ Complete**

---

### **Checkpoint 3.2 - Before Quality Panel Frontend**

**Verification:**
- [ ] Issue 3.2 merged to main
- [ ] Can run quality scan via API
- [ ] Scan results stored in database
- [ ] Violations detected correctly
- [ ] API routes working

**Next:** Add frontend components to visualize quality metrics

---

### **Issue 3.3: Quality Panel - Part 2 (Frontend)**

**⏱️ Estimated:** 3-5 days | **💰 Estimated Cost:** $3-$7 | **Priority:** HIGH

**Dependencies:** Quality Panel Part 1 (Issue 3.2)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Quality Panel Part 2 - Frontend Dashboard

Description:
Create frontend dashboard for visualizing code quality metrics. Displays overall health score, compliance rate, test coverage gauges, violations list, and file tree with compliance indicators. Uses backend API from Part 1.

Context:
- Current state: Backend quality scanner working (Part 1 complete)
- Problem: No UI to view quality metrics
- Goal: Interactive dashboard for quality monitoring
- Integration: Consumes API from Part 1, adds "Quality" tab to App

Technical Specifications:

FRONTEND COMPONENTS:

1. QualityPanel.tsx - Main dashboard
   - Header with "Run Scan" button
   - Overall health score gauge (0-100)
   - Compliance rate gauge (% files passing)
   - Test coverage gauge (placeholder - from backend when available)
   - Recent violations list (top 10)
   - Tabs: Overview | Violations | File Tree
   - Loading state while scan running
   - Error handling

2. QualityMetricsCard.tsx - Individual metric card
   - Metric name and current value
   - Visual indicator: gauge or progress bar
   - Threshold line
   - Trend arrow (up/down from last scan)
   - Color-coded: green (good), yellow (warning), red (error)
   - Click to see details

3. ViolationsList.tsx - Filterable violations list
   - Table view: File | Violation | Severity | Line Count
   - Filter dropdown: All | Errors | Warnings | Info
   - Sort by: Severity | File | Line Count
   - Click row to highlight in file tree
   - Pagination (20 per page)
   - Export violations as CSV (optional)

4. FileTreeView.tsx - Simplified file tree
   - Collapsible directory structure
   - File icons with compliance indicators:
     - ✅ Green: All checks pass
     - ⚠️ Yellow: Warnings
     - ❌ Red: Errors
   - Click file to see metrics in modal
   - Search/filter files
   - Show only non-compliant files (toggle)

5. FileMetricsModal.tsx - Detailed file metrics
   - File path and type
   - Line count, function count, class count
   - Complexity score with gauge
   - Violations list for this file
   - Comparison with thresholds
   - "View File" button (opens in editor if possible)

6. ScanProgressIndicator.tsx - Scan progress display
   - Progress bar
   - Current status: "Scanning... 45/120 files"
   - Estimated time remaining
   - Cancel button (optional)

FRONTEND API CLIENT:
Enhance app/client/src/api/quality-client.ts:
- startQualityScan(projectPath: string): Promise<{ scan_id: number }>
- getScanResults(scanId: number): Promise<QualityScanResult>
- getMetricsSummary(): Promise<MetricsSummary>
- getViolations(severity?: string): Promise<Violation[]>
- getThresholds(): Promise<QualityThreshold[]>
- pollScanStatus(scanId: number): Promise<ScanStatus> (poll until complete)

FRONTEND TYPES (app/client/src/types/quality.ts):
```typescript
export interface QualityScanResult {
  scan: QualityScan;
  metrics: FileMetrics[];
  summary: {
    total_files: number;
    compliant_files: number;
    violation_count: number;
    health_score: number; // 0-100
  };
}

export interface FileMetrics {
  file_path: string;
  file_type: string;
  line_count: number;
  function_count: number;
  class_count: number;
  complexity_score: number;
  compliant: boolean;
  violations: string[];
}

export interface Violation {
  file_path: string;
  violation_type: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
}
```

INTEGRATION:
- Add "Quality" tab to App.tsx
- "Run Scan" button triggers POST /api/v1/quality/scan
- Poll scan status every 2 seconds while running
- When complete, fetch and display results
- Auto-refresh on tab switch (load latest scan)

VISUAL DESIGN:
- Use same dark theme as other panels (slate-900 background)
- Health score gauge: circular gauge with gradient (red → yellow → green)
- Compliance rate: horizontal progress bar
- File tree: Similar to VSCode file explorer
- Violations table: Striped rows, sortable headers

Files to Create:
Frontend:
- app/client/src/components/QualityPanel.tsx
- app/client/src/components/QualityMetricsCard.tsx
- app/client/src/components/ViolationsList.tsx
- app/client/src/components/FileTreeView.tsx
- app/client/src/components/FileMetricsModal.tsx
- app/client/src/components/ScanProgressIndicator.tsx
- app/client/src/api/quality-client.ts
- app/client/src/types/quality.ts

Tests:
- app/client/src/components/__tests__/QualityPanel.test.tsx
- app/client/src/components/__tests__/ViolationsList.test.tsx
- app/client/src/components/__tests__/FileTreeView.test.tsx

Files to Modify:
- app/client/src/App.tsx (add 'quality' tab)

Acceptance Criteria:
- [ ] Quality tab appears in App navigation
- [ ] "Run Scan" button triggers scan via API
- [ ] Scan progress indicator shows while scanning
- [ ] Dashboard displays after scan completes
- [ ] Health score gauge renders correctly (0-100)
- [ ] Compliance rate shows % of compliant files
- [ ] Violations list displays with filtering and sorting
- [ ] File tree shows directory structure with compliance icons
- [ ] Click file in tree opens metrics modal
- [ ] Metrics modal shows detailed file metrics
- [ ] Error handling for API failures
- [ ] Loading states implemented
- [ ] Frontend tests pass
- [ ] Can run scan and view results end-to-end

Testing Requirements:
Frontend:
- Test QualityPanel renders dashboard
- Test "Run Scan" button triggers API call
- Test violations list filtering (by severity)
- Test violations list sorting (by file, severity)
- Test file tree rendering from metrics data
- Test file metrics modal opens on file click
- Test error states (API failure, scan failure)

E2E:
- Full flow: Click "Quality" tab → Click "Run Scan" → Wait for completion → View results
- Test filter violations by severity
- Test click file in tree → Opens modal

Dependencies:
- Quality Panel Part 1 (Issue 3.2) - Backend must be complete

Project Path: /Users/Warmonger0/tac/tac-webbuilder

IMPORTANT: This is Part 2 (frontend). Backend from Part 1 must be working.
```

#### **After Submission:**

**1. Monitor Workflow:**
- [ ] Watch for React component creation
- [ ] Monitor gauge/chart library usage (recharts or similar)
- [ ] Check polling implementation

**2. Review PR:**
- [ ] Verify polling logic (2-second interval)
- [ ] Check gauge rendering
- [ ] Review file tree structure
- [ ] Verify filtering and sorting logic

**3. Test Locally:**
```bash
# Pull PR branch
git fetch origin
git checkout <branch-name>

# Ensure backend is running
cd app/server && uv run python server.py &

# Start frontend
cd app/client && bun run dev

# Manual test:
# 1. Go to http://localhost:5173
# 2. Click "Quality" tab (new tab)
# 3. Click "Run Scan" button
# 4. EXPECT: Progress indicator appears
# 5. Wait for scan to complete (30-60 seconds)
# 6. EXPECT: Dashboard appears with:
#    - Health score gauge
#    - Compliance rate
#    - Violations list
# 7. Test filtering violations (severity dropdown)
# 8. Test sorting violations (click column headers)
# 9. Click "File Tree" tab
# 10. Expand directories
# 11. Click file with violations (red icon)
# 12. EXPECT: Modal opens with file metrics
# 13. Verify metrics match backend data

# Test error handling:
# 1. Stop backend server
# 2. Click "Run Scan"
# 3. EXPECT: Error message displayed
```

**4. Merge:**
```bash
gh pr merge <PR-number> --squash
git checkout main
git pull
```

**5. Update Progress Tracker:**
- [ ] Update status to ✅ Complete
- [ ] Record metrics

#### **If Blocked:**

**Common Issues:**
- **Gauge not rendering:** Check recharts or gauge library installation
- **Polling stuck:** Check API response, scan_id validity
- **File tree not rendering:** Check data structure, recursive component
- **Violations not filtering:** Check severity values match ('info', 'warning', 'error')

**Unblocking Steps:**
1. Test API manually: `curl http://localhost:8000/api/v1/quality/violations`
2. Check React console for errors
3. Test polling manually: Call API every 2 seconds until status='complete'
4. If stuck: Create refinement issue

**Do NOT proceed to Phase 4 until this is ✅ Complete**

---

### **Checkpoint 3.3 - End of Phase 3**

**Phase 3 Complete Checklist:**
- [ ] All issues 3.1, 3.2, 3.3 are ✅ Complete
- [ ] Review Panel working (can review issues)
- [ ] Quality Panel backend working (can run scans)
- [ ] Quality Panel frontend working (can view results)
- [ ] ADW workflows blocked if issue not reviewed
- [ ] All Phase 3 tests passing

**Manual Integration Test:**
1. Create test issue via UI
2. Go to Review Panel → Review issue → Mark ADW Ready
3. Go to Quality Panel → Run scan
4. Review violations in dashboard
5. Go to Plans Panel → Create plan for "Fix Quality Violations"
6. Go to Work Log → Log session about Phase 3 completion

---

## ⚙️ Phase 4: Advanced Workflow (Week 7-10)

**Note:** Phase 4 features are VERY LARGE. Quality Gates will be split into 2 parts.

### **Checkpoint 4.0 - Before Starting**

**Prerequisites:**
- [ ] Phase 3 is ✅ Complete
- [ ] Review Panel working
- [ ] Quality Panel working
- [ ] No blocking bugs

---

### **Issue 4.1: Quality Gates - Part 1 (Backend)**

**⏱️ Estimated:** 7-10 days | **💰 Estimated Cost:** $8-$15 | **Priority:** HIGH

**Dependencies:** Quality Panel (Issues 3.2, 3.3)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Quality Gates Part 1 - Backend Infrastructure

Description:
Create backend infrastructure for quality gates: database schema, gate executor service, and API routes. Quality gates enforce structured handoffs between workflow stages (pre-plan, pre-build, pre-test, pre-ship, post-ship). Each gate checks conditions (artifacts, quality, reviews, tests) before allowing workflow to proceed.

Context:
- Current state: ADW workflows run without quality checks
- Problem: No enforcement of quality standards between workflow phases
- Goal: Automated quality gates with configurable conditions
- Integration: Part 1 = Backend, Part 2 = Frontend visualization

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_quality_gates.sql
```sql
CREATE TABLE quality_gates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gate_name TEXT NOT NULL UNIQUE,
  gate_type TEXT NOT NULL CHECK(gate_type IN ('pre-plan', 'pre-build', 'pre-test', 'pre-ship', 'post-ship')),
  description TEXT,
  enabled BOOLEAN DEFAULT TRUE,
  required BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gate_conditions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gate_id INTEGER NOT NULL,
  condition_type TEXT NOT NULL CHECK(condition_type IN ('artifact', 'quality', 'review', 'test', 'custom')),
  condition_name TEXT NOT NULL,
  condition_check TEXT NOT NULL,
  error_message TEXT,
  severity TEXT DEFAULT 'error' CHECK(severity IN ('info', 'warning', 'error')),
  order_num INTEGER,
  FOREIGN KEY (gate_id) REFERENCES quality_gates(id)
);

CREATE TABLE gate_executions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_id TEXT NOT NULL,
  gate_id INTEGER NOT NULL,
  execution_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL CHECK(status IN ('passed', 'failed', 'warning', 'skipped')),
  passed_conditions INTEGER,
  failed_conditions INTEGER,
  execution_log TEXT,
  override_reason TEXT,
  FOREIGN KEY (gate_id) REFERENCES quality_gates(id)
);

CREATE INDEX idx_gate_executions_workflow ON gate_executions(workflow_id);
CREATE INDEX idx_gate_executions_gate ON gate_executions(gate_id);
CREATE INDEX idx_gate_executions_status ON gate_executions(status);
```

PRE-POPULATED GATES:
Create seed file: app/server/migration/seed_quality_gates.sql

Example Pre-Ship Gate:
```sql
INSERT INTO quality_gates (gate_name, gate_type, description, enabled, required) VALUES
  ('pre-ship', 'pre-ship', 'Checks before creating PR', TRUE, TRUE);

INSERT INTO gate_conditions (gate_id, condition_type, condition_name, condition_check, error_message, severity, order_num) VALUES
  (1, 'test', 'all-tests-passing', '{"command": "pytest", "expected_exit": 0}', 'Tests must pass', 'error', 1),
  (1, 'quality', 'lint-clean', '{"command": "ruff check", "max_violations": 0}', 'No lint violations', 'error', 2),
  (1, 'artifact', 'changelog-updated', '{"file_modified": "CHANGELOG.md"}', 'CHANGELOG updated', 'warning', 3);
```

GATE EXECUTOR:
Create file: app/server/core/gate_executor.py
```python
import subprocess
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ConditionResult:
    condition_name: str
    passed: bool
    severity: str
    message: str
    details: Dict

@dataclass
class GateResult:
    gate_id: int
    status: str  # 'passed', 'failed', 'warning'
    passed_conditions: int
    failed_conditions: int
    condition_results: List[ConditionResult]

class GateExecutor:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

    def execute_gate(self, gate_id: int) -> GateResult:
        """
        Execute all conditions for a gate.

        Steps:
        1. Load gate and conditions from database
        2. For each condition: check_condition()
        3. Aggregate results
        4. Determine overall status (passed/failed/warning)
        5. Log execution to gate_executions table
        6. Return GateResult
        """
        pass

    def check_condition(self, condition: GateCondition) -> ConditionResult:
        """
        Check a single condition based on type.

        Condition types:
        - test: Run command, check exit code
        - quality: Run linter, check violation count
        - artifact: Check file exists/modified
        - review: Check review status in database
        - custom: Run custom Python code

        Returns ConditionResult
        """
        pass

    def check_test_condition(self, check: Dict) -> Tuple[bool, str]:
        """Run test command and check exit code"""
        try:
            result = subprocess.run(
                check['command'],
                shell=True,
                capture_output=True,
                timeout=300
            )
            passed = result.returncode == check['expected_exit']
            message = result.stdout.decode() if passed else result.stderr.decode()
            return passed, message
        except Exception as e:
            return False, str(e)

    def check_quality_condition(self, check: Dict) -> Tuple[bool, str]:
        """Run linter and count violations"""
        # Similar to check_test_condition but parse output for violations
        pass

    def check_artifact_condition(self, check: Dict) -> Tuple[bool, str]:
        """Check if file exists and optionally if modified in current branch"""
        # Use git diff to check if file modified
        pass

    def check_review_condition(self, check: Dict) -> Tuple[bool, str]:
        """Check review status in database"""
        # Query review_repository.is_adw_ready()
        pass

    def determine_status(self, results: List[ConditionResult]) -> str:
        """
        Determine overall gate status from condition results.

        Logic:
        - If any error-severity condition fails → 'failed'
        - If only warning-severity conditions fail → 'warning'
        - If all pass → 'passed'
        """
        pass
```

BACKEND API ROUTES (app/server/routes/gates_routes.py):
- GET /api/v1/gates - List all gates
- GET /api/v1/gates/{gate_id} - Get gate configuration
- POST /api/v1/gates/{gate_id}/execute - Execute gate for workflow
  - Body: { "workflow_id": str }
  - Returns: GateResult
- GET /api/v1/gates/workflow/{workflow_id} - Get all gate executions for workflow
- POST /api/v1/gates/{gate_id}/override - Override failed gate
  - Body: { "workflow_id": str, "reason": str }
  - Returns: { "overridden": true }

BACKEND REPOSITORY (app/server/repositories/gates_repository.py):
- get_all_gates() -> List[QualityGate]
- get_gate(gate_id: int) -> Optional[QualityGate]
- get_gate_conditions(gate_id: int) -> List[GateCondition]
- create_execution(execution: GateExecution) -> int
- get_workflow_executions(workflow_id: str) -> List[GateExecution]
- override_gate(gate_id: int, workflow_id: str, reason: str) -> bool
- get_gate_by_type(gate_type: str) -> Optional[QualityGate]

BACKEND MODELS (app/server/models/gate.py):
```python
@dataclass
class QualityGate:
    id: Optional[int]
    gate_name: str
    gate_type: str
    description: Optional[str]
    enabled: bool
    required: bool
    created_at: datetime

@dataclass
class GateCondition:
    id: Optional[int]
    gate_id: int
    condition_type: str
    condition_name: str
    condition_check: Dict  # JSON
    error_message: Optional[str]
    severity: str
    order_num: int

@dataclass
class GateExecution:
    id: Optional[int]
    workflow_id: str
    gate_id: int
    execution_timestamp: datetime
    status: str
    passed_conditions: int
    failed_conditions: int
    execution_log: str  # JSON
    override_reason: Optional[str]
```

INTEGRATION WITH WORKFLOW SERVICE:
Modify app/server/services/workflow_service.py to check gates before phase transitions:

```python
def check_gate_before_phase(workflow_id: str, phase: str) -> Tuple[bool, str]:
    """
    Check quality gate before phase transition.

    Gate mapping:
    - pre-plan: Before planning phase
    - pre-build: Before build phase
    - pre-test: Before test phase
    - pre-ship: Before ship phase

    Returns (can_proceed: bool, message: str)
    """
    gate_type_map = {
        'plan': 'pre-plan',
        'build': 'pre-build',
        'test': 'pre-test',
        'ship': 'pre-ship'
    }

    gate_type = gate_type_map.get(phase)
    if not gate_type:
        return True, "No gate for this phase"

    gate = gates_repository.get_gate_by_type(gate_type)
    if not gate or not gate.enabled:
        return True, "Gate not enabled"

    executor = GateExecutor(workflow_id)
    result = executor.execute_gate(gate.id)

    if result.status == 'passed':
        return True, "Gate passed"
    elif result.status == 'warning' and not gate.required:
        return True, f"Gate passed with warnings: {result.failed_conditions} warnings"
    else:
        return False, f"Gate failed: {result.failed_conditions} conditions failed"
```

Files to Create:
Backend:
- app/server/migration/add_quality_gates.sql
- app/server/migration/seed_quality_gates.sql
- app/server/core/gate_executor.py
- app/server/routes/gates_routes.py
- app/server/repositories/gates_repository.py
- app/server/models/gate.py

Tests:
- app/server/tests/core/test_gate_executor.py
- app/server/tests/repositories/test_gates_repository.py
- app/server/tests/routes/test_gates_routes.py
- app/server/tests/integration/test_gate_workflow_integration.py

Files to Modify:
- app/server/server.py (register gates_routes)
- app/server/services/workflow_service.py (add check_gate_before_phase)

Acceptance Criteria:
- [ ] Database schema created with 3 tables
- [ ] Pre-ship gate seeded with 3 conditions
- [ ] GateExecutor can execute test conditions (run command, check exit)
- [ ] GateExecutor can execute quality conditions (run linter, count violations)
- [ ] GateExecutor can execute artifact conditions (check file exists)
- [ ] GateExecutor can execute review conditions (check database)
- [ ] Gate status determined correctly (passed/failed/warning)
- [ ] Gate executions logged to database
- [ ] API route: POST /execute runs gate and returns result
- [ ] API route: GET /workflow/{id} returns all executions
- [ ] workflow_service.py checks gates before phase transitions
- [ ] Workflow pauses if gate fails (required=true)
- [ ] Workflow proceeds with warning if gate fails (required=false)
- [ ] All unit tests pass
- [ ] Integration test: Workflow → Gate check → Pass/Fail

Testing Requirements:
Backend:
- Test gate executor with passing conditions
- Test gate executor with failing conditions
- Test gate executor with mixed results (some pass, some fail)
- Test severity handling (error vs warning)
- Test subprocess execution (pytest, ruff)
- Test artifact checking (file exists)
- Test review checking (database query)
- Test gate override functionality

Integration:
- Test full workflow: Start → Check pre-build gate → Pass → Continue
- Test full workflow: Start → Check pre-ship gate → Fail → Pause
- Test gate override: Fail → Override → Continue

Dependencies:
- Quality Panel (Issues 3.2, 3.3) - For quality checks
- Review Panel (Issue 3.1) - For review checks

Project Path: /Users/Warmonger0/tac/tac-webbuilder

IMPORTANT: This is Part 1 (backend). Part 2 will add frontend visualization.
```

**After Submission:**
- Monitor workflow (large feature, 7-10 day estimate)
- Test gate execution thoroughly
- Verify workflow integration
- Test gate blocking logic

**If Blocked:**
- Check subprocess execution (may need timeout handling)
- Verify gate conditions JSON parsing
- Test workflow_service.py integration
- Create refinement issue if needed

**Do NOT proceed to Issue 4.2 until this is ✅ Complete**

---

### **Issue 4.2: Quality Gates - Part 2 (Frontend)**

**⏱️ Estimated:** 3-5 days | **💰 Estimated Cost:** $3-$7 | **Priority:** HIGH

**Dependencies:** Quality Gates Part 1 (Issue 4.1)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Quality Gates Part 2 - Frontend Visualization

Description:
Create frontend components to visualize quality gate executions: gate pipeline view, execution details modal, and workflow integration. Shows which gates passed/failed for each workflow, with detailed condition results and override functionality.

Context:
- Current state: Backend gate system working (Part 1 complete)
- Problem: No UI to see gate execution results
- Goal: Visual pipeline showing gate status in workflow
- Integration: Uses backend from Part 1, adds to Workflow History view

Technical Specifications:

FRONTEND COMPONENTS:

1. QualityGatesPipeline.tsx - Visual gate pipeline
   - Horizontal timeline showing all gates for a workflow
   - Gate nodes: Plan → Build → Test → Ship
   - Color-coded status:
     - ✅ Green: Passed
     - ❌ Red: Failed
     - ⚠️ Yellow: Warning
     - ⏳ Gray: Pending/Not executed
   - Click gate node to see execution details
   - Shows current gate being checked (pulsing animation)

2. GateExecutionDetailsModal.tsx - Execution details
   - Gate name, type, description
   - Execution timestamp
   - Overall status (passed/failed/warning)
   - Conditions list:
     - Condition name
     - Status (passed/failed)
     - Severity (error/warning/info)
     - Error message (if failed)
     - Details (expandable)
   - "Override Gate" button (if failed and user has permission)
   - Execution log (JSON formatted)

3. GateConditionsList.tsx - Conditions with status
   - Table view: Condition | Status | Severity | Message
   - Icons for status (✅ ❌ ⚠️)
   - Color-coded rows
   - Expandable details section
   - Shows command executed (for test/quality conditions)

4. GateOverrideModal.tsx - Override confirmation
   - Warning message: "Overriding failed gate"
   - Reason textarea (required)
   - Confirm/Cancel buttons
   - Shows which conditions failed
   - Logs override to database

5. GateStatusBadge.tsx - Compact status indicator
   - Small badge showing gate status
   - Used in workflow cards
   - Tooltip with summary: "3/4 gates passed"
   - Click to open gates pipeline

FRONTEND API CLIENT:
Create file: app/client/src/api/gates-client.ts
- getGates(): Promise<QualityGate[]>
- executeGate(gateId: number, workflowId: string): Promise<GateResult>
- getWorkflowGates(workflowId: string): Promise<GateExecution[]>
- overrideGate(gateId: number, workflowId: string, reason: string): Promise<void>

FRONTEND TYPES:
Create file: app/client/src/types/gates.ts
```typescript
export interface QualityGate {
  id: number;
  gate_name: string;
  gate_type: string;
  description?: string;
  enabled: boolean;
  required: boolean;
}

export interface GateExecution {
  id: number;
  workflow_id: string;
  gate_id: number;
  execution_timestamp: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped';
  passed_conditions: number;
  failed_conditions: number;
  execution_log: string;
  override_reason?: string;
}

export interface GateResult {
  gate_id: number;
  status: string;
  passed_conditions: number;
  failed_conditions: number;
  condition_results: ConditionResult[];
}

export interface ConditionResult {
  condition_name: string;
  passed: boolean;
  severity: string;
  message: string;
  details: any;
}
```

INTEGRATION WITH WORKFLOW HISTORY:
Modify app/client/src/components/WorkflowHistoryView.tsx:
- Add GateStatusBadge to each workflow card
- Show gate pipeline when workflow expanded
- Link gate status to overall workflow status

INTEGRATION WITH ADW MONITOR:
Modify app/client/src/components/AdwMonitorCard.tsx:
- Show current gate being checked in workflow progress
- Add gate indicator to phase transitions
- Display "Waiting for gate approval" if gate fails

VISUAL DESIGN:
- Gate pipeline: Horizontal flow with connecting lines
- Use same dark theme (slate-900 background)
- Gate nodes: Circular icons with status colors
- Failed gate: Red pulsing border
- Override modal: Warning colors (yellow/red)

Files to Create:
Frontend:
- app/client/src/components/QualityGatesPipeline.tsx
- app/client/src/components/GateExecutionDetailsModal.tsx
- app/client/src/components/GateConditionsList.tsx
- app/client/src/components/GateOverrideModal.tsx
- app/client/src/components/GateStatusBadge.tsx
- app/client/src/api/gates-client.ts
- app/client/src/types/gates.ts

Tests:
- app/client/src/components/__tests__/QualityGatesPipeline.test.tsx
- app/client/src/components/__tests__/GateExecutionDetailsModal.test.tsx
- app/client/src/components/__tests__/GateOverrideModal.test.tsx

Files to Modify:
- app/client/src/components/WorkflowHistoryView.tsx (add GateStatusBadge)
- app/client/src/components/AdwMonitorCard.tsx (show gate checking status)

Acceptance Criteria:
- [ ] Gate pipeline displays for each workflow
- [ ] Gate nodes show correct status colors
- [ ] Click gate node opens execution details modal
- [ ] Execution details modal shows all conditions
- [ ] Failed conditions highlighted with error messages
- [ ] "Override Gate" button appears for failed gates
- [ ] Override modal requires reason before confirming
- [ ] Override sends to backend API and updates status
- [ ] Gate status badge shows in workflow cards
- [ ] Pipeline shows current gate being checked
- [ ] All frontend tests pass
- [ ] Can view gate executions end-to-end

Testing Requirements:
Frontend:
- Test pipeline renders with correct gate nodes
- Test status colors match execution status
- Test modal opens on gate click
- Test conditions list renders correctly
- Test override flow (open modal → enter reason → confirm)
- Test badge displays correct summary

E2E:
- Full flow: View workflow → See gates pipeline → Click failed gate → View details → Override
- Test in workflow history view
- Test in ADW monitor card

Dependencies:
- Quality Gates Part 1 (Issue 4.1) - Backend must be complete

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**Monitor, test, and merge** following same process as previous issues.

**Do NOT proceed to Issue 4.3 until this is ✅ Complete**

---

### **Issue 4.3: Enhanced Patterns Panel**

**⏱️ Estimated:** 7-10 days | **💰 Estimated Cost:** $5-$12 | **Priority:** MEDIUM

**Dependencies:** Pattern system (existing in codebase)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: Enhanced Patterns Panel with Learning and Analytics

Description:
Enhance existing pattern prediction system with learning, analytics, and recommendations. Tracks pattern accuracy over time, builds pattern library with usage stats, recommends patterns based on similar workflows, and detects pattern sequences.

Context:
- Current state: Basic pattern predictions exist (docs/USING_PATTERN_PREDICTIONS.md)
- Problem: No learning from execution, no analytics, no recommendations
- Goal: Self-improving pattern system with analytics dashboard
- Integration: Extends existing pattern_matcher.py, adds analytics

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/enhance_patterns.sql
```sql
CREATE TABLE pattern_library (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pattern_name TEXT NOT NULL UNIQUE,
  pattern_type TEXT NOT NULL,
  description TEXT,
  keywords TEXT,
  default_confidence REAL,
  usage_count INTEGER DEFAULT 0,
  success_count INTEGER DEFAULT 0,
  total_cost REAL DEFAULT 0.0,
  avg_duration_seconds REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pattern_executions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_id TEXT NOT NULL,
  predicted_pattern TEXT,
  actual_pattern TEXT,
  match_accuracy REAL,
  execution_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  duration_seconds REAL,
  cost REAL,
  success BOOLEAN,
  notes TEXT
);

CREATE TABLE pattern_sequences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sequence_name TEXT NOT NULL,
  patterns TEXT NOT NULL,
  frequency INTEGER DEFAULT 1,
  avg_success_rate REAL,
  avg_total_cost REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pattern_executions_workflow ON pattern_executions(workflow_id);
CREATE INDEX idx_pattern_library_type ON pattern_library(pattern_type);
```

PATTERN ANALYTICS ENGINE:
Create file: app/server/core/pattern_analytics.py
```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class PatternRecommendation:
    pattern_name: str
    confidence: float
    reason: str
    similar_workflows: List[str]

class PatternAnalytics:
    def calculate_pattern_accuracy(self, pattern_name: str) -> float:
        """Calculate historical accuracy: success_count / usage_count"""
        pass

    def recommend_patterns(self, workflow_context: dict) -> List[PatternRecommendation]:
        """
        Recommend patterns based on similar workflows.

        Steps:
        1. Analyze workflow_context (description, type, components)
        2. Find similar past workflows
        3. Get patterns used in similar workflows
        4. Calculate confidence based on success rate
        5. Return recommendations sorted by confidence
        """
        pass

    def detect_pattern_sequences(self) -> List[PatternSequence]:
        """
        Find common pattern sequences.

        Steps:
        1. Group workflows by patterns used
        2. Find patterns that frequently appear together
        3. Calculate success rate for each sequence
        4. Return sequences sorted by frequency
        """
        pass

    def analyze_pattern_cost(self, pattern_name: str) -> Dict:
        """
        Analyze cost and duration for a pattern.

        Returns:
        {
          "avg_cost": float,
          "min_cost": float,
          "max_cost": float,
          "avg_duration": float,
          "usage_count": int
        }
        """
        pass

    def update_pattern_confidence(self, pattern_name: str):
        """
        Auto-adjust confidence based on historical accuracy.

        New confidence = default_confidence * (success_count / usage_count)
        """
        pass

    def record_execution(self, execution: PatternExecution):
        """
        Record pattern execution for learning.

        Updates:
        - pattern_executions table
        - pattern_library usage_count, success_count
        - Re-calculate confidence
        """
        pass
```

BACKEND API ROUTES:
Create file: app/server/routes/patterns_routes.py
- GET /api/v1/patterns/library - Get all patterns with stats
- GET /api/v1/patterns/{pattern_name}/analytics - Get detailed analytics
- GET /api/v1/patterns/recommend - Recommend patterns based on context
  - Query params: description, type, components
- GET /api/v1/patterns/sequences - Get common pattern sequences
- POST /api/v1/patterns/executions/{workflow_id} - Record execution

BACKEND REPOSITORY:
Create file: app/server/repositories/pattern_repository.py
- get_pattern_library() -> List[Pattern]
- get_pattern(pattern_name: str) -> Optional[Pattern]
- update_pattern_stats(pattern_name: str, success: bool, cost: float, duration: float)
- create_execution(execution: PatternExecution) -> int
- get_pattern_executions(pattern_name: str) -> List[PatternExecution]
- get_sequences() -> List[PatternSequence]

BACKEND MODELS:
Create file: app/server/models/pattern_enhanced.py
```python
@dataclass
class Pattern:
    id: Optional[int]
    pattern_name: str
    pattern_type: str
    description: Optional[str]
    keywords: List[str]
    default_confidence: float
    usage_count: int
    success_count: int
    total_cost: float
    avg_duration_seconds: Optional[float]
    created_at: datetime

@dataclass
class PatternExecution:
    id: Optional[int]
    workflow_id: str
    predicted_pattern: Optional[str]
    actual_pattern: Optional[str]
    match_accuracy: float
    execution_timestamp: datetime
    duration_seconds: Optional[float]
    cost: Optional[float]
    success: bool
    notes: Optional[str]

@dataclass
class PatternSequence:
    id: Optional[int]
    sequence_name: str
    patterns: List[str]
    frequency: int
    avg_success_rate: float
    avg_total_cost: float
    created_at: datetime
```

FRONTEND COMPONENTS:

1. PatternsPanel.tsx - Main patterns dashboard
   - Pattern library table
   - Sort by: Frequency | Success Rate | Cost
   - Search/filter patterns
   - "Pattern Analytics" tab
   - "Pattern Sequences" tab

2. PatternAnalyticsCard.tsx - Individual pattern stats
   - Pattern name, type, description
   - Usage stats: X times, Y% success
   - Cost stats: Avg $Z
   - Accuracy trend graph
   - "View Details" button

3. PatternRecommendations.tsx - Recommendations widget
   - Shows in RequestFormCore when typing
   - "Based on your input, you might also want to:"
   - List of patterns with confidence scores
   - Click to add pattern to description

4. PatternSequences.tsx - Common sequences view
   - Visual flow diagram of pattern sequences
   - "Users often run these together:"
   - Success rate and cost for each sequence
   - "Use This Sequence" button

5. PatternDetailModal.tsx - Detailed analytics
   - Full pattern details
   - Usage history chart
   - Cost breakdown
   - Success rate over time
   - Recent executions list

FRONTEND API CLIENT:
Create file: app/client/src/api/patterns-client.ts
- getPatternLibrary(): Promise<Pattern[]>
- getPatternAnalytics(patternName: string): Promise<PatternAnalytics>
- getRecommendations(context: any): Promise<PatternRecommendation[]>
- getPatternSequences(): Promise<PatternSequence[]>
- recordExecution(workflowId: string, execution: PatternExecution): Promise<void>

INTEGRATION:
- Add "Patterns" tab to App.tsx
- Show PatternRecommendations in RequestFormCore (below textarea)
- Auto-record pattern executions when workflow completes
- Link patterns to workflow history

SEED DATA:
Create seed file: app/server/migration/seed_patterns.sql
- Seed existing patterns from pattern_matcher.py
- test:pytest:backend, test:vitest:frontend, build:typecheck, etc.

Files to Create:
Backend:
- app/server/migration/enhance_patterns.sql
- app/server/migration/seed_patterns.sql
- app/server/core/pattern_analytics.py
- app/server/routes/patterns_routes.py
- app/server/repositories/pattern_repository.py
- app/server/models/pattern_enhanced.py

Frontend:
- app/client/src/components/PatternsPanel.tsx
- app/client/src/components/PatternAnalyticsCard.tsx
- app/client/src/components/PatternRecommendations.tsx
- app/client/src/components/PatternSequences.tsx
- app/client/src/components/PatternDetailModal.tsx
- app/client/src/api/patterns-client.ts

Tests:
- app/server/tests/core/test_pattern_analytics.py
- app/server/tests/repositories/test_pattern_repository.py
- app/server/tests/routes/test_patterns_routes.py
- app/client/src/components/__tests__/PatternsPanel.test.tsx

Files to Modify:
- app/server/server.py (register patterns_routes)
- app/client/src/App.tsx (add 'patterns' tab)
- app/client/src/components/RequestFormCore.tsx (add PatternRecommendations)
- app/server/services/workflow_service.py (record executions on completion)

Acceptance Criteria:
- [ ] Database schema created with 3 new tables
- [ ] Existing patterns seeded into pattern_library
- [ ] Pattern analytics calculates accuracy correctly
- [ ] Recommendation engine finds similar workflows
- [ ] Pattern sequences detected from execution history
- [ ] Confidence auto-adjusts based on success rate
- [ ] Frontend displays pattern library with stats
- [ ] Pattern detail modal shows analytics
- [ ] Recommendations appear when typing in RequestFormCore
- [ ] Pattern sequences visualized
- [ ] Executions recorded automatically on workflow completion
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] E2E test: Submit request → Get recommendations → Pattern recorded on completion

Testing Requirements:
Backend:
- Test accuracy calculation
- Test recommendation engine with sample data
- Test sequence detection
- Test confidence adjustment algorithm
- Test execution recording

Frontend:
- Test pattern library rendering
- Test sorting and filtering
- Test analytics card display
- Test recommendations widget
- Test sequence visualization

E2E:
- Full flow: Type description → See recommendations → Submit → Pattern recorded
- Test pattern analytics view
- Test pattern sequence usage

Dependencies:
- Existing pattern system (pattern_matcher.py, USING_PATTERN_PREDICTIONS.md)

Project Path: /Users/Warmonger0/tac/tac-webbuilder
```

#### **After Submission:**

**Monitor, test, and merge** following same process.

**Do NOT proceed to Phase 5 until this is ✅ Complete**

---

### **Checkpoint 4.3 - End of Phase 4**

**Phase 4 Complete Checklist:**
- [ ] All issues 4.1, 4.2, 4.3 are ✅ Complete
- [ ] Quality Gates backend working
- [ ] Quality Gates frontend showing pipeline
- [ ] Enhanced Patterns Panel with analytics
- [ ] Pattern recommendations working
- [ ] All Phase 4 tests passing

---

## 🤖 Phase 5: AI-Powered Features (Week 11-14)

### **Checkpoint 5.0 - Before Starting**

**Prerequisites:**
- [ ] Phase 4 is ✅ Complete
- [ ] All previous features integrated
- [ ] No blocking bugs

---

### **Issue 5.1: Workflow Context Review Agent**

**⏱️ Estimated:** 14-21 days | **💰 Estimated Cost:** $15-$30 | **Priority:** MEDIUM

**Dependencies:** None (standalone AI agent)

#### **Submit to tac-webbuilder UI:**

```markdown
Title: AI-Powered Workflow Context Review Agent

Description:
Create an external AI agent that analyzes codebase context before ADW workflow execution. Identifies relevant files, suggests integration strategies, assesses risks, and optimizes context to minimize token usage. Uses Claude API for analysis with result caching.

Context:
- Current state: ADW workflows start with minimal context analysis
- Problem: Context inefficiency leads to longer workflows and higher costs
- Goal: AI-powered context optimization and integration strategy
- Integration: Optional pre-workflow analysis, caches results

Technical Specifications:

DATABASE SCHEMA:
Create migration: app/server/migration/add_context_review.sql
```sql
CREATE TABLE context_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_id TEXT,
  issue_number INTEGER,
  change_description TEXT NOT NULL,
  project_path TEXT NOT NULL,
  analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  analysis_duration_seconds REAL,
  agent_cost REAL,
  status TEXT NOT NULL CHECK(status IN ('pending', 'analyzing', 'complete', 'failed')),
  result TEXT
);

CREATE TABLE context_suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_id INTEGER NOT NULL,
  suggestion_type TEXT NOT NULL CHECK(suggestion_type IN ('file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy')),
  suggestion_text TEXT NOT NULL,
  confidence REAL,
  priority INTEGER,
  rationale TEXT,
  FOREIGN KEY (review_id) REFERENCES context_reviews(id)
);

CREATE TABLE context_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cache_key TEXT NOT NULL UNIQUE,
  analysis_result TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  access_count INTEGER DEFAULT 0,
  last_accessed DATETIME
);

CREATE INDEX idx_context_reviews_workflow ON context_reviews(workflow_id);
CREATE INDEX idx_context_suggestions_review ON context_suggestions(review_id);
CREATE INDEX idx_context_cache_key ON context_cache(cache_key);
```

CONTEXT REVIEW AGENT:
Create file: app/server/core/context_review_agent.py
```python
import anthropic
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ContextReviewResult:
    integration_strategy: str
    files_to_modify: List[str]
    files_to_create: List[str]
    reference_files: List[str]
    risks: List[str]
    optimized_context: Dict
    estimated_tokens: int

class ContextReviewAgent:
    """External AI agent for codebase context analysis"""

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    async def analyze_context(
        self,
        change_description: str,
        project_path: str,
        existing_files: Optional[List[str]] = None
    ) -> ContextReviewResult:
        """
        Analyze codebase context for a proposed change.

        Steps:
        1. Check cache for similar analysis
        2. Identify relevant files using keyword matching
        3. Read sample files to understand patterns
        4. Use Claude to analyze context
        5. Generate integration suggestions
        6. Cache results for similar requests
        """
        # Check cache
        cache_key = self._generate_cache_key(change_description, project_path)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        # Identify relevant files
        relevant_files = self.identify_relevant_files(change_description, project_path)

        # Read file samples
        file_samples = self._read_file_samples(relevant_files[:10])

        # Analyze with Claude
        result = await self._analyze_with_claude(
            change_description,
            relevant_files,
            file_samples
        )

        # Cache result
        self._cache_result(cache_key, result)

        return result

    def identify_relevant_files(
        self,
        change_description: str,
        project_path: str
    ) -> List[str]:
        """
        Find files relevant to the change using keyword matching.

        Steps:
        1. Extract keywords from description
        2. Walk project directory
        3. Match file names and paths against keywords
        4. Score by relevance
        5. Return sorted list
        """
        pass

    async def _analyze_with_claude(
        self,
        description: str,
        relevant_files: List[str],
        file_samples: Dict[str, str]
    ) -> ContextReviewResult:
        """
        Use Claude API to analyze context and generate strategy.

        Prompt includes:
        - Change description
        - Relevant file list
        - Sample file contents
        - Codebase patterns

        Returns structured ContextReviewResult
        """
        prompt = self._build_analysis_prompt(description, relevant_files, file_samples)

        # Use Haiku for cost efficiency (can upgrade to Sonnet for complex cases)
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response JSON
        result_json = json.loads(response.content[0].text)
        return self._parse_result(result_json)

    def _build_analysis_prompt(
        self,
        description: str,
        files: List[str],
        samples: Dict[str, str]
    ) -> str:
        """Build prompt for Claude API"""
        return f"""
You are a codebase context analyzer. Analyze how this change should integrate.

## Proposed Change
{description}

## Relevant Files (Top 20)
{json.dumps(files[:20], indent=2)}

## Sample Files
{self._format_samples(samples)}

Provide analysis as JSON:
{{
  "integration_strategy": "Describe overall approach...",
  "files_to_modify": ["file1.py", "file2.ts"],
  "files_to_create": ["new_file.py"],
  "reference_files": ["example1.py", "pattern.ts"],
  "risks": ["Potential breaking change in...", "Missing test coverage for..."],
  "optimized_context": {{
    "must_read": ["critical_file.py"],
    "optional": ["reference.md"],
    "skip": ["unrelated.py"]
  }},
  "estimated_tokens": 1500
}}
"""

    def _generate_cache_key(self, description: str, project_path: str) -> str:
        """Generate cache key from description + project"""
        content = f"{description}:{project_path}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[ContextReviewResult]:
        """Check if analysis is cached"""
        # Query context_cache table
        pass

    def _cache_result(self, cache_key: str, result: ContextReviewResult):
        """Cache analysis result"""
        # Insert into context_cache table
        pass
```

BACKEND API ROUTES:
Create file: app/server/routes/context_review_routes.py
- POST /api/v1/context-review/analyze - Start analysis (async job)
  - Body: { "change_description": str, "project_path": str }
  - Returns: { "review_id": int, "status": "analyzing" }
- GET /api/v1/context-review/{review_id} - Get analysis result
- GET /api/v1/context-review/{review_id}/suggestions - Get integration suggestions
- POST /api/v1/context-review/cache-lookup - Check if similar analysis cached
  - Body: { "change_description": str, "project_path": str }
  - Returns: { "cached": bool, "review_id"?: int }

BACKEND REPOSITORY:
Create file: app/server/repositories/context_review_repository.py
- create_review(review: ContextReview) -> int
- get_review(review_id: int) -> Optional[ContextReview]
- update_review_status(review_id: int, status: str, result: Dict)
- create_suggestions(suggestions: List[ContextSuggestion]) -> List[int]
- get_suggestions(review_id: int) -> List[ContextSuggestion]
- check_cache(cache_key: str) -> Optional[str]
- cache_result(cache_key: str, result: str) -> int

BACKEND MODELS:
Create file: app/server/models/context_review.py
```python
@dataclass
class ContextReview:
    id: Optional[int]
    workflow_id: Optional[str]
    issue_number: Optional[int]
    change_description: str
    project_path: str
    analysis_timestamp: datetime
    analysis_duration_seconds: Optional[float]
    agent_cost: Optional[float]
    status: str
    result: Optional[str]

@dataclass
class ContextSuggestion:
    id: Optional[int]
    review_id: int
    suggestion_type: str
    suggestion_text: str
    confidence: float
    priority: int
    rationale: Optional[str]
```

FRONTEND COMPONENTS:

1. ContextReviewPanel.tsx - Analysis results display
   - Shows integration strategy
   - Files to modify/create list
   - Reference files list
   - Risk warnings
   - Estimated token savings

2. ContextAnalysisButton.tsx - Trigger analysis
   - "Analyze Context" button in RequestFormCore
   - Shows loading state during analysis
   - Opens result modal when complete

3. IntegrationStrategyView.tsx - Visual strategy
   - Text description of approach
   - File tree with highlighted files (modify=yellow, create=green)
   - Reference files linked
   - "Use This Strategy" button (passes to ADW workflow)

4. RiskWarnings.tsx - Risk assessment display
   - List of identified risks
   - Color-coded by severity
   - Mitigation suggestions
   - "Proceed Anyway" / "Revise Plan" options

5. ContextOptimizationStats.tsx - Optimization metrics
   - Token estimate: Before / After optimization
   - Files to read: Optimized list
   - Estimated cost savings
   - Cache hit/miss indicator

FRONTEND API CLIENT:
Create file: app/client/src/api/context-review-client.ts
- startContextReview(description: string, projectPath: string): Promise<{ review_id: number }>
- getReviewResult(reviewId: number): Promise<ContextReview>
- getSuggestions(reviewId: number): Promise<ContextSuggestion[]>
- checkCache(description: string, projectPath: string): Promise<{ cached: boolean, review_id?: number }>

INTEGRATION WITH RequestFormCore:
- Add "Analyze Context" button below "Generate Issue" button
- Button triggers context analysis
- Shows loading modal: "Analyzing codebase... ~30 seconds"
- When complete: Shows ContextReviewPanel with results
- Option to "Use Suggestions" → Pre-fills additional context for issue

INTEGRATION WITH ADW WORKFLOWS:
- Optional: Run context review before ADW starts
- Pass optimized_context to ADW agent
- Track whether suggestions improved success rate
- Log cost savings from optimization

COST OPTIMIZATION:
- Use Haiku model for analysis ($0.25 per 1M tokens)
- Cache results for 7 days
- Batch multiple similar requests
- Skip analysis if cache hit (save ~$0.10-0.50 per request)

Files to Create:
Backend:
- app/server/migration/add_context_review.sql
- app/server/core/context_review_agent.py
- app/server/routes/context_review_routes.py
- app/server/repositories/context_review_repository.py
- app/server/models/context_review.py

Frontend:
- app/client/src/components/ContextReviewPanel.tsx
- app/client/src/components/ContextAnalysisButton.tsx
- app/client/src/components/IntegrationStrategyView.tsx
- app/client/src/components/RiskWarnings.tsx
- app/client/src/components/ContextOptimizationStats.tsx
- app/client/src/api/context-review-client.ts

Tests:
- app/server/tests/core/test_context_review_agent.py
- app/server/tests/repositories/test_context_review_repository.py
- app/server/tests/routes/test_context_review_routes.py
- app/client/src/components/__tests__/ContextReviewPanel.test.tsx

Files to Modify:
- app/server/server.py (register context_review_routes)
- app/client/src/components/RequestFormCore.tsx (add ContextAnalysisButton)
- app/server/services/workflow_service.py (optional: use optimized context)

Acceptance Criteria:
- [ ] Database schema created with 3 tables
- [ ] Context review agent can analyze changes with Claude API
- [ ] Agent identifies relevant files using keyword matching
- [ ] Agent generates integration strategy
- [ ] Agent assesses risks
- [ ] Agent optimizes context (must-read vs optional files)
- [ ] Results cached for 7 days
- [ ] Cache hit saves API cost
- [ ] Frontend button triggers analysis
- [ ] Frontend displays results with strategy, files, risks
- [ ] Integration strategy visualized
- [ ] Risk warnings displayed
- [ ] Token savings calculated and displayed
- [ ] All unit tests pass (with mocked Claude API)
- [ ] Integration tests pass
- [ ] E2E test: Click "Analyze Context" → Wait → View results

Testing Requirements:
Backend:
- Test file identification (keyword matching)
- Test Claude API call (mocked for tests)
- Test result parsing
- Test caching (cache hit/miss)
- Test cache key generation
- Test cost calculation

Frontend:
- Test analysis button triggers API
- Test loading state displays
- Test results panel renders correctly
- Test risk warnings display
- Test strategy visualization

E2E:
- Full flow: Submit description → Click "Analyze Context" → View strategy → Use suggestions
- Test cache hit (submit similar request, get instant result)
- Test integration with issue creation

Dependencies:
- Anthropic API key (must be configured in environment)

Project Path: /Users/Warmonger0/tac/tac-webbuilder

IMPORTANT: This uses Claude API, ensure ANTHROPIC_API_KEY is set.
Estimated API cost per analysis: $0.10-0.50 (with caching)
```

#### **After Submission:**

**Monitor, test, and merge** following same process.

**This is the FINAL issue!**

---

### **Checkpoint 5.1 - End of Phase 5 & Project Completion**

**Phase 5 Complete Checklist:**
- [ ] Issue 5.1 is ✅ Complete
- [ ] Context review agent working
- [ ] Claude API integration successful
- [ ] Caching working correctly
- [ ] All Phase 5 tests passing

**🎉 PROJECT COMPLETE CHECKLIST:**
- [ ] All 11 issues ✅ Complete
- [ ] All 5 phases complete
- [ ] All features integrated and working together
- [ ] All tests passing (unit + integration + E2E)
- [ ] Total cost within budget ($72-$156)
- [ ] Documentation updated
- [ ] Production-ready

---

## 📝 Submission Guidelines

### **How to Submit Each Issue:**

1. **Navigate to UI:** http://localhost:5173
2. **Copy full text** from issue section above
3. **Paste** into "Describe what you want to build" textarea
4. **Verify Project Path:** `/Users/Warmonger0/tac/tac-webbuilder`
5. **Click** "Generate Issue"
6. **Monitor** in "Workflows" tab

### **After Each Submission:**

1. **Track in Progress Tracker:**
   - Update status to 🏗️ In Progress
   - Add GitHub issue # when created

2. **Monitor ADW Workflow:**
   - Check "Workflows" tab regularly
   - Watch ADW Monitor Card for progress
   - Note any errors immediately

3. **Review PR When Ready:**
   - Read all files changed
   - Check against acceptance criteria
   - Test locally before merging

4. **Test Thoroughly:**
   - Follow "Test Locally" instructions
   - Run all tests
   - Manual testing required

5. **Merge:**
   - Use `gh pr merge --squash`
   - Pull latest main
   - Verify feature works

6. **Update Progress Tracker:**
   - Change status to ✅ Complete
   - Record actual cost, duration, completion date

7. **Before Next Issue:**
   - Complete checkpoint verification
   - No blocking bugs
   - Ready to proceed

### **If Workflow Blocked:**

1. **Check Logs:**
   ```bash
   tail -f app/server/logs/server.log
   ```

2. **Review Error:**
   - Read ADW workflow error message
   - Check what phase failed
   - Identify specific issue

3. **Unblock:**
   - If simple fix: Submit refinement issue with specific fix
   - If complex: Break into smaller sub-issues
   - If stuck: Document in issue comments, ask for help

4. **Do NOT Proceed:**
   - Mark issue as 🚧 Blocked
   - Fix before submitting next issue
   - Update blocking reason in tracker

---

## 🎯 Success Criteria

### **Per-Issue Success:**
- [ ] ADW workflow completes successfully
- [ ] All acceptance criteria met
- [ ] All tests passing (unit + integration + E2E)
- [ ] PR merged to main
- [ ] Feature tested and working
- [ ] Documentation updated (if needed)

### **Per-Phase Success:**
- [ ] All issues in phase ✅ Complete
- [ ] Checkpoint verification passed
- [ ] Integration tests pass
- [ ] No blocking bugs
- [ ] Ready for next phase

### **Overall Project Success:**
- [ ] All 11 issues ✅ Complete
- [ ] All features integrated and working
- [ ] Total cost within budget ($72-$156)
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Production-ready

---

## 📈 Cost & Time Tracking

### **Actual vs Estimated:**

Update after each issue:

| Phase | Estimated Cost | Actual Cost | Estimated Time | Actual Time |
|-------|----------------|-------------|----------------|-------------|
| Phase 1 | $2-$6 | TBD | 1 week | TBD |
| Phase 2 | $10-$20 | TBD | 2-3 weeks | TBD |
| Phase 3 | $20-$40 | TBD | 3-4 weeks | TBD |
| Phase 4 | $20-$40 | TBD | 3-4 weeks | TBD |
| Phase 5 | $20-$50 | TBD | 3-4 weeks | TBD |
| **Total** | **$72-$156** | **TBD** | **12-16 weeks** | **TBD** |

---

## 🚀 Ready to Start?

### **Next Action:**

1. **Review this document** thoroughly
2. **Copy Issue 1.1** (UI Layout Restructuring)
3. **Go to** http://localhost:5173
4. **Paste** into UI
5. **Submit** and monitor

### **Good Luck!**

Track your progress in the Progress Tracker table at the top of this document.

Update statuses after each milestone.

**Remember:** One issue at a time, no proceeding until current issue is ✅ Complete.
