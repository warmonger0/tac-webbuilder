### Workflow 2.4: Update Background Watchers for Workflow Service
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 2.3

**Input Files:**
- `app/server/server.py` (background watcher functions)
- `app/server/services/workflow_service.py`

**Output Files:**
- `app/server/server.py` (modified)

**Tasks:**
1. Update `watch_workflows()` to use workflow_service.get_workflows()
2. Update `watch_routes()` to use workflow_service.get_routes()
3. Update `watch_workflow_history()` to use workflow_service.get_history()
4. Test real-time updates still work

**Code Changes:**
```python
async def watch_workflows():
    previous_workflows = None
    while True:
        try:
            # OLD: workflows = get_workflows_data()
            # NEW:
            workflows = workflow_service.get_workflows()

            if workflows != previous_workflows:
                await manager.broadcast({
                    "type": "workflows_update",
                    "data": [w.dict() for w in workflows]
                })
                previous_workflows = workflows

            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error in workflow watcher: {e}")
```

**Acceptance Criteria:**
- [ ] Background watchers use WorkflowService
- [ ] Real-time updates still broadcast correctly
- [ ] No memory leaks from watcher tasks
- [ ] WebSocket clients receive updates

**Verification Command:**
```bash
# Connect WebSocket client and verify updates received
# (Manual test or automated WebSocket test)
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
