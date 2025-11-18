### Workflow 3.3: Migrate Files to ProcessRunner
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1, 3.2

**Input Files:**
- `app/server/server.py` (multiple subprocess calls)
- `adws/adw_triggers/trigger_webhook.py` (subprocess calls)
- `adws/adw_modules/workflow_ops.py` (subprocess calls)

**Output Files:**
- All above files (modified)

**Tasks:**
1. Create shared ProcessRunner instances
2. Migrate server.py subprocess calls (5+ locations)
3. Migrate trigger_webhook.py subprocess calls (3+ locations)
4. Migrate workflow_ops.py subprocess calls (7+ locations)
5. Remove manual timeout/error handling code
6. Test all subprocess-dependent operations

**Before/After Example:**
```python
# BEFORE:
try:
    result = subprocess.run(
        ["git", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        logger.error(f"Git command failed: {result.stderr}")
        return None
    return result.stdout
except subprocess.TimeoutExpired:
    logger.error("Git command timed out")
    return None
except Exception as e:
    logger.error(f"Error running git: {e}")
    return None

# AFTER:
from core.process_utils import ProcessRunner

runner = ProcessRunner()
result = runner.run(
    ["git", "status"],
    cwd=worktree_path,
    timeout=30
)
if result.success:
    return result.stdout
else:
    if result.timed_out:
        logger.error("Git command timed out")
    else:
        logger.error(f"Git command failed: {result.stderr}")
    return None
```

**Files to Update:**
- `app/server/server.py` - 5+ subprocess calls
- `adws/adw_triggers/trigger_webhook.py` - 3+ subprocess calls
- `adws/adw_modules/workflow_ops.py` - 7+ subprocess calls

**Acceptance Criteria:**
- [ ] All subprocess calls use ProcessRunner
- [ ] No manual timeout handling
- [ ] No manual error handling patterns
- [ ] All tests pass
- [ ] Code duplication reduced by ~120 lines

**Verification Commands:**
```bash
# Search for remaining direct subprocess usage
grep -r "subprocess.run" app/server/ adws/ --exclude-dir=tests --exclude=process_utils.py

# Should only show process_utils.py

# Run all tests
cd app/server && pytest tests/ -v
cd adws && pytest tests/ -v
```
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
