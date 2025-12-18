/**
 * API Configuration
 * Centralized configuration for all API endpoints and service URLs
 */

// Environment variables with fallback defaults
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8002';
const API_BASE_PATH = import.meta.env.VITE_API_BASE_PATH || '/api/v1';
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '8002';
const WEBHOOK_SERVICE_URL = import.meta.env.VITE_WEBHOOK_SERVICE_URL || 'http://localhost:8001';

// GitHub configuration
const GITHUB_REPO_OWNER = import.meta.env.VITE_GITHUB_REPO_OWNER || 'warmonger0';
const GITHUB_REPO_NAME = import.meta.env.VITE_GITHUB_REPO_NAME || 'tac-webbuilder';

/**
 * API endpoint configuration
 */
export const apiConfig = {
  // Base API path - use full backend URL for cross-origin requests
  basePath: `${BACKEND_URL}${API_BASE_PATH}`,

  // Backend port for WebSocket connections
  backendPort: BACKEND_PORT,

  // Webhook service URL
  webhookServiceUrl: WEBHOOK_SERVICE_URL,

  // GitHub repository information
  github: {
    owner: GITHUB_REPO_OWNER,
    repo: GITHUB_REPO_NAME,
    baseUrl: 'https://github.com',
    getIssueUrl: (issueNumber: number) =>
      `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/issues/${issueNumber}`,
    getPullRequestUrl: (prNumber: number) =>
      `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/pull/${prNumber}`,
  },

  // WebSocket endpoints
  websocket: {
    getUrl: (path: string, protocol?: string, host?: string) => {
      const wsProtocol = protocol || (window.location.protocol === 'https:' ? 'wss:' : 'ws:');
      // Use explicit backend host from BACKEND_URL instead of window.location.hostname
      // This ensures WebSocket connections go to the correct backend server
      const backendHost = new URL(BACKEND_URL).hostname;
      const wsHost = host || backendHost;
      return `${wsProtocol}//${wsHost}:${BACKEND_PORT}${API_BASE_PATH}${path}`;
    },
    workflows: () => apiConfig.websocket.getUrl('/ws/workflows'),
    routes: () => apiConfig.websocket.getUrl('/ws/routes'),
    workflowHistory: () => apiConfig.websocket.getUrl('/ws/workflow-history'),
    adwState: (adwId: string) => apiConfig.websocket.getUrl(`/ws/adw-state/${adwId}`),
    adwMonitor: () => apiConfig.websocket.getUrl('/ws/adw-monitor'),
    queue: () => apiConfig.websocket.getUrl('/ws/queue'),
    systemStatus: () => apiConfig.websocket.getUrl('/ws/system-status'),
    webhookStatus: () => apiConfig.websocket.getUrl('/ws/webhook-status'),
    plannedFeatures: () => apiConfig.websocket.getUrl('/ws/planned-features'),
  },

  // REST API endpoints (relative to basePath)
  endpoints: {
    workflowCatalog: '/api/workflow-catalog',
    preflightChecks: (skipTests: boolean = false) =>
      `/api/preflight-checks?skip_tests=${skipTests}`,
  },
} as const;

// Type exports for better TypeScript support
export type ApiConfig = typeof apiConfig;
export type WebSocketConfig = typeof apiConfig.websocket;
export type GitHubConfig = typeof apiConfig.github;
