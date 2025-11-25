# Workflow Save/Resume System - Quick Start

> **Full Documentation:** See [workflow-save-resume.md](/Users/Warmonger0/tac/tac-webbuilder/docs/architecture/workflow-save-resume.md)

## 30-Second Overview

Add pause/resume capabilities to ADW workflows so they can be interrupted and resumed from checkpoints without losing work.

**Current State:**
- Basic resume via `all_adws` array (works for individual phases)
- No explicit pause API or UI
- ZTE workflows don't support resume

**Goal State:**
- Pause workflows via API/UI
- Automatic checkpoints after each phase
- Resume from last checkpoint with validation
- Handle edge cases (deleted worktrees, stale state, etc.)

---

## Quick Reference

### Core Components

```
CheckpointService    → Create/manage checkpoints in DB
ResumeService        → Validate & restore state for resume
ADWState (enhanced)  → Add checkpoint metadata to state file
API Endpoints        → /pause, /resume, /resumable
UI Components        → ResumableWorkflowsCard, pause button
```

### State Storage

```
agents/{adw_id}/adw_state.json  → Phase progress, resource state
workflow_history.db             → Analytics, status tracking
workflow_checkpoints table      → Checkpoint history (NEW)
```

### Key APIs

```bash
# Pause workflow
POST /api/workflow/pause
Body: {"adw_id": "adw-123", "reason": "manual_pause"}

# Resume workflow
POST /api/workflow/resume
Body: {"adw_id": "adw-123"}

# List resumable workflows
GET /api/workflow/resumable
```

---

## Implementation Timeline

**Week 1: Checkpoint Infrastructure**
- Add `workflow_checkpoints` table
- Create `CheckpointService`
- Update `ADWState.save()` to create checkpoints
- Unit tests

**Week 1-2: Pause Functionality**
- `/api/workflow/pause` endpoint
- UI pause button
- GitHub notifications
- Integration tests

**Week 2: Resume Detection**
- Create `ResumeService`
- Stale state detection
- `/api/workflow/resumable` endpoint
- Validation tests

**Week 2-3: Resume Execution**
- Add `--resume-from` flag to workflows
- `/api/workflow/resume` endpoint
- Worktree/port restoration
- E2E tests

**Week 3: UI & Cleanup**
- `ResumableWorkflowsCard` component
- Stale checkpoint cleanup
- Admin dashboard
- Documentation

---

## Key Design Decisions

### ✅ Checkpoint After Each Phase (Not Mid-Phase)
- **Why:** Phases are atomic units; mid-phase state is complex
- **Trade-off:** May lose up to one phase of work if interrupted mid-phase
- **Acceptable:** Most phases complete in < 10 minutes

### ✅ Keep Worktrees After Pause
- **Why:** Fast resume, preserves context
- **Trade-off:** Disk usage
- **Mitigation:** Auto-cleanup stale worktrees after 7 days

### ✅ Hybrid State Storage (File + DB)
- **Why:** File-based state is battle-tested; DB adds history/audit
- **Implementation:** `adw_state.json` for current state, `workflow_checkpoints` for history

### ✅ Validate Before Resume
- **Why:** Prevent resume failures (deleted worktree, branch gone, etc.)
- **Implementation:** `validate_resume_state()` checks all conditions
- **Recovery:** Offer options (recreate worktree, restart, cleanup)

---

## Critical Edge Cases

### 1. Worktree Deleted
- **Detection:** Check `os.path.exists(worktree_path)`
- **Recovery:** Offer to recreate from branch or restart workflow

### 2. Branch Deleted
- **Detection:** Run `git show-ref {branch_name}`
- **Recovery:** Cannot resume; offer cleanup

### 3. Port Conflict
- **Detection:** Check if ports are bound
- **Recovery:** Auto-allocate new ports

### 4. State Corrupted
- **Detection:** JSON parse error or Pydantic validation failure
- **Recovery:** Restore from `workflow_checkpoints` table

### 5. Multiple Resume Attempts
- **Prevention:** Add `resume_lock` flag in database (expires after 5 minutes)

### 6. Code Changes Between Pause/Resume
- **Detection:** Compare `workflow_template` version
- **Options:** Allow if compatible, warn if incompatible, force with `--force`

---

## Data Schema (Key Fields)

### Enhanced adw_state.json
```json
{
  "checkpoint_version": "1.0",
  "last_checkpoint_time": "2025-11-25T10:30:45Z",
  "current_phase": {
    "name": "build",
    "status": "completed"
  },
  "resume_metadata": {
    "can_resume": true,
    "resume_from_phase": "lint",
    "stale_reasons": []
  },
  "phase_results": {
    "plan": {"status": "completed", "checksum": "sha256:..."},
    "build": {"status": "completed", "checksum": "sha256:..."}
  }
}
```

### New Table: workflow_checkpoints
```sql
CREATE TABLE workflow_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    adw_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    checkpoint_time TEXT NOT NULL,
    state_snapshot TEXT NOT NULL,  -- Full adw_state.json
    git_commit TEXT,
    worktree_exists BOOLEAN,
    can_resume BOOLEAN DEFAULT 1,
    stale BOOLEAN DEFAULT 0,
    stale_reason TEXT
);
```

---

## Testing Strategy

### Unit Tests
- ✅ Checkpoint creation/retrieval/deletion
- ✅ Resume validation (all conditions)
- ✅ Stale state detection

### Integration Tests
- ✅ Pause flow (checkpoint created, resources preserved)
- ✅ Resume flow (skip completed phases, continue from checkpoint)
- ✅ Edge cases (worktree deleted, port conflict, etc.)

### E2E Tests
- ✅ Pause after phase 2, resume, complete workflow
- ✅ Resume after worktree deleted (expect failure + recovery options)
- ✅ Multiple pause/resume cycles

---

## Rollout Strategy

**Week 1-2:** Internal testing with `ENABLE_CHECKPOINTS=false` (feature flag)
**Week 3:** Beta rollout (25% of workflows)
**Week 4:** Full rollout (100% of workflows)
**Week 5:** Remove feature flag, optimize based on metrics

---

## Metrics to Monitor

**Success Metrics:**
- Resume success rate > 95%
- Average resume time < 30 seconds
- Stale state rate < 10%

**Alerts:**
- Resume success rate < 80% (critical)
- Stale checkpoint count > 50 (warning)
- Checkpoint creation failures > 5/hour (warning)

---

## Next Steps

1. **Review Architecture:** Read full doc, provide feedback
2. **Database Migration:** Review schema changes
3. **API Contracts:** Validate request/response formats
4. **UI Mockups:** Design pause button + resumable workflows list
5. **Kick off Phase 1:** Start with checkpoint infrastructure

---

## Questions?

- How long to keep checkpoints? **Proposed: 7 days**
- Auto-pause on system shutdown? **Proposed: Yes**
- Support mid-phase resume? **Proposed: No (MVP), Yes (future)**
- Cross-machine resume? **Proposed: No (MVP), Yes (future with cloud backup)**
