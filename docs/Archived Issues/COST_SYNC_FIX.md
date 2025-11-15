# Cost Data Staleness Fix - Comprehensive Design

## 🔴 Problem Statement

**Issue:** Workflow history database shows incorrect (stale) cost data for completed workflows.

**Example:** Issue #17 shows $0.09 in database, but actual cost was $2.37 (24x discrepancy).

---

## 🔍 Root Cause Analysis

### The Bug (workflow_history.py:681-683)

```python
# Current problematic code:
if workflow_data.get("cost_breakdown") and not existing.get("cost_breakdown"):
    # Only updates if cost_breakdown doesn't already exist!
    updates["cost_breakdown"] = workflow_data["cost_breakdown"]
    updates["actual_cost_total"] = workflow_data.get("actual_cost_total", 0.0)
```

### What Happens:

1. **Workflow starts** → Sync runs → Captures partial cost ($0.09 from first agent) → Stores in DB
2. **Workflow continues** → More agents run → Total cost grows to $2.37
3. **Sync runs again** → Sees `cost_breakdown` already exists → **SKIPS UPDATE** ❌
4. **Database permanently stuck** with stale partial cost

### Why This Happens:

The condition `not existing.get("cost_breakdown")` means:
- ✅ First sync: No cost data exists → Update happens
- ❌ Subsequent syncs: Cost data exists → **No update** (even if workflow completed)

---

## 🎯 Comprehensive Fix Design

### Recommended Solution: Hybrid Approach

Combine three strategies:
1. **Fix sync logic** (always update for completed workflows)
2. **Add manual resync endpoint** (cleanup tool)
3. **Enhanced logging** (audit trail)

---

## 📋 Implementation Plan

### Phase A: Fix Sync Logic (CRITICAL - Prevents Future Issues)

**File:** `app/server/core/workflow_history.py`
**Lines:** 680-690

**Current Code:**
```python
# Update cost data if available and not already set
if workflow_data.get("cost_breakdown") and not existing.get("cost_breakdown"):
    updates["cost_breakdown"] = workflow_data["cost_breakdown"]
    updates["actual_cost_total"] = workflow_data.get("actual_cost_total", 0.0)
    updates["input_tokens"] = workflow_data.get("input_tokens", 0)
    updates["cached_tokens"] = workflow_data.get("cached_tokens", 0)
    updates["cache_hit_tokens"] = workflow_data.get("cache_hit_tokens", 0)
    updates["cache_miss_tokens"] = workflow_data.get("cache_miss_tokens", 0)
    updates["output_tokens"] = workflow_data.get("output_tokens", 0)
    updates["total_tokens"] = workflow_data.get("total_tokens", 0)
    updates["cache_efficiency_percent"] = workflow_data.get("cache_efficiency_percent", 0.0)
```

**New Code:**
```python
# ALWAYS update cost data if:
# 1. New cost data is available AND
# 2. (Workflow is completed/failed OR new cost > existing cost)
if workflow_data.get("cost_breakdown"):
    should_update_cost = False
    new_cost = workflow_data.get("actual_cost_total", 0.0)
    existing_cost = existing.get("actual_cost_total", 0.0)

    # Always update for completed/failed workflows (final cost)
    if workflow_data["status"] in ["completed", "failed"]:
        should_update_cost = True
        logger.info(
            f"[SYNC] Updating final cost for {adw_id}: "
            f"${existing_cost:.4f} → ${new_cost:.4f} "
            f"(status: {workflow_data['status']})"
        )
    # For running workflows, only update if cost increased
    elif new_cost > existing_cost:
        should_update_cost = True
        logger.info(
            f"[SYNC] Updating progressive cost for {adw_id}: "
            f"${existing_cost:.4f} → ${new_cost:.4f} "
            f"(status: {workflow_data['status']})"
        )

    if should_update_cost:
        updates["cost_breakdown"] = workflow_data["cost_breakdown"]
        updates["actual_cost_total"] = new_cost
        updates["input_tokens"] = workflow_data.get("input_tokens", 0)
        updates["cached_tokens"] = workflow_data.get("cached_tokens", 0)
        updates["cache_hit_tokens"] = workflow_data.get("cache_hit_tokens", 0)
        updates["cache_miss_tokens"] = workflow_data.get("cache_miss_tokens", 0)
        updates["output_tokens"] = workflow_data.get("output_tokens", 0)
        updates["total_tokens"] = workflow_data.get("total_tokens", 0)
        updates["cache_efficiency_percent"] = workflow_data.get("cache_efficiency_percent", 0.0)
```

