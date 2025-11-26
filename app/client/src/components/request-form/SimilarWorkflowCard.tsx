import { SimilarWorkflowSummary } from '../../types/api.types';

interface SimilarWorkflowCardProps {
  workflow: SimilarWorkflowSummary;
}

/**
 * SimilarWorkflowCard displays a summary of a similar historical workflow
 *
 * Shows:
 * - Natural language input (truncated)
 * - Similarity score with progress bar
 * - Clarity score (if available)
 * - Total cost (if available)
 * - Status badge
 */
export default function SimilarWorkflowCard({ workflow }: SimilarWorkflowCardProps) {
  const truncatedInput = workflow.nl_input.length > 100
    ? `${workflow.nl_input.slice(0, 100)}...`
    : workflow.nl_input;

  const statusColors = {
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-yellow-100 text-yellow-800',
  };

  const statusColor = statusColors[workflow.status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';

  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors cursor-pointer">
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-sm text-gray-700 flex-1">{truncatedInput}</p>
        <span className={`text-xs px-2 py-0.5 rounded ${statusColor} whitespace-nowrap`}>
          {workflow.status}
        </span>
      </div>

      <div className="space-y-1">
        {/* Similarity Score */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-20">Similarity:</span>
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${workflow.similarity_score}%` }}
            />
          </div>
          <span className="text-xs font-medium text-gray-700 w-10 text-right">
            {workflow.similarity_score}%
          </span>
        </div>

        {/* Clarity Score */}
        {workflow.clarity_score !== null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-20">Clarity:</span>
            <span className="text-xs text-gray-700">{workflow.clarity_score.toFixed(1)}/100</span>
          </div>
        )}

        {/* Cost */}
        {workflow.total_cost !== null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-20">Cost:</span>
            <span className="text-xs text-gray-700 font-medium">${workflow.total_cost.toFixed(2)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
