# Issue #68 Walkthrough: Current vs. Ideal Flow

**Date**: 2025-12-13
**Purpose**: Trace what happens when pasting issue text into Panel 1, identify gaps, propose solution

---

## Example Issue (Using Complex Feature Structure)

Let's use a **realistic complex feature** as our example:

```markdown
Title: Implement Real-Time Collaboration Features

Description:
Add real-time collaboration capabilities to the dashboard allowing multiple
users to work on the same workflow simultaneously with conflict resolution.

Requirements:
- WebSocket-based real-time updates (expand existing system)
- User presence indicators ("Alice is viewing Panel 3")
- Optimistic UI updates with conflict detection
- Operational Transform (OT) for concurrent edits
- Database schema for user sessions and locks
- Backend API for collaboration events
- Frontend UI components for presence/locks
- Integration tests for conflict scenarios

Estimated Time: 12 hours
Priority: Medium
Type: Feature
```

**Complexity Analysis:**
- **Estimated Hours:** 12h → Should be **3-4 phases**
- **Cross-cutting:** Database + Backend + Frontend + WebSocket
- **Dependencies:** Sequential (DB → Backend → Frontend)

---

## Current Flow: What Happens Today

### Step 1: User Pastes into Panel 1

```
Panel 1 Request Form:
┌────────────────────────────────────────────┐
│  Create New Request                        │
├────────────────────────────────────────────┤
│                                            │
│  [Paste issue text here]                   │
│                                            │
│  Project Path: /path/to/project (optional) │
│                                            │
│  [ ] Auto-post (skip confirmation)         │
│                                            │
│  [Generate Issue]                          │
└────────────────────────────────────────────┘
```

User pastes the description above and clicks "Generate Issue"

---

### Step 2: Backend Processing

**File:** `app/server/routes/github_routes.py` → `POST /api/request`

```python
# What happens:
1. nl_processor.py analyzes the text:
   ✅ Detects intent: "feature"
   ✅ Extracts requirements
   ⚠️  Estimates complexity: "medium" or "high"
   ❌ Does NOT analyze if it needs phases
   ❌ Does NOT break down into phases
   ❌ Does NOT generate prompts

2. project_detector.py (if project_path provided):
   ✅ Detects frameworks (React, FastAPI, PostgreSQL)
   ✅ Analyzes file structure
   ⚠️  Estimates complexity
   ❌ Does NOT determine phase count

3. template_router.py:
   ✅ Suggests workflow: "adw_sdlc_complete_iso"
   ✅ Suggests model set
   ❌ Does NOT generate implementation prompts

4. Returns preview:
   {
     "request_id": "abc123",
     "title": "Implement Real-Time Collaboration Features",
     "body": "[formatted issue body]",
     "workflow": "adw_sdlc_complete_iso",
     "estimated_cost": {...}
   }
```

**What's MISSING:**
- ❌ No phase analysis ("This should be 3 phases")
- ❌ No phase breakdown ("Phase 1: DB, Phase 2: Backend, Phase 3: Frontend")
- ❌ No prompt generation
- ❌ No execution plan ("Phase 1 & 2 sequential, Phase 3 can be parallel after 2")

---

### Step 3: User Reviews Preview

```
Preview Modal:
┌────────────────────────────────────────────┐
│  Review GitHub Issue                       │
├────────────────────────────────────────────┤
│  Title: Implement Real-Time Collaboration  │
│                                            │
│  Body: [Shows formatted body]              │
│                                            │
│  Workflow: adw_sdlc_complete_iso      │
│  Estimated Cost: $2-$8                     │
│                                            │
│  ❌ NO PHASE BREAKDOWN SHOWN               │
│  ❌ NO EXECUTION PLAN                      │
│  ❌ NO PROMPTS GENERATED                   │
│                                            │
│  [Cancel]  [Confirm & Post]                │
└────────────────────────────────────────────┘
```

**What user DOESN'T see:**
- How many phases this should be
- Execution sequence
- Generated prompts for each phase
- Parallel execution opportunities

---

### Step 4: User Confirms

