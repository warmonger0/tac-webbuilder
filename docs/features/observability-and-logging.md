# Observability and Logging Infrastructure

## Overview

The tac-webbuilder system includes comprehensive observability, pattern learning, and logging infrastructure to track workflow execution, optimize costs, and maintain session summaries.

This document covers:
- **Hook Events System** - Automated capture of workflow events
- **Pattern Learning** - Automatic detection and tracking of recurring patterns
- **Cost Intelligence** - Track savings and optimization opportunities
- **Work Log System** - Manual session summaries with 280-character Twitter-style logging
- **UI Panel 10** - Work Log viewing and management interface

## System Components

### 1. Hook Events Infrastructure

#### Database Schema
The system captures structured events from workflows via the `hook_events` table:

```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,

    -- Event Classification
    event_type TEXT NOT NULL CHECK(
        event_type IN ('PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop',
                       'SubagentStop', 'PreCompact', 'SessionStart', 'SessionEnd', 'Notification')
    ),
    source_app TEXT,  -- 'main_adw', 'test_adw', 'build_adw', etc.
    session_id TEXT,
    workflow_id TEXT,

    -- Event Data
    timestamp TEXT DEFAULT (datetime('now')),
    payload TEXT NOT NULL,  -- JSON

    -- Context
    tool_name TEXT,
    chat_history TEXT,  -- JSON, optional

    -- Processing
    processed INTEGER DEFAULT 0,  -- For pattern learning queue
    processed_at TEXT,

    created_at TEXT DEFAULT (datetime('now'))
);
```

#### Supported Event Types

| Event Type | Description | Captured Data |
|------------|-------------|---------------|
| `PreToolUse` | Before tool execution | Tool parameters, context snapshot |
| `PostToolUse` | After tool execution | Results, duration, success status |
| `UserPromptSubmit` | User submits input | Prompt text, context |
| `Stop` | Workflow stops | Final state, completion reason |
| `SubagentStop` | Subagent completes | Subagent results |
| `PreCompact` | Before context compaction | Context size metrics |
| `SessionStart` | Session begins | Initial configuration |
| `SessionEnd` | Session ends | Summary metrics |
| `Notification` | System notification | Alert details |

#### Usage
Hook events are **automatically captured** during ADW workflow execution. The data flows to:
1. Real-time monitoring dashboards
2. Pattern learning pipeline
3. Cost optimization analysis
4. Debugging and troubleshooting

### 2. Pattern Learning System

#### Purpose
Automatically detect recurring workflow patterns to:
- Identify automation opportunities
- Estimate potential cost savings
- Track pattern evolution over time
- Build confidence scores for automation

#### What Patterns Represent

Patterns are **deterministic tool orchestration sequences** that occur within ADW phases. When the LLM repeatedly performs the same tool routing for the same type of problem, that's a pattern worth extracting.

**Example Patterns**

**Test-Import-Fix Pattern:**
```
Sequence: Bash(pytest) → Read(test_file) → Grep(imports) → Edit(add_import) → Bash(pytest)
Trigger: ModuleNotFoundError in pytest output
Handler: Auto-add missing import from common libraries
Savings: ~2,000 tokens per occurrence (skip LLM orchestration)
```

**Type-Annotation Pattern:**
```
Sequence: Bash(tsc) → Read(type_file) → Edit(add_property) → Bash(tsc)
Trigger: "Property 'X' is missing in type 'Y'"
Handler: Auto-add missing property with inferred type
Savings: ~1,500 tokens per occurrence
```

**Lint-Line-Length Pattern:**
```
Sequence: Bash(ruff) → Read(file) → Edit(break_line) → Bash(ruff)
Trigger: E501 line too long error
Handler: Auto-format long lines (already handled by pre-commit)
Savings: ~500 tokens per occurrence
```

**What Patterns Are NOT**

