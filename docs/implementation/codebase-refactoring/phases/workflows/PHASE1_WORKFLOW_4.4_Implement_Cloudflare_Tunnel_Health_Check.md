### Workflow 4.4: Implement Cloudflare Tunnel Health Check
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/server/services/health_service.py`
- `app/server/server.py` (Cloudflare check logic)

**Output Files:**
- `app/server/services/health_service.py` (modified)

**Tasks:**
1. Implement `check_cloudflare_tunnel()` method
2. Add subprocess execution for cloudflared command
3. Add timeout handling
4. Add handling for missing cloudflared command
5. Add handling for unconfigured tunnel name

**Implementation:**
```python
def check_cloudflare_tunnel(self) -> ServiceHealth:
    """Check Cloudflare tunnel status"""
    if not self.cloudflare_tunnel_name:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message="Tunnel name not configured"
        )

    try:
        result = subprocess.run(
            ["cloudflared", "tunnel", "info", self.cloudflare_tunnel_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return ServiceHealth(
                name="Cloudflare Tunnel",
                status=ServiceStatus.HEALTHY,
                message="Tunnel is active"
            )
        else:
            return ServiceHealth(
                name="Cloudflare Tunnel",
                status=ServiceStatus.UNHEALTHY,
                message="Tunnel not active"
            )
    except subprocess.TimeoutExpired:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNHEALTHY,
            message="Tunnel check timeout"
        )
    except FileNotFoundError:
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message="cloudflared command not found"
        )
    except Exception as e:
        logger.error(f"Cloudflare tunnel check failed: {e}")
        return ServiceHealth(
            name="Cloudflare Tunnel",
            status=ServiceStatus.UNKNOWN,
            message=f"Check error: {str(e)}"
        )
```

**Acceptance Criteria:**
- [ ] Handles unconfigured tunnel name
- [ ] Handles missing cloudflared command
- [ ] Handles tunnel check timeout
- [ ] Returns appropriate status levels

**Verification Command:**
```bash
python -c "
from app.server.services.health_service import HealthService
hs = HealthService(cloudflare_tunnel_name='test-tunnel')
print(hs.check_cloudflare_tunnel())
"
```

---
