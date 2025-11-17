# Phase 2: Context Efficiency Analysis - Implementation Strategy

**Duration:** Week 1-2 (7 days)
**Dependencies:** Phase 1 complete (optional)
**Status:** Ready to implement
**Sub-Phases:** 2A, 2B, 2C (see below)

---

## Overview

Track what context (files, docs) was actually accessed during workflows vs what was loaded, enabling intelligent context reduction in future workflows.

**IMPORTANT:** This phase has been broken into 3 sub-phases for easier implementation. See detailed guides:
- **Phase 2A:** File Access Tracking (`PHASE_2A_FILE_ACCESS_TRACKING.md`)
- **Phase 2B:** Context Efficiency Analysis (`PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`)
- **Phase 2C:** Context Profile Builder (`PHASE_2C_CONTEXT_PROFILE_BUILDER.md`)

---

## Goals

1. ✅ Track file access during workflow execution
2. ✅ Calculate context efficiency metrics
3. ✅ Build context profiles per pattern
4. ✅ Generate recommendations for context optimization
5. ✅ Estimate token savings from smarter context loading

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  WORKFLOW EXECUTES                                    │
│  (Claude Code session running)                        │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  HOOK EVENTS CAPTURE                                  │
│  PreToolUse → PostToolUse                             │
│  Track: Read, Write, Edit, Grep, Glob                │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  hook_events TABLE                                    │
│  event_type: 'FileAccess'                             │
│  payload: {tool_name, file_path, access_type}         │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT ANALYZER                                     │
│  • Calculate files_loaded vs files_accessed           │
│  • Measure efficiency percentage                      │
│  • Estimate wasted tokens                             │
│  • Build context profile for pattern                  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT PROFILES                                     │
│  For pattern "test:pytest:backend":                   │
│    typical_files: ['app/server/**/*.py']              │
│    typical_docs: ['.claude/references/api.md']        │
│    avg_efficiency: 18.5%                              │
│    token_waste: 45000 tokens/workflow                 │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Recommended Implementation Path

**Week 1:**
- **Days 1-2:** Phase 2A - File Access Tracking
  - Implement hook integration
  - Verify events captured in database
  - See: `PHASE_2A_FILE_ACCESS_TRACKING.md`

- **Days 3-4:** Phase 2B - Context Efficiency Analysis
  - Build efficiency analyzer script
  - Calculate metrics for existing workflows
  - See: `PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`

- **Days 5-7:** Phase 2C - Context Profile Builder
  - Generate context profiles per pattern
  - Calculate token savings potential
  - See: `PHASE_2C_CONTEXT_PROFILE_BUILDER.md`

---

## Sub-Phase Overview

### Phase 2A: File Access Tracking (Days 1-2)
**Goal:** Capture which files are accessed during workflow execution

**Deliverables:**
- `app/server/core/context_tracker.py` (300 lines)
- `.claude/hooks/post_tool_use.py` (100 lines)
- Hook integration

**Success:** FileAccess events in database, linked to workflows

**→ Full details:** `PHASE_2A_FILE_ACCESS_TRACKING.md`

---

### Phase 2B: Context Efficiency Analysis (Days 3-4)
**Goal:** Calculate efficiency metrics and identify token waste

**Deliverables:**
- `scripts/analyze_context_efficiency.py` (200 lines)
- Efficiency reports per workflow/pattern

**Success:** Reports showing 15-20% efficiency, 40K+ token waste

**→ Full details:** `PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`

---

### Phase 2C: Context Profile Builder (Days 5-7)
**Goal:** Generate pattern-specific context loading recommendations

**Deliverables:**
- `app/server/core/context_optimizer.py` (400 lines)
- `scripts/generate_context_profiles.py` (100 lines)
- Context profiles for top patterns

**Success:** Profiles show 80%+ efficiency potential, 42K+ token savings

**→ Full details:** `PHASE_2C_CONTEXT_PROFILE_BUILDER.md`

---

## Legacy Implementation Steps (Consolidated View)

**NOTE:** For detailed implementation, use the sub-phase documents above.
This section provides a high-level overview only.

### Step 2.1: Create Context Tracker Module (Phase 2A)
**File:** `app/server/core/context_tracker.py`

**Key Functions:**
- `track_file_access()` - Record file access from hooks
- `calculate_context_efficiency()` - Analyze loaded vs accessed
- `build_context_profile()` - Pattern-specific recommendations
- `estimate_token_waste()` - Calculate wasted tokens

**Database Integration:**
- Store file access events in `hook_events` table
- Link to `workflow_id`
- Query for analysis

### Step 2.2: Hook Integration (Phase 2A)
**File:** `.claude/hooks/post_tool_use.py`

