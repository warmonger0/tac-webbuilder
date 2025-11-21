-- Migration 003: Add Advanced Analytics Metrics
-- Adds fields for Phase 3: Workflow History Advanced Analytics & Optimization Insights

-- Input quality metrics
ALTER TABLE workflow_history ADD COLUMN nl_input_word_count INTEGER;
ALTER TABLE workflow_history ADD COLUMN nl_input_clarity_score REAL; -- 0-100 score based on heuristics
ALTER TABLE workflow_history ADD COLUMN structured_input_completeness_percent REAL;

-- Temporal patterns
-- NOTE: Column names corrected to match Python schema (hour_of_day, day_of_week)
-- Migration 005 renames these columns in existing databases
ALTER TABLE workflow_history ADD COLUMN hour_of_day INTEGER; -- 0-23
ALTER TABLE workflow_history ADD COLUMN day_of_week INTEGER; -- 0-6 (Monday=0)

-- Outcome tracking
ALTER TABLE workflow_history ADD COLUMN pr_merged INTEGER DEFAULT 0; -- Boolean (0 or 1)
ALTER TABLE workflow_history ADD COLUMN time_to_merge_hours REAL;
ALTER TABLE workflow_history ADD COLUMN review_cycles INTEGER;
ALTER TABLE workflow_history ADD COLUMN ci_test_pass_rate REAL;

-- Efficiency scores
ALTER TABLE workflow_history ADD COLUMN cost_efficiency_score REAL; -- 0-100: composite of cost vs estimate, cache efficiency, retry rate
ALTER TABLE workflow_history ADD COLUMN performance_score REAL; -- 0-100: based on duration vs similar workflows
ALTER TABLE workflow_history ADD COLUMN quality_score REAL; -- 0-100: based on error rate, review cycles, test pass rate

-- Pattern metadata
ALTER TABLE workflow_history ADD COLUMN similar_workflow_ids TEXT; -- JSON array of similar workflow ADW IDs
ALTER TABLE workflow_history ADD COLUMN anomaly_flags TEXT; -- JSON array of detected anomalies
ALTER TABLE workflow_history ADD COLUMN optimization_recommendations TEXT; -- JSON array of recommendations

-- Create indexes for improved query performance
CREATE INDEX IF NOT EXISTS idx_hour_of_day ON workflow_history(hour_of_day);
CREATE INDEX IF NOT EXISTS idx_day_of_week ON workflow_history(day_of_week);
CREATE INDEX IF NOT EXISTS idx_pr_merged ON workflow_history(pr_merged);
CREATE INDEX IF NOT EXISTS idx_cost_efficiency_score ON workflow_history(cost_efficiency_score);
CREATE INDEX IF NOT EXISTS idx_performance_score ON workflow_history(performance_score);
CREATE INDEX IF NOT EXISTS idx_quality_score ON workflow_history(quality_score);
