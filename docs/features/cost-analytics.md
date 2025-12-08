# Cost Attribution Analytics System

## Overview

The Cost Attribution Analytics System provides detailed cost analysis and optimization recommendations for ADW workflows. It breaks down costs by phase, workflow type, and time period, identifies trends, and generates actionable insights to reduce expenses.

## Features

- **Phase Cost Analysis** - Aggregate costs by workflow phase (Plan, Build, Test, etc.)
- **Workflow Type Analysis** - Compare costs across different workflow types/templates
- **Time Series Analysis** - Track cost trends over time with moving averages
- **Optimization Detection** - Automatically identify high-cost areas and recommend improvements
- **CLI Reporting** - Generate detailed markdown reports for budget tracking

## Architecture

### Components

1. **Cost Analytics Service** (`services/cost_analytics_service.py`)
   - Core business logic for cost analysis
   - Aggregation and statistical calculations
   - Optimization opportunity detection

2. **API Routes** (`routes/cost_analytics_routes.py`)
   - RESTful endpoints for cost data access
   - 4 endpoints for different analysis types

3. **CLI Tool** (`scripts/analyze_costs.py`)
   - Interactive command-line interface
   - Markdown report generation
   - Batch analysis capabilities

4. **Data Models** (`core/models/workflow.py`)
   - Pydantic models for type safety
   - Response models for API consistency

## API Endpoints

### 1. Phase Breakdown

**GET** `/api/cost-analytics/by-phase`

Analyzes costs aggregated by workflow phase.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "phase_costs": {
    "Plan": 145.23,
    "Validate": 89.45,
    "Build": 312.67,
    "Lint": 45.12,
    "Test": 198.34,
    "Review": 78.23,
    "Document": 43.56,
    "Ship": 38.90,
    "Cleanup": 2.50
  },
  "phase_percentages": {
    "Plan": 15.2,
    "Validate": 9.4,
    "Build": 32.8,
    "Lint": 4.7,
    "Test": 20.8,
    "Review": 8.2,
    "Document": 4.6,
    "Ship": 4.1,
    "Cleanup": 0.3
  },
  "phase_counts": {
    "Plan": 50,
    "Build": 50,
    "Test": 50,
    ...
  },
  "total": 954.00,
  "average_per_workflow": 19.08,
  "workflow_count": 50
}
```

**Example:**
```bash
curl "http://localhost:8000/api/cost-analytics/by-phase?days=30"
```

### 2. Workflow Type Breakdown

**GET** `/api/cost-analytics/by-workflow-type`

Analyzes costs aggregated by workflow type/template.

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "by_type": {
    "adw_sdlc_complete_iso": 450.00,
    "adw_sdlc_complete_zte": 350.00,
    "adw_review_iso": 154.00
  },
  "count_by_type": {
    "adw_sdlc_complete_iso": 25,
    "adw_sdlc_complete_zte": 18,
    "adw_review_iso": 7
  },
  "average_by_type": {
    "adw_sdlc_complete_iso": 18.00,
    "adw_sdlc_complete_zte": 19.44,
    "adw_review_iso": 22.00
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/cost-analytics/by-workflow-type?days=30"
```

### 3. Cost Trends

**GET** `/api/cost-analytics/trends`

Analyzes cost trends over time with moving averages.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "daily_costs": [
    {
      "date": "2025-12-01",
      "cost": 32.50,
      "workflow_count": 3
    },
    ...
  ],
  "moving_average": [30.5, 31.2, 32.0, ...],
  "trend_direction": "increasing",
  "percentage_change": 12.5,
  "total_cost": 954.00,
  "average_daily_cost": 31.80
}
```

**Example:**
```bash
curl "http://localhost:8000/api/cost-analytics/trends?days=30"
```

### 4. Optimization Opportunities

**GET** `/api/cost-analytics/optimizations`

Identifies cost optimization opportunities.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
[
  {
    "category": "phase",
    "description": "Build phase: 32.8% of costs (expected: 25.0%)",
    "current_cost": 312.67,
    "target_cost": 238.50,
    "estimated_savings": 296.68,
    "recommendation": "Enable external tool usage (ruff, mypy) to reduce LLM costs in build phase",
    "priority": "high"
  },
  {
    "category": "workflow_type",
    "description": "adw_review_iso: $22.00/workflow (avg: $18.50)",
    "current_cost": 154.00,
    "target_cost": 129.50,
    "estimated_savings": 98.00,
    "recommendation": "Review adw_review_iso workflow configuration for optimization opportunities",
    "priority": "medium"
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/cost-analytics/optimizations?days=30"
```

