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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
