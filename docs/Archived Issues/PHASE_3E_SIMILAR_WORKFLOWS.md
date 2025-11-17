# Phase 3E: Similar Workflows Comparison

**Status:** Not Started
**Complexity:** HIGH
**Estimated Cost:** $1-2 (Sonnet)
**Execution:** **ADW WORKFLOW** (complex similarity algorithm)
**Duration:** 2-2.5 hours

## Overview

Implement similar workflow detection and comparison visualization. This enables users to benchmark their workflows against similar historical executions and identify optimization patterns.

## Why This Needs ADW

- **Complex similarity algorithm** - Multi-factor comparison logic
- **Text similarity** - NL input comparison (cosine similarity or similar)
- **API integration** - New endpoint for fetching similar workflows
- **Component complexity** - Comparison table with multiple metrics
- **Testing requirements** - Edge cases and data fetching

## Dependencies

- **Phase 3A completed** - Database fields must exist
- **Phase 3B completed** - Similarity detection function stub exists
- **Phase 3C completed** - UI patterns established
- Historical workflow data for testing

## Scope

### 1. Similarity Detection Algorithm

**Function:** `find_similar_workflows(workflow: Dict, all_workflows: List[Dict]) -> List[str]`

**File:** `app/server/core/workflow_analytics.py`

```python
from typing import Dict, List
import math


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings (0-1).

    Uses simple word overlap for now (can be upgraded to cosine similarity later).

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score from 0 (no overlap) to 1 (identical)
    """
    if not text1 or not text2:
        return 0.0

    # Normalize and tokenize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def find_similar_workflows(workflow: Dict, all_workflows: List[Dict]) -> List[str]:
    """
    Find similar workflows based on multiple criteria.

    Similarity scoring breakdown:
    - Same classification type: 30 points
    - Same workflow template: 30 points
    - Similar complexity: 20 points
    - Similar NL input (text similarity): 20 points

    Returns workflows with similarity score >= 70 points, sorted by score.

    Args:
        workflow: Current workflow data
        all_workflows: All historical workflows

    Returns:
        List of ADW IDs for similar workflows (max 10, sorted by similarity)
    """
    current_id = workflow.get('adw_id')
    candidates = []

    for candidate in all_workflows:
        if candidate.get('adw_id') == current_id:
            continue  # Skip self

        similarity_score = 0.0

        # 1. Same classification type (30 points)
        if workflow.get('classification_type') == candidate.get('classification_type'):
            similarity_score += 30

        # 2. Same workflow template (30 points)
        if workflow.get('workflow_template') == candidate.get('workflow_template'):
            similarity_score += 30

        # 3. Similar complexity (20 points)
        current_complexity = detect_complexity(workflow)
        candidate_complexity = detect_complexity(candidate)
        if current_complexity == candidate_complexity:
            similarity_score += 20

        # 4. Similar NL input (20 points max)
        current_nl = workflow.get('nl_input', '')
        candidate_nl = candidate.get('nl_input', '')
        text_sim = calculate_text_similarity(current_nl, candidate_nl)
        similarity_score += text_sim * 20

        # Only include if similarity >= 70 (strong match)
        if similarity_score >= 70:
            candidates.append({
                'adw_id': candidate['adw_id'],
                'similarity_score': similarity_score
            })

    # Sort by similarity score (highest first)
    candidates.sort(key=lambda x: x['similarity_score'], reverse=True)

    # Return top 10 ADW IDs
    return [c['adw_id'] for c in candidates[:10]]


def detect_complexity(workflow: Dict) -> str:
    """
    Detect workflow complexity level.

    Returns: "simple", "medium", "complex"
    """
    # Reuse from Phase 3D if already implemented
    word_count = workflow.get('nl_input_word_count', 0)
    duration = workflow.get('total_duration_seconds', 0)
    error_count = len(workflow.get('errors', []))

    if word_count < 50 and duration < 300 and error_count < 3:
        return "simple"
    elif word_count > 200 or duration > 1800 or error_count > 5:
        return "complex"
    else:
        return "medium"
```

### 2. Sync Integration

**File:** `app/server/core/workflow_history.py`

Update `sync_workflow_history()` to populate similar workflows:

```python
def sync_workflow_history() -> int:
    """Sync with similar workflow detection."""

    # ... existing sync logic ...

    # Get all workflows for comparison
    all_workflows = fetch_all_workflows()

    for workflow in workflows:
        # ... existing score calculations ...

        # Find similar workflows
        workflow['similar_workflow_ids'] = find_similar_workflows(workflow, all_workflows)

        # Update performance score using similar workflows
        similar_workflows_data = [
            w for w in all_workflows
            if w['adw_id'] in workflow['similar_workflow_ids']
        ]
        workflow['performance_score'] = calculate_performance_score(
            workflow,
            similar_workflows_data
        )

        # Serialize for SQLite
        workflow['similar_workflow_ids'] = json.dumps(workflow['similar_workflow_ids'])

    # ... rest of sync logic ...
```

### 3. API Endpoint for Similar Workflows

**File:** `app/server/server.py`

Add endpoint to fetch multiple workflows by IDs:

```python
from typing import List
from fastapi import HTTPException

@app.post("/api/workflows/batch", response_model=List[WorkflowHistoryItem])
async def get_workflows_batch(workflow_ids: List[str]):
    """
    Fetch multiple workflows by ADW IDs.

    Used for loading similar workflows for comparison.

    Args:
        workflow_ids: List of ADW IDs to fetch

    Returns:
        List of workflow history items
    """
    if not workflow_ids:
        return []

    if len(workflow_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 workflows can be fetched at once"
        )

    try:
        workflows = []
        for adw_id in workflow_ids:
            workflow = get_workflow_by_id(adw_id)
            if workflow:
                workflows.append(workflow)

        return workflows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. SimilarWorkflowsComparison Component

**File:** `app/client/src/components/SimilarWorkflowsComparison.tsx`

```tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWorkflowsBatch } from '../api/client';
import type { WorkflowHistoryItem } from '../types/api.types';

interface SimilarWorkflowsComparisonProps {
  currentWorkflowId: string;
  similarWorkflowIds: string[];
}

