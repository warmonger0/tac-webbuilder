-- Migration 002: Add performance and error analytics fields (PostgreSQL)
-- Adds phase-level performance metrics, error categorization, and complexity tracking

ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS phase_durations JSONB;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS idle_time_seconds INTEGER;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS bottleneck_phase VARCHAR(255);
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS error_category VARCHAR(255);
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS retry_reasons JSONB;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS error_phase_distribution JSONB;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS recovery_time_seconds INTEGER;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS complexity_estimated VARCHAR(100);
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS complexity_actual VARCHAR(100);
