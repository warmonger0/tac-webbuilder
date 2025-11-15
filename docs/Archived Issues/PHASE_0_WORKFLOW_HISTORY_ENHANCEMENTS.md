# Phase 0: Pre-Flight Cost Estimation & Confirmation UI

## Overview
Add real-time cost estimation to the workflow submission flow, displaying estimated costs in the web UI preview before users confirm GitHub issue creation and workflow execution.

## Current State
- Cost estimation logic exists (`complexity_analyzer.py`) but is not used
- Web UI shows GitHub issue preview without cost information
- Users cannot see estimated costs before confirming workflow execution
- No warning system for expensive operations

## Why Phase 0 (Before Phase 1)
This is foundational infrastructure that:
- Prevents costly mistakes (user can cancel before execution)
- Provides decision support (informed choices)
- Feeds data into Phase 3 analytics (estimated vs actual tracking)
- Adds zero overhead (0.001ms per request)
- Improves UX immediately

## Requirements

### 1. Backend: Add Cost Estimation to Request Processing

Update `/api/request` endpoint to include cost analysis in the response.

**File:** `app/server/server.py`

**Changes:**

```python
# Add import at top of file
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue

@app.post("/api/request", response_model=SubmitRequestResponse)
async def submit_nl_request(request: SubmitRequestData) -> SubmitRequestResponse:
    """Process natural language request and generate GitHub issue preview WITH cost estimate"""
    try:
        logger.info(f"[INFO] Processing NL request: {request.nl_input[:100]}...")

        # Detect project context
        if request.project_path:
            project_context = detect_project_context(request.project_path)
        else:
            project_context = ProjectContext(
                path=os.getcwd(),
                is_new_project=False,
                complexity="medium",
                has_git=True
            )

        # Process the request to generate GitHub issue
        github_issue = await process_request(request.nl_input, project_context)

        # 🆕 ADD COST ESTIMATION
        # Create ADW-compatible issue object for analysis
        adw_issue = ADWGitHubIssue(
            number=0,
            title=github_issue.title,
            body=github_issue.body,
            user="user",
            labels=github_issue.labels
        )

        # Analyze complexity and get cost estimate
        cost_analysis = analyze_issue_complexity(
            adw_issue,
            f"/{github_issue.classification}"
        )

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in pending requests WITH cost estimate
        pending_requests[request_id] = {
            'issue': github_issue,
            'project_context': project_context,
            'cost_estimate': {  # 🆕 NEW FIELD
                'level': cost_analysis.level,
                'min_cost': cost_analysis.estimated_cost_range[0],
                'max_cost': cost_analysis.estimated_cost_range[1],
                'confidence': cost_analysis.confidence,
                'reasoning': cost_analysis.reasoning,
                'recommended_workflow': cost_analysis.recommended_workflow
            }
        }

        logger.info(f"[SUCCESS] Request processed with cost estimate: {cost_analysis.level} (${cost_analysis.estimated_cost_range[0]:.2f}-${cost_analysis.estimated_cost_range[1]:.2f})")
        return SubmitRequestResponse(request_id=request_id)

    except Exception as e:
        logger.error(f"[ERROR] Failed to process NL request: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error processing request: {str(e)}")
```

### 2. Backend: Add Cost Estimate to Preview Endpoint

**File:** `app/server/server.py`

Add new endpoint to fetch cost estimate separately:

```python
@app.get("/api/preview/{request_id}/cost")
async def get_cost_estimate(request_id: str):
    """Get cost estimate for a pending request"""
    try:
        if request_id not in pending_requests:
            raise HTTPException(404, f"Request ID '{request_id}' not found")

        cost_estimate = pending_requests[request_id].get('cost_estimate')
        if not cost_estimate:
            raise HTTPException(404, "No cost estimate available for this request")

        logger.info(f"[SUCCESS] Retrieved cost estimate for request: {request_id}")
        return cost_estimate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get cost estimate: {str(e)}")
        raise HTTPException(500, f"Error retrieving cost estimate: {str(e)}")
```

### 3. Type Definitions: Add Cost Estimate Models

**File:** `app/server/core/data_models.py`

