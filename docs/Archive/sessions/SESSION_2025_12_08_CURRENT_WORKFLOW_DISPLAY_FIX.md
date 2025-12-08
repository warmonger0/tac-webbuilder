# Session Summary: Current Workflow Display - Failed Workflows & Dynamic Phase Counts

**Date**: December 8, 2025
**Session ID**: session-2025-12-08-workflow-display
**Duration**: ~1.5 hours
**Commit**: ba2a2ce

## Overview

This session fixed critical issues preventing the Current Workflow card (Panel 1) from displaying the most recent workflow state. The user reported that despite workflow #142 failing to start 8 minutes ago, the UI continued showing completed workflow #140. Investigation revealed 5 distinct root causes spanning frontend, backend, and webhook systems.

## The Problem

**Observed Symptoms:**
- Current Workflow card showed workflow #140 (COMPLETED) instead of #142 (FAILED)
- Phase count always displayed "/9 phases" regardless of actual workflow configuration
- Failed workflows (that failed preflight checks) were completely invisible to the system
- Status updates didn't reflect:
  - a) Workflow failures
  - b) New workflow attempts
  - c) Appropriate step in workflow
  - d) Current status
  - e) Dynamic phase counts

**User Quote:**
> "Besides the uncommitted changes, the fact that we still have not figured out how to get the current workflow display in 1. new request panel of the front end, is mind boggling."

## Root Cause Analysis

### 1. Frontend - Poor Workflow Selection Logic

**Location**: `app/client/src/components/CurrentWorkflowCard.tsx:11-16`

**Problem:**
```typescript
// OLD: Only prioritizes running > paused > most recent
const workflow = useMemo(() => {
  if (!workflows.length) return null;
  return workflows.find(w => w.status === 'running')
    || workflows.find(w => w.status === 'paused')
    || workflows[0];
}, [workflows]);
```

**Issues:**
- Completely ignored `failed` status workflows
- Failed workflows never appeared as "current"
- No priority for most recent failures

### 2. Frontend - Hardcoded Phase Count

**Location**: `app/client/src/components/CurrentWorkflowCard.tsx:348`

**Problem:**
```typescript
// OLD: Hardcoded to 9 phases
<span>{workflow.phases_completed.length} / {workflowPhases.length} phases completed</span>
```

**Issues:**
- `workflowPhases` array is a static configuration with 9 phases
- Doesn't reflect actual workflow phase counts
- Different workflows may have different phase structures

### 3. Frontend - No Failed Status Badge

**Location**: `app/client/src/components/CurrentWorkflowCard.tsx:170-177`

**Problem:**
```typescript
// OLD: No case for 'failed' status
workflow.status === 'running' ? 'bg-emerald-500/20 text-emerald-300' :
workflow.status === 'paused' ? 'bg-yellow-500/20 text-yellow-300' :
workflow.status === 'completed' ? 'bg-blue-500/20 text-blue-300' :
'bg-slate-700 text-slate-400'
```

**Issues:**
- Failed workflows defaulted to generic gray styling
- No visual distinction for failures

### 4. Backend - Hardcoded Phase Count

**Location**: `app/server/core/adw_monitor.py:602`

**Problem:**
```python
# OLD: Hardcoded total_phases
workflow_status = {
    # ... other fields
    "total_phases": 9,  # Standard SDLC has 9 phases
}
```

**Issues:**
- Always returned 9 regardless of actual workflow
- `calculate_phase_progress()` calculated correctly but didn't return the value
- Frontend had no way to get actual phase count

### 5. Webhook - No Failed Workflow Tracking (THE CRITICAL BUG)

**Location**: `adws/adw_triggers/trigger_webhook.py:294-313`

**Problem:**
```python
# OLD: When preflight checks fail
can_proceed, preflight_error = can_launch_workflow(workflow, issue_number, provided_adw_id)
if not can_proceed:
    print(f"❌ Pre-flight check failed: {preflight_error}")
    # Posts GitHub comment
    make_issue_comment(...)
    return  # <-- NO STATE FILE CREATED!
```

**Issues:**
- Workflows that fail preflight checks post GitHub comments but never create state files
- `adw_monitor.py:scan_adw_states()` only reads `agents/{adw_id}/adw_state.json` files
- No state file = workflow is completely invisible to ADW monitor
- CurrentWorkflowCard never receives data about failed workflow
- This was the "mind-boggling" root cause

**Why Issue #142 Was Invisible:**
1. User tried to start workflow for issue #142
2. Preflight check detected uncommitted changes (blocking failure)
3. Webhook posted GitHub comment explaining the problem
4. Webhook returned without creating state file
5. ADW monitor had no knowledge of the attempt
6. Frontend continued showing old workflow #140

