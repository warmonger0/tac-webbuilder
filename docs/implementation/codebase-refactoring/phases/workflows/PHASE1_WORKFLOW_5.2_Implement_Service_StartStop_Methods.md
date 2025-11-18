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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
