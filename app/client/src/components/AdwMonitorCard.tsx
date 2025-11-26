import { useState } from 'react';
import {
  type AdwMonitorSummary,
  type AdwWorkflowStatus,
  getAdwMonitor
} from '../api/client';
import { useReliableWebSocket } from '../hooks/useReliableWebSocket';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { ConnectionStatusIndicator } from './ConnectionStatusIndicator';
import { WorkflowPipelineView } from './WorkflowPipelineView';
import { LoadingSkeleton } from './LoadingSkeleton';

// eslint-disable-next-line max-lines-per-function
export function AdwMonitorCard() {
  const [workflows, setWorkflows] = useState<AdwWorkflowStatus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const prefersReducedMotion = useReducedMotion();

  // Use relative WebSocket URL to go through Vite proxy
  const wsUrl = '/ws/adw-monitor';

  const connectionState = useReliableWebSocket<
    { workflows: AdwWorkflowStatus[]; summary: AdwMonitorSummary },
    { workflows: AdwWorkflowStatus[]; summary: AdwMonitorSummary }
  >({
    url: wsUrl,
    queryKey: ['adw-monitor'],
    queryFn: getAdwMonitor,
    onMessage: (data) => {
      setWorkflows(data.workflows);
      setError(null);
    },
    enabled: true,
    pollingInterval: 10000, // 10 seconds fallback polling
    maxReconnectDelay: 30000, // 30 seconds maximum
    maxReconnectAttempts: 10, // matches exponential backoff spec
  });

  // Monitor connection state and show error when disconnected with retries
  const maxReconnectAttempts = 10;
  const shouldShowConnectionError =
    !connectionState.isConnected &&
    (connectionState.reconnectAttempts > 0 || connectionState.connectionQuality === 'disconnected');

  if (!connectionState.isConnected && workflows.length === 0) {
    return <LoadingSkeleton />;
  }

  // Show connection error if disconnected
  if (shouldShowConnectionError && workflows.length === 0) {
    // Determine error message based on connection state
    let errorMessage = 'Unable to connect to server';
    let errorDetail = '';

    if (connectionState.reconnectAttempts === 0) {
      errorMessage = 'Unable to connect to server';
      errorDetail = 'The workflow monitor could not establish a connection.';
    } else if (connectionState.reconnectAttempts > 0 && connectionState.reconnectAttempts < maxReconnectAttempts) {
      errorMessage = 'Connection lost. Retrying...';
      errorDetail = `Attempt ${connectionState.reconnectAttempts}/${maxReconnectAttempts}`;
    } else if (connectionState.reconnectAttempts >= maxReconnectAttempts) {
      errorMessage = 'Connection failed after multiple attempts';
      errorDetail = 'Falling back to polling mode. Updates may be delayed.';
    }

    return (
      <div
        className="bg-gradient-to-br from-red-50 to-rose-100 rounded-lg shadow-xl border border-red-200 p-8 flex-1"
        role="region"
        aria-label="Connection Error"
      >
        <div className="flex flex-col items-center text-center">
          {/* Error Icon */}
          <div className="relative mb-4">
            <div className="absolute -inset-1 bg-gradient-to-r from-red-400/20 to-rose-400/20 rounded-full blur-md"></div>
            <div className="relative w-16 h-16 bg-gradient-to-r from-red-500 to-rose-600 rounded-full flex items-center justify-center shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>

          {/* Error Message */}
          <div
            role="alert"
            aria-live="assertive"
            aria-atomic="true"
          >
            <p className="text-red-700 font-semibold mb-1">{errorMessage}</p>
            <p className="text-red-600 text-sm mb-4">{errorDetail}</p>
          </div>

          {/* Retry Button */}
          <button
            onClick={connectionState.retry}
            className="px-6 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium rounded-lg hover:from-red-600 hover:to-rose-700 transition-all shadow-lg hover:shadow-xl mb-6 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
            aria-label={`Retry connection now. Attempt ${connectionState.reconnectAttempts} of ${maxReconnectAttempts}`}
          >
            Retry Now
          </button>

          {/* Recovery Instructions */}
          <div className="p-4 bg-white/50 rounded-lg border border-red-200 text-left w-full max-w-sm">
            <h4 className="text-sm font-semibold text-red-800 mb-2">Recovery Steps:</h4>
            <ul className="text-xs text-red-700 space-y-1">
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">•</span>
                <span>Check your internet connection</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">•</span>
                <span>Verify the backend server is running</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">•</span>
                <span>Refresh the page if the issue persists</span>
              </li>
            </ul>
          </div>

          {/* Show polling mode indicator if degraded */}
          {connectionState.reconnectAttempts >= maxReconnectAttempts && (
            <div className="mt-4 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
              <p className="text-xs text-yellow-800">
                <strong>Polling Mode Active:</strong> Updates will continue via HTTP polling every 10 seconds.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show general error (non-connection related)
  if (error) {
    return (
      <div
        className="bg-gradient-to-br from-red-50 to-rose-100 rounded-lg shadow-xl border border-red-200 p-8 flex-1"
        role="region"
        aria-label="Error Loading Workflows"
      >
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-rose-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div role="alert" aria-live="assertive" aria-atomic="true">
            <p className="text-red-700 font-semibold mb-2">Unable to load workflows</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // Get only the current (first) workflow in the queue
  const currentWorkflow = workflows.length > 0 ? workflows[0] : null;

  // Determine colors based on workflow status
  const getStatusColors = (status: string) => {
    switch (status) {
      case 'failed':
        return {
          card: 'shadow-red-500/10',
          cardGlow: 'from-red-500/5 to-red-500/5',
          header: 'from-red-500/10 to-red-500/10',
          icon: 'from-red-500 to-red-600',
          iconShadow: 'shadow-[0_0_15px_rgba(239,68,68,0.5)]',
          iconGlow: 'from-red-400/20 to-red-400/20',
          innerGlow: 'from-red-500/5'
        };
      case 'running':
        return {
          card: 'shadow-emerald-500/10',
          cardGlow: 'from-emerald-500/5 to-teal-500/5',
          header: 'from-emerald-500/10 to-teal-500/10',
          icon: 'from-emerald-500 to-teal-500',
          iconShadow: 'shadow-[0_0_15px_rgba(16,185,129,0.5)]',
          iconGlow: 'from-emerald-400/20 to-teal-400/20',
          innerGlow: 'from-emerald-500/5'
        };
      case 'paused':
        return {
          card: 'shadow-yellow-500/10',
          cardGlow: 'from-yellow-500/5 to-orange-500/5',
          header: 'from-yellow-500/10 to-orange-500/10',
          icon: 'from-yellow-500 to-orange-500',
          iconShadow: 'shadow-[0_0_15px_rgba(234,179,8,0.5)]',
          iconGlow: 'from-yellow-400/20 to-orange-400/20',
          innerGlow: 'from-yellow-500/5'
        };
      default: // completed, queued, etc.
        return {
          card: 'shadow-slate-500/10',
          cardGlow: 'from-slate-500/5 to-slate-500/5',
          header: 'from-slate-500/10 to-slate-500/10',
          icon: 'from-slate-500 to-slate-600',
          iconShadow: 'shadow-[0_0_15px_rgba(100,116,139,0.5)]',
          iconGlow: 'from-slate-400/20 to-slate-400/20',
          innerGlow: 'from-slate-500/5'
        };
    }
  };

  const colors = getStatusColors(currentWorkflow?.status || 'completed');

  return (
    <div
      className={`bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl ${colors.card} overflow-hidden border border-slate-700 flex-1 flex flex-col relative`}
      role="region"
      aria-label="ADW Workflow Monitor"
    >
        {/* Subtle status-based glow around the card */}
        <div className={`absolute -inset-0.5 bg-gradient-to-r ${colors.cardGlow} rounded-lg blur-sm -z-10`}></div>

      {/* Header with Gradient */}
      <div className="relative px-4 py-3 border-b border-slate-700/50">
        <div className={`absolute inset-0 bg-gradient-to-r ${colors.header}`}></div>
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`relative w-8 h-8 bg-gradient-to-r ${colors.icon} rounded-lg flex items-center justify-center ${colors.iconShadow}`}>
                {/* Icon glow */}
                <div className={`absolute -inset-1 bg-gradient-to-r ${colors.iconGlow} rounded-lg blur-md ${prefersReducedMotion ? '' : 'animate-pulse'}`}></div>
                <svg className="w-5 h-5 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                  Current Workflow
                </h2>
                <p className="text-slate-400 text-xs">Real-time progress</p>
              </div>
            </div>
            <div aria-live="polite" aria-atomic="true">
              <ConnectionStatusIndicator
                isConnected={connectionState.isConnected}
                connectionQuality={connectionState.connectionQuality}
                lastUpdated={connectionState.lastUpdated}
                reconnectAttempts={connectionState.reconnectAttempts}
                variant="compact"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Display */}
      <div className="p-5 flex-1 flex flex-col">
        {!currentWorkflow ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-slate-300 mb-1">No Active Workflow</p>
            <p className="text-slate-500 text-sm">Queue is empty</p>
          </div>
        ) : (
          <WorkflowPipelineView workflow={currentWorkflow} colors={colors} />
        )}
      </div>

      <style>{`
        /* Accessibility: Disable animations when user prefers reduced motion */
        @media (prefers-reduced-motion: reduce) {
          * {
            animation: none !important;
            transition: none !important;
          }
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgb(30 41 59);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgb(71 85 105);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgb(100 116 139);
        }

        @keyframes flowDot {
          0% {
            left: -4px;
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            left: calc(100% + 4px);
            opacity: 0;
          }
        }

        @keyframes flowToCenter {
          0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
          }
          50% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
            opacity: 0.3;
          }
          25% {
            opacity: 0.6;
          }
          50% {
            transform: translateY(-20px) translateX(10px);
            opacity: 0.8;
          }
          75% {
            opacity: 0.6;
          }
        }

        @keyframes flowFromCenter {
          0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
          }
          20% {
            opacity: 1;
          }
          80% {
            opacity: 1;
          }
          100% {
            opacity: 0;
            transform: translate(calc(-50% + var(--flow-x)), calc(-50% + var(--flow-y))) scale(1.2);
          }
        }
      `}</style>
    </div>
  );
}
