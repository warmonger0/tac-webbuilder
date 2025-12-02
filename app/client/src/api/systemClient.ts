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
 *
 * @param skipTests - Skip the test suite check for faster checks
 * @returns Pre-flight check results with blocking failures and warnings
 */
export async function getPreflightChecks(skipTests: boolean = false): Promise<{
  passed: boolean;
  blocking_failures: Array<{ check: string; error: string; fix: string; failing_tests?: string[] }>;
  warnings: Array<{ check: string; message: string; impact: string }>;
  checks_run: Array<{ check: string; status: string; duration_ms: number; details?: string }>;
  total_duration_ms: number;
}> {
  return fetchJSON<any>(`${API_BASE}/preflight-checks?skip_tests=${skipTests}`);
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
