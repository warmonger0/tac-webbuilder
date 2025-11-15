# Phase 3C: Score Display UI

**Classification:** lightweight | **Model:** Haiku | **Est. Cost:** $0.40-0.60 | **Time:** 5-6 hours

## Context

Phase 3B scoring engine is complete and working. Backend calculates and stores efficiency scores for all workflows. **This phase adds UI to display those scores** in the Workflow History panel.

## What Already Exists

**Backend:** ✅ Complete
- Scores calculated: `cost_efficiency_score`, `performance_score`, `quality_score` (0-100 scale)
- Pattern data: `similar_workflow_ids[]`, `anomaly_flags[]`, `optimization_recommendations[]`
- API endpoint: `/api/workflow-history` returns all data

**Frontend:** ⚠️ Partial
- `ScoreCard.tsx` - Exists, needs review
- `SimilarWorkflowsComparison.tsx` - Exists, needs review
- `WorkflowHistoryCard.tsx` - Has Phase 3 sections partially integrated (lines 693-787)

## Implementation Tasks

### 1. Review & Fix ScoreCard Component

**File:** `app/client/src/components/ScoreCard.tsx`

**Current State:** Component exists but may need adjustments

**Requirements:**
- Display score (0-100) with color coding:
  - 90-100: Green (`bg-green-50 border-green-200 text-green-800`)
  - 70-89: Blue (`bg-blue-50 border-blue-200 text-blue-800`)
  - 50-69: Yellow (`bg-yellow-50 border-yellow-200 text-yellow-800`)
  - 0-49: Orange (`bg-orange-50 border-orange-200 text-orange-800`)
- Large score number (`text-3xl font-bold`)
- Title and description
- Responsive (3-column grid on desktop, 1-column mobile)

**Props:**
```typescript
interface ScoreCardProps {
  title: string;
  score: number;
  description: string;
}
```

### 2. Review & Fix SimilarWorkflowsComparison

**File:** `app/client/src/components/SimilarWorkflowsComparison.tsx`

**Current State:** Component exists but may need adjustments

**Requirements:**
- Show count: `Found {count} similar workflows`
- Display workflow IDs (compact list or table)
- Optional: Fetch and display comparison metrics (cost/duration)

**Props:**
```typescript
interface SimilarWorkflowsComparisonProps {
  currentWorkflowId: string;
  similarWorkflowIds: string[];
}
```

### 3. Complete WorkflowHistoryCard Integration

**File:** `app/client/src/components/WorkflowHistoryCard.tsx`

**Current State:** Lines 693-787 have Phase 3 sections partially added

**Verify These Sections Work:**

**A. Efficiency Scores (lines 693-730):**
```typescript
{(workflow.cost_efficiency_score !== undefined ||
  workflow.performance_score !== undefined ||
  workflow.quality_score !== undefined) && (
  <div className="border-b border-gray-200 pb-6">
    <h3>📊 Efficiency Scores</h3>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {workflow.cost_efficiency_score && <ScoreCard title="Cost Efficiency" score={...} />}
      {workflow.performance_score && <ScoreCard title="Performance" score={...} />}
      {workflow.quality_score && <ScoreCard title="Quality" score={...} />}
    </div>
  </div>
)}
```

**B. Insights & Recommendations (lines 734-767):**
```typescript
{((workflow.anomaly_flags && workflow.anomaly_flags.length > 0) ||
  (workflow.optimization_recommendations && workflow.optimization_recommendations.length > 0)) && (
  <div className="border-b border-gray-200 pb-6">
    <h3>💡 Insights & Recommendations</h3>

    {workflow.anomaly_flags?.length > 0 && (
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-orange-700 mb-2">⚠️ Anomalies Detected</h4>
        <ul className="space-y-2">
          {workflow.anomaly_flags.map((anomaly, idx) => (
            <li key={idx} className="bg-orange-50 border border-orange-200 rounded p-3 text-sm">
              {anomaly}
            </li>
          ))}
        </ul>
      </div>
    )}

    {workflow.optimization_recommendations?.length > 0 && (
      <div>
        <h4 className="text-sm font-semibold text-green-700 mb-2">✅ Optimization Tips</h4>
        <ul className="space-y-2">
          {workflow.optimization_recommendations.map((rec, idx) => (
            <li key={idx} className="bg-green-50 border border-green-200 rounded p-3 text-sm">
              {rec}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
)}
```

