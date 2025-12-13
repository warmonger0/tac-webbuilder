# Unified Prompt Generation Analysis
**Date**: 2025-12-13
**Status**: Architecture Analysis Complete
**Context**: Integration of DESIGN_UNIFIED_PROMPT_GENERATION.md with tac-webbuilder request pipeline

---

## Executive Summary

The unified prompt generation system and ZTE-hopper serve **different, complementary purposes** and should remain **architecturally separate** in the current design, but **can be unified** for a fully automated pipeline.

### Key Insight: Two Workflows, One Vision

**Current State:**
- **ZTE-hopper**: Fully automated "zero-touch" execution (upload → production)
- **Prompt Generation**: Manual development workflow (analyze → generate → human executes)

**Future State (Proposed):**
- **Unified Pipeline**: Panel 1 → Auto-analyze phases → Auto-generate prompts → Auto-orchestrate → ADW execution → Completion

---

## 1. Gap Analysis

### What's Already Implemented ✅

| Component | Status | File Location |
|-----------|--------|---------------|
| **Panel 1 Request Form** | ✅ Production | `app/client/src/components/RequestFormCore.tsx` |
| **ZTE-hopper Queue** | ✅ Production | `app/server/services/phase_coordination/phase_coordinator.py` |
| **ADW 10-Phase Workflows** | ✅ Production | `adws/adw_sdlc_complete_iso.py` |
| **Phase Queue Database** | ✅ Production | `phase_queue` table with dependency tracking |
| **Frontend Phase Parser** | ✅ Production | `app/client/src/utils/phaseParser.ts` |
| **Backend Phase Analyzer** | ✅ Exists | `scripts/plan_phases.py` (analysis only, no prompts) |
| **Single Prompt Generator** | ✅ Exists | `scripts/generate_prompt.py` (no phase support) |
| **Planned Features DB** | ✅ Production | `planned_features` table + service layer |
| **Codebase Analyzer** | ✅ Production | `app/server/utils/codebase_analyzer/` |

### What's Missing ❌

| Component | Status | Impact |
|-----------|--------|--------|
| **Multi-phase prompt generation** | ❌ Not implemented | Manual work for each phase |
| **Orchestrator script** | ❌ Not implemented | No automation of 3-step workflow |
| **`/genprompts` command** | ❌ Not implemented | No unified interface |
| **Panel 1 → Prompt generation link** | ❌ Not implemented | Disconnected workflows |
| **Auto phase detection on submit** | ❌ Not implemented | Manual determination required |
| **Prompt storage in DB** | ❌ Not implemented | File-based only, no tracking |
| **Phase → Prompt → ADW automation** | ❌ Not implemented | Manual orchestration |

### What Needs Modification 🔧

| Component | Current State | Needs Enhancement |
|-----------|---------------|-------------------|
| `plan_phases.py` | Generates coordination doc only | Add `--output-json` for prompt generation |
| `generate_prompt.py` | Single prompts only | Add phase context support (`--phase N --total-phases M`) |
| Template system | No phase awareness | Add conditional phase sections |
| Panel 1 workflow | Direct to GitHub | Add optional phase analysis step |
| ZTE-hopper integration | Separate from prompts | Could trigger prompt generation JIT |

---

## 2. Integration Architecture

### Current Production Flow (Panel 1 → ZTE → ADW)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CURRENT STATE (PRODUCTION)                       │
└─────────────────────────────────────────────────────────────────────┘

Panel 1 Request Form
  │
  ├─ User enters NL description
  ├─ Optional: Upload .md file
  └─ Click "Generate Issue"
       ↓
POST /api/request
  │
  ├─ nl_processor.py analyzes intent (feature/bug/chore)
  ├─ project_detector.py analyzes complexity
  ├─ template_router.py suggests workflow
  └─ Returns request_id
       ↓
GET /api/preview/{request_id}
  │
  └─ Shows GitHub issue preview
       ↓
User reviews and confirms
       ↓
POST /api/confirm/{request_id}
  │
  ├─ If multi-phase .md detected (phaseParser.ts):
  │   ├─ Create parent GitHub issue
  │   ├─ Create Phase 1 GitHub issue
  │   └─ Enqueue Phases 2-N to phase_queue (status: "queued")
  │
  └─ If single issue:
      └─ Create GitHub issue directly
           ↓

┌─────────────────────────────────────────────────────────────────────┐
│              ZTE-HOPPER QUEUE SYSTEM (PRODUCTION)                   │
└─────────────────────────────────────────────────────────────────────┘