**Benefits:**
- ✅ Completed/failed workflows: ALWAYS get latest cost (final total)
- ✅ Running workflows: Only update if cost increased (progressive tracking)
- ✅ Prevents cost from decreasing (data integrity)
- ✅ Enhanced logging for debugging
- ✅ No schema changes needed

**Estimated Effort:** 15-30 minutes (manual implementation)
**Risk:** Low (improves existing logic, no breaking changes)

---

### Phase B: Add Manual Resync Endpoint (Cleanup Tool)

**File:** `app/server/server.py`

**New Endpoint:**
```python
@app.post("/api/workflow-history/resync")
async def resync_workflow_history(
    adw_id: Optional[str] = None,
    force: bool = False
) -> dict:
    """
    Resync workflow history cost data from source files.

    Useful for fixing historical data issues where database has stale costs.

    Args:
        adw_id: Specific workflow to resync (None = resync all completed/failed)
        force: If True, force update even if cost data exists and is recent

    Returns:
        {
            "resynced_count": 5,
            "workflows": ["a5b80595", "107e71f9", ...],
            "errors": []
        }

    Examples:
        # Resync single workflow
        POST /api/workflow-history/resync?adw_id=a5b80595

        # Resync all completed workflows
        POST /api/workflow-history/resync

        # Force resync (ignore existing data)
        POST /api/workflow-history/resync?force=true
    """
    from core.workflow_history import sync_workflow_history
    from core.cost_tracker import read_cost_history

    resynced = []
    errors = []

    if adw_id:
        # Resync single workflow
        try:
            if force:
                # Clear existing cost data to force full recalculation
                with get_db_connection() as conn:
                    conn.execute("""
                        UPDATE workflow_history
                        SET cost_breakdown = NULL,
                            actual_cost_total = 0.0,
                            input_tokens = 0,
                            cached_tokens = 0,
                            cache_hit_tokens = 0,
                            output_tokens = 0,
                            total_tokens = 0,
                            cache_efficiency_percent = 0.0
                        WHERE adw_id = ?
                    """, (adw_id,))

            # Trigger sync for this workflow
            count = sync_workflow_history()  # Will pick up the workflow
            resynced.append(adw_id)

        except Exception as e:
            errors.append(f"{adw_id}: {str(e)}")
    else:
        # Resync all completed/failed workflows
        try:
            if force:
                # Clear cost data for all completed/failed workflows
                with get_db_connection() as conn:
                    conn.execute("""
                        UPDATE workflow_history
                        SET cost_breakdown = NULL,
                            actual_cost_total = 0.0,
                            input_tokens = 0,
                            cached_tokens = 0,
                            cache_hit_tokens = 0,
                            output_tokens = 0,
                            total_tokens = 0,
                            cache_efficiency_percent = 0.0
                        WHERE status IN ('completed', 'failed')
                    """)

            # Trigger full sync
            count = sync_workflow_history()

            # Get list of resynced workflows
            with get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT adw_id FROM workflow_history
                    WHERE status IN ('completed', 'failed')
                """)
                resynced = [row[0] for row in cursor.fetchall()]

        except Exception as e:
            errors.append(f"Bulk resync: {str(e)}")

    return {
        "resynced_count": len(resynced),
        "workflows": resynced,
        "errors": errors
    }
```

**Benefits:**
- ✅ Can fix Issue #17 and other historical issues
- ✅ Useful for one-time cleanup
- ✅ Can be called after workflow completion to guarantee accuracy
- ✅ Supports both single workflow and bulk operations

**Estimated Effort:** 30-45 minutes (manual or via ADW)
**Risk:** Low (read-only for most operations, clears data only if `force=True`)

