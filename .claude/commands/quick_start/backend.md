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
- **queue_routes.py** - Multi-phase workflow queue coordination
- **github_routes.py** - Issue creation, preview, confirmation
- **system_routes.py** - Health checks, service control, ADW monitoring
- **work_log_routes.py** - Session logging (Panel 10)
- **planned_features_routes.py** - Roadmap tracking (Panel 5) - NEW (Session 8A)
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

## Quick Commands
```bash
cd app/server
uv sync --all-extras   # Install dependencies
uv run python server.py # Start server (port 8000 or BACKEND_PORT)
uv run pytest           # Run tests
uv run pytest tests/test_sql_injection.py -v  # Security tests
```

## When to Load Full Docs
- **API details:** `docs/api.md` (2,400 tokens)
- **Architecture:** `docs/architecture.md` (2,300 tokens)
- **Observability (Work Logs, Pattern Learning):** `.claude/commands/references/observability.md` (900 tokens)
- **Setup/troubleshooting:** `README.md` (1,300 tokens)
- **Feature-specific:** Use `conditional_docs.md`
