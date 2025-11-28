/**
 * Application Thresholds Configuration
 * Centralized configuration for all threshold values
 */

export const thresholds = {
  // Cost estimation thresholds
  cost: {
    highCostWarning: 2.0,              // Threshold for high cost warning (in dollars)
  },

  // File upload configuration
  fileUpload: {
    acceptedTypes: '.md,.markdown',    // Accepted file types
    maxFileSize: 10 * 1024 * 1024,     // 10MB max file size (future use)
  },
} as const;

// Type export for better TypeScript support
export type ThresholdsConfig = typeof thresholds;
