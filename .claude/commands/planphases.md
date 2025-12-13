# Phase Planning and Prompt Generation

Analyze issues from planned_features database, determine phase breakdown, and generate implementation prompts for each phase.

## Variables
issue_ids: $@ (space-separated list of issue IDs, or empty for all planned issues)

## Quick Start

```bash
# Plan phases for specific issues
./scripts/plan_phases.sh 49 52 55 57

# Plan phases for all planned issues
./scripts/plan_phases.sh

# Generate phase prompts (not just coordination doc)
./scripts/plan_phases.sh 104 --generate
```

## Instructions

You are the **Phase Planning Coordinator**. Your job is to:
1. Analyze each requested issue for complexity and scope
2. Determine if it needs single or multiple phases
3. Generate implementation prompts for each phase
4. Create a coordination document showing execution sequence and dependencies
5. Identify which phases/issues can be run in parallel

### Phase 1: Fetch and Analyze Issues

```bash
# List available issues if no IDs provided
./scripts/gen_prompt.sh --list --status planned
```

**For each issue ID provided (or all planned if none specified):**
1. Fetch issue details from database
2. Analyze complexity based on:
   - Estimated hours (>4h likely needs phases)
   - Description mentions of "Phase 1", "Phase 2", etc.
   - Cross-cutting concerns (frontend + backend + database)
   - Dependencies on other features
   - Number of files to modify

### Phase 2: Determine Phase Breakdown

**Phasing Logic:**

**Single Phase (0.25h - 2h):**
- Quick wins, bug fixes, small enhancements
- Touch 1-3 files
- No cross-cutting concerns
- Example: "Fix error handling in workLogClient"

**2 Phases (2h - 6h):**
- Medium features with distinct steps
- Phase 1: Foundation/Backend (database, API, services)
- Phase 2: Frontend/Integration (UI, testing, E2E)
- Example: "Add new API endpoint with UI"

**3+ Phases (6h+):**
- Large features with complex dependencies
- Phase 1: Database/Model layer
- Phase 2: Backend services/API
- Phase 3: Frontend UI
- Phase 4: Integration/E2E tests (if needed)
- Example: "Workflow orchestration system"

**Dependency Analysis:**
- Check if issue depends on other planned features
- Identify shared components/files
- Note if phases within an issue are sequential or can overlap

### Phase 3: Generate Prompts

For each phase of each issue:

1. **Generate prompt using existing script:**
   ```bash
   # If issue needs phases, we'll manually create phase-specific prompts
   # For single-phase issues, use existing generator:
   ./scripts/gen_prompt.sh <issue_id>
   ```

2. **For multi-phase issues, create phase prompts manually:**
   - Use the template at `.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`
   - File naming: `FEATURE_<ID>_PHASE_<N>_<slug>.md`
   - Each phase should:
     - Reference the original issue ID
     - Clearly state "Phase N of M"
     - Note dependencies on previous phases
     - Include specific time estimate for that phase
     - List only files relevant to that phase

3. **Prompt content for each phase:**
   ```markdown
   # Feature #<ID> - Phase <N> of <M>: <Phase Title>

   ## Context
   Load: `/prime`
   Depends on: [Phase N-1 completion] OR [Issue #X completion]

   ## Task
   <One sentence describing this phase's goal>

   ## Phase Overview
   This is Phase <N> of <M> for Feature #<ID>: <Full Feature Title>

   **Previous phases:**
   - Phase 1: <What was completed>
   [repeat for all previous phases]

   **This phase:**
   - <What we're building now>

   **Upcoming phases:**
   - Phase N+1: <What comes next>
   [repeat for remaining phases]

   ## Workflow
   [... rest of template ...]

   ## Success Criteria
   - ✅ Phase <N> implementation complete
   - ✅ Ready for Phase <N+1> [or "Feature complete" if last phase]
   [... other criteria ...]
   ```

### Phase 4: Create Coordination Document

Create a file: `PHASE_PLAN_<timestamp>.md` with:

