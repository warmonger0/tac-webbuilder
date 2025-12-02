# Prime - Progressive Context Loader

## Project Essence
**tac-webbuilder** - AI-powered GitHub automation platform with autonomous SDLC workflows

## Four Core Features
1. **ADW Automation** - 9-phase SDLC workflows in isolated git worktrees (Claude Code CLI)
2. **NL → GitHub Issues** - Natural language → Structured issues with auto-routing
3. **Observability & Pattern Learning** - Hook events, cost tracking, automation detection
4. **10-Panel Dashboard** - Real-time workflow monitoring and control

## Quick Architecture
- **Worktree isolation:** Up to 15 concurrent ADWs in `trees/{adw_id}/`
- **Port allocation:** Backend 9100-9114, Frontend 9200-9214
- **9-phase SDLC:** Plan → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup
- **Cost optimization:** 60-80% savings via external test tools
- **Dual database:** SQLite (dev) + PostgreSQL (production)
- **Security:** Multi-layer SQL injection prevention

## What Are You Working On?

### Frontend (app/client/)
**Tech:** React + Vite + TypeScript + Tailwind + TanStack Query
**Note:** Zustand listed in package.json but unused - all state via React hooks

**10-Panel System:**
- Panel 1: Request Form | Panel 6: Patterns (stub)
- Panel 2: ADW Dashboard | Panel 7: Quality (stub)
- Panel 3: History | Panel 8: Review (stub)
- Panel 4: Routes | Panel 9: Data (stub)
- Panel 5: Plans (stub) | Panel 10: Work Log (NEW)

→ Read `.claude/commands/quick_start/frontend.md` [~300 tokens]

### Backend (app/server/)
**Tech:** FastAPI + Python + SQLite/PostgreSQL + OpenAI/Anthropic
**36 endpoints:** GitHub, workflows, queue, work-log, system, websocket

→ Read `.claude/commands/quick_start/backend.md` [~300 tokens]

### ADW Workflows (adws/)
**9-phase orchestration via isolated worktrees**
**Key workflows:** adw_sdlc_complete_iso, adw_sdlc_complete_zte (zero-touch)

→ Read `.claude/commands/quick_start/adw.md` [~400 tokens]

### Observability & Pattern Learning
**Hook events, pattern detection, cost tracking, work logs**

→ Read `.claude/commands/references/observability.md` [~900 tokens]
→ Full doc: `docs/features/observability-and-logging.md` [~2,500 tokens]

### Documentation
**Adding or updating docs**

→ Read `.claude/commands/quick_start/docs.md` [~200 tokens]

### Not Sure / Need Routing Help
→ Read `.claude/commands/references/decision_tree.md` [~400 tokens]

## Quick Commands
```bash
# Full stack
./scripts/start_full.sh                # Backend + frontend

# Backend
cd app/server && uv run python server.py   # Port 8000

# Frontend
cd app/client && bun run dev           # Port 5173

# ADW
cd adws/ && uv run adw_sdlc_complete_iso.py 123  # Full SDLC

# Tests
cd app/server && uv run pytest         # 878 tests
cd app/client && bun test              # 149 tests
```

## After Loading Quick Start
Confirm you understand:
1. Which subsystem you're working in
2. Where to find detailed docs (references/ or full docs/)
3. The progressive loading approach (quick_start → references → full docs)

---

**Progressive Loading Strategy:**
- **Tier 1** (prime): ~150 tokens
- **Tier 2** (quick_start): 300-400 tokens
- **Tier 3** (references): 900-1,700 tokens
- **Tier 4** (full docs): 2,000-4,000 tokens

Load only what you need. Use `conditional_docs.md` for feature-specific documentation.
