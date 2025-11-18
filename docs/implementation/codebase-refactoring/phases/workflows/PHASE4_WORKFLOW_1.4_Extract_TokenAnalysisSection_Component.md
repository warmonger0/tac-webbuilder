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
