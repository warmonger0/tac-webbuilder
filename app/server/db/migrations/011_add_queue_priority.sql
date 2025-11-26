-- Migration 007: Add Priority and Deterministic Ordering to Phase Queue
-- Purpose: Enable deterministic cross-parent phase execution ordering
-- Date: 2025-11-25

BEGIN TRANSACTION;

-- Add priority field (lower number = higher priority)
-- Default: 50 (normal priority)
-- Range: 10 (urgent) to 90 (background)
ALTER TABLE phase_queue ADD COLUMN priority INTEGER DEFAULT 50;

-- Add queue_position for FIFO tiebreaker
-- Auto-increments based on insertion order
ALTER TABLE phase_queue ADD COLUMN queue_position INTEGER;

-- Add timestamps for audit trail
ALTER TABLE phase_queue ADD COLUMN ready_timestamp TEXT;
ALTER TABLE phase_queue ADD COLUMN started_timestamp TEXT;

-- Create index for efficient priority-based queries
CREATE INDEX IF NOT EXISTS idx_phase_queue_priority
  ON phase_queue(priority, queue_position);

-- Populate queue_position for existing records (based on ROWID = insertion order)
UPDATE phase_queue
SET queue_position = ROWID
WHERE queue_position IS NULL;

-- Populate ready_timestamp for existing ready phases
UPDATE phase_queue
SET ready_timestamp = created_at
WHERE status = 'ready' AND ready_timestamp IS NULL;

COMMIT;

-- Verification queries
SELECT 'Migration 007 completed successfully' as status;
SELECT COUNT(*) as total_phases,
       COUNT(priority) as phases_with_priority,
       COUNT(queue_position) as phases_with_position
FROM phase_queue;
