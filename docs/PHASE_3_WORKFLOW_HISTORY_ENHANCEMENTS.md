# Phase 3: Workflow History Advanced Analytics & Optimization Insights

> **⚠️ IMPORTANT: Phase 3 has been broken down into smaller sub-phases for better cost efficiency and manageability.**
>
> **Use these instead:**
> - **PHASE_3A_ANALYTICS_INFRASTRUCTURE.md** - Infrastructure setup ($0.20-0.30, run locally)
> - **PHASE_3B_SCORING_ENGINE.md** - Core scoring algorithms ($2-4, ADW)
> - **PHASE_3C_SCORE_DISPLAY_UI.md** - Score visualization ($0.50-1, ADW)
> - **PHASE_3D_INSIGHTS_RECOMMENDATIONS.md** - Anomaly detection ($1-2, ADW)
> - **PHASE_3E_SIMILAR_WORKFLOWS.md** - Similarity detection ($1-2, ADW)
>
> **Total cost breakdown: $4.70-9.30 (vs $6-11 monolithic)**
>
> See `WORKFLOW_HISTORY_ENHANCEMENT_SUMMARY.md` for updated execution recommendations.

---

## Original Monolithic Specification (For Reference Only)

This document contains the original Phase 3 specification as a single large phase. It has been preserved for reference, but should not be used for implementation. Use the sub-phase documents listed above instead.

## Overview
Add advanced analytics, pattern detection, and optimization recommendations to workflow history. Enable data-driven decision making through trend analysis, cost modeling, and efficiency scoring.

## Dependencies
- Phase 1 must be completed (UI foundation)
- Phase 2 must be completed (performance metrics foundation)

## Current State
After Phase 2:
- Rich performance and error metrics
- Phase-level analysis
- Basic cost tracking

## Requirements

### 1. Database Schema Updates

Add these fields to the `workflow_history` table:

```sql
-- Input quality metrics
nl_input_word_count INTEGER,
nl_input_clarity_score REAL,           -- 0-100 score based on heuristics
structured_input_completeness_percent REAL,

-- Temporal patterns
submission_hour INTEGER,                -- 0-23
submission_day_of_week INTEGER,        -- 0-6 (Monday=0)

-- Outcome tracking
pr_merged BOOLEAN DEFAULT 0,
time_to_merge_hours REAL,
review_cycles INTEGER,
ci_test_pass_rate REAL,

-- Efficiency scores
cost_efficiency_score REAL,            -- 0-100: composite of cost vs estimate, cache efficiency, retry rate
performance_score REAL,                -- 0-100: based on duration vs similar workflows
quality_score REAL,                    -- 0-100: based on error rate, review cycles, test pass rate

-- Pattern metadata
similar_workflow_ids TEXT,             -- JSON array of similar workflow ADW IDs
anomaly_flags TEXT,                    -- JSON array of detected anomalies
optimization_recommendations TEXT      -- JSON array of recommendations
```

Create migration file: `app/server/db/migrations/003_add_analytics_metrics.sql`

### 2. Backend Analytics Engine

#### 2.1 Create `app/server/core/workflow_analytics.py`

New module for advanced analytics:

```python
"""
Advanced analytics engine for workflow history.
Provides pattern detection, scoring, and optimization recommendations.
"""

def calculate_nl_input_clarity_score(nl_input: str) -> float:
    """
    Score 0-100 based on:
    - Length (sweet spot: 50-300 words)
    - Presence of acceptance criteria keywords
    - Technical specificity
    - Question vs statement ratio
    """
    pass

def calculate_cost_efficiency_score(workflow: Dict) -> float:
    """
    Score 0-100 based on:
    - Actual vs estimated cost (penalty for over-budget)
    - Cache efficiency (bonus for high cache hit rate)
    - Retry rate (penalty for retries)
    - Model selection appropriateness
    """
    pass

def calculate_performance_score(workflow: Dict, similar_workflows: List[Dict]) -> float:
    """
    Score 0-100 comparing this workflow to similar ones:
    - Duration vs average for same template
    - Bottleneck presence
    - Idle time
    """
    pass

def calculate_quality_score(workflow: Dict) -> float:
    """
    Score 0-100 based on:
    - Error rate
    - Retry count
    - PR review cycles
    - CI test pass rate
    """
    pass

def find_similar_workflows(workflow: Dict, all_workflows: List[Dict]) -> List[str]:
    """
    Find similar workflows based on:
    - Same classification type
    - Same workflow template
    - Similar complexity
    - Similar nl_input (cosine similarity)

    Returns: List of ADW IDs
    """
    pass

def detect_anomalies(workflow: Dict, historical_data: List[Dict]) -> List[str]:
    """
    Detect anomalies:
    - Cost >2x average for similar workflows
    - Duration >2x average
    - Unusually high retry count
    - Unexpected error category

    Returns: List of anomaly descriptions
    """
    pass

def generate_optimization_recommendations(workflow: Dict) -> List[str]:
    """
    Generate actionable recommendations:
    - "Consider using Haiku model for similar simple features"
    - "Cache efficiency is low - review prompt structure"
    - "Build phase is bottleneck - consider splitting into subtasks"
    - "NL input lacks acceptance criteria - improves with explicit criteria"

    Returns: List of recommendation strings
    """
    pass
```