PhaseCoordinator (background poller, 10s intervals)
  │
  ├─ Check for completed workflows in workflow_history
  ├─ Mark completed phases in phase_queue
  ├─ Trigger next phase dependencies
  │
  └─ For phases with status="ready" and no issue_number:
      ├─ Create GitHub issue (JIT)
      ├─ Update phase_queue with issue_number
      └─ Auto-launch ADW workflow:
           ↓
           subprocess.Popen([
               "uv", "run",
               "adws/adw_sdlc_complete_iso.py",
               str(issue_number),
               adw_id
           ])
           ↓

┌─────────────────────────────────────────────────────────────────────┐
│              ADW WORKFLOWS (PRODUCTION)                             │
└─────────────────────────────────────────────────────────────────────┘

ADW 10-Phase SDLC (adw_sdlc_complete_iso.py)
  │
  ├─ Phase 1: Plan → Creates implementation plan
  ├─ Phase 2: Validate → Baseline error detection
  ├─ Phase 3: Build → Implements solution
  ├─ Phase 4: Lint → Code quality checks
  ├─ Phase 5: Test → Runs tests
  ├─ Phase 6: Review → Validates implementation
  ├─ Phase 7: Document → Generates docs
  ├─ Phase 8: Ship → Auto-approves & merges PR ⚠️
  ├─ Phase 9: Cleanup → Removes worktree
  └─ Completion: POST /api/issue/{N}/complete
       ↓
       Updates phase_queue → Triggers next phase
```

### Proposed Unified Flow (Panel 1 → Auto-Analysis → Prompts → ZTE → ADW)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROPOSED UNIFIED FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

Panel 1 Request Form
  │
  ├─ User enters NL description OR pastes issue #68 text
  ├─ Optional: Upload .md file
  └─ Click "Generate Issue"
       ↓

[NEW] POST /api/request with auto_analyze=true
  │
  ├─ Step 1: NL Processing (existing)
  │   ├─ Analyze intent (feature/bug/chore)
  │   ├─ Extract requirements
  │   └─ Detect complexity
  │
  ├─ Step 2: [NEW] Automatic Phase Analysis
  │   ├─ Call plan_phases.py logic
  │   ├─ Analyze estimated hours
  │   ├─ Identify cross-cutting concerns (DB + Backend + Frontend)
  │   ├─ Determine optimal phase count (1-5 phases)
  │   └─ Create dependency graph
  │
  ├─ Step 3: [NEW] Store in planned_features
  │   ├─ Create planned_features entry with phase breakdown
  │   ├─ Store phase metadata
  │   └─ Return feature_id
  │
  └─ Step 4: [NEW] Generate Prompts for Each Phase
      ├─ For each phase (1 to N):
      │   ├─ Call generate_prompt.py with phase context
      │   ├─ Analyze codebase for relevant files
      │   ├─ Generate phase-specific prompt
      │   └─ Store in generated_prompts table
      │
      └─ Return: feature_id, phase_count, coordination_plan
           ↓

GET /api/preview/{request_id}
  │
  └─ [ENHANCED] Shows:
      ├─ GitHub issue preview
      ├─ Phase breakdown (if multi-phase)
      ├─ Execution plan (sequential/parallel)
      ├─ Generated prompts (downloadable)
      └─ Estimated time per phase
           ↓

User reviews and confirms
  │
  ├─ Option A: "Execute Manually" → Download prompts, run in separate chats
  └─ Option B: "Auto-Execute" → Trigger ZTE-hopper
       ↓

POST /api/confirm/{request_id} with auto_execute=true
  │
  ├─ Create parent GitHub issue
  ├─ Create Phase 1 GitHub issue with generated prompt in body
  ├─ Enqueue Phases 2-N to phase_queue:
  │   ├─ status: "queued" (depends on Phase 1)
  │   ├─ phase_data includes generated prompt
  │   └─ workflow_type: "adw_sdlc_complete_iso"
  │
  └─ Phase 1 auto-launches via PhaseCoordinator
       ↓

[EXISTING] ZTE-Hopper Queue System
  │
  └─ PhaseCoordinator polls and orchestrates
      ├─ Phase 1 executes → Completes
      ├─ Phase 2 becomes ready → Auto-creates issue with prompt → Executes
      ├─ Phase 3 (if parallel to Phase 2) → Executes concurrently
      └─ Continues until all phases complete
           ↓

[EXISTING] ADW Workflows execute each phase
  │
  └─ Uses generated prompt as context for Plan phase
      └─ Completion updates planned_features status
```

---

## 3. Two Separate Phase Detection Systems (Both Valid)

### System A: Frontend Phase Parser (`phaseParser.ts`)

**Purpose:** Parse user-uploaded multi-phase documents

**How it works:**
- Regex detection: `/^(#{1,6})\s*(?:phase\s+)?(\d+|one|two|three|...)[:\s-]*(.*)/i`
- Detects phase headers in markdown (e.g., "# Phase 1: Setup")
- Used during Panel 1 file upload

