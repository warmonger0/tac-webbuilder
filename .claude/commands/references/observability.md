# Observability & Logging Quick Reference

## Four Integrated Systems

### 1. Hook Events (Automated Capture)
**Table:** `hook_events`
**Purpose:** Capture workflow execution events automatically during ADW runs

**Event Types:**
- PreToolUse / PostToolUse - Tool invocations
- UserPromptSubmit - User input
- SessionStart / SessionEnd - Session lifecycle
- Stop / SubagentStop - Workflow completion
- PreCompact - Context optimization
- Notification - System notifications

**Key Fields:**
- `event_id` - Unique identifier
- `event_type` - Event category
- `tool_name` - Tool being used
- `parameters` - Tool parameters (JSON)
- `results` - Tool results (JSON)
- `duration_ms` - Execution time
- `success` - Success/failure flag
- `context_snapshot` - State at event time

### 2. Pattern Learning (AI-Driven Optimization)
**Tables:** `operation_patterns`, `pattern_occurrences`
**Purpose:** Detect recurring workflows for automation opportunities

**Pattern Detection Flow:**
1. Hook events captured during execution
2. Pattern signatures extracted (e.g., "test:pytest:backend")
3. Occurrence counting and typical operations learned
4. Confidence scoring (0-100)
5. Cost analysis (duration, tokens, estimated savings)

**Pattern States:**
- `detected` - Pattern identified
- `candidate` - Ready for automation consideration
- `approved` - Greenlit for implementation
- `implemented` - Automation created
- `active` - Running in production

**Key View:** `v_high_value_patterns` - Patterns with >70 confidence, >$0.50/month savings

### 3. Cost Tracking (ROI Measurement)
**Tables:** `cost_savings_log`, `tool_calls`
**Purpose:** Track optimization impact and measure savings

**Optimization Types:**
- `tool_call` - Replaced LLM call with specialized tool
- `input_split` - Split large context into focused chunks
- `pattern_offload` - Automated recurring pattern
- `inverted_flow` - Restructured workflow for efficiency

**Metrics Tracked:**
- `tokens_saved` - Token reduction
- `cost_saved_usd` - Dollar savings
- `baseline_cost` - Original cost
- `actual_cost` - Optimized cost
- `optimization_type` - Category

**Key View:** `v_cost_savings_summary` - Aggregated savings by type

### 4. Work Logs (Manual Session Logging)
**Table:** `work_log`
**Purpose:** Twitter-style 280-character session summaries (Panel 10)

**Features:**
- 280-character limit for concise summaries
- Session tracking with metadata
- Tag-based categorization
- Links to issues, workflows, chat files
- Full CRUD via API and UI

**Fields:**
- `entry_id` - Auto-increment ID
- `session_id` - Session identifier
- `summary` - 280-char summary (required)
- `chat_file_link` - Path to chat file
- `issue_number` - GitHub issue reference
- `workflow_id` - ADW workflow reference
- `tags` - JSON array of tags
- `created_at` - Timestamp

## API Endpoints

### Work Log API (`/api/v1/work-log`)
```
POST   /                     Create entry (280 char limit)
GET    /                     List entries (paginated: limit, offset)
GET    /session/{session_id} Filter by session
DELETE /{entry_id}           Delete entry
```

**Example Request:**
```json
{
  "session_id": "2025-12-02-panel-10",
  "summary": "Fixed N+1 query in queue_routes.py. Replaced get_all() loop with find_by_id(). 100x speedup on 100-item queue. Tests pass.",
  "tags": ["performance", "database", "n+1"],
  "issue_number": 123,
  "workflow_id": "adw_20251202_103045"
}
```

### ADW Monitor API (`/api/v1/adw-monitor`)
**Purpose:** Real-time workflow status with hook event integration

**Response Fields:**
- Active ADWs with progress
- Phase execution history
- Cost accumulation
- Hook event counts
- Error tracking

## Database Schema Quick Reference

### hook_events Table
```sql
CREATE TABLE hook_events (
    event_id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    tool_name TEXT,
    parameters TEXT,  -- JSON
    results TEXT,     -- JSON
    duration_ms INTEGER,
    success BOOLEAN,
    context_snapshot TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### operation_patterns Table
```sql
CREATE TABLE operation_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_signature TEXT UNIQUE,
    occurrence_count INTEGER DEFAULT 1,
    typical_operations TEXT,  -- JSON array
    confidence_score INTEGER CHECK(confidence_score >= 0 AND confidence_score <= 100),
    avg_duration_ms INTEGER,
    avg_token_usage INTEGER,
    estimated_monthly_savings_usd REAL,
    status TEXT DEFAULT 'detected',  -- detected, candidate, approved, implemented, active
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### cost_savings_log Table
```sql
CREATE TABLE cost_savings_log (
    log_id INTEGER PRIMARY KEY,
    optimization_type TEXT NOT NULL,
    baseline_cost REAL,
    actual_cost REAL,
    tokens_saved INTEGER,
    cost_saved_usd REAL,
    workflow_id TEXT,
    pattern_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(pattern_id)
);
```

### work_log Table
```sql
CREATE TABLE work_log (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL CHECK(length(summary) <= 280),
    chat_file_link TEXT,
    issue_number INTEGER,
    workflow_id TEXT,
    tags TEXT,  -- JSON array
    created_at TEXT DEFAULT (datetime('now'))
);
```

## Integration Flow

```
ADW Execution
    ↓
Hook Events Captured
    ↓
Pattern Detection (async)
    ↓
Confidence Scoring
    ↓
Cost Analysis
    ↓
High-Value Patterns → v_high_value_patterns view
    ↓
Manual Review → Pattern approval
    ↓
Automation Implementation
    ↓
Cost Savings Tracked → cost_savings_log
```

## Common Use Cases

### Viewing High-Value Automation Opportunities
```sql
SELECT * FROM v_high_value_patterns
WHERE confidence_score > 70
  AND estimated_monthly_savings_usd > 0.50
ORDER BY estimated_monthly_savings_usd DESC;
```

### Tracking Total Savings
```sql
SELECT
    optimization_type,
    SUM(cost_saved_usd) as total_saved,
    SUM(tokens_saved) as total_tokens_saved,
    COUNT(*) as optimization_count
FROM cost_savings_log
GROUP BY optimization_type
ORDER BY total_saved DESC;
```

### Recent Work Log Entries
```sql
SELECT * FROM work_log
WHERE session_id = '2025-12-02-panel-10'
ORDER BY created_at DESC
LIMIT 50;
```

## When to Load Full Documentation

**Load full docs when:**
- Implementing observability features
- Troubleshooting pattern detection
- Understanding complete integration flow
- Setting up new hook event types
- Designing automation workflows

**Full Documentation:**
→ `docs/features/observability-and-logging.md` [566 lines, ~2,500 tokens]

**Contains:**
- Complete database schema with indexes
- Detailed API documentation
- Integration examples
- Best practices and troubleshooting
- Performance considerations
- Security guidelines
