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
export interface HistoryItem {
  id: string;
  nl_input: string;
  project: string;
  issue_number?: number;
  status: string;
  timestamp: string;
  github_url?: string;
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
}

// Cost tracking types
export interface CostResponse {
  total_cost: number;
  cost_by_phase?: Record<string, number>;
  estimated_cost?: number;
  cost_breakdown?: Array<{
    phase: string;
    cost: number;
    tokens_used?: number;
  }>;
}