## Changes Made

### 1. Frontend - Fix Workflow Selection Priority

**File**: `app/client/src/components/CurrentWorkflowCard.tsx`

**Change:**
```typescript
// NEW: Prioritizes failed > running > paused > most recent
const workflow = useMemo(() => {
  if (!workflows.length) return null;
  return workflows.find(w => w.status === 'failed')
    || workflows.find(w => w.status === 'running')
    || workflows.find(w => w.status === 'paused')
    || workflows[0];
}, [workflows]);
```

**Impact:**
- Failed workflows now appear as "current workflow"
- Most urgent/problematic workflows get attention first
- Matches user expectations for real-time updates

### 2. Frontend - Use Dynamic Phase Count

**File**: `app/client/src/components/CurrentWorkflowCard.tsx`

**Change:**
```typescript
// NEW: Use workflow.total_phases from backend
<span>{workflow.phases_completed.length} / {workflow.total_phases} phases completed</span>
```

**Impact:**
- Shows accurate phase count per workflow
- Supports workflows with non-standard phase structures
- Eliminates hardcoded assumptions

### 3. Frontend - Add Failed Status Badge

**File**: `app/client/src/components/CurrentWorkflowCard.tsx`

**Change:**
```typescript
// NEW: Red badge for failed status
workflow.status === 'running' ? 'bg-emerald-500/20 text-emerald-300' :
workflow.status === 'paused' ? 'bg-yellow-500/20 text-yellow-300' :
workflow.status === 'completed' ? 'bg-blue-500/20 text-blue-300' :
workflow.status === 'failed' ? 'bg-red-500/20 text-red-300' :
'bg-slate-700 text-slate-400'
```

**Impact:**
- Failed workflows have clear visual indication
- Red color signals urgency/problems
- Consistent with standard UI patterns

### 4. Backend - Return Dynamic Phase Count

**File**: `app/server/core/adw_monitor.py`

**Changes:**

**a) Update `calculate_phase_progress()` signature** (line 324):
```python
# OLD: Returns 3 values
def calculate_phase_progress(adw_id: str, state: dict[str, Any]) -> tuple[str | None, float, list[str]]:

# NEW: Returns 4 values including total_phases
def calculate_phase_progress(adw_id: str, state: dict[str, Any]) -> tuple[str | None, float, list[str], int]:
```

**b) Return total_phases in all code paths** (lines 346, 353, 409):
```python
# OLD: 3 return values
return None, 0.0, []
return None, 0.0, []
return current_phase, round(progress, 1), completed_phases

# NEW: 4 return values
return None, 0.0, [], total_phases
return None, 0.0, [], total_phases
return current_phase, round(progress, 1), completed_phases, total_phases
```

**c) Unpack 4 values in `build_workflow_status()`** (line 556):
```python
# OLD: Unpack 3 values
current_phase, progress, completed_phases = calculate_phase_progress(adw_id, state)

# NEW: Unpack 4 values
current_phase, progress, completed_phases, total_phases = calculate_phase_progress(adw_id, state)
```

**d) Use dynamic value in workflow status** (line 602):
```python
# OLD: Hardcoded
"total_phases": 9,  # Standard SDLC has 9 phases

# NEW: Dynamic
"total_phases": total_phases,  # Dynamically calculated from workflow
```

**Impact:**
- Backend now sends accurate phase counts
- Supports workflows with custom phase structures
- Eliminates hardcoded assumptions at API level

### 5. Webhook - Create State Files for Failed Workflows

**File**: `adws/adw_triggers/trigger_webhook.py`