```python
# app/server/routes/github_routes.py → POST /api/confirm/{request_id}

# What happens:
1. ✅ Creates single GitHub issue #123
2. ❌ Does NOT create child phases
3. ❌ Does NOT enqueue to phase_queue
4. ❌ Does NOT generate prompts
5. ❌ Does NOT trigger ZTE-hopper
6. ✅ Returns: {"issue_number": 123, "url": "..."}
```

**Result:** Single monolithic GitHub issue created.

---

### Step 5: Manual Execution (Current Reality)

**What user must do manually:**

1. **Read issue #123** on GitHub
2. **Mentally break down into phases:**
   - "Hmm, this needs DB changes, backend, and frontend..."
   - "I think 3 phases makes sense"
3. **Manually create Phase 1 prompt:**
   - Open text editor
   - Write prompt for database schema
   - Include relevant files (how do I know which files?)
   - Save as `FEATURE_123_PHASE_1_database.md`
4. **Execute Phase 1:**
   - Open new Claude Code chat
   - Paste prompt
   - Run implementation
   - Review, test, merge
5. **Repeat for Phase 2:**
   - Write backend prompt
   - Execute in new chat
   - Merge
6. **Repeat for Phase 3:**
   - Write frontend prompt
   - Execute
   - Merge

**Problems:**
- ⏰ **Time-consuming:** 30-60 min just writing prompts
- 🎯 **Inconsistent:** Prompts vary in quality
- 🧠 **Mental overhead:** Must remember context between phases
- 📋 **No tracking:** No record of phase structure
- 🔄 **Repetitive:** Same process for every complex feature
- ❌ **No automation:** ZTE-hopper not utilized

---

### Step 6: No ZTE-Hopper Integration

**Current state:**
```
phase_queue table: EMPTY
PhaseCoordinator: Running but nothing to orchestrate
ZTE workflows: Not triggered
```

**Why ZTE-hopper isn't used:**
1. No phases created in database
2. No entries in phase_queue
3. PhaseCoordinator has nothing to poll
4. Manual execution only

**ZTE-hopper is working** but not connected to Panel 1 flow!

---

## Ideal Flow: Full Automation

### Step 1: User Pastes into Panel 1 (Same)

User pastes same issue text, clicks "Generate Issue"

---

### Step 2: Enhanced Backend Processing

**File:** `app/server/routes/github_routes.py` → `POST /api/request`

```python
# NEW enhanced workflow:

async def create_request(request: RequestData):
    # Step 2a: NL Processing (existing)
    analysis = await nl_processor.analyze(request.nl_input)

    # Step 2b: [NEW] Automatic Phase Analysis
    if analysis.estimated_hours > 2.0:
        from scripts.plan_phases import PhaseAnalyzer

        phase_analyzer = PhaseAnalyzer()
        phase_breakdown = phase_analyzer.analyze_complexity(
            estimated_hours=analysis.estimated_hours,
            description=request.nl_input,
            requirements=analysis.extracted_requirements,
            detected_concerns={
                'database': 'Database schema' in request.nl_input,
                'backend': 'Backend API' in request.nl_input or 'API' in request.nl_input,
                'frontend': 'Frontend UI' in request.nl_input or 'UI components' in request.nl_input,
                'websocket': 'WebSocket' in request.nl_input
            }
        )

        # Result:
        # phase_breakdown = {
        #     'phase_count': 3,
        #     'phases': [
        #         {
        #             'number': 1,
        #             'title': 'Database Schema for Collaboration',
        #             'description': 'Create user_sessions, collaboration_locks tables...',
        #             'estimated_hours': 3.0,
        #             'depends_on': None
        #         },
        #         {
        #             'number': 2,
        #             'title': 'Backend Collaboration API',
        #             'description': 'Implement WebSocket handlers, OT logic...',
        #             'estimated_hours': 4.0,
        #             'depends_on': [1]  # Sequential after Phase 1
        #         },
        #         {
        #             'number': 3,
        #             'title': 'Frontend Collaboration UI',
        #             'description': 'User presence, conflict resolution UI...',
        #             'estimated_hours': 5.0,
        #             'depends_on': [2]  # Sequential after Phase 2
        #         }
        #     ],
        #     'execution_plan': {
        #         'parallel_tracks': [],  # All sequential
        #         'total_time': 12.0
        #     }
        # }

    # Step 2c: [NEW] Generate Prompts for Each Phase
    prompts = []
    for phase in phase_breakdown.phases:
        from scripts.generate_prompt import PromptGenerator

        generator = PromptGenerator()
        prompt = generator.generate_with_phase_context(
            phase_number=phase.number,
            total_phases=phase_breakdown.phase_count,
            phase_title=phase.title,
            phase_description=phase.description,
            depends_on=phase.depends_on,
            nl_input=request.nl_input
        )

        prompts.append({
            'phase_number': phase.number,
            'title': phase.title,
            'content': prompt,
            'estimated_hours': phase.estimated_hours
        })

    # Step 2d: [NEW] Store in planned_features
    feature = planned_features_service.create({
        'title': analysis.title,
        'description': request.nl_input,
        'item_type': 'feature',
        'estimated_hours': analysis.estimated_hours,
        'status': 'planned',
        'priority': analysis.priority,
        'tags': {'multi_phase': True, 'phase_count': phase_breakdown.phase_count}
    })

    # Step 2e: Return enhanced preview
    return {
        'request_id': request_id,
        'feature_id': feature.id,
        'title': analysis.title,
        'body': formatted_body,

        # NEW: Phase breakdown info
        'multi_phase': True,
        'phase_count': phase_breakdown.phase_count,
        'phases': phase_breakdown.phases,
        'execution_plan': phase_breakdown.execution_plan,
        'prompts': prompts,

        'workflow': 'adw_sdlc_complete_iso',
        'estimated_cost': {...}
    }
```

