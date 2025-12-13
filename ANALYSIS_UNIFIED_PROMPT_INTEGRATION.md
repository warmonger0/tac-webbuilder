# Unified Prompt Generation System - Integration Analysis

**Date**: 2025-12-13
**Context**: Analysis of DESIGN_UNIFIED_PROMPT_GENERATION.md integration with tac-webbuilder request processing pipeline
**Status**: Technical Design Document

---

## Executive Summary

This document analyzes how the proposed Unified Prompt Generation system (from DESIGN_UNIFIED_PROMPT_GENERATION.md) integrates with the existing tac-webbuilder architecture, specifically:

1. **Panel 1 Request Flow** - Natural language input → GitHub issue creation
2. **ZTE-Hopper Queue System** - Zero-touch execution with JIT issue creation
3. **ADW Workflows** - 10-phase SDLC in isolated worktrees
4. **Phase Coordination** - Automatic phase triggering and dependency management

**Key Finding**: The design document proposes a `/genprompts` command for *manual Claude Code prompt generation*, which is **orthogonal** to the ZTE-hopper's *automated ADW workflow execution*. These are two different workflows serving different purposes.

### Critical Distinction

| Aspect | ZTE-Hopper (Production) | Unified Prompt Gen (Proposed) |
|--------|-------------------------|-------------------------------|
| **Purpose** | Automated ADW execution | Manual Claude Code prompts |
| **Trigger** | GitHub issue creation | Manual `/genprompts` command |
| **Execution** | Subprocess ADW workflows | Human executes in Claude Code |
| **Phase Detection** | `phaseParser.ts` (frontend) | `plan_phases.py` (backend) |
| **Output** | Automated worktree execution | Markdown prompt files |
| **Integration Point** | Panel 1 → GitHub → PhaseCoordinator | `planned_features` DB |

---

## 1. Gap Analysis: Current State vs. Proposed Design

### 1.1 What's Already Implemented ✅

#### A. Panel 1 Request Flow (PRODUCTION)
**Location**: `/Users/Warmonger0/tac/tac-webbuilder/app/client/src/components/RequestFormCore.tsx`

```typescript
// Flow: NL Input → GitHub Issue Creation
handleSubmit() {
  → submitRequest({ nl_input, project_path, auto_post, phases? })
    → POST /api/request
    → GitHubIssueService.submit_nl_request()
      ├─ Single-phase: process_request() → GitHub issue
      └─ Multi-phase: MultiPhaseIssueHandler.handle_multi_phase_request()
         ├─ Create parent issue
         ├─ Create child issues (optional JIT)
         └─ Enqueue phases with dependencies
  → GET /api/preview/{request_id}
  → POST /api/confirm/{request_id}
}
```

**Multi-Phase Detection**: `phaseParser.ts` parses uploaded `.md` files for `## Phase N:` headers
- Detects phases via regex: `/^#{1,3}\s*(?:Phase\s*)?(\d+|One|Two|...)\s*[:：\-—]\s*(.+)/`
- Extracts title, content, external docs per phase
- Sends structured `phases[]` array to backend

#### B. ZTE-Hopper Queue System (PRODUCTION)
**Location**: `/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_coordination/phase_coordinator.py`

**Core Components**:
1. **PhaseQueueService** - CRUD operations on `phase_queue` table
2. **PhaseCoordinator** - Background polling (every 10s)
   - Detects workflow completions via `workflow_history` table
   - Auto-creates GitHub issues JIT for ready phases
   - Auto-launches ADW workflows via subprocess
   - Handles pause/resume queue management
3. **MultiPhaseIssueHandler** - Creates parent + child issues, enqueues phases
4. **HopperSorter** - Priority queue for Phase 1 selection

**Execution Flow**:
```python
# PhaseCoordinator polling loop (async, every 10s)
while running:
  _check_workflow_completions()
    ├─ _create_missing_issues()  # JIT issue creation for ready phases
    ├─ _auto_start_ready_phases()  # Launch ADW subprocess
    │   ├─ determine_workflow_for_phase()  # Select adw_sdlc_complete_iso, etc.
    │   ├─ Generate adw_id
    │   ├─ subprocess.Popen(["uv", "run", workflow_script, issue_number, adw_id])
    │   └─ Mark phase as "running"
    └─ _process_phase_completion()  # Mark complete/failed, trigger next phase
```

**Database Schema** (`phase_queue`):
```sql
CREATE TABLE phase_queue (
  queue_id TEXT PRIMARY KEY,
  parent_issue INTEGER,
  phase_number INTEGER,
  issue_number INTEGER NULL,  -- Created JIT
  status TEXT,  -- pending|ready|running|completed|failed|blocked
  depends_on_phase INTEGER NULL,
  phase_data JSON,
  adw_id TEXT NULL,
  created_at TEXT,
  updated_at TEXT
);
```

#### C. Prompt Generation Infrastructure (PARTIAL)

**Already Exists**:
1. **`scripts/generate_prompt.py`** - Single prompt generation
   - Queries `planned_features` database
   - Uses `CodebaseAnalyzer` to find relevant files
   - Fills `.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`
   - Generates `QUICK_WIN_{id}_{slug}.md` or `FEATURE_{id}_{slug}.md`

2. **`scripts/plan_phases.py`** - Phase analysis (NEW, basic)
   - Analyzes features by hours: ≤2h→1 phase, 2-6h→2 phases, etc.
   - Creates phase breakdown with dependencies
   - Generates `PHASE_PLAN_{timestamp}.md` coordination document
   - **LIMITATION**: Does NOT generate individual prompt files

3. **`PlannedFeaturesService`** - Database CRUD
   - Tracks features in `planned_features` table
   - Status: planned, in_progress, completed, cancelled

**What's Missing** (per design doc):
- ❌ Integration between `plan_phases.py` and `generate_prompt.py`
- ❌ Multi-phase prompt generation (each phase gets its own prompt)
- ❌ Orchestrator script (`orchestrate_prompts.sh`)
- ❌ `/genprompts` slash command
- ❌ JSON output mode for `plan_phases.py`

### 1.2 Architectural Overlap Detection

**CRITICAL INSIGHT**: There are **TWO SEPARATE PHASE DETECTION SYSTEMS**:

| System | Location | Purpose | Phase Source | Output |
|--------|----------|---------|--------------|--------|
| **Frontend Phase Parser** | `phaseParser.ts` | Parse uploaded `.md` files | User-written documents | Panel 1 multi-phase GitHub issues |
| **Backend Phase Analyzer** | `plan_phases.py` | Analyze `planned_features` DB | Database records | Coordination doc (no prompts yet) |

**Do they conflict?** No - they serve different workflows:
- **Frontend** (`phaseParser.ts`): User uploads pre-written multi-phase doc → Panel 1 → ZTE-hopper
- **Backend** (`plan_phases.py`): Analyze DB features → Generate prompts for manual Claude Code execution

---

## 2. Integration Architecture

### 2.1 Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PANEL 1: REQUEST FORM                       │
│  RequestFormCore.tsx                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ NL Input: "Build user management API..."                    │  │
│  │ File Upload: drag-drop .md file (optional)                  │  │
│  │   ↓ phaseParser.ts detects "## Phase 1:" headers            │  │
│  │   ↓ Extracts {phase_number, title, content, externalDocs}   │  │
│  │ [Generate Issue] → submitRequest({ nl_input, phases? })     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    GITHUB ISSUE SERVICE                             │
│  /app/server/services/github_issue_service.py                      │
│                                                                     │
│  submit_nl_request(request)                                         │
│    ├─ Single-phase: process_request() → GitHubIssue                │
│    │   → POST to GitHub → Issue #N created                         │
│    │                                                                │
│    └─ Multi-phase (phases != null):                                │
│        MultiPhaseIssueHandler.handle_multi_phase_request()          │
│          ├─ Create parent issue with full content                  │
│          ├─ Create child issues for Phase 1 (optional JIT)         │
│          ├─ Enqueue phases in phase_queue:                         │
│          │   Phase 1: status=ready, depends_on=null                │
│          │   Phase 2: status=pending, depends_on=1                 │
│          │   Phase 3: status=pending, depends_on=2                 │
│          └─ Return {parent_issue_number, child_issues[]}           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 ZTE-HOPPER: PHASE COORDINATOR                       │
│  /app/server/services/phase_coordination/phase_coordinator.py      │
│                                                                     │
│  Background Polling Loop (every 10s):                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 1. _create_missing_issues()                                  │  │
│  │    → Find phases where status=ready AND issue_number=null    │  │
│  │    → Create GitHub issue JIT                                 │  │
│  │    → Update phase_queue.issue_number                         │  │
│  │                                                               │  │
│  │ 2. _auto_start_ready_phases() (if not paused)                │  │
│  │    → Find phases where status=ready AND issue_number!=null   │  │
│  │    → determine_workflow_for_phase() → adw_sdlc_complete_iso  │  │
│  │    → subprocess.Popen(["uv", "run", workflow, issue, adw_id])│  │
│  │    → Mark phase as "running"                                 │  │
│  │                                                               │  │
│  │ 3. _process_phase_completion()                               │  │
│  │    → Check workflow_history for completed/failed             │  │
│  │    → Mark phase complete/failed                              │  │
│  │    → If complete: trigger next phase (mark ready)            │  │
│  │    → If failed: mark dependent phases as "blocked"           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      ADW WORKFLOWS                                  │
│  /adws/adw_sdlc_complete_iso.py                                    │
│                                                                     │
│  10-Phase SDLC in isolated worktree:                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 1. Plan → 2. Validate → 3. Build → 4. Lint → 5. Test         │  │
│  │ 6. Review → 7. Document → 8. Ship → 9. Cleanup → 10. Verify  │  │
│  │                                                               │  │
│  │ Execution:                                                    │  │
│  │ - Isolated worktree in trees/{adw_id}/                       │  │
│  │ - Shared state: adw_state_{adw_id}.json                      │  │
│  │ - Port allocation: 9100-9199 (server), 9200-9299 (client)    │  │
│  │ - Completion webhook: POST /workflow-complete                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Where Does Unified Prompt Generation Fit?

**Answer**: It's a **SEPARATE, PARALLEL workflow** for manual Claude Code execution.

```
┌─────────────────────────────────────────────────────────────────────┐
│              PROPOSED: UNIFIED PROMPT GENERATION                    │
│  (For manual Claude Code execution, NOT automated ADW)              │
│                                                                     │
│  Trigger: /genprompts 49 52 104                                     │
│    ↓                                                                │
│  scripts/orchestrate_prompts.sh                                     │
│    ├─ Step 1: plan_phases.py --output-json                         │
│    │   → Query planned_features DB                                 │
│    │   → Determine phases: 49→1, 52→1, 104→3                       │
│    │   → Output phase_metadata.json                                │
│    │                                                                │
│    ├─ Step 2: generate_prompt.py (loop)                            │
│    │   → For each phase in metadata:                               │
│    │     gen_prompt.sh 104 --phase 1 --total-phases 3              │
│    │   → Generates:                                                │
│    │     QUICK_WIN_49_fix_error_handling.md                        │
│    │     QUICK_WIN_52_memoize_computations.md                      │
│    │     FEATURE_104_PHASE_1_database_setup.md                     │
│    │     FEATURE_104_PHASE_2_backend_services.md                   │
│    │     FEATURE_104_PHASE_3_frontend_ui.md                        │
│    │                                                                │
│    └─ Step 3: create_coordination_doc.sh                           │
│        → PHASE_PLAN_20251213_120000.md                             │
│        → Shows execution order, dependencies, parallel tracks      │
│                                                                     │
│  Human Execution:                                                   │
│    1. Read PHASE_PLAN_20251213_120000.md                           │
│    2. Open Claude Code contexts                                    │
│    3. Copy/paste prompt files                                      │
│    4. Execute manually in separate Claude Code sessions            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Integration Points

| Integration Point | Current State | Proposed Change | Impact |
|-------------------|---------------|-----------------|--------|
| **Panel 1 → GitHub** | ✅ Production (uses `phaseParser.ts`) | No change | N/A |
| **Panel 1 → planned_features DB** | ❌ No direct link | Could add: Store request in DB for later prompt gen | Optional enhancement |
| **ZTE-Hopper → ADW** | ✅ Production (automated) | No change | N/A |
| **planned_features → Prompts** | ⚠️ Partial (`generate_prompt.py` single only) | ✅ Full multi-phase support via `/genprompts` | New capability |
| **Prompts → ZTE-Hopper** | ❌ No integration | ❌ Not recommended (different purposes) | Keep separate |

**Recommendation**: Keep workflows separate. They serve different needs:
- **ZTE-Hopper**: Automated, zero-touch, production execution
- **Unified Prompts**: Manual, exploratory, development work

---

## 3. Critical Design Decisions

### 3.1 Where Should Prompt Generation Occur?

**Options Analysis**:

| Option | Trigger Point | Pros | Cons | Recommendation |
|--------|--------------|------|------|----------------|
| **A. Panel 1 Submission** | User submits request → auto-generate prompts | Immediate feedback | Mixes automated + manual workflows | ❌ No |
| **B. PhaseCoordinator JIT** | Phase becomes ready → generate prompt | Could provide ADW context | Violates zero-touch philosophy | ❌ No |
| **C. Pre-ADW Execution** | Before ADW workflow starts → generate prompt | Could replace ADW planning | Redundant with ADW's own planning | ❌ No |
| **D. Separate Command** | Manual `/genprompts` invocation | Clean separation, human-driven | Requires manual trigger | ✅ **YES** |
| **E. Hybrid: Store + Generate** | Panel 1 → DB → `/genprompts` later | Captures all requests, deferred prompt gen | Requires DB schema changes | ✅ Future enhancement |

**Decision**: **Option D** (Separate Command) is correct for MVP.

**Reasoning**:
1. ZTE-hopper is production-ready and should NOT be modified for manual workflows
2. Prompt generation is for *development/exploration*, not *production automation*
3. Developers need prompts for features NOT going through Panel 1 (e.g., backlog items, bugs)
4. `/genprompts` command matches the design doc's intent

**Future Enhancement (Option E)**:
```python
# Potential: Link Panel 1 requests to planned_features DB
POST /api/request {nl_input, project_path}
  → Create planned_features record
  → Return {request_id, feature_id}
  → User can later run /genprompts {feature_id}
