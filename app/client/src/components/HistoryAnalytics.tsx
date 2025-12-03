import type { HistoryAnalytics as HistoryAnalyticsType } from '../types';

interface HistoryAnalyticsProps {
  analytics: HistoryAnalyticsType;
}

export function HistoryAnalytics({ analytics }: HistoryAnalyticsProps) {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(3)}`;
  };

  const formatTrend = (trend: number) => {
    if (Math.abs(trend) < 0.1) return '→'; // No significant change
    if (trend > 0) return `↑${trend.toFixed(1)}%`; // Increasing
    return `↓${Math.abs(trend).toFixed(1)}%`; // Decreasing
  };

  const getTrendColor = (trend: number) => {
    if (Math.abs(trend) < 0.1) return 'text-gray-500'; // No change
    if (trend > 0) return 'text-red-600'; // Increasing cost is bad (red)
    return 'text-green-600'; // Decreasing cost is good (green)
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
      label: 'Avg Cost / Completion',
      value: formatCost(analytics.avg_cost_per_completion),
      color: 'text-emerald-600',
      subtitle: (
        <div className="flex items-center justify-center gap-2 text-[10px] mt-1">
          <span className={getTrendColor(analytics.cost_trend_7day)}>
            7d: {formatTrend(analytics.cost_trend_7day)}
          </span>
          <span className="text-gray-300">|</span>
          <span className={getTrendColor(analytics.cost_trend_30day)}>
            30d: {formatTrend(analytics.cost_trend_30day)}
          </span>
        </div>
      ),
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Analytics Summary</h3>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="text-center">
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-600 mt-1">{stat.label}</p>
            {stat.subtitle && stat.subtitle}
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
