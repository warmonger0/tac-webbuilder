# Phased Implementation Plan: Multi-Stage Planning with Sub-Agents

**Feature ID:** #130
**Estimated Total Effort:** 8.0 hours
**Phases:** 5
**Token Budget:** ~52,761 tokens (avg per phase)
**Cost Estimate:** $0.42 total (19% reduction vs monolithic)

---

## Executive Summary

This implementation plan introduces a **new Analyze phase** to ADW's workflow, separating component decomposition from plan synthesis. The system will use Claude Code's Task tool to spawn sub-agents for component analysis, DRY checking, and file context calculation - then **enhance** the existing Plan phase to consume this analysis when generating implementation phases.

**Architectural Pattern:**
```
adw_analyze_work_iso.py (NEW - Phase 0: Analyze)
  ↓ Persists: components, DRY findings, context analysis → ADWState

adw_plan_iso.py (ENHANCED - Phase 1: Plan)
  ↓ IF analysis exists: Use 3-constraint framework
  ↓ ELSE: Fall back to time-based heuristics (backward compatible)

adw_analyze_plan_iso.py (NEW - Coupled workflow)
  ↓ Runs analyze → plan sequentially (like adw_plan_build_iso.py)
```

**New ADW Phase Sequence (11 phases):**
0. **Analyze** ← NEW
1. **Plan** ← Enhanced
2. Validate
3. Build
4. Lint
5. Test
6. Review
7. Document
8. Ship
9. Cleanup
10. Verify

**Key Benefits:**
- 19% token reduction (271k → 220k tokens) when using analyze+plan
- Modularity: Can run analysis standalone ("how complex is this?")
- Backward compatible: Plan phase works with OR without prior analysis
- DRY principle enforcement via dedicated sub-agent
- Context-aware phase boundaries (file count + token limits + logical coupling)

---

## Component Architecture

### C1: Component Decomposition Sub-Agent
**Purpose:** Parse GitHub issue into logical components
**Location:** `.claude/subagents/component_analyzer.md`
**Invoked by:** `adw_analyze_work_iso.py` via Task tool
**Reuses:** Sub-agent prompt patterns (100% reuse)
**New Code:** ~80 lines (sub-agent definition)

**Key Functions:**
- Parse issue description and acceptance criteria
- Identify database, API, UI, testing, documentation components
- Detect dependencies between components
- Output structured ComponentAnalysis markdown table

**Output Format:**
```markdown
| Component ID | Type | Description | Dependencies | Files | Hours | Tokens |
|--------------|------|-------------|--------------|-------|-------|--------|
| C1 | database | Add users table | - | 3 | 1.5 | 1500 |
```

---

### C2: DRY Checker Sub-Agent
**Purpose:** Detect code duplication opportunities and reusable patterns
**Location:** `.claude/subagents/dry_checker.md`
**Invoked by:** `adw_analyze_work_iso.py` via Task tool
**Reuses:** codebase-expert sub-agent pattern (100% reuse)
**New Code:** ~80 lines (custom prompt template)

**Key Functions:**
- Search for existing implementations of similar features using Grep/Read
- Identify reusable utility functions, dataclasses, API patterns
- Flag potential duplication before implementation
- Output JSON array of DRYFinding objects

**Output Format:**
```json
[{
  "finding_id": "DRY-001",
  "duplicate_type": "pattern",
  "existing_file": "routes/users.py",
  "existing_lines": "45-67",
  "reuse_recommendation": "Reuse pagination pattern",
  "tokens_saved_estimate": 300
}]
```

---

### C3: Context Calculator Sub-Agent
**Purpose:** Calculate file context and token budgets per component
**Location:** `.claude/subagents/context_calculator.md`
**Invoked by:** `adw_analyze_work_iso.py` via Task tool
**Reuses:** `complexity_analyzer.py` patterns (80% reuse)
**New Code:** ~80 lines (sub-agent definition)

**Key Functions:**
- Use Glob/Grep to identify relevant files per component
- Calculate line counts and token estimates (1 line ≈ 10 tokens)
- Determine file dependencies and imports
- Output ContextAnalysis markdown table

**Output Format:**
```markdown
| Component | Files to Modify | Files for Reference | Total Lines | Tokens | Phase |
|-----------|-----------------|---------------------|-------------|--------|-------|
| C1 | users.py, schema.sql | models.py | 450 | 4500 | 1 |
```

---

### C4: Analyze Orchestrator
**Purpose:** Coordinate sub-agent spawning and result aggregation
**Location:** `adws/adw_analyze_work_iso.py`
**Type:** NEW discrete ADW phase (Phase 0)
**Reuses:** `adw_plan_iso.py` structure (70% reuse)
**New Code:** ~300 lines (orchestration logic)

**Key Functions:**
- Create worktree for analysis
- Spawn 3 sub-agents via Task tool in sequence:
  1. component_analyzer
  2. dry_checker
  3. context_calculator
- Parse sub-agent results from markdown/JSON responses
- Aggregate and persist to ADWState
- Can be run standalone or as part of coupled workflow

**CLI Usage:**
```bash
uv run adw_analyze_work_iso.py <issue-number>
# Returns ADW ID with analysis persisted to state
```

---

### C5: Enhanced Plan Phase
**Purpose:** Generate implementation phases using analysis or fallback to heuristics
**Location:** `adws/adw_plan_iso.py` (MODIFIED, not new)
**Type:** ENHANCED existing phase
**Reuses:** Existing plan logic (90% reuse)
**New Code:** ~100 lines (conditional logic for consuming analysis)

**Key Functions:**
- Check if analysis exists in ADWState (`multistage_components` field)
- **IF analysis exists:**
  - Apply three-constraint decision framework:
    1. Token budget (100k max per phase)
    2. File count (15-20 files max per phase)
    3. Logical coupling (keep dependent components together)
  - Generate context-aware phase boundaries
- **ELSE (backward compatible):**
  - Fall back to time-based heuristics (current behavior)
  - Use `scripts/plan_phases.py` logic
- Generate markdown implementation plan

**CLI Usage:**
```bash
# With prior analysis (uses 3-constraint framework)
uv run adw_plan_iso.py <issue-number> <adw-id>

# Without analysis (falls back to time-based heuristics)
uv run adw_plan_iso.py <issue-number>
```

---

### C6: Coupled Workflow Script
**Purpose:** Run analyze → plan sequentially in one command
**Location:** `adws/adw_analyze_plan_iso.py`
**Type:** NEW coupled workflow
**Reuses:** `adw_plan_build_iso.py` pattern (100% reuse)
**New Code:** ~100 lines (sequential orchestration)

**Key Functions:**
- Create worktree (if not exists)
- Run analyze phase → get ADW ID
- Run plan phase with ADW ID
- Return combined output

**CLI Usage:**
```bash
uv run adw_analyze_plan_iso.py <issue-number>
# Equivalent to: analyze → plan
```

---

### C7: Data Types & State Extensions
**Purpose:** Support multi-stage analysis results in ADWState
**Location:** `adw_modules/data_types.py`, `adw_modules/state.py`
**Reuses:** Existing dataclass patterns (95% reuse)
**New Code:** ~70 lines (3 dataclasses + state fields)

