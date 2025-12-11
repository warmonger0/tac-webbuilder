import React from 'react';

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

/**
 * Standardized error display component.
 *
 * @example
 * ```tsx
 * <ErrorBanner error={error} onDismiss={() => setError(null)} />
 * <ErrorBanner error="Something went wrong" title="Error" />
 * ```
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
          {/* Error Icon */}
          <svg
            className="h-5 w-5 text-red-400 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>

          {/* Error Content */}
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">{title}</h3>
            <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
          </div>
        </div>

        {/* Dismiss Button */}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-red-400 hover:text-red-600 transition-colors"
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
