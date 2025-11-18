### Workflow 1.1: Extract Utility Functions to utils/ Directory
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (lines 16-128)

**Output Files:**
- `app/client/src/utils/formatters.ts` (new)
- `app/client/src/utils/workflowHelpers.ts` (new)

**Tasks:**
1. Create `app/client/src/utils/` directory if it doesn't exist
2. Create `formatters.ts` with date, duration, cost, number formatters
3. Create `workflowHelpers.ts` with workflow calculation functions
4. Add TypeScript interfaces for function parameters
5. Add JSDoc comments to all exported functions

**Implementation - formatters.ts:**

```typescript
/**
 * Format date to human-readable string
 * @param date - Date string or Date object
 * @returns Formatted date string (e.g., "Jan 15, 2025, 10:30 AM")
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format duration in seconds to human-readable string
 * @param seconds - Duration in seconds
 * @returns Formatted duration (e.g., "2m 30s", "1h 15m")
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

/**
 * Format cost to currency string with 4 decimal places
 * @param cost - Cost in dollars
 * @returns Formatted currency string (e.g., "$1.2346")
 */
export function formatCost(cost: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4
  }).format(cost);
}

/**
 * Format large numbers with commas
 * @param num - Number to format
 * @returns Formatted number string (e.g., "1,234,567")
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US');
}

/**
 * Format percentage with specified decimal places
 * @param value - Percentage value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "75.5%")
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Truncate text to specified length
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text with ellipsis if needed
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
```

**Implementation - workflowHelpers.ts:**

```typescript
import type { WorkflowHistoryItem, PhaseCost, CostBreakdown } from '../types';

/**
 * Transform cost breakdown to phase costs array
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
 * Calculate budget delta and status
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
 * Calculate cache savings
 */
export function calculateCacheSavings(workflow: WorkflowHistoryItem): number {
  const cacheHitCostPerToken = workflow.cost_per_token * 0.1;
  const cacheMissCostPerToken = workflow.cost_per_token;
  const savings =
    workflow.cache_hit_tokens * (cacheMissCostPerToken - cacheHitCostPerToken);
  return savings;
}

/**
 * Get classification badge color classes
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
export function formatStructuredInputForDisplay(
  input?: Record<string, any>
): Array<{ key: string; value: any }> {
  if (!input) return [];

  return Object.entries(input)
    .filter(([_, value]) => value !== null && value !== undefined)
    .map(([key, value]) => ({ key, value }));
}
```

**Acceptance Criteria:**
- [ ] formatters.ts created with 6 formatting functions
- [ ] workflowHelpers.ts created with 6 helper functions
- [ ] All functions have JSDoc comments
- [ ] All functions have TypeScript type annotations
- [ ] No compilation errors

**Verification Commands:**
```bash
cd app/client
npm run typecheck
npm run build
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
