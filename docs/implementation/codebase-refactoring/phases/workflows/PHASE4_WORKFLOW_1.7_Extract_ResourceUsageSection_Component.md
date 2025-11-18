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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
