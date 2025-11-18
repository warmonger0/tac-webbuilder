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
