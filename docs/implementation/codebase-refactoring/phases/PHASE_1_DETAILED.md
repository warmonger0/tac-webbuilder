# Phase 1: Extract Server Services - Detailed Implementation Plan

**Status:** Not Started
**Duration:** 4-5 days (20-25 atomic workflows)
**Priority:** CRITICAL
**Risk:** Low

## Overview

Split `app/server/server.py` (2,091 lines) into focused service modules, reducing the main server file to <300 lines. This phase establishes the service layer architecture pattern for the entire application.

**Success Criteria:**
- ✅ `server.py` reduced to <300 lines
- ✅ 5 new service modules created and tested
- ✅ All existing functionality preserved
- ✅ No performance degradation
- ✅ 80%+ test coverage for new services

---

## Hierarchical Decomposition

### Level 1: Major Components
1. WebSocket Manager Service (3 workflows)
2. Workflow Service (4 workflows)
3. Background Tasks Service (4 workflows)
4. Health Service (6 workflows)
5. Service Controller (4 workflows)
6. Integration & Migration (4 workflows)

### Level 2: Atomic Workflow Units

---

## 1. WebSocket Manager Service (3 workflows)

### Workflow 1.1: Create WebSocket Manager Module
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 124-154)

**Output Files:**
- `app/server/services/__init__.py` (new)
- `app/server/services/websocket_manager.py` (new)

**Tasks:**
1. Create `app/server/services/` directory
2. Create `__init__.py` with module exports
3. Extract `ConnectionManager` class from server.py
4. Add logging and error handling
5. Add docstrings to all methods

**Acceptance Criteria:**
- [ ] ConnectionManager class exists in websocket_manager.py
- [ ] All methods have type hints
- [ ] All methods have docstrings
- [ ] Module can be imported without errors

**Code to Extract:**
```python
# Lines 124-154 from server.py
class ConnectionManager:
    def __init__(self): ...
    async def connect(self, websocket: WebSocket): ...
    def disconnect(self, websocket: WebSocket): ...
    async def broadcast(self, message: dict): ...
```

**Verification Command:**
```bash
python -c "from app.server.services.websocket_manager import ConnectionManager; print('Import successful')"
```

---

### Workflow 1.2: Create WebSocket Manager Tests
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1

**Input Files:**
- `app/server/services/websocket_manager.py`

**Output Files:**
- `app/server/tests/services/__init__.py` (new)
- `app/server/tests/services/test_websocket_manager.py` (new)

**Tasks:**
1. Create test directory structure
2. Write test for `connect()` method
3. Write test for `disconnect()` method
4. Write test for `broadcast()` method
5. Write test for error handling in broadcast
6. Write test for `connection_count()` method

**Test Cases:**
- ✅ Connect adds websocket to active connections
- ✅ Disconnect removes websocket from active connections
- ✅ Broadcast sends message to all connections
- ✅ Broadcast handles disconnected clients gracefully
- ✅ Connection count returns correct number

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] All edge cases covered (disconnected clients, errors)

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_websocket_manager.py -v --cov=services.websocket_manager --cov-report=term-missing
```

---

### Workflow 1.3: Integrate WebSocket Manager into server.py
**Estimated Time:** 30 minutes
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/server/server.py`
- `app/server/services/websocket_manager.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 124-154)

**Tasks:**
1. Add import statement for ConnectionManager
2. Remove ConnectionManager class definition
3. Verify all WebSocket routes still work
4. Update any type hints if needed

**Code Changes:**
```python
# Add at top of server.py
from services.websocket_manager import ConnectionManager

# Remove lines 124-154 (ConnectionManager class)

# Existing usage remains unchanged:
manager = ConnectionManager()
```

**Acceptance Criteria:**
- [ ] server.py imports ConnectionManager successfully
- [ ] WebSocket endpoints work correctly
- [ ] All existing tests still pass
- [ ] Integration tests pass

**Verification Commands:**
```bash
# Start server and test WebSocket connection
cd app/server && python server.py &
sleep 2
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws/workflows
```

---

## 2. Workflow Service (4 workflows)

### Workflow 2.1: Create Workflow Service Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 156-277, 327-373)

**Output Files:**
- `app/server/services/workflow_service.py` (new)

**Tasks:**
1. Create WorkflowService class
2. Extract `get_workflows_data()` → `get_workflows()`
3. Extract `get_routes_data()` → `get_routes()`
4. Add `get_history()` wrapper method
5. Add configuration for workflows directory path
6. Add error handling and logging

**Class Structure:**
```python
class WorkflowService:
    def __init__(self, workflows_dir: str = "agents"):
        self.workflows_dir = Path(workflows_dir)

    def get_workflows(self) -> List[Workflow]:
        """Scan and return all workflows"""

    def _parse_workflow_directory(self, workflow_dir: Path) -> Optional[Workflow]:
        """Parse single workflow directory"""

    def get_routes(self) -> List[Route]:
        """Get all available API routes"""

    def get_history(...) -> WorkflowHistoryResponse:
        """Get workflow history with filtering"""