**New Dataclasses:**
```python
@dataclass
class ComponentAnalysis:
    component_id: str
    component_type: Literal["database", "api", "ui", "test", "docs"]
    description: str
    dependencies: List[str]
    estimated_hours: float
    file_count: int
    token_estimate: int

@dataclass
class DRYFinding:
    finding_id: str
    duplicate_type: Literal["exact", "similar", "pattern"]
    existing_file: str
    existing_lines: str
    reuse_recommendation: str
    tokens_saved_estimate: int

@dataclass
class ContextAnalysis:
    component_id: str
    files_to_modify: List[str]
    files_for_reference: List[str]
    total_lines: int
    total_tokens: int
    phase_recommendation: int
```

**State Extensions:**
```python
# In ADWStateData
multistage_components: Optional[List[Dict[str, Any]]] = None
dry_findings: Optional[List[Dict[str, Any]]] = None
context_analysis: Optional[Dict[str, Any]] = None
planning_approach: Optional[Literal["monolithic", "multistage"]] = "monolithic"
```

---

### C8: Parsing & Workflow Helpers
**Purpose:** Parse sub-agent responses and support orchestration
**Location:** `adw_modules/workflow_ops.py`
**Reuses:** Existing parsing patterns (80% reuse)
**New Code:** ~50 lines (markdown/JSON parsers)

**New Functions:**
```python
def parse_component_analysis(response: str) -> List[ComponentAnalysis]:
    """Extract markdown table and convert to ComponentAnalysis objects"""

def parse_dry_findings(response: str) -> List[DRYFinding]:
    """Extract JSON array and convert to DRYFinding objects"""

def parse_context_analysis(response: str) -> Dict[str, ContextAnalysis]:
    """Extract markdown table and convert to ContextAnalysis map"""

def extract_markdown_table(text: str, table_name: str) -> List[Dict[str, str]]:
    """Generic markdown table extractor"""
```

---

### C9: Testing Infrastructure
**Purpose:** Validate analyze phase and enhanced plan phase
**Location:** `adws/tests/test_multi_stage_planning.py`
**Reuses:** `test_sdlc_complete.py` patterns (80% reuse)
**New Code:** ~250 lines (test cases)

**Test Coverage:**
- Analyze phase standalone execution
- Plan phase with analysis (3-constraint framework)
- Plan phase without analysis (backward compatible fallback)
- Coupled workflow (analyze → plan)
- Sub-agent response parsing
- State persistence

---

### C10: Observability & Integration
**Purpose:** Track sub-agent spawns and integrate with complete workflows
**Location:** `adw_modules/tool_call_tracker.py`, `adw_sdlc_complete_iso.py`
**Reuses:** Existing patterns (95% reuse)
**New Code:** ~40 lines (tracking + integration)

**Tool Call Tracking:**
```python
def track_subagent_spawn(
    self,
    subagent_type: str,
    prompt_preview: str,
    duration_ms: int,
    success: bool
):
    self.tool_calls.append({
        "tool_name": "Task",
        "subagent_type": subagent_type,
        "prompt_preview": prompt_preview[:100],
        "duration_ms": duration_ms,
        "success": success,
        "timestamp": datetime.now().isoformat()
    })
```

**Complete SDLC Integration:**
```python
# In adw_sdlc_complete_iso.py
parser.add_argument("--skip-analysis", action="store_true",
                    help="Skip analyze phase, use time-based planning")

# Workflow sequence:
if not args.skip_analysis:
    run_phase("analyze", "adw_analyze_work_iso.py", issue_number)
run_phase("plan", "adw_plan_iso.py", issue_number, adw_id)
run_phase("validate", "adw_validate_iso.py", issue_number, adw_id)
# ... rest of phases
```

---

## Dependency Analysis

### Phase Dependencies

```
Phase 1: Data Types & State Extensions
  ↓ (provides dataclasses)
Phase 2: Sub-Agent Definitions
  ↓ (provides sub-agent prompts)
Phase 3: Analyze Phase & Enhanced Plan
  ↓ (provides adw_analyze_work_iso.py, enhanced adw_plan_iso.py)
Phase 4: Integration & Observability
  ↓ (wires into complete workflows)
Phase 5: Testing & Documentation
```

**Parallelization:** None possible - strictly sequential dependency chain
**Critical Path:** All phases are on critical path (no parallel work)

### Dependency Rationale

| Phase | Depends On | Why | Can Parallelize? |
|-------|------------|-----|------------------|
| Phase 1 | None | Foundational data types | N/A (first phase) |
| Phase 2 | Phase 1 | Sub-agent prompts reference ComponentAnalysis, DRYFinding, ContextAnalysis dataclasses in output format specs | ❌ No |
| Phase 3 | Phase 1, 2 | Analyze script needs dataclasses (Phase 1) and sub-agent definitions (Phase 2) | ❌ No |
| Phase 4 | Phase 3 | Integration needs adw_analyze_work_iso.py and enhanced adw_plan_iso.py to wire up | ❌ No |
| Phase 5 | Phase 1-4 | Tests validate all components implemented in previous phases | ❌ No |

---

## Copy-Paste Ready Phase Prompts

### Phase 1 Prompt (Data Types & State Extensions)

**Prerequisites:** None
**Estimated Time:** 0.5h
**Files Modified:** 2

```
Implement Phase 1 of the Multi-Stage Planning feature (#130): Data Types & State Extensions

Tasks:
1. Add three new dataclasses to adw_modules/data_types.py:
   - ComponentAnalysis (component_id, component_type, description, dependencies, estimated_hours, file_count, token_estimate)
   - DRYFinding (finding_id, duplicate_type, existing_file, existing_lines, reuse_recommendation, tokens_saved_estimate)
   - ContextAnalysis (component_id, files_to_modify, files_for_reference, total_lines, total_tokens, phase_recommendation)

2. Extend ADWStateData in adw_modules/state.py with 4 new optional fields:
   - multistage_components: Optional[List[Dict[str, Any]]] = None
   - dry_findings: Optional[List[Dict[str, Any]]] = None
   - context_analysis: Optional[Dict[str, Any]] = None
   - planning_approach: Optional[Literal["monolithic", "multistage"]] = "monolithic"

3. Write unit tests for dataclass validation in adws/tests/test_data_types.py

Reference implementation plan: docs/architecture/IMPLEMENTATION_PLAN_MULTISTAGE_PLANNING.md (lines 330-353)

Success criteria:
- All dataclasses have proper type hints and validation
- State extensions maintain backward compatibility (all fields Optional)
- Unit tests pass for serialization/deserialization
```

---

### Phase 2 Prompt (Sub-Agent Definitions)

**Prerequisites:** Phase 1 completed
**Estimated Time:** 1.0h
**Files Created:** 3

