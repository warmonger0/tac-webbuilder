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
