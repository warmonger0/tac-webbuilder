### Workflow 4.2: Implement Backend and Database Health Checks
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/server/services/health_service.py`
- `app/server/server.py` (database check logic)

**Output Files:**
- `app/server/services/health_service.py` (modified)

**Tasks:**
1. Implement `check_backend()` method
2. Implement `check_database()` method
3. Add database table existence checks
4. Add error handling for database connection failures
5. Add logging for health check results

**Implementation:**
```python
def check_backend(self) -> ServiceHealth:
    """Backend is healthy if this code runs"""
    return ServiceHealth(
        name="Backend API",
        status=ServiceStatus.HEALTHY,
        message="Backend server is running"
    )

def check_database(self) -> ServiceHealth:
    """Check database connectivity and structure"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check critical tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('workflows', 'workflow_history')
        """)
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()

        if len(tables) >= 2:
            return ServiceHealth(
                name="Database",
                status=ServiceStatus.HEALTHY,
                message="Database accessible with all tables",
                details={"tables": tables}
            )
        else:
            return ServiceHealth(
                name="Database",
                status=ServiceStatus.DEGRADED,
                message="Database accessible but missing tables",
                details={"tables": tables}
            )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ServiceHealth(
            name="Database",
            status=ServiceStatus.UNHEALTHY,
            message=f"Database error: {str(e)}"
        )
```

**Acceptance Criteria:**
- [ ] Backend check always returns HEALTHY
- [ ] Database check verifies table existence
- [ ] Database check handles missing DB file
- [ ] Database check handles missing tables
- [ ] Errors logged appropriately

**Verification Command:**
```bash
python -c "
from app.server.services.health_service import HealthService
hs = HealthService()
print(hs.check_backend())
print(hs.check_database())
"
```

---