**User Flow:**
```
Panel 1 → User uploads phases.md → phaseParser detects 3 phases
  → Creates parent issue + 3 child issues
  → Enqueues to ZTE-hopper
```

**Strengths:**
- Respects user's explicit phase structure
- Immediate detection during upload
- No analysis delay

**Weaknesses:**
- Requires user to pre-structure phases
- No optimization of phase breakdown
- No codebase-aware analysis

### System B: Backend Phase Analyzer (`plan_phases.py`)

**Purpose:** Analyze complexity and recommend optimal phase breakdown

**How it works:**
- Analyzes estimated hours: `≤2h → 1 phase, 6-12h → 3 phases, 18h+ → 5 phases`
- Identifies cross-cutting concerns (DB changes + API changes + UI changes)
- Analyzes file modifications and conflicts
- Creates dependency graph

**User Flow:**
```
planned_features DB → Run plan_phases.py → Analyzes complexity
  → Recommends 3 phases: "Data + Backend + Frontend"
  → Generates coordination document
```

**Strengths:**
- Intelligent complexity analysis
- Codebase-aware recommendations
- Optimizes phase granularity

**Weaknesses:**
- Requires DB entry first
- Asynchronous (not during submission)
- May override user intent

### Recommendation: Unified Hybrid Approach

```
Panel 1 Submission:
  │
  ├─ If user uploaded .md with phases:
  │   └─ Use phaseParser.ts (respect user structure)
  │
  └─ If NL description only:
      └─ Use plan_phases.py (auto-analyze complexity)
           ↓
           Present recommendation to user:
           "Based on analysis, we recommend 3 phases:
            Phase 1: Database schema (2h)
            Phase 2: Backend services (3h)
            Phase 3: Frontend UI (3h)

            [Use Recommendation] [Edit Phases] [Single Phase]"
```

---

## 4. Critical Design Decisions

### Decision 1: Where Should Prompt Generation Occur?

**Analysis of 4 Options:**

#### Option A: During Panel 1 Submission
```
Panel 1 → Generate Issue (button)
  ↓
  [NEW] Auto-analyze phases
  [NEW] Generate prompts
  ↓
  Show preview with prompts
  ↓
  User confirms → Create issues + enqueue
```

**Pros:**
- Seamless UX (one click)
- Prompts available immediately
- User can review before confirming

**Cons:**
- Adds latency to submission (5-10s for analysis + generation)
- Couples workflows (analysis failure blocks submission)
- Complexity in error handling

**Verdict:** ✅ **Best for full automation** - Recommended for unified pipeline

---

#### Option B: PhaseCoordinator Just-In-Time
```
PhaseCoordinator polls
  ↓
  Phase 2 becomes ready
  ↓
  [NEW] Generate prompt for Phase 2
  [NEW] Create GitHub issue with prompt
  ↓
  Launch ADW workflow
```

**Pros:**
- Lazy evaluation (only when needed)
- No upfront cost
- Can adapt based on Phase 1 results

**Cons:**
- Too late for manual workflows
- Adds complexity to PhaseCoordinator
- May delay phase execution

**Verdict:** ⚠️ **Useful for dynamic prompts** - Consider as enhancement

---

#### Option C: Pre-ADW Hook (Before Workflow Starts)
```
PhaseCoordinator launches ADW
  ↓
  [NEW] adw_analyze_iso.py (Phase 0)
  ↓
  Analyzes issue, generates prompts
  ↓
  Saves prompts to state
  ↓
  adw_plan_iso.py reads prompt from state
```

**Pros:**
- ADW-integrated (clean separation)
- Prompts always fresh
- Can use worktree context

**Cons:**
- Breaks "zero-touch" (adds manual phase)
- Increases ADW execution time
- Redundant if prompts pre-generated

**Verdict:** ❌ **Not recommended** - Violates ZTE philosophy

---

#### Option D: Separate `/genprompts` Command (As Designed)
```
Manual workflow:
  /genprompts 49 52 104
  ↓
  plan_phases.py analyzes
  ↓
  generate_prompt.py creates prompts
  ↓
  coordination_doc.py shows execution plan
  ↓
  Human executes prompts in separate chats
```

**Pros:**
- Clean separation of concerns
- No coupling with ZTE
- As designed in DESIGN_UNIFIED_PROMPT_GENERATION.md

**Cons:**
- Fully manual (no automation)
- Disconnected from Panel 1
- Requires DB entries

**Verdict:** ✅ **Good for MVP** - Low risk, implements design as-is

---

### Decision Matrix: Which Option When?

