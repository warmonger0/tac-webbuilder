-- Context Review Tables Migration
-- This migration adds support for AI-powered context review and caching

-- Main context reviews table
-- Stores metadata about context analysis requests and results
CREATE TABLE IF NOT EXISTS context_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT,
    issue_number INTEGER,
    change_description TEXT NOT NULL,
    project_path TEXT NOT NULL,
    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    analysis_duration_seconds REAL,
    agent_cost REAL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'analyzing', 'complete', 'failed')),
    result TEXT
);

-- Context suggestions table
-- Stores individual suggestions from the analysis
CREATE TABLE IF NOT EXISTS context_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    suggestion_type TEXT NOT NULL CHECK(suggestion_type IN ('file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy')),
    suggestion_text TEXT NOT NULL,
    confidence REAL,
    priority INTEGER,
    rationale TEXT,
    FOREIGN KEY (review_id) REFERENCES context_reviews(id) ON DELETE CASCADE
);

-- Context cache table
-- Caches analysis results to save costs on similar requests
CREATE TABLE IF NOT EXISTS context_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    analysis_result TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_context_reviews_workflow ON context_reviews(workflow_id);
CREATE INDEX IF NOT EXISTS idx_context_reviews_issue ON context_reviews(issue_number);
CREATE INDEX IF NOT EXISTS idx_context_reviews_status ON context_reviews(status);
CREATE INDEX IF NOT EXISTS idx_context_suggestions_review ON context_suggestions(review_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_key ON context_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_context_cache_created ON context_cache(created_at);
