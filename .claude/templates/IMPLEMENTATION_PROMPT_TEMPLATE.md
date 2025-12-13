# [Type] #[ID]: [Title]

## LENGTH GUIDELINES

**Target prompt length based on task time:**
- 0.5h task: ~60-80 lines
- 1.0h task: ~100-120 lines
- 1.5h task: ~120-150 lines
- 2.0h+ task: ~150-200 lines max

**Keep it concise:**
- ❌ Don't write full code blocks (show key snippets only)
- ❌ Don't include exhaustive troubleshooting sections
- ❌ Don't explain obvious things
- ✅ DO provide concrete commands
- ✅ DO show critical logic points
- ✅ DO structure with clear workflow steps

**Example:** See `FEATURE_104_SESSION_1_BASIC_GENERATOR.md` (95 lines for 1h task)

---

## Context
Load: `/prime`
[Add dependencies if any: "Depends on: [prerequisite]"]

## Task
[One sentence describing what to build]

## Workflow

### 1. Investigate (X min)
```bash
# Verify current state
# Check dependencies
# Understand scope
```

### 2. Implement (X min)

**Key changes:**
- File/location to modify
- Core logic (brief code snippet if needed)
- Critical implementation points

```python
# Only show essential code snippets
# Not full implementations
```

### 3. Test (X min)
```bash
# Test commands
# Expected outcomes
```

### 4. Quality & Ship (X min)
```bash
# Linting
cd app/[client|server]
[Frontend: npx eslint ./src --fix]
[Backend: .venv/bin/ruff check . --fix]

# Type checking
[Frontend: npx tsc --noEmit]
[Backend: .venv/bin/mypy . --ignore-missing-imports]

# Full test suite
[Frontend: cd app/client && bun test]
[Backend: cd app/server && env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/ -v]

# Commit (NO AI REFERENCES)
git add [files]
git commit -m "[type]: [Short description]

Problem:
- [What was wrong]

Solution:
- [What changed]
- [Key decisions]

Result:
- [What works now]

Files:
- [file1] ([changes])

Location: [primary file]"

# Push to origin
git push origin main

# Update documentation (if applicable - see guidelines below)
[Run /updatedocs if new features/APIs/architecture changes]

# Cleanup prompt files
[For multi-phase features: Keep prompts until ALL phases complete]
[For single-phase/session features: Archive after completion]
mkdir -p docs/Archive/sessions/[session-name]
git mv FEATURE_[ID]_*.md docs/Archive/sessions/[session-name]/
git commit -m "chore: Archive Feature #[ID] prompt files"
git push origin main
```

## Success Criteria
- ✅ [Specific check 1]
- ✅ [Specific check 2]
- ✅ 0 linting/type errors
- ✅ All tests passing
- ✅ Changes pushed to origin
- ✅ Prompt files cleaned up

## Time: Xh

## Next
[Next phase/task if applicable]

---

## OPTIONAL SECTIONS (use sparingly)

### Problem Statement (only if complex)
**Current:** [What's wrong]
**Expected:** [What should happen]
**Impact:** [Why it matters]

### Files Modified (only if many files)
- `file1` - [changes]
- `file2` - [changes]

### /updatedocs Decision
**Run /updatedocs if:**
- New features/API endpoints
- Architecture changes
- Breaking changes

**Skip if:**
- Bug fixes
- Internal refactoring
- Test additions

---

## COMMIT MESSAGE FORMAT

```
[type]: [Short description - max 50 chars]

Problem:
- [What was wrong]
- [Why it mattered]

Solution:
- [What you changed]
- [How it solves the problem]

Result:
- [What works now]
- [Impact]

Files:
- [file1] ([brief description])
- [file2] ([brief description])

Location: [primary file]:[line numbers]
```

**Type options**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`

---

## CLEANUP GUIDELINES

### Prompt File Archiving

**When to archive:**
- ✅ Feature/session FULLY complete (all phases)
- ✅ Plans Panel marked as "completed"
- ✅ All commits pushed to origin
- ✅ Documentation updated

**Where to archive:**
```bash
# Session-based (FEATURE_104_SESSION_1, FEATURE_104_SESSION_2, etc.)
docs/Archive/sessions/feature-[id]-[short-name]/

# Phase-based (FEATURE_63_PHASE_1, FEATURE_63_PHASE_2, etc.)
docs/Archive/features/feature-[id]-[short-name]/
```

**Archive commands:**
```bash
# For session-based features (all sessions complete)
mkdir -p docs/Archive/sessions/feature-104-prompt-generator
git mv FEATURE_104_*.md docs/Archive/sessions/feature-104-prompt-generator/
git commit -m "chore: Archive Feature #104 prompt files (3 sessions complete)"
git push origin main

# For phase-based features (all phases complete)
mkdir -p docs/Archive/features/feature-63-pattern-validation
git mv FEATURE_63_*.md docs/Archive/features/feature-63-pattern-validation/
git commit -m "chore: Archive Feature #63 prompt files (3 phases complete)"
git push origin main

# For single-phase features/bugs/quick-wins
mkdir -p docs/Archive/features/feature-[id]-[short-name]
git mv FEATURE_[ID]_*.md QUICK_WIN_[ID]_*.md docs/Archive/features/feature-[id]-[short-name]/
git commit -m "chore: Archive Feature #[ID] prompt files"
git push origin main
```

**DO NOT archive:**
- ❌ Prompts for incomplete multi-phase features
- ❌ Tracking files (TRACKING_*.md, HANDOFF_*.md)
- ❌ Reference documentation

---

## PLANS PANEL UPDATES

**Mark in progress:**
```bash
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'
```

**Mark completed:**
```bash
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": [X.X],
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completion_notes": "[Brief summary]"
  }'
```