export function SimilarWorkflowsComparison({
  currentWorkflowId,
  similarWorkflowIds,
}: SimilarWorkflowsComparisonProps) {
  // Fetch similar workflows
  const { data: similarWorkflows, isLoading, error } = useQuery({
    queryKey: ['workflows-batch', similarWorkflowIds],
    queryFn: () => fetchWorkflowsBatch(similarWorkflowIds),
    enabled: similarWorkflowIds.length > 0,
  });

  if (isLoading) {
    return (
      <div className="text-sm text-gray-500 italic">
        Loading similar workflows...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Error loading similar workflows
      </div>
    );
  }

  if (!similarWorkflows || similarWorkflows.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No similar workflows found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Workflow
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Cost
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Duration
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Cache Hit
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Errors
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {similarWorkflows.map((workflow: WorkflowHistoryItem) => {
            const cacheHitRate = workflow.input_tokens
              ? (workflow.cache_read_tokens / workflow.input_tokens) * 100
              : 0;

            return (
              <tr key={workflow.adw_id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">
                    ADW-{workflow.adw_id}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(workflow.created_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-gray-900">
                    ${workflow.actual_cost?.toFixed(2) || 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-gray-900">
                    {workflow.total_duration_seconds
                      ? `${(workflow.total_duration_seconds / 60).toFixed(1)}m`
                      : 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={
                      cacheHitRate >= 80
                        ? 'text-green-600'
                        : cacheHitRate >= 50
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }
                  >
                    {cacheHitRate.toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={
                      (workflow.errors?.length || 0) === 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }
                  >
                    {workflow.errors?.length || 0}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => {
                      // Scroll to workflow in history or open in new view
                      const element = document.getElementById(`workflow-${workflow.adw_id}`);
                      if (element) {
                        element.scrollIntoView({ behavior: 'smooth' });
                      }
                    }}
                    className="text-blue-600 hover:text-blue-800 text-xs underline"
                  >
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Summary Statistics */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
        <h5 className="text-xs font-semibold text-blue-700 mb-2">
          Comparison Summary
        </h5>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <div className="text-gray-600">Avg Cost</div>
            <div className="font-semibold text-gray-900">
              $
              {(
                similarWorkflows.reduce(
                  (sum, w) => sum + (w.actual_cost || 0),
                  0
                ) / similarWorkflows.length
              ).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Avg Duration</div>
            <div className="font-semibold text-gray-900">
              {(
                similarWorkflows.reduce(
                  (sum, w) => sum + (w.total_duration_seconds || 0),
                  0
                ) /
                similarWorkflows.length /
                60
              ).toFixed(1)}
              m
            </div>
          </div>
          <div>
            <div className="text-gray-600">Avg Cache Hit</div>
            <div className="font-semibold text-gray-900">
              {(
                similarWorkflows.reduce((sum, w) => {
                  const rate = w.input_tokens
                    ? (w.cache_read_tokens / w.input_tokens) * 100
                    : 0;
                  return sum + rate;
                }, 0) / similarWorkflows.length
              ).toFixed(0)}
              %
            </div>
          </div>
          <div>
            <div className="text-gray-600">Success Rate</div>
            <div className="font-semibold text-gray-900">
              {(
                (similarWorkflows.filter((w) => (w.errors?.length || 0) === 0)
                  .length /
                  similarWorkflows.length) *
                100
              ).toFixed(0)}
              %
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 5. API Client Function

**File:** `app/client/src/api/client.ts`

Add function to fetch workflows in batch:

```typescript
export async function fetchWorkflowsBatch(
  workflowIds: string[]
): Promise<WorkflowHistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/workflows/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(workflowIds),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch workflows: ${response.statusText}`);
  }

  return response.json();
}
```

### 6. WorkflowHistoryCard Integration

**File:** `app/client/src/components/WorkflowHistoryCard.tsx`

Add Similar Workflows section after Insights & Recommendations:

```tsx
import { SimilarWorkflowsComparison } from './SimilarWorkflowsComparison';

// ... existing imports and code ...

{/* Similar Workflows Section */}
{workflow.similar_workflow_ids && workflow.similar_workflow_ids.length > 0 && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      🔗 Similar Workflows
    </h3>

    <div className="text-sm text-gray-600 mb-3">
      Found {workflow.similar_workflow_ids.length} similar workflow
      {workflow.similar_workflow_ids.length !== 1 ? 's' : ''}
    </div>

    <SimilarWorkflowsComparison
      currentWorkflowId={workflow.adw_id}
      similarWorkflowIds={workflow.similar_workflow_ids}
    />
  </div>
)}
```

## Acceptance Criteria

- [ ] `calculate_text_similarity()` function implemented
- [ ] Text similarity works with Jaccard index
- [ ] `find_similar_workflows()` implemented with multi-factor scoring
- [ ] Similarity threshold set to 70+ points
- [ ] Returns max 10 similar workflows, sorted by score
- [ ] Sync process populates similar_workflow_ids
- [ ] Performance score uses similar workflows for comparison
- [ ] `/api/workflows/batch` endpoint created
- [ ] Endpoint validates input (max 20 workflows)
- [ ] `fetchWorkflowsBatch()` API client function created
- [ ] `SimilarWorkflowsComparison` component created
- [ ] Component displays comparison table
- [ ] Component shows summary statistics
- [ ] Component handles loading/error states
- [ ] Similar Workflows section added to WorkflowHistoryCard
- [ ] Section only renders when similar workflows exist
- [ ] "View" button scrolls to workflow (if in current view)
- [ ] Unit tests for similarity algorithm (5+ test cases)
- [ ] Component tests for SimilarWorkflowsComparison
- [ ] No TypeScript/Python errors

## Testing Requirements

### Unit Tests

**File:** `app/server/tests/test_workflow_analytics_similarity.py`

```python
import pytest
from core.workflow_analytics import calculate_text_similarity, find_similar_workflows

class TestTextSimilarity:
    def test_identical_text(self):
        result = calculate_text_similarity("hello world", "hello world")
        assert result == 1.0

    def test_no_overlap(self):
        result = calculate_text_similarity("foo bar", "baz qux")
        assert result == 0.0

    def test_partial_overlap(self):
        result = calculate_text_similarity("foo bar baz", "bar baz qux")
        assert 0.4 < result < 0.7

    def test_case_insensitive(self):
        result = calculate_text_similarity("Hello World", "hello world")
        assert result == 1.0

    def test_empty_strings(self):
        assert calculate_text_similarity("", "test") == 0.0
        assert calculate_text_similarity("test", "") == 0.0


class TestSimilarWorkflows:
    def test_finds_exact_match(self):
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'standard',
            'nl_input': 'implement auth',
            'nl_input_word_count': 30,
            'total_duration_seconds': 200,
            'errors': []
        }

        all_workflows = [
            workflow,
            {
                'adw_id': '2',
                'classification_type': 'feature',
                'workflow_template': 'standard',
                'nl_input': 'implement authentication system',
                'nl_input_word_count': 28,
                'total_duration_seconds': 220,
                'errors': []
            }
        ]

        similar = find_similar_workflows(workflow, all_workflows)
        assert '2' in similar

    def test_excludes_self(self):
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        similar = find_similar_workflows(workflow, [workflow])
        assert len(similar) == 0

    def test_similarity_threshold(self):
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'standard',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        dissimilar = {
            'adw_id': '2',
            'classification_type': 'bug',  # Different type
            'workflow_template': 'hotfix',  # Different template
            'nl_input': 'completely different',
            'nl_input_word_count': 500,
            'total_duration_seconds': 3000,
            'errors': list(range(10))
        }

        similar = find_similar_workflows(workflow, [workflow, dissimilar])
        assert '2' not in similar

    def test_max_10_results(self):
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'standard',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        # Create 15 similar workflows
        all_workflows = [workflow]
        for i in range(15):
            all_workflows.append({
                'adw_id': str(i + 2),
                'classification_type': 'feature',
                'workflow_template': 'standard',
                'nl_input': 'test implementation',
                'nl_input_word_count': 22,
                'total_duration_seconds': 110,
                'errors': []
            })

        similar = find_similar_workflows(workflow, all_workflows)
        assert len(similar) <= 10
```

## Files to Create

- `app/client/src/components/SimilarWorkflowsComparison.tsx`
- `app/client/src/components/__tests__/SimilarWorkflowsComparison.test.tsx`
- `app/server/tests/test_workflow_analytics_similarity.py`

## Files to Modify

- `app/server/core/workflow_analytics.py` (add 2 functions)
- `app/server/core/workflow_history.py` (integrate similarity detection)
- `app/server/server.py` (add batch endpoint)
- `app/client/src/api/client.ts` (add batch fetch function)
- `app/client/src/components/WorkflowHistoryCard.tsx` (add section)

## Time Estimate

- Similarity algorithm: 45 minutes
- Sync integration: 20 minutes
- Batch API endpoint: 20 minutes
- SimilarWorkflowsComparison component: 60 minutes
- API client function: 10 minutes
- UI integration: 20 minutes
- Unit tests: 45 minutes
- Component tests: 30 minutes
- Testing/debugging: 30 minutes
- **Total: 4.5 hours**

## ADW Workflow Recommendations

**Classification:** `standard`
**Model:** Sonnet (complex similarity algorithm)
**Issue Title:** "Implement Phase 3E: Similar Workflows Detection & Comparison"

**Issue Description:**
```markdown
Add similar workflow detection and comparison visualization.

Requirements:
- Multi-factor similarity scoring algorithm
- Batch API endpoint for fetching workflows
- Comparison table component
- Summary statistics
- Unit and component tests

See: docs/PHASE_3E_SIMILAR_WORKFLOWS.md
```

## Success Metrics

- Similarity algorithm finds relevant workflows
- Comparison table displays clearly
- Summary statistics accurate
- All tests pass (10+ test cases)
- Performance acceptable (batch fetch <500ms)

## Future Enhancements

- **Advanced text similarity** - Use TF-IDF or embeddings
- **Configurable thresholds** - Let users adjust similarity threshold
- **Export comparison** - Download comparison table as CSV
- **Visual diff** - Show NL input differences highlighted
- **Trend analysis** - Show how metrics evolved over similar workflows

## Notes

- **Similarity is subjective** - 70-point threshold may need tuning
- **Text similarity is basic** - Jaccard is simple, can upgrade later
- **Performance matters** - Batch endpoint should be efficient
- **UI should be scannable** - Table format allows quick comparison
- **Summary is key** - Aggregate stats give context at a glance
