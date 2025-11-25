import type { PatternStatisticsSummary } from '../../types';

interface PatternStatisticsPanelProps {
  summary: PatternStatisticsSummary;
}

export function PatternStatisticsPanel({ summary }: PatternStatisticsPanelProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const stats = [
    {
      label: 'Total Patterns',
      value: summary.total_patterns.toString(),
      color: 'text-gray-900',
      bgColor: 'bg-gray-100',
    },
    {
      label: 'Automated',
      value: summary.automated_patterns.toString(),
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      label: 'Avg Confidence',
      value: `${summary.avg_confidence_score.toFixed(1)}%`,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      label: 'Monthly Savings',
      value: formatCurrency(summary.total_potential_monthly_savings),
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6 mb-6">
      <h2 className="text-lg font-bold text-white mb-4">📊 Pattern Learning Statistics</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className={`${stat.bgColor} rounded-lg p-4`}>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-600 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Additional metrics */}
      <div className="mt-6 pt-6 border-t border-slate-600 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-xl font-semibold text-white">{summary.automation_rate.toFixed(1)}%</p>
          <p className="text-xs text-slate-400 mt-1">Automation Rate</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-white">{summary.high_confidence_patterns}</p>
          <p className="text-xs text-slate-400 mt-1">High Confidence (≥75%)</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-white">{summary.recent_discoveries}</p>
          <p className="text-xs text-slate-400 mt-1">Recent Discoveries (7d)</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-white">{formatCurrency(summary.total_potential_annual_savings)}</p>
          <p className="text-xs text-slate-400 mt-1">Annual Savings Potential</p>
        </div>
      </div>
    </div>
  );
}
