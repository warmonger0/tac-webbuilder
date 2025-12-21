# Backend Quick Start

## Tech Stack
FastAPI + Python 3.10+ + PostgreSQL + OpenAI/Anthropic APIs + Pydantic

## Key Directories
- `app/server/routes/` - API route modules (9 files, 40+ endpoints)
- `app/server/services/` - Business logic layer (10+ services)
- `app/server/repositories/` - Data access layer (5 repositories)
- `app/server/database/` - Database abstraction (PostgreSQL-only, SQLite removed)
- `app/server/core/` - Core business logic (13 modules)
- `app/server/tests/` - Test suite (878+ test functions across 50+ files)

## API Routes (40+ Endpoints)
- **data_routes.py** - File upload, NL→SQL queries, exports
- **workflow_routes.py** - Workflow management, history, analytics
- **queue_routes.py** - Multi-phase workflow queue coordination, resume workflow endpoint
- **github_routes.py** - Issue creation, preview, confirmation
- **system_routes.py** - Health checks, service control, ADW monitoring
- **work_log_routes.py** - Session logging (Panel 10)
- **planned_features_routes.py** - Roadmap tracking (Panel 5), AI plan generation (Session 21)
- **websocket_routes.py** - Real-time updates (workflows, routes, history, ADW monitor, queue)
- **context_review_routes.py** - Context analysis

## Database Support
- **PostgreSQL** (only) - Production-ready, connection pooling, advanced features
- **SQLite removed:** As of Session 3, codebase is PostgreSQL-only
- **Configuration:** Set `POSTGRES_*` env vars (see `.env.example`)
- **Database Adapter:** `database/get_database_adapter.py` provides unified interface

## Security Architecture
**SQL Injection Prevention (4 layers):**
1. Identifier validation (whitelist)
2. Parameterized queries
3. Dangerous operation blocking
4. DDL permission checks

Module: `core/sql_security.py`
Tests: `tests/test_sql_injection.py` (30+ tests)

## Session 19: Repository Standards (NEW)

### Standard CRUD Naming
**All repositories follow consistent naming:**
```python
from typing import Optional, List
from pydantic import BaseModel

class MyRepository:
    # Create
    def create(self, item: ModelCreate) -> Model:
        """Create new record, return full object"""

    # Read
    def get_by_id(self, id: int) -> Optional[Model]:
        """Get single record by primary key"""

    def get_by_<field>(self, value: Any) -> Optional[Model]:
        """Get by unique field (e.g., get_by_email)"""

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Model]:
        """Get all with pagination"""

    def get_all_by_<field>(self, value: Any, limit: int = 100) -> List[Model]:
        """Get all matching field value"""

    # Update
    def update(self, id: int, data: ModelUpdate) -> Optional[Model]:
        """Update existing record"""

    # Delete
    def delete(self, id: int) -> bool:
        """Delete by ID"""

    # Custom
    def find_<custom_criteria>(...) -> List[Model]:
        """Complex queries with descriptive name"""
```

**Benefits:**
- Predictable method names across all repositories
- Easy IDE autocomplete
- Consistent pagination support
- create() returns full object (not just ID)

### WebSocket Broadcasting
**Broadcast state changes to connected clients:**
```python
from app.server.routes.websocket_routes import manager

async def update_workflow(workflow_id: int, status: str):
    # Update database
    workflow = repository.update_status(workflow_id, status)

    # Broadcast to all clients
    await manager.broadcast({
        "type": "workflows_update",
        "data": [workflow.model_dump()]
    })
```

**Documentation:**
- Repository Standards: `docs/backend/repository-standards.md`
- Backend Patterns: `docs/patterns/backend-patterns.md`
- Migration Guide: `docs/guides/migration-guide-session-19.md`

## Common Tasks

### API Endpoints
- Quick reference: `.claude/commands/references/api_endpoints.md` (1,700 tokens)
- Full details: `docs/api.md` (2,400 tokens)
- Modify: `app/server/server.py`

### SQL Security
Read: `app/server/core/sql_security.py` directly
Always use: `execute_query_safely()`, `validate_identifier()`

