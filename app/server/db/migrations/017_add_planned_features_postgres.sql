-- Migration 017: Add Planned Features Table (PostgreSQL)
-- Created: 2025-12-07
-- Purpose: Database-driven planning system for tracking sessions, features, bugs, and enhancements

-- Main planned_features table
CREATE TABLE IF NOT EXISTS planned_features (
    id SERIAL PRIMARY KEY,
    item_type TEXT NOT NULL CHECK(item_type IN ('session', 'feature', 'bug', 'enhancement')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    estimated_hours REAL,
    actual_hours REAL,
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER,
    tags JSONB,  -- Use JSONB for PostgreSQL
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES planned_features(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_planned_features_status ON planned_features(status);
CREATE INDEX IF NOT EXISTS idx_planned_features_priority ON planned_features(priority);
CREATE INDEX IF NOT EXISTS idx_planned_features_type ON planned_features(item_type);
CREATE INDEX IF NOT EXISTS idx_planned_features_session ON planned_features(session_number);
CREATE INDEX IF NOT EXISTS idx_planned_features_github ON planned_features(github_issue_number);
CREATE INDEX IF NOT EXISTS idx_planned_features_completed ON planned_features(completed_at);
CREATE INDEX IF NOT EXISTS idx_planned_features_parent ON planned_features(parent_id);

-- GIN index for JSONB tags for efficient tag searching
CREATE INDEX IF NOT EXISTS idx_planned_features_tags ON planned_features USING GIN (tags);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_planned_features_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
DROP TRIGGER IF EXISTS update_planned_features_timestamp ON planned_features;
CREATE TRIGGER update_planned_features_timestamp
BEFORE UPDATE ON planned_features
FOR EACH ROW
EXECUTE FUNCTION update_planned_features_timestamp();
