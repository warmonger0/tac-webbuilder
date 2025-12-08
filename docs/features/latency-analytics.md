# Workflow Latency Analytics System

## Overview

The Workflow Latency Analytics System provides comprehensive performance analysis and bottleneck identification for ADW workflows. It analyzes execution times by phase, calculates percentiles (p50, p95, p99), detects performance bottlenecks, tracks latency trends over time, and generates optimization recommendations to improve workflow speed.

## Features

- **Latency Summary** - Overall workflow execution time statistics with percentiles
- **Phase Latency Analysis** - Detailed breakdown of execution times by workflow phase
- **Bottleneck Detection** - Automatically identify slow phases exceeding thresholds
- **Trend Analysis** - Track latency patterns over time with moving averages
- **Optimization Recommendations** - Actionable suggestions to reduce execution times
- **CLI Reporting** - Generate detailed markdown reports for performance tracking

## Architecture

### Components

1. **Latency Analytics Service** (`services/latency_analytics_service.py`)
   - Core business logic for latency analysis
   - Statistical calculations (percentiles, outliers)
   - Bottleneck detection and optimization recommendations

2. **API Routes** (`routes/latency_analytics_routes.py`)
   - RESTful endpoints for latency data access
   - 5 endpoints for different analysis types

3. **CLI Tool** (`scripts/analyze_latency.py`)
   - Interactive command-line interface
   - Markdown report generation
   - Multiple analysis modes

4. **Data Models** (`core/models/workflow.py`)
   - Pydantic models for type safety
   - Response models for API consistency

## API Endpoints

### 1. Latency Summary

**GET** `/api/latency-analytics/summary`

Get overall latency summary statistics including percentiles and slowest phase.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_workflows": 145,
  "average_duration_seconds": 428.5,
  "p50_duration": 385.0,
  "p95_duration": 642.0,
  "p99_duration": 891.0,
  "slowest_phase": "Test",
  "slowest_phase_avg": 156.3
}
```

**Example:**
```bash
curl "http://localhost:8000/api/latency-analytics/summary?days=30"
```

**Interpretation:**
- **p50 (median)**: 50% of workflows complete faster than this
- **p95**: 95% of workflows complete faster than this (common SLA target)
- **p99**: 99% of workflows complete faster than this (tail latency)

### 2. Phase Latency Breakdown

**GET** `/api/latency-analytics/by-phase`

Analyzes execution times broken down by workflow phase with full percentile statistics.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "phase_latencies": {
    "Plan": {
      "p50": 32.0,
      "p95": 56.0,
      "p99": 78.0,
      "average": 38.5,
      "min": 25.0,
      "max": 85.0,
      "std_dev": 12.3,
      "sample_count": 145
    },
    "Build": {
      "p50": 98.0,
      "p95": 156.0,
      "p99": 189.0,
      "average": 112.4,
      "min": 85.0,
      "max": 205.0,
      "std_dev": 28.7,
      "sample_count": 145
    },
    "Test": {
      "p50": 142.0,
      "p95": 198.0,
      "p99": 245.0,
      "average": 156.3,
      "min": 120.0,
      "max": 280.0,
      "std_dev": 35.2,
      "sample_count": 145
    }
  },
  "total_duration_avg": 428.5
}
```

**Example:**
```bash
curl "http://localhost:8000/api/latency-analytics/by-phase?days=30"
```

**Use Cases:**
- Identify which phases contribute most to overall latency
- Compare phase performance across different time periods
- Set performance SLAs for individual phases
- Track impact of optimizations over time

### 3. Bottleneck Detection

**GET** `/api/latency-analytics/bottlenecks`

Identifies phases that consistently exceed latency thresholds.

**Query Parameters:**
- `threshold` (optional): Threshold in seconds (default: 300)
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
[
  {
    "phase": "Test",
    "p95_latency": 198.0,
    "threshold": 300.0,
    "percentage_over_threshold": 5.0,
    "affected_workflows": 7,
    "recommendation": "Enable test result caching, run tests in parallel, skip redundant test suites",
    "estimated_speedup": "30-40% faster with optimization"
  }
]
```

**Example:**
```bash
# Detect phases exceeding 5 minutes (300s)
curl "http://localhost:8000/api/latency-analytics/bottlenecks?threshold=300"

