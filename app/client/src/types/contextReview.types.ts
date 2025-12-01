/**
 * TypeScript type definitions for context review feature.
 *
 * These types match the backend API models and provide type safety
 * for context analysis operations.
 */

export interface ContextReview {
  id: number;
  workflow_id?: string | null;
  issue_number?: number | null;
  change_description: string;
  project_path: string;
  analysis_timestamp?: string | null;
  analysis_duration_seconds?: number | null;
  agent_cost?: number | null;
  status: 'pending' | 'analyzing' | 'complete' | 'failed';
  result?: ContextReviewResultData | null;
}

export interface ContextSuggestion {
  id: number;
  review_id: number;
  suggestion_type: 'file-to-modify' | 'file-to-create' | 'reference' | 'risk' | 'strategy';
  suggestion_text: string;
  confidence?: number | null;
  priority?: number | null;
  rationale?: string | null;
}

export interface OptimizedContext {
  must_read: string[];
  optional: string[];
  skip: string[];
}

export interface ContextReviewResultData {
  integration_strategy: string;
  files_to_modify: string[];
  files_to_create: string[];
  reference_files: string[];
  risks: string[];
  optimized_context: OptimizedContext;
  estimated_tokens: number;
}

export interface AnalyzeRequest {
  change_description: string;
  project_path: string;
  workflow_id?: string;
  issue_number?: number;
}

export interface AnalyzeResponse {
  review_id: number;
  status: 'pending' | 'analyzing' | 'complete' | 'failed';
}

export interface ReviewResponse {
  review: ContextReview;
  suggestions: ContextSuggestion[];
}

export interface SuggestionsResponse {
  suggestions: ContextSuggestion[];
}

export interface CacheLookupRequest {
  change_description: string;
  project_path: string;
}

export interface CacheLookupResponse {
  cached: boolean;
  review_id?: number;
  result?: ContextReviewResultData;
}

export interface TokenSavings {
  before_tokens: number;
  after_tokens: number;
  savings_tokens: number;
  savings_percent: number;
  files_must_read: number;
  files_optional: number;
  files_skip: number;
}