**Change** (lines 296-352):
```python
# Run comprehensive pre-flight checks
can_proceed, preflight_error = can_launch_workflow(workflow, issue_number, provided_adw_id)
if not can_proceed:
    print(f"❌ Pre-flight check failed: {preflight_error}")
    error_logger.warning(f"Pre-flight check failed for issue #{issue_number}: {preflight_error}")

    # NEW: Create state file for failed workflow so it appears in ADW monitor
    if not provided_adw_id:
        adw_id = make_adw_id()
    else:
        adw_id = provided_adw_id

    # Build GitHub URL for this issue
    repo_url = get_repo_url()
    repo_path = extract_repo_path(repo_url)
    github_url = f"https://github.com/{repo_path}/issues/{issue_number}"

    # Determine model_used based on model_set
    model_mapping = {
        "base": "sonnet",
        "heavy": "opus",
        "lightweight": "haiku"
    }
    model_used = model_mapping.get(model_set, "sonnet")

    # Create minimal state file for failed workflow
    state = ADWState(adw_id)
    state.update(
        adw_id=adw_id,
        issue_number=str(issue_number),
        model_set=model_set,
        status="failed",
        workflow_template=workflow,
        model_used=model_used,
        start_time=datetime.now().isoformat(),
        end_time=datetime.now().isoformat(),
        nl_input=content_to_check[:500],
        github_url=github_url,
        last_error=f"Preflight check failed: {preflight_error}"
    )
    state.save("webhook_trigger")
    print(f"💾 Created state file for failed workflow {adw_id} (issue #{issue_number})")

    try:
        make_issue_comment(
            str(issue_number),
            f"❌ **Cannot Start ADW Workflow**\n\n"
            f"{preflight_error}\n\n"
            f"**System Status:**\n"
            f"- Active worktrees: {count_active_worktrees()}/15\n"
            f"- Disk usage: {get_disk_usage()*100:.1f}%\n\n"
            f"The workflow will automatically retry when resources are available.\n\n"
            f"ADW ID: `{adw_id}` (for tracking)\n\n"  # NEW: Include ADW ID
            f"{ADW_BOT_IDENTIFIER}",
        )
    except Exception as e:
        print(f"Failed to post preflight error comment: {e}")
        error_logger.error(f"Failed to post preflight error comment: {e}")
    return
```

**Impact:**
- Failed workflows now create lightweight state files
- State files include:
  - `status="failed"` for proper categorization
  - `last_error` field with preflight failure message
  - Start/end timestamps (same time = instant failure)
  - All standard metadata (issue, workflow, model)
- ADW monitor can now track failed workflows
- Frontend receives data about failed attempts
- GitHub comments include ADW ID for tracking
- Solves the "mind-boggling" visibility problem

## System Architecture

### Current Workflow Display Data Flow

```
1. Webhook Trigger (adw_triggers/trigger_webhook.py)
   ├─ Receives GitHub issue event
   ├─ Runs preflight checks
   ├─ Creates ADWState file in agents/{adw_id}/adw_state.json
   │  ├─ Success: status="running", launches workflow
   │  └─ Failure: status="failed", includes error (NEW!)
   └─ Posts GitHub comment

2. ADW Monitor (core/adw_monitor.py)
   ├─ Scans agents/ directory for state files
   ├─ Reads all *_state.json files
   ├─ Calculates phase progress (returns total_phases - NEW!)
   ├─ Builds workflow status objects
   └─ Returns via /api/v1/adw/monitor endpoint

3. WebSocket Updates (routes/websocket_routes.py)
   ├─ Broadcasts workflow state changes
   ├─ Includes all workflow statuses (running, paused, failed, completed)
   └─ Real-time updates to connected clients

4. Frontend Hook (hooks/useWebSocket.tsx)
   ├─ Subscribes to adw-monitor WebSocket events
   ├─ Updates local workflows state
   └─ Triggers React re-render

5. CurrentWorkflowCard Component
   ├─ Receives workflows array from WebSocket
   ├─ Selects "current" workflow: failed > running > paused > recent (NEW!)
   ├─ Displays workflow.total_phases (NEW!)
   └─ Shows red badge for failed status (NEW!)
```

### State File Location

**Successful Workflows:**
```
agents/{adw_id}/adw_state.json
```

**Failed Workflows (NEW):**
```
agents/{adw_id}/adw_state.json  # Same location!
```

The key insight: Failed workflows now create state files in the SAME location as successful ones, just with `status="failed"` instead of `status="running"`.

## Testing Verification

### Manual Testing

**Test Case 1: Failed Workflow Visibility**
1. Ensure repository has uncommitted changes
2. Attempt to start new workflow (will fail preflight)
3. Expected behavior:
   - GitHub comment posted with error
   - State file created with status="failed"
   - CurrentWorkflowCard shows failed workflow
   - Red "FAILED" badge displayed
   - Error message visible in card

**Test Case 2: Dynamic Phase Counts**
1. Create workflow with non-standard phases
2. Launch workflow
3. Expected behavior:
   - Card shows actual phase count (e.g., "3 / 7 phases")
   - Not hardcoded to "/9 phases"

**Test Case 3: Workflow Priority**
1. Have multiple workflows in different states
2. Expected priority order:
   - Failed workflows shown first
   - Running workflows shown second
   - Paused workflows shown third
   - Most recent workflow shown last

### Edge Cases Handled

1. **No ADW ID provided + preflight failure**: Generates new ADW ID
2. **Existing ADW ID + preflight failure**: Uses provided ADW ID
3. **Multiple failed workflows**: Shows most recent failed
4. **Mixed status workflows**: Prioritizes correctly
5. **Empty workflow list**: Gracefully shows "No workflows" state

