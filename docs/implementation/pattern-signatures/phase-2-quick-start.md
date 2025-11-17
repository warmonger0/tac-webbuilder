# Phase 2 Quick Start Guide

**Goal:** Identify and measure context efficiency to enable 80% token reduction in Phase 3

**Duration:** 7 days (split into 3 sub-phases)

---

## Why Phase 2 Was Split

Phase 2 involves multiple distinct components that can be built and tested independently:

1. **Capture** file access (Phase 2A)
2. **Analyze** efficiency (Phase 2B)
3. **Optimize** recommendations (Phase 2C)

Each sub-phase delivers incremental value and has clear dependencies.

---

## Implementation Path

### Day 1-2: Phase 2A - File Access Tracking
**File:** `PHASE_2A_FILE_ACCESS_TRACKING.md`

**What you'll build:**
- Hook integration to capture file access
- Context tracker module
- Database event storage

**Success check:**
```bash
# Run workflow
cd adws/ && uv run adw_test_iso.py 42

# Verify events captured
sqlite3 app/server/db/workflow_history.db "
SELECT COUNT(*) FROM hook_events WHERE event_type = 'FileAccess';
"
# Should show > 0
```

**Deliverables:**
- `app/server/core/context_tracker.py` (300 lines)
- `.claude/hooks/post_tool_use.py` (100 lines)

---

### Day 3-4: Phase 2B - Context Efficiency Analysis
**File:** `PHASE_2B_CONTEXT_EFFICIENCY_ANALYSIS.md`

**What you'll build:**
- Efficiency analyzer script
- Token waste calculation
- Pattern-level aggregation

**Success check:**
```bash
# Analyze workflow
python scripts/analyze_context_efficiency.py --workflow-id 42

# Should show:
# Files loaded: 150
# Files accessed: 25
# Efficiency: 16.7%
# Token waste: 45,000
```

**Deliverables:**
- `scripts/analyze_context_efficiency.py` (200 lines)

---

### Day 5-7: Phase 2C - Context Profile Builder
**File:** `PHASE_2C_CONTEXT_PROFILE_BUILDER.md`

**What you'll build:**
- Context optimizer module
- Glob pattern generator
- Token savings calculator

**Success check:**
```bash
# Generate profiles
python scripts/generate_context_profiles.py --top 5

# Should show for each pattern:
# Recommended globs: ['app/server/**/*.py', ...]
# Coverage: 95.8%
# Token savings: 42,000/workflow
```

**Deliverables:**
- `app/server/core/context_optimizer.py` (400 lines)
- `scripts/generate_context_profiles.py` (100 lines)

---

## Dependencies

```
Phase 2A (File Access Tracking)
    ↓
Phase 2B (Efficiency Analysis)
    ↓
Phase 2C (Context Profiles)
    ↓
Phase 3 (Tool Routing - uses profiles)
```

**Note:** Phase 2A must complete before 2B, and 2B before 2C.

---

## Expected Results

**Before optimization (current state):**
- Test workflow loads: 150 files (54,000 tokens)
- Actually accesses: 25 files (9,000 tokens)
- Efficiency: 16.7%
- Waste: 45,000 tokens per workflow

**After Phase 2 (recommendations):**
- Recommended globs: `app/server/**/*.py`, `tests/**/*.py`
- Coverage: 95%+
- Predicted efficiency: 85%+
- Predicted savings: 42,000+ tokens per workflow

**After Phase 3 (implementation):**
- Actual efficiency: 80-90% (validated)
- Actual savings: 40,000+ tokens per workflow

---

## Common Issues

### Phase 2A: No events captured
**Fix:** Check hook enabled in `.claude/config.yaml`

### Phase 2B: Efficiency always 0%
**Fix:** Verify Phase 2A working, check file access events exist

### Phase 2C: Coverage too low
**Fix:** Adjust glob generation to be more inclusive

---

## Quick Commands

```bash
# Phase 2A - Test tracking
cd adws/ && uv run adw_test_iso.py 42
sqlite3 app/server/db/workflow_history.db "SELECT COUNT(*) FROM hook_events WHERE event_type = 'FileAccess';"

# Phase 2B - Analyze efficiency
python scripts/analyze_context_efficiency.py --workflow-id 42
python scripts/analyze_context_efficiency.py --pattern "test:pytest:backend"

# Phase 2C - Generate profiles
python scripts/generate_context_profiles.py --top 10
python scripts/generate_context_profiles.py --pattern "test:pytest:backend" --output profile.json
```

---

## Total Effort

- **Lines of code:** ~1,100
- **Time:** 7 days (12-18 hours coding)
- **Testing:** Built into each sub-phase

---

## Next Steps

After completing all three sub-phases:
→ **Phase 3: Tool Routing** - Implement the recommendations from Phase 2C

---

**Read detailed implementation guides in the individual sub-phase documents!**
