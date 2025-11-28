import type { CostEstimate } from '../types';
import { thresholds } from '../config/thresholds';
import { costEstimateIcons } from '../config/theme';

interface CostEstimateCardProps {
  estimate: CostEstimate;
}

/**
 * CostEstimateCard - Displays cost estimation for workflow execution
 *
 * Shows complexity level, cost range, confidence, reasoning, and high-cost warnings.
 * Color-coded by complexity: green (lightweight), yellow (standard), red (complex).
 */
export function CostEstimateCard({ estimate }: CostEstimateCardProps) {
  // Color coding by complexity level
  const levelConfig = {
    lightweight: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      badge: 'bg-green-100 text-green-800',
      icon: costEstimateIcons.lightweight,
    },
    standard: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      badge: 'bg-yellow-100 text-yellow-800',
      icon: costEstimateIcons.standard,
    },
    complex: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      badge: 'bg-red-100 text-red-800',
      icon: costEstimateIcons.complex,
    },
  };

  const config = levelConfig[estimate.level];
  const showWarning = estimate.max_cost > thresholds.cost.highCostWarning;

  return (
    <div className={`rounded-lg border-2 p-5 ${config.bg} ${config.border}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <h3 className={`text-lg font-semibold ${config.text}`}>
            Estimated Cost
          </h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.badge}`}>
          {estimate.level.toUpperCase()}
        </span>
      </div>

      {/* Cost Range */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Cost Range</div>
        <div className={`text-3xl font-bold ${config.text}`}>
          ${estimate.min_cost.toFixed(2)} - ${estimate.max_cost.toFixed(2)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Confidence: {(estimate.confidence * 100).toFixed(0)}%
        </div>
      </div>

      {/* Workflow */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Recommended Workflow</div>
        <code className="text-sm bg-white rounded px-2 py-1 border border-gray-200">
          {estimate.recommended_workflow}
        </code>
      </div>

      {/* Reasoning */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Analysis</div>
        <div className="text-sm text-gray-700 bg-white rounded p-3 border border-gray-200">
          {estimate.reasoning || 'Standard complexity assessment'}
        </div>
      </div>

      {/* High Cost Warning */}
      {showWarning && (
        <div className="bg-red-100 border border-red-300 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <div className="flex-1">
              <div className="font-semibold text-red-800 mb-1">
                High Cost Warning
              </div>
              <div className="text-sm text-red-700 mb-2">
                This workflow may be expensive. Consider:
              </div>
              <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                <li>Breaking into smaller issues (2-3 separate workflows)</li>
                <li>Narrowing the scope to essential features only</li>
                <li>Implementing manually for complex parts</li>
                <li>Using the lightweight workflow if applicable</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Cost Comparison */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          💡 <strong>Tip:</strong> Lightweight workflows ($0.20-$0.50) are ideal for simple
          UI changes, docs, and single-file modifications.
        </div>
      </div>
    </div>
  );
}