**C. Similar Workflows (lines 771-787):**
```typescript
{workflow.similar_workflow_ids && workflow.similar_workflow_ids.length > 0 && (
  <div className="border-b border-gray-200 pb-6">
    <h3>🔗 Similar Workflows</h3>
    <div className="text-sm text-gray-600 mb-3">
      Found {workflow.similar_workflow_ids.length} similar workflows
    </div>
    <SimilarWorkflowsComparison
      currentWorkflowId={workflow.adw_id}
      similarWorkflowIds={workflow.similar_workflow_ids}
    />
  </div>
)}
```

### 4. Create Unit Tests

**Files to Create:**
- `app/client/src/components/__tests__/ScoreCard.test.tsx`
- `app/client/src/components/__tests__/SimilarWorkflowsComparison.test.tsx`

**Enhance Existing:**
- `app/client/src/components/__tests__/WorkflowHistoryCard.test.tsx` - Add Phase 3 integration tests

**Test Coverage Requirements:**
- ✅ ScoreCard renders with correct colors for all score ranges
- ✅ ScoreCard is accessible (ARIA labels)
- ✅ SimilarWorkflowsComparison handles empty arrays
- ✅ WorkflowHistoryCard shows/hides Phase 3 sections based on data
- ✅ WorkflowHistoryCard handles workflows without analytics data (backwards compatibility)

## Acceptance Criteria

**Functional:**
- [ ] All 3 score cards display when data exists
- [ ] Score colors match requirements (green/blue/yellow/orange)
- [ ] Anomaly alerts display in orange/yellow warning style
- [ ] Optimization tips display in green success style
- [ ] Similar workflows section shows count and comparison
- [ ] All sections hide when data is missing (conditional rendering)

**Quality:**
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] Test coverage >80% for new/modified components
- [ ] Accessible (ARIA labels, semantic HTML, keyboard navigation)
- [ ] Responsive (mobile 375px+, tablet, desktop)
- [ ] No performance regression

## Test Data

Use existing workflow data or create test data with:
```typescript
const mockWorkflow: WorkflowHistoryItem = {
  // ... existing fields ...
  cost_efficiency_score: 85,
  performance_score: 72,
  quality_score: 95,
  anomaly_flags: [
    "Cost 1.6x higher than average for similar workflows",
    "Unusual retry count (3 retries detected)"
  ],
  optimization_recommendations: [
    "Consider using Haiku model for similar simple features",
    "Cache efficiency is low (45%) - review prompt structure"
  ],
  similar_workflow_ids: ["abc123", "def456", "ghi789"],
  scoring_version: "1.0"
};
```

## Edge Cases

1. **No analytics data:** Workflow from before Phase 3 - sections should not render
2. **Partial scores:** Only cost_efficiency_score exists - show only that ScoreCard
3. **Empty arrays:** `anomaly_flags: []` - section should not render
4. **Score of 0:** Valid poor score, not missing data - show in orange/red
5. **Many similar workflows:** Handle 20+ IDs without UI breaking

## Files Summary

**Review/Fix:**
- `app/client/src/components/ScoreCard.tsx`
- `app/client/src/components/SimilarWorkflowsComparison.tsx`

**Verify Integration:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (lines 693-787)

**Create:**
- `app/client/src/components/__tests__/ScoreCard.test.tsx`
- `app/client/src/components/__tests__/SimilarWorkflowsComparison.test.tsx`

**Enhance:**
- `app/client/src/components/__tests__/WorkflowHistoryCard.test.tsx`

## Success Metrics

- ✅ Scores visible in workflow history cards
- ✅ Color coding intuitive and correct
- ✅ Mobile responsive (tested 375px width)
- ✅ Test coverage >80%
- ✅ Zero TypeScript/console errors
- ✅ Zero accessibility violations

## Reference

- Backend data models: `app/server/core/data_models.py`
- TypeScript types: `app/client/src/types/api.types.ts`
- Full Phase 3 spec: `docs/PHASE_3C_SCORE_DISPLAY_UI.md`
