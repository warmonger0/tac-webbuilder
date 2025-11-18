# Phase 4: Frontend Component Refactoring - Detailed Implementation Plan

**Status:** Not Started
**Duration:** 3-4 days (15-17 atomic workflows)
**Priority:** HIGH
**Risk:** Medium

## Overview

Refactor frontend React components to improve maintainability and eliminate code duplication. This phase focuses on splitting the oversized `WorkflowHistoryCard.tsx` component (793 lines) into focused section components and consolidating duplicated WebSocket hooks (275 lines → ~80 lines).

**Success Criteria:**
- ✅ WorkflowHistoryCard.tsx reduced from 793 lines to <200 lines
- ✅ 8 new section components created and tested
- ✅ WebSocket hooks consolidated from 275 lines to ~80 lines
- ✅ Utility formatters extracted to reusable module
- ✅ Test coverage >80% for all new components
- ✅ Zero visual regressions (UI/UX unchanged)

---

## Hierarchical Decomposition

### Level 1: Major Components
1. WorkflowHistoryCard Split (12 workflows)
2. WebSocket Hooks Consolidation (4 workflows)

### Level 2: Atomic Workflow Units

---

## 1. WorkflowHistoryCard Split (12 workflows)

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

---

### Workflow 1.2: Create Component Directory Structure
**Estimated Time:** 30 minutes
**Complexity:** Low
**Dependencies:** None

**Tasks:**
1. Create directory structure for section components
2. Create TypeScript interface file for shared props
3. Set up index file for clean imports

**Directory Structure:**
```bash
mkdir -p app/client/src/components/workflow-history
touch app/client/src/components/workflow-history/types.ts
touch app/client/src/components/workflow-history/index.ts
```

**Implementation - types.ts:**

```typescript
import type { WorkflowHistoryItem } from '../../types';

/**
 * Common props for all workflow history section components
 */
export interface WorkflowSectionProps {
  workflow: WorkflowHistoryItem;
}
```

**Implementation - index.ts:**

```typescript
/**
 * Workflow History Components - Public Exports
 */
export { WorkflowHistoryCard } from './WorkflowHistoryCard';
export { CostEconomicsSection } from './CostEconomicsSection';
export { TokenAnalysisSection } from './TokenAnalysisSection';
export { PerformanceAnalysisSection } from './PerformanceAnalysisSection';
export { ErrorAnalysisSection } from './ErrorAnalysisSection';
export { ResourceUsageSection } from './ResourceUsageSection';
export { WorkflowJourneySection } from './WorkflowJourneySection';
export { EfficiencyScoresSection } from './EfficiencyScoresSection';
export { InsightsSection } from './InsightsSection';

export type { WorkflowSectionProps } from './types';
```

**Acceptance Criteria:**
- [ ] Directory structure created
- [ ] Types file created with WorkflowSectionProps interface
- [ ] Index file prepared for exports

**Verification Commands:**
```bash
ls -la app/client/src/components/workflow-history/
```

**Status:** Not Started

---

### Workflow 1.3: Extract CostEconomicsSection Component
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (lines 252-354)

**Output Files:**
- `app/client/src/components/workflow-history/CostEconomicsSection.tsx` (new)

**Tasks:**
1. Create CostEconomicsSection.tsx component
2. Import WorkflowSectionProps interface
3. Extract budget comparison, cost breakdown, charts
4. Import formatters and helpers from utils/
5. Preserve all existing styling and logic

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { CostBreakdownChart } from '../CostBreakdownChart';
import { CumulativeCostChart } from '../CumulativeCostChart';
import { formatCost } from '../../utils/formatters';
import { transformToPhaseCosts, calculateBudgetDelta } from '../../utils/workflowHelpers';

/**
 * Cost Economics Section
 *
 * Displays workflow cost analysis including:
 * - Budget comparison (estimated vs actual)
 * - Cost breakdown by phase (chart)
 * - Cumulative cost progression (chart)
 * - Per-step cost analysis
 *
 * @param props - Workflow section props
 */
