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

### 3. Pattern Review Workflow

Before detected patterns are automated, they go through manual review for safety and validation.

#### Review Criteria

Patterns are categorized based on confidence, occurrence count, and estimated savings:

- **Auto-Approve (>99%):** Well-known patterns, 200+ occurrences, $5000+ annual savings
- **Manual Review (95-99%):** Novel patterns, 100-200 occurrences, $1000-5000 annual savings
- **Auto-Reject (<95%):** Suspicious patterns, destructive operations, low occurrence count

#### Database Schema

**Pattern Approvals**
```sql
CREATE TABLE pattern_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'auto-approved', 'auto-rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    approval_notes TEXT,
    confidence_score REAL NOT NULL,
    occurrence_count INTEGER NOT NULL,
    estimated_savings_usd REAL NOT NULL,
    tool_sequence TEXT NOT NULL,
    pattern_context TEXT,
    example_sessions TEXT,  -- JSON array of session IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Pattern Review History**
```sql
CREATE TABLE pattern_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('approved', 'rejected', 'flagged', 'commented')),
    reviewer TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### CLI Usage

**Show Statistics**
```bash
python scripts/review_patterns.py --stats
```

**Review All Pending Patterns**
```bash
python scripts/review_patterns.py
python scripts/review_patterns.py --limit 10
```

**Review Specific Pattern**
```bash
python scripts/review_patterns.py --pattern-id test-retry-pattern
```

**Custom Reviewer Name**
```bash
python scripts/review_patterns.py --reviewer "Jane Smith"
```

#### Review Actions

During interactive review, you can:

- **[a] Approve:** Pattern will be queued for automation (optional notes)
- **[r] Reject:** Pattern blocked from automation (reason required)
- **[s] Skip:** Review pattern later
- **[d] Details:** Show full JSON pattern data
- **[q] Quit:** Exit review session

#### Impact Score Calculation

Patterns are prioritized by impact score for review:

```
Impact Score = Confidence × Occurrence Count × Estimated Savings (USD)
```

**Example:**
- Confidence: 98% (0.98)
- Occurrences: 250
- Estimated Savings: $2,500
- **Impact Score: 612,500**

Higher impact patterns are shown first for review.

#### Integration

Approved patterns feed into Sessions 12-13 (Closed-loop learning, workflow generation). The review system acts as a safety gate between pattern detection and automated workflow generation.

#### Audit Trail

All review actions are logged in `pattern_review_history` table, providing full transparency:
- Who reviewed the pattern
- What action was taken
- When the review occurred
- Why the decision was made (notes/reason)

This ensures accountability and allows pattern review decisions to be audited or reversed if needed.

### 4. Daily Pattern Analysis

The daily pattern analysis system automatically discovers automation patterns from hook events, calculates metrics, and populates the pattern review system for approval.

#### Overview

The analysis system runs as a scheduled batch job (typically daily) to:
- Extract tool sequences from `hook_events` table
- Identify repeated patterns across multiple sessions
- Calculate confidence scores using statistical analysis
- Estimate cost savings for each pattern
- Auto-classify patterns based on thresholds
- Deduplicate against existing patterns
- Notify reviewers of new patterns requiring approval

#### How It Works

1. **Extraction**: Query `hook_events` table for configurable time window (default: last 24 hours)
2. **Pattern Discovery**: Group tool sequences by session, identify repeated patterns
3. **Metrics Calculation**: Calculate confidence scores, occurrence counts, estimated savings
4. **Auto-Classification**:
   - **Auto-approve**: >99% confidence + 200+ occurrences + $5000+ savings
   - **Auto-reject**: <95% confidence OR destructive operations
   - **Pending**: 95-99% confidence (manual review required)
5. **Deduplication**: Check existing patterns, update occurrence counts
6. **Notification**: Alert reviewers of new pending patterns

#### Analysis Script

**Location**: `scripts/analyze_daily_patterns.py`

**Manual Execution**:
```bash
# Analyze last 24 hours (default)
python scripts/analyze_daily_patterns.py

# Analyze last 48 hours
python scripts/analyze_daily_patterns.py --hours 48

# Customize minimum occurrences threshold
python scripts/analyze_daily_patterns.py --min-occurrences 5

# Dry run (no database changes)
python scripts/analyze_daily_patterns.py --dry-run --verbose

# Generate markdown report
python scripts/analyze_daily_patterns.py --report

# Send notifications for new pending patterns
python scripts/analyze_daily_patterns.py --notify
```

