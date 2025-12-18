import type { WorkflowHistoryItem } from '../../../types';

interface InsightsSectionProps {
  workflow: WorkflowHistoryItem;
}

export function InsightsSection({ workflow }: InsightsSectionProps) {
  const hasAnomalies = workflow.anomaly_flags && workflow.anomaly_flags.length > 0;
  const hasRecommendations = workflow.optimization_recommendations && workflow.optimization_recommendations.length > 0;

  if (!hasAnomalies && !hasRecommendations) return null;

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        💡 Insights & Recommendations
      </h3>

      {/* Anomaly Alerts */}
      {hasAnomalies && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-orange-700 mb-2">⚠️ Anomalies Detected</h4>
          <ul className="space-y-2">
            {workflow.anomaly_flags!.map((anomaly, idx) => (
              <li key={`anomaly-${idx}`} className="bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                {anomaly}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Optimization Recommendations */}
      {hasRecommendations && (
        <div>
          <h4 className="text-sm font-semibold text-green-700 mb-2">✅ Optimization Tips</h4>
          <ul className="space-y-2">
            {workflow.optimization_recommendations!.map((rec, idx) => (
              <li key={`rec-${idx}`} className="bg-green-50 border border-green-200 rounded p-3 text-sm">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
