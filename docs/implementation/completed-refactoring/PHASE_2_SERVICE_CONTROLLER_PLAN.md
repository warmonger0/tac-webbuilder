# Phase 2: Service Controller Extraction Plan

**Date Created:** 2025-11-19
**Phase:** 2 of 5
**Status:** 📋 READY TO START
**Estimated Effort:** 3-4 hours
**Target Reduction:** ~350 lines from server.py

---

## Context

Following successful completion of Phase 1 (WorkflowService and BackgroundTaskManager extraction), we now proceed to extract service management endpoints into a dedicated ServiceController.

**Phase 1 Results:**
- ✅ Reduced server.py from 2,110 → 1,888 lines
- ✅ Created 2 new services (WorkflowService, BackgroundTaskManager)
- ✅ 320/324 tests passing (zero regressions)

**Phase 2 Goal:**
- Extract service management endpoints from server.py
- Create ServiceController utility class
- Target: Reduce server.py to ~1,500 lines

---

## Scope Analysis

### Target Endpoints (Lines 856-1183 in server.py)

These endpoints manage external services:

1. **Webhook Service Management**
   - `POST /api/services/webhook/start` (lines 856-911)
   - Starts webhook service subprocess
   - Checks if already running
   - Returns status

2. **Cloudflare Tunnel Management**
   - `POST /api/services/cloudflare/restart` (lines 912-967)
   - Restarts Cloudflare tunnel
   - Kills existing processes
   - Starts new tunnel

3. **GitHub Webhook Health**
   - `GET /api/services/github-webhook/health` (lines 968-1053)
   - Checks GitHub webhook configuration
   - Queries GitHub API
   - Returns webhook status

4. **GitHub Webhook Redelivery**
   - `POST /api/services/github-webhook/redeliver` (lines 1054-1183)
   - Redeliver recent GitHub webhook
   - Complex diagnostics
   - 129 lines - largest function!

### Common Patterns

All these endpoints share:
- Subprocess management (start, stop, check status)
- Error handling and logging
- Status response formatting
- Process lifecycle management

---

## Extraction Plan

### Step 1: Create ServiceController Class

**File:** `app/server/services/service_controller.py`

**Responsibilities:**
- Manage external service processes (webhook, cloudflare)
- Check service health/status
- Start/stop/restart services
- Provide diagnostic information

**Methods:**

```python
class ServiceController:
    def start_webhook_service(self) -> dict
    def restart_cloudflare_tunnel(self) -> dict
    def get_github_webhook_health(self) -> dict
    def redeliver_github_webhook(self) -> dict

    # Private helpers
    def _is_process_running(self, port: int) -> bool
    def _kill_process_on_port(self, port: int) -> None
    def _start_subprocess(self, cmd: list[str], cwd: str, log_file: str) -> subprocess.Popen
```

### Step 2: Extract Helper Functions

**Subprocess utilities** (used across all service endpoints):

```python
def _is_process_running(self, port: int) -> bool:
    """Check if process is running on given port"""

def _kill_process_on_port(self, port: int) -> None:
    """Kill process running on given port"""

def _start_subprocess(self, cmd: list[str], cwd: str, log_file: str) -> subprocess.Popen:
    """Start subprocess with proper logging and error handling"""
```

### Step 3: Update server.py Endpoints

Replace implementation with service calls:

```python
@app.post("/api/services/webhook/start")
async def start_webhook_service() -> dict:
    """Start webhook service - delegates to ServiceController"""
    return service_controller.start_webhook_service()

@app.post("/api/services/cloudflare/restart")
async def restart_cloudflare_tunnel() -> dict:
    """Restart Cloudflare tunnel - delegates to ServiceController"""
    return service_controller.restart_cloudflare_tunnel()

# etc.
```

### Step 4: Initialize ServiceController

Add to server.py initialization section:

```python
# Initialize services
manager = ConnectionManager()
workflow_service = WorkflowService()
service_controller = ServiceController(
    webhook_port=8001,
    webhook_script="../../adws/adw_triggers/trigger_webhook.py",
    cloudflare_tunnel_name=os.getenv("CLOUDFLARE_TUNNEL_NAME"),
    github_token=os.getenv("GITHUB_TOKEN"),
    github_repo=os.getenv("GITHUB_REPO", "warmonger0/tac-webbuilder")
)
```

---

## Expected Results

### File Size Targets

| File | Current | Target | Reduction |
|------|---------|--------|-----------|
| server.py | 1,888 lines | ~1,500 lines | -388 lines |
| services/service_controller.py | 0 lines | ~400 lines | NEW |

### Metrics

- **Lines extracted:** ~400 lines
- **Endpoints refactored:** 4
- **Helper functions created:** ~3-5
- **Test coverage target:** 80%+ for new service

---

## Testing Strategy

### Unit Tests

**File:** `app/server/tests/test_service_controller.py`

Test cases needed:

```python
def test_start_webhook_service_success()
def test_start_webhook_service_already_running()
def test_restart_cloudflare_tunnel_success()
def test_restart_cloudflare_tunnel_not_configured()
def test_github_webhook_health_check()
def test_redeliver_github_webhook_success()
def test_redeliver_github_webhook_no_recent()
def test_is_process_running()
def test_kill_process_on_port()
```

