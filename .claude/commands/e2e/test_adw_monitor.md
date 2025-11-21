# E2E Test: ADW Monitor Endpoint

Test the ADW Monitor endpoint functionality for real-time workflow status tracking.

## User Story

As a system administrator
I want to monitor all active ADW workflows in real-time
So that I can track progress, identify issues, and understand system resource usage

## Test Steps

### Part 1: API Endpoint Test

1. **Verify** the server is running at the backend URL
2. Call the ADW monitor endpoint: `curl http://localhost:8000/api/adw-monitor`
3. **Verify** the response status code is 200
4. **Verify** the response is valid JSON
5. **Verify** the response contains the required top-level fields:
   - `summary`
   - `workflows`
   - `last_updated`

### Part 2: Response Schema Validation

6. **Verify** the `summary` object contains:
   - `total` (number)
   - `running` (number)
   - `completed` (number)
   - `failed` (number)
   - `paused` (number)

7. **Verify** `workflows` is an array
8. **Verify** `last_updated` is a valid ISO 8601 timestamp

### Part 3: Empty State Test

9. If no workflows are present:
   - **Verify** `summary.total` equals 0
   - **Verify** `workflows` is an empty array
   - **Verify** all status counts are 0

### Part 4: Workflow Data Validation

10. If workflows are present, for each workflow verify:
    - `adw_id` is present
    - `issue_number` is present (can be null)
    - `status` is one of: running, completed, failed, paused, queued
    - `phase_progress` is between 0 and 100
    - `total_phases` equals 8 (standard SDLC)
    - `is_process_active` is a boolean
    - `error_count` is a number

### Part 5: Summary Statistics Accuracy

11. **Verify** `summary.total` equals the length of `workflows` array
12. **Verify** status counts match the actual workflow statuses:
    - Count workflows with status "running" = `summary.running`
    - Count workflows with status "completed" = `summary.completed`
    - Count workflows with status "failed" = `summary.failed`
    - Count workflows with status "paused" = `summary.paused`

### Part 6: Data Quality Checks

13. **Verify** workflows are sorted by start time (most recent first)
14. **Verify** no duplicate `adw_id` values exist
15. **Verify** all workflow titles are non-empty strings
16. **Verify** cost fields (if present) are valid numbers

### Part 7: Performance Test

17. Record the response time for the API call
18. **Verify** response time is less than 200ms (with up to 15 workflows)
19. Make a second API call immediately after
20. **Verify** the second call returns cached data (same `last_updated` timestamp)

### Part 8: Error Handling Test

21. Test with corrupt state file (if possible):
    - Create a workflow with invalid JSON in `adw_state.json`
    - Call the endpoint
    - **Verify** the endpoint still returns 200
    - **Verify** the corrupt workflow is skipped (not in results)

## Success Criteria

- Endpoint returns 200 status code
- Response structure matches the defined schema
- Summary statistics are calculated correctly
- Workflows array contains valid workflow objects
- Empty state is handled gracefully
- Response time is acceptable (<200ms)
- Caching improves performance
- Error handling works (corrupt files don't break the endpoint)

## Manual Verification Commands

```bash
# Test the endpoint directly
curl http://localhost:8000/api/adw-monitor | python3 -m json.tool

# Check response time
time curl -s http://localhost:8000/api/adw-monitor > /dev/null

# Verify JSON structure with jq
curl -s http://localhost:8000/api/adw-monitor | jq '.summary, .workflows | length'
```

## Expected Output Example

```json
{
  "summary": {
    "total": 2,
    "running": 1,
    "completed": 1,
    "failed": 0,
    "paused": 0
  },
  "workflows": [
    {
      "adw_id": "abc123",
      "issue_number": 42,
      "issue_class": "bug",
      "title": "Fix authentication bug",
      "status": "running",
      "current_phase": "build",
      "phase_progress": 25.0,
      "workflow_template": "adw_sdlc_iso",
      "start_time": "2025-01-01T10:00:00",
      "end_time": null,
      "duration_seconds": null,
      "github_url": "https://github.com/test/repo/issues/42",
      "worktree_path": "/path/to/trees/abc123",
      "current_cost": 1.23,
      "estimated_cost_total": 5.67,
      "error_count": 0,
      "last_error": null,
      "is_process_active": true,
      "phases_completed": [],
      "total_phases": 8
    }
  ],
  "last_updated": "2025-01-01T12:00:00"
}
```

## Notes

- This is primarily an API test (no UI components in Phase 1)
- Frontend component will be added in Phase 2
- Test can be run manually or automated with pytest
- Focus on data accuracy and performance
