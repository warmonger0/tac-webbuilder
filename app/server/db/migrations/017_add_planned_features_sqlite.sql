-- Migration 017: Add Planned Features Table (SQLite)
-- Single Source of Truth for all planned work items

CREATE TABLE IF NOT EXISTS planned_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL CHECK(item_type IN ('session', 'feature', 'bug', 'enhancement')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled')),
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    estimated_hours REAL,
    actual_hours REAL,
    session_number INTEGER,
    github_issue_number INTEGER,
    parent_id INTEGER,
    tags TEXT DEFAULT '[]',  -- JSON string for SQLite
    completion_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES planned_features(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_planned_features_status ON planned_features(status);
CREATE INDEX IF NOT EXISTS idx_planned_features_priority ON planned_features(priority);
CREATE INDEX IF NOT EXISTS idx_planned_features_type ON planned_features(item_type);
CREATE INDEX IF NOT EXISTS idx_planned_features_session ON planned_features(session_number);
CREATE INDEX IF NOT EXISTS idx_planned_features_github ON planned_features(github_issue_number);
CREATE INDEX IF NOT EXISTS idx_planned_features_completed ON planned_features(completed_at);
CREATE INDEX IF NOT EXISTS idx_planned_features_parent ON planned_features(parent_id);

-- Trigger for automatic updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_planned_features_timestamp
AFTER UPDATE ON planned_features
FOR EACH ROW
BEGIN
    UPDATE planned_features SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
