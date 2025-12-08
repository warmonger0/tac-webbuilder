# Confidence Updating System

**Session:** 13
**Status:** Implemented
**Last Updated:** 2025-12-08

## Overview

The Confidence Updating System automatically adjusts pattern confidence scores based on actual performance data from the ROI tracking system. This creates a self-improving feedback loop where patterns with proven effectiveness gain higher confidence, while underperforming patterns are downgraded or flagged for review.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Confidence Update Flow                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Pattern        │      │  ROI Tracking    │      │  Confidence      │
│   Executions     │─────▶│  Service         │─────▶│  Update Service  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        │                          │                         │
        │                          │                         │
        ▼                          ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ pattern_         │      │ pattern_roi_     │      │ pattern_         │
│ executions       │      │ summary          │      │ approvals        │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                              │
                                                              ▼
                                                     ┌──────────────────┐
                                                     │ pattern_         │
                                                     │ confidence_      │
                                                     │ history          │
                                                     └──────────────────┘
```

## Core Components

### 1. Confidence Calculation Algorithm

The confidence score is calculated using a multi-factor formula:

```python
new_confidence = base_confidence + roi_bonus + execution_bonus - roi_penalty

where:
  base_confidence = success_rate (0.0-1.0)
  roi_bonus = min(0.1, roi_percentage / 1000)
  execution_bonus = min(0.05, total_executions / 1000)
  roi_penalty = abs(roi_percentage) / 100  (if ROI < 0)

  # Final score clamped to [0.0, 1.0]
```

**Example Calculations:**

| Pattern Type | Success Rate | ROI % | Executions | Confidence Score |
|-------------|-------------|-------|------------|------------------|
| Excellent   | 98.7%       | 312%  | 150        | 1.00 (maxed)     |
| Good        | 90.0%       | 180%  | 75         | 0.97             |
| Acceptable  | 80.0%       | 60%   | 30         | 0.83             |
| Poor        | 60.0%       | -25%  | 20         | 0.35             |

### 2. Database Schema

**Table: `pattern_confidence_history`**

```sql
CREATE TABLE pattern_confidence_history (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    old_confidence REAL NOT NULL,
    new_confidence REAL NOT NULL,
    adjustment_reason TEXT NOT NULL,
    roi_data JSONB,
    updated_by TEXT DEFAULT 'system',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id) ON DELETE CASCADE
);

CREATE INDEX idx_confidence_history_pattern ON pattern_confidence_history(pattern_id);
CREATE INDEX idx_confidence_history_date ON pattern_confidence_history(updated_at DESC);
CREATE INDEX idx_confidence_history_pattern_date ON pattern_confidence_history(pattern_id, updated_at DESC);
```

### 3. Status Change Recommendations

The system automatically recommends status changes based on performance thresholds:

| Current Status | Performance Criteria | Recommended Status | Severity |
|---------------|---------------------|-------------------|----------|
| Approved      | Success < 70% OR ROI < 0% | Rejected | High |
| Pending       | Success > 95% AND ROI > 200% | Auto-approved | Medium |
| Approved      | 70% ≤ Success < 80% OR 0% ≤ ROI < 50% | Manual-review | Low |

## API Endpoints

### POST `/api/confidence/update/{pattern_id}`

Update confidence score for a single pattern.

**Query Parameters:**
- `dry_run` (boolean, optional): Calculate but don't persist changes

**Response:**
```json
{
  "message": "Confidence updated successfully",
  "pattern_id": "test-retry-automation",
  "old_confidence": 0.80,
  "new_confidence": 0.92,
  "change": 0.12,
  "adjustment_reason": "Confidence increased by 0.120 based on performance: 150 executions, 98.7% success rate, 312.0% ROI",
  "roi_data": {
    "total_executions": 150,
    "success_rate": 0.987,
    "roi_percentage": 312.0,
    "total_cost_saved_usd": 425.50
  },
  "dry_run": false
}
```

### POST `/api/confidence/update-all`

Update confidence scores for all patterns with ROI data.

**Query Parameters:**
- `dry_run` (boolean, optional): Calculate but don't persist changes

**Response:**
```json
{
  "message": "Confidence updates completed",
  "total_patterns": 15,
  "increased": 8,
  "decreased": 5,
  "unchanged": 2,
  "average_change": 0.042,
  "max_increase": 0.15,
  "max_decrease": -0.08,
  "changes": {
    "pattern-1": 0.12,
    "pattern-2": -0.05,
    "pattern-3": 0.08
  },
  "dry_run": false
}
```

### GET `/api/confidence/history/{pattern_id}`

Get confidence change history for a pattern.

**Query Parameters:**
- `limit` (integer, optional, default: 50): Maximum number of records

**Response:**
```json
[
  {
    "id": 3,
    "pattern_id": "test-retry-automation",
    "old_confidence": 0.80,
    "new_confidence": 0.92,
    "change": 0.12,
    "adjustment_reason": "Improved performance: 150 executions, 98.7% success, 312.0% ROI",
    "roi_data": {
      "total_executions": 150,
      "success_rate": 0.987,
      "roi_percentage": 312.0,
      "total_cost_saved_usd": 425.50
    },
    "updated_by": "system",
    "updated_at": "2025-12-08T03:00:00Z"
  }
]
```

### GET `/api/confidence/recommendations`

Get status change recommendations based on performance.

**Response:**
```json
{
  "total_recommendations": 3,
  "high_severity": [
    {
      "pattern_id": "poor-performer",
      "current_status": "approved",
      "recommended_status": "rejected",
      "reason": "Low performance: 60.0% success rate, -10.0% ROI over 25 executions. Consider revocation or pattern refinement.",
      "confidence_score": 0.65,
      "roi_percentage": -10.0
    }
  ],
  "medium_severity": [
    {
      "pattern_id": "excellent-pending",
      "current_status": "pending",
      "recommended_status": "auto-approved",
      "reason": "Excellent performance: 97.0% success rate, 250.0% ROI over 50 executions. Strong candidate for auto-approval.",
      "confidence_score": 0.98,
      "roi_percentage": 250.0
    }
  ],
  "low_severity": [
    {
      "pattern_id": "borderline-approved",
      "current_status": "approved",
      "recommended_status": "manual-review",
      "reason": "Borderline performance: 75.0% success rate, 40.0% ROI over 30 executions. Recommend manual review to assess continued approval.",
      "confidence_score": 0.75,
      "roi_percentage": 40.0
    }
  ]
}
```

## CLI Usage

### Update All Patterns

```bash
# Dry run (see what would change)
python scripts/update_confidence_scores.py --update-all --dry-run