---

### Phase C: Fix Existing Data (One-Time Cleanup)

**Option 1: Use Resync Endpoint**

```bash
# Fix Issue #17 specifically
curl -X POST http://localhost:8000/api/workflow-history/resync?adw_id=a5b80595&force=true

# Fix all completed workflows
curl -X POST http://localhost:8000/api/workflow-history/resync?force=true
```

**Option 2: Manual SQL**

```sql
-- Clear cost data for specific workflow
UPDATE workflow_history
SET cost_breakdown = NULL, actual_cost_total = 0.0
WHERE adw_id = 'a5b80595';

-- Clear cost data for all completed workflows
UPDATE workflow_history
SET cost_breakdown = NULL, actual_cost_total = 0.0
WHERE status IN ('completed', 'failed');

-- Then restart backend to trigger automatic sync
```

**Option 3: Python Script**

```bash
# Clear and resync all workflows
sqlite3 app/server/db/workflow_history.db "UPDATE workflow_history SET cost_breakdown = NULL WHERE status IN ('completed', 'failed');"

# Restart backend (triggers auto-sync)
# Or manually trigger sync via API
```

**Estimated Effort:** 5 minutes
**Risk:** Very low (data will be recalculated from source)

---

## 🧪 Testing Strategy

### Test Case 1: Running Workflow Progressive Tracking
```
1. Start a new workflow
2. After first agent: Check DB → Should show small cost (e.g., $0.15)
3. After more agents: Check DB → Should show increased cost (e.g., $0.45)
4. Continue workflow: Cost should keep increasing
5. Complete workflow: Should show final total cost

Expected: Cost increases progressively, never decreases
```

### Test Case 2: Completed Workflow Final Cost
```
1. Complete a workflow with cost $2.37
2. Verify DB shows $2.37
3. Manually trigger resync
4. Verify DB still shows $2.37 (no change)

Expected: Final cost is accurate and stable
```

### Test Case 3: Cost Decrease Prevention
```
1. Manually set workflow cost to $5.00 in DB
2. Actual cost is $2.37
3. Trigger sync (workflow still running)
4. Check DB → Should still be $5.00 (no decrease)
5. Mark workflow as completed
6. Trigger sync
7. Check DB → Should now be $2.37 (final cost update)

Expected: Running workflows don't decrease, completed workflows get accurate final cost
```

### Test Case 4: Force Resync
```
1. Set wrong cost ($0.09) in DB for completed workflow
2. Actual cost is $2.37
3. Call /api/workflow-history/resync?adw_id=xxx&force=true
4. Check DB → Should now be $2.37

Expected: Force resync fixes incorrect historical data
```

### Test Case 5: Issue #17 Fix Verification
```
1. Check current cost for Issue #17: Should be $0.09 (wrong)
2. Run: curl -X POST .../resync?adw_id=a5b80595&force=true
3. Check cost again: Should be $2.37 (correct)
4. Refresh workflow history UI: Should display $2.37

Expected: Issue #17 shows correct cost after resync
```

---

## ✅ Success Criteria

After implementing all phases:

1. ✅ **Completed workflows always show final accurate cost**
2. ✅ **Running workflows show progressively increasing cost**
3. ✅ **Cost never decreases unexpectedly**
4. ✅ **Issue #17 shows $2.37 (not $0.09)**
5. ✅ **New workflows track cost accurately from start**
6. ✅ **Manual resync endpoint available for cleanup**
7. ✅ **Logs show cost update activity for debugging**

---

## 📊 Impact Analysis

### Affected Workflows (Current Database)

Run this query to find workflows with potentially stale costs:

```sql
-- Find workflows that might have stale costs
-- (completed but cost seems low)
SELECT
    adw_id,
    issue_number,
    status,
    actual_cost_total as db_cost,
    total_tokens
FROM workflow_history
WHERE status = 'completed'
  AND actual_cost_total < 0.50  -- Suspiciously low
  AND total_tokens > 100000      -- But high token count
ORDER BY actual_cost_total ASC;
```

**Expected results:**
- Issue #17 (a5b80595): $0.09 → Should be ~$2.37
- Potentially others with similar pattern

