# Phase 3.5: Finalize Context Pattern for Remaining Commands

**Status:** COMPLETE ✅
**Priority:** High
**Actual Effort:** ~1.5 hours
**Impact:** Complete elimination of git commands from all ADW workflows

---

## Problem

Phase 3 successfully implemented context files for core workflow commands (`/patch`, `/review`, `/implement`, planning commands). However, three utility commands still use git commands directly:

1. **`/document`** - Uses `git diff --stat`, `git diff --name-only`
2. **`/pull_request`** - Uses `git diff`, `git log`, `git push`
3. **`/test`** - May need context for targeted testing

---

## Commands Requiring Updates

### 1. `/document` Command

**Current Anti-Pattern:**
```markdown
### 1. Analyze Changes
- Run `git diff origin/main --stat` to see files changed
- Run `git diff origin/main --name-only` to get list of changed files
- For significant changes (>50 lines), run `git diff origin/main <file>`
```

**Issues:**
- 3 git commands per documentation generation
- ~1500-2000 tokens of git output
- Subprocess execution overhead

**Context Needed:**
```json
{
  "changed_files": ["file1.py", "file2.tsx"],
  "changed_files_stats": {
    "file1.py": {"additions": 45, "deletions": 12},
    "file2.tsx": {"additions": 23, "deletions": 8}
  },
  "spec_file": "/path/to/original/spec.md",
  "documentation_screenshots_dir": "/path/to/screenshots"
}
```

**Token Savings:** ~1500-2000 per document generation

---

### 2. `/pull_request` Command

**Current Anti-Pattern:**
```markdown
## Run
1. Run `git diff origin/main...HEAD --stat` to see summary
2. Run `git log origin/main..HEAD --oneline` to see commits
3. Run `git diff origin/main...HEAD --name-only` for file list
4. Run `git push -u origin <branch_name>` to push
5. Run `gh pr create --title "..." --body "..."`
```

**Issues:**
- 4-5 git/gh commands per PR creation
- ~2000-3000 tokens of git output
- Multiple subprocess calls

**Context Needed:**
```json
{
  "changed_files": ["file1.py", "file2.tsx"],
  "changed_files_stats": {...},
  "commits": [
    {"sha": "abc123", "message": "feat: Add feature X"},
    {"sha": "def456", "message": "fix: Resolve issue Y"}
  ],
  "branch_name": "feature-issue-123-adw-12345678-add-auth",
  "plan_file": "/path/to/plan.md",
  "issue": {...}
}
```

