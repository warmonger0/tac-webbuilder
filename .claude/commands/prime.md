# Prime - Progressive Context Loader

## Project Essence
**tac-webbuilder** - Natural language web development assistant with automated GitHub workflows

## Three Core Features
1. **NL SQL Interface** - Natural language → SQL queries (FastAPI + React + SQLite)
2. **NL → GitHub Issues** - Natural language → Structured issues with auto-routing
3. **ADW Automation** - Automated development in isolated git worktrees (Claude Code CLI)

## Quick Architecture
- **Worktree isolation:** Up to 15 concurrent ADWs in `trees/{adw_id}/`
- **Port allocation:** Backend 9100-9114, Frontend 9200-9214
- **Cost optimization:** $0.20-0.50 (lightweight) → $3-5 (standard)
- **Security:** Multi-layer SQL injection prevention

## What Are You Working On?

### Frontend (app/client/)
**Tech:** React + Vite + TypeScript + Tailwind + TanStack Query + Zustand

→ Read `.claude/commands/quick_start/frontend.md` [~300 tokens]

### Backend (app/server/)
**Tech:** FastAPI + Python + SQLite + OpenAI/Anthropic

→ Read `.claude/commands/quick_start/backend.md` [~300 tokens]

### ADW Workflows (adws/)
**Automated development via isolated worktrees**

→ Read `.claude/commands/quick_start/adw.md` [~400 tokens]

### Documentation
**Adding or updating docs**

→ Read `.claude/commands/quick_start/docs.md` [~200 tokens]

### Not Sure / Need Routing Help
→ Read `.claude/commands/references/decision_tree.md` [~400 tokens]

## Quick Commands
```bash
# Run
git ls-files                           # List all tracked files

# Full stack
./scripts/start_full.sh                # Start backend + frontend

# Backend
cd app/server && uv run python server.py   # Port 8000

# Frontend
cd app/client && bun run dev           # Port 5173

# ADW
cd adws/ && uv run adw_sdlc_iso.py 123  # Run workflow

# Tests
cd app/server && uv run pytest         # Backend tests
```

## After Loading Quick Start
Confirm you understand:
1. Which subsystem you're working in
2. Where to find detailed docs if needed (references/ or full docs/)
3. The progressive loading approach (quick_start → references → full docs)

---

**Progressive Loading Strategy:**
- **Tier 1** (you are here): 50-100 tokens
- **Tier 2** (quick_start): 300-400 tokens
- **Tier 3** (references): 900-1,700 tokens
- **Tier 4** (full docs): 2,000-4,000 tokens

Load only what you need. Use `conditional_docs.md` for feature-specific documentation.