export function CostEconomicsSection({ workflow }: WorkflowSectionProps) {
  const phaseCosts = transformToPhaseCosts(workflow.cost_breakdown);
  const budgetDelta = calculateBudgetDelta(
    workflow.estimated_cost_total,
    workflow.actual_cost_total
  );
  const hasCostData = workflow.actual_cost_total > 0;

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        💰 Cost Economics
      </h3>

      {/* Charts Section */}
      {phaseCosts ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="border border-gray-200 rounded-lg p-4 bg-white">
            <CostBreakdownChart phases={phaseCosts} />
          </div>
          <div className="border border-gray-200 rounded-lg p-4 bg-white">
            <CumulativeCostChart phases={phaseCosts} />
          </div>
        </div>
      ) : (
        hasCostData && (
          <div className="text-sm text-gray-500 mb-6 p-4 bg-gray-50 border border-gray-200 rounded">
            Cost breakdown by phase is not available for this workflow (may be from an
            older execution)
          </div>
        )
      )}

      {/* Budget Comparison Section */}
      {hasCostData && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Budget Comparison</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            {/* Estimated Total */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-gray-600 mb-1">Estimated Total</div>
              <div className="text-lg font-semibold text-blue-700">
                {formatCost(workflow.estimated_cost_total)}
              </div>
            </div>

            {/* Actual Total */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-gray-600 mb-1">Actual Total</div>
              <div className="text-lg font-semibold text-green-700">
                {formatCost(workflow.actual_cost_total)}
              </div>
            </div>

            {/* Budget Delta */}
            <div
              className={`rounded-lg p-3 border ${
                budgetDelta.status === 'under'
                  ? 'bg-green-50 border-green-200'
                  : budgetDelta.status === 'over'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="text-gray-600 mb-1">Budget Delta</div>
              <div
                className={`text-lg font-semibold ${
                  budgetDelta.status === 'under'
                    ? 'text-green-700'
                    : budgetDelta.status === 'over'
                    ? 'text-red-700'
                    : 'text-gray-700'
                }`}
              >
                {budgetDelta.delta >= 0 ? '+' : ''}
                {formatCost(Math.abs(budgetDelta.delta))}
              </div>
              <div
                className={`text-xs ${
                  budgetDelta.status === 'under'
                    ? 'text-green-600'
                    : budgetDelta.status === 'over'
                    ? 'text-red-600'
                    : 'text-gray-600'
                }`}
              >
                {budgetDelta.percentage >= 0 ? '+' : ''}
                {budgetDelta.percentage.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Per-step comparison */}
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-50 rounded p-3">
              <div className="text-gray-600">Estimated per Step</div>
              <div className="font-medium">{formatCost(workflow.estimated_cost_per_step)}</div>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <div className="text-gray-600">Actual per Step</div>
              <div className="font-medium">{formatCost(workflow.actual_cost_per_step)}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/CostEconomicsSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostEconomicsSection } from '../CostEconomicsSection';
import type { WorkflowHistoryItem } from '../../../types';

const mockWorkflow: WorkflowHistoryItem = {
  id: 'test-workflow-123',
  workflow_id: 'test-123',
  issue_number: 42,
  status: 'completed',
  started_at: '2025-01-15T10:00:00Z',
  completed_at: '2025-01-15T10:30:00Z',
  duration_seconds: 1800,
  estimated_cost_total: 2.0,
  actual_cost_total: 1.5,
  estimated_cost_per_step: 0.2,
  actual_cost_per_step: 0.15,
  total_tokens: 50000,
  cost_per_token: 0.00003,
  cache_hit_tokens: 10000,
  cache_efficiency_percent: 20,
  retry_count: 0,
  error_message: null,
  cost_breakdown: {
    by_phase: {
      'Phase 1': 0.5,
      'Phase 2': 0.7,
      'Phase 3': 0.3
    }
  },
  // ... other required fields
} as WorkflowHistoryItem;

describe('CostEconomicsSection', () => {
  it('renders section title', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);
    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
  });

  it('displays budget comparison', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    expect(screen.getByText('Estimated Total')).toBeInTheDocument();
    expect(screen.getByText('$2.0000')).toBeInTheDocument();
    expect(screen.getByText('Actual Total')).toBeInTheDocument();
    expect(screen.getByText('$1.5000')).toBeInTheDocument();
  });

  it('shows under budget when actual < estimated', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    // Budget delta should be negative and shown in green
    const deltaSection = screen.getByText('Budget Delta').closest('div');
    expect(deltaSection).toHaveClass('bg-green-50');
  });

  it('shows over budget when actual > estimated', () => {
    const overBudgetWorkflow = {
      ...mockWorkflow,
      actual_cost_total: 2.5,
      actual_cost_per_step: 0.25
    };

    render(<CostEconomicsSection workflow={overBudgetWorkflow} />);

    const deltaSection = screen.getByText('Budget Delta').closest('div');
    expect(deltaSection).toHaveClass('bg-red-50');
  });

  it('displays per-step costs', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    expect(screen.getByText('Estimated per Step')).toBeInTheDocument();
    expect(screen.getByText('$0.2000')).toBeInTheDocument();
    expect(screen.getByText('Actual per Step')).toBeInTheDocument();
    expect(screen.getByText('$0.1500')).toBeInTheDocument();
  });

  it('renders cost breakdown chart when data available', () => {
    render(<CostEconomicsSection workflow={mockWorkflow} />);

    // Chart components should be rendered
    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
    // Charts render with canvas/svg, hard to test exact content
  });

  it('shows message when cost breakdown unavailable', () => {
    const noCostBreakdownWorkflow = {
      ...mockWorkflow,
      cost_breakdown: undefined
    };

    render(<CostEconomicsSection workflow={noCostBreakdownWorkflow} />);

    expect(screen.getByText(/Cost breakdown by phase is not available/)).toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] CostEconomicsSection component created
- [ ] All formatting uses utilities from utils/
- [ ] Component renders correctly with mock data
- [ ] Tests pass with >80% coverage
- [ ] No visual regressions (UI matches original)

**Verification Commands:**
```bash
cd app/client
npm run test -- CostEconomicsSection.test.tsx
npm run typecheck
npm run dev
# Manual: Navigate to workflow history and verify rendering
```

**Status:** Not Started

---

### Workflow 1.4: Extract TokenAnalysisSection Component
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (lines 356-448)

**Output Files:**
- `app/client/src/components/workflow-history/TokenAnalysisSection.tsx` (new)

**Tasks:**
1. Create TokenAnalysisSection.tsx component
2. Extract token breakdown, cache performance display
3. Import TokenBreakdownChart component
4. Import formatters from utils/
5. Add comprehensive tests

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { TokenBreakdownChart } from '../TokenBreakdownChart';
import { CacheEfficiencyBadge } from '../CacheEfficiencyBadge';
import { formatNumber, formatPercentage, formatCost } from '../../utils/formatters';
import { calculateCacheSavings } from '../../utils/workflowHelpers';

/**
 * Token Analysis Section
 *
 * Displays token usage analytics including:
 * - Token breakdown chart (input, output, cache)
 * - Cache efficiency metrics
 * - Cache hit/miss details
 * - Cache savings calculation
 *
 * @param props - Workflow section props
 */
export function TokenAnalysisSection({ workflow }: WorkflowSectionProps) {
  const cacheSavings = calculateCacheSavings(workflow);
  const hasTokenData = workflow.total_tokens > 0;

  if (!hasTokenData) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        🔢 Token Usage & Cache Performance
      </h3>

      {/* Token Breakdown Chart */}
      <div className="mb-6">
        <TokenBreakdownChart workflow={workflow} />
      </div>

      {/* Cache Efficiency Summary */}
      {workflow.cache_efficiency_percent > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-700">Cache Efficiency</h4>
            <CacheEfficiencyBadge efficiency={workflow.cache_efficiency_percent} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div className="text-gray-600">Cache Hits</div>
              <div className="font-medium text-green-700">
                {formatNumber(workflow.cache_hit_tokens)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Cache Misses</div>
              <div className="font-medium text-orange-700">
                {formatNumber(workflow.cache_miss_tokens || 0)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Hit Rate</div>
              <div className="font-medium text-blue-700">
                {formatPercentage(workflow.cache_efficiency_percent)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Savings</div>
              <div className="font-medium text-green-700">
                {formatCost(cacheSavings)}
              </div>
            </div>
          </div>

          {/* Cache Details Table */}
          <div className="mt-4 text-xs">
            <table className="w-full">
              <thead className="bg-blue-100">
                <tr>
                  <th className="px-2 py-1 text-left text-gray-700">Type</th>
                  <th className="px-2 py-1 text-right text-gray-700">Tokens</th>
                  <th className="px-2 py-1 text-right text-gray-700">% of Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-2 py-1">Input Tokens</td>
                  <td className="px-2 py-1 text-right font-medium">
                    {formatNumber(workflow.input_tokens || 0)}
                  </td>
                  <td className="px-2 py-1 text-right">
                    {formatPercentage(((workflow.input_tokens || 0) / workflow.total_tokens) * 100)}
                  </td>
                </tr>
                <tr>
                  <td className="px-2 py-1">Output Tokens</td>
                  <td className="px-2 py-1 text-right font-medium">
                    {formatNumber(workflow.output_tokens || 0)}
                  </td>
                  <td className="px-2 py-1 text-right">
                    {formatPercentage(((workflow.output_tokens || 0) / workflow.total_tokens) * 100)}
                  </td>
                </tr>
                <tr className="bg-green-50">
                  <td className="px-2 py-1 text-green-700">Cache Read Tokens</td>
                  <td className="px-2 py-1 text-right font-medium text-green-700">
                    {formatNumber(workflow.cache_hit_tokens)}
                  </td>
                  <td className="px-2 py-1 text-right text-green-700">
                    {formatPercentage(workflow.cache_efficiency_percent)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/TokenAnalysisSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TokenAnalysisSection } from '../TokenAnalysisSection';
import type { WorkflowHistoryItem } from '../../../types';

const mockWorkflow: WorkflowHistoryItem = {
  id: 'test-workflow-123',
  workflow_id: 'test-123',
  total_tokens: 50000,
  input_tokens: 30000,
  output_tokens: 10000,
  cache_hit_tokens: 10000,
  cache_miss_tokens: 20000,
  cache_efficiency_percent: 20,
  cost_per_token: 0.00003,
  // ... other required fields
} as WorkflowHistoryItem;

describe('TokenAnalysisSection', () => {
  it('renders section title', () => {
    render(<TokenAnalysisSection workflow={mockWorkflow} />);
    expect(screen.getByText(/Token Usage & Cache Performance/)).toBeInTheDocument();
  });

  it('displays cache efficiency metrics', () => {
    render(<TokenAnalysisSection workflow={mockWorkflow} />);

    expect(screen.getByText('Cache Hits')).toBeInTheDocument();
    expect(screen.getByText('10,000')).toBeInTheDocument();
    expect(screen.getByText('Cache Misses')).toBeInTheDocument();
    expect(screen.getByText('20,000')).toBeInTheDocument();
  });

  it('calculates and displays cache savings', () => {
    render(<TokenAnalysisSection workflow={mockWorkflow} />);

    // Cache savings = cache_hit_tokens * (standard_cost - cache_cost)
    // = 10000 * (0.00003 - 0.000003) = 0.27
    expect(screen.getByText(/Savings/)).toBeInTheDocument();
  });

  it('shows cache details table', () => {
    render(<TokenAnalysisSection workflow={mockWorkflow} />);

    expect(screen.getByText('Input Tokens')).toBeInTheDocument();
    expect(screen.getByText('Output Tokens')).toBeInTheDocument();
    expect(screen.getByText('Cache Read Tokens')).toBeInTheDocument();
  });

  it('returns null when no token data available', () => {
    const noTokenWorkflow = {
      ...mockWorkflow,
      total_tokens: 0
    };

    const { container } = render(<TokenAnalysisSection workflow={noTokenWorkflow} />);
    expect(container.firstChild).toBeNull();
  });

  it('does not render cache section when efficiency is 0', () => {
    const noCacheWorkflow = {
      ...mockWorkflow,
      cache_efficiency_percent: 0,
      cache_hit_tokens: 0
    };

    render(<TokenAnalysisSection workflow={noCacheWorkflow} />);

    expect(screen.queryByText('Cache Efficiency')).not.toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] TokenAnalysisSection component created
- [ ] Cache savings calculated correctly
- [ ] Tests pass with >80% coverage
- [ ] Component renders null when no token data
- [ ] UI matches original appearance

**Verification Commands:**
```bash
cd app/client
npm run test -- TokenAnalysisSection.test.tsx
npm run typecheck
```

**Status:** Not Started

---

### Workflow 1.5: Extract PerformanceAnalysisSection Component
**Estimated Time:** 1.5 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (lines 450-481)

**Output Files:**
- `app/client/src/components/workflow-history/PerformanceAnalysisSection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { PhaseDurationChart } from '../PhaseDurationChart';
import { formatDuration } from '../../utils/formatters';

/**
 * Performance Analysis Section
 *
 * Displays workflow performance metrics including:
 * - Total duration
 * - Phase duration breakdown
 * - Phase duration chart
 *
 * @param props - Workflow section props
 */
export function PerformanceAnalysisSection({ workflow }: WorkflowSectionProps) {
  const hasDurationData = workflow.duration_seconds > 0;

  if (!hasDurationData) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        ⏱️ Performance Analysis
      </h3>

      {/* Duration Summary */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-600">Total Duration</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatDuration(workflow.duration_seconds)}
            </div>
          </div>
          {workflow.steps_completed > 0 && (
            <div>
              <div className="text-gray-600">Avg Time per Step</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatDuration(Math.round(workflow.duration_seconds / workflow.steps_completed))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Phase Duration Chart */}
      {workflow.phase_durations && Object.keys(workflow.phase_durations).length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <PhaseDurationChart phaseDurations={workflow.phase_durations} />
        </div>
      )}
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/PerformanceAnalysisSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PerformanceAnalysisSection } from '../PerformanceAnalysisSection';
import type { WorkflowHistoryItem } from '../../../types';

const mockWorkflow: WorkflowHistoryItem = {
  id: 'test-workflow-123',
  workflow_id: 'test-123',
  duration_seconds: 1800,
  steps_completed: 10,
  phase_durations: {
    'Phase 1': 600,
    'Phase 2': 800,
    'Phase 3': 400
  },
  // ... other required fields
} as WorkflowHistoryItem;

describe('PerformanceAnalysisSection', () => {
  it('renders section title', () => {
    render(<PerformanceAnalysisSection workflow={mockWorkflow} />);
    expect(screen.getByText(/Performance Analysis/)).toBeInTheDocument();
  });

  it('displays total duration formatted correctly', () => {
    render(<PerformanceAnalysisSection workflow={mockWorkflow} />);

    expect(screen.getByText('Total Duration')).toBeInTheDocument();
    expect(screen.getByText('30m 0s')).toBeInTheDocument();
  });

  it('calculates and displays average time per step', () => {
    render(<PerformanceAnalysisSection workflow={mockWorkflow} />);

    expect(screen.getByText('Avg Time per Step')).toBeInTheDocument();
    expect(screen.getByText('3m 0s')).toBeInTheDocument();
  });

  it('returns null when no duration data', () => {
    const noDurationWorkflow = {
      ...mockWorkflow,
      duration_seconds: 0
    };

    const { container } = render(<PerformanceAnalysisSection workflow={noDurationWorkflow} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders phase duration chart when data available', () => {
    render(<PerformanceAnalysisSection workflow={mockWorkflow} />);

    // Chart component should be rendered
    expect(screen.getByText(/Performance Analysis/)).toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] PerformanceAnalysisSection component created
- [ ] Duration formatting uses formatDuration utility
- [ ] Tests pass with >80% coverage
- [ ] Returns null when no duration data
- [ ] UI matches original appearance

**Verification Commands:**
```bash
cd app/client
npm run test -- PerformanceAnalysisSection.test.tsx
npm run typecheck
```

**Status:** Not Started

---

### Workflow 1.6: Extract ErrorAnalysisSection Component
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Output Files:**
- `app/client/src/components/workflow-history/ErrorAnalysisSection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';

/**
 * Error Analysis Section
 *
 * Displays error information and retry analysis:
 * - Error message (if any)
 * - Retry count
 * - Retry cost impact
 *
 * @param props - Workflow section props
 */
export function ErrorAnalysisSection({ workflow }: WorkflowSectionProps) {
  const hasError = workflow.error_message || workflow.retry_count > 0;

  if (!hasError) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        ⚠️ Error Analysis
      </h3>

      {/* Error Message */}
      {workflow.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="text-sm font-medium text-red-700 mb-2">Error Message:</div>
          <div className="text-sm text-red-900 font-mono whitespace-pre-wrap">
            {workflow.error_message}
          </div>
        </div>
      )}

      {/* Retry Information */}
      {workflow.retry_count > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="text-sm font-medium text-orange-700 mb-2">
            Retry Information
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-600">Retry Count</div>
              <div className="font-semibold text-orange-700">
                {workflow.retry_count} {workflow.retry_count === 1 ? 'retry' : 'retries'}
              </div>
            </div>
            {workflow.actual_cost_total > workflow.estimated_cost_total && (
              <div>
                <div className="text-gray-600">Additional Cost from Retries</div>
                <div className="font-semibold text-orange-700">
                  ~${(workflow.actual_cost_total - workflow.estimated_cost_total).toFixed(4)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/ErrorAnalysisSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorAnalysisSection } from '../ErrorAnalysisSection';
import type { WorkflowHistoryItem } from '../../../types';

describe('ErrorAnalysisSection', () => {
  it('renders error message when present', () => {
    const workflowWithError = {
      id: 'test-123',
      error_message: 'API rate limit exceeded',
      retry_count: 0
    } as WorkflowHistoryItem;

    render(<ErrorAnalysisSection workflow={workflowWithError} />);

    expect(screen.getByText('Error Message:')).toBeInTheDocument();
    expect(screen.getByText('API rate limit exceeded')).toBeInTheDocument();
  });

  it('renders retry information when retries occurred', () => {
    const workflowWithRetries = {
      id: 'test-123',
      retry_count: 3,
      estimated_cost_total: 1.0,
      actual_cost_total: 1.5
    } as WorkflowHistoryItem;

    render(<ErrorAnalysisSection workflow={workflowWithRetries} />);

    expect(screen.getByText('Retry Information')).toBeInTheDocument();
    expect(screen.getByText('3 retries')).toBeInTheDocument();
    expect(screen.getByText(/Additional Cost from Retries/)).toBeInTheDocument();
  });

  it('returns null when no errors or retries', () => {
    const cleanWorkflow = {
      id: 'test-123',
      error_message: null,
      retry_count: 0
    } as WorkflowHistoryItem;

    const { container } = render(<ErrorAnalysisSection workflow={cleanWorkflow} />);
    expect(container.firstChild).toBeNull();
  });

  it('uses singular "retry" for retry_count === 1', () => {
    const workflowWithOneRetry = {
      id: 'test-123',
      retry_count: 1
    } as WorkflowHistoryItem;

    render(<ErrorAnalysisSection workflow={workflowWithOneRetry} />);
    expect(screen.getByText('1 retry')).toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] ErrorAnalysisSection component created
- [ ] Renders error message correctly
- [ ] Displays retry information when applicable
- [ ] Returns null when no errors/retries
- [ ] Tests pass with >80% coverage

**Verification Commands:**
```bash
cd app/client
npm run test -- ErrorAnalysisSection.test.tsx
```

**Status:** Not Started

---

### Workflow 1.7: Extract ResourceUsageSection Component
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Output Files:**
- `app/client/src/components/workflow-history/ResourceUsageSection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { formatNumber } from '../../utils/formatters';

/**
 * Resource Usage Section
 *
 * Displays resource consumption metrics:
 * - API calls count
 * - Steps completed
 * - Memory usage (if available)
 * - Other resource metrics
 *
 * @param props - Workflow section props
 */
export function ResourceUsageSection({ workflow }: WorkflowSectionProps) {
  const hasResourceData = workflow.steps_completed > 0 || workflow.api_calls > 0;

  if (!hasResourceData) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        📊 Resource Usage
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        {workflow.steps_completed > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-gray-600 mb-1">Steps Completed</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatNumber(workflow.steps_completed)}
            </div>
          </div>
        )}

        {workflow.api_calls > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-gray-600 mb-1">API Calls</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatNumber(workflow.api_calls)}
            </div>
          </div>
        )}

        {workflow.tools_used && workflow.tools_used.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-gray-600 mb-1">Tools Used</div>
            <div className="text-lg font-semibold text-gray-900">
              {workflow.tools_used.length}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {workflow.tools_used.slice(0, 3).join(', ')}
              {workflow.tools_used.length > 3 && '...'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/ResourceUsageSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResourceUsageSection } from '../ResourceUsageSection';
import type { WorkflowHistoryItem } from '../../../types';

describe('ResourceUsageSection', () => {
  it('displays steps completed', () => {
    const workflow = {
      id: 'test-123',
      steps_completed: 25,
      api_calls: 50
    } as WorkflowHistoryItem;

    render(<ResourceUsageSection workflow={workflow} />);

    expect(screen.getByText('Steps Completed')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('displays API calls', () => {
    const workflow = {
      id: 'test-123',
      steps_completed: 0,
      api_calls: 100
    } as WorkflowHistoryItem;

    render(<ResourceUsageSection workflow={workflow} />);

    expect(screen.getByText('API Calls')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('displays tools used with truncation', () => {
    const workflow = {
      id: 'test-123',
      steps_completed: 10,
      api_calls: 20,
      tools_used: ['Read', 'Write', 'Bash', 'Grep', 'Edit']
    } as WorkflowHistoryItem;

    render(<ResourceUsageSection workflow={workflow} />);

    expect(screen.getByText('Tools Used')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText(/Read, Write, Bash\.\.\./)).toBeInTheDocument();
  });

  it('returns null when no resource data', () => {
    const workflow = {
      id: 'test-123',
      steps_completed: 0,
      api_calls: 0
    } as WorkflowHistoryItem;

    const { container } = render(<ResourceUsageSection workflow={workflow} />);
    expect(container.firstChild).toBeNull();
  });
});
```

**Acceptance Criteria:**
- [ ] ResourceUsageSection component created
- [ ] Displays all resource metrics
- [ ] Tests pass with >80% coverage
- [ ] Returns null when no resource data

**Verification Commands:**
```bash
cd app/client
npm run test -- ResourceUsageSection.test.tsx
```

**Status:** Not Started

---

### Workflow 1.8: Extract WorkflowJourneySection Component
**Estimated Time:** 1.5 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Output Files:**
- `app/client/src/components/workflow-history/WorkflowJourneySection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { formatDate } from '../../utils/formatters';

/**
 * Workflow Journey Section
 *
 * Displays workflow timeline:
 * - Started at timestamp
 * - Completed at timestamp
 * - Duration
 * - Status transitions (if available)
 *
 * @param props - Workflow section props
 */
export function WorkflowJourneySection({ workflow }: WorkflowSectionProps) {
  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        🗺️ Workflow Journey
      </h3>

      <div className="relative">
        {/* Timeline */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300"></div>

        {/* Started */}
        <div className="relative pl-12 pb-6">
          <div className="absolute left-2.5 top-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white"></div>
          <div className="text-sm">
            <div className="font-semibold text-gray-700">Started</div>
            <div className="text-gray-600">{formatDate(workflow.started_at)}</div>
          </div>
        </div>

        {/* Completed */}
        {workflow.completed_at && (
          <div className="relative pl-12">
            <div className="absolute left-2.5 top-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
            <div className="text-sm">
              <div className="font-semibold text-gray-700">
                {workflow.status === 'completed' ? 'Completed' : workflow.status === 'failed' ? 'Failed' : 'Stopped'}
              </div>
              <div className="text-gray-600">{formatDate(workflow.completed_at)}</div>
            </div>
          </div>
        )}

        {/* In Progress */}
        {!workflow.completed_at && workflow.status === 'running' && (
          <div className="relative pl-12">
            <div className="absolute left-2.5 top-1 w-3 h-3 bg-yellow-500 rounded-full border-2 border-white animate-pulse"></div>
            <div className="text-sm">
              <div className="font-semibold text-yellow-700">In Progress...</div>
              <div className="text-gray-600">Currently executing</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/WorkflowJourneySection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowJourneySection } from '../WorkflowJourneySection';
import type { WorkflowHistoryItem } from '../../../types';

describe('WorkflowJourneySection', () => {
  it('displays started timestamp', () => {
    const workflow = {
      id: 'test-123',
      started_at: '2025-01-15T10:00:00Z',
      status: 'running'
    } as WorkflowHistoryItem;

    render(<WorkflowJourneySection workflow={workflow} />);

    expect(screen.getByText('Started')).toBeInTheDocument();
  });

  it('displays completed timestamp for completed workflow', () => {
    const workflow = {
      id: 'test-123',
      started_at: '2025-01-15T10:00:00Z',
      completed_at: '2025-01-15T10:30:00Z',
      status: 'completed'
    } as WorkflowHistoryItem;

    render(<WorkflowJourneySection workflow={workflow} />);

    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('shows "In Progress..." for running workflow', () => {
    const workflow = {
      id: 'test-123',
      started_at: '2025-01-15T10:00:00Z',
      completed_at: null,
      status: 'running'
    } as WorkflowHistoryItem;

    render(<WorkflowJourneySection workflow={workflow} />);

    expect(screen.getByText('In Progress...')).toBeInTheDocument();
  });

  it('shows "Failed" for failed workflow', () => {
    const workflow = {
      id: 'test-123',
      started_at: '2025-01-15T10:00:00Z',
      completed_at: '2025-01-15T10:15:00Z',
      status: 'failed'
    } as WorkflowHistoryItem;

    render(<WorkflowJourneySection workflow={workflow} />);

    expect(screen.getByText('Failed')).toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] WorkflowJourneySection component created
- [ ] Timeline displays correctly
- [ ] Tests pass with >80% coverage
- [ ] Animations work for in-progress workflows

**Verification Commands:**
```bash
cd app/client
npm run test -- WorkflowJourneySection.test.tsx
```

**Status:** Not Started

---

### Workflow 1.9: Extract EfficiencyScoresSection Component
**Estimated Time:** 1.5 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Output Files:**
- `app/client/src/components/workflow-history/EfficiencyScoresSection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { ScoreCard } from '../ScoreCard';

/**
 * Efficiency Scores Section
 *
 * Displays workflow quality scores:
 * - NL Input Clarity Score
 * - Cost Efficiency Score
 * - Performance Score
 * - Overall Quality Score
 *
 * @param props - Workflow section props
 */
export function EfficiencyScoresSection({ workflow }: WorkflowSectionProps) {
  const hasScores =
    workflow.nl_input_clarity_score > 0 ||
    workflow.cost_efficiency_score > 0 ||
    workflow.performance_score > 0 ||
    workflow.overall_quality_score > 0;

  if (!hasScores) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        📈 Efficiency Scores
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {workflow.nl_input_clarity_score > 0 && (
          <ScoreCard
            title="NL Input Clarity"
            score={workflow.nl_input_clarity_score}
            description="Quality of natural language input"
          />
        )}

        {workflow.cost_efficiency_score > 0 && (
          <ScoreCard
            title="Cost Efficiency"
            score={workflow.cost_efficiency_score}
            description="Cost optimization effectiveness"
          />
        )}

        {workflow.performance_score > 0 && (
          <ScoreCard
            title="Performance"
            score={workflow.performance_score}
            description="Execution speed and efficiency"
          />
        )}

        {workflow.overall_quality_score > 0 && (
          <ScoreCard
            title="Overall Quality"
            score={workflow.overall_quality_score}
            description="Combined quality metric"
            highlighted
          />
        )}
      </div>
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/EfficiencyScoresSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EfficiencyScoresSection } from '../EfficiencyScoresSection';
import type { WorkflowHistoryItem } from '../../../types';

describe('EfficiencyScoresSection', () => {
  it('displays all score cards when scores available', () => {
    const workflow = {
      id: 'test-123',
      nl_input_clarity_score: 85,
      cost_efficiency_score: 90,
      performance_score: 75,
      overall_quality_score: 83
    } as WorkflowHistoryItem;

    render(<EfficiencyScoresSection workflow={workflow} />);

    expect(screen.getByText('NL Input Clarity')).toBeInTheDocument();
    expect(screen.getByText('Cost Efficiency')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Overall Quality')).toBeInTheDocument();
  });

  it('returns null when no scores available', () => {
    const workflow = {
      id: 'test-123',
      nl_input_clarity_score: 0,
      cost_efficiency_score: 0,
      performance_score: 0,
      overall_quality_score: 0
    } as WorkflowHistoryItem;

    const { container } = render(<EfficiencyScoresSection workflow={workflow} />);
    expect(container.firstChild).toBeNull();
  });

  it('only displays scores that are greater than 0', () => {
    const workflow = {
      id: 'test-123',
      nl_input_clarity_score: 85,
      cost_efficiency_score: 0,
      performance_score: 75,
      overall_quality_score: 0
    } as WorkflowHistoryItem;

    render(<EfficiencyScoresSection workflow={workflow} />);

    expect(screen.getByText('NL Input Clarity')).toBeInTheDocument();
    expect(screen.queryByText('Cost Efficiency')).not.toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.queryByText('Overall Quality')).not.toBeInTheDocument();
  });
});
```

**Acceptance Criteria:**
- [ ] EfficiencyScoresSection component created
- [ ] Only non-zero scores displayed
- [ ] Tests pass with >80% coverage
- [ ] Returns null when no scores

**Verification Commands:**
```bash
cd app/client
npm run test -- EfficiencyScoresSection.test.tsx
```

**Status:** Not Started

---

### Workflow 1.10: Extract InsightsSection Component
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 1.1, 1.2

**Output Files:**
- `app/client/src/components/workflow-history/InsightsSection.tsx` (new)

**Implementation:**

```typescript
import type { WorkflowSectionProps } from './types';
import { SimilarWorkflowsComparison } from '../SimilarWorkflowsComparison';

/**
 * Insights Section
 *
 * Displays workflow insights and recommendations:
 * - Similar workflows comparison
 * - Optimization suggestions
 * - Pattern detection results
 *
 * @param props - Workflow section props
 */
export function InsightsSection({ workflow }: WorkflowSectionProps) {
  const hasSimilarWorkflows =
    workflow.similar_workflows && workflow.similar_workflows.length > 0;

  const hasInsights =
    hasSimilarWorkflows ||
    workflow.optimization_suggestions ||
    workflow.detected_patterns;

  if (!hasInsights) {
    return null;
  }

  return (
    <div className="pb-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        💡 Insights & Recommendations
      </h3>

      {/* Similar Workflows */}
      {hasSimilarWorkflows && (
        <div className="mb-6">
          <SimilarWorkflowsComparison
            currentWorkflow={workflow}
            similarWorkflows={workflow.similar_workflows}
          />
        </div>
      )}

      {/* Optimization Suggestions */}
      {workflow.optimization_suggestions && workflow.optimization_suggestions.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">
            Optimization Suggestions
          </h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-yellow-900">
            {workflow.optimization_suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Detected Patterns */}
      {workflow.detected_patterns && workflow.detected_patterns.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-purple-800 mb-2">
            Detected Patterns
          </h4>
          <div className="flex flex-wrap gap-2">
            {workflow.detected_patterns.map((pattern, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
              >
                {pattern}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Test File:**

```typescript
// app/client/src/components/workflow-history/__tests__/InsightsSection.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InsightsSection } from '../InsightsSection';
import type { WorkflowHistoryItem } from '../../../types';

describe('InsightsSection', () => {
  it('displays similar workflows comparison', () => {
    const workflow = {
      id: 'test-123',
      similar_workflows: [
        { id: 'similar-1', similarity_score: 0.85 },
        { id: 'similar-2', similarity_score: 0.75 }
      ]
    } as WorkflowHistoryItem;

    render(<InsightsSection workflow={workflow} />);

    expect(screen.getByText(/Insights & Recommendations/)).toBeInTheDocument();
  });

  it('displays optimization suggestions', () => {
    const workflow = {
      id: 'test-123',
      optimization_suggestions: [
        'Consider using cache to reduce API calls',
        'Break down complex tasks into smaller steps'
      ]
    } as WorkflowHistoryItem;

    render(<InsightsSection workflow={workflow} />);

    expect(screen.getByText('Optimization Suggestions')).toBeInTheDocument();
    expect(screen.getByText(/cache to reduce API calls/)).toBeInTheDocument();
  });

  it('displays detected patterns', () => {
    const workflow = {
      id: 'test-123',
      detected_patterns: ['file-read-write', 'git-commit', 'test-execution']
    } as WorkflowHistoryItem;

    render(<InsightsSection workflow={workflow} />);

    expect(screen.getByText('Detected Patterns')).toBeInTheDocument();
    expect(screen.getByText('file-read-write')).toBeInTheDocument();
    expect(screen.getByText('git-commit')).toBeInTheDocument();
  });

  it('returns null when no insights available', () => {
    const workflow = {
      id: 'test-123',
      similar_workflows: [],
      optimization_suggestions: [],
      detected_patterns: []
    } as WorkflowHistoryItem;

    const { container } = render(<InsightsSection workflow={workflow} />);
    expect(container.firstChild).toBeNull();
  });
});
```

**Acceptance Criteria:**
- [ ] InsightsSection component created
- [ ] Similar workflows comparison integrated
- [ ] Tests pass with >80% coverage
- [ ] Returns null when no insights

**Verification Commands:**
```bash
cd app/client
npm run test -- InsightsSection.test.tsx
```

**Status:** Not Started

---

### Workflow 1.11: Update Main WorkflowHistoryCard to Use Section Components
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflows 1.3-1.10

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx`

**Output Files:**
- `app/client/src/components/workflow-history/WorkflowHistoryCard.tsx` (moved and refactored)

**Tasks:**
1. Move WorkflowHistoryCard.tsx to workflow-history/ directory
2. Update imports to use section components
3. Remove all extracted helper functions (now in utils/)
4. Remove all extracted sections (now separate components)
5. Keep only main card structure and toggle logic
6. Update all imports in parent components

**Implementation:**

```typescript
// app/client/src/components/workflow-history/WorkflowHistoryCard.tsx
import { useState } from 'react';
import type { WorkflowHistoryItem } from '../../types';
import { StatusBadge } from '../StatusBadge';
import { formatCost, formatNumber, formatDate } from '../../utils/formatters';
import { getClassificationColor } from '../../utils/workflowHelpers';

// Section components
import { CostEconomicsSection } from './CostEconomicsSection';
import { TokenAnalysisSection } from './TokenAnalysisSection';
import { PerformanceAnalysisSection } from './PerformanceAnalysisSection';
import { ErrorAnalysisSection } from './ErrorAnalysisSection';
import { ResourceUsageSection } from './ResourceUsageSection';
import { WorkflowJourneySection } from './WorkflowJourneySection';
import { EfficiencyScoresSection } from './EfficiencyScoresSection';
import { InsightsSection } from './InsightsSection';

interface WorkflowHistoryCardProps {
  workflow: WorkflowHistoryItem;
}

/**
 * Workflow History Card
 *
 * Main component for displaying workflow execution history.
 * Renders summary information and expandable details sections.
 *
 * @param props - Component props
 */
export function WorkflowHistoryCard({ workflow }: WorkflowHistoryCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 border border-gray-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-semibold text-gray-900">
              #{workflow.issue_number} {workflow.nl_input_text?.substring(0, 60)}
              {workflow.nl_input_text && workflow.nl_input_text.length > 60 && '...'}
            </h2>
            <StatusBadge status={workflow.status} />
            {workflow.classification && (
              <span className={`px-2 py-1 text-xs font-medium rounded border ${getClassificationColor(workflow.classification)}`}>
                {workflow.classification}
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500">
            Workflow ID: {workflow.workflow_id}
          </div>
        </div>
      </div>

      {/* Cost & Token Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
        {workflow.actual_cost_total > 0 && (
          <div>
            <div className="text-gray-600">Actual Cost</div>
            <div className="font-semibold text-green-600">{formatCost(workflow.actual_cost_total)}</div>
          </div>
        )}
        {workflow.total_tokens > 0 && (
          <div>
            <div className="text-gray-600">Total Tokens</div>
            <div className="font-medium text-gray-900">{formatNumber(workflow.total_tokens)}</div>
          </div>
        )}
        {workflow.cache_efficiency_percent > 0 && (
          <div>
            <div className="text-gray-600">Cache Efficiency</div>
            <div className="font-medium text-blue-600">{workflow.cache_efficiency_percent.toFixed(1)}%</div>
          </div>
        )}
        {workflow.retry_count > 0 && (
          <div>
            <div className="text-gray-600">Retries</div>
            <div className="font-medium text-orange-600">{workflow.retry_count}</div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {workflow.error_message && (
        <div className="mb-4">
          <div className="text-sm font-medium text-red-700 mb-1">Error:</div>
          <div className="text-sm text-red-900 bg-red-50 rounded p-3 border border-red-200">
            {workflow.error_message}
          </div>
        </div>
      )}

      {/* Toggle Details Button */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {showDetails ? '▼ Hide Details' : '▶ Show Details'}
      </button>

      {/* Detailed Information Sections */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-6">
          <CostEconomicsSection workflow={workflow} />
          <TokenAnalysisSection workflow={workflow} />
          <PerformanceAnalysisSection workflow={workflow} />
          <ErrorAnalysisSection workflow={workflow} />
          <ResourceUsageSection workflow={workflow} />
          <WorkflowJourneySection workflow={workflow} />
          <EfficiencyScoresSection workflow={workflow} />
          <InsightsSection workflow={workflow} />
        </div>
      )}
    </div>
  );
}
```

**Migration Tasks:**
1. Update imports in parent components:

```typescript
// Before
import { WorkflowHistoryCard } from './components/WorkflowHistoryCard';

// After
import { WorkflowHistoryCard } from './components/workflow-history';
```

2. Delete old file:
```bash
rm app/client/src/components/WorkflowHistoryCard.tsx
```

**Acceptance Criteria:**
- [ ] WorkflowHistoryCard reduced to <200 lines
- [ ] All sections render correctly
- [ ] Toggle functionality works
- [ ] No visual regressions
- [ ] All imports updated

**Verification Commands:**
```bash
cd app/client
npm run typecheck
npm run build
npm run dev
# Manual: Test workflow history card UI
```

**Status:** Not Started

---

### Workflow 1.12: Create Component Tests and Integration Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.11

**Output Files:**
- `app/client/src/components/workflow-history/__tests__/WorkflowHistoryCard.test.tsx` (new)
- `app/client/src/components/workflow-history/__tests__/integration.test.tsx` (new)

**Tasks:**
1. Write integration test for full WorkflowHistoryCard
2. Test section visibility based on data
3. Test toggle functionality
4. Test responsive layout
5. Visual regression testing setup

**Implementation:**

```typescript
// app/client/src/components/workflow-history/__tests__/WorkflowHistoryCard.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkflowHistoryCard } from '../WorkflowHistoryCard';
import type { WorkflowHistoryItem } from '../../../types';

const fullMockWorkflow: WorkflowHistoryItem = {
  id: 'full-test-workflow',
  workflow_id: 'test-123',
  issue_number: 42,
  nl_input_text: 'Test workflow for comprehensive testing',
  classification: 'feature',
  status: 'completed',
  started_at: '2025-01-15T10:00:00Z',
  completed_at: '2025-01-15T10:30:00Z',
  duration_seconds: 1800,
  estimated_cost_total: 2.0,
  actual_cost_total: 1.5,
  estimated_cost_per_step: 0.2,
  actual_cost_per_step: 0.15,
  total_tokens: 50000,
  input_tokens: 30000,
  output_tokens: 10000,
  cache_hit_tokens: 10000,
  cost_per_token: 0.00003,
  cache_efficiency_percent: 20,
  retry_count: 0,
  error_message: null,
  steps_completed: 10,
  api_calls: 25,
  nl_input_clarity_score: 85,
  cost_efficiency_score: 90,
  performance_score: 75,
  overall_quality_score: 83,
  cost_breakdown: {
    by_phase: {
      'Phase 1': 0.5,
      'Phase 2': 0.7,
      'Phase 3': 0.3
    }
  },
  similar_workflows: [],
  optimization_suggestions: [],
  detected_patterns: []
  // ... all other required fields
} as WorkflowHistoryItem;

describe('WorkflowHistoryCard Integration', () => {
  it('renders workflow summary', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    expect(screen.getByText(/#42/)).toBeInTheDocument();
    expect(screen.getByText(/Test workflow/)).toBeInTheDocument();
    expect(screen.getByText('feature')).toBeInTheDocument();
  });

  it('toggles details section on button click', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    expect(screen.queryByText(/Cost Economics/)).not.toBeInTheDocument();

    fireEvent.click(toggleButton);

    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
    expect(screen.getByText(/Hide Details/)).toBeInTheDocument();
  });

  it('renders all sections when details shown', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    fireEvent.click(toggleButton);

    // Verify all sections render
    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
    expect(screen.getByText(/Token Usage & Cache Performance/)).toBeInTheDocument();
    expect(screen.getByText(/Performance Analysis/)).toBeInTheDocument();
    expect(screen.getByText(/Resource Usage/)).toBeInTheDocument();
    expect(screen.getByText(/Workflow Journey/)).toBeInTheDocument();
    expect(screen.getByText(/Efficiency Scores/)).toBeInTheDocument();
  });

  it('hides sections with no data', () => {
    const minimalWorkflow = {
      ...fullMockWorkflow,
      total_tokens: 0,
      cache_efficiency_percent: 0,
      nl_input_clarity_score: 0,
      cost_efficiency_score: 0,
      performance_score: 0,
      overall_quality_score: 0
    };

    render(<WorkflowHistoryCard workflow={minimalWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    fireEvent.click(toggleButton);

    // Sections with no data should not render
    expect(screen.queryByText(/Token Usage & Cache Performance/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Efficiency Scores/)).not.toBeInTheDocument();
  });

  it('displays error message when present', () => {
    const errorWorkflow = {
      ...fullMockWorkflow,
      error_message: 'API rate limit exceeded'
    };

    render(<WorkflowHistoryCard workflow={errorWorkflow} />);

    expect(screen.getByText('Error:')).toBeInTheDocument();
    expect(screen.getByText('API rate limit exceeded')).toBeInTheDocument();
  });
});
```

**Integration Test:**

```typescript
// app/client/src/components/workflow-history/__tests__/integration.test.tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { WorkflowHistoryCard } from '../WorkflowHistoryCard';
import type { WorkflowHistoryItem } from '../../../types';

describe('WorkflowHistoryCard Visual Regression', () => {
  it('matches snapshot for completed workflow', () => {
    const workflow = {
      // ... full mock workflow
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches snapshot for failed workflow', () => {
    const workflow = {
      // ... failed workflow mock
      status: 'failed',
      error_message: 'Test error'
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches snapshot for running workflow', () => {
    const workflow = {
      // ... running workflow mock
      status: 'running',
      completed_at: null
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

**Visual Regression Testing Notes:**

1. **Setup Chromatic (optional but recommended):**
```bash
npm install --save-dev chromatic
```

2. **Add Storybook stories for each section:**
```typescript
// app/client/src/components/workflow-history/CostEconomicsSection.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { CostEconomicsSection } from './CostEconomicsSection';

const meta: Meta<typeof CostEconomicsSection> = {
  title: 'Workflow History/Cost Economics Section',
  component: CostEconomicsSection,
};

export default meta;
type Story = StoryObj<typeof CostEconomicsSection>;

export const UnderBudget: Story = {
  args: {
    workflow: {
      // ... mock workflow under budget
    }
  }
};

export const OverBudget: Story = {
  args: {
    workflow: {
      // ... mock workflow over budget
    }
  }
};
```

**Acceptance Criteria:**
- [ ] Main WorkflowHistoryCard tests pass
- [ ] Integration tests pass
- [ ] Snapshot tests created
- [ ] Test coverage >80% for all components
- [ ] Visual regression baseline captured

**Verification Commands:**
```bash
cd app/client
npm run test
npm run test:coverage
npm run storybook
# Visual: Compare UI before/after in Storybook
```

**Status:** Not Started

---

## 2. WebSocket Hooks Consolidation (4 workflows)

### Workflow 2.1: Create Generic useWebSocket Hook
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/client/src/hooks/useWebSocket.ts` (analyze patterns)

**Output Files:**
- `app/client/src/hooks/useGenericWebSocket.ts` (new)

**Tasks:**
1. Extract common WebSocket connection logic
2. Create generic hook with configuration interface
3. Implement reconnection with exponential backoff
4. Implement React Query fallback polling
5. Add TypeScript generics for type safety

**Implementation:**

```typescript
// app/client/src/hooks/useGenericWebSocket.ts
import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';

interface WebSocketConfig<T> {
  /** WebSocket endpoint URL */
  endpoint: string;

  /** Message type to filter for */
  messageType: string;

  /** React Query key for fallback polling */
  queryKey: string[];

  /** React Query fetch function for fallback */
  queryFn: () => Promise<T>;

  /** Extract data from WebSocket message */
  dataExtractor: (message: any) => T;

  /** Reconnection configuration */
  reconnection?: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
  };

  /** Polling configuration for fallback */
  polling?: {
    interval?: number;
    enabled?: boolean;
  };
}

/**
 * Generic WebSocket Hook
 *
 * Provides real-time data updates via WebSocket with automatic
 * fallback to React Query polling on connection failure.
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Graceful degradation to polling
 * - TypeScript generic for type safety
 * - Connection state management
 *
 * @template T - Type of data received from WebSocket
 * @param config - WebSocket configuration
 * @returns Data and connection state
 */
export function useGenericWebSocket<T>({
  endpoint,
  messageType,
  queryKey,
  queryFn,
  dataExtractor,
  reconnection = {},
  polling = {}
}: WebSocketConfig<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Reconnection configuration with defaults
  const {
    maxRetries = 5,
    initialDelay = 1000,
    maxDelay = 30000
  } = reconnection;

  // Polling configuration with defaults
  const {
    interval = 5000,
    enabled = true
  } = polling;

  /**
   * Calculate exponential backoff delay
   */
  const getReconnectDelay = (): number => {
    const delay = initialDelay * Math.pow(2, reconnectAttemptsRef.current);
    return Math.min(delay, maxDelay);
  };

  /**
   * Connect to WebSocket
   */
  const connect = () => {
    try {
      const ws = new WebSocket(endpoint);

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${endpoint}`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === messageType) {
            const extractedData = dataExtractor(message);
            setData(extractedData);
          }
        } catch (err) {
          console.error('[WebSocket] Error parsing message:', err);
          setError(err instanceof Error ? err : new Error('Failed to parse message'));
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setError(new Error('WebSocket connection error'));
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);

        // Attempt reconnection if not exceeded max retries
        if (reconnectAttemptsRef.current < maxRetries) {
          const delay = getReconnectDelay();
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxRetries})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          console.log('[WebSocket] Max reconnection attempts reached. Falling back to polling.');
          setError(new Error('WebSocket connection failed. Using polling fallback.'));
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WebSocket] Connection error:', err);
      setError(err instanceof Error ? err : new Error('Failed to connect'));
    }
  };

  /**
   * Disconnect from WebSocket
   */
  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  };

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [endpoint]);

  // Fallback to React Query polling when WebSocket disconnected
  const { data: fallbackData } = useQuery({
    queryKey,
    queryFn,
    enabled: enabled && !isConnected,
    refetchInterval: isConnected ? false : interval,
    staleTime: interval,
  });

  // Use fallback data when WebSocket not connected
  useEffect(() => {
    if (fallbackData && !isConnected) {
      setData(fallbackData);
    }
  }, [fallbackData, isConnected]);

  return {
    data,
    isConnected,
    error,
    reconnect: connect,
    disconnect
  };
}
```

**Test File:**

```typescript
// app/client/src/hooks/__tests__/useGenericWebSocket.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGenericWebSocket } from '../useGenericWebSocket';

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  send(data: string) {}
  close() {
    if (this.onclose) this.onclose();
  }
}

describe('useGenericWebSocket', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    global.WebSocket = MockWebSocket as any;
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [],
        dataExtractor: (msg) => msg.data
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('receives and processes messages', async () => {
    const mockData = [{ id: 1, name: 'Test' }];

    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => [],
        dataExtractor: (msg) => msg.data
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate message
    const ws = global.WebSocket as any;
    if (ws.onmessage) {
      ws.onmessage({
        data: JSON.stringify({
          type: 'test_update',
          data: mockData
        })
      });
    }

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });
  });

  it('falls back to polling when WebSocket fails', async () => {
    const mockFallbackData = [{ id: 2, name: 'Fallback' }];

    // Mock WebSocket to fail
    global.WebSocket = class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          if (this.onerror) this.onerror(new Event('error'));
          if (this.onclose) this.onclose();
        }, 0);
      }
    } as any;

    const { result } = renderHook(
      () => useGenericWebSocket({
        endpoint: 'ws://localhost:8000/test',
        messageType: 'test_update',
        queryKey: ['test'],
        queryFn: async () => mockFallbackData,
        dataExtractor: (msg) => msg.data,
        polling: { interval: 100 }
      }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockFallbackData);
    }, { timeout: 3000 });
  });
});
```

**Acceptance Criteria:**
- [ ] Generic hook created with TypeScript generics
- [ ] Reconnection with exponential backoff works
- [ ] Fallback to polling when WebSocket fails
- [ ] Tests pass with >80% coverage
- [ ] No memory leaks from WebSocket connections

**Verification Commands:**
```bash
cd app/client
npm run test -- useGenericWebSocket.test.ts
npm run typecheck
```

**Status:** Not Started

---

### Workflow 2.2: Migrate useWorkflowsWebSocket to Generic Hook
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/client/src/hooks/useWebSocket.ts` (useWorkflowsWebSocket function)
- `app/client/src/hooks/useGenericWebSocket.ts`

**Output Files:**
- `app/client/src/hooks/useWorkflowsWebSocket.ts` (new, refactored)

**Implementation:**

```typescript
// app/client/src/hooks/useWorkflowsWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { Workflow } from '../types';

/**
 * WebSocket hook for real-time workflow updates
 *
 * Connects to /ws/workflows endpoint and receives workflow list updates.
 * Falls back to REST API polling if WebSocket connection fails.
 *
 * @returns Workflows data and connection state
 */
export function useWorkflowsWebSocket() {
  return useGenericWebSocket<Workflow[]>({
    endpoint: `ws://${window.location.host}/ws/workflows`,
    messageType: 'workflows_update',
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await fetch('/api/workflows');
      if (!response.ok) {
        throw new Error('Failed to fetch workflows');
      }
      const data = await response.json();
      return data.workflows || [];
    },
    dataExtractor: (message) => message.data,
    reconnection: {
      maxRetries: 5,
      initialDelay: 1000,
      maxDelay: 30000
    },
    polling: {
      interval: 5000,
      enabled: true
    }
  });
}
```

**Test File:**

```typescript
// app/client/src/hooks/__tests__/useWorkflowsWebSocket.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkflowsWebSocket } from '../useWorkflowsWebSocket';

describe('useWorkflowsWebSocket', () => {
  it('connects to workflows WebSocket endpoint', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('fetches workflows via REST API as fallback', async () => {
    const mockWorkflows = [
      { id: '1', name: 'Workflow 1', status: 'running' },
      { id: '2', name: 'Workflow 2', status: 'completed' }
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ workflows: mockWorkflows })
    });

    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockWorkflows);
    });
  });
});
```

**Acceptance Criteria:**
- [ ] useWorkflowsWebSocket refactored to use generic hook
- [ ] Reduced from ~81 lines to ~30 lines
- [ ] Tests pass
- [ ] Functionality unchanged
- [ ] Type safety maintained

**Verification Commands:**
```bash
cd app/client
npm run test -- useWorkflowsWebSocket.test.ts
npm run typecheck
npm run dev
# Manual: Verify workflows list updates in real-time
```

**Status:** Not Started

---

### Workflow 2.3: Migrate useRoutesWebSocket and useWorkflowHistoryWebSocket
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 2.1

**Output Files:**
- `app/client/src/hooks/useRoutesWebSocket.ts` (new, refactored)
- `app/client/src/hooks/useWorkflowHistoryWebSocket.ts` (new, refactored)

**Implementation - useRoutesWebSocket.ts:**

```typescript
// app/client/src/hooks/useRoutesWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { Route } from '../types';