| Use Case | Recommended Option | Rationale |
|----------|-------------------|-----------|
| **Full automation pipeline** | Option A | Seamless UX, one-click automation |
| **MVP implementation** | Option D | Low risk, as designed |
| **Manual development** | Option D | Separate tool for experimentation |
| **Dynamic phase adaptation** | Option B | Adjust based on prior results |
| **Learning/training** | Option D | Explicit prompts for review |

---

### Decision 2: Should Prompts Be Stored in Database?

**File System (Current Design):**
```
QUICK_WIN_49_fix_error_handling.md
FEATURE_104_PHASE_1_database.md
FEATURE_104_PHASE_2_backend.md
PHASE_PLAN_20251213_120000.md
```

**Pros:**
- Simple implementation
- Easy to review in IDE
- Version control via git
- Human-readable

**Cons:**
- No tracking/history
- Hard to query
- No relationship to phase_queue
- Cleanup/organization needed

---

**Database Storage (Proposed Enhancement):**

```sql
CREATE TABLE generated_prompts (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER REFERENCES planned_features(id),
    phase_number INTEGER,
    total_phases INTEGER,
    prompt_content TEXT NOT NULL,
    codebase_context JSONB,  -- Files, functions analyzed
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP,
    result_summary TEXT,
    UNIQUE(feature_id, phase_number)
);
```

**Pros:**
- Trackable history
- Queryable ("show all prompts for feature #104")
- Links to planned_features
- Can store execution results
- API-accessible

**Cons:**
- More complex implementation
- Requires migration
- Still need file export for use

---

**Recommendation: Hybrid Approach**

```
Phase 1 (MVP):
  ├─ Generate prompts to files (as designed)
  └─ Simple, no DB changes

Phase 2 (Enhancement):
  ├─ Store prompts in DB
  ├─ Export to files on demand
  └─ Track execution status

Phase 3 (Advanced):
  ├─ Store codebase context
  ├─ Track success/failure
  └─ ML-based prompt optimization
```

---

### Decision 3: Integration with ZTE-Hopper Philosophy

**ZTE-Hopper Core Principles:**
1. **Zero-Touch:** Upload once → Production (no human intervention)
2. **Automated Orchestration:** Sequential/parallel phase execution
3. **Quality Gates:** Lint, test, review must pass
4. **Isolated Execution:** Worktrees prevent conflicts

**How Prompt Generation Fits:**

#### Approach 1: Prompts as ADW Input (Recommended)
```
Phase Analysis → Generate Prompts → Store in phase_queue.phase_data
  ↓
PhaseCoordinator launches ADW with prompt
  ↓
ADW Plan phase uses prompt as guidance
  ↓
Zero-touch continues (no human needed)
```

**Fits ZTE:** ✅ Prompts enhance automation, don't break it

---

#### Approach 2: Prompts as Parallel Workflow (Current Design)
```
ZTE Pipeline: Panel 1 → ZTE → ADW → Production
Prompt Pipeline: planned_features → /genprompts → Manual execution

Completely separate, no interaction
```

**Fits ZTE:** ✅ No conflict, different use cases

---

#### Approach 3: Prompts Require Human Review (Anti-pattern)
```
Phase Analysis → Generate Prompts → Human reviews → Approves → Continue
                                          ↓
                                    Breaks zero-touch ❌
```

**Fits ZTE:** ❌ Violates zero-touch principle

---

**Recommendation:** Use Approach 1 for automation, keep Approach 2 available for manual workflows

---

## 5. Implementation Roadmap

### Phase 1: MVP - Standalone Prompt Generation (3.25h)

**Goal:** Implement DESIGN_UNIFIED_PROMPT_GENERATION.md exactly as designed

**No changes to:**
- Panel 1
- ZTE-hopper
- ADW workflows
- Database schema

**Tasks:**

1. **Enhance `plan_phases.py`** (0.5h)
   ```bash
   # Add --output-json flag
   ./scripts/plan_phases.sh 49 52 104 --output-json > phase_metadata.json
   ```
   - Output JSON with phase metadata
   - Include dependencies, parallel tracks, file conflicts
   - Schema: `{features: [...], summary: {...}, parallel_tracks: [...]}`

2. **Enhance `generate_prompt.py`** (1h)
   ```bash
   # Add phase context support
   ./scripts/gen_prompt.sh 104 --phase 2 --total-phases 3 --depends-on "104:1"
   ```
   - Accept `--phase`, `--total-phases`, `--depends-on` flags
   - Modify template filling to include phase context
   - Generate phase-aware filename: `FEATURE_104_PHASE_2_backend.md`

