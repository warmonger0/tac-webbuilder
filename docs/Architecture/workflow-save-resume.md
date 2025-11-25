# Workflow Save/Resume System Architecture

## Executive Summary

This document outlines a comprehensive save/resume system for tac-webbuilder's ADW (Automated Development Workflow) multi-phase workflows. The system enables workflows to be paused, saved, and resumed from checkpoints, preventing duplicate work and allowing graceful interruption/recovery.

**Key Goals:**
- Zero data loss on interruption (system crash, manual pause, errors)
- Resume workflows from last successful checkpoint
- Handle edge cases (deleted worktrees, stale state, code changes)
- Minimal performance overhead (checkpoint after each phase)
- Backward compatible with existing running workflows

**Current State:**
- ✅ Individual phase scripts support basic resume via `all_adws` array
- ✅ State persisted in `agents/{adw_id}/adw_state.json`
- ❌ No explicit pause/resume API or UI
- ❌ ZTE (complete SDLC) workflows don't support resume
- ❌ No stale state detection or cleanup
- ❌ No mid-phase checkpoint recovery

---

## 1. System Architecture

### 1.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Workflow Execution                          │
│                                                                 │
│  Start ──┬──> Phase 1 ──> [Checkpoint] ──> Phase 2 ──> [Checkpoint]
│          │                    │                           │     │
│          │                    ▼                           ▼     │
│          │              Save State                   Save State │
│          │                                                       │
│          └──> Resume ──> Validate ──> Restore ──> Continue      │
│                 Detection    State      Context    from Last    │
│                                                    Checkpoint    │
└─────────────────────────────────────────────────────────────────┘

Storage Layers:
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  adw_state.json  │  │ workflow_history │  │  phase_queue.db  │
│  (File System)   │  │      .db         │  │  (Coordinator)   │
│                  │  │  (Analytics)     │  │                  │
│ • Phase progress │  │ • Status/metrics │  │ • Multi-phase    │
│ • Worktree info  │  │ • Cost tracking  │  │   orchestration  │
│ • Port allocs    │  │ • Error logs     │  │ • Dependencies   │
│ • Results cache  │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### 1.2 Component Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Checkpoint Manager                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ CheckpointService                                       │ │
│  │  • create_checkpoint()                                  │ │
│  │  • validate_checkpoint()                                │ │
│  │  • list_resumable()                                     │ │
│  │  • cleanup_stale()                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                   State Persistence Layer                     │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ ADWState         │  │ WorkflowHistory  │                 │
│  │ (File-based)     │  │ (SQLite-based)   │                 │
│  └──────────────────┘  └──────────────────┘                 │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                    Resume Orchestrator                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ResumeService                                           │ │
│  │  • detect_incomplete()                                  │ │
│  │  • validate_resume_state()                              │ │
│  │  • restore_worktree()                                   │ │
│  │  • resume_from_checkpoint()                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                      API Endpoints                            │
│  POST /api/workflow/pause                                     │
│  POST /api/workflow/resume                                    │
│  GET  /api/workflow/resumable                                 │
│  GET  /api/workflow/{adw_id}/checkpoints                      │
│  DELETE /api/workflow/{adw_id}/checkpoint/{checkpoint_id}     │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. State Schema

### 2.1 Enhanced ADWState (agents/{adw_id}/adw_state.json)

