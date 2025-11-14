import { useQuery } from '@tanstack/react-query';
import { listWorkflows } from '../api/client';
import { WorkflowCard } from './WorkflowCard';

export function WorkflowDashboard() {
  const {
    data: workflows,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflows'],
    queryFn: listWorkflows,
    refetchInterval: 5000, // Poll every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-600">Loading workflows...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        Error loading workflows: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (!workflows || workflows.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 text-lg">No active workflows</p>
        <p className="text-gray-500 text-sm mt-2">
          Submit a request to start a new workflow
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Active Workflows ({workflows.length})
      </h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workflows.map((workflow) => (
          <WorkflowCard key={workflow.adw_id} workflow={workflow} />
        ))}
      </div>
    </div>
  );
}
