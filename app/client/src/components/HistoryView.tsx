import { useState, useEffect } from 'react';
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';
import { WorkflowHistoryCard } from './WorkflowHistoryCard';
import { WorkflowHistoryFilters } from './WorkflowHistoryFilters';
import { WorkflowHistorySummary } from './WorkflowHistorySummary';
import type { WorkflowHistoryFilter, WorkflowHistoryItem } from '../types';

export function HistoryView() {
  const { workflowHistory, isConnected, lastUpdated } = useWorkflowHistoryWebSocket();
  const [filters, setFilters] = useState<WorkflowHistoryFilter>({
    sort_by: 'date',
    order: 'desc',
    model_filter: 'all',
    template_filter: 'all',
    status_filter: 'all',
    search_query: '',
  });

  // Apply client-side filtering and sorting
  const [filteredHistory, setFilteredHistory] = useState<WorkflowHistoryItem[]>([]);

  useEffect(() => {
    let filtered = [...workflowHistory];

    // Apply search filter
    if (filters.search_query && filters.search_query.trim() !== '') {
      const query = filters.search_query.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.adw_id.toLowerCase().includes(query) ||
          item.issue_number?.toString().includes(query) ||
          item.user_input?.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (filters.status_filter && filters.status_filter !== 'all') {
      filtered = filtered.filter((item) => item.status === filters.status_filter);
    }

    // Apply model filter
    if (filters.model_filter && filters.model_filter !== 'all') {
      filtered = filtered.filter((item) => item.model_set === filters.model_filter);
    }

    // Apply sorting
    if (filters.sort_by === 'date') {
      filtered.sort((a, b) => {
        const dateA = new Date(a.started_at).getTime();
        const dateB = new Date(b.started_at).getTime();
        return filters.order === 'asc' ? dateA - dateB : dateB - dateA;
      });
    } else if (filters.sort_by === 'duration') {
      filtered.sort((a, b) => {
        const durA = a.total_duration_seconds || 0;
        const durB = b.total_duration_seconds || 0;
        return filters.order === 'asc' ? durA - durB : durB - durA;
      });
    } else if (filters.sort_by === 'status') {
      filtered.sort((a, b) => {
        const statusOrder = { in_progress: 0, completed: 1, failed: 2 };
        const statusA = statusOrder[a.status as keyof typeof statusOrder] ?? 3;
        const statusB = statusOrder[b.status as keyof typeof statusOrder] ?? 3;
        return filters.order === 'asc' ? statusA - statusB : statusB - statusA;
      });
    }

    setFilteredHistory(filtered);
  }, [workflowHistory, filters]);

  const handleFilterChange = (newFilters: Partial<WorkflowHistoryFilter>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleClearFilters = () => {
    setFilters({
      sort_by: 'date',
      order: 'desc',
      model_filter: 'all',
      template_filter: 'all',
      status_filter: 'all',
      search_query: '',
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Workflow History</h2>

        {/* Connection Status */}
        <div className="flex items-center gap-2 text-sm">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          ></div>
          <span className="text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {lastUpdated && (
            <span className="text-gray-500">
              • Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Summary Panel */}
      <WorkflowHistorySummary />

      {/* Filters */}
      <WorkflowHistoryFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
      />

      {/* Workflow History Cards */}
      {filteredHistory.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 text-lg">No workflow history found</p>
          <p className="text-gray-500 text-sm mt-2">
            {workflowHistory.length === 0
              ? 'Workflow executions will appear here once they start'
              : 'Try adjusting your filters to see more results'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredHistory.map((item) => (
            <WorkflowHistoryCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
