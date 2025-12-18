-- Migration 006: Add scoring version field (PostgreSQL)
-- Tracks which version of the scoring algorithm was used for metrics calculation

ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS scoring_version VARCHAR(50) DEFAULT '1.0';
