import { useQuery } from '@tanstack/react-query';
import type { WorkflowTemplate } from '../types';

export function WorkflowDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['workflowCatalog'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/workflow-catalog');
      if (!response.ok) {
        throw new Error('Failed to fetch workflow catalog');
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600">Loading workflow catalog...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-lg p-8 text-center">
        <p className="text-red-600">Error loading workflow catalog</p>
        <p className="text-gray-500 text-sm mt-2">{(error as Error).message}</p>
      </div>
    );
  }

  const workflows: WorkflowTemplate[] = data?.workflows || [];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          ADW Workflow Catalog
        </h2>
        <p className="text-gray-600">
          Available automated development workflows for your projects
        </p>
      </div>

      {/* Workflow catalog cards */}
      <div className="space-y-4">
        {workflows.map((workflow) => (
          <div
            key={workflow.name}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1">
                  {workflow.display_name}
                </h3>
                <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-700">
                  {workflow.name}
                </code>
              </div>
              <div className="ml-4">
                <span className="inline-block px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded">
                  {workflow.cost_range}
                </span>
              </div>
            </div>

            {/* Workflow phases */}
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Workflow Steps:
              </div>
              <div className="flex flex-wrap gap-2">
                {workflow.phases.map((phase, index) => (
                  <div key={index} className="flex items-center">
                    <span className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded">
                      {phase}
                    </span>
                    {index < workflow.phases.length - 1 && (
                      <span className="mx-2 text-gray-400">→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Purpose */}
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-700 mb-1">
                Purpose:
              </div>
              <p className="text-sm text-gray-600">{workflow.purpose}</p>
            </div>

            {/* Best for */}
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Best for:
              </div>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {workflow.best_for.map((useCase, index) => (
                  <li
                    key={index}
                    className="flex items-start text-sm text-gray-600"
                  >
                    <span className="text-green-500 mr-2">✓</span>
                    {useCase}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