- ❌ Full ADW workflows (e.g., "sdlc:full:all")
- ❌ Individual phases (e.g., "test:complete:phase")
- ❌ Single tool calls (e.g., "bash:pytest:run")
- ❌ Non-deterministic sequences (different resolution each time)

Patterns must be:
- **Repeatable** (same sequence)
- **Deterministic** (same input → same output)
- **Valuable** (saves significant tokens)
- **Automatable** (can be a function, not requiring LLM reasoning)

#### Database Schema

**Operation Patterns**
```sql
CREATE TABLE operation_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_signature TEXT UNIQUE NOT NULL,  -- e.g., "test:pytest:backend"
    pattern_type TEXT NOT NULL,              -- e.g., "test", "build", "deploy"

    -- Detection Metrics
    first_detected TEXT,
    last_seen TEXT,
    occurrence_count INTEGER DEFAULT 1,

    -- Characteristics (learned from executions)
    typical_input_pattern TEXT,    -- Common input characteristics
    typical_operations TEXT,        -- JSON array of operations
    typical_files_accessed TEXT,    -- JSON array of file patterns

    -- Cost Analysis
    avg_tokens_with_llm INTEGER DEFAULT 0,
    avg_cost_with_llm REAL DEFAULT 0.0,
    avg_tokens_with_tool INTEGER DEFAULT 0,      -- Estimated at 5% of LLM
    avg_cost_with_tool REAL DEFAULT 0.0,         -- Estimated at 5% of LLM
    potential_monthly_savings REAL DEFAULT 0.0,

    -- Automation Status
    automation_status TEXT DEFAULT 'detected' CHECK(
        automation_status IN ('detected', 'candidate', 'approved', 'implemented', 'active', 'deprecated')
    ),
    confidence_score REAL DEFAULT 0.0,  -- 0.0 to 100.0
    tool_name TEXT,
    tool_script_path TEXT,

    -- Human Review
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_notes TEXT
);
```

**Pattern Occurrences**
```sql
CREATE TABLE pattern_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    workflow_id TEXT NOT NULL,
    similarity_score REAL DEFAULT 0.0,
    matched_characteristics TEXT,  -- JSON
    detected_at TEXT DEFAULT (datetime('now'))
);
```

#### Pattern Detection Flow

1. **Workflow Execution** → Captured in `workflow_history`
2. **Pattern Detection** → `pattern_detector.py` analyzes workflow
3. **Pattern Recording** → `pattern_persistence.py` stores/updates pattern
4. **Statistics Update** → Running averages, confidence scores updated
5. **Cost Estimation** → Calculate potential savings

#### Pattern Signature Examples

```
test:pytest:backend          - Backend pytest execution
test:vitest:frontend         - Frontend vitest execution
build:typescript:full        - Full TypeScript compilation
build:docker:image           - Docker image build
deploy:production:api        - API production deployment
```

#### Confidence Score Calculation

Confidence based on:
- **Occurrence count** (more = higher confidence)
- **Success rate** (fewer failures = higher confidence)
- **Consistency** (similar duration/tokens = higher confidence)
- **Pattern type** (test patterns easier to automate)

Scale: 0-100, threshold for automation consideration: 70+

#### Pattern Statistics Views

**High-Value Patterns**
```sql
CREATE VIEW v_high_value_patterns AS
SELECT
    p.*,
    p.potential_monthly_savings * 12 as annual_savings_usd,
    (SELECT COUNT(*) FROM pattern_occurrences po WHERE po.pattern_id = p.id) as total_occurrences
FROM operation_patterns p
WHERE p.automation_status IN ('detected', 'candidate')
AND p.confidence_score >= 70
AND p.potential_monthly_savings >= 0.50
ORDER BY p.potential_monthly_savings DESC;
```

### 3. Tool Call Tracking

