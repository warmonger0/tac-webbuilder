import { useQuery } from '@tanstack/react-query';
import { getWorkflowHistorySummary } from '../api/client';

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}

export function WorkflowHistorySummary() {
  const {
    data: summary,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflow-history-summary'],
    queryFn: getWorkflowHistorySummary,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="text-gray-600">Loading summary...</div>
      </div>
    );
  }

  if (error || !summary) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">
        Workflow History Summary
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {/* Total Workflows */}
        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900">
            {summary.total_workflows}
          </div>
          <div className="text-sm text-gray-600 mt-1">Total Workflows</div>
        </div>

        {/* Average Cost */}
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600">
            ${summary.avg_cost.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600 mt-1">Average Cost</div>
        </div>

        {/* Average Duration */}
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600">
            {formatDuration(summary.avg_duration)}
          </div>
          <div className="text-sm text-gray-600 mt-1">Average Duration</div>
        </div>

        {/* Success Rate */}
        <div className="text-center">
          <div className="text-3xl font-bold text-purple-600">
            {summary.success_rate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600 mt-1">Success Rate</div>
        </div>
      </div>

      {/* Workflow Counts by Template */}
      {Object.keys(summary.workflow_counts).length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Workflows by Template
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.workflow_counts).map(([template, count]) => (
              <div
                key={template}
                className="bg-gray-100 px-3 py-1 rounded-full text-sm"
              >
                <span className="font-medium">{template}:</span>{' '}
                <span className="text-gray-700">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflow Counts by Model */}
      {Object.keys(summary.model_counts).length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Workflows by Model
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.model_counts).map(([model, count]) => (
              <div
                key={model}
                className="bg-purple-100 px-3 py-1 rounded-full text-sm"
              >
                <span className="font-medium">{model}:</span>{' '}
                <span className="text-purple-700">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
