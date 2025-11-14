# Validate Workflow Execution

Verify that the workflow execution matched the plan and all setup steps completed correctly.

## Variables
validation_artifacts: $1

## Instructions

You are a **validation specialist**. Your job is to verify that the deterministic execution phase completed successfully and matches the plan.

The `validation_artifacts` variable contains a JSON object with:
- `plan`: The original workflow configuration (YAML)
- `execution`: The execution results (files created, commands run, etc.)
- `git_status`: Current git status
- `file_system`: Actual files that exist

## Your Verification Tasks

### 1. Branch Verification
- **Check**: Was the branch created with the correct name?
- **Expected**: `{plan.branch_name}`
- **Actual**: Compare with git status

### 2. Plan File Verification
- **Check**: Was the plan file created?
- **Expected**: `specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-*.md`
- **Actual**: Check if file exists

### 3. Worktree Verification (if required)
If `plan.requires_worktree` is `true`:
- **Check**: Was worktree created at correct location?
- **Expected**: `trees/{adw_id}/` directory exists
- **Actual**: Check file system
- **Check**: Does worktree contain expected files?
- **Expected**: All source files copied to worktree

If `plan.requires_worktree` is `false`:
- **Check**: No worktree was created
- **Expected**: Work done in main repo

### 4. Worktree Setup Verification (if worktree created)
For each step in `plan.worktree_setup.steps`:

**a) Port Configuration**
- **Check**: `.ports.env` file created
- **Expected contents**:
  ```
  BACKEND_PORT={plan.worktree_setup.backend_port}
  FRONTEND_PORT={plan.worktree_setup.frontend_port}
  VITE_BACKEND_URL=http://localhost:{plan.worktree_setup.backend_port}
  ```

**b) Environment Files**
- **Check**: `.env` and `app/server/.env` exist
- **Expected**: Both files contain port configuration appended

**c) MCP Configuration Files**
- **Check**: `.mcp.json` and `playwright-mcp-config.json` exist (if applicable)
- **Expected**: Paths updated to absolute paths
- **Expected**: `videos/` directory created

**d) Backend Dependencies**
- **Check**: `app/server/.venv/` directory exists
- **Expected**: Virtual environment with installed packages
- **Verify**: Check for key packages (FastAPI, Anthropic, etc.)

**e) Frontend Dependencies**
- **Check**: `app/client/node_modules/` directory exists
- **Expected**: Node modules installed
- **Verify**: Check for key packages (React, Vite, TypeScript)

**f) Database Setup**
- **Check**: Database file exists (if applicable)
- **Expected**: `app/server/database.db` or similar
- **Verify**: Database initialized and accessible

### 5. Execution Results Verification
- **Check**: Execution completed without errors
- **Review**: `execution.errors` array (should be empty)
- **Review**: `execution.warnings` array (document any warnings)
- **Check**: All expected files in `execution.files_created`

### 6. Git Status Verification
- **Check**: Current branch matches plan
- **Check**: Uncommitted changes match expectations (plan file should be staged/uncommitted)
- **Check**: No unexpected modifications

### 7. Project Context Verification
- **Check**: Did project detection make sense?
- **Review**: `plan.detection_reasoning`
- **Check**: Confidence level appropriate for decision made
- **Warning**: If confidence was "low", note potential for review

## Output Format

Generate a **validation report** in this format:

```markdown
# Workflow Validation Report

## Summary
- **Status**: ✅ PASSED / ⚠️ PASSED WITH WARNINGS / ❌ FAILED
- **Issue**: #{issue_number}
- **ADW ID**: {adw_id}
- **Branch**: {branch_name}
- **Validated**: {timestamp}

## Verification Results

### ✅ Branch Verification
- Branch created: `{branch_name}`
- Current branch: `{actual_branch}`
- Status: PASS

### ✅ Plan File Verification
- Expected: `specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-*.md`
- Found: `{actual_plan_file}`
- Status: PASS

### ✅/❌ Worktree Verification
{if requires_worktree}
- Worktree path: `{worktree_path}`
- Directory exists: YES/NO
- Files present: {file_count}
- Status: PASS/FAIL
{else}
- Worktree not required: Correctly skipped
- Status: PASS
{endif}

### ✅/❌ Setup Steps Verification
{for each step in plan.worktree_setup.steps}
#### {step.action}
- Description: {step.description}
- Executed: YES/NO
- Verification: {details}
- Status: PASS/FAIL
{endfor}

### ✅/⚠️/❌ Execution Results
- Errors: {count} {list errors if any}
- Warnings: {count} {list warnings if any}
- Files created: {count}
- Commands executed: {count}
- Overall: PASS/WARNING/FAIL

### ✅/⚠️ Project Context Detection
- Detected: `{plan.project_context}`
- Confidence: `{plan.confidence}`
- Reasoning: {plan.detection_reasoning}
- Assessment: {your assessment of whether detection was correct}
- Status: PASS/WARNING

## Issues Found
{if any issues found}
1. **[ERROR/WARNING]** {description}
   - Impact: {impact level}
   - Recommendation: {how to fix}
{else}
No issues found. Workflow executed successfully.
{endif}

## Recommendations
{list any recommendations for improvement}

## Conclusion
{summary of validation - did everything work as planned?}
```

## Important Notes

- Be thorough but concise
- Every ✅/❌ should have a reason
- Warnings are non-blocking issues
- Errors are blocking issues
- If project context detection seemed wrong, flag it as WARNING
- Focus on ACTUAL vs EXPECTED comparisons
- Don't just trust the execution result - verify files actually exist

## Artifacts Reference

The `validation_artifacts` JSON structure:
```json
{
  "plan": {
    "issue_type": "feature",
    "project_context": "tac-7-root",
    "requires_worktree": false,
    "branch_name": "feat-issue-123-adw-abc12345-...",
    "worktree_setup": {...},
    "validation_criteria": [...]
  },
  "execution": {
    "success": true,
    "errors": [],
    "warnings": [],
    "files_created": ["path1", "path2"],
    "commands_executed": [...]
  },
  "git_status": "...",
  "file_system": {
    "worktree_exists": true,
    "plan_file_exists": true,
    ...
  }
}
```

## Your Goal

Provide confidence that the workflow executed correctly OR identify specific issues that need attention.