3. **Create `orchestrate_prompts.sh`** (1h)
   ```bash
   #!/bin/bash
   # 3-step orchestration

   # Step 1: Analyze phases
   METADATA=$(./scripts/plan_phases.sh $@ --output-json)

   # Step 2: Generate prompts for each phase
   python3 -c "
   import json, subprocess
   data = json.loads('$METADATA')
   for feature in data['features']:
       for phase in feature['phases']:
           subprocess.run(['./scripts/gen_prompt.sh',
                          str(feature['issue_id']),
                          '--phase', str(phase['phase_number']),
                          '--total-phases', str(phase['total_phases'])])
   "

   # Step 3: Create coordination document
   ./scripts/create_coordination_doc.sh "$METADATA"
   ```

4. **Create `/genprompts` slash command** (0.25h)
   ```markdown
   # File: .claude/commands/genprompts.md

   Execute unified prompt generation:

   ./scripts/orchestrate_prompts.sh $@

   Generates prompts for phases + coordination doc.
   ```

5. **Testing & Documentation** (0.5h)
   - Test with single issue: `/genprompts 49`
   - Test with multiple: `/genprompts 49 52 104`
   - Test with complex feature: `/genprompts 104`
   - Document usage in README

**Deliverables:**
- ✅ `/genprompts` command working
- ✅ Multi-phase prompt generation
- ✅ Coordination document with execution plan
- ✅ No breaking changes to existing systems

---

### Phase 2: Panel 1 Integration (7h)

**Goal:** Connect Panel 1 request flow to prompt generation system

**Tasks:**

1. **Link Panel 1 to `planned_features` Database** (2h)
   ```typescript
   // RequestFormCore.tsx enhancement

   async function handleSubmit() {
     // Existing: Create GitHub issue preview
     const preview = await createRequest(nlInput, projectPath);

     // NEW: Also create planned_features entry
     const feature = await api.post('/api/v1/planned-features', {
       title: preview.title,
       description: preview.body,
       item_type: classifyType(preview),  // feature/bug/enhancement
       estimated_hours: estimateHours(preview),
       status: 'planned'
     });

     // Store feature_id for later use
     setFeatureId(feature.id);
   }
   ```

2. **Add Automatic Phase Analysis** (2h)
   ```python
   # app/server/routes/github_routes.py

   @router.post("/request")
   async def create_request(request: RequestData):
       # Existing: NL processing
       analysis = await nl_processor.analyze(request.nl_input)

       # NEW: Phase analysis
       if analysis.estimated_hours > 2.0:
           phase_analyzer = PhaseAnalyzer()
           phase_breakdown = phase_analyzer.analyze_complexity(
               estimated_hours=analysis.estimated_hours,
               description=request.nl_input,
               detected_concerns=analysis.concerns
           )

           # Generate prompts for each phase
           prompts = []
           for phase in phase_breakdown.phases:
               prompt = generate_phase_prompt(
                   phase_number=phase.number,
                   total_phases=len(phase_breakdown.phases),
                   phase_context=phase
               )
               prompts.append(prompt)

           return {
               'request_id': request_id,
               'multi_phase': True,
               'phase_count': len(phase_breakdown.phases),
               'prompts': prompts,
               'execution_plan': phase_breakdown.execution_plan
           }
       else:
           return {'request_id': request_id, 'multi_phase': False}
   ```

3. **Enhance Preview UI** (2h)
   ```tsx
   // RequestFormPreview.tsx

   {preview.multi_phase && (
     <div className="phase-breakdown">
       <h3>Phase Breakdown ({preview.phase_count} phases)</h3>

       <ExecutionPlan plan={preview.execution_plan} />

       <PromptList prompts={preview.prompts} />

       <ButtonGroup>
         <Button onClick={downloadPrompts}>
           Download Prompts
         </Button>
         <Button onClick={autoExecute} variant="primary">
           Auto-Execute with ZTE
         </Button>
       </ButtonGroup>
     </div>
   )}
   ```

4. **Add "Generate Prompts" Button to Plans Panel** (1h)
   ```tsx
   // PlansPanel.tsx

   <Button onClick={() => generatePrompts(feature.id)}>
     Generate Implementation Prompts
   </Button>

   async function generatePrompts(featureId) {
     const result = await api.post(`/api/v1/prompts/generate/${featureId}`);

     // Show prompts in modal or download
     setPrompts(result.prompts);
     setShowPromptsModal(true);
   }
   ```

**Deliverables:**
- ✅ Panel 1 creates planned_features entries
- ✅ Automatic phase analysis on submission
- ✅ Generated prompts shown in preview
- ✅ User can download or auto-execute
- ✅ Plans Panel can generate prompts on-demand

---

### Phase 3: Full ZTE Integration (12h)

**Goal:** Complete automation pipeline with intelligent orchestration

**Tasks:**

1. **Prompt Storage in Database** (3h)
   - Create `generated_prompts` table
   - Migration script
   - Service layer (PromptService)
   - API endpoints

