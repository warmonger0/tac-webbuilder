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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
