# Next Session: Phase 2 ServiceController Extraction

**Ready to Start:** ✅ YES
**Prerequisites:** All complete
**Estimated Duration:** 3-4 hours

---

## Copy/Paste This Prompt

```
I'm continuing the manual ADW-style refactoring of server.py. We just completed Phase 1
(WorkflowService & BackgroundTaskManager extraction), reducing server.py from 2,110 to
1,888 lines with zero test regressions.

I'm ready to start Phase 2: ServiceController extraction.

**Context:**
- Phase 1 complete: 222 lines extracted, 320/324 tests passing
- Target: Extract 4 service management endpoints (~350 lines)
- Goal: Reduce server.py to ~1,500 lines

**Phase 2 Scope:**
Extract these endpoints into ServiceController class:
1. POST /api/services/webhook/start (~55 lines)
2. POST /api/services/cloudflare/restart (~55 lines)
3. GET /api/services/github-webhook/health (~85 lines)
4. POST /api/services/github-webhook/redeliver (~129 lines)

**Documentation to Review:**
- @docs/refactoring/PHASE_2_SERVICE_CONTROLLER_PLAN.md (detailed plan)
- @docs/refactoring/REFACTORING_PROGRESS.md (progress tracker)
- @docs/refactoring/SERVER_PY_REFACTORING_LOG.md (Phase 1 results)

**Working Directory:**
/Users/Warmonger0/tac/tac-webbuilder/app/server

**Instructions:**
Follow the ADW workflow methodology (Plan → Build → Test → Review → Document → Ship):
1. Review Phase 2 plan
2. Create services/service_controller.py
3. Extract the 4 service management endpoints
4. Update server.py to delegate to ServiceController
5. Write tests for ServiceController
6. Run test suite (verify no regressions)
7. Document results
8. Commit changes

**Success Criteria:**
- server.py reduced to ~1,500 lines
- ServiceController created (~400 lines)
- All tests pass (target: 330+/334+)
- Zero breaking changes
- Comprehensive documentation

Let's start with reviewing the Phase 2 plan and then create the ServiceController class.
```

---

## Alternative Short Prompt

If you want a quicker start:

```
Continue Phase 2 of server.py refactoring - extract ServiceController from
@docs/refactoring/PHASE_2_SERVICE_CONTROLLER_PLAN.md. Phase 1 reduced server.py
from 2,110 → 1,888 lines with zero regressions. Target: ~1,500 lines after Phase 2.
```

---

## Key Files to Reference

### Planning Documents
- `docs/refactoring/PHASE_2_SERVICE_CONTROLLER_PLAN.md` - Detailed extraction plan
- `docs/refactoring/REFACTORING_PROGRESS.md` - Master progress tracker
- `docs/refactoring/SERVER_PY_REFACTORING_LOG.md` - Phase 1 complete log

### Code to Modify
- `app/server/server.py` - Lines 856-1183 (service management endpoints)
- Create: `app/server/services/service_controller.py` (new file)
- Update: `app/server/services/__init__.py` (add export)

### Tests to Write
- Create: `app/server/tests/test_service_controller.py` (unit tests)
- Update: `app/server/tests/` (integration tests for endpoints)

---

## Phase 2 Quick Reference

### Target Endpoints

```python
# Lines 856-911: Webhook Service Start
@app.post("/api/services/webhook/start")
async def start_webhook_service() -> dict

# Lines 912-967: Cloudflare Tunnel Restart
@app.post("/api/services/cloudflare/restart")
async def restart_cloudflare_tunnel() -> dict

# Lines 968-1053: GitHub Webhook Health
@app.get("/api/services/github-webhook/health")
async def get_github_webhook_health() -> dict

# Lines 1054-1183: GitHub Webhook Redelivery
@app.post("/api/services/github-webhook/redeliver")
async def redeliver_github_webhook() -> dict
```

### Expected ServiceController Structure

