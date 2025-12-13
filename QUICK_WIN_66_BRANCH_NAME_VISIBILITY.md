# Quick Win #66: Branch Name Not Visible in Workflow State

## Context
Load: `/prime`

## Task
Fix bug where `branch_name` stored in `adw_state.json` but not extracted to workflow metadata → null in DB/UI.

## Evidence
- ✅ Planning phase saves `branch_name` to `adw_state.json` (confirmed: agents/abbfec9e/adw_state.json:4)
- ❌ `_extract_workflow_metadata()` reads state but doesn't add `branch_name` to return dict
- ❌ Database `workflow_history.branch_name` is null
- ❌ UI shows no branch/PR links

**Location**: `app/server/utils/filesystem.py:46-62` (`_extract_workflow_metadata`)

## Workflow

### 1. Investigate (5 min)
```bash
# Confirm state file has branch_name
cat agents/*/adw_state.json | grep branch_name | head -3

# Check _extract_workflow_metadata
grep -A15 "def _extract_workflow_metadata" app/server/utils/filesystem.py
```

### 2. Fix (15 min)

**File**: `app/server/utils/filesystem.py`

**Add to return dict** (line ~57):
```python
def _extract_workflow_metadata(adw_id: str, adw_dir: Path, state_data: dict) -> dict:
    return {
        "adw_id": adw_id,
        "issue_number": None,
        "nl_input": state_data.get("nl_input"),
        "github_url": state_data.get("github_url"),
        "workflow_template": state_data.get("workflow_template", state_data.get("workflow")),
        "model_used": state_data.get("model_used", state_data.get("model")),
        "status": state_data.get("status") or "pending",
        "start_time": state_data.get("start_time"),
        "branch_name": state_data.get("branch_name"),  # ← ADD THIS LINE
        "plan_file": state_data.get("plan_file"),      # ← ADD THIS LINE
        "issue_class": state_data.get("issue_class"),  # ← ADD THIS LINE
        "current_phase": state_data.get("current_phase"),
        # ... rest unchanged
    }
```

### 3. Test (15 min)
```bash
# Backend tests
cd app/server
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/utils/test_filesystem.py -v -k metadata

# Check database after next workflow
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder -c "SELECT adw_id, branch_name, plan_file, issue_class FROM workflow_history ORDER BY created_at DESC LIMIT 5;"

# Verify WebSocket broadcast includes branch_name
# Start servers, trigger workflow, check browser devtools
```

### 4. Quality (10 min)
```bash
cd app/server
ruff check utils/filesystem.py --fix
mypy utils/filesystem.py --ignore-missing-imports
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/ -v

# Plans Panel
curl -X PATCH http://localhost:8002/api/v1/planned-features/66 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "actual_hours": 0.75, "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "completion_notes": "Fixed branch_name extraction in filesystem.py"}'

# Commit (NO AI references)
git add app/server/utils/filesystem.py
git commit -m "fix: Extract branch_name from workflow state

Planning phase saves branch_name to adw_state.json but _extract_workflow_metadata() didn't include it in return dict.

Problem:
- branch_name null in database
- UI shows no PR links
- Poor workflow tracking UX

Solution:
- Added branch_name, plan_file, issue_class to _extract_workflow_metadata()
- Now properly extracted to workflow history
- WebSocket broadcasts complete state

Result:
- Database workflow_history.branch_name populated
- UI can show PR links
- Better workflow visibility

Location: app/server/utils/filesystem.py:57-59"

# Update docs (if needed - likely skip for small bug fix)
# /updatedocs
```

## Success Criteria
- ✅ `branch_name` in return dict
- ✅ Database shows non-null `branch_name` for new workflows
- ✅ UI displays branch/PR links
- ✅ All tests pass

## Time: 0.75h (45 min)
