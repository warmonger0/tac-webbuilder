-- Migration 021: Add workflow_type column to planned_features table
-- Allows users to select which ADW workflow to run (e.g., adw_sdlc_complete_iso, adw_sdlc_from_build_iso)

-- Add workflow_type column
ALTER TABLE planned_features
ADD COLUMN IF NOT EXISTS workflow_type TEXT DEFAULT 'adw_sdlc_complete_iso';

-- Add index for performance (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_planned_features_workflow_type
ON planned_features(workflow_type);

-- Update existing records to have default workflow
UPDATE planned_features
SET workflow_type = 'adw_sdlc_complete_iso'
WHERE workflow_type IS NULL;

-- Add comment
COMMENT ON COLUMN planned_features.workflow_type IS 'ADW workflow template to use (e.g., adw_sdlc_complete_iso, adw_sdlc_from_build_iso)';
