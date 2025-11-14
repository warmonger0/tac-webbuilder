import type {
  GitHubIssue,
  Workflow,
  HistoryItem,
  SubmitRequestData,
  SubmitRequestResponse,
  ConfirmResponse,
  RoutesResponse,
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
