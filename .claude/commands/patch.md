# Patch Plan

Create a **focused patch plan** to resolve a specific issue based on the `review_change_request`. Follow the `Instructions` to create a concise plan that addresses the issue with minimal, targeted changes.

## Variables

adw_id: $1
review_change_request: $2

## Instructions

- **IMPORTANT: Read `.adw-context.json` from the worktree root** to get pre-computed paths and context:
  - `spec_file` - original specification file (absolute path)
  - `patch_file_path` - where to save the patch plan (pre-computed, use this exact path)
  - `target_files` - specific files to modify (if provided, only modify these)
  - `issue_screenshots` - screenshot paths for visual context (if provided)
  - `changed_files` - files changed in this branch (for understanding scope)
- IMPORTANT: You're creating a patch plan to fix a specific review issue. Keep changes small, focused, and targeted
- IMPORTANT Use the `review_change_request` to understand exactly what needs to be fixed and use it as the basis for your patch plan
- If the context file contains `spec_file`, read it to understand the original requirements and context
- If the context file contains `issue_screenshots`, examine them to better understand the visual context of the issue
- **IMPORTANT: Save the patch plan to the exact path specified in `patch_file_path` from the context file**
- If no `patch_file_path` in context, create the patch plan in `specs/patch/` directory with filename: `patch-adw-{adw_id}-{descriptive-name}.md`
- IMPORTANT: This is a PATCH - keep the scope minimal. Only fix what's described in the `review_change_request` and nothing more
- If the context file contains `target_files`, focus your patch exclusively on those specific files - do not modify any other files
- DO NOT run git commands - all necessary file information is pre-computed and available in the context file
- Ultra think about the most efficient way to implement the solution with minimal code changes
- Base your `Plan Format: Validation` on the validation steps from `spec_path` if provided
  - If any tests fail in the validation steps, you must fix them.
  - If not provided, READ `.claude/commands/test.md: ## Test Execution Sequence` and execute the tests to understand the tests that need to be run to validate the patch.
- Replace every <placeholder> in the `Plan Format` with specific implementation details
- IMPORTANT: When you finish writing the patch plan, return exclusively the path to the patch plan file created and nothing else.

## Plan Format

```md
# Patch: <concise patch title>

## Metadata
adw_id: `{adw_id}`
review_change_request: `{review_change_request}`

## Issue Summary
**Original Spec:** <spec_path>
**Issue:** <brief description of the review issue based on the `review_change_request`>
**Solution:** <brief description of the solution approach based on the `review_change_request`>

## Files to Modify
**CRITICAL: This section defines file scope boundaries for cost optimization.**
**List EVERY file that needs to be modified - be specific and minimal for patches.**
**The implementation phase will ONLY load these files - unlisted files will NOT be accessible.**

### Existing Files
<List ALL existing files that will be modified, using absolute paths from project root. Example:
- app/server/routes/workflow_routes.py - Fix response format
>

### New Files
<List ALL new files that will be created (most patches won't need new files).>

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

<list 2-5 focused steps to implement the patch. Each step should be a concrete action.>

### Step 1: <specific action>
- <implementation detail>
- <implementation detail>

### Step 2: <specific action>
- <implementation detail>
- <implementation detail>

<continue as needed, but keep it minimal>

## Validation
Execute every command to validate the patch is complete with zero regressions.

<list 1-5 specific commands or checks to verify the patch works correctly>

## Patch Scope
**Lines of code to change:** <estimate>
**Risk level:** <low|medium|high>
**Testing required:** <brief description>
```

## Report

- IMPORTANT: Return exclusively the path to the patch plan file created and nothing else.