```

**Acceptance Criteria:**
- [ ] WorkflowService class created
- [ ] All methods have type hints
- [ ] All methods have docstrings
- [ ] Error handling for missing directories
- [ ] Logging for important operations

**Verification Command:**
```bash
python -c "from app.server.services.workflow_service import WorkflowService; ws = WorkflowService(); print(len(ws.get_workflows()))"
```

---

### Workflow 2.2: Create Workflow Service Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/server/services/workflow_service.py`

**Output Files:**
- `app/server/tests/services/test_workflow_service.py` (new)

**Tasks:**
1. Create fixtures for temporary workflow directories
2. Write test for empty directory
3. Write test for valid workflow directory
4. Write test for invalid workflow directory (no state file)
5. Write test for corrupted state file
6. Write test for workflow sorting (newest first)
7. Write test for history pagination

**Test Cases:**
- ✅ Empty directory returns empty list
- ✅ Valid workflow directory parsed correctly
- ✅ Invalid directories are skipped
- ✅ Corrupted JSON handled gracefully
- ✅ Workflows sorted by creation time
- ✅ History pagination works correctly

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] Edge cases covered (missing files, bad JSON, etc.)
- [ ] Temporary test data cleaned up properly

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_workflow_service.py -v --cov=services.workflow_service --cov-report=term-missing
```

---

### Workflow 2.3: Integrate Workflow Service into server.py
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 2.1, 2.2

**Input Files:**
- `app/server/server.py`
- `app/server/services/workflow_service.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 156-277, 327-373)

**Tasks:**
1. Add import for WorkflowService
2. Instantiate WorkflowService
3. Update `/api/workflows` endpoint to use service
4. Update `/api/workflow-history` endpoint to use service
5. Remove old function definitions
6. Test all workflow-related endpoints

**Code Changes:**
```python
# Add import
from services.workflow_service import WorkflowService

# Instantiate service
workflow_service = WorkflowService()

# Update endpoints
@app.get("/api/workflows")
async def get_workflows():
    workflows = workflow_service.get_workflows()
    return {"workflows": workflows}

@app.get("/api/workflow-history")
async def get_workflow_history_endpoint(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    return workflow_service.get_history(
        limit=limit, offset=offset,
        status_filter=status, search_query=search
    )
```

**Acceptance Criteria:**
- [ ] All workflow endpoints return correct data
- [ ] No regression in functionality
- [ ] All existing tests pass
- [ ] API response times unchanged

**Verification Commands:**
```bash
# Test workflows endpoint
curl http://localhost:8000/api/workflows | jq '.workflows | length'

# Test history endpoint
curl http://localhost:8000/api/workflow-history?limit=10 | jq '.workflows | length'
```

---

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

---

## 3. Background Tasks Service (4 workflows)

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

---

### Workflow 3.2: Create Background Tasks Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1

**Input Files:**
- `app/server/services/background_tasks.py`

**Output Files:**
- `app/server/tests/services/test_background_tasks.py` (new)

**Tasks:**
1. Write test for task startup
2. Write test for task shutdown
3. Write test for workflow watcher broadcasts
4. Write test for routes watcher broadcasts
5. Write test for history watcher broadcasts
6. Write test for error handling in watchers
7. Write test for cancellation handling

