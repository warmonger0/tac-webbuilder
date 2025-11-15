# Phase 2: Workflow History Performance & Error Analytics

## Overview
Add performance metrics tracking and error analysis capabilities to workflow history, enabling identification of bottlenecks, retry patterns, and optimization opportunities.

## Dependencies
- Phase 1 must be completed first (UI foundation for displaying new data)

## Current State
- Basic cost and token metrics tracked
- Limited error tracking (only error_message field)
- No phase-level performance data
- No retry reason tracking

## Requirements

### 1. Database Schema Updates

Add these fields to the `workflow_history` table:

```sql
-- Performance metrics
phase_durations TEXT,              -- JSON: {"plan": 45, "build": 120, "test": 80, ...}
idle_time_seconds INTEGER,         -- Time between phases
bottleneck_phase TEXT,             -- Phase that took longest

-- Error & retry analysis
error_category TEXT,               -- "syntax_error", "timeout", "api_quota", "validation", etc.
retry_reasons TEXT,                -- JSON array: ["parse_failure", "validation_error"]
error_phase_distribution TEXT,     -- JSON: {"build": 2, "test": 1}
recovery_time_seconds INTEGER,     -- Total time spent in error->recovery

-- Decision quality
complexity_estimated TEXT,         -- "low", "medium", "high"
complexity_actual TEXT,            -- "low", "medium", "high"
```

Create migration file: `app/server/db/migrations/002_add_performance_metrics.sql`

### 2. Backend Updates

#### 2.1 Update `workflow_history.py`
Add functions to:
- Calculate phase durations from cost_breakdown timestamps
- Detect bottleneck phases (phase taking >30% of total time)
- Calculate idle time between phases
- Extract error categories from error messages
- Track retry reasons when workflows are retried

```python
def calculate_phase_metrics(cost_data: CostData) -> Dict:
    """
    Calculate phase-level performance metrics.

    Returns:
        {
            "phase_durations": {"plan": 45, "build": 120, ...},
            "bottleneck_phase": "build",
            "idle_time_seconds": 10
        }
    """
    pass

def categorize_error(error_message: str) -> str:
    """
    Categorize error message into standard types.

    Returns: "syntax_error" | "timeout" | "api_quota" | "validation" | "unknown"
    """
    pass
```

#### 2.2 Update `sync_workflow_history()`
Enhance sync to populate new fields:
- Extract phase durations from cost_breakdown timestamps
- Calculate bottleneck phase
- Estimate complexity based on steps_total and duration
- Categorize errors when present

### 3. Frontend Updates

#### 3.1 Performance Metrics Section
Add new section in WorkflowHistoryCard details:

```tsx
{/* Performance Analysis Section */}
{workflow.phase_durations && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      ⚡ Performance Analysis
    </h3>

    {/* Phase Duration Bar Chart */}
    <PhaseDurationChart phaseDurations={workflow.phase_durations} />

    {/* Bottleneck Alert */}
    {workflow.bottleneck_phase && (
      <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <div className="text-sm font-medium text-yellow-800">
          ⚠️ Bottleneck Detected: {workflow.bottleneck_phase} phase
        </div>
        <div className="text-xs text-yellow-700 mt-1">
          This phase took significantly longer than others
        </div>
      </div>
    )}

    {/* Idle Time */}
    {workflow.idle_time_seconds > 0 && (
      <div className="mt-2 text-sm text-gray-600">
        Idle time between phases: {formatDuration(workflow.idle_time_seconds)}
      </div>
    )}
  </div>
)}
```

#### 3.2 Enhanced Error Analysis Section
Upgrade existing "Cost of Errors" section:

