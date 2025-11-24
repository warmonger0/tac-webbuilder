import type { WorkflowHistoryItem } from '../../../types';

interface ResourceSectionProps {
  workflow: WorkflowHistoryItem;
}

export function ResourceSection({ workflow }: ResourceSectionProps) {
  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        💾 Resource Usage
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
        {workflow.backend_port && (
          <div className="bg-gray-50 rounded p-3">
            <div className="text-gray-600">Backend Port</div>
            <div className="font-medium">{workflow.backend_port}</div>
          </div>
        )}
        {workflow.frontend_port && (
          <div className="bg-gray-50 rounded p-3">
            <div className="text-gray-600">Frontend Port</div>
            <div className="font-medium">{workflow.frontend_port}</div>
          </div>
        )}
        <div className="bg-gray-50 rounded p-3">
          <div className="text-gray-600">Concurrent Workflows</div>
          <div className="font-medium">{workflow.concurrent_workflows}</div>
        </div>
        <div className="bg-gray-50 rounded p-3">
          <div className="text-gray-600">Worktree Reused</div>
          <div className="font-medium">{workflow.worktree_reused ? 'Yes' : 'No'}</div>
        </div>
      </div>
    </div>
  );
}
