/**
 * Polling and Timing Intervals Configuration
 * Centralized configuration for all timing-related values
 */

export const intervals = {
  // WebSocket Configuration
  websocket: {
    pollingInterval: 60000,             // Fallback polling interval when WebSocket disconnected (ms) - reduced from 3s to 60s to prevent log spam
    maxReconnectDelay: 30000,           // Max reconnect delay (ms)
    maxReconnectAttempts: 10,           // Max reconnect attempts
    qualityUpdateInterval: 5000,        // Quality update interval (ms)

    // Connection quality thresholds
    quality: {
      excellentThreshold: 5000,         // Excellent quality threshold (ms)
      goodThreshold: 15000,              // Good quality threshold (ms)
      poorThreshold: 30000,              // Poor quality threshold (ms)
    },
  },

  // Polling Configuration
  polling: {
    defaultInterval: 60000,             // Default polling interval (1 minute)
    minInterval: 30000,                 // Min interval (30 seconds)
    maxInterval: 120000,                // Max interval (2 minutes)
    maxConsecutiveErrors: 5,            // Max consecutive errors before backing off
    backoffMultiplier: 1.5,             // Exponential backoff multiplier
    randomStaggerMax: 2000,             // Random stagger delay max (ms)

    // Polling quality thresholds
    quality: {
      excellentThreshold: 10000,        // Excellent quality time threshold (ms)
      goodThreshold: 30000,              // Good quality time threshold (ms)
      poorThreshold: 60000,              // Poor quality time threshold (ms)
    },
  },

  // Component-Specific Intervals
  components: {
    preflightChecks: {
      autoRefreshInterval: 30000,       // Auto-refresh interval (ms)
    },

    systemStatus: {
      pollingInterval: 30000,           // Status polling interval (ms)
      refreshDelayAfterAction: 2000,    // Delay after action (ms)
    },

    hopperQueue: {
      pollingInterval: 10000,           // Queue polling interval (ms)
    },

    adwMonitor: {
      activePollingInterval: 10000,     // Active workflow polling (ms)
      idlePollingInterval: 30000,       // Idle workflow polling (ms)
      maxReconnectAttempts: 5,          // Max reconnect attempts for ADW state
    },

    fileUpload: {
      successMessageDelay: 3000,        // Success message auto-hide delay (ms)
    },

    workflowHistory: {
      defaultLimit: 50,                 // Default workflow history limit
    },
  },
} as const;

// Type export for better TypeScript support
export type IntervalsConfig = typeof intervals;
