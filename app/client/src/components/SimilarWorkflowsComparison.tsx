import { useEffect, useState } from 'react';
import { WorkflowHistoryItem } from '../types/api.types';
import { fetchWorkflowsBatch } from '../api/workflowClient';

interface SimilarWorkflowsComparisonProps {
  currentWorkflowId: string;
  similarWorkflowIds: string[];
}

export function SimilarWorkflowsComparison({
  currentWorkflowId,
  similarWorkflowIds,
}: SimilarWorkflowsComparisonProps) {
  const [similarWorkflows, setSimilarWorkflows] = useState<WorkflowHistoryItem[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowHistoryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;

    const fetchSimilarWorkflows = async () => {
      try {
        setLoading(true);
        setError(null);

        // OPTIMIZED: Single batch request for all workflows (current + similar)
        const allIds = [currentWorkflowId, ...similarWorkflowIds];
        const allWorkflows = await fetchWorkflowsBatch(allIds, signal);

        // Check if the request was aborted before updating state
        if (signal.aborted) {
          return;
        }

        // Separate current workflow from similar workflows
        const current = allWorkflows.find(w => w.adw_id === currentWorkflowId);
        const similar = allWorkflows.filter(w => w.adw_id !== currentWorkflowId);

        setCurrentWorkflow(current || null);
        setSimilarWorkflows(similar);
      } catch (err) {
        // Don't show error UI for aborted requests
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }
        setError(err instanceof Error ? err.message : 'Failed to fetch workflows');
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchSimilarWorkflows();

    // Cleanup function to abort the request when component unmounts
    return () => {
      controller.abort();
    };
  }, [currentWorkflowId, similarWorkflowIds]);

  if (loading) {
    return (
      <div className="text-sm text-gray-500 italic">
        Loading similar workflows...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Error: {error}
      </div>
    );
  }

  if (similarWorkflows.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No similar workflows found
      </div>
    );
  }

  const formatDuration = (seconds: number | undefined): string => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatCost = (cost: number | undefined): string => {
    if (cost === undefined || cost === 0) return 'N/A';
    return `$${cost.toFixed(4)}`;
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-semibold text-gray-700">Workflow</th>
            <th className="px-4 py-2 text-left font-semibold text-gray-700">Status</th>
            <th className="px-4 py-2 text-right font-semibold text-gray-700">Duration</th>
            <th className="px-4 py-2 text-right font-semibold text-gray-700">Cost</th>
            <th className="px-4 py-2 text-right font-semibold text-gray-700">Cache Eff.</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {/* Current workflow row (highlighted) */}
          {currentWorkflow && (
            <tr className="bg-blue-50">
              <td className="px-4 py-2 font-mono text-xs">
                <span className="font-semibold text-blue-700">
                  {currentWorkflow.adw_id}
                </span>
                <span className="ml-2 text-xs text-blue-600">(current)</span>
              </td>
              <td className="px-4 py-2">
                <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                  currentWorkflow.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : currentWorkflow.status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : currentWorkflow.status === 'running'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {currentWorkflow.status}
                </span>
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {formatDuration(currentWorkflow.duration_seconds)}
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {formatCost(currentWorkflow.actual_cost_total)}
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {currentWorkflow.cache_efficiency_percent
                  ? `${currentWorkflow.cache_efficiency_percent.toFixed(1)}%`
                  : 'N/A'}
              </td>
            </tr>
          )}

          {/* Similar workflows rows */}
          {similarWorkflows.map((workflow) => (
            <tr key={workflow.adw_id} className="hover:bg-gray-50">
              <td className="px-4 py-2 font-mono text-xs">
                <a
                  href={workflow.github_url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {workflow.adw_id}
                </a>
              </td>
              <td className="px-4 py-2">
                <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                  workflow.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : workflow.status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : workflow.status === 'running'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {workflow.status}
                </span>
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {formatDuration(workflow.duration_seconds)}
                {currentWorkflow && workflow.duration_seconds && currentWorkflow.duration_seconds && (
                  <span className={`ml-2 text-xs ${
                    workflow.duration_seconds < currentWorkflow.duration_seconds
                      ? 'text-green-600'
                      : workflow.duration_seconds > currentWorkflow.duration_seconds
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}>
                    {workflow.duration_seconds < currentWorkflow.duration_seconds
                      ? '↓'
                      : workflow.duration_seconds > currentWorkflow.duration_seconds
                      ? '↑'
                      : '='}
                  </span>
                )}
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {formatCost(workflow.actual_cost_total)}
                {currentWorkflow && workflow.actual_cost_total && currentWorkflow.actual_cost_total && (
                  <span className={`ml-2 text-xs ${
                    workflow.actual_cost_total < currentWorkflow.actual_cost_total
                      ? 'text-green-600'
                      : workflow.actual_cost_total > currentWorkflow.actual_cost_total
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}>
                    {workflow.actual_cost_total < currentWorkflow.actual_cost_total
                      ? '↓'
                      : workflow.actual_cost_total > currentWorkflow.actual_cost_total
                      ? '↑'
                      : '='}
                  </span>
                )}
              </td>
              <td className="px-4 py-2 text-right font-mono text-xs">
                {workflow.cache_efficiency_percent
                  ? `${workflow.cache_efficiency_percent.toFixed(1)}%`
                  : 'N/A'}
                {currentWorkflow && workflow.cache_efficiency_percent && currentWorkflow.cache_efficiency_percent && (
                  <span className={`ml-2 text-xs ${
                    workflow.cache_efficiency_percent > currentWorkflow.cache_efficiency_percent
                      ? 'text-green-600'
                      : workflow.cache_efficiency_percent < currentWorkflow.cache_efficiency_percent
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}>
                    {workflow.cache_efficiency_percent > currentWorkflow.cache_efficiency_percent
                      ? '↑'
                      : workflow.cache_efficiency_percent < currentWorkflow.cache_efficiency_percent
                      ? '↓'
                      : '='}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-3 text-xs text-gray-500">
        <span className="font-semibold">Legend:</span>{' '}
        <span className="text-green-600">↓</span> = Better than current,{' '}
        <span className="text-red-600">↑</span> = Worse than current,{' '}
        = = Same as current
      </div>
    </div>
  );
}
