# Context Handoff: Issue #11 Onward

**Date:** 2025-11-14
**Previous Work:** Issue #8 diagnosis, fixes, and systemic improvements
**Current State:** Main branch updated with all fixes, ready for new work

---

## 🎯 Quick Context

You are working on **tac-webbuilder**, a natural language web development assistant with automated GitHub workflows.

### What Just Happened (Issue #8)

Issue #8 revealed **systemic problems** that have now been **completely fixed**:

1. ✅ **Type System** - Reorganized into domain-specific modules
2. ✅ **ADW Concurrency** - Mutex locking prevents duplicate workflows
3. ✅ **API Quota** - Pre-flight checks prevent mid-execution failures
4. ✅ **Documentation** - TypeScript standards and best practices documented

**All fixes merged to main. System is now robust and ready for new features.**

---

## 📁 Current Project State

### Repository Structure

```
tac-webbuilder/
├── app/
│   ├── client/              # React + Vite + TypeScript frontend
│   │   ├── src/
│   │   │   ├── types/       # ✨ NEW: Domain-specific type organization
│   │   │   │   ├── api.types.ts
│   │   │   │   ├── workflow.types.ts
│   │   │   │   ├── template.types.ts
│   │   │   │   ├── database.types.ts
│   │   │   │   └── index.ts
│   │   │   ├── components/
│   │   │   │   ├── HistoryAnalytics.tsx  # ✨ NEW: From PR #10
│   │   │   │   └── ...
│   │   │   └── api/client.ts  # ✨ UPDATED: Added quota/cost functions
│   │   └── ...
│   └── server/              # FastAPI + Python backend
│       ├── core/
│       │   ├── adw_lock.py       # ✨ NEW: Concurrency control
│       │   ├── api_quota.py      # ✨ NEW: Quota monitoring
│       │   └── ...
│       ├── tests/
│       │   └── test_workflow_history.py  # ✨ NEW: 375 lines from PR #10
│       └── ...
├── adws/                    # ADW workflow automation
│   ├── adw_triggers/
│   │   └── trigger_webhook.py  # ✨ UPDATED: Lock + quota integration
│   └── ...
├── docs/
│   ├── ISSUE_8_PR_COMPARISON.md  # ✨ NEW: Detailed analysis
│   └── ...
└── .claude/
    └── references/
        └── typescript_standards.md  # ✨ NEW: Type system guide
```

### Key Technologies

- **Frontend:** React 18, Vite, TypeScript, Tailwind, TanStack Query, Zustand
- **Backend:** FastAPI, Python, SQLite, OpenAI/Anthropic APIs
- **ADW:** Isolated git worktrees, Claude Code CLI automation

---

## 🔑 Critical Concepts

### 1. Type System (IMPORTANT!)

**Always use domain-specific types:**

```typescript
// ✅ Correct
import { WorkflowExecution, WorkflowTemplate } from '@/types';

// ❌ Wrong (old pattern)
import { Workflow } from '../types';  // Ambiguous!
```

**Type Categories:**
- `WorkflowExecution` - Active workflow state (adw_id, phase, status)
- `WorkflowTemplate` - Workflow definitions (name, script_name, category)
- `api.types.ts` - API request/response types
- `database.types.ts` - Database schema types

**See:** `.claude/references/typescript_standards.md` for full guide

### 2. ADW Concurrency Control

**Before starting new workflows:**

```python
from core.adw_lock import acquire_lock, release_lock

# Try to acquire lock
if not acquire_lock(issue_number, adw_id):
    print(f"Issue #{issue_number} already locked by another ADW")
    return False

# Do work...

# Always release lock when done
release_lock(issue_number, adw_id)
```

**Database Schema:**
```sql
CREATE TABLE adw_locks (
    issue_number INTEGER PRIMARY KEY,
    adw_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. API Quota Monitoring

**Before launching ADWs:**

```python
from core.api_quota import can_start_adw, should_skip_e2e_tests

# Check quota before starting
can_proceed, error_msg = can_start_adw()
if not can_proceed:
    print(f"Cannot start: {error_msg}")
    return False

# During testing phase
skip_e2e, reason = should_skip_e2e_tests()
if skip_e2e:
    print(f"Skipping E2E tests: {reason}")
