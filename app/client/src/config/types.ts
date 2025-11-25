/**
 * Configuration Type Definitions
 *
 * This file contains TypeScript interfaces for all configuration objects
 * in the application. These types ensure type safety across the config system.
 */

/**
 * Environment types supported by the application
 */
export type Environment = 'development' | 'staging' | 'production';

/**
 * API configuration interface
 * Controls all API endpoint URLs, timeouts, and request behavior
 */
export interface ApiConfig {
  /** Base path for all API requests (e.g., '/api') */
  BASE_PATH: string;

  /** Full webhook service URL for direct access */
  WEBHOOK_URL: string;

  /** Default timeout for API requests in milliseconds */
  DEFAULT_TIMEOUT: number;

  /** Number of retry attempts for failed requests */
  RETRY_ATTEMPTS: number;

  /** Delay between retry attempts in milliseconds */
  RETRY_DELAY: number;

  /** All API endpoint paths */
  ENDPOINTS: {
    REQUEST: string;
    PREVIEW: string;
    CONFIRM: string;
    WORKFLOWS: string;
    HISTORY: string;
    WORKFLOW_HISTORY: string;
    ROUTES: string;
    QUERY: string;
    RANDOM_QUERY: string;
    UPLOAD: string;
    SCHEMA: string;
    EXPORT: string;
    WEBHOOK_STATUS: string;
    SYSTEM_STATUS: string;
    QUEUE: string;
    ADW_MONITOR: string;
  };
}

/**
 * WebSocket configuration interface
 * Controls WebSocket connection URLs, ports, and reconnection behavior
 */
export interface WebSocketConfig {
  /** WebSocket port number */
  PORT: number;

  /** WebSocket protocol (ws: or wss:) */
  PROTOCOL: 'ws:' | 'wss:';

  /** Polling interval when WebSocket is disconnected (milliseconds) */
  POLLING_INTERVAL: number;

  /** Maximum delay between reconnection attempts (milliseconds) */
  MAX_RECONNECT_DELAY: number;

  /** Maximum number of reconnection attempts before giving up */
  MAX_RECONNECT_ATTEMPTS: number;

  /** WebSocket endpoint paths */
  ENDPOINTS: {
    WORKFLOWS: string;
    ROUTES: string;
    WORKFLOW_HISTORY: string;
    ADW_STATE: string;
  };

  /**
   * Build a complete WebSocket URL for the given endpoint
   * @param endpoint - The endpoint path (e.g., '/ws/workflows')
   * @param params - Optional URL parameters (e.g., { adwId: '123' })
   * @returns Complete WebSocket URL
   */
  getWebSocketUrl: (endpoint: string, params?: Record<string, string>) => string;
}

/**
 * Storage configuration interface
 * Controls localStorage key names and storage behavior
 */
export interface StorageConfig {
  /** Namespace prefix for all localStorage keys */
  NAMESPACE: string;

  /** Storage key for request form state */
  REQUEST_FORM_STATE_KEY: string;

  /** Storage key for request form state version */
  REQUEST_FORM_STATE_VERSION: number;

  /** Storage key for project path */
  PROJECT_PATH_KEY: string;

  /** Storage key for active tab persistence */
  ACTIVE_TAB_KEY: string;

  /**
   * Get a namespaced storage key
   * @param key - The key name
   * @returns Namespaced key (e.g., 'tac-webbuilder-my-key')
   */
  getStorageKey: (key: string) => string;

  /**
   * Clear all application-related localStorage data
   */
  clearAppStorage: () => void;
}

/**
 * GitHub integration configuration interface
 * Controls GitHub repository URLs and integration settings
 */
export interface GitHubConfig {
  /** GitHub repository owner username */
  REPO_OWNER: string;

  /** GitHub repository name */
  REPO_NAME: string;

  /** Full repository URL */
  REPO_URL: string;

  /** Issues URL template */
  ISSUES_URL: string;

  /** Pull requests URL template */
  PULLS_URL: string;

  /**
   * Get the full URL for a specific issue
   * @param issueNumber - The issue number
   * @returns Full GitHub issue URL
   */
  getIssueUrl: (issueNumber: number) => string;

  /**
   * Get the full URL for a specific pull request
   * @param prNumber - The pull request number
   * @returns Full GitHub pull request URL
   */
  getPullRequestUrl: (prNumber: number) => string;
}

/**
 * Application constants interface
 * General application-wide constants and branding
 */
export interface AppConstants {
  /** Application name */
  NAME: string;

  /** Application tagline/description */
  TAGLINE: string;

  /** Application namespace for localStorage and other identifiers */
  NAMESPACE: string;

  /** Application version (from package.json or hardcoded) */
  VERSION: string;
}

/**
 * Environment-specific configuration interface
 * Controls environment detection and environment-specific overrides
 */
export interface EnvironmentConfig {
  /** Current environment (development, staging, production) */
  CURRENT: Environment;

  /** Check if running in development mode */
  isDevelopment: () => boolean;

  /** Check if running in production mode */
  isProduction: () => boolean;

  /** Check if running in staging mode */
  isStaging: () => boolean;
}

/**
 * Root application configuration interface
 * Aggregates all configuration modules
 */
export interface AppConfig {
  /** Application constants */
  app: AppConstants;

  /** API configuration */
  api: ApiConfig;

  /** WebSocket configuration */
  websocket: WebSocketConfig;

  /** Storage configuration */
  storage: StorageConfig;

  /** GitHub integration configuration */
  github: GitHubConfig;

  /** Environment configuration */
  environment: EnvironmentConfig;
}
