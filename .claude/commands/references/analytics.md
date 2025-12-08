# Analytics & ROI Tracking Quick Reference

## Overview (Sessions 9-13)
**Five analytics systems for measuring automation impact:**
- **Session 9:** Cost Attribution Analytics
- **Session 10:** Error Analytics
- **Session 11:** Latency Analytics
- **Session 12:** Closed-Loop ROI Tracking
- **Session 13:** Confidence Updating System

All analytics systems are CLI-based and query the `hook_events` and `pattern_approvals` tables.

## 1. Cost Attribution Analytics (Session 9)

**Purpose:** Break down costs by ADW, session, phase, and tool usage

**CLI:** `scripts/cost_attribution.py`

**Usage:**
```bash
# Analyze last 7 days
python scripts/cost_attribution.py --days 7

# With detailed report
python scripts/cost_attribution.py --days 7 --report

# By specific ADW
python scripts/cost_attribution.py --adw-id adw_20251208_123456
```

**Metrics Calculated:**
- Total costs by ADW workflow
- Cost breakdown by SDLC phase (Plan, Build, Test, etc.)
- Tool-level cost attribution
- Session-level spend analysis
- Time-series cost trends

**Output:**
- Console summary (colored tables)
- Optional markdown report in `logs/`
- Cost per phase, cost per tool, total spend

**Data Sources:**
- `hook_events` table (tool usage, duration, context)
- `workflow_history` table (ADW metadata)

## 2. Error Analytics (Session 10)

**Purpose:** Analyze error frequency, categorize failures, identify root causes

**CLI:** `scripts/error_analytics.py`

**Usage:**
```bash
# Analyze errors
python scripts/error_analytics.py

# With detailed report
python scripts/error_analytics.py --report

# Filter by ADW
python scripts/error_analytics.py --adw-id adw_20251208_123456
```

**Metrics Calculated:**
- Error frequency by phase
- Error categorization (syntax, permission, timeout, etc.)
- Root cause analysis
- Error rate trends
- Top error messages

**Output:**
- Error frequency tables
- Error categories (grouped)
- Root cause summaries
- Optional markdown report

**Data Sources:**
- `hook_events` table (success=false, error messages)
- Pattern matching on error messages

## 3. Latency Analytics (Session 11)

**Purpose:** Identify performance bottlenecks, measure percentiles, track slow operations

**CLI:** `scripts/latency_analytics.py`

**Usage:**
```bash
# Analyze latency
python scripts/latency_analytics.py

# With threshold filtering (5 seconds)
python scripts/latency_analytics.py --threshold 5000

# Detailed report
python scripts/latency_analytics.py --report --threshold 3000
```

**Metrics Calculated:**
- P50, P95, P99 latency by tool
- Slowest operations
- Latency trends over time
- Bottleneck identification
- Phase-level performance

**Output:**
- Latency percentile tables
- Slowest operations (top 10)
- Performance bottleneck report
- Optional markdown report

**Data Sources:**
- `hook_events` table (duration_ms field)
- Percentile calculations from duration distributions

## 4. Closed-Loop ROI Tracking (Session 12)

**Purpose:** Track pattern detection → approval → implementation → actual savings

**CLI:** `scripts/roi_tracker.py`

**Usage:**
```bash
# Full ROI report
python scripts/roi_tracker.py --report

# By pattern status
python scripts/roi_tracker.py --status approved

# Specific pattern
python scripts/roi_tracker.py --pattern-id abc123def456
```

**Metrics Calculated:**
- Estimated vs actual savings
- Pattern implementation rate
- ROI by pattern category
- Time to value (detection → implementation)
- Approval conversion rate

**Workflow:**
```
Pattern Detected (analyze_daily_patterns.py)
    ↓
Estimated Savings Calculated
    ↓
Manual/Auto Approval (pattern_approvals table)
    ↓
Pattern Implemented (status = 'implemented')
    ↓
Actual Savings Tracked (cost_savings_log table)
    ↓
ROI Report (estimated vs actual)
```

**Output:**
- ROI summary by pattern
- Estimated vs actual savings comparison
- Implementation timeline
- Optional markdown report

**Data Sources:**
- `pattern_approvals` table (estimated savings, status)
- `cost_savings_log` table (actual savings)
- `operation_patterns` table (pattern metadata)