---

## ⚠️ Potential Issues & Mitigations

### Issue 1: What if cost_history file is incomplete during workflow?
**Mitigation:**
- Only update if cost increased (running workflows)
- Always update when completed (final cost)
- Log warnings when cost data is missing

### Issue 2: What if sync runs during agent execution?
**Mitigation:**
- Progressive update strategy handles this gracefully
- Cost only increases, never decreases (for running workflows)
- Prevents partial overwrites

### Issue 3: What if multiple syncs run concurrently?
**Mitigation:**
- Database transactions ensure atomicity
- Last write wins (all writers use same source data)
- Completed workflows always get final cost

### Issue 4: What if force resync is called on wrong workflow?
**Mitigation:**
- Data is recalculated from source files (idempotent)
- No data loss risk (source files are authoritative)
- Can be run multiple times safely

---

## 📝 Documentation Updates Needed

### 1. Code Comments
Add detailed comments in `workflow_history.py` explaining the cost update logic.

### 2. API Documentation
Document the `/api/workflow-history/resync` endpoint in API docs or OpenAPI spec.

### 3. Troubleshooting Guide
Add section to main docs:

**"If Workflow Costs Seem Incorrect:**
1. Check if workflow is still running (cost may be partial)
2. For completed workflows, call `/api/workflow-history/resync?adw_id=XXX&force=true`
3. Check logs for cost update activity
4. Verify source cost files exist in `agents/ADW_ID/` directories"

### 4. Admin Guide
Add operational procedures:
- When to run manual resync
- How to verify cost accuracy
- How to bulk-fix historical data

---

## 🚀 Deployment Strategy

### Pre-Deployment
1. ✅ Review and test Phase A changes locally
2. ✅ Verify logging output is helpful
3. ✅ Test with a running workflow
4. ✅ Test with a completed workflow

### Deployment
1. Deploy Phase A (sync logic fix)
2. Restart backend
3. Verify new workflows get accurate costs
4. Deploy Phase B (resync endpoint)
5. Run Phase C (one-time cleanup)

### Post-Deployment
1. Monitor logs for cost update activity
2. Verify Issue #17 cost is now $2.37
3. Check other completed workflows for accuracy
4. Document any anomalies

---

## 💡 Future Enhancements

### Enhancement 1: Cost Update Webhooks
Send notifications when cost data is updated:
```python
@app.post("/api/workflow-history/webhook/cost-updated")
async def on_cost_updated(adw_id: str, old_cost: float, new_cost: float):
    # Notify external systems
    pass
```

### Enhancement 2: Cost Audit Log
Track all cost changes for debugging:
```sql
CREATE TABLE cost_audit_log (
    id INTEGER PRIMARY KEY,
    adw_id TEXT,
    old_cost REAL,
    new_cost REAL,
    reason TEXT,
    timestamp TEXT
);
```

### Enhancement 3: Automatic Resync on Completion
Trigger automatic force-resync when workflow completes:
```python
# In workflow completion handler
if workflow.status == "completed":
    resync_workflow_history(adw_id=workflow.adw_id, force=True)
```

---

## 📅 Timeline

**Total Implementation Time:** ~1-2 hours

| Phase | Task | Effort | Who |
|-------|------|--------|-----|
| A | Fix sync logic | 15-30 min | Manual or ADW |
| A | Add logging | 5-10 min | Manual or ADW |
| A | Test locally | 10-15 min | Manual |
| B | Add resync endpoint | 30-45 min | Manual or ADW |
| B | Test endpoint | 10-15 min | Manual |
| C | Run cleanup | 5 min | Manual |
| - | Documentation | 15-20 min | Manual or ADW |

**Can be split into separate issues if using ADW for implementation.**

---

## 🎯 Next Steps

**After Issue #19 is complete:**

1. Create GitHub issue for this fix (or implement manually)
2. Implement Phase A first (most critical)
3. Test with a new workflow
4. Implement Phase B (resync endpoint)
5. Run Phase C (fix Issue #17 and others)
6. Update documentation

---

**This design is ready for implementation when you're ready to proceed!**
