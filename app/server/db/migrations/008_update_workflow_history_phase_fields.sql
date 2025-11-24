-- Migration 008: Add multi-phase support to workflow_history table
-- Tracks parent-child relationships and phase information for multi-phase workflows
-- NOTE: These columns were already added in a previous migration, keeping for reference

-- ALTER TABLE workflow_history ADD COLUMN phase_number INTEGER;
-- ALTER TABLE workflow_history ADD COLUMN parent_workflow_id TEXT;
-- ALTER TABLE workflow_history ADD COLUMN is_multi_phase BOOLEAN DEFAULT 0;

-- Columns already exist:
-- - phase_number (column 70)
-- - parent_workflow_id (column 64)
-- - is_multi_phase (column 71)
