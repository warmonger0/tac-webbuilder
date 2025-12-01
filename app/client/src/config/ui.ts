/**
 * UI Text Configuration
 * Centralized configuration for UI text strings and labels
 * This enables easy internationalization (i18n) in the future
 */

export const uiText = {
  // ADW Monitor Card
  adwMonitor: {
    currentWorkflowTitle: 'Current Workflow',
    currentWorkflowSubtitle: 'Real-time progress',
    noActiveWorkflow: 'No Active Workflow',
    hopperQueueTitle: 'Hopper Queue',
    phasesCompleted: 'phases completed',
    processActive: 'Process Active',
  },

  // Workflow States
  workflowStates: {
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
    paused: 'Paused',
    pending: 'Pending',
  },

  // Common Actions
  actions: {
    viewOnGitHub: 'View on GitHub',
    refresh: 'Refresh',
    retry: 'Retry',
    cancel: 'Cancel',
  },

  // Status Messages
  status: {
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    noData: 'No data available',
  },
} as const;

// Type export for better TypeScript support
export type UiTextConfig = typeof uiText;
