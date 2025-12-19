# Prime - Progressive Context Loader

## Project Essence
**tac-webbuilder** - Web-based, AI-powered, phased autonomous workflow system with self-improving capabilities via pattern learning

## Four Core Features
1. **ADW Automation** - 10-phase SDLC workflows in isolated git worktrees (Claude Code CLI)
2. **NL → GitHub Issues** - Natural language → Structured issues with auto-routing
3. **Observability & Analytics** - Pattern analysis, cost attribution, error/latency tracking, ROI metrics
4. **10-Panel Dashboard** - Real-time workflow monitoring, roadmap tracking, and control

## What Are You Working On?

### Need Architecture/Commands/Ports?
→ Read `.claude/QUICK_REF.md` [~600 tokens]
- Port configuration (8001 webhook, 8002 API, 5173 frontend)
- Startup commands
- Database setup
- Quick command reference
- Tech stack details

### Need Code Standards/Commit Rules?
→ Read `.claude/CODE_STANDARDS.md` [~400 tokens]
- Git commit standards (CRITICAL: no AI attribution)
- Loop prevention & retry limits
- Behavioral requirements (delegation, comprehensive fixes)
- Quality gates (before shipping)
- PR & documentation standards

### Frontend (app/client/)
**Tech:** React + Vite + TypeScript + Tailwind + TanStack Query
**10-Panel System:** Request Form, ADW Dashboard, History, Routes, Plans, Patterns, Quality, Review, Data, Work Log

→ Read `.claude/commands/quick_start/frontend.md` [~300 tokens]

### Backend (app/server/)
**Tech:** FastAPI + Python + PostgreSQL + OpenAI/Anthropic
**37 endpoints:** GitHub, workflows, queue, work-log, system, websocket, observability

→ Read `.claude/commands/quick_start/backend.md` [~300 tokens]

### ADW Workflows (adws/)
**10-phase orchestration via isolated worktrees**
**Key workflows:** adw_sdlc_complete_iso (full SDLC), adw_sdlc_complete_zte (zero-touch with auto-merge)

→ Read `.claude/commands/quick_start/adw.md` [~400 tokens]

### Recent Work & Features

**Session 22 (Current) - Tool Call Tracking:**
- ToolCallTracker for ADW pattern learning (20/20 tests passing)
- Enabled by default in all build workflows
- Two-layer tracking: hook_events (Claude Code) + task_logs.tool_calls (ADW)
- 29K events captured, 11 patterns discovered, $183K potential savings

→ Full docs: `docs/architecture/adw-tracking-architecture.md`, `docs/design/tool-call-tracking-design.md`

**Session 21 - Workflow Resume & Panel 7 Performance:**
- PhaseTracker: Resume workflows from last incomplete phase (50% time savings)
- Panel 7: 20x faster (< 1s vs 15-20s) via file filtering + parallelization

→ Full docs: `app_docs/feature-workflow-resume.md`, `app_docs/feature-panel7-performance-optimization.md`

**Session 20 - GitHub Rate Limit Handling:**
- Proactive API quota management with graceful degradation
- Real-time monitoring: `/api/v1/github-rate-limit` endpoint

**Session 19 - ADW Loop Prevention (Issue #168):**
- Dual-layer protection against infinite retry loops
- Verification-based loop control + pattern-based circuit breaker

**Session 15-16, 21 - WebSocket Real-Time Updates:**
- 6/6 components migrated from HTTP polling to WebSocket
- Performance: <2s latency (vs 3-10s polling)

**Observability & Analytics (Sessions 7-14):**
- Daily pattern analysis, cost attribution, error/latency analytics
- Closed-loop ROI tracking with confidence updating

### Planned Features & Roadmap
→ Read `.claude/commands/references/planned_features.md` [~600 tokens]
→ Full doc: `docs/features/planned-features-system.md` [~1,500 tokens]

### Observability Deep-Dive
→ Read `.claude/commands/references/observability.md` [~900 tokens]
→ Read `.claude/commands/references/analytics.md` [~800 tokens]
→ Full doc: `docs/features/observability-and-logging.md` [~2,500 tokens]

### Documentation
**Adding or updating docs**
→ Read `.claude/commands/quick_start/docs.md` [~200 tokens]

### Not Sure / Need Routing Help
→ Read `.claude/commands/references/decision_tree.md` [~400 tokens]

---

## Progressive Loading Strategy

Load only what you need, when you need it:

- **Tier 0:** QUICK_REF.md (~600 tokens) - Architecture, commands, tech stack
- **Tier 1:** prime.md (~300 tokens) - YOU ARE HERE - Project orientation, routing
- **Tier 2:** quick_start/ (~300-400 tokens) - Subsystem primers
- **Tier 3:** references/ (~900-1,700 tokens) - Feature deep-dives
- **Tier 4:** full docs/ (~2,000-4,000 tokens) - Complete context

**Logic Gates:** See `CLAUDE.md` for deterministic checkpoints (before commit, before API calls, before shipping, etc.)

---

## After Loading

Confirm you understand:
1. Which subsystem you're working in (frontend/backend/ADW)
2. Where to find detailed docs (references/ or full docs/)
3. The progressive loading approach (QUICK_REF → quick_start → references → full docs)
4. Logic gates enforce standards at critical moments (CLAUDE.md)
