-- Workflow History Schema
-- Stores comprehensive execution data for ADW workflows

CREATE TABLE IF NOT EXISTS workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Workflow identifiers
    adw_id TEXT NOT NULL,
    issue_number INTEGER,
    workflow_template TEXT NOT NULL,

    -- Timing
    start_timestamp TEXT NOT NULL,
    end_timestamp TEXT,
    completion_time_seconds REAL,

    -- Status
    status TEXT NOT NULL CHECK(status IN ('in_progress', 'completed', 'failed')),
    error_message TEXT,

    -- User input
    nl_input TEXT NOT NULL,
    structured_input TEXT, -- JSON

    -- Model and template
    model_used TEXT,

    -- Cost metrics
    estimated_cost_total REAL DEFAULT 0.0,
    actual_cost_total REAL DEFAULT 0.0,

    -- Token metrics
    total_tokens INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_efficiency_percent REAL DEFAULT 0.0,

    -- Performance metrics
    retry_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,

    -- Resource usage
    worktree_id TEXT,
    worktree_reused INTEGER DEFAULT 0, -- Boolean: 0 or 1
    ports_used TEXT, -- JSON: {"frontend": 5173, "backend": 8000}
    concurrent_workflows_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_workflow_history_adw_id ON workflow_history(adw_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_issue_number ON workflow_history(issue_number);
CREATE INDEX IF NOT EXISTS idx_workflow_history_start_timestamp ON workflow_history(start_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_history_workflow_template ON workflow_history(workflow_template);
CREATE INDEX IF NOT EXISTS idx_workflow_history_status ON workflow_history(status);
CREATE INDEX IF NOT EXISTS idx_workflow_history_model_used ON workflow_history(model_used);
CREATE INDEX IF NOT EXISTS idx_workflow_history_created_at ON workflow_history(created_at DESC);

-- Composite index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_workflow_history_status_timestamp ON workflow_history(status, start_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_history_template_timestamp ON workflow_history(workflow_template, start_timestamp DESC);
