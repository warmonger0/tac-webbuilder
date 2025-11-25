import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import type { PatternStatisticsResponse, PatternStatisticsItem, AutomationStatus } from '../types';
import { getPatternStatistics } from '../api/client';
import { PatternStatisticsPanel } from './pattern-learning-dashboard/PatternStatisticsPanel';

export function PatternLearningDashboard() {
  const [selectedPattern, setSelectedPattern] = useState<PatternStatisticsItem | null>(null);
  const [sortBy, setSortBy] = useState<"occurrence_count" | "confidence_score" | "potential_monthly_savings">("occurrence_count");
  const [filterStatus, setFilterStatus] = useState<string>("");

  // Fetch pattern statistics with polling
  const { data, isLoading, error, refetch } = useQuery<PatternStatisticsResponse>({
    queryKey: ['pattern-statistics', sortBy, filterStatus],
    queryFn: () => getPatternStatistics({
      limit: 20,
      sort_by: sortBy,
      filter_by_status: filterStatus || undefined,
    }),
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 25000,
  });

  const getStatusColor = (status: AutomationStatus): string => {
    const colors: Record<AutomationStatus, string> = {
      detected: 'bg-gray-100 text-gray-800',
      candidate: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      implemented: 'bg-green-100 text-green-800',
      active: 'bg-green-100 text-green-800',
      deprecated: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading pattern statistics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-red-900 mb-2">Error Loading Pattern Statistics</h2>
        <p className="text-red-700 mb-4">{error instanceof Error ? error.message : 'Unknown error occurred'}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center text-gray-600 py-12">
        No pattern data available
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pattern Learning Dashboard</h1>
          <p className="text-sm text-gray-600 mt-1">Monitor pattern recognition progress and automation opportunities</p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Statistics Panel */}
      <PatternStatisticsPanel summary={data.summary} />

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label htmlFor="sort-by" className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="occurrence_count">Occurrence Count</option>
              <option value="confidence_score">Confidence Score</option>
              <option value="potential_monthly_savings">Potential Savings</option>
            </select>
          </div>

          <div>
            <label htmlFor="filter-status" className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Status
            </label>
            <select
              id="filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="detected">Detected</option>
              <option value="candidate">Candidate</option>
              <option value="approved">Approved</option>
              <option value="implemented">Implemented</option>
              <option value="active">Active</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>
        </div>
      </div>

      {/* Top Patterns Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">Top Patterns</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pattern
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occurrences
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monthly Savings
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.top_patterns.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No patterns detected yet
                  </td>
                </tr>
              ) : (
                data.top_patterns.map((pattern) => (
                  <tr key={pattern.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {pattern.pattern_signature}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pattern.pattern_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(pattern.automation_status)}`}>
                        {pattern.automation_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pattern.occurrence_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pattern.confidence_score.toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatCurrency(pattern.potential_monthly_savings)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedPattern(pattern)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Discoveries */}
      {data.recent_discoveries.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Discoveries (Last 30 Days)</h3>
          <div className="space-y-2">
            {data.recent_discoveries.map((pattern) => (
              <div key={pattern.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{pattern.pattern_signature}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Discovered: {pattern.first_detected ? new Date(pattern.first_detected).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(pattern.automation_status)}`}>
                  {pattern.automation_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pattern Details Modal */}
      {selectedPattern && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedPattern(null)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900">Pattern Details</h3>
              <button
                onClick={() => setSelectedPattern(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Pattern Signature</h4>
                <p className="text-sm text-gray-900">{selectedPattern.pattern_signature}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Pattern Type</h4>
                  <p className="text-sm text-gray-900">{selectedPattern.pattern_type}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Status</h4>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedPattern.automation_status)}`}>
                    {selectedPattern.automation_status}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Occurrences</h4>
                  <p className="text-2xl font-bold text-gray-900">{selectedPattern.occurrence_count}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Confidence</h4>
                  <p className="text-2xl font-bold text-gray-900">{selectedPattern.confidence_score.toFixed(1)}%</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Monthly Savings</h4>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(selectedPattern.potential_monthly_savings)}</p>
                </div>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Cost Comparison</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-red-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">With LLM</p>
                    <p className="font-semibold text-gray-900">{selectedPattern.avg_tokens_with_llm} tokens</p>
                    <p className="text-xs text-gray-600">{formatCurrency(selectedPattern.avg_cost_with_llm)}</p>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">With Tool</p>
                    <p className="font-semibold text-gray-900">{selectedPattern.avg_tokens_with_tool} tokens</p>
                    <p className="text-xs text-gray-600">{formatCurrency(selectedPattern.avg_cost_with_tool)}</p>
                  </div>
                </div>
              </div>
              {selectedPattern.tool_name && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Associated Tool</h4>
                  <p className="text-sm text-gray-900">{selectedPattern.tool_name}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">First Detected</h4>
                  <p className="text-sm text-gray-900">
                    {selectedPattern.first_detected ? new Date(selectedPattern.first_detected).toLocaleString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Last Seen</h4>
                  <p className="text-sm text-gray-900">
                    {selectedPattern.last_seen ? new Date(selectedPattern.last_seen).toLocaleString() : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
