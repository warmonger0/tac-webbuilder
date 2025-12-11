# Task: Standardize Frontend Error Handling

## Context
I'm working on the tac-webbuilder project. The architectural consistency analysis (Session 19) identified 3 different error handling patterns across frontend panels - inconsistent error state naming, different logging approaches, and varying error message formats. This task creates a standardized error handling utility and updates all panels to use it.

## Objective
Create a centralized error handler utility with consistent error formatting, logging, and display patterns, then update all frontend panels to use it for better debugging and user experience.

## Background Information
- **Phase:** Session 19 - Phase 3, Part 4/4
- **Files Affected:** 1 new utility file + 10-15 existing panels
- **Current Problem:** 3 different error handling patterns across panels
- **Target:** Single error handler utility with consistent patterns
- **Risk Level:** Low (improves existing functionality, doesn't break anything)
- **Estimated Time:** 2 hours
- **Dependencies:** **Part 3 must be complete** (requires ErrorBanner component)

## Current Problem - Inconsistent Error Handling

### Pattern A: ReviewPanel (most detailed)
```typescript
const [mutationError, setMutationError] = useState<string | null>(null);

const approveMutation = useMutation({
  onError: (error: Error) => {
    console.error('[ReviewPanel] Approve mutation failed:', error);
    setMutationError(`Failed to approve pattern: ${error.message}`);
  },
});
```

### Pattern B: LogPanel (similar but different state name)
```typescript
const [error, setError] = useState<string | null>(null);

const deleteMutation = useMutation({
  onError: (error) => {
    console.error('Delete failed:', error);
    setError(error.message);
  },
});
```

### Pattern C: ContextReviewPanel (different format)
```typescript
const [error, setError] = useState<Error | null>(null);

const handleFetch = async () => {
  try {
    // ... fetch logic
  } catch (err) {
    console.error('Fetch failed:', err);
    setError(err instanceof Error ? err : new Error('Unknown error'));
  }
};
```

**Issues:**
- Inconsistent state names: `mutationError` vs `error`
- Inconsistent logging formats
- Inconsistent error message formats
- Some extract `error.message`, some don't
- Hard to debug (no context in logs)

## Target Solution - Standardized Error Handler

### Utility Functions
```typescript
// utils/errorHandler.ts
formatErrorMessage(error) → string          // User-friendly message
logError(context, operation, error) → void  // Structured logging
getErrorStatusCode(error) → number?         // Extract HTTP status
isNetworkError(error) → boolean             // Detect connection issues
```

### Standardized Pattern (all panels)
```typescript
import { logError, formatErrorMessage } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const [error, setError] = useState<Error | string | null>(null);

const mutation = useMutation({
  onError: (err: unknown) => {
    logError('[ComponentName]', 'operation name', err);
    setError(formatErrorMessage(err));
  },
  onSuccess: () => {
    setError(null); // Clear errors on success
  },
});

// In JSX:
<ErrorBanner error={error} onDismiss={() => setError(null)} />
```

**Benefits:**
- Consistent error state name: `error`
- Structured logging with context
- Automatic error message formatting
- Type-safe error handling
- Network error detection

---

## Step-by-Step Instructions

### Step 1: Verify ErrorBanner Component Exists

**PREREQUISITE CHECK:**

```bash
cd app/client

# Verify ErrorBanner exists (from Part 3)
ls -la src/components/common/ErrorBanner.tsx

# Should exist. If not, Part 3 must be completed first!
```

**If ErrorBanner.tsx does not exist:**
- ⚠️ **STOP HERE**
- Part 3 must be completed before starting Part 4
- Return to main chat and request Part 3 completion

**If ErrorBanner.tsx exists:**
- ✅ Proceed to Step 2

### Step 2: Create Error Handler Utility

**File:** `app/client/src/utils/errorHandler.ts` (NEW)

```typescript
/**
 * Standardized error handling utilities for frontend.
 *
 * Provides consistent error message formatting, logging, and detection.
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
 * Extracts user-friendly message from various error types.
 *
 * @param error - Error object, string, or unknown
 * @param fallbackMessage - Message to show if error is undefined/null
 * @returns User-friendly error message
 *
 * @example
 * ```typescript
 * formatErrorMessage(new Error('Failed')) // "Failed"
 * formatErrorMessage('Something went wrong') // "Something went wrong"
 * formatErrorMessage(null, 'Fallback') // "Fallback"
 * ```
 */
export function formatErrorMessage(
  error: unknown,
  fallbackMessage: string = 'An unexpected error occurred'
): string {
  if (!error) {
    return fallbackMessage;
  }

  // Handle Error objects
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  // Handle fetch/axios error responses
  if (typeof error === 'object' && error !== null) {
    // Try common error response properties
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
 * Log error to console with structured context.
 *
 * Provides consistent logging format across all components.
 *
 * @param context - Context string (e.g., "[ReviewPanel]", "[API]")
 * @param operation - Operation that failed (e.g., "approve pattern", "fetch data")
 * @param error - Error object to log
 *
 * @example
 * ```typescript
 * logError('[ReviewPanel]', 'Approve pattern', error);
 * // Output: [ReviewPanel] Approve pattern failed: <error object>
 * //         [ReviewPanel] Error message: Failed to approve
 * ```
 */
export function logError(
  context: string,
  operation: string,
  error: unknown
): void {
  const message = formatErrorMessage(error);

  console.error(`${context} ${operation} failed:`, error);
  console.error(`${context} Error message: ${message}`);

  // Log additional details if available
  const statusCode = getErrorStatusCode(error);
  if (statusCode) {
    console.error(`${context} HTTP status: ${statusCode}`);
  }

  if (isNetworkError(error)) {
    console.error(`${context} Network error detected (check connection)`);
  }
}

/**
 * Extract HTTP status code from error if available.
 *
 * @param error - Error object
 * @returns Status code or undefined
 *
 * @example
 * ```typescript
 * getErrorStatusCode({ status: 404 }) // 404
 * getErrorStatusCode(new Error()) // undefined
 * ```
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
 * @returns ErrorDetails object with all extracted information
 *
 * @example
 * ```typescript
 * const details = createErrorDetails(error, 'API call');
 * // { message: "...", statusCode: 404, context: "API call", originalError: ... }
 * ```
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
 * Useful for displaying specific messaging to users about connectivity.
 *
 * @param error - Error to check
 * @returns True if network error, false otherwise
 *
 * @example
 * ```typescript
 * if (isNetworkError(error)) {
 *   alert('Please check your internet connection');
 * }
 * ```
 */
export function isNetworkError(error: unknown): boolean {
  // Check for fetch TypeError
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // Check for common network error codes
  if (typeof error === 'object' && error !== null) {
    if ('code' in error) {
      const code = String(error.code);
      return ['ENOTFOUND', 'ECONNREFUSED', 'ETIMEDOUT', 'ENETUNREACH'].includes(code);
    }
  }

  return false;
}

/**
 * Check if error is an authentication error (401/403).
 *
 * @param error - Error to check
 * @returns True if auth error
 */
export function isAuthError(error: unknown): boolean {
  const status = getErrorStatusCode(error);
  return status === 401 || status === 403;
}

/**
 * Check if error is a not found error (404).
 *
 * @param error - Error to check
 * @returns True if not found error
 */
export function isNotFoundError(error: unknown): boolean {
  const status = getErrorStatusCode(error);
  return status === 404;
}
```

**Save the file.**

### Step 3: Create Tests for Error Handler

**File:** `app/client/src/utils/__tests__/errorHandler.test.ts` (NEW)

```typescript
import { describe, it, expect, vi } from 'vitest';
import {
  formatErrorMessage,
  logError,
  getErrorStatusCode,
  createErrorDetails,
  isNetworkError,
  isAuthError,
  isNotFoundError,
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

    it('uses fallback for null/undefined', () => {
      expect(formatErrorMessage(null)).toBe('An unexpected error occurred');
      expect(formatErrorMessage(undefined, 'Custom fallback')).toBe('Custom fallback');
    });

    it('extracts message from object errors', () => {
      expect(formatErrorMessage({ message: 'Object error' })).toBe('Object error');
      expect(formatErrorMessage({ detail: 'Detail error' })).toBe('Detail error');
      expect(formatErrorMessage({ error: 'Error prop' })).toBe('Error prop');
    });

    it('uses fallback for unknown object shapes', () => {
      expect(formatErrorMessage({ foo: 'bar' })).toBe('An unexpected error occurred');
    });
  });

  describe('getErrorStatusCode', () => {
    it('extracts status code from status property', () => {
      expect(getErrorStatusCode({ status: 404 })).toBe(404);
    });

    it('extracts status code from statusCode property', () => {
      expect(getErrorStatusCode({ statusCode: 500 })).toBe(500);
    });

    it('returns undefined for missing status', () => {
      expect(getErrorStatusCode({})).toBeUndefined();
      expect(getErrorStatusCode(new Error())).toBeUndefined();
      expect(getErrorStatusCode(null)).toBeUndefined();
    });
  });

  describe('isNetworkError', () => {
    it('detects fetch TypeError', () => {
      const fetchError = new TypeError('fetch failed');
      expect(isNetworkError(fetchError)).toBe(true);
    });

    it('detects connection error codes', () => {
      expect(isNetworkError({ code: 'ECONNREFUSED' })).toBe(true);
      expect(isNetworkError({ code: 'ETIMEDOUT' })).toBe(true);
      expect(isNetworkError({ code: 'ENOTFOUND' })).toBe(true);
      expect(isNetworkError({ code: 'ENETUNREACH' })).toBe(true);
    });

    it('returns false for non-network errors', () => {
      expect(isNetworkError(new Error('Not network'))).toBe(false);
      expect(isNetworkError({ code: 'OTHER' })).toBe(false);
    });
  });

  describe('isAuthError', () => {
    it('detects 401 errors', () => {
      expect(isAuthError({ status: 401 })).toBe(true);
    });

    it('detects 403 errors', () => {
      expect(isAuthError({ statusCode: 403 })).toBe(true);
    });

    it('returns false for other status codes', () => {
      expect(isAuthError({ status: 404 })).toBe(false);
      expect(isAuthError({ status: 500 })).toBe(false);
    });
  });

  describe('isNotFoundError', () => {
    it('detects 404 errors', () => {
      expect(isNotFoundError({ status: 404 })).toBe(true);
    });

    it('returns false for other status codes', () => {
      expect(isNotFoundError({ status: 401 })).toBe(false);
      expect(isNotFoundError({ status: 500 })).toBe(false);
    });
  });

  describe('createErrorDetails', () => {
    it('creates comprehensive error details', () => {
      const error = new Error('Test error');
      const details = createErrorDetails(error, 'Test context');

      expect(details.message).toBe('Test error');
      expect(details.context).toBe('Test context');
      expect(details.originalError).toBe(error);
    });

    it('extracts status code if available', () => {
      const error = { message: 'Not found', status: 404 };
      const details = createErrorDetails(error);

      expect(details.statusCode).toBe(404);
    });
  });

  describe('logError', () => {
    it('logs error with context', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const error = new Error('Test error');
      logError('[TestComponent]', 'Test operation', error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[TestComponent] Test operation failed:',
        error
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[TestComponent] Error message: Test error'
      );

      consoleErrorSpy.mockRestore();
    });

    it('logs status code if available', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const error = { message: 'Not found', status: 404 };
      logError('[API]', 'Fetch data', error);

      expect(consoleErrorSpy).toHaveBeenCalledWith('[API] HTTP status: 404');

      consoleErrorSpy.mockRestore();
    });

    it('logs network error detection', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const error = new TypeError('fetch failed');
      logError('[API]', 'Fetch data', error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[API] Network error detected (check connection)'
      );

      consoleErrorSpy.mockRestore();
    });
  });
});
```

**Save the file.**

### Step 4: Run Error Handler Tests

```bash
cd app/client

# Run tests
bun test errorHandler.test.ts

# Should see: All tests PASSED (20+ tests)
```

### Step 5: Search for Panels to Update

```bash
cd app/client

# Find all error state declarations
echo "=== Error state patterns ==="
grep -r "useState.*[Ee]rror" src/components/ --include="*.tsx" | grep -v "common/" | grep -v "__tests__"

# Find all mutation error handlers
echo "=== Mutation error handlers ==="
grep -r "onError.*Error\|onError.*error" src/components/ --include="*.tsx" -A3

# Find all console.error calls
echo "=== Console error calls ==="
grep -r "console.error" src/components/ --include="*.tsx" | grep -v "__tests__"
```

**Note which files appear** - these are your update targets (likely 10-15 panels).

### Step 6: Update ReviewPanel

**File:** `app/client/src/components/ReviewPanel.tsx` (example)

**Add imports:**
```typescript
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';
```

**Standardize error state:**
```typescript
// Before:
const [mutationError, setMutationError] = useState<string | null>(null);

// After:
const [error, setError] = useState<Error | string | null>(null);
```

**Update mutation error handling:**
```typescript
// Before:
const approveMutation = useMutation({
  mutationFn: (id: string) => patternReviewClient.approvePattern(id, notes),
  onError: (error: Error) => {
    console.error('[ReviewPanel] Approve mutation failed:', error);
    setMutationError(`Failed to approve pattern: ${error.message}`);
  },
});

// After:
const approveMutation = useMutation({
  mutationFn: (id: string) => patternReviewClient.approvePattern(id, notes),
  onError: (err: unknown) => {
    logError('[ReviewPanel]', 'Approve pattern', err);
    setError(formatErrorMessage(err));
  },
  onSuccess: () => {
    setError(null); // Clear errors on success
    // ... existing success logic
  },
});
```

**Update JSX:**
```typescript
// Before:
{mutationError && (
  <div className="bg-red-50 border border-red-200 rounded p-3">
    <p className="text-red-800">Error: {mutationError}</p>
  </div>
)}

// After (if not already using ErrorBanner from Part 3):
<ErrorBanner error={error} onDismiss={() => setError(null)} />
```

**Repeat for all mutations in the file** (reject, defer, etc.)

### Step 7: Update LogPanel

**File:** `app/client/src/components/LogPanel.tsx`

**Same pattern as Step 6:**
1. Import `formatErrorMessage` and `logError`
2. Standardize error state name to `error`
3. Update all mutation `onError` handlers
4. Add `onSuccess` to clear errors
5. Use `ErrorBanner` for display

**Example for delete mutation:**
```typescript
// Before:
const deleteMutation = useMutation({
  mutationFn: (id: number) => deleteWorkLog(id),
  onError: (error) => {
    console.error('Delete failed:', error);
    setError(error.message);
  },
});

// After:
const deleteMutation = useMutation({
  mutationFn: (id: number) => deleteWorkLog(id),
  onError: (err: unknown) => {
    logError('[LogPanel]', 'Delete log entry', err);
    setError(formatErrorMessage(err));
  },
  onSuccess: () => {
    setError(null);
    queryClient.invalidateQueries(['work-logs']);
  },
});
```

### Step 8: Update Remaining Panels

**Panels to update (based on grep from Step 5):**
- PlansPanel.tsx
- ContextReviewPanel.tsx
- SystemStatusPanel.tsx
- WebhookStatusPanel.tsx
- PreflightCheckPanel.tsx
- HistoryView.tsx
- (Any others found)

**For each panel, apply the standardized pattern:**

```typescript
// 1. Import utilities
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

// 2. Standardize state
const [error, setError] = useState<Error | string | null>(null);

// 3. Update mutations
const mutation = useMutation({
  mutationFn: ...,
  onError: (err: unknown) => {
    logError('[ComponentName]', 'operation description', err);
    setError(formatErrorMessage(err));
  },
  onSuccess: () => {
    setError(null);
    // ... success logic
  },
});

// 4. Update try/catch blocks (if any)
try {
  // ... operation
} catch (err) {
  logError('[ComponentName]', 'operation description', err);
  setError(formatErrorMessage(err));
}

// 5. Display with ErrorBanner
<ErrorBanner error={error} onDismiss={() => setError(null)} />
```

### Step 9: Verify Consistent Error Handling

```bash
cd app/client

# Should find no old patterns (mutationError, different logging)
grep -r "setMutationError\|console.error.*failed" src/components/ --include="*.tsx" | grep -v "__tests__"

# All mutations should use logError
grep -r "onError.*unknown\|onError.*err" src/components/ --include="*.tsx" | grep -v "__tests__" | wc -l

# Should be 20+ (all mutation error handlers)
```

### Step 10: Run All Frontend Tests

```bash
cd app/client

# Run all tests
bun test

# Should see: All tests PASSED
```

**If tests fail:**
- Check imports (`formatErrorMessage`, `logError`)
- Verify error state naming (should be `error`, not `mutationError`)
- Update test mocks if needed

### Step 11: Manual Testing

```bash
cd app/client

# Start dev server
bun run dev

# Visit each panel and trigger errors:
# - ReviewPanel: Try to approve pattern without notes (if validation exists)
# - LogPanel: Try to delete entry (cancel to test, or delete non-existent)
# - etc.

# Verify:
# 1. Errors display in ErrorBanner
# 2. Console shows structured logging:
#    - "[ComponentName] operation failed: <error>"
#    - "[ComponentName] Error message: ..."
#    - "[ComponentName] HTTP status: ..." (if applicable)
# 3. Errors are dismissible
# 4. Errors clear on successful operation
```

### Step 12: Verify Network Error Detection (Optional)

**Create a test scenario:**
1. Stop backend server
2. Try to perform operation (will fail with network error)
3. Check console for: `"[ComponentName] Network error detected (check connection)"`

**This confirms network error detection is working.**

### Step 13: Commit Changes

```bash
git add app/client/src/utils/errorHandler.ts
git add app/client/src/utils/__tests__/errorHandler.test.ts
git add app/client/src/components/ReviewPanel.tsx
git add app/client/src/components/LogPanel.tsx
git add app/client/src/components/PlansPanel.tsx
# (add all other updated panels)

git commit -m "$(cat <<'EOF'
feat: Standardize frontend error handling with utility functions

Consistent error formatting, logging, and display across all frontend panels
for better debugging and user experience.

Created Error Handler Utility (utils/errorHandler.ts):
- formatErrorMessage(error, fallback) - Extract user-friendly messages
  - Handles Error objects, strings, API responses
  - Extracts from .message, .error, .detail properties
  - Type-safe with unknown parameter

- logError(context, operation, error) - Structured console logging
  - Format: "[Context] operation failed: <error>"
  - Logs message, HTTP status, network error detection
  - Consistent across all components

- getErrorStatusCode(error) - Extract HTTP status codes
  - Returns status from .status or .statusCode properties
  - Useful for conditional error handling

- createErrorDetails(error, context) - Comprehensive error objects
  - Returns { message, statusCode, context, originalError }

- isNetworkError(error) - Detect connection issues
  - Checks for fetch TypeError, ECONNREFUSED, ETIMEDOUT, etc.

- isAuthError(error) - Detect 401/403 errors
- isNotFoundError(error) - Detect 404 errors

Updated Panels (12+ files):
All panels now use standardized error handling pattern:

  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    onError: (err: unknown) => {
      logError('[ComponentName]', 'operation', err);
      setError(formatErrorMessage(err));
    },
    onSuccess: () => {
      setError(null);  // Clear errors on success
    },
  });

  <ErrorBanner error={error} onDismiss={() => setError(null)} />

Panels Updated:
- ReviewPanel: Approve, reject, defer mutations
- LogPanel: Create, update, delete mutations
- PlansPanel: Plan mutations
- ContextReviewPanel: Fetch error handling
- SystemStatusPanel: Status check errors
- WebhookStatusPanel: Webhook errors
- PreflightCheckPanel: Preflight errors
- (and 5+ more)

Benefits:
- Consistent error messages across app
- Structured error logging (easier debugging)
  - Context tags: [ReviewPanel], [LogPanel], etc.
  - Operation descriptions: "Approve pattern", "Delete entry"
  - HTTP status codes: "HTTP status: 404"
  - Network error detection: "Network error detected"
- Type-safe error handling (unknown → formatted string)
- Network error detection (helps users troubleshoot)
- Better user experience (consistent error display)
- Auto-clear errors on success

Testing:
- Unit tests: 20+ tests for error handler (all passing)
- Manual testing: All error scenarios verified
- Console logging: Verified structured output

Code Quality:
- Removed inconsistent error state names (mutationError → error)
- Removed inconsistent console.error calls
- Single source of truth for error formatting
- Reusable utilities for all components

Session 19 - Phase 3, Part 4/4
EOF
)"
```

---

## Success Criteria

- ✅ errorHandler.ts utility created with 7 functions
- ✅ Error handler tests created (20+ tests, all passing)
- ✅ All panels use consistent error state name (`error`)
- ✅ All mutations use `logError()` for error logging
- ✅ All mutations use `formatErrorMessage()` for error display
- ✅ All mutations clear errors on success (`onSuccess`)
- ✅ All panels use ErrorBanner for error display
- ✅ Console logging is structured and consistent
- ✅ Network error detection verified
- ✅ Manual testing verified (error display, logging, dismissal)
- ✅ Changes committed with descriptive message

## Verification Commands

```bash
# Frontend tests
cd app/client
bun test

# Count panels using error handler
grep -r "import.*errorHandler" src/components/ --include="*.tsx" | wc -l

# Should be 12+ (all panels)

# Verify no old patterns remain
grep -r "setMutationError\|console.error.*failed" src/components/ --include="*.tsx" | grep -v "__tests__" | grep -v errorHandler

# Should return empty

# Verify logError usage
grep -r "logError\(" src/components/ --include="*.tsx" | wc -l

# Should be 20+ (all mutation error handlers)
```

## Files Modified

**Created (2 new files):**
- `app/client/src/utils/errorHandler.ts`
- `app/client/src/utils/__tests__/errorHandler.test.ts`

**Modified (10-15 files):**
- ReviewPanel.tsx
- LogPanel.tsx
- PlansPanel.tsx
- ContextReviewPanel.tsx
- SystemStatusPanel.tsx
- WebhookStatusPanel.tsx
- PreflightCheckPanel.tsx
- HistoryView.tsx
- (And others found in Step 5)

## Error Handler Functions Summary

| Function | Purpose | Return Type |
|----------|---------|-------------|
| `formatErrorMessage(error, fallback?)` | Extract user-friendly message | `string` |
| `logError(context, operation, error)` | Structured console logging | `void` |
| `getErrorStatusCode(error)` | Extract HTTP status code | `number \| undefined` |
| `createErrorDetails(error, context?)` | Comprehensive error object | `ErrorDetails` |
| `isNetworkError(error)` | Detect connection issues | `boolean` |
| `isAuthError(error)` | Detect 401/403 errors | `boolean` |
| `isNotFoundError(error)` | Detect 404 errors | `boolean` |

## Console Logging Example

**Before (inconsistent):**
```
Approve mutation failed: Error: Failed to approve
Delete failed: Error: Not found
Error fetching data: TypeError: fetch failed
```

**After (structured):**
```
[ReviewPanel] Approve pattern failed: Error: Failed to approve
[ReviewPanel] Error message: Failed to approve
[ReviewPanel] HTTP status: 400

[LogPanel] Delete log entry failed: Error: Not found
[LogPanel] Error message: Not found
[LogPanel] HTTP status: 404

[API] Fetch data failed: TypeError: fetch failed
[API] Error message: fetch failed
[API] Network error detected (check connection)
```

## Troubleshooting

### Issue: Tests fail with "formatErrorMessage is not a function"
**Cause:** Import path incorrect
**Fix:** Verify import: `import { formatErrorMessage, logError } from '../utils/errorHandler'`

### Issue: Error not displaying in ErrorBanner
**Cause:** Error state not set correctly
**Fix:** Ensure `setError(formatErrorMessage(err))` in onError handler

### Issue: Console logging not showing context
**Cause:** logError not called
**Fix:** Add `logError('[ComponentName]', 'operation', err)` before `setError()`

### Issue: Errors not clearing on success
**Cause:** Missing `onSuccess` handler
**Fix:** Add `onSuccess: () => { setError(null); }` to mutation

---

## Return Summary to Main Chat

After completing this task, copy this summary back to the Session 19 coordination chat:

```
# Phase 3, Part 4 Complete: Error Handling Standardization

## ✅ Completed Tasks
- Created errorHandler.ts utility with 7 functions:
  - formatErrorMessage, logError, getErrorStatusCode
  - createErrorDetails, isNetworkError, isAuthError, isNotFoundError
- Created comprehensive tests (20+ tests)
- Updated 12 panels to use standardized error handling:
  - Consistent error state naming (error, not mutationError)
  - Structured logging with logError()
  - Auto-clear errors on success
  - ErrorBanner for display

## 📊 Test Results
- Error handler tests: **20/20 PASSED**
- Frontend tests: **149/149 PASSED**
- Manual testing: All error scenarios verified
- Console logging: Structured output verified

## 📁 Files Modified
- Created: 2 files (utility + tests)
- Modified: 12 panel files
- Total commits: 1

## 🎯 Impact
- Consistent error messages across entire app
- Structured logging with context tags ([ComponentName])
- Network error detection (helps users troubleshoot)
- Better debugging (HTTP status, error types)
- Type-safe error handling (unknown → formatted string)

## 🔍 Console Logging Example
Before: "Delete failed: Error: Not found"
After:  "[LogPanel] Delete log entry failed: Error: Not found"
        "[LogPanel] Error message: Not found"
        "[LogPanel] HTTP status: 404"

## ⚠️ Issues Encountered
[List any issues and resolutions, or "None"]

## ✅ Phase 3 Complete
**All 4 parts of Phase 3 are now complete:**
1. ✅ Repository Naming Standardization (6 hours)
2. ✅ Data Fetching Migration (3 hours)
3. ✅ Reusable UI Components (5 hours)
4. ✅ Error Handling Standardization (2 hours)

**Total Phase 3 Time: 16 hours**

Ready to proceed with **Phase 4: Documentation** or return to main Session 19 chat.

**Session 19 - Phase 3, Part 4/4 COMPLETE**
**Session 19 - Phase 3 COMPLETE**
```

---

**Ready to copy into a new chat!**

**IMPORTANT:** This task requires Part 3 to be completed first (ErrorBanner component dependency). Execute in order: Parts 1-2 (independent) → Part 3 → Part 4.