/**
 * WebSocket hook for real-time routes updates
 *
 * @returns Routes data and connection state
 */
export function useRoutesWebSocket() {
  return useGenericWebSocket<Route[]>({
    endpoint: `ws://${window.location.host}/ws/routes`,
    messageType: 'routes_update',
    queryKey: ['routes'],
    queryFn: async () => {
      const response = await fetch('/api/routes');
      if (!response.ok) {
        throw new Error('Failed to fetch routes');
      }
      const data = await response.json();
      return data.routes || [];
    },
    dataExtractor: (message) => message.data,
  });
}
```

**Implementation - useWorkflowHistoryWebSocket.ts:**

```typescript
// app/client/src/hooks/useWorkflowHistoryWebSocket.ts
import { useGenericWebSocket } from './useGenericWebSocket';
import type { WorkflowHistoryResponse } from '../types';

/**
 * WebSocket hook for real-time workflow history updates
 *
 * @returns Workflow history data and connection state
 */
export function useWorkflowHistoryWebSocket() {
  return useGenericWebSocket<WorkflowHistoryResponse>({
    endpoint: `ws://${window.location.host}/ws/workflow-history`,
    messageType: 'workflow_history_update',
    queryKey: ['workflowHistory'],
    queryFn: async () => {
      const response = await fetch('/api/workflow-history?limit=50');
      if (!response.ok) {
        throw new Error('Failed to fetch workflow history');
      }
      return await response.json();
    },
    dataExtractor: (message) => message.data,
  });
}
```

**Update useWebSocket.ts Index:**

```typescript
// app/client/src/hooks/useWebSocket.ts
/**
 * WebSocket Hooks
 *
 * Consolidated exports for all WebSocket hooks.
 * All hooks use the generic useGenericWebSocket implementation.
 */

