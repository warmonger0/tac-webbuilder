/**
 * Queue and ADW Monitor API client for managing phase queues and monitoring ADW workflows.
 *
 * This module handles:
 * - Phase queue operations (list, execute, dequeue)
 * - Queue configuration (pause/resume)
 * - ADW workflow monitoring and health checks
 */

import { API_BASE, apiDelete, apiPost, fetchJSON } from './baseClient';

// ============================================================================
// Phase Queue Types
// ============================================================================

export interface PhaseQueueItem {
  queue_id: string;
  parent_issue: number;
  phase_number: number;
  issue_number?: number;
  status: 'queued' | 'ready' | 'running' | 'completed' | 'blocked' | 'failed';
  depends_on_phase?: number;
  phase_data: {
    title: string;
    content: string;
    externalDocs?: string[];
  };
  created_at: string;
  updated_at: string;
  error_message?: string;
  adw_id?: string;
  pr_number?: number;
}

export interface QueueListResponse {
  phases: PhaseQueueItem[];
  total: number;
}

export interface QueueConfigResponse {
  paused: boolean;
}

export interface ExecutePhaseResponse {
  success: boolean;
  message: string;
  issue_number?: number;
  adw_id?: string;
}

// ============================================================================
// ADW Monitor Types
// ============================================================================

export interface AdwWorkflowStatus {
  adw_id: string;
  issue_number: number | null;
  pr_number: number | null;
  issue_class: string;
  title: string;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'queued';
  current_phase: string | null;
  phase_progress: number;
  workflow_template: string;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  github_url: string | null;
  worktree_path: string | null;
  current_cost: number | null;
  estimated_cost_total: number | null;
  error_count: number;
  last_error: string | null;
  is_process_active: boolean;
  phases_completed: string[];
  total_phases: number;
}

export interface AdwMonitorSummary {
  total: number;
  running: number;
  completed: number;
  failed: number;
  paused: number;
}

export interface AdwMonitorResponse {
  summary: AdwMonitorSummary;
  workflows: AdwWorkflowStatus[];
  last_updated: string;
}

// ============================================================================
// ADW Health Check Types
// ============================================================================

export interface PortHealthCheck {
  status: 'ok' | 'warning' | 'critical';
  backend_port: number | null;
  frontend_port: number | null;
  available: boolean;
  in_use: boolean;
  conflicts: any[];
  warnings: string[];
}

export interface WorktreeHealthCheck {
  status: 'ok' | 'warning' | 'critical';
  path: string | null;
  exists: boolean;
  clean: boolean;
  uncommitted_files: string[];
  git_registered: boolean;
  warnings: string[];
}

export interface StateFileHealthCheck {
  status: 'ok' | 'warning' | 'critical';
  path: string;
  exists: boolean;
  valid: boolean;
  last_modified: string | null;
  age_seconds: number | null;
  warnings: string[];
}

export interface ProcessHealthCheck {
  status: 'ok' | 'warning' | 'critical';
  active: boolean;
  processes: any[];
  warnings: string[];
}

export interface AdwHealthCheckResponse {
  adw_id: string;
  overall_health: 'ok' | 'warning' | 'critical';
  checks: {
    ports: PortHealthCheck;
    worktree: WorktreeHealthCheck;
    state_file: StateFileHealthCheck;
    process: ProcessHealthCheck;
  };
  warnings: string[];
  checked_at: string;
}

// ============================================================================
// Phase Queue API Functions
// ============================================================================

/**
 * Get all queue items across all parents.
 *
 * @returns List of all queue items with total count
 */
export async function getQueueAll(): Promise<QueueListResponse> {
  return fetchJSON<QueueListResponse>(`${API_BASE}/queue`);
}

/**
 * Get queue items for a specific parent issue.
 *
 * @param parentIssue - The parent issue number
 * @returns List of queue items for the parent
 */