```tsx
{/* Enhanced Error Analysis */}
{(workflow.retry_count > 0 || workflow.status === 'failed') && (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      ⚠️ Error Analysis
    </h3>

    {/* Error Category Badge */}
    {workflow.error_category && (
      <div className="mb-3">
        <span className="inline-block bg-red-100 text-red-800 text-sm px-3 py-1 rounded">
          {workflow.error_category.replace('_', ' ').toUpperCase()}
        </span>
      </div>
    )}

    {/* Error Message (existing) */}
    {workflow.error_message && (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div className="text-sm font-medium text-red-800 mb-2">Error Message:</div>
        <p className="text-sm text-red-900">{workflow.error_message}</p>
      </div>
    )}

    {/* Retry Reasons */}
    {workflow.retry_reasons && workflow.retry_reasons.length > 0 && (
      <div className="mb-4">
        <div className="text-sm font-medium text-gray-700 mb-2">Retry Triggers:</div>
        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
          {workflow.retry_reasons.map((reason, idx) => (
            <li key={idx}>{reason.replace('_', ' ')}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Error Phase Distribution */}
    {workflow.error_phase_distribution && (
      <div className="mb-4">
        <div className="text-sm font-medium text-gray-700 mb-2">Errors by Phase:</div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {Object.entries(workflow.error_phase_distribution).map(([phase, count]) => (
            <div key={phase} className="bg-red-50 rounded p-2 text-sm">
              <div className="text-gray-600">{phase}</div>
              <div className="font-semibold text-red-700">{count} errors</div>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Recovery Time */}
    {workflow.recovery_time_seconds > 0 && (
      <div className="text-sm text-gray-600">
        Total recovery time: {formatDuration(workflow.recovery_time_seconds)}
      </div>
    )}
  </div>
)}
```

#### 3.3 New Component: PhaseDurationChart
Create `app/client/src/components/PhaseDurationChart.tsx`:

```tsx
interface PhaseDurationChartProps {
  phaseDurations: Record<string, number>; // {phase: seconds}
}

export function PhaseDurationChart({ phaseDurations }: PhaseDurationChartProps) {
  // Horizontal bar chart showing duration of each phase
  // Similar to existing cost breakdown chart but for time
  // Color-code bars (green for fast, yellow for medium, red for slow)
}
```

### 4. Type Definition Updates

Update `app/client/src/types/api.types.ts`:

```typescript
class WorkflowHistoryItem(BaseModel):
    # ... existing fields ...

    # Performance metrics
    phase_durations: Optional[Dict[str, int]] = Field(None, description="Duration in seconds per phase")
    idle_time_seconds: Optional[int] = Field(None, description="Idle time between phases")
    bottleneck_phase: Optional[str] = Field(None, description="Phase that took longest")

    # Error analysis
    error_category: Optional[str] = Field(None, description="Categorized error type")
    retry_reasons: Optional[List[str]] = Field(None, description="List of retry trigger reasons")
    error_phase_distribution: Optional[Dict[str, int]] = Field(None, description="Error count by phase")
    recovery_time_seconds: Optional[int] = Field(None, description="Time spent in error recovery")

    # Complexity tracking
    complexity_estimated: Optional[str] = Field(None, description="Estimated complexity (low/medium/high)")
    complexity_actual: Optional[str] = Field(None, description="Actual complexity (low/medium/high)")
```

## Acceptance Criteria

- [ ] Database migration created and runs successfully
- [ ] Phase duration calculation works from cost_breakdown data
- [ ] Bottleneck detection identifies phases >30% of total time
- [ ] Error categorization maps common error messages to types
- [ ] Retry reasons tracked when workflows retry
- [ ] PhaseDurationChart component displays horizontal bar chart
- [ ] Performance Analysis section shows in WorkflowHistoryCard details
- [ ] Bottleneck alert displays when detected
- [ ] Error Analysis section shows categorized errors
- [ ] Retry reasons list displays when available
- [ ] Error phase distribution shows error counts by phase
- [ ] All new fields gracefully handle null/missing data
- [ ] No TypeScript errors or console warnings
- [ ] Existing Phase 1 features still work correctly
- [ ] Database sync populates new fields for existing workflows

## Testing Notes

Test with workflows that:
1. Have complete cost_breakdown with timestamps (calculate phase durations)
2. Have clear bottleneck (one phase 2x longer than others)
3. Have retry_count > 0 (test retry reason tracking)
4. Failed with error_message (test error categorization)
5. No cost_breakdown (graceful degradation)

## Files to Create/Modify

**New Files:**
- `app/server/db/migrations/002_add_performance_metrics.sql`
- `app/client/src/components/PhaseDurationChart.tsx`

**Modified Files:**
- `app/server/core/workflow_history.py` - Add metric calculation functions
- `app/client/src/components/WorkflowHistoryCard.tsx` - Add new sections
- `app/client/src/types/api.types.ts` - Update types
- `app/server/core/data_models.py` - Update Pydantic models

## Notes

- Phase 2 focuses on **performance and error diagnostics**
- Enables data-driven optimization decisions
- Sets foundation for Phase 3 (predictive analytics)
- All metrics calculated from existing data where possible