# Live update
python scripts/update_confidence_scores.py --update-all
```

**Output:**
```
================================================================================
CONFIDENCE UPDATE - LIVE UPDATE
================================================================================

Processed 15 patterns:

  ↑ Increased confidence: 8
  ↓ Decreased confidence: 5
  = Unchanged confidence: 2
  Average change: +0.042

--------------------------------------------------------------------------------
TOP CONFIDENCE INCREASES
--------------------------------------------------------------------------------

1. test-retry-automation
   Change: +0.120

2. build-optimization
   Change: +0.095

...

================================================================================
CONFIDENCE UPDATE COMPLETE
================================================================================
```

### Update Single Pattern

```bash
python scripts/update_confidence_scores.py --pattern-id test-retry-automation
```

### Show Recommendations

```bash
python scripts/update_confidence_scores.py --recommendations
```

**Output:**
```
================================================================================
STATUS CHANGE RECOMMENDATIONS
================================================================================

Found 3 recommendations:

  🔴 High severity: 1
  🟡 Medium severity: 1
  🟢 Low severity: 1

================================================================================
🔴 HIGH SEVERITY - IMMEDIATE ACTION REQUIRED
================================================================================

1. Pattern: poor-performer
   Current: approved → Recommended: rejected
   Confidence: 0.650 | ROI: -10.0%
   Reason: Low performance: 60.0% success rate, -10.0% ROI over 25 executions...
```

### View Confidence History

```bash
python scripts/update_confidence_scores.py --history --pattern-id test-retry-automation
```

## Scheduled Automation

### Cron Job

The system includes a cron wrapper for daily updates:

```bash
# Edit crontab
crontab -e

# Add daily update at 3:00 AM
0 3 * * * /path/to/tac-webbuilder/scripts/cron/update_confidence.sh
```

**Script:** `scripts/cron/update_confidence.sh`

**Scheduling:**
- Runs daily at 3:00 AM
- Executes after pattern analysis (2:00 AM)
- Logs to `logs/confidence_update_YYYYMMDD.log`
- Cleans up logs older than 30 days

**Log Output:**
```
[2025-12-08 03:00:00] ==========================================
[2025-12-08 03:00:00] Starting daily confidence score updates
[2025-12-08 03:00:00] ==========================================
[2025-12-08 03:00:00] Using virtual environment: /path/to/.venv
[2025-12-08 03:00:00] Updating confidence scores for all patterns...
[2025-12-08 03:00:15] ✓ Confidence scores updated successfully
[2025-12-08 03:00:15] Generating status change recommendations...
[2025-12-08 03:00:16] ✓ Recommendations generated successfully
[2025-12-08 03:00:16] Cleaning up old log files...
[2025-12-08 03:00:16] ✓ Log cleanup complete
[2025-12-08 03:00:16] ==========================================
[2025-12-08 03:00:16] Daily confidence score updates completed
[2025-12-08 03:00:16] ==========================================
```

## Integration with Pattern Lifecycle

The confidence updating system integrates with the pattern approval workflow:

```
Pattern Discovery → Pattern Analysis → Pattern Review → Pattern Approval
                                             ↓
                                      Initial Confidence
                                             ↓
                                       ROI Tracking
                                             ↓
                                    Confidence Updates ←─────┐
                                             │               │
                                             ↓               │
                                   Status Recommendations    │
                                             │               │
                                             ↓               │
                                    Manual/Auto Actions      │
                                             │               │
                                             └───────────────┘
