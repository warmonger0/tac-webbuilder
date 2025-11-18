### Workflow 5.1: Create Service Controller Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 845-1171 - service management routes)

**Output Files:**
- `app/server/services/service_controller.py` (new)

**Tasks:**
1. Create ServiceController class
2. Extract webhook service start/stop logic
3. Extract Cloudflare tunnel restart logic
4. Extract GitHub webhook redeliver logic
5. Add error handling and logging
6. Add service state tracking

**Class Structure:**
```python
class ServiceController:
    """Controls starting, stopping, and restarting external services"""

    def __init__(self):
        self.webhook_process: Optional[subprocess.Popen] = None
        self.cloudflare_process: Optional[subprocess.Popen] = None

    async def start_webhook_service(self) -> Dict[str, Any]:
        """Start webhook service"""

    async def stop_webhook_service(self) -> Dict[str, Any]:
        """Stop webhook service"""

    async def restart_cloudflare_tunnel(self) -> Dict[str, Any]:
        """Restart Cloudflare tunnel"""

    async def redeliver_github_webhook(self, issue_number: int) -> Dict[str, Any]:
        """Redeliver GitHub webhook for issue"""
```

**Acceptance Criteria:**
- [ ] ServiceController class created
- [ ] All methods have type hints and docstrings
- [ ] Process tracking implemented
- [ ] Error handling for failed operations

**Verification Command:**
```bash
python -c "from app.server.services.service_controller import ServiceController; sc = ServiceController(); print('Module created')"
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
