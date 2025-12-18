/**
 * System API client for managing system status, routes, and services.
 *
 * This module handles:
 * - System status and health checks
 * - API route discovery
 * - Webhook service management
 * - Cloudflare tunnel management
 * - GitHub webhook operations
 */

import type { RoutesResponse } from '../types';
import { API_BASE, fetchJSON } from './baseClient';
import { apiConfig } from '../config/api';

/**
 * Get list of available API routes.
 *
 * @returns Available routes and their documentation
 */
export async function getRoutes(): Promise<RoutesResponse> {
  return fetchJSON<RoutesResponse>(`${API_BASE}/routes`);
}

/**
 * Get webhook service status.
 *
 * NOTE: This endpoint is only used as HTTP fallback for the WebSocket connection.
 * The primary webhook status data comes from the WebSocket at /api/v1/ws/webhook-status.
 * This HTTP endpoint is intentionally NOT IMPLEMENTED in the backend because:
 * 1. Webhook service (port 8001) doesn't have CORS configured (security by design)
 * 2. WebSocket provides real-time updates without polling
 * 3. Backend fetches from port 8001 internally and broadcasts via WebSocket
 *
 * @returns Empty object (WebSocket should be used instead)
 */
export async function getWebhookStatus(): Promise<any> {
  // Return empty object - webhook status comes from WebSocket only
  // This function exists for API compatibility but should not be called
  console.warn('[API] getWebhookStatus called - webhook status should come from WebSocket');
  return { status: 'unknown', message: 'Use WebSocket for webhook status' };
}

/**
 * Get overall system status including all services.
 *
 * @returns System status with health of all components
 */
export async function getSystemStatus(): Promise<any> {
  return fetchJSON<any>(`${API_BASE}/system-status`);
}

export interface PreflightCheckResult {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  duration_ms: number;
  details?: string | number;
}

export interface PreflightBlockingFailure {
  check: string;
  error: string;
  fix: string;
  failing_tests?: string[];
}

export interface PreflightWarning {
  check: string;
  message: string;
  impact: string;
  evidence?: string[];
  recommendation?: string;
}

export interface IssueValidation {
  is_resolved: boolean;
  confidence: number;
  message: string;
  summary: string;
  evidence: string[];
  recommendation: string;
  closed_at: string | null;
  related_commits: string[];
  duplicate_of: number[];
}

export interface DryRunPhase {
  phase_number: number;
  title: string;
  description: string;
  estimated_cost: string;
  estimated_time: string;
  estimated_tokens: number;
  files_to_modify: string[];
  risk_level: 'low' | 'medium' | 'high';
  depends_on: number[];
}

export interface DryRunSummary {
  total_phases: number;
  total_cost: string;
  total_time: string;
  total_tokens: number;
  high_risk_phases: number;
  approval_recommended: boolean;
}

export interface DryRunResult {
  feature_id: number;
  feature_title: string;
  phases: DryRunPhase[];
  summary: DryRunSummary;
  pattern_info: {
    matched: boolean;
    source: string | null;
  };
}

export interface PreflightChecksResponse {
  passed: boolean;
  blocking_failures: PreflightBlockingFailure[];
  warnings: PreflightWarning[];
  checks_run: PreflightCheckResult[];
  total_duration_ms: number;
  issue_validation?: IssueValidation;
  dry_run?: DryRunResult;
}

/**
 * Run pre-flight health checks before launching workflows.
 *
 * Checks for:
 * - Uncommitted git changes (blocking)
 * - Worktree availability (blocking)
 * - Critical test failures (blocking)
 * - Port availability (warning)
 * - Disk space (warning)
 * - Python environment (blocking)
 * - Observability database (blocking)
 * - Hook events recording (warning)
 * - Pattern analysis system (warning)
 * - Issue already resolved (warning, if issue_number provided)
 *
 * @param params - Configuration options
 * @param params.skipTests - Skip the test suite check for faster checks
 * @param params.issueNumber - GitHub issue number to check for duplicate work
 * @returns Pre-flight check results with blocking failures and warnings
 */
export async function getPreflightChecks(params?: {
  skipTests?: boolean;
  issueNumber?: number;
  runDryRun?: boolean;
  featureId?: number;
  featureTitle?: string;
}): Promise<PreflightChecksResponse> {
  const queryParams = new URLSearchParams();
  if (params?.skipTests) queryParams.append('skip_tests', 'true');
  if (params?.issueNumber) queryParams.append('issue_number', params.issueNumber.toString());
  if (params?.runDryRun) queryParams.append('run_dry_run', 'true');
  if (params?.featureId) queryParams.append('feature_id', params.featureId.toString());
  if (params?.featureTitle) queryParams.append('feature_title', params.featureTitle);

  const url = queryParams.toString()
    ? `${API_BASE}/preflight-checks?${queryParams}`
    : `${API_BASE}/preflight-checks`;

  return fetchJSON<PreflightChecksResponse>(url);
}

/**
 * Start the webhook service.
 *
 * @returns Service start response
 * @throws Error if service fails to start
 */
export async function startWebhookService(): Promise<any> {
  const response = await fetch(`${API_BASE}/services/webhook/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to start webhook service: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Restart the Cloudflare tunnel service.
 *
 * @returns Service restart response
 * @throws Error if service fails to restart
 */
export async function restartCloudflare(): Promise<any> {
  const response = await fetch(`${API_BASE}/services/cloudflare/restart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to restart Cloudflare: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get GitHub webhook health status.
 *
 * @returns GitHub webhook health information
 */
export async function getGitHubWebhookHealth(): Promise<any> {
  return fetchJSON<any>(`${API_BASE}/services/github-webhook/health`);
}

/**
 * Manually trigger redelivery of GitHub webhook.
 *
 * @returns Redelivery response
 * @throws Error if redelivery fails
 */
export async function redeliverGitHubWebhook(): Promise<any> {
  const response = await fetch(
    `${API_BASE}/services/github-webhook/redeliver`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to redeliver webhook: ${response.statusText}`);
  }
  return response.json();
}

/**
 * System client namespace for organized access to all system operations.
 */
export const systemClient = {
  getRoutes,
  getWebhookStatus,
  getSystemStatus,
  getPreflightChecks,
  startWebhookService,
  restartCloudflare,
  getGitHubWebhookHealth,
  redeliverGitHubWebhook,
};