**Test Cases:**
- ✅ start_all() creates all tasks
- ✅ stop_all() cancels all tasks
- ✅ Workflow watcher broadcasts on changes
- ✅ Routes watcher broadcasts on changes
- ✅ History watcher broadcasts on changes
- ✅ Errors in watchers don't crash tasks
- ✅ Cancellation handled gracefully

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] Async behavior tested properly
- [ ] No task leaks in tests

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_background_tasks.py -v --cov=services.background_tasks --cov-report=term-missing
```

---

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

---

## 4. Health Service (6 workflows)

### Workflow 4.1: Create Health Service Module - Core Structure
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 610-843)

**Output Files:**
- `app/server/services/health_service.py` (new)

**Tasks:**
1. Create ServiceStatus enum
2. Create ServiceHealth dataclass
3. Create HealthService class skeleton
4. Add configuration for health check targets
5. Add `check_all()` method structure

**Code Structure:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus
    message: str
    details: Optional[Dict] = None

class HealthService:
    def __init__(
        self,
        db_path: str = "db/database.db",
        webhook_url: str = "http://localhost:8001/health",
        cloudflare_tunnel_name: Optional[str] = None,
        frontend_url: str = "http://localhost:5173"
    ):
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.cloudflare_tunnel_name = cloudflare_tunnel_name
        self.frontend_url = frontend_url

    async def check_all(self) -> Dict[str, ServiceHealth]:
        """Check health of all services"""
        return {
            "backend": self.check_backend(),
            "database": self.check_database(),
            "webhook": await self.check_webhook(),
            "cloudflare": self.check_cloudflare_tunnel(),
            "github_webhook": await self.check_github_webhook(),
            "frontend": await self.check_frontend()
        }
```

**Acceptance Criteria:**
- [ ] Module imports without errors
- [ ] Enums and dataclasses defined
- [ ] HealthService class instantiable
- [ ] check_all() method defined (stub implementations OK)

**Verification Command:**
```bash
python -c "from app.server.services.health_service import HealthService; hs = HealthService(); print('Module created successfully')"
```

---

### Workflow 4.2: Implement Backend and Database Health Checks
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/server/services/health_service.py`
- `app/server/server.py` (database check logic)

**Output Files:**
- `app/server/services/health_service.py` (modified)

**Tasks:**
1. Implement `check_backend()` method
2. Implement `check_database()` method
3. Add database table existence checks
4. Add error handling for database connection failures
5. Add logging for health check results

**Implementation:**
```python
def check_backend(self) -> ServiceHealth:
    """Backend is healthy if this code runs"""
    return ServiceHealth(
        name="Backend API",
        status=ServiceStatus.HEALTHY,
        message="Backend server is running"
    )

def check_database(self) -> ServiceHealth:
    """Check database connectivity and structure"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check critical tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('workflows', 'workflow_history')
        """)
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()

        if len(tables) >= 2:
            return ServiceHealth(
                name="Database",
                status=ServiceStatus.HEALTHY,
                message="Database accessible with all tables",
                details={"tables": tables}
            )
        else:
            return ServiceHealth(
                name="Database",
                status=ServiceStatus.DEGRADED,
                message="Database accessible but missing tables",
                details={"tables": tables}
            )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ServiceHealth(
            name="Database",
            status=ServiceStatus.UNHEALTHY,
            message=f"Database error: {str(e)}"
        )
```

**Acceptance Criteria:**
- [ ] Backend check always returns HEALTHY
- [ ] Database check verifies table existence
- [ ] Database check handles missing DB file
- [ ] Database check handles missing tables
- [ ] Errors logged appropriately

**Verification Command:**
```bash
python -c "
from app.server.services.health_service import HealthService
hs = HealthService()
print(hs.check_backend())
print(hs.check_database())
"
```

---

### Workflow 4.3: Implement HTTP Service Health Checks
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/server/services/health_service.py`
- `app/server/server.py` (webhook/frontend check logic)

**Output Files:**
- `app/server/services/health_service.py` (modified)

**Tasks:**
1. Implement `check_webhook()` method
2. Implement `check_frontend()` method
3. Implement `check_github_webhook()` method
4. Add timeout handling for HTTP requests
5. Add error handling for connection failures

