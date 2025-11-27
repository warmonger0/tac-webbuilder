-- PostgreSQL Migration Schema for TAC WebBuilder
-- Converted from SQLite schemas (database.db + workflow_history.db)
-- Migration Date: 2025-11-26
-- Target: PostgreSQL 15+

-- Use tac_webbuilder schema (or public if preferred)
-- CREATE SCHEMA IF NOT EXISTS tac_webbuilder;
-- SET search_path TO tac_webbuilder;

-- ============================================================================
-- CORE WORKFLOW TABLES
-- ============================================================================

-- ADW Locks Table
CREATE TABLE adw_locks (
    issue_number INTEGER PRIMARY KEY,
    adw_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK(status IN ('planning', 'building', 'testing', 'reviewing', 'documenting')),
    github_url TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_adw_locks_status ON adw_locks(status);

-- Workflow History Table (Primary Table - 50MB in SQLite)
CREATE TABLE workflow_history (
    id BIGSERIAL PRIMARY KEY,
    adw_id VARCHAR(255) NOT NULL UNIQUE,
    issue_number INTEGER,
    nl_input TEXT,
    github_url TEXT,
    gh_issue_state VARCHAR(50),  -- GitHub issue state: 'open', 'closed', or NULL
    workflow_template VARCHAR(255),
    model_used VARCHAR(255),
    status VARCHAR(50) NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    start_time TIMESTAMP WITHOUT TIME ZONE,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    duration_seconds INTEGER,
    error_message TEXT,
    phase_count INTEGER,
    current_phase VARCHAR(255),
    success_rate DOUBLE PRECISION,
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
    cache_efficiency_percent DOUBLE PRECISION DEFAULT 0.0,

    -- Cost tracking fields (use NUMERIC for money)
    estimated_cost_total NUMERIC(10, 4) DEFAULT 0.0,
    actual_cost_total NUMERIC(10, 4) DEFAULT 0.0,
    estimated_cost_per_step NUMERIC(10, 4) DEFAULT 0.0,
    actual_cost_per_step NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_token NUMERIC(10, 6) DEFAULT 0.0,

    -- Structured data fields (JSON)
    structured_input JSONB,  -- PostgreSQL JSONB for better performance
    cost_breakdown JSONB,
    token_breakdown JSONB,

    -- Resource usage
    worktree_reused BOOLEAN DEFAULT FALSE,
    steps_completed INTEGER DEFAULT 0,
    steps_total INTEGER DEFAULT 0,

    -- Phase 3A: Analytics fields (temporal and scoring)
    hour_of_day INTEGER DEFAULT -1,
    day_of_week INTEGER DEFAULT -1,
    nl_input_clarity_score DOUBLE PRECISION DEFAULT 0.0,
    cost_efficiency_score DOUBLE PRECISION DEFAULT 0.0,
    performance_score DOUBLE PRECISION DEFAULT 0.0,
    quality_score DOUBLE PRECISION DEFAULT 0.0,

    -- Phase 3B: Scoring version tracking
    scoring_version VARCHAR(50) DEFAULT '1.0',

    -- Phase 3D: Insights & Recommendations
    anomaly_flags JSONB,  -- JSON array of anomaly objects
    optimization_recommendations JSONB,  -- JSON array of recommendation strings

    -- Additional fields from workflow_history.db
    workflow_id VARCHAR(255),
    workflow_type VARCHAR(100) DEFAULT 'planning',
    parent_workflow_id VARCHAR(255),
    input_hash VARCHAR(255),
    output_summary TEXT,
    nl_input_word_count INTEGER,
    structured_input_completeness_percent DOUBLE PRECISION,
    submission_hour INTEGER,
    submission_day_of_week INTEGER,
    pr_merged BOOLEAN DEFAULT FALSE,
    time_to_merge_hours DOUBLE PRECISION,
    review_cycles INTEGER,
    ci_test_pass_rate DOUBLE PRECISION,
    similar_workflow_ids JSONB,
    idle_time_seconds INTEGER,
    bottleneck_phase VARCHAR(255),
    error_category VARCHAR(255),
    retry_reasons JSONB,
    error_phase_distribution JSONB,
    recovery_time_seconds INTEGER,
    complexity_estimated VARCHAR(100),
    complexity_actual VARCHAR(100),
    phase_number INTEGER,
    is_multi_phase BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Workflow History Indexes (41 total in SQLite)
CREATE INDEX idx_workflow_history_adw_id ON workflow_history(adw_id);
CREATE INDEX idx_workflow_history_status ON workflow_history(status);
CREATE INDEX idx_workflow_history_created_at ON workflow_history(created_at DESC);
CREATE INDEX idx_workflow_history_issue_number ON workflow_history(issue_number);
CREATE INDEX idx_workflow_history_model_used ON workflow_history(model_used);
CREATE INDEX idx_workflow_history_workflow_template ON workflow_history(workflow_template);
CREATE INDEX idx_workflow_history_workflow_id ON workflow_history(workflow_id);
CREATE INDEX idx_workflow_history_workflow_type ON workflow_history(workflow_type);
CREATE INDEX idx_workflow_history_parent_id ON workflow_history(parent_workflow_id);
CREATE INDEX idx_workflow_history_input_hash ON workflow_history(input_hash);
CREATE INDEX idx_workflow_history_submission_hour ON workflow_history(submission_hour);
CREATE INDEX idx_workflow_history_pr_merged ON workflow_history(pr_merged);
CREATE INDEX idx_workflow_history_cost_efficiency_score ON workflow_history(cost_efficiency_score);
CREATE INDEX idx_workflow_history_performance_score ON workflow_history(performance_score);
CREATE INDEX idx_workflow_history_quality_score ON workflow_history(quality_score);
CREATE INDEX idx_workflow_history_day_of_week ON workflow_history(day_of_week);

-- Phase Queue Table (Multi-phase workflow support)
CREATE TABLE phase_queue (
    queue_id VARCHAR(255) PRIMARY KEY,
    parent_issue INTEGER NOT NULL,
    phase_number INTEGER NOT NULL,
    issue_number INTEGER,  -- NULL until GitHub issue created
    status VARCHAR(50) CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
    depends_on_phase INTEGER,  -- Phase number that must complete first (NULL for Phase 1)
    phase_data JSONB,  -- JSON: {title, content, externalDocs}
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    adw_id VARCHAR(255),
    pr_number INTEGER,
    priority INTEGER DEFAULT 50,
    queue_position INTEGER,
    ready_timestamp TIMESTAMP WITHOUT TIME ZONE,
    started_timestamp TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_issue ON phase_queue(issue_number);
CREATE INDEX idx_phase_queue_priority ON phase_queue(priority, queue_position);

-- Queue Configuration
CREATE TABLE queue_config (
    config_key VARCHAR(255) PRIMARY KEY,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COST OPTIMIZATION & PATTERN LEARNING TABLES
-- ============================================================================

-- Tool Calls Tracking
CREATE TABLE tool_calls (
    id BIGSERIAL PRIMARY KEY,
    tool_call_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,

    -- Tool Details
    tool_name VARCHAR(255) NOT NULL,
    tool_params JSONB,  -- JSON

    -- Timing
    called_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    duration_seconds DOUBLE PRECISION,

    -- Results
    success BOOLEAN DEFAULT FALSE,
    result_data JSONB,  -- JSON
    error_message TEXT,

    -- Cost Impact
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd NUMERIC(10, 4) DEFAULT 0.0,

    -- Captured via hooks
    pre_tool_snapshot JSONB,  -- JSON from PreToolUse hook
    post_tool_snapshot JSONB,  -- JSON from PostToolUse hook

    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id) ON DELETE CASCADE
);

CREATE INDEX idx_tool_calls_workflow ON tool_calls(workflow_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
CREATE INDEX idx_tool_calls_called_at ON tool_calls(called_at);
CREATE INDEX idx_tool_calls_success ON tool_calls(success);

-- Operation Patterns (Pattern Learning)
CREATE TABLE operation_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_signature VARCHAR(255) UNIQUE NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,

    -- Detection
    first_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    occurrence_count INTEGER DEFAULT 1,

    -- Characteristics (learned from actual executions)
    typical_input_pattern TEXT,  -- Common input characteristics
    typical_operations JSONB,  -- JSON array of operations
    typical_files_accessed JSONB,  -- JSON array of file patterns

    -- Cost Analysis
    avg_tokens_with_llm INTEGER DEFAULT 0,
    avg_cost_with_llm NUMERIC(10, 4) DEFAULT 0.0,
    avg_tokens_with_tool INTEGER DEFAULT 0,
    avg_cost_with_tool NUMERIC(10, 4) DEFAULT 0.0,
    potential_monthly_savings NUMERIC(10, 4) DEFAULT 0.0,

    -- Automation Status
    automation_status VARCHAR(50) DEFAULT 'detected' CHECK(
        automation_status IN ('detected', 'candidate', 'approved', 'implemented', 'active', 'deprecated')
    ),
    confidence_score DOUBLE PRECISION DEFAULT 0.0,
    tool_name VARCHAR(255),
    tool_script_path TEXT,

    -- Human Review
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE,
    review_notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_operation_patterns_type ON operation_patterns(pattern_type);
CREATE INDEX idx_operation_patterns_status ON operation_patterns(automation_status);
CREATE INDEX idx_operation_patterns_confidence ON operation_patterns(confidence_score);
CREATE INDEX idx_operation_patterns_occurrence ON operation_patterns(occurrence_count);

-- Pattern Occurrences
CREATE TABLE pattern_occurrences (
    id BIGSERIAL PRIMARY KEY,
    pattern_id BIGINT NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,

    -- Similarity Metrics
    similarity_score DOUBLE PRECISION DEFAULT 0.0,
    matched_characteristics JSONB,  -- JSON

    detected_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id) ON DELETE CASCADE
);

CREATE INDEX idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX idx_pattern_occurrences_workflow ON pattern_occurrences(workflow_id);
CREATE INDEX idx_pattern_occurrences_detected ON pattern_occurrences(detected_at);

-- Hook Events
CREATE TABLE hook_events (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,

    -- Event Classification
    event_type VARCHAR(100) NOT NULL CHECK(
        event_type IN ('PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop',
                       'SubagentStop', 'PreCompact', 'SessionStart', 'SessionEnd', 'Notification')
    ),
    source_app VARCHAR(255),  -- 'main_adw', 'test_adw', 'build_adw', etc.
    session_id VARCHAR(255),
    workflow_id VARCHAR(255),

    -- Event Data
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    payload JSONB NOT NULL,  -- JSON

    -- Context
    tool_name VARCHAR(255),
    chat_history JSONB,  -- JSON, optional

    -- Processing
    processed BOOLEAN DEFAULT FALSE,  -- For pattern learning queue
    processed_at TIMESTAMP WITHOUT TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id) ON DELETE SET NULL
);

CREATE INDEX idx_hook_events_type ON hook_events(event_type);
CREATE INDEX idx_hook_events_session ON hook_events(session_id);
CREATE INDEX idx_hook_events_workflow ON hook_events(workflow_id);
CREATE INDEX idx_hook_events_processed ON hook_events(processed);
CREATE INDEX idx_hook_events_timestamp ON hook_events(timestamp);
CREATE INDEX idx_hook_events_source_app ON hook_events(source_app);

-- ADW Tools Registry
CREATE TABLE adw_tools (
    id BIGSERIAL PRIMARY KEY,
    tool_name VARCHAR(255) UNIQUE NOT NULL,

    -- Tool Definition
    description TEXT NOT NULL,
    tool_schema JSONB NOT NULL,  -- JSON schema for tool parameters
    script_path TEXT NOT NULL,

    -- Capabilities
    input_patterns JSONB,  -- JSON array
    output_format JSONB,  -- JSON schema

    -- Performance Metrics
    avg_duration_seconds DOUBLE PRECISION DEFAULT 0.0,
    avg_tokens_consumed INTEGER DEFAULT 0,
    avg_cost_usd NUMERIC(10, 4) DEFAULT 0.0,
    success_rate DOUBLE PRECISION DEFAULT 1.0,  -- 0.0 to 1.0

    -- Usage
    total_invocations INTEGER DEFAULT 0,
    last_invoked TIMESTAMP WITHOUT TIME ZONE,

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK(status IN ('active', 'deprecated', 'experimental')),

    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_adw_tools_name ON adw_tools(tool_name);
CREATE INDEX idx_adw_tools_status ON adw_tools(status);

-- Cost Savings Log
CREATE TABLE cost_savings_log (
    id BIGSERIAL PRIMARY KEY,

    -- What saved cost
    optimization_type VARCHAR(100) NOT NULL CHECK(
        optimization_type IN ('tool_call', 'input_split', 'pattern_offload', 'inverted_flow')
    ),
    workflow_id VARCHAR(255) NOT NULL,
    tool_call_id VARCHAR(255),
    pattern_id BIGINT,

    -- Savings
    baseline_tokens INTEGER DEFAULT 0,
    actual_tokens INTEGER DEFAULT 0,
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd NUMERIC(10, 4) DEFAULT 0.0,

    -- Context
    saved_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    notes TEXT,

    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id) ON DELETE CASCADE,
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(tool_call_id) ON DELETE SET NULL,
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id) ON DELETE SET NULL
);

CREATE INDEX idx_cost_savings_type ON cost_savings_log(optimization_type);
CREATE INDEX idx_cost_savings_workflow ON cost_savings_log(workflow_id);
CREATE INDEX idx_cost_savings_saved_at ON cost_savings_log(saved_at);

-- ============================================================================
-- SCHEMA MIGRATIONS TABLE
-- ============================================================================

CREATE TABLE schema_migrations (
    id BIGSERIAL PRIMARY KEY,
    migration_file VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(255)
);

-- ============================================================================
-- WORKFLOW HISTORY ARCHIVE
-- ============================================================================

CREATE TABLE workflow_history_archive (
    id BIGSERIAL PRIMARY KEY,
    original_id BIGINT NOT NULL,
    adw_id VARCHAR(255) NOT NULL,
    issue_number INTEGER,
    nl_input TEXT,
    github_url TEXT,
    workflow_template VARCHAR(255),
    model_used VARCHAR(255),
    status VARCHAR(50) NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    start_time TIMESTAMP WITHOUT TIME ZONE,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    duration_seconds INTEGER,
    error_message TEXT,
    phase_count INTEGER,
    current_phase VARCHAR(255),
    success_rate DOUBLE PRECISION,
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
    cache_efficiency_percent DOUBLE PRECISION DEFAULT 0.0,
    estimated_cost_total NUMERIC(10, 4) DEFAULT 0.0,
    actual_cost_total NUMERIC(10, 4) DEFAULT 0.0,
    estimated_cost_per_step NUMERIC(10, 4) DEFAULT 0.0,
    actual_cost_per_step NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_token NUMERIC(10, 6) DEFAULT 0.0,
    structured_input JSONB,
    cost_breakdown JSONB,
    token_breakdown JSONB,
    worktree_reused BOOLEAN DEFAULT FALSE,
    steps_completed INTEGER DEFAULT 0,
    steps_total INTEGER DEFAULT 0,
    hour_of_day INTEGER DEFAULT -1,
    day_of_week INTEGER DEFAULT -1,
    nl_input_clarity_score DOUBLE PRECISION DEFAULT 0.0,
    cost_efficiency_score DOUBLE PRECISION DEFAULT 0.0,
    performance_score DOUBLE PRECISION DEFAULT 0.0,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    scoring_version VARCHAR(50) DEFAULT '1.0',
    anomaly_flags JSONB,
    optimization_recommendations JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);

CREATE INDEX idx_archive_issue_number ON workflow_history_archive(issue_number);
CREATE INDEX idx_archive_adw_id ON workflow_history_archive(adw_id);
CREATE INDEX idx_archive_archived_at ON workflow_history_archive(archived_at DESC);

-- ============================================================================
-- TEST/DEMO TABLES (from SQLite - keep for compatibility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employees (
    department TEXT,
    employee TEXT,
    salary INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    age INTEGER,
    city TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product TEXT,
    price DOUBLE PRECISION,
    stock INTEGER
);

CREATE TABLE IF NOT EXISTS staff (
    department TEXT,
    employee TEXT,
    salary INTEGER
);

CREATE TABLE IF NOT EXISTS empty (
    name TEXT,
    age TEXT,
    city TEXT
);

CREATE TABLE IF NOT EXISTS large (
    name TEXT,
    age INTEGER,
    city TEXT
);

CREATE TABLE IF NOT EXISTS special (
    name TEXT,
    description TEXT,
    price DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS people (
    name TEXT,
    age INTEGER,
    city TEXT
);

CREATE TABLE IF NOT EXISTS file1 (
    id INTEGER,
    value TEXT
);

CREATE TABLE IF NOT EXISTS file4 (
    id INTEGER,
    value TEXT
);

CREATE TABLE IF NOT EXISTS file0 (
    id INTEGER,
    value TEXT
);

CREATE TABLE IF NOT EXISTS file3 (
    id INTEGER,
    value TEXT
);

CREATE TABLE IF NOT EXISTS file2 (
    id INTEGER,
    value TEXT
);

CREATE TABLE IF NOT EXISTS wide (
    col0 INTEGER, col1 INTEGER, col2 INTEGER, col3 INTEGER, col4 INTEGER,
    col5 INTEGER, col6 INTEGER, col7 INTEGER, col8 INTEGER, col9 INTEGER,
    col10 INTEGER, col11 INTEGER, col12 INTEGER, col13 INTEGER, col14 INTEGER,
    col15 INTEGER, col16 INTEGER, col17 INTEGER, col18 INTEGER, col19 INTEGER,
    col20 INTEGER, col21 INTEGER, col22 INTEGER, col23 INTEGER, col24 INTEGER,
    col25 INTEGER, col26 INTEGER, col27 INTEGER, col28 INTEGER, col29 INTEGER,
    col30 INTEGER, col31 INTEGER, col32 INTEGER, col33 INTEGER, col34 INTEGER,
    col35 INTEGER, col36 INTEGER, col37 INTEGER, col38 INTEGER, col39 INTEGER,
    col40 INTEGER, col41 INTEGER, col42 INTEGER, col43 INTEGER, col44 INTEGER,
    col45 INTEGER, col46 INTEGER, col47 INTEGER, col48 INTEGER, col49 INTEGER,
    col50 INTEGER, col51 INTEGER, col52 INTEGER, col53 INTEGER, col54 INTEGER,
    col55 INTEGER, col56 INTEGER, col57 INTEGER, col58 INTEGER, col59 INTEGER,
    col60 INTEGER, col61 INTEGER, col62 INTEGER, col63 INTEGER, col64 INTEGER,
    col65 INTEGER, col66 INTEGER, col67 INTEGER, col68 INTEGER, col69 INTEGER,
    col70 INTEGER, col71 INTEGER, col72 INTEGER, col73 INTEGER, col74 INTEGER,
    col75 INTEGER, col76 INTEGER, col77 INTEGER, col78 INTEGER, col79 INTEGER,
    col80 INTEGER, col81 INTEGER, col82 INTEGER, col83 INTEGER, col84 INTEGER,
    col85 INTEGER, col86 INTEGER, col87 INTEGER, col88 INTEGER, col89 INTEGER,
    col90 INTEGER, col91 INTEGER, col92 INTEGER, col93 INTEGER, col94 INTEGER,
    col95 INTEGER, col96 INTEGER, col97 INTEGER, col98 INTEGER, col99 INTEGER
);

CREATE TABLE IF NOT EXISTS data (
    name TEXT,
    age INTEGER,
    city TEXT
);

-- ============================================================================
-- VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW v_high_value_patterns AS
SELECT
    p.*,
    p.potential_monthly_savings * 12 as annual_savings_usd,
    (SELECT COUNT(*) FROM pattern_occurrences po WHERE po.pattern_id = p.id) as total_occurrences
FROM operation_patterns p
WHERE p.automation_status IN ('detected', 'candidate')
AND p.confidence_score >= 70
AND p.potential_monthly_savings >= 0.50
ORDER BY p.potential_monthly_savings DESC;

CREATE OR REPLACE VIEW v_tool_performance AS
SELECT
    t.tool_name,
    t.total_invocations,
    t.success_rate * 100 as success_rate_percent,
    t.avg_duration_seconds,
    t.avg_cost_usd,
    (SELECT COUNT(*) FROM tool_calls tc WHERE tc.tool_name = t.tool_name AND tc.success = TRUE) as successful_calls,
    (SELECT COUNT(*) FROM tool_calls tc WHERE tc.tool_name = t.tool_name AND tc.success = FALSE) as failed_calls,
    (SELECT SUM(cost_saved_usd) FROM tool_calls tc WHERE tc.tool_name = t.tool_name) as total_cost_saved
FROM adw_tools t
WHERE t.status = 'active'
ORDER BY t.total_invocations DESC;

CREATE OR REPLACE VIEW v_cost_savings_summary AS
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

CREATE OR REPLACE VIEW v_hook_events_daily AS
SELECT
    DATE(timestamp) as event_date,
    event_type,
    source_app,
    COUNT(*) as event_count,
    SUM(CASE WHEN processed = TRUE THEN 1 ELSE 0 END) as processed_count,
    SUM(CASE WHEN processed = FALSE THEN 1 ELSE 0 END) as pending_count
FROM hook_events
GROUP BY DATE(timestamp), event_type, source_app
ORDER BY event_date DESC, event_count DESC;

-- ============================================================================
-- TRIGGERS (PostgreSQL uses functions + triggers)
-- ============================================================================

-- Trigger function to update operation_patterns timestamp
CREATE OR REPLACE FUNCTION trigger_update_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pattern_timestamp
BEFORE UPDATE ON operation_patterns
FOR EACH ROW
EXECUTE FUNCTION trigger_update_pattern_timestamp();

-- Trigger function to update adw_tools timestamp
CREATE OR REPLACE FUNCTION trigger_update_tool_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tool_timestamp
BEFORE UPDATE ON adw_tools
FOR EACH ROW
EXECUTE FUNCTION trigger_update_tool_timestamp();

-- Trigger function to increment tool invocations
CREATE OR REPLACE FUNCTION trigger_increment_tool_invocations()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE adw_tools
    SET
        total_invocations = total_invocations + 1,
        last_invoked = NOW()
    WHERE tool_name = NEW.tool_name;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_tool_invocations
AFTER INSERT ON tool_calls
FOR EACH ROW
EXECUTE FUNCTION trigger_increment_tool_invocations();

-- Trigger function to update tool success rate
CREATE OR REPLACE FUNCTION trigger_update_tool_success_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.success IS NOT NULL THEN
        UPDATE adw_tools
        SET success_rate = (
            SELECT CAST(SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) AS DOUBLE PRECISION) / COUNT(*)
            FROM tool_calls
            WHERE tool_name = NEW.tool_name
        )
        WHERE tool_name = NEW.tool_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tool_success_rate
AFTER UPDATE OF success ON tool_calls
FOR EACH ROW
EXECUTE FUNCTION trigger_update_tool_success_rate();

-- ============================================================================
-- POSTGRESQL-SPECIFIC OPTIMIZATIONS
-- ============================================================================

-- Enable auto-vacuum for large tables
ALTER TABLE workflow_history SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE tool_calls SET (autovacuum_vacuum_scale_factor = 0.02);
ALTER TABLE hook_events SET (autovacuum_vacuum_scale_factor = 0.02);

-- Add table comments for documentation
COMMENT ON TABLE workflow_history IS 'Primary workflow execution history table (50MB in SQLite)';
COMMENT ON TABLE phase_queue IS 'Multi-phase workflow queue management';
COMMENT ON TABLE tool_calls IS 'Tool invocation tracking for cost optimization';
COMMENT ON TABLE operation_patterns IS 'Learned patterns for automation opportunities';
COMMENT ON COLUMN workflow_history.structured_input IS 'JSONB for fast querying';
COMMENT ON COLUMN workflow_history.cost_breakdown IS 'JSONB cost analytics data';

-- Grant permissions (adjust as needed for your deployment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO tac_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tac_user;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Insert migration record
INSERT INTO schema_migrations (migration_file, checksum)
VALUES ('initial_postgres_migration.sql', MD5('postgres_schema_v1'));
