# Design: Unified Prompt Generation Workflow

**Date**: 2025-12-13
**Status**: Design Phase
**Context**: Session discussing implementation of `/genprompts` command

---

## Problem Statement

**User Request:**
> "Add functionality to a custom slash command to perform the following: review each issue in turn, determining if it needs 1 or more phases to implement, then provide the prompt for each phase (as applicable). Phases will be run in a separate context. If phases or issues can be run in parallel, indicate such, and sequence for implementation if dependencies. Use the current prompt templates we've been using to create the prompts for each phase."

**Current Pain Points:**
- Manual determination of whether an issue needs multiple phases
- No automated analysis of complexity and phase breakdown
- No coordination document showing execution sequence and dependencies
- Manual creation of phase-specific prompts

---

## Current State Analysis

### Existing Tools

#### 1. `scripts/gen_prompt.sh` (Single Issue Prompt Generator)
**Purpose**: Generate single implementation prompt for one issue
**How it works**:
```bash
./scripts/gen_prompt.sh 49    # Generates QUICK_WIN_49_*.md
./scripts/gen_prompt.sh 104   # Generates FEATURE_104_*.md
```

**What it does**:
- Queries `planned_features` database for issue details
- Analyzes codebase for relevant files (backend/frontend)
- Uses template at `.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`
- Generates single prompt file with codebase context
- Naming: `QUICK_WIN_ID_slug.md` (≤2h) or `TYPE_ID_slug.md` (>2h)

**Limitations**:
- Only handles single-phase issues
- No phase breakdown logic
- No dependency analysis
- Manual determination of whether issue needs phases

#### 2. `scripts/plan_phases.sh` (NEW - Phase Analysis)
**Purpose**: Analyze issues and determine phase breakdown
**How it works**:
```bash
./scripts/plan_phases.sh 49 52 55 57    # Analyze specific issues
./scripts/plan_phases.sh                # Analyze all planned issues
```

**What it does**:
- Analyzes each issue for complexity (hours, files, cross-cutting concerns)
- Determines optimal phase count (1-5 phases based on estimated hours)
- Identifies dependencies between phases
- Identifies file modification conflicts
- Generates coordination document (`PHASE_PLAN_<timestamp>.md`)

**Phase Breakdown Logic**:
```python
0.25h - 2h   → 1 phase  (quick win/bug fix)
2h - 6h      → 2 phases (foundation + integration)
6h - 12h     → 3 phases (data + backend + frontend)
12h - 18h    → 4 phases (data + backend + API + frontend)
18h+         → 5 phases (data + backend + API + frontend + integration)
```

**Current Limitation**:
- Creates coordination document but **does NOT generate actual prompt files**
- Only outputs phase plan, not the prompts themselves

#### 3. `.claude/commands/plan_complete_workflow.md` (ADW Planning)
**Purpose**: Comprehensive workflow planning for ADW executions
**Scope**: Used by ADW automation system for isolated worktree workflows
**Not relevant**: Different context (ADW vs manual Claude Code prompts)

### Key Insight: Overlap and Gaps

**We have:**
✅ Phase analysis logic (`plan_phases.sh`)
✅ Single prompt generation (`gen_prompt.sh`)
✅ Prompt template (`.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`)

**We need:**
❌ Integration between phase analysis and prompt generation
❌ Multi-phase prompt generation
❌ Single command that orchestrates the full workflow
❌ Coordination document with execution order and links to generated prompts

---

## Proposed Solution

### Architecture: Three-Step Orchestration

