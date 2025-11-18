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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
