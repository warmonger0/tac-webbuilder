# Phase 3: Optimize Slash Commands with Explicit File Paths

**Status:** COMPLETE ✅
**Priority:** High
**Actual Effort:** ~3 hours
**Impact:** Better tool usage, faster execution, massive token savings

## Problem

Slash commands currently instruct agents to use Bash/Git for file discovery instead of passing explicit file paths. This causes:

1. **Improper tool usage** - Agents use Bash instead of Read/Grep/Glob
2. **Added latency** - Subprocess execution overhead
3. **Wasted tokens** - Git commands and output in context
4. **Inconsistent behavior** - Different agents might use different discovery methods

## Current Anti-Pattern

### `/review` command
```markdown
## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch
- Find the spec file by looking for specs/*.md files in the diff
- Read the identified spec file to understand requirements
```

**Problems:**
- Agent uses Bash tool for `git branch`
- Agent uses Bash tool for `git diff`
- Agent parses diff output to find spec file
- Agent then uses Read tool for spec file

### `/patch` command
```markdown
## Instructions

- Run `git diff --stat`. If changes are available, use them to understand...
```

**Problems:**
- Agent uses Bash tool for `git diff --stat`
- Adds latency and tokens for deterministic information

## Solution: Pass Explicit Paths

### 1. Update `/review` Command

**File:** `.claude/commands/review.md`

**Current Variables:**
```markdown
adw_id: $ARGUMENT
spec_file: $ARGUMENT
agent_name: $ARGUMENT if provided, otherwise use 'review_agent'
```

**New Variables:**
```markdown
adw_id: $1
spec_file: $2 (absolute path to spec file)
agent_name: $3 (if provided, otherwise use 'review_agent')
worktree_path: $4 (absolute path to worktree)
changed_files: $5 (newline-separated list of changed files since main)
review_image_dir: `{worktree_path}/agents/{adw_id}/{agent_name}/review_img/`
```

**Updated Instructions:**
```markdown
## Instructions

- Review the implementation in worktree at: `{worktree_path}`
- Spec file to review against: `{spec_file}`
- Files changed since main branch:
  ```
  {changed_files}
  ```
- Use the Read tool to examine changed files
- Use the spec file to understand requirements
- DO NOT use git commands - all file information is provided
```

### 2. Update Python Caller (adw_review_iso.py)

```python
# Get changed files using Python (no AI needed)
result = subprocess.run(
    ["git", "diff", "origin/main", "--name-only"],
    capture_output=True,
    text=True,
    cwd=worktree_path
)
changed_files = result.stdout.strip()

# Pass everything to the review command
request = AgentTemplateRequest(
    agent_name=AGENT_REVIEWER,
    slash_command="/review",
    args=[
        adw_id,
        spec_file,  # Absolute path
        AGENT_REVIEWER,
        worktree_path,  # Absolute path
        changed_files  # Pre-computed list
    ],
    adw_id=adw_id,
    working_dir=worktree_path,
)
```

### 3. Update `/patch` Command

**File:** `.claude/commands/patch.md`

**Current Variables:**
```markdown
adw_id: $1
review_change_request: $2
spec_path: $3 if provided, otherwise leave it blank
agent_name: $4 if provided, otherwise use 'patch_agent'
issue_screenshots: $5 (optional)
```

**New Variables:**
```markdown
adw_id: $1
review_change_request: $2
spec_path: $3 (absolute path to original spec)
agent_name: $4 (if provided, otherwise use 'patch_agent')
issue_screenshots: $5 (optional comma-separated screenshot paths)
patch_file_path: $6 (pre-computed path where to save patch)
target_files: $7 (optional - specific files to modify based on review issue)
```

**Updated Instructions:**
```markdown
## Instructions

- IMPORTANT: You're creating a patch plan to fix: {review_change_request}
- Original specification: {spec_path}
- Save patch plan to: {patch_file_path}
- Target files to modify: {target_files} (if provided)
- DO NOT run git diff - focus on the specific issue described
- If target_files provided, only modify those files
```

### 4. Remove Redundant Doc Loading

**File:** `.claude/commands/patch.md`

**Remove:**
```markdown
## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and instructions.
- `app/server/**` - Contains the codebase server.
- ...

- Read `.claude/commands/conditional_docs.md` to check if your task requires additional documentation
```

**Why:** Patch scope should be minimal - don't load generic docs for targeted fixes

## Files to Update

1. `.claude/commands/review.md` - Add explicit file path arguments
2. `.claude/commands/patch.md` - Add explicit file path arguments, remove doc loading
3. `adw_review_iso.py` - Pre-compute changed files, pass to review
4. `adw_modules/workflow_ops.py` - Update `create_and_implement_patch()` to pass target files

## Implementation Steps

1. Update `/review` command signature and instructions
2. Update `adw_review_iso.py` to pre-compute file list
3. Update `/patch` command signature and instructions
4. Update `create_and_implement_patch()` to pass target files
5. Test review workflow with explicit paths

## Expected Benefits

### Token Savings
- **Review:** ~2000-3000 tokens saved per review
  - No git command output in context
  - No conditional_docs.md loading
  - Direct file access

- **Patch:** ~500-1500 tokens saved per patch
  - No git diff output
  - No generic docs loading
  - Focused on specific issue

### Performance
- **Faster execution:** No subprocess calls from agent
- **Better tool usage:** Read/Grep instead of Bash
- **More reliable:** Deterministic file paths

### Code Quality
- **Explicit contracts:** Clear what's passed to commands
- **Easier debugging:** See exactly what agent received
- **Testable:** Can unit test path pre-computation

## Validation

```python
# Before: Agent discovers files
# git branch -> git diff -> parse output -> find files

# After: Python provides files
changed_files = subprocess.run(
    ["git", "diff", "origin/main", "--name-only"],
    capture_output=True,
    cwd=worktree_path
).stdout.strip()
# Pass to agent as argument
```

## Next Steps

See `PHASE_4_VALIDATE_WORKING_DIR.md` for next phase.
