# ADW Fix Implementation Summary

**Quick Reference:** Critical fixes needed to prevent empty PRs and incomplete phases

---

## TL;DR - What Happened

**Problem:** 3 ADWs created empty PRs for Issue #83 with only spec documents, no actual code.

**Root Cause:** Used planning-only workflow (`adw_plan_iso`) instead of full SDLC workflow (`adw_sdlc_complete_iso`).

**Impact:** Wasted resources, confusion, incomplete phase implementation.

---

## Critical Fixes (Priority Order)

### 1. Workflow Type Selection (HIGHEST PRIORITY)

**Problem:** System always uses `adw_plan_iso` for phase execution.

**Fix Location:** `app/server/services/phase_queue_service.py` or wherever phase execution is triggered

**Required Code:**
```python
def execute_phase(queue_id: str) -> dict:
    """Execute a phase from the queue."""
    phase = self.repository.get_phase(queue_id)

    # Determine if this needs implementation or just validation
    if "validate" in phase.phase_data.get("title", "").lower():
        workflow = "adws/adw_plan_iso.py"  # Planning only
    else:
        workflow = "adws/adw_sdlc_complete_iso.py"  # Full SDLC

    cmd = ["uv", "run", workflow, str(phase.issue_number)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return {"success": result.returncode == 0}
```

**Test:**
```bash
# Should use full SDLC for implementation phases
pytest -xvs app/server/tests/services/test_phase_queue_service.py::test_correct_workflow_selection
```

**Verify:**
```bash
# Check that ADWs use sdlc_complete, not plan_iso
cat agents/*/adw_state.json | grep "all_adws"
# Should show: "all_adws": ["adw_sdlc_complete_iso"]
```

---

### 2. ADW Coordination/Locking (HIGH PRIORITY)

**Problem:** Multiple ADWs work on same issue simultaneously.

**Fix:** Create `ADWCoordinationService` with database-backed locks.

**Quick Implementation:**
```bash
# 1. Create migration
cat > app/server/db/migrations/009_add_adw_locks.sql <<EOF
CREATE TABLE IF NOT EXISTS adw_locks (
    issue_number INTEGER PRIMARY KEY,
    adw_id TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL
);
EOF

# 2. Run migration
sqlite3 app/server/db/database.db < app/server/db/migrations/009_add_adw_locks.sql

# 3. Add coordination check in adw_modules/workflow_ops.py
# Before starting ADW, check if issue is locked
```

**Test:**
```bash
# Try to start 2 ADWs on same issue
uv run adws/adw_sdlc_complete_iso.py 83 adw-test-1 &
uv run adws/adw_sdlc_complete_iso.py 83 adw-test-2 &
# Second should fail with "Issue already locked" error
```

---

### 3. PR Validation (HIGH PRIORITY)

**Problem:** PRs created even when only spec files changed.

**Fix:** Add `PRValidator` to check changes before creating PR.

**Quick Implementation:**
```python
# In adw_modules/git_ops.py, before creating PR:

def should_create_pr(worktree_path: str) -> bool:
    """Check if PR should be created."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "main...HEAD"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    )

    changed_files = result.stdout.strip().split("\n")

    # Check if only spec/config files changed
    code_files = [f for f in changed_files
                  if f.endswith((".ts", ".tsx", ".py"))
                  and not f.startswith("specs/")]

    if not code_files:
        logger.warning("No code files changed - skipping PR")
        return False

    return True

# Use it:
if not should_create_pr(state.get("worktree_path")):
    logger.warning("Skipping PR creation - no implementation")
    make_issue_comment(issue_number, "⚠️ Planning complete but no code implemented")
    return
```

**Test:**
```bash
# Create test worktree with only spec changes
pytest -xvs tests/adw/test_pr_validator.py::test_reject_spec_only_pr
```

---

## Implementation Order

### Phase 1: Stop the Bleeding (TODAY)

1. **Manually fix workflow selection** (30 min)
   - Find where phases are executed
   - Add workflow type determination
   - Test with one phase

2. **Add basic locking** (1 hour)
   - Create adw_locks table
   - Add lock check before ADW starts
   - Test with concurrent ADWs

### Phase 2: Comprehensive Fix (THIS WEEK)

3. **Implement full ADWCoordinationService** (2 hours)
   - Complete lock lifecycle
   - Add expiration handling
   - Add monitoring

4. **Implement PRValidator** (2 hours)
   - Full file categorization
   - Integration with git_ops
   - Test all scenarios

5. **Integration testing** (3 hours)
   - E2E multi-phase workflow
   - Concurrent ADW prevention
   - PR validation scenarios

### Phase 3: Polish & Monitor (NEXT WEEK)

6. **Add monitoring dashboard** (2 hours)
7. **Update documentation** (1 hour)
8. **Train team** (1 hour)
9. **Monitor for 7 days**

---

## Quick Verification Commands

### Check ADW States
```bash
# See what workflows ADWs ran
for dir in agents/*/; do
  echo "=== $(basename $dir) ==="
  cat "$dir/adw_state.json" | python3 -m json.tool | grep -E "adw_id|all_adws|issue_number"
done
```

### Check Active Locks
```bash
# See what issues are currently locked
sqlite3 app/server/db/database.db "SELECT * FROM adw_locks WHERE expires_at > datetime('now')"
```

### Check Recent PRs
```bash
# See recent PRs and their file changes
gh pr list --limit 10 --json number,title,files
```

### Monitor ADW Logs
```bash
# Watch ADW activity in real-time
tail -f agents/*/adw_*.log
```

---

## Emergency Procedures

### If ADW Stuck on Lock
```bash
# Force release lock
sqlite3 app/server/db/database.db "DELETE FROM adw_locks WHERE issue_number = X"
```

### If Wrong Workflow Type Used
```bash
# Stop ADW
pkill -f "adw_plan_iso"

# Clean up worktree
rm -rf trees/adw-xxxxxx

# Restart with correct workflow
uv run adws/adw_sdlc_complete_iso.py <issue-number>
```

### If Empty PR Created
```bash
# Close PR
gh pr close <pr-number> --comment "Empty PR - no implementation"

# Clean up branch
git branch -D feature-issue-X-adw-xxxxxx
git push origin --delete feature-issue-X-adw-xxxxxx
```

---

## Success Metrics

**Daily:**
- [ ] Zero empty PRs created
- [ ] Zero concurrent ADW conflicts
- [ ] All phases use correct workflow type

**Weekly:**
- [ ] 95%+ ADW success rate
- [ ] <5% lock contention
- [ ] Zero manual interventions

**Monthly:**
- [ ] All multi-phase workflows complete successfully
- [ ] Average ADW cost within budget
- [ ] Zero regression issues

---

## Next Steps

1. **Read full protocol:** `docs/ADW_FAILURE_ANALYSIS_AND_FIX_PROTOCOL.md`
2. **Implement critical fixes:** Start with workflow selection
3. **Test thoroughly:** Run E2E tests before deploying
4. **Monitor closely:** Watch for issues in first week
5. **Iterate:** Refine based on real-world usage

---

## Questions & Support

- **Architecture questions:** Review full protocol document
- **Implementation help:** Check code examples in protocol
- **Issues found:** Open GitHub issue with `adw-coordination` label
- **Urgent problems:** Disable automatic ADW execution temporarily

---

**Document Version:** 1.0
**Created:** 2025-11-24
**Owned by:** Engineering Team
**Review:** After first production deployment