```
Implement Phase 2 of the Multi-Stage Planning feature (#130): Sub-Agent Definitions

Tasks:
1. Create .claude/subagents/component_analyzer.md:
   - Prompt instructions for parsing GitHub issue into logical components
   - Output format: Markdown table with columns: Component ID, Type, Description, Dependencies, Files, Hours, Tokens
   - Include examples of good component decomposition
   - Handle edge cases (single-component issues, unclear requirements)

2. Create .claude/subagents/dry_checker.md:
   - Prompt instructions for searching existing code for reusable patterns
   - Search strategies: Grep for keywords, Glob for file patterns
   - Output format: JSON array of DRYFinding objects
   - Include examples of patterns to detect (pagination, CRUD, auth)

3. Create .claude/subagents/context_calculator.md:
   - Prompt instructions for calculating file context and token budgets
   - Token estimation formula: 1 line ≈ 10 tokens, add 20% safety margin
   - Output format: Markdown table with columns: Component, Files to Modify, Files for Reference, Total Lines, Tokens, Phase
   - Phase boundary recommendations based on 3-constraint framework

Reference implementation plan: docs/architecture/IMPLEMENTATION_PLAN_MULTISTAGE_PLANNING.md (lines 356-385)

Success criteria:
- Sub-agent prompts produce consistent, parseable output
- Manual validation with sample issues shows accurate component identification
- Token estimates within 10% of actual
```

---

### Phase 3 Prompt (Analyze Phase & Enhanced Plan)

**Prerequisites:** Phase 1 and Phase 2 completed
**Estimated Time:** 3.0h
**Files Created:** 2
**Files Modified:** 2

```
Implement Phase 3 of the Multi-Stage Planning feature (#130): Analyze Phase & Enhanced Plan

Tasks:

3A. Create adws/adw_analyze_work_iso.py (~300 lines):
   - Clone structure from adw_plan_iso.py (setup, worktree creation, state init)
   - Implement 3-stage sub-agent orchestration:
     * Stage 1: Spawn component_analyzer sub-agent (Task tool, subagent_type="Explore")
     * Stage 2: Spawn dry_checker sub-agent (Task tool, subagent_type="codebase-expert")
     * Stage 3: Spawn context_calculator sub-agent (Task tool, subagent_type="Explore")
   - Parse sub-agent results using workflow_ops helpers
   - Persist results to ADWState (multistage_components, dry_findings, context_analysis, planning_approach="multistage")
   - CLI: uv run adw_analyze_work_iso.py <issue-number>

3B. Enhance adws/adw_plan_iso.py (+100 lines):
   - Add conditional logic: if state.data.planning_approach == "multistage", use 3-constraint framework
   - Implement generate_phases_from_analysis() function:
     * Apply token budget constraint (max 100k per phase)
     * Apply file count constraint (max 15-20 files per phase)
     * Apply logical coupling constraint (keep dependent components together)
   - Fallback to time-based heuristics if no analysis present (backward compatible)

3C. Add parsing helpers to adw_modules/workflow_ops.py (+50 lines):
   - parse_component_analysis(response: str) -> List[ComponentAnalysis]
   - parse_dry_findings(response: str) -> List[DRYFinding]
   - parse_context_analysis(response: str) -> Dict[str, ContextAnalysis]
   - extract_markdown_table(text: str, table_name: str) -> List[Dict[str, str]]

3D. Create adws/adw_analyze_plan_iso.py (~100 lines):
   - Clone structure from adw_plan_build_iso.py
   - Sequential execution: run analyze phase → extract ADW ID → run plan phase with ADW ID

Reference implementation plan: docs/architecture/IMPLEMENTATION_PLAN_MULTISTAGE_PLANNING.md (lines 388-486)

Success criteria:
- Analyze phase spawns 3 sub-agents successfully
- Sub-agent responses parse correctly
- Enhanced plan phase uses 3-constraint framework when analysis available
- Enhanced plan phase falls back to heuristics when analysis unavailable
- Integration test with issue #130 passes
```

---

### Phase 4 Prompt (Integration & Observability)

**Prerequisites:** Phase 3 completed
**Estimated Time:** 1.0h
**Files Modified:** 4

```
Implement Phase 4 of the Multi-Stage Planning feature (#130): Integration & Observability

Tasks:
1. Update adws/adw_sdlc_complete_iso.py (+20 lines):
   - Add --skip-analysis CLI flag (default: False, meaning analyze runs by default)
   - Add analyze phase as first step in workflow sequence (before plan)
   - Update phase numbering (11 phases total: 0=Analyze, 1=Plan, ..., 10=Verify)

2. Update adws/adw_sdlc_complete_zte_iso.py (+20 lines):
   - Mirror changes from adw_sdlc_complete_iso.py
   - Ensure auto-merge works with new analyze phase

3. Extend adw_modules/tool_call_tracker.py (+15 lines):
   - Add track_subagent_spawn(subagent_type, prompt_preview, duration_ms, success) method
   - Log Task tool invocations with metadata
   - Enable cost attribution per sub-agent type

4. Update .claude/commands/quick_start/adw.md (+10 lines):
   - Document new phase sequence (11 phases total)
   - Add analyze phase description
   - Update phase numbering throughout

Reference implementation plan: docs/architecture/IMPLEMENTATION_PLAN_MULTISTAGE_PLANNING.md (lines 489-521)

Success criteria:
- Complete SDLC workflow includes analyze phase by default
- --skip-analysis flag bypasses analyze phase (backward compatible)
- Tool call tracker logs sub-agent spawns
- Documentation reflects 11-phase sequence
```

---

### Phase 5 Prompt (Testing & Documentation)

**Prerequisites:** Phase 1-4 completed
**Estimated Time:** 2.5h
**Files Created:** 2
**Files Modified:** 2

```
Implement Phase 5 of the Multi-Stage Planning feature (#130): Testing & Documentation

Tasks:
1. Create adws/tests/test_multi_stage_planning.py (~250 lines):
   - test_analyze_phase_creates_worktree()
   - test_analyze_phase_persists_results()
   - test_plan_phase_uses_analysis() - verify 3-constraint framework applied
   - test_plan_phase_fallback_without_analysis() - verify backward compatibility
   - test_coupled_workflow() - verify analyze → plan sequential execution
   - test_component_analysis_parsing()
   - test_dry_finding_detection()
   - test_sdlc_complete_with_analyze()
   - test_sdlc_complete_skip_analysis()

2. Update adws/README.md (+50 lines):
   - Document new analyze phase
   - Add usage examples for standalone, coupled, and complete workflows
   - Document cost savings (19% reduction)
   - Update phase sequence table (11 phases)

3. Update .claude/commands/references/adw_workflows.md (+30 lines):
   - Add analyze phase to workflow selection guide
   - Document when to use analyze vs --skip-analysis
   - Add workflow decision tree

4. Create .claude/commands/references/multi_stage_planning.md (~120 lines):
   - Complete reference for analyze phase
   - Sub-agent descriptions and expected outputs
   - Three-constraint decision framework documentation
   - Troubleshooting guide
   - Cost analysis and token budgets

Reference implementation plan: docs/architecture/IMPLEMENTATION_PLAN_MULTISTAGE_PLANNING.md (lines 524-573)

Success criteria:
- All unit tests pass
- All integration tests pass
- Test coverage ≥ 80% for new code
- Documentation completeness score ≥ 90%
- Manual testing checklist completed
```

---

## Phase-by-Phase Implementation

### Phase 1: Data Types & State Extensions (0.5h, ~70 lines)

**Objective:** Create foundational data structures for multi-stage analysis

