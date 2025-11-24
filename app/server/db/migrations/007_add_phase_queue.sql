-- Migration 007: Add phase queue table for multi-phase workflow management
-- Enables sequential execution of multi-phase requests with dependency tracking

CREATE TABLE IF NOT EXISTS phase_queue (
  queue_id TEXT PRIMARY KEY,
  parent_issue INTEGER NOT NULL,
  phase_number INTEGER NOT NULL,
  issue_number INTEGER,  -- NULL until GitHub issue created
  status TEXT CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')) DEFAULT 'queued',
  depends_on_phase INTEGER,  -- Phase number that must complete first (NULL for Phase 1)
  phase_data TEXT,  -- JSON: {title, content, externalDocs}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  error_message TEXT
);

CREATE INDEX idx_phase_queue_status ON phase_queue(status);
CREATE INDEX idx_phase_queue_parent ON phase_queue(parent_issue);
CREATE INDEX idx_phase_queue_issue ON phase_queue(issue_number);