2. **Auto-Execute with ZTE** (4h)
   - Enhance PhaseCoordinator to read prompts from DB
   - Include prompt in GitHub issue body
   - ADW Plan phase uses prompt as context
   - Track prompt execution success

3. **Bi-Directional Sync** (3h)
   - ADW completion updates planned_features
   - Actual hours vs. estimated
   - Completion notes from ADW
   - Success/failure tracking

4. **Advanced Features** (2h)
   - Parallel execution detection
   - Smart phase merging
   - Template selection based on patterns
   - ML-based time estimation

**Deliverables:**
- ✅ Full automation: Panel 1 → Analysis → Prompts → ZTE → ADW → Production
- ✅ Prompt execution tracking
- ✅ Historical data for optimization
- ✅ Intelligent orchestration

---

## 6. Potential Issues & Risks

### Risk 1: Architectural Conflicts

**Risk:** Mixing manual and automated workflows creates confusion

**Impact:** High - Users don't know which workflow to use

**Mitigation:**
- Clear decision matrix: "When to use ZTE vs. Manual prompts"
- UI indicators: "This feature will run automatically" vs. "Download prompts for manual execution"
- Documentation with flowcharts
- Default to automation, allow override

---

### Risk 2: Performance Bottlenecks

**Risk:** Phase analysis + prompt generation adds 5-10s to submission

**Impact:** Medium - User experience degradation

**Mitigation:**
- Make analysis async: "Analyzing phases..." progress indicator
- Cache analysis results for similar requests
- Optimize CodebaseAnalyzer queries
- Allow user to skip analysis: "Quick submit" option

---

### Risk 3: Prompt Quality Variance

**Risk:** Auto-generated prompts may not be as good as hand-crafted

**Impact:** High - Poor prompts lead to failed ADW executions

**Mitigation:**
- Template library with proven patterns
- User review step before auto-execute
- Feedback loop: Track prompt success rate
- Allow manual prompt editing before execution
- A/B testing: Compare auto vs. manual success rates

---

### Risk 4: Phase Breakdown Disagreements

**Risk:** User wants different phase structure than analyzer recommends

**Impact:** Medium - User friction

**Mitigation:**
- Show recommendation as suggestion, not requirement
- Allow manual phase editing in preview
- "Use my structure" option if user uploads .md
- Learn from user overrides (ML feedback)

---

### Risk 5: ZTE "Runaway" Workflows

**Risk:** Auto-executed workflows fail repeatedly, consuming resources

**Impact:** High - Cost, resource exhaustion

**Mitigation:**
- Circuit breaker: Max 3 retry attempts (already exists in adw_test_iso.py)
- Pause queue on repeated failures
- Alert user after 2nd failure: "Manual review needed"
- Cost limits per feature

---

### Risk 6: Data Consistency Issues

**Risk:** GitHub issues, phase_queue, planned_features, generated_prompts get out of sync

**Impact:** High - Lost work, duplicate issues

**Mitigation:**
- Transactional operations where possible
- Foreign key constraints
- Reconciliation script: `./scripts/sync_data.sh`
- Audit logging for all state changes
- Weekly cleanup job

---

## 7. Recommendations

### Immediate Actions (This Week)

1. ✅ **Document current state** (this file)
2. ✅ **Verify ZTE-hopper status**
   - Test multi-phase workflow end-to-end
   - Confirm PhaseCoordinator is running
   - Check completion webhooks working

3. ⚠️ **Decide on implementation approach:**
   - Option A: MVP only (3.25h, low risk)
   - Option B: Full automation (22h, high value)
   - Option C: Phased rollout (3.25h → 7h → 12h)

4. 📋 **Create test case with issue #68:**
   - Paste into Panel 1
   - Observe current behavior
   - Identify specific gaps
   - Design ideal flow

### Near-Term Enhancements (Next Sprint)

5. **Implement chosen approach** (see above)

6. **Build feedback loop:**
   - Track prompt success rate
   - Store actual hours vs. estimated
   - Identify patterns in successful prompts
   - Use data to improve analyzer

7. **Enhance Plans Panel:**
   - Show phase breakdown for features
   - "Generate Prompts" button
   - Execution status tracking
   - Link to ADW workflows

### Long-Term Vision (Next Quarter)

8. **ML-Based Optimization:**
   - Train model on historical data
   - Predict optimal phase count
   - Recommend templates based on success patterns
   - Auto-detect parallel opportunities

9. **Template Library:**
   - Categorize by pattern (CRUD, API, UI, etc.)
   - Success rate tracking
   - Community-contributed templates
   - A/B testing framework

10. **Observability Dashboard:**
    - Track phase execution times
    - Cost per feature
    - Success/failure rates
    - Bottleneck identification

---

## 8. What NOT to Do (Anti-Patterns)

### ❌ Anti-Pattern 1: Force All Requests Through Prompt Generation