```
User invokes: /genprompts 49 52 55 104

Step 1: ANALYZE PHASES
┌─────────────────────────────────────┐
│ plan_phases.sh --output-json        │
│                                     │
│ Input:  Issue IDs                   │
│ Output: phase_metadata.json         │
│                                     │
│ {                                   │
│   "features": [                     │
│     {                               │
│       "issue_id": 104,              │
│       "phases": [                   │
│         {                           │
│           "phase_num": 1,           │
│           "total_phases": 3,        │
│           "title": "...",           │
│           "hours": 1.5,             │
│           "depends_on": []          │
│         },                          │
│         ...                         │
│       ]                             │
│     }                               │
│   ],                                │
│   "parallel_tracks": [...],         │
│   "dependencies": {...}             │
│ }                                   │
└─────────────────────────────────────┘
                 ↓
Step 2: GENERATE PROMPTS
┌─────────────────────────────────────┐
│ For each phase in phase_metadata:  │
│                                     │
│ gen_prompt.sh <issue_id> \          │
│   --phase <num> \                   │
│   --total-phases <total> \          │
│   --depends-on "<deps>"             │
│                                     │
│ Generates:                          │
│ - FEATURE_104_PHASE_1_*.md          │
│ - FEATURE_104_PHASE_2_*.md          │
│ - FEATURE_104_PHASE_3_*.md          │
│ - QUICK_WIN_49_*.md (single phase)  │
└─────────────────────────────────────┘
                 ↓
Step 3: CREATE COORDINATION DOC
┌─────────────────────────────────────┐
│ coordination_doc.py                 │
│                                     │
│ Creates: PHASE_PLAN_<timestamp>.md  │
│                                     │
│ Content:                            │
│ - Executive summary                 │
│ - Feature/phase breakdown table     │
│ - Execution sequence with tracks    │
│ - File modification conflicts       │
│ - Links to generated prompt files   │
│ - Next steps for execution          │
└─────────────────────────────────────┘
```

### Output Example

**For input**: `/genprompts 49 52 104`

**Generated files**:
```
QUICK_WIN_49_fix_error_handling.md
QUICK_WIN_52_memoize_computations.md
FEATURE_104_PHASE_1_database_setup.md
FEATURE_104_PHASE_2_backend_services.md
FEATURE_104_PHASE_3_frontend_ui.md
PHASE_PLAN_20251213_120000.md
```

**PHASE_PLAN_20251213_120000.md** contains:
```markdown
# Phase Implementation Plan

## Executive Summary
- Total Features: 3
- Total Phases: 5
- Estimated Time: 8.5h
- Parallel Tracks: 3

## Execution Sequence

### Track 1 (parallel)
- **QUICK_WIN_49_fix_error_handling.md**
  - Issue #49: Fix error handling
  - Estimated: 0.25h
  - No dependencies

- **QUICK_WIN_52_memoize_computations.md**
  - Issue #52: Memoize computations
  - Estimated: 0.25h
  - No dependencies

- **FEATURE_104_PHASE_1_database_setup.md**
  - Issue #104 Phase 1 of 3: Database setup
  - Estimated: 2.0h
  - No dependencies

### Track 2 (sequential - depends on Track 1)
- **FEATURE_104_PHASE_2_backend_services.md** (depends on: #104 Phase 1)
  - Issue #104 Phase 2 of 3: Backend services
  - Estimated: 3.0h

### Track 3 (sequential - depends on Track 2)
- **FEATURE_104_PHASE_3_frontend_ui.md** (depends on: #104 Phase 2)
  - Issue #104 Phase 3 of 3: Frontend UI
  - Estimated: 3.0h

## Next Steps
1. Execute Track 1 phases in parallel (3 separate Claude Code contexts)
2. After Track 1 complete, execute Track 2
3. After Track 2 complete, execute Track 3
4. Mark each phase complete in Plans Panel before proceeding
```

---

## Implementation Details

### Modifications Required

#### A. Enhance `scripts/plan_phases.py`

**Add JSON output mode**:
```python
def output_json(self, all_phases: List[List[Phase]], dependency_analysis: Dict) -> str:
    """Output phase metadata as JSON for orchestration."""
    data = {
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
                "depends_on": phase.depends_on
            })
        data["features"].append(feature_data)

    # Add parallel tracks
    for i, track in enumerate(dependency_analysis['parallel_tracks']):
        track_data = []
        for phase in track:
            track_data.append({
                "issue_id": phase.issue_id,
                "phase_number": phase.phase_number,
                "filename": phase.filename
            })
        data["parallel_tracks"].append(track_data)

    return json.dumps(data, indent=2)
```

**CLI update**:
```bash
./scripts/plan_phases.sh 49 52 104 --output-json > phase_metadata.json
```

#### B. Enhance `scripts/generate_prompt.py`

**Add phase context support**:
```python
def generate_with_phase_context(
    self,
    feature_id: int,
    phase_number: int = 1,
    total_phases: int = 1,
    depends_on: List[Tuple[int, int]] = None
) -> str:
    """Generate prompt with phase context."""

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
    output_path = Path.cwd() / filename
    output_path.write_text(prompt_content)

    return prompt_content
```

**CLI update**:
```bash
./scripts/gen_prompt.sh 104 --phase 2 --total-phases 3 --depends-on "104:1"
```

