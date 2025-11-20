# Review and Merge Remaining Uncommitted Changes

## Context

After E2E test fixes (Sessions 1 & 2), there are uncommitted changes from previous work sessions that need review before merging to main.

## Current Git Status

**Modified Files (11 files):**
- `adws/adw_modules/app_lifecycle.py`
- `adws/adw_triggers/trigger_webhook.py`
- `app/client/src/components/RoutesView.tsx`
- `app/client/src/components/WorkflowHistoryCard.tsx`
- `app/client/src/types/api.types.ts`
- `app/server/app/db/cost_estimates_by_issue.json`
- `app/server/core/adw_lock.py`
- `app/server/core/data_models.py`
- `app/server/pyproject.toml`
- `app/server/server.py`
- `app/server/uv.lock`

**Untracked Documentation (6 items):**
- `docs/implementation/refactor/`
- `docs/refactoring/E2E_INTEGRATION_TESTING_PLAN.md`
- `docs/refactoring/NEXT_SESSION_PHASE_4.md`
- `docs/refactoring/PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md`
- `docs/refactoring/SESSION_SUMMARY_2025-11-19.md`
- `docs/refactoring/phase_3_artifacts/`

---

## Task: Review and Merge Remaining Changes

### Objective
Review all uncommitted changes, determine which should be committed, and merge them to main with appropriate commit messages.

### Working Directory
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
```

---

## Step 1: Review Modified Files

**Review each modified file to understand the changes:**

```bash
# See what changed in each file
git diff adws/adw_modules/app_lifecycle.py
git diff adws/adw_triggers/trigger_webhook.py
git diff app/client/src/components/RoutesView.tsx
git diff app/client/src/components/WorkflowHistoryCard.tsx
git diff app/client/src/types/api.types.ts
git diff app/server/app/db/cost_estimates_by_issue.json
git diff app/server/core/adw_lock.py
git diff app/server/core/data_models.py
git diff app/server/pyproject.toml
git diff app/server/server.py
git diff app/server/uv.lock

# Or see all changes at once
git diff
```

**Questions to Answer:**
1. What feature/fix do these changes implement?
2. Are they related to each other or separate concerns?
3. Should they be committed together or separately?
4. Are there any changes that should NOT be committed?

---

## Step 2: Review Untracked Documentation

**Check what's in the untracked documentation:**

```bash
# List contents
ls -la docs/implementation/refactor/
ls -la docs/refactoring/phase_3_artifacts/

# Read key files
cat docs/refactoring/E2E_INTEGRATION_TESTING_PLAN.md
cat docs/refactoring/NEXT_SESSION_PHASE_4.md
cat docs/refactoring/PHASE_4_WORKFLOW_HISTORY_SPLIT_PLAN.md
cat docs/refactoring/SESSION_SUMMARY_2025-11-19.md
```

**Questions to Answer:**
1. Are these documentation files still relevant?
2. Should they be committed or archived?
3. Do they duplicate information elsewhere?

---

## Step 3: Group Changes Logically

Based on review, group changes into logical commits:

**Example Groupings:**

### Option A: Group by Subsystem
- **Commit 1:** ADW module changes (adws/)
- **Commit 2:** Client changes (app/client/)
- **Commit 3:** Server changes (app/server/)
- **Commit 4:** Documentation (docs/)

### Option B: Group by Feature/Purpose
- **Commit 1:** All changes related to Feature X
- **Commit 2:** All changes related to Bug Fix Y
- **Commit 3:** Documentation updates

### Option C: Single Comprehensive Commit
- **Commit 1:** All changes with detailed message explaining each part

---

## Step 4: Create Commits

**For each logical group, create a commit:**

```bash
# Stage files for commit
git add <files>

# Create commit with detailed message
git commit -m "$(cat <<'EOF'
<type>: <short description>

<Detailed description of what changed and why>

Changes:
- file1.py: Description of changes
- file2.tsx: Description of changes
- etc.

<Optional sections>
## Breaking Changes
...

## Migration Notes
...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Commit Type Prefixes:**
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring (no behavior change)
- `docs:` - Documentation only
- `chore:` - Maintenance (dependencies, config)
- `perf:` - Performance improvement
- `test:` - Test additions/fixes
- `style:` - Code style changes (formatting)

---

## Step 5: Push to Remote

After all commits are created:

```bash
# Push to main
git push origin main

# Verify status
git status
```

---

## Step 6: Verify Everything is Clean

