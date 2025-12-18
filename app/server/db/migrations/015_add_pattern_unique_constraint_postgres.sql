-- Migration 015: Add unique constraint to pattern_occurrences (PostgreSQL)
-- Prevents duplicate pattern detections for same workflow

-- Add unique index on (pattern_id, workflow_id)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pattern_occurrence_unique
ON pattern_occurrences(pattern_id, workflow_id);