```

### Integration Points

1. **Pattern Approval** (initial confidence):
   - New patterns start with discovery-based confidence
   - Typically 0.60-0.75 range

2. **ROI Tracking** (performance data):
   - Execution success/failure
   - Time saved vs estimated
   - Cost saved vs invested
   - Calculated ROI percentage

3. **Confidence Updates** (automatic adjustment):
   - Daily batch updates via cron
   - On-demand via API or CLI
   - Logged to history table

4. **Status Changes** (review and action):
   - High severity: immediate review required
   - Medium severity: auto-approval candidates
   - Low severity: periodic review

## Monitoring

### Key Metrics

Track confidence update health with these queries:

```sql
-- Patterns with declining confidence
SELECT
    pattern_id,
    old_confidence,
    new_confidence,
    new_confidence - old_confidence AS change,
    adjustment_reason
FROM pattern_confidence_history
WHERE new_confidence < old_confidence
ORDER BY (new_confidence - old_confidence) ASC
LIMIT 10;

-- Average confidence change over time
SELECT
    DATE(updated_at) AS date,
    COUNT(*) AS updates,
    AVG(new_confidence - old_confidence) AS avg_change
FROM pattern_confidence_history
WHERE updated_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(updated_at)
ORDER BY date DESC;

-- Patterns due for status review
SELECT
    pa.pattern_id,
    pa.status,
    pa.confidence_score,
    rs.success_rate,
    rs.roi_percentage,
    rs.total_executions
FROM pattern_approvals pa
INNER JOIN pattern_roi_summary rs ON pa.pattern_id = rs.pattern_id
WHERE
    (pa.status = 'approved' AND (rs.success_rate < 0.70 OR rs.roi_percentage < 0))
    OR (pa.status = 'pending' AND rs.success_rate > 0.95 AND rs.roi_percentage > 200)
ORDER BY rs.success_rate ASC;
```

## Performance Impact

**Database:**
- Confidence history grows ~15-50 records/day
- Indexes optimize pattern and date queries
- Minimal impact on workflow execution

**Computation:**
- Batch updates: 50-100 patterns in ~5 seconds
- Single update: < 100ms
- ROI calculation already performed

**Benefits:**
- Self-improving pattern system
- Automatic quality control
- Data-driven pattern lifecycle
- Reduced manual review burden

## Troubleshooting

### Confidence Not Updating

**Check ROI Data:**
```bash
docker exec tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder \
  -c "SELECT * FROM pattern_roi_summary WHERE pattern_id = 'your-pattern-id';"
```

**Check Confidence History:**
```bash
docker exec tac-webbuilder-postgres psql -U tac_user -d tac_webbuilder \
  -c "SELECT * FROM pattern_confidence_history WHERE pattern_id = 'your-pattern-id' ORDER BY updated_at DESC LIMIT 5;"
```

### Unexpected Confidence Score

Run dry-run to see calculation details:
```bash
python scripts/update_confidence_scores.py --pattern-id your-pattern-id --dry-run
```

### Cron Job Not Running

Check cron logs:
```bash
cat logs/confidence_update_$(date +%Y%m%d).log
```

Verify crontab entry:
```bash
crontab -l | grep update_confidence
```

## Future Enhancements

- [ ] Machine learning-based confidence prediction
- [ ] Pattern similarity clustering for confidence transfer
- [ ] A/B testing framework for confidence thresholds
- [ ] Real-time confidence updates (streaming)
- [ ] Confidence trend visualization in dashboard
- [ ] Custom confidence formulas per pattern type

## Related Documentation

- [ROI Tracking](./roi-tracking.md) - Performance measurement foundation
- [Pattern Review System](./pattern-review-system.md) - Pattern approval workflow
- [Observability & Logging](./observability-and-logging.md) - Hook events and tracking

## See Also

- **Migration:** `app/server/db/migrations/019_add_confidence_history_postgres.sql`
- **Service:** `app/server/services/confidence_update_service.py`
- **Routes:** `app/server/routes/confidence_update_routes.py`
- **CLI:** `scripts/update_confidence_scores.py`
- **Cron:** `scripts/cron/update_confidence.sh`
- **Tests:** `app/server/tests/services/test_confidence_update_service.py`
