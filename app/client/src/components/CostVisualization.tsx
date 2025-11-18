import { useEffect, useState } from 'react';
import { fetchWorkflowCosts } from '../api/client';
import type { CostData, PhaseCost } from '../types';
import { CacheEfficiencyBadge } from './CacheEfficiencyBadge';
import { CostBreakdownChart } from './CostBreakdownChart';
import { CumulativeCostChart } from './CumulativeCostChart';

interface CostVisualizationProps {
  adwId: string;
}

export function CostVisualization({ adwId }: CostVisualizationProps) {
  const [costData, setCostData] = useState<CostData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const loadCostData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchWorkflowCosts(adwId);

        if (response.error) {
          setError(response.error);
        } else if (response.cost_data) {
          setCostData(response.cost_data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load cost data');
      } finally {
        setLoading(false);
      }
    };

    loadCostData();
  }, [adwId]);

  if (loading) {
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-sm text-gray-600">Loading cost data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
        <p className="text-sm text-yellow-800">
          Cost data not available: {error}
        </p>
      </div>
    );
  }

  if (!costData) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-gray-200 pt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-700">
            💰 Cost Analysis
          </span>
          <CacheEfficiencyBadge
            cacheEfficiencyPercent={costData.cache_efficiency_percent}
            cacheSavingsAmount={costData.cache_savings_amount}
          />
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-6">
          {/* Summary Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500 uppercase font-medium">
                Total Cost
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${costData.total_cost.toFixed(4)}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500 uppercase font-medium">
                Total Tokens
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {costData.total_tokens.toLocaleString()}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500 uppercase font-medium">
                Phases Completed
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {costData.phases.length}
              </p>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <CostBreakdownChart phases={costData.phases} />
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <CumulativeCostChart phases={costData.phases} />
            </div>
          </div>

          {/* Detailed Phase Breakdown */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-semibold mb-3 text-gray-700">
              Phase Details
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-600">
                      Phase
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">
                      Cost
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">
                      Input Tokens
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">
                      Cache Write
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">
                      Cache Read
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-gray-600">
                      Output
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {costData.phases.map((phase: PhaseCost) => (
                    <tr key={phase.phase} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium text-gray-900">
                        {phase.phase}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        ${phase.cost.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-600">
                        {phase.tokens.input_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-600">
                        {phase.tokens.cache_creation_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right text-green-600 font-medium">
                        {phase.tokens.cache_read_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-600">
                        {phase.tokens.output_tokens.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