export { useWorkflowsWebSocket } from './useWorkflowsWebSocket';
export { useRoutesWebSocket } from './useRoutesWebSocket';
export { useWorkflowHistoryWebSocket } from './useWorkflowHistoryWebSocket';
export { useGenericWebSocket } from './useGenericWebSocket';

// Re-export types
export type { WebSocketConfig } from './useGenericWebSocket';
```

**Acceptance Criteria:**
- [ ] useRoutesWebSocket refactored
- [ ] useWorkflowHistoryWebSocket refactored
- [ ] Total code reduced from 275 lines to ~80 lines
- [ ] All tests pass
- [ ] Real-time updates work correctly

**Verification Commands:**
```bash
cd app/client
npm run test -- useWebSocket
npm run typecheck
npm run dev
# Manual: Verify all real-time updates work
```

**Status:** Not Started

---

### Workflow 2.4: Create Tests and Cleanup Old Code
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflows 2.2, 2.3

**Tasks:**
1. Create comprehensive integration tests
2. Test all three WebSocket hooks together
3. Test reconnection scenarios
4. Test fallback polling
5. Delete old duplicated code
6. Update documentation

**Integration Test:**

```typescript
// app/client/src/hooks/__tests__/webSocketIntegration.test.ts
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useWorkflowsWebSocket,
  useRoutesWebSocket,
  useWorkflowHistoryWebSocket
} from '../useWebSocket';