**Template modifications** when phase context provided:
```markdown
# Feature #104 - Phase 2 of 3: Backend Services

## Context
Load: `/prime`
Depends on: Phase 1 completion (#104 Phase 1)

## Task
Implement backend services for feature #104.

## Phase Overview
This is Phase 2 of 3 for Feature #104: Prompt Generator with Codebase Analysis

**Previous phases:**
- Phase 1: Database schema and repositories (COMPLETED)

**This phase:**
- Implement service layer
- Create API endpoints
- Add business logic

**Upcoming phases:**
- Phase 3: Frontend UI and integration

[... rest of template ...]
```

#### C. Create Orchestrator `scripts/orchestrate_prompts.sh`

**New script**:
```bash
#!/bin/bash
# Orchestrates full prompt generation workflow

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

ISSUE_IDS="$@"

echo "🔍 Step 1: Analyzing phases for issues: $ISSUE_IDS"
METADATA=$(./scripts/plan_phases.sh $ISSUE_IDS --output-json)

if [ $? -ne 0 ]; then
    echo "❌ Phase analysis failed"
    exit 1
fi

# Save metadata to temp file
TEMP_FILE=$(mktemp)
echo "$METADATA" > "$TEMP_FILE"

echo ""
echo "📝 Step 2: Generating prompts for each phase..."

# Parse JSON and generate prompts
# (Using Python to parse JSON reliably)
python3 <<EOF
import json
import subprocess
import sys

with open('$TEMP_FILE', 'r') as f:
    data = json.load(f)

total_prompts = 0
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
            print(f"❌ Failed to generate prompt for #{ issue_id} Phase {phase_num}", file=sys.stderr)
            sys.exit(1)
        total_prompts += 1

print(f"\n✅ Generated {total_prompts} prompt files")
EOF

if [ $? -ne 0 ]; then
    echo "❌ Prompt generation failed"
    rm "$TEMP_FILE"
    exit 1
fi

echo ""
echo "📊 Step 3: Creating coordination document..."

# Generate coordination doc from metadata
COORD_FILE=$(./scripts/create_coordination_doc.sh "$TEMP_FILE")

rm "$TEMP_FILE"

echo ""
echo "✅ Prompt generation complete!"
echo ""
echo "📄 Coordination Document: $COORD_FILE"
echo ""
echo "Next steps:"
echo "1. Review $COORD_FILE for execution sequence"
echo "2. Execute phases as shown in parallel tracks"
echo "3. Mark each phase complete before proceeding to next"
```

#### D. Create `/genprompts` Slash Command

**File**: `.claude/commands/genprompts.md`
```markdown
# Generate Implementation Prompts

Analyze issues, determine phase breakdown, and generate all implementation prompts.

## Variables
issue_ids: $@ (space-separated issue IDs, or empty for all planned)

## Instructions

Execute the unified prompt generation workflow:

```bash
./scripts/orchestrate_prompts.sh $@
```

This will:
1. **Analyze complexity** - Determine how many phases each issue needs
2. **Generate prompts** - Create implementation prompts for each phase
3. **Create coordination doc** - Show execution sequence and dependencies

## Output

You will receive:
- Individual prompt files (QUICK_WIN_*.md, FEATURE_*_PHASE_*.md)
- Coordination document (PHASE_PLAN_<timestamp>.md)
- Execution guidance (parallel tracks, dependencies)

## Examples

```bash
# Generate prompts for specific issues
/genprompts 49 52 55 57

# Generate prompts for all planned issues
/genprompts

# Generate prompts for a single complex feature
/genprompts 104
```

## What You Get

**For simple issues (≤2h):**
- Single prompt file: `QUICK_WIN_49_fix_error_handling.md`

**For complex features (>2h):**
- Multiple phase prompts:
  - `FEATURE_104_PHASE_1_database.md`
  - `FEATURE_104_PHASE_2_backend.md`
  - `FEATURE_104_PHASE_3_frontend.md`

**Coordination document:**
- Shows which phases can run in parallel
- Shows dependencies between phases
- Provides execution order
- Lists file modification conflicts

## Next Steps

After running this command:
1. Read the coordination document
2. Execute phases in the order shown
3. Use separate Claude Code contexts for parallel phases
4. Mark each phase complete in Plans Panel before proceeding
```

---

## File Structure Summary

