/**
 * Workflow API client for managing ADW workflow executions and history.
 *
 * This module handles:
 * - Listing active workflows
 * - Fetching workflow history with filtering
 * - Batch operations for efficiency
 * - Cost tracking for workflows
 */

import type {
  CostResponse,
  HistoryFilters,
  HistoryItem,
  WorkflowExecution,
  WorkflowHistoryItem,
  WorkflowHistoryResponse,
} from '../types';
import { API_BASE, fetchJSON } from './baseClient';

/**
 * List all active workflow executions.
 *
 * @returns Array of active workflow executions
 */
export async function listWorkflows(): Promise<WorkflowExecution[]> {
  return fetchJSON<WorkflowExecution[]>(`${API_BASE}/workflows`);
}

/**
 * Get recent workflow history with optional limit.
 *
 * @param limit - Maximum number of history items to return (default: 20)
 * @returns Array of workflow history items
 */
export async function getHistory(limit: number = 20): Promise<HistoryItem[]> {
  return fetchJSON<HistoryItem[]>(`${API_BASE}/history?limit=${limit}`);
}

/**
 * Get workflow history with advanced filtering and pagination.
 *
 * @param filters - Optional filters for status, model, date range, search, etc.
 * @returns Paginated workflow history response with total count
 */
export async function getWorkflowHistory(
  filters?: HistoryFilters
): Promise<WorkflowHistoryResponse> {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.model) params.append('model', filters.model);
    if (filters.template) params.append('template', filters.template);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.search) params.append('search', filters.search);
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
  }
  const url = params.toString()
    ? `${API_BASE}/workflow-history?${params.toString()}`
    : `${API_BASE}/workflow-history`;
  return fetchJSON<WorkflowHistoryResponse>(url);
}

/**
 * Fetch multiple workflows by ADW IDs in a single batch request.
 *
 * This is optimized for fetching similar workflows or related executions.
 * Instead of making N separate requests, this batches them into one.
 *
 * @param workflowIds - Array of ADW IDs to fetch (max 20)
 * @param signal - Optional AbortSignal for request cancellation
 * @returns Array of workflow history items
 * @throws Error if request fails or more than 20 IDs provided
 */
export async function fetchWorkflowsBatch(
  workflowIds: string[],
  signal?: AbortSignal
): Promise<WorkflowHistoryItem[]> {
  const response = await fetch(`${API_BASE}/workflows/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(workflowIds),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch workflows: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch cost information for a specific workflow execution.
 *
 * @param adwId - The ADW ID of the workflow
 * @returns Cost details including tokens used and total cost
 */
export async function fetchWorkflowCosts(
  adwId: string
): Promise<CostResponse> {
  return fetchJSON<CostResponse>(`${API_BASE}/workflows/${adwId}/costs`);
}

/**
 * Workflow client namespace for organized access to all workflow operations.
 */
export const workflowClient = {
  listWorkflows,
  getHistory,
  getWorkflowHistory,
  fetchWorkflowsBatch,
  fetchWorkflowCosts,
};
