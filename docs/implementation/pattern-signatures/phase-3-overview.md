# Phase 3: Automated Tool Routing - Overview & Guide

**Duration:** Week 2 (5-7 days)
**Dependencies:** Phase 1 complete (patterns detected)
**Priority:** HIGH - Delivers immediate cost savings
**Status:** Ready to implement

---

## ⚠️ Phase 3 has been split into 3 sub-phases for easier implementation

The original Phase 3 document (`PHASE_3_TOOL_ROUTING.md`) contains 1,322 lines and ~1,300 lines of code. To make implementation more manageable, it has been broken into **3 sequential sub-phases**:

---

## Sub-Phase Breakdown

### Phase 3A: Pattern Matching Foundation
**File:** [`PHASE_3A_PATTERN_MATCHING.md`](PHASE_3A_PATTERN_MATCHING.md)
**Duration:** 1-2 days
**Lines of Code:** ~650

**What you'll build:**
- Core pattern matching module (query and similarity logic only)
- Unit tests for pattern matching
- Standalone test script

**Deliverables:**
- `app/server/core/pattern_matcher.py` (matching functions)
- `app/server/tests/test_pattern_matcher.py`
- `scripts/test_pattern_matching.py`

**Why separate?** Test the matching logic thoroughly before adding execution complexity.

---

### Phase 3B: Tool Registration & Activation
**File:** [`PHASE_3B_TOOL_REGISTRATION.md`](PHASE_3B_TOOL_REGISTRATION.md)
**Duration:** 1 day
**Lines of Code:** ~400

**What you'll build:**
- Tool registration system
- Pattern-to-tool linking scripts
- Pattern activation workflow

**Deliverables:**
- `scripts/register_tools.py`
- `scripts/link_patterns_to_tools.py`
- `scripts/activate_patterns.py`

**Why separate?** Tool registration is one-time setup that can be validated independently.

---

### Phase 3C: ADW Integration & Routing
**File:** [`PHASE_3C_ADW_INTEGRATION.md`](PHASE_3C_ADW_INTEGRATION.md)
**Duration:** 2-3 days
**Lines of Code:** ~900

**What you'll build:**
- Tool execution logic (subprocess + error handling)
- Full routing workflow with fallback
- Cost savings tracking
- ADW executor integration

**Deliverables:**
- `app/server/core/pattern_matcher.py` (execution functions)
- Modified `adws/adw_sdlc_iso.py`
- `scripts/test_tool_routing.py`

**Why separate?** This is the most complex part with external dependencies and error handling.

---

## Implementation Order

```
START
  │
  ├─► Phase 3A: Pattern Matching Foundation (Days 1-2)
  │   │
  │   ├─ Implement match_input_to_pattern()
  │   ├─ Implement calculate_input_similarity()
  │   ├─ Write unit tests
  │   └─ Validate with standalone test script
  │
  ├─► Phase 3B: Tool Registration & Activation (Day 3)
  │   │
  │   ├─ Run register_tools.py
  │   ├─ Run link_patterns_to_tools.py
  │   ├─ Run activate_patterns.py
  │   └─ Verify database state
  │
  └─► Phase 3C: ADW Integration & Routing (Days 4-5)
      │
      ├─ Add route_to_tool() and execute_tool_script()
      ├─ Add should_fallback_to_llm() and log_cost_savings()
      ├─ Integrate with adw_sdlc_iso.py
      ├─ Test end-to-end routing
      └─ Verify cost savings tracking

END: Tool routing operational
```

---

## Quick Start

### Day 1-2: Pattern Matching

```bash
# Read the guide
cat docs/implementation/PHASE_3A_PATTERN_MATCHING.md

# Implement pattern_matcher.py (matching functions only)
# Write unit tests
# Run tests

cd app/server
uv run pytest tests/test_pattern_matcher.py -v

# Run standalone test
python scripts/test_pattern_matching.py
```

### Day 3: Tool Registration

```bash
# Read the guide
cat docs/implementation/PHASE_3B_TOOL_REGISTRATION.md

# Register tools
python scripts/register_tools.py

# Link patterns to tools
python scripts/link_patterns_to_tools.py

# Activate patterns
python scripts/activate_patterns.py

# Verify database
sqlite3 app/server/db/workflow_history.db "
SELECT pattern_signature, tool_name, automation_status
FROM operation_patterns
WHERE automation_status = 'active';
"
```

### Day 4-5: Full Integration

```bash
# Read the guide
cat docs/implementation/PHASE_3C_ADW_INTEGRATION.md

# Complete pattern_matcher.py (add execution functions)
# Modify adw_sdlc_iso.py
# Test integration

python scripts/test_tool_routing.py

# Test with real issue
gh issue create --title "Test: Run backend tests" --body "Run the backend test suite"
cd adws && uv run python adw_sdlc_iso.py <ISSUE_NUMBER>
```

---

## Goals (Overall Phase 3)

