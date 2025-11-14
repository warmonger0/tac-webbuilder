# tac-webbuilder Project Summary

## What It Is
Natural language web development assistant with automated GitHub workflow execution.

## Three Core Features
1. **NL SQL Interface** - Natural language → SQL queries on uploaded data (FastAPI + React + SQLite)
2. **NL → GitHub Issues** - Natural language → Structured GitHub issues with auto-routing
3. **ADW Automation** - Automated dev workflows in isolated git worktrees (Claude Code CLI integration)

## Key Concepts
- **Worktree Isolation:** Each workflow runs in `trees/{adw_id}/` with dedicated ports (9100-9114 backend, 9200-9214 frontend)
- **Cost Optimization:** Complexity analyzer routes to lightweight ($0.20-0.50) vs standard ($3-5) workflows
- **SDLC Phases:** Plan → Build → Test → Review → Document → Ship
- **Security:** Multi-layer SQL injection prevention in `app/server/core/sql_security.py`

## Tech Stack
**Frontend:** React 18.3 + Vite + TypeScript + Tailwind + TanStack Query + Zustand
**Backend:** FastAPI + Python 3.10+ + SQLite + OpenAI/Anthropic
**ADW:** Git worktrees + Claude Code CLI + GitHub CLI + Bash orchestration

## Quick Start
```bash
./scripts/start_full.sh              # Start full stack
cd adws/ && uv run adw_sdlc_iso.py 123  # Run ADW workflow
cd app/server && uv run pytest       # Run tests
```

## File Structure
```
app/server/          # FastAPI backend
app/client/          # React frontend
adws/                # ADW workflow system
  adw_modules/       # Core modules (agent, workflow_ops, worktree_ops, etc.)
  adw_*_iso.py      # Workflow scripts
  adw_triggers/      # Webhook/cron triggers
scripts/             # Utility scripts (18 files)
docs/                # Technical docs (13 files)
.claude/commands/    # 35+ slash commands
  references/        # Detailed reference docs
```

## When to Read More

**For architecture details:** `.claude/commands/references/architecture_overview.md`
**For ADW workflows:** `.claude/commands/references/adw_workflows.md`
**For API endpoints:** `.claude/commands/references/api_endpoints.md`
**For conditional loading:** `.claude/commands/conditional_docs.md` (320 lines - comprehensive guide)

**For specific features:** See `conditional_docs.md` for 40+ documentation files mapped to specific conditions
