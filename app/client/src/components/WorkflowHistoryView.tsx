import { useState } from 'react';
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';
import { WorkflowHistoryCard } from './WorkflowHistoryCard';
import { HistoryAnalytics } from './HistoryAnalytics';

export function WorkflowHistoryView() {
  const { workflows, totalCount, analytics, isConnected, lastUpdated } = useWorkflowHistoryWebSocket();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterModel, setFilterModel] = useState<string>('');

  // Filter workflows locally based on current filters
  const filteredWorkflows = workflows.filter((workflow) => {
    if (searchTerm && !workflow.adw_id.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !workflow.nl_input?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterStatus && workflow.status !== filterStatus) {
      return false;
    }
    if (filterModel && workflow.model_used !== filterModel) {
      return false;
    }
    return true;
  });

  // Get unique models and statuses for filter dropdowns
  const uniqueModels = Array.from(new Set(workflows.map(w => w.model_used).filter(Boolean)));
  const uniqueStatuses = Array.from(new Set(workflows.map(w => w.status)));

  // Connection status indicator
  const ConnectionStatus = () => {
    const statusColor = isConnected ? 'bg-green-500' : 'bg-yellow-500';
    const statusText = isConnected ? 'Live' : 'Polling';

    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${statusColor} ${isConnected ? 'animate-pulse' : ''}`} />
        <span className="text-sm text-gray-600">{statusText}</span>
        {lastUpdated && (
          <span className="text-xs text-gray-500">
            Updated {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Workflow History</h2>
        <ConnectionStatus />
      </div>

      {/* Analytics Summary */}
      {analytics && <HistoryAnalytics analytics={analytics} />}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by ADW ID or request..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              {uniqueStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Model Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model
            </label>
            <select
              value={filterModel}
              onChange={(e) => setFilterModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Models</option>
              {uniqueModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filters Display */}
        {(searchTerm || filterStatus || filterModel) && (
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-600">Active filters:</span>
            {searchTerm && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Search: {searchTerm}
              </span>
            )}
            {filterStatus && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Status: {filterStatus}
              </span>
            )}
            {filterModel && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Model: {filterModel}
              </span>
            )}
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('');
                setFilterModel('');
              }}
              className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredWorkflows.length} of {totalCount} workflows
      </div>

      {/* Workflow Cards */}
      {filteredWorkflows.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 text-lg">No workflow history found</p>
          <p className="text-gray-500 text-sm mt-2">
            {workflows.length === 0
              ? 'Workflow executions will appear here once they are run'
              : 'Try adjusting your filters'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredWorkflows.map((workflow) => (
            <WorkflowHistoryCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      )}
    </div>
  );
}