```python
class ServiceController:
    """Manages external service processes and health checks"""

    def __init__(
        self,
        webhook_port: int = 8001,
        webhook_script: str = "../../adws/adw_triggers/trigger_webhook.py",
        cloudflare_tunnel_name: str | None = None,
        github_token: str | None = None,
        github_repo: str = "warmonger0/tac-webbuilder"
    ):
        # Initialize configuration

    def start_webhook_service(self) -> dict:
        # Extract from lines 856-911

    def restart_cloudflare_tunnel(self) -> dict:
        # Extract from lines 912-967

    def get_github_webhook_health(self) -> dict:
        # Extract from lines 968-1053

    def redeliver_github_webhook(self) -> dict:
        # Extract from lines 1054-1183

    # Private helpers
    def _is_process_running(self, port: int) -> bool:
        # Check if process running on port

    def _kill_process_on_port(self, port: int) -> None:
        # Kill process on port

    def _start_subprocess(self, cmd: list[str], cwd: str, log_file: str) -> subprocess.Popen:
        # Start subprocess with logging
```

---

## Commands to Run

```bash
# Navigate to working directory
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Check current state
wc -l server.py services/*.py

# After extraction, test imports
uv run python -c "import server; print('✓ Server imports successfully')"

# Run test suite
uv run pytest tests/ -v

# Check line count reduction
wc -l server.py  # Should be ~1,500 lines
```

---

## Expected Results

### Metrics

| Metric | Current | Target | Change |
|--------|---------|--------|--------|
| server.py | 1,888 lines | ~1,500 lines | -388 |
| ServiceController | 0 lines | ~400 lines | NEW |
| Tests passing | 320/324 | 330+/334+ | +10 new tests |
| Overall progress | 13% | 36% | +23% |

### Commits

```bash
# Expected commit message pattern:
refactor: Extract ServiceController from server.py

Reduce server.py from 1,888 to ~1,500 lines (-388 lines, -20.6%) by extracting
service management endpoints into dedicated ServiceController class.

## Changes

### New Service Created

- **ServiceController** (~400 lines)
  - Webhook service start/stop
  - Cloudflare tunnel management
  - GitHub webhook health checks
  - GitHub webhook redelivery

### server.py Modifications

- Removed 388 lines of service management logic
- Updated endpoints to delegate to ServiceController
- Maintained backwards compatibility

## Testing

✅ Server imports successfully
✅ 330+/334+ tests pass
✅ Zero test failures from refactoring
✅ 100% backwards compatible

## Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| server.py lines | 1,888 | ~1,500 | -388 (-20.6%) |
| Service modules | 4 | 5 | +1 |
| Overall progress | 13% | 36% | +23% |
```

---

## Troubleshooting

### If Server Won't Import

```bash
# Check for syntax errors
uv run python -m py_compile server.py

# Check specific service
uv run python -c "from services.service_controller import ServiceController; print('OK')"
```

### If Tests Fail

```bash
# Run specific test
uv run pytest tests/test_service_controller.py -v

# Run with verbose output
uv run pytest tests/ -vv --tb=long

# Check for regressions only
uv run pytest tests/ -k "not test_pattern_persistence"
```

### If Endpoints Don't Work

```bash
# Start server and test endpoint
uv run python server.py &
curl -X POST http://localhost:8000/api/services/webhook/start
```

---

## Success Checklist

Before completing Phase 2:

- [ ] ServiceController class created
- [ ] All 4 endpoints extracted
- [ ] server.py updated to delegate
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests pass
- [ ] Server imports successfully
- [ ] All tests pass (330+/334+)
- [ ] Zero regressions
- [ ] Phase 2 log documented
- [ ] Progress tracker updated
- [ ] Changes committed

---

**Ready to Start:** ✅ YES
**Blocking Issues:** None
**Prerequisites:** All complete

**Good luck with Phase 2! 🚀**
