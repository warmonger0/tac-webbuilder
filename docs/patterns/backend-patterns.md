# Backend Patterns & Standards

This document defines the standard patterns for backend development in the tac-webbuilder project, established during Session 19's architectural improvements.

## Table of Contents

1. [Repository Pattern](#repository-pattern)
2. [Service Layer Pattern](#service-layer-pattern)
3. [State Management Pattern](#state-management-pattern)
4. [WebSocket Broadcast Pattern](#websocket-broadcast-pattern)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

---

## Repository Pattern

### Standard CRUD Methods

All repositories MUST follow this naming convention. See `docs/backend/repository-standards.md` for complete documentation.

**Quick Reference:**

```python
from typing import Optional, List
from app.server.database.connection import get_connection

class StandardRepository:
    """Base pattern for all repositories."""

    def create(self, item: ModelCreate) -> Model:
        """
        Create new record and return created object.

        Args:
            item: Pydantic model with creation data

        Returns:
            Created model with ID populated

        Example:
            >>> repo = UserRepository()
            >>> user = repo.create(UserCreate(name="Alice"))
            >>> user.id  # 123
        """
        pass

    def get_by_id(self, id: int) -> Optional[Model]:
        """
        Get single record by primary key.

        Args:
            id: Primary key value

        Returns:
            Model if found, None otherwise

        Example:
            >>> user = repo.get_by_id(123)
            >>> user.name  # "Alice"
        """
        pass

    def get_by_<field>(self, value: Any) -> Optional[Model]:
        """
        Get single record by unique field.

        Args:
            value: Field value to search for

        Returns:
            Model if found, None otherwise

        Example:
            >>> user = repo.get_by_email("alice@example.com")
        """
        pass

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Model]:
        """
        Get all records with pagination.

        Args:
            limit: Maximum records to return (default: 100)
            offset: Number of records to skip (default: 0)

        Returns:
            List of models

        Example:
            >>> users = repo.get_all(limit=10, offset=20)  # Page 3
        """
        pass

    def get_all_by_<field>(self, value: Any, limit: int = 100) -> List[Model]:
        """
        Get all records matching field value.

        Args:
            value: Field value to filter by
            limit: Maximum records to return

        Returns:
            List of matching models

        Example:
            >>> phases = repo.get_all_by_parent_issue("123", limit=50)
        """
        pass

    def update(self, id: int, data: ModelUpdate) -> Optional[Model]:
        """
        Update existing record.

        Args:
            id: Primary key of record to update
            data: Pydantic model with update data

        Returns:
            Updated model if found, None otherwise

        Example:
            >>> user = repo.update(123, UserUpdate(name="Alice Updated"))
        """
        pass

    def delete(self, id: int) -> bool:
        """
        Delete record by ID.

        Args:
            id: Primary key of record to delete

        Returns:
            True if deleted, False if not found

        Example:
            >>> success = repo.delete(123)
            >>> success  # True
        """
        pass

    def find_<custom_criteria>(self, ...) -> List[Model]:
        """
        Custom query with descriptive name.

        Use 'find_' prefix for complex queries that don't fit
        standard patterns.

        Examples:
            - find_ready_phases()
            - find_pending_with_priority()
            - find_expired_sessions()
        """
        pass
```

### Implementation Example

```python
# File: app/server/repositories/phase_queue_repository.py
from typing import Optional, List
from app.server.models.phase_queue import PhaseQueueItem, PhaseQueueCreate
from app.server.database.connection import get_connection

class PhaseQueueRepository:
    """Repository for phase_queue table."""

    def create(self, item: PhaseQueueCreate) -> PhaseQueueItem:
        """Create new phase queue item."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO phase_queue (issue_number, phase, status, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (item.issue_number, item.phase, item.status, item.metadata)
            )
            conn.commit()

            # Fetch created record
            queue_id = cursor.lastrowid
            return self.get_by_id(queue_id)

    def get_by_id(self, queue_id: int) -> Optional[PhaseQueueItem]:
        """Get phase queue item by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM phase_queue WHERE queue_id = ?",
                (queue_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

    def get_all_by_parent_issue(
        self,
        parent_issue: str,
        limit: int = 100
    ) -> List[PhaseQueueItem]:
        """Get all phases for parent issue."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM phase_queue
                WHERE parent_issue = ?
                ORDER BY created_at
                LIMIT ?
                """,
                (parent_issue, limit)
            )
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

    def _row_to_model(self, row: tuple) -> PhaseQueueItem:
        """Convert database row to Pydantic model."""
        return PhaseQueueItem(
            queue_id=row[0],
            issue_number=row[1],
            parent_issue=row[2],
            phase=row[3],
            status=row[4],
            priority=row[5],
            metadata=row[6],
            created_at=row[7],
            updated_at=row[8]
        )
```

### Benefits

1. **Predictability:** Developers know what methods exist
2. **Consistency:** Same names across all repositories
3. **Discoverability:** Easy to find methods (IDE autocomplete)
4. **Maintainability:** Clear contracts between layers
5. **Testability:** Standard methods easy to mock/test

---

## Service Layer Pattern

### Purpose

Services orchestrate business logic and coordinate between repositories, external APIs, and other services.

### Pattern

```python
# File: app/server/services/phase_queue_service.py
from app.server.repositories.phase_queue_repository import PhaseQueueRepository
from app.server.models.phase_queue import PhaseQueueCreate, PhaseQueueItem
from typing import List, Optional

class PhaseQueueService:
    """Business logic for phase queue management."""

    def __init__(self):
        self.repository = PhaseQueueRepository()

    def create_phase(self, item: PhaseQueueCreate) -> PhaseQueueItem:
        """
        Create new phase with validation and side effects.

        Args:
            item: Phase data to create

        Returns:
            Created phase

        Raises:
            ValueError: If validation fails
        """
        # 1. Validate business rules
        self._validate_phase_creation(item)

        # 2. Create in database
        phase = self.repository.create(item)

        # 3. Trigger side effects
        self._notify_phase_created(phase)

        # 4. Return result
        return phase

    def get_ready_phases(self) -> List[PhaseQueueItem]:
        """Get all phases ready for execution."""
        # Use custom repository method
        return self.repository.find_ready_phases()

    def transition_phase_status(
        self,
        queue_id: int,
        new_status: str
    ) -> Optional[PhaseQueueItem]:
        """
        Transition phase to new status with validation.

        Args:
            queue_id: Phase to update
            new_status: New status

        Returns:
            Updated phase if successful

        Raises:
            ValueError: If transition is invalid
        """
        # 1. Get current state
        phase = self.repository.get_by_id(queue_id)
        if not phase:
            return None

        # 2. Validate transition
        if not self._is_valid_transition(phase.status, new_status):
            raise ValueError(
                f"Invalid transition: {phase.status} → {new_status}"
            )

        # 3. Update status
        updated_phase = self.repository.update_status(queue_id, new_status)

        # 4. Broadcast change (WebSocket)
        self._broadcast_phase_update(updated_phase)

        return updated_phase

    def _validate_phase_creation(self, item: PhaseQueueCreate) -> None:
        """Validate business rules before creation."""
        # Example validations
        if not item.issue_number:
            raise ValueError("Issue number required")

        if item.phase not in ['plan', 'validate', 'build', 'test']:
            raise ValueError(f"Invalid phase: {item.phase}")

    def _is_valid_transition(
        self,
        current_status: str,
        new_status: str
    ) -> bool:
        """Validate status transitions."""
        valid_transitions = {
            'ready': ['in_progress', 'failed'],
            'in_progress': ['complete', 'failed'],
            'complete': [],  # Terminal
            'failed': ['ready'],  # Can retry
        }

        return new_status in valid_transitions.get(current_status, [])

    def _notify_phase_created(self, phase: PhaseQueueItem) -> None:
        """Send notifications about new phase."""
        # Could send to:
        # - WebSocket clients
        # - Webhook endpoints
        # - Logging systems
        pass

    def _broadcast_phase_update(self, phase: PhaseQueueItem) -> None:
        """Broadcast phase update via WebSocket."""
        from app.server.routes.websocket_routes import broadcast_phase_update
        broadcast_phase_update(phase)
```

### Responsibilities

**Services handle:**
- ✅ Business logic and validation
- ✅ Coordinating between repositories
- ✅ Transaction management
- ✅ Side effects (notifications, webhooks)
- ✅ Complex queries spanning multiple tables

**Services do NOT:**
- ❌ Direct database access (use repositories)
- ❌ Request/response handling (use routes)
- ❌ Data transformation for API (use routes)

---

## State Management Pattern

### Single Source of Truth (SSOT)

**Principle:** The database is the authoritative source for all ADW state.

**Implementation:**

```python
# All state flows through phase_queue table
class ADWStateManager:
    """Manages ADW state transitions (SSOT pattern)."""

    def __init__(self):
        self.repo = PhaseQueueRepository()

    def get_current_state(self, queue_id: int) -> Optional[str]:
        """
        Get current state from SSOT (phase_queue table).

        Args:
            queue_id: Phase queue ID

        Returns:
            Current status or None
        """
        phase = self.repo.get_by_id(queue_id)
        return phase.status if phase else None

    def update_state(
        self,
        queue_id: int,
        new_status: str,
        metadata: dict = None
    ) -> bool:
        """
        Update state in SSOT with validation.

        Args:
            queue_id: Phase to update
            new_status: New status
            metadata: Optional metadata to update

        Returns:
            Success

        Raises:
            ValueError: If transition invalid
        """
        # 1. Read current state from SSOT
        current = self.get_current_state(queue_id)
        if not current:
            raise ValueError(f"Phase {queue_id} not found")

        # 2. Validate transition
        if not self._validate_transition(current, new_status):
            raise ValueError(f"Invalid transition: {current} → {new_status}")

        # 3. Update SSOT (atomic operation)
        success = self.repo.update_status(queue_id, new_status, metadata)

        # 4. Broadcast change if successful
        if success:
            self._broadcast_state_change(queue_id, new_status)

        return success

    def _validate_transition(
        self,
        current: str,
        new: str
    ) -> bool:
        """Validate state transition is allowed."""
        # Same validation as service layer
        pass

    def _broadcast_state_change(
        self,
        queue_id: int,
        new_status: str
    ) -> None:
        """Broadcast state change to all listeners."""
        # WebSocket, webhooks, etc.
        pass
```

### Idempotent Operations

**Principle:** Operations should be safe to retry without side effects.

**Implementation:**

```python
def execute_phase_idempotent(queue_id: int, phase: str) -> None:
    """
    Execute phase in idempotent manner.

    Can be called multiple times safely - will skip if already complete.

    Args:
        queue_id: Phase to execute
        phase: Phase name
    """
    state_manager = ADWStateManager()

    # 1. Check current state
    current_status = state_manager.get_current_state(queue_id)

    # 2. Skip if already complete (idempotent)
    if current_status == 'complete':
        logger.info(f"Phase {queue_id} already complete, skipping")
        return

    # 3. Skip if already in progress (avoid duplicate execution)
    if current_status == 'in_progress':
        logger.warning(f"Phase {queue_id} already in progress")
        return

    try:
        # 4. Mark in progress (atomic)
        state_manager.update_state(queue_id, 'in_progress')

        # 5. Execute phase work
        result = execute_phase_work(phase)

        # 6. Mark complete (atomic)
        state_manager.update_state(
            queue_id,
            'complete',
            metadata={'result': result}
        )

    except Exception as e:
        # 7. Mark failed (atomic)
        state_manager.update_state(
            queue_id,
            'failed',
            metadata={'error': str(e)}
        )
        raise

# Safe to call multiple times:
execute_phase_idempotent(123, 'test')  # Executes
execute_phase_idempotent(123, 'test')  # Skips (already complete)
```

### State Validation Middleware

**Pattern:** Validate all state changes before persisting.

```python
# File: app/server/middleware/state_validation.py
from typing import Optional

def validate_phase_transition(
    current_status: str,
    new_status: str
) -> bool:
    """
    Validate phase status transition is legal.

    Args:
        current_status: Current status
        new_status: Proposed new status

    Returns:
        True if transition allowed

    Example:
        >>> validate_phase_transition('ready', 'in_progress')
        True
        >>> validate_phase_transition('complete', 'in_progress')
        False
    """
    valid_transitions = {
        'ready': ['in_progress', 'failed'],
        'in_progress': ['complete', 'failed'],
        'complete': [],  # Terminal state
        'failed': ['ready'],  # Can retry
    }

    allowed = valid_transitions.get(current_status, [])
    return new_status in allowed

# Use in repository
class PhaseQueueRepository:
    def update_status(
        self,
        queue_id: int,
        new_status: str
    ) -> bool:
        """Update status with validation."""
        # 1. Get current status
        phase = self.get_by_id(queue_id)
        if not phase:
            return False

        # 2. Validate transition
        if not validate_phase_transition(phase.status, new_status):
            raise ValueError(
                f"Invalid transition: {phase.status} → {new_status}"
            )

        # 3. Perform update
        # ... database update ...

        return True
```

---

## WebSocket Broadcast Pattern

### Purpose

Notify all connected clients when state changes, enabling real-time updates without polling.

### Pattern

```python
# File: app/server/routes/websocket_routes.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import List
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Dict to send as JSON

        Note: Automatically removes disconnected clients
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Client disconnected, mark for removal
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time status updates.

    Clients connect and receive broadcasts when state changes.
    """
    await manager.connect(websocket)

    try:
        # Keep connection alive
        while True:
            # Receive (keeps connection active)
            data = await websocket.receive_text()

            # Could handle client messages here
            # For now, just keep alive

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Broadcast functions (called from services)
async def broadcast_workflow_update(workflow_data: dict):
    """Broadcast workflow status update."""
    await manager.broadcast({
        'type': 'workflow_update',
        'timestamp': datetime.utcnow().isoformat(),
        'data': workflow_data
    })

async def broadcast_phase_update(phase_data: dict):
    """Broadcast phase status update."""
    await manager.broadcast({
        'type': 'phase_update',
        'timestamp': datetime.utcnow().isoformat(),
        'data': phase_data
    })

async def broadcast_queue_update(queue_data: dict):
    """Broadcast queue update."""
    await manager.broadcast({
        'type': 'queue_update',
        'timestamp': datetime.utcnow().isoformat(),
        'data': queue_data
    })
```

### Usage in Services

```python
# File: app/server/services/phase_queue_service.py
import asyncio
from app.server.routes.websocket_routes import broadcast_phase_update

class PhaseQueueService:
    def transition_phase_status(self, queue_id: int, new_status: str):
        """Transition phase and broadcast update."""
        # 1. Update in database
        phase = self.repository.update_status(queue_id, new_status)

        # 2. Broadcast to WebSocket clients
        if phase:
            asyncio.create_task(broadcast_phase_update({
                'queue_id': phase.queue_id,
                'issue_number': phase.issue_number,
                'phase': phase.phase,
                'status': phase.status,
                'updated_at': phase.updated_at.isoformat()
            }))

        return phase
```

### When to Broadcast

Broadcast when:
- ✅ Phase status changes (ready → in_progress → complete)
- ✅ New workflow starts
- ✅ ADW status changes
- ✅ Queue is updated
- ✅ Important events occur

Don't broadcast:
- ❌ On every database write
- ❌ For high-frequency updates (>1/second)
- ❌ For non-state-changing operations

---

## Error Handling

### Pattern: Consistent Error Responses

```python
# File: app/server/routes/queue_routes.py
from fastapi import HTTPException
from app.server.services.phase_queue_service import PhaseQueueService

@router.post("/phases", response_model=PhaseQueueItem)
async def create_phase(item: PhaseQueueCreate):
    """Create new phase."""
    try:
        service = PhaseQueueService()
        return service.create_phase(item)

    except ValueError as e:
        # Business logic error (400)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected error (500)
        logger.error(f"Failed to create phase: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

### Pattern: Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

class PhaseQueueService:
    def create_phase(self, item: PhaseQueueCreate) -> PhaseQueueItem:
        """Create phase with structured logging."""
        logger.info(
            f"Creating phase",
            extra={
                'issue_number': item.issue_number,
                'phase': item.phase,
                'status': item.status
            }
        )

        try:
            phase = self.repository.create(item)

            logger.info(
                f"Phase created",
                extra={
                    'queue_id': phase.queue_id,
                    'issue_number': phase.issue_number
                }
            )

            return phase

        except Exception as e:
            logger.error(
                f"Failed to create phase",
                extra={
                    'issue_number': item.issue_number,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
```

---

## Best Practices

### DO ✅

**Repository Layer:**
- ✅ Follow standard CRUD naming
- ✅ Return Pydantic models, not raw tuples
- ✅ Use type hints on all methods
- ✅ Include docstrings with examples
- ✅ Add pagination to get_all methods

**Service Layer:**
- ✅ Validate business rules
- ✅ Coordinate between repositories
- ✅ Handle transactions
- ✅ Trigger side effects (WebSocket, webhooks)
- ✅ Log important operations

**State Management:**
- ✅ Use phase_queue as Single Source of Truth
- ✅ Validate all state transitions
- ✅ Make operations idempotent
- ✅ Use atomic updates
- ✅ Broadcast state changes

**WebSocket:**
- ✅ Broadcast only on state change
- ✅ Include timestamp in messages
- ✅ Handle disconnections gracefully
- ✅ Keep connections alive
- ✅ Use structured message format

### DON'T ❌

**Repository Layer:**
- ❌ Put business logic in repositories
- ❌ Return raw database tuples
- ❌ Use different naming conventions
- ❌ Make direct HTTP calls

**Service Layer:**
- ❌ Direct database access (use repositories)
- ❌ Handle HTTP request/response
- ❌ Skip validation
- ❌ Ignore errors silently

**State Management:**
- ❌ Have multiple sources of truth
- ❌ Skip state validation
- ❌ Make non-idempotent operations
- ❌ Race conditions on updates

**WebSocket:**
- ❌ Broadcast on every database write
- ❌ Send high-frequency updates (>1/sec)
- ❌ Forget to handle disconnections
- ❌ Block the event loop

---

## Migration Checklist

When updating backend code to these patterns:

**Repository:**
- [ ] Rename methods to standard CRUD names
- [ ] Add type hints to all methods
- [ ] Return Pydantic models (not tuples)
- [ ] Add pagination parameters
- [ ] Add docstrings with examples

**Service:**
- [ ] Move business logic from routes to services
- [ ] Add validation before database operations
- [ ] Use repositories (not direct DB access)
- [ ] Add structured logging
- [ ] Trigger WebSocket broadcasts

**State:**
- [ ] Use phase_queue as SSOT
- [ ] Add state validation
- [ ] Make operations idempotent
- [ ] Use atomic updates

**WebSocket:**
- [ ] Add broadcast calls to services
- [ ] Handle disconnections
- [ ] Use structured message format
- [ ] Test with multiple clients

---

## Examples in Codebase

**Repository Pattern:**
- `app/server/repositories/phase_queue_repository.py`
- `app/server/repositories/work_log_repository.py`

**Service Pattern:**
- `app/server/services/phase_queue_service.py`
- `app/server/services/phase_dependency_tracker.py`

**State Management:**
- `app/server/middleware/state_validation.py`
- `adws/adw_sdlc_complete_iso.py` (Lines 53-149)

**WebSocket:**
- `app/server/routes/websocket_routes.py`

---

## Additional Resources

- **Repository Standards (Complete Spec):** `docs/backend/repository-standards.md`
- **Frontend Patterns:** `docs/patterns/frontend-patterns.md`
- **Migration Guide:** `docs/guides/migration-guide-session-19.md`
- **WebSocket API:** `docs/api/websocket-api.md`
- **Architecture:** `docs/architecture/session-19-improvements.md`
