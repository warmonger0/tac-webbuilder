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
