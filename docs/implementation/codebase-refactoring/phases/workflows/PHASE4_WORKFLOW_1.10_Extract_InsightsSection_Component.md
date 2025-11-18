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
