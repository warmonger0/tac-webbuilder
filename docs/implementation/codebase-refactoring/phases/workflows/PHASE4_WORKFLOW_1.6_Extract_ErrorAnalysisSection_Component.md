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