### LLM Integration
- Module: `core/llm_processor.py`
- Feature doc: `app_docs/feature-4c768184-model-upgrades.md`

### Database Schema
Dynamic schema from uploaded files. Check: `core/file_processor.py`

### Work Log API (Panel 10)
- **Routes:** `routes/work_log_routes.py`
- **Repository:** `repositories/work_log_repository.py`
- **Endpoints:**
  - `POST /api/v1/work-log` - Create 280-char session summary
  - `GET /api/v1/work-log` - List entries (paginated)
  - `DELETE /api/v1/work-log/{id}` - Delete entry
- **Quick reference:** `.claude/commands/references/observability.md`

### Planned Features API (Panel 5) - NEW (Session 8A)
- **Routes:** `routes/planned_features_routes.py`
- **Service:** `services/planned_features_service.py`
- **Repository:** `repositories/planned_features_repository.py`
- **Endpoints:**
  - `POST /api/v1/planned-features` - Create roadmap item
  - `GET /api/v1/planned-features` - List all features
  - `GET /api/v1/planned-features/{id}` - Get by ID
  - `PUT /api/v1/planned-features/{id}` - Update feature
  - `DELETE /api/v1/planned-features/{id}` - Delete feature
- **Quick reference:** `.claude/commands/references/planned_features.md`

### WebSocket Real-Time Updates (Sessions 15-16)
- **Routes:** `routes/websocket_routes.py`
- **Background Tasks:** `services/background_tasks.py` (5 watchers, 2s intervals)
- **Endpoints:**
  - `/ws/workflows` - Real-time workflow status updates
  - `/ws/routes` - Real-time route updates
  - `/ws/workflow-history` - Real-time history updates
  - `/ws/adw-monitor` - Real-time ADW monitoring
  - `/ws/queue` - Real-time queue updates (NEW in Session 16)
- **Performance:** Broadcast only on state change, <2s latency
- **Architecture:** Background watchers check every 2s, compare state via JSON, broadcast to connected clients

### Analytics Services (Sessions 7, 9-13)
- **Pattern Review:** `services/pattern_review_service.py` - Pattern approval workflow
- **Cost Attribution:** CLI-based analytics (no service layer yet)
- **Error Analytics:** CLI-based analytics (no service layer yet)
- **Latency Analytics:** CLI-based analytics (no service layer yet)
- **ROI Tracking:** CLI-based analytics (no service layer yet)
- **Confidence Updates:** CLI-based system (no service layer yet)

## Resume Workflow Feature (Issue #106)
**Endpoint:** `POST /api/v1/queue/resume/{adw_id}`

**Purpose:** Resume paused ADW workflows after running preflight checks

**Features:**
- Runs preflight checks with `skip_tests=True` for faster resume
- Requires clean git state (no uncommitted changes)
- Returns clear error messages if checks fail
- Launches workflow in background using subprocess.Popen()
- Frontend UI: Resume button in CurrentWorkflowCard (only for paused workflows)

**Implementation:**
- Handler: `queue_routes.py:289-381` (`_resume_adw_handler()`)
- Endpoint: `queue_routes.py:538-547`
- Frontend API: `app/client/src/api/queueClient.ts:247-271` (`resumeAdw()`)
- UI: `app/client/src/components/CurrentWorkflowCard.tsx:221-269`

## Quick Commands
```bash
cd app/server
uv sync --all-extras   # Install dependencies
uv run python server.py # Start server (port 8000 or BACKEND_PORT)
uv run pytest           # Run tests
uv run pytest tests/test_sql_injection.py -v  # Security tests

# Reliable startup (prevents PostgreSQL PoolError)
../../scripts/start_full_clean.sh  # Kills processes, no --reload flag
```

## When to Load Full Docs
- **API details:** `docs/api.md` (2,400 tokens)
- **Architecture:** `docs/architecture.md` (2,300 tokens)
- **Observability (Work Logs, Pattern Learning):** `.claude/commands/references/observability.md` (900 tokens)
- **Setup/troubleshooting:** `README.md` (1,300 tokens)
- **Feature-specific:** Use `conditional_docs.md`
