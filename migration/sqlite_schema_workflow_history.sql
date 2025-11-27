CREATE TABLE workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adw_id TEXT NOT NULL UNIQUE,
                issue_number INTEGER,
                nl_input TEXT,
                github_url TEXT,
                workflow_template TEXT,
                model_used TEXT,
                status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                error_message TEXT,
                phase_count INTEGER,
                current_phase TEXT,
                success_rate REAL,
                retry_count INTEGER DEFAULT 0,
                worktree_path TEXT,
                backend_port INTEGER,
                frontend_port INTEGER,
                concurrent_workflows INTEGER DEFAULT 0,

                -- Token usage fields
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cached_tokens INTEGER DEFAULT 0,
                cache_hit_tokens INTEGER DEFAULT 0,
                cache_miss_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cache_efficiency_percent REAL DEFAULT 0.0,

                -- Cost tracking fields
                estimated_cost_total REAL DEFAULT 0.0,
                actual_cost_total REAL DEFAULT 0.0,
                estimated_cost_per_step REAL DEFAULT 0.0,
                actual_cost_per_step REAL DEFAULT 0.0,
                cost_per_token REAL DEFAULT 0.0,

                -- Structured data fields (JSON)
                structured_input TEXT,  -- JSON object
                cost_breakdown TEXT,    -- JSON object
                token_breakdown TEXT,   -- JSON object

                -- Resource usage
                worktree_reused INTEGER DEFAULT 0,  -- Boolean (0 or 1)
                steps_completed INTEGER DEFAULT 0,
                steps_total INTEGER DEFAULT 0,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            , nl_input_word_count INTEGER, nl_input_clarity_score REAL, structured_input_completeness_percent REAL, submission_hour INTEGER, submission_day_of_week INTEGER, pr_merged INTEGER DEFAULT 0, time_to_merge_hours REAL, review_cycles INTEGER, ci_test_pass_rate REAL, cost_efficiency_score REAL, performance_score REAL, quality_score REAL, similar_workflow_ids TEXT, anomaly_flags TEXT, optimization_recommendations TEXT, idle_time_seconds INTEGER, bottleneck_phase TEXT, error_category TEXT, retry_reasons TEXT, error_phase_distribution TEXT, recovery_time_seconds INTEGER, complexity_estimated TEXT, complexity_actual TEXT, workflow_type TEXT DEFAULT 'planning', parent_workflow_id TEXT, input_hash TEXT, output_summary TEXT, workflow_id TEXT, gh_issue_state TEXT, scoring_version TEXT DEFAULT '1.0', phase_number INTEGER, is_multi_phase BOOLEAN DEFAULT 0, day_of_week INTEGER);
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_adw_id ON workflow_history(adw_id)
        ;
CREATE INDEX idx_status ON workflow_history(status)
        ;
CREATE INDEX idx_created_at ON workflow_history(created_at DESC)
        ;
CREATE INDEX idx_issue_number ON workflow_history(issue_number)
        ;
CREATE INDEX idx_model_used ON workflow_history(model_used)
        ;
CREATE INDEX idx_workflow_template ON workflow_history(workflow_template)
        ;
CREATE INDEX idx_submission_hour ON workflow_history(submission_hour);
CREATE INDEX idx_pr_merged ON workflow_history(pr_merged);
CREATE INDEX idx_cost_efficiency_score ON workflow_history(cost_efficiency_score);
CREATE INDEX idx_performance_score ON workflow_history(performance_score);
CREATE INDEX idx_quality_score ON workflow_history(quality_score);
CREATE TABLE schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_file TEXT UNIQUE NOT NULL,
            applied_at TEXT DEFAULT (datetime('now')),
            checksum TEXT
        );
CREATE INDEX idx_workflow_history_workflow_type ON workflow_history(workflow_type);
CREATE INDEX idx_workflow_history_parent_id ON workflow_history(parent_workflow_id);
CREATE INDEX idx_workflow_history_input_hash ON workflow_history(input_hash);
CREATE INDEX idx_workflow_history_workflow_id ON workflow_history(workflow_id);
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
CREATE INDEX idx_tool_calls_workflow ON tool_calls(workflow_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
CREATE INDEX idx_tool_calls_called_at ON tool_calls(called_at);
CREATE INDEX idx_tool_calls_success ON tool_calls(success);
CREATE TABLE operation_patterns (
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
CREATE INDEX idx_operation_patterns_type ON operation_patterns(pattern_type);
CREATE INDEX idx_operation_patterns_status ON operation_patterns(automation_status);
CREATE INDEX idx_operation_patterns_confidence ON operation_patterns(confidence_score);
CREATE INDEX idx_operation_patterns_occurrence ON operation_patterns(occurrence_count);
CREATE TABLE pattern_occurrences (
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
CREATE INDEX idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX idx_pattern_occurrences_workflow ON pattern_occurrences(workflow_id);
CREATE INDEX idx_pattern_occurrences_detected ON pattern_occurrences(detected_at);
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

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id)
);
CREATE INDEX idx_hook_events_type ON hook_events(event_type);
CREATE INDEX idx_hook_events_session ON hook_events(session_id);
CREATE INDEX idx_hook_events_workflow ON hook_events(workflow_id);
CREATE INDEX idx_hook_events_processed ON hook_events(processed);
CREATE INDEX idx_hook_events_timestamp ON hook_events(timestamp);
CREATE INDEX idx_hook_events_source_app ON hook_events(source_app);
CREATE TABLE adw_tools (
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
CREATE INDEX idx_adw_tools_name ON adw_tools(tool_name);
CREATE INDEX idx_adw_tools_status ON adw_tools(status);
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
    notes TEXT,

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id),
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(tool_call_id),
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);
CREATE INDEX idx_cost_savings_type ON cost_savings_log(optimization_type);
CREATE INDEX idx_cost_savings_workflow ON cost_savings_log(workflow_id);
CREATE INDEX idx_cost_savings_saved_at ON cost_savings_log(saved_at);
CREATE VIEW v_high_value_patterns AS
SELECT
    p.*,
    p.potential_monthly_savings * 12 as annual_savings_usd,
    (SELECT COUNT(*) FROM pattern_occurrences po WHERE po.pattern_id = p.id) as total_occurrences
