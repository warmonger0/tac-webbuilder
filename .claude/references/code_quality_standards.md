# Code Quality Standards

**Purpose:** Maintain clean, modular, and maintainable code across the tac-webbuilder project.

## File Organization

### File Length Limits

- **Soft Limit:** 500 lines
  - Files approaching or exceeding this should be refactored when modified
  - Warning level - address during normal development

- **Hard Limit:** 800 lines
  - Files exceeding this MUST be refactored before merging new changes
  - Blocking level - prevents merge until addressed

**Rationale:**
- Easier code review and comprehension
- Forces separation of concerns
- Reduces merge conflicts
- Improves testability and IDE performance
- Enables better modularity and reusability

### Function Length Limits

- **Soft Limit:** 100 lines
  - Functions approaching or exceeding this should be refactored
  - Extract logical units to separate functions
  - Warning level - address when touching the function

- **Hard Limit:** 300 lines
  - Functions exceeding this MUST be refactored
  - Blocking level - prevents merge until addressed
  - Exceptions require explicit justification in comments

**Rationale:**
- Single Responsibility Principle enforcement
- Easier debugging and maintenance
- Better readability and reduced cognitive load
- Simpler unit testing

### Refactoring Preference

**Modularity Over Monoliths:**
- Extract reusable logic to dedicated modules in `utils/` or shared directories
- Create logical groupings with clear boundaries
- Prefer composition over large files
- Make functions importable and reusable across features

## Naming Conventions

### Python Files and Code

**Files:**
- Use `snake_case.py` for all Python files
- Examples: `workflow_history.py`, `github_poster.py`, `nl_processor.py`

**Functions:**
- Use `snake_case()` for function names
- Be descriptive: `process_workflow_data()` not `process()`
- Avoid abbreviations unless commonly understood

**Classes:**
- Use `PascalCase` for class names
- Examples: `WorkflowAnalytics`, `PatternDetector`, `GitHubPoster`

**Constants:**
- Use `UPPER_SNAKE_CASE` for constants
- Examples: `MAX_RETRIES`, `DEFAULT_TIMEOUT`, `API_BASE_URL`

**Variables:**
- Use `snake_case` for variables
- Be descriptive: `workflow_count` not `wc`

### TypeScript/React Files and Code

**Component Files:**
- Use `PascalCase.tsx` for React components
- Examples: `WorkflowHistoryCard.tsx`, `RequestForm.tsx`, `SystemStatusPanel.tsx`

**Utility/Hook Files:**
- Use `camelCase.ts` for utilities and non-component files
- Examples: `useWebSocket.ts`, `client.ts`, `formatters.ts`

**Type Files:**
- Use `camelCase.types.ts` for type definition files
- Examples: `api.types.ts`, `workflow.types.ts`, `database.types.ts`

**Components:**
- Use `PascalCase` for component names
- Match filename: `WorkflowHistoryCard` in `WorkflowHistoryCard.tsx`

**Functions:**
- Use `camelCase()` for function names
- Examples: `fetchWorkflows()`, `formatDate()`, `calculateScore()`

**Hooks:**
- Prefix with `use` and use `camelCase`
- Examples: `useWebSocket()`, `useQueryHistory()`, `useWorkflowData()`

**Constants:**
- Use `UPPER_SNAKE_CASE` for constants
- Examples: `MAX_RETRIES`, `API_ENDPOINT`, `DEFAULT_PORT`

**Interfaces/Types:**
- Use `PascalCase` for type names
- Be specific: `WorkflowExecution`, `QueryRequest`, `ApiResponse`

## Folder Structure Conventions

### Backend Structure (app/server/)

```
app/server/
├── core/              # Core business logic (analytics, processing, etc.)
├── routes/            # API route handlers (future: extract from server.py)
├── utils/             # Shared utilities (formatters, helpers)
├── models/            # Data models and schemas
├── tests/             # Test files (mirror source structure)
│   └── core/          # Tests for core/ modules
└── server.py          # Main application entry point
```

### Frontend Structure (app/client/src/)

```
app/client/src/
├── components/        # React components
│   └── __tests__/     # Component tests (co-located)
├── hooks/             # Custom React hooks
├── api/               # API client and fetchers
├── types/             # TypeScript type definitions
│   └── index.ts       # Central type exports
├── utils/             # Shared utilities
├── stores/            # Zustand state stores
└── __tests__/         # App-level tests
```

### ADW Structure (adws/)

```
adws/
├── adw_*.py           # Main workflow scripts
├── adw_modules/       # Shared modules for workflows
├── adw_triggers/      # Webhook and trigger handlers
├── adw_tests/         # ADW-specific test utilities
└── tests/             # Workflow tests
```

## Code Organization Guidelines

### Module Extraction Rules

**When to extract to a new module:**
1. Function is used in 2+ files → Extract to `utils/`
2. Related functions form a logical group → Create dedicated module
3. File approaching 500 lines → Split by responsibility
4. Complex logic buried in larger file → Extract for clarity

