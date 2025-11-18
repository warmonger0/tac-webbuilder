# Phase 3 Implementation Review

**Date:** 2025-11-18
**Status:** PARTIALLY IMPLEMENTED (~20% Complete)

## Executive Summary

Phase 3 aimed to optimize slash commands by pre-computing file paths in Python and passing them as explicit arguments to agents, eliminating the need for agents to run Bash/Git commands. The implementation has begun but is incomplete.

### What Works ✅
- Patch file path is pre-computed in Python (`workflow_ops.py:641-644`)
- Patch file path is passed as an explicit argument to `/patch` command
- Agent no longer needs to parse output to find patch file location

### What's Missing ❌
- Git commands still present in `/patch` instructions
- Documentation loading section still present in `/patch`
- `/review` command hasn't been updated at all
- No file discovery pre-computation for review
- No `target_files` support for targeted patches

---

## Detailed Analysis

### 1. `/patch` Command (`.claude/commands/patch.md`)

**Implementation Status: 40% Complete**

#### ✅ Implemented:
```markdown
# Line 11
patch_file_path: $5 (optional) - Pre-computed path where to save the patch plan

# Line 12
issue_screenshots: $6 (optional) - Variable position updated

# Line 20
**IMPORTANT: If `patch_file_path` is provided, save the patch plan to that exact path**
```

**Python Integration:** `workflow_ops.py:641-658`
```python
# Pre-compute patch file path (deterministic, no parsing needed)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
issue_slug = re.sub(r'[^a-z0-9]+', '-', review_change_request[:30].lower()).strip('-')
expected_patch_file = f"specs/patch/patch-adw-{adw_id}-{timestamp}-{issue_slug}.md"

# Pass to agent
args.append(expected_patch_file)  # NEW: Tell agent where to save
```

#### ❌ Not Implemented (Phase 3 Requirements):

**1. Git Command Still Present (Line 24):**
```markdown
# CURRENT (Anti-pattern):
- Run `git diff --stat`. If changes are available, use them to understand...

# SHOULD BE (Phase 3):
# Removed entirely - Python should pre-compute and pass changed files
```

**2. Doc Loading Section Still Present (Lines 32-43):**
```markdown
# CURRENT (Adds 1000+ tokens):
## Relevant Files
Focus on the following files:
- `README.md` - Contains the project overview...
- Read `.claude/commands/conditional_docs.md` to check if...

# SHOULD BE (Phase 3):
# Removed entirely - patch scope should be minimal
```

**3. Missing `target_files` Parameter:**
```markdown
# SHOULD HAVE (Phase 3 spec line 133):
target_files: $7 (optional - specific files to modify based on review issue)

# And in instructions (line 143):
- Target files to modify: {target_files} (if provided)
- If target_files provided, only modify those files
```

**Impact:**
- Still wastes ~2000-3000 tokens per patch (git output + docs)
- Agent still uses Bash tool instead of Read tool
- Adds latency from subprocess execution

---

### 2. `workflow_ops.py` (`create_and_implement_patch`)

**Implementation Status: 50% Complete**

#### ✅ Implemented:
```python
# Lines 641-644: Pre-computation
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
issue_slug = re.sub(r'[^a-z0-9]+', '-', review_change_request[:30].lower()).strip('-')
expected_patch_file = f"specs/patch/patch-adw-{adw_id}-{timestamp}-{issue_slug}.md"

# Line 658: Pass to agent
args.append(expected_patch_file)

# Line 688: Use directly (no parsing!)
patch_file_path = expected_patch_file
logger.info(f"Using pre-computed patch file: {patch_file_path}")
```

#### ❌ Not Implemented (Phase 3 Requirements):

**Missing `target_files` Parameter:**

**Current function signature (line 628):**
```python
def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
```

**Should be (Phase 3 spec line 171):**
```python
def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    target_files: Optional[List[str]] = None,  # NEW
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
```

**Missing logic to pass target_files:**
```python
# Should add after line 660:
if target_files:
    args.append(','.join(target_files))  # Pass as comma-separated
```

**Impact:**
- Can't tell patch agent which specific files to modify
- Patch agent might change unrelated files
- Less focused, more risky patches

---

### 3. `/review` Command (`.claude/commands/review.md`)

**Implementation Status: 0% Complete - NOT STARTED**

#### ❌ Current Anti-Pattern (Lines 7-10):
```markdown
## Variables

adw_id: $ARGUMENT
spec_file: $ARGUMENT
agent_name: $ARGUMENT if provided, otherwise use 'review_agent'
review_image_dir: `<absolute path to codebase>/agents/<adw_id>/<agent_name>/review_img/`
```

#### ❌ Current Anti-Pattern (Lines 14-16):
```markdown
## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch
- Find the spec file by looking for specs/*.md files in the diff
```

#### 🎯 Phase 3 Target (spec lines 59-67):
```markdown
## Variables

adw_id: $1
spec_file: $2 (absolute path to spec file)
agent_name: $3 (if provided, otherwise use 'review_agent')
worktree_path: $4 (absolute path to worktree)
changed_files: $5 (newline-separated list of changed files since main)
review_image_dir: `{worktree_path}/agents/{adw_id}/{agent_name}/review_img/`
```

#### 🎯 Phase 3 Target Instructions (spec lines 71-82):
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

