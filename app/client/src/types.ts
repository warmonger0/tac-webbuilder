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

// Workflow History Types
export interface WorkflowExecutionMetrics {
  total_tokens: number;
  input_tokens: number;
  cache_creation_tokens: number;
  cache_read_tokens: number;
  output_tokens: number;
  cache_efficiency_percent: number;
  estimated_cost_total: number;
  actual_cost_total: number;
  cost_per_token: number;
}

export interface WorkflowPerformanceMetrics {
  completion_time_seconds?: number;
  retry_count: number;
  success_rate: number;
  concurrent_workflows_count: number;
}

export interface WorkflowResourceMetrics {
  worktree_id?: string;
  worktree_reused: boolean;
  ports_used: Record<string, number>;
  structured_input?: Record<string, any>;
}

export interface WorkflowHistoryItem {
  id?: number;
  adw_id: string;
  issue_number?: number;
  workflow_template: string;
  start_timestamp: string;
  end_timestamp?: string;
  status: 'in_progress' | 'completed' | 'failed';
  nl_input: string;
  model_used?: string;
  error_message?: string;
  execution_metrics: WorkflowExecutionMetrics;
  performance_metrics: WorkflowPerformanceMetrics;
  resource_metrics: WorkflowResourceMetrics;
  phases: PhaseCost[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowAnalytics {
  total_workflows: number;
  avg_cost_by_model: Record<string, number>;
  avg_cost_by_template: Record<string, number>;
  avg_completion_time: number;
  overall_success_rate: number;
  cache_hit_rate: number;
  most_expensive_workflows: Array<{
    adw_id: string;
    nl_input: string;
    cost: number;
    template: string;
  }>;
  token_efficiency_by_model: Record<string, number>;
  total_cost_all_time: number;
  total_tokens_all_time: number;
}

export interface WorkflowHistoryFilter {
  limit?: number;
  offset?: number;
  sort_by?: 'date' | 'cost' | 'duration' | 'success_rate' | 'model';
  order?: 'asc' | 'desc';
  filter_status?: 'in_progress' | 'completed' | 'failed';
  filter_template?: string;
  filter_model?: string;
  date_from?: string;
  date_to?: string;
  search_query?: string;
}

export interface WorkflowHistoryResponse {
  items: WorkflowHistoryItem[];
  analytics: WorkflowAnalytics;
  total: number;
  has_more: boolean;
}
