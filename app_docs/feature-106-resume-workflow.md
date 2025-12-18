# Feature: Resume Workflow

**Issue:** #106
**Status:** Implemented
**Session:** December 2025 (Previous session + cleanup)

## Overview

Allows users to resume paused ADW workflows through a dedicated API endpoint and UI button. The feature runs preflight checks before resuming to ensure the system is in a valid state.

## Implementation

### Backend

**Endpoint:** `POST /api/v1/queue/resume/{adw_id}`

**Handler Function:** `_resume_adw_handler()` in `app/server/routes/queue_routes.py:289-381`

**Flow:**
1. Run preflight checks with `skip_tests=True` for faster execution
2. Check if Git State preflight failed (uncommitted changes)
3. If git dirty: Return 400 error with clear message to commit/stash
4. If other checks fail: Return 400 error listing blocking failures
5. Read ADW state from `agents/{adw_id}/adw_state.json`
6. Build command: `uv run {workflow_template}.py {issue_number} {adw_id}`
7. Launch workflow in background using `subprocess.Popen()`
8. Return success response with ADW info and preflight duration

**Key Design Decisions:**
- **No auto-commit/stash:** User must manually handle uncommitted changes
- **skip_tests=True:** Preflight checks run faster without running full test suite
- **Background execution:** Workflow runs in separate process to avoid blocking API

### Frontend

**API Client:** `app/client/src/api/queueClient.ts:247-271`

```typescript
export async function resumeAdw(adwId: string): Promise<ResumeResponse> {
  return apiPost<ResumeResponse>(`${API_BASE}/queue/resume/${adwId}`);
}
```

**UI Component:** `app/client/src/components/CurrentWorkflowCard.tsx:221-269`

**Features:**
- Resume button only visible when `workflow.status === 'paused'`
- Loading state: "Running Preflight Checks..."
- Success message (auto-clears after 5s)
- Error message (auto-clears after 10s)
- Disabled state while loading

**Visual Design:**
- Gradient button: emerald-600 to teal-600
- Play icon with "Resume Workflow" text
- Help text: "Workflow is paused. Click Resume to run preflight checks and continue to the next phase."

## Testing

**Manual Test:**
```bash
# Test endpoint directly
curl -X POST http://localhost:8002/api/v1/queue/resume/adw-29336056

# Expected responses:
# - 400: "Preflight checks failed: Uncommitted changes detected..."
# - 200: {"success": true, "message": "ADW {adw_id} resumed successfully", ...}
```

**UI Test:**
1. Navigate to Panel 2 (Current Workflow)
2. Ensure workflow status is "paused"
3. Click "Resume Workflow" button
4. Verify preflight checks run
5. Verify workflow resumes or error is displayed

## Error Handling

### Uncommitted Changes (400)
```json
{
  "detail": "Preflight checks failed: Uncommitted changes detected. Please commit or stash your changes before resuming the workflow."
}
```

### Other Preflight Failures (400)
```json
{
  "detail": "Preflight checks failed. Cannot resume workflow. Failures: GitHub Auth, Database Connection"
}
```

### ADW Directory Not Found (404)
```json
{
  "detail": "ADW directory not found: adw-abc123"
}
```

### ADW State File Missing (404)
```json
{
  "detail": "ADW state file not found for adw-abc123"
}
```

### No Issue Number in State (400)
```json
{
  "detail": "ADW adw-abc123 has no issue number in state"
}
```

### Workflow Script Not Found (500)
```json
{
  "detail": "Workflow script not found: /path/to/adws/adw_sdlc_complete_iso.py"
}
```

## Related Files

**Backend:**
- `app/server/routes/queue_routes.py` (289-381, 538-547)
- `app/server/core/preflight_checks.py` (preflight check implementation)

**Frontend:**
- `app/client/src/api/queueClient.ts` (247-271, 311)
- `app/client/src/components/CurrentWorkflowCard.tsx` (1-52, 221-269)

**Documentation:**
- `.claude/commands/quick_start/backend.md` (Resume Workflow section)
- `docs/troubleshooting.md` (PostgreSQL PoolError section)
- `scripts/start_full_clean.sh` (reliable startup script)

## Integration with Preflight Checks

**Preflight Checks Run:**
1. Git State (main requirement - must be clean)
2. GitHub Authentication
3. Environment Variables
4. Database Connection
5. Required Tools Installed
6. Port Availability
7. File Permissions

**Performance:**
- With `skip_tests=True`: ~1-3 seconds
- Without skip: ~30-60 seconds (includes pytest run)

## Known Limitations

1. **No auto-recovery:** User must manually fix preflight failures
2. **Git state required:** Workflow cannot resume with dirty working tree
3. **Single ADW at a time:** Backend doesn't queue multiple resume requests
4. **No progress feedback:** After launching, no real-time progress updates during resume

## Future Enhancements

1. Auto-stash option for uncommitted changes
2. Resume with specific phase override
3. Dry-run mode (check without launching)
4. Queue multiple resume requests
5. Real-time progress notifications via WebSocket
6. Resume history tracking

## Session Notes

**Original Implementation:** Previous session (Issue #224)
- Added endpoint, API client, UI button
- Tested with paused workflow adw-29336056

**Cleanup Session:** 2025-12-18
- Created reliable startup script (`start_full_clean.sh`)
- Documented PostgreSQL PoolError workaround
- Verified endpoint works correctly
- Updated documentation

## Related Issues

- **#106:** Resume workflow feature request
- **#224:** Test workflow used during implementation
- **#168:** Loop prevention (related to workflow control)
