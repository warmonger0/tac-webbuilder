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
