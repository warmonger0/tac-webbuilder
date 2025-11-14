import type {
  GitHubIssue,
  Workflow,
  HistoryItem,
  SubmitRequestData,
  SubmitRequestResponse,
  ConfirmResponse,
  RoutesResponse,
  CostResponse,
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

export async function listWorkflows(): Promise<Workflow[]> {
  return fetchJSON<Workflow[]>(`${API_BASE}/workflows`);
}

export async function getHistory(limit: number = 20): Promise<HistoryItem[]> {
  return fetchJSON<HistoryItem[]>(`${API_BASE}/history?limit=${limit}`);
}

export async function getWorkflowHistory(
  filters?: HistoryFilters
): Promise<WorkflowHistoryResponse> {
  const params = new URLSearchParams();

  if (filters) {
    if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters.offset !== undefined) params.append('offset', filters.offset.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.model) params.append('model', filters.model);
    if (filters.template) params.append('template', filters.template);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.search) params.append('search', filters.search);
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
  }

  const queryString = params.toString();
  const url = `${API_BASE}/history${queryString ? `?${queryString}` : ''}`;

  return fetchJSON<WorkflowHistoryResponse>(url);
}

export async function getRoutes(): Promise<RoutesResponse> {
  return fetchJSON<RoutesResponse>(`${API_BASE}/routes`);
}

export async function fetchWorkflowCosts(adwId: string): Promise<CostResponse> {
  return fetchJSON<CostResponse>(`${API_BASE}/workflows/${adwId}/costs`);
}
