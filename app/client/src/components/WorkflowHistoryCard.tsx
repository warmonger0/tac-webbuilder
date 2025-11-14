import { useState } from 'react';
import type { WorkflowHistoryItem } from '../types';

interface WorkflowHistoryCardProps {
  workflow: WorkflowHistoryItem;
}

export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  const [expanded, setExpanded] = useState(false);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const statusColors: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h4 className="text-lg font-bold text-gray-900">
            {workflow.issue_number ? `Issue #${workflow.issue_number}` : workflow.adw_id}
          </h4>
          <p className="text-sm text-gray-600 mt-1">ADW ID: {workflow.adw_id}</p>
          <p className="text-xs text-gray-500 mt-1">
            {formatTimestamp(workflow.created_at)}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            statusColors[workflow.status] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {workflow.status.toUpperCase()}
        </span>
      </div>

      {/* Request Summary */}
      {workflow.nl_input && (
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">Request:</h5>
          <p className="text-sm text-gray-600 line-clamp-2">
            {workflow.nl_input}
          </p>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500">Duration</p>
          <p className="text-sm font-medium text-gray-900">
            {formatDuration(workflow.duration_seconds)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Model</p>
          <p className="text-sm font-medium text-gray-900">
            {workflow.model_used || 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Template</p>
          <p className="text-sm font-medium text-gray-900">
            {workflow.workflow_template || 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Phase</p>
          <p className="text-sm font-medium text-gray-900">
            {workflow.current_phase || 'N/A'}
          </p>
        </div>
      </div>

      {/* Cost Data */}
      {workflow.cost_data && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold text-gray-700">Total Cost:</span>
            <span className="text-lg font-bold text-gray-900">
              ${workflow.cost_data.total_cost.toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between items-center mt-2 text-xs text-gray-600">
            <span>Cache Efficiency:</span>
            <span>{workflow.cost_data.cache_efficiency_percent.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between items-center text-xs text-gray-600">
            <span>Cache Savings:</span>
            <span>${workflow.cost_data.cache_savings_amount.toFixed(4)}</span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {workflow.error_message && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-semibold text-red-800 mb-1">Error:</p>
          <p className="text-xs text-red-700">{workflow.error_message}</p>
        </div>
      )}

      {/* Expandable Details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {expanded ? '▼ Hide Details' : '▶ Show Details'}
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
          {workflow.worktree_path && (
            <div>
              <p className="text-xs font-semibold text-gray-700">Worktree:</p>
              <p className="text-xs text-gray-600 font-mono break-all">
                {workflow.worktree_path}
              </p>
            </div>
          )}
          {(workflow.backend_port || workflow.frontend_port) && (
            <div className="grid grid-cols-2 gap-4">
              {workflow.backend_port && (
                <div>
                  <p className="text-xs font-semibold text-gray-700">Backend Port:</p>
                  <p className="text-xs text-gray-600">{workflow.backend_port}</p>
                </div>
              )}
              {workflow.frontend_port && (
                <div>
                  <p className="text-xs font-semibold text-gray-700">Frontend Port:</p>
                  <p className="text-xs text-gray-600">{workflow.frontend_port}</p>
                </div>
              )}
            </div>
          )}
          {workflow.cost_data && workflow.cost_data.phases.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-2">Phase Costs:</p>
              <div className="space-y-1">
                {workflow.cost_data.phases.map((phase) => (
                  <div key={phase.phase} className="flex justify-between text-xs text-gray-600">
                    <span>{phase.phase}:</span>
                    <span>${phase.cost.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* GitHub Link */}
      {workflow.github_url && (
        <a
          href={workflow.github_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center mt-4 text-blue-600 hover:text-blue-800 font-medium text-sm"
        >
          View on GitHub →
        </a>
      )}
    </div>
  );
}
