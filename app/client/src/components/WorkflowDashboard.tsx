import { useQuery } from '@tanstack/react-query';
import { PreflightCheckPanel } from './PreflightCheckPanel';

interface WorkflowExecution {
  adw_id: string;
  issue_number: number;
  phase: string;
  github_url: string;
}

export function WorkflowDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await fetch('/api/v1/workflows');
      if (!response.ok) {
        throw new Error('Failed to fetch workflows');
      }
      return response.json();
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600">Loading active workflows...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-lg p-8 text-center">
        <p className="text-red-600">Error loading workflows</p>
        <p className="text-gray-500 text-sm mt-2">{(error as Error).message}</p>
      </div>
    );
  }

  const workflows: WorkflowExecution[] = Array.isArray(data) ? data : [];

  // Group workflows by phase
  const phaseGroups = workflows.reduce((acc, workflow) => {
    const phase = workflow.phase || 'unknown';
    if (!acc[phase]) {
      acc[phase] = [];
    }
    acc[phase].push(workflow);
    return acc;
  }, {} as Record<string, WorkflowExecution[]>);

  const phaseOrder = ['plan', 'build', 'test', 'review', 'document', 'ship'];
  const sortedPhases = Object.keys(phaseGroups).sort((a, b) => {
    const indexA = phaseOrder.indexOf(a);
    const indexB = phaseOrder.indexOf(b);
    if (indexA === -1 && indexB === -1) return a.localeCompare(b);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });

  const getPhaseColor = (phase: string) => {
    const colors: Record<string, string> = {
      'plan': 'bg-blue-100 text-blue-800',
      'build': 'bg-yellow-100 text-yellow-800',
      'test': 'bg-purple-100 text-purple-800',
      'review': 'bg-pink-100 text-pink-800',
      'document': 'bg-green-100 text-green-800',
      'ship': 'bg-emerald-100 text-emerald-800',
    };
    return colors[phase] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Pre-flight Health Checks */}
      <PreflightCheckPanel />

      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Active ADW Workflows
        </h2>
        <p className="text-gray-600">
          {workflows.length} workflow{workflows.length !== 1 ? 's' : ''} currently tracked
        </p>
      </div>

      {workflows.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600">No active workflows</p>
          <p className="text-gray-500 text-sm mt-2">
            Submit a request in the "New Request" tab to start a workflow
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {sortedPhases.map((phase) => (
            <div key={phase} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {/* Phase Header */}
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 capitalize">
                    {phase} Phase
                  </h3>
                  <span className="text-sm text-gray-600">
                    {phaseGroups[phase].length} workflow{phaseGroups[phase].length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Workflows Table */}
              <div className="divide-y divide-gray-200">
                {phaseGroups[phase].map((workflow) => (
                  <div
                    key={workflow.adw_id}
                    className="p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <a
                            href={workflow.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            Issue #{workflow.issue_number}
                          </a>
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getPhaseColor(workflow.phase)}`}>
                            {workflow.phase}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <code className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">
                            {workflow.adw_id}
                          </code>
                        </div>
                      </div>
                      <div className="ml-4">
                        <a
                          href={workflow.github_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                          </svg>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
