-- Migration 014: Add context review tables (PostgreSQL)
-- Date: 2025-12-01
-- Purpose: Add AI-powered context review system for workflow optimization
--
-- NOTE: The actual schema is created programmatically in
-- core/context_review/database/schema.py to support both SQLite and PostgreSQL.
-- This migration file is provided for reference and manual database setup.

-- Table: context_reviews
-- Stores AI analysis results for codebase context before workflow execution
CREATE TABLE IF NOT EXISTS context_reviews (
    id SERIAL PRIMARY KEY,
    workflow_id TEXT,
    issue_number INTEGER,
    change_description TEXT NOT NULL,
    project_path TEXT NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_duration_seconds REAL,
    agent_cost REAL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'analyzing', 'complete', 'failed')),
    result TEXT
);

-- Table: context_suggestions
-- Stores specific integration suggestions from AI analysis
CREATE TABLE IF NOT EXISTS context_suggestions (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL,
    suggestion_type TEXT NOT NULL CHECK(suggestion_type IN (
        'file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy'
    )),
    suggestion_text TEXT NOT NULL,
    confidence REAL,
    priority INTEGER,
    rationale TEXT,
    FOREIGN KEY (review_id) REFERENCES context_reviews(id)
);

-- Table: context_cache
-- Caches analysis results to avoid redundant API calls
CREATE TABLE IF NOT EXISTS context_cache (
    id SERIAL PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE,
    analysis_result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_context_reviews_workflow
ON context_reviews(workflow_id);

CREATE INDEX IF NOT EXISTS idx_context_reviews_issue
ON context_reviews(issue_number);

CREATE INDEX IF NOT EXISTS idx_context_reviews_status
ON context_reviews(status);

CREATE INDEX IF NOT EXISTS idx_context_suggestions_review
ON context_suggestions(review_id);

CREATE INDEX IF NOT EXISTS idx_context_suggestions_type
ON context_suggestions(suggestion_type);

CREATE INDEX IF NOT EXISTS idx_context_cache_key
ON context_cache(cache_key);
