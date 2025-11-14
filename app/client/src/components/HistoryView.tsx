import { useState } from 'react';
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';
import type { WorkflowHistoryItem } from '../types';

function formatDate(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function formatDuration(seconds?: number): string {
  if (!seconds) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}

interface WorkflowCardProps {
  item: WorkflowHistoryItem;
}

function WorkflowCard({ item }: WorkflowCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusColors = {
    in_progress: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{item.adw_id}</h3>
          <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
            <span>{formatDate(item.start_timestamp)}</span>
            <span>•</span>
            <span>{item.workflow_template}</span>
            {item.model_used && (
              <>
                <span>•</span>
                <span>{item.model_used}</span>
              </>
            )}
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[item.status]}`}>
          {item.status.replace('_', ' ')}
        </span>
      </div>

      {/* Request */}
      <div className="mb-4">
        <p className="text-sm text-gray-700 line-clamp-2">{item.nl_input}</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 uppercase">Cost</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatCost(item.execution_metrics.actual_cost_total)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Duration</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatDuration(item.performance_metrics.completion_time_seconds)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Tokens</div>
          <div className="text-lg font-semibold text-gray-900">
            {item.execution_metrics.total_tokens.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Cache Efficiency</div>
          <div className="text-lg font-semibold text-gray-900">
            {item.execution_metrics.cache_efficiency_percent.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Expandable Details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        {expanded ? 'Hide Details' : 'Show Details'}
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Token Breakdown */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Token Breakdown</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Input:</span>
                <span className="font-medium">{item.execution_metrics.input_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Output:</span>
                <span className="font-medium">{item.execution_metrics.output_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cache Creation:</span>
                <span className="font-medium">{item.execution_metrics.cache_creation_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cache Read:</span>
                <span className="font-medium">{item.execution_metrics.cache_read_tokens.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Phase Costs */}
          {item.phases.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Phase Costs</h4>
              <div className="space-y-1">
                {item.phases.map((phase, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{phase.phase}</span>
                    <span className="font-medium">{formatCost(phase.cost)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Performance</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Success Rate:</span>
                <span className="font-medium">{item.performance_metrics.success_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Retries:</span>
                <span className="font-medium">{item.performance_metrics.retry_count}</span>
              </div>
            </div>
          </div>

          {/* Resource Usage */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Resources</h4>
            <div className="space-y-1 text-sm">
              {item.resource_metrics.worktree_id && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Worktree:</span>
                  <span className="font-medium">{item.resource_metrics.worktree_id}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Worktree Reused:</span>
                <span className="font-medium">{item.resource_metrics.worktree_reused ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {item.error_message && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <h4 className="text-sm font-semibold text-red-900 mb-1">Error</h4>
              <p className="text-sm text-red-800">{item.error_message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AnalyticsPanel({ analytics }: { analytics: any }) {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Analytics Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Total Workflows</div>
          <div className="text-2xl font-bold text-gray-900">{analytics.total_workflows}</div>
        </div>
        <div className="bg-white rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Total Cost</div>
          <div className="text-2xl font-bold text-gray-900">{formatCost(analytics.total_cost_all_time)}</div>
        </div>
        <div className="bg-white rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Avg Duration</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatDuration(analytics.avg_completion_time)}
          </div>
        </div>
        <div className="bg-white rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-gray-900">{analytics.overall_success_rate.toFixed(1)}%</div>
        </div>
      </div>
    </div>
  );
}

export function HistoryView() {
  const { historyData, isConnected, lastUpdated } = useWorkflowHistoryWebSocket();

  if (!historyData) {
    return (
      <div className="flex flex-col justify-center items-center py-12">
        <div className="text-gray-600 mb-2">Loading workflow history...</div>
        <div className="text-sm text-gray-500">
          WebSocket: {isConnected ? 'Connected' : 'Connecting...'}
        </div>
      </div>
    );
  }

  if (historyData.items.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 text-lg">No workflow history</p>
        <p className="text-gray-500 text-sm mt-2">
          Workflow execution history will appear here
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Header with Connection Status */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Workflow History</h2>
        <div className="flex items-center gap-2 text-sm">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-gray-600">
            {isConnected ? 'Live' : 'Disconnected'}
            {lastUpdated && ` • Updated ${lastUpdated.toLocaleTimeString()}`}
          </span>
        </div>
      </div>

      {/* Analytics Panel */}
      <AnalyticsPanel analytics={historyData.analytics} />

      {/* Workflow Cards */}
      <div className="space-y-4">
        {historyData.items.map((item) => (
          <WorkflowCard key={item.adw_id} item={item} />
        ))}
      </div>

      {/* Load More */}
      {historyData.has_more && (
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Showing {historyData.items.length} of {historyData.total} workflows
          </p>
        </div>
      )}
    </div>
  );
}