```
scripts/
├── plan_phases.py              # Modified: Add --output-json flag
├── plan_phases.sh              # Modified: Pass --output-json to Python
├── generate_prompt.py          # Modified: Add phase context support
├── gen_prompt.sh               # Modified: Accept --phase, --total-phases flags
├── orchestrate_prompts.sh      # NEW: Main orchestration script
└── create_coordination_doc.sh  # NEW: Generate final coordination doc

.claude/
├── commands/
│   └── genprompts.md           # NEW: Slash command
└── templates/
    └── IMPLEMENTATION_PROMPT_TEMPLATE.md  # Modified: Phase-aware sections
```

---

## Testing Plan

### Test Case 1: Single Simple Issue
```bash
/genprompts 49

Expected:
- 1 prompt file: QUICK_WIN_49_*.md
- Coordination doc shows 1 phase, no dependencies
```

### Test Case 2: Multiple Simple Issues
```bash
/genprompts 49 52 55 57

Expected:
- 4 prompt files (all QUICK_WIN)
- Coordination doc shows 4 parallel tracks
- No dependencies between issues
```

### Test Case 3: Complex Multi-Phase Feature
```bash
/genprompts 104

Expected:
- 3 prompt files: FEATURE_104_PHASE_1/2/3_*.md
- Coordination doc shows sequential execution
- Phase 2 depends on Phase 1, Phase 3 depends on Phase 2
```

### Test Case 4: Mixed Complexity
```bash
/genprompts 49 52 104

Expected:
- 5 prompt files (2 QUICK_WIN + 3 FEATURE phases)
- Coordination doc shows parallel tracks for quick wins and Phase 1
- Sequential dependencies for Phase 2 and 3
```

### Test Case 5: Multiple Complex Features
```bash
/genprompts 72 99

Expected:
- 7 prompt files (2 phases for #72, 5 phases for #99)
- Coordination doc shows parallel execution where possible
- Proper dependency chains within each feature
```

---

## Success Criteria

- ✅ Single command generates all prompts for any number of issues
- ✅ Automatically determines phase breakdown based on complexity
- ✅ Phase prompts include context about dependencies
- ✅ Coordination document clearly shows execution order
- ✅ Parallel execution opportunities identified
- ✅ File modification conflicts highlighted
- ✅ Reuses existing templates and prompt generation logic
- ✅ Works for simple (1 phase) and complex (5 phase) features
- ✅ Output is ready for immediate execution in Claude Code

---

## Implementation Sequence

1. **Phase 1: Enhance plan_phases.py** (0.5h)
   - Add JSON output mode
   - Test JSON generation

2. **Phase 2: Enhance generate_prompt.py** (1h)
   - Add phase context parameters
   - Modify template filling logic
   - Test phase-aware prompt generation

3. **Phase 3: Create orchestrator** (1h)
   - Write orchestrate_prompts.sh
   - Create create_coordination_doc.sh
   - Test end-to-end workflow

4. **Phase 4: Create slash command** (0.25h)
   - Write .claude/commands/genprompts.md
   - Test command invocation

5. **Phase 5: Testing & Documentation** (0.5h)
   - Run all test cases
   - Verify output quality
   - Update documentation

**Total Estimated Time**: 3.25h

---

## Questions to Resolve

1. **Coordination doc location**: Should it determine execution order or just provide information?
   - **Decision**: Information only. Human reviews and decides execution order.

2. **Phase prompt content**: Should each phase prompt include full feature context or just that phase?
   - **Decision**: Full feature context + "Phase N of M" section showing what's before/after.

3. **Template modifications**: Modify existing template or create phase-specific template?
   - **Decision**: Modify existing template with conditional phase sections.

4. **Parallel execution**: How to indicate which phases can run in parallel?
   - **Decision**: Coordination doc shows "Track 1 (parallel)", "Track 2 (parallel)", etc.

---

## Next Steps for Implementation

**Immediate**:
- Review this design document
- Confirm approach is correct
- Identify any missing requirements

**Then**:
- Implement modifications in sequence (Phases 1-5 above)
- Test each phase before moving to next
- Create comprehensive test suite
- Document usage in README

**Future Enhancements** (out of scope for now):
- Auto-detection of which phases are actually needed based on file changes
- Integration with Plans Panel for automatic status updates
- Dependency validation (check if prerequisite phases are complete)
- Smart phase merging (combine small phases if beneficial)
