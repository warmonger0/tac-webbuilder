import { useState } from 'react';
import type { WorkflowHistoryItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatDate, formatDuration, formatCost, formatNumber, truncateText, getClassificationColor } from './workflow-history-card/helpers';
import { CostSection } from './workflow-history-card/sections/CostSection';
import { TokenSection } from './workflow-history-card/sections/TokenSection';
import { ErrorSection } from './workflow-history-card/sections/ErrorSection';
import { PerformanceSection } from './workflow-history-card/sections/PerformanceSection';
import { ResourceSection } from './workflow-history-card/sections/ResourceSection';
import { WorkflowJourneySection } from './workflow-history-card/sections/WorkflowJourneySection';
import { ScoresSection } from './workflow-history-card/sections/ScoresSection';
import { InsightsSection } from './workflow-history-card/sections/InsightsSection';
import { SimilarWorkflowsSection } from './workflow-history-card/sections/SimilarWorkflowsSection';

interface WorkflowHistoryCardProps {
  workflow: WorkflowHistoryItem;
}

export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-900">
              ADW: {workflow.adw_id}
            </h3>
            <StatusBadge status={workflow.status} />
            {workflow.gh_issue_state && (
              <span
                className={`text-xs px-2 py-1 rounded ${
                  workflow.gh_issue_state === 'open'
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : 'bg-purple-100 text-purple-800 border border-purple-300'
                }`}
                title={`GitHub Issue Status: ${workflow.gh_issue_state}`}
              >
                Issue: {workflow.gh_issue_state.toUpperCase()}
              </span>
            )}
            {workflow.structured_input?.classification && (
              <span className={`text-xs px-2 py-1 rounded border ${getClassificationColor(workflow.structured_input.classification)}`}>
                {workflow.structured_input.classification.toUpperCase()}
              </span>
            )}
          </div>
          {workflow.nl_input && (
            <div className="text-sm text-gray-700 mt-2">
              "{truncateText(workflow.nl_input, 60)}"
            </div>
          )}
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
          {(workflow.workflow_template || workflow.model_used) && (
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-600">
              {workflow.workflow_template && (
                <span>
                  <span className="font-medium">Workflow:</span> {workflow.workflow_template}
                </span>
              )}
              {workflow.model_used && (
                <span>
                  <span className="font-medium">Model:</span> {workflow.model_used}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="text-right text-sm text-gray-600">
          <div>{formatDate(workflow.created_at)}</div>
          {workflow.duration_seconds && (
            <div className="text-gray-500">Duration: {formatDuration(workflow.duration_seconds)}</div>
          )}
        </div>
      </div>

      {/* Metadata Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
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
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-6">
          <CostSection workflow={workflow} />
          <TokenSection workflow={workflow} />
          <PerformanceSection workflow={workflow} />
          <ErrorSection workflow={workflow} />
          <ResourceSection workflow={workflow} />
          <WorkflowJourneySection workflow={workflow} />
          <ScoresSection workflow={workflow} />
          <InsightsSection workflow={workflow} />
          <SimilarWorkflowsSection workflow={workflow} />
        </div>
      )}
    </div>
  );
}