```

### 3.2 Multi-Phase Detection: Which System to Use?

**Current Duplication**:

| System | When Used | Phase Source | Output |
|--------|-----------|--------------|--------|
| **phaseParser.ts** | Panel 1 file upload | Parse `.md` headers | GitHub issues + phase_queue entries |
| **plan_phases.py** | `/genprompts` command | Analyze `planned_features` DB by hours/complexity | Coordination doc + prompt files |

**Do they need to align?** No - different purposes:
- **Frontend parser**: Handles user-provided multi-phase documents (explicit phases)
- **Backend analyzer**: Auto-detects phases based on complexity (implicit phases)

**Recommendation**: Keep both, but consider:

```python
# Option: Reuse plan_phases.py logic in Panel 1 flow
# If user doesn't upload .md file, auto-analyze NL input

POST /api/request {nl_input, auto_detect_phases: true}
  → If no phases provided:
    → Run plan_phases.py logic on nl_input
    → Detect: hours, complexity, files
    → Auto-split into phases: 1-5 based on heuristics
  → Create parent + child issues
```

**Risk**: Auto-detection may be inaccurate. User-provided phases are explicit and safer.

**Decision**: Keep current approach (user-provided phases via file upload). Auto-detection is future enhancement.

### 3.3 Prompt Storage: Database or File System?

**Current State**: File system only (`QUICK_WIN_*.md` files in project root)

**Options**:

| Storage | Pros | Cons | Use Case |
|---------|------|------|----------|
| **File System** | Simple, version controlled, human-readable | No queryability, clutters repo | ✅ MVP (design doc approach) |
| **Database** | Queryable, structured, no clutter | Harder to read/share, needs UI | Future: prompt library, search |
| **Hybrid** | Files for human use, DB for metadata | Best of both | Complex implementation |

**Recommendation**: File system for MVP (matches design doc).

**Future Enhancement**:
```sql
CREATE TABLE generated_prompts (
  prompt_id TEXT PRIMARY KEY,
  feature_id INTEGER REFERENCES planned_features(id),
  phase_number INTEGER,
  filename TEXT,
  content TEXT,
  created_at TIMESTAMP,
  used_in_session TEXT NULL  -- Track which Claude Code session used it
);
```

### 3.4 Relation to ZTE's "Zero-Touch" Philosophy

**Core Question**: Does prompt generation conflict with zero-touch execution?

**Answer**: No - they're complementary:

| Aspect | ZTE-Hopper (Zero-Touch) | Unified Prompts (Manual) |
|--------|-------------------------|---------------------------|
| **Philosophy** | Minimize human intervention | Maximize human control |
| **Use Case** | Production features (clear requirements) | Exploratory work (unclear scope) |
| **Workflow** | Panel 1 → GitHub → Auto-execute | DB → Generate prompts → Manual execute |
| **Intervention** | None (fully automated) | Full (human reads/edits prompts) |
| **Complexity** | Handles well-defined features | Handles ambiguous/complex features |

**When to Use Each**:

```
Decision Tree:

Is the feature well-defined with clear requirements?
  ├─ Yes → Use ZTE-Hopper (Panel 1 → Auto-execute)
  └─ No → Use Unified Prompts (/genprompts → Manual review)

Does the feature need human judgment/creativity?
  ├─ Yes → Unified Prompts (manual Claude Code)
  └─ No → ZTE-Hopper (automated ADW)

Is this a production-critical feature?
  ├─ Yes → ZTE-Hopper (tested, reliable workflows)
  └─ No → Unified Prompts (experimental, flexible)