FROM operation_patterns p
WHERE p.automation_status IN ('detected', 'candidate')
AND p.confidence_score >= 70
AND p.potential_monthly_savings >= 0.50
ORDER BY p.potential_monthly_savings DESC
/* v_high_value_patterns(id,pattern_signature,pattern_type,first_detected,last_seen,occurrence_count,typical_input_pattern,typical_operations,typical_files_accessed,avg_tokens_with_llm,avg_cost_with_llm,avg_tokens_with_tool,avg_cost_with_tool,potential_monthly_savings,automation_status,confidence_score,tool_name,tool_script_path,reviewed_by,reviewed_at,review_notes,created_at,updated_at,annual_savings_usd,total_occurrences) */;
CREATE VIEW v_tool_performance AS
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
ORDER BY t.total_invocations DESC
/* v_tool_performance(tool_name,total_invocations,success_rate_percent,avg_duration_seconds,avg_cost_usd,successful_calls,failed_calls,total_cost_saved) */;
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
ORDER BY total_cost_saved_usd DESC
/* v_cost_savings_summary(optimization_type,optimization_count,total_tokens_saved,total_cost_saved_usd,avg_cost_saved_per_use,first_saving,latest_saving) */;
CREATE VIEW v_hook_events_daily AS
SELECT
    DATE(timestamp) as event_date,
    event_type,
    source_app,
    COUNT(*) as event_count,
    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count,
    SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pending_count
FROM hook_events
GROUP BY DATE(timestamp), event_type, source_app
ORDER BY event_date DESC, event_count DESC
/* v_hook_events_daily(event_date,event_type,source_app,event_count,processed_count,pending_count) */;
CREATE TRIGGER trigger_update_pattern_timestamp
AFTER UPDATE ON operation_patterns
FOR EACH ROW
BEGIN
    UPDATE operation_patterns
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;
CREATE TRIGGER trigger_update_tool_timestamp
AFTER UPDATE ON adw_tools
FOR EACH ROW
BEGIN
    UPDATE adw_tools
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;
CREATE TRIGGER trigger_increment_tool_invocations
AFTER INSERT ON tool_calls
FOR EACH ROW
BEGIN
    UPDATE adw_tools
    SET
        total_invocations = total_invocations + 1,
        last_invoked = datetime('now')
    WHERE tool_name = NEW.tool_name;
END;
CREATE TRIGGER trigger_update_tool_success_rate
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
CREATE TABLE workflow_history_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_id INTEGER NOT NULL,
    adw_id TEXT NOT NULL,
    issue_number INTEGER,
    nl_input TEXT,
    github_url TEXT,
    workflow_template TEXT,
    model_used TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    start_time TEXT,
    end_time TEXT,
    duration_seconds INTEGER,
    error_message TEXT,
    phase_count INTEGER,
    current_phase TEXT,
    success_rate REAL,
    retry_count INTEGER DEFAULT 0,
    worktree_path TEXT,
    backend_port INTEGER,
    frontend_port INTEGER,
    concurrent_workflows INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cached_tokens INTEGER DEFAULT 0,
    cache_hit_tokens INTEGER DEFAULT 0,
    cache_miss_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cache_efficiency_percent REAL DEFAULT 0.0,
    estimated_cost_total REAL DEFAULT 0.0,
    actual_cost_total REAL DEFAULT 0.0,
    estimated_cost_per_step REAL DEFAULT 0.0,
    actual_cost_per_step REAL DEFAULT 0.0,
    cost_per_token REAL DEFAULT 0.0,
    structured_input TEXT,
    cost_breakdown TEXT,
    token_breakdown TEXT,
    worktree_reused INTEGER DEFAULT 0,
    steps_completed INTEGER DEFAULT 0,
    steps_total INTEGER DEFAULT 0,
    hour_of_day INTEGER DEFAULT -1,
    day_of_week INTEGER DEFAULT -1,
    nl_input_clarity_score REAL DEFAULT 0.0,
    cost_efficiency_score REAL DEFAULT 0.0,
    performance_score REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    scoring_version TEXT DEFAULT '1.0',
    anomaly_flags TEXT,
    optimization_recommendations TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);
CREATE INDEX idx_archive_issue_number ON workflow_history_archive(issue_number);
CREATE INDEX idx_archive_adw_id ON workflow_history_archive(adw_id);
CREATE INDEX idx_archive_archived_at ON workflow_history_archive(archived_at DESC);
CREATE INDEX idx_day_of_week ON workflow_history(day_of_week);
CREATE INDEX idx_workflow_type ON workflow_history(workflow_type);
