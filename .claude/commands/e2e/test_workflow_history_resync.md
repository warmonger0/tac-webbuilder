# E2E Test: Workflow History Cost Resync

Test the manual workflow history cost resync endpoint functionality.

## User Story

As a system administrator
I want to manually trigger cost data resynchronization for workflow history
So that I can repair historical cost data that was corrupted before the sync logic bug was fixed

## Prerequisites

- Backend server is running on the configured port
- At least one completed workflow exists in the workflow history database
- Cost files exist in the `agents/<adw_id>/costs/*.jsonl` directories
- curl or Postman installed for making API requests

## Test Steps

### Test 1: Single Workflow Resync

1. **Identify a workflow to resync**
   - Open browser developer tools (F12)
   - Navigate to the application workflow history page
   - Note down an `adw_id` from a completed workflow (e.g., `test-workflow-123`)

2. **Send POST request to resync single workflow**
   ```bash
   curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=<ADW_ID>" \
        -H "Content-Type: application/json"
   ```

3. **Verify response**
   - Response status code is 200
   - Response contains:
     ```json
     {
       "resynced_count": 1,
       "workflows": [
         {
           "adw_id": "<ADW_ID>",
           "cost_updated": true
         }
       ],
       "errors": [],
       "message": "Successfully resynced workflow <ADW_ID>"
     }
     ```

4. **Query workflow history to verify cost data was updated**
   ```bash
   curl "http://localhost:8000/api/workflow-history" | jq '.workflows[] | select(.adw_id=="<ADW_ID>")'
   ```
   - Verify `actual_cost_total` is updated
   - Verify `cost_breakdown` contains phase-level costs
   - Verify token metrics are populated

### Test 2: Bulk Resync All Completed Workflows

1. **Send POST request to resync all completed workflows**
   ```bash
   curl -X POST "http://localhost:8000/api/workflow-history/resync" \
        -H "Content-Type: application/json"
   ```

2. **Verify response**
   - Response status code is 200
   - Response contains:
     ```json
     {
       "resynced_count": <N>,
       "workflows": [
         {"adw_id": "...", "status": "completed", "cost_updated": true},
         ...
       ],
       "errors": [],
       "message": "Bulk resync completed: <N> workflows updated, 0 errors"
     }
     ```

3. **Verify workflows list**
   - `resynced_count` matches the number of completed/failed workflows
   - Each workflow in the list has `adw_id` and `cost_updated` status

### Test 3: Force Resync (Clear and Recalculate)

1. **Send POST request with force=true**
   ```bash
   curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=<ADW_ID>&force=true" \
        -H "Content-Type: application/json"
   ```

2. **Verify response**
   - Response status code is 200
   - Response indicates successful resync
   - Cost data is recalculated from source files regardless of existing values

3. **Check server logs**
   - Look for log message: `[RESYNC] Force resync for <ADW_ID> - clearing existing data`

### Test 4: Error Handling - Nonexistent Workflow

1. **Send POST request with invalid adw_id**
   ```bash
   curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=nonexistent-workflow-999" \
        -H "Content-Type: application/json"
   ```

2. **Verify error response**
   - Response status code is 200 (graceful error handling)
   - Response contains:
     ```json
     {
       "resynced_count": 0,
       "workflows": [],
       "errors": ["Workflow not found: nonexistent-workflow-999"],
       "message": "Failed to resync workflow nonexistent-workflow-999"
     }
     ```

### Test 5: Error Handling - Missing Cost Files

1. **Identify a workflow without cost files**
   - Check `agents/<adw_id>` directories
   - Find a workflow that exists in DB but has no cost files

2. **Send POST request**
   ```bash
   curl -X POST "http://localhost:8000/api/workflow-history/resync?adw_id=<ADW_ID_WITHOUT_COSTS>" \
        -H "Content-Type: application/json"
   ```

3. **Verify error response**
   - Response contains error message about missing cost files
   - Error is in the `errors` array
   - `resynced_count` is 0

### Test 6: Verify in UI (Optional)

1. **Navigate to Workflow History page in browser**
2. **Before resync:**
   - Note the cost values for a specific workflow
   - Take screenshot of workflow details

3. **Execute resync via curl** (as in Test 1)

4. **After resync:**
   - Refresh the Workflow History page
   - Verify cost values are updated
   - Take screenshot showing updated costs
   - Compare before/after screenshots

### Test 7: Check Server Logs

1. **View server logs** during resync operations
   - Look for `[RESYNC]` log messages
   - Verify logging includes:
     - `Starting resync: adw_id=XXX, force=false`
     - `Successfully resynced cost data for XXX`
     - `Bulk resync completed: N updated, M errors`

2. **Verify log levels**
   - INFO for successful operations
   - ERROR for failed operations
   - WARNING for partial failures

## Success Criteria

- ✓ Single workflow resync successfully updates cost data
- ✓ Bulk resync processes all completed/failed workflows
- ✓ Force mode clears and recalculates cost data
- ✓ Error handling returns meaningful error messages
- ✓ Response format matches API specification
- ✓ Cost data in database matches source files after resync
- ✓ Running workflows are not affected by bulk resync
- ✓ Server logs record all resync operations
- ✓ No 500 errors or crashes during resync operations

## Expected API Response Format

### Successful Single Resync
```json
{
  "resynced_count": 1,
  "workflows": [
    {
      "adw_id": "workflow-123",
      "cost_updated": true
    }
  ],
  "errors": [],
  "message": "Successfully resynced workflow workflow-123"
}
```

### Successful Bulk Resync
```json
{
  "resynced_count": 5,
  "workflows": [
    {"adw_id": "w1", "status": "completed", "cost_updated": true},
    {"adw_id": "w2", "status": "completed", "cost_updated": true},
    {"adw_id": "w3", "status": "failed", "cost_updated": true},
    {"adw_id": "w4", "status": "completed", "cost_updated": false},
    {"adw_id": "w5", "status": "completed", "cost_updated": true}
  ],
  "errors": [],
  "message": "Bulk resync completed: 5 workflows updated, 0 errors"
}
```

### Error Response
```json
{
  "resynced_count": 0,
  "workflows": [],
  "errors": ["Workflow not found: nonexistent"],
  "message": "Failed to resync workflow nonexistent"
}
```

### Partial Success Response
```json
{
  "resynced_count": 2,
  "workflows": [
    {"adw_id": "w1", "status": "completed", "cost_updated": true},
    {"adw_id": "w2", "status": "completed", "cost_updated": true},
    {"adw_id": "w3", "status": "completed", "cost_updated": false}
  ],
  "errors": ["w3: Cost files not found"],
  "message": "Bulk resync completed: 2 workflows updated, 1 errors"
}
```

## Notes

- This is an administrative endpoint - use with caution in production
- The resync operation reads from authoritative cost files in `agents/<adw_id>/costs/*.jsonl`
- Force mode should be used when you need to completely recalculate cost data
- Bulk resync only processes completed and failed workflows (not running workflows)
- The endpoint is idempotent - running it multiple times should produce consistent results
- Cost data source of truth: `agents/<adw_id>/costs/*.jsonl` files
