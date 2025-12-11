# Error Handler API Reference

Complete reference for the `errorHandler` utility functions that provide standardized error handling across the tac-webbuilder frontend.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Core Functions](#core-functions)
4. [Type Definitions](#type-definitions)
5. [Usage Patterns](#usage-patterns)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

---

## Overview

The `errorHandler` utility provides consistent error handling across all frontend components with:

- **User-friendly messages:** Extract readable messages from any error type
- **Structured logging:** Consistent console output with context tags
- **Type detection:** Identify network, auth, and 404 errors
- **HTTP status extraction:** Get status codes from errors
- **Type safety:** Works with TypeScript's `unknown` error type

**Location:** `app/client/src/utils/errorHandler.ts`

---

## Installation

The errorHandler utility is already available in the project. Import what you need:

```typescript
import {
  formatErrorMessage,
  logError,
  getErrorStatusCode,
  createErrorDetails,
  isNetworkError,
  isAuthError,
  isNotFoundError,
  type ErrorDetails
} from '../utils/errorHandler';
```

---

## Core Functions

### formatErrorMessage()

Extract user-friendly message from any error type.

**Signature:**
```typescript
function formatErrorMessage(
  error: unknown,
  fallbackMessage?: string
): string
```

**Parameters:**
- `error: unknown` - Error object, string, or any value
- `fallbackMessage?: string` - Message to show if error is undefined/null (default: "An unexpected error occurred")

**Returns:** `string` - User-friendly error message

**Examples:**
```typescript
// Error objects
formatErrorMessage(new Error('Failed'))
// → "Failed"

// String errors
formatErrorMessage('Something went wrong')
// → "Something went wrong"

// Null/undefined with fallback
formatErrorMessage(null, 'Custom fallback')
// → "Custom fallback"

// Objects with message property
formatErrorMessage({ message: 'API error' })
// → "API error"

// Objects with error property
formatErrorMessage({ error: 'Validation failed' })
// → "Validation failed"

// Objects with detail property (FastAPI format)
formatErrorMessage({ detail: 'Not found' })
// → "Not found"

// Undefined with default fallback
formatErrorMessage(undefined)
// → "An unexpected error occurred"
```

**Supported Error Formats:**
- `Error` objects (extracts `error.message`)
- String errors (returns as-is)
- Objects with `message` property
- Objects with `error` property
- Objects with `detail` property (FastAPI)
- `null`/`undefined` (returns fallback)

**Use Cases:**
- Displaying errors to users in ErrorBanner
- Creating user-friendly error messages
- Normalizing various error formats

---

### logError()

Log error to console with structured context.

**Signature:**
```typescript
function logError(
  context: string,
  operation: string,
  error: unknown
): void
```

**Parameters:**
- `context: string` - Context string identifying where error occurred (e.g., `"[ReviewPanel]"`, `"[API]"`)
- `operation: string` - Operation that failed (e.g., `"Approve pattern"`, `"Fetch data"`)
- `error: unknown` - Error object to log

**Returns:** `void`

**Console Output Format:**
```
[Context] Operation failed: <error object>
[Context] Error message: <formatted message>
[Context] HTTP status: <status code>  (if available)
[Context] Network error detected (check connection)  (if network error)
```

**Examples:**
```typescript
// Basic error logging
logError('[ReviewPanel]', 'Approve pattern', error);
// Console output:
// [ReviewPanel] Approve pattern failed: Error: Failed to approve
// [ReviewPanel] Error message: Failed to approve

// With HTTP status
logError('[API]', 'Fetch users', { status: 404, message: 'Not found' });
// Console output:
// [API] Fetch users failed: { status: 404, message: 'Not found' }
// [API] Error message: Not found
// [API] HTTP status: 404

// Network error
logError('[LogPanel]', 'Delete entry', new TypeError('fetch failed'));
// Console output:
// [LogPanel] Delete entry failed: TypeError: fetch failed
// [LogPanel] Error message: fetch failed
// [LogPanel] Network error detected (check connection)
```

**Use Cases:**
- Debugging in development
- Consistent log format across components
- Easy log filtering with context tags (`grep "\[ReviewPanel\]"`)
- Identifying network vs application errors

**Benefits:**
- **Searchable logs:** Context tags make logs easy to grep
- **Complete information:** Shows error object, message, status, and type
- **Consistent format:** Same pattern across all components
- **Debugging aid:** Helps identify error source and type

---

### getErrorStatusCode()

Extract HTTP status code from error if available.

**Signature:**
```typescript
function getErrorStatusCode(error: unknown): number | undefined
```

**Parameters:**
- `error: unknown` - Error object to extract status from

**Returns:** `number | undefined` - HTTP status code or undefined if not found

**Examples:**
```typescript
// Object with status property
getErrorStatusCode({ status: 404 })
// → 404

// Object with statusCode property
getErrorStatusCode({ statusCode: 500 })
// → 500

// Error object without status
getErrorStatusCode(new Error('Failed'))
// → undefined

// null/undefined
getErrorStatusCode(null)
// → undefined
```

**Supported Properties:**
- `error.status` (Fetch API, Axios)
- `error.statusCode` (Node.js HTTP)

**Use Cases:**
- Conditional error handling based on status
- Logging HTTP status codes
- Determining error severity
- Routing errors to appropriate handlers

---

### createErrorDetails()

Create standardized error details object.

**Signature:**
```typescript
function createErrorDetails(
  error: unknown,
  context?: string
): ErrorDetails
```

**Parameters:**
- `error: unknown` - Error to process
- `context?: string` - Context where error occurred

**Returns:** `ErrorDetails` - Object containing all extracted error information

**ErrorDetails Type:**
```typescript
interface ErrorDetails {
  message: string;         // User-friendly message
  statusCode?: number;     // HTTP status code (if available)
  context?: string;        // Context string
  originalError?: unknown; // Original error object
}
```

**Examples:**
```typescript
// Create error details
const details = createErrorDetails(
  { status: 404, message: 'Not found' },
  'API call'
);
// Returns:
// {
//   message: "Not found",
//   statusCode: 404,
//   context: "API call",
//   originalError: { status: 404, message: 'Not found' }
// }

// Without context
const details = createErrorDetails(new Error('Failed'));
// Returns:
// {
//   message: "Failed",
//   statusCode: undefined,
//   context: undefined,
//   originalError: Error: Failed
// }
```

**Use Cases:**
- Creating structured error objects for storage
- Passing error information to error reporting services
- Normalizing errors for consistent processing
- Error analytics and tracking

---

### isNetworkError()

Check if error is a network/connection error.

**Signature:**
```typescript
function isNetworkError(error: unknown): boolean
```

**Parameters:**
- `error: unknown` - Error to check

**Returns:** `boolean` - True if network error, false otherwise

**Detection Logic:**
- `TypeError` with "fetch" in message
- Error codes: `ENOTFOUND`, `ECONNREFUSED`, `ETIMEDOUT`, `ENETUNREACH`

**Examples:**
```typescript
// Fetch network error
isNetworkError(new TypeError('fetch failed'))
// → true

// Node.js connection error
isNetworkError({ code: 'ECONNREFUSED' })
// → true

// Regular error
isNetworkError(new Error('Not found'))
// → false

// HTTP error
isNetworkError({ status: 500 })
// → false
```

**Use Cases:**
- Display specific messaging for network issues
- Retry logic for connection errors
- Different handling for network vs application errors
- User notifications about connectivity

**Example Usage:**
```typescript
onError: (err: unknown) => {
  if (isNetworkError(err)) {
    setError('Network connection lost. Please check your internet connection.');
  } else {
    setError(formatErrorMessage(err));
  }
}
```

---

### isAuthError()

Check if error is an authentication error (401/403).

**Signature:**
```typescript
function isAuthError(error: unknown): boolean
```

**Parameters:**
- `error: unknown` - Error to check

**Returns:** `boolean` - True if status is 401 or 403

**Examples:**
```typescript
// 401 Unauthorized
isAuthError({ status: 401 })
// → true

// 403 Forbidden
isAuthError({ statusCode: 403 })
// → true

// 404 Not Found
isAuthError({ status: 404 })
// → false

// No status
isAuthError(new Error('Failed'))
// → false
```

**Use Cases:**
- Redirect to login page on auth failure
- Clear authentication tokens
- Show authentication-specific error messages
- Trigger re-authentication flow

**Example Usage:**
```typescript
onError: (err: unknown) => {
  if (isAuthError(err)) {
    // Clear tokens and redirect to login
    localStorage.removeItem('authToken');
    router.push('/login');
  } else {
    setError(formatErrorMessage(err));
  }
}
```

---

### isNotFoundError()

Check if error is a not found error (404).

**Signature:**
```typescript
function isNotFoundError(error: unknown): boolean
```

**Parameters:**
- `error: unknown` - Error to check

**Returns:** `boolean` - True if status is 404

**Examples:**
```typescript
// 404 Not Found
isNotFoundError({ status: 404 })
// → true

// 404 with statusCode property
isNotFoundError({ statusCode: 404 })
// → true

// 500 Internal Server Error
isNotFoundError({ status: 500 })
// → false

// No status
isNotFoundError(new Error('Failed'))
// → false
```

**Use Cases:**
- Display resource-specific error messages
- Conditional rendering for missing resources
- Navigation to 404 pages
- Logging missing resources

**Example Usage:**
```typescript
onError: (err: unknown) => {
  if (isNotFoundError(err)) {
    setError('Resource not found. It may have been deleted.');
  } else {
    setError(formatErrorMessage(err));
  }
}
```

---

## Type Definitions

### ErrorDetails

```typescript
interface ErrorDetails {
  message: string;         // User-friendly error message
  statusCode?: number;     // HTTP status code (if available)
  context?: string;        // Context where error occurred
  originalError?: unknown; // Original error object
}
```

**Properties:**
- `message` - Formatted, user-friendly error message
- `statusCode` - HTTP status code extracted from error (optional)
- `context` - String identifying where error occurred (optional)
- `originalError` - Original error object for debugging (optional)

**Usage:**
```typescript
const details: ErrorDetails = createErrorDetails(error, '[API]');

// Access properties
console.log(details.message);       // "Not found"
console.log(details.statusCode);    // 404
console.log(details.context);       // "[API]"
console.log(details.originalError); // Original error object
```

---

## Usage Patterns

### Pattern 1: Standard Error Handling in Mutations

```typescript
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const MyComponent = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    mutationFn: submitData,

    onError: (err: unknown) => {
      // 1. Log with context for debugging
      logError('[MyComponent]', 'Submit data', err);

      // 2. Set user-friendly error message
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      // 3. Clear errors on success
      setError(null);
    },
  });

  return (
    <div>
      {/* 4. Display error */}
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <button onClick={() => mutation.mutate(data)}>
        Submit
      </button>
    </div>
  );
};
```

---

### Pattern 2: Conditional Error Handling

```typescript
import {
  formatErrorMessage,
  logError,
  isNetworkError,
  isAuthError,
  isNotFoundError
} from '../utils/errorHandler';

const mutation = useMutation({
  mutationFn: apiCall,

  onError: (err: unknown) => {
    // Log all errors
    logError('[Component]', 'API call', err);

    // Handle based on error type
    if (isAuthError(err)) {
      // Redirect to login
      router.push('/login');
      return;
    }

    if (isNetworkError(err)) {
      setError('Network connection lost. Please check your internet connection.');
      return;
    }

    if (isNotFoundError(err)) {
      setError('Resource not found. It may have been deleted.');
      return;
    }

    // Default error handling
    setError(formatErrorMessage(err));
  },
});
```

---

### Pattern 3: Error Details for Reporting

```typescript
import { createErrorDetails } from '../utils/errorHandler';

const reportError = (error: unknown, context: string) => {
  const details = createErrorDetails(error, context);

  // Send to error reporting service
  errorReportingService.log({
    message: details.message,
    statusCode: details.statusCode,
    context: details.context,
    timestamp: Date.now(),
    userAgent: navigator.userAgent,
    url: window.location.href,
  });
};

// Usage in component
onError: (err: unknown) => {
  reportError(err, '[PaymentForm]');
  setError(formatErrorMessage(err));
}
```

---

### Pattern 4: Retry Logic for Network Errors

```typescript
import { isNetworkError, logError } from '../utils/errorHandler';

const mutation = useMutation({
  mutationFn: apiCall,
  retry: (failureCount, error) => {
    // Only retry network errors up to 3 times
    if (isNetworkError(error) && failureCount < 3) {
      logError('[Component]', `Retry ${failureCount + 1}/3`, error);
      return true;
    }
    return false;
  },
  retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
});
```

---

## Examples

### Example 1: Review Panel Error Handling

```typescript
// From: app/client/src/components/ReviewPanel.tsx
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const ReviewPanel = () => {
  const [error, setError] = useState<Error | string | null>(null);

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

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deletePattern(id),

    onError: (err: unknown) => {
      logError('[ReviewPanel]', 'Delete pattern', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
    },
  });

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <button onClick={() => approveMutation.mutate(patternId)}>
        Approve
      </button>
      <button onClick={() => deleteMutation.mutate(patternId)}>
        Delete
      </button>
    </div>
  );
};
```

---

### Example 2: Log Panel Error Handling

```typescript
// From: app/client/src/components/LogPanel.tsx
import { formatErrorMessage, logError } from '../utils/errorHandler';
import { ErrorBanner } from './common/ErrorBanner';

const LogPanel = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteLogEntry(id),

    onError: (err: unknown) => {
      logError('[LogPanel]', 'Delete log entry', err);
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['work-logs'] });
    },
  });

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {/* Component content */}
    </div>
  );
};
```

---

### Example 3: Advanced Error Handling with Retries

```typescript
import {
  formatErrorMessage,
  logError,
  isNetworkError,
  isAuthError,
  getErrorStatusCode
} from '../utils/errorHandler';

const AdvancedComponent = () => {
  const [error, setError] = useState<Error | string | null>(null);

  const mutation = useMutation({
    mutationFn: complexApiCall,

    // Retry configuration
    retry: (failureCount, err) => {
      // Don't retry auth errors
      if (isAuthError(err)) return false;

      // Retry network errors up to 3 times
      if (isNetworkError(err) && failureCount < 3) return true;

      // Retry 5xx errors once
      const statusCode = getErrorStatusCode(err);
      if (statusCode && statusCode >= 500 && failureCount < 1) return true;

      return false;
    },

    retryDelay: attemptIndex => {
      // Exponential backoff: 1s, 2s, 4s
      return Math.min(1000 * 2 ** attemptIndex, 10000);
    },

    onError: (err: unknown) => {
      logError('[AdvancedComponent]', 'Complex API call', err);

      if (isAuthError(err)) {
        // Handle auth errors
        router.push('/login');
        return;
      }

      if (isNetworkError(err)) {
        setError('Network connection lost. Please check your internet connection and try again.');
        return;
      }

      const statusCode = getErrorStatusCode(err);
      if (statusCode && statusCode >= 500) {
        setError('Server error. Our team has been notified. Please try again later.');
        return;
      }

      // Default error message
      setError(formatErrorMessage(err));
    },

    onSuccess: () => {
      setError(null);
    },
  });

  return (
    <div>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {/* Component content */}
    </div>
  );
};
```

---

## Best Practices

### DO ✅

**Error Logging:**
- ✅ Use `logError()` for all error logging
- ✅ Include context tags (e.g., `"[ComponentName]"`)
- ✅ Include operation description (e.g., `"Approve pattern"`)
- ✅ Log errors before displaying to user

**Error Display:**
- ✅ Use `formatErrorMessage()` for user-facing messages
- ✅ Provide fallback messages for undefined errors
- ✅ Use ErrorBanner component for display
- ✅ Allow users to dismiss errors

**Error Handling:**
- ✅ Clear errors on success (`onSuccess: () => setError(null)`)
- ✅ Use type detection functions (`isNetworkError`, `isAuthError`, etc.)
- ✅ Handle different error types differently
- ✅ Provide specific messages for network/auth errors

**Type Safety:**
- ✅ Use `unknown` type for error parameters
- ✅ Type error state as `Error | string | null`
- ✅ Use TypeScript's type guards

### DON'T ❌

**Error Logging:**
- ❌ Use `console.error` directly
- ❌ Log errors without context
- ❌ Skip error logging
- ❌ Use different log formats across components

**Error Display:**
- ❌ Show raw error objects to users
- ❌ Display technical error messages
- ❌ Leave errors undefined
- ❌ Create custom error display components

**Error Handling:**
- ❌ Ignore errors silently
- ❌ Forget to clear errors on success
- ❌ Use same message for all error types
- ❌ Block UI indefinitely on error

**Type Safety:**
- ❌ Type errors as `any`
- ❌ Assume error structure
- ❌ Access error properties without checking
- ❌ Skip type guards

---

## Testing

### Unit Tests

```typescript
import {
  formatErrorMessage,
  logError,
  getErrorStatusCode,
  isNetworkError,
  isAuthError,
  isNotFoundError,
  createErrorDetails
} from '../errorHandler';

describe('errorHandler', () => {
  describe('formatErrorMessage', () => {
    it('should format Error objects', () => {
      const error = new Error('Test error');
      expect(formatErrorMessage(error)).toBe('Test error');
    });

    it('should format string errors', () => {
      expect(formatErrorMessage('Error text')).toBe('Error text');
    });

    it('should use fallback for null', () => {
      expect(formatErrorMessage(null, 'Fallback')).toBe('Fallback');
    });

    it('should extract message from objects', () => {
      expect(formatErrorMessage({ message: 'Object error' })).toBe('Object error');
    });
  });

  describe('getErrorStatusCode', () => {
    it('should extract status from object', () => {
      expect(getErrorStatusCode({ status: 404 })).toBe(404);
    });

    it('should extract statusCode from object', () => {
      expect(getErrorStatusCode({ statusCode: 500 })).toBe(500);
    });

    it('should return undefined for errors without status', () => {
      expect(getErrorStatusCode(new Error())).toBeUndefined();
    });
  });

  describe('isNetworkError', () => {
    it('should detect fetch TypeError', () => {
      const error = new TypeError('fetch failed');
      expect(isNetworkError(error)).toBe(true);
    });

    it('should detect ECONNREFUSED', () => {
      expect(isNetworkError({ code: 'ECONNREFUSED' })).toBe(true);
    });

    it('should return false for non-network errors', () => {
      expect(isNetworkError(new Error('Not found'))).toBe(false);
    });
  });

  describe('isAuthError', () => {
    it('should detect 401', () => {
      expect(isAuthError({ status: 401 })).toBe(true);
    });

    it('should detect 403', () => {
      expect(isAuthError({ statusCode: 403 })).toBe(true);
    });

    it('should return false for 404', () => {
      expect(isAuthError({ status: 404 })).toBe(false);
    });
  });

  describe('isNotFoundError', () => {
    it('should detect 404', () => {
      expect(isNotFoundError({ status: 404 })).toBe(true);
    });

    it('should return false for 500', () => {
      expect(isNotFoundError({ status: 500 })).toBe(false);
    });
  });

  describe('createErrorDetails', () => {
    it('should create complete error details', () => {
      const error = { status: 404, message: 'Not found' };
      const details = createErrorDetails(error, 'API');

      expect(details).toEqual({
        message: 'Not found',
        statusCode: 404,
        context: 'API',
        originalError: error
      });
    });
  });
});
```

---

## Troubleshooting

### Issue: Error message is generic

**Problem:** User sees "An unexpected error occurred" instead of specific message

**Solutions:**
1. Check if error has `message`, `error`, or `detail` property
2. Pass custom fallback message to `formatErrorMessage()`
3. Log error to see structure: `console.log(error)`
4. Verify API returns proper error format

### Issue: Console logs are inconsistent

**Problem:** Different log formats across components

**Solutions:**
1. Always use `logError()` instead of `console.error()`
2. Include context tag (e.g., `"[ComponentName]"`)
3. Follow pattern: `logError('[Context]', 'Operation', error)`

### Issue: Network errors not detected

**Problem:** `isNetworkError()` returns false for connection errors

**Solutions:**
1. Check error structure in console
2. Verify error is TypeError with "fetch" in message
3. Check for error.code property
4. Add custom network error detection if needed

---

## Additional Resources

- **Frontend Patterns:** `docs/patterns/frontend-patterns.md`
- **Migration Guide:** `docs/guides/migration-guide-session-19.md`
- **ErrorBanner Component:** `docs/api/reusable-components.md#errorbanner`
- **Implementation:** `app/client/src/utils/errorHandler.ts`
- **Tests:** `app/client/src/utils/__tests__/errorHandler.test.ts`

---

**Error Handler API Reference - Complete**

This reference covers all errorHandler utility functions for standardized error handling in the tac-webbuilder frontend.