describe('WebSocket Hooks Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('all hooks can connect simultaneously', async () => {
    const workflows = renderHook(() => useWorkflowsWebSocket(), { wrapper });
    const routes = renderHook(() => useRoutesWebSocket(), { wrapper });
    const history = renderHook(() => useWorkflowHistoryWebSocket(), { wrapper });

    await waitFor(() => {
      expect(workflows.result.current.isConnected).toBe(true);
      expect(routes.result.current.isConnected).toBe(true);
      expect(history.result.current.isConnected).toBe(true);
    });
  });

  it('all hooks fall back to polling on connection failure', async () => {
    // Mock WebSocket to fail
    global.WebSocket = class {
      constructor() {
        setTimeout(() => {
          if (this.onerror) this.onerror(new Event('error'));
          if (this.onclose) this.onclose();
        }, 0);
      }
    } as any;

    const workflows = renderHook(() => useWorkflowsWebSocket(), { wrapper });

    await waitFor(() => {
      expect(workflows.result.current.data).not.toBeNull();
      expect(workflows.result.current.isConnected).toBe(false);
    }, { timeout: 3000 });
  });
});
```

**Documentation Update:**

```markdown
// app/client/src/hooks/README.md

# WebSocket Hooks

## Overview

This directory contains WebSocket hooks for real-time data updates. All hooks use a unified `useGenericWebSocket` implementation that provides:

