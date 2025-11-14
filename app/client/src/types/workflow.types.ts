/**
 * Workflow Execution Types
 *
 * These types represent active workflow executions and their state.
 * Renamed from "Workflow" to "WorkflowExecution" to avoid naming conflicts.
 */

export interface WorkflowExecution {
  adw_id: string;
  issue_number: number;
  phase: string;
  github_url: string;
}