#### Database Schema
```sql
CREATE TABLE tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_call_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,

    -- Tool Details
    tool_name TEXT NOT NULL,
    tool_params TEXT,  -- JSON

    -- Timing
    called_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    duration_seconds REAL,

    -- Results
    success INTEGER DEFAULT 0,
    result_data TEXT,  -- JSON
    error_message TEXT,

    -- Cost Impact
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd REAL DEFAULT 0.0,

    -- Captured via hooks
    pre_tool_snapshot TEXT,   -- JSON from PreToolUse hook
    post_tool_snapshot TEXT   -- JSON from PostToolUse hook
);
```

#### Purpose
Track every tool invocation to:
- Measure actual cost savings
- Monitor tool performance
- Debug tool failures
- Calculate ROI of optimizations

### 4. Cost Savings Tracking

#### Database Schema
```sql
CREATE TABLE cost_savings_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What saved cost
    optimization_type TEXT NOT NULL CHECK(
        optimization_type IN ('tool_call', 'input_split', 'pattern_offload', 'inverted_flow')
    ),
    workflow_id TEXT NOT NULL,
    tool_call_id TEXT,
    pattern_id INTEGER,

    -- Savings
    baseline_tokens INTEGER DEFAULT 0,
    actual_tokens INTEGER DEFAULT 0,
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd REAL DEFAULT 0.0,

    -- Context
    saved_at TEXT DEFAULT (datetime('now')),
    notes TEXT
);
```

#### Optimization Types

| Type | Description | Example |
|------|-------------|---------|
| `tool_call` | Using specialized tool instead of LLM | Running pytest via tool vs asking LLM to run tests |
| `input_split` | Breaking large input into chunks | Split 50-file query into 5x10 batches |
| `pattern_offload` | Detected pattern automated | Recurring test pattern → automated tool |
| `inverted_flow` | Reversing expensive flow | Request-driven sync instead of full sync |

#### Cost Savings View
```sql
CREATE VIEW v_cost_savings_summary AS
SELECT
    optimization_type,
    COUNT(*) as optimization_count,
    SUM(tokens_saved) as total_tokens_saved,
    SUM(cost_saved_usd) as total_cost_saved_usd,
    AVG(cost_saved_usd) as avg_cost_saved_per_use,
    MIN(saved_at) as first_saving,
    MAX(saved_at) as latest_saving
FROM cost_savings_log
GROUP BY optimization_type
ORDER BY total_cost_saved_usd DESC;
```

### 5. Work Log System (Panel 10)

#### Overview
**Manual logging system** for tracking chat session summaries with a 280-character limit (Twitter-style). Unlike the automated hook events, work logs are manually created to document key decisions, outcomes, and session context.

#### Database Schema
```sql
CREATE TABLE work_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL CHECK(length(summary) <= 280),
    chat_file_link TEXT,
    issue_number INTEGER,
    workflow_id TEXT,
    tags TEXT,  -- JSON array stored as text
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### Backend API

**Models** (`core/models/work_log.py`)
```python
class WorkLogEntry(BaseModel):
    id: int | None = None
    timestamp: datetime
    session_id: str
    summary: str = Field(..., max_length=280)
    chat_file_link: str | None = None
    issue_number: int | None = None
    workflow_id: str | None = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime

    @field_validator('summary')
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        if len(v) > 280:
            raise ValueError("Summary must be at most 280 characters")
        return v
```

**API Endpoints** (`routes/work_log_routes.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/work-log` | GET | List all entries (paginated) |
| `/api/v1/work-log` | POST | Create new entry |
| `/api/v1/work-log/session/{id}` | GET | Get entries for session |
| `/api/v1/work-log/{id}` | DELETE | Delete entry |

**Query Parameters**
- `limit` (default: 50) - Max entries to return
- `offset` (default: 0) - Skip this many entries

**Example Request**
```bash
# Create entry
curl -X POST http://localhost:8000/api/v1/work-log \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-2025-12-02",
    "summary": "Added Panel 10 with work log UI. Integrated pattern learning system. Updated all docs.",
    "issue_number": 123,
    "workflow_id": "wf-abc123",
    "tags": ["documentation", "ui", "pattern-learning"]
  }'

