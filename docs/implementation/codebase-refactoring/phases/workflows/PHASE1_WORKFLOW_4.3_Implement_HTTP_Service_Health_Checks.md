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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
