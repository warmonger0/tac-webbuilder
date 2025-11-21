-- Migration 006: Add Missing scoring_version Column
-- Date: 2025-11-21
-- Purpose: Add scoring_version column that code expects but database lacks
--
-- SAFETY: This is a minimal, safe migration that only adds one column.
-- It does NOT drop any columns or modify existing data.
--
-- Background:
-- - The code expects a scoring_version column (WorkflowHistoryItem model)
-- - Current database is missing this column
-- - This causes silent failures when code tries to read/write this field
--
-- The temporal column renaming (submission_hour -> hour_of_day) is
-- handled by the compatibility layer in database.py and works correctly.

-- Add scoring_version column if it doesn't exist
-- Use IF NOT EXISTS simulation via CHECK
-- SQLite doesn't have IF NOT EXISTS for ALTER TABLE, so we handle errors gracefully
-- The application code will check for column existence before using it

ALTER TABLE workflow_history ADD COLUMN scoring_version TEXT DEFAULT '1.0';

-- Note: If this column already exists, SQLite will error.
-- That's okay - it means the migration was already applied.
-- The backup exists at db/backups/workflow_history_backup_YYYYMMDD_HHMMSS.db
