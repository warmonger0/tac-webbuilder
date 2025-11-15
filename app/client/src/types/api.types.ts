/**
 * API Request/Response Types
 *
 * These types represent the data structures for API communication
 * between the frontend and backend.
 */

// File Upload Types
export interface FileUploadResponse {
  table_name: string;
  table_schema: Record<string, string>;
  row_count: number;
  sample_data: Record<string, any>[];
  error?: string;
}

// Query Types
export interface QueryRequest {
  query: string;
  llm_provider: "openai" | "anthropic";
  table_name?: string;
}

export interface QueryResponse {
  sql: string;
  results: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  error?: string;
}

// Health Check Types
export interface HealthCheckResponse {
  status: "ok" | "error";
  database_connected: boolean;
  tables_count: number;
  version: string;
  uptime_seconds: number;
}

// System Status Types
export interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "error" | "unknown";
  uptime_seconds?: number;
  uptime_human?: string;
  message?: string;
  details?: Record<string, any>;
}

export interface SystemStatusResponse {
  overall_status: "healthy" | "degraded" | "error";
  timestamp: string;
  services: Record<string, ServiceHealth>;
  summary: {
    healthy_services: number;
    total_services: number;
    health_percentage: number;
  };
}

// Random Query Generation Types
export interface RandomQueryResponse {
  query: string;
  error?: string;
}

// Insights Types
export interface InsightsRequest {
  table_name: string;
  column_names?: string[];
}

export interface ColumnInsight {
  column_name: string;
  data_type: string;
  unique_values: number;
  null_count: number;
  min_value?: any;
  max_value?: any;
  avg_value?: number;
  most_common?: Record<string, any>[];
}

export interface InsightsResponse {
  table_name: string;
  insights: ColumnInsight[];
  generated_at: string;
  error?: string;
}

// GitHub Integration Types
export interface GitHubIssue {
  title: string;
  body: string;
  labels: string[];
  classification: string;
  workflow: string;
  model_set: string;
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

// Routes Types
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

// History Types
export interface TokenBreakdown {
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;
  cache_hit_tokens: number;
  cache_miss_tokens: number;
  total_tokens: number;
}

export interface PhaseCost {
  phase: string;
  cost: number;
  tokens: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_tokens: number;
    cache_read_tokens: number;
  };
}

export interface CostBreakdown {
  estimated_total: number;
  actual_total: number;
  estimated_per_step: number;
  actual_per_step: number;
  cost_per_token: number;
  by_phase?: Record<string, number>;
}

export interface WorkflowHistoryItem {
  // Core fields
  id: number;
  adw_id: string;
  issue_number?: number;
  nl_input?: string;
  github_url?: string;
  workflow_template?: string;
  model_used?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';

  // Time tracking
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  created_at: string;
  updated_at: string;

  // Progress tracking
  error_message?: string;
  phase_count?: number;
  current_phase?: string;
  success_rate?: number;
  retry_count: number;
  steps_completed: number;
  steps_total: number;

  // Resource usage
  worktree_path?: string;
  backend_port?: number;
  frontend_port?: number;
  concurrent_workflows: number;
  worktree_reused: boolean;

  // Token metrics
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;
  cache_hit_tokens: number;
  cache_miss_tokens: number;
  total_tokens: number;
  cache_efficiency_percent: number;

  // Cost metrics
  estimated_cost_total: number;
  actual_cost_total: number;
  estimated_cost_per_step: number;
  actual_cost_per_step: number;
  cost_per_token: number;

  // Structured data (JSON fields)
  structured_input?: Record<string, any>;
  cost_breakdown?: CostBreakdown;
  token_breakdown?: TokenBreakdown;
}

export interface HistoryAnalytics {
  total_workflows: number;
  completed_workflows: number;
  failed_workflows: number;
  avg_duration_seconds: number;
  success_rate_percent: number;
  workflows_by_model: Record<string, number>;
  workflows_by_template: Record<string, number>;
  workflows_by_status: Record<string, number>;
  avg_cost: number;
  total_cost: number;
  avg_tokens: number;
  avg_cache_efficiency: number;
}

export interface HistoryFilters {
  limit?: number;
  offset?: number;
  status?: string;
  model?: string;
  template?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'ASC' | 'DESC';
}

export interface WorkflowHistoryResponse {
  workflows: WorkflowHistoryItem[];
  total_count: number;
  analytics: HistoryAnalytics;
}

// Legacy type for backwards compatibility
export interface HistoryItem {
  id: string;
  nl_input: string;
  project: string;
  issue_number?: number;
  status: string;
  timestamp: string;
  github_url?: string;
}

// Cost tracking types
export interface CostData {
  total_cost: number;
  total_tokens: number;
  cache_efficiency_percent: number;
  cache_savings_amount: number;
  phases: PhaseCost[];
}

export interface CostResponse {
  error?: string;
  cost_data?: CostData;
  // Legacy fields for backwards compatibility
  total_cost?: number;
  cost_by_phase?: Record<string, number>;
  estimated_cost?: number;
  cost_breakdown?: Array<{
    phase: string;
    cost: number;
    tokens_used?: number;
  }>;
}