#### 2.2 Update `sync_workflow_history()`

Enhance sync to calculate analytics:
```python
def sync_workflow_history() -> int:
    """Enhanced with analytics calculation"""
    # ... existing sync logic ...

    # For each workflow:
    # - Calculate clarity score
    # - Calculate efficiency scores
    # - Find similar workflows
    # - Detect anomalies
    # - Generate recommendations
    # - Extract temporal data (hour, day of week)
    pass
```

### 3. Frontend Analytics Dashboard

#### 3.1 New Section: Efficiency Scores
Add to WorkflowHistoryCard details:

```tsx
{/* Efficiency Scores Section */}
{(workflow.cost_efficiency_score || workflow.performance_score || workflow.quality_score) && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      📊 Efficiency Scores
    </h3>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Cost Efficiency */}
      {workflow.cost_efficiency_score !== null && (
        <ScoreCard
          title="Cost Efficiency"
          score={workflow.cost_efficiency_score}
          description="Budget adherence, cache usage, retry rate"
        />
      )}

      {/* Performance */}
      {workflow.performance_score !== null && (
        <ScoreCard
          title="Performance"
          score={workflow.performance_score}
          description="Duration vs similar workflows"
        />
      )}

      {/* Quality */}
      {workflow.quality_score !== null && (
        <ScoreCard
          title="Quality"
          score={workflow.quality_score}
          description="Error rate, review cycles, tests"
        />
      )}
    </div>
  </div>
)}
```

