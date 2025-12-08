# Error Analytics System

## Overview

The Error Analytics System provides systematic error analysis and debugging recommendations for ADW workflows. It detects recurring error patterns, identifies failure-prone phases, tracks error trends over time, and generates actionable debugging recommendations to improve workflow reliability.

## Features

- **Error Summary Statistics** - Overall failure rates, top error patterns, and problematic phases
- **Phase Error Analysis** - Break down error rates by workflow phase (Plan, Build, Test, etc.)
- **Pattern Detection** - Automatically classify and group similar errors into patterns
- **Trend Analysis** - Track error rates over time to identify increasing/decreasing trends
- **Debugging Recommendations** - Generate prioritized, actionable debugging suggestions
- **CLI Reporting** - Generate detailed markdown reports for error analysis

## Architecture

### Components

1. **Error Analytics Service** (`services/error_analytics_service.py`)
   - Core business logic for error analysis
   - Pattern detection and classification
   - Trend analysis and forecasting
   - Recommendation generation

2. **API Routes** (`routes/error_analytics_routes.py`)
   - RESTful endpoints for error data access
   - 5 endpoints for different analysis types

3. **CLI Tool** (`scripts/analyze_errors.py`)
   - Interactive command-line interface
   - Markdown report generation
   - Batch analysis capabilities

4. **Data Models** (`core/models/workflow.py`)
   - Pydantic models for type safety
   - Response models for API consistency

## Error Classification Patterns

The system automatically classifies errors into the following categories:

| Pattern | Keywords | Category | Severity |
|---------|----------|----------|----------|
| **Import Error** | ModuleNotFoundError, ImportError, cannot import | Dependency Issue | High |
| **Connection Error** | ECONNREFUSED, Connection refused, Failed to connect | Network Issue | High |
| **Timeout Error** | timeout, timed out, TimeoutError, deadline exceeded | Performance Issue | Medium |
| **Syntax Error** | SyntaxError, invalid syntax, unexpected token | Code Quality | High |
| **Type Error** | TypeError, type object, is not callable | Type Issue | Medium |
| **File Not Found** | FileNotFoundError, ENOENT, no such file | File System Issue | Medium |
| **Permission Error** | PermissionError, EACCES, access denied | Permission Issue | Medium |
| **API Error** | API error, 404, 500, 503, status code | API Issue | High |
| **Database Error** | DatabaseError, SQL error, constraint violation | Database Issue | High |
| **Git Error** | git error, merge conflict, divergent branches | Git Issue | Medium |

## API Endpoints

### 1. Error Summary

**GET** `/api/error-analytics/summary`

Get overall error summary statistics.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_workflows": 150,
  "failed_workflows": 12,
  "failure_rate": 8.0,
  "top_errors": [
    ["import_error", 5],
    ["connection_error", 3],
    ["timeout_error", 2]
  ],
  "most_problematic_phase": "Test",
  "error_categories": {
    "Dependency Issue": 5,
    "Network Issue": 3,
    "Performance Issue": 2
  }
}
```

### 2. Phase Error Breakdown

**GET** `/api/error-analytics/by-phase`

Analyze error rates by workflow phase.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "phase_error_counts": {
    "Plan": 0,
    "Build": 5,
    "Test": 4,
    "Lint": 2,
    "Review": 1
  },
  "phase_failure_rates": {
    "Plan": 0.0,
    "Build": 10.5,
    "Test": 8.3,
    "Lint": 4.2,
    "Review": 2.1
  },
  "total_errors": 12,
  "most_error_prone_phase": "Build"
}
```

### 3. Error Patterns

**GET** `/api/error-analytics/patterns`

Detect and return recurring error patterns.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
[
  {
    "pattern_name": "Import Error",
    "pattern_category": "Dependency Issue",
    "occurrences": 5,
    "example_message": "ModuleNotFoundError: No module named 'requests'",
    "affected_workflows": ["adw-001", "adw-003", "adw-007"],
    "recommendation": "Add missing package to requirements.txt and ensure dependencies are installed",
    "severity": "high"
  },
  {
    "pattern_name": "Connection Error",
    "pattern_category": "Network Issue",
    "occurrences": 3,
    "example_message": "ECONNREFUSED localhost:9100",
    "affected_workflows": ["adw-002", "adw-005"],
    "recommendation": "Check service availability and port allocation. Verify backend/frontend are running",
    "severity": "high"
  }
]
```

### 4. Error Trends

**GET** `/api/error-analytics/trends`

Analyze error trends over time.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "daily_errors": [
    {
      "date": "2025-12-01",
      "error_count": 2,
      "failure_rate": 10.5,
      "workflow_count": 19
    },
    {
      "date": "2025-12-02",
      "error_count": 1,
      "failure_rate": 5.0,
      "workflow_count": 20
    }
  ],
  "trend_direction": "decreasing",
  "percentage_change": -45.2,
  "average_daily_failures": 1.5
}
```

