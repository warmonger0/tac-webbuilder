/**
 * Central Configuration Export
 *
 * This is the main entry point for the configuration system.
 * Import configuration from this file throughout the application:
 *
 * @example
 * import { config } from '@/config';
 * const apiUrl = config.api.BASE_PATH;
 *
 * @example
 * import { apiConfig, websocketConfig } from '@/config';
 * const wsUrl = websocketConfig.getWebSocketUrl('/ws/workflows');
 */

import type { AppConfig } from './types';
import { constants } from './constants';
import { environmentConfig } from './environment';
import { apiConfig } from './api.config';
import { websocketConfig } from './websocket.config';
import { storageConfig } from './storage.config';
import { githubConfig } from './github.config';

/**
 * Unified configuration object
 * Contains all configuration modules in a single object
 */
export const config: AppConfig = {
  app: constants,
  api: apiConfig,
  websocket: websocketConfig,
  storage: storageConfig,
  github: githubConfig,
  environment: environmentConfig,
};

/**
 * Get the full configuration object
 * @returns Complete application configuration
 */
export function getConfig(): AppConfig {
  return config;
}

/**
 * Re-export individual configuration modules for direct imports
 */
export { constants, environmentConfig, apiConfig, websocketConfig, storageConfig, githubConfig };

/**
 * Re-export types for convenience
 */
export type * from './types';

/**
 * Default export for convenient importing
 */
export default config;
