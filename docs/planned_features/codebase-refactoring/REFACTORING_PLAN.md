# Refactoring Implementation Plan

**Date:** 2025-11-17
**Status:** Planning Complete - Ready for Implementation
**Estimated Duration:** 15-20 days
**Priority:** High

## Overview

This document provides a detailed, phase-by-phase implementation plan for refactoring the TAC WebBuilder codebase. The plan is designed to be executed incrementally with minimal disruption to ongoing development.

**Related Documents:**
- [Refactoring Analysis](./REFACTORING_ANALYSIS.md) - Comprehensive analysis of issues
- [Architecture Guide](../../architecture/README.md) - Current architecture documentation

---

## Table of Contents

1. [Refactoring Strategy](#refactoring-strategy)
2. [Phase 1: Extract Server Services](#phase-1-extract-server-services)
3. [Phase 2: Create Helper Utilities](#phase-2-create-helper-utilities)
4. [Phase 3: Split Large Core Modules](#phase-3-split-large-core-modules)
5. [Phase 4: Frontend Component Refactoring](#phase-4-frontend-component-refactoring)
6. [Phase 5: Fix Import Structure](#phase-5-fix-import-structure)
7. [Testing Strategy](#testing-strategy)
8. [Risk Management](#risk-management)
9. [Success Metrics](#success-metrics)

---

## Refactoring Strategy

### Guiding Principles

1. **Incremental Changes** - Small, verifiable changes over big rewrites
2. **Test-Driven** - Write/update tests before refactoring
3. **Backwards Compatible** - Maintain existing APIs during transition
4. **One Phase at a Time** - Complete and verify each phase before starting next
5. **Continuous Integration** - Merge to main frequently, use feature flags if needed

### Priority Matrix

| Priority | Impact | Effort | Risk | Phases |
|----------|--------|--------|------|--------|
| **CRITICAL** | High | Medium | Low | Phase 1, 2 |
| **HIGH** | High | Medium | Medium | Phase 3, 4 |
| **MEDIUM** | Medium | Low | Low | Phase 5 |

### File Size Targets

- **Maximum file size:** 800 lines (excluding tests)
- **Target file size:** 200-400 lines
- **Maximum function size:** 80 lines
- **Target function size:** 20-50 lines

---

## Phase 1: Extract Server Services

**Duration:** 4-5 days
**Priority:** CRITICAL
**Risk:** Low

### Goals

- Split `server.py` (2091 lines) into focused service modules
- Reduce main server file to <300 lines
- Improve testability and maintainability
- Enable parallel development

### Step 1.1: Create Services Directory Structure

**Duration:** 30 minutes

```bash
mkdir -p app/server/services
touch app/server/services/__init__.py
touch app/server/services/websocket_manager.py
touch app/server/services/workflow_service.py
touch app/server/services/background_tasks.py
touch app/server/services/health_service.py
touch app/server/services/service_controller.py
```

**Deliverable:** Empty service module files

---

### Step 1.2: Extract WebSocket Manager

**Duration:** 2-3 hours

**Current Location:** `server.py` lines 124-154

**Target:** `services/websocket_manager.py`

**Implementation:**

```python
# app/server/services/websocket_manager.py
"""WebSocket connection management for real-time updates"""

from fastapi import WebSocket
from typing import Set
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection from active set"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Send message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
```

**Update server.py:**

```python
# app/server/server.py
from services.websocket_manager import ConnectionManager

# Replace ConnectionManager class definition with import
manager = ConnectionManager()
```

**Tests:**

```python
# app/server/tests/test_websocket_manager.py
import pytest
from services.websocket_manager import ConnectionManager
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_connection_manager_connect():
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)

    assert mock_websocket in manager.active_connections
    assert manager.connection_count() == 1
    mock_websocket.accept.assert_called_once()

@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)
    manager.disconnect(mock_websocket)

    assert mock_websocket not in manager.active_connections
    assert manager.connection_count() == 0

@pytest.mark.asyncio
async def test_broadcast_to_all_connections():
    manager = ConnectionManager()
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    await manager.connect(mock_ws1)
    await manager.connect(mock_ws2)

    message = {"type": "update", "data": "test"}
    await manager.broadcast(message)

    mock_ws1.send_json.assert_called_once_with(message)
    mock_ws2.send_json.assert_called_once_with(message)
```

**Verification:**
- [ ] Unit tests pass
- [ ] WebSocket connections work in dev environment
- [ ] No regressions in existing functionality

---

### Step 1.3: Extract Workflow Service

**Duration:** 3-4 hours

**Current Location:** `server.py` lines 156-277, 327-373

**Target:** `services/workflow_service.py`

**Implementation:**

```python
# app/server/services/workflow_service.py
"""Service for workflow data operations"""

from typing import List, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

from core.data_models import Workflow, Route, WorkflowHistoryResponse
from core.workflow_history import get_workflow_history

logger = logging.getLogger(__name__)

class WorkflowService:
    """Handles workflow data fetching and processing"""

    def __init__(self, workflows_dir: str = "agents"):
        self.workflows_dir = Path(workflows_dir)

    def get_workflows(self) -> List[Workflow]:
        """
        Scan and return all workflows from the workflows directory

        Returns:
            List of Workflow objects with metadata
        """
        workflows = []

        if not self.workflows_dir.exists():
            logger.warning(f"Workflows directory not found: {self.workflows_dir}")
            return workflows

        for workflow_dir in self.workflows_dir.iterdir():
            if not workflow_dir.is_dir():
                continue

            try:
                workflow = self._parse_workflow_directory(workflow_dir)
                if workflow:
                    workflows.append(workflow)
            except Exception as e:
                logger.error(f"Error parsing workflow {workflow_dir.name}: {e}")

        # Sort by creation time, newest first
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        return workflows

    def _parse_workflow_directory(self, workflow_dir: Path) -> Optional[Workflow]:
        """Parse workflow directory and extract metadata"""
        state_file = workflow_dir / "adw_state.json"

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            state = json.load(f)

        return Workflow(
            id=workflow_dir.name,
            name=state.get('name', workflow_dir.name),
            status=state.get('status', 'unknown'),
            created_at=state.get('created_at', ''),
            updated_at=state.get('updated_at', ''),
            # ... additional fields
        )

    def get_routes(self) -> List[Route]:
        """
        Get all available API routes

        Returns:
            List of Route objects with metadata
        """
        routes = []
        # Implementation for route discovery
        # This would parse OpenAPI schema or introspect FastAPI app
        return routes

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> WorkflowHistoryResponse:
        """
        Get workflow history with filtering and pagination

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            status_filter: Filter by status (e.g., 'completed', 'failed')
            search_query: Search term for workflow names/descriptions

        Returns:
            WorkflowHistoryResponse with workflows and metadata
        """
        return get_workflow_history(
            limit=limit,
            offset=offset,
            status=status_filter,
            search=search_query
        )
```

**Update server.py:**

```python
# app/server/server.py
from services.workflow_service import WorkflowService

workflow_service = WorkflowService()

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
    result = workflow_service.get_history(
        limit=limit,
        offset=offset,
        status_filter=status,
        search_query=search
    )
    return result
```

**Tests:**

```python
# app/server/tests/test_workflow_service.py
import pytest
from pathlib import Path
from services.workflow_service import WorkflowService
import json
import tempfile

@pytest.fixture
def temp_workflows_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def workflow_service(temp_workflows_dir):
    return WorkflowService(workflows_dir=str(temp_workflows_dir))

def test_get_workflows_empty_directory(workflow_service):
    workflows = workflow_service.get_workflows()
    assert workflows == []

def test_get_workflows_with_data(workflow_service, temp_workflows_dir):
    # Create test workflow directory
    workflow_dir = temp_workflows_dir / "test-workflow-123"
    workflow_dir.mkdir()

    # Create state file
    state = {
        "name": "Test Workflow",
        "status": "completed",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T01:00:00Z"
    }
    with open(workflow_dir / "adw_state.json", 'w') as f:
        json.dump(state, f)

    workflows = workflow_service.get_workflows()

    assert len(workflows) == 1
    assert workflows[0].id == "test-workflow-123"
    assert workflows[0].name == "Test Workflow"
    assert workflows[0].status == "completed"

def test_get_workflows_ignores_invalid_directories(workflow_service, temp_workflows_dir):
    # Create valid workflow
    valid_dir = temp_workflows_dir / "valid-workflow"
    valid_dir.mkdir()
    with open(valid_dir / "adw_state.json", 'w') as f:
        json.dump({"name": "Valid", "status": "completed"}, f)

    # Create invalid directory (no state file)
    invalid_dir = temp_workflows_dir / "invalid-workflow"
    invalid_dir.mkdir()

    workflows = workflow_service.get_workflows()

    assert len(workflows) == 1
    assert workflows[0].id == "valid-workflow"
```

**Verification:**
- [ ] Unit tests pass
- [ ] Workflow listing works in UI
- [ ] History pagination works correctly

---

### Step 1.4: Extract Background Tasks

**Duration:** 2-3 hours

**Current Location:** `server.py` lines 279-408

**Target:** `services/background_tasks.py`

**Implementation:**

```python
# app/server/services/background_tasks.py
"""Background tasks for watching file changes and broadcasting updates"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from services.websocket_manager import ConnectionManager
from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manages background watching tasks"""

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
        self._tasks.append(asyncio.create_task(self.watch_workflows()))
        self._tasks.append(asyncio.create_task(self.watch_routes()))
        self._tasks.append(asyncio.create_task(self.watch_workflow_history()))
        logger.info("Background tasks started")

    async def stop_all(self) -> None:
        """Stop all background tasks"""
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Background tasks stopped")

    async def watch_workflows(self) -> None:
        """Watch workflow directory for changes and broadcast updates"""
        logger.info("Starting workflow watcher")
        previous_workflows = None

        while True:
            try:
                workflows = self.workflow_service.get_workflows()

                # Only broadcast if data changed
                if workflows != previous_workflows:
                    await self.websocket_manager.broadcast({
                        "type": "workflows_update",
                        "data": [w.dict() for w in workflows]
                    })
                    previous_workflows = workflows

                await asyncio.sleep(self.watch_interval)

            except asyncio.CancelledError:
                logger.info("Workflow watcher cancelled")
                break
            except Exception as e:
                logger.error(f"Error in workflow watcher: {e}")
                await asyncio.sleep(self.watch_interval)

    async def watch_routes(self) -> None:
        """Watch routes for changes and broadcast updates"""
        logger.info("Starting routes watcher")
        previous_routes = None

        while True:
            try:
                routes = self.workflow_service.get_routes()

                if routes != previous_routes:
                    await self.websocket_manager.broadcast({
                        "type": "routes_update",
                        "data": [r.dict() for r in routes]
                    })
                    previous_routes = routes

                await asyncio.sleep(self.watch_interval)

            except asyncio.CancelledError:
                logger.info("Routes watcher cancelled")
                break
            except Exception as e:
                logger.error(f"Error in routes watcher: {e}")
                await asyncio.sleep(self.watch_interval)

    async def watch_workflow_history(self) -> None:
        """Watch workflow history for changes and broadcast updates"""
        logger.info("Starting workflow history watcher")
        previous_history = None

        while True:
            try:
                history = self.workflow_service.get_history(limit=50)

                if history != previous_history:
                    await self.websocket_manager.broadcast({
                        "type": "workflow_history_update",
                        "data": history.dict()
                    })
                    previous_history = history

                await asyncio.sleep(self.watch_interval)

            except asyncio.CancelledError:
                logger.info("Workflow history watcher cancelled")
                break
            except Exception as e:
                logger.error(f"Error in workflow history watcher: {e}")
                await asyncio.sleep(self.watch_interval)
```

**Update server.py:**

```python
# app/server/server.py
from services.background_tasks import BackgroundTaskManager

task_manager = BackgroundTaskManager(
    websocket_manager=manager,
    workflow_service=workflow_service,
    watch_interval=2.0
)

@app.on_event("startup")
async def startup_event():
    await task_manager.start_all()

@app.on_event("shutdown")
async def shutdown_event():
    await task_manager.stop_all()
```

**Tests:**

```python
# app/server/tests/test_background_tasks.py
import pytest
import asyncio
from services.background_tasks import BackgroundTaskManager
from services.websocket_manager import ConnectionManager
from services.workflow_service import WorkflowService
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_websocket_manager():
    return MagicMock(spec=ConnectionManager)

@pytest.fixture
def mock_workflow_service():
    return MagicMock(spec=WorkflowService)

@pytest.mark.asyncio
async def test_start_all_tasks(mock_websocket_manager, mock_workflow_service):
    manager = BackgroundTaskManager(
        websocket_manager=mock_websocket_manager,
        workflow_service=mock_workflow_service,
        watch_interval=0.1
    )

    await manager.start_all()
    assert len(manager._tasks) == 3

    await manager.stop_all()
    assert len(manager._tasks) == 0

@pytest.mark.asyncio
async def test_workflow_watcher_broadcasts_changes(mock_websocket_manager, mock_workflow_service):
    workflows = [MagicMock(dict=lambda: {"id": "test"})]
    mock_workflow_service.get_workflows.return_value = workflows
    mock_websocket_manager.broadcast = AsyncMock()

    manager = BackgroundTaskManager(
        websocket_manager=mock_websocket_manager,
        workflow_service=mock_workflow_service,
        watch_interval=0.1
    )

    # Run watcher for short time
    task = asyncio.create_task(manager.watch_workflows())
    await asyncio.sleep(0.2)
    task.cancel()

    # Should have broadcasted at least once
    assert mock_websocket_manager.broadcast.called
```

**Verification:**
- [ ] Background tasks start on server startup
- [ ] WebSocket clients receive updates
- [ ] No memory leaks from running tasks

---

### Step 1.5: Extract Health Service

**Duration:** 4-5 hours

**Current Location:** `server.py` lines 610-843

**Target:** `services/health_service.py`

**Implementation:**

```python
# app/server/services/health_service.py
"""System health checking service"""

import subprocess
import httpx
import sqlite3
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(str, Enum):
    """Service health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    """Health status of a single service"""
    name: str
    status: ServiceStatus
    message: str
    details: Optional[Dict] = None

class HealthService:
    """Performs health checks on various system services"""

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
        """
        Check health of all services

        Returns:
            Dictionary mapping service name to ServiceHealth
        """
        return {
            "backend": self.check_backend(),
            "database": self.check_database(),
            "webhook": await self.check_webhook(),
            "cloudflare": self.check_cloudflare_tunnel(),
            "github_webhook": await self.check_github_webhook(),
            "frontend": await self.check_frontend()
        }

    def check_backend(self) -> ServiceHealth:
        """Check backend server health (always healthy if this runs)"""
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

            # Check if critical tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('workflows', 'workflow_history')
            """)
            tables = cursor.fetchall()
            conn.close()

            if len(tables) >= 2:
                return ServiceHealth(
                    name="Database",
                    status=ServiceStatus.HEALTHY,
                    message="Database accessible with all tables",
                    details={"tables": [t[0] for t in tables]}
                )
            else:
                return ServiceHealth(
                    name="Database",
                    status=ServiceStatus.DEGRADED,
                    message="Database accessible but missing tables",
                    details={"tables": [t[0] for t in tables]}
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ServiceHealth(
                name="Database",
                status=ServiceStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )

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

    async def check_github_webhook(self) -> ServiceHealth:
        """Check GitHub webhook configuration"""
        # This would check GitHub API for webhook status
        # Implementation depends on GitHub API access
        return ServiceHealth(
            name="GitHub Webhook",
            status=ServiceStatus.UNKNOWN,
            message="Check not implemented"
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

    def get_overall_status(self, services: Dict[str, ServiceHealth]) -> ServiceStatus:
        """
        Determine overall system status from individual service statuses

        Returns:
            HEALTHY: All services healthy
            DEGRADED: At least one service degraded/unknown
            UNHEALTHY: At least one service unhealthy
        """
        statuses = [s.status for s in services.values()]

        if ServiceStatus.UNHEALTHY in statuses:
            return ServiceStatus.UNHEALTHY
        elif ServiceStatus.DEGRADED in statuses or ServiceStatus.UNKNOWN in statuses:
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.HEALTHY
```

**Update server.py:**

```python
# app/server/server.py
from services.health_service import HealthService

health_service = HealthService(
    db_path="db/database.db",
    webhook_url="http://localhost:8001/health",
    cloudflare_tunnel_name=os.getenv("CLOUDFLARE_TUNNEL_NAME"),
    frontend_url="http://localhost:5173"
)

@app.get("/api/system-status")
async def get_system_status():
    services = await health_service.check_all()
    overall_status = health_service.get_overall_status(services)

    return {
        "overall_status": overall_status,
        "services": {name: health.dict() for name, health in services.items()}
    }
```

**Tests:**

```python
# app/server/tests/test_health_service.py
import pytest
from services.health_service import HealthService, ServiceStatus
import tempfile
import sqlite3

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE workflows (id TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE workflow_history (id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

    yield db_path

@pytest.fixture
def health_service(temp_db):
    return HealthService(db_path=temp_db)

def test_check_backend_always_healthy(health_service):
    result = health_service.check_backend()
    assert result.status == ServiceStatus.HEALTHY

def test_check_database_healthy(health_service):
    result = health_service.check_database()
    assert result.status == ServiceStatus.HEALTHY
    assert "workflows" in result.details["tables"]
    assert "workflow_history" in result.details["tables"]

def test_check_database_unhealthy_missing_file():
    service = HealthService(db_path="/nonexistent/database.db")
    result = service.check_database()
    assert result.status == ServiceStatus.UNHEALTHY

@pytest.mark.asyncio
async def test_check_all_services(health_service):
    services = await health_service.check_all()

    assert "backend" in services
    assert "database" in services
    assert "webhook" in services
    assert "cloudflare" in services
    assert "github_webhook" in services
    assert "frontend" in services

def test_get_overall_status_all_healthy(health_service):
    from services.health_service import ServiceHealth

    services = {
        "svc1": ServiceHealth("svc1", ServiceStatus.HEALTHY, "ok"),
        "svc2": ServiceHealth("svc2", ServiceStatus.HEALTHY, "ok")
    }

    status = health_service.get_overall_status(services)
    assert status == ServiceStatus.HEALTHY

def test_get_overall_status_one_unhealthy(health_service):
    from services.health_service import ServiceHealth

    services = {
        "svc1": ServiceHealth("svc1", ServiceStatus.HEALTHY, "ok"),
        "svc2": ServiceHealth("svc2", ServiceStatus.UNHEALTHY, "error")
    }

    status = health_service.get_overall_status(services)
    assert status == ServiceStatus.UNHEALTHY
```

**Verification:**
- [ ] Health endpoint returns correct status
- [ ] Individual service checks work
- [ ] Overall status calculation correct

---

### Step 1.6: Integration and Testing

**Duration:** 1 day

**Tasks:**
1. Update all imports in `server.py`
2. Remove extracted code from `server.py`
3. Run full integration test suite
4. Test WebSocket connections
5. Test background tasks
6. Test health endpoints
7. Performance testing

**Verification Checklist:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] WebSocket real-time updates work
- [ ] Background tasks don't leak memory
- [ ] Health checks return correct statuses
- [ ] API response times unchanged
- [ ] No regressions in UI

**Rollback Plan:**
If issues are found, revert changes:
```bash
git revert <commit-hash>
```

---

## Phase 2: Create Helper Utilities

**Duration:** 2-3 days
**Priority:** CRITICAL
**Risk:** Low

### Goals

- Eliminate ~30% code duplication
- Create reusable utility modules
- Standardize error handling patterns
- Improve code consistency

### Step 2.1: Create DatabaseManager

**Duration:** 4-6 hours

**Target:** `app/server/core/database.py`

**Implementation:** See [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md#1-database-connection-pattern)

**Files to Update:**
1. `app/server/core/workflow_history.py`
2. `app/server/core/file_processor.py`
3. `app/server/core/sql_processor.py`
4. `app/server/core/insights.py`
5. `app/server/core/adw_lock.py`
6. `app/server/server.py`

**Migration Example:**

```python
# Before:
conn = sqlite3.connect("db/database.db")
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM workflows")
    results = cursor.fetchall()
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
finally:
    conn.close()

# After:
from core.database import DatabaseManager

db = DatabaseManager()
with db.get_connection(sqlite3.Row) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflows")
    results = cursor.fetchall()
```

**Tests:**

```python
# app/server/tests/test_database.py
import pytest
import sqlite3
import tempfile
from core.database import DatabaseManager

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        return f.name

def test_database_manager_connection(temp_db):
    db = DatabaseManager(db_path=temp_db)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test (id) VALUES (1)")

    # Verify data persisted
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        assert cursor.fetchone()[0] == 1

def test_database_manager_rollback_on_error(temp_db):
    db = DatabaseManager(db_path=temp_db)

    # Create table
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

    # Try to insert with error
    with pytest.raises(sqlite3.IntegrityError):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO test (id) VALUES (1)")
            cursor.execute("INSERT INTO test (id) VALUES (1)")  # Duplicate

    # Verify rollback - no data inserted
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test")
        assert cursor.fetchone()[0] == 0
```

**Verification:**
- [ ] All updated files use DatabaseManager
- [ ] Tests pass
- [ ] No database connection leaks
- [ ] Rollback works on errors

---

### Step 2.2: Create LLMClient

**Duration:** 4-6 hours

**Target:** `app/server/core/llm_client.py`

**Implementation:** See [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md#2-llm-api-call-pattern)

**Files to Update:**
1. `app/server/core/nl_processor.py`
2. `app/server/core/llm_processor.py`
3. `app/server/core/api_quota.py`

**Tests:**

```python
# app/server/tests/test_llm_client.py
import pytest
from core.llm_client import LLMClient
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_anthropic_client():
    with patch('core.llm_client.Anthropic') as mock:
        yield mock

def test_llm_client_initialization(mock_anthropic_client):
    client = LLMClient(provider="anthropic")
    assert client.provider == "anthropic"

def test_generate_text(mock_anthropic_client):
    # Setup mock
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response")]
    mock_anthropic_client.return_value.messages.create.return_value = mock_response

    client = LLMClient(provider="anthropic")
    result = client.generate_text(prompt="Test prompt")

    assert result == "Test response"

def test_generate_json(mock_anthropic_client):
    # Setup mock
    mock_response = Mock()
    mock_response.content = [Mock(text='{"key": "value"}')]
    mock_anthropic_client.return_value.messages.create.return_value = mock_response

    client = LLMClient(provider="anthropic")
    result = client.generate_json(prompt="Test prompt")

    assert result == {"key": "value"}

def test_clean_markdown():
    client = LLMClient()

    # Test JSON code block
    assert client._clean_markdown("```json\n{}\n```") == "{}"

    # Test generic code block
    assert client._clean_markdown("```\ntext\n```") == "text"

    # Test no markdown
    assert client._clean_markdown("plain text") == "plain text"
```

**Verification:**
- [ ] All updated files use LLMClient
- [ ] Tests pass
- [ ] API calls work correctly
- [ ] JSON parsing works

---

### Step 2.3: Create ProcessRunner

**Duration:** 3-4 hours

**Target:** `app/server/core/process_utils.py`

**Implementation:** See [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md#3-subprocess-execution-pattern)

**Files to Update:**
1. `app/server/server.py` (multiple locations)
2. `adws/adw_triggers/trigger_webhook.py`
3. `adws/adw_modules/workflow_ops.py`

**Tests:**

```python
# app/server/tests/test_process_utils.py
import pytest
from core.process_utils import ProcessRunner, ProcessResult

def test_run_successful_command():
    runner = ProcessRunner()
    result = runner.run(["echo", "test"])

    assert result.success
    assert result.returncode == 0
    assert "test" in result.stdout

def test_run_failed_command():
    runner = ProcessRunner()
    result = runner.run(["ls", "/nonexistent/path"])

    assert not result.success
    assert result.returncode != 0

def test_run_with_timeout():
    runner = ProcessRunner()
    result = runner.run(["sleep", "10"], timeout=1)

    assert not result.success
    assert result.timed_out

def test_run_background():
    runner = ProcessRunner()
    process = runner.run_background(["sleep", "1"])

    assert process.pid > 0
    process.wait()  # Clean up

def test_run_with_retry():
    runner = ProcessRunner()
    result = runner.run_with_retry(
        ["ls", "/tmp"],
        max_retries=3,
        timeout=5
    )

    assert result.success
```

**Verification:**
- [ ] All updated files use ProcessRunner
- [ ] Tests pass
- [ ] Timeout handling works
- [ ] Background processes work

---

### Step 2.4: Create Frontend Formatters

**Duration:** 2-3 hours

**Target:** `app/client/src/utils/formatters.ts`

**Implementation:** See [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md#4-frontend-formatting-functions)

**Files to Update:**
1. `WorkflowHistoryCard.tsx`
2. `SimilarWorkflowsComparison.tsx`
3. `RoutesView.tsx`
4. `TokenBreakdownChart.tsx`
5. `CostBreakdownChart.tsx`

**Tests:**

```typescript
// app/client/src/utils/__tests__/formatters.test.ts
import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatDuration,
  formatCost,
  formatNumber,
  formatBytes,
  formatPercentage,
  formatTokenCount
} from '../formatters';

describe('formatters', () => {
  describe('formatDate', () => {
    it('formats date correctly', () => {
      const date = new Date('2025-01-15T10:30:00Z');
      const result = formatDate(date);
      expect(result).toContain('Jan');
      expect(result).toContain('15');
    });
  });

  describe('formatDuration', () => {
    it('formats seconds', () => {
      expect(formatDuration(45)).toBe('45s');
    });

    it('formats minutes and seconds', () => {
      expect(formatDuration(125)).toBe('2m 5s');
    });

    it('formats hours and minutes', () => {
      expect(formatDuration(3665)).toBe('1h 1m');
    });
  });

  describe('formatCost', () => {
    it('formats cost with 4 decimal places', () => {
      expect(formatCost(1.23456)).toBe('$1.2346');
    });
  });

  describe('formatNumber', () => {
    it('formats large numbers with commas', () => {
      expect(formatNumber(1234567)).toBe('1,234,567');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes', () => {
      expect(formatBytes(100)).toBe('100.00 B');
    });

    it('formats kilobytes', () => {
      expect(formatBytes(2048)).toBe('2.00 KB');
    });

    it('formats megabytes', () => {
      expect(formatBytes(5242880)).toBe('5.00 MB');
    });
  });

  describe('formatPercentage', () => {
    it('formats percentage with default decimals', () => {
      expect(formatPercentage(75.5)).toBe('75.5%');
    });

    it('formats percentage with custom decimals', () => {
      expect(formatPercentage(75.567, 2)).toBe('75.57%');
    });
  });

  describe('formatTokenCount', () => {
    it('formats small token counts', () => {
      expect(formatTokenCount(500)).toBe('500');
    });

    it('formats thousands with K suffix', () => {
      expect(formatTokenCount(5000)).toBe('5.0K');
    });

    it('formats millions with M suffix', () => {
      expect(formatTokenCount(2500000)).toBe('2.50M');
    });
  });
});
```

**Verification:**
- [ ] All components use formatters
- [ ] Tests pass
- [ ] Formatting is consistent across UI
- [ ] No visual regressions

---

## Phase 3: Split Large Core Modules

**Duration:** 4-5 days
**Priority:** HIGH
**Risk:** Medium

### Goals

- Split `workflow_history.py` (1,276 lines) into focused modules
- Split `workflow_analytics.py` (904 lines) into scoring modules
- Improve module cohesion
- Maintain backwards compatibility

### Step 3.1: Split workflow_history.py

**Duration:** 2-3 days

**Target Structure:**
```
app/server/core/workflow_history/
├── __init__.py                  # Public API
├── database.py                  # DB operations
├── scanner.py                   # File system scanning
├── enrichment.py               # Cost data enrichment
├── analytics.py                # Analytics calculations
├── similarity.py               # Similarity detection
└── resync.py                   # Resync operations
```

**Step 3.1.1: Create Directory and __init__.py**

```python
# app/server/core/workflow_history/__init__.py
"""
Workflow history module - Public API

This module maintains backwards compatibility while using
internally refactored submodules.
"""

from .database import (
    init_db,
    insert_workflow,
    update_workflow,
    get_workflow_by_id,
    get_workflow_history
)

from .scanner import (
    scan_agents_directory,
    parse_workflow_file
)

from .enrichment import (
    load_cost_data,
    enrich_with_cost_data
)

from .analytics import (
    calculate_phase_metrics,
    get_history_analytics
)

from .similarity import (
    calculate_workflow_similarity
)

from .resync import (
    resync_workflow_cost,
    resync_all_completed_workflows
)

# Main function that orchestrates everything
from .sync import sync_workflow_history

__all__ = [
    'init_db',
    'insert_workflow',
    'update_workflow',
    'get_workflow_by_id',
    'get_workflow_history',
    'scan_agents_directory',
    'parse_workflow_file',
    'load_cost_data',
    'enrich_with_cost_data',
    'calculate_phase_metrics',
    'get_history_analytics',
    'calculate_workflow_similarity',
    'resync_workflow_cost',
    'resync_all_completed_workflows',
    'sync_workflow_history'
]
```

**Step 3.1.2: Extract database.py**

Extract lines 196-613 from original file:

```python
# app/server/core/workflow_history/database.py
"""Database operations for workflow history"""

import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from core.database import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(db_path="db/database.db")

def init_db() -> None:
    """Initialize workflow history database tables"""
    # Implementation...

def insert_workflow(workflow: Dict[str, Any]) -> bool:
    """Insert new workflow into database"""
    # Implementation...

def update_workflow(workflow_id: str, updates: Dict[str, Any]) -> bool:
    """Update existing workflow in database"""
    # Implementation...

def get_workflow_by_id(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Get workflow by ID"""
    # Implementation...

def get_workflow_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """Get workflow history with filtering and pagination"""
    # Implementation...
```

**Step 3.1.3: Extract scanner.py, enrichment.py, analytics.py, similarity.py, resync.py**

Similar pattern for each module - extract relevant functions and create focused modules.

**Step 3.1.4: Create sync.py**

```python
# app/server/core/workflow_history/sync.py
"""Main sync orchestration"""

import logging
from typing import Dict

from .scanner import scan_agents_directory
from .enrichment import enrich_with_cost_data
from .analytics import calculate_phase_metrics
from .similarity import calculate_workflow_similarity
from .database import insert_workflow, update_workflow

logger = logging.getLogger(__name__)

def sync_workflow_history(silent: bool = False) -> Dict[str, Any]:
    """
    Synchronize workflow history from file system to database

    This is the main orchestration function that:
    1. Scans agents directory for workflows
    2. Enriches with cost data
    3. Calculates analytics scores
    4. Calculates similarity scores
    5. Updates database

    Args:
        silent: If True, suppress log output

    Returns:
        Dictionary with sync statistics
    """
    if not silent:
        logger.info("Starting workflow history sync")

    # Phase 1: Scan
    workflows = scan_agents_directory()

    # Phase 2: Enrich
    workflows = enrich_with_cost_data(workflows)

    # Phase 3: Calculate scores
    for workflow in workflows:
        workflow['metrics'] = calculate_phase_metrics(workflow)

    # Phase 3E: Similarity
    workflows = calculate_workflow_similarity(workflows)

    # Phase 4: Update database
    stats = {'inserted': 0, 'updated': 0, 'failed': 0}

    for workflow in workflows:
        try:
            existing = get_workflow_by_id(workflow['id'])
            if existing:
                update_workflow(workflow['id'], workflow)
                stats['updated'] += 1
            else:
                insert_workflow(workflow)
                stats['inserted'] += 1
        except Exception as e:
            logger.error(f"Failed to sync workflow {workflow['id']}: {e}")
            stats['failed'] += 1

    if not silent:
        logger.info(f"Sync complete: {stats}")

    return stats
```

**Step 3.1.5: Update Imports**

Update all files that import from `workflow_history`:

```python
# Before:
from core.workflow_history import sync_workflow_history, get_workflow_history

# After: (Same - backwards compatible)
from core.workflow_history import sync_workflow_history, get_workflow_history
```

**Tests:**

```python
# app/server/tests/test_workflow_history_integration.py
"""Integration tests for workflow_history module"""

import pytest
from core.workflow_history import (
    init_db,
    sync_workflow_history,
    get_workflow_history
)

def test_full_sync_workflow():
    """Test complete workflow sync process"""
    init_db()

    result = sync_workflow_history(silent=True)

    assert 'inserted' in result
    assert 'updated' in result
    assert 'failed' in result

def test_get_workflow_history_pagination():
    """Test pagination of workflow history"""
    result = get_workflow_history(limit=10, offset=0)

    assert 'workflows' in result
    assert 'total' in result
    assert len(result['workflows']) <= 10
```

**Verification:**
- [ ] All imports still work
- [ ] Tests pass
- [ ] Sync functionality unchanged
- [ ] Performance unchanged

---

### Step 3.2: Split workflow_analytics.py

**Duration:** 2 days

**Target Structure:**
```
app/server/core/workflow_analytics/
├── __init__.py
├── temporal.py
├── complexity.py
├── scoring/
│   ├── __init__.py
│   ├── base.py
│   ├── clarity_score.py
│   ├── cost_efficiency_score.py
│   ├── performance_score.py
│   └── quality_score.py
├── similarity.py
├── anomalies.py
└── recommendations.py
```

Similar process as workflow_history splitting.

**Verification:**
- [ ] All imports still work
- [ ] Tests pass
- [ ] Scoring unchanged
- [ ] Performance unchanged

---

## Phase 4: Frontend Component Refactoring

**Duration:** 3-4 days
**Priority:** HIGH
**Risk:** Medium

### Goals

- Split `WorkflowHistoryCard.tsx` (793 lines) into section components
- Consolidate WebSocket hooks (reduce 260 lines to 80 lines)
- Extract custom hooks from components
- Improve component testability

### Step 4.1: Split WorkflowHistoryCard.tsx

**Duration:** 2 days

**Target Structure:**
```
app/client/src/components/workflow-history/
├── WorkflowHistoryCard.tsx (~150 lines)
├── CostEconomicsSection.tsx
├── TokenAnalysisSection.tsx
├── PerformanceAnalysisSection.tsx
├── ErrorAnalysisSection.tsx
├── ResourceUsageSection.tsx
├── WorkflowJourneySection.tsx
├── EfficiencyScoresSection.tsx
└── InsightsSection.tsx
```

**Step 4.1.1: Create Directory and Extract First Section**

```typescript
// app/client/src/components/workflow-history/CostEconomicsSection.tsx
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { CostBreakdownChart } from '@/components/charts/CostBreakdownChart';
import { formatCost } from '@/utils/formatters';
import { calculateBudgetDelta } from '@/utils/workflowHelpers';

interface CostEconomicsSectionProps {
  workflow: Workflow;
}

export function CostEconomicsSection({ workflow }: CostEconomicsSectionProps) {
  const budgetDelta = calculateBudgetDelta(workflow);

  return (
    <Card>
      <CardHeader>
        <h3>Cost Economics</h3>
      </CardHeader>
      <CardContent>
        {/* Budget comparison */}
        <div className="budget-comparison">
          <div>Actual Cost: {formatCost(workflow.total_cost)}</div>
          <div>Budget: {formatCost(workflow.budget)}</div>
          <div className={budgetDelta < 0 ? 'text-green-600' : 'text-red-600'}>
            {budgetDelta < 0 ? 'Under' : 'Over'} Budget: {formatCost(Math.abs(budgetDelta))}
          </div>
        </div>

        {/* Cost breakdown chart */}
        <CostBreakdownChart workflow={workflow} />

        {/* Per-step comparison */}
        {/* ... */}
      </CardContent>
    </Card>
  );
}
```

**Step 4.1.2: Update Main Component**

```typescript
// app/client/src/components/workflow-history/WorkflowHistoryCard.tsx
import { CostEconomicsSection } from './CostEconomicsSection';
import { TokenAnalysisSection } from './TokenAnalysisSection';
// ... other imports

interface WorkflowHistoryCardProps {
  workflow: Workflow;
}

export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  return (
    <Card>
      <CardHeader>
        {/* Main header */}
      </CardHeader>
      <CardContent>
        <CostEconomicsSection workflow={workflow} />
        <TokenAnalysisSection workflow={workflow} />
        <PerformanceAnalysisSection workflow={workflow} />
        <ErrorAnalysisSection workflow={workflow} />
        <ResourceUsageSection workflow={workflow} />
        <WorkflowJourneySection workflow={workflow} />
        <EfficiencyScoresSection workflow={workflow} />
        <InsightsSection workflow={workflow} />
      </CardContent>
    </Card>
  );
}
```

**Tests:**

```typescript
// app/client/src/components/workflow-history/__tests__/CostEconomicsSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostEconomicsSection } from '../CostEconomicsSection';

describe('CostEconomicsSection', () => {
  const mockWorkflow = {
    id: 'test-123',
    total_cost: 1.2345,
    budget: 2.0,
    // ... other fields
  };

  it('renders cost information', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    expect(screen.getByText(/Actual Cost/)).toBeInTheDocument();
    expect(screen.getByText(/\$1.2345/)).toBeInTheDocument();
  });

  it('shows under budget when cost is less than budget', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    expect(screen.getByText(/Under Budget/)).toBeInTheDocument();
  });

  it('shows over budget when cost exceeds budget', () => {
    const overBudgetWorkflow = { ...mockWorkflow, total_cost: 2.5 };
    render(<CostEconomicsSection workflow={overBudgetWorkflow} />);

    expect(screen.getByText(/Over Budget/)).toBeInTheDocument();
  });
});
```

**Repeat for all 8 sections**

**Verification:**
- [ ] All sections render correctly
- [ ] Tests pass for each section
- [ ] No visual regressions
- [ ] Component performance unchanged

---

### Step 4.2: Consolidate WebSocket Hooks

**Duration:** 1 day

See [REFACTORING_ANALYSIS.md](./REFACTORING_ANALYSIS.md#websocket-hook-duplication) for full implementation.

**Target:**
```typescript
// hooks/useGenericWebSocket.ts
export function useGenericWebSocket<T>({ ... }) { ... }

// hooks/useWorkflowsWebSocket.ts
export function useWorkflowsWebSocket() {
  return useGenericWebSocket<Workflow[]>({ ... });
}
```

**Tests:**

```typescript
// hooks/__tests__/useGenericWebSocket.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGenericWebSocket } from '../useGenericWebSocket';

describe('useGenericWebSocket', () => {
  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(() =>
      useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [],
        dataExtractor: (msg) => msg.data
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('falls back to polling when WebSocket fails', async () => {
    // Mock WebSocket failure
    vi.stubGlobal('WebSocket', function() {
      throw new Error('Connection failed');
    });

    const { result } = renderHook(() =>
      useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [{ id: '1' }],
        dataExtractor: (msg) => msg.data
      })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual([{ id: '1' }]);
    });
  });
});
```

**Verification:**
- [ ] Generic hook works for all use cases
- [ ] Tests pass
- [ ] WebSocket connections stable
- [ ] Fallback polling works

---

## Phase 5: Fix Import Structure

**Duration:** 1-2 days
**Priority:** MEDIUM
**Risk:** Low

### Goals

- Eliminate path manipulation in imports
- Create shared package for common types
- Establish proper dependency hierarchy

### Step 5.1: Create Shared Package

**Duration:** 4 hours

```bash
mkdir -p shared/models
mkdir -p shared/services
touch shared/__init__.py
touch shared/models/__init__.py
touch shared/services/__init__.py
```

**Move shared types:**

```python
# shared/models/github_issue.py
"""Shared GitHub issue model"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class GitHubIssue:
    """GitHub issue representation used by both server and ADWs"""
    number: int
    title: str
    body: str
    state: str
    author: str
    labels: list[str]
    created_at: str
    updated_at: str
    url: str

# shared/models/complexity.py
"""Shared complexity types"""

from enum import Enum

class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
```

**Update imports:**

```python
# app/server/server.py
# BEFORE:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue

# AFTER:
from shared.models.github_issue import GitHubIssue
```

```python
# adws/adw_modules/workflow_ops.py
# BEFORE:
from adw_modules.data_types import GitHubIssue

# AFTER:
from shared.models.github_issue import GitHubIssue
```

**Verification:**
- [ ] No path manipulation remaining
- [ ] All imports resolve correctly
- [ ] Tests pass
- [ ] No circular dependencies

---

## Testing Strategy

### Unit Testing

**Coverage Target:** 80% for new modules

**Framework:** pytest (backend), vitest (frontend)

**Test Structure:**
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_websocket_manager.py
│   │   ├── test_workflow_service.py
│   │   ├── test_health_service.py
│   │   └── test_background_tasks.py
│   ├── core/
│   │   ├── test_database.py
│   │   ├── test_llm_client.py
│   │   └── test_process_utils.py
│   └── components/
│       └── workflow-history/
│           ├── CostEconomicsSection.test.tsx
│           └── ...
├── integration/
│   ├── test_workflow_history_integration.py
│   └── test_api_endpoints.py
└── e2e/
    └── test_workflow_lifecycle.py
```

### Integration Testing

**Test Scenarios:**
1. Complete workflow sync process
2. WebSocket real-time updates
3. Background task coordination
4. Health check aggregation
5. Database transactions

### End-to-End Testing

**Test Scenarios:**
1. User creates workflow via UI
2. Workflow processes and updates in real-time
3. History displays correctly
4. Analytics calculate properly

### Performance Testing

**Metrics to Track:**
- API response times (should not increase)
- Memory usage (should not increase)
- Database query performance
- WebSocket connection stability

**Tools:**
- `pytest-benchmark` for Python
- Chrome DevTools for frontend
- Load testing with `locust`

---

## Risk Management

### Identified Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking changes in API | High | Low | Maintain backwards compatibility, comprehensive tests |
| Database migration issues | High | Low | Test migrations in staging first |
| WebSocket connection instability | Medium | Medium | Fallback to polling, extensive testing |
| Performance degradation | Medium | Low | Benchmark before/after, optimize if needed |
| Team disruption | Medium | Medium | Clear communication, incremental changes |

### Rollback Strategy

**For each phase:**
1. Create feature branch
2. Make changes incrementally
3. Commit after each logical step
4. Test thoroughly before merging
5. If issues found post-merge:
   ```bash
   git revert <commit-range>
   git push origin main
   ```

### Contingency Plans

**If Phase 1 takes too long:**
- Complete Steps 1.1-1.3 first (WebSocket + Workflow Service)
- Defer health service and background tasks to Phase 1.5

**If tests reveal issues:**
- Fix issues before proceeding to next phase
- Add additional tests to prevent regression
- Consider breaking phase into smaller steps

**If performance degrades:**
- Profile to identify bottleneck
- Optimize specific module
- If optimization fails, revert and redesign

---

## Success Metrics

### Code Quality Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Largest file size | 2091 lines | <400 lines | Line count |
| Files >500 lines | 12 files | 0 files | File scan |
| Functions >100 lines | 14 functions | 0 functions | Code analysis |
| Code duplication | ~500 lines | ~50 lines | SonarQube |
| Test coverage | ~60% | >80% | pytest-cov |

### Performance Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| API response time (p95) | <200ms | <200ms | Load testing |
| Memory usage | Baseline | +0-10% | Memory profiler |
| WebSocket latency | Baseline | No change | Network monitor |
| Database query time | Baseline | No change | Query profiler |

### Development Velocity Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code review time | -30% | GitHub metrics |
| Time to understand module | -50% | Developer survey |
| Merge conflicts | -40% | Git metrics |
| Bug fix time | -25% | Issue tracking |

### Tracking Progress

**Weekly Reviews:**
- Check completed phases
- Review metrics
- Adjust plan if needed

**Documentation:**
- Update this document with progress
- Document any deviations from plan
- Record lessons learned

---

## Timeline Summary

| Phase | Duration | Dependencies | Status |
|-------|----------|--------------|--------|
| Phase 1: Server Services | 4-5 days | None | Pending |
| Phase 2: Helper Utilities | 2-3 days | None | Pending |
| Phase 3: Core Modules | 4-5 days | Phase 2 | Pending |
| Phase 4: Frontend | 3-4 days | Phase 2 | Pending |
| Phase 5: Import Structure | 1-2 days | Phase 1, 3 | Pending |
| **Total** | **15-20 days** | | **Not Started** |

**Parallel Work:**
- Phases 1 and 2 can run in parallel
- Phases 3 and 4 can run in parallel after Phase 2

**Optimal Schedule (with 2 developers):**
- Week 1: Phase 1 (Dev A) + Phase 2 (Dev B) = 5 days
- Week 2: Phase 3 (Dev A) + Phase 4 (Dev B) = 5 days
- Week 3: Phase 5 (Dev A + B) + Buffer = 5 days
- **Total: 15 days with 2 developers**

---

## Next Steps

1. **Review this plan** with team
2. **Approve refactoring** strategy
3. **Create feature branch** `refactor/phase-1-server-services`
4. **Begin Phase 1.1** - Create services directory
5. **Set up tracking** - Create project board for phases
6. **Schedule check-ins** - Daily standup updates on progress

---

## References

- [Refactoring Analysis](./REFACTORING_ANALYSIS.md)
- [Architecture Guide](../../architecture/README.md)
- [Testing Strategy](../../testing/README.md)
- [Python Best Practices](https://peps.python.org/pep-0008/)
- [React Testing Best Practices](https://react.dev/learn/testing)

---

**Document Status:** Complete
**Last Updated:** 2025-11-17
**Owner:** Development Team
**Next Review:** After Phase 1 completion
