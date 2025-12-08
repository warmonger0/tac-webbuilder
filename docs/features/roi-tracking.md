# ROI Tracking System

**Session 12 - Closed-Loop ROI Tracking**

## Overview

The ROI Tracking System completes the automation feedback loop by measuring actual savings from approved patterns, validating their effectiveness, and providing data for confidence score updates. This system enables data-driven decisions about pattern automation and identifies underperforming patterns for review.

## Closed-Loop Workflow

```
Pattern Detection → Review & Approval → Execution → ROI Measurement → Confidence Update
        ↑                                                                        ↓
        └────────────────────────────────────────────────────────────────────────┘
                              (Session 13: Confidence updating)
```

### Key Components

1. **Pattern Executions**: Track individual pattern usage instances
2. **ROI Summaries**: Aggregated metrics per pattern
3. **Effectiveness Ratings**: Categorize pattern performance
4. **ROI Reports**: Comprehensive analysis for decision-making

## Database Schema

### pattern_executions

Tracks individual pattern execution instances with actual vs estimated metrics.

```sql
CREATE TABLE pattern_executions (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    workflow_id INTEGER,
    execution_time_seconds REAL NOT NULL,
    estimated_time_seconds REAL NOT NULL,
    actual_cost REAL NOT NULL,
    estimated_cost REAL NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id),
    FOREIGN KEY (workflow_id) REFERENCES workflow_history(id)
);
```

**Indexes:**
- `idx_pattern_executions_pattern` on `pattern_id`
- `idx_pattern_executions_workflow` on `workflow_id`
- `idx_pattern_executions_date` on `executed_at`
- `idx_pattern_executions_success` on `success`

### pattern_roi_summary

Aggregated ROI metrics per pattern for quick access and analysis.

```sql
CREATE TABLE pattern_roi_summary (
    pattern_id TEXT PRIMARY KEY,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    total_time_saved_seconds REAL DEFAULT 0.0,
    total_cost_saved_usd REAL DEFAULT 0.0,
    average_time_saved_seconds REAL DEFAULT 0.0,
    average_cost_saved_usd REAL DEFAULT 0.0,
    roi_percentage REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id)
);
```

**Indexes:**
- `idx_pattern_roi_success_rate` on `success_rate`
- `idx_pattern_roi_savings` on `total_cost_saved_usd`
- `idx_pattern_roi_percentage` on `roi_percentage`

## ROI Calculation Methodology

### Time Savings

```
Time Saved = Estimated Time - Actual Time
```

Only successful executions contribute to time savings.

### Cost Savings

```
Cost Saved = Estimated Cost - Actual Cost
```

Based on actual API usage vs estimated usage at approval time.

### ROI Percentage

```
ROI % = (Total Cost Saved / Total Investment) × 100
```

Where:
- **Total Cost Saved**: Sum of cost savings across all successful executions
- **Total Investment**: Sum of estimated costs for successful executions

### Success Rate

```
Success Rate = Successful Executions / Total Executions
```

## Effectiveness Rating Criteria

The system categorizes patterns into effectiveness tiers:

### Excellent ⭐⭐⭐
- **Success Rate**: ≥ 95%
- **ROI**: ≥ 200%
- **Action**: Continue automation, consider expanding to similar workflows

### Good ⭐⭐
- **Success Rate**: ≥ 85%
- **ROI**: ≥ 100%
- **Action**: Monitor for continued effectiveness

### Acceptable ⭐
- **Success Rate**: ≥ 70%
- **ROI**: ≥ 50%
- **Action**: Investigate failure cases, consider refinements

### Poor ⚠️
- **Success Rate**: < 70% OR
- **ROI**: < 0%
- **Action**: Review pattern logic, consider refinements or revocation

### Failed ❌
- **Success Rate**: Significantly low
- **ROI**: Negative
- **Action**: Immediate revocation recommended, investigate failures

## API Endpoints

### POST /api/roi-tracking/executions

Record a pattern execution instance.