### Integration Tests

Verify endpoints still work:

```python
def test_webhook_start_endpoint()
def test_cloudflare_restart_endpoint()
def test_github_webhook_health_endpoint()
def test_github_webhook_redeliver_endpoint()
```

---

## ADW Workflow Steps

Following standard 8-phase ADW methodology:

### Phase 1: Plan ✅
- This document
- Scope analysis complete
- Extraction boundaries identified

### Phase 2: Build
1. Create `services/service_controller.py`
2. Implement ServiceController class
3. Extract endpoint logic
4. Update server.py imports
5. Update server.py endpoints
6. Initialize service_controller

### Phase 3: Lint
- Run ruff/pylint on new file
- Ensure code style compliance
- Fix any linting issues

### Phase 4: Test
- Write unit tests for ServiceController
- Write integration tests for endpoints
- Run full test suite
- Verify no regressions

### Phase 5: Review
- Check code quality
- Verify separation of concerns
- Validate error handling
- Ensure logging is adequate

### Phase 6: Document
- Update SERVICE_CONTROLLER docstrings
- Add usage examples
- Update Phase 2 log
- Record lessons learned

### Phase 7: Ship
- Commit changes
- Push to repository
- Update main branch

### Phase 8: Cleanup
- Archive any temporary files
- Update refactoring progress
- Plan Phase 3

---

## Potential Challenges

### 1. GitHub API Token Management

**Issue:** GitHub webhook operations require API token

**Solution:**
- Accept token via constructor
- Fall back to environment variable
- Handle missing token gracefully
- Return clear error messages

### 2. Subprocess Lifecycle

**Issue:** Process management is complex (start, stop, check, restart)

**Solution:**
- Use ProcessRunner utility (from Phase 2 of main plan)
- Implement proper timeout handling
- Add comprehensive error handling
- Log all subprocess operations

### 3. Port Conflict Detection

**Issue:** Checking if port is in use requires platform-specific commands

**Solution:**
- Use `lsof -ti :PORT` on macOS/Linux
- Use `netstat` on Windows
- Handle command not found errors
- Provide fallback methods

### 4. Log File Management

**Issue:** Subprocesses need log files, which can grow large

**Solution:**
- Create logs directory if not exists
- Use unique log file names (timestamp or PID)
- Consider log rotation (future enhancement)
- Document log file locations

---

## Dependencies

### Required Imports

```python
import logging
import os
import subprocess
from typing import Dict, Optional
from pathlib import Path
```

### Internal Dependencies

- May use ProcessRunner if created in Phase 2 (Utils)
- Will use environment variables for configuration
- Requires GitHub token for webhook operations

---

## Success Criteria

### Code Quality

- ✅ ServiceController has single responsibility
- ✅ All methods have proper docstrings
- ✅ Error handling is comprehensive
- ✅ Logging is clear and helpful

### Functionality

- ✅ All 4 endpoints work correctly
- ✅ Subprocess management is reliable
- ✅ Error messages are user-friendly
- ✅ Status responses are accurate

### Testing

- ✅ 80%+ code coverage
- ✅ All existing tests still pass
- ✅ Integration tests for endpoints
- ✅ Zero regressions

### Metrics

- ✅ server.py reduced by ~350+ lines
- ✅ ServiceController is ~400 lines
- ✅ Code is well-organized
- ✅ Backwards compatible

---

## Timeline

**Estimated:** 3-4 hours

1. **Planning** (complete): 30 min ✅
2. **Build ServiceController**: 90 min
3. **Write Tests**: 60 min
4. **Integration & Testing**: 30 min
5. **Documentation**: 30 min

**Total:** ~3.5 hours

---

## Next Phase Preview

After Phase 2 completion, Phase 3 will focus on:

**Phase 3: Create Helper Utilities**
- DatabaseManager (eliminate ~60 lines duplication)
- LLMClient (eliminate ~90 lines duplication)
- ProcessRunner (eliminate ~120 lines duplication)
- Frontend formatters (eliminate ~50 lines duplication)

**Estimated Impact:** Reduce codebase by ~320 lines of duplicated code

---

## References

- [Phase 1 Results](./SERVER_PY_REFACTORING_LOG.md)
- [Main Refactoring Plan](../implementation/codebase-refactoring/REFACTORING_PLAN.md)
- [Refactoring Analysis](../implementation/codebase-refactoring/REFACTORING_ANALYSIS.md)

---

**Status:** 📋 READY TO START
**Prerequisites:** ✅ All complete
**Blocking Issues:** None
**Ready to Begin:** Yes

---

## Quick Start Command for Next Session

```bash
# Start Phase 2 refactoring
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
# Review this plan
cat ../../docs/refactoring/PHASE_2_SERVICE_CONTROLLER_PLAN.md
# Begin extraction
# Step 1: Create services/service_controller.py
```

---

**Document Version:** 1.0
**Created:** 2025-11-19
**Last Updated:** 2025-11-19
**Next Review:** After Phase 2 completion