```

**Example Scenarios**:

| Scenario | Recommended Workflow | Reason |
|----------|---------------------|--------|
| Fix typo in docs | ZTE-Hopper | Simple, clear scope |
| Add CRUD endpoint | ZTE-Hopper | Well-defined pattern |
| Refactor authentication system | Unified Prompts | Complex, needs human oversight |
| Explore new architecture | Unified Prompts | Unclear scope, needs iteration |
| Batch process 10 small bugs | ZTE-Hopper | Repetitive, automated |

---

## 4. Implementation Roadmap

### Phase 1: Minimal Viable Integration (MVP)

**Goal**: Get `/genprompts` command working without touching ZTE-hopper

**Tasks**:
1. ✅ Enhance `plan_phases.py` with `--output-json` flag (0.5h)
   ```python
   # Add to plan_phases.py
   if args.output_json:
       print(json.dumps({
           "features": [...],
           "parallel_tracks": [...],
           "file_conflicts": {...}
       }))
   ```

2. ✅ Enhance `generate_prompt.py` with phase context (1h)
   ```python
   # Add parameters: --phase, --total-phases, --depends-on
   def generate_with_phase_context(feature_id, phase_number, total_phases, depends_on):
       # Modify template to include phase context
       # Generate filename: FEATURE_{id}_PHASE_{num}_{slug}.md
   ```

3. ✅ Create `scripts/orchestrate_prompts.sh` (1h)
   ```bash
   #!/bin/bash
   # 1. Run plan_phases.py --output-json > phase_metadata.json
   # 2. Parse JSON, loop over phases
   # 3. Call gen_prompt.sh for each phase
   # 4. Generate coordination doc
   ```

4. ✅ Create `.claude/commands/genprompts.md` (0.25h)
   ```markdown
   # Generate Implementation Prompts
   Execute: ./scripts/orchestrate_prompts.sh $@
   ```

5. ✅ Test end-to-end with sample features (0.5h)
   ```bash
   /genprompts 49 52 104
   # Expected output:
   # - QUICK_WIN_49_*.md
   # - QUICK_WIN_52_*.md
   # - FEATURE_104_PHASE_1_*.md
   # - FEATURE_104_PHASE_2_*.md
   # - FEATURE_104_PHASE_3_*.md
   # - PHASE_PLAN_20251213_*.md
   ```

**Total Time**: 3.25 hours (matches design doc estimate)

**Success Criteria**:
- ✅ `/genprompts` command generates all prompt files
- ✅ Coordination doc shows correct execution order
- ✅ Phase prompts include dependency context
- ✅ No impact on ZTE-hopper functionality

### Phase 2: Enhanced Automation (Future)

**Goal**: Improve integration between Panel 1 and prompt generation

**Tasks**:
1. **Link Panel 1 to planned_features DB** (2h)
   ```python
   # Modify github_issue_service.py
   async def submit_nl_request(request):
       # After creating GitHub issue:
       feature_record = await planned_features_service.create({
           "title": github_issue.title,
           "description": request.nl_input,
           "issue_number": issue_number,
           "estimated_hours": estimate_hours(github_issue),
           "status": "in_progress"
       })
       return {
           "request_id": request_id,
           "feature_id": feature_record.id  # NEW
       }
   ```

2. **Auto-detect phases in Panel 1** (3h)
   ```python
   # Add to github_issue_service.py
   if not request.phases and request.auto_detect_phases:
       # Run plan_phases.py logic
       phases = analyze_phases_from_nl_input(request.nl_input)
       # Create multi-phase request automatically
   ```

3. **Prompt regeneration from existing issues** (2h)
   ```bash
   /genprompts --from-issue 123
   # Fetch issue from GitHub
   # Analyze complexity
   # Generate prompts
   ```

**Total Time**: 7 hours

### Phase 3: Full Zero-Touch Prompt Generation (Advanced)

**Goal**: Generate prompts automatically as part of ZTE-hopper workflow

**Tasks**:
1. **Pre-execution prompt generation** (4h)
   ```python
   # PhaseCoordinator._auto_start_ready_phases()
   if GENERATE_PROMPTS_FOR_PHASES:  # Feature flag
       prompt_file = generate_prompt_for_phase(phase)
       attach_to_github_issue(phase.issue_number, prompt_file)
   ```

2. **Prompt effectiveness tracking** (3h)
   ```sql
   CREATE TABLE prompt_usage (
       prompt_id TEXT PRIMARY KEY,
       feature_id INTEGER,
       phase_number INTEGER,
       used_at TIMESTAMP,
       adw_id TEXT,
       completion_status TEXT,
       human_edits_made BOOLEAN
   );
   ```

3. **Adaptive phase detection** (5h)
   ```python
   # Learn from successful executions
   # If Feature X with Y hours usually needs 3 phases
   # Auto-suggest 3 phases for similar features
   ```

**Total Time**: 12 hours

**Risk**: High complexity, may conflict with zero-touch philosophy. Recommend careful evaluation before implementing.

---

## 5. Potential Issues & Risks

### 5.1 Architectural Conflicts

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Confusion between workflows** | Users unsure when to use ZTE vs. prompts | Clear documentation, UI indicators |
| **Divergent phase detection** | Frontend parser ≠ backend analyzer | Accept as feature (different purposes) |
| **Prompt files clutter repo** | Root directory full of `.md` files | Move to `prompts/` directory, add to `.gitignore` |
| **Duplicate effort** | Same feature in Panel 1 AND planned_features | Link via `feature_id`, check for duplicates |

**Mitigation Plan**:
```bash
# Move generated prompts to dedicated directory
mkdir -p prompts/generated
echo "prompts/generated/*.md" >> .gitignore

# Update orchestrate_prompts.sh
OUTPUT_DIR="prompts/generated"
```

### 5.2 Performance Bottlenecks

| Bottleneck | Cause | Impact | Solution |
|------------|-------|--------|----------|
| **CodebaseAnalyzer slowness** | Scans entire codebase per feature | `/genprompts` takes minutes for many features | Cache results, parallel processing |
| **Database queries** | N+1 queries in loop | Slow for 100+ features | Batch fetch from `planned_features` |
| **Template filling** | Reads template file each time | Minor overhead | Cache template in memory |

**Optimization**:
```python
# plan_phases.py enhancement
class PhaseAnalyzer:
    def __init__(self):
        self.codebase_cache = {}  # Cache codebase analysis results

    def analyze_feature(self, feature_id):
        # Check cache first
        if feature_id in self.codebase_cache:
            return self.codebase_cache[feature_id]

        # Analyze and cache
        result = self.codebase_analyzer.find_relevant_files(feature)
        self.codebase_cache[feature_id] = result
        return result
```

### 5.3 User Experience Concerns

| Concern | Description | Impact | Solution |
|---------|-------------|--------|----------|
| **Prompt file discovery** | Users lose track of generated files | Wasted time searching | Coordination doc includes file list |
| **Outdated prompts** | Prompts generated, then feature changes | Stale prompts used | Timestamp in filename, warn if old |
| **Manual execution burden** | Copy-paste prompts into Claude Code | Tedious for many phases | Accept as tradeoff for control |
| **Lack of feedback loop** | No way to track if prompts worked | Can't improve generation | Phase 3: Add usage tracking |

**UX Enhancement**:
```markdown
# PHASE_PLAN_20251213_120000.md (enhanced)

