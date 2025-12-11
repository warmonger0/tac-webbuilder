# Prime - Progressive Context Loader

## Project Essence
**tac-webbuilder** - AI-powered GitHub automation platform with autonomous SDLC workflows

## Four Core Features
1. **ADW Automation** - 10-phase SDLC workflows in isolated git worktrees (Claude Code CLI)
2. **NL → GitHub Issues** - Natural language → Structured issues with auto-routing
3. **Observability & Analytics** - Pattern analysis, cost attribution, error/latency tracking, ROI metrics
4. **10-Panel Dashboard** - Real-time workflow monitoring, roadmap tracking, and control

## Quick Architecture
- **Worktree isolation:** Up to 15 concurrent ADWs in `trees/{adw_id}/`
- **Port allocation:** Backend 9100-9114, Frontend 9200-9214 (calculated from adw_id)
- **Main ports:** Backend 8002, Frontend 5173 (from .ports.env)
- **10-phase SDLC:** Plan → Validate → Build → Lint → Test → Review → Document → Ship → Cleanup → Verify
- **Cost optimization:** 60-80% savings via external test tools
- **Loop prevention:** Verification-based loop control + pattern-based circuit breaker (Issue #168)
- **Database:** PostgreSQL only (production-grade, required for observability)
- **Security:** Multi-layer SQL injection prevention
- **Claude Code timeout:** 20-minute timeout for planning tasks (prevents premature termination)

## Code Standards - Git Commits
**CRITICAL:** Never include in commit messages:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Any AI generation references

Commits should be professional and focused on technical changes only.

## What Are You Working On?

### Frontend (app/client/)
**Tech:** React + Vite + TypeScript + Tailwind + TanStack Query
**Note:** Zustand listed in package.json but unused - all state via React hooks

**10-Panel System:**
- Panel 1: Request Form | Panel 6: Patterns (stub)
- Panel 2: ADW Dashboard | Panel 7: Quality (stub)
- Panel 3: History | Panel 8: Review (active, needs fixes)
- Panel 4: Routes | Panel 9: Data (stub)
- Panel 5: Plans (complete, database-driven) | Panel 10: Work Log (complete)

→ Read `.claude/commands/quick_start/frontend.md` [~300 tokens]

### Backend (app/server/)
**Tech:** FastAPI + Python + PostgreSQL + OpenAI/Anthropic
**36 endpoints:** GitHub, workflows, queue, work-log, system, websocket, observability

→ Read `.claude/commands/quick_start/backend.md` [~300 tokens]

### ADW Workflows (adws/)
**10-phase orchestration via isolated worktrees**
**Key workflows:** adw_sdlc_complete_iso, adw_sdlc_complete_zte (zero-touch)

→ Read `.claude/commands/quick_start/adw.md` [~400 tokens]

### Plans Panel (Session 8A/8B)
**Database-driven roadmap tracking with session management**
**Panel 5:** View/edit planned features, track session progress, manage roadmap

→ Read `.claude/commands/references/planned_features.md` [~600 tokens]
→ Full doc: `docs/features/planned-features-system.md` [~1,500 tokens]

### Observability & Analytics
**Pattern analysis, cost attribution, error/latency analytics, ROI tracking**
**New in Sessions 7-14:** Daily pattern analysis, cost attribution, error analytics, latency analytics, closed-loop ROI tracking, confidence updating, auto-archiving

→ Read `.claude/commands/references/observability.md` [~900 tokens]
→ Read `.claude/commands/references/analytics.md` [~800 tokens] (Sessions 9-11)
→ Full doc: `docs/features/observability-and-logging.md` [~2,500 tokens]

### WebSocket Real-Time Updates
**Migration from HTTP polling to WebSocket for real-time dashboard updates**
**Status:** 5/6 components migrated (Sessions 15-16)
- ✅ CurrentWorkflowCard - Real-time workflow status
- ✅ AdwMonitorCard - Real-time ADW monitoring
- ✅ ZteHopperQueueCard - Real-time queue updates
- ✅ RoutesView - Real-time route updates
- ✅ WorkflowHistoryView - Real-time history updates
- 🟢 SystemStatusPanel - Polling OK (status rarely changes)

**Performance:** <2s latency (vs 3-10s polling), reduced network traffic, broadcast only on state change

### ADW Loop Prevention (Session 19 - Issue #168)
**Dual-layer protection against infinite retry loops**
**Problem:** Test resolver agents claimed "✅ Resolved" but tests still failed → infinite loop (62 comments)
**Solution:**
- **Layer 1:** Verification-based loop control - Re-runs tests after each resolution to verify actual progress
- **Layer 2:** Pattern-based circuit breaker - Detects same agent posting 8+ times in 15 comments
- **Files:** `adws/adw_test_iso.py` (lines 806-909, 1097-1200), `adws/adw_sdlc_complete_iso.py` (lines 53-149)
- **Retry limits:** Max 3 attempts (test and E2E)
- **Exit conditions:** No progress detected OR max attempts OR circuit breaker triggered

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
cd app/server && uv run python server.py   # Port from .ports.env (BACKEND_PORT=8002)

# Frontend
cd app/client && bun run dev           # Port from .ports.env (FRONTEND_PORT=5173)

# ADW
cd adws/ && uv run adw_sdlc_complete_iso.py 123  # Full SDLC

# Tests
cd app/server && uv run pytest         # 878 tests
cd app/client && bun test              # 149 tests

# CLI Tools (Sessions 7-14)
./scripts/run_analytics.sh analyze_daily_patterns.py --report  # Pattern analysis (auto-credentials)
./scripts/run_analytics.sh analyze_errors.py --report          # Error analysis
./scripts/run_analytics.sh analyze_costs.py --report           # Cost analytics
./scripts/health_check.sh                                      # Full system health check
```

## Health Checks & Observability (Session 18)
```bash
# Multi-layer health check system
./scripts/health_check.sh              # Terminal: 7 sections including observability
curl localhost:8002/api/v1/preflight-checks  # API: 9 checks (port from .ports.env)
# Panel 1 UI: Automatic display of all preflight checks

# 3 New Observability Checks:
# - observability_database: PostgreSQL connection + tables
# - hook_events_recording: Verify events being captured
# - pattern_analysis_system: Analytics scripts functional
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
