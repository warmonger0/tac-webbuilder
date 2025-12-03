import type { HistoryAnalytics as HistoryAnalyticsType } from '../types';
import { TrendIndicator } from './TrendIndicator';

interface HistoryAnalyticsProps {
  analytics: HistoryAnalyticsType;
}

export function HistoryAnalytics({ analytics }: HistoryAnalyticsProps) {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  };

  const stats = [
    {
      label: 'Total Workflows',
      value: analytics.total_workflows.toString(),
      color: 'text-gray-900',
    },
    {
      label: 'Completed',
      value: analytics.completed_workflows.toString(),
      color: 'text-green-600',
    },
    {
      label: 'Failed',
      value: analytics.failed_workflows.toString(),
      color: 'text-red-600',
    },
    {
      label: 'Success Rate',
      value: `${analytics.success_rate_percent.toFixed(1)}%`,
      color: 'text-blue-600',
    },
    {
      label: 'Avg Duration',
      value: formatDuration(analytics.avg_duration_seconds),
      color: 'text-purple-600',
    },
    {
      label: 'Avg Cost/Success',
      value: `$${(analytics.avg_cost_per_successful_completion ?? 0).toFixed(3)}`,
      color: 'text-green-600',
      trend: analytics.cost_trend_7d !== undefined && analytics.cost_trend_7d !== null
        ? {
            percentChange: analytics.cost_trend_7d,
            direction: analytics.cost_trend_7d > 1 ? 'up' as const : analytics.cost_trend_7d < -1 ? 'down' as const : 'neutral' as const
          }
        : undefined,
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Analytics Summary</h3>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="text-center">
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-600 mt-1">{stat.label}</p>
            {stat.trend && (
              <div className="mt-1">
                <TrendIndicator
                  percentChange={stat.trend.percentChange}
                  trend={stat.trend.direction}
                  invertColors={true}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Breakdown by Model */}
      {Object.keys(analytics.workflows_by_model).length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">By Model:</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(analytics.workflows_by_model).map(([model, count]) => (
              <span
                key={model}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"
              >
                {model}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Breakdown by Template */}
      {Object.keys(analytics.workflows_by_template).length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">By Template:</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(analytics.workflows_by_template).map(([template, count]) => (
              <span
                key={template}
                className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium"
              >
                {template}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
