import { useState, useEffect } from 'react';
import { getSystemStatus } from '../api/client';
import type { SystemStatusResponse, ServiceHealth } from '../types';

export function SystemStatusPanel() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getSystemStatus();
      setStatus(data);
      setLastChecked(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status');
      setStatus(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Fetch on mount
    fetchStatus();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (serviceStatus: string) => {
    switch (serviceStatus) {
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
        return 'bg-green-50 border-green-300';
      case 'degraded':
        return 'bg-yellow-50 border-yellow-300';
      case 'error':
        return 'bg-red-50 border-red-300';
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">System Status</h2>
          <button
            onClick={fetchStatus}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {isLoading ? 'Checking...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
            {error}
          </div>
        )}

        {status && (
          <>
            {/* Overall Status Banner */}
            <div className={`mb-6 p-4 rounded-lg border-2 ${getOverallStatusColor(status.overall_status)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-1">
                    Overall Status: {status.overall_status.charAt(0).toUpperCase() + status.overall_status.slice(1)}
                  </h3>
                  <p className="text-sm opacity-80">
                    {status.summary.healthy_services} of {status.summary.total_services} services healthy
                    ({status.summary.health_percentage}%)
                  </p>
                </div>
                <div className="text-4xl">
                  {getStatusIcon(status.overall_status)}
                </div>
              </div>
            </div>

            {/* Individual Services Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(status.services).map(([key, service]: [string, ServiceHealth]) => (
                <div
                  key={key}
                  className={`p-4 rounded-lg border ${getStatusColor(service.status)}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-sm">{service.name}</h4>
                    <span className="text-2xl">{getStatusIcon(service.status)}</span>
                  </div>

                  {service.message && (
                    <p className="text-xs mb-2 opacity-90">{service.message}</p>
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
                </div>
              ))}
            </div>
          </>
        )}

        {lastChecked && (
          <div className="mt-4 text-xs text-gray-500 text-center">
            Last checked: {lastChecked.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