**Note:** `git push` and `gh pr create` must still run (they're actions, not queries)

**Token Savings:** ~2000-3000 per PR creation

---

### 3. `/test` Command

**Current State:**
```markdown
## Instructions
- Execute each test in the sequence
- All file paths are relative to project root
- Always run `pwd` and `cd` before each test
```

**Potential Context:**
```json
{
  "changed_files": ["file1.py", "file2.tsx"],
  "test_targets": [
    "app/server/tests/test_api.py",
    "app/client/src/Button.test.tsx"
  ],
  "backend_port": "9100",
  "frontend_port": "9200"
}
```

**Benefits:**
- Targeted testing (only test what changed)
- No need to discover test files
- Application URLs readily available

**Token Savings:** ~500-1000 per test run

---

## Implementation Plan

### Step 1: Update `/document` Command

**File:** `.claude/commands/document.md`

**Changes:**
1. Add context file reading instruction
2. Remove git diff commands (lines 14-16)
3. Use `changed_files` from context
4. Use `spec_file` from context

**Before:**
```markdown
### 1. Analyze Changes
- Run `git diff origin/main --stat`
- Run `git diff origin/main --name-only`
```

**After:**
```markdown
### 1. Analyze Changes
- **Read `.adw-context.json`** to get:
  - `changed_files` - list of modified files
  - `changed_files_stats` - additions/deletions per file
  - `spec_file` - original specification
  - `documentation_screenshots_dir` - screenshot location
- DO NOT run git commands - all info pre-computed
```

---

### Step 2: Update `/pull_request` Command

**File:** `.claude/commands/pull_request.md`

**Changes:**
1. Add context file reading instruction
2. Remove query git commands (diff, log)
3. Keep action commands (push, gh pr create)
4. Use pre-computed data from context

**Before:**
```markdown
## Run
1. Run `git diff origin/main...HEAD --stat`
2. Run `git log origin/main..HEAD --oneline`
3. Run `git diff origin/main...HEAD --name-only`
4. Run `git push -u origin <branch_name>`
5. Run `gh pr create...`
```

**After:**
```markdown
## Instructions
- **Read `.adw-context.json`** to get:
  - `changed_files` - modified files
  - `commits` - commit history
  - `branch_name` - current branch
  - `plan_file` - implementation plan
  - `issue` - GitHub issue data

## Run
1. Review context data (no git commands needed)
2. Run `git push -u origin {branch_name}` to push
3. Run `gh pr create...` to create PR
```

---

### Step 3: Update `/test` Command (Optional Enhancement)

**File:** `.claude/commands/test.md`

**Changes:**
1. Add context file reading (optional)
2. Use `test_targets` if available for targeted testing
3. Use application URLs from context

**Enhancement:**
```markdown
## Instructions
- **OPTIONAL: Read `.adw-context.json`** for:
  - `test_targets` - specific test files to run (if provided)
  - `changed_files` - files that were modified
  - `backend_port`, `frontend_port` - application URLs
- If `test_targets` provided, run those tests first
- Otherwise, run full test suite as normal
```

---

### Step 4: Update Python Callers

#### A. Create Context in Documentation Workflow

**File:** (Find where `/document` is called - likely `adw_document_iso.py` or similar)

```python
def run_documentation(
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
    state: Optional[ADWState] = None,
):
    from adw_modules.workflow_ops import create_context_file

    # Pre-compute changed files with stats
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=working_dir
    )
    changed_files = result.stdout.strip().split('\n')

    # Get file stats
    changed_files_stats = {}
    for file in changed_files:
        stat_result = subprocess.run(
            ["git", "diff", "origin/main", "--", file, "--numstat"],
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        # Parse: "additions deletions filename"
        if stat_result.stdout:
            parts = stat_result.stdout.split()
            if len(parts) >= 2:
                changed_files_stats[file] = {
                    "additions": int(parts[0]) if parts[0].isdigit() else 0,
                    "deletions": int(parts[1]) if parts[1].isdigit() else 0
                }

    context_data = {
        "changed_files": changed_files,
        "changed_files_stats": changed_files_stats,
        "spec_file": state.get("spec_file") if state else None,
        "documentation_screenshots_dir": f"{working_dir}/agents/{adw_id}/reviewer/review_img"
    }

    create_context_file(working_dir, adw_id, context_data, logger)
```

#### B. Create Context for PR Creation

**File:** `workflow_ops.py` (in `create_pull_request` function)

```python
def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes."""

    # Pre-compute PR context
    # Get changed files
    result = subprocess.run(
        ["git", "diff", "origin/main...HEAD", "--name-only"],
        capture_output=True,
        text=True,
        cwd=working_dir
    )
    changed_files = result.stdout.strip().split('\n') if result.returncode == 0 else []

    # Get commits
    result = subprocess.run(
        ["git", "log", "origin/main..HEAD", "--oneline"],
        capture_output=True,
        text=True,
        cwd=working_dir
    )
    commits = []
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if line:
                sha, *msg_parts = line.split(' ', 1)
                commits.append({
                    "sha": sha,
                    "message": msg_parts[0] if msg_parts else ""
                })

    # Create context
    context_data = {
        "branch_name": branch_name,
        "changed_files": changed_files,
        "commits": commits,
        "plan_file": state.get("plan_file"),
        "issue": issue.model_dump() if issue else state.get("issue", {})
    }

    create_context_file(working_dir, state.get("adw_id"), context_data, logger)

    # Continue with existing PR creation logic...
```

---

## Expected Benefits

### Token Savings Summary

| Command | Current Tokens | After Context | Savings |
|---------|---------------|---------------|---------|
| `/document` | ~2000-2500 | ~100-200 | ~2000 |
| `/pull_request` | ~2500-3500 | ~200-300 | ~2500 |
| `/test` (optional) | ~500-1000 | ~100-200 | ~500 |
| **Total per workflow** | **~5000-7000** | **~400-700** | **~5000** |

### Performance Improvements

- **Latency:** 10-15s reduction per workflow (no subprocess overhead)
- **Tool Usage:** Agents use Read tool instead of Bash
- **Reliability:** Pre-computed data is deterministic

### Developer Experience

- **Debugging:** Inspect context file to see what agent received
- **Transparency:** All pre-computed data visible in JSON
- **Consistency:** Same pattern across all workflows

---

## Validation Plan

### 1. Documentation Workflow
```bash
# Test document generation
uv run adw_document_iso.py <adw-id>

# Verify context file
cat trees/adw-<id>/.adw-context.json | jq .changed_files

# Verify no git commands in agent logs
grep "git diff" logs/adw-<id>_document.log  # Should be empty
```

### 2. PR Creation Workflow
```bash
# Test PR creation
# (via workflow that calls create_pull_request)

# Verify context file has commits and changed files
cat trees/adw-<id>/.adw-context.json | jq .commits

# Verify agent reads from context, not git
grep "git diff" logs/adw-<id>_pr_creator.log  # Should be empty
```

### 3. Test Workflow (if enhanced)
```bash
# Run tests with context
uv run adw_test_iso.py <adw-id>

# Verify context has test targets
cat trees/adw-<id>/.adw-context.json | jq .test_targets
```

---

## Files to Update

### Slash Commands
1. `.claude/commands/document.md` - Replace git commands with context
2. `.claude/commands/pull_request.md` - Replace git commands with context
3. `.claude/commands/test.md` - Add optional context support

### Python Files
4. `adw_modules/workflow_ops.py` - Update `create_pull_request()` to create context
5. Find and update document workflow caller (likely `adw_document_iso.py`)
6. Optionally update test workflow caller

---

## Success Criteria

- [ ] All git query commands removed from `/document`
- [ ] All git query commands removed from `/pull_request`
- [ ] Context file created before calling these commands
- [ ] Agent logs show no git commands (except push/gh actions)
- [ ] Token usage reduced by ~5000 tokens per workflow
- [ ] Phase 3.5 documentation complete

---

## Next Steps After Phase 3.5

1. **Phase 4:** Production validation and monitoring
2. **Phase 5:** Context file optimizations (caching, validation)
3. **Phase 6:** Remove any remaining backward compatibility code

---

**Ready to implement Phase 3.5!**
