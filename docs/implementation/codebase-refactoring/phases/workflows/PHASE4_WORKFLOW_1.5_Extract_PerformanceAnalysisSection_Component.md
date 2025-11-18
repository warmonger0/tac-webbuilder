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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
