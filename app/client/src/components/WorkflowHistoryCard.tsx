import { useState } from 'react';
import type { WorkflowHistoryItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { CostVisualization } from './CostVisualization';

interface WorkflowHistoryCardProps {
  item: WorkflowHistoryItem;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString();
}

function formatDuration(seconds?: number): string {
  if (!seconds) return 'N/A';

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}

export function WorkflowHistoryCard({ item }: WorkflowHistoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {item.adw_id}
            </h3>
            <StatusBadge status={item.status} />
            {item.status === 'in_progress' && (
              <span className="flex items-center gap-1 text-sm text-blue-600">
                <span className="inline-block w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                In Progress
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-600">
            {item.issue_number && item.github_url && (
              <a
                href={item.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-blue-600 font-medium"
              >
                Issue #{item.issue_number}
              </a>
            )}

            {item.workflow_template && (
              <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                {item.workflow_template}
              </span>
            )}

            {item.model_set && (
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                {item.model_set} model
              </span>
            )}
          </div>
        </div>

        <div className="text-right text-sm text-gray-600">
          <div>Started: {formatDate(item.started_at)}</div>
          {item.completed_at && (
            <div>Completed: {formatDate(item.completed_at)}</div>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-gray-200">
        <div>
          <div className="text-xs text-gray-500 mb-1">Duration</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatDuration(item.total_duration_seconds)}
          </div>
        </div>

        {item.cost_data && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Total Cost</div>
            <div className="text-lg font-semibold text-green-600">
              ${item.cost_data.total_cost.toFixed(4)}
            </div>
          </div>
        )}

        {item.concurrent_workflows !== undefined && (
          <div>
            <div className="text-xs text-gray-500 mb-1">Concurrent Workflows</div>
            <div className="text-lg font-semibold text-gray-900">
              {item.concurrent_workflows}
            </div>
          </div>
        )}
      </div>

      {/* Cost Visualization */}
      {item.cost_data && (
        <div className="mb-4">
          <CostVisualization adwId={item.adw_id} />
        </div>
      )}

      {/* Error Message */}
      {item.status === 'failed' && item.error_message && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-sm font-medium text-red-800 mb-1">Error:</div>
          <div className="text-sm text-red-700">{item.error_message}</div>
        </div>
      )}

      {/* Expandable Details */}
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-primary hover:text-blue-600 font-medium"
        >
          {isExpanded ? 'Hide Details' : 'Show Details'}
        </button>

        {isExpanded && (
          <div className="mt-4 space-y-4">
            {/* User Input */}
            {item.user_input && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Original Request:
                </div>
                <div className="bg-gray-50 p-3 rounded-lg text-sm text-gray-700 whitespace-pre-wrap">
                  {item.user_input}
                </div>
              </div>
            )}

            {/* Resource Information */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              {item.worktree_path && (
                <div>
                  <div className="text-gray-500 mb-1">Worktree Path:</div>
                  <div className="text-gray-900 font-mono text-xs break-all">
                    {item.worktree_path}
                  </div>
                </div>
              )}

              {item.backend_port && (
                <div>
                  <div className="text-gray-500 mb-1">Backend Port:</div>
                  <div className="text-gray-900">{item.backend_port}</div>
                </div>
              )}

              {item.frontend_port && (
                <div>
                  <div className="text-gray-500 mb-1">Frontend Port:</div>
                  <div className="text-gray-900">{item.frontend_port}</div>
                </div>
              )}

              {item.github_url && (
                <div>
                  <div className="text-gray-500 mb-1">GitHub URL:</div>
                  <a
                    href={item.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-blue-600 break-all"
                  >
                    {item.github_url}
                  </a>
                </div>
              )}
            </div>

            {/* Token Statistics */}
            {item.cost_data && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Token Statistics:
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Total Tokens:</span>
                      <span className="ml-2 font-semibold text-gray-900">
                        {item.cost_data.total_tokens.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Cache Efficiency:</span>
                      <span className="ml-2 font-semibold text-green-600">
                        {item.cost_data.cache_efficiency_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Cache Savings:</span>
                      <span className="ml-2 font-semibold text-green-600">
                        ${item.cost_data.cache_savings_amount.toFixed(4)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
