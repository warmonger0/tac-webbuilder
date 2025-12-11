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
