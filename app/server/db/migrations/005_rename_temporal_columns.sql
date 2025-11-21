-- Migration 005: Rename Temporal Columns to Match Code Schema
-- Fixes bug #64: Schema mismatch causing "table workflow_history has no column named hour_of_day" errors
-- This migration renames submission_hour -> hour_of_day and submission_day_of_week -> day_of_week
-- to align database schema with Python code expectations in data_models.py and database.py

-- SQLite doesn't support ALTER TABLE RENAME COLUMN directly in older versions
-- We need to use a more complex approach:
-- 1. Create new columns with correct names
-- 2. Copy data from old columns
-- 3. Drop old columns (requires recreating table)

-- Step 1: Add new columns with correct names
ALTER TABLE workflow_history ADD COLUMN hour_of_day INTEGER;
ALTER TABLE workflow_history ADD COLUMN day_of_week INTEGER;

-- Step 2: Copy data from old columns to new ones
UPDATE workflow_history
SET hour_of_day = submission_hour,
    day_of_week = submission_day_of_week;

-- Step 3: Drop old indexes
DROP INDEX IF EXISTS idx_submission_hour;
DROP INDEX IF EXISTS idx_submission_day_of_week;

-- Step 4: Since SQLite has limited ALTER TABLE support, we need to recreate the table
-- to remove the old columns. This is done via CREATE TABLE AS SELECT.
-- Save the table structure first by backing up to a temp table.

CREATE TABLE workflow_history_temp AS
SELECT
    adw_id,
    issue_number,
    issue_title,
    issue_body,
    started_at,
    completed_at,
    duration_seconds,
    status,
    error_message,
    workflow_type,
    base_model,
    total_prompt_tokens,
    total_completion_tokens,
    total_cost,
    cache_creation_tokens,
    cache_read_tokens,
    retry_count,
    files_changed_count,
    nl_input_word_count,
    nl_input_clarity_score,
    structured_input_completeness_percent,
    hour_of_day,
    day_of_week,
    pr_merged,
    time_to_merge_hours,
    review_cycles,
    ci_test_pass_rate,
    cost_efficiency_score,
    performance_score,
    quality_score,
    similar_workflow_ids,
    anomaly_flags,
    optimization_recommendations,
    key_learnings,
    pattern_frequency,
    similar_pattern_success_rate
FROM workflow_history;

-- Drop the original table
DROP TABLE workflow_history;

-- Recreate the table with the correct schema
CREATE TABLE workflow_history (
    adw_id TEXT PRIMARY KEY,
    issue_number INTEGER,
    issue_title TEXT,
    issue_body TEXT,
    started_at TEXT,
    completed_at TEXT,
    duration_seconds REAL,
    status TEXT,
    error_message TEXT,
    workflow_type TEXT,
    base_model TEXT,
    total_prompt_tokens INTEGER DEFAULT 0,
    total_completion_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    files_changed_count INTEGER DEFAULT 0,
    nl_input_word_count INTEGER,
    nl_input_clarity_score REAL,
    structured_input_completeness_percent REAL,
    hour_of_day INTEGER,
    day_of_week INTEGER,
    pr_merged INTEGER DEFAULT 0,
    time_to_merge_hours REAL,
    review_cycles INTEGER,
    ci_test_pass_rate REAL,
    cost_efficiency_score REAL,
    performance_score REAL,
    quality_score REAL,
    similar_workflow_ids TEXT,
    anomaly_flags TEXT,
    optimization_recommendations TEXT,
    key_learnings TEXT,
    pattern_frequency INTEGER,
    similar_pattern_success_rate REAL
);

-- Restore data from temp table
INSERT INTO workflow_history SELECT * FROM workflow_history_temp;

-- Drop temp table
DROP TABLE workflow_history_temp;

-- Step 5: Recreate indexes with correct column names
CREATE INDEX IF NOT EXISTS idx_hour_of_day ON workflow_history(hour_of_day);
CREATE INDEX IF NOT EXISTS idx_day_of_week ON workflow_history(day_of_week);
CREATE INDEX IF NOT EXISTS idx_pr_merged ON workflow_history(pr_merged);
CREATE INDEX IF NOT EXISTS idx_cost_efficiency_score ON workflow_history(cost_efficiency_score);
CREATE INDEX IF NOT EXISTS idx_performance_score ON workflow_history(performance_score);
CREATE INDEX IF NOT EXISTS idx_quality_score ON workflow_history(quality_score);
CREATE INDEX IF NOT EXISTS idx_status ON workflow_history(status);
CREATE INDEX IF NOT EXISTS idx_workflow_type ON workflow_history(workflow_type);
CREATE INDEX IF NOT EXISTS idx_started_at ON workflow_history(started_at);
