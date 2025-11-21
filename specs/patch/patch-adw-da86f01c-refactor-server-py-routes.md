# Patch: Refactor server.py to Meet 800-Line Hard Limit

## Metadata
adw_id: `da86f01c`
review_change_request: `Issue #1: server.py has 999 lines, exceeding the 800-line hard limit specified in .claude/references/code_quality_standards.md. The file MUST be refactored before merging. Resolution: Refactor server.py to extract endpoints into separate route modules or group related endpoints into dedicated files (e.g., adw_routes.py, workflow_routes.py, system_routes.py). This will improve maintainability and comply with code quality standards. Severity: blocker`

## Issue Summary
**Original Spec:** `/Users/Warmonger0/tac/tac-webbuilder/trees/da86f01c/specs/issue-72-adw-da86f01c-sdlc_planner-move-docs-planned-features-adw-monitor-folder-to-d.md`
**Issue:** server.py has 999 lines, exceeding the 800-line hard limit specified in code quality standards
**Solution:** Extract endpoints into logical route modules organized by functional domain (data operations, workflow operations, system operations, GitHub operations)

## Files to Modify

### New Files to Create
- `app/server/routes/__init__.py` - Empty init file to make routes a package
- `app/server/routes/data_routes.py` - Data operations endpoints (upload, query, schema, insights, export, tables)
- `app/server/routes/workflow_routes.py` - Workflow-related endpoints (workflows, workflow-history, costs, analytics, trends, predictions, catalog)
- `app/server/routes/system_routes.py` - System/service endpoints (health, system-status, adw-monitor, services)
- `app/server/routes/github_routes.py` - GitHub integration endpoints (request, preview, confirm)
- `app/server/routes/websocket_routes.py` - WebSocket endpoints (ws/workflows, ws/routes, ws/workflow-history)

### Files to Modify
- `app/server/server.py` - Strip out endpoint handlers, keep only app initialization and legacy wrapper functions

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create routes directory structure
- Create `app/server/routes/` directory
- Create empty `app/server/routes/__init__.py` file to make it a Python package

### Step 2: Extract data operation endpoints to data_routes.py
- Create `app/server/routes/data_routes.py` with FastAPI router
- Move the following endpoints from server.py:
  - `/api/upload` (POST) - File upload and conversion
  - `/api/query` (POST) - Natural language query processing
  - `/api/schema` (GET) - Database schema retrieval
  - `/api/insights` (POST) - Insights generation
  - `/api/generate-random-query` (GET) - Random query generation
  - `/api/table/{table_name}` (DELETE) - Table deletion
  - `/api/export/table` (POST) - Table export
  - `/api/export/query` (POST) - Query results export
- Import required dependencies (FastAPI, HTTPException, Response, File, UploadFile)
- Import required core modules (file_processor, sql_processor, insights, export_utils, etc.)
- Import required data models from core.data_models
- Create APIRouter instance with prefix="" and tags=["Data Operations"]
- Estimated lines: ~200

### Step 3: Extract workflow endpoints to workflow_routes.py
- Create `app/server/routes/workflow_routes.py` with FastAPI router
- Move the following endpoints from server.py:
  - `/api/workflows` (GET) - Get all workflows
  - `/api/routes` (GET) - Get routes
  - `/api/workflows/{adw_id}/costs` (GET) - Get workflow costs
  - `/api/workflow-history` (GET) - Get workflow history with filters
  - `/api/workflow-history/resync` (POST) - Resync workflow history
  - `/api/workflows/batch` (POST) - Get batch workflows
  - `/api/workflow-analytics/{adw_id}` (GET) - Get workflow analytics
  - `/api/workflow-trends` (GET) - Get workflow trends
  - `/api/cost-predictions` (GET) - Predict workflow costs
  - `/api/workflow-catalog` (GET) - Get workflow catalog
- Import WorkflowService, workflow_history functions, cost_tracker
- Import required data models
- Create APIRouter instance with prefix="" and tags=["Workflows"]
- Estimated lines: ~250

### Step 4: Extract system endpoints to system_routes.py
- Create `app/server/routes/system_routes.py` with FastAPI router
- Move the following endpoints from server.py:
  - `/api/health` (GET) - Health check
  - `/api/system-status` (GET) - System status
  - `/api/adw-monitor` (GET) - ADW monitor status
  - `/api/services/webhook/start` (POST) - Start webhook service
  - `/api/services/cloudflare/restart` (POST) - Restart Cloudflare tunnel
  - `/api/services/github-webhook/health` (GET) - GitHub webhook health
  - `/api/services/github-webhook/redeliver` (POST) - Redeliver GitHub webhook
- Import HealthService, ServiceController, adw_monitor
- Import required data models
- Create APIRouter instance with prefix="" and tags=["System"]
- Estimated lines: ~120