export async function getQueueByParent(
  parentIssue: number
): Promise<QueueListResponse> {
  return fetchJSON<QueueListResponse>(`${API_BASE}/queue/${parentIssue}`);
}

/**
 * Get queue configuration (paused state, etc.).
 *
 * @returns Current queue configuration
 */
export async function getQueueConfig(): Promise<QueueConfigResponse> {
  return fetchJSON<QueueConfigResponse>(`${API_BASE}/queue/config`);
}

/**
 * Get full queue data including phases and configuration (for WebSocket fallback).
 * Combines getQueueAll and getQueueConfig into a single call.
 *
 * @returns Queue data with phases, total count, and paused state
 */
export async function getQueueData(): Promise<{ phases: PhaseQueueItem[]; total: number; paused: boolean }> {
  const [queueData, configData] = await Promise.all([
    getQueueAll(),
    getQueueConfig()
  ]);
  return {
    phases: queueData.phases,
    total: queueData.total,
    paused: configData.paused
  };
}

/**
 * Set queue paused state.
 *
 * @param paused - True to pause queue, false to resume
 * @returns Updated queue configuration
 */
export async function setQueuePaused(
  paused: boolean
): Promise<QueueConfigResponse> {
  return apiPost<QueueConfigResponse>(`${API_BASE}/queue/config/pause`, {
    paused,
  });
}

/**
 * Remove a phase from the queue.
 *
 * @param queueId - The queue item ID to remove
 * @returns Success response
 */
export async function dequeuePhase(
  queueId: string
): Promise<{ success: boolean; message: string }> {
  return apiDelete<{ success: boolean; message: string }>(
    `${API_BASE}/queue/${queueId}`
  );
}

/**
 * Execute a queued phase immediately.
 *
 * @param queueId - The queue item ID to execute
 * @returns Execution response with issue number and ADW ID
 */
export async function executePhase(
  queueId: string
): Promise<ExecutePhaseResponse> {
  return apiPost<ExecutePhaseResponse>(
    `${API_BASE}/queue/${queueId}/execute`
  );
}

/**
 * Resume a paused ADW workflow after running preflight checks.
 *
 * @param adwId - The ADW ID to resume
 * @returns Success response with workflow details
 */
export async function resumeAdw(
  adwId: string
): Promise<{
  success: boolean;
  message: string;
  adw_id: string;
  issue_number: string;
  workflow: string;
  preflight_checks: {
    passed: boolean;
    duration_ms: number;
  };
}> {
  return apiPost<{
    success: boolean;
    message: string;
    adw_id: string;
    issue_number: string;
    workflow: string;
    preflight_checks: {
      passed: boolean;
      duration_ms: number;
    };
  }>(`${API_BASE}/queue/resume/${adwId}`);
}

// ============================================================================
// ADW Monitor API Functions
// ============================================================================

/**
 * Get ADW monitor dashboard with all active workflows.
 *
 * @returns Monitor summary and list of all workflows
 */
export async function getAdwMonitor(): Promise<AdwMonitorResponse> {
  return fetchJSON<AdwMonitorResponse>(`${API_BASE}/adw-monitor`);
}

/**
 * Get detailed health check for a specific ADW workflow.
 *
 * @param adwId - The ADW ID to check
 * @returns Health check results for ports, worktree, state file, and process
 */
export async function getAdwHealth(
  adwId: string
): Promise<AdwHealthCheckResponse> {
  return fetchJSON<AdwHealthCheckResponse>(
    `${API_BASE}/adw-monitor/${adwId}/health`
  );
}

/**
 * Queue client namespace for organized access to all queue and ADW operations.
 */
export const queueClient = {
  // Phase Queue operations
  getQueueAll,
  getQueueByParent,
  getQueueConfig,
  setQueuePaused,
  dequeuePhase,
  executePhase,
  resumeAdw,
  // ADW Monitor operations
  getAdwMonitor,
  getAdwHealth,
};
