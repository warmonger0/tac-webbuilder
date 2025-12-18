# ADW Workflow Tracking & Observability Architecture

**Last Updated:** 2025-12-18
**Version:** 1.0
**Status:** Production

---

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Services & Components](#services--components)
5. [Tracking Coverage](#tracking-coverage)
6. [Integration Points](#integration-points)
7. [Analytics Capabilities](#analytics-capabilities)
8. [Gaps & Future Enhancements](#gaps--future-enhancements)

---

## Overview

The ADW (Autonomous Development Workflow) tracking system provides comprehensive observability into workflow execution, costs, performance, and outcomes. It combines database persistence, structured logging, real-time monitoring, and analytics to enable pattern learning and continuous optimization.

### Key Capabilities

- **Real-time Monitoring**: WebSocket updates for workflow status and progress
- **Cost Tracking**: Per-phase and total cost with token breakdown
- **Performance Analysis**: Latency metrics, bottleneck detection, trend analysis
- **Error Analytics**: Error categorization, retry tracking, recovery time
- **Pattern Learning**: Automatic pattern detection and ROI calculation
- **Quality Scoring**: Cost efficiency, performance, and quality metrics
- **Structured Logging**: JSONL files for post-mortem analysis

### Architecture Principles

1. **Zero-Overhead Design**: Logging failures never block workflow execution
2. **Dual Persistence**: Database (queryable) + JSONL (detailed logs)
3. **Enrichment Pipeline**: Separates data capture from analysis
4. **Background Sync**: Non-blocking updates with 10-second cache
5. **Multi-Layer Tracking**: Workflow → Phase → Step granularity

---

## Database Schema

### Primary Tables

#### 1. `workflow_history` - Central Workflow Tracking

**Location:** `app/server/core/workflow_history_utils/database/schema.py`

**Purpose:** Complete record of all ADW workflow executions

**Key Field Groups:**

```sql
CREATE TABLE workflow_history (
    -- Identity
    id SERIAL PRIMARY KEY,
    adw_id TEXT UNIQUE NOT NULL,
    issue_number INTEGER,
    github_url TEXT,
    workflow_template TEXT,
    model_used TEXT,

    -- Status & Timing
    status TEXT NOT NULL,  -- pending, running, completed, failed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL,
    current_phase TEXT,
    phase_count INTEGER,

    -- Cost Tracking
    estimated_cost_total REAL,
    actual_cost_total REAL,
    cost_per_token REAL,
    cost_breakdown JSONB,  -- Per-phase breakdown
    estimated_cost_per_step REAL,
    actual_cost_per_step REAL,

    -- Token Metrics
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_tokens INTEGER,
    cache_hit_tokens INTEGER,
    cache_miss_tokens INTEGER,
    total_tokens INTEGER,
    cache_efficiency_percent REAL,
    token_breakdown JSONB,

    -- Performance Metrics
    phase_durations JSONB,  -- Duration per phase
    idle_time_seconds REAL,
    bottleneck_phase TEXT,

    -- Error Analytics
    error_message TEXT,
    error_category TEXT,
    retry_count INTEGER DEFAULT 0,
    retry_reasons JSONB,  -- Array of retry triggers
    error_phase_distribution JSONB,
    recovery_time_seconds REAL,

    -- Quality Scoring
    complexity_estimated TEXT,  -- low, medium, high
    complexity_actual TEXT,
    nl_input_clarity_score INTEGER,  -- 0-100
    cost_efficiency_score INTEGER,
    performance_score INTEGER,
    quality_score INTEGER,
    scoring_version TEXT,

    -- Insights & Recommendations
    anomaly_flags JSONB,  -- Array of anomaly messages
    optimization_recommendations JSONB,

    -- Temporal Analysis
    hour_of_day INTEGER,  -- 0-23
    day_of_week INTEGER,  -- 0-6 (Monday = 0)

    -- Outcome Tracking
    pr_merged BOOLEAN,
    time_to_merge_hours REAL,
    review_cycles INTEGER,
    ci_test_pass_rate REAL,

    -- Pattern Learning
    similar_workflow_ids JSONB,

    -- Resource Utilization
    worktree_path TEXT,
    backend_port INTEGER,
    frontend_port INTEGER,
    concurrent_workflows INTEGER,
    worktree_reused BOOLEAN,
    steps_completed INTEGER,
    steps_total INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_adw_id` - Fast workflow lookup
- `idx_status` - Filter by execution status
- `idx_created_at DESC` - Time-ordered queries
- `idx_issue_number` - Link to GitHub issues
- `idx_model_used` - Group by model
- `idx_workflow_template` - Group by template type

#### 2. `task_logs` - Phase Execution Tracking

**Location:** Migration `015_add_task_logs_and_user_prompts.sql`

**Purpose:** Granular phase-level execution logs

```sql
CREATE TABLE task_logs (
    id SERIAL PRIMARY KEY,
    adw_id TEXT NOT NULL,
    issue_number INTEGER,
    workflow_template TEXT,

    -- Phase Details
    phase_name TEXT NOT NULL,
    phase_number INTEGER,
    phase_status TEXT NOT NULL,  -- started, completed, failed, skipped

    -- Logging
    log_message TEXT,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,

    -- Cost
    tokens_used INTEGER,
    cost_usd REAL,

    -- Metadata
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_task_logs_adw_id` - Group logs by workflow
- `idx_task_logs_issue_number` - Link to GitHub issues
- `idx_task_logs_phase_status` - Filter by status

#### 3. `user_prompts` - User Input Capture

**Location:** Migration `015_add_task_logs_and_user_prompts.sql`

**Purpose:** Track initial user requests and estimates

```sql
CREATE TABLE user_prompts (
    id SERIAL PRIMARY KEY,
    request_id TEXT UNIQUE NOT NULL,
    session_id TEXT,

    -- User Input
    nl_input TEXT NOT NULL,
    issue_title TEXT,
    issue_body TEXT,
    issue_type TEXT,  -- bug, feature, refactor, docs, test
    complexity TEXT,  -- low, medium, high

    -- Multi-Phase Support
    is_multi_phase BOOLEAN DEFAULT FALSE,
    phase_count INTEGER,
    parent_issue_number INTEGER,

    -- Estimates
    estimated_cost_usd REAL,
    estimated_tokens INTEGER,
    model_name TEXT,

    -- GitHub Integration
    github_issue_number INTEGER,
    github_issue_url TEXT,
    posted_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. `tool_calls` - Tool Invocation Tracking

**Location:** Migration `004_add_observability_and_pattern_learning.sql`

**Purpose:** Track ADW-to-ADW tool calls (specialized workflows)

**Status:** ⚠️ Schema exists, but NOT used for individual Claude Code tool calls (Bash, Read, Write, etc.)

```sql
CREATE TABLE tool_calls (
    id BIGSERIAL PRIMARY KEY,
    tool_call_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,

    -- Tool Details
    tool_name VARCHAR(255) NOT NULL,
    tool_params JSONB,

    -- Timing
    called_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds DOUBLE PRECISION,

    -- Results
    success BOOLEAN DEFAULT FALSE,
    result_data JSONB,
    error_message TEXT,

    -- Cost Impact
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd NUMERIC(10, 4) DEFAULT 0.0,

    -- Captured via hooks
    pre_tool_snapshot JSONB,
    post_tool_snapshot JSONB
);
```

**Note:** This table is designed for ADW tool registry calls, NOT individual Claude Code operations. See [Gaps](#gaps--future-enhancements) for planned enhancement.

#### 5. `hook_events` - Event Capture

**Location:** Migration `004_add_observability_and_pattern_learning.sql`

**Purpose:** Capture PreToolUse/PostToolUse events from Claude Code

**Status:** ❓ Schema exists, integration status unclear

```sql
CREATE TABLE hook_events (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- PreToolUse, PostToolUse, etc.
    source_app VARCHAR(100),
    session_id VARCHAR(255),
    workflow_id VARCHAR(255),
    timestamp TIMESTAMP,
    payload JSONB,
    tool_name VARCHAR(255),
    chat_history JSONB,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);
```

#### 6. `operation_patterns` - Pattern Learning

**Location:** Migration `004_add_observability_and_pattern_learning.sql`

**Purpose:** Detect and track repeating operational patterns

```sql
CREATE TABLE operation_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_signature VARCHAR(512) UNIQUE NOT NULL,
    pattern_type VARCHAR(100),  -- file_operation, test_cycle, build_sequence

    -- Detection
    first_detected TIMESTAMP,
    last_seen TIMESTAMP,
    occurrence_count INTEGER DEFAULT 0,

    -- Pattern Details
    typical_input_pattern JSONB,
    typical_operations JSONB,
    typical_files_accessed TEXT[],

    -- ROI Analysis
    avg_tokens_with_llm INTEGER,
    avg_cost_with_llm NUMERIC(10, 4),
    avg_tokens_with_tool INTEGER,
    avg_cost_with_tool NUMERIC(10, 4),
    potential_monthly_savings NUMERIC(10, 2),

    -- Automation Status
    automation_status VARCHAR(50),  -- candidate, approved, implemented, rejected
    confidence_score DOUBLE PRECISION,

    -- Tool Mapping
    tool_name VARCHAR(255),
    tool_script_path TEXT,

    -- Review
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_notes TEXT
);
```

#### 7. Supporting Tables

**Other tracking tables:**
- `work_log` - Session-level work tracking
- `webhook_events` - GitHub webhook processing
- `adw_locks` - Workflow locking mechanism
- `phase_queue` - Multi-phase workflow coordination
- `adw_tools` - Tool registry for ADW-to-ADW calls
- `cost_savings_log` - Cost optimization tracking
- `pattern_occurrences` - Pattern instance tracking

---

## Data Flow Architecture

### Execution → Database Flow

```
┌─────────────────────────────────────┐
│   ADW Workflow Execution            │
│   (agents/{adw_id}/)                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 1. Observability Module             │
│    adws/adw_modules/observability.py│
│                                      │
│    - log_phase_start()              │
│    - log_phase_completion()         │
│    - log_task_completion()          │
└────────┬───────────────┬────────────┘
         │               │
         │               └──────────────────┐
         │                                  │
         ▼                                  ▼
┌────────────────────────┐    ┌────────────────────────┐
│ 2a. Structured Logger  │    │ 2b. API POST Request   │
│     JSONL Files        │    │     /api/v1/           │
│                        │    │     observability/     │
│ logs/structured/       │    │     task-logs          │
│   workflow_{adw_id}    │    └───────────┬────────────┘
│   .jsonl               │                │
└────────────────────────┘                ▼
                              ┌────────────────────────┐
                              │ 3. Backend API Route   │
                              │    observability_      │
                              │    routes.py           │
                              │                        │
                              │    - Validates input   │
                              │    - Calls repository  │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ 4. TaskLogRepository   │
                              │    .create()           │
                              │                        │
                              │    INSERT INTO         │
                              │    task_logs           │
                              └────────────────────────┘

┌─────────────────────────────────────┐
│ 5. Background Sync Worker           │
│    (Every 10 seconds)                │
│                                      │
│    workflow_service.py               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 6. Sync Manager                     │
│    sync_manager.py                  │
│                                      │
│    - Scans agents/ directory        │
│    - Reads adw_state.json files     │
│    - Detects status changes         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 7. Enrichment Pipeline              │
│    enrichment.py                    │
│                                      │
│    - enrich_cost_data()             │
│    - enrich_github_state()          │
│    - enrich_error_category()        │
│    - enrich_temporal_fields()       │
│    - enrich_scores()                │
│    - enrich_insights()              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 8. Database Mutations               │
│    mutations.py                     │
│                                      │
│    - insert_workflow_history()      │
│    - update_workflow_history()      │
│                                      │
│    INSERT/UPDATE workflow_history   │
└─────────────────────────────────────┘
```

### Query & Analytics Flow

```
┌─────────────────────────────────────┐
│   Frontend Dashboard / API Client   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Backend API Routes                │
│                                      │
│   - /api/v1/workflows               │
│   - /api/v1/workflows/history       │
│   - /api/v1/cost-analytics/*        │
│   - /api/v1/latency-analytics/*     │
│   - /api/v1/error-analytics/*       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Analytics Services                │
│                                      │
│   - CostAnalyticsService            │
│   - LatencyAnalyticsService         │
│   - ErrorAnalyticsService           │
│   - WorkflowService                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Database Query Layer              │
│   (queries.py, analytics.py)        │
│                                      │
│   SELECT FROM workflow_history      │
│   JOIN task_logs                    │
│   GROUP BY, ORDER BY, AGGREGATE     │
└─────────────────────────────────────┘
```

---

## Services & Components

### Core Services

#### 1. WorkflowService
**Location:** `app/server/services/workflow_service.py`

**Responsibilities:**
- Scan agents directory for active workflows
- Provide workflow history with 10-second cache
- Background sync worker (updates every 10s)
- Cost prediction based on historical patterns
- Trend analysis (cost, duration, success rate, cache efficiency)

**Key Methods:**
- `get_workflows()` - List active workflows from filesystem
- `get_workflow_history_with_cache()` - Cached history queries
- `predict_workflow_cost(workflow_type, model, complexity)` - Cost estimation
- `get_workflow_trends(days=30)` - Historical trends

#### 2. Sync Manager
**Location:** `app/server/core/workflow_history_utils/sync_manager.py`

**Responsibilities:**
- Orchestrate workflow state synchronization
- Scan agent directories for state changes
- Trigger enrichment pipeline
- Update database with minimal overhead

**Key Functions:**
- `sync_workflow_history()` - Full sync from agents → database
- `resync_workflow_cost(adw_id)` - Recalculate cost data
- `resync_all_completed_workflows()` - Bulk resync

**Sync Logic:**
```python
# Only sync if:
1. New workflow detected (INSERT)
2. Status changed (UPDATE)
3. Status = completed/failed (UPDATE cost)
4. Cost increased for running workflow (UPDATE cost)
```

#### 3. Enrichment Pipeline
**Location:** `app/server/core/workflow_history_utils/enrichment.py`

**Purpose:** Transform raw workflow data into analytics-ready records

**Enrichment Functions:**

| Function | Purpose | Output |
|----------|---------|--------|
| `enrich_cost_data()` | Parse and structure cost information | cost_breakdown JSON |
| `enrich_cost_estimate()` | Estimate costs from historical data | estimated_cost_total |
| `enrich_github_state()` | Fetch GitHub issue state | github_url, pr_merged |
| `enrich_workflow_template()` | Identify workflow template used | workflow_template |
| `enrich_error_category()` | Categorize errors | error_category |
| `enrich_duration()` | Calculate execution duration | duration_seconds |
| `enrich_complexity()` | Assess workflow complexity | complexity_actual |
| `enrich_temporal_fields()` | Extract time patterns | hour_of_day, day_of_week |
| `enrich_scores()` | Calculate quality metrics | cost_efficiency_score, performance_score |
| `enrich_insights()` | Generate recommendations | anomaly_flags, optimization_recommendations |

#### 4. Analytics Services

**CostAnalyticsService** (`app/server/services/cost_analytics_service.py`)
- Breakdown by phase (Plan, Build, Test, Review, Document, Ship)
- Breakdown by workflow type/template
- 7-day moving average trends
- Optimization opportunity identification

**LatencyAnalyticsService** (`app/server/services/latency_analytics_service.py`)
- Latency summary (p50, p95, p99 percentiles)
- Phase latency breakdown
- Bottleneck detection
- Trend analysis with recommendations

**ErrorAnalyticsService** (`app/server/services/error_analytics_service.py`)
- Error pattern classification (Import, Connection, Timeout, Syntax, Type, etc.)
- Failure rate by phase
- Error trend analysis
- Debug recommendations with severity levels

#### 5. Observability Module
**Location:** `adws/adw_modules/observability.py`

**Purpose:** Capture workflow execution events from ADW agents

**Key Functions:**
```python
def log_phase_start(adw_id, issue_number, phase_name, phase_number, workflow_template):
    """Log phase start to backend API and JSONL"""

def log_phase_completion(adw_id, issue_number, phase_name, phase_number, success, started_at):
    """Log phase completion with duration and status"""

def log_task_completion(adw_id, issue_number, phase_name, phase_number, success, log_message, error_message=None):
    """Log task completion with detailed message"""

def track_pattern_execution(pattern_name, workflow_id, tokens_used, cost_usd, success):
    """Track pattern execution for ROI analysis"""
```

**Design Principles:**
- Zero overhead: Failures never block workflow execution
- Non-blocking API calls with timeout
- Fallback to local JSONL if API unavailable
- Thread-safe logging

#### 6. Structured Logger
**Location:** `adws/adw_modules/structured_logger.py`

**Purpose:** Write detailed execution logs in JSONL format

**Features:**
- Per-workflow isolation: `logs/structured/workflow_{adw_id}.jsonl`
- Thread-safe file writes
- Pydantic-based serialization
- Supports phase and workflow-level events

**Usage:**
```python
logger = ADWStructuredLogger(adw_id="abc123")
logger.log_phase("Build", "started", {"phase_number": 3})
logger.log_workflow("workflow_completed", {"duration_seconds": 450})
```

---

## Tracking Coverage

### ✅ What IS Being Tracked

#### Workflow-Level Metrics
- **Execution Status**: pending, running, completed, failed
- **Timing**: start_time, end_time, duration_seconds
- **Phase Progression**: current_phase, phase_count, phase_durations
- **Success Metrics**: success_rate, retry_count, steps_completed/total

#### Cost & Token Metrics
- **Token Usage**: input_tokens, output_tokens, cached_tokens
- **Cache Metrics**: cache_hit_tokens, cache_miss_tokens, cache_efficiency_percent
- **Cost Breakdown**: estimated vs actual, per-phase, per-step
- **Token Breakdown**: Detailed JSON with cache analysis

#### Performance Metrics
- **Duration Tracking**: Overall and per-phase
- **Bottleneck Detection**: Slowest phase identification
- **Idle Time**: Time between phases
- **Latency Percentiles**: p50, p95, p99 across workflows

#### Error Analytics
- **Error Categorization**: Import, Connection, Timeout, Syntax, Type, File, etc.
- **Retry Tracking**: retry_count, retry_reasons (JSON array)
- **Error Distribution**: error_phase_distribution (JSON)
- **Recovery Metrics**: recovery_time_seconds

#### Quality Scoring
- **Input Quality**: nl_input_clarity_score (0-100)
- **Efficiency Scores**: cost_efficiency_score, performance_score, quality_score
- **Complexity**: estimated vs actual complexity (low/medium/high)
- **Insights**: anomaly_flags, optimization_recommendations

#### Temporal Analysis
- **Time Patterns**: hour_of_day (0-23), day_of_week (0-6)
- **Trend Analysis**: 30-day trends for cost, duration, success rate

#### Outcome Tracking
- **GitHub Integration**: PR merged status, time to merge
- **Review Metrics**: review_cycles count
- **CI/CD**: ci_test_pass_rate

#### Phase Execution
- **Phase Status**: started, completed, failed, skipped
- **Phase Timing**: started_at, completed_at, duration_seconds
- **Phase Costs**: tokens_used, cost_usd per phase
- **Phase Errors**: error_message per phase

#### User Input
- **Natural Language**: nl_input capture
- **Issue Metadata**: title, body, type, complexity
- **Multi-Phase**: is_multi_phase, phase_count, parent_issue
- **Estimates**: estimated_cost_usd, estimated_tokens

#### Pattern Learning
- **Pattern Detection**: Automatic pattern discovery from execution
- **ROI Calculation**: Cost with LLM vs tool automation
- **Pattern Tracking**: occurrence_count, confidence_score
- **Automation Status**: candidate, approved, implemented, rejected

### ❌ What is NOT Being Tracked (Gaps)

#### Individual Tool Calls
**Status:** NOT IMPLEMENTED

- No tracking of Bash, Read, Write, Edit, Grep operations
- No tool call sequences or patterns
- No tool-level duration or success/failure tracking
- No tool call context (file types, parameters)

**Impact:** Cannot analyze tool usage efficiency, detect redundant operations, or optimize tool call patterns

#### Hook Events Integration
**Status:** UNCLEAR

- Schema exists (`hook_events` table)
- Integration status unknown
- May not be actively populated during workflow runs

**Impact:** Missing PreToolUse/PostToolUse event capture for detailed analysis

#### Decision Points
**Status:** NOT IMPLEMENTED

- LLM reasoning steps not captured
- Tool selection rationale not logged
- Branch decisions (retry vs modify) not tracked
- Context compaction decisions not recorded

**Impact:** Cannot understand what drives agent decisions or optimize decision-making

#### Granular Context Usage
**Status:** LIMITED

- No context size per tool call
- No cache hit/miss at tool-level (only workflow-level)
- No input vs output token breakdown per tool

**Impact:** Cannot optimize context management or identify context bloat

#### Resource Utilization
**Status:** MINIMAL

- Only tracks: worktree_path, ports
- Missing: CPU, memory, disk usage during execution
- No network I/O tracking
- No database query tracking

**Impact:** Cannot identify resource bottlenecks or optimize resource allocation

#### Multi-Phase Relationships
**Status:** PARTIAL

- Tracks phase_count but not parent-child relationships
- No parent_adw_id field for linking child workflows
- No dependency graph between phases

**Impact:** Cannot analyze how parent workflow decisions affect child phases

#### GitHub Artifact Tracking
**Status:** MINIMAL

- Only tracks PR merged status
- Missing: commits made, PR created timestamp, review comments
- No link to specific commits or branches

**Impact:** Cannot correlate workflow actions with GitHub artifacts

---

## Integration Points

### Best Injection Points for New Tracking

#### Priority 1: Low Effort, High Value

**1. Tool Call Tracking**
- **Where:** `adws/adw_modules/observability.py` - extend `log_task_completion()`
- **What:** Add `tool_calls` parameter (JSON array)
- **Track:** tool_name, duration_ms, success, parameters, result
- **Storage:** Extend `task_logs.tool_calls` field (JSONB)

**2. Model Performance Metrics**
- **Where:** `app/server/core/workflow_history_utils/enrichment.py`
- **What:** Create `enrich_model_performance()` function
- **Track:** Per-model latency, cost variance, success rates
- **Storage:** Extend `workflow_history` with model-specific fields

**3. Cache Analysis Enhancement**
- **Where:** `enrichment.py:enrich_cost_data()`
- **What:** Analyze cache patterns by operation type
- **Track:** Cache hit rate by tool, file type, operation
- **Storage:** Extend `token_breakdown` JSON

#### Priority 2: Medium Effort, Strategic Value

**4. Pattern Execution Tracking**
- **Where:** `sync_manager.py:sync_workflow_history()`
- **What:** Link workflows to patterns used
- **Track:** Which patterns executed, success rate, ROI
- **Storage:** New table `pattern_executions`

**5. Multi-Phase Relationships**
- **Where:** `database/schema.py`
- **What:** Add `parent_adw_id` field
- **Track:** Parent-child workflow dependencies
- **Storage:** `workflow_history.parent_adw_id` (foreign key)

**6. GitHub Artifact Tracking**
- **Where:** `enrichment.py:enrich_github_state()`
- **What:** Fetch PR creation, commits, reviews
- **Track:** PR created timestamp, commit SHAs, review count
- **Storage:** Extend `workflow_history` with GitHub fields

#### Priority 3: Foundational but Higher Effort

**7. Phase Dependency Graph**
- **Where:** New table + enrichment function
- **What:** Build dependency graph from phase execution
- **Track:** Critical path, predecessor impacts
- **Storage:** New table `phase_dependencies`

**8. Resource Utilization Monitoring**
- **Where:** ADW agent execution wrapper
- **What:** Monitor CPU, memory, disk during execution
- **Track:** Resource usage over time
- **Storage:** New table `resource_snapshots`

---

## Analytics Capabilities

### Current Analytics Queries

#### Cost Analytics
**Routes:** `app/server/routes/cost_analytics_routes.py`

**Available Queries:**
- `/cost-analytics/breakdown-by-phase` - Cost distribution across Plan, Build, Test, Review, Document, Ship
- `/cost-analytics/breakdown-by-workflow-type` - Cost comparison by workflow template
- `/cost-analytics/trends` - 7-day moving average with percentage change
- `/cost-analytics/optimizations` - High-cost phases and workflow types

**Example Response:**
```json
{
  "by_phase": {
    "Plan": {"total": 2.50, "avg": 0.25, "count": 10},
    "Build": {"total": 5.75, "avg": 0.58, "count": 10},
    "Test": {"total": 8.20, "avg": 0.82, "count": 10}
  },
  "trends": {
    "daily_costs": [...],
    "moving_average_7d": [...],
    "percent_change": 15.2
  }
}
```

#### Latency Analytics
**Routes:** `app/server/routes/latency_analytics_routes.py`

**Available Queries:**
- `/latency-analytics/summary` - P50, P95, P99 latency distribution
- `/latency-analytics/by-phase` - Phase-specific latency breakdown
- `/latency-analytics/bottlenecks` - Phases exceeding p95 threshold
- `/latency-analytics/trends` - Historical latency patterns

**Example Response:**
```json
{
  "summary": {
    "p50": 120.5,
    "p95": 450.2,
    "p99": 780.8,
    "avg": 156.3
  },
  "bottlenecks": [
    {"phase": "Test", "p95": 520.5, "count": 15}
  ],
  "recommendations": [
    "Optimize Test phase - 30% of workflows exceed p95"
  ]
}
```

#### Error Analytics
**Routes:** `app/server/routes/error_analytics_routes.py`

**Available Queries:**
- `/error-analytics/patterns` - Error categorization and frequency
- `/error-analytics/failure-rates` - Failure rate by phase and workflow type
- `/error-analytics/trends` - Error rate changes over time
- `/error-analytics/debug-recommendations` - Actionable suggestions

**Example Response:**
```json
{
  "error_patterns": {
    "ImportError": {"count": 12, "phases": ["Build", "Test"]},
    "TimeoutError": {"count": 5, "phases": ["Test"]}
  },
  "failure_rates": {
    "overall": 0.15,
    "by_phase": {
      "Build": 0.08,
      "Test": 0.25
    }
  },
  "recommendations": [
    {
      "severity": "high",
      "message": "Test phase has 25% failure rate - investigate timeout issues"
    }
  ]
}
```

#### Workflow Analytics
**Routes:** `app/server/routes/workflow_routes.py`

**Available Queries:**
- `/workflows/history` - Filtered workflow history
- `/workflows/trends` - 30-day trends for cost, duration, success rate, cache efficiency
- `/workflows/predict-cost` - Cost prediction based on workflow type, model, complexity
- `/workflows/catalog` - Available workflow templates

**Filters:**
- status (pending, running, completed, failed)
- model_used
- workflow_template
- date_range (start_date, end_date)
- min/max cost, duration

---

## Gaps & Future Enhancements

### Critical Gaps

#### 1. Individual Tool Call Tracking
**Problem:** No tracking of Bash, Read, Write, Edit, Grep operations during workflow execution

**Impact:**
- Cannot analyze tool usage efficiency
- Cannot detect redundant operations (e.g., reading same file multiple times)
- Cannot identify tool call patterns for optimization
- Missing tool-level cost and latency data

**Proposed Solution:**
```python
# Extend task_logs schema
ALTER TABLE task_logs ADD COLUMN tool_calls JSONB;

# Tool call format
{
  "tool_calls": [
    {
      "tool_name": "Bash",
      "command": "pytest tests/",
      "duration_ms": 1250,
      "success": true,
      "tokens_consumed": 450,
      "cache_hit": true,
      "context_size_before": 45000,
      "timestamp": "2025-12-18T10:00:00Z"
    },
    {
      "tool_name": "Read",
      "file_path": "app/server/routes.py",
      "duration_ms": 80,
      "success": true,
      "lines_read": 250,
      "timestamp": "2025-12-18T10:00:05Z"
    }
  ]
}
```

**Implementation:**
1. Extend `observability.py:log_task_completion()` to accept tool_calls parameter
2. Capture tool calls in ADW phase execution
3. Store in `task_logs.tool_calls` JSONB field
4. Create analytics queries for tool usage patterns

#### 2. Tool Sequence Analysis
**Problem:** No tracking of tool call sequences (e.g., Read→Edit→Write patterns)

**Impact:**
- Cannot identify common multi-tool workflows
- Cannot detect inefficient sequences
- Cannot learn optimal tool usage patterns

**Proposed Solution:**
```sql
CREATE TABLE tool_sequences (
    id SERIAL PRIMARY KEY,
    sequence_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,
    session_id TEXT NOT NULL,

    -- Sequence
    tool_sequence TEXT[],  -- ['Read', 'Edit', 'Write']
    sequence_signature TEXT,  -- 'Read→Edit→Write'

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_duration_ms INTEGER,
    step_durations INTEGER[],

    -- Outcome
    success BOOLEAN,
    retry_count INTEGER DEFAULT 0,

    -- Context
    context JSONB,  -- file_types, operation_types

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(adw_id)
);
```

#### 3. Decision Point Tracking
**Problem:** LLM decision-making is not captured

**Impact:**
- Cannot understand what drives tool selection
- Cannot optimize decision strategies
- Cannot learn from successful/failed decisions

**Proposed Solution:**
```python
# Capture decision metadata
{
  "decision_type": "tool_selection",
  "available_options": ["Bash", "Read", "Edit"],
  "chosen_option": "Bash",
  "decision_factors": {
    "context": "test_failed",
    "previous_attempts": 2,
    "file_state": "modified"
  },
  "outcome": "success",
  "time_to_decide_ms": 150
}
```

### Architectural Improvements

#### 1. Event-Driven Architecture
**Current:** Sync manager polls filesystem every 10 seconds
**Proposed:** Message queue for real-time event processing

**Benefits:**
- Instant updates instead of 10s delay
- Reduced filesystem polling overhead
- Better scalability

#### 2. Execution Timeline
**Current:** Only start/end times tracked
**Proposed:** Intermediate checkpoints throughout execution

**Benefits:**
- Detailed execution timeline visualization
- Better bottleneck identification
- More accurate performance analysis

#### 3. Query Optimization
**Current:** Analytics services do full table scans
**Proposed:** Materialized views for common queries

**Example:**
```sql
CREATE MATERIALIZED VIEW mv_workflow_summary AS
SELECT
  workflow_template,
  model_used,
  COUNT(*) as total_workflows,
  AVG(duration_seconds) as avg_duration,
  AVG(actual_cost_total) as avg_cost,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)::REAL / COUNT(*) as success_rate
FROM workflow_history
GROUP BY workflow_template, model_used;
```

#### 4. Audit Trail
**Current:** No tracking of who/what triggered updates
**Proposed:** Add audit fields to all mutations

```sql
ALTER TABLE workflow_history ADD COLUMN updated_by TEXT;
ALTER TABLE workflow_history ADD COLUMN update_source TEXT;  -- 'sync_manager', 'api', 'manual'
```

---

## File Reference

### Database Layer
- **Schema:** `app/server/core/workflow_history_utils/database/schema.py`
- **Queries:** `app/server/core/workflow_history_utils/database/queries.py`
- **Mutations:** `app/server/core/workflow_history_utils/database/mutations.py`
- **Analytics:** `app/server/core/workflow_history_utils/database/analytics.py`

### Services
- **Workflow Service:** `app/server/services/workflow_service.py`
- **Sync Manager:** `app/server/core/workflow_history_utils/sync_manager.py`
- **Enrichment:** `app/server/core/workflow_history_utils/enrichment.py`
- **Cost Analytics:** `app/server/services/cost_analytics_service.py`
- **Latency Analytics:** `app/server/services/latency_analytics_service.py`
- **Error Analytics:** `app/server/services/error_analytics_service.py`
- **Structured Logger:** `app/server/services/structured_logger.py`

### Models
- **Workflow Models:** `app/server/core/models/workflow.py`
- **Observability Models:** `app/server/core/models/observability.py`
- **Structured Logs:** `app/server/core/models/structured_logs.py`

### Routes
- **Workflow Routes:** `app/server/routes/workflow_routes.py`
- **Observability Routes:** `app/server/routes/observability_routes.py`
- **Cost Analytics Routes:** `app/server/routes/cost_analytics_routes.py`
- **Latency Analytics Routes:** `app/server/routes/latency_analytics_routes.py`
- **Error Analytics Routes:** `app/server/routes/error_analytics_routes.py`

### Repositories
- **Task Log Repository:** `app/server/repositories/task_log_repository.py`
- **Work Log Repository:** `app/server/repositories/work_log_repository.py`

### ADW Observability
- **Observability Module:** `adws/adw_modules/observability.py`
- **Structured Logger:** `adws/adw_modules/structured_logger.py`

---

## Version History

- **v1.0 (2025-12-18):** Initial comprehensive documentation of tracking architecture
