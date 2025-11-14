import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getWorkflowHistory } from '../api/client';
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';
import { WorkflowHistoryCard } from './WorkflowHistoryCard';
import { HistoryAnalytics } from './HistoryAnalytics';
import type { HistoryFilters } from '../types';

export function HistoryView() {
  const [filters, setFilters] = useState<HistoryFilters>({
    limit: 20,
    offset: 0,
    sort_by: 'created_at',
    sort_order: 'DESC',
  });

  const [searchTerm, setSearchTerm] = useState('');

  // Use WebSocket for real-time updates
  const { history: wsHistory, isConnected } = useWorkflowHistoryWebSocket();

  // Fallback to REST API when WebSocket disconnected
  const {
    data: apiData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflow-history', filters],
    queryFn: () => getWorkflowHistory(filters),
    enabled: !isConnected, // Only query when WebSocket is not connected
  });

  // Use WebSocket data if available, otherwise use API data
  const history = isConnected ? wsHistory : (apiData?.workflows || []);
  const analytics = apiData?.analytics;

  const handleSearch = () => {
    setFilters({
      ...filters,
      search: searchTerm || undefined,
      offset: 0, // Reset to first page on new search
    });
  };

  const handleFilterChange = (key: keyof HistoryFilters, value: string | undefined) => {
    setFilters({
      ...filters,
      [key]: value,
      offset: 0, // Reset to first page on filter change
    });
  };

  const handleSortChange = (sortBy: string) => {
    setFilters({
      ...filters,
      sort_by: sortBy,
      offset: 0,
    });
  };

  if (isLoading && !isConnected) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-600">Loading workflow history...</div>
      </div>
    );
  }

  if (error && !isConnected) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        Error loading history: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Workflow History</h2>
          <p className="text-sm text-gray-600 mt-1">
            {isConnected ? (
              <span className="text-green-600">● Live updates</span>
            ) : (
              <span className="text-gray-500">○ Polling</span>
            )}
          </p>
        </div>
      </div>

      {/* Analytics Summary */}
      {analytics && <HistoryAnalytics analytics={analytics} />}

      {/* Search and Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <input
              type="text"
              placeholder="Search by ADW ID or request..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <select
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
            <option value="pending">Pending</option>
          </select>

          {/* Sort */}
          <select
            value={filters.sort_by}
            onChange={(e) => handleSortChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="created_at">Sort by Date</option>
            <option value="duration_seconds">Sort by Duration</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>

        {/* Search Button */}
        <button
          onClick={handleSearch}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Search
        </button>
      </div>

      {/* Empty State */}
      {history.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 text-lg">No workflow history</p>
          <p className="text-gray-500 text-sm mt-2">
            Workflow executions will appear here once they are tracked
          </p>
        </div>
      )}

      {/* History Cards */}
      {history.length > 0 && (
        <div className="grid grid-cols-1 gap-4">
          {history.map((workflow) => (
            <WorkflowHistoryCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      )}

      {/* Pagination Info */}
      {history.length > 0 && apiData && (
        <div className="text-center text-sm text-gray-600">
          Showing {history.length} of {apiData.total} workflows
        </div>
      )}
    </div>
  );
}
