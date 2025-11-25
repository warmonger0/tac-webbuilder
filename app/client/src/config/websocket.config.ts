/**
 * WebSocket Configuration
 *
 * This module provides centralized configuration for WebSocket connections,
 * including URLs, ports, reconnection settings, and helper functions for
 * building WebSocket URLs.
 */

import type { WebSocketConfig } from './types';

/**
 * Get the WebSocket port from environment variable or default
 */
function getWebSocketPort(): number {
  const envPort = import.meta.env.VITE_WEBSOCKET_PORT;
  if (envPort) {
    return parseInt(envPort, 10);
  }
  return 8000; // Default WebSocket port
}

/**
 * Detect the WebSocket protocol based on current page protocol
 */
function getWebSocketProtocol(): 'ws:' | 'wss:' {
  return window.location.protocol === 'https:' ? 'wss:' : 'ws:';
}

/**
 * Build a complete WebSocket URL for the given endpoint
 * @param endpoint - The endpoint path (e.g., '/ws/workflows')
 * @param params - Optional URL parameters (e.g., { adwId: '123' })
 * @returns Complete WebSocket URL
 */
function getWebSocketUrl(endpoint: string, params?: Record<string, string>): string {
  const protocol = getWebSocketProtocol();
  const host = window.location.hostname;
  const port = getWebSocketPort();

  // Replace URL parameters in the endpoint (e.g., :adwId -> 123)
  let finalEndpoint = endpoint;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      finalEndpoint = finalEndpoint.replace(`:${key}`, value);
    });
  }

  return `${protocol}//${host}:${port}${finalEndpoint}`;
}

/**
 * WebSocket configuration object
 */
export const websocketConfig: WebSocketConfig = {
  /** WebSocket port number */
  PORT: getWebSocketPort(),

  /** WebSocket protocol (ws: or wss:) */
  PROTOCOL: getWebSocketProtocol(),

  /** Polling interval when WebSocket is disconnected (3 seconds) */
  POLLING_INTERVAL: 3000,

  /** Maximum delay between reconnection attempts (30 seconds) */
  MAX_RECONNECT_DELAY: 30000,

  /** Maximum number of reconnection attempts before giving up */
  MAX_RECONNECT_ATTEMPTS: 10,

  /** WebSocket endpoint paths */
  ENDPOINTS: {
    WORKFLOWS: '/ws/workflows',
    ROUTES: '/ws/routes',
    WORKFLOW_HISTORY: '/ws/workflow-history',
    ADW_STATE: '/ws/adw-state/:adwId',
  },

  /** Helper function to build WebSocket URLs */
  getWebSocketUrl,
};

/**
 * Default export for convenient importing
 */
export default websocketConfig;