```

**Auto-integrated in:** `adws/adw_triggers/trigger_webhook.py`

---

## 📝 Important Files to Know

### Frontend

- **`app/client/src/types/`** - All TypeScript types (domain-organized)
- **`app/client/src/api/client.ts`** - API client with all endpoints
- **`app/client/src/components/`** - React components
  - `HistoryAnalytics.tsx` - New analytics component
  - `WorkflowCard.tsx` - Shows active workflows
  - `WorkflowDashboard.tsx` - Workflow catalog

### Backend

- **`app/server/core/adw_lock.py`** - Concurrency control (NEW)
- **`app/server/core/api_quota.py`** - Quota monitoring (NEW)
- **`app/server/core/data_models.py`** - Pydantic models
- **`app/server/tests/test_workflow_history.py`** - Comprehensive tests (NEW)

### ADW Workflows

- **`adws/adw_triggers/trigger_webhook.py`** - Webhook handler (UPDATED)
- **`adws/adw_plan_build_test_iso.py`** - Full SDLC workflow
- **`adws/adw_patch_iso.py`** - Quick patch workflow

### Documentation

- **`docs/ISSUE_8_PR_COMPARISON.md`** - PR analysis & lessons learned
- **`.claude/references/typescript_standards.md`** - Type system guide
- **`.claude/commands/quick_start/`** - Subsystem quick starts

---

## ⚡ Recent Changes (Last 24 Hours)

### Commits on Main

1. **`686c193`** - Type system refactor (domain-specific)
2. **`65c520f`** - Cherry-picked components from PR #10
3. **`5a828ea`** - ADW concurrency + API quota monitoring
4. **`b2cd47f`** - Documentation (standards + analysis)

### What Changed

**Type System:**
- `types.ts` & `types.d.ts` → DELETED
- New: `types/api.types.ts`, `types/workflow.types.ts`, etc.
- `Workflow` renamed to `WorkflowExecution` throughout

**New Modules:**
- `core/adw_lock.py` - Mutex locking for ADW workflows
- `core/api_quota.py` - Quota monitoring functions
- `test_workflow_history.py` - 375 lines of tests

**Updated Modules:**
- `adws/adw_triggers/trigger_webhook.py` - Added lock + quota checks
- `app/client/src/api/client.ts` - Added missing functions + namespace export

---

## 🚀 Starting Fresh with Issue #11+

### Pre-Flight Checklist

Before working on new issues:

1. ✅ **TypeScript Compilation** - Always run `npx tsc --noEmit` before committing
2. ✅ **Use Correct Types** - Import from `@/types` with specific names
3. ✅ **Check ADW Locks** - System auto-handles, but be aware
4. ✅ **Monitor Quotas** - System auto-checks before workflows

### Common Commands

```bash
# Frontend
cd app/client
bun run dev          # Start dev server (port 5173)
npx tsc --noEmit     # Type check without building

# Backend
cd app/server
uv run python server.py  # Start server (port 8000)
uv run pytest        # Run tests

# Full Stack
./scripts/start_full.sh  # Start both backend + frontend

# ADW Workflows
cd adws
uv run adw_plan_build_test_iso.py <issue_number>
```

### Where to Find Things

**Need to understand subsystem?**
- Read `.claude/commands/quick_start/<subsystem>.md` first
- Then `.claude/references/<topic>.md` if needed

**Need architecture context?**
- `docs/features/adw/technical-overview.md` - ADW system design
- `docs/REALTIME_WEBSOCKET_IMPLEMENTATION.md` - WebSocket patterns
- `.claude/references/decision_tree.md` - Routing guide

---

## 🎓 Key Learnings from Issue #8

### What to Do

✅ **Use domain-specific types** - Prevent naming collisions
✅ **Check for existing locks** - System handles automatically
✅ **Monitor API quotas** - System checks before workflows
✅ **Run TypeScript checks** - Before every commit
✅ **Cherry-pick best components** - Review all PRs for quality

### What NOT to Do

❌ **Don't use ambiguous type names** - `Workflow` is now `WorkflowExecution`
❌ **Don't bypass lock checks** - Respect concurrency control
❌ **Don't ignore quota warnings** - System won't start if exhausted
❌ **Don't create monolithic components** - Keep them modular
❌ **Don't skip tests** - We have 375 lines of test coverage now

---

## 🔍 Quick Debugging

### TypeScript Errors?

```bash
cd app/client
npx tsc --noEmit  # See all errors
```

**Common fix:** Update imports to use new type paths:
```typescript
import { WorkflowExecution } from '@/types';  # Not from '../types'
```

### ADW Won't Start?

Check logs for:
- `[ADW Lock] Issue #X already locked` → Another workflow active
- `[API Quota] Cannot start` → Quota exhausted (wait for reset)

### Database Errors?

```bash
cd app/server
sqlite3 db/database.db ".schema adw_locks"  # Check lock table exists
```

---

## 📋 Active PRs & Issues

### Open PRs

- **PR #12** - Still open from issue #8 (can be updated with main branch fixes)

### Closed Issues

- **Issue #8** - ✅ Closed (systemic fixes completed)

### Next Issues

- **Issue #11+** - Ready to work on with improved codebase

---

## 💡 Recommended Next Steps

### If Working on Issue #11+

1. Read this handoff document
2. Check `.claude/commands/quick_start/<relevant-subsystem>.md`
3. Review `docs/ISSUE_8_PR_COMPARISON.md` for context on what not to do
4. Start work with confidence - all systemic issues fixed!

### If Updating PR #12

1. Rebase onto main: `git rebase origin/main`
2. Resolve conflicts using new type system
3. Run `npx tsc --noEmit` to verify
4. Update PR description with fixes applied

---

## 🎯 Context Summary for New Session

**TL;DR for Claude:**

"You're working on tac-webbuilder. Issue #8 just got resolved after fixing systemic TypeScript type conflicts, implementing ADW concurrency locks, and adding API quota monitoring. The type system is now organized into domain-specific modules (`types/api.types.ts`, `types/workflow.types.ts`, etc.). All fixes are merged to main. The codebase is robust and ready for new work on issue #11+. Key changes: `Workflow` → `WorkflowExecution`, new `adw_lock.py` and `api_quota.py` modules, comprehensive test suite added. See `.claude/references/typescript_standards.md` for type guidelines."

---

**Ready to tackle issue #11 with a clean, well-documented, and robust codebase!**

🤖 Generated: 2025-11-14
📝 Context handoff from Issue #8 resolution
