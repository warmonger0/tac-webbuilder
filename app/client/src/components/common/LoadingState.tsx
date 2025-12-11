import React from 'react';

interface LoadingStateProps {
  /** Message to display below spinner */
  message?: string;

  /** Size of spinner */
  size?: 'small' | 'medium' | 'large';

  /** Additional CSS classes */
  className?: string;
}

/**
 * Standardized loading state component with spinner.
 *
 * @example
 * ```tsx
 * <LoadingState message="Loading data..." />
 * <LoadingState size="small" />
 * ```
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
