# TypeScript Standards & Type Organization

## Type System Architecture

### Directory Structure

```
app/client/src/types/
├── index.ts              # Central export point
├── api.types.ts          # API request/response types
├── database.types.ts     # Database schema types
├── workflow.types.ts     # Workflow execution types
├── template.types.ts     # Workflow template catalog types
└── [feature].types.ts    # Feature-specific types
```

### Naming Conventions

#### Avoid Naming Collisions

**Problem:** Using the same name for different concepts causes conflicts.

❌ **Bad:**
```typescript
// types.ts
interface Workflow { /* active execution */ }

// types.d.ts
interface Workflow { /* template catalog */ }
```

✅ **Good:**
```typescript
// workflow.types.ts
interface WorkflowExecution { /* active execution */ }

// template.types.ts
interface WorkflowTemplate { /* template catalog */ }
```

#### Use Descriptive Names

- **Active state:** `WorkflowExecution`, `UserSession`, `ActiveRequest`
- **Templates/Definitions:** `WorkflowTemplate`, `UserProfile`, `RequestTemplate`
- **Responses:** `WorkflowResponse`, `UserResponse`, `RequestResponse`
- **Requests:** `WorkflowRequest`, `UserRequest`, `SubmitRequest`

### Import Patterns

#### Centralized Imports (Preferred)

```typescript
import type { QueryResponse, WorkflowExecution, WorkflowTemplate } from '@/types';
```

#### Domain-Specific Imports (When Needed)

```typescript
import type { QueryResponse } from '@/types/api.types';
import type { WorkflowExecution } from '@/types/workflow.types';
```

### File Organization

#### 1. API Types (`api.types.ts`)

Types for HTTP request/response communication.

```typescript
export interface QueryRequest {
  query: string;
  llm_provider: "openai" | "anthropic";
}

export interface QueryResponse {
  sql: string;
  results: Record<string, any>[];
  columns: string[];
}
```

#### 2. Database Types (`database.types.ts`)

Types representing database structures.

```typescript
export interface TableSchema {
  name: string;
  columns: ColumnInfo[];
  row_count: number;
}
```

#### 3. Workflow Types (`workflow.types.ts`)

Types for active workflow state/execution.

```typescript
export interface WorkflowExecution {
  adw_id: string;
  issue_number: number;
  phase: string;
  github_url: string;
}
```

#### 4. Template Types (`template.types.ts`)

Types for workflow definitions/catalog.

```typescript
export interface WorkflowTemplate {
  name: string;
  script_name: string;
  description: string;
  category: "single-phase" | "multi-phase" | "full-sdlc";
}
```

### Type Exports

#### Central Export File (`index.ts`)

```typescript
// Re-export all types for convenient imports
export * from './api.types';
export * from './database.types';
export * from './workflow.types';
export * from './template.types';
```

### Common Patterns

#### Discriminated Unions

```typescript
type WebSocketMessage =
  | { type: 'workflows_update'; data: WorkflowExecution[] }
  | { type: 'routes_update'; data: Route[] }
  | { type: 'error'; message: string };
```

#### Optional Fields

```typescript
export interface HistoryItem {
  id: string;
  nl_input: string;
  status: string;
  issue_number?: number;  // Optional
  github_url?: string;    // Optional
}
```

#### Generic Types

```typescript
export interface ApiResponse<T> {
  data: T;
  error?: string;
  metadata?: {
    timestamp: string;
    duration_ms: number;
  };
}
```

## Pre-Commit Checklist

Before committing code that modifies types:

- [ ] TypeScript compilation passes (`npx tsc --noEmit`)
- [ ] No duplicate type names across different files
- [ ] Types are in appropriate domain-specific files
- [ ] Central `index.ts` exports all new types
- [ ] No unused type imports
- [ ] Type names clearly describe their purpose

## Migration Guide

### Moving from Monolithic to Domain-Specific Types

**Step 1:** Create domain-specific type files
```bash
mkdir -p src/types
touch src/types/{api,database,workflow,template,index}.types.ts
```

**Step 2:** Categorize existing types by domain
- API request/response → `api.types.ts`
- Database structures → `database.types.ts`
- Active state/execution → `workflow.types.ts`
- Templates/definitions → `template.types.ts`

**Step 3:** Update imports throughout codebase
```typescript
// Before
import type { Workflow } from '../types';

// After
import type { WorkflowExecution } from '../types';
```

**Step 4:** Delete old type files
```bash
rm src/types.ts src/types.d.ts
```

**Step 5:** Verify compilation
```bash
npx tsc --noEmit
```

## Lessons Learned from Issue #8

### Problem
Multiple ADW workflows failed due to type naming collision:
- `types.ts` defined `Workflow` for active executions
- `types.d.ts` defined `Workflow` for template catalog
- TypeScript couldn't resolve which definition to use

### Solution
1. Renamed types to reflect their purpose:
   - `Workflow` (executions) → `WorkflowExecution`
   - `WorkflowTemplate` (catalog) - kept as-is
2. Organized types into domain-specific files
3. Created centralized export point

### Prevention
- One type name = one concept
- Domain-specific organization prevents overlap
- TypeScript compilation as pre-commit check

## Best Practices

1. **Single Responsibility:** Each type file covers one domain
2. **Explicit Naming:** Type names should be unambiguous
3. **Central Exports:** Always export through `index.ts`
4. **No Ambient Declarations:** Avoid `.d.ts` files for application types (use for third-party declarations only)
5. **Compilation Verification:** Run `npx tsc --noEmit` before committing
