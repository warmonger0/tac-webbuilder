### Workflow 3.4: Add Background Task Monitoring
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 3.3

**Input Files:**
- `app/server/services/background_tasks.py`

**Output Files:**
- `app/server/services/background_tasks.py` (modified)
- `app/server/server.py` (add monitoring endpoint)

**Tasks:**
1. Add task health tracking to BackgroundTaskManager
2. Add method to get task status
3. Add endpoint to expose task health
4. Add tests for monitoring

**Code Changes:**
```python
# In BackgroundTaskManager
def get_task_status(self) -> Dict[str, Any]:
    """Get status of all background tasks"""
    return {
        "total_tasks": len(self._tasks),
        "running_tasks": sum(1 for t in self._tasks if not t.done()),
        "tasks": [
            {
                "name": t.get_name(),
                "done": t.done(),
                "cancelled": t.cancelled() if t.done() else False
            }
            for t in self._tasks
        ]
    }

# In server.py
@app.get("/api/background-tasks/status")
async def get_background_tasks_status():
    return task_manager.get_task_status()
```

**Acceptance Criteria:**
- [ ] Task status endpoint returns correct data
- [ ] Status includes all tasks
- [ ] Status updates in real-time

**Verification Command:**
```bash
curl http://localhost:8000/api/background-tasks/status | jq
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
