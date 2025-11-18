### Workflow 4.1: Create Health Service Module - Core Structure
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 610-843)

**Output Files:**
- `app/server/services/health_service.py` (new)

**Tasks:**
1. Create ServiceStatus enum
2. Create ServiceHealth dataclass
3. Create HealthService class skeleton
4. Add configuration for health check targets
5. Add `check_all()` method structure

**Code Structure:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus
    message: str
    details: Optional[Dict] = None

class HealthService:
    def __init__(
        self,
        db_path: str = "db/database.db",
        webhook_url: str = "http://localhost:8001/health",
        cloudflare_tunnel_name: Optional[str] = None,
        frontend_url: str = "http://localhost:5173"
    ):
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.cloudflare_tunnel_name = cloudflare_tunnel_name
        self.frontend_url = frontend_url

    async def check_all(self) -> Dict[str, ServiceHealth]:
        """Check health of all services"""
        return {
            "backend": self.check_backend(),
            "database": self.check_database(),
            "webhook": await self.check_webhook(),
            "cloudflare": self.check_cloudflare_tunnel(),
            "github_webhook": await self.check_github_webhook(),
            "frontend": await self.check_frontend()
        }
```

**Acceptance Criteria:**
- [ ] Module imports without errors
- [ ] Enums and dataclasses defined
- [ ] HealthService class instantiable
- [ ] check_all() method defined (stub implementations OK)

**Verification Command:**
```bash
python -c "from app.server.services.health_service import HealthService; hs = HealthService(); print('Module created successfully')"
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