#### 3.2 New Section: Insights & Recommendations
```tsx
{/* Insights & Recommendations Section */}
{(workflow.anomaly_flags?.length > 0 || workflow.optimization_recommendations?.length > 0) && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      💡 Insights & Recommendations
    </h3>

    {/* Anomaly Alerts */}
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

    {/* Optimization Recommendations */}
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

#### 3.3 New Section: Similar Workflows Comparison
```tsx
{/* Similar Workflows Section */}
{workflow.similar_workflow_ids?.length > 0 && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      🔗 Similar Workflows
    </h3>

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

#### 3.4 New Components

**`ScoreCard.tsx`:**
```tsx
interface ScoreCardProps {
  title: string;
  score: number; // 0-100
  description: string;
}

export function ScoreCard({ title, score, description }: ScoreCardProps) {
  // Display score as circular progress indicator
  // Color: green (80+), yellow (50-79), red (<50)
  // Show title, score, and description
}
```

**`SimilarWorkflowsComparison.tsx`:**
```tsx
interface SimilarWorkflowsComparisonProps {
  currentWorkflowId: string;
  similarWorkflowIds: string[];
}

export function SimilarWorkflowsComparison({ currentWorkflowId, similarWorkflowIds }: SimilarWorkflowsComparisonProps) {
  // Fetch similar workflows from API
  // Display comparison table:
  // - Cost comparison
  // - Duration comparison
  // - Cache efficiency comparison
  // - Links to view each similar workflow
}
```

### 4. Analytics API Endpoints

Add to `app/server/server.py`:

```python
@app.get("/api/workflow-analytics/{adw_id}", response_model=WorkflowAnalytics)
async def get_workflow_analytics(adw_id: str):
    """Get advanced analytics for a specific workflow"""
    pass

@app.get("/api/workflow-trends", response_model=WorkflowTrends)
async def get_workflow_trends(
    days: int = 30,
    group_by: str = "day"  # "hour", "day", "week"
):
    """Get trend data over time"""
    pass

@app.get("/api/cost-predictions", response_model=CostPredictions)
async def predict_workflow_cost(
    classification: str,
    complexity: str,
    model: str
):
    """Predict workflow cost based on historical data"""
    pass
```

### 5. Analytics Dashboard Page (Optional Enhancement)

Create new dashboard page at `/analytics` showing:
- Aggregate trend charts (cost over time, success rate over time)
- Model performance comparison
- Template effectiveness comparison
- Peak usage times heatmap
- Cost breakdown by classification type
- Top optimization opportunities

### 6. Type Definition Updates

Update `app/client/src/types/api.types.ts`:

```typescript
class WorkflowHistoryItem(BaseModel):
    # ... existing fields ...

    # Input quality
    nl_input_word_count: Optional[int] = None
    nl_input_clarity_score: Optional[float] = None
    structured_input_completeness_percent: Optional[float] = None

    # Temporal
    submission_hour: Optional[int] = None
    submission_day_of_week: Optional[int] = None

    # Outcomes
    pr_merged: Optional[bool] = None
    time_to_merge_hours: Optional[float] = None
    review_cycles: Optional[int] = None
    ci_test_pass_rate: Optional[float] = None

    # Efficiency scores
    cost_efficiency_score: Optional[float] = None
    performance_score: Optional[float] = None
    quality_score: Optional[float] = None

    # Patterns
    similar_workflow_ids: Optional[List[str]] = None
    anomaly_flags: Optional[List[str]] = None
    optimization_recommendations: Optional[List[str]] = None
```

## Acceptance Criteria

- [ ] Database migration runs successfully with all new analytics fields
- [ ] `workflow_analytics.py` module created with all scoring functions
- [ ] Clarity score calculation works (0-100 scale)
- [ ] Cost efficiency score incorporates budget adherence, cache, retries
- [ ] Performance score compares to similar workflows
- [ ] Quality score factors in errors, reviews, tests
- [ ] Similar workflow detection finds relevant comparisons
- [ ] Anomaly detection identifies outliers (>2x average)
- [ ] Optimization recommendations generated based on patterns
- [ ] Efficiency Scores section displays in WorkflowHistoryCard
- [ ] ScoreCard component shows circular progress with color coding
- [ ] Insights & Recommendations section shows anomalies and tips
- [ ] SimilarWorkflowsComparison component fetches and displays data
- [ ] All analytics gracefully handle missing data
- [ ] No TypeScript errors or console warnings
- [ ] Phase 1 and Phase 2 features still work correctly
- [ ] Analytics API endpoints return correct data structures
- [ ] Sync process populates all analytics fields

## Testing Notes

Test with workflows that:
1. Have different clarity scores (short vs detailed nl_input)
2. Are over/under budget (test cost efficiency scoring)
3. Have varying performance (fast vs slow for same template)
4. Have different quality outcomes (errors vs clean runs)
5. Are anomalies (unusually expensive or slow)
6. Have similar counterparts (test similarity detection)

Test edge cases:
- Workflow with no similar matches
- Workflow with perfect scores (100 across the board)
- Workflow with zero scores
- Very first workflow in system (no historical data)

## Files to Create/Modify

**New Files:**
- `app/server/db/migrations/003_add_analytics_metrics.sql`
- `app/server/core/workflow_analytics.py`
- `app/client/src/components/ScoreCard.tsx`
- `app/client/src/components/SimilarWorkflowsComparison.tsx`
- `app/client/src/pages/AnalyticsDashboard.tsx` (optional)

**Modified Files:**
- `app/server/core/workflow_history.py` - Integrate analytics engine
- `app/server/server.py` - Add analytics API endpoints
- `app/client/src/components/WorkflowHistoryCard.tsx` - Add new sections
- `app/client/src/types/api.types.ts` - Update types
- `app/server/core/data_models.py` - Update Pydantic models

## Notes

- Phase 3 provides **actionable intelligence** from workflow data
- Enables **predictive cost modeling** and **proactive optimization**
- Sets foundation for **ML-based recommendations** in future
- Analytics run during sync (batch) to avoid slowing down workflow execution
- All scores normalized to 0-100 for consistent interpretation
- Recommendations should be specific and actionable, not generic

## Future Enhancements (Post-Phase 3)

Consider for future iterations:
- Machine learning models for cost prediction
- Automated A/B testing of different models/templates
- Workflow optimization suggestions based on code analysis
- Integration with external CI/CD metrics
- Real-time anomaly alerts
- Custom analytics dashboards per user
