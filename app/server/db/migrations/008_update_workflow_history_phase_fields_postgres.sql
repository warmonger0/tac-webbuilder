-- Migration 008: Add multi-phase support to workflow_history table (PostgreSQL)
-- Tracks parent-child relationships and phase information for multi-phase workflows

ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS phase_number INTEGER;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS is_multi_phase BOOLEAN DEFAULT false;

-- Note: parent_workflow_id may already exist from migration 004
-- Using IF NOT EXISTS to avoid errors
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_history' AND column_name = 'parent_workflow_id'
    ) THEN
        ALTER TABLE workflow_history ADD COLUMN parent_workflow_id TEXT;
    END IF;
END $$;
