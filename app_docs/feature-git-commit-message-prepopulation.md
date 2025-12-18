# Feature: Pre-populate Git Commit Messages in Plans Panel

## Overview

Add intelligent commit message pre-population in Panel 5 (Plans Panel) based on git status and current in-progress features. When "Check Status" finds uncommitted changes, automatically suggest a thoughtful commit message following conventional commit format.

## Status

- **Type**: Feature Enhancement
- **Status**: Planned
- **Priority**: Medium
- **Estimated Effort**: 2 hours
- **Tags**: frontend, git, plans-panel, ux-enhancement

## Problem Statement

Currently, the Git Commit UI exists in Panel 1 (System Status) and requires users to manually type commit messages. Users working on planned features in Panel 5 have to:
1. Switch to Panel 1 to commit
2. Manually write commit messages without context
3. No connection between the planned feature and the commit

This creates friction and results in less descriptive commit messages.

## Proposed Solution

### User Flow

1. **User is working on a planned feature** in Panel 5 (e.g., "Fix N+1 query patterns")
2. **Feature is marked "in_progress"** in the Plans panel
3. **User clicks "Check Status"** (new button in Plans panel)
4. **System detects uncommitted changes** via git status
5. **System generates thoughtful commit message** based on:
   - Changed files (frontend/backend/docs)
   - Current in-progress feature context
   - Conventional commit format (feat/fix/perf/docs/etc.)
6. **Pre-populated message appears** in editable textarea
7. **User reviews/edits** the suggestion
8. **User clicks "Commit"** to finalize

### Example Generated Messages

**Scenario 1: Backend performance work**
```
Feature: "Fix N+1 query patterns"
Changed files: app/server/routes/queue_routes.py, app/server/repositories/phase_queue_repository.py

Generated message:
perf: Fix N+1 query patterns in queue routes

Replace inefficient get_all() + loop with direct find_by_id() queries.
Uses database indexes for O(1) lookups instead of O(n) scanning.
```

**Scenario 2: Frontend UI enhancement**
```
Feature: "Add Git commit UI to system status"
Changed files: app/client/src/components/GitCommitPanel.tsx, app/client/src/components/SystemStatusPanel.tsx

Generated message:
feat: Add Git commit UI panel to system status dashboard

New GitCommitPanel component with check status and commit functionality.
Integrated into SystemStatusPanel for quick access.
```

**Scenario 3: Documentation update**
```
Feature: None (no in-progress feature)
Changed files: app_docs/feature-git-commit-ui.md

Generated message:
docs: Add Git commit UI feature documentation

Document GitCommitPanel component and system status integration.
```

## Technical Design

### Architecture Option: Frontend-Only (Recommended for MVP)

**Advantages:**
- No backend changes required
- Fast to implement (2 hours)
- Works with existing git status endpoint
- Can be enhanced later

**Components:**

1. **New Git Section in PlansPanel**
   - Location: `app/client/src/components/PlansPanel.tsx`
   - Add collapsible "Development Tools" section
   - Include "Check Status" button
   - Display git status summary
   - Show pre-populated commit message

2. **Message Generation Logic (Frontend)**
   - Analyze git status response (changed files)
   - Check current in-progress features
   - Classify change type (frontend/backend/docs)
   - Generate conventional commit message
   - Format: `type(scope): description\n\ndetails`

3. **Integration with Existing API**
   - Use existing `GET /api/v1/git/status` endpoint
   - Use existing `POST /api/v1/git/commit` endpoint
   - Use existing PlannedFeatures WebSocket context

### Message Generation Algorithm

