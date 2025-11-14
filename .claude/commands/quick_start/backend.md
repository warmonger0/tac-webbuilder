# Backend Quick Start

## Tech Stack
FastAPI + Python 3.10+ + SQLite + OpenAI/Anthropic APIs + Pydantic

## Key Directories
- `app/server/core/` - Business logic (13 modules)
- `app/server/tests/` - Test suite (5 test files)
- `app/server/server.py` - FastAPI application
- `app/server/main.py` - Entry point

## Core Modules
- **server.py** - FastAPI app, endpoints
- **llm_processor.py** - AI model integration
- **nl_processor.py** - Natural language processing
- **sql_processor.py** - SQL execution
- **sql_security.py** - Multi-layer SQL injection prevention
- **file_processor.py** - CSV/JSON upload handling
- **data_models.py** - Pydantic models (20+)

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
- **Setup/troubleshooting:** `README.md` (1,300 tokens)
- **Feature-specific:** Use `conditional_docs.md`
