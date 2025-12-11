# Reusable Components API Reference

Complete reference for the standardized UI components used throughout the tac-webbuilder frontend.

## Table of Contents

1. [Overview](#overview)
2. [LoadingState Component](#loadingstate-component)
3. [ErrorBanner Component](#errorbanner-component)
4. [ConfirmationDialog Component](#confirmationdialog-component)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)
7. [Testing](#testing)

---

## Overview

Session 19 introduced three reusable UI components to standardize visual patterns across the application:

| Component | Purpose | Use Cases |
|-----------|---------|-----------|
| LoadingState | Loading indicator | Data fetching, async operations |
| ErrorBanner | Error display | API errors, validation errors |
| ConfirmationDialog | Confirmation modal | Destructive actions, important decisions |

**Benefits:**
- **Visual Consistency:** Same UI patterns across all panels
- **Accessibility:** ARIA labels, keyboard navigation, screen reader support
- **Maintainability:** Single source of truth for UI patterns
- **Developer Experience:** Simple API, minimal props

**Location:** `app/client/src/components/common/`

---

## LoadingState Component

Standardized loading indicator with spinner and optional message.

### Import

```typescript
import { LoadingState } from './common/LoadingState';
```

### Props

```typescript
interface LoadingStateProps {
  /** Message to display below spinner */
  message?: string;

  /** Size of spinner */
  size?: 'small' | 'medium' | 'large';

  /** Additional CSS classes */
  className?: string;
}
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `string` | `"Loading..."` | Message displayed below spinner |
| `size` | `'small' \| 'medium' \| 'large'` | `'medium'` | Spinner size |
| `className` | `string` | `''` | Additional Tailwind CSS classes |

### Spinner Sizes

| Size | Dimensions | Use Case |
|------|-----------|----------|
| `small` | 16px (h-4 w-4) | Inline loading, buttons |
| `medium` | 32px (h-8 w-8) | Default, panels, cards |
| `large` | 48px (h-12 w-12) | Full page loading, important sections |

### Basic Usage

```typescript
import { LoadingState } from './common/LoadingState';

// Default - medium spinner with "Loading..." message
<LoadingState />

// Custom message
<LoadingState message="Loading analysis..." />

// Different sizes
<LoadingState size="small" />
<LoadingState size="large" message="Processing data..." />

// With custom styling
<LoadingState message="Please wait..." className="my-8" />
```

### Usage in Components

```typescript
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from './common/LoadingState';

const MyComponent = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['data'],
    queryFn: fetchData,
  });

  if (isLoading) {
    return <LoadingState message="Loading data..." />;
  }

  return <div>{/* Render data */}</div>;
};
```

### Accessibility

- `role="status"` - Announces loading state to screen readers
- `aria-label="Loading"` - Labels spinner for assistive technology
- Semantic HTML structure
- Sufficient color contrast

### Visual Appearance

```
┌─────────────────────────┐
│                         │
│         ◐ (spinning)    │
│                         │
│     Loading data...     │
│                         │
└─────────────────────────┘
```

**Colors:**
- Spinner: Blue (`border-blue-600`)
- Message: Gray (`text-gray-600`)

---

## ErrorBanner Component

Standardized error display with dismiss option.

### Import

```typescript
import { ErrorBanner } from './common/ErrorBanner';
```

### Props

```typescript
interface ErrorBannerProps {
  /** Error to display (Error object or string) */
  error: Error | string | null;

  /** Callback when user dismisses error */
  onDismiss?: () => void;

  /** Optional title for error */
  title?: string;

  /** Additional CSS classes */
  className?: string;
}
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `error` | `Error \| string \| null` | Required | Error to display |
| `onDismiss` | `() => void` | `undefined` | Called when dismiss button clicked |
| `title` | `string` | `"Error"` | Error title/heading |
| `className` | `string` | `''` | Additional Tailwind CSS classes |

### Error Handling

The component automatically handles different error types:

```typescript
// Error objects - extracts message
<ErrorBanner error={new Error('Failed to load')} />
// Displays: "Failed to load"

// String errors - displays as-is
<ErrorBanner error="Something went wrong" />
// Displays: "Something went wrong"

// null - renders nothing
<ErrorBanner error={null} />
// Renders: null (nothing displayed)
```

### Basic Usage

```typescript
import { ErrorBanner } from './common/ErrorBanner';
import { useState } from 'react';

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
  error="Connection failed"
  title="Network Error"
  onDismiss={() => setError(null)}
/>

// With custom styling
<ErrorBanner
  error={error}
  onDismiss={() => setError(null)}
  className="my-4"
/>
```

### Usage with Error Handler

Combine with `errorHandler` utility for best results:

```typescript
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const MyComponent = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    mutationFn: apiCall,

    onError: (err: unknown) => {
      // Structured logging
      logError('[MyComponent]', 'API call', err);

      // User-friendly error message
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      // Clear errors on success
      setError(null);
    },
  });

  return (
    <div>
      {/* Display error */}
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {/* Rest of component */}
    </div>
  );
};
```

### Accessibility

- `role="alert"` - Announces errors to screen readers
- `aria-label="Dismiss error"` - Labels dismiss button
- Keyboard accessible dismiss button
- High contrast colors for visibility
- Semantic HTML structure

### Visual Appearance

```
┌──────────────────────────────────────────┐
│  ⊗  Error                            × │
│     Failed to load data                 │
└──────────────────────────────────────────┘
```

**Colors:**
- Background: Light red (`bg-red-50`)
- Border: Red (`border-red-200`)
- Icon: Red (`text-red-400`)
- Title: Dark red (`text-red-800`)
- Message: Red (`text-red-700`)
- Dismiss button: Red hover (`hover:text-red-600`)

---

## ConfirmationDialog Component

Modal dialog for confirming important actions.

### Import

```typescript
import { ConfirmationDialog } from './common/ConfirmationDialog';
```

### Props

```typescript
interface ConfirmationDialogProps {
  /** Whether dialog is open */
  isOpen: boolean;

  /** Callback when dialog should close */
  onClose: () => void;

  /** Callback when user confirms */
  onConfirm: () => void;

  /** Dialog title */
  title: string;

  /** Dialog message */
  message: string;

  /** Text for confirm button */
  confirmText?: string;

  /** Text for cancel button */
  cancelText?: string;

  /** Variant for confirm button */
  confirmVariant?: 'danger' | 'primary';
}
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `isOpen` | `boolean` | Required | Controls dialog visibility |
| `onClose` | `() => void` | Required | Called when dialog should close |
| `onConfirm` | `() => void` | Required | Called when user confirms |
| `title` | `string` | Required | Dialog title |
| `message` | `string` | Required | Dialog message/description |
| `confirmText` | `string` | `"Confirm"` | Confirm button text |
| `cancelText` | `string` | `"Cancel"` | Cancel button text |
| `confirmVariant` | `'danger' \| 'primary'` | `'primary'` | Confirm button style |

### Button Variants

| Variant | Color | Use Case |
|---------|-------|----------|
| `danger` | Red | Destructive actions (delete, remove) |
| `primary` | Blue | Normal confirmations (approve, save) |

### Basic Usage

```typescript
import { ConfirmationDialog } from './common/ConfirmationDialog';
import { useState } from 'react';

const [showConfirm, setShowConfirm] = useState(false);

// Destructive action (delete)
<ConfirmationDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  title="Delete Entry?"
  message="This action cannot be undone. Are you sure you want to delete this entry?"
  confirmText="Delete"
  confirmVariant="danger"
/>

// Normal confirmation (approve)
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

### Usage Pattern

```typescript
import { ConfirmationDialog } from './common/ConfirmationDialog';
import { useState } from 'react';

const MyComponent = () => {
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const deleteMutation = useMutation({
    mutationFn: deleteItem,
    onSuccess: () => {
      setDeleteConfirmId(null);
    },
  });

  // Trigger confirmation
  const handleDeleteClick = (id: number) => {
    setDeleteConfirmId(id);
  };

  // Handle confirmation
  const handleDeleteConfirm = () => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId);
    }
  };

  return (
    <div>
      <button onClick={() => handleDeleteClick(item.id)}>
        Delete
      </button>

      <ConfirmationDialog
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Entry?"
        message="This action cannot be undone."
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
};
```

### Keyboard Support

- **Escape key:** Closes dialog
- **Tab:** Navigate between Cancel and Confirm buttons
- **Enter:** Activates focused button
- **Space:** Activates focused button

### Accessibility

- `role="dialog"` - Identifies as dialog
- `aria-modal="true"` - Indicates modal behavior
- `aria-labelledby` - Links to dialog title
- Keyboard navigation support
- Focus management
- Backdrop click to close
- Escape key to close

### Visual Appearance

```
┌─────────────────────────────────────┐
│  Semi-transparent backdrop          │
│                                     │
│    ┌───────────────────────────┐   │
│    │  Delete Entry?            │   │
│    │                           │   │
│    │  This action cannot be    │   │
│    │  undone. Are you sure?    │   │
│    │                           │   │
│    │      [Cancel]  [Delete]   │   │
│    └───────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Colors:**

**Danger variant:**
- Confirm button: Red (`bg-red-600`, `hover:bg-red-700`)

**Primary variant:**
- Confirm button: Blue (`bg-blue-600`, `hover:bg-blue-700`)

**Both variants:**
- Cancel button: Gray (`bg-gray-100`, `hover:bg-gray-200`)
- Backdrop: Black with 50% opacity
- Dialog background: White
- Title: Dark gray (`text-gray-900`)
- Message: Medium gray (`text-gray-700`)

---

## Usage Examples

### Example 1: Data Fetching with useQuery

```typescript
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from './common/LoadingState';
import { ErrorBanner } from './common/ErrorBanner';
import { formatErrorMessage, logError } from '../utils/errorHandler';

const DataView = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const { data, isLoading, error: queryError } = useQuery({
    queryKey: ['data'],
    queryFn: fetchData,

    onError: (err: unknown) => {
      logError('[DataView]', 'Fetch data', err);
      setError(formatErrorMessage(err));
    },
  });

  if (isLoading) {
    return <LoadingState message="Loading data..." />;
  }

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {/* Render data */}
    </div>
  );
};
```

---

### Example 2: Mutation with Confirmation

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ErrorBanner } from './common/ErrorBanner';
import { ConfirmationDialog } from './common/ConfirmationDialog';
import { formatErrorMessage, logError } from '../utils/errorHandler';

const ItemList = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const deleteMutation = useMutation({
    mutationFn: deleteItem,

    onError: (err: unknown) => {
      logError('[ItemList]', 'Delete item', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      setDeleteConfirmId(null);
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
  });

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {items.map(item => (
        <div key={item.id}>
          <span>{item.name}</span>
          <button
            onClick={() => setDeleteConfirmId(item.id)}
            className="text-red-600"
          >
            Delete
          </button>
        </div>
      ))}

      <ConfirmationDialog
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={() => {
          if (deleteConfirmId) {
            deleteMutation.mutate(deleteConfirmId);
          }
        }}
        title="Delete Item?"
        message="This action cannot be undone. Are you sure you want to delete this item?"
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
};
```