**Tasks:**
1. Add `ComponentAnalysis`, `DRYFinding`, `ContextAnalysis` dataclasses to `adw_modules/data_types.py`
   - Include type hints, validation, and serialization methods
   - Follow existing dataclass patterns (`ComplexityAnalysis` as template)

2. Extend `ADWStateData` in `adw_modules/state.py`
   - Add 4 new optional fields for analysis results
   - Maintain backward compatibility (all fields Optional)

3. Write unit tests for dataclass validation
   - Test field constraints (e.g., component_type must be in enum)
   - Test serialization/deserialization to JSON

**Files Modified:** 2
- `adw_modules/data_types.py` (+60 lines)
- `adw_modules/state.py` (+10 lines)

**Token Budget:** ~2,200 tokens
**Testing:** Unit tests in `test_data_types.py`

---

### Phase 2: Sub-Agent Definitions (1.0h, ~240 lines)

**Objective:** Create specialized sub-agent prompt templates

**Tasks:**
1. Create `.claude/subagents/component_analyzer.md`
   - Prompt instructions for parsing GitHub issue
   - Output format specification (markdown table)
   - Examples of good component decomposition
   - Edge case handling (single-component issues, unclear requirements)

2. Create `.claude/subagents/dry_checker.md`
   - Prompt instructions for searching existing code
   - Search strategies (Grep for keywords, Glob for file patterns)
   - Output format specification (JSON array)
   - Examples of reusable patterns to detect

3. Create `.claude/subagents/context_calculator.md`
   - Prompt instructions for calculating file context
   - Token estimation formula (1 line ≈ 10 tokens, add 20% safety margin)
   - Output format specification (markdown table)
   - Phase boundary recommendations

**Files Created:** 3
- `.claude/subagents/component_analyzer.md` (~80 lines)
- `.claude/subagents/dry_checker.md` (~80 lines)
- `.claude/subagents/context_calculator.md` (~80 lines)