**Implementation:**
```python
async def check_webhook(self) -> ServiceHealth:
    """Check webhook service health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(self.webhook_url)

            if response.status_code == 200:
                return ServiceHealth(
                    name="Webhook Service",
                    status=ServiceStatus.HEALTHY,
                    message="Webhook service responding"
                )
            else:
                return ServiceHealth(
                    name="Webhook Service",
                    status=ServiceStatus.DEGRADED,
                    message=f"Webhook returned status {response.status_code}"
                )
    except httpx.TimeoutException:
        return ServiceHealth(
            name="Webhook Service",
            status=ServiceStatus.UNHEALTHY,
            message="Webhook service timeout"
        )
    except Exception as e:
        logger.error(f"Webhook health check failed: {e}")
        return ServiceHealth(
            name="Webhook Service",
            status=ServiceStatus.UNHEALTHY,
            message=f"Webhook error: {str(e)}"
        )

async def check_frontend(self) -> ServiceHealth:
    """Check frontend server health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(self.frontend_url)

            if response.status_code == 200:
                return ServiceHealth(
                    name="Frontend",
                    status=ServiceStatus.HEALTHY,
                    message="Frontend server responding"
                )
            else:
                return ServiceHealth(
                    name="Frontend",
                    status=ServiceStatus.DEGRADED,
                    message=f"Frontend returned status {response.status_code}"
                )
    except Exception as e:
        logger.error(f"Frontend health check failed: {e}")
        return ServiceHealth(
            name="Frontend",
            status=ServiceStatus.UNHEALTHY,
            message=f"Frontend error: {str(e)}"
        )
```

**Acceptance Criteria:**
- [ ] Webhook check handles timeouts
- [ ] Frontend check handles connection errors
- [ ] HTTP status codes evaluated correctly
- [ ] All async operations use timeout

**Verification Command:**
```bash
python -c "
import asyncio
from app.server.services.health_service import HealthService

async def test():
    hs = HealthService()
    print(await hs.check_webhook())
    print(await hs.check_frontend())

asyncio.run(test())
"
```

---

### Workflow 4.4: Implement Cloudflare Tunnel Health Check
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/server/services/health_service.py`
- `app/server/server.py` (Cloudflare check logic)

**Output Files:**
- `app/server/services/health_service.py` (modified)

**Tasks:**
1. Implement `check_cloudflare_tunnel()` method
2. Add subprocess execution for cloudflared command
3. Add timeout handling
4. Add handling for missing cloudflared command
5. Add handling for unconfigured tunnel name

**Implementation:**
```python
def check_cloudflare_tunnel(self) -> ServiceHealth:
    """Check Cloudflare tunnel status"""
    if not self.cloudflare_tunnel_name:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message="Tunnel name not configured"
        )

    try:
        result = subprocess.run(
            ["cloudflared", "tunnel", "info", self.cloudflare_tunnel_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return ServiceHealth(
                name="Cloudflare Tunnel",
                status=ServiceStatus.HEALTHY,
                message="Tunnel is active"
            )
        else:
            return ServiceHealth(
                name="Cloudflare Tunnel",
                status=ServiceStatus.UNHEALTHY,
                message="Tunnel not active"
            )
    except subprocess.TimeoutExpired:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNHEALTHY,
            message="Tunnel check timeout"
        )
    except FileNotFoundError:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message="cloudflared command not found"
        )
    except Exception as e:
        logger.error(f"Cloudflare tunnel check failed: {e}")
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message=f"Check error: {str(e)}"
        )
```

**Acceptance Criteria:**
- [ ] Handles unconfigured tunnel name
- [ ] Handles missing cloudflared command
- [ ] Handles tunnel check timeout
- [ ] Returns appropriate status levels

**Verification Command:**
```bash
python -c "
from app.server.services.health_service import HealthService
hs = HealthService(cloudflare_tunnel_name='test-tunnel')
print(hs.check_cloudflare_tunnel())
"
```

---

### Workflow 4.5: Create Health Service Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflows 4.2, 4.3, 4.4

**Input Files:**
- `app/server/services/health_service.py`

**Output Files:**
- `app/server/tests/services/test_health_service.py` (new)

**Tasks:**
1. Create fixtures for temporary database
2. Write tests for backend check
3. Write tests for database check (healthy, degraded, unhealthy)
4. Write tests for webhook check (mocked HTTP)
5. Write tests for frontend check (mocked HTTP)
6. Write tests for Cloudflare check (mocked subprocess)
7. Write tests for overall status calculation
8. Write tests for check_all() method

**Test Cases:**
- ✅ Backend check always returns HEALTHY
- ✅ Database check with valid DB returns HEALTHY
- ✅ Database check with missing tables returns DEGRADED
- ✅ Database check with missing file returns UNHEALTHY
- ✅ Webhook check with 200 response returns HEALTHY
- ✅ Webhook check with timeout returns UNHEALTHY
- ✅ Frontend check with 200 response returns HEALTHY
- ✅ Cloudflare check handles missing command
- ✅ Overall status aggregation works correctly
- ✅ check_all() returns all service statuses

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] HTTP requests properly mocked
- [ ] Subprocess calls properly mocked
- [ ] Async tests work correctly

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_health_service.py -v --cov=services.health_service --cov-report=term-missing
```

