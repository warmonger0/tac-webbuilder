import type { CostEstimate, GitHubIssue, PredictedPattern } from '../types';
import { IssuePreview } from './IssuePreview';
import { CostEstimateCard } from './CostEstimateCard';

interface ConfirmDialogProps {
  issue: GitHubIssue;
  costEstimate?: CostEstimate | null;
  predictedPatterns?: PredictedPattern[] | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  issue,
  costEstimate,
  predictedPatterns,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 space-y-6">
          <h3 className="text-2xl font-bold">Confirm GitHub Issue</h3>

          {/* Predicted Patterns Display */}
          {predictedPatterns && predictedPatterns.length > 0 && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
              <h4 className="text-sm font-medium text-emerald-600 mb-2">
                🎯 Detected Patterns
              </h4>
              <div className="flex flex-wrap gap-2">
                {predictedPatterns.map((pred, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-emerald-500/20 text-emerald-700 text-xs rounded-md border border-emerald-500/30">
                      {pred.pattern}
                    </span>
                    <span className="text-xs text-gray-600">
                      {(pred.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cost Estimate - Show prominently at top */}
          {costEstimate && (
            <CostEstimateCard estimate={costEstimate} />
          )}

          {/* GitHub Issue Preview */}
          <IssuePreview issue={issue} />

          <div className="flex gap-4">
            <button
              onClick={onConfirm}
              className="flex-1 bg-primary text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              {costEstimate
                ? `Post to GitHub (Est. $${costEstimate.min_cost.toFixed(2)}-$${costEstimate.max_cost.toFixed(2)})`
                : 'Post to GitHub'}
            </button>
            <button
              onClick={onCancel}
              className="flex-1 bg-gray-200 text-gray-800 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
