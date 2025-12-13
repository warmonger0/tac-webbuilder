# Feature #106: #106: Auto-Workflow Launcher

## Task Summary
**Issue**: Auto-inject generated prompt into request form or API. Launch appropriate ADW workflow with correct parameters (model, timeout, cost limits). Return control to user with workflow tracking link.
**Priority**: High
**Type**: Feature
**Estimated Time**: 1.5
**Status**: Planned → In Progress

## Codebase Context (Auto-Generated)

### Relevant Backend Files

- `app/server/core/nl_processor.py` (relevance: 12.0)
- `app/server/routes/workflow_routes.py` (relevance: 11.5)
- `app/server/repositories/user_prompt_repository.py` (relevance: 11.0)
- `app/server/services/github_issue_service.py` (relevance: 11.0)
- `app/server/tests/integration/conftest.py` (relevance: 11.0)
- `app/server/tests/e2e/test_github_issue_flow.py` (relevance: 10.0)
- `app/server/tests/services/test_phase_coordinator.py` (relevance: 10.0)
- `app/server/tests/conftest.py` (relevance: 9.5)
- `app/server/utils/llm_client.py` (relevance: 9.5)
- `app/server/core/models/requests.py` (relevance: 9.5)

### Relevant Frontend Files

- `app/client/src/components/RequestFormCore.tsx` (relevance: 16.0)
- `app/client/src/components/__tests__/RequestForm.test.tsx` (relevance: 16.0)
- `app/client/src/components/RequestFormHooks.tsx` (relevance: 14.5)
- `app/client/src/components/RequestForm.tsx` (relevance: 11.0)
- `app/client/src/components/RequestFormPreview.tsx` (relevance: 11.0)
- `app/client/src/components/SimilarWorkflowsComparison.tsx` (relevance: 9.5)
- `app/client/src/workflows.ts` (relevance: 9.0)
- `app/client/src/components/AdwWorkflowCatalog.tsx` (relevance: 9.0)
- `app/client/src/types/api.types.ts` (relevance: 8.5)
- `app/client/src/api/workflowClient.ts` (relevance: 8.5)

### Related Functions

- `get_workflows_data()` in `app/server/server.py`
- `get_workflow_history_data()` in `app/server/server.py`
- `format_preview()` in `app/server/core/github_poster.py`
- `_detect_formatter()` in `app/server/core/pattern_signatures.py`
- `format_issue()` in `app/server/core/issue_formatter.py`
- `format_requirements_list()` in `app/server/core/issue_formatter.py`
- `format_technical_approach()` in `app/server/core/issue_formatter.py`
- `format_workflow_section()` in `app/server/core/issue_formatter.py`
- `suggest_workflow()` in `app/server/core/project_detector.py`
- `validate_repo_format()` in `app/server/core/config.py`
- `extract_explicit_workflow()` in `app/server/core/nl_processor.py`
- `suggest_adw_workflow()` in `app/server/core/nl_processor.py`
- `format_script_result_for_llm()` in `app/server/core/pattern_matcher.py`
- `format_test_results()` in `app/server/core/pattern_matcher.py`
- `format_build_results()` in `app/server/core/pattern_matcher.py`

### Suggested Test Files

- `app/server/tests/core/test_nl_processor.py` (may need creation)
- `app/server/tests/routes/test_workflow_routes.py` (may need creation)
- `app/server/tests/repositories/test_user_prompt_repository.py` (may need creation)
- `app/server/tests/services/test_github_issue_service.py` (may need creation)
- `app/server/tests/tests/integration/test_conftest.py` (may need creation)
- `app/client/src/components/RequestFormCore.test.tsx` (may need creation)
- `app/client/src/components/RequestFormHooks.test.tsx` (may need creation)
- `app/client/src/components/RequestForm.test.tsx` (may need creation)
- `app/client/src/components/RequestFormPreview.test.tsx` (may need creation)

### Implementation Suggestions

- Modify existing: app/server/core/nl_processor.py
- Modify existing: app/client/src/components/RequestFormCore.tsx


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
curl -X PATCH http://localhost:8002/api/v1/planned-features/106 \
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
curl -X PATCH http://localhost:8002/api/v1/planned-features/106 \
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
# Session Summary: Feature #106 - #106: Auto-Workflow Launcher ✅

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
curl -X PATCH http://localhost:8002/api/v1/planned-features/106 -H "Content-Type: application/json" -d '{"status": "in_progress", "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'

# Update Plans Panel (completed)
curl -X PATCH http://localhost:8002/api/v1/planned-features/106 -H "Content-Type: application/json" -d '{"status": "completed", "actual_hours": [X.X], "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "completion_notes": "[summary]"}'

# Update documentation
/updatedocs

# Start backend
cd app/server && .venv/bin/python3 server.py

# Start frontend
cd app/client && bun run dev
```
