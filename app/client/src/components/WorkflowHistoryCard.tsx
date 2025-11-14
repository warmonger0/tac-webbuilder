import { useState } from 'react';
import type { WorkflowHistoryItem } from '../types';
import { StatusBadge } from './StatusBadge';

interface WorkflowHistoryCardProps {
  workflow: WorkflowHistoryItem;
}

export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  const formatDate = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              ADW: {workflow.adw_id}
            </h3>
            <StatusBadge status={workflow.status} />
          </div>
          {workflow.issue_number && (
            <a
              href={workflow.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-1 inline-block"
            >
              Issue #{workflow.issue_number}
            </a>
          )}
        </div>
        <div className="text-right text-sm text-gray-600">
          <div>{formatDate(workflow.created_at)}</div>
          {workflow.duration_seconds && (
            <div className="text-gray-500">Duration: {formatDuration(workflow.duration_seconds)}</div>
          )}
        </div>
      </div>

      {/* Natural Language Input */}
      {workflow.nl_input && (
        <div className="mb-4">
          <div className="text-sm font-medium text-gray-700 mb-1">Request:</div>
          <div className="text-sm text-gray-900 bg-gray-50 rounded p-3">
            {workflow.nl_input}
          </div>
        </div>
      )}

      {/* Metadata Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
        {workflow.model_used && (
          <div>
            <div className="text-gray-600">Model</div>
            <div className="font-medium text-gray-900">{workflow.model_used}</div>
          </div>
        )}
        {workflow.workflow_template && (
          <div>
            <div className="text-gray-600">Template</div>
            <div className="font-medium text-gray-900">{workflow.workflow_template}</div>
          </div>
        )}
        {workflow.current_phase && (
          <div>
            <div className="text-gray-600">Phase</div>
            <div className="font-medium text-gray-900">{workflow.current_phase}</div>
          </div>
        )}
        {workflow.steps_total > 0 && (
          <div>
            <div className="text-gray-600">Progress</div>
            <div className="font-medium text-gray-900">
              {workflow.steps_completed}/{workflow.steps_total} steps
            </div>
          </div>
        )}
      </div>

      {/* Cost & Token Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
        {workflow.actual_cost_total > 0 && (
          <div>
            <div className="text-gray-600">Actual Cost</div>
            <div className="font-semibold text-green-600">{formatCost(workflow.actual_cost_total)}</div>
          </div>
        )}
        {workflow.total_tokens > 0 && (
          <div>
            <div className="text-gray-600">Total Tokens</div>
            <div className="font-medium text-gray-900">{formatNumber(workflow.total_tokens)}</div>
          </div>
        )}
        {workflow.cache_efficiency_percent > 0 && (
          <div>
            <div className="text-gray-600">Cache Efficiency</div>
            <div className="font-medium text-blue-600">{workflow.cache_efficiency_percent.toFixed(1)}%</div>
          </div>
        )}
        {workflow.retry_count > 0 && (
          <div>
            <div className="text-gray-600">Retries</div>
            <div className="font-medium text-orange-600">{workflow.retry_count}</div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {workflow.error_message && (
        <div className="mb-4">
          <div className="text-sm font-medium text-red-700 mb-1">Error:</div>
          <div className="text-sm text-red-900 bg-red-50 rounded p-3 border border-red-200">
            {workflow.error_message}
          </div>
        </div>
      )}

      {/* Toggle Details Button */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {showDetails ? '▼ Hide Details' : '▶ Show Details'}
      </button>

      {/* Detailed Information */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Token Breakdown */}
          {workflow.total_tokens > 0 && (
            <div>
              <div className="text-sm font-semibold text-gray-700 mb-2">Token Breakdown:</div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Input</div>
                  <div className="font-medium">{formatNumber(workflow.input_tokens)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Output</div>
                  <div className="font-medium">{formatNumber(workflow.output_tokens)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Cached</div>
                  <div className="font-medium">{formatNumber(workflow.cached_tokens)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Cache Hits</div>
                  <div className="font-medium text-green-600">{formatNumber(workflow.cache_hit_tokens)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Cache Misses</div>
                  <div className="font-medium text-orange-600">{formatNumber(workflow.cache_miss_tokens)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Total</div>
                  <div className="font-medium">{formatNumber(workflow.total_tokens)}</div>
                </div>
              </div>
            </div>
          )}

          {/* Cost Analysis */}
          {workflow.actual_cost_total > 0 && (
            <div>
              <div className="text-sm font-semibold text-gray-700 mb-2">Cost Analysis:</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Estimated Total</div>
                  <div className="font-medium">{formatCost(workflow.estimated_cost_total)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Actual Total</div>
                  <div className="font-medium text-green-600">{formatCost(workflow.actual_cost_total)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Cost per Step</div>
                  <div className="font-medium">{formatCost(workflow.actual_cost_per_step)}</div>
                </div>
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Cost per Token</div>
                  <div className="font-medium">{formatCost(workflow.cost_per_token)}</div>
                </div>
              </div>
            </div>
          )}

          {/* Resource Usage */}
          <div>
            <div className="text-sm font-semibold text-gray-700 mb-2">Resource Usage:</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
              {workflow.backend_port && (
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Backend Port</div>
                  <div className="font-medium">{workflow.backend_port}</div>
                </div>
              )}
              {workflow.frontend_port && (
                <div className="bg-gray-50 rounded p-2">
                  <div className="text-gray-600">Frontend Port</div>
                  <div className="font-medium">{workflow.frontend_port}</div>
                </div>
              )}
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Concurrent Workflows</div>
                <div className="font-medium">{workflow.concurrent_workflows}</div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-gray-600">Worktree Reused</div>
                <div className="font-medium">{workflow.worktree_reused ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>

          {/* Structured Input */}
          {workflow.structured_input && (
            <div>
              <div className="text-sm font-semibold text-gray-700 mb-2">Structured Input:</div>
              <pre className="text-xs bg-gray-50 rounded p-3 overflow-x-auto">
                {JSON.stringify(workflow.structured_input, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
