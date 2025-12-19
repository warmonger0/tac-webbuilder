# CLAUDE.md - Progressive Loading & Logic Gates

## Progressive Loading for Architecture

When you encounter questions about project architecture, startup procedures, port configuration, database setup, or other foundational topics:

1. **First:** Check session handoff documents if provided (often contain "Quick Facts")
2. **Second:** Read `.claude/QUICK_REF.md` for common architecture patterns (~600 tokens)
3. **Last resort:** Spin up an Explore subagent to search full documentation and report back

**Goal:** Avoid re-researching the same architectural facts every session. The quick reference acts as a "cache" for commonly needed information. Use delegation for deep research to keep main context clean.

**When to skip quick reference:**
- Deep implementation work requiring detailed context
- Novel issues not covered by basic architecture
- User explicitly provides all needed context

---

## Logic Gates (Load Before Action)

These are **deterministic checkpoints** where specific context MUST be loaded before proceeding. Think of them as "guardrails" that ensure standards are always enforced.

### Before Git Commit

**TRIGGER:** ANY git commit command (`git commit`, `gh pr create` with auto-commit, etc.)

**ACTION REQUIRED:**
1. Read `.claude/CODE_STANDARDS.md` Section 1 (Git Commit Standards)
2. Verify commit message follows standards:
   - ❌ No "Generated with Claude Code" attribution
   - ❌ No "Co-Authored-By: Claude" attribution
   - ❌ No AI generation references
   - ✅ Professional, technical focus only

**WHY:** Prevents AI attribution in commit history (critical for professional codebase)

**ENFORCEMENT:** Manual (AI must remember to check) + Template-based in `adw_modules/commit_generator.py`

---

### Before GitHub API Calls

**TRIGGER:** Bulk GitHub operations (pr create, issue comment loops, GraphQL queries)

**ACTION REQUIRED:**
1. Check `adw_modules/rate_limit.py` → `ensure_rate_limit_available()`
2. Verify sufficient quota remaining:
   - REST API: 5000 requests/hour
   - GraphQL API: 5000 points/hour
3. If quota low, pause workflow gracefully (don't fail)

**WHY:** Prevents workflow failures from quota exhaustion, enables graceful degradation

**ENFORCEMENT:** Automated in ADW workflows via `rate_limit.py` module

---

### Before Test Retries

**TRIGGER:** Test failure in ADW workflow, considering retry

**ACTION REQUIRED:**
1. Read `.claude/CODE_STANDARDS.md` Section 2 (Loop Prevention)
2. Check retry limits:
   - `MAX_TEST_RETRY_ATTEMPTS = 3`
   - `MAX_SAME_AGENT_REPEATS = 8` in 15 comments
3. Apply verification-based loop control:
   - Re-run tests after fix
   - Verify actual progress (not just agent claims)
   - Circuit break if no progress

**WHY:** Prevents infinite retry loops (Issue #168 - 62 comment loop)

**ENFORCEMENT:** Automated in `adw_test_iso.py` and `adw_sdlc_complete_iso.py`

---

### When Facing Uncertainty

**TRIGGER:** Questions about architecture, unsure about project structure, don't understand why something works

**ACTION REQUIRED:**
1. Read `.claude/CODE_STANDARDS.md` Section 3 (Behavioral Requirements)
2. Apply delegation mandate:
   - ✅ Spawn Explore agent to research
   - ✅ "Trust but verify" findings
   - ❌ DON'T guess or assume
   - ❌ DON'T skip research

**WHY:** Prevents costly mistakes from guessing, ensures comprehensive understanding

**ENFORCEMENT:** Manual (AI judgment call on when uncertain)

---

### Before Shipping Code

**TRIGGER:** PR creation, manual deployment, workflow Ship phase

**ACTION REQUIRED:**
1. Read `.claude/CODE_STANDARDS.md` Section 4 (Quality Gates)
2. Verify ALL gates pass:
   - ✅ All tests pass (backend + frontend)
   - ✅ Type checking passes (tsc, mypy)
   - ✅ Linting passes (eslint, ruff)
   - ✅ Health checks pass (`./scripts/health_check.sh`)
   - ✅ Rate limit check before GitHub operations

**WHY:** Ensures production-quality code, prevents regressions

**ENFORCEMENT:** Manual (AI must run checks) + Automated health check script

---

## Progressive Loading Strategy

**Tier 0:** QUICK_REF.md (~600 tokens) - Architecture, commands, tech stack
**Tier 1:** prime.md (~300 tokens) - Project orientation, routing
**Tier 2:** quick_start/ (~300-400 tokens) - Subsystem primers
**Tier 3:** references/ (~900-1,700 tokens) - Feature deep-dives
**Tier 4:** full docs/ (~2,000-4,000 tokens) - Complete context

**Principle:** Load only what you need, when you need it. Use logic gates to ensure critical context loads at deterministic moments.

---

## Workflow-Specific Loading

### Planning Phases (Plan, Validate)
**Load:** QUICK_REF.md (architecture) + CODE_STANDARDS.md Section 3 (behavioral standards)

### Implementation Phases (Build, Lint, Test)
**Load:** Subsystem quick_start (frontend.md, backend.md, or adw.md)

### Shipping Phase (Ship)
**Load:** CODE_STANDARDS.md Sections 1, 4, 5 (commit rules, quality gates, PR standards)

### Error/Uncertainty
**Load:** CODE_STANDARDS.md Section 3 (delegation mandate) → Spawn Explore agent

---

## Quick Reference Map

| Need | File | Tokens |
|------|------|--------|
| Project orientation | `.claude/commands/prime.md` | ~300 |
| Architecture, ports, commands | `.claude/QUICK_REF.md` | ~600 |
| Coding standards, commit rules | `.claude/CODE_STANDARDS.md` | ~400 |
| Frontend primer | `.claude/commands/quick_start/frontend.md` | ~300 |
| Backend primer | `.claude/commands/quick_start/backend.md` | ~300 |
| ADW primer | `.claude/commands/quick_start/adw.md` | ~400 |
| Observability deep-dive | `.claude/commands/references/observability.md` | ~900 |
| Full architecture | `app_docs/architecture.md` | ~2,500 |

---

## When to Read This File

**You should read CLAUDE.md when:**
- Starting a new session (quick orientation on progressive loading)
- About to perform a deterministic action (commit, PR, deploy)
- Unsure which document to load (use Quick Reference Map)

**You should NOT read CLAUDE.md for:**
- Architecture details (use QUICK_REF.md)
- Coding standards (use CODE_STANDARDS.md)
- Implementation details (use quick_start/ or references/)

**This file is a router and logic gate enforcer, not a reference.**