---

### Step 3: Enhanced Preview with Phase Breakdown

```
Preview Modal (ENHANCED):
┌─────────────────────────────────────────────────────────────┐
│  Review Implementation Plan                                 │
├─────────────────────────────────────────────────────────────┤
│  Title: Implement Real-Time Collaboration Features         │
│                                                             │
│  📊 Phase Breakdown (3 phases, ~12 hours total)            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Phase 1: Database Schema for Collaboration          │   │
│  │ - Create user_sessions table                        │   │
│  │ - Create collaboration_locks table                  │   │
│  │ - Add indexes for performance                       │   │
│  │ ⏱️ Est: 3 hours                                      │   │
│  │ 📝 [View Prompt] [Download]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓ (sequential)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Phase 2: Backend Collaboration API                  │   │
│  │ - WebSocket event handlers                          │   │
│  │ - Operational Transform logic                       │   │
│  │ - Session management service                        │   │
│  │ ⏱️ Est: 4 hours | 🔗 Depends on: Phase 1            │   │
│  │ 📝 [View Prompt] [Download]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓ (sequential)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Phase 3: Frontend Collaboration UI                  │   │
│  │ - User presence indicators                          │   │
│  │ - Conflict resolution modal                         │   │
│  │ - Optimistic UI updates                             │   │
│  │ ⏱️ Est: 5 hours | 🔗 Depends on: Phase 2            │   │
│  │ 📝 [View Prompt] [Download]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🎯 Execution Strategy:                                    │
│  - All phases run sequentially (no parallelism)            │
│  - Phase 2 waits for Phase 1 completion                    │
│  - Phase 3 waits for Phase 2 completion                    │
│  - Total time: ~12 hours across 3 workflows                │
│                                                             │
│  💰 Estimated Cost: $6-$12 (across all phases)            │
│  🤖 Workflow: Zero-Touch Execution (ZTE)                   │
│                                                             │
│  ┌──────────────────┐  ┌────────────────────────────┐     │
│  │ Download All     │  │ Execute Manually           │     │
│  │ Prompts (.zip)   │  │ (use prompts in separate   │     │
│  └──────────────────┘  │  Claude Code contexts)     │     │
│                        └────────────────────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⚡ Auto-Execute with ZTE                            │   │
│  │ Automatically runs all phases sequentially via      │   │
│  │ ZTE-hopper queue system. No manual intervention.    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Cancel]                               [Confirm & Execute]│
└─────────────────────────────────────────────────────────────┘
```

**What user SEES:**
- ✅ Clear phase breakdown
- ✅ Execution dependencies
- ✅ Generated prompts (viewable/downloadable)
- ✅ Time estimates per phase
- ✅ Two execution options: Manual or Auto