# Stricter threshold (2 minutes)
curl "http://localhost:8000/api/latency-analytics/bottlenecks?threshold=120"
```

**Bottleneck Detection Logic:**
- Flags phases where **p95 latency** exceeds the threshold
- Estimates percentage of workflows affected
- Provides phase-specific optimization recommendations
- Sorted by severity (highest p95 first)

**Common Thresholds:**
- **60s**: Strict performance requirements
- **300s (5min)**: Standard threshold (default)
- **600s (10min)**: Relaxed threshold for complex workflows

### 4. Latency Trends

**GET** `/api/latency-analytics/trends`

Analyzes latency patterns over time with trend detection.

**Query Parameters:**
- `period` (optional): Time period ('day', 'week') - currently only 'day' supported
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "daily_latencies": [
    {
      "date": "2025-11-01",
      "duration": 420.5,
      "workflow_count": 5
    },
    {
      "date": "2025-11-02",
      "duration": 435.2,
      "workflow_count": 6
    }
  ],
  "moving_average": [420.5, 427.8, 430.1, ...],
  "trend_direction": "increasing",
  "percentage_change": 12.5,
  "average_daily_duration": 428.5
}
```

**Example:**
```bash
curl "http://localhost:8000/api/latency-analytics/trends?days=30"
```

**Trend Directions:**
- **increasing**: Latency is getting worse over time (⚠️ action needed)
- **decreasing**: Latency is improving (✅ optimizations working)
- **stable**: No significant change (±5%)

**Use Cases:**
- Detect performance regressions after deployments
- Validate optimization efforts are working
- Identify gradual performance degradation
- Capacity planning and resource allocation

### 5. Optimization Recommendations

**GET** `/api/latency-analytics/recommendations`

