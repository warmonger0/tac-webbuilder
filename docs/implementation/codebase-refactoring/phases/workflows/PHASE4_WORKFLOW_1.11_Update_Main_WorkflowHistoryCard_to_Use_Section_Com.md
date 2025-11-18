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
