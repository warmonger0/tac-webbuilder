import { PreflightCheckPanel } from './PreflightCheckPanel';
import { AdwWorkflowCatalog } from './AdwWorkflowCatalog';

interface WorkflowExecution {
  adw_id: string;
  issue_number: number;
  phase: string;
  github_url: string;
}

export function WorkflowDashboard() {
  return (
    <div className="space-y-6">
      {/* Pre-flight Health Checks */}
      <PreflightCheckPanel />

      {/* ADW Workflow Catalog */}
      <AdwWorkflowCatalog />
    </div>
  );
}
