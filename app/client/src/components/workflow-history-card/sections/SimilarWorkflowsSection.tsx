import type { WorkflowHistoryItem } from '../../../types';
import { SimilarWorkflowsComparison } from '../../SimilarWorkflowsComparison';

interface SimilarWorkflowsSectionProps {
  workflow: WorkflowHistoryItem;
}

export function SimilarWorkflowsSection({ workflow }: SimilarWorkflowsSectionProps) {
  if (!workflow.similar_workflow_ids || workflow.similar_workflow_ids.length === 0) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        🔗 Similar Workflows
      </h3>

      <div className="text-sm text-gray-600 mb-3">
        Found {workflow.similar_workflow_ids.length} similar workflows
      </div>

      <SimilarWorkflowsComparison
        currentWorkflowId={workflow.adw_id}
        similarWorkflowIds={workflow.similar_workflow_ids}
      />
    </div>
  );
}
