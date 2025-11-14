import type { Workflow } from '../types';
import { StatusBadge } from './StatusBadge';
import { ProgressBar } from './ProgressBar';

interface WorkflowCardProps {
  workflow: Workflow;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const phases = ['plan', 'build', 'test', 'review', 'document', 'ship'];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-lg font-bold text-gray-900">
            Issue #{workflow.issue_number}
          </h4>
          <p className="text-sm text-gray-600 mt-1">ADW ID: {workflow.adw_id}</p>
        </div>
        <StatusBadge status={workflow.phase} />
      </div>

      <div className="mb-4">
        <ProgressBar phases={phases} current={workflow.phase} />
      </div>

      <a
        href={workflow.github_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center text-primary hover:text-blue-600 font-medium text-sm"
      >
        View on GitHub →
      </a>
    </div>
  );
}