Generates actionable optimization recommendations based on latency analysis.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
[
  {
    "target": "Test Phase",
    "current_latency": 156.3,
    "target_latency": 93.8,
    "improvement_percentage": 40.0,
    "actions": [
      "Enable test result caching",
      "Run test suites in parallel",
      "Skip redundant tests for unchanged code",
      "Use test sharding for large test suites"
    ]
  },
  {
    "target": "Build Phase",
    "current_latency": 112.4,
    "target_latency": 67.4,
    "improvement_percentage": 40.0,
    "actions": [
      "Enable dependency caching (pip, npm)",
      "Use incremental builds where possible",
      "Parallelize independent build steps"
    ]
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/latency-analytics/recommendations?days=30"
```

**Recommendation Selection Criteria:**
- Focuses on top 3 slowest phases
- Only includes phases that are >15% of total duration
- Provides specific, actionable optimization steps
- Estimates 40% improvement potential per recommendation

## CLI Usage

The `analyze_latency.py` CLI tool provides comprehensive latency analysis from the command line.

### Installation

```bash
cd /path/to/tac-webbuilder
chmod +x scripts/analyze_latency.py
```

### Commands

#### 1. Show Summary

```bash
python scripts/analyze_latency.py --summary --days 30
```

**Output:**
```
================================================================================
LATENCY ANALYSIS SUMMARY - Last 30 Days
================================================================================

Total workflows analyzed: 145

Average duration:    7.1m
p50 (median):        6.4m
p95:                 10.7m
p99:                 14.9m

Slowest phase:       Test (avg: 2.6m)
================================================================================
```

#### 2. Phase Breakdown

```bash
python scripts/analyze_latency.py --phase --days 30
```

**Output:**
```
================================================================================
PHASE LATENCY BREAKDOWN - Last 30 Days
================================================================================

Phase           p50      p95      p99      Avg   Sample
--------------------------------------------------------------------------------
Test           2.4m     3.3m     4.1m     2.6m      145
Build          1.6m     2.6m     3.1m     1.9m      145
Review         0.8m     1.5m     1.9m     1.0m      145
Plan           0.5m     0.9m     1.3m     0.6m      145
Lint           0.2m     0.5m     0.8m     0.3m      145
--------------------------------------------------------------------------------
Total workflow avg: 7.1m
================================================================================
```

#### 3. Detect Bottlenecks

```bash
python scripts/analyze_latency.py --bottlenecks --threshold 300
```

**Output:**
```
================================================================================
PERFORMANCE BOTTLENECKS - Last 30 Days (Threshold: 300s)
================================================================================

Found 1 bottleneck(s):

1. Test Phase
   p95 Latency:        3.3m
   Threshold:          5.0m
   % Over Threshold:   5.0%
   Affected Workflows: 7
   Estimated Speedup:  30-40% faster with optimization
   Recommendation:     Enable test result caching, run tests in parallel...

================================================================================
```

#### 4. Show Trends

```bash
python scripts/analyze_latency.py --trends --days 30
```

**Output:**
```
================================================================================
LATENCY TRENDS - Last 30 Days
================================================================================

Trend Direction:      INCREASING
Percentage Change:    +12.5%
Average Daily:        7.1m

Recent Daily Latencies:
Date          Avg Duration    Workflows
--------------------------------------------------------------------------------
2025-11-22         6.8m           5
2025-11-23         7.2m           6
2025-11-24         7.4m           4
...
================================================================================
```

#### 5. Show Recommendations

```bash
python scripts/analyze_latency.py --recommendations
```

**Output:**
```
================================================================================
OPTIMIZATION RECOMMENDATIONS - Last 30 Days
================================================================================

Found 2 optimization opportunity(ies):

1. Test Phase
   Current Latency:  2.6m
   Target Latency:   1.6m
   Improvement:      40% faster
   Actions:
   - Enable test result caching
   - Run test suites in parallel
   - Skip redundant tests for unchanged code

2. Build Phase
   Current Latency:  1.9m
   Target Latency:   1.1m
   Improvement:      40% faster
   Actions:
   - Enable dependency caching (pip, npm)
   - Use incremental builds where possible
   - Parallelize independent build steps

================================================================================
```

#### 6. Generate Comprehensive Report

```bash
python scripts/analyze_latency.py --report --output latency_report.md
```

Generates a detailed markdown report with all analyses combined, suitable for:
- Performance review meetings
- Tracking optimization progress over time
- Identifying trends and patterns
- Sharing with team members

## Optimization Strategies

### By Phase

#### Plan Phase (Target: <60s)
- **Enable prompt caching** for repeated planning patterns
- **Use structured inputs** to reduce LLM processing time
- **Implement plan templates** for common workflows

#### Validate Phase (Target: <30s)
- **Implement validation result caching**
- **Parallelize validation checks** where possible
- **Skip validations** for unchanged components

#### Build Phase (Target: <120s)
- **Enable dependency caching** (pip, npm, docker layers)
- **Use incremental builds** where supported
- **Parallelize independent build steps**

#### Lint Phase (Target: <20s)
- **Run linters in parallel**
- **Cache linting results** for unchanged files
- **Use incremental linting** where supported

#### Test Phase (Target: <180s)
- **Enable test result caching**
- **Run test suites in parallel** (pytest-xdist, jest --maxWorkers)
- **Skip redundant tests** for unchanged code
- **Use test sharding** for large test suites

#### Review Phase (Target: <60s)
- **Cache review results** for similar code patterns
- **Parallelize independent review checks**
- **Use automated review tools** where appropriate

#### Document Phase (Target: <30s)
- **Use template-based documentation generation**
- **Cache documentation** for unchanged code
- **Generate docs incrementally**

#### Ship Phase (Target: <20s)
- **Optimize git operations** (shallow clones, sparse checkouts)
- **Parallelize PR creation steps**
- **Use async webhooks** for notifications

#### Cleanup Phase (Target: <10s)
- **Defer non-critical cleanup**
- **Run cleanup asynchronously**
- **Batch cleanup operations**

## Performance Benchmarks

### Typical ADW Workflow Latencies

| Workflow Type | p50 | p95 | p99 | Notes |
|--------------|-----|-----|-----|-------|
| Small Feature | 5-7min | 8-10min | 12-15min | Simple changes, minimal tests |
| Medium Feature | 10-15min | 18-25min | 30-40min | Moderate complexity |
| Large Feature | 20-30min | 35-50min | 60-90min | Complex changes, full test suites |
| Bug Fix | 3-5min | 6-8min | 10-12min | Focused changes |

### Phase Distribution (Typical)

| Phase | % of Total Time | Optimization Potential |
|-------|----------------|----------------------|
| Test | 35-40% | High (caching, parallelization) |
| Build | 20-25% | High (caching, incremental builds) |
| Review | 12-15% | Medium (automated tools) |
| Plan | 10-12% | Medium (prompt caching) |
| Other | 13-18% | Low (mostly I/O bound) |

## Monitoring and Alerts

### Recommended Alerts

1. **p95 Latency Spike**
   - Trigger: p95 > 150% of 7-day average
   - Action: Check for infrastructure issues, recent changes

2. **Trend Degradation**
   - Trigger: Increasing trend with >20% change
   - Action: Review recent optimizations, identify regressions

3. **Bottleneck Detection**
   - Trigger: Any phase p95 > 600s (10min)
   - Action: Immediate investigation and optimization

4. **Phase-Specific Alerts**
   - Test phase > 300s: Check test parallelization
   - Build phase > 180s: Check dependency caching
   - Plan phase > 90s: Check prompt caching

## Integration with Monitoring Tools

### Prometheus Metrics

```python
from prometheus_client import Histogram, Gauge

# Workflow duration histogram
workflow_duration_seconds = Histogram(
    'adw_workflow_duration_seconds',
    'Workflow execution time',
    ['phase', 'workflow_type'],
    buckets=[30, 60, 120, 300, 600, 1200]
)

# Phase latency gauge
phase_latency_p95 = Gauge(
    'adw_phase_latency_p95_seconds',
    'Phase p95 latency',
    ['phase']
)
```

### Grafana Dashboard Queries

```promql
# p95 latency by phase
histogram_quantile(0.95,
  rate(adw_workflow_duration_seconds_bucket[5m])
)

# Trend over 7 days
avg_over_time(
  adw_workflow_duration_seconds_sum[7d]
) /
avg_over_time(
  adw_workflow_duration_seconds_count[7d]
)
```

## Best Practices

1. **Regular Analysis**
   - Run latency analysis weekly
   - Track trends after each optimization
   - Set baseline metrics for new workflows

2. **Set Realistic Thresholds**
   - Start with generous thresholds (e.g., 600s)
   - Gradually tighten as optimizations improve performance
   - Account for workflow complexity differences

3. **Focus on p95, Not Average**
   - Average can be skewed by outliers
   - p95 represents user experience for 95% of workflows
   - Use p99 to catch tail latency issues

4. **Prioritize High-Impact Phases**
   - Test and Build phases typically have highest impact
   - 40% improvement in Test phase = 14-16% overall improvement
   - Focus optimization efforts on phases >15% of total time

5. **Validate Optimizations**
   - Run before/after analysis
   - Use same time period for comparison
   - Monitor for regressions in subsequent weeks

## Troubleshooting

### Issue: High Latency, No Bottlenecks Detected

**Cause:** Threshold may be too high

**Solution:**
```bash
# Try lower threshold
python scripts/analyze_latency.py --bottlenecks --threshold 120
```

### Issue: Trend Shows "Stable" But Latency Increasing

**Cause:** Change may be <5% (threshold for "increasing")

**Solution:** Check raw percentage_change value in trends response

### Issue: Recommendations Not Generated

**Cause:** No phase exceeds 15% of total duration

**Solution:** All phases are well-balanced, focus on overall workflow optimization

### Issue: Missing Phase Data

**Cause:** `phase_durations` field not populated in workflow_history

**Solution:** Ensure ADW workflows are recording phase_durations JSON field

## Future Enhancements

- **Real-time latency tracking** during workflow execution
- **Automatic optimization application** (auto-enable caching)
- **Phase-to-phase dependency analysis** (critical path detection)
- **Anomaly detection** using machine learning
- **Cost-latency tradeoffs** (faster but more expensive options)
- **Historical comparison** (compare current vs. last month)

## References

- Cost Analytics: `docs/features/cost-analytics.md`
- Error Analytics: `docs/features/error-analytics.md`
- Workflow History Schema: `migration/postgres_schema.sql`
- Service Implementation: `app/server/services/latency_analytics_service.py`
