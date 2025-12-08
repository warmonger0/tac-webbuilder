import { useState, useEffect } from 'react';
import { useWebhookStatusWebSocket } from '../hooks/useWebSocket';
import { ConnectionStatusIndicator } from './ConnectionStatusIndicator';
import { thresholds } from '../config/thresholds';

interface WebhookStatus {
  status: 'healthy' | 'degraded' | 'error' | 'unknown';
  uptime?: {
    hours: number;
    human: string;
  };
  stats?: {
    total_received: number;
    successful: number;
    failed: number;
    success_rate: string;
  };
  recent_failures?: Array<{
    issue: number;
    timestamp: string;
    error: string;
  }>;
  last_successful?: {
    issue: number;
    adw_id: string;
    workflow: string;
    timestamp: string;
  } | null;
}

export function WebhookStatusPanel() {
  const [status, setStatus] = useState<WebhookStatus>({ status: 'unknown' });
  const [error, setError] = useState<string | null>(null);

  // Use WebSocket for real-time updates instead of polling
  const { webhookStatus, isConnected, connectionQuality, lastUpdated } = useWebhookStatusWebSocket();

  // Update status when WebSocket data changes
  useEffect(() => {
    if (webhookStatus) {
      setStatus(webhookStatus);
      setError(null);
    }
  }, [webhookStatus]);

  const fetchStatus = () => {
    // WebSocket will automatically reconnect, no manual action needed
    window.location.reload();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✓';
      case 'degraded':
        return '⚠';
      case 'error':
        return '✗';
      default:
        return '?';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Workflow Status</h2>
          <div className="flex items-center gap-3">
            <ConnectionStatusIndicator
              isConnected={isConnected}
              connectionQuality={connectionQuality}
              lastUpdated={lastUpdated}
              consecutiveErrors={0}
              onRetry={fetchStatus}
              variant="compact"
            />
            <button
              onClick={fetchStatus}
              disabled={!isConnected}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Main Status Indicator */}
          <div className={`p-4 rounded-lg border ${getStatusColor(status.status)}`}>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{getStatusIcon(status.status)}</span>
              <div>
                <div className="font-semibold text-lg">
                  {getStatusText(status.status)}
                </div>
                {status.uptime && (
                  <div className="text-sm opacity-80">
                    Uptime: {status.uptime.human}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Statistics */}
          {status.stats && (
            <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="font-semibold text-gray-900 mb-2">Statistics</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Received:</span>
                  <span className="font-medium">{status.stats.total_received}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Successful:</span>
                  <span className="font-medium text-green-600">
                    {status.stats.successful}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Failed:</span>
                  <span className="font-medium text-red-600">
                    {status.stats.failed}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Success Rate:</span>
                  <span className="font-medium">{status.stats.success_rate}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Last Successful */}
        {status.last_successful && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
            <div className="text-sm font-medium text-green-900 mb-1">
              Last Successful Workflow
            </div>
            <div className="text-sm text-green-800">
              Issue #{status.last_successful.issue} • {status.last_successful.workflow} • ADW ID:{' '}
              {status.last_successful.adw_id}
            </div>
            <div className="text-xs text-green-700 mt-1">
              {new Date(status.last_successful.timestamp).toLocaleString()}
            </div>
          </div>
        )}

        {/* Recent Failures */}
        {status.recent_failures && status.recent_failures.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="text-sm font-medium text-yellow-900 mb-2">
              Recent Failures ({status.recent_failures.length})
            </div>
            <div className="space-y-2">
              {status.recent_failures.slice(0, thresholds.display.recentFailuresLimit).map((failure, idx) => (
                <div key={idx} className="text-xs text-yellow-800">
                  <span className="font-medium">Issue #{failure.issue}</span> •{' '}
                  {new Date(failure.timestamp).toLocaleString()}
                  <div className="text-yellow-700 mt-0.5 truncate">
                    {failure.error}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
