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
