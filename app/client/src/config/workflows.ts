/**
 * Workflow Configuration
 * Centralized configuration for workflow definitions and phases
 */

/**
 * Workflow Phase Definitions
 */
export const workflowPhases = [
  { phase: 'plan', name: 'Plan', icon: '📋' },
  { phase: 'validate', name: 'Validate', icon: '✅' },
  { phase: 'build', name: 'Build', icon: '🔨' },
  { phase: 'lint', name: 'Lint', icon: '🧹' },
  { phase: 'test', name: 'Test', icon: '🧪' },
  { phase: 'review', name: 'Review', icon: '👀' },
  { phase: 'doc', name: 'Doc', icon: '📝' },
  { phase: 'ship', name: 'Ship', icon: '🚀' },
  { phase: 'cleanup', name: 'Cleanup', icon: '🧹' },
] as const;

/**
 * Workflow Type Labels
 */
export const workflowTypeLabels = {
  planning: 'Planning Phase',
  full: 'Full SDLC',
  standard: 'Standard SDLC',
  getLabel: (workflowId: string) => {
    if (workflowId.includes('planning')) return workflowTypeLabels.planning;
    if (workflowId.includes('full')) return workflowTypeLabels.full;
    if (workflowId.includes('standard')) return workflowTypeLabels.standard;
    return `Workflow ${workflowId}`;
  },
} as const;

// Type exports for better TypeScript support
export type WorkflowPhase = typeof workflowPhases[number];
export type WorkflowPhaseType = WorkflowPhase['phase'];
