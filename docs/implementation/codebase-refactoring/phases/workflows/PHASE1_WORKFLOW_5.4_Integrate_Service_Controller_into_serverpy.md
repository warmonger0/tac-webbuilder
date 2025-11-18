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
