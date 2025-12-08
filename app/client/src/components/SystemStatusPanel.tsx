import React, { useState, useEffect } from 'react';
import { redeliverGitHubWebhook, restartCloudflare, startWebhookService } from '../api/client';
import type { ServiceHealth, SystemStatusResponse } from '../types';
import { useSystemStatusWebSocket } from '../hooks/useWebSocket';
import { ConnectionStatusIndicator } from './ConnectionStatusIndicator';
import { PreflightCheckPanel } from './PreflightCheckPanel';
import { intervals } from '../config/intervals';
import { serviceDisplayOrder } from '../config/services';

export function SystemStatusPanel() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  // Use WebSocket for real-time updates instead of polling
  const { systemStatus, isConnected, connectionQuality, lastUpdated } = useSystemStatusWebSocket();

  // Update status when WebSocket data changes
  useEffect(() => {
    if (systemStatus) {
      setStatus(systemStatus);
      setError(null);
    }
  }, [systemStatus]);

  // Manual refresh function (re-connects WebSocket)
  const fetchStatus = () => {
    // WebSocket will automatically reconnect, no manual action needed
    window.location.reload();
  };

  const getStatusColor = (serviceStatus: string) => {
    switch (serviceStatus) {
      case 'healthy':
        return 'bg-emerald-900/30 text-emerald-200 border-emerald-500/50';
      case 'degraded':
        return 'bg-yellow-900/30 text-yellow-200 border-yellow-500/50';
      case 'error':
        return 'bg-red-900/30 text-red-200 border-red-500/50';
      default:
        return 'bg-slate-700/30 text-slate-300 border-slate-500/50';
    }
  };

  const getStatusIcon = (serviceStatus: string) => {
    switch (serviceStatus) {
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

  const getOverallStatusColor = (overallStatus: string) => {
    switch (overallStatus) {
      case 'healthy':
        return 'bg-emerald-900/20 border-emerald-500/50';
      case 'degraded':
        return 'bg-yellow-900/20 border-yellow-500/50';
      case 'error':
        return 'bg-red-900/20 border-red-500/50';
      default:
        return 'bg-slate-700/20 border-slate-500/50';
    }
  };

  const handleStartWebhook = async () => {
    setActionLoading('webhook');
    setActionMessage(null);
    try {
      const result = await startWebhookService();
      setActionMessage({ type: 'success', text: result.message || 'Webhook service started' });
      // Refresh status after a moment
      setTimeout(() => fetchStatus(), intervals.components.systemStatus.refreshDelayAfterAction);
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to start webhook service'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRestartCloudflare = async () => {
    setActionLoading('cloudflare');
    setActionMessage(null);
    try {
      const result = await restartCloudflare();
      setActionMessage({ type: 'success', text: result.message || 'Cloudflare tunnel restarted' });
      // Refresh status after a moment
      setTimeout(() => fetchStatus(), intervals.components.systemStatus.refreshDelayAfterAction);
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to restart Cloudflare tunnel'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRedeliverWebhook = async () => {
    setActionLoading('github-webhook');
    setActionMessage(null);
    try {
      const result = await redeliverGitHubWebhook();

      // Format diagnostics if available
      let messageText = result.message || 'Webhook redelivered';
      if (result.diagnostics && Array.isArray(result.diagnostics)) {
        messageText += '\n\nDiagnostics:\n' + result.diagnostics.join('\n');
      }
      if (result.recommendations) {
        const recs = result.recommendations.filter((r: string | null) => r !== null);
        if (recs.length > 0) {
          messageText += '\n\nRecommendations:\n' + recs.join('\n');
        }
      }

      // Determine message type based on status
      const messageType = result.status === 'success' ? 'success' :
                         result.status === 'warning' ? 'error' :
                         result.status === 'info' ? 'success' : 'error';

      setActionMessage({ type: messageType, text: messageText });

      // Refresh status after a moment
      setTimeout(() => fetchStatus(), intervals.components.systemStatus.refreshDelayAfterAction);
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to redeliver webhook'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Memoized service card component to prevent unnecessary re-renders
  const ServiceCard = React.memo(({ serviceKey, service, onAction }: {
    serviceKey: string;
    service: ServiceHealth;
    onAction: (action: string) => void;
  }) => {
    const hasAction = serviceKey === 'webhook' || serviceKey === 'cloudflare_tunnel' || serviceKey === 'github_webhook';
    const isActionDisabled = service.status === 'healthy' && serviceKey !== 'github_webhook';

    return (
      <div
        className={`p-3 rounded-lg border ${getStatusColor(service.status)}`}
      >
        <div className="flex items-start justify-between mb-2">
          <h4 className="font-semibold text-sm">{service.name}</h4>
          <span className="text-xl text-current">{getStatusIcon(service.status)}</span>
        </div>

        {service.message && (
          <p className="text-xs mb-2">{service.message}</p>
        )}

        {service.uptime_human && (
          <p className="text-xs opacity-75">Uptime: {service.uptime_human}</p>
        )}

        {service.details && Object.keys(service.details).length > 0 && (
          <div className="mt-2 pt-2 border-t border-current border-opacity-20">
            {Object.entries(service.details).map(([detailKey, detailValue]) => (
              <div key={detailKey} className="flex justify-between text-xs opacity-75">
                <span>{detailKey.replace(/_/g, ' ')}:</span>
                <span className="font-medium">{String(detailValue)}</span>
              </div>
            ))}
          </div>
        )}

        {hasAction && (
          <div className="mt-3 pt-2 border-t border-current border-opacity-20">
            {serviceKey === 'webhook' && (
              <button
                onClick={() => onAction('webhook')}
                disabled={actionLoading === 'webhook' || isActionDisabled}
                className={`w-full px-3 py-1.5 rounded text-xs font-medium transition-all shadow ${
                  isActionDisabled
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 disabled:from-slate-600 disabled:to-slate-600'
                }`}
              >
                {actionLoading === 'webhook' ? 'Starting...' : 'Start Service'}
              </button>
            )}
            {serviceKey === 'cloudflare_tunnel' && (
              <button
                onClick={() => onAction('cloudflare')}
                disabled={actionLoading === 'cloudflare'}
                className="w-full px-3 py-1.5 rounded text-xs font-medium bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:from-blue-700 hover:to-cyan-700 disabled:from-slate-600 disabled:to-slate-600 transition-all shadow"
              >
                {actionLoading === 'cloudflare' ? 'Restarting...' : 'Restart Tunnel'}
              </button>
            )}
            {serviceKey === 'github_webhook' && (
              <button
                onClick={() => onAction('github-webhook')}
                disabled={actionLoading === 'github-webhook'}
                className="w-full px-3 py-1.5 rounded text-xs font-medium bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 disabled:from-slate-600 disabled:to-slate-600 transition-all shadow"
              >
                {actionLoading === 'github-webhook'
                  ? 'Redelivering...'
                  : service.status === 'healthy'
                    ? 'Test Webhook'
                    : 'Redeliver Failed'}
              </button>
            )}
          </div>
        )}
      </div>
    );
  }, (prevProps, nextProps) => {
    // Only re-render if service status, message, or details changed
    return (
      prevProps.service.status === nextProps.service.status &&
      prevProps.service.message === nextProps.service.message &&
      JSON.stringify(prevProps.service.details) === JSON.stringify(nextProps.service.details) &&
      prevProps.service.uptime_human === nextProps.service.uptime_human
    );
  });

  const handleServiceAction = (action: string) => {
    if (action === 'webhook') {
      handleStartWebhook();
    } else if (action === 'cloudflare') {
      handleRestartCloudflare();
    } else if (action === 'github-webhook') {
      handleRedeliverWebhook();
    }
  };

  // Define service order (swapping frontend and cloudflare_tunnel)
  // Use service display order from configuration
  const serviceOrder = [...serviceDisplayOrder];

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg shadow-xl border border-slate-700 p-4 flex-1 flex flex-col">
        <div className="relative mb-3">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg -m-2"></div>
          <div className="flex items-center justify-between relative z-10">
            <h2 className="text-xl font-bold text-white">System Status</h2>
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
                className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all text-sm font-medium shadow-lg"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        {actionMessage && (
          <div className={`mb-4 p-3 rounded text-sm border ${
            actionMessage.type === 'success'
              ? 'bg-emerald-900/20 border-emerald-500/50 text-emerald-200'
              : 'bg-red-900/20 border-red-500/50 text-red-200'
          }`}>
            <div className="whitespace-pre-wrap font-mono text-xs">
              {actionMessage.text}
            </div>
          </div>
        )}

        {status && (
          <>
            {/* Overall Status Banner */}
            <div className={`mb-3 p-3 rounded-lg border-2 ${getOverallStatusColor(status.overall_status)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold mb-1 text-white">
                    Overall Status: {status.overall_status.charAt(0).toUpperCase() + status.overall_status.slice(1)}
                  </h3>
                  <p className="text-sm text-slate-300">
                    {status.summary.healthy_services} of {status.summary.total_services} services healthy
                    ({status.summary.health_percentage}%)
                  </p>
                </div>
                <div className="text-3xl text-white">
                  {getStatusIcon(status.overall_status)}
                </div>
              </div>
            </div>

            {/* Individual Services Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {serviceOrder.map((key) => {
                const service = status.services[key];
                return service ? (
                  <ServiceCard
                    key={key}
                    serviceKey={key}
                    service={service}
                    onAction={handleServiceAction}
                  />
                ) : null;
              })}
            </div>

            {/* Pre-Flight Health Checks */}
            <div className="mt-6">
              <PreflightCheckPanel />
            </div>
          </>
        )}

    </div>
  );
}
