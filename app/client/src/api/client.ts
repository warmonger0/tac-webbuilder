import type {
  GitHubIssue,
  WorkflowExecution,
  HistoryItem,
  SubmitRequestData,
  SubmitRequestResponse,
  ConfirmResponse,
  RoutesResponse,
  CostResponse,
  QueryRequest,
  QueryResponse,
  FileUploadResponse,
  DatabaseSchemaResponse,
  RandomQueryResponse,
  WorkflowHistoryResponse,
  HistoryFilters,
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

export async function listWorkflows(): Promise<WorkflowExecution[]> {
  return fetchJSON<WorkflowExecution[]>(`${API_BASE}/workflows`);
}

export async function getHistory(limit: number = 20): Promise<HistoryItem[]> {
  return fetchJSON<HistoryItem[]>(`${API_BASE}/history?limit=${limit}`);
}

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

export async function getRoutes(): Promise<RoutesResponse> {
  return fetchJSON<RoutesResponse>(`${API_BASE}/routes`);
}

export async function fetchWorkflowCosts(adwId: string): Promise<CostResponse> {
  return fetchJSON<CostResponse>(`${API_BASE}/workflows/${adwId}/costs`);
}

export async function processQuery(data: QueryRequest): Promise<QueryResponse> {
  return fetchJSON<QueryResponse>(`${API_BASE}/query`, {
    method: 'POST',
    body: JSON.stringify(data),
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
  // Convert results to CSV
  const csv = [
    columns.join(','),
    ...results.map(row => columns.map(col => {
      const value = row[col];
      // Escape values that contain commas or quotes
      if (value === null || value === undefined) return '';
      const stringValue = String(value);
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    }).join(','))
  ].join('\n');

  // Download file
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `query-results-${new Date().toISOString()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function exportTable(tableName: string): Promise<void> {
  const response = await fetch(`${API_BASE}/export/${tableName}`);

  if (!response.ok) {
    throw new Error('Failed to export table');
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${tableName}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function getWebhookStatus(): Promise<any> {
  // Try to fetch from webhook service directly
  try {
    const response = await fetch('http://localhost:8001/webhook-status');
    if (response.ok) {
      return response.json();
    }
  } catch (err) {
    // Fallback to backend proxy if direct access fails
  }

  // Fallback to backend API proxy
  return fetchJSON<any>(`${API_BASE}/webhook-status`);
}

export async function getSystemStatus(): Promise<any> {
  return fetchJSON<any>(`${API_BASE}/system-status`);
}

// Export as namespace object for compatibility with existing code
export const api = {
  submitRequest,
  getPreview,
  confirmAndPost,
  listWorkflows,
  getHistory,
  getWorkflowHistory,
  getRoutes,
  fetchWorkflowCosts,
  processQuery,
  generateRandomQuery,
  uploadFile,
  getSchema,
  exportQueryResults,
  exportTable,
  getWebhookStatus,
  getSystemStatus,
};