**Why it's bad:**
- Not all requests need phases (simple bugs, quick fixes)
- Adds unnecessary latency
- User friction for simple tasks

**Better approach:**
- Make phase analysis optional
- Auto-trigger only for estimated_hours > 2h
- Allow "Quick submit" bypass

---

### ❌ Anti-Pattern 2: Replace Frontend Parser with Backend Analyzer

**Why it's bad:**
- Frontend parser handles user-explicit phases (respects intent)
- Backend analyzer is for DB-based analysis (different context)
- Both serve valid purposes

**Better approach:**
- Keep both systems
- Use frontend parser for uploaded .md files
- Use backend analyzer for NL-only requests
- Hybrid: Validate user phases with analyzer recommendations

---

### ❌ Anti-Pattern 3: Store Prompts Only in Database

**Why it's bad:**
- Prompts need to be human-readable (review in IDE)
- Version control important (track changes)
- File-based easier for manual workflows

**Better approach:**
- Store in DB + export to files
- DB = source of truth, tracking, history
- Files = working copies for execution

---

### ❌ Anti-Pattern 4: Tightly Couple Prompt Generation to ZTE

**Why it's bad:**
- Prompt generation is useful standalone (manual workflows)
- ZTE failures would block prompt generation
- Violates separation of concerns

**Better approach:**
- Generate prompts regardless of execution method
- Make ZTE integration optional
- Support both manual and automated workflows

---

## 9. Decision Matrices

### When to Use ZTE vs. Manual Prompts

| Criterion | Use ZTE | Use Manual Prompts |
|-----------|---------|-------------------|
| **Task Size** | Well-defined, <8h per phase | Complex, >8h per phase |
| **Risk Level** | Low risk, established patterns | High risk, new patterns |
| **Urgency** | Not urgent, can wait | Urgent, needs human oversight |
| **Complexity** | Standard CRUD, API, UI | Novel architecture, R&D |
| **Learning Goal** | Production delivery | Learning, experimentation |
| **Observability Needs** | Standard metrics sufficient | Need detailed debugging |
| **Cost Sensitivity** | Cost-efficient at scale | One-off, cost less important |
| **Quality Requirements** | Standard quality gates OK | Mission-critical, extra review |
| **Experimentation** | Proven approach | Trying new techniques |
| **Team Familiarity** | Team knows pattern well | New pattern, needs learning |

**Rule of Thumb:**
- **ZTE:** Established patterns, low risk, production delivery
- **Manual Prompts:** New patterns, learning, high-stakes features

---

### Phase Detection Method Selection

| Scenario | Method | Rationale |
|----------|--------|-----------|
| User uploads .md with phases | Frontend parser | Respect user intent |
| User enters NL only, >2h estimated | Backend analyzer | Auto-optimization needed |
| User enters NL, but has specific structure in mind | Hybrid (recommend + allow edit) | Balance automation + control |
| Bug fix, <30min | Skip phase detection | Unnecessary overhead |
| Complex feature, unclear scope | Backend analyzer + review | Need intelligent breakdown |
| User editing existing feature | Use stored phase structure | Consistency |

---

### Storage Location Decision

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Feature metadata | `planned_features` table | Queryable, trackable |
| Phase metadata | `phase_queue` table | Orchestration needs |
| Generated prompts (tracking) | `generated_prompts` table | History, success rate |
| Generated prompts (files) | `.md` files | Human-readable, version control |
| Execution results | `workflow_history` table | ADW integration |
| Codebase analysis cache | Redis/Memory | Performance |

---

## 10. Appendices

### Appendix A: File Path Reference

**Current Production Files:**
```
app/
├── client/src/
│   ├── components/
│   │   ├── RequestFormCore.tsx           # Panel 1 request form
│   │   ├── PlansPanel.tsx                # Panel 5 planned features
│   │   └── ZteHopperQueueCard.tsx        # ZTE queue visualization
│   └── utils/
│       └── phaseParser.ts                # Frontend phase detection
│
└── server/
    ├── routes/
    │   ├── github_routes.py              # /api/request endpoints
    │   ├── planned_features_routes.py    # /api/v1/planned-features
    │   └── issue_completion_routes.py    # /api/issue/{N}/complete
    ├── services/
    │   ├── planned_features_service.py   # PlannedFeaturesService
    │   ├── phase_queue_service.py        # Phase queue management
    │   └── phase_coordination/
    │       └── phase_coordinator.py      # PhaseCoordinator poller
    └── utils/
        └── codebase_analyzer/
            └── analyzer.py               # CodebaseAnalyzer

adws/
├── adw_sdlc_complete_iso.py         # Full 10-phase ZTE workflow
├── adw_plan_iso.py                      # Plan phase
├── adw_build_iso.py                     # Build phase
└── adw_modules/
    ├── state.py                         # ADW state management
    └── worktree_ops.py                  # Worktree creation/cleanup

scripts/
├── generate_prompt.py                   # Single prompt generator
├── gen_prompt.sh                        # Shell wrapper
├── plan_phases.py                       # Phase analyzer (NEW)
└── plan_phases.sh                       # Shell wrapper (NEW)

.claude/
├── commands/
│   └── planphases.md                    # /planphases slash command
└── templates/
    └── IMPLEMENTATION_PROMPT_TEMPLATE.md # Prompt template

docs/
└── analysis/
    └── DESIGN_UNIFIED_PROMPT_GENERATION.md # Original design doc
```