## CLI Usage

### Basic Commands

**Show phase breakdown:**
```bash
python scripts/analyze_costs.py --phase --days 30
```

Output:
```
================================================================================
COST BREAKDOWN BY PHASE - Last 30 Days
================================================================================

Phase           Cost    Percentage    Count
--------------------------------------------------------------------------------
Build          $312.67       32.8%       50
Test           $198.34       20.8%       50
Plan           $145.23       15.2%       50
Validate        $89.45        9.4%       50
Review          $78.23        8.2%       50
Lint            $45.12        4.7%       50
Document        $43.56        4.6%       50
Ship            $38.90        4.1%       50
Cleanup          $2.50        0.3%       50
--------------------------------------------------------------------------------
TOTAL          $954.00      100.0%       50

Average cost per workflow: $19.08
================================================================================
```

**Show workflow type breakdown:**
```bash
python scripts/analyze_costs.py --workflow --days 30
```

**Show cost trends:**
```bash
python scripts/analyze_costs.py --trends --days 30
```

**Show optimization opportunities:**
```bash
python scripts/analyze_costs.py --optimize
```

Output:
```
================================================================================
OPTIMIZATION OPPORTUNITIES - Last 30 Days
================================================================================

Found 2 optimization opportunities
Total potential monthly savings: $394.68

1. [HIGH] PHASE
   Build phase: 32.8% of costs (expected: 25.0%)
   Current: $312.67 → Target: $238.50
   Estimated monthly savings: $296.68
   Recommendation: Enable external tool usage (ruff, mypy) to reduce LLM costs in build phase

2. [MEDIUM] WORKFLOW_TYPE
   adw_review_iso: $22.00/workflow (avg: $18.50)
   Current: $154.00 → Target: $129.50
   Estimated monthly savings: $98.00
   Recommendation: Review adw_review_iso workflow configuration for optimization opportunities

================================================================================
```

**Generate comprehensive report:**
```bash
python scripts/analyze_costs.py --report --output cost_report.md
```

Creates a markdown file with:
- Executive summary
- Phase breakdown table
- Workflow type breakdown table
- Cost trends analysis
- Recent daily costs
- Optimization opportunities with recommendations

**Show all analyses:**
```bash
python scripts/analyze_costs.py --all --days 30
```

### Advanced Usage

**Custom date range:**
```bash
python scripts/analyze_costs.py --phase --start-date 2025-12-01 --end-date 2025-12-07
```

**Verbose output for debugging:**
```bash
python scripts/analyze_costs.py --all --days 30 --verbose
```

## Cost Attribution Methodology

### Phase Cost Extraction

Phase costs are extracted from the `cost_breakdown` JSON field in `workflow_history`:

```sql
SELECT cost_breakdown, actual_cost_total
FROM workflow_history
WHERE created_at >= ? AND created_at <= ?
  AND actual_cost_total > 0
  AND cost_breakdown IS NOT NULL
```

The `cost_breakdown` structure:
```json
{
  "by_phase": {
    "Plan": 2.0,
    "Build": 8.0,
    "Test": 5.5,
    ...
  }
}
```

### Optimization Detection

#### 1. Phase Anomaly Detection

Compares actual phase percentages against expected baseline:

| Phase | Expected % | Threshold |
|-------|-----------|-----------|
| Plan | 15% | >20% triggers alert |
| Validate | 10% | >20% triggers alert |
| Build | 25% | >20% triggers alert |
| Lint | 5% | >20% triggers alert |
| Test | 20% | >20% triggers alert |
| Review | 10% | >20% triggers alert |
| Document | 8% | >20% triggers alert |
| Ship | 5% | >20% triggers alert |
| Cleanup | 2% | >20% triggers alert |

**Priority:**
- **High**: Actual > 50% above expected
- **Medium**: Actual > 20% above expected

#### 2. Workflow Inefficiency Detection

Flags workflow types where average cost is >50% above overall average:

```python
if avg_cost > overall_average * 1.5:
    # Flag as optimization opportunity
```

#### 3. Outlier Detection

Uses statistical analysis to find high-cost outliers:

```python
threshold = avg_cost + (2 * stddev_cost)
# Workflows above threshold are flagged
```

### Savings Calculation

Monthly savings are estimated using weekly analysis multiplied by 4:

```python
estimated_monthly_savings = (current_cost - target_cost) * 4
```

## Optimization Recommendations

### By Phase

| Phase | Recommendation |
|-------|---------------|
| Plan | Enable prompt caching, use structured inputs |
| Validate | Implement validation result caching |
| Build | Use external tools (ruff, mypy) to reduce LLM costs |
| Lint | Use external linting tools (ruff) instead of LLM |
| Test | Implement test result caching, use pytest directly |
| Review | Cache code review results for similar changes |
| Document | Use template-based documentation generation |
| Ship | Optimize git operations and PR creation |
| Cleanup | Review cleanup process for unnecessary operations |

### Implementation Guide

1. **Enable External Tool Usage**
   - Configure ADW workflows to use external tools (ruff, mypy, pytest)
   - Reduces LLM token usage by 60-80% for lint/test phases

2. **Implement Result Caching**
   - Cache validation, test, and review results
   - Skip redundant operations on similar code

3. **Optimize Prompt Engineering**
   - Use structured inputs over natural language
   - Enable prompt caching for repeated contexts

4. **Review Workflow Configuration**
   - Analyze high-cost workflow types
   - Identify unnecessary steps or redundant operations

## Integration with ADW Workflows

Cost analytics integrates with the ADW workflow system through:

1. **Cost Tracking** - Workflow history captures phase-level costs
2. **Automatic Analysis** - Background workers sync and analyze costs
3. **Real-time Insights** - Dashboard integration (future)

### Workflow Cost Flow

```
ADW Workflow Execution
  ↓
Cost Tracking per Phase
  ↓
workflow_history.cost_breakdown (JSON)
  ↓
Cost Analytics Service
  ↓
Analysis & Recommendations
  ↓
API/CLI Output
```

## Testing

### Run Tests

```bash
cd app/server
pytest tests/services/test_cost_analytics_service.py -v
```

### Test Coverage

The test suite includes:
- Phase cost aggregation (3 tests)
- Workflow type analysis (2 tests)
- Time series analysis (2 tests)
- Optimization detection (3 tests)
- Helper method validation (6 tests)

**Total: 16 test cases**

## Performance Considerations

### Query Optimization

1. **Date Range Filtering** - Limits data scanned
2. **Indexed Queries** - Uses `created_at` index
3. **Aggregation at DB Level** - Reduces data transfer

### Caching Strategy

Cost analytics queries are relatively expensive. Recommended caching:

- **Phase breakdown**: Cache for 1 hour
- **Workflow type breakdown**: Cache for 1 hour
- **Trends**: Cache for 15 minutes (more dynamic)
- **Optimizations**: Cache for 1 hour

## Future Enhancements

1. **Real-time Cost Tracking** - WebSocket updates during workflow execution
2. **Budget Alerts** - Notifications when costs exceed thresholds
3. **Cost Predictions** - ML-based cost forecasting
4. **Dashboard Integration** - Visual cost analytics in Panel 11
5. **Export Formats** - CSV, Excel exports for external analysis
6. **Historical Comparisons** - Month-over-month, quarter-over-quarter analysis
7. **Team/Project Attribution** - Cost breakdown by team or project

## Troubleshooting

### No Data Returned

**Symptom:** Empty results from analytics queries

**Solutions:**
1. Check date range - ensure workflows exist in period
2. Verify `cost_breakdown` field is populated
3. Check `actual_cost_total > 0` in workflows
4. Review database connectivity

### Incorrect Phase Costs

**Symptom:** Phase costs don't match expectations

**Solutions:**
1. Verify `cost_breakdown` JSON structure
2. Check for JSON parsing errors in logs
3. Ensure phase names match expected format
4. Review workflow execution logs for cost tracking

### Missing Optimizations

**Symptom:** No optimization opportunities detected

**Solutions:**
1. Ensure sufficient data (at least 5-10 workflows)
2. Check if costs are actually within normal ranges
3. Review thresholds in optimization detection logic
4. Increase analysis period (try 60-90 days)

## References

- **Service Implementation**: `app/server/services/cost_analytics_service.py`
- **API Routes**: `app/server/routes/cost_analytics_routes.py`
- **CLI Tool**: `scripts/analyze_costs.py`
- **Data Models**: `app/server/core/models/workflow.py`
- **Tests**: `app/server/tests/services/test_cost_analytics_service.py`
- **Workflow History**: `docs/features/observability-and-logging.md`