```json
{
  // Core identification (existing)
  "adw_id": "adw-3af4a34d",
  "issue_number": 83,
  "branch_name": "feature-issue-83-...",
  "plan_file": "specs/issue-83-...",
  "issue_class": "/feature",

  // Resource allocation (existing)
  "worktree_path": "/path/to/trees/adw-3af4a34d",
  "backend_port": 9108,
  "frontend_port": 9208,
  "model_set": "base",

  // Progress tracking (existing)
  "all_adws": ["adw_plan_iso", "adw_build_iso"],

  // NEW: Checkpoint metadata
  "checkpoint_version": "1.0",
  "last_checkpoint_time": "2025-11-25T10:30:45Z",
  "current_phase": {
    "name": "build",
    "status": "completed",
    "started_at": "2025-11-25T10:15:00Z",
    "completed_at": "2025-11-25T10:30:45Z",
    "error": null
  },

  // NEW: Resume metadata
  "resume_metadata": {
    "can_resume": true,
    "resume_from_phase": "lint",
    "last_known_good_commit": "abc123...",
    "uncommitted_files": [],
    "stale_reasons": []
  },

  // NEW: Phase results cache (for resume validation)
  "phase_results": {
    "plan": {
      "status": "completed",
      "output_files": ["specs/issue-83-..."],
      "checksum": "sha256:..."
    },
    "build": {
      "status": "completed",
      "build_artifacts": ["app/client/dist"],
      "typescript_errors": 0,
      "checksum": "sha256:..."
    }
  },

  // NEW: Resource state
  "resource_state": {
    "worktree_exists": true,
    "worktree_clean": false,
    "branch_exists": true,
    "ports_allocated": true,
    "ports_in_use": [9108, 9208]
  },

  // Cost tracking (existing)
  "estimated_cost_total": 0.45,
  "estimated_cost_breakdown": {...},

  // Workflow history sync fields (existing)
  "status": "running",
  "workflow_template": "adw_sdlc_complete_iso",
  "model_used": "claude-sonnet-4-5",
  "start_time": "2025-11-25T10:00:00Z"
}
```

### 2.2 Checkpoint History Table (New)

Add to `workflow_history.db`:

```sql
CREATE TABLE workflow_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,  -- UUID
    adw_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    checkpoint_time TEXT NOT NULL,

    -- State snapshot (JSON)
    state_snapshot TEXT NOT NULL,  -- Full adw_state.json at checkpoint time

    -- Validation data
    git_commit TEXT,               -- Commit SHA at checkpoint time
    worktree_path TEXT,
    uncommitted_files TEXT,        -- JSON array of file paths

    -- Resource state
    backend_port INTEGER,
    frontend_port INTEGER,
    worktree_exists BOOLEAN,

    -- Metadata
    can_resume BOOLEAN DEFAULT 1,
    stale BOOLEAN DEFAULT 0,
    stale_reason TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (adw_id) REFERENCES workflow_history(adw_id)
);

CREATE INDEX idx_checkpoint_adw_id ON workflow_checkpoints(adw_id);
CREATE INDEX idx_checkpoint_time ON workflow_checkpoints(checkpoint_time DESC);
CREATE INDEX idx_checkpoint_can_resume ON workflow_checkpoints(can_resume);
```

### 2.3 Enhanced Workflow History Fields

Add to `workflow_history` table:

```sql
ALTER TABLE workflow_history ADD COLUMN last_checkpoint_time TEXT;
ALTER TABLE workflow_history ADD COLUMN resume_count INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN pause_count INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN paused_at TEXT;
ALTER TABLE workflow_history ADD COLUMN resumed_at TEXT;
```

---

## 3. API Specification

### 3.1 Pause Workflow

```
POST /api/workflow/pause

Request:
{
  "adw_id": "adw-3af4a34d",
  "reason": "manual_pause" | "system_shutdown" | "resource_constraint"
}

Response:
{
  "success": true,
  "checkpoint_id": "ckpt-abc123...",
  "checkpoint_time": "2025-11-25T10:30:45Z",
  "current_phase": "build",
  "can_resume": true,
  "resume_from_phase": "lint"
}
```

