-- Migration 019: Add Confidence History Tracking
-- Purpose: Track confidence score updates for pattern learning system
-- Date: 2025-12-08
-- Session: 13 - Confidence Updating System

-- Create pattern_confidence_history table
CREATE TABLE IF NOT EXISTS pattern_confidence_history (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    old_confidence REAL NOT NULL,
    new_confidence REAL NOT NULL,
    adjustment_reason TEXT NOT NULL,
    roi_data JSONB,
    updated_by TEXT DEFAULT 'system',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id) ON DELETE CASCADE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_confidence_history_pattern
ON pattern_confidence_history(pattern_id);

CREATE INDEX IF NOT EXISTS idx_confidence_history_date
ON pattern_confidence_history(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_confidence_history_pattern_date
ON pattern_confidence_history(pattern_id, updated_at DESC);

-- Comments for documentation
COMMENT ON TABLE pattern_confidence_history IS 'Tracks confidence score adjustments based on pattern performance';
COMMENT ON COLUMN pattern_confidence_history.pattern_id IS 'Reference to pattern in pattern_approvals';
COMMENT ON COLUMN pattern_confidence_history.old_confidence IS 'Previous confidence score (0.0-1.0)';
COMMENT ON COLUMN pattern_confidence_history.new_confidence IS 'New confidence score (0.0-1.0)';
COMMENT ON COLUMN pattern_confidence_history.adjustment_reason IS 'Human-readable explanation for adjustment';
COMMENT ON COLUMN pattern_confidence_history.roi_data IS 'Snapshot of ROI metrics at time of update (JSON)';
COMMENT ON COLUMN pattern_confidence_history.updated_by IS 'Who/what triggered the update (system, user, etc.)';
COMMENT ON COLUMN pattern_confidence_history.updated_at IS 'Timestamp when confidence was updated';