**Impact:**
- Agent wastes 2000-3000 tokens on git command output
- Agent uses Bash tool instead of Read tool
- Adds subprocess execution latency
- Inconsistent behavior across reviews

---

### 4. `adw_review_iso.py` (`run_review` function)

**Implementation Status: 0% Complete - NOT STARTED**

#### ❌ Current Implementation (Lines 72-85):
```python
def run_review(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> ReviewResult:
    """Run the review using the /review command."""
    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEWER,
        slash_command="/review",
        args=[adw_id, spec_file, AGENT_REVIEWER],  # Only 3 args!
        adw_id=adw_id,
        working_dir=working_dir,
    )
```

#### 🎯 Phase 3 Target (spec lines 87-110):
```python
def run_review(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> ReviewResult:
    """Run the review using the /review command."""

    # PRE-COMPUTE changed files (deterministic Python, no AI needed)
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=working_dir
    )
    changed_files = result.stdout.strip()

    # Pass everything to the review command
    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEWER,
        slash_command="/review",
        args=[
            adw_id,
            spec_file,           # Absolute path
            AGENT_REVIEWER,
            working_dir,         # Absolute path
            changed_files        # Pre-computed list
        ],
        adw_id=adw_id,
        working_dir=working_dir,
    )
```

**Impact:**
- Python does the git command ONCE deterministically
- Agent receives file list as argument (no Bash needed)
- Saves 2000-3000 tokens per review
- Faster execution (no subprocess from agent)

---

## Token & Cost Impact Analysis

### Current State (Partial Implementation)
| Operation | Token Waste | Root Cause |
|-----------|-------------|------------|
| `/patch` | ~2000-3000 | Git commands + doc loading |
| `/review` | ~2000-3000 | Git commands + file discovery |
| **Total per workflow** | **~4000-6000** | **Anti-patterns still present** |

### Phase 3 Complete Target
| Operation | Token Savings | How |
|-----------|---------------|-----|
| `/patch` | ~2000-3000 | Remove git/docs, pass explicit paths |
| `/review` | ~2000-3000 | Pre-compute files, pass as args |
| **Total per workflow** | **~4000-6000** | **Python does discovery once** |

**Cost Savings:** $0.04-0.06 per workflow (at $10/MTok input rates)

---

## Files Requiring Updates

### ✅ Partially Updated
1. `.claude/commands/patch.md` - patch_file_path added, but needs:
   - Remove git diff instruction (line 24)
   - Remove "Relevant Files" section (lines 32-43)
   - Add target_files parameter

2. `adw_modules/workflow_ops.py` - patch path pre-computed, but needs:
   - Add target_files parameter to function
   - Pass target_files to agent

### ❌ Not Started
3. `.claude/commands/review.md` - Complete overhaul needed:
   - Change to numbered variables ($1-$5)
   - Add worktree_path, changed_files variables
   - Remove all git commands from instructions

4. `adws/adw_review_iso.py` - Update run_review:
   - Pre-compute changed files with subprocess
   - Pass 5 arguments instead of 3

---

## Implementation Plan to Complete Phase 3

### Step 1: Complete `/patch` Optimization
**Files:** `.claude/commands/patch.md`, `workflow_ops.py`

1. Remove line 24 from patch.md (`git diff --stat`)
2. Remove lines 32-43 from patch.md ("Relevant Files" section)
3. Add `target_files: $7` variable to patch.md
4. Update instructions to use target_files
5. Add `target_files` parameter to `create_and_implement_patch()`
6. Pass target_files to agent as arg 7

**Estimated effort:** 30 minutes
**Token savings:** ~2000-3000 per patch

### Step 2: Implement `/review` Optimization
**Files:** `.claude/commands/review.md`, `adw_review_iso.py`

1. Update review.md variables to numbered format ($1-$5)
2. Add worktree_path and changed_files variables
3. Remove git commands from instructions (lines 14-16)
4. Update `run_review()` to pre-compute changed files
5. Pass 5 arguments to review command

**Estimated effort:** 45 minutes
**Token savings:** ~2000-3000 per review

### Step 3: Validation
1. Run full workflow with Phase 3 complete
2. Verify agents use Read/Grep instead of Bash
3. Measure token usage reduction
4. Update Phase 3 doc status to "Complete"

**Estimated effort:** 15 minutes

**Total effort to complete:** ~90 minutes
**Total token savings:** ~4000-6000 per workflow

---

## Recommendations

### High Priority
1. **Complete `/patch` first** - Already 40% done, low-hanging fruit
2. **Then do `/review`** - Bigger impact, more complex

### Medium Priority
3. **Add `target_files` support** - Enables more precise patches
4. **Remove doc loading** - Reduces noise, keeps patches focused

### Low Priority
5. **Measure and document savings** - Validate Phase 3 benefits

---

## Conclusion

Phase 3 implementation has begun with patch file path pre-computation, demonstrating the pattern works. However, the full benefits won't be realized until:

1. Git commands are removed from agent instructions
2. File discovery is moved to deterministic Python
3. All paths are passed as explicit arguments

**Next Action:** Complete Step 1 (patch optimization) to validate full benefits before tackling review optimization.

**Estimated ROI:** ~90 minutes of work → ~4000-6000 tokens saved per workflow → $0.04-0.06 saved per run → Pays for itself after ~25 workflow runs.
