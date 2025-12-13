# [Type] #[ID]: [Title]

## Task Summary
**Issue**: [One-line description]
**Priority**: [High/Medium/Low]
**Type**: [Bug/Feature/Enhancement/Session]
**Estimated Time**: [X hours]
**Status**: Planned → In Progress

## Problem Statement

### Current Behavior
[Describe what's happening now - include evidence from codebase]

### Expected Behavior
[Describe what should happen]

### Impact
[Why this matters - user impact, technical debt, etc.]

## Root Cause
[Technical explanation of why the problem exists]

## Solution

### Overview
[High-level solution approach in 2-3 sentences]

### Technical Details
[Detailed implementation steps with code examples]

## Implementation Steps

### Step 1: Investigation & Setup
```bash
# Verify current state
# Check relevant files
# Understand the scope
```

### Step 2-N: Implementation
[Detailed steps with commands and code changes]

### Final Step: Verification Checklist

**Pre-Commit Checklist**:
```bash
# 1. Linting
cd /Users/Warmonger0/tac/tac-webbuilder/app/[client|server]
[Frontend: npx eslint ./src --fix]
[Backend: ruff check . --fix]

# 2. Type checking
[Frontend: npx tsc --noEmit]
[Backend: mypy . --ignore-missing-imports]

# 3. Tests
[Frontend: bun test]
[Backend: POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/ -v]

# 4. Build (if frontend)
[Frontend: bun run build]

# 5. Manual testing
[Start servers and verify functionality]

# 6. Update Plans Panel
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'

# 7. Commit with professional message (NO AI REFERENCES)
git add [files]
git commit -m "[type]: [description]

[Problem/Solution/Result format - see template below]"

# 8. Update documentation
/updatedocs

# 9. Mark Plans Panel as completed
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": [X.X],
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completion_notes": "[Brief summary of what was done]"
  }'
```

## Success Criteria

### Code Quality
- ✅ **Linting**: 0 errors, 0 warnings
- ✅ **Type Safety**: 0 TypeScript/mypy errors
- ✅ **Tests**: All existing tests pass, new tests added for new functionality
- ✅ **Build**: Successful build (frontend if applicable)

### Functionality
- ✅ **Feature Works**: Manual testing confirms expected behavior
- ✅ **No Regressions**: Existing features still work
- ✅ **Edge Cases**: Handled appropriately

### Documentation & Tracking
- ✅ **Plans Panel Updated**: Status changed to completed, actual hours recorded
- ✅ **Documentation Updated**: /updatedocs run if needed (see guidelines below)
- ✅ **Commit Message**: Professional, no AI references, clear problem/solution/result

### /updatedocs Guidelines

**When to run /updatedocs:**

YES - Always update docs for:
- New features that users/developers will interact with
- New API endpoints or significant endpoint changes
- Architecture changes
- New workflows or ADWs
- Configuration changes
- Breaking changes

NO - Skip docs update for:
- Bug fixes (unless they change usage patterns)
- Internal refactoring
- Minor UI tweaks
- Code quality improvements (linting, typing)
- Test additions

**If unsure**: Run `/updatedocs` and let it analyze whether updates are needed.

## Commit Message Template

```
[type]: [Short description - max 50 chars]

[Detailed description of the problem]

Problem:
- [What was wrong]
- [Why it mattered]
- [What triggered this work]

Solution:
- [What you changed]
- [How it solves the problem]
- [Key technical decisions]

Result:
- [What works now]
- [Performance/quality improvements]
- [Any remaining work]

Files Changed:
- [file1] ([brief description])
- [file2] ([brief description])

[If applicable]
Testing:
- [Test results]
- [Coverage improvements]

Location: [primary file]:[line numbers]
```

**Type options**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`

## Files Modified

### Expected Changes
- `[file1]` - [description]
- `[file2]` - [description]

### New Files (if any)
- `[file1]` - [description]

## Testing Strategy

### Unit Tests
```bash
# Test specific functionality
[Test commands]
```

### Integration Tests
```bash
# Test component interactions
[Test commands]
```

### E2E/Manual Tests
```bash
# User-facing verification
[Steps to verify]
```

## Expected Time Breakdown
- **Investigation**: [X] minutes
- **Implementation**: [X] minutes
- **Testing**: [X] minutes
- **Documentation**: [X] minutes
- **Linting/Quality**: [X] minutes
- **Commit/Cleanup**: [X] minutes

**Total**: [X] hours ✅

## Session Summary Template

After completion, provide this summary:

```markdown
# Session Summary: [Type] #[ID] - [Title] ✅

## What Was Done
- [Change 1]
- [Change 2]
- [Change 3]

## Results
- ✅ Linting: [X errors → 0, X warnings → 0]
- ✅ Type Safety: [X errors → 0]
- ✅ Tests: [X passing, Y added]
- ✅ Build: [Success/N/A]
- ✅ Documentation: [Updated via /updatedocs / No update needed]
- ✅ Plans Panel: [#ID] updated (planned → completed, [X]h actual)

## Files Changed
1. [file1] ([description])
2. [file2] ([description])

## Testing
- [Test results]
- [Manual verification]

## Documentation Updates
[If /updatedocs run, summarize changes]
[If skipped, explain why per guidelines]

## Time Spent
Approximately [X] hours ([within/under/over] estimate)

## Next Task
#[NextID]: [Next task title] ([Xh], [priority], [type])
```

---

## Quick Reference Commands

```bash
# Project root
cd /Users/Warmonger0/tac/tac-webbuilder

# Frontend linting
cd app/client && npx eslint ./src --fix

# Frontend type check
cd app/client && npx tsc --noEmit

# Frontend tests
cd app/client && bun test

# Frontend build
cd app/client && bun run build

# Backend linting
cd app/server && ruff check . --fix

# Backend type check
cd app/server && mypy . --ignore-missing-imports

# Backend tests
cd app/server && POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/ -v

# Update Plans Panel (in progress)
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] -H "Content-Type: application/json" -d '{"status": "in_progress", "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'

# Update Plans Panel (completed)
curl -X PATCH http://localhost:8002/api/v1/planned-features/[ID] -H "Content-Type: application/json" -d '{"status": "completed", "actual_hours": [X.X], "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "completion_notes": "[summary]"}'

# Update documentation
/updatedocs

# Start backend
cd app/server && .venv/bin/python3 server.py

# Start frontend
cd app/client && bun run dev
```
