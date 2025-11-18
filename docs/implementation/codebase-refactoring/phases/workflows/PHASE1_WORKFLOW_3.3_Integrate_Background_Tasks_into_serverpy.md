### Workflow 3.3: Integrate Background Tasks into server.py
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 3.1, 3.2

**Input Files:**
- `app/server/server.py`
- `app/server/services/background_tasks.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 279-408)

**Tasks:**
1. Add import for BackgroundTaskManager
2. Instantiate BackgroundTaskManager
3. Update startup event to call task_manager.start_all()
4. Update shutdown event to call task_manager.stop_all()
5. Remove old watcher function definitions

**Code Changes:**
```python
# Add import
from services.background_tasks import BackgroundTaskManager

# Instantiate manager
task_manager = BackgroundTaskManager(
    websocket_manager=manager,
    workflow_service=workflow_service,
    watch_interval=2.0
)

# Update lifecycle events
@app.on_event("startup")
async def startup_event():
    await task_manager.start_all()
    logger.info("Server started - background tasks running")

@app.on_event("shutdown")
async def shutdown_event():
    await task_manager.stop_all()
    logger.info("Server shutdown - background tasks stopped")
```

**Acceptance Criteria:**
- [ ] Background tasks start on server startup
- [ ] Background tasks stop on server shutdown
- [ ] WebSocket clients receive updates
- [ ] No task leaks on restart

**Verification Commands:**
```bash
# Start server and verify tasks running
cd app/server && python server.py &
SERVER_PID=$!
sleep 5

# Verify WebSocket updates being sent
# (Connect WebSocket client and verify messages)

# Shutdown and verify cleanup
kill $SERVER_PID
sleep 2
# Verify no hanging processes
```

---