**Request Body:**
```json
{
  "pattern_id": "test-retry-automation",
  "workflow_id": 123,
  "execution_time_seconds": 45.2,
  "estimated_time_seconds": 60.0,
  "actual_cost": 0.012,
  "estimated_cost": 0.015,
  "success": true,
  "error_message": null,
  "executed_at": "2024-12-08T12:00:00Z"
}
```

**Response:**
```json
{
  "message": "Execution recorded successfully",
  "execution_id": 1,
  "pattern_id": "test-retry-automation"
}
```

### GET /api/roi-tracking/pattern/{pattern_id}

Get ROI summary for a specific pattern.

**Response:**
```json
{
  "pattern_id": "test-retry-automation",
  "total_executions": 150,
  "successful_executions": 148,
  "success_rate": 0.987,
  "total_time_saved_seconds": 3450.0,
  "total_cost_saved_usd": 425.50,
  "average_time_saved_seconds": 23.0,
  "average_cost_saved_usd": 2.84,
  "roi_percentage": 312.0,
  "last_updated": "2024-12-08T12:00:00Z"
}
```

### GET /api/roi-tracking/summary

Get ROI summaries for all patterns, ordered by cost savings.

### GET /api/roi-tracking/report/{pattern_id}

Generate comprehensive ROI report including executions, summary, effectiveness rating, and recommendations.

### GET /api/roi-tracking/top-performers

Get top performing patterns by ROI (requires ≥5 executions).

**Query Parameters:**
- `limit` (default: 10, max: 50)

### GET /api/roi-tracking/underperformers

Get underperforming patterns by success rate and ROI (requires ≥3 executions).

**Query Parameters:**
- `limit` (default: 10, max: 50)

### GET /api/roi-tracking/effectiveness/{pattern_id}

Calculate effectiveness rating and get recommendation.

**Response:**
```json
{
  "pattern_id": "test-retry-automation",
  "effectiveness_rating": "excellent",
  "success_rate": 0.987,
  "roi_percentage": 312.0,
  "total_executions": 150,
  "recommendation": "Exceptional performance! Pattern achieves 98.7% success rate and 312.0% ROI..."
}
```

## CLI Tool Usage

### Show Overall Summary

```bash
python scripts/roi_report.py --summary
```

**Output:**
```
================================================================================
PATTERN ROI SUMMARY
================================================================================

TOP PERFORMERS (by ROI)
1. Pattern: test-retry-automation
   Executions: 150 (148 successful, 98.7% success rate)
   Time saved: 3,450 seconds (57.5 minutes)
   Cost saved: $425.50
   ROI: 312%
   Rating: EXCELLENT ⭐⭐⭐
...
```

### Show Pattern-Specific Report

```bash
python scripts/roi_report.py --pattern-id test-retry-automation
```

### Show Top Performers

```bash
python scripts/roi_report.py --top-performers --limit 10
```

### Show Underperformers

```bash
python scripts/roi_report.py --underperformers --limit 5
```

### Generate Markdown Report

```bash
python scripts/roi_report.py --report --output roi_report.md
```

## Integration with ADW Workflows

### Recording Pattern Executions

From ADW workflows, use the observability module to track pattern execution:

```python
from adw_modules.observability import track_pattern_execution
import time

# Before executing pattern
start_time = time.time()

try:
    # Execute automated pattern
    result = execute_pattern(pattern_id="test-retry-automation")
    success = True
    error_msg = None
except Exception as e:
    success = False
    error_msg = str(e)

# After execution
end_time = time.time()
execution_time = end_time - start_time

# Track execution for ROI
track_pattern_execution(
    pattern_id="test-retry-automation",
    workflow_id=workflow_id,
    execution_time_seconds=execution_time,
    estimated_time_seconds=60.0,  # From pattern approval
    actual_cost=calculate_cost(execution_time),
    estimated_cost=0.015,  # From pattern approval
    success=success,
    error_message=error_msg
)
```

## Feeding ROI Data to Confidence Updates

ROI tracking data serves as input for Session 13's confidence updating system:

### Data Points for Confidence Adjustment

1. **Success Rate**: Higher success rate → increased confidence
2. **ROI Percentage**: Higher ROI → increased confidence
3. **Total Executions**: More data → more stable confidence
4. **Recent Trend**: Improving performance → increase confidence
5. **Effectiveness Rating**: Direct mapping to confidence level

