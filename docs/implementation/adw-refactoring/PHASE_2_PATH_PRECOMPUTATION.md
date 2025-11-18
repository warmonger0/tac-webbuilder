# Phase 2: Fix Path Pre-computation

**Status:** Planned
**Priority:** High
**Estimated Effort:** 2 hours
**Impact:** Code quality, fewer file operations

## Problem

Currently, ADW workflows parse agent output to extract file paths instead of pre-computing them. This causes:

1. **50-100 line path validation blocks** - Complex fallback logic
2. **File location ambiguity** - Agent might create files in wrong location
3. **Unnecessary file moves** - Moving files from parent repo to worktree
4. **Masked bugs** - Fallback logic hides real issues

## Current Anti-Pattern

```python
# CURRENT (BAD): Parsing agent output
plan_response = build_plan(issue, issue_command, adw_id, logger)
plan_file_path_raw = plan_response.output.strip()

# Then 50+ lines of validation/recovery logic
for line in plan_file_path_raw.split('\n'):
    if 'specs/' in line and line.endswith('.md'):
        # Extract path from agent output
        # Check if absolute or relative
        # Check if in worktree or parent
        # Move file if in wrong location
        # Handle edge cases...
```

## Solution Pattern (Already Implemented in adw_plan_iso.py)

```python
# BETTER: Pre-compute the path
title_slug = re.sub(r'[^a-z0-9]+', '-', issue.title.lower()).strip('-')[:50]
expected_plan_file = f"specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-{title_slug}.md"

# Pass to agent as argument
plan_response = build_plan(
    issue, issue_command, adw_id, logger,
    working_dir=worktree_path,
    plan_file_path=expected_plan_file  # Tell agent where to save
)

# Use pre-computed path - no parsing needed!
plan_file_path = expected_plan_file
```

## Files to Update

### 1. `adw_modules/workflow_ops.py`

**Function:** `create_and_implement_patch()` (lines 723-873)

**Current:** 150 lines with complex path resolution
**Target:** 30 lines with pre-computed paths

**Changes:**
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
    """Create a patch plan and implement it."""

    # PRE-COMPUTE patch file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    issue_slug = re.sub(r'[^a-z0-9]+', '-', review_change_request[:30].lower()).strip('-')
    expected_patch_file = f"specs/patch/patch-adw-{adw_id}-{timestamp}-{issue_slug}.md"

    # Pass pre-computed path to agent
    args = [adw_id, review_change_request]
    if spec_path:
        args.append(spec_path)
    else:
        args.append("")
    args.append(agent_name_planner)
    args.append(expected_patch_file)  # NEW: Tell agent where to save

    if issue_screenshots:
        args.append(issue_screenshots)

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/patch",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}",
            success=False
        )

    # Use pre-computed path - no parsing!
    patch_file_path = expected_patch_file
    logger.info(f"Using pre-computed patch file: {patch_file_path}")

    # Implement the patch
    implement_response = implement_plan(
        patch_file_path, adw_id, logger, agent_name_implementor, working_dir=working_dir
    )

    return patch_file_path, implement_response
```

### 2. Update `/patch` command

**File:** `.claude/commands/patch.md`

**Add to Variables:**
```markdown
patch_file_path: $6 (optional) - Pre-computed path where to save the patch plan
```

**Add to Instructions:**
```markdown
- IMPORTANT: If `patch_file_path` is provided, save the patch plan to that exact path
- If not provided, generate the path as: `specs/patch/patch-adw-{adw_id}-{descriptive-name}.md`
```

### 3. Remove Fallback Logic

**Function:** `workflow_ops.py:find_spec_file()` (lines 653-720)

**Current:** 70 lines of search and fallback logic
**Target:** Fail fast if not in state

```python
def find_spec_file(state: ADWState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state - fail fast if not present."""
    worktree_path = state.get("worktree_path")
    spec_file = state.get("plan_file")

    if not spec_file:
        raise ValueError("No plan_file in state - run planning phase first")

    # Make absolute if needed
    if worktree_path and not os.path.isabs(spec_file):
        spec_file = os.path.join(worktree_path, spec_file)

    if not os.path.exists(spec_file):
        raise ValueError(f"Spec file not found: {spec_file}")

    logger.info(f"Using spec file from state: {spec_file}")
    return spec_file
```

## Implementation Steps

1. Update `create_and_implement_patch()` to pre-compute paths
2. Update `/patch` command to accept pre-computed path
3. Simplify `find_spec_file()` to fail fast
4. Remove `find_plan_for_issue()` function entirely
5. Test with review workflow that has blocker issues

## Expected Benefits

- **Code Quality:** 150 lines → 30 lines in patch creation
- **Clarity:** No more "where did the agent save the file?" debugging
- **Reliability:** File locations are deterministic and predictable
- **Bug Detection:** Issues surface immediately instead of being masked

## Validation

```python
# Before: 50+ lines of path resolution
# After: 1 line
patch_file_path = expected_patch_file
```

## Next Steps

See `PHASE_3_OPTIMIZE_SLASH_COMMANDS.md` for next phase.
