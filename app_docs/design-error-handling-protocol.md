# Error Handling Sub-Agent Protocol - Design Document

**Feature ID:** 108 (9th sub-feature of Closed-Loop Automation System)
**Parent Feature:** 99 (Closed-Loop Workflow Automation System)
**Created:** 2025-12-12
**Status:** Design Phase
**Estimated Hours:** 2.5-3h
**Priority:** High

## Overview

A comprehensive error handling system that detects workflow failures, analyzes root causes, updates the Plans Panel, and provides one-click fix workflows. This completes the "closing the loop" for both success and failure paths in the autonomous development system.

## Problem Statement

Currently, when ADW workflows abort (e.g., after phase 4 due to test failures, build errors, or other exceptions):

1. **Silent failures** - User must manually check workflow status
2. **No root cause analysis** - User must investigate error logs manually
3. **Manual recovery** - User must create new issues and launch fix workflows
4. **Lost context** - Error details and workflow state are scattered across logs
5. **Plans Panel drift** - Failed workflows remain marked as "in_progress" indefinitely

## Solution Architecture

### High-Level Workflow

```
ADW Execution (10 phases)
        ↓
  Phase Failure Detected
        ↓
  Capture Error Context
        ↓
  Trigger Error Handler Sub-Agent
        ↓
  ┌─────────────────────────────┐
  │ Error Analysis Sub-Agent    │
  │ - Identify error type       │
  │ - Review changed files      │
  │ - Analyze workflow state    │
  │ - Determine root cause      │
  │ - Suggest fix strategy      │
  └─────────────────────────────┘
        ↓
  Generate Error Report
        ↓
  Update Plans Panel
  ├─ Mark original workflow "failed"
  ├─ Add error summary to completion_notes
  ├─ Auto-create fix issue (child task)
  └─ Set priority based on severity
        ↓
  Run Cleanup Operations
  ├─ Close/comment on GitHub issue
  ├─ Clean up worktree (optional)
  ├─ Post error summary to GH issue
  └─ Update workflow_history
        ↓
  Generate Fix Prompt
  ├─ Create detailed prompt with error context
  ├─ Include relevant code snippets
  └─ Suggest workflow type (patch vs full)
        ↓
  Present to User
  ├─ Show error analysis in Panel 2
  ├─ Highlight fix issue in Panel 5
  └─ [One-Click Fix] button → Launch workflow
```

## Trigger Points

### Phase-Level Failures

**High-Priority Triggers** (immediate error handling):
- **Build Phase** - Compilation errors, missing dependencies
- **Lint Phase** - Linting errors that block progress
- **Test Phase** - Test failures after max retry attempts (3 attempts)
- **E2E Test Phase** - E2E failures after max retry attempts
- **Review Phase** - Blocker issues that can't be auto-resolved

**Medium-Priority Triggers** (may continue with warnings):
- **Plan Phase** - Invalid plan structure, missing requirements
- **Document Phase** - Documentation generation failures

**Low-Priority Triggers** (log but continue):
- **Ship Phase** - Merge conflicts (usually user decision)
- **Cleanup Phase** - Worktree cleanup failures

### Exception-Based Failures

**System Errors**:
- `TimeoutError` - Workflow exceeds 20-minute planning timeout
- `WorktreeCreationError` - Git worktree creation failures
- `DatabaseConnectionError` - PostgreSQL connection issues
- `APIError` - OpenAI/Anthropic API failures (rate limits, service down)