### Example Confidence Update Logic (Session 13)

```python
def update_confidence_from_roi(pattern_id: str) -> float:
    """Update pattern confidence based on ROI data."""
    roi_summary = roi_service.get_pattern_roi(pattern_id)
    effectiveness = roi_service.calculate_effectiveness(pattern_id)

    # Base confidence from effectiveness
    base_confidence = {
        'excellent': 0.95,
        'good': 0.85,
        'acceptable': 0.70,
        'poor': 0.50,
        'failed': 0.30
    }[effectiveness]

    # Adjust based on sample size
    if roi_summary.total_executions >= 50:
        confidence_boost = 0.05
    elif roi_summary.total_executions >= 20:
        confidence_boost = 0.02
    else:
        confidence_boost = 0.0

    return min(base_confidence + confidence_boost, 1.0)
```

## Monitoring and Alerts

### Recommended Alerts

1. **Pattern Failure Spike**: Success rate drops below 70%
2. **Negative ROI**: Cost savings become negative
3. **Underutilization**: Pattern approved but rarely executed
4. **Performance Degradation**: Success rate declining over time

### Dashboard Metrics

- Total patterns tracked
- Total executions this month
- Total cost saved this month
- Average success rate across all patterns
- Top 5 performers by ROI
- Patterns requiring attention (poor/failed ratings)

## Best Practices

### 1. Accurate Estimates

Ensure estimated time and cost at approval time are realistic:
- Base on historical data
- Include buffer for edge cases
- Update estimates as patterns evolve

### 2. Timely Recording

Record executions immediately after completion:
- Don't batch executions
- Include both successes and failures
- Capture detailed error messages

### 3. Regular Review

Review ROI reports regularly:
- Weekly: Check for new underperformers
- Monthly: Full portfolio review
- Quarterly: Pattern optimization planning

### 4. Feedback Loop

Use ROI data to improve patterns:
- Investigate failures
- Refine pattern logic
- Update estimates based on actuals
- Consider expanding successful patterns

## Testing

Run tests:
```bash
cd app/server
pytest tests/services/test_roi_tracking_service.py -v
```

**Test Coverage:**
- ✅ Record execution
- ✅ Update ROI summary
- ✅ Get pattern ROI
- ✅ Calculate effectiveness (excellent, good, poor)
- ✅ Get top performers
- ✅ Get underperformers
- ✅ Generate ROI report

All 11 tests passing.

## Future Enhancements

### Session 13: Confidence Updating
- Automatic confidence score adjustments based on ROI
- Pattern promotion/demotion based on performance
- Trigger re-review for degrading patterns

### Session 14+: Advanced Analytics
- ROI trend analysis over time
- Predictive ROI modeling
- Pattern similarity scoring
- Cost optimization recommendations

## Troubleshooting

### Issue: Executions not being recorded

**Symptoms:** API calls succeeding but no data in database

**Solutions:**
1. Check backend logs for errors
2. Verify pattern exists in `pattern_approvals`
3. Ensure workflow_id is valid (or use NULL)
4. Check PostgreSQL connection

### Issue: ROI percentages seem wrong

**Symptoms:** Negative ROI when pattern appears successful

**Solutions:**
1. Verify estimated costs at approval were accurate
2. Check if actual_cost includes all API calls
3. Review execution_time_seconds calculation
4. Ensure only successful executions counted in savings

### Issue: Effectiveness rating unexpected

**Symptoms:** Pattern rated "poor" but high success rate

**Solutions:**
1. Check ROI percentage (may be below threshold)
2. Review effectiveness criteria in documentation
3. Ensure sufficient executions for accurate rating
4. Verify estimated vs actual costs are reasonable

## Related Documentation

- [Pattern Approval System](./pattern-approval-system.md) - Session 6
- [Daily Pattern Analysis](./daily-pattern-analysis.md) - Session 7
- [Observability & Logging](./observability-and-logging.md) - Sessions 2-3

## Support

For issues or questions about ROI tracking:
1. Check troubleshooting section above
2. Review API endpoint documentation
3. Run tests to verify system health
4. Check backend logs for errors
