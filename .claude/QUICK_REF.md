# Architecture Quick Reference

**Purpose:** Prevent re-researching common architectural facts every session. Read this when you encounter questions about ports, startup, database, or project structure.

---

## Port Configuration

- **8001**: ADW Webhook Service (`adws/adw_triggers/trigger_webhook.py`)
- **8002**: Main FastAPI Backend (`app/server/server.py`)
- **5173**: Frontend Dev Server (`app/client`)

**Why dual backends?**
- Port 8001 handles ADW workflow triggers via webhook
- Port 8002 serves the main API for frontend + general usage
- They run independently and serve different purposes

---

## Startup

**Correct command:** `./scripts/start_full_clean.sh`

**Avoid these (broken/deprecated):**
- `scripts/start.sh` - Missing environment variables
- `scripts/start_full.sh` - References missing start_webbuilder.sh

**What startup does:**
1. Starts ADW webhook service on port 8001
2. Starts main backend API on port 8002
3. Starts frontend dev server on port 5173

**Health checks:**
- `curl http://localhost:8001/webhook-status`
- `curl http://localhost:8002/api/v1/health`
- `curl http://localhost:5173`

---

## Database

**Type:** PostgreSQL
**Location:** localhost:5432
**Database:** tac_webbuilder
**Credentials:** tac_user / changeme (dev environment)

**Connection config:** See `app/server/db/connection.py`
**Environment vars:** `.env` files or `.ports.env`

---

## Project Structure

```
tac-webbuilder/
├── adws/                    # ADW (Autonomous Digital Worker) system
│   ├── adw_modules/         # Reusable workflow components
│   ├── adw_triggers/        # Webhook trigger service (port 8001)
│   ├── adw_*_workflow.py    # Self-contained workflow definitions
│   └── tests/               # ADW unit tests
├── app/
│   ├── server/              # Main FastAPI backend (port 8002)
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Database access layer
│   │   └── db/              # Database connection and migrations
│   └── client/              # React frontend (port 5173)
│       └── src/components/panels/  # Panel-based UI architecture
├── scripts/                 # Utility scripts (startup, migrations, etc.)
└── .claude/                 # Claude Code configuration
    ├── commands/            # Slash commands
    └── QUICK_REF.md         # This file
```

---

## Common Gotchas

- **Always use dual backends:** Both 8001 and 8002 must be running for full functionality
- **Environment variables:** Check `.ports.env` for port configuration
- **ADW workflows are self-contained:** Everything in `adws/` directory, don't mix with main app
- **Tool tracking system:** Two layers - `hook_events` table (Claude Code tools) + `task_logs.tool_calls` (ADW workflow tools)
- **Test commands:** Use `pytest` for backend, `vitest` for frontend
- **ADW worktree isolation:** Up to 15 concurrent ADWs in `trees/{adw_id}/` with dynamic port allocation
- **10-phase SDLC:** Plan → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup → Verify

---

## GitHub API Rate Limiting

ADW workflows automatically handle GitHub API rate limiting with intelligent fallback:

**Rate Limits (separate quotas):**
- GraphQL API: 5,000 requests/hour
- REST API: 5,000 requests/hour

**Automatic Fallback:**
- When GraphQL quota exhausted → Automatically uses REST API
- When REST API quota exhausted → Workflow pauses gracefully
- Status messages shown in stderr with current limit info
- Both APIs checked before making requests

**Where This Matters:**
- `fetch_issue()` - Issue fetching in Plan phase
- `make_issue_comment()` - Comment posting after phases complete
- Both functions in `adws/adw_modules/github.py`

**What You'll See:**
```
⚠️  GraphQL Rate Limit Exhausted - Falling back to REST API
GraphQL: 0/5000 (resets in 1823s)
REST API: 4832/5000 remaining
```

**Prevention:**
- Monitor rate limit usage during high-volume ADW runs
- Stagger issue processing if running 10+ concurrent workflows
- Rate limits reset hourly

---

## Quick Commands

### Full Stack
```bash
./scripts/start_full_clean.sh          # Correct startup (all three services)
./scripts/health_check.sh              # Full system health check
```

### Backend
```bash
cd app/server && uv run python server.py   # Uses BACKEND_PORT from .ports.env (8002)
cd app/server && uv run pytest             # Run 878 backend tests
```

### Frontend
```bash
cd app/client && bun run dev           # Uses FRONTEND_PORT from .ports.env (5173)
cd app/client && bun test              # Run 149 frontend tests
```

### ADW Workflows
```bash
cd adws/ && uv run adw_sdlc_complete_iso.py 123  # Full 10-phase SDLC for issue #123
```

### Analytics & Observability (Sessions 7-14)
```bash
./scripts/run_analytics.sh analyze_daily_patterns.py --report  # Pattern analysis
./scripts/run_analytics.sh analyze_errors.py --report          # Error analysis
./scripts/run_analytics.sh analyze_costs.py --report           # Cost analytics
```

### Health Checks (Session 18)
```bash
./scripts/health_check.sh                        # Terminal: 7 sections including observability
curl localhost:8002/api/v1/preflight-checks      # API: 9 checks (JSON response)
# Panel 1 UI also shows automatic preflight checks
```

### Developer Tools
```bash
./scripts/gen_prompt.sh --list         # List all planned features
./scripts/gen_prompt.sh 49             # Generate implementation prompt for issue #49
```

---

## Tech Stack

**Backend:** FastAPI + Python + PostgreSQL + OpenAI/Anthropic
- 37 API endpoints across 7 route modules
- PostgreSQL only (production-grade, required for observability)
- Multi-layer SQL injection prevention

**Frontend:** React + Vite + TypeScript + Tailwind + TanStack Query
- 10-panel dashboard architecture
- WebSocket for real-time updates (6/6 components migrated)
- Dev mode has silent logging for cleaner console

**ADW System:** Claude Code CLI orchestration
- Self-contained workflow definitions in `adws/`
- Isolated git worktrees prevent conflicts
- Dynamic port allocation (Backend 9100-9114, Frontend 9200-9214)

---

## When to Read Full Docs

This quick reference covers ~80% of common architecture questions. Read full documentation when:
- Implementing new features (not just understanding existing structure)
- Deep-diving into specific subsystems
- Troubleshooting complex issues requiring detailed context

**Key docs:**
- `app_docs/architecture.md` - Full architecture overview
- `adws/README.md` - ADW system documentation
- `.claude/commands/prime.md` - Current project status
- `.claude/commands/quick_start/` - Subsystem quick starts (frontend, backend, adw, docs)
- `.claude/commands/references/` - Deep references (observability, analytics, patterns)
