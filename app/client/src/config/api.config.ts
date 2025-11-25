/**
 * API Configuration
 *
 * This module provides centralized configuration for all API endpoints,
 * timeouts, retry logic, and request behavior.
 */

import type { ApiConfig } from './types';
import { environmentConfig } from './environment';

/**
 * Get the webhook service URL based on environment
 * In development, use localhost. In production, use the configured URL.
 */
function getWebhookUrl(): string {
  // Allow override via environment variable
  const envUrl = import.meta.env.VITE_WEBHOOK_URL;
  if (envUrl) {
    return envUrl;
  }

  // Default based on environment
  if (environmentConfig.isDevelopment()) {
    return 'http://localhost:8001/webhook-status';
  }

  // In production, webhook service should be proxied through the backend
  return '/api/webhook-status';
}

/**
 * Get the API timeout value
 */
function getApiTimeout(): number {
  const envTimeout = import.meta.env.VITE_API_TIMEOUT;
  if (envTimeout) {
    return parseInt(envTimeout, 10);
  }
  return 30000; // 30 seconds default
}

/**
 * API configuration object
 */
export const apiConfig: ApiConfig = {
  /** Base path for all API requests */
  BASE_PATH: '/api',

  /** Webhook service URL */
  WEBHOOK_URL: getWebhookUrl(),

  /** Default timeout for API requests (30 seconds) */
  DEFAULT_TIMEOUT: getApiTimeout(),

  /** Number of retry attempts for failed requests */
  RETRY_ATTEMPTS: 3,

  /** Delay between retry attempts (1 second) */
  RETRY_DELAY: 1000,

  /** API endpoint paths */
  ENDPOINTS: {
    REQUEST: '/api/request',
    PREVIEW: '/api/preview',
    CONFIRM: '/api/confirm',
    WORKFLOWS: '/api/workflows',
    HISTORY: '/api/history',
    WORKFLOW_HISTORY: '/api/workflow-history',
    ROUTES: '/api/routes',
    QUERY: '/api/query',
    RANDOM_QUERY: '/api/random-query',
    UPLOAD: '/api/upload',
    SCHEMA: '/api/schema',
    EXPORT: '/api/export',
    WEBHOOK_STATUS: '/api/webhook-status',
    SYSTEM_STATUS: '/api/system-status',
    QUEUE: '/api/queue',
    ADW_MONITOR: '/api/adw-monitor',
  },
};

/**
 * Default export for convenient importing
 */
export default apiConfig;