```typescript
function generateCommitMessage(
  gitStatus: GitStatusResponse,
  inProgressFeatures: PlannedFeature[]
): string {
  // 1. Classify change type
  const changedFiles = [...gitStatus.staged, ...gitStatus.unstaged];
  const type = classifyChangeType(changedFiles);

  // 2. Determine scope
  const scope = determineScope(changedFiles, inProgressFeatures[0]);

  // 3. Generate subject line
  const subject = generateSubject(type, scope, inProgressFeatures[0]);

  // 4. Generate body
  const body = generateBody(changedFiles, inProgressFeatures[0]);

  return `${subject}\n\n${body}`;
}

function classifyChangeType(files: GitStatusFile[]): CommitType {
  const hasBackend = files.some(f => f.path.includes('app/server'));
  const hasFrontend = files.some(f => f.path.includes('app/client'));
  const hasDocs = files.some(f => f.path.includes('docs/') || f.path.includes('.md'));
  const hasTests = files.some(f => f.path.includes('test'));

  if (hasDocs && !hasBackend && !hasFrontend) return 'docs';
  if (hasTests && !hasBackend && !hasFrontend) return 'test';

  // Infer from feature type or file patterns
  if (files.some(f => f.path.includes('perf') || f.path.includes('optimization'))) {
    return 'perf';
  }
  if (files.some(f => f.path.includes('fix') || f.path.includes('bug'))) {
    return 'fix';
  }

  return 'feat'; // Default to feature
}
```

### Future Enhancement: Backend-Powered Generation

**Phase 2 (Optional - 2 additional hours):**
- New endpoint: `POST /api/v1/git/generate-message`
- Perform `git diff` analysis for deeper context
- Integration with PlannedFeatures database
- LLM-powered intelligent summaries (optional)

## Data Available for Message Generation

### From Git Status API (`/api/v1/git/status`)
- Current branch
- Staged files (paths, status)
- Unstaged files (paths, status)
- Untracked files
- Commits ahead/behind

### From Plans Panel Context
- Current in-progress features (title, description, type, tags)
- GitHub issue number (if linked)
- Priority level
- Session context

### From Project Standards (CLAUDE.md)
- Conventional commit format enforced
- **CRITICAL**: NO AI attribution in commit messages
- Types: feat, fix, perf, docs, refactor, style, test, chore

## Implementation Steps

### Frontend Implementation (2 hours)

1. **Add Git Section to PlansPanel** (30 min)
   - New collapsible section "Development Tools"
   - "Check Status" button
   - Git status display area
   - Commit message textarea

2. **Implement Message Generation** (45 min)
   - Create `generateCommitMessage()` helper
   - File classification logic
   - Conventional commit formatting
   - Integration with in-progress features

3. **Wire Up API Calls** (30 min)
   - Call `GET /api/v1/git/status` on "Check Status"
   - Pre-populate textarea with generated message
   - Call `POST /api/v1/git/commit` on submit
   - Success/error handling

4. **Testing & Polish** (15 min)
   - Test with various file combinations
   - Test with/without in-progress features
   - Verify commit messages follow standards
   - Ensure no AI attribution appears

## User Interface Mockup