**Proposed New Files:**
```
scripts/
├── orchestrate_prompts.sh               # [NEW] 3-step orchestrator
└── create_coordination_doc.sh           # [NEW] Coordination doc generator

.claude/commands/
└── genprompts.md                        # [NEW] /genprompts slash command

app/server/
├── routes/
│   └── prompt_routes.py                 # [NEW] /api/v1/prompts endpoints
└── services/
    └── prompt_service.py                # [NEW] PromptService

Generated outputs/
├── QUICK_WIN_49_fix_error.md           # Single phase prompt
├── FEATURE_104_PHASE_1_database.md     # Multi-phase prompt 1
├── FEATURE_104_PHASE_2_backend.md      # Multi-phase prompt 2
├── FEATURE_104_PHASE_3_frontend.md     # Multi-phase prompt 3
└── PHASE_PLAN_20251213_120000.md       # Coordination document
```

---

### Appendix B: Database Schema Reference

**Production Tables:**

```sql
-- Feature planning and tracking
CREATE TABLE planned_features (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planned',
    priority VARCHAR(20),
    estimated_hours NUMERIC(5,2),
    actual_hours NUMERIC(5,2),
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER REFERENCES planned_features(id),
    tags JSONB DEFAULT '[]',
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Phase queue for ZTE orchestration
CREATE TABLE phase_queue (
    queue_id TEXT PRIMARY KEY,
    parent_issue INTEGER NOT NULL,
    phase_number INTEGER NOT NULL,
    issue_number INTEGER,
    status TEXT NOT NULL,
    depends_on_phase INTEGER,
    phase_data TEXT,
    priority INTEGER DEFAULT 50,
    queue_position INTEGER,
    adw_id TEXT,
    ready_timestamp TEXT,
    started_timestamp TEXT,
    created_at TEXT,
    updated_at TEXT,
    error_message TEXT
);

-- ADW workflow execution history
CREATE TABLE workflow_history (
    id SERIAL PRIMARY KEY,
    adw_id TEXT NOT NULL,
    issue_number INTEGER,
    workflow_type TEXT,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);
```

**Proposed New Tables:**

```sql
-- Generated prompts tracking
CREATE TABLE generated_prompts (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER REFERENCES planned_features(id) ON DELETE CASCADE,
    phase_number INTEGER NOT NULL,
    total_phases INTEGER NOT NULL,
    prompt_content TEXT NOT NULL,

    -- Codebase context
    backend_files JSONB,           -- [{file, score}, ...]
    frontend_files JSONB,
    related_functions JSONB,
    suggested_locations JSONB,

    -- Metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    template_used VARCHAR(100),

    -- Execution tracking
    executed BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP,
    execution_method VARCHAR(50),  -- 'manual', 'zte', 'adw'
    adw_id TEXT,

    -- Results
    success BOOLEAN,
    actual_hours NUMERIC(5,2),
    result_summary TEXT,

    UNIQUE(feature_id, phase_number)
);

CREATE INDEX idx_generated_prompts_feature ON generated_prompts(feature_id);
CREATE INDEX idx_generated_prompts_executed ON generated_prompts(executed, success);
```

---

## Summary

This analysis document provides a comprehensive overview of:
1. ✅ Current state of all systems (Panel 1, ZTE-hopper, ADW, prompt generation)
2. ✅ Gap analysis (what exists, what's missing, what needs enhancement)
3. ✅ Integration architecture (how systems connect)
4. ✅ Critical design decisions (where, when, how to generate prompts)
5. ✅ Implementation roadmap (3 phases: MVP → Integration → Advanced)
6. ✅ Risk analysis and mitigations
7. ✅ Recommendations and anti-patterns
8. ✅ Decision matrices for choosing workflows

**Key Takeaway:** The unified prompt generation system can work both as a **standalone tool** (MVP, 3.25h) and as **part of a fully automated pipeline** (Phase 3, 22h total). The architecture supports both use cases without conflicts.

**Next Step:** Trace through issue #68 to identify specific gaps and design the ideal automated flow.