## Execution Checklist

- [ ] Phase 1: Database Setup (FEATURE_104_PHASE_1_database_setup.md)
      Started: ____  Completed: ____  Notes: __________

- [ ] Phase 2: Backend Services (FEATURE_104_PHASE_2_backend_services.md)
      Started: ____  Completed: ____  Notes: __________

- [ ] Phase 3: Frontend UI (FEATURE_104_PHASE_3_frontend_ui.md)
      Started: ____  Completed: ____  Notes: __________
```

### 5.4 Data Consistency Challenges

| Challenge | Scenario | Risk | Mitigation |
|-----------|----------|------|------------|
| **planned_features ≠ GitHub issues** | Feature updated in DB, not in GitHub | Prompts out of sync with reality | Sync mechanism, timestamp checks |
| **Phase count mismatch** | DB says 3 phases, GitHub has 5 issues | Incorrect dependencies | Validate before prompt generation |
| **Deleted features** | Feature removed from DB, prompts remain | Orphaned prompt files | Cleanup script, reference checking |

**Consistency Check**:
```python
# Pre-execution validation
def validate_feature_consistency(feature_id):
    db_feature = planned_features_service.get_by_id(feature_id)
    if db_feature.issue_number:
        gh_issue = github_poster.get_issue(db_feature.issue_number)
        if gh_issue.state == "closed":
            raise ValueError(f"Feature {feature_id} already completed (issue closed)")
```

---

## 6. Concrete Code Examples

### 6.1 Enhanced plan_phases.py with JSON Output

```python
# scripts/plan_phases.py

