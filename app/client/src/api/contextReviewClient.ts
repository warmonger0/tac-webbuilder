/**
 * API client for context review operations.
 *
 * Provides functions for:
 * - Starting context analysis
 * - Fetching analysis results
 * - Checking cache
 * - Getting suggestions
 */

import type {
  AnalyzeRequest,
  AnalyzeResponse,
  CacheLookupRequest,
  CacheLookupResponse,
  ReviewResponse,
  SuggestionsResponse,
} from '@/types';
import { fetchJSON } from './baseClient';

export const contextReviewClient = {
  /**
   * Start a new context analysis.
   *
   * @param request - Analysis request data
   * @returns Promise resolving to analysis response with review_id
   */
  async startAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    return fetchJSON<AnalyzeResponse>('/context-review/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Get context review result by ID.
   *
   * @param reviewId - Review ID to fetch
   * @returns Promise resolving to review with suggestions
   */
  async getReviewResult(reviewId: number): Promise<ReviewResponse> {
    return fetchJSON<ReviewResponse>(`/context-review/${reviewId}`);
  },

  /**
   * Get suggestions for a review.
   *
   * @param reviewId - Review ID
   * @returns Promise resolving to suggestions list
   */
  async getSuggestions(reviewId: number): Promise<SuggestionsResponse> {
    return fetchJSON<SuggestionsResponse>(`/context-review/${reviewId}/suggestions`);
  },

  /**
   * Check if analysis is cached.
   *
   * @param request - Cache lookup request
   * @returns Promise resolving to cache status and result if cached
   */
  async checkCache(request: CacheLookupRequest): Promise<CacheLookupResponse> {
    return fetchJSON<CacheLookupResponse>('/context-review/cache-lookup', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Health check for context review feature.
   *
   * @returns Promise resolving to health status
   */
  async healthCheck(): Promise<{ status: string; service_initialized: boolean }> {
    return fetchJSON('/context-review/health');
  },
};

// Export individual functions for backward compatibility
export const {
  startAnalysis,
  getReviewResult,
  getSuggestions,
  checkCache,
  healthCheck: checkContextReviewHealth,
} = contextReviewClient;