---

### Example 3: Multiple Mutations (ReviewPanel pattern)

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ErrorBanner } from './common/ErrorBanner';
import { ConfirmationDialog } from './common/ConfirmationDialog';
import { formatErrorMessage, logError } from '../utils/errorHandler';

const ReviewPanel = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (id: number) => approvePattern(id),

    onError: (err: unknown) => {
      logError('[ReviewPanel]', 'Approve pattern', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (id: number) => rejectPattern(id),

    onError: (err: unknown) => {
      logError('[ReviewPanel]', 'Reject pattern', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
    },
  });

  // Delete mutation (with confirmation)
  const deleteMutation = useMutation({
    mutationFn: (id: number) => deletePattern(id),

    onError: (err: unknown) => {
      logError('[ReviewPanel]', 'Delete pattern', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      setDeleteConfirmId(null);
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
    },
  });

  return (
    <div>
      {/* Error display */}
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {/* Pattern list */}
      {patterns.map(pattern => (
        <div key={pattern.id} className="border p-4 rounded">
          <h3>{pattern.name}</h3>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => approveMutation.mutate(pattern.id)}
              className="px-3 py-1 bg-green-600 text-white rounded"
            >
              Approve
            </button>

            <button
              onClick={() => rejectMutation.mutate(pattern.id)}
              className="px-3 py-1 bg-yellow-600 text-white rounded"
            >
              Reject
            </button>

            <button
              onClick={() => setDeleteConfirmId(pattern.id)}
              className="px-3 py-1 bg-red-600 text-white rounded"
            >
              Delete
            </button>
          </div>
        </div>
      ))}

      {/* Delete confirmation */}
      <ConfirmationDialog
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={() => {
          if (deleteConfirmId) {
            deleteMutation.mutate(deleteConfirmId);
          }
        }}
        title="Delete Pattern?"
        message="This action cannot be undone. Are you sure you want to delete this pattern?"
        confirmText="Delete"
        confirmVariant="danger"
      />
    </div>
  );
};
```

---

## Best Practices

### DO ✅

**LoadingState:**
- ✅ Use for all loading indicators throughout the app
- ✅ Provide descriptive loading messages
- ✅ Use appropriate size for context (small for inline, large for full page)
- ✅ Place in logical position (centered for full content, inline for partial)

**ErrorBanner:**
- ✅ Always provide `onDismiss` handler
- ✅ Clear errors on successful operations
- ✅ Use with `formatErrorMessage()` for consistent messaging
- ✅ Place at top of component for visibility
- ✅ Handle both Error objects and strings

**ConfirmationDialog:**
- ✅ Use for destructive actions (delete, remove, clear)
- ✅ Use for important state changes
- ✅ Provide clear, specific messages
- ✅ Use `danger` variant for destructive actions
- ✅ Store ID of item being confirmed in state

### DON'T ❌

**LoadingState:**
- ❌ Create custom loading spinners
- ❌ Use for very short operations (<200ms)
- ❌ Skip loading message for long operations
- ❌ Use wrong size for context

**ErrorBanner:**
- ❌ Show raw error objects to users
- ❌ Forget to dismiss errors after successful retry
- ❌ Create custom error displays
- ❌ Use for success messages (use toast/banner instead)
- ❌ Block user interaction with errors

**ConfirmationDialog:**
- ❌ Use `window.confirm()` or `window.alert()`
- ❌ Use for non-destructive actions
- ❌ Use for simple notifications
- ❌ Skip confirmation for destructive actions
- ❌ Use generic messages ("Are you sure?")

---

## Testing

### Unit Tests

#### LoadingState Tests

```typescript
import { render, screen } from '@testing-library/react';
import { LoadingState } from './LoadingState';

