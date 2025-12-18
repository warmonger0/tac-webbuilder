-- Migration 013: Add performance indexes for phase queue (PostgreSQL)
-- Date: 2025-11-25
-- Purpose: Optimize frequently used queries on phase_queue table

-- Index for parent_issue lookups (used in get_queue_by_parent)
CREATE INDEX IF NOT EXISTS idx_phase_queue_parent_issue
ON phase_queue(parent_issue);

-- Index for status filtering (used in get_next_phase_1, get_all_queued)
CREATE INDEX IF NOT EXISTS idx_phase_queue_status
ON phase_queue(status);

-- Index for issue_number lookups (used in issue completion endpoint)
CREATE INDEX IF NOT EXISTS idx_phase_queue_issue_number
ON phase_queue(issue_number);

-- Note: Composite index idx_phase_queue_priority already exists from migration 011
-- (priority, queue_position)