**Loop Prevention Triggers**:
- **Circuit Breaker** - Same agent posting 8+ times in 15 comments (Issue #168)
- **No Progress Detection** - Tests still failing after 3 resolution attempts

**Resource Errors**:
- `PortAllocationError` - All 15 ports occupied
- `DiskSpaceError` - Insufficient disk space for worktree
- `MemoryError` - Out of memory during execution

## Error Analysis Sub-Agent

### Sub-Agent Configuration

```python
{
    "subagent_type": "error-analyzer",
    "model": "haiku",  # Fast, cost-effective for analysis
    "tools": ["Read", "Grep", "Bash"],
    "timeout": 300000,  # 5 minutes
    "context_limit": 50000  # tokens
}
```

### Analysis Workflow

**Step 1: Context Capture** (30 seconds)
- Failed phase name and number
- Error message and stack trace
- Workflow state (ADWState.json)
- Changed files since branch creation
- Test output (if applicable)
- Recent GitHub issue comments

**Step 2: Error Classification** (1 minute)
```python
ERROR_TYPES = {
    "syntax": "Code syntax errors (missing braces, typos)",
    "type": "Type errors (TypeScript, Python type hints)",
    "logic": "Logic errors (wrong conditions, off-by-one)",
    "dependency": "Missing/incorrect dependencies",
    "integration": "API/service integration failures",
    "test": "Test-specific issues (fixture problems, mocks)",
    "build": "Build configuration errors",
    "lint": "Linting rule violations",
    "timeout": "Execution timeout",
    "resource": "Resource exhaustion (memory, disk, ports)"
}
```

**Step 3: Root Cause Analysis** (2 minutes)
- Review changed files for common patterns
- Check if error existed before changes (regression vs new)
- Identify triggering code change
- Analyze test failure patterns (if test phase)
- Check for known issues in codebase

**Step 4: Fix Strategy Recommendation** (1 minute)
```python
FIX_STRATEGIES = {
    "quick_patch": {
        "description": "Simple 1-file fix, use adw_patch_iso",
        "estimated_hours": 0.5,
        "confidence": "high"
    },
    "targeted_fix": {
        "description": "2-5 files, use adw_plan_build_test_iso",
        "estimated_hours": 1.5,
        "confidence": "medium"
    },
    "full_rework": {
        "description": "Complex issue, use adw_sdlc_complete_iso",
        "estimated_hours": 3.0,
        "confidence": "low"
    },
    "revert_and_redesign": {
        "description": "Architectural issue, revert PR and replan",
        "estimated_hours": 4.0,
        "confidence": "low"
    }
}
```

### Error Report Schema

```json
{
    "error_id": "err_20251212_143045",
    "workflow_id": "adw_20251212_120000",
    "issue_number": 123,
    "failed_phase": "test",
    "failed_at": "2025-12-12T14:30:45Z",
    "error_type": "test",
    "error_message": "TypeError: Cannot read property 'map' of undefined",
    "stack_trace": "...",
    "root_cause": "fetchPlannedFeatures returns null when API fails, but PlansPanel.tsx doesn't handle null case",
    "affected_files": [
        "app/client/src/components/PlansPanel.tsx:42",
        "app/client/src/api/plannedFeatures.ts:15"
    ],
    "fix_strategy": "quick_patch",
    "fix_description": "Add null check before .map() call in PlansPanel.tsx",
    "estimated_fix_hours": 0.5,
    "confidence": "high",
    "recommended_workflow": "adw_patch_iso",
    "context_snapshot": {
        "branch": "feat-123-add-plans-panel",
        "changed_files": 3,
        "tests_failed": 2,
        "tests_passed": 147
    }
}
```

## Plans Panel Integration

### Database Schema Changes

**Add "failed" status** (requires migration 020):
```sql
-- Modify status CHECK constraint
ALTER TABLE planned_features
DROP CONSTRAINT planned_features_status_check;

ALTER TABLE planned_features
ADD CONSTRAINT planned_features_status_check
CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled', 'failed'));

-- Add error tracking fields
ALTER TABLE planned_features
ADD COLUMN error_id TEXT,
ADD COLUMN error_type TEXT,
ADD COLUMN error_summary TEXT,
ADD COLUMN failed_at TIMESTAMP,
ADD COLUMN retry_count INTEGER DEFAULT 0;

-- Index for failed items
CREATE INDEX idx_planned_features_failed ON planned_features(failed_at)
WHERE status = 'failed';
```

### Plans Panel API Updates

**New endpoint** - `PUT /api/v1/planned-features/{id}/mark-failed`
```python
@router.put("/{id}/mark-failed")
async def mark_feature_as_failed(
    id: int,
    error_report: ErrorReport
):
    """Mark feature as failed and create fix task."""

    # Update original feature
    service.update(id, {
        "status": "failed",
        "failed_at": datetime.now(),
        "error_id": error_report.error_id,
        "error_type": error_report.error_type,
        "error_summary": error_report.error_message[:280],
        "completion_notes": error_report.root_cause,
        "retry_count": retry_count + 1
    })

    # Create fix task (child of original)
    fix_task = service.create({
        "item_type": "bug",
        "title": f"Fix: {original_feature.title} - {error_report.error_type}",
        "description": error_report.fix_description,
        "status": "planned",
        "priority": "high" if error_report.error_type in ["build", "syntax"] else "medium",
        "estimated_hours": error_report.estimated_fix_hours,
        "parent_id": id,
        "github_issue_number": create_github_fix_issue(error_report),
        "tags": ["auto-generated", "error-fix", error_report.error_type]
    })

    return {
        "original_feature": original_feature,
        "fix_task": fix_task,
        "error_report": error_report
    }
```

### UI Updates (Panel 5)

**Failed Status Display**:
- Red card background for failed items
- Error icon with tooltip showing error_summary
- "Retry Count" badge
- Link to error report details
- Highlight child fix task

**Fix Task Card**:
- Yellow/orange "Fix Required" banner
- Parent issue reference with link
- Error type badge
- One-click "Launch Fix Workflow" button
- Estimated vs actual hours tracking

## Cleanup Operations

### GitHub Integration

**On Workflow Failure**:
```python
async def handle_workflow_failure(error_report: ErrorReport):
    """Post failure details to GitHub issue."""

    comment_body = f"""
## Workflow Failed - {error_report.failed_phase.upper()} Phase

**Error Type:** {error_report.error_type}
**Failed At:** {error_report.failed_at}

### Error Summary
{error_report.error_message}

### Root Cause Analysis
{error_report.root_cause}

### Recommended Fix
- **Strategy:** {error_report.fix_strategy}
- **Estimated Time:** {error_report.estimated_fix_hours}h
- **Workflow:** `{error_report.recommended_workflow}`

### Affected Files
{format_file_list(error_report.affected_files)}

---

**Fix Issue Created:** #{fix_issue_number}
**Status:** This workflow has been marked as failed. A fix task has been created and added to the Plans Panel.
"""

    gh.post_issue_comment(error_report.issue_number, comment_body)
    gh.add_label(error_report.issue_number, "workflow-failed")
    gh.add_label(error_report.issue_number, f"error:{error_report.error_type}")
```

### Worktree Cleanup

**Configurable cleanup policy**:
```python
CLEANUP_POLICY = {
    "immediate": [
        "syntax",  # Always cleanup syntax errors (quick fix)
        "type"     # Type errors are quick fixes
    ],
    "on_fix_start": [
        "test",    # Keep worktree until fix starts
        "lint",
        "integration"
    ],
    "manual": [
        "build",      # May need investigation
        "resource",   # May be environmental
        "timeout"     # May be transient
    ]
}

async def cleanup_worktree(error_report: ErrorReport):
    """Cleanup worktree based on error type."""

    cleanup_policy = get_cleanup_policy(error_report.error_type)

    if cleanup_policy == "immediate":
        # Remove worktree immediately
        await remove_worktree(error_report.workflow_id)
        log_cleanup(error_report.workflow_id, "immediate")

    elif cleanup_policy == "on_fix_start":
        # Mark for cleanup when fix workflow starts
        await mark_for_deferred_cleanup(error_report.workflow_id)

    else:  # manual
        # Notify user, wait for manual cleanup
        await notify_manual_cleanup_required(error_report.workflow_id)
```

### Database Updates

**workflow_history table**:
```sql
UPDATE workflow_history
SET status = 'failed',
    error_type = %s,
    error_message = %s,
    failed_at = NOW(),
    completed_at = NOW()
WHERE workflow_id = %s;
```

**hook_events table** (capture failure event):
```sql
INSERT INTO hook_events (
    event_type,
    workflow_id,
    tool_name,
    context_snapshot,
    success,
    error_message,
    created_at
) VALUES (
    'WorkflowFailure',
    %s,  -- workflow_id
    %s,  -- failed phase
    %s,  -- error context JSON
    FALSE,
    %s,  -- error message
    NOW()
);
```

## Fix Prompt Generation

### Prompt Template

```markdown
# Task: Fix Failed Workflow - {error_type}

## Context
Working on tac-webbuilder. Workflow {workflow_id} failed during {failed_phase} phase.

**Original Issue:** #{issue_number} - {original_title}
**Failed At:** {failed_at}
**Error Type:** {error_type}

## Error Summary

{error_message}

## Root Cause Analysis

{root_cause}

## Affected Files

{affected_files_with_line_numbers}

## Fix Strategy

**Recommended Approach:** {fix_strategy}
**Estimated Time:** {estimated_hours}h
**Confidence:** {confidence}

{fix_description}

## Implementation Steps

{generated_steps_based_on_error_type}

## Verification

After fixing:
1. Run tests: `cd app/server && uv run pytest {affected_test_files}`
2. Verify build: `cd app/client && bun run build`
3. Check lint: `bun run lint`
4. Launch fix workflow: `uv run {recommended_workflow} {fix_issue_number}`

## Success Criteria

- [ ] Error no longer occurs
- [ ] All tests pass
- [ ] Build succeeds
- [ ] No new errors introduced
- [ ] Original issue can be retried

---

**Parent Workflow:** {workflow_id}
**Original Issue:** #{issue_number}
**Fix Issue:** #{fix_issue_number}
```

### One-Click Fix Launch

**Panel 5 UI Integration**:
```typescript
const handleLaunchFix = async (fixTask: PlannedFeature) => {
    // Generate prompt from error report
    const prompt = await generateFixPrompt(fixTask.error_id);

    // Copy prompt to clipboard
    await navigator.clipboard.writeText(prompt);

    // Show confirmation modal
    showModal({
        title: "Fix Prompt Ready",
        message: "Prompt copied to clipboard. Open new Claude Code chat and paste to start fix workflow.",
        actions: [
            {
                label: "Open GitHub Issue",
                onClick: () => window.open(`https://github.com/user/repo/issues/${fixTask.github_issue_number}`)
            },
            {
                label: "View Error Report",
                onClick: () => setActiveErrorReport(fixTask.error_id)
            }
        ]
    });

    // Update Plans Panel - mark as in_progress
    await updateFeature(fixTask.id, {
        status: "in_progress",
        started_at: new Date().toISOString()
    });
};
```

## Integration with Closed-Loop System

### Post-Failure Hooks

**Integrate with existing post-workflow hooks**:
```python
# In adws/adw_sdlc_complete_iso.py

