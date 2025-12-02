# Backend Quick Start

## Tech Stack
FastAPI + Python 3.10+ + SQLite/PostgreSQL + OpenAI/Anthropic APIs + Pydantic

## Key Directories
- `app/server/routes/` - API route modules (8 files, 36 endpoints)
- `app/server/services/` - Business logic layer (7+ services)
- `app/server/repositories/` - Data access layer (3 repositories)
- `app/server/database/` - Database abstraction (SQLite/PostgreSQL adapters)
- `app/server/core/` - Core business logic (13 modules)
- `app/server/tests/` - Test suite (878 test functions across 50 files)

## API Routes (36 Endpoints)
- **data_routes.py** - File upload, NL→SQL queries, exports
- **workflow_routes.py** - Workflow management, history, analytics
- **queue_routes.py** - Multi-phase workflow queue coordination
- **github_routes.py** - Issue creation, preview, confirmation
- **system_routes.py** - Health checks, service control, ADW monitoring
- **work_log_routes.py** - Session logging (Panel 10) - NEW
- **websocket_routes.py** - Real-time updates
- **context_review_routes.py** - Context analysis

## Database Support
- **SQLite** (default) - Zero-config, single-file, development-friendly
- **PostgreSQL** (production) - Connection pooling, production-ready
- **Configuration:** Set `DB_TYPE` env var (sqlite | postgresql)
- **Adapter Pattern:** `database/factory.py` provides unified interface

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

### Work Log API (Panel 10) - NEW
- **Routes:** `routes/work_log_routes.py`
- **Repository:** `repositories/work_log_repository.py`
- **Endpoints:**
  - `POST /api/v1/work-log` - Create 280-char session summary
  - `GET /api/v1/work-log` - List entries (paginated)
  - `DELETE /api/v1/work-log/{id}` - Delete entry
- **Quick reference:** `.claude/commands/references/observability.md`

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