## 5. Confidence Updating System (Session 13)

**Purpose:** Automatically update pattern confidence scores based on implementation outcomes

**CLI:** `scripts/confidence_updater.py`

**Usage:**
```bash
# Auto-update confidence scores
python scripts/confidence_updater.py --auto

# Dry run (preview changes)
python scripts/confidence_updater.py --dry-run

# Manual review
python scripts/confidence_updater.py --manual
```

**Confidence Calculation:**
- Initial confidence from frequency analysis
- Updated based on approval/rejection history
- Adjusted for implementation success/failure
- Factors: occurrence count, savings accuracy, error rate

**Adjustment Rules:**
- Approved patterns: +0.05 to +0.15 confidence
- Rejected patterns: -0.10 to -0.30 confidence
- Implemented with positive ROI: +0.20 confidence
- Implemented with negative ROI: -0.40 confidence

**Output:**
- Updated confidence scores in `pattern_approvals`
- Change log (old vs new confidence)
- Reasoning for each adjustment

**Data Sources:**
- `pattern_approvals` table (status, current confidence)
- `cost_savings_log` table (implementation outcomes)
- `operation_patterns` table (historical data)

## Common Analytics Workflows

### Daily Analytics Review
```bash
# Run all analytics for last 24 hours
python scripts/analyze_daily_patterns.py --report
python scripts/cost_attribution.py --days 1 --report
python scripts/error_analytics.py --report
python scripts/latency_analytics.py --threshold 3000 --report
python scripts/roi_tracker.py --report
python scripts/confidence_updater.py --auto
```

### Weekly ROI Review
```bash
# Cost breakdown
python scripts/cost_attribution.py --days 7 --report

# Pattern ROI
python scripts/roi_tracker.py --report

# Update confidence based on weekly outcomes
python scripts/confidence_updater.py --auto
```

### Performance Investigation
```bash
# Find slow operations
python scripts/latency_analytics.py --threshold 5000 --report

# Identify error hotspots
python scripts/error_analytics.py --report

# Cost impact of errors
python scripts/cost_attribution.py --days 7
```

## Database Schema (Analytics Tables)

### pattern_approvals (Session 7)
```sql
CREATE TABLE pattern_approvals (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT UNIQUE NOT NULL,
    tool_sequence TEXT NOT NULL,
    confidence_score REAL,  -- Updated by confidence_updater.py
    occurrence_count INTEGER,
    estimated_savings_usd REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### cost_savings_log (Existing, used by ROI tracking)
```sql
CREATE TABLE cost_savings_log (
    log_id SERIAL PRIMARY KEY,
    optimization_type TEXT NOT NULL,
    baseline_cost REAL,
    actual_cost REAL,
    cost_saved_usd REAL,  -- Actual savings
    pattern_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Reports Location
All CLI tools support `--report` flag to generate markdown reports in:
```
logs/
  pattern_analysis_YYYYMMDD_HHMMSS.md
  cost_attribution_YYYYMMDD_HHMMSS.md
  error_analytics_YYYYMMDD_HHMMSS.md
  latency_analytics_YYYYMMDD_HHMMSS.md
  roi_tracking_YYYYMMDD_HHMMSS.md
```

## When to Use Which Tool

| Scenario | Tool |
|----------|------|
| Find automation opportunities | `analyze_daily_patterns.py` |
| Understand cost breakdown | `cost_attribution.py` |
| Investigate failures | `error_analytics.py` |
| Find performance bottlenecks | `latency_analytics.py` |
| Measure pattern ROI | `roi_tracker.py` |
| Improve pattern accuracy | `confidence_updater.py` |

## When to Load Full Documentation

**Load full docs when:**
- Implementing new analytics features
- Customizing confidence calculation logic
- Adding new error categorization
- Extending cost attribution models
- Integrating analytics with UI

**Full Documentation:**
- Session 9 prompt: `archives/prompts/2025/SESSION_9_PROMPT.md`
- Session 10 prompt: `archives/prompts/2025/SESSION_10_PROMPT.md`
- Session 11 prompt: `archives/prompts/2025/SESSION_11_PROMPT.md`
- Session 12 prompt: `archives/prompts/2025/SESSION_12_PROMPT.md`
- Session 13 prompt: `archives/prompts/2025/SESSION_13_PROMPT.md`