# List entries
curl http://localhost:8000/api/v1/work-log?limit=10&offset=0
```

#### Frontend UI (Panel 10)

**Component**: `LogPanel.tsx`

**Features**:
- View paginated work log entries
- Create new entries with form validation
- Filter by session ID
- Delete entries with confirmation
- Tag management (add/remove)
- Display links to chat files, issues, workflows
- Real-time character counter (280 limit)
- Responsive Tailwind CSS design

**API Client** (`api/workLogClient.ts`)
```typescript
// Get all work logs
const logs = await workLogClient.getWorkLogs(limit, offset);

// Create entry
const entry = await workLogClient.createWorkLog({
  session_id: 'session-123',
  summary: 'Completed feature X with pattern Y',
  tags: ['feature', 'pattern']
});

// Filter by session
const sessionLogs = await workLogClient.getSessionWorkLogs('session-123');

// Delete entry
await workLogClient.deleteWorkLog(entryId);
```

**UI Access**: Navigate to **"10. Log Panel"** tab in the main navigation bar.

## Integration Points

### Hook Events → Pattern Learning
1. Workflow executes → Hook events captured
2. Events stored in `hook_events` table
3. Pattern detector analyzes workflow
4. Patterns recorded in `operation_patterns`
5. Statistics updated (costs, confidence)

### Pattern Learning → Cost Savings
1. Pattern detected with high confidence (70+)
2. Cost analysis estimates savings
3. Pattern marked as automation candidate
4. Tool implemented (manual or automated)
5. Savings tracked in `cost_savings_log`

### Work Log → Session Tracking
1. Manual entry creation in Panel 10
2. Link to session_id, issue_number, workflow_id
3. Tag for categorization
4. Reference from other tools/dashboards

## Querying the System

### Find High-Value Automation Candidates
```sql
SELECT
    pattern_signature,
    occurrence_count,
    confidence_score,
    potential_monthly_savings,
    potential_monthly_savings * 12 as annual_savings
FROM v_high_value_patterns
WHERE confidence_score >= 80
ORDER BY potential_monthly_savings DESC
LIMIT 10;
```

### Track Cost Savings Over Time
```sql
SELECT
    DATE(saved_at) as date,
    optimization_type,
    SUM(cost_saved_usd) as daily_savings
FROM cost_savings_log
WHERE saved_at >= datetime('now', '-30 days')
GROUP BY DATE(saved_at), optimization_type
ORDER BY date DESC;
```

### Recent Hook Events by Type
```sql
SELECT
    event_type,
    source_app,
    COUNT(*) as event_count
FROM hook_events
WHERE timestamp >= datetime('now', '-1 day')
GROUP BY event_type, source_app
ORDER BY event_count DESC;
```

### Session Work Log Summary
```sql
SELECT
    session_id,
    COUNT(*) as log_count,
    GROUP_CONCAT(DISTINCT tags) as all_tags,
    MIN(created_at) as first_log,
    MAX(created_at) as last_log