---

### Step 4: User Chooses "Auto-Execute with ZTE"

```python
# POST /api/confirm/{request_id} with auto_execute=true

async def confirm_request(request_id: str, auto_execute: bool = False):
    # Step 4a: Create parent GitHub issue
    parent_issue = github_api.create_issue(
        title=f"[PARENT] {feature.title}",
        body=f"Multi-phase feature with {phase_count} phases\n\n{feature.description}",
        labels=["multi-phase", "parent"]
    )

    # Update planned_features
    planned_features_service.update(feature.id, {
        'github_issue_number': parent_issue.number,
        'status': 'in_progress'
    })

    if auto_execute:
        # Step 4b: Create Phase 1 GitHub issue with generated prompt
        phase_1_prompt = prompts[0]['content']

        phase_1_issue = github_api.create_issue(
            title=f"{feature.title} - Phase 1: {prompts[0]['title']}",
            body=f"{phase_1_prompt}\n\nInclude workflow: adw_sdlc_complete_iso",
            labels=["phase-1", f"parent-{parent_issue.number}"]
        )

        # Step 4c: Enqueue Phase 1 to phase_queue (status: ready)
        queue_id_1 = phase_queue_service.enqueue(
            parent_issue=parent_issue.number,
            phase_number=1,
            issue_number=phase_1_issue.number,
            status="ready",  # Ready to execute immediately
            depends_on_phase=None,
            phase_data={
                'title': prompts[0]['title'],
                'content': prompts[0]['content'],
                'estimated_hours': prompts[0]['estimated_hours'],
                'workflow_type': 'adw_sdlc_complete_iso',
                'prompt_content': phase_1_prompt
            },
            priority=50,
            queue_position=get_next_position()
        )

        # Step 4d: Enqueue Phase 2 (status: queued, depends on Phase 1)
        queue_id_2 = phase_queue_service.enqueue(
            parent_issue=parent_issue.number,
            phase_number=2,
            issue_number=None,  # Created JIT by PhaseCoordinator
            status="queued",  # Waiting for Phase 1
            depends_on_phase=1,
            phase_data={
                'title': prompts[1]['title'],
                'content': prompts[1]['content'],
                'estimated_hours': prompts[1]['estimated_hours'],
                'workflow_type': 'adw_sdlc_complete_iso',
                'prompt_content': prompts[1]['content']
            },
            priority=50
        )

        # Step 4e: Enqueue Phase 3 (status: queued, depends on Phase 2)
        queue_id_3 = phase_queue_service.enqueue(
            parent_issue=parent_issue.number,
            phase_number=3,
            issue_number=None,
            status="queued",
            depends_on_phase=2,
            phase_data={
                'title': prompts[2]['title'],
                'content': prompts[2]['content'],
                'estimated_hours': prompts[2]['estimated_hours'],
                'workflow_type': 'adw_sdlc_complete_iso',
                'prompt_content': prompts[2]['content']
            },
            priority=50
        )

    return {
        'success': True,
        'parent_issue': parent_issue.number,
        'phase_1_issue': phase_1_issue.number,
        'queued_phases': [queue_id_1, queue_id_2, queue_id_3],
        'message': 'Phase 1 queued for execution. Phases 2-3 will auto-execute upon completion.'
    }
```

---

### Step 5: ZTE-Hopper Orchestration (Automatic)