def output_json(self, all_phases: List[List[Phase]], dependency_analysis: Dict) -> str:
    """Output phase metadata as JSON for orchestration."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "features": [],
        "summary": {
            "total_features": len(all_phases),
            "total_phases": dependency_analysis['total_phases'],
            "total_hours": dependency_analysis['total_hours'],
            "parallel_tracks": len(dependency_analysis['parallel_tracks'])
        },
        "parallel_tracks": [],
        "file_conflicts": dependency_analysis['file_conflicts']
    }

    # Populate features and phases
    for phases in all_phases:
        feature_data = {
            "issue_id": phases[0].issue_id,
            "phases": []
        }
        for phase in phases:
            feature_data["phases"].append({
                "phase_number": phase.phase_number,
                "total_phases": phase.total_phases,
                "title": phase.title,
                "description": phase.description,
                "estimated_hours": phase.estimated_hours,
                "filename": phase.filename,
                "depends_on": phase.depends_on,
                "files_to_modify": phase.files_to_modify
            })
        data["features"].append(feature_data)

    # Add parallel tracks with execution order
    for i, track in enumerate(dependency_analysis['parallel_tracks']):
        track_data = {
            "track_number": i + 1,
            "can_run_parallel": len(dependency_analysis['parallel_tracks']) > 1,
            "phases": []
        }
        for phase in track:
            track_data["phases"].append({
                "issue_id": phase.issue_id,
                "phase_number": phase.phase_number,
                "filename": phase.filename,
                "estimated_hours": phase.estimated_hours
            })
        data["parallel_tracks"].append(track_data)

    return json.dumps(data, indent=2)

# Add to main()
if args.output_json:
    json_output = doc_gen.output_json(all_phases, dependency_analysis)
    print(json_output)
    sys.exit(0)
```

### 6.2 Enhanced generate_prompt.py with Phase Context

```python
# scripts/generate_prompt.py

def generate_with_phase_context(
    self,
    feature_id: int,
    phase_number: int = 1,
    total_phases: int = 1,
    depends_on: List[Tuple[int, int]] = None
) -> str:
    """
    Generate prompt with phase context.

    Args:
        feature_id: Feature ID from planned_features
        phase_number: Current phase number (1-based)
        total_phases: Total number of phases for this feature
        depends_on: List of (feature_id, phase_number) dependencies

    Returns:
        Generated prompt content with phase context
    """
    feature = self.service.get_by_id(feature_id)
    if not feature:
        raise ValueError(f"Feature #{feature_id} not found")

    # Analyze codebase
    context = self.analyzer.find_relevant_files(feature)

    # Fill template with phase modifications
    prompt_content = self._fill_template_with_phase(
        feature,
        context,
        phase_number,
        total_phases,
        depends_on or []
    )

    # Generate phase-aware filename
    filename = self._generate_phase_filename(
        feature,
        phase_number,
        total_phases
    )

    # Write to file
    output_path = Path.cwd() / "prompts" / "generated" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt_content)

    print(f"✅ Generated: {filename}")
    return prompt_content

def _fill_template_with_phase(self, feature, context, phase_num, total, deps):
    """Fill template with phase-specific sections."""
    content = self.template

    # Basic replacements
    replacements = {
        "[Type]": feature.item_type.capitalize(),
        "[ID]": str(feature.id),
        "[Title]": feature.title if total == 1 else f"{feature.title} - Phase {phase_num}",
        "[One-line description]": feature.description or feature.title,
        "[High/Medium/Low]": (feature.priority or "Medium").capitalize(),
        "[Bug/Feature/Enhancement/Session]": feature.item_type.capitalize(),
        "[X hours]": f"{feature.estimated_hours / total:.1f}" if feature.estimated_hours else "TBD",
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    # Add phase overview section if multi-phase
    if total > 1:
        phase_section = self._generate_phase_overview(phase_num, total, deps, feature)
        # Insert after Task Summary section
        task_summary_end = content.find("## Problem Statement")
        if task_summary_end != -1:
            content = (
                content[:task_summary_end] +
                phase_section + "\n\n" +
                content[task_summary_end:]
            )

    # Insert codebase context
    codebase_section = self._generate_codebase_section(feature, context)
    problem_statement_pos = content.find("## Problem Statement")
    if problem_statement_pos != -1:
        content = (
            content[:problem_statement_pos] +
            codebase_section + "\n\n" +
            content[problem_statement_pos:]
        )

    return content

def _generate_phase_overview(self, phase_num, total, deps, feature):
    """Generate phase overview section for multi-phase prompts."""
    sections = ["## Phase Overview", ""]

    sections.append(f"**This is Phase {phase_num} of {total}** for Feature #{feature.id}: {feature.title}")
    sections.append("")

    # Previous phases
    if phase_num > 1:
        sections.append("**Completed Phases:**")
        for i in range(1, phase_num):
            sections.append(f"- Phase {i}: ✅ Completed")
        sections.append("")

    # Current phase
    sections.append("**Current Phase:**")
    sections.append(f"- Phase {phase_num}: 🔨 In Progress")
    sections.append("")

    # Dependencies
    if deps:
        sections.append("**Dependencies:**")
        for dep_feature_id, dep_phase_num in deps:
            if dep_feature_id == feature.id:
                sections.append(f"- Requires Phase {dep_phase_num} to be completed")
            else:
                sections.append(f"- Requires Feature #{dep_feature_id} Phase {dep_phase_num}")
        sections.append("")

    # Upcoming phases
    if phase_num < total:
        sections.append("**Upcoming Phases:**")
        for i in range(phase_num + 1, total + 1):
            sections.append(f"- Phase {i}: ⏳ Pending")
        sections.append("")

    return "\n".join(sections)

def _generate_phase_filename(self, feature, phase_num, total):
    """Generate filename for phase prompt."""
    slug = self._slugify(feature.title)

    if total == 1:
        # Single phase
        if feature.estimated_hours and feature.estimated_hours <= 2.0:
            return f"QUICK_WIN_{feature.id}_{slug}.md"
        return f"FEATURE_{feature.id}_{slug}.md"
    else:
        # Multi-phase
        phase_slug = slug.split('_')[0]  # Take first word of title
        return f"FEATURE_{feature.id}_PHASE_{phase_num}_{phase_slug}.md"

# Add CLI support
parser.add_argument("--phase", type=int, default=1, help="Phase number (for multi-phase features)")
parser.add_argument("--total-phases", type=int, default=1, help="Total number of phases")
parser.add_argument("--depends-on", type=str, help="Dependencies (format: '104:1,105:2')")

args = parser.parse_args()

# Parse dependencies
depends_on = []
if args.depends_on:
    for dep in args.depends_on.split(','):
        feature_id, phase_num = dep.split(':')
        depends_on.append((int(feature_id), int(phase_num)))

generator.generate_with_phase_context(
    args.feature_id,
    args.phase,
    args.total_phases,
    depends_on
)
```

### 6.3 Orchestrator Script

```bash
#!/bin/bash
# scripts/orchestrate_prompts.sh
# Orchestrates full prompt generation workflow

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

ISSUE_IDS="$@"

# Output directory for generated prompts
PROMPTS_DIR="prompts/generated"
mkdir -p "$PROMPTS_DIR"

echo "🔍 Step 1: Analyzing phases for issues: $ISSUE_IDS"
echo ""

# Run phase analysis with JSON output
METADATA_JSON=$(./scripts/plan_phases.sh $ISSUE_IDS --output-json)

if [ $? -ne 0 ]; then
    echo "❌ Phase analysis failed"
    exit 1
fi

# Save metadata to temp file for parsing
TEMP_FILE=$(mktemp)
echo "$METADATA_JSON" > "$TEMP_FILE"

echo "📝 Step 2: Generating prompts for each phase..."
echo ""

# Parse JSON and generate prompts using Python
python3 <<EOF
import json
import subprocess
import sys

with open('$TEMP_FILE', 'r') as f:
    data = json.load(f)

total_prompts = 0
failed_prompts = []

for feature in data['features']:
    issue_id = feature['issue_id']
    for phase in feature['phases']:
        phase_num = phase['phase_number']
        total = phase['total_phases']
        depends = ','.join([f"{d[0]}:{d[1]}" for d in phase.get('depends_on', [])])

        cmd = [
            './scripts/gen_prompt.sh',
            str(issue_id),
            '--phase', str(phase_num),
            '--total-phases', str(total)
        ]
        if depends:
            cmd.extend(['--depends-on', depends])

        print(f"   Generating {phase['filename']}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"   ❌ Failed: {result.stderr}", file=sys.stderr)
            failed_prompts.append(phase['filename'])
        else:
            total_prompts += 1
            print(f"   ✅ Success")

print(f"\n{'✅' if not failed_prompts else '⚠️'} Generated {total_prompts} prompt files")

if failed_prompts:
    print(f"\n⚠️  Failed to generate {len(failed_prompts)} prompts:")
    for f in failed_prompts:
        print(f"   - {f}")
    sys.exit(1)

# Output summary for coordination doc
print(f"\n📊 Summary:")
print(f"   Total Features: {data['summary']['total_features']}")
print(f"   Total Phases: {data['summary']['total_phases']}")
print(f"   Estimated Hours: {data['summary']['total_hours']:.1f}h")
print(f"   Parallel Tracks: {data['summary']['parallel_tracks']}")
EOF

if [ $? -ne 0 ]; then
    echo "❌ Prompt generation failed"
    rm "$TEMP_FILE"
    exit 1
fi

echo ""
echo "📊 Step 3: Creating coordination document..."
echo ""

# Generate coordination doc from metadata
COORD_FILE=$(./scripts/create_coordination_doc.sh "$TEMP_FILE")

rm "$TEMP_FILE"

echo "✅ Prompt generation complete!"
echo ""
echo "📄 Coordination Document: $COORD_FILE"
echo "📁 Prompt Files: $PROMPTS_DIR/"
echo ""
echo "Next steps:"
echo "1. Review $COORD_FILE for execution sequence"
echo "2. Execute phases as shown in parallel tracks"
echo "3. Mark each phase complete before proceeding to next"
```

### 6.4 Slash Command Integration

```markdown
<!-- .claude/commands/genprompts.md -->
# Generate Implementation Prompts

Analyze issues, determine phase breakdown, and generate all implementation prompts.

## Usage

```bash
/genprompts [issue_ids...]
```

## Examples

```bash
# Generate prompts for specific issues
/genprompts 49 52 55 57

# Generate prompts for all planned issues
/genprompts

# Generate prompts for a single complex feature
/genprompts 104
```

## What This Does

1. **Analyzes Complexity** - Determines how many phases each issue needs based on:
   - Estimated hours (≤2h = 1 phase, 2-6h = 2 phases, etc.)
   - File count and cross-cutting concerns
   - Explicit phase mentions in description

2. **Generates Phase Prompts** - Creates individual prompt files:
   - Simple issues: `QUICK_WIN_{id}_{slug}.md`
   - Complex features: `FEATURE_{id}_PHASE_{n}_{slug}.md`
   - Each prompt includes codebase context, dependencies, phase overview

3. **Creates Coordination Doc** - Shows execution order:
   - Parallel execution opportunities
   - Dependencies between phases
   - File modification conflicts
   - Execution checklist

## Output Location

All files are generated in: `prompts/generated/`

- Prompt files: `FEATURE_104_PHASE_1_database.md`, etc.
- Coordination doc: `PHASE_PLAN_20251213_120000.md`

## Next Steps

After running this command:

1. **Read** the coordination document to understand execution order
2. **Open** separate Claude Code contexts for parallel phases
3. **Copy/paste** prompt content into each context
4. **Execute** phases in the order shown
5. **Mark complete** in Plans Panel before proceeding to next phase

## Notes

- This generates prompts for **manual** Claude Code execution
- Does NOT trigger automated ADW workflows (use Panel 1 for that)
- Prompts are for development/exploration, not production automation
- Files are timestamped - regenerate if feature changes
```

---

## 7. Decision Matrices

### 7.1 Workflow Selection Matrix

| Feature Characteristic | Use ZTE-Hopper | Use Unified Prompts | Reasoning |
|------------------------|----------------|---------------------|-----------|
| **Well-defined scope** | ✅ | ❌ | Automation works best with clear requirements |
| **Ambiguous requirements** | ❌ | ✅ | Needs human judgment to clarify |
| **Repetitive pattern** | ✅ | ❌ | ADW workflows handle patterns efficiently |
| **Novel/experimental** | ❌ | ✅ | Needs exploration, iteration |
| **Production-critical** | ✅ | ❌ | Tested workflows more reliable |
| **Learning/research** | ❌ | ✅ | Prompts allow deeper understanding |
| **Time-sensitive** | ✅ | ❌ | Automation faster for execution |
| **Needs human creativity** | ❌ | ✅ | ADW is systematic, not creative |
| **Batch processing** | ✅ | ❌ | Parallel ADW execution scales better |
| **Complex refactoring** | ❌ | ✅ | Requires careful manual oversight |

### 7.2 Phase Detection Method Matrix

| Scenario | Frontend Parser (phaseParser.ts) | Backend Analyzer (plan_phases.py) | Both | Reasoning |
|----------|----------------------------------|-----------------------------------|------|-----------|
| **User uploads multi-phase .md** | ✅ | ❌ | ❌ | Explicit phases defined by user |
| **NL input with no file** | ❌ | ✅ | ❌ | Auto-detect from complexity |
| **Feature in DB, no GitHub issue** | ❌ | ✅ | ❌ | Backend has DB access |
| **Panel 1 submission** | ✅ | ❌ | ❌ | Frontend-driven workflow |
| **Manual `/genprompts`** | ❌ | ✅ | ❌ | Backend-driven workflow |
| **Validate user phases** | ✅ | ✅ | ✅ | Frontend parses, backend validates complexity |

### 7.3 Storage Location Matrix

| Data Type | Database | File System | Both | Reasoning |
|-----------|----------|-------------|------|-----------|
| **Generated prompts** | ❌ | ✅ (MVP) | ✅ (Future) | Files human-readable, DB queryable |
| **Phase metadata** | ✅ (`phase_queue`) | ❌ | ❌ | Structured data for automation |
| **Coordination docs** | ❌ | ✅ | ❌ | Reference documents, not operational data |
| **Feature definitions** | ✅ (`planned_features`) | ❌ | ❌ | Source of truth for prompts |
| **Execution history** | ✅ (`workflow_history`) | ❌ | ❌ | Tracking and analytics |
| **Codebase analysis cache** | ❌ | ✅ (temp files) | ❌ | Large data, short-lived |

---

## 8. Recommendations

### 8.1 Immediate Actions (MVP)

1. **Implement `/genprompts` command** as designed in DESIGN_UNIFIED_PROMPT_GENERATION.md
   - Follow the 3-step orchestration: analyze → generate → coordinate
   - Estimated effort: 3.25 hours (as per design doc)
   - **Do NOT modify ZTE-hopper** - keep workflows separate

2. **Create dedicated prompts directory**
   ```bash
   mkdir -p prompts/generated
   echo "prompts/generated/*.md" >> .gitignore
   ```

3. **Document the two workflows clearly**
   - Update README with workflow decision tree
   - Add examples of when to use each approach
   - Create troubleshooting guide

4. **Test with real features**
   - Run `/genprompts` on backlog items
   - Compare generated prompts vs. manual prompts
   - Collect feedback on prompt quality

### 8.2 Near-term Enhancements (Phase 2)

1. **Link Panel 1 to planned_features DB** (Optional)
   - When user creates request, also create DB entry
   - Enables: Panel 1 → ZTE-hopper → Later review with `/genprompts`
   - Use case: Re-generate prompts for failed ADW runs

2. **Improve phase detection logic**
   - Analyze successful executions to refine heuristics
   - Add machine learning: "Similar to Feature X which needed N phases"
   - Allow manual override in coordination doc

3. **Add prompt versioning**
   - Track: feature_id, phase_number, version, generated_at
   - Warn users if prompt is stale (feature updated since generation)
   - Store in DB for queryability

### 8.3 Long-term Considerations (Phase 3)

1. **Evaluate ZTE integration carefully**
   - Only integrate if clear benefit (e.g., attach prompts to issues)
   - Avoid breaking zero-touch philosophy
   - Consider feature flag: `ATTACH_PROMPTS_TO_ISSUES=true`

2. **Build prompt effectiveness feedback loop**
   - Track: Which prompts were used? Did ADW succeed after manual execution?
   - Use data to improve generation logic
   - Surface insights: "Phases 1-2 usually succeed, Phase 3 often fails"

3. **Consider prompt library**
   - Store common patterns: "CRUD API", "Auth System", "Data Migration"
   - Template-based generation: Select pattern → Customize → Generate
   - Community-driven: Share successful prompts

### 8.4 What NOT to Do ❌

1. **Do NOT merge workflows prematurely**
   - Keep ZTE-hopper and unified prompts separate
   - Avoid: "Auto-generate prompts on Panel 1 submission"
   - Reason: Mixes automated + manual philosophies

2. **Do NOT duplicate phase detection everywhere**
   - Frontend parser for user uploads
   - Backend analyzer for DB features
   - Don't add: Third system in ZTE-hopper
   - Reason: Maintenance nightmare

3. **Do NOT store prompts ONLY in database**
   - Files are essential for human review
   - DB is optional enhancement, not replacement
   - Reason: Prompts must be readable/editable

4. **Do NOT auto-execute generated prompts**
   - Prompts are for human review, not automation
   - If auto-execution needed, use ZTE-hopper
   - Reason: Defeats purpose of manual oversight

---

## 9. Conclusion

### Key Takeaways

1. **Two Complementary Workflows**:
   - **ZTE-Hopper**: Automated, production-ready, zero-touch execution via Panel 1
   - **Unified Prompts**: Manual, exploratory, development workflow via `/genprompts`

2. **No Architectural Conflict**:
   - Systems serve different purposes
   - Minimal overlap (both analyze phases, but different contexts)
   - Can coexist without modification

3. **Implementation Path**:
   - Phase 1 (MVP): Implement as designed - 3.25 hours
   - Phase 2: Optional enhancements - 7 hours
   - Phase 3: Advanced features - 12 hours (evaluate carefully)

4. **Critical Success Factors**:
   - ✅ Keep workflows separate
   - ✅ Clear documentation on when to use each
   - ✅ File-based storage for prompts (human-readable)
   - ✅ Coordination docs show execution order
   - ❌ Don't break zero-touch philosophy
   - ❌ Don't duplicate phase detection unnecessarily

### Next Steps

1. **Review this analysis** with development team
2. **Decide on implementation timeline**:
   - MVP only? (3.25 hours)
   - MVP + Phase 2? (10.25 hours)
   - Full roadmap? (22.25 hours)
3. **Create implementation ticket** with:
   - Tasks from Phase 1 roadmap
   - Acceptance criteria from design doc
   - Testing requirements
4. **Update documentation**:
   - README: Workflow decision tree
   - CONTRIBUTING: When to use /genprompts
   - ARCHITECTURE: Diagram showing both workflows

---

## Appendix A: File Path Reference

### Current Architecture Files
```
app/
├── client/src/
│   ├── components/
│   │   ├── RequestFormCore.tsx          # Panel 1 UI
│   │   └── RequestFormHooks.tsx         # Panel 1 logic
│   ├── utils/
│   │   └── phaseParser.ts               # Frontend phase detection
│   └── api/
│       └── githubClient.ts              # API calls
│
└── server/
    ├── routes/
    │   ├── github_routes.py             # /request, /preview, /confirm
    │   └── queue_routes.py              # /queue, /workflow-complete
    ├── services/
    │   ├── github_issue_service.py      # Issue creation logic
    │   ├── multi_phase_issue_handler.py # Multi-phase GitHub issues
    │   ├── phase_queue_service.py       # Queue CRUD
    │   ├── planned_features_service.py  # DB CRUD
    │   └── phase_coordination/
    │       ├── phase_coordinator.py     # ZTE-hopper core
    │       ├── phase_github_notifier.py # GitHub comments
    │       └── workflow_completion_detector.py
    └── repositories/
        └── phase_queue_repository.py    # DB access

scripts/
├── generate_prompt.py                   # Single prompt generation
├── gen_prompt.sh                        # Wrapper for above
├── plan_phases.py                       # Phase analysis
└── plan_phases.sh                       # Wrapper for above

.claude/
└── templates/
    └── IMPLEMENTATION_PROMPT_TEMPLATE.md
```

### Proposed New Files
```
scripts/
├── orchestrate_prompts.sh               # NEW: Main orchestrator
└── create_coordination_doc.sh           # NEW: Doc generator

.claude/
└── commands/
    └── genprompts.md                    # NEW: Slash command

prompts/
└── generated/                           # NEW: Output directory
    ├── QUICK_WIN_49_*.md
    ├── FEATURE_104_PHASE_1_*.md
    ├── FEATURE_104_PHASE_2_*.md
    └── PHASE_PLAN_20251213_*.md
```

---

## Appendix B: Database Schema Reference

### phase_queue (Production)
```sql
CREATE TABLE phase_queue (
  queue_id TEXT PRIMARY KEY,          -- UUID
  parent_issue INTEGER NOT NULL,      -- GitHub parent issue #
  phase_number INTEGER NOT NULL,      -- 1, 2, 3, ...
  issue_number INTEGER,               -- GitHub child issue # (JIT creation)
  status TEXT NOT NULL,               -- pending|ready|running|completed|failed|blocked
  depends_on_phase INTEGER,           -- Phase number dependency
  phase_data TEXT NOT NULL,           -- JSON {title, content, externalDocs, workflow_type, adw_id}
  adw_id TEXT,                        -- ADW workflow ID when running
  pr_number INTEGER,                  -- Pull request # if created
  error_message TEXT,                 -- Error if failed/blocked
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_depends ON phase_queue(parent_issue, depends_on_phase);
```

### planned_features (Production)
```sql
CREATE TABLE planned_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  item_type TEXT NOT NULL,            -- session|feature|bug|enhancement
  priority TEXT,                      -- high|medium|low
  estimated_hours REAL,
  status TEXT NOT NULL,               -- planned|in_progress|completed|cancelled
  issue_number INTEGER,               -- GitHub issue # (if created)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Proposed: generated_prompts (Future)
```sql
CREATE TABLE generated_prompts (
  prompt_id TEXT PRIMARY KEY,         -- UUID
  feature_id INTEGER NOT NULL REFERENCES planned_features(id),
  phase_number INTEGER NOT NULL,
  total_phases INTEGER NOT NULL,
  filename TEXT NOT NULL,
  content TEXT NOT NULL,              -- Full prompt markdown
  coordination_doc TEXT,              -- Path to coordination doc
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  used_at TIMESTAMP,                  -- When prompt was opened in Claude Code
  effectiveness_rating INTEGER,       -- 1-5 stars (user feedback)
  notes TEXT                          -- User notes on prompt usage
);

CREATE INDEX idx_prompts_feature ON generated_prompts(feature_id);
CREATE INDEX idx_prompts_generated ON generated_prompts(generated_at);
```

---

**End of Analysis**
