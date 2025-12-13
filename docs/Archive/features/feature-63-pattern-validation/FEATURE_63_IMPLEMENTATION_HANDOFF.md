# Feature #63: Pattern Validation Loop - Implementation Context

## Context
Load: `/prime`

## Your Role
Analyze this feature, break it into implementation phases, and create phase-specific prompts following our template workflow structure.

## Source Material
Read the full implementation plan:
- `docs/implementation/PATTERN_VALIDATION_LOOP_IMPLEMENTATION.md`
- `docs/implementation/MIGRATION_010_VERIFICATION.md`

## Your Tasks

### 1. Analyze Complexity (10 min)
- Review the implementation plan
- Identify natural phase boundaries
- Determine dependencies between phases
- Estimate time per phase

### 2. Break Into Phases (15 min)
Create 2-4 phase prompts, each following our template:
- Phase should be 0.5-1.5h max
- Each phase = discrete, testable deliverable
- Clear dependencies (Phase N requires Phase N-1 complete)

### 3. Generate Phase Prompts (20 min)
For each phase, create a structured prompt:

```markdown
# Feature #63 Phase N: [Phase Name]

## Context
Load: `/prime`
Depends on: [Previous phase or "None"]

## Task
[One-line objective]

## Workflow

### 1. Investigate (X min)
[Verify dependencies, check existing code]

### 2. Implement (X min)
[Core changes with specific file/line references]

### 3. Test (X min)
[Validation commands]

### 4. Quality (X min)
[Linting, commit, partial progress update]

## Success Criteria
[Clear checklist]

## Time: Xh
```

### 4. Return Phase Summary (5 min)
Provide a summary table:

```
Feature #63: Pattern Validation Loop (3.0h total)

Phase 1: [Name] (Xh)
- Deliverable: [What gets built]
- Depends on: None
- Files: [List]

Phase 2: [Name] (Xh)
- Deliverable: [What gets built]
- Depends on: Phase 1 complete
- Files: [List]

...

Total Phases: N
Total Time: 3.0h
```

## Key Constraints

### Must Follow Template
- Use IMPLEMENTATION_PROMPT_TEMPLATE.md structure
- Each phase: Investigate → Implement → Test → Quality
- Include pre-commit checklist
- Professional commits (NO AI references)

### Phase Guidelines
- Max 1.5h per phase
- Each phase must be independently testable
- Partial progress tracked in Plans Panel (don't mark complete until all phases done)
- Return to coordination chat with summary after each phase

### Technical Context
**What exists:**
- ✅ `pattern_predictor.py` - Predicts patterns at submission
- ✅ `pattern_detector.py` - Detects patterns after completion
- ✅ Migration 010 - Database schema ready
- ✅ `pattern_predictions` table
- ✅ `operation_patterns` table

**What's missing (build this):**
- ❌ `pattern_validator.py` - Compare predicted vs actual
- ❌ Workflow completion hook - Trigger validation
- ❌ Analytics queries - Report accuracy
- ❌ Tests - Validate the validator

## Expected Output

Return to coordination chat with:

1. **Phase breakdown summary** (table format above)
2. **Phase prompt files** (FEATURE_63_PHASE_N_*.md)
3. **Implementation order** (which phase to start with)
4. **Any questions or concerns** about the breakdown

Then await instruction to proceed with Phase 1.

## Success Criteria

- ✅ 2-4 distinct phases identified
- ✅ Each phase ≤1.5h
- ✅ Phase prompts follow template structure
- ✅ Clear dependencies mapped
- ✅ Total time = 3.0h ±0.5h
- ✅ Ready to implement Phase 1 immediately

## Time for This Analysis: 0.5h (30 min)

---

**Note**: You are NOT implementing #63 yet. You are analyzing and creating the phase prompts. Implementation happens after coordination chat approval.
