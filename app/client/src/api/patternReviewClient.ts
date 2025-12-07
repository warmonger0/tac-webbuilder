/**
 * Pattern Review API Client
 *
 * Client for reviewing and approving automation patterns.
 */

import { API_BASE, fetchJSON } from './baseClient';

// ============================================================================
// Types
// ============================================================================

export interface PatternReview {
  pattern_id: string;
  tool_sequence: string;
  status: 'pending' | 'approved' | 'rejected' | 'auto-approved' | 'auto-rejected';
  confidence_score: number;
  occurrence_count: number;
  estimated_savings_usd: number;
  impact_score: number;
  pattern_context?: string;
  example_sessions?: string[];
  reviewed_by?: string;
  reviewed_at?: string;
  approval_notes?: string;
  created_at?: string;
}

export interface ApproveRequest {
  notes?: string;
}

export interface RejectRequest {
  reason: string;
}

export interface CommentRequest {
  comment: string;
}

export interface ReviewStatistics {
  pending: number;
  approved: number;
  rejected: number;
  auto_approved: number;
  auto_rejected: number;
  total: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get pending patterns for review (ordered by impact score)
 */
export async function getPendingPatterns(limit: number = 20): Promise<PatternReview[]> {
  return fetchJSON<PatternReview[]>(
    `${API_BASE}/patterns/pending?limit=${limit}`,
    { method: 'GET' }
  );
}

/**
 * Get details for a specific pattern
 */
export async function getPatternDetails(patternId: string): Promise<PatternReview> {
  return fetchJSON<PatternReview>(
    `${API_BASE}/patterns/${patternId}`,
    { method: 'GET' }
  );
}

/**
 * Approve a pattern for automation
 */
export async function approvePattern(
  patternId: string,
  request: ApproveRequest
): Promise<PatternReview> {
  return fetchJSON<PatternReview>(
    `${API_BASE}/patterns/${patternId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Reject a pattern from automation
 */
export async function rejectPattern(
  patternId: string,
  request: RejectRequest
): Promise<PatternReview> {
  return fetchJSON<PatternReview>(
    `${API_BASE}/patterns/${patternId}/reject`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Add a comment to a pattern (for further discussion)
 */
export async function addComment(
  patternId: string,
  request: CommentRequest
): Promise<{ status: string; message: string }> {
  return fetchJSON<{ status: string; message: string }>(
    `${API_BASE}/patterns/${patternId}/comment`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Get review statistics
 */
export async function getReviewStatistics(): Promise<ReviewStatistics> {
  return fetchJSON<ReviewStatistics>(
    `${API_BASE}/patterns/statistics`,
    { method: 'GET' }
  );
}

// ============================================================================
// Client namespace export
// ============================================================================

export const patternReviewClient = {
  getPendingPatterns,
  getPatternDetails,
  approvePattern,
  rejectPattern,
  addComment,
  getReviewStatistics,
};
