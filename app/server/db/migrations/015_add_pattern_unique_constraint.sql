-- Migration 015: Add unique constraint to pattern_occurrences
-- Prevents duplicate pattern detections for same workflow

-- Add unique index on (pattern_id, workflow_id)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pattern_occurrence_unique
ON pattern_occurrences(pattern_id, workflow_id);

-- Verify index created
SELECT sql FROM sqlite_master
WHERE type = 'index'
AND name = 'idx_pattern_occurrence_unique';
