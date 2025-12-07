-- Migration 016: Add Pattern Approvals and Review History
-- Created: 2025-12-06
-- Purpose: Pattern review system with manual approval/rejection, database tracking, and safety layer

-- Main pattern approvals table
CREATE TABLE IF NOT EXISTS pattern_approvals (
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

-- Audit trail for pattern review actions
CREATE TABLE IF NOT EXISTS pattern_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('approved', 'rejected', 'flagged', 'commented')),
    reviewer TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_approvals(pattern_id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_status ON pattern_approvals(status);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_reviewed_at ON pattern_approvals(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_pattern_approvals_confidence ON pattern_approvals(confidence_score);
CREATE INDEX IF NOT EXISTS idx_pattern_review_history_pattern ON pattern_review_history(pattern_id);

-- Update timestamp trigger for pattern_approvals
CREATE TRIGGER IF NOT EXISTS update_pattern_approvals_timestamp
AFTER UPDATE ON pattern_approvals
BEGIN
    UPDATE pattern_approvals SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
