import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary for AdwMonitorCard component.
 * Catches render errors and displays a fallback UI with recovery options.
 */
export class AdwMonitorErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details for debugging
    console.error('[AdwMonitorErrorBoundary] Component error caught:', error);
    console.error('[AdwMonitorErrorBoundary] Error info:', errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="bg-gradient-to-br from-red-50 to-rose-100 rounded-lg shadow-xl border border-red-200 p-8 flex-1">
          <div className="flex flex-col items-center text-center">
            {/* Error Icon */}
            <div className="relative mb-4">
              <div className="absolute -inset-1 bg-gradient-to-r from-red-400/20 to-rose-400/20 rounded-full blur-md"></div>
              <div className="relative w-16 h-16 bg-gradient-to-r from-red-500 to-rose-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
            </div>

            {/* Error Message */}
            <h3 className="text-lg font-bold text-red-800 mb-2">
              Something went wrong
            </h3>
            <p className="text-red-700 text-sm mb-1">
              The workflow monitor encountered an error and couldn't render properly.
            </p>

            {/* Error Details (collapsible in production, shown here for debugging) */}
            {this.state.error && (
              <div className="mt-4 p-3 bg-red-100 border border-red-300 rounded-lg text-left w-full max-w-md">
                <p className="text-xs font-mono text-red-800 break-words">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            {/* Reset Button */}
            <button
              onClick={this.handleReset}
              className="mt-6 px-6 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium rounded-lg hover:from-red-600 hover:to-rose-700 transition-all shadow-lg hover:shadow-xl"
            >
              Reset Monitor
            </button>

            {/* Recovery Instructions */}
            <div className="mt-6 p-4 bg-white/50 rounded-lg border border-red-200 text-left w-full max-w-md">
              <h4 className="text-sm font-semibold text-red-800 mb-2">
                Recovery Steps:
              </h4>
              <ul className="text-xs text-red-700 space-y-1">
                <li className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">•</span>
                  <span>Try refreshing the page</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">•</span>
                  <span>Check browser console for detailed error logs</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">•</span>
                  <span>Contact support if the issue persists</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
