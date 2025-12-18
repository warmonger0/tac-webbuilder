-- Migration 012: Add adw_id column to phase_queue table (PostgreSQL)
-- Description: Track the ADW ID for running phases to enable real-time state updates

ALTER TABLE phase_queue ADD COLUMN IF NOT EXISTS adw_id TEXT;
