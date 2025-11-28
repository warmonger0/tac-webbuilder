/**
 * Base API client with shared utilities for making API requests.
 *
 * This module provides the foundational HTTP request functionality
 * used by all domain-specific API clients.
 */

import { apiConfig } from '../config/api';

export const API_BASE = apiConfig.basePath;

/**
 * Generic fetch wrapper with JSON handling and error management.
 *
 * @template T - The expected response type
 * @param url - The URL to fetch from
 * @param options - Optional fetch configuration
 * @returns Promise resolving to the parsed JSON response
 * @throws Error if the response is not ok or JSON parsing fails
 */
export async function fetchJSON<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
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

/**
 * Helper for GET requests
 */
export async function apiGet<T>(url: string): Promise<T> {
  return fetchJSON<T>(url, { method: 'GET' });
}

/**
 * Helper for POST requests
 */
export async function apiPost<T>(
  url: string,
  data?: any
): Promise<T> {
  return fetchJSON<T>(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper for DELETE requests
 */
export async function apiDelete<T>(url: string): Promise<T> {
  return fetchJSON<T>(url, { method: 'DELETE' });
}
