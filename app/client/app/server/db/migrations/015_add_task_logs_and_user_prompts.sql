-- Migration 015: Add task_logs and user_prompts tables
-- Created: 2025-12-02
-- Description: Observability tables for ADW phase logs and user request capture

-- =====================================================================
-- TABLE: user_prompts
-- Purpose: Capture structured user requests before they're sent to workflows
-- Hook: github_issue_service.submit_nl_request() (after processing)
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_prompts (
  id SERIAL PRIMARY KEY,

  -- Request Identification
  request_id TEXT UNIQUE NOT NULL,
  session_id TEXT,

  -- User Input (Raw)
  nl_input TEXT NOT NULL,
  project_path TEXT,
  auto_post BOOLEAN DEFAULT FALSE,

  -- Processed Output (Structured)
  issue_title TEXT,
  issue_body TEXT,
  issue_type TEXT, -- 'feature', 'bug', 'chore'
  complexity TEXT, -- 'ATOMIC', 'DECOMPOSE'

  -- Multi-Phase Info
  is_multi_phase BOOLEAN DEFAULT FALSE,
  phase_count INTEGER DEFAULT 1,
  parent_issue_number INTEGER,

  -- Cost Estimate
  estimated_cost_usd REAL,
  estimated_tokens INTEGER,
  model_name TEXT,

  -- GitHub Info
  github_issue_number INTEGER,
  github_issue_url TEXT,
  posted_at TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_prompts_request_id ON user_prompts(request_id);
CREATE INDEX IF NOT EXISTS idx_user_prompts_session ON user_prompts(session_id);
CREATE INDEX IF NOT EXISTS idx_user_prompts_issue ON user_prompts(github_issue_number);
CREATE INDEX IF NOT EXISTS idx_user_prompts_created ON user_prompts(created_at DESC);

-- =====================================================================
-- TABLE: task_logs
-- Purpose: Capture ADW phase completion logs (Plan, Build, Test, etc.)
-- Hook: ADW phase scripts (at completion) or GitHub comment webhook
-- =====================================================================

CREATE TABLE IF NOT EXISTS task_logs (
  id SERIAL PRIMARY KEY,

  -- Task Identification
  adw_id TEXT NOT NULL,
  issue_number INTEGER NOT NULL,
  workflow_template TEXT, -- 'adw_sdlc_complete_iso', 'adw_stepwise_iso', etc.

  -- Phase Info
  phase_name TEXT NOT NULL, -- 'Plan', 'Validate', 'Build', 'Lint', 'Test', 'Review', 'Document', 'Ship', 'Cleanup'
  phase_number INTEGER, -- 1-9
  phase_status TEXT NOT NULL CHECK(phase_status IN ('started', 'completed', 'failed', 'skipped')),

  -- Log Content
  log_message TEXT NOT NULL, -- The actual log message (e.g., "✅ Isolated planning phase completed")
  error_message TEXT, -- Only populated if phase_status = 'failed'

  -- Timing
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  duration_seconds REAL,

  -- Cost Data (if available)
  tokens_used INTEGER,
  cost_usd REAL,

  -- Metadata
  captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_logs_adw_id ON task_logs(adw_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_issue ON task_logs(issue_number);
CREATE INDEX IF NOT EXISTS idx_task_logs_phase ON task_logs(phase_name);
CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(phase_status);
CREATE INDEX IF NOT EXISTS idx_task_logs_created ON task_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_logs_issue_phase ON task_logs(issue_number, phase_number);

-- =====================================================================
-- VIEWS
-- =====================================================================

-- View: Latest phase status per issue
CREATE OR REPLACE VIEW v_task_logs_latest AS
SELECT
  issue_number,
  adw_id,
  phase_name,
  phase_number,
  phase_status,
  log_message,
  completed_at,
  ROW_NUMBER() OVER (PARTITION BY issue_number ORDER BY phase_number DESC, completed_at DESC) as rn
FROM task_logs
WHERE phase_status IN ('completed', 'failed');

-- View: Issue progress summary
CREATE OR REPLACE VIEW v_issue_progress AS
SELECT
  issue_number,
  adw_id,
  workflow_template,
  COUNT(*) as total_phases,
  SUM(CASE WHEN phase_status = 'completed' THEN 1 ELSE 0 END) as completed_phases,
  SUM(CASE WHEN phase_status = 'failed' THEN 1 ELSE 0 END) as failed_phases,
  MAX(phase_number) as latest_phase,
  MAX(completed_at) as last_activity
FROM task_logs
GROUP BY issue_number, adw_id, workflow_template;

-- View: User prompts with linked task progress
CREATE OR REPLACE VIEW v_user_prompts_with_progress AS
SELECT
  up.*,
  ip.total_phases,
  ip.completed_phases,
  ip.failed_phases,
  ip.latest_phase,
  ip.last_activity
FROM user_prompts up
LEFT JOIN v_issue_progress ip ON up.github_issue_number = ip.issue_number;
