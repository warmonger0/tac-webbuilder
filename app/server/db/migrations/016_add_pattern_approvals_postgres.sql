-- Migration 016: Add Pattern Approvals and Review History (PostgreSQL)
-- Created: 2025-12-06
-- Purpose: Pattern review system with manual approval/rejection, database tracking, and safety layer

-- Main pattern approvals table
CREATE TABLE IF NOT EXISTS pattern_approvals (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit trail for pattern review actions
CREATE TABLE IF NOT EXISTS pattern_review_history (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('approved', 'rejected', 'flagged', 'commented')),
    reviewer TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_status ON pattern_approvals(status);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_reviewed_at ON pattern_approvals(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_confidence ON pattern_approvals(confidence_score);
CREATE INDEX IF NOT EXISTS idx_pattern_review_history_pattern ON pattern_review_history(pattern_id);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_pattern_approvals_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
DROP TRIGGER IF EXISTS update_pattern_approvals_timestamp ON pattern_approvals;
CREATE TRIGGER update_pattern_approvals_timestamp
BEFORE UPDATE ON pattern_approvals
FOR EACH ROW
EXECUTE FUNCTION update_pattern_approvals_timestamp();