**Token Budget:** ~4,800 tokens
**Testing:** Manual validation with sample issues (#130, simple 2h issue, complex 12h issue)

---

### Phase 3: Analyze Phase & Enhanced Plan (3.0h, ~500 lines)

**Objective:** Implement new analyze phase and enhance existing plan phase

**Tasks:**

#### 3A: Create Analyze Orchestrator (~300 lines)
Create `adws/adw_analyze_work_iso.py`:
- Clone structure from `adw_plan_iso.py` (setup, worktree creation, state init)
- Implement 3-stage sub-agent orchestration:
  ```python
  # Stage 1: Component Analysis
  component_response = agent.spawn_subagent(
      subagent_type="Explore",
      prompt=load_template(".claude/subagents/component_analyzer.md", issue_number)
  )
  components = parse_component_analysis(component_response)

  # Stage 2: DRY Analysis
  dry_response = agent.spawn_subagent(
      subagent_type="codebase-expert",
      prompt=load_template(".claude/subagents/dry_checker.md", components)
  )
  dry_findings = parse_dry_findings(dry_response)

  # Stage 3: Context Calculation
  context_response = agent.spawn_subagent(
      subagent_type="Explore",
      prompt=load_template(".claude/subagents/context_calculator.md", components)
  )
  context_analysis = parse_context_analysis(context_response)
  ```
- Persist results to ADWState:
  ```python
  state.data.multistage_components = [c.to_dict() for c in components]
  state.data.dry_findings = [d.to_dict() for d in dry_findings]
  state.data.context_analysis = {k: v.to_dict() for k, v in context_analysis.items()}
  state.data.planning_approach = "multistage"
  state.save()
  ```

#### 3B: Enhance Plan Phase (~100 lines)
Modify `adws/adw_plan_iso.py`:
- Add conditional logic to check for prior analysis:
  ```python
  state = ADWState.load(issue_number, adw_id)

  if state.data.planning_approach == "multistage":
      # Use 3-constraint framework
      components = [ComponentAnalysis.from_dict(c) for c in state.data.multistage_components]
      context = {k: ContextAnalysis.from_dict(v) for k, v in state.data.context_analysis.items()}
      phases = generate_phases_from_analysis(components, context)
  else:
      # Fall back to time-based heuristics (existing logic)
      phases = generate_phases_from_hours(feature.estimated_hours)
  ```
- Implement `generate_phases_from_analysis()`:
  - Apply token budget constraint (max 100k per phase)
  - Apply file count constraint (max 15-20 files per phase)
  - Apply logical coupling constraint (keep dependent components together)
- Maintain backward compatibility (if no adw_id provided, use heuristics)

#### 3C: Add Parsing Helpers (~50 lines)
Modify `adw_modules/workflow_ops.py`:
- Add `parse_component_analysis()` - extract markdown table rows
- Add `parse_dry_findings()` - extract JSON array
- Add `parse_context_analysis()` - extract markdown table rows
- Add `extract_markdown_table()` - generic table parser with regex

#### 3D: Create Coupled Workflow (~100 lines)
Create `adws/adw_analyze_plan_iso.py`:
- Clone structure from `adw_plan_build_iso.py`
- Sequential execution:
  ```python
  # Run analyze phase
  analyze_result = subprocess.run([
      "uv", "run", "adw_analyze_work_iso.py", issue_number
  ], capture_output=True)
  adw_id = extract_adw_id(analyze_result.stdout)

  # Run plan phase with ADW ID
  plan_result = subprocess.run([
      "uv", "run", "adw_plan_iso.py", issue_number, adw_id
  ], capture_output=True)

  return plan_result
  ```

**Files Created:** 2
- `adws/adw_analyze_work_iso.py` (~300 lines)
- `adws/adw_analyze_plan_iso.py` (~100 lines)

**Files Modified:** 2
- `adws/adw_plan_iso.py` (+100 lines)
- `adw_modules/workflow_ops.py` (+50 lines)

**Token Budget:** ~35,000 tokens
**Testing:** Integration test with issue #130

---

### Phase 4: Integration & Observability (1.0h, ~40 lines)

**Objective:** Wire analyze phase into complete workflows and add observability

**Tasks:**
1. Update `adws/adw_sdlc_complete_iso.py` (+20 lines)
   - Add analyze phase as first step (before plan)
   - Add `--skip-analysis` CLI flag for backward compatibility
   - Update phase sequence documentation

2. Update `adws/adw_sdlc_complete_zte_iso.py` (+20 lines)
   - Mirror changes from complete_iso.py
   - Ensure auto-merge works with new phase

3. Extend `adw_modules/tool_call_tracker.py` (+15 lines)
   - Add `track_subagent_spawn()` method
   - Log Task tool invocations with metadata
   - Enable cost attribution per sub-agent type

4. Update `.claude/commands/quick_start/adw.md` (+10 lines)
   - Document new phase sequence (11 phases total)
   - Add analyze phase to workflow descriptions
   - Update phase numbering

**Files Modified:** 4
- `adws/adw_sdlc_complete_iso.py` (+20 lines)
- `adws/adw_sdlc_complete_zte_iso.py` (+20 lines)
- `adw_modules/tool_call_tracker.py` (+15 lines)
- `.claude/commands/quick_start/adw.md` (+10 lines)

**Token Budget:** ~3,300 tokens
**Testing:** End-to-end workflow test with `--skip-analysis` flag

---

### Phase 5: Testing & Documentation (2.5h, ~450 lines)

**Objective:** Comprehensive testing and documentation

**Tasks:**
1. Create `adws/tests/test_multi_stage_planning.py` (~250 lines)
   - Test analyze phase standalone:
     ```python
     def test_analyze_phase_standalone():
         result = subprocess.run(["uv", "run", "adw_analyze_work_iso.py", "130"])
         assert result.returncode == 0
         state = ADWState.load("130", extract_adw_id(result.stdout))
         assert state.data.planning_approach == "multistage"
         assert len(state.data.multistage_components) >= 5
     ```
   - Test plan phase with analysis (3-constraint framework)
   - Test plan phase without analysis (backward compatible fallback)
   - Test coupled workflow (analyze → plan)
   - Test sub-agent response parsing edge cases
   - Test state persistence and retrieval

2. Update `adws/README.md` (+50 lines)
   - Document new analyze phase
   - Add usage examples for standalone and coupled workflows
   - Document expected cost savings (19% reduction)
   - Update phase sequence table

3. Update `.claude/commands/references/adw_workflows.md` (+30 lines)
   - Add analyze phase to workflow selection guide
   - Document when to use analyze vs skip-analysis
   - Add workflow decision tree

4. Create `.claude/commands/references/multi_stage_planning.md` (~120 lines)
   - Complete reference for analyze phase
   - Sub-agent descriptions and expected outputs
   - Three-constraint decision framework documentation
   - Troubleshooting guide
   - Cost analysis and token budgets

**Files Created:** 2
- `adws/tests/test_multi_stage_planning.py` (~250 lines)
- `.claude/commands/references/multi_stage_planning.md` (~120 lines)

**Files Modified:** 2
- `adws/README.md` (+50 lines)
- `.claude/commands/references/adw_workflows.md` (+30 lines)

**Token Budget:** ~8,100 tokens
**Testing:** Full test suite execution, documentation review

---

## File Modification Summary

### Files to Create (7 files, ~1,130 lines)
1. `.claude/subagents/component_analyzer.md` - 80 lines
2. `.claude/subagents/dry_checker.md` - 80 lines
3. `.claude/subagents/context_calculator.md` - 80 lines
4. `adws/adw_analyze_work_iso.py` - 300 lines (NEW discrete phase)
5. `adws/adw_analyze_plan_iso.py` - 100 lines (NEW coupled workflow)
6. `adws/tests/test_multi_stage_planning.py` - 250 lines
7. `.claude/commands/references/multi_stage_planning.md` - 120 lines

### Files to Modify (9 files, ~370 lines added)
1. `adw_modules/data_types.py` - +60 lines (3 dataclasses)
2. `adw_modules/state.py` - +10 lines (state fields)
3. `adw_modules/workflow_ops.py` - +50 lines (parsing helpers)
4. `adws/adw_plan_iso.py` - +100 lines (ENHANCED with conditional logic)
5. `adw_modules/tool_call_tracker.py` - +15 lines (subagent tracking)
6. `adws/adw_sdlc_complete_iso.py` - +20 lines (analyze phase integration)
7. `adws/adw_sdlc_complete_zte_iso.py` - +20 lines (analyze phase integration)
8. `adws/README.md` - +50 lines (documentation)
9. `.claude/commands/quick_start/adw.md` - +30 lines (quick reference)
10. `.claude/commands/references/adw_workflows.md` - +30 lines (workflow guide)

### Code Reuse Analysis
- **Total lines needed:** ~1,500 lines
- **Reusable patterns:** ~1,100 lines (73%)
- **Net new logic:** ~400 lines (27%)

**Key Reuse Opportunities:**
- ADWState persistence → 95% reuse from `state.py`
- CLI flag handling → 100% reuse from existing flags
- Sub-agent spawning → 100% reuse from Task tool examples
- Coupled workflow pattern → 100% reuse from `adw_plan_build_iso.py`
- Result parsing → 80% reuse from `complexity_analyzer.py` patterns
- Test infrastructure → 80% reuse from `test_sdlc_complete.py`

---

## New ADW Phase Sequence

### Before (10 phases):
```
1. Plan
2. Validate
3. Build
4. Lint
5. Test
6. Review
7. Document
8. Ship
9. Cleanup
10. Verify
```

### After (11 phases):
```
0. Analyze      ← NEW (optional, skip with --skip-analysis)
1. Plan         ← ENHANCED (consumes analyze results if present)
2. Validate
3. Build
4. Lint
5. Test
6. Review
7. Document
8. Ship
9. Cleanup
10. Verify
```

### Workflow Options

**Option 1: Full analyze+plan (recommended for complex features)**
```bash
uv run adw_sdlc_complete_iso.py 130
# Runs: Analyze → Plan → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup → Verify
# Total: 11 phases
# Cost: $0.42 for planning phases (19% savings)
```

**Option 2: Skip analysis (backward compatible, simple features)**
```bash
uv run adw_sdlc_complete_iso.py 130 --skip-analysis
# Runs: Plan (time-based) → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup → Verify
# Total: 10 phases (current workflow)
# Cost: $0.62 for planning phase (current cost)
```

**Option 3: Standalone analyze (exploratory analysis)**
```bash
uv run adw_analyze_work_iso.py 130
# Returns: Component breakdown, DRY findings, context analysis
# Use case: Estimate complexity before committing to implementation
```

**Option 4: Coupled analyze+plan only**
```bash
uv run adw_analyze_plan_iso.py 130
# Runs: Analyze → Plan (stops after planning)
# Use case: Generate implementation plan without executing it
```

---

## Token Budget & Cost Analysis

### Per-Phase Token Estimates

| Phase | Files to Modify | Reference Files | Total Tokens | % of Budget |
|-------|----------------|-----------------|--------------|-------------|
| Phase 1 | 2 files, 70 lines | 5 refs, 500 lines | ~5,700 | 5.7% |
| Phase 2 | 3 new files, 240 lines | 3 refs, 300 lines | ~5,400 | 5.4% |
| Phase 3 | 4 files, 550 lines | 8 refs, 1,500 lines | ~20,500 | 20.5% |
| Phase 4 | 4 files, 65 lines | 4 refs, 400 lines | ~4,650 | 4.7% |
| Phase 5 | 4 files, 450 lines | 6 refs, 800 lines | ~12,500 | 12.5% |

**Total Estimated Tokens:** ~48,750 tokens (avg per phase: ~9,750)
**Max Recommended per Phase:** 100,000 tokens
**Safety Margin:** 51,250 tokens (51% headroom)

### Cost Comparison

**Monolithic Planning (Current):**
- Single-pass analysis: 271,000 tokens
- Cost: $0.54 (input) + $0.08 (output) = **$0.62**

**Analyze + Plan (Proposed):**
- Analyze phase: 100,000 tokens
- Plan phase (with analysis): 120,000 tokens
- Sub-agent overhead: 0 tokens (shared context)
- Total: 220,000 tokens
- Cost: $0.35 (input) + $0.07 (output) = **$0.42**

**Plan Only (Backward Compatible):**
- Plan phase (time-based): 271,000 tokens
- Cost: $0.54 (input) + $0.08 (output) = **$0.62** (unchanged)

**Savings:** 19% reduction when using analyze+plan ($0.20 saved per run)

---

## Three-Constraint Decision Framework

When analyze phase runs, the enhanced plan phase applies these constraints:

### Constraint 1: Token Budget
- **Max:** 100,000 tokens per phase
- **Calculation:** (files_to_modify + files_for_reference) × 10 tokens/line
- **Safety margin:** Add 20% buffer
- **Action:** If component exceeds budget, split across multiple phases

### Constraint 2: File Count
- **Max:** 15-20 files per phase
- **Rationale:** Prevent context window overflow, maintain focus
- **Action:** If component touches 25+ files, split by subsystem

### Constraint 3: Logical Coupling
- **Rule:** Keep tightly-coupled components in same phase
- **Detection:** Check component dependency graph
- **Action:** If C2 depends on C1, group in same phase (unless violates constraints 1-2)

### Example Application

**Scenario:** Feature #130 analysis identifies 9 components

| Component | Files | Tokens | Dependencies |
|-----------|-------|--------|--------------|
| C1: DataTypes | 2 | 1,200 | - |
| C2: SubAgents | 3 | 2,400 | C1 |
| C3: Analyze Script | 1 | 3,000 | C1, C2 |
| C4: Plan Enhancement | 1 | 1,000 | C1 |
| C5: Coupled Workflow | 1 | 1,000 | C3, C4 |
| C6: Integration | 3 | 600 | C3, C4 |
| C7: Tests | 1 | 2,500 | C1-C6 |
| C8: Docs | 3 | 1,200 | C1-C6 |

**Phase Boundary Decision:**

**Phase 1:** C1 only
- Files: 2, Tokens: 1,200 (LOW)
- Justification: Foundational, no dependencies, quick win

**Phase 2:** C2 (depends on C1, but not tightly coupled)
- Files: 3, Tokens: 2,400 (LOW)
- Justification: Sub-agent prompts are independent once dataclasses exist

**Phase 3:** C3, C4, C5 (tightly coupled - all three form the core workflow)
- Files: 3, Tokens: 5,000 (MEDIUM)
- Justification: Analyze script needs plan enhancement to be useful, coupled workflow ties them together

**Phase 4:** C6 (integration depends on C3-C5 being complete)
- Files: 3, Tokens: 600 (LOW)
- Justification: Simple wiring, low coupling

**Phase 5:** C7, C8 (tests and docs cover entire implementation)
- Files: 4, Tokens: 3,700 (MEDIUM)
- Justification: Test all components, document entire system

**Result:** 5 phases, all under token budget, logical separation maintained

---

## Success Criteria

### Functional Requirements
- ✅ Analyze phase completes within single Claude Code session
- ✅ Sub-agents spawn via Task tool without subprocess calls
- ✅ Component analysis identifies 5-10 logical components per feature
- ✅ DRY checker detects at least 70% of reusable patterns
- ✅ Context analyzer calculates token budgets within 10% accuracy
- ✅ Enhanced plan phase respects all 3 constraints when analysis available
- ✅ Enhanced plan phase falls back to time-based heuristics when analysis unavailable
- ✅ Backward compatibility: existing workflows work with `--skip-analysis`
- ✅ Standalone analyze phase returns useful complexity metrics

### Performance Requirements
- ✅ 19% token reduction vs monolithic (220k vs 271k) when using analyze+plan
- ✅ Analyze phase completes in < 3 minutes
- ✅ Enhanced plan phase completes in < 2 minutes
- ✅ Sub-agent response time < 60 seconds each
- ✅ Total analyze+plan time < 5 minutes

### Quality Requirements
- ✅ Test coverage ≥ 80% for new code
- ✅ Type checking passes (mypy --strict)
- ✅ Linting passes (ruff check)
- ✅ Zero regression in existing ADW workflows
- ✅ Documentation completeness score ≥ 90%

---

## Testing Strategy

### Unit Tests
**File:** `adws/tests/test_multi_stage_planning.py`

```python
def test_analyze_phase_creates_worktree():
    """Verify analyze phase creates worktree and returns ADW ID"""
    result = run_analyze_phase(issue_number="130")
    assert result.returncode == 0
    assert re.match(r"adw-[a-f0-9]{8}", result.adw_id)
    assert os.path.exists(f"trees/{result.adw_id}")

def test_analyze_phase_persists_results():
    """Verify analyze phase stores components, DRY findings, context in state"""
    result = run_analyze_phase(issue_number="130")
    state = ADWState.load("130", result.adw_id)

    assert state.data.planning_approach == "multistage"
    assert len(state.data.multistage_components) >= 5
    assert len(state.data.dry_findings) >= 1
    assert state.data.context_analysis is not None

def test_plan_phase_uses_analysis():
    """Verify plan phase applies 3-constraint framework when analysis exists"""
    # Setup: Run analyze phase first
    analyze_result = run_analyze_phase(issue_number="130")

    # Test: Run plan phase with ADW ID
    plan_result = run_plan_phase(issue_number="130", adw_id=analyze_result.adw_id)

    # Verify plan used multistage approach
    state = ADWState.load("130", analyze_result.adw_id)
    assert state.data.planning_approach == "multistage"

    # Verify phases respect constraints
    plan = parse_plan_markdown(plan_result.stdout)
    for phase in plan.phases:
        assert phase.token_estimate <= 100_000  # Token constraint
        assert phase.file_count <= 20  # File constraint

def test_plan_phase_fallback_without_analysis():
    """Verify plan phase falls back to time-based heuristics without analysis"""
    # Run plan phase WITHOUT prior analyze phase
    plan_result = run_plan_phase(issue_number="130")

    # Verify fallback to monolithic approach
    assert "time-based" in plan_result.stdout.lower()
    # Verify still generates valid plan
    assert plan_result.returncode == 0

def test_coupled_workflow():
    """Verify analyze_plan workflow runs both phases sequentially"""
    result = run_coupled_workflow(issue_number="130")

    assert result.returncode == 0
    # Verify both phases completed
    assert "Analyze phase complete" in result.stdout
    assert "Plan phase complete" in result.stdout

    # Verify state shows multistage approach
    state = ADWState.load("130", result.adw_id)
    assert state.data.planning_approach == "multistage"

def test_component_analysis_parsing():
    """Verify ComponentAnalysis dataclass parsing from markdown"""
    markdown_response = """
    | Component | Type | Description | Dependencies | Files | Hours | Tokens |
    |-----------|------|-------------|--------------|-------|-------|--------|
    | C1 | database | Add users table | - | 3 | 1.5 | 1500 |
    | C2 | api | Create users endpoint | C1 | 2 | 1.0 | 1000 |
    """
    components = parse_component_analysis(markdown_response)

    assert len(components) == 2
    assert components[0].component_type == "database"
    assert components[0].estimated_hours == 1.5
    assert components[1].dependencies == ["C1"]

def test_dry_finding_detection():
    """Verify DRY checker output parsing"""
    json_response = """
    ```json
    [{
        "finding_id": "DRY-001",
        "duplicate_type": "pattern",
        "existing_file": "routes/users.py",
        "existing_lines": "45-67",
        "reuse_recommendation": "Reuse pagination pattern",
        "tokens_saved_estimate": 300
    }]
    ```
    """
    findings = parse_dry_findings(json_response)

    assert len(findings) == 1
    assert findings[0].duplicate_type == "pattern"
    assert findings[0].tokens_saved_estimate == 300
```

### Integration Tests

```python
def test_sdlc_complete_with_analyze():
    """Verify complete SDLC workflow includes analyze phase by default"""
    result = subprocess.run([
        "uv", "run", "adw_sdlc_complete_iso.py", "130"
    ], capture_output=True, timeout=600)

    assert result.returncode == 0
    assert "Running analyze phase" in result.stdout
    assert "Running plan phase" in result.stdout

def test_sdlc_complete_skip_analysis():
    """Verify --skip-analysis flag bypasses analyze phase"""
    result = subprocess.run([
        "uv", "run", "adw_sdlc_complete_iso.py", "130", "--skip-analysis"
    ], capture_output=True, timeout=600)

    assert result.returncode == 0
    assert "Skipping analyze phase" in result.stdout
    assert "Running plan phase" in result.stdout

def test_backward_compatibility():
    """Verify existing workflows work unchanged without analyze phase"""
    result = subprocess.run([
        "uv", "run", "adw_plan_build_iso.py", "130"
    ], capture_output=True, timeout=600)

    assert result.returncode == 0
    # Verify plan phase used time-based heuristics
    state = ADWState.load("130", extract_adw_id(result.stdout))
    assert state.data.planning_approach in ["monolithic", None]
```

### Manual Testing Checklist
- [ ] Run analyze phase on simple issue (2h estimate, 1-2 components expected)
- [ ] Run analyze phase on complex issue (12h estimate, 8-10 components expected)
- [ ] Verify sub-agent responses parse correctly (check for markdown/JSON format errors)
- [ ] Confirm DRY checker finds known duplicates (test with issue that reuses existing patterns)
- [ ] Validate phase boundaries match expectations (review generated plan for constraint violations)
- [ ] Test coupled workflow (analyze → plan) on 3 different issues
- [ ] Test complete SDLC with analyze phase
- [ ] Test complete SDLC with `--skip-analysis` flag
- [ ] Verify observability (check database for tool call tracking)

---

## Risk Mitigation

### Risk 1: Sub-Agent Response Format Inconsistency
**Impact:** High (parsing failures block workflow)
**Likelihood:** Medium
**Mitigation:**
- Use strict markdown/JSON output format specifications in sub-agent prompts
- Add fallback parsing with regex patterns for malformed responses
- Log unparseable responses for debugging
- Implement retry logic (max 2 attempts per sub-agent)
- Provide clear examples in sub-agent prompt templates

### Risk 2: Analyze Phase Adds Latency
**Impact:** Medium (users may prefer faster time-based planning)
**Likelihood:** Low
**Mitigation:**
- Make analyze phase optional via `--skip-analysis` flag (default: enabled)
- Optimize sub-agent prompts to minimize response time
- Target 3-minute analyze phase (vs 2-minute time-based plan)
- Communicate cost/time tradeoff clearly in documentation

### Risk 3: Token Budget Calculation Inaccuracy
**Impact:** Medium (phases may overflow context)
**Likelihood:** Low
**Mitigation:**
- Use conservative 10 tokens/line estimate (actual is 8-9)
- Add 20% safety margin to all token calculations
- Monitor actual token usage via observability system
- Implement circuit breaker if phase exceeds 90k tokens
- Iterate on estimation formula based on real-world data

### Risk 4: DRY Checker False Negatives
**Impact:** Low (missed optimization opportunities)
**Likelihood:** Medium
**Mitigation:**
- Provide example patterns in sub-agent prompt (pagination, CRUD, auth)
- Use multiple search strategies (Grep keywords + Glob file patterns + Read similar files)
- Review DRY findings manually in first 10 implementations
- Iterate on sub-agent prompt based on feedback
- Track false negative rate in observability system

### Risk 5: Logical Coupling Misjudgment
**Impact:** Medium (phases may have unexpected dependencies)
**Likelihood:** Medium
**Mitigation:**
- Conservative coupling detection (err on side of keeping components together)
- Validate dependency graph in component analysis stage
- Allow manual phase adjustments in generated plan
- Test with known tightly-coupled features first (auth, payments, multi-table schemas)
- Collect feedback on phase boundary quality

### Risk 6: Backward Compatibility Regression
**Impact:** High (breaks existing workflows)
**Likelihood:** Low
**Mitigation:**
- **Analyze phase is optional** (skip with `--skip-analysis` flag)
- Plan phase **falls back** to time-based heuristics if no analysis present
- Comprehensive integration tests for monolithic workflow
- Separate scripts isolate new logic (no modifications to core phase executors)
- Gradual rollout (test on 5-10 issues before making analyze phase default)

---

## Rollout Plan

### Phase 1: Development & Testing (Weeks 1-2)
- Implement all 5 implementation phases
- Run unit and integration tests
- Manual testing on 3-5 sample issues (simple, medium, complex)
- Documentation review and iteration

### Phase 2: Alpha Testing (Week 3)
- Deploy analyze phase to production (opt-in)
- Test on 10 real GitHub issues of varying complexity:
  - 3 simple issues (2h, 1-2 components)
  - 5 medium issues (6h, 4-6 components)
  - 2 complex issues (12h, 8-10 components)
- Monitor token usage and cost savings
- Collect feedback on phase boundaries
- Measure DRY checker accuracy

### Phase 3: Beta Testing (Week 4)
- Make analyze phase **default** (remove opt-in flag)
- Add `--skip-analysis` flag for fallback
- Announce in project README and documentation
- Track success rate and error patterns
- Iterate on sub-agent prompts based on results
- Measure time-to-plan vs time-based approach

### Phase 4: General Availability (Week 5+)
- Analyze phase is production-ready
- Publish cost savings metrics (target: 19% average)
- Update all workflow documentation
- Archive monolithic planning documentation (keep for reference)
- Monitor observability metrics ongoing

---

## Dependencies

### External Dependencies
- ✅ Claude Code CLI with Task tool support (already available)
- ✅ `.claude/commands/implement.md` examples (already exist)
- ✅ `adw_modules/agent.py` sub-agent infrastructure (already exists)
- ✅ `adw_plan_build_iso.py` coupled workflow pattern (already exists)

### Internal Dependencies
**Phase 1 Dependencies:** None (foundational data types)
**Phase 2 Dependencies:** Phase 1 (dataclasses needed for sub-agent output)
**Phase 3 Dependencies:** Phase 1, 2 (needs dataclasses and sub-agent definitions)
**Phase 4 Dependencies:** Phase 3 (needs analyze and enhanced plan scripts)
**Phase 5 Dependencies:** Phase 1-4 (tests need all components implemented)

### Blocking Issues
- None identified (all required infrastructure exists)

---

## Monitoring & Observability

### Key Metrics to Track

**Cost Metrics:**
- Average tokens per analyze phase (target: 100k)
- Average tokens per plan phase with analysis (target: 120k)
- Average tokens per plan phase without analysis (baseline: 271k)
- Cost savings vs monolithic (target: 19% reduction)
- Sub-agent spawning overhead (target: <10k tokens per sub-agent)

**Quality Metrics:**
- DRY detection accuracy (target: 70%+ true positives)
- Phase boundary violations (target: <5% phases exceed 100k tokens)
- Component analysis completeness (target: 100% coverage of issue requirements)
- False negative rate (missed reuse opportunities) (target: <30%)

**Performance Metrics:**
- Analyze phase duration (target: <3 minutes)
- Plan phase duration (with analysis) (target: <2 minutes)
- Sub-agent response time (target: <60 seconds each)
- Total analyze+plan time (target: <5 minutes)
- File context calculation accuracy (target: ±10%)

### Database Queries

```sql
-- Average tokens per analyze phase
SELECT
    AVG(total_tokens) as avg_tokens,
    COUNT(*) as total_runs
FROM task_logs
WHERE workflow_type = 'adw_analyze_work_iso'
  AND created_at >= NOW() - INTERVAL '30 days';

-- Cost savings comparison
SELECT
    planning_approach,
    AVG(total_tokens) as avg_tokens,
    AVG(total_cost_usd) as avg_cost,
    COUNT(*) as runs
FROM task_logs
WHERE workflow_type IN ('adw_plan_iso', 'adw_analyze_plan_iso')
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY planning_approach;

-- DRY findings per analyze phase
SELECT
    workflow_id,
    json_array_length(tool_calls::json, '$.dry_findings') as finding_count,
    created_at
FROM task_logs
WHERE workflow_type = 'adw_analyze_work_iso'
ORDER BY finding_count DESC;

-- Phase boundary violations (phases exceeding 100k tokens)
SELECT
    workflow_id,
    phase_number,
    token_estimate,
    file_count
FROM task_logs
WHERE workflow_type LIKE '%build%'
  AND token_estimate > 100000
  AND created_at >= NOW() - INTERVAL '30 days';

-- Sub-agent performance tracking
SELECT
    tool_calls::json->>'subagent_type' as subagent_type,
    AVG((tool_calls::json->>'duration_ms')::int) as avg_duration_ms,
    COUNT(*) as invocations
FROM task_logs
WHERE tool_calls::json->>'tool_name' = 'Task'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY subagent_type;
```

---

## Appendix: Example Workflow Execution

### Example 1: Analyze Phase Standalone

```bash
$ uv run adw_analyze_work_iso.py 130

Creating worktree for issue #130...
✓ Worktree created: trees/adw-99ff48a6

Running component analysis sub-agent...
✓ Component analysis complete: 9 components identified

Running DRY checker sub-agent...
✓ DRY analysis complete: 3 reuse opportunities found

Running context calculator sub-agent...
✓ Context analysis complete: Token budgets calculated

Persisting results to ADWState...
✓ Analysis saved: agents/adw-99ff48a6/adw_state.json

Analysis Summary:
  Components: 9
  DRY Findings: 3 (estimated savings: 3,300 tokens)
  Recommended Phases: 5
  Total Estimated Tokens: ~48,750

ADW ID: adw-99ff48a6
```

### Example 2: Enhanced Plan Phase (with prior analysis)

```bash
$ uv run adw_plan_iso.py 130 adw-99ff48a6

Loading analysis from ADWState...
✓ Found multistage analysis (9 components, 3 DRY findings)

Applying 3-constraint framework...
  Token Budget Constraint: Max 100k per phase
  File Count Constraint: Max 20 files per phase
  Logical Coupling Constraint: Keep dependencies together

Generating phase boundaries...
✓ Phase 1: Data Types & State (2 files, 1,200 tokens)
✓ Phase 2: Sub-Agent Definitions (3 files, 2,400 tokens)
✓ Phase 3: Analyze & Plan Scripts (3 files, 5,000 tokens)
✓ Phase 4: Integration (3 files, 600 tokens)
✓ Phase 5: Testing & Docs (4 files, 3,700 tokens)

Implementation Plan: docs/architecture/IMPLEMENTATION_PLAN_130.md
Estimated Cost: $0.42 (19% savings vs time-based)
```

### Example 3: Coupled Workflow

```bash
$ uv run adw_analyze_plan_iso.py 130

Running analyze phase...
✓ Analyze complete: adw-99ff48a6

Running plan phase...
✓ Plan complete

Total Time: 4m 32s
Total Cost: $0.42
Savings vs. time-based: $0.20 (19%)

Implementation Plan: docs/architecture/IMPLEMENTATION_PLAN_130.md
```

### Example 4: Complete SDLC with Analyze Phase

```bash
$ uv run adw_sdlc_complete_iso.py 130

Phase 0: Analyze [0/11]
  Running adw_analyze_work_iso.py...
  ✓ Complete (3m 12s, $0.16)

Phase 1: Plan [1/11]
  Running adw_plan_iso.py (using analyze results)...
  ✓ Complete (1m 48s, $0.26)

Phase 2: Validate [2/11]
  Running adw_validate_iso.py...
  ✓ Complete (2m 05s, $0.08)

[... rest of SDLC phases ...]

Total Cost: $4.85
Planning Savings: $0.20 (4% of total SDLC cost)
```

### Example 5: Backward Compatible (Skip Analysis)

```bash
$ uv run adw_sdlc_complete_iso.py 130 --skip-analysis

Skipping analyze phase (backward compatible mode)

Phase 1: Plan [0/10]
  Running adw_plan_iso.py (using time-based heuristics)...
  ✓ Complete (2m 30s, $0.62)

Phase 2: Validate [1/10]
  Running adw_validate_iso.py...
  ✓ Complete (2m 05s, $0.08)

[... rest of SDLC phases ...]

Total Cost: $5.05 (no planning savings)
```

---

## Conclusion

This revised phased implementation plan introduces a **new discrete Analyze phase** to ADW's workflow, following the established pattern of:
- **Discrete phases** with single responsibility (`adw_X_iso.py`)
- **Coupled workflows** for convenience (`adw_X_Y_iso.py`)
- **Higher-order orchestration** in complete workflows (`adw_sdlc_complete_iso.py`)

**Key Architectural Decisions:**
1. ✅ Analyze phase is **discrete** and **optional** (can run standalone or skip)
2. ✅ Plan phase is **enhanced** (not replaced) with backward-compatible fallback
3. ✅ Coupled workflow follows existing pattern (`adw_plan_build_iso.py`)
4. ✅ Complete SDLC now has **11 phases** (Analyze added as Phase 0)
5. ✅ All changes maintain **100% backward compatibility**

**Next Steps:**
1. Review and approve this corrected architecture
2. Clarify any remaining questions about phase separation
3. Begin Phase 1 implementation (Data Types & State Extensions)
4. Iteratively implement Phases 2-5 with testing at each stage

**Questions or Concerns:**
- Does the discrete phase pattern match your mental model?
- Should analyze phase be **default** (skip with `--skip-analysis`) or **opt-in** (enable with `--use-analyze`)?
- Should we test with both simple and complex issues before making it default?