async def run_phase_with_error_handling(phase_name: str, phase_func: callable):
    """Execute phase with error handling wrapper."""

    try:
        result = await phase_func()
        return result

    except WorkflowException as e:
        # Capture error context
        error_context = capture_error_context(
            phase_name=phase_name,
            exception=e,
            adw_state=load_adw_state(),
            workflow_id=workflow_id
        )

        # Trigger error handler sub-agent
        error_report = await trigger_error_analysis_agent(error_context)

        # Update Plans Panel
        await update_plans_panel_failure(
            issue_number=issue_number,
            error_report=error_report
        )

        # Run cleanup
        await run_failure_cleanup(
            workflow_id=workflow_id,
            error_report=error_report
        )

        # Generate and save fix prompt
        fix_prompt = generate_fix_prompt(error_report)
        save_fix_prompt(fix_prompt, error_report.error_id)

        # Notify user
        await notify_user_of_failure(error_report)

        # Re-raise to stop workflow
        raise
```

## Monitoring & Analytics

### Error Analytics Dashboard (Future - Panel 6/7/9)

**Metrics to Track**:
- Error frequency by type
- Most common error types
- Average time to fix by error type
- Retry success rate
- Failed phase distribution
- Error trends over time

**Database Queries**:
```sql
-- Error frequency by type (last 30 days)
SELECT
    error_type,
    COUNT(*) as occurrence_count,
    AVG(retry_count) as avg_retries,
    AVG(EXTRACT(EPOCH FROM (completed_at - failed_at))/3600) as avg_fix_hours
