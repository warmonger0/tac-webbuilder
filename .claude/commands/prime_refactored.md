# Prime - Progressive Context Loader

## Project Essence
**tac-webbuilder** - AI-powered GitHub automation platform with autonomous SDLC workflows

## Four Core Features
1. **ADW Automation** - 10-phase SDLC workflows in isolated git worktrees (Claude Code CLI)
2. **NL → GitHub Issues** - Natural language → Structured issues with auto-routing
3. **Observability & Analytics** - Pattern analysis, cost attribution, error/latency tracking, ROI metrics
4. **10-Panel Dashboard** - Real-time workflow monitoring, roadmap tracking, and control

## Code Standards - Behavioral Requirements (Session 22)

**CRITICAL COMMIT RULES:**
- ❌ Never include "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ Never include "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Never reference AI generation in commits
- ✅ Professional, technical-focused messages only

**DELEGATION IS MANDATORY:**
- ✅ Use sub-agents for research, exploration, and specialized tasks
- ✅ "Trust but verify" - Review sub-agent findings before acting
- ✅ Let sub-agents "occupy a lane and advise you on it"
- ❌ DO NOT try to do everything yourself - context is finite
- ❌ DO NOT skip documentation research when unsure

**COMPREHENSIVE FIXES ONLY:**
- ✅ See errors, fix them comprehensively at the root cause
- ✅ Document why the error occurred and what was fixed
- ❌ DO NOT create temporary workarounds or "just make it work" fixes
- ❌ DO NOT say "don't worry, I'll just do this to make it work"

## What Are You Working On?

### Need Architecture/Commands Reference?
→ Read `.claude/QUICK_REF.md` [~600 tokens] - Ports, startup, database, commands, tech stack

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
**Key workflows:** adw_sdlc_complete_iso, adw_sdlc_complete_zte (zero-touch)

→ Read `.claude/commands/quick_start/adw.md` [~400 tokens]

### Plans Panel (Session 8A/8B)
**Database-driven roadmap tracking with session management**

→ Read `.claude/commands/references/planned_features.md` [~600 tokens]
→ Full doc: `docs/features/planned-features-system.md` [~1,500 tokens]

### Observability & Analytics
**Pattern analysis, cost attribution, error/latency analytics, ROI tracking**
**Status:** Daily pattern analysis, cost attribution, error analytics, latency analytics, closed-loop ROI, confidence updating, auto-archiving

→ Read `.claude/commands/references/observability.md` [~900 tokens]
→ Read `.claude/commands/references/analytics.md` [~800 tokens]
→ Full doc: `docs/features/observability-and-logging.md` [~2,500 tokens]

### WebSocket Real-Time Updates (Sessions 15-16, 21)
**Migration from HTTP polling to WebSocket**
**Status:** 6/6 components migrated - CurrentWorkflowCard, AdwMonitorCard, QualityPanel, ZteHopperQueueCard, RoutesView, WorkflowHistoryView
**Performance:** <2s latency (vs 3-10s polling)

### ADW Loop Prevention (Session 19 - Issue #168)
**Dual-layer protection against infinite retry loops**
- **Layer 1:** Verification-based loop control
- **Layer 2:** Pattern-based circuit breaker
- **Files:** `adws/adw_test_iso.py`, `adws/adw_sdlc_complete_iso.py`

### GitHub Rate Limit Handling (Session 20)
**Proactive API quota management with graceful degradation**
- Verifies quota before API calls
- Clear error messages with remaining quota
- Workflows pause instead of failing
- **Files:** `adws/adw_modules/rate_limit.py`, `app/server/routes/system_routes.py`

### Workflow Resume & Performance Optimization (Session 21)
**Intelligent phase skipping + Panel 7 optimization**
- **PhaseTracker:** Tracks completed phases, enables resume from last incomplete
- **50% time savings:** Pause after Phase 5 = only run 5 phases (not 10)
- **Panel 7:** 20x faster (< 1s vs 15-20s)
- **Files:** `adws/adw_modules/phase_tracker.py`, `adws/adw_sdlc_complete_iso.py`

→ Full docs: `app_docs/feature-workflow-resume.md`, `app_docs/feature-panel7-performance-optimization.md`

### Tool Call Tracking & Pattern Detection (Session 22)
**Infrastructure for ADW pattern learning and automation**
- **29K hook events captured**, 11 patterns discovered (5 approved)
- **$183K potential savings** identified in approved patterns
- **ToolCallTracker:** Context manager for automatic tool tracking (20/20 tests passing)
  - Enabled by default in all ADW build workflows
  - Zero-overhead guarantee
  - Two-layer tracking: hook_events (Claude Code tools) + task_logs.tool_calls (ADW workflow tools)
- **Files:** `adws/adw_modules/tool_call_tracker.py`, `adws/adw_build_workflow.py`

→ Full docs: `docs/architecture/adw-tracking-architecture.md`, `docs/design/tool-call-tracking-design.md`

### Documentation
**Adding or updating docs**

→ Read `.claude/commands/quick_start/docs.md` [~200 tokens]

### Not Sure / Need Routing Help
→ Read `.claude/commands/references/decision_tree.md` [~400 tokens]

---

## After Loading Quick Start

Confirm you understand:
1. Which subsystem you're working in
2. Where to find detailed docs (references/ or full docs/)
3. The progressive loading approach (QUICK_REF → quick_start → references → full docs)

---

**Progressive Loading Strategy:**
- **Tier 0** (QUICK_REF.md): ~600 tokens - Architecture, commands, tech stack
- **Tier 1** (prime): ~150 tokens - Project orientation
- **Tier 2** (quick_start): 300-400 tokens - Subsystem primers
- **Tier 3** (references): 900-1,700 tokens - Feature deep-dives
- **Tier 4** (full docs): 2,000-4,000 tokens - Complete context

Load only what you need. When in doubt, check QUICK_REF.md first for architecture questions.
