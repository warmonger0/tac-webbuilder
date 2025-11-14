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
  WorkflowHistorySummary,
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

export async function getHistory(limit: number = 20): Promise<HistoryItem[]> {
  return fetchJSON<HistoryItem[]>(`${API_BASE}/history?limit=${limit}`);
}

export async function getRoutes(): Promise<RoutesResponse> {
  return fetchJSON<RoutesResponse>(`${API_BASE}/routes`);
}

export async function fetchWorkflowCosts(adwId: string): Promise<CostResponse> {
  return fetchJSON<CostResponse>(`${API_BASE}/workflows/${adwId}/costs`);
}

export async function getWorkflowHistory(
  filters?: Partial<WorkflowHistoryFilter>
): Promise<WorkflowHistoryResponse> {
  const params = new URLSearchParams();

  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.order) params.append('order', filters.order);
  if (filters?.model_filter) params.append('model_filter', filters.model_filter);
  if (filters?.template_filter) params.append('template_filter', filters.template_filter);
  if (filters?.status_filter) params.append('status_filter', filters.status_filter);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.search_query) params.append('search_query', filters.search_query);
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters?.offset !== undefined) params.append('offset', filters.offset.toString());

  const queryString = params.toString();
  const url = queryString
    ? `${API_BASE}/workflow-history?${queryString}`
    : `${API_BASE}/workflow-history`;

  return fetchJSON<WorkflowHistoryResponse>(url);
}

export async function getWorkflowHistorySummary(): Promise<WorkflowHistorySummary> {
  return fetchJSON<WorkflowHistorySummary>(`${API_BASE}/workflow-history/summary`);
}
