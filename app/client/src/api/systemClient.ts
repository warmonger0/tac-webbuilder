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
 * Attempts to fetch directly from webhook service first (port 8001),
 * then falls back to backend proxy if direct access fails.
 *
 * @returns Webhook service status
 */
export async function getWebhookStatus(): Promise<any> {
  // Try to fetch from webhook service directly
  try {
    const response = await fetch(`${apiConfig.webhookServiceUrl}/webhook-status`);
    if (response.ok) {
      return response.json();
    }
  } catch {
    // Fallback to backend proxy if direct access fails
  }

  // Fallback to backend API proxy
  return fetchJSON<any>(`${API_BASE}/webhook-status`);
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

export interface PreflightChecksResponse {
  passed: boolean;
  blocking_failures: PreflightBlockingFailure[];
  warnings: PreflightWarning[];
  checks_run: PreflightCheckResult[];
  total_duration_ms: number;
  issue_validation?: IssueValidation;
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
}): Promise<PreflightChecksResponse> {
  const queryParams = new URLSearchParams();
  if (params?.skipTests) queryParams.append('skip_tests', 'true');
  if (params?.issueNumber) queryParams.append('issue_number', params.issueNumber.toString());

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