## Files Modified

### Frontend
- `app/client/src/components/CurrentWorkflowCard.tsx` (3 changes)
  - Line 11-16: Workflow selection priority
  - Line 171-177: Failed status badge
  - Line 349: Dynamic phase count display

### Backend
- `app/server/core/adw_monitor.py` (5 changes)
  - Line 324: Function signature (return 4 values)
  - Line 346: Return statement (4 values)
  - Line 353: Return statement (4 values)
  - Line 409: Return statement (4 values)
  - Line 556: Unpack 4 values
  - Line 602: Use dynamic total_phases

### Webhook
- `adws/adw_triggers/trigger_webhook.py` (1 major change)
  - Lines 296-352: Create state files for failed workflows

## Commit Information

**Commit Hash**: `ba2a2ce`

**Commit Message**:
```
fix: Fix current workflow display to show failed workflows and dynamic phase counts

This commit fixes 5 critical issues preventing proper workflow status display:

**Frontend Fixes (CurrentWorkflowCard.tsx):**
1. Workflow Selection Priority: Now prioritizes failed > running > paused > recent
2. Dynamic Phase Count: Uses workflow.total_phases instead of hardcoded 9
3. Failed Status Badge: Added red badge styling for failed status

**Backend Fixes (adw_monitor.py):**
1. Dynamic Total Phases: calculate_phase_progress() now returns total_phases
2. Workflow Status: Uses dynamic total_phases in workflow status object

**Webhook Fixes (trigger_webhook.py):**
1. Failed Workflow Tracking: Creates state files for failed-to-start workflows
```

## Impact & Benefits

### Before This Fix
- Failed workflows invisible to system
- Users confused by stale workflow display
- No way to track preflight failures
- Hardcoded phase counts misleading
- Poor real-time update UX

### After This Fix
- All workflow attempts tracked (success or failure)
- Failed workflows prioritized in UI
- Clear visual feedback (red badges)
- Accurate phase counts per workflow
- True real-time workflow state reflection

### User Experience Improvements
1. **Visibility**: Every workflow attempt is now tracked and visible
2. **Clarity**: Failed workflows clearly marked with red badges
3. **Accuracy**: Phase counts reflect actual workflow structure
4. **Transparency**: GitHub comments include ADW ID for tracking
5. **Priority**: Most urgent workflows (failed) appear first

### Developer Experience Improvements
1. **Debugging**: Failed workflows have state files for investigation
2. **Monitoring**: ADW monitor tracks all workflow attempts
3. **Traceability**: ADW IDs link GitHub issues to state files
4. **Flexibility**: Dynamic phase counts support workflow variations
5. **Consistency**: Same state file structure for success/failure

## Technical Debt Addressed

1. **Hardcoded Assumptions**: Eliminated hardcoded 9-phase assumption
2. **Silent Failures**: Preflight failures no longer invisible
3. **State Management**: Consistent state file creation for all workflows
4. **Priority Logic**: Frontend now properly prioritizes workflow states
5. **Visual Feedback**: All workflow states have appropriate styling

## Future Enhancements

### Potential Improvements
1. **Retry Mechanism**: Auto-retry failed workflows when conditions improve
2. **Failure Categories**: Categorize failures (git, quota, resources)
3. **Notification System**: Alert users of failed workflows
4. **Analytics**: Track failure patterns and common causes
5. **Recovery UI**: Add "Retry" button for failed workflows

### Related Work
- Session 16: WebSocket migration (5/6 components complete)
- Session 18: Health checks & observability
- Planned: Auto-retry system for transient failures

## Lessons Learned

1. **Multi-Layer Debugging**: Issue spanned frontend, backend, and webhook systems
2. **State File Importance**: State files are the source of truth for ADW monitor
3. **Silent Failures**: System must track failures as explicitly as successes
4. **Visual Feedback**: Clear status indication critical for UX
5. **Dynamic Configuration**: Avoid hardcoded assumptions about workflow structure

## Conclusion

This session resolved a critical visibility issue that made failed workflow attempts completely invisible to the system. The fix required changes across three layers (frontend, backend, webhook) but resulted in a robust solution that:

1. Tracks all workflow attempts (success or failure)
2. Provides clear visual feedback for all states
3. Supports dynamic workflow configurations
4. Maintains consistent state management
5. Improves both user and developer experience

The "mind-boggling" issue turned out to be a missing state file creation step in the webhook preflight failure path - a simple oversight with significant UX impact.

---

**Next Steps:**
1. Monitor failed workflow tracking in production
2. Consider implementing auto-retry for transient failures
3. Add analytics for failure patterns
4. Enhance UI with recovery actions