```bash
# Should show clean working directory
git status

# Expected output:
# On branch main
# Your branch is up to date with 'origin/main'.
# nothing to commit, working tree clean
```

---

## Recommended Prompts for New Chat Session

### Prompt Option 1: Detailed Review

```
# Task: Review and Commit Remaining Uncommitted Changes

## Context
After E2E test fixes (Sessions 1 & 2), there are uncommitted changes from previous work sessions. Need to review and commit these changes with appropriate grouping and commit messages.

## Files to Review
Read `/Users/Warmonger0/tac/tac-webbuilder/REVIEW_REMAINING_CHANGES.md` for complete context.

## Modified Files (11 files)
- ADW modules: app_lifecycle.py, trigger_webhook.py
- Client: RoutesView.tsx, WorkflowHistoryCard.tsx, api.types.ts
- Server: adw_lock.py, data_models.py, server.py, pyproject.toml, uv.lock
- Database: cost_estimates_by_issue.json

## Untracked Documentation (6 items)
- docs/implementation/refactor/
- docs/refactoring/ (various planning docs)

## Requirements
1. Review each modified file using `git diff`
2. Understand what changes were made and why
3. Group changes into logical commits by feature/subsystem
4. Create detailed commit messages explaining changes
5. Add untracked documentation with appropriate commits
6. Push all commits to origin/main
7. Verify clean working directory

## Execution Plan
1. Run `git diff` on each modified file and analyze changes
2. Read untracked documentation to determine if relevant
3. Group changes into 2-4 logical commits
4. Create commits with detailed messages
5. Push to origin/main
6. Verify `git status` shows clean working tree

Start by reviewing the modified files to understand what changes were made.
```

### Prompt Option 2: Quick Commit (if you know what the changes are)

```
# Task: Commit Remaining Work-in-Progress Changes

## Context
After E2E test fixes, there are 11 modified files and some documentation from previous work that need to be committed.

Working directory: /Users/Warmonger0/tac/tac-webbuilder

## Modified Files
- ADW: app_lifecycle.py, trigger_webhook.py
- Client: RoutesView.tsx, WorkflowHistoryCard.tsx, api.types.ts
- Server: adw_lock.py, data_models.py, server.py, pyproject.toml, uv.lock
- DB: cost_estimates_by_issue.json

## Untracked Docs
- docs/implementation/refactor/
- docs/refactoring/ (E2E plan, Phase 4 plan, session summary, artifacts)

## Task
Review changes with `git diff`, group into logical commits (by subsystem or feature), create detailed commit messages, and push to main.

These changes are from [DESCRIBE WHAT YOU KNOW ABOUT THESE CHANGES].

Commit them appropriately and push to origin/main.
```

### Prompt Option 3: Selective Review (if some files should not be committed)

```
# Task: Selectively Review and Commit Changes

## Context
Review 11 modified files and determine which should be committed. Some may be temporary/debug changes that should be discarded.

Working directory: /Users/Warmonger0/tac/tac-webbuilder

## Requirements
1. Review each file with `git diff`
2. Determine which changes are intentional vs accidental
3. Use `git restore <file>` to discard unwanted changes
4. Commit remaining changes in logical groups
5. Add relevant documentation
6. Push to origin/main

## Modified Files to Review
[List from git status]

Start by reviewing each file's diff and asking me which changes to keep.
```

---

## Additional Context

### Recent Commits (for reference)
```bash
git log --oneline -5
```

**Recent commits:**
- `ac6eae7` - docs: Add archived documentation, planned features, and utility scripts
- `3cc306e` - docs: Add Session 3 continuation guide for GitHub E2E tests
- `a9738c0` - docs: Add E2E test infrastructure and documentation
- `9558c9e` - fix: Fix 50 E2E integration test failures across 3 test suites

### Working Directory Structure
```
tac-webbuilder/
├── adws/                      # ADW workflow modules
├── app/
│   ├── client/               # React frontend
│   └── server/               # FastAPI backend
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

---

## Notes

- The modified files appear to be from previous work sessions (not from E2E test fixes)
- The untracked documentation is refactoring/planning docs from 2025-11-19
- uv.lock changes are likely from dependency updates (pyproject.toml changes)
- cost_estimates_by_issue.json changes might be generated/computed data

---

## Success Criteria

✅ All relevant changes committed with clear messages
✅ Unwanted changes discarded (if any)
✅ All commits pushed to origin/main
✅ Clean working directory (`git status` shows nothing)
✅ Commit history is logical and well-documented