```python
class CostEstimate(BaseModel):
    """Cost estimate for a workflow"""
    level: Literal["lightweight", "standard", "complex"] = Field(..., description="Complexity level")
    min_cost: float = Field(..., description="Minimum estimated cost in dollars")
    max_cost: float = Field(..., description="Maximum estimated cost in dollars")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Explanation of the estimate")
    recommended_workflow: str = Field(..., description="Recommended ADW workflow")

class GitHubIssueWithCost(BaseModel):
    """GitHub issue preview with cost estimate"""
    issue: GitHubIssue
    cost_estimate: CostEstimate
```

**File:** `app/client/src/types/api.types.ts`

```typescript
export interface CostEstimate {
  level: 'lightweight' | 'standard' | 'complex';
  min_cost: number;
  max_cost: number;
  confidence: number;
  reasoning: string;
  recommended_workflow: string;
}
```

### 4. Frontend: Cost Estimate Display Component

**File:** `app/client/src/components/CostEstimateCard.tsx` (NEW)

```tsx
import React from 'react';

interface CostEstimateCardProps {
  estimate: {
    level: 'lightweight' | 'standard' | 'complex';
    min_cost: number;
    max_cost: number;
    confidence: number;
    reasoning: string;
    recommended_workflow: string;
  };
}

export function CostEstimateCard({ estimate }: CostEstimateCardProps) {
  // Color coding by complexity level
  const levelConfig = {
    lightweight: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      badge: 'bg-green-100 text-green-800',
      icon: '💡',
    },
    standard: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      badge: 'bg-yellow-100 text-yellow-800',
      icon: '💰',
    },
    complex: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      badge: 'bg-red-100 text-red-800',
      icon: '⚠️',
    },
  };

  const config = levelConfig[estimate.level];
  const showWarning = estimate.max_cost > 2.0;

  return (
    <div className={`rounded-lg border-2 p-5 ${config.bg} ${config.border}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <h3 className={`text-lg font-semibold ${config.text}`}>
            Estimated Cost
          </h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.badge}`}>
          {estimate.level.toUpperCase()}
        </span>
      </div>

      {/* Cost Range */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Cost Range</div>
        <div className={`text-3xl font-bold ${config.text}`}>
          ${estimate.min_cost.toFixed(2)} - ${estimate.max_cost.toFixed(2)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Confidence: {(estimate.confidence * 100).toFixed(0)}%
        </div>
      </div>

      {/* Workflow */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Recommended Workflow</div>
        <code className="text-sm bg-white rounded px-2 py-1 border border-gray-200">
          {estimate.recommended_workflow}
        </code>
      </div>

      {/* Reasoning */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">Analysis</div>
        <div className="text-sm text-gray-700 bg-white rounded p-3 border border-gray-200">
          {estimate.reasoning || 'Standard complexity assessment'}
        </div>
      </div>

      {/* High Cost Warning */}
      {showWarning && (
        <div className="bg-red-100 border border-red-300 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <div className="flex-1">
              <div className="font-semibold text-red-800 mb-1">
                High Cost Warning
              </div>
              <div className="text-sm text-red-700 mb-2">
                This workflow may be expensive. Consider:
              </div>
              <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                <li>Breaking into smaller issues (2-3 separate workflows)</li>
                <li>Narrowing the scope to essential features only</li>
                <li>Implementing manually for complex parts</li>
                <li>Using the lightweight workflow if applicable</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Cost Comparison */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          💡 <strong>Tip:</strong> Lightweight workflows ($0.20-$0.50) are ideal for simple
          UI changes, docs, and single-file modifications.
        </div>
      </div>
    </div>
  );
}
```

### 5. Frontend: Integrate into Preview Page

**File:** `app/client/src/pages/RequestPreview.tsx` (or similar)