```markdown
# Phase Implementation Plan
Generated: <timestamp>

## Executive Summary
- Total Issues: <N>
- Total Phases: <M>
- Estimated Time: <X>h
- Parallelizable: <Y> phases

## Issues Analyzed
<table showing all issues with phase breakdown>

## Execution Sequence

### Parallel Track A (can run simultaneously)
1. Feature #<ID> Phase 1 (<X>h) → FEATURE_<ID>_PHASE_1_<slug>.md
2. Feature #<ID2> (single phase, <Y>h) → QUICK_WIN_<ID2>_<slug>.md

### Parallel Track B (can run simultaneously with Track A)
1. Feature #<ID3> Phase 1 (<Z>h) → FEATURE_<ID3>_PHASE_1_<slug>.md

### Sequential: After Track A completes
1. Feature #<ID> Phase 2 (<X>h) → FEATURE_<ID>_PHASE_2_<slug>.md
   - Depends on: Feature #<ID> Phase 1

### Sequential: After Track A & B complete
1. Feature #<ID4> (<X>h) → FEATURE_<ID4>_<slug>.md
   - Depends on: Feature #<ID> complete, Feature #<ID3> complete

## Dependency Graph
```
[ASCII diagram showing dependencies]
```

## Generated Prompt Files
- FEATURE_X_PHASE_1_foundation.md
- FEATURE_X_PHASE_2_integration.md
- QUICK_WIN_Y_error_handling.md
[... list all generated files ...]

## Implementation Notes
- Phases within same feature must run sequentially
- Independent features can run in parallel
- Shared file modifications require coordination
[... other notes ...]
```

### Phase 5: Report Results

Output a summary:
```
✅ Phase Planning Complete

Issues Analyzed: <N>
Total Phases: <M>
Estimated Time: <X>h

Parallelizable Phases: <Y>
Sequential Phases: <Z>

Files Generated:
- PHASE_PLAN_<timestamp>.md (coordination document)
- <list of all prompt files>

Next Steps:
1. Review PHASE_PLAN_<timestamp>.md for execution sequence
2. Start with Parallel Track A phases
3. Execute phases in order per coordination document
```

## Execution Logic

**Step-by-step:**

1. **Parse input:**
   ```python
   issue_ids = "$@".split() if "$@" else get_all_planned_issue_ids()
   ```

2. **For each issue:**
   ```python
   issue = fetch_issue(issue_id)
   phase_count = determine_phases(issue)

   if phase_count == 1:
       generate_single_prompt(issue)
   else:
       for phase in range(1, phase_count + 1):
           generate_phase_prompt(issue, phase, phase_count)
   ```

3. **Analyze dependencies:**
   ```python
   for issue in issues:
       check_dependencies(issue)
       check_file_conflicts(issue)
   ```

4. **Create coordination document:**
   ```python
   create_coordination_doc(issues, phases, dependencies)
   ```

## Template Usage

**Use existing template for:**
- Single-phase issues (0.25h - 2h)
- Individual phases of multi-phase features

**Modify template for phases by:**
1. Adding "Phase N of M" to title
2. Adding "Depends on" to Context section
3. Adding "Phase Overview" section after Task
4. Updating "Next" section to reference next phase

## File Naming Convention

**Single Phase:**
- `QUICK_WIN_<ID>_<slug>.md` (if ≤ 2h)
- `<TYPE>_<ID>_<slug>.md` (if > 2h)

**Multi-Phase:**
- `FEATURE_<ID>_PHASE_1_<slug>.md`
- `FEATURE_<ID>_PHASE_2_<slug>.md`
- etc.

**Coordination:**
- `PHASE_PLAN_<YYYYMMDD_HHMMSS>.md`

## Success Criteria

- ✅ All requested issues analyzed
- ✅ Phase breakdown determined for each
- ✅ Prompt file generated for each phase
- ✅ Coordination document created
- ✅ Dependencies identified
- ✅ Parallel execution opportunities identified
- ✅ Clear execution sequence provided

## Example Usage

```bash
# Plan phases for specific issues
/planphases 49 52 55 57

# Plan phases for all planned issues
/planphases

# Plan phases for specific feature
/planphases 104
```

## Implementation Approach

Since this is a complex coordination task:
1. Use Python script (similar to generate_prompt.py)
2. Leverage existing PlannedFeaturesService
3. Create new PhaseAnalyzer class
4. Output structured coordination document
5. Generate individual phase prompts

## Notes

- Phases should be sized 0.5h - 4h each (optimal for single context)
- Very large features (>12h) might need 4-5 phases
- Always check for file modification conflicts
- Prefer parallel execution when safe
- Sequential execution when dependencies exist
