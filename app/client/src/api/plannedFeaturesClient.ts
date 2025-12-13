/**
 * Planned Features API Client
 *
 * Client for managing planned features, sessions, and work items.
 */

import { API_BASE, fetchJSON } from './baseClient';

// ============================================================================
// Types
// ============================================================================

export interface PlannedFeature {
  id: number;
  item_type: 'session' | 'feature' | 'bug' | 'enhancement';
  title: string;
  description?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'high' | 'medium' | 'low';
  estimated_hours?: number;
  actual_hours?: number;
  session_number?: number;
  github_issue_number?: number;
  parent_id?: number;
  tags: string[];
  completion_notes?: string;
  created_at?: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PlannedFeatureCreate {
  item_type: string;
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  session_number?: number;
  github_issue_number?: number;
  parent_id?: number;
  tags?: string[];
}

export interface PlannedFeatureUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  estimated_hours?: number;
  actual_hours?: number;
  github_issue_number?: number;
  tags?: string[];
  completion_notes?: string;
}

export interface PlannedFeaturesStats {
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
  total_estimated_hours: number;
  total_actual_hours: number;
  completion_rate: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get all planned features with optional filtering
 */
export async function getAll(params?: {
  status?: string;
  item_type?: string;
  priority?: string;
  limit?: number;
}): Promise<PlannedFeature[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.item_type) queryParams.append('item_type', params.item_type);
  if (params?.priority) queryParams.append('priority', params.priority);
  if (params?.limit) queryParams.append('limit', params.limit.toString());

  const url = queryParams.toString()
    ? `${API_BASE}/planned-features?${queryParams}`
    : `${API_BASE}/planned-features`;

  return fetchJSON<PlannedFeature[]>(url, { method: 'GET' });
}

/**
 * Get single planned feature by ID
 */
export async function getById(id: number): Promise<PlannedFeature> {
  return fetchJSON<PlannedFeature>(
    `${API_BASE}/planned-features/${id}`,
    { method: 'GET' }
  );
}

/**
 * Get statistics about planned features
 */
export async function getStats(): Promise<PlannedFeaturesStats> {
  return fetchJSON<PlannedFeaturesStats>(
    `${API_BASE}/planned-features/stats`,
    { method: 'GET' }
  );
}

/**
 * Get recently completed features
 */
export async function getRecentCompletions(days: number = 30): Promise<PlannedFeature[]> {
  return fetchJSON<PlannedFeature[]>(
    `${API_BASE}/planned-features/recent-completions?days=${days}`,
    { method: 'GET' }
  );
}

/**
 * Create a new planned feature
 */
export async function create(data: PlannedFeatureCreate): Promise<PlannedFeature> {
  return fetchJSON<PlannedFeature>(
    `${API_BASE}/planned-features`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );
}

/**
 * Update an existing planned feature
 */
export async function update(id: number, data: PlannedFeatureUpdate): Promise<PlannedFeature> {
  return fetchJSON<PlannedFeature>(
    `${API_BASE}/planned-features/${id}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    }
  );
}

/**
 * Delete a planned feature (soft delete)
 */
export async function deletePlannedFeature(id: number): Promise<void> {
  return fetchJSON<void>(
    `${API_BASE}/planned-features/${id}`,
    { method: 'DELETE' }
  );
}

/**
 * Start event-driven automation for a planned feature
 *
 * Analyzes the feature, creates phase breakdown, and launches ADWs automatically.
 */
export interface AutomationSummary {
  feature_id: number;
  feature_title: string;
  total_phases: number;
  phases_created: Array<{
    queue_id: string;
    phase_number: number;
    title: string;
    status: string;
    depends_on_phases: number[];
    estimated_hours: number;
  }>;
  ready_phases: number;
  queued_phases: number;
  message: string;
}

export async function startAutomation(id: number): Promise<AutomationSummary> {
  return fetchJSON<AutomationSummary>(
    `${API_BASE}/planned-features/${id}/start-automation`,
    { method: 'POST' }
  );
}

// ============================================================================
// Client namespace export
// ============================================================================

export const plannedFeaturesClient = {
  getAll,
  getById,
  getStats,
  getRecentCompletions,
  create,
  update,
  delete: deletePlannedFeature,
  startAutomation,
};