```tsx
import { CostEstimateCard } from '../components/CostEstimateCard';

export function RequestPreview() {
  const [issue, setIssue] = useState(null);
  const [costEstimate, setCostEstimate] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPreview() {
      try {
        setLoading(true);

        // Fetch issue preview
        const issueResponse = await fetch(`/api/preview/${requestId}`);
        const issueData = await issueResponse.json();
        setIssue(issueData);

        // Fetch cost estimate
        const costResponse = await fetch(`/api/preview/${requestId}/cost`);
        const costData = await costResponse.json();
        setCostEstimate(costData);
      } catch (error) {
        console.error('Failed to load preview:', error);
      } finally {
        setLoading(false);
      }
    }

    loadPreview();
  }, [requestId]);

  if (loading) return <div>Loading preview...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Review Your Request</h1>

      {/* 🆕 COST ESTIMATE CARD - PROMINENT PLACEMENT */}
      {costEstimate && (
        <CostEstimateCard estimate={costEstimate} />
      )}

      {/* GitHub Issue Preview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">GitHub Issue Preview</h2>
        <div className="space-y-4">
          <div>
            <div className="text-sm text-gray-600">Title</div>
            <div className="font-medium">{issue.title}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Description</div>
            <div className="prose prose-sm">{issue.body}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Labels</div>
            <div className="flex gap-2">
              {issue.labels.map(label => (
                <span key={label} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={handleCancel}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Confirm & Create Issue (${costEstimate?.max_cost.toFixed(2)})
        </button>
      </div>
    </div>
  );
}
```

### 6. User Confirmation Flow Enhancement

Update the confirmation button to show cost:

```tsx
<button
  onClick={handleConfirm}
  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
>
  Confirm & Create Issue
  {costEstimate && (
    <span className="ml-2 opacity-80">
      (Est. ${costEstimate.min_cost.toFixed(2)}-${costEstimate.max_cost.toFixed(2)})
    </span>
  )}
</button>
```

## Acceptance Criteria

- [ ] Backend `/api/request` endpoint includes cost estimate in response
- [ ] Backend `/api/preview/{id}/cost` endpoint returns cost estimate
- [ ] `CostEstimateCard` component displays cost range, level, and reasoning
- [ ] Cost estimate shown prominently in preview page (above issue preview)
- [ ] Color coding works correctly (green/yellow/red for light/standard/complex)
- [ ] High cost warning displays for workflows >$2.00
- [ ] Confidence score displays as percentage
- [ ] Recommended workflow shown to user
- [ ] Reasoning explains why complexity level was chosen
- [ ] Confirmation button shows estimated cost
- [ ] Cancel button allows user to abort before issue creation
- [ ] No errors when cost estimate unavailable (graceful degradation)
- [ ] All TypeScript types properly defined
- [ ] No console errors or warnings
- [ ] Responsive design works on mobile
- [ ] Performance overhead is negligible (<5ms added to request)

## Testing Notes

Test with various request types:

### Lightweight Requests (should show green):
- "Add a button to the header"
- "Change the color of the submit button to blue"
- "Fix typo in README"
- "Update documentation for API endpoints"

### Standard Requests (should show yellow):
- "Create a new component for displaying user profiles"
- "Add filters to the workflow history page"
- "Implement CSV export functionality"

### Complex Requests (should show red + warning):
- "Add user authentication with JWT and password reset"
- "Implement full-stack analytics dashboard with charts and export"
- "Migrate database schema to support multi-tenancy"
- "Integrate third-party payment processing API"

### Edge Cases:
- Very short input ("add button")
- Very long input (500+ words)
- Input with no clear complexity signals
- Empty structured input

## Performance Requirements

- Cost estimation must complete in <5ms
- No external API calls during estimation
- Graceful degradation if complexity analyzer fails
- No blocking of UI rendering

## Files to Create/Modify

**New Files:**
- `app/client/src/components/CostEstimateCard.tsx` - Cost display component

**Modified Files:**
- `app/server/server.py` - Add cost estimation to request processing
- `app/server/core/data_models.py` - Add CostEstimate model
- `app/client/src/types/api.types.ts` - Add TypeScript types
- `app/client/src/pages/RequestPreview.tsx` - Integrate cost display
- `pyproject.toml` or `requirements.txt` - May need to add sys.path config

## Notes

- Phase 0 is **prerequisite** for meaningful Phase 3 analytics
- Estimated vs actual cost tracking starts here
- Zero overhead (0.001ms) per benchmark results
- Pure heuristics - no API costs
- User can always cancel if cost seems too high
- Prevents expensive mistakes before they happen
- Improves trust through transparency

## Future Enhancements (Post-Phase 0)

After Phase 0 is implemented, consider:
- Historical accuracy tracking (compare estimated vs actual)
- Machine learning cost predictions (Phase 3)
- Budget limits and alerts
- Cost approval workflow for team settings
- Slack/email notifications for expensive workflows
