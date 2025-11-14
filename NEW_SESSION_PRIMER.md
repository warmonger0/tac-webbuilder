# New Session Context Primer

**Paste this at the start of your new Claude Code session for issue #11+**

---

## 🎯 Quick Context

Working on **tac-webbuilder** - NL web development assistant with automated GitHub workflows.

**Previous Session:** Fixed systemic issues from issue #8 (TypeScript type conflicts, ADW concurrency, API quotas)

**Current State:** All fixes merged to main. Codebase is robust and ready for issue #11+.

---

## ⚡ What You Need to Know

### 1. Type System (CRITICAL!)

✅ **Always import from domain-specific types:**

```typescript
// Correct
import { WorkflowExecution, WorkflowTemplate } from '@/types';

// Wrong (old pattern - REMOVED)
import { Workflow } from '../types';  // ❌ File doesn't exist anymore!
```

**Key type files:**
- `app/client/src/types/api.types.ts` - API requests/responses
- `app/client/src/types/workflow.types.ts` - `WorkflowExecution` (active workflows)
- `app/client/src/types/template.types.ts` - `WorkflowTemplate` (workflow catalog)
- `app/client/src/types/database.types.ts` - Database schemas

**See:** `.claude/references/typescript_standards.md`

### 2. New Modules (Added in Last Session)

**Backend:**
- `app/server/core/adw_lock.py` - Prevents concurrent ADWs on same issue
- `app/server/core/api_quota.py` - Pre-flight quota checks
- `app/server/tests/test_workflow_history.py` - 375 lines of tests

**Updated:**
- `adws/adw_triggers/trigger_webhook.py` - Auto lock + quota checking
- `app/client/src/api/client.ts` - New functions + namespace export

### 3. Recent Commits (Last 4)

```
da77e84 - docs: Add context handoff for issue #11 onward
b2cd47f - docs: Add TypeScript standards and issue #8 analysis
5a828ea - feat: Add ADW concurrency locking and API quota monitoring
65c520f - feat: Cherry-pick best components from PR #10 for issue #8
686c193 - refactor: Reorganize TypeScript types into domain-specific modules
```

---

## 📚 Documentation

**Start here for subsystems:**
- `.claude/commands/quick_start/frontend.md` - React/TypeScript frontend
- `.claude/commands/quick_start/backend.md` - FastAPI/Python backend
- `.claude/commands/quick_start/adw.md` - ADW workflow automation

**Deep dives:**
- `docs/CONTEXT_HANDOFF_ISSUE_11.md` - Full context from previous session
- `docs/ISSUE_8_PR_COMPARISON.md` - What went wrong + how we fixed it
- `.claude/references/typescript_standards.md` - Type organization guide

---

## 🚀 Quick Start Commands

```bash
# Frontend
cd app/client
npx tsc --noEmit     # ALWAYS run before committing!
bun run dev          # Dev server (port 5173)

# Backend
cd app/server
uv run python server.py   # API server (port 8000)
uv run pytest             # Run tests

# Full Stack
./scripts/start_full.sh   # Both servers

# Check what's changed
git log --oneline -10     # Recent commits
git status                # Current state
```

---

## ⚠️ Important Changes from Previous Session

### Type System Reorganized

**Before (OLD - DON'T USE):**
```typescript
import { Workflow } from '../types';  // DELETED!
```

**After (NEW - USE THIS):**
```typescript
import { WorkflowExecution } from '@/types';  // Correct!
```

### New Safeguards in Place

✅ **ADW Concurrency** - Only 1 ADW per issue (automatic via `adw_lock.py`)
✅ **API Quota** - Pre-flight checks prevent mid-execution failures
✅ **TypeScript Checks** - Must pass before committing

---

## 🎯 Working on Issue #11+

### Pre-Flight

1. Read this primer
2. Check `.claude/commands/quick_start/<subsystem>.md`
3. Review `docs/CONTEXT_HANDOFF_ISSUE_11.md` if needed
4. Start coding!

### During Development

- Run `npx tsc --noEmit` frequently
- Use domain-specific types from `@/types`
- System handles ADW locks & quotas automatically

### Before Committing

```bash
cd app/client
npx tsc --noEmit  # Must pass!

cd ../server
uv run pytest     # All tests pass
```

---

## 📊 Issue Status

- **Issue #8** - ✅ CLOSED (systemic fixes completed)
- **PR #9, #10** - ✅ CLOSED (components cherry-picked)
- **PR #12** - ⏸️ OPEN (can update with main branch fixes)
- **Issue #11+** - 🎯 READY TO START

---

## 🔍 Quick Reference

### File Structure

```
app/client/src/
├── types/           # ✨ NEW: Domain-specific types
│   ├── api.types.ts
│   ├── workflow.types.ts
│   ├── template.types.ts
│   └── index.ts
├── components/
│   └── HistoryAnalytics.tsx  # ✨ NEW: From PR #10
└── api/client.ts    # ✨ UPDATED: New functions

app/server/core/
├── adw_lock.py      # ✨ NEW: Concurrency control
└── api_quota.py     # ✨ NEW: Quota monitoring
```

### Key Concepts

- **WorkflowExecution** - Active workflow (adw_id, phase, status)
- **WorkflowTemplate** - Workflow definition (name, script_name, category)
- **ADW Lock** - Prevents concurrent workflows on same issue
- **Quota Check** - Validates API availability before workflows

---

## ✅ TL;DR

**You're ready to work on issue #11+ with:**
- ✅ Fixed type system (domain-organized)
- ✅ ADW concurrency control (auto-handled)
- ✅ API quota monitoring (auto-checked)
- ✅ Comprehensive tests (375 lines)
- ✅ Clear documentation (standards + guides)

**Just remember:** Use `WorkflowExecution` not `Workflow`, import from `@/types`, and run `npx tsc --noEmit` before committing!

**Full details:** `docs/CONTEXT_HANDOFF_ISSUE_11.md`

---

🤖 **Ready to code!**