describe('LoadingState', () => {
  it('should render with default message', () => {
    render(<LoadingState />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render with custom message', () => {
    render(<LoadingState message="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('should have role="status" for accessibility', () => {
    render(<LoadingState />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('should apply size classes', () => {
    const { container } = render(<LoadingState size="large" />);
    const spinner = container.querySelector('.h-12.w-12');
    expect(spinner).toBeInTheDocument();
  });
});
```

#### ErrorBanner Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBanner } from './ErrorBanner';

describe('ErrorBanner', () => {
  it('should render error string', () => {
    render(<ErrorBanner error="Test error" />);
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should render Error object message', () => {
    const error = new Error('Error message');
    render(<ErrorBanner error={error} />);
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('should render nothing when error is null', () => {
    const { container } = render(<ErrorBanner error={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('should call onDismiss when dismiss clicked', () => {
    const onDismiss = jest.fn();
    render(<ErrorBanner error="Test" onDismiss={onDismiss} />);

    const dismissButton = screen.getByLabelText('Dismiss error');
    fireEvent.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('should have role="alert" for accessibility', () => {
    render(<ErrorBanner error="Test" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
```

#### ConfirmationDialog Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmationDialog } from './ConfirmationDialog';

describe('ConfirmationDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    title: 'Delete Item?',
    message: 'This action cannot be undone.',
  };

  it('should render when isOpen is true', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Delete Item?')).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    render(<ConfirmationDialog {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Delete Item?')).not.toBeInTheDocument();
  });

  it('should call onConfirm when confirm clicked', () => {
    render(<ConfirmationDialog {...defaultProps} confirmText="Delete" />);

    const confirmButton = screen.getByText('Delete');
    fireEvent.click(confirmButton);

    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when cancel clicked', () => {
    render(<ConfirmationDialog {...defaultProps} />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('should close on Escape key', () => {
    render(<ConfirmationDialog {...defaultProps} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('should have role="dialog" and aria-modal', () => {
    render(<ConfirmationDialog {...defaultProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('should render danger variant button', () => {
    render(<ConfirmationDialog {...defaultProps} confirmVariant="danger" confirmText="Delete" />);

    const confirmButton = screen.getByText('Delete');
    expect(confirmButton).toHaveClass('bg-red-600');
  });
});
```

---

## Troubleshooting

### LoadingState Issues

**Issue:** Loading state flashes briefly

**Solutions:**
1. Add minimum display time with `setTimeout`
2. Use `isLoading && delay > 200` condition
3. Show skeleton UI instead for very short loads

**Issue:** Spinner not visible

**Solutions:**
1. Check background color contrast
2. Ensure component has height (use `min-h-[200px]`)
3. Verify no z-index conflicts

---

### ErrorBanner Issues

**Issue:** Error doesn't dismiss

**Solutions:**
1. Verify `onDismiss` is passed
2. Check `setError(null)` is called in `onDismiss`
3. Ensure error state is actually being updated

**Issue:** Error shows as "[object Object]"

**Solutions:**
1. Use `formatErrorMessage()` before passing to ErrorBanner
2. Ensure error has `message` property
3. Pass string error instead of object

---

### ConfirmationDialog Issues

**Issue:** Dialog won't close on Escape

**Solutions:**
1. Verify `onClose` is provided
2. Check for event listener conflicts
3. Ensure component is mounted when open

**Issue:** Multiple dialogs overlap

**Solutions:**
1. Use separate state for each dialog (`deleteConfirmId`, `approveConfirmId`)
2. Close other dialogs before opening new one
3. Increase z-index if needed

---

## Additional Resources

- **Frontend Patterns:** `docs/patterns/frontend-patterns.md`
- **Migration Guide:** `docs/guides/migration-guide-session-19.md`
- **Error Handler API:** `docs/api/error-handler.md`
- **Architecture:** `docs/architecture/session-19-improvements.md`

**Component Implementations:**
- `app/client/src/components/common/LoadingState.tsx`
- `app/client/src/components/common/ErrorBanner.tsx`
- `app/client/src/components/common/ConfirmationDialog.tsx`

**Tests:**
- `app/client/src/components/common/__tests__/LoadingState.test.tsx`
- `app/client/src/components/common/__tests__/ErrorBanner.test.tsx`
- `app/client/src/components/common/__tests__/ConfirmationDialog.test.tsx`

**Example Usage:**
- `app/client/src/components/ReviewPanel.tsx`
- `app/client/src/components/LogPanel.tsx`
- `app/client/src/components/TaskLogsView.tsx`
- `app/client/src/components/UserPromptsView.tsx`

---

**Reusable Components API Reference - Complete**

This reference covers all standardized UI components for the tac-webbuilder frontend with complete API documentation, usage patterns, and examples.
