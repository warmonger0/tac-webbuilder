-- Migration 003: Add Advanced Analytics Metrics (PostgreSQL)
-- Adds fields for Phase 3: Workflow History Advanced Analytics & Optimization Insights

-- Input quality metrics
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS nl_input_word_count INTEGER;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS nl_input_clarity_score REAL;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS structured_input_completeness_percent REAL;

-- Temporal patterns
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS hour_of_day INTEGER DEFAULT -1;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS day_of_week INTEGER DEFAULT -1;

-- Outcome tracking
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS pr_merged BOOLEAN DEFAULT false;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS time_to_merge_hours REAL;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS review_cycles INTEGER;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS ci_test_pass_rate REAL;

-- Efficiency scores
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS cost_efficiency_score REAL DEFAULT 0.0;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS performance_score REAL DEFAULT 0.0;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS quality_score REAL DEFAULT 0.0;

-- Pattern metadata
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS similar_workflow_ids JSONB;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS anomaly_flags JSONB;
ALTER TABLE workflow_history ADD COLUMN IF NOT EXISTS optimization_recommendations JSONB;

-- Create indexes for improved query performance
CREATE INDEX IF NOT EXISTS idx_hour_of_day ON workflow_history(hour_of_day);
CREATE INDEX IF NOT EXISTS idx_day_of_week ON workflow_history(day_of_week);
CREATE INDEX IF NOT EXISTS idx_pr_merged ON workflow_history(pr_merged);
CREATE INDEX IF NOT EXISTS idx_cost_efficiency_score ON workflow_history(cost_efficiency_score);
CREATE INDEX IF NOT EXISTS idx_performance_score ON workflow_history(performance_score);
CREATE INDEX IF NOT EXISTS idx_quality_score ON workflow_history(quality_score);