```
PhaseCoordinator Background Poller (every 10 seconds):
┌─────────────────────────────────────────────────────────┐
│  Iteration 1 (T+0s):                                    │
├─────────────────────────────────────────────────────────┤
│  1. Check for ready phases:                             │
│     SELECT * FROM phase_queue WHERE status='ready'      │
│     → Found: Phase 1 (issue_number=124, parent=123)     │
│                                                         │
│  2. Auto-launch ADW workflow:                           │
│     subprocess.Popen([                                  │
│         "uv", "run",                                    │
│         "adws/adw_sdlc_complete_iso.py",           │
│         "124",  # issue_number                          │
│         "adw-abc123"  # auto-generated ADW ID           │
│     ])                                                  │
│                                                         │
│  3. Update phase_queue:                                 │
│     UPDATE phase_queue                                  │
│     SET status='running', adw_id='adw-abc123',         │
│         started_timestamp=NOW()                         │
│     WHERE queue_id=queue_id_1                          │
└─────────────────────────────────────────────────────────┘

ADW Workflow Executes (trees/adw-abc123/):
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Plan → Creates database migration plan       │
│  Phase 2: Validate → No baseline errors                │
│  Phase 3: Build → Creates migration files              │
│  Phase 4: Lint → Passes                                │
│  Phase 5: Test → Runs migration tests                  │
│  Phase 6: Review → Validates schema                    │
│  Phase 7: Document → Updates schema docs               │
│  Phase 8: Ship → Auto-approves & merges PR ✅          │
│  Phase 9: Cleanup → Removes worktree                   │
│                                                         │
│  Completion: POST /api/issue/124/complete              │
└─────────────────────────────────────────────────────────┘

PhaseCoordinator (Iteration 120, T+1200s = 20 min later):
┌─────────────────────────────────────────────────────────┐
│  1. Check workflow_history:                             │
│     SELECT * FROM workflow_history                      │
│     WHERE issue_number=124 AND status='completed'       │
│     → Found: Phase 1 completed at T+1200s               │
│                                                         │
│  2. Mark Phase 1 complete in phase_queue:               │
│     UPDATE phase_queue SET status='completed'           │
│     WHERE queue_id=queue_id_1                          │
│                                                         │
│  3. Trigger Phase 2 dependency:                         │
│     - Phase 2 depends_on_phase=1 (now complete)         │
│     - Create GitHub issue for Phase 2 (JIT):            │
│       issue_125 = create_issue(                         │
│           title="Phase 2: Backend Collaboration API",   │
│           body=prompts[1]['content']                    │
│       )                                                 │
│     - Update Phase 2 in phase_queue:                    │
│       UPDATE phase_queue                                │
│       SET status='ready', issue_number=125              │
│       WHERE queue_id=queue_id_2                        │
│                                                         │
│  4. Next iteration (T+1210s):                           │
│     - Detects Phase 2 status='ready'                    │
│     - Auto-launches ADW for issue 125                   │
│     - Repeat process                                    │
└─────────────────────────────────────────────────────────┘

... Phase 2 executes (~4 hours) ...
... PhaseCoordinator detects completion ...
... Triggers Phase 3 ...
... Phase 3 executes (~5 hours) ...
... All phases complete ...

Final State:
┌─────────────────────────────────────────────────────────┐
│  phase_queue:                                           │
│  - Phase 1: status='completed', issue=124              │
│  - Phase 2: status='completed', issue=125              │
│  - Phase 3: status='completed', issue=126              │
│                                                         │
│  planned_features:                                      │
│  - Feature #123: status='completed'                    │
│  - actual_hours: 11.5h (vs. estimated 12h)             │
│  - completion_notes: "All phases shipped successfully" │
│                                                         │
│  GitHub:                                                │
│  - Issue #123: Closed (parent)                         │
│  - Issue #124: Closed (Phase 1 merged)                 │
│  - Issue #125: Closed (Phase 2 merged)                 │
│  - Issue #126: Closed (Phase 3 merged)                 │
│                                                         │
│  Production: All features live! ✅                      │
└─────────────────────────────────────────────────────────┘
```

---

## Gap Summary: Current vs. Ideal

| Capability | Current State | Ideal State |
|------------|---------------|-------------|
| **Phase Detection** | ❌ Manual only | ✅ Automatic during submission |
| **Phase Breakdown** | ❌ None | ✅ Intelligent analysis (1-5 phases) |
| **Prompt Generation** | ❌ Manual per phase | ✅ Auto-generated for all phases |
| **Execution Planning** | ❌ None | ✅ Sequential/parallel detection |
| **Panel 1 Integration** | ⚠️ Partial (single issues only) | ✅ Full multi-phase support |
| **ZTE-Hopper Connection** | ❌ Not connected | ✅ Fully integrated |
| **planned_features Link** | ❌ No link from Panel 1 | ✅ Auto-creates DB entries |
| **Prompt Storage** | ❌ No storage | ✅ Database + files |
| **Progress Tracking** | ❌ Manual | ✅ Automatic (phase_queue + planned_features) |
| **Zero-Touch Execution** | ❌ Not available | ✅ One-click automation |

