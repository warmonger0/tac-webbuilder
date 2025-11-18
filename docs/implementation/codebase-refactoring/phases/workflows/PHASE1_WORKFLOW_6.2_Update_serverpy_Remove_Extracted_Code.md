### Workflow 6.2: Update server.py - Remove Extracted Code
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflows 1.3, 2.3, 3.3, 4.6, 5.4

**Input Files:**
- `app/server/server.py`

**Output Files:**
- `app/server/server.py` (modified - final cleanup)

**Tasks:**
1. Remove all extracted service code
2. Verify all imports are at top
3. Organize imports (stdlib, third-party, local)
4. Verify no dead code remains
5. Add comments for service layer architecture
6. Count final line count

**Expected Final Structure:**
```python
# Imports (stdlib)
# Imports (third-party)
# Imports (local - services)
from services.websocket_manager import ConnectionManager
from services.workflow_service import WorkflowService
from services.background_tasks import BackgroundTaskManager
from services.health_service import HealthService
from services.service_controller import ServiceController

# FastAPI app initialization
app = FastAPI()

# Service initialization
manager = ConnectionManager()
workflow_service = WorkflowService()
task_manager = BackgroundTaskManager(manager, workflow_service)
health_service = HealthService()
service_controller = ServiceController()

# Lifecycle events
@app.on_event("startup")
async def startup_event(): ...

@app.on_event("shutdown")
async def shutdown_event(): ...

# WebSocket routes
@app.websocket("/ws/workflows")
async def websocket_workflows(websocket: WebSocket): ...

# API routes (grouped by domain)
# ... workflow routes ...
# ... health routes ...
# ... service management routes ...
```

**Acceptance Criteria:**
- [ ] server.py is <300 lines
- [ ] All extracted code removed
- [ ] No dead code or commented code
- [ ] Imports organized properly
- [ ] Code is well-commented

**Verification Command:**
```bash
wc -l app/server/server.py
# Should be <300 lines
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
