/**
 * GitHub API client for managing issue requests and GitHub integrations.
 *
 * This module handles the workflow of:
 * 1. Submitting natural language requests
 * 2. Previewing generated GitHub issues
 * 3. Estimating costs
 * 4. Confirming and posting issues to GitHub
 */

import type {
  ConfirmResponse,
  CostEstimate,
  GitHubIssue,
  SubmitRequestData,
  SubmitRequestResponse,
} from '../types';
import { API_BASE, apiPost, fetchJSON } from './baseClient';

/**
 * Submit a natural language request to generate a GitHub issue.
 *
 * @param data - The request data including natural language description
 * @returns Response with request ID and processing status
 */
export async function submitRequest(
  data: SubmitRequestData
): Promise<SubmitRequestResponse> {
  return fetchJSON<SubmitRequestResponse>(`${API_BASE}/request`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get a preview of the generated GitHub issue.
 *
 * @param request_id - The request ID from submitRequest
 * @returns Preview of the GitHub issue structure
 */
export async function getPreview(request_id: string): Promise<GitHubIssue> {
  return fetchJSON<GitHubIssue>(`${API_BASE}/preview/${request_id}`);
}

/**
 * Get cost estimate for executing the generated issue.
 *
 * @param request_id - The request ID from submitRequest
 * @returns Cost estimate including model and token usage
 */
export async function getCostEstimate(
  request_id: string
): Promise<CostEstimate> {
  return fetchJSON<CostEstimate>(`${API_BASE}/preview/${request_id}/cost`);
}

/**
 * Confirm and post the GitHub issue.
 *
 * @param request_id - The request ID from submitRequest
 * @returns Confirmation with GitHub issue number and URL
 */
export async function confirmAndPost(
  request_id: string
): Promise<ConfirmResponse> {
  return apiPost<ConfirmResponse>(`${API_BASE}/confirm/${request_id}`);
}

/**
 * GitHub client namespace for organized access to all GitHub operations.
 */
export const githubClient = {
  submitRequest,
  getPreview,
  getCostEstimate,
  confirmAndPost,
};