---

## Key Missing Components

### 1. Phase Analysis Integration in Panel 1

**File:** `app/server/routes/github_routes.py`

**Current:** Only does NL processing
**Needed:** Add phase analysis step

```python
# Add after NL processing:
if analysis.estimated_hours > 2.0:
    phase_breakdown = analyze_phases(analysis)
```

---

### 2. Prompt Generation for Each Phase

**File:** `scripts/generate_prompt.py`

**Current:** Single prompts only
**Needed:** Phase context support

```python
# Add method:
def generate_with_phase_context(
    phase_number, total_phases, depends_on
)
```

---

### 3. Preview UI Enhancement

**File:** `app/client/src/components/RequestFormPreview.tsx`

**Current:** Shows single issue preview
**Needed:** Phase breakdown visualization

```tsx
{preview.multi_phase && (
  <PhaseBreakdown
    phases={preview.phases}
    execution_plan={preview.execution_plan}
    prompts={preview.prompts}
  />
)}
```

---

### 4. Confirmation with Auto-Execute

**File:** `app/server/routes/github_routes.py`

**Current:** Creates single issue
**Needed:** Create parent + enqueue phases

```python
if auto_execute:
    # Create parent issue
    # Create Phase 1 issue
    # Enqueue Phases 2-N to phase_queue
    # Return queue IDs
```

---

### 5. Prompt Content in phase_queue

**Table:** `phase_queue`

**Current:** `phase_data` is generic TEXT/JSONB
**Needed:** Include prompt_content

```json
{
  "title": "Phase 1: Database Schema",
  "content": "Brief description",
  "prompt_content": "[Full generated prompt]",  // NEW
  "workflow_type": "adw_sdlc_complete_iso",
  "estimated_hours": 3.0
}
```

---

## Advantages of Ideal Flow

### 1. **Efficiency Gains**

| Task | Current Time | Ideal Time | Savings |
|------|-------------|-----------|---------|
| Analyze complexity | 10-15 min | 0 min (auto) | 100% |
| Break into phases | 15-30 min | 0 min (auto) | 100% |
| Write Phase 1 prompt | 15-20 min | 0 min (auto) | 100% |
| Write Phase 2 prompt | 15-20 min | 0 min (auto) | 100% |
| Write Phase 3 prompt | 15-20 min | 0 min (auto) | 100% |
| Execute Phase 1 | Manual | Auto | - |
| Wait & trigger Phase 2 | Manual | Auto | - |
| Execute Phase 2 | Manual | Auto | - |
| Wait & trigger Phase 3 | Manual | Auto | - |
| Execute Phase 3 | Manual | Auto | - |
| **Total Overhead** | **70-105 min** | **~30 sec** | **99% reduction** |

---

### 2. **Token/Context Efficiency**

**Current (Manual Prompts):**
- Each prompt ~800-1,200 tokens
- Repetitive context (project background, file locations)
- Inconsistent quality

**Ideal (Auto-Generated):**
- Optimized templates ~600-800 tokens
- Shared context loaded once (`/prime`)
- Codebase-analyzed file suggestions (only relevant files)
- Consistent quality

**Savings:** ~25-40% token reduction per phase

---

### 3. **Observability Efficiency**

**Current:**
- Manual tracking in separate documents
- No structured data
- Hard to query historical patterns

**Ideal:**
- All phases tracked in `phase_queue`
- Prompts stored in `generated_prompts` table
- Execution results in `workflow_history`
- Queryable: "What's the avg time for 3-phase features?"

**Benefit:** Complete audit trail, ROI tracking, pattern analysis

---

### 4. **Best Practices Enforcement**

**Current:**
- User decides phase granularity (inconsistent)
- May create too-large phases (context overflow)
- May create too-small phases (unnecessary overhead)

**Ideal:**
- Algorithm enforces optimal granularity:
  - ≤2h = 1 phase (quick wins)
  - 2-6h = 2 phases (foundation + integration)
  - 6-12h = 3 phases (data + backend + frontend)
  - 12-18h = 4 phases (granular breakdown)
  - 18h+ = 5 phases (maximum split)

