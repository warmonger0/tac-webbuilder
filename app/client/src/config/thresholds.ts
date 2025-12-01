/**
 * Application Thresholds Configuration
 * Centralized configuration for all threshold values
 */

export const thresholds = {
  // Cost estimation thresholds
  cost: {
    highCostWarning: 2.0,              // Threshold for high cost warning (in dollars)
  },

  // Cache efficiency thresholds (percentage)
  cacheEfficiency: {
    excellent: 80,                     // Excellent cache efficiency (≥80%)
    good: 60,                          // Good cache efficiency (≥60%)
    fair: 40,                          // Fair cache efficiency (≥40%)
  },

  // Score thresholds (0-100 scale)
  scores: {
    excellent: 90,                     // Excellent score (≥90)
    good: 70,                          // Good score (≥70)
    fair: 50,                          // Fair score (≥50)
  },

  // Display limits for UI components
  display: {
    recentFailuresLimit: 3,            // Number of recent failures to show
    similarWorkflowsLimit: 1,          // Number of similar workflows to fetch per comparison
  },

  // File upload configuration
  fileUpload: {
    acceptedTypes: '.md,.markdown',    // Accepted file types
    maxFileSize: 10 * 1024 * 1024,     // 10MB max file size (future use)
  },
} as const;

// Type export for better TypeScript support
export type ThresholdsConfig = typeof thresholds;
