# Workflow History Schema Mismatch Documentation

## Issue

**Date:** 2025-11-21
**Status:** Fixed with temporary field mapping
**Migration Required:** Yes (future)

## Problem Description

The workflow history database schema doesn't match the code's expected schema, causing workflow history API endpoints to return empty results even though the database contains 453+ records.

### Schema Differences

| Code Field Name | Database Column Name | Status |
|----------------|---------------------|---------|
| `hour_of_day` | `submission_hour` | **Mismatch** |
| `day_of_week` | `submission_day_of_week` | **Mismatch** |
| `scoring_version` | _(column missing)_ | **Missing** |

## Root Cause

1. **INSERT/UPDATE Failures:** Code tried to insert fields `hour_of_day`, `day_of_week`, and `scoring_version` into columns that don't exist in the database
2. **Sync Errors:** `sync_workflow_history()` failed silently when trying to enrich and insert workflow data
3. **Empty Results:** API endpoints caught the error and returned empty responses

## Quick Fix Applied (Option 1)

### Changes Made to `app/server/core/workflow_history_utils/database.py`:

1. **Field Name Mapping (Bidirectional):**
   - **Insert/Update:** Maps `hour_of_day` → `submission_hour`, `day_of_week` → `submission_day_of_week`
   - **Query Results:** Maps `submission_hour` → `hour_of_day`, `submission_day_of_week` → `day_of_week`

2. **Column Validation:**
   - Before INSERT/UPDATE: Check `PRAGMA table_info()` to validate columns exist
   - Skip fields that don't exist in database (with debug logging)
   - Prevents SQL errors from column mismatches

3. **Default Values:**
   - Set `hour_of_day = -1` when `submission_hour` is NULL
   - Set `day_of_week = -1` when `submission_day_of_week` is NULL
   - Ensures Pydantic validation passes

4. **Removed Broken Query Aliases:**
   - Changed from `SELECT *, submission_hour as hour_of_day, ...`
   - To: `SELECT *` with post-query field mapping
   - Eliminates SQL errors from attempting aliasing

### Files Modified

- `app/server/core/workflow_history_utils/database.py`:
  - `insert_workflow_history()` - Added field mapping and column validation
  - `update_workflow_history()` - Added field mapping and column validation
  - `get_workflow_history()` - Removed aliases, added result field mapping
  - `get_workflow_by_adw_id()` - Added result field mapping

## Future Migration (Option 2 - Recommended)

Apply database migration `005_rename_temporal_columns.sql` to:

1. Add `hour_of_day` and `day_of_week` columns
2. Copy data from `submission_hour` and `submission_day_of_week`
3. Drop old columns
4. Recreate indexes
5. Add missing `scoring_version` column

**Migration file:** `app/server/db/migrations/005_rename_temporal_columns.sql`

**Risk:** Requires table recreation (SQLite limitation), needs database backup first

## Testing

### Verified Working:
- ✅ REST API: `GET /api/workflow-history` returns 458 workflows
- ✅ WebSocket: `/ws/workflow-history` streams 50 workflows initially
- ✅ Direct function calls: `get_workflow_history()` returns full data
- ✅ Sync operations: `sync_workflow_history()` no longer fails

### Test Commands:
```bash
# Test API endpoint
curl -s http://localhost:8000/api/workflow-history?limit=3 | python3 -m json.tool

# Test WebSocket
uv run python3 -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8000/ws/workflow-history') as ws:
        data = json.loads(await ws.recv())
        print(f'Workflows: {len(data[\"data\"][\"workflows\"])}')
asyncio.run(test())
"
```

## Impact

**Before Fix:**
- Workflow history tab showed "No workflow history found"
- Database had 453 records but API returned 0
- `sync_workflow_history()` failed silently on every call

**After Fix:**
- Workflow history displays 458 workflows correctly
- All API endpoints functional
- WebSocket real-time updates working
- Frontend can display workflow cards with full details

## Recommendations

1. **Short-term:** Current fix is stable and working
2. **Medium-term:** Schedule maintenance window to apply migration 005
3. **Long-term:** Add database schema versioning to detect mismatches early
4. **Testing:** Add integration tests that verify schema matches code expectations

## Related Issues

- Original issue: #66 (workflow history not displaying)
- Migration file: `db/migrations/005_rename_temporal_columns.sql`
- Related columns: `submission_hour`, `submission_day_of_week`, `scoring_version`