**Automated Execution**:

The cron wrapper script runs analysis daily at 2 AM:

```bash
# Install cron job
chmod +x scripts/cron/daily_pattern_analysis.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /path/to/tac-webbuilder/scripts/cron/daily_pattern_analysis.sh
```

**Cron wrapper** (`scripts/cron/daily_pattern_analysis.sh`):
- Sets up database environment variables
- Runs analysis with reporting and notifications
- Logs output to `logs/pattern_analysis_YYYYMMDD.log`
- Cleans up old logs (keeps last 30 days)
- Sends email alerts on failure (if configured)

#### Configuration

**Analysis Thresholds** (in `analyze_daily_patterns.py`):

```python
# Auto-approve criteria
confidence > 0.99 and occurrences > 200 and savings > 5000

# Auto-reject criteria
confidence < 0.95 or has_destructive_operations

# Pending review criteria
0.95 <= confidence <= 0.99
```

**Destructive Operations** (auto-rejected):
- Delete, Remove, Drop, Truncate, ForceDelete
- DeleteFile, RemoveFile, DropTable, TruncateTable

#### Confidence Score Calculation

```python
def calculate_confidence(occurrences, total_sessions):
    """Statistical confidence based on frequency and occurrence count."""
    frequency = occurrences / total_sessions

    # Boost confidence for high occurrence counts
    if occurrences >= 100:
        confidence = min(0.99, frequency * 1.2)
    elif occurrences >= 50:
        confidence = min(0.97, frequency * 1.15)
    elif occurrences >= 10:
        confidence = min(0.95, frequency * 1.1)
    else:
        confidence = frequency

    return confidence
```

#### Estimated Savings Calculation

```python
def estimate_savings(pattern, occurrences):
    """Estimate cost savings if pattern is automated."""
    # Average time per tool execution
    avg_time_per_tool = 30  # seconds

    # Parse tool sequence
    tools = pattern.split('→')
    pattern_time_seconds = len(tools) * avg_time_per_tool

    # Assume $100/hour AI cost (conservative)
    cost_per_second = 100.0 / 3600.0

    # Savings if automated
    savings_per_occurrence = pattern_time_seconds * cost_per_second
    total_savings = savings_per_occurrence * occurrences

    return total_savings
```

#### Output Format

**Console Output**:
```
================================================================================
DAILY PATTERN ANALYSIS SUMMARY
================================================================================
Analysis Window:     24 hours
Total Sessions:      145
Patterns Discovered: 12
  - New Patterns:    8
  - Updated:         4

Classification:
  - Auto-Approved:   2
  - Pending Review:  7
  - Auto-Rejected:   3

Estimated Total Savings: $12,450.00
================================================================================
```

**Report Generation** (`--report` flag):

Generates markdown report in `logs/pattern_analysis_YYYYMMDD_HHMMSS.md`:

```markdown
# Daily Pattern Analysis Report

**Generated:** 2025-12-07T10:00:00
**Analysis Window:** 24 hours

## Summary
- Total Sessions: 145
- Patterns Discovered: 12
- New Patterns: 8
- Updated Patterns: 4

## Classification
- Auto-Approved: 2
- Pending Review: 7
- Auto-Rejected: 3

## Impact
- Estimated Total Savings: $12,450.00
```

#### Notification System

When new patterns require manual review, notifications are logged to `logs/pattern_notifications.log`:

```
[2025-12-07T10:00:00]
New Patterns Requiring Review
==============================
Date: 2025-12-07T10:00:00

7 new patterns discovered that require manual approval.

Pattern: Read→Edit→Write
Confidence: 97.5%
Occurrences: 150
Estimated Savings: $3,750.00
---

Pattern: Test→Fix→Test
Confidence: 96.2%
Occurrences: 85
Estimated Savings: $2,125.00
---
...

Review via CLI: python scripts/review_patterns.py
Review via Web UI: http://localhost:5173 (Panel 8)
```

**Future Enhancement**: Email/Slack notifications (infrastructure ready).

#### Review Workflow Integration

After daily analysis discovers new patterns:

1. **CLI Review**:
   ```bash
   python scripts/review_patterns.py --stats
   python scripts/review_patterns.py  # Interactive review
   ```

2. **Web UI Review** (Future - Panel 8):
   - Navigate to Panel 8 (Review Panel)
   - Review pending patterns
   - Approve/reject with notes

3. **Automated Workflows** (Future - Sessions 12+):
   - Auto-approved patterns ready for workflow generation
   - Pending patterns require manual review
   - Auto-rejected patterns logged for audit

#### Database Integration

**Service Methods** (in `pattern_review_service.py`):

```python
# Create new pattern
service.create_pattern({
    'pattern_id': 'abc123',
    'status': 'pending',
    'tool_sequence': 'Read→Edit→Write',
    'confidence_score': 0.97,
    'occurrence_count': 150,
    'estimated_savings_usd': 3750.0,
    'pattern_context': 'Sequence of 3 tools: Read, Edit, Write',
    'example_sessions': ['session-1', 'session-2', ...]
})

# Update occurrence count for existing pattern
service.update_occurrence_count('abc123', new_count=175)
```

#### Testing

Run comprehensive test suite:

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql python -m pytest scripts/tests/test_daily_pattern_analysis.py -v
```

**Test Coverage** (13 tests):
- ✅ Extract tool sequences from hook events
- ✅ Find repeated patterns
- ✅ Calculate confidence (high/low occurrences)
- ✅ Estimate savings
- ✅ Auto-classify (high confidence, low confidence, pending, destructive)
- ✅ Save new pattern
- ✅ Update existing pattern
- ✅ Calculate metrics
- ✅ Full analysis workflow

#### Best Practices

**Analysis Frequency**:
- ✅ **Do**: Run daily during off-peak hours (2 AM)
- ✅ **Do**: Generate reports for trending analysis
- ❌ **Don't**: Run too frequently (hourly) - creates noise
- ❌ **Don't**: Analyze windows shorter than 12 hours

**Pattern Classification**:
- ✅ **Do**: Review pending patterns promptly
- ✅ **Do**: Document rejection reasons
- ✅ **Do**: Monitor auto-approved patterns
- ❌ **Don't**: Lower confidence thresholds without justification
- ❌ **Don't**: Ignore high-savings patterns

**Maintenance**:
- ✅ **Do**: Monitor log files for errors
- ✅ **Do**: Archive old analysis reports (30+ days)
- ✅ **Do**: Review notification queue regularly
- ❌ **Don't**: Disable notifications for pending patterns
- ❌ **Don't**: Ignore cron job failures

#### Troubleshooting

**No patterns discovered**:
1. Check hook_events table has data: `SELECT COUNT(*) FROM hook_events WHERE timestamp >= NOW() - INTERVAL '24 hours'`
2. Verify PreToolUse events exist: `SELECT COUNT(*) FROM hook_events WHERE event_type = 'PreToolUse'`
3. Check minimum occurrence threshold (default: 2)
4. Review session_id population in hook_events

**Analysis script fails**:
1. Check database connection: `echo $POSTGRES_HOST $POSTGRES_PORT`
2. Verify database credentials
3. Check logs: `tail -f logs/pattern_analysis_YYYYMMDD.log`
4. Run with `--verbose` flag for detailed output

**Patterns not auto-classifying correctly**:
1. Review confidence calculation logic
2. Check threshold values in `auto_classify()` method
3. Verify occurrence counts and savings calculations
4. Test with `--dry-run` flag first

**Cron job not running**:
1. Verify crontab entry: `crontab -l`
2. Check script permissions: `ls -la scripts/cron/daily_pattern_analysis.sh`
3. Review cron logs: `/var/log/cron` or `grep CRON /var/log/syslog`
4. Test script manually first

#### Performance Metrics

**Typical Performance** (1000 sessions/day):
- Analysis time: ~10-30 seconds
- Patterns discovered: 5-15 per day
- Database impact: Minimal (read-heavy, few writes)
- Log size: ~100-500 KB per day

**Scaling Considerations**:
- 10,000+ sessions/day: Consider partitioning hook_events table
- 100+ patterns/day: Batch notification system
- Large tool sequences (20+ tools): May need sequence length limits

### 5. Tool Call Tracking

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

### 6. Cost Savings Tracking

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

### 7. Work Log System (Panel 10)

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