```
┌─ Plans Panel (Panel 5) ────────────────────────────────┐
│                                                          │
│ [Filters: Priority ▼] [Type ▼]                         │
│                                                          │
│ ┌─ In Progress ──────────────────────────────────┐      │
│ │ 🔵 Fix N+1 query patterns                       │      │
│ │    Priority: High | Estimated: 2h               │      │
│ │    [View Details] [Mark Complete]               │      │
│ └─────────────────────────────────────────────────┘      │
│                                                          │
│ ┌─ Development Tools ─────────────────────────────┐     │
│ │ [Check Status] [Refresh]                         │     │
│ │                                                   │     │
│ │ Git Status: 3 files changed                      │     │
│ │ ✓ app/server/routes/queue_routes.py (modified)  │     │
│ │ ✓ app/server/repositories/...  (modified)       │     │
│ │ ✓ app_docs/feature-n1-fix.md (new)              │     │
│ │                                                   │     │
│ │ Suggested Commit Message:                        │     │
│ │ ┌─────────────────────────────────────────────┐ │     │
│ │ │ perf: Fix N+1 query patterns in queue routes│ │     │
│ │ │                                               │ │     │
│ │ │ Replace inefficient get_all() + loop with    │ │     │
│ │ │ direct find_by_id() queries. Uses database   │ │     │
│ │ │ indexes for O(1) lookups instead of O(n).    │ │     │
│ │ └─────────────────────────────────────────────┘ │     │
│ │                                                   │     │
│ │ [Commit Changes]                                 │     │
│ └───────────────────────────────────────────────────┘     │
│                                                          │
│ ┌─ Planned ───────────────────────────────────────┐      │
│ │ ...                                              │      │
│ └─────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

## Testing Strategy

### Test Cases

1. **No uncommitted changes**
   - Check Status → "Working tree clean" message
   - No commit message area shown

2. **Backend files changed, in-progress feature**
   - Check Status → Suggests "perf: Fix N+1..." with feature context

3. **Frontend files changed, no in-progress feature**
   - Check Status → Generic "feat: Update..." based on files

4. **Documentation only changed**
   - Check Status → Suggests "docs: Update..."

5. **Mixed changes (backend + frontend + docs)**
   - Check Status → Suggests based on majority or feature type

6. **User edits suggested message**
   - Textarea is editable
   - Commit uses edited message, not original suggestion

## Success Criteria

- ✅ "Check Status" button in Plans Panel
- ✅ Git status displayed when uncommitted changes exist
- ✅ Commit message pre-populated with thoughtful suggestion
- ✅ Message follows conventional commit format
- ✅ Message incorporates in-progress feature context
- ✅ User can edit message before committing
- ✅ Commit API call succeeds with suggested/edited message
- ✅ **CRITICAL**: No AI attribution in generated messages
- ✅ Works with existing git status/commit endpoints
- ✅ No backend changes required for MVP

## Related Features

- Panel 1: System Status with Git UI (existing)
- Panel 5: Plans Panel (existing)
- Git Status API (existing)
- Git Commit API (existing)
- PlannedFeatures Database (existing)
- WebSocket PlannedFeatures Context (existing)

## Future Enhancements (Out of Scope for MVP)

1. **Commit History Auto-Complete**
   - Learn from user's past commit message patterns
   - Suggest similar messages for similar changes

2. **Multi-File Smart Grouping**
   - Detect when changes form coherent logical units
   - Suggest splitting into multiple commits if too broad

3. **GitHub Issue Linking**
   - Automatically add "Fixes #123" or "Relates to #123"
   - Based on in-progress feature's GitHub issue number

4. **LLM-Powered Summaries**
   - Use Claude/GPT to analyze `git diff` and generate description
   - More intelligent understanding of code changes
   - **Note**: Must still follow CLAUDE.md rule - no AI attribution in final message

5. **Template Library**
   - User-defined commit message templates
   - Quick-select for common patterns

## References

- Investigation Report: Generated during assessment session
- CLAUDE.md: Project commit message standards
- GitCommitPanel: `app/client/src/components/GitCommitPanel.tsx`
- PlansPanel: `app/client/src/components/PlansPanel.tsx`
- Git Status API: `app/server/routes/git_routes.py:50-147`
- Git Commit API: `app/server/routes/git_routes.py:149-232`

## Estimated Value

**Time Saved Per Commit:**
- Current: ~30 seconds to manually write message
- With feature: ~5 seconds to review/edit suggestion
- **Savings: 25 seconds per commit**

**Improved Message Quality:**
- Consistent conventional commit format
- Better feature context integration
- Reduced typos and formatting errors

**Developer Experience:**
- Seamless workflow (stay in Plans panel)
- Contextual awareness (knows what you're working on)
- One less thing to think about

**ROI:**
- If 10 commits/day: 250 seconds saved = 4.2 minutes/day
- Monthly: ~84 minutes = 1.4 hours
- Annual: ~17 hours saved + better git history quality