1. ✅ Build pattern matching engine that queries operation_patterns table
2. ✅ Implement tool routing logic with fallback to LLM
3. ✅ Register existing external tools (test, build, etc.)
4. ✅ Integrate into ADW workflow executor
5. ✅ Track cost savings in real-time
6. ✅ Ensure graceful degradation on tool failures

---

## Success Criteria (Overall Phase 3)

After completing all 3 sub-phases:

- [ ] ✅ Pattern matcher returns high-confidence matches (>=70%)
- [ ] ✅ Tool routing executes external tools successfully
- [ ] ✅ Cost savings tracked in cost_savings_log table
- [ ] ✅ Fallback to LLM works on tool failures
- [ ] ✅ 40%+ of test/build operations auto-routed within 1 week
- [ ] ✅ No regressions in workflow success rate
- [ ] ✅ Average token savings: 45,000+ per routed workflow

---

## Benefits of This Breakdown

### 1. **Incremental Progress**
- Each sub-phase delivers testable value
- Can pause/resume between phases
- Easier to track progress

### 2. **Reduced Complexity**
- Smaller code chunks to review
- Focused testing per phase
- Clearer debugging

### 3. **Risk Mitigation**
- Find issues early in simple phases
- Don't commit to full integration until foundations are solid
- Easier rollback if needed

### 4. **Better Testing**
- Test matching logic in isolation (3A)
- Test registration system independently (3B)
- Test integration with all pieces working (3C)

---

## File Structure After Phase 3

```
app/server/
├── core/
│   └── pattern_matcher.py        # Created in 3A, completed in 3C
└── tests/
    └── test_pattern_matcher.py   # Created in 3A

adws/
└── adw_sdlc_iso.py               # Modified in 3C

scripts/
├── test_pattern_matching.py      # Created in 3A
├── register_tools.py             # Created in 3B
├── link_patterns_to_tools.py     # Created in 3B
├── activate_patterns.py          # Created in 3B
└── test_tool_routing.py          # Created in 3C

docs/implementation/
├── PHASE_3_OVERVIEW.md           # This file
├── PHASE_3A_PATTERN_MATCHING.md  # Day 1-2 guide
├── PHASE_3B_TOOL_REGISTRATION.md # Day 3 guide
├── PHASE_3C_ADW_INTEGRATION.md   # Day 4-5 guide
└── PHASE_3_TOOL_ROUTING.md       # Original comprehensive doc
```

---

## Documentation Relationship

```
PHASE_3_OVERVIEW.md (this file)
  │
  │  Start here for phase breakdown and order
  │
  ├─► PHASE_3A_PATTERN_MATCHING.md
  │   Detailed implementation guide for pattern matching
  │
  ├─► PHASE_3B_TOOL_REGISTRATION.md
  │   Detailed implementation guide for tool registration
  │
  ├─► PHASE_3C_ADW_INTEGRATION.md
  │   Detailed implementation guide for ADW integration
  │
  └─► PHASE_3_TOOL_ROUTING.md (original)
      Comprehensive reference with all code in one place
      Use for understanding overall architecture
```

---

## When to Use Which Document

### Use PHASE_3_OVERVIEW.md (this file) when:
- Starting Phase 3 implementation
- Need to understand sub-phase breakdown
- Planning your implementation schedule
- Checking progress across all sub-phases

### Use PHASE_3A/3B/3C documents when:
- Actually implementing code
- Need step-by-step instructions
- Writing tests
- Troubleshooting specific sub-phase

### Use PHASE_3_TOOL_ROUTING.md when:
- Need complete architecture overview
- Want to see all code in one place
- Understanding data flow
- Reference for design decisions

---

## Total Effort

### Lines of Code
- **Phase 3A:** ~650 lines
- **Phase 3B:** ~400 lines
- **Phase 3C:** ~900 lines
- **Total:** ~1,950 lines

### Time Estimate
- **Phase 3A:** 1-2 days (foundation)
- **Phase 3B:** 1 day (setup)
- **Phase 3C:** 2-3 days (integration)
- **Total:** 5-7 days

---

## Next Steps After Phase 3

Once all 3 sub-phases are complete:

1. **Monitor for 1 week**
   - Track routing success rate
   - Measure actual token savings
   - Review cost_savings_log

2. **Adjust thresholds**
   - Fine-tune confidence thresholds
   - Add more trigger keywords if needed
   - Activate more patterns

3. **Proceed to Phase 4**
   - Auto-discovery of new patterns
   - Automated recommendations
   - GitHub issue creation

---

## Support

If you encounter issues:

1. **Check the troubleshooting section** in the specific sub-phase document
2. **Review database state** with provided SQL queries
3. **Run test scripts** to validate each component
4. **Check logs** for detailed error messages

---

## Summary

Phase 3 has been split into 3 manageable sub-phases to:
- Reduce implementation complexity
- Enable incremental testing
- Make progress tracking easier
- Minimize integration risks

**Start with Phase 3A** and work through sequentially. Each sub-phase document provides complete implementation guidance.

**Good luck with your implementation!** 🚀