**Module naming:**
- Describe what the module does, not what it contains
- Good: `formatters.py`, `validators.py`, `github_client.py`
- Bad: `helpers.py`, `utils.py`, `common.py` (too generic)

### Import Organization

**Python:**
```python
# Standard library
import os
from typing import Optional

# Third-party
from fastapi import APIRouter
import pandas as pd

# Local application
from app.server.core.workflow_analytics import calculate_score
from app.server.utils.formatters import format_date
```

**TypeScript:**
```typescript
// React and third-party
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// Types
import type { WorkflowExecution, QueryResponse } from '@/types';

// Local modules
import { fetchWorkflows } from '@/api/client';
import { formatDate } from '@/utils/formatters';
```

## Enforcement Strategy

### Non-Blocking (Warnings)

These trigger warnings but don't block merges:
- Files between 500-800 lines
- Functions between 100-300 lines
- Minor naming convention deviations

**Action:** Address when you next modify the file/function

### Blocking (Must Fix)

These MUST be addressed before merge:
- Files over 800 lines
- Functions over 300 lines
- Naming convention violations in new code
- Type naming collisions (see `typescript_standards.md`)

**Action:** Refactor immediately

### Linting Integration

**Python (Ruff):**
- Runs via: `cd app/server && uv run ruff check`
- Auto-fix: `cd app/server && uv run ruff check --fix`
- Configuration: `ruff.toml` in project root

**TypeScript (ESLint):**
- Runs via: `cd app/client && bun run lint`
- Configuration: `eslint.config.js` in `app/client/`

## Pre-Commit Checklist

Before committing code, verify:

- [ ] No files exceed 800 lines (hard limit)
- [ ] Files over 500 lines have a refactoring plan or justification
- [ ] No functions exceed 300 lines (hard limit)
- [ ] Functions over 100 lines are justified or refactored
- [ ] Naming conventions followed (snake_case Python, PascalCase components)
- [ ] Extracted reusable logic to appropriate modules
- [ ] Imports organized by category (stdlib → third-party → local)
- [ ] Type definitions follow `typescript_standards.md`
- [ ] Linting passes: `bun run lint` (frontend), `ruff check` (backend)
- [ ] TypeScript compilation: `bun tsc --noEmit`
- [ ] Tests pass: `pytest` (backend), `bun test` (frontend)

## Validation Commands

Run these before committing:

```bash
# Frontend
cd app/client
bun run lint                    # ESLint check
bun tsc --noEmit               # TypeScript compilation
bun run build                   # Production build
bun test                        # Run tests

# Backend
cd app/server
uv run ruff check              # Linting
uv run ruff format --check     # Format check
uv run pytest                  # Run tests

# Full validation
cd /Users/Warmonger0/tac/tac-webbuilder
./scripts/validate_all.sh      # (if exists)
```

## Refactoring Guidelines

### Splitting Large Files

**Step 1: Identify Logical Boundaries**
- Group related functions
- Identify dependencies
- Find natural separation points

**Step 2: Extract to Modules**
- Create appropriately named module files
- Move related functions together
- Update imports

**Step 3: Update Tests**
- Create/update test files for new modules
- Ensure test coverage maintained
- Update import paths

**Example: Splitting `server.py` (2,069 lines)**
```
server.py (2,069 lines)
↓
server.py (entry point, ~200 lines)
routes/query_routes.py (~300 lines)
routes/workflow_routes.py (~400 lines)
routes/admin_routes.py (~200 lines)
routes/websocket_routes.py (~150 lines)
```

### Extracting Long Functions

**Step 1: Identify Extraction Candidates**
- Look for logical blocks (parsing, validation, processing)
- Find code with clear inputs/outputs
- Identify reusable logic

**Step 2: Extract to Helper Functions**
- Create descriptive function names
- Keep single responsibility
- Add type hints/annotations

**Step 3: Document**
- Add docstrings explaining purpose
- Document parameters and return values
- Include usage examples if complex

## Related Documentation

- **TypeScript Standards:** `.claude/references/typescript_standards.md`
  - Type organization and naming
  - Domain-specific type files
  - Import patterns

- **Feature Planning:** `.claude/commands/feature.md`
  - How to plan features following these standards

- **Implementation:** `.claude/commands/implement.md`
  - How to implement following these standards

- **Code Review:** `.claude/commands/review.md`
  - How quality standards are verified

## Notes for AI Developers

When implementing features:

1. **Check file lengths** before adding significant code
2. **Extract functions** proactively when approaching limits
3. **Create modules** for related functionality
4. **Follow naming conventions** from the start (easier than refactoring)
5. **Run linting** after each significant change
6. **Document** why functions are long if justified (rare cases)

**Remember:** These standards exist to maintain code quality over time. Follow them during initial implementation to avoid technical debt.
