import type { CostBreakdown, PhaseCost, WorkflowHistoryItem } from '../../types';

/**
 * Transform cost_breakdown.by_phase to PhaseCost array
 */
export function transformToPhaseCosts(costBreakdown?: CostBreakdown): PhaseCost[] | null {
  if (!costBreakdown?.by_phase) return null;

  const phases = Object.entries(costBreakdown.by_phase).map(([phase, cost]) => ({
    phase,
    cost,
    tokens: {
      input_tokens: 0,
      output_tokens: 0,
      cache_creation_tokens: 0,
      cache_read_tokens: 0,
    },
  }));

  return phases.length > 0 ? phases : null;
}

/**
 * Calculate budget delta between estimated and actual costs
 */
export function calculateBudgetDelta(
  estimated: number,
  actual: number
): { delta: number; percentage: number; status: 'under' | 'over' | 'neutral' } {
  const delta = actual - estimated;
  const percentage = estimated > 0 ? (delta / estimated) * 100 : 0;

  let status: 'under' | 'over' | 'neutral';
  if (actual < estimated * 0.95) {
    status = 'under';
  } else if (actual > estimated * 1.05) {
    status = 'over';
  } else {
    status = 'neutral';
  }

  return { delta, percentage, status };
}

/**
 * Calculate retry cost impact
 */
export function calculateRetryCost(workflow: WorkflowHistoryItem): number | null {
  if (workflow.retry_count === 0) return null;
  if (workflow.actual_cost_total > workflow.estimated_cost_total) {
    return workflow.actual_cost_total - workflow.estimated_cost_total;
  }
  return null;
}

/**
 * Calculate cache savings based on cache hit tokens
 */
export function calculateCacheSavings(workflow: WorkflowHistoryItem): number {
  // Cache hits are ~90% cheaper than cache misses
  // Assuming cache miss cost is standard input token cost
  const cacheHitCostPerToken = workflow.cost_per_token * 0.1;
  const cacheMissCostPerToken = workflow.cost_per_token;
  const savings =
    workflow.cache_hit_tokens * (cacheMissCostPerToken - cacheHitCostPerToken);
  return savings;
}

/**
 * Truncate text to specified length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Get Tailwind CSS classes for classification badge
 */
export function getClassificationColor(classification?: string): string {
  switch (classification?.toLowerCase()) {
    case 'feature':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'bug':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'chore':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

/**
 * Format structured input for display
 */
export function formatStructuredInputForDisplay(input?: Record<string, any>): Array<{ key: string; value: any }> {
  if (!input) return [];

  return Object.entries(input)
    .filter(([_, value]) => value !== null && value !== undefined)
    .map(([key, value]) => ({ key, value }));
}

/**
 * Format date timestamp
 */
export function formatDate(timestamp?: string): string {
  if (!timestamp) return 'N/A';
  try {
    // Handle timestamps that may or may not have timezone info
    // If no timezone marker (Z or +/-), assume UTC
    let dateStr = timestamp;
    if (!timestamp.includes('Z') && !timestamp.includes('+') && !timestamp.includes('T')) {
      // Old format: "2025-11-19 07:08:51" -> assume UTC
      dateStr = timestamp.replace(' ', 'T') + 'Z';
    } else if (timestamp.includes('T') && !timestamp.includes('Z') && !timestamp.includes('+')) {
      // ISO format without timezone: "2025-11-19T07:08:51" -> assume UTC
      dateStr = timestamp + 'Z';
    }
    return new Date(dateStr).toLocaleString();
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format duration in seconds to readable string
 */
export function formatDuration(seconds?: number): string {
  if (!seconds) return 'N/A';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

/**
 * Format cost with dollar sign
 */
export function formatCost(cost: number | undefined): string {
  if (cost === undefined || cost === 0) {
    return 'N/A';
  }
  return `$${cost.toFixed(4)}`;
}

/**
 * Format number with thousand separators
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}