FROM planned_features
WHERE status = 'failed'
  AND failed_at > NOW() - INTERVAL '30 days'
GROUP BY error_type
ORDER BY occurrence_count DESC;

-- Success rate of fix workflows
SELECT
    parent.error_type,
    COUNT(CASE WHEN child.status = 'completed' THEN 1 END) as fixes_succeeded,
    COUNT(CASE WHEN child.status = 'failed' THEN 1 END) as fixes_failed,
    ROUND(
        100.0 * COUNT(CASE WHEN child.status = 'completed' THEN 1 END) / COUNT(*),
        2
    ) as success_rate
FROM planned_features parent
JOIN planned_features child ON child.parent_id = parent.id
WHERE parent.status = 'failed'
GROUP BY parent.error_type
ORDER BY success_rate DESC;
```

## Implementation Phases

### Phase 1: Foundation (1h)
- [ ] Create error_analyzer subagent type
- [ ] Implement error context capture utility
- [ ] Add phase-level error handling wrapper
- [ ] Create error report data models

### Phase 2: Analysis Engine (1h)
- [ ] Implement error classification logic
- [ ] Build root cause analysis prompts
- [ ] Create fix strategy recommender
- [ ] Generate error report JSON

### Phase 3: Plans Panel Integration (0.5h)
- [ ] Add "failed" status to database (migration 020)
- [ ] Create mark-failed API endpoint
- [ ] Update UI to display failed items
- [ ] Add one-click fix button

### Phase 4: Cleanup & Prompt Generation (0.5h)
- [ ] Implement GitHub comment posting
- [ ] Add worktree cleanup policies
- [ ] Create fix prompt generator
- [ ] Build clipboard copy functionality

### Testing & Validation (0.5h)
- [ ] Unit tests for error classification
- [ ] Integration test for full error flow
- [ ] E2E test with intentional failure
- [ ] Manual testing with various error types

## Dependencies

**Requires**:
- Closed-Loop Automation System foundation (Feature #99)
- Plans Panel with hierarchical features (Migration 017)
- Hook events system (existing)
- Workflow history tracking (existing)

**Blocks**:
- Full autonomous closed-loop operation
- Error analytics dashboard
- Pattern-based error prediction

## Success Criteria

- [ ] All 10 error types correctly classified
- [ ] Error analysis completes in <5 minutes
- [ ] Plans Panel shows failed status within 10 seconds
- [ ] Fix prompts include all necessary context
- [ ] One-click fix button works end-to-end
- [ ] Cleanup runs without manual intervention
- [ ] Failed workflows don't block new workflows
- [ ] Error reports are queryable for analytics

## Risk Assessment

**Low Risk**:
- Error detection (well-defined exception points)
- Plans Panel updates (existing API)
- Prompt generation (templating)

**Medium Risk**:
- Error analysis accuracy (depends on LLM quality)
- Root cause identification (may need iteration)
- Fix strategy confidence (heuristic-based)

**Mitigation**:
- Use conservative fix strategies (default to full workflow)
- Allow manual override of fix recommendations
- Track success rate and improve analysis prompts over time

## Future Enhancements

1. **Pattern-Based Error Prediction** (Session 25+)
   - Analyze past errors to predict failures before they occur
   - Suggest preventive measures during planning phase

2. **Auto-Fix for Common Errors** (Session 26+)
   - Automatically apply fixes for known error patterns
   - Skip sub-agent for simple syntax/type errors

3. **Error Analytics Dashboard** (Panel 6/7/9)
   - Visualize error trends
   - Identify systemic issues
   - Track fix success rates

4. **Cascading Error Prevention** (Session 27+)
   - Detect errors in error handler itself
   - Implement fallback mechanisms
   - Alert user if error handler fails

## Notes

- Error handling should NEVER fail silently
- Always prioritize data preservation (error context, logs)
- User notification is mandatory for all failures
- Fix prompts should be copy-pasteable and self-contained
- Cleanup should be cautious (keep data unless explicitly safe)

## References

- ADW Workflows: `.claude/commands/references/adw_workflows.md`
- Observability: `.claude/commands/references/observability.md`
- Plans Panel: `.claude/commands/references/planned_features.md`
- Loop Prevention: Issue #168 (Session 19)
- Closed-Loop Automation: Feature #99 (Parent)