**Implementation:**
1. Check if workflow is running (query `workflow_history`)
2. Create checkpoint with current state
3. Update workflow status to "paused"
4. Preserve worktree and ports (don't clean up)
5. Post GitHub comment notifying pause

### 3.2 Resume Workflow

```
POST /api/workflow/resume

Request:
{
  "adw_id": "adw-3af4a34d",
  "checkpoint_id": "ckpt-abc123..."  // optional, uses latest if omitted
}

Response:
{
  "success": true,
  "validation": {
    "worktree_exists": true,
    "branch_exists": true,
    "ports_available": true,
    "state_valid": true
  },
  "resume_phase": "lint",
  "workflow_pid": 12345
}

Error Response (422):
{
  "success": false,
  "error": "stale_state",
  "details": {
    "worktree_exists": false,
    "stale_reasons": ["worktree_deleted", "branch_gone"]
  },
  "recovery_options": [
    "recreate_worktree",
    "restart_workflow",
    "cleanup_and_retry"
  ]
}
```

**Implementation:**
1. Load checkpoint state
2. Validate resume conditions (worktree exists, branch exists, etc.)
3. Restore context (git checkout, port allocation)
4. Determine resume phase (next phase after last completed)
5. Launch workflow with `--resume-from={phase}` flag
6. Update workflow status to "running"

### 3.3 List Resumable Workflows

```
GET /api/workflow/resumable

Response:
{
  "resumable": [
    {
      "adw_id": "adw-3af4a34d",
      "issue_number": 83,
      "workflow_template": "adw_sdlc_complete_iso",
      "last_checkpoint": "2025-11-25T10:30:45Z",
      "paused_phase": "build",
      "resume_from_phase": "lint",
      "can_resume": true,
      "stale": false,
      "worktree_exists": true,
      "age_hours": 2.5
    }
  ]
}
```

### 3.4 Get Workflow Checkpoints

```
GET /api/workflow/{adw_id}/checkpoints

Response:
{
  "checkpoints": [
    {
      "checkpoint_id": "ckpt-abc123...",
      "phase_name": "build",
      "checkpoint_time": "2025-11-25T10:30:45Z",
      "git_commit": "abc123...",
      "can_resume": true,
      "stale": false
    },
    {
      "checkpoint_id": "ckpt-def456...",
      "phase_name": "plan",
      "checkpoint_time": "2025-11-25T10:15:00Z",
      "git_commit": "abc123...",
      "can_resume": true,
      "stale": false
    }
  ]
}
```

### 3.5 Delete Checkpoint

```
DELETE /api/workflow/{adw_id}/checkpoint/{checkpoint_id}

Response:
{
  "success": true,
  "deleted_checkpoint_id": "ckpt-abc123..."
}
```

---

## 4. Implementation Phases

### Phase 1: Checkpoint Infrastructure (Week 1)

**Goal:** Create checkpoint storage and basic save functionality

**Tasks:**
1. Add `workflow_checkpoints` table to database
2. Create `CheckpointService` class
   - `create_checkpoint(adw_id, phase_name, state_data)`
   - `get_latest_checkpoint(adw_id)`
   - `list_checkpoints(adw_id)`
3. Enhance `ADWState.save()` to create checkpoints
4. Add checkpoint creation after each phase in `adw_sdlc_complete_iso.py`
5. Write unit tests for checkpoint creation

**Deliverables:**
- `app/server/services/checkpoint_service.py`
- Database migration script
- Tests in `app/server/tests/services/test_checkpoint_service.py`

### Phase 2: Pause Functionality (Week 1-2)

**Goal:** Enable manual workflow pausing

**Tasks:**
1. Create `/api/workflow/pause` endpoint
2. Implement pause logic:
   - Create checkpoint
   - Update workflow status to "paused"
   - Preserve resources (worktree, ports)
   - Post GitHub comment
3. Add "Pause Workflow" button to UI (WorkflowProgressVisualization)
4. Add pause handling to `PhaseCoordinator`
5. Write integration tests for pause flow

**Deliverables:**
- `app/server/routes/workflow_pause_routes.py`
- UI component updates
- Integration tests

### Phase 3: Resume Detection & Validation (Week 2)

**Goal:** Detect incomplete workflows and validate resume conditions

**Tasks:**
1. Create `ResumeService` class
   - `detect_incomplete_workflows()`
   - `validate_resume_state(adw_id)`
   - `check_worktree_exists(worktree_path)`
   - `check_branch_exists(branch_name)`
   - `check_ports_available(backend_port, frontend_port)`
2. Add stale state detection logic
3. Implement recovery suggestions
4. Create `/api/workflow/resumable` endpoint
5. Add resume validation to startup sequence

**Deliverables:**
- `app/server/services/resume_service.py`
- Resume validation tests
- API endpoint

### Phase 4: Resume Execution (Week 2-3)

**Goal:** Restore state and resume workflow execution

**Tasks:**
1. Add `--resume-from={phase}` flag to ZTE workflows
2. Implement resume logic in `adw_sdlc_complete_iso.py`:
   - Load checkpoint state
   - Skip completed phases
   - Resume from specified phase
3. Create `/api/workflow/resume` endpoint
4. Add worktree/branch restoration logic
5. Add port re-allocation logic
6. Write end-to-end resume tests

**Deliverables:**
- Enhanced ZTE workflow scripts with resume support
- Resume API endpoint
- E2E tests

### Phase 5: UI & Cleanup (Week 3)

**Goal:** User interface for managing saved workflows and cleanup

**Tasks:**
1. Create `ResumableWorkflowsCard` UI component
   - List paused/incomplete workflows
   - Show resume viability (green/yellow/red status)
   - "Resume" and "Cleanup" buttons
2. Add resume detection on system startup
3. Implement stale checkpoint cleanup (age > 7 days)
4. Add checkpoint management to `/api/workflow/{adw_id}/checkpoints`
5. Create admin dashboard for checkpoint monitoring
6. Documentation and user guide

**Deliverables:**
- `app/client/src/components/ResumableWorkflowsCard.tsx`
- Cleanup service and cron job
- User documentation

---

## 5. Edge Cases & Solutions

### 5.1 Workflow Paused Mid-Phase

**Problem:** Phase is running when pause is requested.

**Solution:**
- Set flag in `adw_state.json`: `"pause_requested": true`
- Phase checks flag periodically (every subprocess call)
- Phase completes current step, creates checkpoint, exits gracefully
- Next resume starts from next phase (not mid-step)

**Alternative:** Support mid-phase resume by saving uncommitted work:
- Store uncommitted files in checkpoint
- On resume, restore uncommitted files before continuing

### 5.2 Worktree Deleted Externally

**Problem:** User runs `./scripts/purge_tree.sh {adw_id}` while workflow is paused.

**Detection:**
- `validate_resume_state()` checks `os.path.exists(worktree_path)`
- Mark checkpoint as stale with reason "worktree_deleted"

**Recovery Options:**
1. **Recreate worktree:** Clone from branch if branch still exists
2. **Restart workflow:** Start fresh from phase 1
3. **Manual recovery:** User manually recreates worktree, then resume

### 5.3 Branch Deleted on GitHub

**Problem:** PR merged or branch deleted while workflow paused.

**Detection:**
- `validate_resume_state()` runs `git show-ref {branch_name}`
- Mark checkpoint as stale with reason "branch_gone"

**Recovery:**
- Cannot resume (branch is source of truth)
- Offer cleanup: Remove checkpoint, free resources
- Workflow marked as "completed_externally"

### 5.4 Port Conflict

**Problem:** Another workflow allocated same ports.

**Detection:**
- `validate_resume_state()` checks if ports are bound
- Query `workflow_history` for active workflows using ports

**Recovery:**
- Auto-allocate new ports
- Update `adw_state.json` with new ports
- Resume with new port configuration

### 5.5 State File Corrupted

**Problem:** `adw_state.json` has invalid JSON or missing required fields.

**Detection:**
- `ADWState.load()` catches `json.JSONDecodeError`
- Pydantic validation fails on load

**Recovery:**
1. **Restore from checkpoint:** Load from `workflow_checkpoints` table
2. **Reconstruct from workflow_history:** Rebuild minimal state
3. **Mark unrecoverable:** User must restart workflow

### 5.6 Multiple Resume Attempts

**Problem:** User clicks "Resume" multiple times before workflow starts.

**Prevention:**
- Add `resume_lock` flag in database
- Check lock before allowing resume
- Lock expires after 5 minutes (timeout safety)

### 5.7 Resume After Code Changes

**Problem:** Codebase changed between pause and resume (e.g., new phase added).

**Detection:**
- Compare `workflow_template` version in checkpoint vs current code
- Check if phase list changed

**Options:**
1. **Compatible changes:** Resume normally if phases are backward compatible
2. **Incompatible changes:** Warn user, offer restart
3. **Force resume:** Allow resume with `--force` flag (risk of errors)

### 5.8 System Shutdown During Execution

**Problem:** Server crash or restart while workflow running.

**Detection on Startup:**
- Query `workflow_history` for status="running" and no recent heartbeat
- Check if PID still exists

**Recovery:**
- Mark workflow as "interrupted"
- Create checkpoint from last known state
- Offer resume via UI dashboard

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Checkpoint Service:**
- ✅ Create checkpoint with valid state
- ✅ Retrieve latest checkpoint
- ✅ List all checkpoints for workflow
- ✅ Delete checkpoint
- ✅ Handle missing adw_id

**Resume Service:**
- ✅ Detect incomplete workflows
- ✅ Validate resume state (all conditions)
- ✅ Detect stale state (all reasons)
- ✅ Generate recovery suggestions

**ADWState:**
- ✅ Save with checkpoint metadata
- ✅ Load with checkpoint data
- ✅ Handle corrupted state file

### 6.2 Integration Tests

**Pause Flow:**
- ✅ Pause running workflow
- ✅ Checkpoint created correctly
- ✅ Workflow status updated
- ✅ Resources preserved (worktree, ports)
- ✅ GitHub comment posted

**Resume Flow:**
- ✅ Resume from latest checkpoint
- ✅ Resume from specific checkpoint
- ✅ Skip completed phases
- ✅ Continue from resume phase
- ✅ Handle validation failures

**Edge Cases:**
- ✅ Resume after worktree deleted
- ✅ Resume after branch deleted
- ✅ Resume with port conflict
- ✅ Prevent multiple resume attempts

### 6.3 End-to-End Tests

**Happy Path:**
```python
def test_pause_and_resume_workflow():
    # Start workflow
    adw_id = start_workflow(issue_number=123)

    # Wait for build phase to complete
    wait_for_phase(adw_id, "build")

    # Pause workflow
    response = pause_workflow(adw_id)
    assert response["success"] == True
    assert response["current_phase"] == "build"

    # Verify workflow paused
    status = get_workflow_status(adw_id)
    assert status == "paused"

    # Resume workflow
    response = resume_workflow(adw_id)
    assert response["success"] == True
    assert response["resume_phase"] == "lint"

    # Verify workflow continues
    wait_for_completion(adw_id)
    assert get_workflow_status(adw_id) == "completed"
```

**Stale State:**
```python
def test_resume_after_worktree_deleted():
    adw_id = start_workflow(issue_number=123)
    wait_for_phase(adw_id, "build")
    pause_workflow(adw_id)

    # Delete worktree externally
    subprocess.run(["./scripts/purge_tree.sh", adw_id])

    # Attempt resume
    response = resume_workflow(adw_id)
    assert response["success"] == False
    assert "worktree_deleted" in response["details"]["stale_reasons"]
    assert "recreate_worktree" in response["recovery_options"]
```

---

## 7. Migration Strategy

### 7.1 Existing Running Workflows

**Goal:** Don't disrupt workflows in progress when deploying resume system.

**Approach:**
1. Deploy with feature flag: `ENABLE_CHECKPOINTS=false` (default off)
2. Let existing workflows complete naturally
3. Enable checkpoints for new workflows only
4. No migration needed for `adw_state.json` (backward compatible)

### 7.2 Database Migration

**Migration Script:** `migrations/007_add_checkpoints.sql`

```sql
-- Add checkpoint table
CREATE TABLE IF NOT EXISTS workflow_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    adw_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    checkpoint_time TEXT NOT NULL,
    state_snapshot TEXT NOT NULL,
    git_commit TEXT,
    worktree_path TEXT,
    uncommitted_files TEXT,
    backend_port INTEGER,
    frontend_port INTEGER,
    worktree_exists BOOLEAN,
    can_resume BOOLEAN DEFAULT 1,
    stale BOOLEAN DEFAULT 0,
    stale_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (adw_id) REFERENCES workflow_history(adw_id)
);

-- Add indexes
CREATE INDEX idx_checkpoint_adw_id ON workflow_checkpoints(adw_id);
CREATE INDEX idx_checkpoint_time ON workflow_checkpoints(checkpoint_time DESC);
CREATE INDEX idx_checkpoint_can_resume ON workflow_checkpoints(can_resume);

-- Add workflow_history fields
ALTER TABLE workflow_history ADD COLUMN last_checkpoint_time TEXT;
ALTER TABLE workflow_history ADD COLUMN resume_count INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN pause_count INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN paused_at TEXT;
ALTER TABLE workflow_history ADD COLUMN resumed_at TEXT;
```

**Rollback Script:** `migrations/007_add_checkpoints_rollback.sql`

```sql
DROP INDEX IF EXISTS idx_checkpoint_adw_id;
DROP INDEX IF EXISTS idx_checkpoint_time;
DROP INDEX IF EXISTS idx_checkpoint_can_resume;
DROP TABLE IF EXISTS workflow_checkpoints;

-- Note: Cannot rollback ALTER TABLE ADD COLUMN in SQLite
-- Would require full table recreation with backup/restore
```

### 7.3 Backward Compatibility

**Checkpoint Version Field:**
- `adw_state.json` includes `"checkpoint_version": "1.0"`
- Resume service checks version compatibility
- Support reading old state files without checkpoint metadata

**Graceful Degradation:**
- If checkpoint table doesn't exist, fall back to basic resume (existing behavior)
- If `CheckpointService` fails, workflow continues without checkpoints
- Resume attempts on old workflows show "upgrade required" message

### 7.4 Rollout Phases

**Week 1-2: Internal Testing**
- Deploy to staging with `ENABLE_CHECKPOINTS=true`
- Test pause/resume with internal workflows
- Monitor for issues, tune parameters

**Week 3: Beta Rollout**
- Enable for 25% of new workflows (random sampling)
- Monitor metrics: pause_count, resume_success_rate, stale_state_rate
- Gather user feedback

**Week 4: Full Rollout**
- Enable for all workflows
- Add resume UI to main dashboard
- Documentation and training materials

**Week 5: Cleanup**
- Remove feature flag
- Clean up legacy code paths
- Performance optimization based on metrics

---

## 8. Monitoring & Metrics

### 8.1 Key Metrics

**Checkpoint Metrics:**
- `checkpoint_creation_rate`: Checkpoints created per hour
- `checkpoint_size_bytes`: Average checkpoint size
- `checkpoint_creation_latency_ms`: Time to create checkpoint

**Resume Metrics:**
- `resume_success_rate`: % of resume attempts that succeed
- `resume_validation_failures`: Count by failure reason
- `stale_state_rate`: % of checkpoints that become stale
- `resume_time_saved_seconds`: Time saved by resuming vs restarting

**Resource Metrics:**
- `paused_workflow_count`: Currently paused workflows
- `resumable_workflow_count`: Workflows eligible for resume
- `stale_checkpoint_count`: Checkpoints needing cleanup

### 8.2 Alerting

**Critical Alerts:**
- Resume success rate < 80% (indicates systemic issues)
- Stale checkpoint count > 50 (disk usage concern)
- Checkpoint creation failures > 5 per hour

**Warning Alerts:**
- Paused workflows > 10 (workflows stuck?)
- Average checkpoint size > 10MB (optimization needed)
- Resume validation failures > 20% (edge cases?)

### 8.3 Dashboard Widgets

**Admin Dashboard:**
- Resumable workflows list (with viability status)
- Checkpoint statistics (count, size, age distribution)
- Resume success timeline (7-day chart)
- Top stale state reasons (pie chart)

---

## 9. Future Enhancements

### 9.1 Advanced Features (Post-MVP)

**Phase Rollback:**
- Allow reverting to previous checkpoint
- Re-run failed phase with fixes
- API: `POST /api/workflow/rollback`

**State Snapshots:**
- Automatic snapshots before risky operations
- Snapshot retention policy (keep last 3)
- Quick rollback to any snapshot

**Resume UI Improvements:**
- Visual timeline of checkpoints
- Diff view of state changes between checkpoints
- Estimated time to complete from resume point

**Cloud Backup:**
- Upload checkpoints to S3/GCS for disaster recovery
- Cross-machine resume support
- Archive completed workflow states

**Smart Resume:**
- ML-based prediction of resume success likelihood
- Automatic recovery action selection
- Proactive stale state detection (before resume attempt)

### 9.2 Performance Optimizations

**Incremental Checkpoints:**
- Only save state delta since last checkpoint
- Reduces checkpoint size by ~70%
- Faster save/load times

**Checkpoint Compression:**
- Gzip compress state snapshots
- Reduces disk usage
- Negligible CPU overhead

**Async Checkpointing:**
- Create checkpoint in background thread
- Don't block workflow execution
- Checkpoint lag monitoring

---

## 10. Security & Privacy

### 10.1 Sensitive Data Handling

**Checkpoints May Contain:**
- API keys in environment variables
- GitHub tokens in worktree state
- Cost data (business sensitive)

**Mitigations:**
1. **Encryption at rest:** Encrypt checkpoint snapshots with AES-256
2. **Access control:** Only workflow owner can access checkpoints
3. **Redaction:** Strip sensitive fields before saving
4. **Auto-cleanup:** Delete checkpoints after 7 days

### 10.2 Resume Authorization

**Security Requirements:**
- Only authenticated users can resume workflows
- Verify user owns the workflow (issue_number → assignee check)
- Rate limit resume attempts (5 per hour per user)

---

## 11. Appendix

### 11.1 Glossary

- **Checkpoint:** Saved state at a specific point in workflow execution
- **Resume:** Continue workflow from last checkpoint
- **Stale State:** Checkpoint that cannot be resumed due to external changes
- **Phase:** Individual step in multi-phase workflow (plan, build, lint, test, etc.)
- **Worktree:** Isolated git working directory for workflow
- **ZTE:** Zero Touch Execution (complete SDLC workflow)

### 11.2 Related Documentation

- `/Users/Warmonger0/tac/tac-webbuilder/docs/adw/resume-logic.md` - Current resume logic
- `/Users/Warmonger0/tac/tac-webbuilder/docs/ADW_ROBUSTNESS_SYSTEM.md` - Robustness features
- `/Users/Warmonger0/tac/tac-webbuilder/docs/features/adw/technical-overview.md` - ADW architecture

### 11.3 Decision Log

**Why file-based state + database checkpoints?**
- File-based state (`adw_state.json`) is already working and battle-tested
- Database checkpoints add history/audit without disrupting existing code
- Hybrid approach balances simplicity and power

**Why not pause mid-phase?**
- Complexity: Saving mid-phase state is hard (uncommitted work, in-flight API calls)
- ROI: Most phases complete in < 10 minutes, losing some work is acceptable
- Future: Can add mid-phase checkpoints if users demand it

**Why keep worktrees after pause?**
- Fast resume: Worktree already set up with correct code
- Context preservation: Uncommitted work, logs, artifacts intact
- Trade-off: Disk usage (mitigated by stale cleanup after 7 days)

### 11.4 Open Questions

1. **How long to keep checkpoints?** Proposed: 7 days, configurable
2. **Should we support cross-machine resume?** Proposed: No (MVP), Yes (future with cloud backup)
3. **Auto-pause on system shutdown?** Proposed: Yes, via signal handlers
4. **Resume priority in queue?** Proposed: Resumed workflows get priority over new workflows

---

## Summary

This architecture provides a comprehensive save/resume system for ADW workflows with:

✅ **Zero data loss** via automated checkpoints after each phase
✅ **Robust validation** detecting stale state and offering recovery options
✅ **User-friendly APIs** for pause/resume/list operations
✅ **Backward compatible** migration strategy
✅ **Edge case handling** for deleted worktrees, branch conflicts, port conflicts
✅ **Monitoring & alerts** to track system health
✅ **Clear implementation plan** with 5 phases over ~3-4 weeks

The system builds on existing state management while adding explicit checkpoint history, validation, and orchestration. It maintains the simplicity of file-based state while adding the power of database-backed checkpoints for audit and recovery.
