import { useState, useEffect } from 'react';
import { getAdwMonitor, type AdwWorkflowStatus, type AdwMonitorSummary } from '../api/client';

export function AdwMonitorCard() {
  const [workflows, setWorkflows] = useState<AdwWorkflowStatus[]>([]);
  const [summary, setSummary] = useState<AdwMonitorSummary>({ total: 0, running: 0, completed: 0, failed: 0, paused: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMonitorData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getAdwMonitor();
        setWorkflows(data.workflows);
        setSummary(data.summary);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch ADW monitor data');
        console.error('Failed to fetch ADW monitor:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMonitorData();

    // Poll based on activity: 10s for active workflows, 30s for idle
    const interval = setInterval(fetchMonitorData, summary.running > 0 ? 10000 : 30000);
    return () => clearInterval(interval);
  }, [summary.running]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'queued': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '⚙️';
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'paused': return '⏸️';
      case 'queued': return '⏳';
      default: return '❓';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  };

  const formatCost = (cost: number | null) => {
    if (!cost) return '$0.00';
    return `$${cost.toFixed(2)}`;
  };

  if (isLoading && workflows.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-2">⚙️</div>
            <p className="text-gray-500">Loading ADW monitor...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">⚠️ {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header with Summary */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">ADW Workflows</h2>
        <div className="flex gap-4 text-sm">
          <span className="text-gray-600">
            <span className="font-semibold text-blue-600">{summary.running}</span> running
          </span>
          <span className="text-gray-600">
            <span className="font-semibold text-green-600">{summary.completed}</span> completed
          </span>
          {summary.failed > 0 && (
            <span className="text-gray-600">
              <span className="font-semibold text-red-600">{summary.failed}</span> failed
            </span>
          )}
        </div>
      </div>

      {/* Workflows List */}
      {workflows.length === 0 ? (
        <div className="bg-emerald-50 rounded-lg p-8 text-center">
          <p className="text-emerald-700 font-medium text-lg">No active workflows</p>
          <p className="text-emerald-600 text-sm mt-2">Workflows will appear here when they are running</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[500px] overflow-y-auto">
          {workflows.map((workflow) => (
            <div
              key={workflow.adw_id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(workflow.status)}`}>
                      {getStatusIcon(workflow.status)} {workflow.status.toUpperCase()}
                    </span>
                    {workflow.issue_class && (
                      <span className="text-xs text-gray-500">{workflow.issue_class}</span>
                    )}
                  </div>
                  <h3 className="font-semibold text-gray-900 truncate" title={workflow.title}>
                    {workflow.title || `ADW ${workflow.adw_id.substring(0, 8)}`}
                  </h3>
                  {workflow.github_url && (
                    <a
                      href={workflow.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline"
                    >
                      #{workflow.issue_number}
                    </a>
                  )}
                </div>
                <div className="text-right text-sm">
                  <div className="font-semibold text-gray-900">
                    {formatCost(workflow.current_cost)}
                  </div>
                  {workflow.estimated_cost_total && (
                    <div className="text-xs text-gray-500">
                      of {formatCost(workflow.estimated_cost_total)}
                    </div>
                  )}
                </div>
              </div>

              {/* Phase Progress */}
              {workflow.current_phase && (
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">
                      {workflow.current_phase}
                      {workflow.phases_completed.length > 0 && (
                        <span className="text-gray-400 ml-1">
                          ({workflow.phases_completed.length} completed)
                        </span>
                      )}
                    </span>
                    <span className="text-gray-500 font-medium">
                      {Math.round(workflow.phase_progress)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        workflow.status === 'running'
                          ? 'bg-blue-600'
                          : workflow.status === 'completed'
                          ? 'bg-green-600'
                          : workflow.status === 'failed'
                          ? 'bg-red-600'
                          : 'bg-gray-400'
                      }`}
                      style={{ width: `${workflow.phase_progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span title={workflow.adw_id}>ID: {workflow.adw_id.substring(0, 8)}</span>
                {workflow.workflow_template && (
                  <span>{workflow.workflow_template}</span>
                )}
                {workflow.duration_seconds !== null && (
                  <span>⏱️ {formatDuration(workflow.duration_seconds)}</span>
                )}
                {workflow.is_process_active && (
                  <span className="text-green-600 font-medium">● Active</span>
                )}
                {workflow.error_count > 0 && (
                  <span className="text-red-600" title={workflow.last_error || undefined}>
                    ⚠️ {workflow.error_count} error{workflow.error_count > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Live Update Indicator */}
      {workflows.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <p className="text-xs text-gray-500">
              Auto-refresh every {summary.running > 0 ? '10' : '30'} seconds
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
