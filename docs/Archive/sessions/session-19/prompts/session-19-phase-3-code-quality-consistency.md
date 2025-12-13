# Session 19 - Phase 3: Code Quality & Consistency Implementation

## Context
I'm working on the tac-webbuilder project. The architectural consistency analysis identified inconsistent patterns across frontend and backend code - 4 different repository naming conventions, mixed data fetching patterns, and inconsistent error handling. This phase standardizes these patterns for better maintainability and code quality.

## Objectives
Implement 4 improvements to standardize repository methods, frontend data fetching, UI components, and error handling across the codebase.

## Background Information
**Analysis Source**: Multi-agent architectural consistency review (Session 19)
**Priority Level**: MEDIUM - Code quality and maintainability
**Estimated Time**: 16 hours total (can be split into 4 sub-tasks)
**Risk Level**: Medium - Refactoring affects multiple files but patterns are well-tested
**Dependencies**: Phases 1 & 2 must be complete

## Current Inconsistency Problems

### Problem 1: Repository Method Naming (INCONSISTENT)

| Repository | Create Method | Get Method | Delete Method |
|-----------|---------------|------------|---------------|
| PhaseQueueRepository | `insert_phase()` | `find_by_id()` | `delete_phase()` |
| WorkLogRepository | `create_entry()` | `get_all()` | `delete_entry()` |
| TaskLogRepository | `create()` | `get_by_adw_id()` | (none) |
| UserPromptRepository | `create()` | `get_by_request_id()` | (none) |

**Issue**: 4 different naming conventions for same operations

### Problem 2: Frontend Data Fetching (MIXED)

- **Pattern A**: TanStack Query `useQuery` (20+ uses) - RECOMMENDED
- **Pattern B**: Manual `fetch()` + `useState` (ContextReviewPanel, HistoryView)
- **Pattern C**: WebSocket hooks (already standardized)

**Issue**: Manual fetch has more boilerplate, no cache management, inconsistent error handling

### Problem 3: UI Components (DUPLICATED)

Repeated patterns across panels:
- Loading states: 5+ different implementations
- Error displays: 3+ different styles
- Confirmation dialogs: Toast-based, inconsistent

**Issue**: Code duplication, visual inconsistency

### Problem 4: Error Handling (INCONSISTENT)

Frontend has 3 different error handling patterns:
- ReviewPanel: `setMutationError()` + console.error
- LogPanel: Similar but different state names
- ContextReviewPanel: `setError()` with different format

**Issue**: Inconsistent user experience, harder to maintain

---

## Phase 3 Tasks Overview

### Task 3.1: Standardize Repository Method Naming (6 hours)
**Files:**
- `app/server/repositories/phase_queue_repository.py`
- `app/server/repositories/work_log_repository.py`
- `app/server/repositories/task_log_repository.py`
- `app/server/repositories/user_prompt_repository.py`
- All services that call these repositories

**Target Standard:**
```python
# CRUD operations
create(item)           # Was: insert_phase, create_entry
get_by_id(id)         # Was: find_by_id, get_by_*
get_by_<field>(val)   # Was: find_by_*, get_by_*
get_all(limit, offset) # Was: find_all, get_all
update(id, data)      # Consistent across all
delete(id)            # Was: delete_phase, delete_entry
```

### Task 3.2: Migrate Manual Fetch to useQuery (3 hours)
**Files:**
- `app/client/src/components/context-review/ContextReviewPanel.tsx`
- `app/client/src/components/HistoryView.tsx`

**Target Pattern:**
```typescript
// Replace manual fetch + useState
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['context-review', reviewId],
  queryFn: () => fetchAnalysis(reviewId),
  refetchInterval: 3000,  // If polling needed
  enabled: !!reviewId,
});
```

### Task 3.3: Create Reusable UI Components (5 hours)
**New Files:**
- `app/client/src/components/common/LoadingState.tsx`
- `app/client/src/components/common/ErrorBanner.tsx`
- `app/client/src/components/common/ConfirmationDialog.tsx`

**Replace 20+ instances** of duplicate loading/error/confirmation code

### Task 3.4: Standardize Frontend Error Handling (2 hours)
**New File:**
- `app/client/src/utils/errorHandler.ts`

**Update all panels** to use consistent error formatting

---

## Multi-Part Implementation Approach

This phase should be implemented in **4 sequential parts**:

### Part 1: Standardize Repository Naming
- Estimated: 6 hours
- Risk: Medium (many callers to update)
- Dependencies: None
- **Do First** - Backend changes, comprehensive tests

### Part 2: Migrate to useQuery
- Estimated: 3 hours
- Risk: Low (isolated to 2 components)
- Dependencies: None
- **Do Second** - Frontend improvements

### Part 3: Create Reusable UI Components
- Estimated: 5 hours
- Risk: Low (additive, doesn't break existing)
- Dependencies: None
- **Do Third** - Largest frontend task

### Part 4: Standardize Error Handling
- Estimated: 2 hours
- Risk: Low (uses components from Part 3)
- Dependencies: Part 3 (ErrorBanner component)
- **Do Last** - Ties everything together

---

## PART 1: Standardize Repository Method Naming

### Step 1.1: Define Standard Naming Convention

**File:** `docs/backend/repository-standards.md` (NEW)

```markdown
# Repository Naming Standards

All repository classes MUST follow this naming convention for consistency and maintainability.

## Standard Method Names

### Create
```python
def create(self, item: ModelCreate) -> Model:
    """Create a new record.

    Args:
        item: Pydantic model with creation data

    Returns:
        Created model with ID populated
    """
```

### Read (Single Record)
```python
def get_by_id(self, id: int) -> Optional[Model]:
    """Get single record by primary key.

    Args:
        id: Primary key value

    Returns:
        Model if found, None otherwise
    """
```

### Read (By Field)
```python
def get_by_<field>(self, value: Any) -> Optional[Model]:
    """Get single record by unique field.

    Args:
        value: Field value to search for

    Returns:
        Model if found, None otherwise
    """

# For one-to-many relationships
def get_all_by_<field>(self, value: Any, limit: int = 100) -> List[Model]:
    """Get all records matching field value.

    Args:
        value: Field value to filter by
        limit: Maximum records to return

    Returns:
        List of matching models
    """
```

### Read (All)
```python
def get_all(self, limit: int = 100, offset: int = 0) -> List[Model]:
    """Get all records with pagination.

    Args:
        limit: Maximum records to return
        offset: Number of records to skip

    Returns:
        List of models
    """
```

### Update
```python
def update(self, id: int, data: ModelUpdate) -> Optional[Model]:
    """Update existing record.

    Args:
        id: Primary key of record to update
        data: Pydantic model with update data

    Returns:
        Updated model if found, None otherwise
    """
```

### Delete
```python
def delete(self, id: int) -> bool:
    """Delete record by primary key.

    Args:
        id: Primary key of record to delete

    Returns:
        True if deleted, False if not found
    """
```

### Custom Queries
```python
def find_<custom_criteria>(self, ...) -> List[Model]:
    """Custom query with descriptive name.

    Use 'find_' prefix for complex queries that don't fit
    standard patterns.

    Examples:
    - find_ready_phases()
    - find_pending_with_priority()
    - find_expired_sessions()
    """
```

## Migration Checklist

When renaming methods:
1. ✅ Update repository method name
2. ✅ Update all service callers
3. ✅ Update all route callers
4. ✅ Update tests
5. ✅ Run full test suite
6. ✅ Commit with clear migration message

## Examples

### Before (Inconsistent)
```python
class PhaseQueueRepository:
    def insert_phase(self, item): ...
    def find_by_id(self, id): ...
    def delete_phase(self, id): ...

class WorkLogRepository:
    def create_entry(self, item): ...
    def get_all(self): ...
    def delete_entry(self, id): ...
```

### After (Consistent)
```python
class PhaseQueueRepository:
    def create(self, item): ...
    def get_by_id(self, id): ...
    def delete(self, id): ...

class WorkLogRepository:
    def create(self, item): ...
    def get_all(self, limit, offset): ...
    def delete(self, id): ...
```
```

### Step 1.2: Rename PhaseQueueRepository Methods

**File:** `app/server/repositories/phase_queue_repository.py`

**Renames needed:**
- `insert_phase()` → `create()`
- `find_by_id()` → `get_by_id()`
- `find_by_parent()` → `get_all_by_parent_issue()`
- `find_all()` → `get_all()`
- `delete_phase()` → `delete()`

**Example:**
```python
# Before
def insert_phase(self, item: PhaseQueueItem) -> int:
    """Insert new phase queue item."""
    # ... implementation ...

# After
def create(self, item: PhaseQueueItem) -> PhaseQueueItem:
    """Create new phase queue item.

    Args:
        item: Phase queue item to create

    Returns:
        Created item with queue_id populated
    """
    # ... implementation (same) ...
```

### Step 1.3: Update All Callers

**Search for all callers:**
```bash
cd app/server

# Find all insert_phase calls
grep -r "insert_phase" services/ routes/ --include="*.py"

# Find all find_by_id calls (phase_queue context)
grep -r "\.find_by_id" services/ routes/ --include="*.py" | grep phase_queue

# Find all delete_phase calls
grep -r "delete_phase" services/ routes/ --include="*.py"
```

**Update pattern:**
```python
# Before
queue_id = phase_queue_repository.insert_phase(item)

# After
created_item = phase_queue_repository.create(item)
queue_id = created_item.queue_id
```

**Files likely to update:**
- `app/server/services/phase_queue_service.py`
- `app/server/services/phase_dependency_tracker.py`
- `app/server/routes/queue_routes.py`

### Step 1.4: Repeat for Other Repositories

**WorkLogRepository:**
- `create_entry()` → `create()`
- `delete_entry()` → `delete()`

**TaskLogRepository:**
- Already uses `create()` ✅
- Rename: `get_by_adw_id()` → consistent (keep as-is, follows standard)

**UserPromptRepository:**
- Already uses `create()` ✅
- Already uses `get_by_*()` pattern ✅

### Step 1.5: Update Tests

```bash
cd app/server

# Update test files
grep -r "insert_phase\|create_entry\|delete_phase\|delete_entry" tests/ --include="*.py"

# Update each test file with new method names
```

### Step 1.6: Run Full Test Suite

```bash
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest -v

# All tests should pass
```

### Step 1.7: Commit Repository Standardization

```bash
git add app/server/repositories/
git add app/server/services/
git add app/server/routes/
git add app/server/tests/
git add docs/backend/repository-standards.md

git commit -m "$(cat <<'EOF'
refactor: Standardize repository method naming conventions

Aligned all repositories to consistent CRUD naming pattern.

Standard Methods:
- create(item) - Create new record
- get_by_id(id) - Get by primary key
- get_by_<field>(value) - Get by unique field
- get_all(limit, offset) - Get all with pagination
- update(id, data) - Update existing
- delete(id) - Delete by ID
- find_<criteria>() - Custom queries

Renamed Methods:
- PhaseQueueRepository:
  - insert_phase() → create()
  - find_by_id() → get_by_id()
  - find_by_parent() → get_all_by_parent_issue()
  - find_all() → get_all()
  - delete_phase() → delete()

- WorkLogRepository:
  - create_entry() → create()
  - delete_entry() → delete()

Updated:
- All service callers (phase_queue_service, etc.)
- All route callers (queue_routes, work_log_routes, etc.)
- All tests

Benefits:
- Consistent API across all repositories
- Easier to learn and maintain
- Clear naming conventions documented
- Reduced cognitive load

Session 19 - Phase 3, Part 1/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 2: Migrate Manual Fetch to useQuery

### Step 2.1: Migrate ContextReviewPanel

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

**Current code (lines 44-81):**
```typescript
// Manual fetch with useState
const [analysis, setAnalysis] = useState<ContextAnalysis | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const fetchAnalysis = async () => {
  setIsLoading(true);
  setError(null);
  try {
    const reviewResponse = await fetch(`/api/v1/context-review/${reviewId}`);
    if (!reviewResponse.ok) throw new Error('Failed to fetch analysis');
    const reviewData = await reviewResponse.json();
    setAnalysis(reviewData);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error');
  } finally {
    setIsLoading(false);
  }
};

// Manual polling
useEffect(() => {
  let pollInterval: NodeJS.Timeout | null = null;
  if (analysis?.status === 'analyzing') {
    pollInterval = setInterval(fetchAnalysis, 3000);
  }
  return () => {
    if (pollInterval) clearInterval(pollInterval);
  };
}, [analysis?.status]);
```

**New code (useQuery pattern):**
```typescript
import { useQuery } from '@tanstack/react-query';

// API client function
const fetchAnalysis = async (reviewId: string): Promise<ContextAnalysis> => {
  const response = await fetch(`/api/v1/context-review/${reviewId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch analysis');
  }
  return response.json();
};

// Component
const ContextReviewPanel: React.FC<Props> = ({ reviewId }) => {
  const {
    data: analysis,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['context-review', reviewId],
    queryFn: () => fetchAnalysis(reviewId),
    refetchInterval: (data) => {
      // Poll every 3s while analyzing, stop when complete
      return data?.status === 'analyzing' ? 3000 : false;
    },
    enabled: !!reviewId,
  });

  // Remove manual useState, useEffect, and fetchAnalysis function
  // TanStack Query handles everything automatically
```

**Benefits:**
- Automatic polling control (stops when status !== 'analyzing')
- Built-in error handling
- Automatic cache management
- Less boilerplate code (removed ~40 lines)

### Step 2.2: Migrate HistoryView

**File:** `app/client/src/components/HistoryView.tsx`

**Current code (lines 12-20):**
```typescript
const {
  data: history,
  isLoading,
  error,
} = useQuery({
  queryKey: ['history'],
  queryFn: () => getHistory(intervals.components.workflowHistory.defaultLimit),
  refetchInterval: 30000, // 30s polling
});
```

**Issue**: Already uses useQuery, but should use WebSocket instead!

**New code (use WebSocket):**
```typescript
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';

const HistoryView: React.FC = () => {
  const {
    workflowHistory,
    analytics,
    isConnected,
    connectionQuality,
    lastUpdated
  } = useWorkflowHistoryWebSocket();

  // Remove useQuery completely - WebSocket provides real-time updates
  // No polling needed!

  if (!isConnected) {
    return <div>Connecting to real-time updates...</div>;
  }

  return (
    <div>
      {/* Use workflowHistory from WebSocket */}
      {workflowHistory.map(workflow => (
        <WorkflowCard key={workflow.id} workflow={workflow} />
      ))}
    </div>
  );
};
```

**Benefits:**
- Real-time updates instead of 30-second polling
- Consistent with other panels (already using WebSockets)
- Better user experience (<2s latency vs 30s)

### Step 2.3: Test Data Fetching

```bash
cd app/client

# Run tests
bun test ContextReviewPanel.test.tsx
bun test HistoryView.test.tsx

# Manual test
bun run dev
# Visit panels and verify:
# - ContextReviewPanel loads data correctly
# - Polling stops when analysis completes
# - HistoryView shows real-time updates
```

### Step 2.4: Commit Data Fetching Migration

```bash
git add app/client/src/components/context-review/ContextReviewPanel.tsx
git add app/client/src/components/HistoryView.tsx

git commit -m "$(cat <<'EOF'
refactor: Migrate manual fetch to useQuery/WebSocket patterns

Standardized data fetching across frontend components.

Changes:
- ContextReviewPanel: Manual fetch → useQuery
  - Removed 40+ lines of boilerplate
  - Automatic polling control (3s while analyzing)
  - Built-in cache management
  - Consistent error handling

- HistoryView: HTTP polling → WebSocket
  - Removed 30-second polling (was useQuery)
  - Real-time updates via useWorkflowHistoryWebSocket
  - <2s latency instead of 30s
  - Consistent with other panels

Benefits:
- Less code to maintain
- Better user experience (real-time updates)
- Automatic cache deduplication
- Consistent patterns across app
- NO POLLING (as mandated)

Session 19 - Phase 3, Part 2/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 3: Create Reusable UI Components

### Step 3.1: Create LoadingState Component

**File:** `app/client/src/components/common/LoadingState.tsx` (NEW)

```typescript
import React from 'react';

interface LoadingStateProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

/**
 * Standardized loading state component with spinner.
 *
 * Usage:
 *   <LoadingState message="Loading data..." />
 *   <LoadingState size="small" />
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
  size = 'medium',
  className = '',
}) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <div
        className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="mt-4 text-sm text-gray-600">{message}</p>
      )}
    </div>
  );
};
```

### Step 3.2: Create ErrorBanner Component

**File:** `app/client/src/components/common/ErrorBanner.tsx` (NEW)

```typescript
import React from 'react';

interface ErrorBannerProps {
  error: Error | string | null;
  onDismiss?: () => void;
  title?: string;
  className?: string;
}

/**
 * Standardized error display component.
 *
 * Usage:
 *   <ErrorBanner error={error} onDismiss={() => setError(null)} />
 *   <ErrorBanner error="Something went wrong" title="Error" />
 */
export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  error,
  onDismiss,
  title = 'Error',
  className = '',
}) => {
  if (!error) return null;

  const errorMessage = error instanceof Error ? error.message : error;

  return (
    <div
      className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}
      role="alert"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          <svg
            className="h-5 w-5 text-red-400 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">{title}</h3>
            <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-red-400 hover:text-red-600"
            aria-label="Dismiss error"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
```

### Step 3.3: Create ConfirmationDialog Component

**File:** `app/client/src/components/common/ConfirmationDialog.tsx` (NEW)

```typescript
import React from 'react';

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'danger' | 'primary';
}

/**
 * Standardized confirmation dialog component.
 *
 * Usage:
 *   <ConfirmationDialog
 *     isOpen={showConfirm}
 *     onClose={() => setShowConfirm(false)}
 *     onConfirm={handleDelete}
 *     title="Delete Entry?"
 *     message="This action cannot be undone."
 *     confirmText="Delete"
 *     confirmVariant="danger"
 *   />
 */
export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
}) => {
  if (!isOpen) return null;

  const confirmClasses =
    confirmVariant === 'danger'
      ? 'bg-red-600 hover:bg-red-700 text-white'
      : 'bg-blue-600 hover:bg-blue-700 text-white';

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            {title}
          </h3>
          <p className="text-sm text-gray-700 mb-6">{message}</p>

          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              {cancelText}
            </button>
            <button
              onClick={handleConfirm}
              className={`px-4 py-2 text-sm font-medium rounded-md ${confirmClasses}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
```

### Step 3.4: Update Panels to Use Components

**Example: Replace loading states**

**Before (ReviewPanel.tsx):**
```typescript
{isLoading && <div>Loading...</div>}
```

**After:**
```typescript
import { LoadingState } from './common/LoadingState';

{isLoading && <LoadingState message="Loading patterns..." />}
```

**Example: Replace error displays**

**Before:**
```typescript
{error && (
  <div className="bg-red-50 border border-red-200 rounded p-3">
    <p className="text-red-800">Error: {error.message}</p>
  </div>
)}
```

**After:**
```typescript
import { ErrorBanner } from './common/ErrorBanner';

<ErrorBanner error={error} onDismiss={() => setError(null)} />
```

**Example: Replace toast confirmations**

**Before (LogPanel.tsx, lines 457-479):**
```typescript
onClick={() => {
  toast((t) => (
    <div>
      <p className="mb-3">Delete this entry?</p>
      <div className="flex gap-2">
        <button onClick={() => { deleteMutation.mutate(entry.id) }}>Delete</button>
        <button onClick={() => toast.dismiss(t.id)}>Cancel</button>
      </div>
    </div>
  ), { duration: Infinity, icon: '🗑️' });
}}
```

**After:**
```typescript
import { ConfirmationDialog } from './common/ConfirmationDialog';

const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

<ConfirmationDialog
  isOpen={deleteConfirm === entry.id}
  onClose={() => setDeleteConfirm(null)}
  onConfirm={() => deleteMutation.mutate(entry.id)}
  title="Delete Entry?"
  message="This action cannot be undone."
  confirmText="Delete"
  confirmVariant="danger"
/>
```

### Step 3.5: Create Component Tests

**File:** `app/client/src/components/common/__tests__/LoadingState.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { LoadingState } from '../LoadingState';

describe('LoadingState', () => {
  it('renders with default message', () => {
    render(<LoadingState />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingState message="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('renders different sizes', () => {
    const { rerender } = render(<LoadingState size="small" />);
    expect(screen.getByRole('status')).toHaveClass('h-4');

    rerender(<LoadingState size="large" />);
    expect(screen.getByRole('status')).toHaveClass('h-12');
  });
});
```

Similar tests for ErrorBanner and ConfirmationDialog.

### Step 3.6: Commit UI Components

```bash
git add app/client/src/components/common/LoadingState.tsx
git add app/client/src/components/common/ErrorBanner.tsx
git add app/client/src/components/common/ConfirmationDialog.tsx
git add app/client/src/components/common/__tests__/
git add app/client/src/components/ReviewPanel.tsx  # (and other updated panels)
git add app/client/src/components/LogPanel.tsx

git commit -m "$(cat <<'EOF'
feat: Create reusable UI components for loading, errors, and confirmations

Standardized UI patterns across all panels to reduce duplication and improve consistency.

Created Components:
- LoadingState.tsx
  - Standardized spinner with sizes (small, medium, large)
  - Customizable message
  - Accessibility support (role="status")

- ErrorBanner.tsx
  - Consistent error display with icon
  - Dismissible with onDismiss callback
  - Supports Error objects or strings

- ConfirmationDialog.tsx
  - Modal confirmation dialog
  - Danger/primary variants
  - Backdrop with click-to-close
  - Customizable text

Updated Panels:
- ReviewPanel: LoadingState + ErrorBanner + ConfirmationDialog
- LogPanel: LoadingState + ErrorBanner + ConfirmationDialog
- PlansPanel: LoadingState + ErrorBanner
- SystemStatusPanel: ErrorBanner
- (and 6 more panels)

Code Reduction:
- Removed 200+ lines of duplicate code
- Replaced 20+ custom loading states
- Replaced 15+ custom error displays
- Replaced 8+ toast-based confirmations

Benefits:
- Visual consistency across app
- Single place to update UI patterns
- Better accessibility
- Easier to maintain
- Improved user experience

Session 19 - Phase 3, Part 3/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## PART 4: Standardize Frontend Error Handling

### Step 4.1: Create Error Handler Utility

**File:** `app/client/src/utils/errorHandler.ts` (NEW)

```typescript
/**
 * Standardized error handling utilities for frontend.
 *
 * Provides consistent error message formatting and logging.
 */

export interface ErrorDetails {
  message: string;
  statusCode?: number;
  context?: string;
  originalError?: unknown;
}

/**
 * Format error for display to user.
 *
 * @param error - Error object, string, or unknown
 * @param fallbackMessage - Message to show if error is undefined
 * @returns User-friendly error message
 */
export function formatErrorMessage(
  error: unknown,
  fallbackMessage: string = 'An unexpected error occurred'
): string {
  if (!error) {
    return fallbackMessage;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  // Handle fetch/axios errors
  if (typeof error === 'object' && error !== null) {
    if ('message' in error && typeof error.message === 'string') {
      return error.message;
    }
    if ('error' in error && typeof error.error === 'string') {
      return error.error;
    }
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail;
    }
  }

  return fallbackMessage;
}

/**
 * Log error to console with context.
 *
 * @param context - Context string (e.g., "[ReviewPanel]", "[API]")
 * @param operation - Operation that failed (e.g., "approve pattern", "fetch data")
 * @param error - Error object
 */
export function logError(
  context: string,
  operation: string,
  error: unknown
): void {
  const message = formatErrorMessage(error);
  console.error(`${context} ${operation} failed:`, error);
  console.error(`${context} Error message: ${message}`);
}

/**
 * Extract HTTP status code from error if available.
 *
 * @param error - Error object
 * @returns Status code or undefined
 */
export function getErrorStatusCode(error: unknown): number | undefined {
  if (typeof error === 'object' && error !== null) {
    if ('status' in error && typeof error.status === 'number') {
      return error.status;
    }
    if ('statusCode' in error && typeof error.statusCode === 'number') {
      return error.statusCode;
    }
  }
  return undefined;
}

/**
 * Create standardized error details object.
 *
 * @param error - Error to process
 * @param context - Context where error occurred
 * @returns ErrorDetails object
 */
export function createErrorDetails(
  error: unknown,
  context?: string
): ErrorDetails {
  return {
    message: formatErrorMessage(error),
    statusCode: getErrorStatusCode(error),
    context,
    originalError: error,
  };
}

/**
 * Check if error is a network/connection error.
 *
 * @param error - Error to check
 * @returns True if network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  if (typeof error === 'object' && error !== null) {
    if ('code' in error) {
      const code = String(error.code);
      return ['ENOTFOUND', 'ECONNREFUSED', 'ETIMEDOUT'].includes(code);
    }
  }

  return false;
}
```

### Step 4.2: Update Panel Error Handling

**Pattern to apply to all panels:**

**Before (inconsistent):**
```typescript
// ReviewPanel.tsx
const [mutationError, setMutationError] = useState<string | null>(null);

const approveMutation = useMutation({
  mutationFn: (id: string) => patternReviewClient.approvePattern(id, notes),
  onError: (error: Error) => {
    console.error('[ReviewPanel] Approve mutation failed:', error);
    setMutationError(`Failed to approve pattern: ${error.message}`);
  },
});
```

**After (consistent):**
```typescript
import { formatErrorMessage, logError, createErrorDetails } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const [error, setError] = useState<Error | string | null>(null);

const approveMutation = useMutation({
  mutationFn: (id: string) => patternReviewClient.approvePattern(id, notes),
  onError: (err: unknown) => {
    logError('[ReviewPanel]', 'Approve pattern', err);
    const details = createErrorDetails(err, 'Approve pattern');
    setError(details.message);
  },
  onSuccess: () => {
    setError(null); // Clear errors on success
  },
});

// In JSX:
<ErrorBanner error={error} onDismiss={() => setError(null)} />
```

### Step 4.3: Apply to All Panels

**Panels to update:**
- ReviewPanel.tsx
- LogPanel.tsx
- PlansPanel.tsx
- ContextReviewPanel.tsx
- SystemStatusPanel.tsx
- WebhookStatusPanel.tsx
- PreflightCheckPanel.tsx
- (any others with error handling)

### Step 4.4: Create Tests for Error Handler

**File:** `app/client/src/utils/__tests__/errorHandler.test.ts`

```typescript
import {
  formatErrorMessage,
  getErrorStatusCode,
  isNetworkError,
  createErrorDetails,
} from '../errorHandler';

describe('errorHandler', () => {
  describe('formatErrorMessage', () => {
    it('formats Error objects', () => {
      const error = new Error('Test error');
      expect(formatErrorMessage(error)).toBe('Test error');
    });

    it('formats string errors', () => {
      expect(formatErrorMessage('String error')).toBe('String error');
    });

    it('uses fallback for unknown errors', () => {
      expect(formatErrorMessage(null)).toBe('An unexpected error occurred');
      expect(formatErrorMessage(undefined, 'Custom fallback')).toBe('Custom fallback');
    });

    it('extracts message from object errors', () => {
      expect(formatErrorMessage({ message: 'Object error' })).toBe('Object error');
      expect(formatErrorMessage({ detail: 'Detail error' })).toBe('Detail error');
    });
  });

  describe('getErrorStatusCode', () => {
    it('extracts status code', () => {
      expect(getErrorStatusCode({ status: 404 })).toBe(404);
      expect(getErrorStatusCode({ statusCode: 500 })).toBe(500);
    });

    it('returns undefined for missing status', () => {
      expect(getErrorStatusCode({})).toBeUndefined();
      expect(getErrorStatusCode(new Error())).toBeUndefined();
    });
  });

  describe('isNetworkError', () => {
    it('detects fetch errors', () => {
      const fetchError = new TypeError('fetch failed');
      expect(isNetworkError(fetchError)).toBe(true);
    });

    it('detects connection errors', () => {
      expect(isNetworkError({ code: 'ECONNREFUSED' })).toBe(true);
      expect(isNetworkError({ code: 'ETIMEDOUT' })).toBe(true);
    });

    it('returns false for non-network errors', () => {
      expect(isNetworkError(new Error('Not network'))).toBe(false);
    });
  });
});
```

### Step 4.5: Run Tests

```bash
cd app/client

# Run error handler tests
bun test errorHandler.test.ts

# Run all tests
bun test
```

### Step 4.6: Commit Error Handling Standardization

```bash
git add app/client/src/utils/errorHandler.ts
git add app/client/src/utils/__tests__/errorHandler.test.ts
git add app/client/src/components/ReviewPanel.tsx
git add app/client/src/components/LogPanel.tsx
# (and other updated panels)

git commit -m "$(cat <<'EOF'
feat: Standardize frontend error handling with utility functions

Consistent error formatting and logging across all frontend panels.

Created:
- utils/errorHandler.ts
  - formatErrorMessage() - Consistent user-facing messages
  - logError() - Structured console logging
  - getErrorStatusCode() - Extract HTTP status
  - createErrorDetails() - Comprehensive error objects
  - isNetworkError() - Detect connection issues

Updated Panels:
- Consistent error state naming (error, not mutationError)
- Standardized logging with logError()
- ErrorBanner component for display
- Auto-clear errors on success
- Network error detection

Error Handling Pattern:
  onError: (err: unknown) => {
    logError('[ComponentName]', 'operation', err);
    setError(createErrorDetails(err).message);
  }

Benefits:
- Consistent error messages across app
- Structured error logging (easier debugging)
- Type-safe error handling
- Network error detection
- Better user experience

Session 19 - Phase 3, Part 4/4

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Success Criteria - Phase 3 Complete

After completing all 4 parts, verify:

### Part 1: Repository Naming Standardization
- ✅ docs/backend/repository-standards.md created
- ✅ PhaseQueueRepository methods renamed (5 methods)
- ✅ WorkLogRepository methods renamed (2 methods)
- ✅ All service callers updated
- ✅ All route callers updated
- ✅ All tests updated and passing

### Part 2: Data Fetching Migration
- ✅ ContextReviewPanel uses useQuery (no manual fetch)
- ✅ HistoryView uses WebSocket (no HTTP polling)
- ✅ Automatic polling control implemented
- ✅ Tests passing for both components

### Part 3: Reusable UI Components
- ✅ LoadingState component created and tested
- ✅ ErrorBanner component created and tested
- ✅ ConfirmationDialog component created and tested
- ✅ 10+ panels updated to use components
- ✅ 200+ lines of duplicate code removed

### Part 4: Error Handling Standardization
- ✅ errorHandler.ts utility created
- ✅ All panels use consistent error pattern
- ✅ Tests passing for error utilities
- ✅ Structured logging implemented

### Overall Phase 3 Verification

```bash
# Backend tests
cd app/server
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest -v

# Frontend tests
cd app/client
bun test

# Verify no old method names remain
grep -r "insert_phase\|create_entry\|delete_phase\|delete_entry" app/server/services/ app/server/routes/ || echo "All methods renamed ✓"

# Verify no manual fetch in components
grep -r "useState.*Loading\|useState.*Error" app/client/src/components/ | grep -v "common/" || echo "Components use standard patterns ✓"
```

---

## Files Modified Summary

**Created (7 new files):**
- `docs/backend/repository-standards.md` - Repository naming standards
- `app/client/src/components/common/LoadingState.tsx` - Loading component
- `app/client/src/components/common/ErrorBanner.tsx` - Error component
- `app/client/src/components/common/ConfirmationDialog.tsx` - Confirmation component
- `app/client/src/utils/errorHandler.ts` - Error utilities
- Tests for components and utilities

**Modified (20+ files):**
- 4 repository files (renamed methods)
- 5+ service files (updated callers)
- 5+ route files (updated callers)
- 10+ panel files (use new components and patterns)
- Test files (updated for new patterns)

---

## Return Summary Template

After completing Phase 3, return to Session 19 main chat with this summary:

```
# Session 19 - Phase 3 Implementation Summary

## Completed Tasks

**Part 1: Repository Naming Standardization (6 hours)**
- ✅ Created repository naming standards documentation
- ✅ Renamed PhaseQueueRepository methods (5 changes)
- ✅ Renamed WorkLogRepository methods (2 changes)
- ✅ Updated all service and route callers
- ✅ All tests passing (878/878)

**Part 2: Data Fetching Migration (3 hours)**
- ✅ ContextReviewPanel migrated to useQuery
- ✅ HistoryView migrated to WebSocket
- ✅ Removed 40+ lines of boilerplate
- ✅ Eliminated HTTP polling (NO POLLING mandate met)

**Part 3: Reusable UI Components (5 hours)**
- ✅ Created LoadingState component (3 sizes)
- ✅ Created ErrorBanner component (dismissible)
- ✅ Created ConfirmationDialog component (2 variants)
- ✅ Updated 10+ panels to use components
- ✅ Removed 200+ lines of duplicate code

**Part 4: Error Handling Standardization (2 hours)**
- ✅ Created errorHandler.ts utilities
- ✅ Standardized error logging pattern
- ✅ All panels use consistent error display
- ✅ Tests passing (149/149 frontend tests)

## Issues Encountered
[List any issues and how they were resolved]

## Test Results
- Backend tests: 878/878 PASS
- Frontend tests: 149/149 PASS
- Manual verification: PASS

## Code Quality Impact
- Repository methods: Consistent across all repos
- Data fetching: NO POLLING, all WebSocket or useQuery
- UI components: 200+ lines removed, visual consistency
- Error handling: Structured logging, better UX

## Files Modified
- Created: 7 new files (docs, components, utilities)
- Modified: 20+ existing files (repos, services, routes, panels)
- Total commits: 4 (one per part)

## Ready for Phase 4
Phase 3 complete and meets expectations. Code quality significantly improved, patterns standardized. Ready to proceed with Phase 4: Documentation.
```

---

**End of Phase 3 Implementation Guide**
