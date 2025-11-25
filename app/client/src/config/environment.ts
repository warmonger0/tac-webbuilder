/**
 * Environment Detection and Configuration
 *
 * This module provides environment detection utilities and exposes
 * environment-specific configuration overrides.
 */

import type { Environment, EnvironmentConfig } from './types';

/**
 * Detect the current environment from Vite's environment variables
 * @returns The current environment (development, staging, or production)
 */
function getEnvironment(): Environment {
  // Vite exposes the mode via import.meta.env.MODE
  // Common modes: 'development', 'production', 'staging'
  const mode = import.meta.env.MODE;

  if (mode === 'production') {
    return 'production';
  }

  if (mode === 'staging') {
    return 'staging';
  }

  // Default to development for any other mode
  return 'development';
}

/**
 * Current detected environment
 */
const currentEnvironment = getEnvironment();

/**
 * Environment configuration object
 */
export const environmentConfig: EnvironmentConfig = {
  /** Current environment */
  CURRENT: currentEnvironment,

  /** Check if running in development mode */
  isDevelopment: () => currentEnvironment === 'development',

  /** Check if running in production mode */
  isProduction: () => currentEnvironment === 'production',

  /** Check if running in staging mode */
  isStaging: () => currentEnvironment === 'staging',
};

/**
 * Default export for convenient importing
 */
export default environmentConfig;
