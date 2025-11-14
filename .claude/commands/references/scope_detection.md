# Scope Detection Reference

**Purpose:** Detect task scope to minimize context loading
**When to use:** Before implementing features, when analyzing issues
**Token savings:** 50-90% depending on scope

---

## Scope Types

### Frontend-only
**Keywords:** app/client, React, UI, component, frontend, .tsx, CSS, Tailwind, Vite
**Load:**
- `app/client/**/*.{ts,tsx,css}`
- `app/client/package.json`
**Skip:** app/server/**, adws/**, scripts/**
**Savings:** ~60%

### Backend-only
**Keywords:** app/server, API, FastAPI, database, backend, .py, SQLite, routes
**Load:**
- `app/server/**/*.py`
- `app/server/pyproject.toml`
**Skip:** app/client/**, adws/**, scripts/**
**Savings:** ~50%

### Documentation
**Keywords:** docs, README, markdown, documentation, .md
**Load:**
- `docs/**/*.md`
- `*.md` (root level)
**Skip:** app/**, adws/**, scripts/**
**Savings:** ~90%

### Scripts
**Keywords:** scripts/, shell, bash, .sh, automation, setup
**Load:**
- `scripts/**/*.{sh,py}`
**Skip:** app/**, adws/**, docs/**
**Savings:** ~80%

### ADW Workflows
**Keywords:** adws/, workflow, ADW, automation, agent
**Load:**
- `adws/**/*.py`
- `.claude/commands/**/*.md`
**Skip:** app/**, scripts/**
**Savings:** ~70%

### Full-stack
**Keywords:** multiple subsystems, integration, end-to-end, full-stack
**Load:** All relevant subsystems
**Savings:** Use conditional docs

---

## Usage

When implementing a task:
1. Analyze task description for keywords
2. Identify dominant scope
3. Load only files matching that scope
4. Reference this doc if uncertain