### Step 5: Extract GitHub integration endpoints to github_routes.py
- Create `app/server/routes/github_routes.py` with FastAPI router
- Move the following endpoints from server.py:
  - `/api/request` (POST) - Submit natural language request
  - `/api/preview/{request_id}` (GET) - Get issue preview
  - `/api/preview/{request_id}/cost` (GET) - Get cost estimate
  - `/api/confirm/{request_id}` (POST) - Confirm and post issue
- Import GitHubIssueService, GitHubPoster, complexity_analyzer
- Import required data models
- Create APIRouter instance with prefix="" and tags=["GitHub Integration"]
- Estimated lines: ~80

### Step 6: Extract WebSocket endpoints to websocket_routes.py
- Create `app/server/routes/websocket_routes.py` with FastAPI router
- Move the following endpoints from server.py:
  - `/ws/workflows` (WebSocket) - Workflows WebSocket
  - `/ws/routes` (WebSocket) - Routes WebSocket
  - `/ws/workflow-history` (WebSocket) - Workflow history WebSocket
- Import WebSocket, WebSocketDisconnect, ConnectionManager
- Import WorkflowService, workflow_history functions
- Create APIRouter instance with prefix="" and tags=["WebSockets"]
- Estimated lines: ~100

### Step 7: Update server.py to use routers
- Keep only the following in server.py:
  - Imports for FastAPI, CORSMiddleware, lifespan context manager
  - App initialization with lifespan
  - CORS middleware configuration
  - Service initialization (health_service, service_controller, workflow_service, etc.)
  - Legacy wrapper functions (get_workflows_data, get_routes_data, get_workflow_history_data)
  - Router registration using app.include_router()
- Import all route modules from routes package
- Register each router with app.include_router(router)
- Add main block for running uvicorn
- Estimated lines: ~150 (well under 800-line limit)

### Step 8: Update imports and ensure all dependencies are available
- Verify all route modules can import their required dependencies
- Ensure service instances (health_service, workflow_service, etc.) are passed to routers or made globally accessible
- Update any circular import issues if they arise
- Test that all imports resolve correctly

### Step 9: Verify file line counts meet standards
- Run `wc -l` on server.py to confirm it's under 800 lines
- Run `wc -l` on each route module to confirm they're under 800 lines
- Document the new line counts in comments

### Step 10: Update any tests that import directly from server.py
- Check test files for imports like `from server import app`
- These should still work since app is still defined in server.py
- Verify no tests import endpoint handlers directly

## Validation
Execute every command to validate the patch is complete with zero regressions.

### File Length Validation
```bash
# Verify server.py is under 800 lines
wc -l app/server/server.py
# Expected: < 800 lines

# Verify all route modules are under 800 lines
wc -l app/server/routes/*.py
# Expected: All files < 800 lines each
```

### Syntax and Import Validation
```bash
# Verify Python syntax for all files
cd app/server && uv run python -m py_compile server.py routes/*.py

# Verify no import errors
cd app/server && uv run python -c "from server import app; print('✓ server.py imports successfully')"
cd app/server && uv run python -c "from routes import data_routes, workflow_routes, system_routes, github_routes, websocket_routes; print('✓ All route modules import successfully')"
```

### Linting Validation
```bash
# Run ruff to check code quality
cd app/server && uv run ruff check .
```

### Test Suite Validation
```bash
# Run all backend tests to ensure no regressions
cd app/server && uv run pytest tests/ -v --tb=short
```

### API Endpoint Validation
```bash
# Start the server and verify all endpoints are registered
cd app/server && uv run python server.py &
sleep 3

# Test a few key endpoints to ensure they still work
curl -s http://localhost:8000/api/health | python3 -m json.tool
curl -s http://localhost:8000/api/system-status | python3 -m json.tool
curl -s http://localhost:8000/api/workflows | python3 -m json.tool
curl -s http://localhost:8000/api/adw-monitor | python3 -m json.tool

# Kill the server
pkill -f "python server.py"
```

### Full Test Suite (from .claude/commands/test.md)
```bash
# Run comprehensive test suite
cd app/server && uv run python -m py_compile server.py main.py core/*.py routes/*.py
cd app/server && uv run ruff check .
cd app/server && uv run pytest tests/ -v --tb=short
```

## Patch Scope
**Lines of code to change:** ~999 lines (extracting ~850 lines to route modules, leaving ~150 in server.py)
**Risk level:** medium (major refactoring but preserving all functionality)
**Testing required:** Full backend test suite must pass, all endpoints must remain functional, no import errors

## Success Criteria
- [ ] server.py is under 800 lines (target: ~150 lines)
- [ ] All route modules created and under 800 lines each
- [ ] All 29 endpoints still registered and functional
- [ ] No import errors or circular dependencies
- [ ] All backend tests pass
- [ ] Ruff linting passes
- [ ] API endpoints respond correctly when server is running
- [ ] No regressions in functionality
