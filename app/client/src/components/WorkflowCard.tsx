import { useEffect, useState } from 'react';
import type { WorkflowExecution } from '../types';
import { StatusBadge } from './StatusBadge';
import { ProgressBar } from './ProgressBar';
import { CostVisualization } from './CostVisualization';

interface WorkflowCardProps {
  workflow: WorkflowExecution;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const phases = ['plan', 'build', 'test', 'review', 'document', 'ship'];
  const [isUpdating, setIsUpdating] = useState(false);

  // Trigger pulse animation when phase changes
  useEffect(() => {
    setIsUpdating(true);
    const timer = setTimeout(() => setIsUpdating(false), 1000);
    return () => clearTimeout(timer);
  }, [workflow.phase]);

  return (
    <div
      className={`bg-white border rounded-lg p-6 hover:shadow-lg transition-all duration-300 ${
        isUpdating
          ? 'border-blue-500 shadow-md ring-2 ring-blue-200'
          : 'border-gray-200'
      }`}
    >
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

      <CostVisualization adwId={workflow.adw_id} />
    </div>
  );
}