**Benefit:** Consistent quality, optimal context usage

---

### 5. **Parallel Execution Detection**

**Current:**
- User must manually identify parallelism
- Often misses opportunities

**Ideal:**
- Algorithm detects independent phases:
  - "Phase 1 (DB) and Phase 2 (Docs) can run parallel"
  - "Phase 3 (Frontend) must wait for Phase 1 (API)"

**Benefit:** Faster delivery through parallelism

---

## Disadvantages / Risks

### 1. **Increased Complexity**

**Risk:** More moving parts = more potential failures

**Mitigation:**
- Phased rollout (MVP → Enhancement → Full)
- Comprehensive testing
- Fallback to manual mode if auto fails

---

### 2. **Prompt Quality Variance**

**Risk:** Auto-generated prompts may not be as good as hand-crafted

**Mitigation:**
- Template library with proven patterns
- User review before auto-execute
- Feedback loop to improve templates
- Allow manual editing

---

### 3. **Phase Breakdown Disagreements**

**Risk:** User may disagree with recommended phases

**Mitigation:**
- Show as recommendation, not requirement
- "Edit Phases" button in preview
- Learn from user overrides

---

### 4. **Latency During Submission**

**Risk:** 5-10s delay for analysis + generation

**Mitigation:**
- Async processing with progress indicator
- "Quick submit" option to skip analysis
- Cache results for similar requests

---

### 5. **Data Consistency**

**Risk:** More databases = more sync challenges

**Mitigation:**
- Transactional operations
- Foreign key constraints
- Reconciliation scripts

---

## Recommendations

### Immediate Next Steps

1. ✅ **Verify ZTE-hopper is working:**
   ```bash
   # Test end-to-end
   cd app/server
   env POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
       POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user \
       POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
       python3 -c "
   from services.phase_queue_service import PhaseQueueService
   svc = PhaseQueueService()
   all_phases = svc.get_all()
   print(f'Total phases in queue: {len(all_phases)}')
   for p in all_phases[:5]:
       print(f'  {p.queue_id}: Phase {p.phase_number}, Status: {p.status}')
   "

   # Check PhaseCoordinator is running
   ps aux | grep phase_coordinator
   ```

2. 📋 **Create test case with realistic feature:**
   - Use issue #68 or create new complex feature
   - Document current vs. ideal flow
   - Identify specific gaps

3. 🎯 **Choose implementation approach:**
   - **Option A:** MVP (3.25h) - Standalone `/genprompts`, no Panel 1 changes
   - **Option B:** Full automation (22h) - Complete integration
   - **Option C:** Phased (recommended) - Start with MVP, add Panel 1 integration (Phase 2), then full ZTE (Phase 3)

---

### Recommended Path: Phased Implementation

**Week 1: MVP (3.25h)**
- Implement `/genprompts` as designed
- Test with existing planned_features
- **Value:** Manual prompt generation tool

**Week 2: Panel 1 Integration (7h)**
- Link Panel 1 to planned_features
- Add auto phase analysis
- Enhanced preview with phase breakdown
- **Value:** Seamless UX, see phases immediately

**Week 3: ZTE Integration (12h)**
- Auto-enqueue to phase_queue
- Prompt content in phase_data
- Full automation option
- **Value:** Zero-touch execution

**Week 4: Refinement (8h)**
- User feedback integration
- Template optimization
- Observability dashboard
- **Value:** Production-quality system

---

## Summary

**The Problem:** Currently, pasting issue text into Panel 1 creates a single GitHub issue with no phase analysis, no prompt generation, and no ZTE-hopper integration. User must manually break down, write prompts, and execute phases.

**The Solution:** Enhance Panel 1 flow with automatic phase analysis, multi-phase prompt generation, and ZTE-hopper orchestration for fully automated execution.

**The Value:** Reduces 70-105 minutes of manual work per complex feature to ~30 seconds. Improves consistency, enables observability, and leverages existing ZTE-hopper infrastructure.

**The Path:** Phased implementation over 4 weeks, starting with MVP (`/genprompts`), then Panel 1 integration, then full ZTE automation.

**Next Action:** Verify ZTE-hopper status, choose implementation approach, start with MVP or go straight to full automation based on urgency/resources.