---

### Workflow 4.6: Integrate Health Service into server.py
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflows 4.2, 4.3, 4.4, 4.5

**Input Files:**
- `app/server/server.py`
- `app/server/services/health_service.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 610-843)

**Tasks:**
1. Add import for HealthService
2. Instantiate HealthService with configuration
3. Update `/api/system-status` endpoint
4. Remove old health check function definitions
5. Test health endpoint

**Code Changes:**
```python
# Add import
from services.health_service import HealthService

# Instantiate service
health_service = HealthService(
    db_path="db/database.db",
    webhook_url="http://localhost:8001/health",
    cloudflare_tunnel_name=os.getenv("CLOUDFLARE_TUNNEL_NAME"),
    frontend_url="http://localhost:5173"
)

# Update endpoint
@app.get("/api/system-status")
async def get_system_status():
    services = await health_service.check_all()
    overall_status = health_service.get_overall_status(services)

    return {
        "overall_status": overall_status,
        "services": {
            name: {
                "status": health.status,
                "message": health.message,
                "details": health.details
            }
            for name, health in services.items()
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Acceptance Criteria:**
- [ ] Health endpoint returns correct structure
- [ ] All services checked
- [ ] Overall status calculated correctly
- [ ] Response includes timestamp

**Verification Command:**
```bash
curl http://localhost:8000/api/system-status | jq
```

---

## 5. Service Controller (4 workflows)

### Workflow 5.1: Create Service Controller Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 845-1171 - service management routes)

**Output Files:**
- `app/server/services/service_controller.py` (new)

**Tasks:**
1. Create ServiceController class
2. Extract webhook service start/stop logic
3. Extract Cloudflare tunnel restart logic
4. Extract GitHub webhook redeliver logic
5. Add error handling and logging
6. Add service state tracking

**Class Structure:**
```python
class ServiceController:
    """Controls starting, stopping, and restarting external services"""

    def __init__(self):
        self.webhook_process: Optional[subprocess.Popen] = None
        self.cloudflare_process: Optional[subprocess.Popen] = None

    async def start_webhook_service(self) -> Dict[str, Any]:
        """Start webhook service"""

    async def stop_webhook_service(self) -> Dict[str, Any]:
        """Stop webhook service"""

    async def restart_cloudflare_tunnel(self) -> Dict[str, Any]:
        """Restart Cloudflare tunnel"""

    async def redeliver_github_webhook(self, issue_number: int) -> Dict[str, Any]:
        """Redeliver GitHub webhook for issue"""
```

**Acceptance Criteria:**
- [ ] ServiceController class created
- [ ] All methods have type hints and docstrings
- [ ] Process tracking implemented
- [ ] Error handling for failed operations

**Verification Command:**
```bash
python -c "from app.server.services.service_controller import ServiceController; sc = ServiceController(); print('Module created')"
```

---

### Workflow 5.2: Implement Service Start/Stop Methods
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 5.1

**Input Files:**
- `app/server/services/service_controller.py`
- `app/server/server.py` (webhook start/stop logic)

**Output Files:**
- `app/server/services/service_controller.py` (modified)

**Tasks:**
1. Implement webhook service start
2. Implement webhook service stop
3. Add process PID tracking
4. Add graceful shutdown logic
5. Add force kill after timeout

**Implementation:**
```python
async def start_webhook_service(self) -> Dict[str, Any]:
    """Start webhook service in background"""
    if self.webhook_process and self.webhook_process.poll() is None:
        return {
            "status": "already_running",
            "message": "Webhook service is already running",
            "pid": self.webhook_process.pid
        }

    try:
        self.webhook_process = subprocess.Popen(
            ["python", "adws/adw_triggers/trigger_webhook.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Give it a moment to start
        await asyncio.sleep(1)

        if self.webhook_process.poll() is None:
            return {
                "status": "started",
                "message": "Webhook service started successfully",
                "pid": self.webhook_process.pid
            }
        else:
            return {
                "status": "failed",
                "message": "Webhook service failed to start"
            }
    except Exception as e:
        logger.error(f"Failed to start webhook service: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def stop_webhook_service(self) -> Dict[str, Any]:
    """Stop webhook service gracefully"""
    if not self.webhook_process or self.webhook_process.poll() is not None:
        return {
            "status": "not_running",
            "message": "Webhook service is not running"
        }

    try:
        # Try graceful shutdown first
        self.webhook_process.terminate()

        # Wait up to 5 seconds for graceful shutdown
        for _ in range(50):
            if self.webhook_process.poll() is not None:
                return {
                    "status": "stopped",
                    "message": "Webhook service stopped gracefully"
                }
            await asyncio.sleep(0.1)

        # Force kill if still running
        self.webhook_process.kill()
        self.webhook_process.wait()

        return {
            "status": "stopped",
            "message": "Webhook service force killed after timeout"
        }
    except Exception as e:
        logger.error(f"Failed to stop webhook service: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
```

**Acceptance Criteria:**
- [ ] Start method launches process
- [ ] Stop method terminates gracefully
- [ ] Force kill used if graceful fails
- [ ] PID tracking works correctly
- [ ] Already running state handled

**Verification Command:**
```bash
python -c "
import asyncio
from app.server.services.service_controller import ServiceController

async def test():
    sc = ServiceController()
    result = await sc.start_webhook_service()
    print('Start:', result)
    await asyncio.sleep(2)
    result = await sc.stop_webhook_service()
    print('Stop:', result)

asyncio.run(test())
"
```

---

### Workflow 5.3: Create Service Controller Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 5.2

**Input Files:**
- `app/server/services/service_controller.py`

**Output Files:**
- `app/server/tests/services/test_service_controller.py` (new)

**Tasks:**
1. Write tests for webhook start (mocked subprocess)
2. Write tests for webhook stop (mocked subprocess)
3. Write tests for already running scenario
4. Write tests for not running scenario
5. Write tests for start failure
6. Write tests for stop timeout (force kill)

**Test Cases:**
- ✅ Start webhook service creates process
- ✅ Start when already running returns appropriate status
- ✅ Stop webhook service terminates process
- ✅ Stop when not running returns appropriate status
- ✅ Stop uses force kill after timeout
- ✅ Start failure handled gracefully

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] Subprocess calls properly mocked
- [ ] Async operations tested correctly

**Verification Command:**
```bash
cd app/server && pytest tests/services/test_service_controller.py -v --cov=services.service_controller --cov-report=term-missing
```

---

### Workflow 5.4: Integrate Service Controller into server.py
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 5.3

**Input Files:**
- `app/server/server.py`
- `app/server/services/service_controller.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 845-1171)

**Tasks:**
1. Add import for ServiceController
2. Instantiate ServiceController
3. Update service management endpoints
4. Remove old service management code
5. Test all service control endpoints

**Code Changes:**
```python
# Add import
from services.service_controller import ServiceController

# Instantiate controller
service_controller = ServiceController()

# Update endpoints
@app.post("/api/services/webhook/start")
async def start_webhook():
    return await service_controller.start_webhook_service()

@app.post("/api/services/webhook/stop")
async def stop_webhook():
    return await service_controller.stop_webhook_service()

@app.post("/api/services/cloudflare/restart")
async def restart_cloudflare():
    return await service_controller.restart_cloudflare_tunnel()

@app.post("/api/services/github-webhook/redeliver/{issue_number}")
async def redeliver_webhook(issue_number: int):
    return await service_controller.redeliver_github_webhook(issue_number)
```

**Acceptance Criteria:**
- [ ] All service control endpoints work
- [ ] Services can be started/stopped via API
- [ ] Error handling works correctly
- [ ] No regression in functionality

**Verification Commands:**
```bash
# Start webhook service
curl -X POST http://localhost:8000/api/services/webhook/start | jq

# Check status
sleep 2

# Stop webhook service
curl -X POST http://localhost:8000/api/services/webhook/stop | jq
```

---

## 6. Integration & Migration (4 workflows)

### Workflow 6.1: Create Integration Test Suite
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** All previous workflows

**Input Files:**
- All service modules
- `app/server/server.py`

**Output Files:**
- `app/server/tests/integration/test_phase1_integration.py` (new)

**Tasks:**
1. Write test for complete server startup
2. Write test for WebSocket + workflow updates
3. Write test for health checks + service status
4. Write test for background tasks + broadcasts
5. Write test for service lifecycle (start/stop/restart)

**Test Cases:**
- ✅ Server starts with all services initialized
- ✅ WebSocket connections receive workflow updates
- ✅ Health checks return correct system status
- ✅ Background tasks broadcast changes
- ✅ Service controller can manage services
- ✅ All services interact correctly

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Tests cover service interactions
- [ ] End-to-end flows verified
- [ ] No race conditions or timing issues

**Verification Command:**
```bash
cd app/server && pytest tests/integration/test_phase1_integration.py -v
```

---

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

---

### Workflow 6.3: Performance Benchmarking
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 6.2

**Input Files:**
- All service modules
- `app/server/server.py`

**Output Files:**
- `docs/implementation/codebase-refactoring/PHASE_1_BENCHMARKS.md` (new)

**Tasks:**
1. Benchmark API response times (before vs after)
2. Benchmark memory usage
3. Benchmark WebSocket latency
4. Benchmark background task overhead
5. Document all metrics
6. Compare with baseline

**Metrics to Capture:**
- `/api/workflows` response time (p50, p95, p99)
- `/api/workflow-history` response time
- `/api/system-status` response time
- Memory usage at startup
- Memory usage after 1 hour
- WebSocket message latency
- Background task CPU usage

**Acceptance Criteria:**
- [ ] All metrics within acceptable ranges
- [ ] No performance regression (>10%)
- [ ] Memory usage stable
- [ ] Benchmark document created

**Verification Command:**
```bash
# Use Apache Bench or similar tool
ab -n 1000 -c 10 http://localhost:8000/api/workflows
```

---

### Workflow 6.4: Documentation and Cleanup
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** All previous workflows

**Input Files:**
- All new service modules
- All test files

**Output Files:**
- `app/server/services/README.md` (new)
- `docs/implementation/codebase-refactoring/PHASE_1_COMPLETE.md` (new)

**Tasks:**
1. Create services README documenting architecture
2. Document each service module's responsibility
3. Create Phase 1 completion report
4. Update main REFACTORING_PLAN.md with completion status
5. Document lessons learned
6. Document any deviations from plan

**Services README Structure:**
```markdown
# Server Services Layer

## Overview
Service layer extracted from monolithic server.py to improve modularity.

## Services

### WebSocketManager (websocket_manager.py)
- Manages WebSocket connections
- Broadcasts updates to connected clients
- Usage: ...

### WorkflowService (workflow_service.py)
- Workflow data operations
- Directory scanning and parsing
- Usage: ...

### BackgroundTaskManager (background_tasks.py)
- Background file watchers
- Real-time update broadcasting
- Usage: ...

### HealthService (health_service.py)
- System health monitoring
- Service status checks
- Usage: ...

### ServiceController (service_controller.py)
- External service management
- Start/stop/restart operations
- Usage: ...
```

**Acceptance Criteria:**
- [ ] All services documented
- [ ] Architecture decisions explained
- [ ] Usage examples provided
- [ ] Completion report created
- [ ] REFACTORING_PLAN.md updated

**Verification:**
- [ ] Documentation is clear and complete
- [ ] Future developers can understand architecture
- [ ] All changes tracked in git commits

---

## Summary Statistics

**Total Workflows:** 25 atomic units
**Total Estimated Time:** 35-45 hours
**Parallelization Potential:** High (services can be extracted independently)

**Workflow Dependencies:**
```
1.1 → 1.2 → 1.3
2.1 → 2.2 → 2.3 → 2.4
3.1 → 3.2 → 3.3 → 3.4
4.1 → 4.2 ↘
       4.3 → 4.5 → 4.6
       4.4 ↗
5.1 → 5.2 → 5.3 → 5.4

All → 6.1 → 6.2 → 6.3 → 6.4
```

**Optimal Execution Order (with 3 parallel workers):**
- **Day 1:** 1.1-1.3, 2.1-2.2, 4.1-4.2 (parallel)
- **Day 2:** 2.3-2.4, 3.1-3.2, 4.3-4.4 (parallel)
- **Day 3:** 3.3-3.4, 5.1-5.2, 4.5-4.6 (parallel)
- **Day 4:** 5.3-5.4, 6.1-6.2 (parallel)
- **Day 5:** 6.3-6.4 (sequential)

---

## Next Steps

1. Review this detailed plan
2. Select first workflow to implement (recommend 1.1)
3. Create feature branch: `refactor/phase1-websocket-manager`
4. Execute workflow 1.1
5. Commit and test
6. Proceed to workflow 1.2
7. Continue through all workflows systematically

---

**Document Status:** Complete
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Related:** [REFACTORING_PLAN.md](../REFACTORING_PLAN.md)
