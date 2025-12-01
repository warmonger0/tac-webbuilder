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
 * Phase SVG Icon Mappings (for UI components using Heroicons)
 */
export const phaseSvgIconMap: Record<string, string> = {
  plan: 'clipboard',
  validate: 'check-circle',
  build: 'cube',
  lint: 'sparkles',
  test: 'beaker',
  review: 'eye',
  doc: 'document',
  ship: 'rocket',
  cleanup: 'trash'
} as const;

/**
 * Workflow Type Labels
 */
export const workflowTypeLabels = {
  planning: 'Planning Phase',
  full: 'Full SDLC',
  standard: 'Standard SDLC',
  defaultPrefix: 'Workflow',
  getLabel: (workflowId: string) => {
    if (workflowId.includes('planning')) return workflowTypeLabels.planning;
    if (workflowId.includes('full')) return workflowTypeLabels.full;
    if (workflowId.includes('standard')) return workflowTypeLabels.standard;
    // Return just the workflow type without prefix if it's a known pattern
    const cleanId = workflowId.replace('adw_', '').replace(/_/g, ' ');
    return cleanId || workflowTypeLabels.defaultPrefix;
  },
} as const;

// Type exports for better TypeScript support
export type WorkflowPhase = typeof workflowPhases[number];
export type WorkflowPhaseType = WorkflowPhase['phase'];
