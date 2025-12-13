-- Migration 020: Add Branch Tracking Fields to Workflow History
-- Purpose: Add branch_name, plan_file, and issue_class for better workflow visibility
-- Date: 2025-12-12
-- Session: Quick Win #66 - Branch Name Visibility

-- Add columns to workflow_history table
ALTER TABLE workflow_history
ADD COLUMN IF NOT EXISTS branch_name TEXT,
ADD COLUMN IF NOT EXISTS plan_file TEXT,
ADD COLUMN IF NOT EXISTS issue_class TEXT;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_workflow_history_branch_name ON workflow_history(branch_name);
CREATE INDEX IF NOT EXISTS idx_workflow_history_issue_class ON workflow_history(issue_class);

-- Add comments for documentation
COMMENT ON COLUMN workflow_history.branch_name IS 'Git branch name for this workflow';
COMMENT ON COLUMN workflow_history.plan_file IS 'Path to plan file (if completed planning)';
COMMENT ON COLUMN workflow_history.issue_class IS 'Issue classification (e.g., /bug, /feature, /chore)';
