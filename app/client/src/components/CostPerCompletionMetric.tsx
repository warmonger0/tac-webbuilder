import { useEffect, useState } from 'react';
import { getCostPerCompletionMetrics } from '../api/workflowClient';
import type { CostPerCompletionMetrics } from '../types';
import { TrendIndicator } from './TrendIndicator';

interface CostPerCompletionMetricProps {
  defaultPeriod?: '7d' | '30d' | 'all';
}

/**
 * Detailed cost per completion metric component with trend comparison and phase breakdown.
 *
 * Features:
 * - Displays average cost per successful completion prominently
 * - Shows trend indicator for selected period
 * - Includes completion count and total cost for context
 * - Expandable section for phase cost breakdown
 * - Period toggle (7d/30d/all)
 * - Loading and error states
 */
export function CostPerCompletionMetric({ defaultPeriod = '7d' }: CostPerCompletionMetricProps) {
  const [period, setPeriod] = useState<'7d' | '30d' | 'all'>(defaultPeriod);
  const [metrics, setMetrics] = useState<CostPerCompletionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBreakdown, setShowBreakdown] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCostPerCompletionMetrics(period, true);
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [period]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <p className="text-red-600 text-sm">Error: {error}</p>
      </div>
    );
  }

  if (!metrics) return null;

  const avgCost = metrics.current_period.avg_cost;
  const completionCount = metrics.current_period.completion_count;
  const totalCost = metrics.current_period.total_cost;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold text-gray-900">Avg Cost Per Success</h3>

        {/* Period Toggle */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {(['7d', '30d', 'all'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                period === p
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {p === 'all' ? 'All Time' : p}
            </button>
          ))}
        </div>
      </div>

      {/* Main Metric */}
      <div className="mb-4">
        <div className="flex items-baseline gap-3">
          <p className="text-3xl font-bold text-green-600">
            ${avgCost.toFixed(3)}
          </p>
          {metrics.trend && (
            <TrendIndicator
              percentChange={metrics.trend.percent_change}
              trend={metrics.trend.trend}
              invertColors={true}
            />
          )}
        </div>
        <p className="text-sm text-gray-600 mt-1">
          {completionCount} successful completion{completionCount !== 1 ? 's' : ''} • Total: ${totalCost.toFixed(2)}
        </p>
      </div>

      {/* Phase Breakdown Toggle */}
      {metrics.phase_breakdown && metrics.phase_breakdown.length > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <button
            onClick={() => setShowBreakdown(!showBreakdown)}
            className="w-full flex items-center justify-between text-sm font-semibold text-gray-700 hover:text-gray-900"
            aria-expanded={showBreakdown}
          >
            <span>Phase Cost Breakdown</span>
            <span className="text-lg">{showBreakdown ? '−' : '+'}</span>
          </button>

          {showBreakdown && (
            <div className="mt-4 space-y-3">
              {metrics.phase_breakdown.map((phase) => (
                <div key={phase.phase} className="flex items-center justify-between text-sm">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-700">{phase.phase}</span>
                      <span className="text-gray-900 font-semibold">${phase.total_cost.toFixed(3)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${phase.percent_of_total}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {phase.workflow_count} workflow{phase.workflow_count !== 1 ? 's' : ''} • {phase.percent_of_total.toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {completionCount === 0 && (
        <p className="text-sm text-gray-500 italic">No successful completions in this period</p>
      )}
    </div>
  );
}
