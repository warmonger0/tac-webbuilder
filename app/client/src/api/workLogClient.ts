/**
 * Work Log API Client
 *
 * Client for managing work log entries (chat session summaries).
 */

import { API_BASE, fetchJSON } from './baseClient';

// ============================================================================
// Types
// ============================================================================

export interface WorkLogEntry {
  id: number;
  timestamp: string;
  session_id: string;
  summary: string;
  chat_file_link?: string;
  issue_number?: number;
  workflow_id?: string;
  tags: string[];
  created_at: string;
}

export interface WorkLogEntryCreate {
  session_id: string;
  summary: string;
  chat_file_link?: string;
  issue_number?: number;
  workflow_id?: string;
  tags?: string[];
}

export interface WorkLogListResponse {
  entries: WorkLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get all work log entries with pagination
 */
export async function getWorkLogs(
  limit: number = 50,
  offset: number = 0
): Promise<WorkLogListResponse> {
  return fetchJSON<WorkLogListResponse>(
    `${API_BASE}/work-log?limit=${limit}&offset=${offset}`,
    { method: 'GET' }
  );
}

/**
 * Get work log entries for a specific session
 */
export async function getSessionWorkLogs(sessionId: string): Promise<WorkLogEntry[]> {
  return fetchJSON<WorkLogEntry[]>(
    `${API_BASE}/work-log/session/${sessionId}`,
    { method: 'GET' }
  );
}

/**
 * Create a new work log entry
 */
export async function createWorkLog(entry: WorkLogEntryCreate): Promise<WorkLogEntry> {
  return fetchJSON<WorkLogEntry>(`${API_BASE}/work-log`, {
    method: 'POST',
    body: JSON.stringify(entry),
  });
}

/**
 * Delete a work log entry
 */
export async function deleteWorkLog(entryId: number): Promise<void> {
  await fetch(`${API_BASE}/work-log/${entryId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Client namespace export
// ============================================================================

export const workLogClient = {
  getWorkLogs,
  getSessionWorkLogs,
  createWorkLog,
  deleteWorkLog,
};
