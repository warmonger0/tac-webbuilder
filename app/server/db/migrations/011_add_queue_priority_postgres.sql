-- Migration 011: Add Priority and Deterministic Ordering to Phase Queue (PostgreSQL)
-- Purpose: Enable deterministic cross-parent phase execution ordering
-- Date: 2025-11-25

-- Add priority field (lower number = higher priority)
-- Default: 50 (normal priority)
-- Range: 10 (urgent) to 90 (background)
ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 50;

-- Add queue_position for FIFO tiebreaker
-- Note: PostgreSQL doesn't have ROWID like SQLite, we'll use a sequence
ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS queue_position INTEGER;

-- Add timestamps for audit trail
ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS ready_timestamp TIMESTAMP;
ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS started_timestamp TIMESTAMP;

-- Create index for efficient priority-based queries
CREATE INDEX IF NOT EXISTS idx_phase_queue_priority
  ON phase_queue(priority, queue_position);

-- Populate queue_position for existing records (based on creation order)
-- Use ROW_NUMBER() window function to assign positions
UPDATE phase_queue
SET queue_position = subquery.rn
FROM (
    SELECT queue_id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
    FROM phase_queue
    WHERE queue_position IS NULL
) AS subquery
WHERE phase_queue.queue_id = subquery.queue_id
  AND phase_queue.queue_position IS NULL;

-- Populate ready_timestamp for existing ready phases
UPDATE phase_queue
SET ready_timestamp = created_at
WHERE status = 'ready' AND ready_timestamp IS NULL;
