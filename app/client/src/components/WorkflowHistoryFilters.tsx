import type { WorkflowHistoryFilter } from '../types';

interface WorkflowHistoryFiltersProps {
  filters: WorkflowHistoryFilter;
  onFilterChange: (filters: Partial<WorkflowHistoryFilter>) => void;
  onClearFilters: () => void;
}

export function WorkflowHistoryFilters({
  filters,
  onFilterChange,
  onClearFilters,
}: WorkflowHistoryFiltersProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Sort By */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select
            value={filters.sort_by || 'date'}
            onChange={(e) => onFilterChange({ sort_by: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="date">Date</option>
            <option value="duration">Duration</option>
            <option value="status">Status</option>
          </select>
        </div>

        {/* Order */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order
          </label>
          <select
            value={filters.order || 'desc'}
            onChange={(e) => onFilterChange({ order: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filters.status_filter || 'all'}
            onChange={(e) => onFilterChange({ status_filter: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Model Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Model Set
          </label>
          <select
            value={filters.model_filter || 'all'}
            onChange={(e) => onFilterChange({ model_filter: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All</option>
            <option value="base">Base</option>
            <option value="heavy">Heavy</option>
          </select>
        </div>

        {/* Search */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search (ADW ID, Issue #, or User Input)
          </label>
          <input
            type="text"
            value={filters.search_query || ''}
            onChange={(e) => onFilterChange({ search_query: e.target.value })}
            placeholder="Search..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* Clear Filters Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={onClearFilters}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
}
