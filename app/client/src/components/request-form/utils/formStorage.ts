import type { RequestFormPersistedState } from '../../../types';

const REQUEST_FORM_STATE_STORAGE_KEY = 'tac-webbuilder-request-form-state';
const REQUEST_FORM_STATE_VERSION = 1;
export const PROJECT_PATH_STORAGE_KEY = 'tac-webbuilder-project-path';

/**
 * Save form state to localStorage
 */
export function saveFormState(state: Omit<RequestFormPersistedState, 'version' | 'timestamp'>): void {
  try {
    const persistedState: RequestFormPersistedState = {
      version: REQUEST_FORM_STATE_VERSION,
      timestamp: new Date().toISOString(),
      ...state,
    };
    localStorage.setItem(REQUEST_FORM_STATE_STORAGE_KEY, JSON.stringify(persistedState));
  } catch (err) {
    // Handle quota exceeded or unavailable storage
    console.error('Failed to save form state:', err);
    throw err;
  }
}

/**
 * Load form state from localStorage
 */
export function loadFormState(): RequestFormPersistedState | null {
  try {
    const savedData = localStorage.getItem(REQUEST_FORM_STATE_STORAGE_KEY);
    if (!savedData) {
      return null;
    }

    const parsed = JSON.parse(savedData);

    // Validate structure and version
    if (!validateFormState(parsed)) {
      console.warn('Invalid form state found, ignoring');
      return null;
    }

    return parsed as RequestFormPersistedState;
  } catch (err) {
    console.error('Failed to load form state:', err);
    return null;
  }
}

/**
 * Clear form state from localStorage
 */
export function clearFormState(): void {
  try {
    localStorage.removeItem(REQUEST_FORM_STATE_STORAGE_KEY);
  } catch (err) {
    console.error('Failed to clear form state:', err);
  }
}

/**
 * Validate form state structure
 */
function validateFormState(data: unknown): data is RequestFormPersistedState {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const obj = data as Record<string, unknown>;

  // Check version
  if (obj.version !== REQUEST_FORM_STATE_VERSION) {
    return false;
  }

  // Check required fields
  if (
    typeof obj.nlInput !== 'string' ||
    typeof obj.projectPath !== 'string' ||
    typeof obj.autoPost !== 'boolean' ||
    typeof obj.timestamp !== 'string'
  ) {
    return false;
  }

  return true;
}