**Capture file access from tool use:**
```python
def hook(data):
    tool_name = data.get('tool_name')

    # Track file operations
    if tool_name in ['Read', 'Edit', 'Write', 'Grep', 'Glob']:
        record_file_access(
            session_id=data['session_id'],
            tool_name=tool_name,
            file_path=extract_file_path(data),
            access_type='read' if tool_name == 'Read' else 'write'
        )
```

### Step 2.3: Context Efficiency Analyzer (Phase 2B)
**File:** `scripts/analyze_context_efficiency.py`

**Calculate efficiency metrics for workflows and patterns**

→ See `PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md` for full implementation

### Step 2.4: Context Profile Builder (Phase 2C)
**File:** `app/server/core/context_optimizer.py`

**Aggregate file access across all workflows with same pattern:**
```python
def build_context_profile(pattern_signature: str) -> Dict:
    """
    Returns:
        {
            'typical_files': ['app/server/**/*.py', 'tests/**/*.py'],
            'typical_docs': ['.claude/references/api_endpoints.md'],
            'avg_files_loaded': 150,
            'avg_files_accessed': 25,
            'efficiency': 16.7,
            'token_waste_avg': 45000,
            'recommended_glob': 'app/server/**/*.py'
        }
    """
```

### Step 2.5: Generate Context Profiles (Phase 2C)
**File:** `scripts/generate_context_profiles.py`

**Generate profiles for all patterns:**
```bash
python scripts/generate_context_profiles.py --top 10

# Output:
# Analyzing: test:pytest:backend
#   Workflows: 12
#   Efficiency: 15.3% → 85.7%
#   Savings: 42,000 tokens/workflow
#
# Analyzing: build:npm:frontend
#   Workflows: 8
#   Efficiency: 18.2% → 88.9%
#   Savings: 38,500 tokens/workflow
```

→ See `PHASE_2C_CONTEXT_PROFILE_BUILDER.md` for full implementation

---

## Testing Strategy

**Phase 2A - File Access Tracking:**
```bash
# Run workflow and verify events captured
cd adws/
uv run adw_test_iso.py 42

sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) FROM hook_events WHERE event_type = 'FileAccess';
"
```

**Phase 2B - Efficiency Analysis:**
```bash
# Analyze workflow efficiency
python scripts/analyze_context_efficiency.py --workflow-id 42
python scripts/analyze_context_efficiency.py --pattern "test:pytest:backend"
```

**Phase 2C - Context Profiles:**
```bash
# Generate profiles
python scripts/generate_context_profiles.py --top 5
python scripts/generate_context_profiles.py --pattern "test:pytest:backend" --output profile.json
```

→ See individual sub-phase documents for detailed testing strategies

---

## Success Criteria

**Phase 2A:**
- [ ] ✅ File access events captured in hook_events table
- [ ] ✅ Events linked to session_id/workflow_id
- [ ] ✅ Hook fires for Read, Edit, Write, Grep, Glob tools

**Phase 2B:**
- [ ] ✅ Context efficiency calculated for workflows
- [ ] ✅ Token waste estimates generated
- [ ] ✅ Pattern-level aggregation working

**Phase 2C:**
- [ ] ✅ Context profiles built for top 5+ patterns
- [ ] ✅ Glob recommendations cover 90%+ of accessed files
- [ ] ✅ >40% efficiency improvement potential identified

**Overall Phase 2:**
- [ ] ✅ All three sub-phases complete
- [ ] ✅ Profiles ready for Phase 3 integration
- [ ] ✅ Token savings estimates validated

---

## Deliverables

**Phase 2A: File Access Tracking**
1. ✅ `app/server/core/context_tracker.py` (300 lines)
2. ✅ `.claude/hooks/post_tool_use.py` (100 lines)
3. ✅ Unit tests

**Phase 2B: Context Efficiency Analysis**
4. ✅ `scripts/analyze_context_efficiency.py` (200 lines)
5. ✅ Efficiency reports

**Phase 2C: Context Profile Builder**
6. ✅ `app/server/core/context_optimizer.py` (400 lines)
7. ✅ `scripts/generate_context_profiles.py` (100 lines)
8. ✅ Context profiles (JSON)

**Optional:**
9. ⭕ Context efficiency dashboard (if time permits)

**Total Lines of Code:** ~1,100 lines

→ See individual sub-phase documents for detailed specifications

---

## Expected Results

**Before optimization:**
- Test workflow loads: 150 files (54,000 tokens)
- Actually accesses: 25 files (9,000 tokens)
- Efficiency: 16.7%
- **Waste: 45,000 tokens per workflow**

**After optimization (Phase 3):**
- Load only: `app/server/**/*.py, tests/**/*.py` (30 files, 10,800 tokens)
- Accesses: 25 files (9,000 tokens)
- Efficiency: 83%
- **Savings: 43,200 tokens per workflow (80% reduction)**
