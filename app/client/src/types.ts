export interface GitHubIssue {
  title: string;
  body: string;
  labels: string[];
  classification: string;
  workflow: string;
  model_set: string;
}

export interface Workflow {
  adw_id: string;
  issue_number: number;
  phase: string;
  github_url: string;
}

export interface HistoryItem {
  id: string;
  nl_input: string;
  project: string;
  issue_number?: number;
  status: string;
  timestamp: string;
  github_url?: string;
}

export interface SubmitRequestData {
  nl_input: string;
  project_path?: string;
  auto_post: boolean;
}

export interface SubmitRequestResponse {
  request_id: string;
}

export interface ConfirmResponse {
  issue_number: number;
  github_url: string;
}

export interface Route {
  path: string;
  method: string;
  handler: string;
  description: string;
}

export interface RoutesResponse {
  routes: Route[];
  total: number;
}

export interface WorkflowTemplate {
  name: string;
  display_name: string;
  phases: string[];
  purpose: string;
  cost_range: string;
  best_for: string[];
}

export interface WorkflowCatalogResponse {
  workflows: WorkflowTemplate[];
  total: number;
}

// Cost Visualization Types
export interface TokenBreakdown {
  input_tokens: number;
  cache_creation_tokens: number;
  cache_read_tokens: number;
  output_tokens: number;
}

export interface PhaseCost {
  phase: string;
  cost: number;
  tokens: TokenBreakdown;
  timestamp?: string;
}

export interface CostData {
  adw_id: string;
  phases: PhaseCost[];
  total_cost: number;
  cache_efficiency_percent: number;
  cache_savings_amount: number;
  total_tokens: number;
}

export interface CostResponse {
  cost_data?: CostData;
  error?: string;
}
