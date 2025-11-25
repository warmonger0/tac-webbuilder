/**
 * Storage Configuration
 *
 * This module provides centralized configuration for localStorage keys,
 * including namespace prefixes and helper functions for storage operations.
 */

import type { StorageConfig } from './types';
import { constants } from './constants';

/**
 * Get a namespaced storage key
 * @param key - The key name
 * @returns Namespaced key (e.g., 'tac-webbuilder-my-key')
 */
function getStorageKey(key: string): string {
  return `${constants.NAMESPACE}-${key}`;
}

/**
 * Clear all application-related localStorage data
 */
function clearAppStorage(): void {
  try {
    // Get all keys from localStorage
    const keys = Object.keys(localStorage);

    // Filter keys that start with our namespace
    const appKeys = keys.filter((key) => key.startsWith(`${constants.NAMESPACE}-`));

    // Remove all app-specific keys
    appKeys.forEach((key) => {
      localStorage.removeItem(key);
    });

    console.log(`Cleared ${appKeys.length} application storage keys`);
  } catch (err) {
    console.error('Failed to clear application storage:', err);
  }
}

/**
 * Storage configuration object
 */
export const storageConfig: StorageConfig = {
  /** Namespace prefix for all localStorage keys */
  NAMESPACE: constants.NAMESPACE,

  /** Storage key for request form state */
  REQUEST_FORM_STATE_KEY: getStorageKey('request-form-state'),

  /** Storage key for request form state version */
  REQUEST_FORM_STATE_VERSION: 1,

  /** Storage key for project path */
  PROJECT_PATH_KEY: getStorageKey('project-path'),

  /** Storage key for active tab persistence */
  ACTIVE_TAB_KEY: getStorageKey('active-tab'),

  /** Helper function to get namespaced storage keys */
  getStorageKey,

  /** Helper function to clear all app storage */
  clearAppStorage,
};

/**
 * Default export for convenient importing
 */
export default storageConfig;
