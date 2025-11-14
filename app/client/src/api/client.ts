/// <reference path="../types.d.ts" />

import type {
  GitHubIssue,
  Workflow,
  SubmitRequestData,
  SubmitRequestResponse,
  ConfirmResponse,
  RoutesResponse,
  CostResponse,
  WorkflowHistoryResponse,
  WorkflowHistoryFilter,
} from '../types';

const API_BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} ${error}`);
  }

  return response.json();
}

export async function submitRequest(
  data: SubmitRequestData
): Promise<SubmitRequestResponse> {
  return fetchJSON<SubmitRequestResponse>(`${API_BASE}/request`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getPreview(request_id: string): Promise<GitHubIssue> {
  return fetchJSON<GitHubIssue>(`${API_BASE}/preview/${request_id}`);
}

export async function confirmAndPost(
  request_id: string
): Promise<ConfirmResponse> {
  return fetchJSON<ConfirmResponse>(`${API_BASE}/confirm/${request_id}`, {
    method: 'POST',
  });
}

export async function listWorkflows(): Promise<Workflow[]> {
  return fetchJSON<Workflow[]>(`${API_BASE}/workflows`);
}

export async function getHistory(filters: WorkflowHistoryFilter): Promise<WorkflowHistoryResponse> {
  // Build query string from filters
  const params = new URLSearchParams();

  if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters.offset !== undefined) params.append('offset', filters.offset.toString());
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.order) params.append('order', filters.order);
  if (filters.filter_status) params.append('filter_status', filters.filter_status);
  if (filters.filter_template) params.append('filter_template', filters.filter_template);
  if (filters.filter_model) params.append('filter_model', filters.filter_model);
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  if (filters.search_query) params.append('search_query', filters.search_query);

  const queryString = params.toString();
  const url = queryString ? `${API_BASE}/history?${queryString}` : `${API_BASE}/history`;

  return fetchJSON<WorkflowHistoryResponse>(url);
}

export async function getRoutes(): Promise<RoutesResponse> {
  return fetchJSON<RoutesResponse>(`${API_BASE}/routes`);
}

export async function fetchWorkflowCosts(adwId: string): Promise<CostResponse> {
  return fetchJSON<CostResponse>(`${API_BASE}/workflows/${adwId}/costs`);
}

// Database query API functions (placeholder implementations)
export async function processQuery(request: QueryRequest): Promise<QueryResponse> {
  return fetchJSON<QueryResponse>(`${API_BASE}/query`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function generateRandomQuery(): Promise<RandomQueryResponse> {
  return fetchJSON<RandomQueryResponse>(`${API_BASE}/random-query`);
}

export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} ${error}`);
  }

  return response.json();
}

export async function getSchema(): Promise<DatabaseSchemaResponse> {
  return fetchJSON<DatabaseSchemaResponse>(`${API_BASE}/schema`);
}

export async function exportQueryResults(results: Record<string, any>[], columns: string[]): Promise<void> {
  // Client-side CSV export
  const csv = [
    columns.join(','),
    ...results.map(row => columns.map(col => JSON.stringify(row[col] ?? '')).join(','))
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'query-results.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportTable(tableName: string): Promise<void> {
  const response = await fetch(`${API_BASE}/export/${tableName}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} ${error}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${tableName}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