### 5. Debugging Recommendations

**GET** `/api/error-analytics/recommendations`

Get prioritized debugging recommendations.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
[
  {
    "issue": "Import Error occurring 5 times",
    "severity": "high",
    "root_cause": "Dependency Issue",
    "solution": "Add missing package to requirements.txt and ensure dependencies are installed",
    "estimated_fix_time": "15-30 minutes (low priority)",
    "affected_count": 5
  },
  {
    "issue": "Connection Error occurring 3 times",
    "severity": "high",
    "root_cause": "Network Issue",
    "solution": "Check service availability and port allocation. Verify backend/frontend are running",
    "estimated_fix_time": "15-30 minutes (low priority)",
    "affected_count": 3
  }
]
```

## CLI Usage

### Installation

No installation required. The CLI tool is available at `scripts/analyze_errors.py`.

### Commands

#### Show Error Summary

```bash
python scripts/analyze_errors.py --summary --days 30
```

**Output:**
```
================================================================================
ERROR ANALYSIS SUMMARY - Last 30 Days
================================================================================

Total workflows:     150
Failed workflows:    12
Failure rate:        8.0%
Most problematic phase: Test

TOP ERROR PATTERNS:
--------------------------------------------------------------------------------
1. Import Error                     5 occurrences
2. Connection Error                 3 occurrences
3. Timeout Error                    2 occurrences
```

#### Show Phase Breakdown

```bash
python scripts/analyze_errors.py --phase --days 30
```

**Output:**
```
================================================================================
ERROR BREAKDOWN BY PHASE - Last 30 Days
================================================================================

Total errors: 12
Most error-prone phase: Build

PHASE ERROR RATES:
Phase                     Errors   Failure Rate
--------------------------------------------------------------------------------
Build                          5          10.5%  🟡 WARNING
Test                           4           8.3%  🟢 OK
Lint                           2           4.2%  🟢 OK
Review                         1           2.1%  🟢 OK
```

#### Show Error Patterns

```bash
python scripts/analyze_errors.py --patterns --days 30
```

**Output:**
```
================================================================================
ERROR PATTERNS - Last 30 Days
================================================================================

1. 🔴 Import Error (5 occurrences)
   Category: Dependency Issue
   Severity: HIGH
   Example: ModuleNotFoundError: No module named 'requests'...
   Recommendation: Add missing package to requirements.txt and ensure dependencies are installed
   Affected workflows: 5

2. 🔴 Connection Error (3 occurrences)
   Category: Network Issue
   Severity: HIGH
   Example: ECONNREFUSED localhost:9100...
   Recommendation: Check service availability and port allocation. Verify backend/frontend are running
   Affected workflows: 3
```

#### Show Error Trends

```bash
python scripts/analyze_errors.py --trends --days 30
```

**Output:**
```
================================================================================
ERROR TRENDS - Last 30 Days
================================================================================

Trend direction: DECREASING
Percentage change: -45.2%
Average daily failures: 1.5

DAILY ERROR TRENDS:
Date         Errors  Failure Rate    Total
--------------------------------------------------------------------------------
2025-12-01        2          10.5%      19  ██
2025-12-02        1           5.0%      20  █
2025-12-03        0           0.0%      22
```

#### Show Debugging Recommendations

```bash
python scripts/analyze_errors.py --recommendations --days 30
```

**Output:**
```
================================================================================
DEBUGGING RECOMMENDATIONS - Last 30 Days
================================================================================

1. [🔴 HIGH] Import Error occurring 5 times
   Root Cause: Dependency Issue
   Solution: Add missing package to requirements.txt and ensure dependencies are installed
   Estimated Fix Time: 15-30 minutes (low priority)
   Affected Workflows: 5

