import { AdwWorkflowCatalog } from './AdwWorkflowCatalog';

export function WorkflowDashboard() {
  return (
    <div className="space-y-4">
      {/* Workflow Catalog */}
      <div className="min-h-[600px]">
        <AdwWorkflowCatalog />
      </div>
    </div>
  );
}
