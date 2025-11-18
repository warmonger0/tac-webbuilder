### Workflow 3.1: Create Background Tasks Manager Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1, 2.1

**Input Files:**
- `app/server/server.py` (lines 279-408)

**Output Files:**
- `app/server/services/background_tasks.py` (new)

**Tasks:**
1. Create BackgroundTaskManager class
2. Extract `watch_workflows()` method
3. Extract `watch_routes()` method
4. Extract `watch_workflow_history()` method
5. Add `start_all()` and `stop_all()` methods
6. Add proper task lifecycle management
7. Add error handling and logging

**Class Structure:**
```python
class BackgroundTaskManager:
    def __init__(
        self,
        websocket_manager: ConnectionManager,
        workflow_service: WorkflowService,
        watch_interval: float = 2.0
    ):
        self.websocket_manager = websocket_manager
        self.workflow_service = workflow_service
        self.watch_interval = watch_interval
        self._tasks: list[asyncio.Task] = []

    async def start_all(self) -> None:
        """Start all background tasks"""

    async def stop_all(self) -> None:
        """Stop all background tasks"""

    async def watch_workflows(self) -> None:
        """Watch workflow directory for changes"""

    async def watch_routes(self) -> None:
        """Watch routes for changes"""

    async def watch_workflow_history(self) -> None:
        """Watch workflow history for changes"""
```

**Acceptance Criteria:**
- [ ] BackgroundTaskManager class created
- [ ] All watcher methods properly handle cancellation
- [ ] Task lifecycle managed (start/stop)
- [ ] Logging for task state changes
- [ ] No task leaks on shutdown

**Verification Command:**
```bash
python -c "
from app.server.services.background_tasks import BackgroundTaskManager
from app.server.services.websocket_manager import ConnectionManager
from app.server.services.workflow_service import WorkflowService
import asyncio

async def test():
    manager = BackgroundTaskManager(
        ConnectionManager(),
        WorkflowService(),
        watch_interval=0.5
    )
    await manager.start_all()
    await asyncio.sleep(1)
    await manager.stop_all()
    print('Task lifecycle test passed')

asyncio.run(test())
"
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
