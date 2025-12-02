/**
 * Observability API Client
 *
 * Client for task logs and user prompts (observability data).
 */

import { API_BASE, fetchJSON } from './baseClient';

// ============================================================================
// Types - Task Logs
// ============================================================================

export interface TaskLog {
  id: number | null;
  adw_id: string;
  issue_number: number;
  workflow_template: string | null;
  phase_name: string;
  phase_number: number | null;
  phase_status: 'started' | 'completed' | 'failed' | 'skipped';
  log_message: string;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  tokens_used: number | null;
  cost_usd: number | null;
  captured_at: string;
  created_at: string;
}

export interface TaskLogCreate {
  adw_id: string;
  issue_number: number;
  workflow_template?: string;
  phase_name: string;
  phase_number?: number;
  phase_status: 'started' | 'completed' | 'failed' | 'skipped';
  log_message: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  tokens_used?: number;
  cost_usd?: number;
}

export interface IssueProgress {
  issue_number: number;
  adw_id: string;
  workflow_template: string | null;
  total_phases: number;
  completed_phases: number;
  failed_phases: number;
  latest_phase: number | null;
  last_activity: string | null;
}

// ============================================================================
// Types - User Prompts
// ============================================================================

export interface UserPrompt {
  id: number | null;
  request_id: string;
  session_id: string | null;
  nl_input: string;
  project_path: string | null;
  auto_post: boolean;
  issue_title: string | null;
  issue_body: string | null;
  issue_type: string | null;
  complexity: string | null;
  is_multi_phase: boolean;
  phase_count: number;
  parent_issue_number: number | null;
  estimated_cost_usd: number | null;
  estimated_tokens: number | null;
  model_name: string | null;
  github_issue_number: number | null;
  github_issue_url: string | null;
  posted_at: string | null;
  created_at: string;
  captured_at: string;
}

export interface UserPromptWithProgress extends UserPrompt {
  total_phases: number | null;
  completed_phases: number | null;
  failed_phases: number | null;
  latest_phase: number | null;
  last_activity: string | null;
}

// ============================================================================
// API Functions - Task Logs
// ============================================================================

/**
 * Get all task logs with pagination and filtering
 */
export async function getTaskLogs(params?: {
  issue_number?: number;
  adw_id?: string;
  phase_name?: string;
  phase_status?: string;
  limit?: number;
  offset?: number;
}): Promise<TaskLog[]> {
  const query = new URLSearchParams();
  if (params?.issue_number) query.append('issue_number', params.issue_number.toString());
  if (params?.adw_id) query.append('adw_id', params.adw_id);
  if (params?.phase_name) query.append('phase_name', params.phase_name);
  if (params?.phase_status) query.append('phase_status', params.phase_status);
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const url = `${API_BASE}/observability/task-logs${query.toString() ? '?' + query.toString() : ''}`;
  return fetchJSON<TaskLog[]>(url, { method: 'GET' });
}

/**
 * Get task logs for a specific issue
 */
export async function getTaskLogsByIssue(issueNumber: number): Promise<TaskLog[]> {
  return fetchJSON<TaskLog[]>(
    `${API_BASE}/observability/task-logs/issue/${issueNumber}`,
    { method: 'GET' }
  );
}

/**
 * Get task logs for a specific ADW
 */
export async function getTaskLogsByAdw(adwId: string): Promise<TaskLog[]> {
  return fetchJSON<TaskLog[]>(
    `${API_BASE}/observability/task-logs/adw/${adwId}`,
    { method: 'GET' }
  );
}

/**
 * Get progress for a specific issue
 */
export async function getIssueProgress(issueNumber: number): Promise<IssueProgress | null> {
  return fetchJSON<IssueProgress | null>(
    `${API_BASE}/observability/issue-progress/${issueNumber}`,
    { method: 'GET' }
  );
}

/**
 * Create a new task log entry
 */
export async function createTaskLog(log: TaskLogCreate): Promise<TaskLog> {
  return fetchJSON<TaskLog>(`${API_BASE}/observability/task-logs`, {
    method: 'POST',
    body: JSON.stringify(log),
  });
}

// ============================================================================
// API Functions - User Prompts
// ============================================================================

/**
 * Get all user prompts with pagination and filtering
 */
export async function getUserPrompts(params?: {
  session_id?: string;
  issue_number?: number;
  issue_type?: string;
  is_multi_phase?: boolean;
  limit?: number;
  offset?: number;
}): Promise<UserPrompt[]> {
  const query = new URLSearchParams();
  if (params?.session_id) query.append('session_id', params.session_id);
  if (params?.issue_number) query.append('issue_number', params.issue_number.toString());
  if (params?.issue_type) query.append('issue_type', params.issue_type);
  if (params?.is_multi_phase !== undefined) query.append('is_multi_phase', params.is_multi_phase.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const url = `${API_BASE}/observability/user-prompts${query.toString() ? '?' + query.toString() : ''}`;
  return fetchJSON<UserPrompt[]>(url, { method: 'GET' });
}

/**
 * Get user prompts for a specific issue
 */
export async function getUserPromptsByIssue(issueNumber: number): Promise<UserPrompt[]> {
  return fetchJSON<UserPrompt[]>(
    `${API_BASE}/observability/user-prompts/issue/${issueNumber}`,
    { method: 'GET' }
  );
}

/**
 * Get user prompts with progress information
 */
export async function getUserPromptsWithProgress(params?: {
  limit?: number;
  offset?: number;
}): Promise<UserPromptWithProgress[]> {
  const query = new URLSearchParams();
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const url = `${API_BASE}/observability/user-prompts/with-progress${query.toString() ? '?' + query.toString() : ''}`;
  return fetchJSON<UserPromptWithProgress[]>(url, { method: 'GET' });
}

// ============================================================================
// Client namespace export
// ============================================================================

export const observabilityClient = {
  // Task Logs
  getTaskLogs,
  getTaskLogsByIssue,
  getTaskLogsByAdw,
  getIssueProgress,
  createTaskLog,

  // User Prompts
  getUserPrompts,
  getUserPromptsByIssue,
  getUserPromptsWithProgress,
};