FROM work_log
GROUP BY session_id
ORDER BY last_log DESC;
```

## Best Practices

### Hook Events
- ✅ **Do**: Rely on automatic capture - no manual intervention needed
- ✅ **Do**: Use for debugging and pattern analysis
- ❌ **Don't**: Manually insert hook events
- ❌ **Don't**: Delete hook events (archive old data instead)

### Pattern Learning
- ✅ **Do**: Review patterns with confidence > 70 for automation
- ✅ **Do**: Monitor `v_high_value_patterns` view regularly
- ✅ **Do**: Document automation decisions in `review_notes`
- ❌ **Don't**: Automate low-confidence patterns (<50)
- ❌ **Don't**: Ignore patterns with high monthly savings

### Work Logs
- ✅ **Do**: Keep summaries concise and actionable (280 char limit)
- ✅ **Do**: Link to issue numbers and workflow IDs
- ✅ **Do**: Use tags consistently (`bug`, `feature`, `refactor`, `docs`, etc.)
- ✅ **Do**: Include key decisions and outcomes
- ❌ **Don't**: Duplicate information already in hook events
- ❌ **Don't**: Use for verbose documentation (use docs/ instead)

### Cost Tracking
- ✅ **Do**: Track all optimization types
- ✅ **Do**: Measure before/after tokens for accuracy
- ✅ **Do**: Link to pattern_id when applicable
- ❌ **Don't**: Estimate savings without baseline measurement

## Troubleshooting

### No Hook Events Captured
1. Check workflow is using hooks-enabled ADW
2. Verify `hook_events` table exists (run migration 004)
3. Check database connection
4. Review workflow logs for errors

### Patterns Not Detected
1. Ensure workflows have `workflow_id` populated
2. Check pattern detector is running
3. Verify `process_workflow_for_patterns()` is called
4. Review pattern detection logs

### Work Log Validation Errors
1. **"Summary too long"** → Reduce to 280 characters
2. **"Session ID required"** → Provide session_id
3. **404 on delete** → Entry already deleted or invalid ID

## Monitoring Dashboard Locations

| Dashboard | Location | Purpose |
|-----------|----------|---------|
| Hook Events | Panel 2 (ADW's Panel) → Current Workflow | Real-time workflow events |
| Pattern Stats | Database query or future Panel | Pattern detection metrics |
| Cost Savings | Future Panel | ROI and optimization impact |
| Work Logs | **Panel 10 (Log Panel)** | Session summaries |

## Future Enhancements

### Planned Features
- [ ] **Pattern Recommendation Engine** - AI-suggested automation candidates
- [ ] **Cost Dashboard Panel** - Visual cost savings over time
- [ ] **Pattern Analytics Panel** - Deep-dive pattern analysis
- [ ] **Work Log Search** - Full-text search across summaries
- [ ] **Export Functionality** - Export logs/patterns to CSV/JSON
- [ ] **Automated Pattern Tool Generation** - Auto-create tools from patterns

### Under Consideration
- [ ] Hook event replay for debugging
- [ ] Pattern similarity clustering
- [ ] Real-time cost savings alerts
- [ ] Work log templates
- [ ] Session analytics dashboard

## Related Documentation

- [Architecture](../architecture.md) - Overall system design
- [API Reference](../api.md) - Complete API documentation
- [Database Migrations](../../migration/README.md) - Migration 004 details
- [ADW Documentation](./adw/README.md) - ADW workflow system
- [Cost Optimization](./cost-optimization/README.md) - Cost optimization strategies
- [Pattern Learning](../planned_features/pattern-learning/) - Future pattern learning enhancements

## Schema Diagram

```
┌─────────────────┐
│  workflow_history│
│  (executions)   │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┬──────────────┐
         │              │              │              │              │
┌────────▼────────┐ ┌───▼────────┐ ┌──▼──────────┐ ┌──▼──────────┐ ┌▼──────────┐
│  hook_events    │ │ tool_calls │ │  operation  │ │cost_savings │ │ work_log  │
│  (automated)    │ │  (tracked) │ │  _patterns  │ │    _log     │ │ (manual)  │
└─────────────────┘ └────────────┘ └──────┬──────┘ └─────────────┘ └───────────┘
                                           │
                                   ┌───────▼────────┐
                                   │    pattern     │
                                   │  _occurrences  │
                                   └────────────────┘
```

## Summary

The tac-webbuilder observability infrastructure provides:
1. **Automated tracking** via hook events and pattern learning
2. **Cost intelligence** through pattern analysis and savings tracking
3. **Manual logging** via Work Log system (Panel 10)
4. **Complete visibility** into workflow execution and optimization

This multi-layered approach enables both real-time monitoring and long-term trend analysis while maintaining flexibility for manual annotation and review.
