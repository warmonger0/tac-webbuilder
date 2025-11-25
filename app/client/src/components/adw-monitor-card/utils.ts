import type { AdwWorkflowStatus } from '../../api/client';

export const formatDuration = (seconds: number | null): string => {
  if (!seconds) return 'N/A';
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) return `${hours}h ${mins}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
};

export const formatCost = (cost: number | null): string => {
  if (!cost) return '$0.00';
  return `$${cost.toFixed(2)}`;
};

export const getPhaseStatus = (
  workflow: AdwWorkflowStatus,
  phaseKey: string
): 'pending' | 'active' | 'completed' => {
  const lowerPhase = phaseKey.toLowerCase();
  const currentPhase = workflow.current_phase?.toLowerCase() || '';

  // Check if this phase is completed
  if (workflow.phases_completed.some(p => p.toLowerCase().includes(lowerPhase))) {
    return 'completed';
  }
  // Check if this is the current phase
  if (currentPhase.includes(lowerPhase)) {
    return 'active';
  }
  // Otherwise it's pending
  return 'pending';
};

export const workflowPhases = [
  { name: 'Plan', icon: 'clipboard', key: 'plan' },
  { name: 'Validate', icon: 'check-circle', key: 'validate' },
  { name: 'Build', icon: 'cube', key: 'build' },
  { name: 'Lint', icon: 'sparkles', key: 'lint' },
  { name: 'Test', icon: 'beaker', key: 'test' },
  { name: 'Review', icon: 'eye', key: 'review' },
  { name: 'Doc', icon: 'document', key: 'doc' },
  { name: 'Ship', icon: 'rocket', key: 'ship' },
  { name: 'Cleanup', icon: 'trash', key: 'cleanup' }
];
