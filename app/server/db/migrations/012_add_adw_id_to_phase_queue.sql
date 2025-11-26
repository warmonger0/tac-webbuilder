-- Migration 008: Add adw_id column to phase_queue table
-- Description: Track the ADW ID for running phases to enable real-time state updates

ALTER TABLE phase_queue ADD COLUMN adw_id TEXT;
