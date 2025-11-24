/**
 * WorkflowStateDisplay Component
 *
 * Displays real-time ADW workflow state updates via WebSocket.
 * Shows status, progress, and other workflow information.
 */

import { useADWStateWebSocket } from '../hooks/useWebSocket';

interface WorkflowStateDisplayProps {
  adwId: string | null;
}

export function WorkflowStateDisplay({ adwId }: WorkflowStateDisplayProps) {
  const { state, isConnected } = useADWStateWebSocket(adwId);

  // Don't render if no ADW ID
  if (!adwId) {
    return null;
  }

  // Show loading state while connecting
  if (!isConnected || !state) {
    return (
      <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="animate-spin">⚙️</span>
          <span>Connecting to workflow...</span>
        </div>
      </div>
    );
  }

  // Determine status color
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="mt-2 p-3 bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-gray-700">Workflow State</h5>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>

      {/* Status */}
      {state.status && (
        <div className="mb-2">
          <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${getStatusColor(state.status)}`}>
            {state.status.toUpperCase()}
          </span>
        </div>
      )}

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {state.issue_number && (
          <div>
            <span className="text-gray-500">Issue:</span>{' '}
            <span className="font-medium text-gray-900">#{state.issue_number}</span>
          </div>
        )}

        {state.model_set && (
          <div>
            <span className="text-gray-500">Model:</span>{' '}
            <span className="font-medium text-gray-900">{state.model_set}</span>
          </div>
        )}

        {state.workflow_template && (
          <div className="col-span-2">
            <span className="text-gray-500">Template:</span>{' '}
            <span className="font-medium text-gray-900">{state.workflow_template}</span>
          </div>
        )}

        {state.start_time && (
          <div className="col-span-2">
            <span className="text-gray-500">Started:</span>{' '}
            <span className="font-medium text-gray-900">
              {new Date(state.start_time).toLocaleString()}
            </span>
          </div>
        )}

        {state.backend_port && (
          <div>
            <span className="text-gray-500">Backend:</span>{' '}
            <span className="font-medium text-gray-900">:{state.backend_port}</span>
          </div>
        )}

        {state.frontend_port && (
          <div>
            <span className="text-gray-500">Frontend:</span>{' '}
            <span className="font-medium text-gray-900">:{state.frontend_port}</span>
          </div>
        )}

        {state.all_adws && state.all_adws.length > 0 && (
          <div className="col-span-2">
            <span className="text-gray-500">Workflows:</span>{' '}
            <span className="font-medium text-gray-900">{state.all_adws.join(', ')}</span>
          </div>
        )}
      </div>

      {/* ADW ID (small at bottom) */}
      <div className="mt-2 pt-2 border-t border-gray-100">
        <span className="text-xs text-gray-400">ADW ID: {state.adw_id}</span>
      </div>
    </div>
  );
}
