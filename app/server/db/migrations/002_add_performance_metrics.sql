-- Migration 002: Add performance and error analytics fields
-- Adds phase-level performance metrics, error categorization, and complexity tracking

ALTER TABLE workflow_history ADD COLUMN phase_durations TEXT;
ALTER TABLE workflow_history ADD COLUMN idle_time_seconds INTEGER;
ALTER TABLE workflow_history ADD COLUMN bottleneck_phase TEXT;
ALTER TABLE workflow_history ADD COLUMN error_category TEXT;
ALTER TABLE workflow_history ADD COLUMN retry_reasons TEXT;
ALTER TABLE workflow_history ADD COLUMN error_phase_distribution TEXT;
ALTER TABLE workflow_history ADD COLUMN recovery_time_seconds INTEGER;
ALTER TABLE workflow_history ADD COLUMN complexity_estimated TEXT;
ALTER TABLE workflow_history ADD COLUMN complexity_actual TEXT;