- Automatic reconnection with exponential backoff
- Graceful degradation to REST API polling on connection failure
- Type-safe data handling
- Consistent error handling

## Available Hooks

### `useWorkflowsWebSocket()`

Connects to `/ws/workflows` for real-time workflow list updates.

```typescript
const { data, isConnected, error } = useWorkflowsWebSocket();
```

### `useRoutesWebSocket()`

Connects to `/ws/routes` for real-time API routes updates.

```typescript
const { data, isConnected } = useRoutesWebSocket();
```

### `useWorkflowHistoryWebSocket()`

Connects to `/ws/workflow-history` for real-time workflow history updates.

```typescript
const { data, isConnected } = useWorkflowHistoryWebSocket();
```

## Creating Custom WebSocket Hooks

Use `useGenericWebSocket` to create new WebSocket hooks:

```typescript
import { useGenericWebSocket } from './useGenericWebSocket';
import type { MyDataType } from '../types';

export function useMyWebSocket() {
  return useGenericWebSocket<MyDataType>({
    endpoint: 'ws://localhost:8000/ws/my-endpoint',
    messageType: 'my_update',
    queryKey: ['myData'],
    queryFn: async () => {
      const response = await fetch('/api/my-data');
      return await response.json();
    },
    dataExtractor: (message) => message.data
  });
}
```

