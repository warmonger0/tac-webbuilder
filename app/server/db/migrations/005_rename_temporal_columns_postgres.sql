-- Migration 005: Rename Temporal Columns to Match Code Schema (PostgreSQL)
-- Fixes bug #64: Schema mismatch causing "table workflow_history has no column named hour_of_day" errors
-- This migration renames submission_hour -> hour_of_day and submission_day_of_week -> day_of_week
-- to align database schema with Python code expectations in data_models.py and database.py

-- PostgreSQL supports ALTER TABLE RENAME COLUMN directly
-- Check if old columns exist and rename them, or create new ones if they don't exist

-- Rename submission_hour to hour_of_day (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_history' AND column_name = 'submission_hour'
    ) THEN
        ALTER TABLE workflow_history RENAME COLUMN submission_hour TO hour_of_day;
    END IF;
END $$;

-- Rename submission_day_of_week to day_of_week (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_history' AND column_name = 'submission_day_of_week'
    ) THEN
        ALTER TABLE workflow_history RENAME COLUMN submission_day_of_week TO day_of_week;
    END IF;
END $$;

-- Drop old indexes if they exist
DROP INDEX IF EXISTS idx_submission_hour;
DROP INDEX IF EXISTS idx_submission_day_of_week;

-- Recreate indexes with correct column names (if not already created)
CREATE INDEX IF NOT EXISTS idx_hour_of_day ON workflow_history(hour_of_day);
CREATE INDEX IF NOT EXISTS idx_day_of_week ON workflow_history(day_of_week);
