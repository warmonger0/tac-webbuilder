-- Migration 004: Add Observability and Pattern Learning Tables
-- Implements the complete cost optimization intelligence system with:
-- - Tool call tracking (LLM tool orchestration)
-- - Hook event capture (structured observability)
-- - Pattern learning (automated optimization discovery)
-- - Cost savings tracking (ROI measurement)
-- - ADW tool registry (specialized workflow tools)

-- ============================================================================
-- RENAME workflow_history to workflow_executions (semantic clarity)
-- ============================================================================
-- NOTE: SQLite doesn't support ALTER TABLE RENAME directly with all constraints
-- We'll add new columns to workflow_history instead and use it as workflow_executions

ALTER TABLE workflow_history ADD COLUMN workflow_id TEXT;
ALTER TABLE workflow_history ADD COLUMN workflow_type TEXT DEFAULT 'planning';
ALTER TABLE workflow_history ADD COLUMN parent_workflow_id TEXT;
ALTER TABLE workflow_history ADD COLUMN input_hash TEXT;
ALTER TABLE workflow_history ADD COLUMN output_summary TEXT;

-- Create index on workflow_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_workflow_history_workflow_id ON workflow_history(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_workflow_type ON workflow_history(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflow_history_parent_id ON workflow_history(parent_workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_input_hash ON workflow_history(input_hash);

-- ============================================================================
-- TOOL CALLS TABLE - Tracks LLM tool invocations
-- ============================================================================
CREATE TABLE IF NOT EXISTS tool_calls (
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
    success INTEGER DEFAULT 0,  -- SQLite uses INTEGER for BOOLEAN
    result_data TEXT,  -- JSON
    error_message TEXT,

    -- Cost Impact
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd REAL DEFAULT 0.0,

    -- Captured via hooks
    pre_tool_snapshot TEXT,  -- JSON from PreToolUse hook
    post_tool_snapshot TEXT,  -- JSON from PostToolUse hook

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_workflow ON tool_calls(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_name ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_called_at ON tool_calls(called_at);
CREATE INDEX IF NOT EXISTS idx_tool_calls_success ON tool_calls(success);

-- ============================================================================
-- OPERATION PATTERNS TABLE - Pattern learning core
-- ============================================================================
CREATE TABLE IF NOT EXISTS operation_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_signature TEXT UNIQUE NOT NULL,
    pattern_type TEXT NOT NULL,

    -- Detection
    first_detected TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now')),
    occurrence_count INTEGER DEFAULT 1,

    -- Characteristics (learned from actual executions)
    typical_input_pattern TEXT,  -- Common input characteristics
    typical_operations TEXT,  -- JSON array of operations
    typical_files_accessed TEXT,  -- JSON array of file patterns

    -- Cost Analysis
    avg_tokens_with_llm INTEGER DEFAULT 0,
    avg_cost_with_llm REAL DEFAULT 0.0,
    avg_tokens_with_tool INTEGER DEFAULT 0,
    avg_cost_with_tool REAL DEFAULT 0.0,
    potential_monthly_savings REAL DEFAULT 0.0,

    -- Automation Status
    automation_status TEXT DEFAULT 'detected' CHECK(
        automation_status IN ('detected', 'candidate', 'approved', 'implemented', 'active', 'deprecated')
    ),
    confidence_score REAL DEFAULT 0.0,
    tool_name TEXT,
    tool_script_path TEXT,

    -- Human Review
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_notes TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_operation_patterns_type ON operation_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_status ON operation_patterns(automation_status);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_confidence ON operation_patterns(confidence_score);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_occurrence ON operation_patterns(occurrence_count);

-- ============================================================================
-- PATTERN OCCURRENCES TABLE - Links executions to patterns
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    workflow_id TEXT NOT NULL,

    -- Similarity Metrics
    similarity_score REAL DEFAULT 0.0,
    matched_characteristics TEXT,  -- JSON

    detected_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id),
    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_workflow ON pattern_occurrences(workflow_id);
CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_detected ON pattern_occurrences(detected_at);

-- ============================================================================
-- HOOK EVENTS TABLE - Raw hook data from observability system
-- ============================================================================
CREATE TABLE IF NOT EXISTS hook_events (
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

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_hook_events_type ON hook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_hook_events_session ON hook_events(session_id);
CREATE INDEX IF NOT EXISTS idx_hook_events_workflow ON hook_events(workflow_id);
CREATE INDEX IF NOT EXISTS idx_hook_events_processed ON hook_events(processed);
CREATE INDEX IF NOT EXISTS idx_hook_events_timestamp ON hook_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_hook_events_source_app ON hook_events(source_app);

-- ============================================================================
-- ADW TOOLS TABLE - Registry of available specialized tools
-- ============================================================================
CREATE TABLE IF NOT EXISTS adw_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT UNIQUE NOT NULL,

    -- Tool Definition
    description TEXT NOT NULL,
    tool_schema TEXT NOT NULL,  -- JSON schema for tool parameters
    script_path TEXT NOT NULL,

    -- Capabilities
    input_patterns TEXT,  -- JSON array
    output_format TEXT,  -- JSON schema

    -- Performance Metrics
    avg_duration_seconds REAL DEFAULT 0.0,
    avg_tokens_consumed INTEGER DEFAULT 0,
    avg_cost_usd REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 1.0,  -- 0.0 to 1.0

    -- Usage
    total_invocations INTEGER DEFAULT 0,
    last_invoked TEXT,

    -- Status
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'deprecated', 'experimental')),

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_adw_tools_name ON adw_tools(tool_name);
CREATE INDEX IF NOT EXISTS idx_adw_tools_status ON adw_tools(status);

-- ============================================================================
-- COST SAVINGS LOG TABLE - Measure actual impact
-- ============================================================================
CREATE TABLE IF NOT EXISTS cost_savings_log (
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
    notes TEXT,

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id),
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(tool_call_id),
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);

CREATE INDEX IF NOT EXISTS idx_cost_savings_type ON cost_savings_log(optimization_type);
CREATE INDEX IF NOT EXISTS idx_cost_savings_workflow ON cost_savings_log(workflow_id);
CREATE INDEX IF NOT EXISTS idx_cost_savings_saved_at ON cost_savings_log(saved_at);

-- ============================================================================
-- VIEWS for easier querying
-- ============================================================================

-- Active patterns with high savings potential
CREATE VIEW IF NOT EXISTS v_high_value_patterns AS
SELECT
    p.*,
    p.potential_monthly_savings * 12 as annual_savings_usd,
    (SELECT COUNT(*) FROM pattern_occurrences po WHERE po.pattern_id = p.id) as total_occurrences
FROM operation_patterns p
WHERE p.automation_status IN ('detected', 'candidate')
AND p.confidence_score >= 70
AND p.potential_monthly_savings >= 0.50
ORDER BY p.potential_monthly_savings DESC;

-- Recent tool performance
CREATE VIEW IF NOT EXISTS v_tool_performance AS
SELECT
    t.tool_name,
    t.total_invocations,
    t.success_rate * 100 as success_rate_percent,
    t.avg_duration_seconds,
    t.avg_cost_usd,
    (SELECT COUNT(*) FROM tool_calls tc WHERE tc.tool_name = t.tool_name AND tc.success = 1) as successful_calls,
    (SELECT COUNT(*) FROM tool_calls tc WHERE tc.tool_name = t.tool_name AND tc.success = 0) as failed_calls,
    (SELECT SUM(cost_saved_usd) FROM tool_calls tc WHERE tc.tool_name = t.tool_name) as total_cost_saved
FROM adw_tools t
WHERE t.status = 'active'
ORDER BY t.total_invocations DESC;

-- Cost savings summary by optimization type
CREATE VIEW IF NOT EXISTS v_cost_savings_summary AS
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

-- Daily hook event summary
CREATE VIEW IF NOT EXISTS v_hook_events_daily AS
SELECT
    DATE(timestamp) as event_date,
    event_type,
    source_app,
    COUNT(*) as event_count,
    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count,
    SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pending_count
FROM hook_events
GROUP BY DATE(timestamp), event_type, source_app
ORDER BY event_date DESC, event_count DESC;

-- ============================================================================
-- TRIGGERS for automated maintenance
-- ============================================================================

-- Update operation_patterns.updated_at on changes
CREATE TRIGGER IF NOT EXISTS trigger_update_pattern_timestamp
AFTER UPDATE ON operation_patterns
FOR EACH ROW
BEGIN
    UPDATE operation_patterns
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Update adw_tools.updated_at on changes
CREATE TRIGGER IF NOT EXISTS trigger_update_tool_timestamp
AFTER UPDATE ON adw_tools
FOR EACH ROW
BEGIN
    UPDATE adw_tools
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Increment tool invocation count when tool_calls record is created
CREATE TRIGGER IF NOT EXISTS trigger_increment_tool_invocations
AFTER INSERT ON tool_calls
FOR EACH ROW
BEGIN
    UPDATE adw_tools
    SET
        total_invocations = total_invocations + 1,
        last_invoked = datetime('now')
    WHERE tool_name = NEW.tool_name;
END;

-- Update tool success rate after tool call completes
CREATE TRIGGER IF NOT EXISTS trigger_update_tool_success_rate
AFTER UPDATE OF success ON tool_calls
FOR EACH ROW
WHEN NEW.success IS NOT NULL
BEGIN
    UPDATE adw_tools
    SET success_rate = (
        SELECT CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)
        FROM tool_calls
        WHERE tool_name = NEW.tool_name
    )
    WHERE tool_name = NEW.tool_name;
END;

-- ============================================================================
-- DATA MIGRATIONS (backfill workflow_id for existing records)
-- ============================================================================

-- Generate workflow_id for existing workflow_history records that don't have one
UPDATE workflow_history
SET workflow_id = 'wf-' || lower(hex(randomblob(16)))
WHERE workflow_id IS NULL;

-- Set workflow_type based on existing data
UPDATE workflow_history
SET workflow_type = CASE
    WHEN workflow_template LIKE '%test%' THEN 'testing'
    WHEN workflow_template LIKE '%build%' THEN 'building'
    WHEN workflow_template LIKE '%plan%' OR workflow_template IS NULL THEN 'planning'
    ELSE 'planning'
END
WHERE workflow_type = 'planning';  -- Only update defaults

-- Generate input_hash for deduplication
UPDATE workflow_history
SET input_hash = lower(hex(randomblob(8)))
WHERE input_hash IS NULL AND nl_input IS NOT NULL;

-- ============================================================================
-- INITIAL SEED DATA
-- ============================================================================

-- Seed ADW tools table with test workflow tool (will be implemented next)
INSERT OR IGNORE INTO adw_tools (tool_name, description, tool_schema, script_path, input_patterns, output_format, status)
VALUES (
    'run_test_workflow',
    'Run the project test suite and return failures only. Dramatically reduces context by not loading test files.',
    '{"type": "object", "properties": {"test_path": {"type": "string"}, "test_type": {"type": "string", "enum": ["pytest", "vitest", "all"]}}}',
    'adws/adw_test_workflow.py',
    '["run tests", "test suite", "pytest", "vitest", "execute tests", "run all tests"]',
    '{"type": "object", "properties": {"summary": {"type": "object"}, "failures": {"type": "array"}, "next_steps": {"type": "array"}}}',
    'experimental'
);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Migration 004 adds comprehensive observability and pattern learning infrastructure
-- This enables the cost optimization intelligence system to:
-- 1. Track all tool calls and measure savings
-- 2. Capture structured events via hooks
-- 3. Automatically discover optimization patterns
-- 4. Measure ROI of optimizations
-- 5. Build a library of specialized ADW tools