2. [🔴 HIGH] Connection Error occurring 3 times
   Root Cause: Network Issue
   Solution: Check service availability and port allocation. Verify backend/frontend are running
   Estimated Fix Time: 15-30 minutes (low priority)
   Affected Workflows: 3
```

#### Generate Full Report

```bash
python scripts/analyze_errors.py --report --output error_report.md --days 30
```

Generates a comprehensive markdown report with all analysis sections.

## Debugging Workflow

### 1. Identify Error Patterns

Start by running the summary to get a high-level overview:

```bash
python scripts/analyze_errors.py --summary --days 30
```

### 2. Analyze Problematic Phases

If a specific phase is problematic, analyze phase-specific errors:

```bash
python scripts/analyze_errors.py --phase --days 30
```

### 3. Review Error Patterns

Get detailed information about recurring error patterns:

```bash
python scripts/analyze_errors.py --patterns --days 30
```

### 4. Check Trends

Determine if errors are increasing or decreasing:

```bash
python scripts/analyze_errors.py --trends --days 30
```

### 5. Apply Recommendations

Get prioritized debugging recommendations:

```bash
python scripts/analyze_errors.py --recommendations --days 30
```

### 6. Fix and Verify

After applying fixes:

1. Re-run the analysis to verify error rates have decreased
2. Monitor trends to ensure errors don't recur
3. Update documentation with lessons learned

## Prevention Strategies

### Import Errors

**Prevention:**
- Keep `requirements.txt` and `package.json` up to date
- Use virtual environments consistently
- Run `pip install -r requirements.txt` before workflows
- Add dependency checks in pre-flight validation

### Connection Errors

**Prevention:**
- Verify port availability before starting services
- Add health checks for backend/frontend services
- Implement retry logic with exponential backoff
- Use connection pooling for better reliability

### Timeout Errors

**Prevention:**
- Set appropriate timeout thresholds
- Optimize long-running operations
- Add progress indicators for lengthy tasks
- Consider async processing for heavy workloads

### Syntax/Type Errors

**Prevention:**
- Run linters (pylint, eslint) before commits
- Use type checkers (mypy, TypeScript)
- Enable pre-commit hooks for automatic checking
- Enforce code review before merging

## Integration

### With Panel 8 (Error Review)

The Error Analytics System can be integrated with Panel 8 to provide:
- Real-time error monitoring
- Visual error trend charts
- One-click debugging recommendations
- Historical error comparison

### With Observability System

Error analytics integrates with the observability system by:
- Reading from `workflow_history.error_message`
- Analyzing `hook_events` for error events
- Tracking `tool_calls.error_message` for tool-specific errors
- Correlating errors with workflow phases

## Performance

- **Query Performance:** Sub-second response times for 30-day analysis
- **Pattern Detection:** O(n) complexity for error classification
- **Scalability:** Handles 1000+ workflows efficiently
- **Caching:** Results can be cached for frequently accessed periods

## Future Enhancements

1. **Machine Learning Classification** - Use ML to improve error pattern detection
2. **Automated Fix Suggestions** - Generate code fixes for common errors
3. **Root Cause Analysis** - Deep dive into error causes using stack traces
4. **Predictive Analytics** - Forecast future error rates based on trends
5. **Integration Tests** - Automated integration with CI/CD pipelines
6. **Alert System** - Send notifications when error rates spike

## Troubleshooting

### No Error Data

**Issue:** All analytics show zero errors.

**Solution:**
- Verify workflows are being recorded in `workflow_history`
- Check that failed workflows have `status = 'failed'`
- Ensure `error_message` field is populated

### Incorrect Pattern Classification

**Issue:** Errors are classified as "Unknown" when they should match a pattern.

**Solution:**
- Review error message format
- Add new keywords to `ERROR_PATTERNS` dictionary
- Check for typos or case sensitivity issues

### Slow Query Performance

**Issue:** API endpoints or CLI commands are slow.

**Solution:**
- Reduce the `days` parameter
- Add database indexes on `started_at` and `status` columns
- Consider caching results for common queries

## Related Documentation

- [Cost Analytics](./cost-analytics.md) - Analyze workflow costs
- [Observability and Logging](./observability-and-logging.md) - Hook events and logging
- [Pattern Review System](./pattern-review.md) - Automated pattern detection
