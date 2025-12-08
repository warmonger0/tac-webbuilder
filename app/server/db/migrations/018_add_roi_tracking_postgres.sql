-- Migration 018: Add ROI Tracking Tables
-- Purpose: Track pattern execution metrics and ROI for closed-loop automation validation
-- Related: Session 12 - Closed-Loop ROI Tracking System

-- =============================================================================
-- Table: pattern_executions
-- Purpose: Track individual pattern execution instances with actual vs estimated metrics
-- =============================================================================

CREATE TABLE IF NOT EXISTS pattern_executions (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    workflow_id INTEGER,
    execution_time_seconds REAL NOT NULL,
    estimated_time_seconds REAL NOT NULL,
    actual_cost REAL NOT NULL,
    estimated_cost REAL NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_pattern_executions_pattern
        FOREIGN KEY (pattern_id)
        REFERENCES pattern_approvals(pattern_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_pattern_executions_workflow
        FOREIGN KEY (workflow_id)
        REFERENCES workflow_history(id)
        ON DELETE SET NULL
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_pattern_executions_pattern
    ON pattern_executions(pattern_id);

CREATE INDEX IF NOT EXISTS idx_pattern_executions_workflow
    ON pattern_executions(workflow_id);

CREATE INDEX IF NOT EXISTS idx_pattern_executions_date
    ON pattern_executions(executed_at);

CREATE INDEX IF NOT EXISTS idx_pattern_executions_success
    ON pattern_executions(success);

-- =============================================================================
-- Table: pattern_roi_summary
-- Purpose: Aggregated ROI metrics per pattern for quick access
-- =============================================================================

CREATE TABLE IF NOT EXISTS pattern_roi_summary (
    pattern_id TEXT PRIMARY KEY,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    total_time_saved_seconds REAL DEFAULT 0.0,
    total_cost_saved_usd REAL DEFAULT 0.0,
    average_time_saved_seconds REAL DEFAULT 0.0,
    average_cost_saved_usd REAL DEFAULT 0.0,
    roi_percentage REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_pattern_roi_pattern
        FOREIGN KEY (pattern_id)
        REFERENCES pattern_approvals(pattern_id)
        ON DELETE CASCADE,

    -- Validation constraints
    CONSTRAINT chk_total_executions_positive
        CHECK (total_executions >= 0),

    CONSTRAINT chk_successful_executions_valid
        CHECK (successful_executions >= 0 AND successful_executions <= total_executions),

    CONSTRAINT chk_success_rate_valid
        CHECK (success_rate >= 0.0 AND success_rate <= 1.0)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_pattern_roi_success_rate
    ON pattern_roi_summary(success_rate);

CREATE INDEX IF NOT EXISTS idx_pattern_roi_savings
    ON pattern_roi_summary(total_cost_saved_usd);

CREATE INDEX IF NOT EXISTS idx_pattern_roi_percentage
    ON pattern_roi_summary(roi_percentage);

CREATE INDEX IF NOT EXISTS idx_pattern_roi_last_updated
    ON pattern_roi_summary(last_updated);

-- =============================================================================
-- Triggers: Auto-update last_updated timestamp
-- =============================================================================

-- Trigger function to update last_updated
CREATE OR REPLACE FUNCTION update_pattern_roi_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to pattern_roi_summary
DROP TRIGGER IF EXISTS trigger_update_pattern_roi_timestamp ON pattern_roi_summary;
CREATE TRIGGER trigger_update_pattern_roi_timestamp
    BEFORE UPDATE ON pattern_roi_summary
    FOR EACH ROW
    EXECUTE FUNCTION update_pattern_roi_timestamp();

-- =============================================================================
-- Comments for documentation
-- =============================================================================

COMMENT ON TABLE pattern_executions IS
'Tracks individual pattern execution instances with actual vs estimated metrics for ROI calculation';

COMMENT ON COLUMN pattern_executions.pattern_id IS
'Reference to the pattern being executed';

COMMENT ON COLUMN pattern_executions.workflow_id IS
'Optional reference to the workflow where pattern was executed';

COMMENT ON COLUMN pattern_executions.execution_time_seconds IS
'Actual execution time in seconds';

COMMENT ON COLUMN pattern_executions.estimated_time_seconds IS
'Estimated execution time in seconds from pattern approval';

COMMENT ON COLUMN pattern_executions.actual_cost IS
'Actual cost in USD based on execution time and API usage';

COMMENT ON COLUMN pattern_executions.estimated_cost IS
'Estimated cost in USD from pattern approval';

COMMENT ON COLUMN pattern_executions.success IS
'Whether the execution completed successfully';

COMMENT ON COLUMN pattern_executions.error_message IS
'Error details if execution failed';

COMMENT ON TABLE pattern_roi_summary IS
'Aggregated ROI metrics per pattern for performance tracking and confidence updates';

COMMENT ON COLUMN pattern_roi_summary.success_rate IS
'Percentage of successful executions (0.0 to 1.0)';

COMMENT ON COLUMN pattern_roi_summary.total_time_saved_seconds IS
'Cumulative time saved across all successful executions';

COMMENT ON COLUMN pattern_roi_summary.total_cost_saved_usd IS
'Cumulative cost saved across all successful executions';

COMMENT ON COLUMN pattern_roi_summary.roi_percentage IS
'Return on investment percentage: (savings / investment) * 100';
