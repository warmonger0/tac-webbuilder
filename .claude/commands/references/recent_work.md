# Recent Work & Session History

Quick reference for recent development work and major architectural milestones.

**For detailed session documentation:** See `docs/sessions/`
**For commit history:** Run `git log --oneline --grep="Session"` or `git log --oneline`

---

## Major Architectural Milestones

**Session 23 (Dec 2025) - Progressive Loading System:**
- Implemented lazy loading with deterministic logic gates
- 75% reduction in always-loaded context (3,190 → 801 tokens)
- Created CODE_STANDARDS.md (single source of truth for standards)
- Enhanced CLAUDE.md with logic gates for critical checkpoints
- Progressive escalation: prime → QUICK_REF → quick_start → references → full docs

→ Full docs: `docs/sessions/SESSION_23_PROGRESSIVE_LOADING_REFACTOR.md`

**Session 22 (Dec 2025) - Tool Call Tracking:**
- ToolCallTracker for ADW pattern learning (20/20 tests passing)
- Enabled by default in all build workflows
- Two-layer tracking: hook_events (Claude Code) + task_logs.tool_calls (ADW)
- 29K events captured, 11 patterns discovered, $183K potential savings

→ Full docs: `docs/sessions/session-22-tool-call-tracker-implementation.md`
→ Full docs: `docs/architecture/adw-tracking-architecture.md`, `docs/design/tool-call-tracking-design.md`

**Session 19 (Nov 2025) - ADW Loop Prevention:**
- Dual-layer protection against infinite retry loops (Issue #168)
- Verification-based loop control + pattern-based circuit breaker
- MAX_TEST_RETRY_ATTEMPTS = 3, MAX_SAME_AGENT_REPEATS = 8 in 15 comments

→ Full docs: See CODE_STANDARDS.md Section 2 (Loop Prevention)

**Sessions 15-16, 21 (Oct-Nov 2025) - WebSocket Real-Time Updates:**
- 6/6 components migrated from HTTP polling to WebSocket
- Performance: <2s latency (vs 3-10s polling)
- Real-time workflow updates across all panels

→ Full docs: Search git history for websocket-related commits

**Sessions 7-14 (Sep-Oct 2025) - Observability & Analytics Foundation:**
- Daily pattern analysis, cost attribution, error/latency analytics
- Closed-loop ROI tracking with confidence updating
- Observability database and metrics infrastructure

→ Full docs: `.claude/commands/references/observability.md`, `analytics.md`
→ Full docs: `docs/features/observability-and-logging.md`

---

## Recent Sessions (Last 5)

**Session 25 (Dec 2025) - GitHub REST API Fallback & Critical Fixes:**
- **REST API Fallback**: Automatic fallback when GraphQL rate limit exhausted
  - Doubles GitHub API capacity: 5000 GraphQL + 5000 REST = 10,000 operations/hour
  - Token management: GITHUB_PAT → GH_TOKEN → gh CLI extraction
  - Comprehensive error handling with graceful degradation
- **PostgreSQL Pool Fix**: Resolved `PoolError` in connection pool (thread ID key)
- **Panel 5 Automation**: GitHub issue creation with `issue_exists()` validation
- Files: `github_poster.py`, `postgres_adapter.py`, `planned_features_routes.py`

→ Full docs: TBD (see git commits 09752ec, 60c8407, 698fb4a)

**Session 24 (Dec 2025) - Single Source of Truth Fixes:**
- Fixed phase detection: ADW Monitor now queries `task_logs` database (not filesystem)
- Fixed cost display: Queries `task_logs` for cumulative costs (not null state file)
- Identified Issue #224 hung during Plan phase (PR creator agent, no timeout)
- **Key lesson**: Database is source of truth; filesystem/state files are caches

→ Full docs: `docs/sessions/SESSION_24_SINGLE_SOURCE_OF_TRUTH.md`

**Session 21 (Nov 2025) - Workflow Resume & Panel 7 Performance:**
- PhaseTracker: Resume workflows from last incomplete phase (50% time savings)
- Panel 7: 20x faster (< 1s vs 15-20s) via file filtering + parallelization

→ Full docs: `app_docs/feature-workflow-resume.md`, `app_docs/feature-panel7-performance-optimization.md`

**Session 20 (Nov 2025) - GitHub Rate Limit Handling:**
- Proactive API quota management with graceful degradation
- Real-time monitoring: `/api/v1/github-rate-limit` endpoint

→ Full docs: See git history for rate limit commits

**Session 19 (Nov 2025) - ADW Loop Prevention:**
- (See Major Architectural Milestones above)

---

## Full Session Archive

For complete session-by-session history: `docs/sessions/` directory

**Available session documentation:**
- `SESSION_23_PROGRESSIVE_LOADING_REFACTOR.md`
- `SESSION_24_SINGLE_SOURCE_OF_TRUTH.md`
- `session-22-tool-call-tracker-implementation.md`
- Additional sessions documented in git history
