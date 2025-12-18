# Feature: Workflow Resume Functionality

## Overview
Workflows can now resume from where they paused instead of restarting from Phase 1. This eliminates wasted time and resources when workflows are interrupted or paused due to rate limits, errors, or manual intervention.

## Problem Solved
**Before:** When clicking "Resume" on a paused workflow, the system would restart from Phase 1 even if Phases 1-3 were already completed. This wasted time, compute resources, and API costs.

**After:** The system tracks which phases have been completed and automatically skips them when resuming, starting from the first incomplete phase.

## Architecture

### Components

1. **PhaseTracker Module** (`/adws/adw_modules/phase_tracker.py`)
   - Tracks phase completion in `agents/{adw_id}/completed_phases.json`
   - Provides methods to check completion, mark phases complete, and determine next phase
   - Stores completion data with timestamps

2. **Resume Flag in Backend** (`/app/server/routes/queue_routes.py`)
   - Resume endpoint now passes `--resume` flag to workflow scripts
   - Command: `["uv", "run", workflow_script, str(issue_number), adw_id, "--resume"]`

3. **Workflow Script Integration** (`/adws/adw_sdlc_complete_iso.py`)
   - Detects `--resume` flag and enters resume mode
   - Loads completion state and skips completed phases
   - Marks each phase as completed after successful execution

### Data Storage

**File:** `agents/{adw_id}/completed_phases.json`

```json
{
  "completed": ["Plan", "Validate", "Build", "Lint"],
  "current": "Test",
  "last_updated": "2025-12-18T10:30:45"
}
```

## Usage

### From UI
1. Navigate to System Status dashboard
2. Find a paused workflow in the Git Commit UI panel
3. Click "Resume" button
4. Workflow resumes from the first incomplete phase

### From CLI
```bash
# Resume a workflow manually
uv run adws/adw_sdlc_complete_iso.py <issue-number> <adw-id> --resume
```

### From API
```bash
# POST to resume endpoint
curl -X POST http://localhost:8000/queue/resume/{adw_id}
```

## Implementation Details

### Phase Completion Tracking

Each phase is marked as completed immediately after successful execution:

```python
# Before running phase
if phase_tracker.should_skip_phase("Build", resume_mode):
    print("PHASE 3: BUILD - SKIPPED (already completed)")
    logger.info("Skipping Build phase (already completed)")
else:
    # Run phase...
    phase_tracker.set_current_phase("Build")
    exit_code = run_phase_with_retry(...)

    # Mark as completed after success
    phase_tracker.mark_phase_completed("Build")
    logger.info("✅ Build phase marked as completed")
```

### Resume Mode Detection

```python
# Workflow script checks for --resume flag
resume_mode = "--resume" in sys.argv

if resume_mode:
    completed_phases = phase_tracker.get_completed_phases()
    next_phase = phase_tracker.get_next_phase_to_run(ALL_PHASES)

    print(f"Completed phases: {', '.join(completed_phases)}")
    print(f"Resuming from: {next_phase}")
```

### Phase Definitions

All 10 phases in order:
1. Plan
2. Validate
3. Build
4. Lint
5. Test
6. Review
7. Document
8. Ship
9. Cleanup
10. Verify

## Benefits

### Time Savings
- **Before:** Pausing after Phase 5 and resuming = 10 phases executed (5 wasted)
- **After:** Pausing after Phase 5 and resuming = 5 phases executed (0 wasted)
- **Savings:** 50% reduction in redundant work

### Cost Savings
- Avoids re-running expensive LLM calls for completed phases
- Reduces API usage and token consumption
- Minimizes compute resources

### Reliability
- Works seamlessly with rate limit pausing
- Handles manual pauses/interruptions
- Idempotent phase execution ensures safety

## Testing

### Manual Test Procedure

1. **Start a workflow:**
   ```bash
   uv run adws/adw_sdlc_complete_iso.py 123 adw-test-001
   ```

2. **Pause after Phase 3 completes:**
   - Press Ctrl+C after "Build phase marked as completed"
   - Or let it pause due to rate limit

3. **Verify completion tracking:**
   ```bash
   cat agents/adw-test-001/completed_phases.json
   # Should show: {"completed": ["Plan", "Validate", "Build"], ...}
   ```

4. **Resume the workflow:**
   ```bash
   uv run adws/adw_sdlc_complete_iso.py 123 adw-test-001 --resume
   ```

5. **Verify phases are skipped:**
   - Output should show: "PHASE 1: PLAN - SKIPPED (already completed)"
   - Output should show: "PHASE 2: VALIDATE - SKIPPED (already completed)"
   - Output should show: "PHASE 3: BUILD - SKIPPED (already completed)"
   - Should start executing at Phase 4 (Lint)

### Expected Behavior

**Resume Mode Output:**
```
============================================================
🔄 RESUME MODE
============================================================
Completed phases: Plan, Validate, Build
Resuming from: Lint
============================================================

============================================================
PHASE 1/10: PLAN - ⏭️  SKIPPED (already completed)
============================================================

============================================================
PHASE 2/10: VALIDATE - ⏭️  SKIPPED (already completed)
============================================================

============================================================
PHASE 3/10: BUILD - ⏭️  SKIPPED (already completed)
============================================================

============================================================
PHASE 4/10: LINT
============================================================
Running: uv run .../adw_lint_iso.py 123 adw-test-001
...
```

## Edge Cases Handled

1. **All phases already completed:**
   - Workflow exits gracefully with "All phases already completed, nothing to resume"

2. **Resume on fresh workflow:**
   - No completion file exists, behaves like normal start

3. **Clean start flag:**
   - `--clean-start` resets phase tracker before starting
   - Ensures fresh execution from Phase 1

4. **Concurrent fresh start and resume:**
   - Resume flag has priority (explicit user intent)
   - Clean start only applies when not resuming

## Future Enhancements

### Potential Improvements

1. **Phase-level checkpointing:**
   - Store intermediate results for each phase
   - Allow resuming within a failed phase (not just after completion)

2. **Partial phase execution:**
   - Track sub-steps within phases
   - Resume from specific agent calls within a phase

3. **Dashboard visualization:**
   - Show completed vs remaining phases in UI
   - Display phase progress bar

4. **Resume strategies:**
   - Add `--force-rerun` to re-execute specific phases
   - Add `--from-phase` to start from arbitrary phase

5. **Multi-workflow coordination:**
   - Share completion state across related workflows
   - Parent/child workflow resume dependencies

## Related Files

### Core Implementation
- `/adws/adw_modules/phase_tracker.py` - Phase completion tracking
- `/adws/adw_sdlc_complete_iso.py` - Workflow script with resume logic
- `/app/server/routes/queue_routes.py` - Resume endpoint with --resume flag

### Testing
- Test manually with the procedure above
- Future: Add automated integration tests

### Documentation
- This file: Feature documentation
- `/adws/adw_sdlc_complete_iso.py` docstring: Usage documentation

## Version History

### v1.0 (2025-12-18)
- Initial implementation of workflow resume functionality
- Phase completion tracking with JSON file storage
- Resume mode detection and phase skipping
- Integration with Resume button in UI