## Architecture

All WebSocket hooks follow this pattern:

1. **Connect** to WebSocket endpoint on mount
2. **Receive** typed messages and update state
3. **Reconnect** automatically on disconnection (up to 5 attempts)
4. **Fallback** to REST API polling if WebSocket fails
5. **Cleanup** on unmount

This architecture ensures resilient real-time updates with minimal code duplication.
```

**Cleanup Tasks:**

1. Delete old duplicated code from original `useWebSocket.ts`
2. Move new hooks to individual files
3. Update all imports in components

**Acceptance Criteria:**
- [ ] Integration tests pass
- [ ] All old duplicated code removed
- [ ] Documentation updated
- [ ] Code reduced from 275 lines to ~80 lines core logic
- [ ] No regressions in real-time functionality

**Verification Commands:**
```bash
cd app/client
npm run test
npm run typecheck
npm run build

# Verify file sizes
wc -l src/hooks/use*.ts
```

**Status:** Not Started

---

## Summary Statistics

**Total Workflows:** 16 atomic units
**Total Estimated Time:** 24-30 hours
**Parallelization Potential:** Medium

**Workflow Dependencies:**
```
1.1 → 1.2 → 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10 → 1.11 → 1.12
2.1 → 2.2, 2.3 → 2.4
```

**Code Reduction:**
- WorkflowHistoryCard: 793 lines → <200 lines (75% reduction)
- WebSocket hooks: 275 lines → ~80 lines (71% reduction)
- **Total: ~788 lines reduced**

**Files Created:**
- 8 section components (CostEconomics, TokenAnalysis, Performance, Error, Resource, Journey, EfficiencyScores, Insights)
- 2 utility modules (formatters.ts, workflowHelpers.ts)
- 1 generic WebSocket hook
- 3 refactored WebSocket hooks
- 12+ test files

---

## Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| WorkflowHistoryCard size | 793 lines | <200 lines | Not Started |
| WebSocket hooks total | 275 lines | ~80 lines | Not Started |
| Component test coverage | 0% | >80% | Not Started |
| Visual regressions | N/A | 0 | Not Started |
| Code duplication | High | Minimal | Not Started |

---

## Testing Strategy

### Unit Testing
- Test each section component independently
- Test utility functions (formatters, helpers)
- Test WebSocket hook reconnection logic
- Test fallback polling behavior

### Integration Testing
- Test WorkflowHistoryCard with all sections
- Test WebSocket hooks together
- Test real-time update flow end-to-end

### Visual Regression Testing
- Capture snapshots for each component state
- Use Storybook for component isolation
- Compare UI before/after refactoring

### Performance Testing
- Measure component render time
- Verify no memory leaks from WebSocket connections
- Test with large datasets (100+ workflows)

---

## Risk Management

**Low Risk:**
- Extracting utility functions (pure functions, easy to test)
- Creating section components (isolated, testable)

**Medium Risk:**
- WebSocket hook consolidation (complex state management)
- Maintaining UI/UX consistency (requires careful testing)

**Mitigation:**
- Comprehensive test coverage before refactoring
- Visual regression testing with snapshots
- Gradual migration (one section at a time)
- Keep old code until new code verified

---

## Next Steps

1. **Review this plan** with team
2. **Approve Phase 4** refactoring strategy
3. **Create feature branch** `refactor/phase-4-frontend-components`
4. **Begin Workflow 1.1** - Extract utility functions
5. **Set up Storybook** for visual regression testing
6. **Schedule check-ins** - Daily updates on progress

---

**Document Status:** Complete - Ready for Implementation
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Related:** [REFACTORING_PLAN.md](../REFACTORING_PLAN.md), [PHASE_1_DETAILED.md](./PHASE_1_DETAILED.md), [PHASE_2_DETAILED.md](./PHASE_2_DETAILED.md)
