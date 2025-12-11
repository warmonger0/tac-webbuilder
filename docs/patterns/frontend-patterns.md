# Frontend Patterns & Standards

This document defines the standard patterns for frontend development in the tac-webbuilder project, established during Session 19's architectural improvements.

## Table of Contents

1. [Data Fetching Patterns](#data-fetching-patterns)
2. [UI Component Patterns](#ui-component-patterns)
3. [Error Handling Pattern](#error-handling-pattern)
4. [State Management](#state-management)
5. [Best Practices](#best-practices)
6. [Migration Checklist](#migration-checklist)

---

## Data Fetching Patterns

### Pattern 1: One-Time Fetch with useQuery

**Use Case:** Fetching data that doesn't change frequently or needs caching.

**When to Use:**
- Static or infrequently changing data
- API calls that should be cached
- Data that doesn't need real-time updates
- Initial page load data

**Implementation:**

```typescript
import { useQuery } from '@tanstack/react-query';

// 1. Define API client function (outside component)
const fetchResource = async (id: string): Promise<Resource> => {
  const response = await fetch(`/api/v1/resource/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch resource: ${response.statusText}`);
  }

  return response.json();
};

// 2. Use in component
const MyComponent: React.FC<Props> = ({ id }) => {
  const {
    data,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['resource', id],  // Unique key for caching
    queryFn: () => fetchResource(id),
    enabled: !!id,  // Only run if id exists
    staleTime: 5000,  // Consider fresh for 5s
  });

  if (isLoading) return <LoadingState message="Loading resource..." />;
  if (error) return <ErrorBanner error={error} />;

  return <div>{/* Use data */}</div>;
};
```

**Benefits:**
- ✅ Automatic caching and deduplication
- ✅ Built-in loading and error states
- ✅ Easy refetching
- ✅ TypeScript type safety
- ✅ No manual state management

**When NOT to Use:**
- ❌ Real-time data (use WebSocket instead)
- ❌ Data that changes every few seconds
- ❌ High-frequency updates

**Examples in Codebase:**
- `ContextReviewPanel.tsx` - Fetches analysis results
- Plan review data
- User prompts

---

### Pattern 2: Real-Time Data with WebSocket

**Use Case:** Data that updates in real-time and needs <2s latency.

**When to Use:**
- Dashboard data that changes frequently
- Workflow status updates
- Queue monitoring
- Real-time notifications
- Any data requiring <2s latency

**Implementation:**

```typescript
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';

const MyComponent: React.FC = () => {
  const {
    workflowHistory,      // Real-time data
    analytics,            // Real-time analytics
    isConnected,          // Connection status
    connectionQuality,    // 'good' | 'poor'
    lastUpdated          // Timestamp of last update
  } = useWorkflowHistoryWebSocket();

  // Show connection status
  if (!isConnected) {
    return <div>Connecting to real-time updates...</div>;
  }

  // Optional: Show connection quality indicator
  const qualityIndicator = (
    <span className={connectionQuality === 'good' ? 'text-green-500' : 'text-yellow-500'}>
      {connectionQuality === 'good' ? '●' : '◐'} Live
    </span>
  );

  return (
    <div>
      <div className="header">
        {qualityIndicator}
        <span className="text-xs text-gray-500">
          Updated {new Date(lastUpdated).toLocaleTimeString()}
        </span>
      </div>

      {workflowHistory.map(workflow => (
        <WorkflowCard key={workflow.id} workflow={workflow} />
      ))}
    </div>
  );
};
```

**Available WebSocket Hooks:**
```typescript
// Workflow history updates
const { workflowHistory, isConnected } = useWorkflowHistoryWebSocket();

// ADW status updates
const { adwStatus, isConnected } = useAdwStatusWebSocket();

// Queue updates
const { queueItems, isConnected } = useQueueWebSocket();

// Route updates
const { routes, isConnected } = useRoutesWebSocket();
```

**Benefits:**
- ✅ <2s update latency
- ✅ No HTTP polling
- ✅ Automatic reconnection
- ✅ Connection quality monitoring
- ✅ 80% less network traffic

**When NOT to Use:**
- ❌ Static data (use useQuery instead)
- ❌ Heavy data payloads (>1MB)
- ❌ Data that rarely changes (use useQuery)

**Examples in Codebase:**
- `HistoryView.tsx` - Real-time workflow history
- `CurrentWorkflowCard.tsx` - Live workflow status
- `ZteHopperQueueCard.tsx` - Real-time queue
- `AdwMonitorCard.tsx` - Live ADW monitoring
- `RoutesView.tsx` - Real-time route status

---

### Pattern 3: Conditional Refetch with useQuery

**Use Case:** Long-running operations that need temporary polling which should stop when complete.

**When to Use:**
- Background jobs with progress tracking
- Analysis or processing tasks
- Operations that transition from "in-progress" to "complete"
- Temporary polling that self-terminates

**Implementation:**

```typescript
const { data: analysis, isLoading } = useQuery({
  queryKey: ['analysis', analysisId],
  queryFn: () => fetchAnalysis(analysisId),

  // Conditional refetch: Poll while analyzing, stop when complete
  refetchInterval: (data) => {
    // If status is 'analyzing', poll every 3s
    // Otherwise, stop polling (return false)
    return data?.status === 'analyzing' ? 3000 : false;
  },

  enabled: !!analysisId,
});

// Component will automatically:
// 1. Start polling when status === 'analyzing'
// 2. Stop polling when status changes to anything else
// 3. No manual cleanup needed
```

**Benefits:**
- ✅ Self-terminating polling (no manual cleanup)
- ✅ Only polls when necessary
- ✅ Automatic cache management
- ✅ Built-in loading states

**When NOT to Use:**
- ❌ Permanent real-time updates (use WebSocket)
- ❌ Simple one-time fetches (use basic useQuery)

**Examples in Codebase:**
- `ContextReviewPanel.tsx` - Polls while analysis is running

---

### ❌ AVOID: Manual Fetch Pattern

**DO NOT USE THIS PATTERN:**

```typescript
// ❌ BAD: Manual fetch + useState
const [data, setData] = useState(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);

const fetchData = async () => {
  setIsLoading(true);
  setError(null);
  try {
    const response = await fetch(url);
    const json = await response.json();
    setData(json);
  } catch (err) {
    setError(err);
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => {
  fetchData();
}, []);
```

**Problems:**
- ❌ 40+ lines of boilerplate
- ❌ Manual state management
- ❌ No caching
- ❌ No automatic refetch
- ❌ Manual error handling
- ❌ Manual loading states

**Instead, Use:**
- ✅ useQuery for one-time fetches
- ✅ WebSocket hooks for real-time data

---

## UI Component Patterns

### LoadingState Component

**Purpose:** Standardized loading indicator across the application.

**Usage:**

```typescript
import { LoadingState } from './common/LoadingState';

// Basic usage with default message
<LoadingState />
// Displays: Spinner + "Loading..."

// Custom message
<LoadingState message="Loading analysis results..." />

// Different sizes
<LoadingState size="small" />   // Small spinner (16px)
<LoadingState size="medium" />  // Medium spinner (32px) - default
<LoadingState size="large" />   // Large spinner (48px)

// With custom styling
<LoadingState message="Please wait..." className="my-4" />
```

**Props:**
```typescript
interface LoadingStateProps {
  message?: string;  // Default: "Loading..."
  size?: 'small' | 'medium' | 'large';  // Default: 'medium'
  className?: string;  // Additional CSS classes
}
```

**Accessibility:**
- Includes `role="status"` for screen readers
- Aria-label "Loading" on spinner

**When to Use:**
- ✅ All loading states throughout the app
- ✅ While fetching data
- ✅ During async operations

**When NOT to Use:**
- ❌ For very short operations (<200ms)
- ❌ When you need a different style (create new component)

---

### ErrorBanner Component

**Purpose:** Consistent error display with dismissible option.

**Usage:**

```typescript
import { ErrorBanner } from './common/ErrorBanner';

const [error, setError] = useState<Error | string | null>(null);

// Basic usage
<ErrorBanner error={error} />

// With dismiss handler
<ErrorBanner
  error={error}
  onDismiss={() => setError(null)}
/>

// Custom title
<ErrorBanner
  error="Something went wrong"
  title="Connection Error"
  onDismiss={() => setError(null)}
/>

// With additional styling
<ErrorBanner
  error={error}
  onDismiss={() => setError(null)}
  className="my-4"
/>
```

**Props:**
```typescript
interface ErrorBannerProps {
  error: Error | string | null;  // Error to display
  onDismiss?: () => void;  // Dismiss callback
  title?: string;  // Default: "Error"
  className?: string;  // Additional CSS classes
}
```

**Error Types Supported:**
- `Error` objects (extracts `error.message`)
- String errors (displays as-is)
- `null` (renders nothing)

**Accessibility:**
- Includes `role="alert"` for screen readers
- Keyboard-accessible dismiss button
- High-contrast colors

**When to Use:**
- ✅ All error displays
- ✅ Form validation errors
- ✅ API errors
- ✅ General error messages

**When NOT to Use:**
- ❌ Success messages (use toast or banner)
- ❌ Warnings (create separate WarningBanner if needed)

**Example in Context:**

```typescript
const MyComponent = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    mutationFn: submitData,
    onError: (err: unknown) => {
      logError('[MyComponent]', 'Submit data', err);
      setError(formatErrorMessage(err));
    },
    onSuccess: () => {
      setError(null);  // Clear error on success
    },
  });

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {/* Rest of component */}
    </div>
  );
};
```

---

### ConfirmationDialog Component

**Purpose:** Modal confirmation dialogs for destructive or important actions.

**Usage:**

```typescript
import { ConfirmationDialog } from './common/ConfirmationDialog';

const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
const [itemToDelete, setItemToDelete] = useState<number | null>(null);

// Trigger dialog
const handleDeleteClick = (id: number) => {
  setItemToDelete(id);
  setShowDeleteConfirm(true);
};

// Render dialog
<ConfirmationDialog
  isOpen={showDeleteConfirm}
  onClose={() => setShowDeleteConfirm(false)}
  onConfirm={() => {
    if (itemToDelete) {
      deleteMutation.mutate(itemToDelete);
    }
    setShowDeleteConfirm(false);
  }}
  title="Delete Entry?"
  message="This action cannot be undone. Are you sure you want to delete this entry?"
  confirmText="Delete"
  confirmVariant="danger"
/>

// Primary action variant (default)
<ConfirmationDialog
  isOpen={showApprove}
  onClose={() => setShowApprove(false)}
  onConfirm={handleApprove}
  title="Approve Pattern?"
  message="This will mark the pattern as approved for use."
  confirmText="Approve"
  confirmVariant="primary"
/>
```

**Props:**
```typescript
interface ConfirmationDialogProps {
  isOpen: boolean;  // Dialog visibility
  onClose: () => void;  // Close handler
  onConfirm: () => void;  // Confirm handler
  title: string;  // Dialog title
  message: string;  // Dialog message
  confirmText?: string;  // Default: "Confirm"
  cancelText?: string;  // Default: "Cancel"
  confirmVariant?: 'danger' | 'primary';  // Default: 'primary'
}
```

**Variants:**
- `danger` - Red confirm button (for destructive actions)
- `primary` - Blue confirm button (for normal confirmations)

**Accessibility:**
- Modal with backdrop
- Keyboard navigation (Tab, Enter, Escape)
- `role="dialog"` and `aria-modal="true"`
- Focus trap (focuses dialog when opened)
- Escape key closes dialog

**When to Use:**
- ✅ Before deleting items
- ✅ Before destructive actions
- ✅ Before important state changes
- ✅ When action cannot be undone

**When NOT to Use:**
- ❌ For simple notifications (use ErrorBanner or toast)
- ❌ For non-destructive actions
- ❌ When user can easily undo action

**Pattern for Managing Dialog State:**

```typescript
// Store ID of item being confirmed
const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

// Trigger confirmation
<button onClick={() => setDeleteConfirmId(entry.id)}>Delete</button>

// Dialog
<ConfirmationDialog
  isOpen={deleteConfirmId === entry.id}
  onClose={() => setDeleteConfirmId(null)}
  onConfirm={() => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId);
    }
  }}
  title="Delete Entry?"
  message="This action cannot be undone."
  confirmVariant="danger"
/>
```

---

## Error Handling Pattern

### Standard Error Handling with errorHandler Utility

**Purpose:** Consistent error logging and user messaging across the application.

**Import:**

```typescript
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';
```

**Standard Pattern:**

```typescript
const MyComponent = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    mutationFn: (data) => apiCall(data),

    onError: (err: unknown) => {
      // 1. Log with context
      logError('[ComponentName]', 'Operation description', err);

      // 2. Set user-friendly error message
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      // 3. Clear errors on success
      setError(null);
      // ... other success logic
    },
  });

  return (
    <div>
      {/* 4. Display error */}
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {/* Rest of component */}
    </div>
  );
};
```

### Error Handler Functions

#### formatErrorMessage()

Extracts user-friendly message from any error type.

```typescript
formatErrorMessage(error: unknown, fallback?: string): string

// Examples:
formatErrorMessage(new Error('Failed'))  // → "Failed"
formatErrorMessage('Error text')  // → "Error text"
formatErrorMessage({ message: 'API error' })  // → "API error"
formatErrorMessage(null, 'Fallback')  // → "Fallback"
formatErrorMessage(undefined)  // → "An unexpected error occurred"
```

#### logError()

Structured console logging with context.

```typescript
logError(context: string, operation: string, error: unknown): void

// Example:
logError('[ReviewPanel]', 'Approve pattern', error);

// Console output:
// [ReviewPanel] Approve pattern failed: Error: Failed to approve
// [ReviewPanel] Error message: Failed to approve
// [ReviewPanel] HTTP status: 400  (if available)
// [ReviewPanel] Network error detected  (if network error)
```

#### getErrorStatusCode()

Extract HTTP status code from error if available.

```typescript
getErrorStatusCode(error: unknown): number | undefined

// Examples:
getErrorStatusCode({ status: 404 })  // → 404
getErrorStatusCode({ statusCode: 500 })  // → 500
getErrorStatusCode(new Error())  // → undefined
```

#### isNetworkError()

Detect connection/network errors.

```typescript
isNetworkError(error: unknown): boolean

// Examples:
isNetworkError(new TypeError('fetch failed'))  // → true
isNetworkError({ code: 'ECONNREFUSED' })  // → true
isNetworkError(new Error('Not found'))  // → false
```

#### isAuthError()

Detect 401/403 authentication errors.

```typescript
isAuthError(error: unknown): boolean

// Examples:
isAuthError({ status: 401 })  // → true
isAuthError({ statusCode: 403 })  // → true
isAuthError({ status: 404 })  // → false
```

#### isNotFoundError()

Detect 404 errors.

```typescript
isNotFoundError(error: unknown): boolean

// Examples:
isNotFoundError({ status: 404 })  // → true
isNotFoundError({ status: 500 })  // → false
```

### Console Logging Format

**Before (inconsistent):**
```
Approve mutation failed: Error: Failed
Delete failed: Error: Not found
```

**After (structured):**
```
[ReviewPanel] Approve pattern failed: Error: Failed to approve
[ReviewPanel] Error message: Failed to approve
[ReviewPanel] HTTP status: 400

[LogPanel] Delete log entry failed: Error: Not found
[LogPanel] Error message: Entry not found
[LogPanel] HTTP status: 404
[LogPanel] Network error detected (check connection)
```

**Benefits:**
- Easy to grep logs by component: `grep "\[ReviewPanel\]"`
- Clear operation context
- HTTP status for debugging
- Network error detection

---

## State Management

### Pattern: Local Component State

**Use Case:** Component-specific state that doesn't need to be shared.

```typescript
// Use useState for local state
const [isExpanded, setIsExpanded] = useState(false);
const [selectedId, setSelectedId] = useState<number | null>(null);
```

### Pattern: Server State (via useQuery)

**Use Case:** Data from the server that may be shared across components.

```typescript
// useQuery automatically caches and shares data
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
});

// Other components using same queryKey get cached data
```

### Pattern: Real-Time State (via WebSocket)

**Use Case:** Real-time data that updates across all connected clients.

```typescript
// WebSocket hook manages connection and state
const { workflowHistory } = useWorkflowHistoryWebSocket();
```

### ❌ AVOID: Zustand for New Features

**Note:** While Zustand is in `package.json`, it's not actively used. For new features:
- ✅ Use `useState` for local state
- ✅ Use `useQuery` for server state
- ✅ Use WebSocket hooks for real-time state
- ❌ Don't use Zustand (legacy, being phased out)

---

## Best Practices

### DO ✅

**Data Fetching:**
- ✅ Use `useQuery` for one-time fetches
- ✅ Use WebSocket hooks for real-time data
- ✅ Use conditional `refetchInterval` for long-running ops
- ✅ Extract API client functions outside components

**UI Components:**
- ✅ Use `LoadingState` for all loading indicators
- ✅ Use `ErrorBanner` for all error displays
- ✅ Use `ConfirmationDialog` for destructive actions
- ✅ Make components reusable and generic

**Error Handling:**
- ✅ Use `errorHandler` utilities consistently
- ✅ Use `logError()` for structured logging
- ✅ Clear errors on success (`onSuccess: () => setError(null)`)
- ✅ Handle errors at component boundary

**Code Organization:**
- ✅ Type all props and state with TypeScript
- ✅ Extract reusable logic into custom hooks
- ✅ Keep components focused (single responsibility)
- ✅ Document complex logic with comments

### DON'T ❌

**Data Fetching:**
- ❌ Use manual fetch + useState
- ❌ Use HTTP polling (except conditional refetch)
- ❌ Use setInterval for polling
- ❌ Make API calls in useEffect without cleanup

**UI Components:**
- ❌ Create custom loading spinners
- ❌ Create custom error displays
- ❌ Use toast notifications for confirmations
- ❌ Duplicate UI code across components

**Error Handling:**
- ❌ Use console.error directly
- ❌ Show raw error objects to users
- ❌ Ignore errors silently
- ❌ Have inconsistent error messages

**State Management:**
- ❌ Use Zustand for new features
- ❌ Prop drill more than 2 levels
- ❌ Mix server state with local state
- ❌ Store derived state in useState

---

## Migration Checklist

When updating an existing component to use these patterns:

### Data Fetching
- [ ] Replace manual fetch with useQuery or WebSocket
- [ ] Remove manual useState for data, loading, error
- [ ] Remove manual useEffect for fetching
- [ ] Remove setInterval polling
- [ ] Use appropriate pattern (useQuery vs WebSocket)

### UI Components
- [ ] Replace custom loading states with LoadingState
- [ ] Replace custom error displays with ErrorBanner
- [ ] Replace toast confirmations with ConfirmationDialog
- [ ] Remove duplicate UI code

### Error Handling
- [ ] Import errorHandler utilities
- [ ] Replace console.error with logError
- [ ] Use formatErrorMessage for user-facing messages
- [ ] Add onSuccess to clear errors
- [ ] Use ErrorBanner for display

### Code Quality
- [ ] Add TypeScript types to all props
- [ ] Extract reusable logic to custom hooks
- [ ] Add JSDoc comments to exported functions
- [ ] Test all error paths
- [ ] Verify accessibility (keyboard, screen reader)

---

## Examples in Codebase

### useQuery Pattern
- `app/client/src/components/context-review/ContextReviewPanel.tsx`
- Pattern review components

### WebSocket Pattern
- `app/client/src/components/HistoryView.tsx`
- `app/client/src/components/CurrentWorkflowCard.tsx`
- `app/client/src/components/ZteHopperQueueCard.tsx`
- `app/client/src/components/AdwMonitorCard.tsx`
- `app/client/src/components/RoutesView.tsx`

### UI Components
- `app/client/src/components/ReviewPanel.tsx` (uses all 3 components)
- `app/client/src/components/LogPanel.tsx` (uses all 3 components)

### Error Handling
- `app/client/src/components/ReviewPanel.tsx` (standardized pattern)
- `app/client/src/components/LogPanel.tsx` (standardized pattern)

---

## Additional Resources

- **Backend Patterns:** `docs/patterns/backend-patterns.md`
- **Migration Guide:** `docs/guides/migration-guide-session-19.md`
- **WebSocket API:** `docs/api/websocket-api.md`
- **Error Handler API:** `docs/api/error-handler.md`
- **Component API:** `docs/api/reusable-components.md`
- **Architecture:** `docs/architecture/session-19-improvements.md`
