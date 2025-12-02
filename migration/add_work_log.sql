-- Migration: Add work_log table for tracking chat session summaries
-- Created: 2025-12-02
-- Description: Simple logging system to track what happened in each chat session

-- PostgreSQL version
CREATE TABLE IF NOT EXISTS work_log (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT NOT NULL,
  summary TEXT NOT NULL CHECK(length(summary) <= 280),
  chat_file_link TEXT,
  issue_number INTEGER,
  workflow_id TEXT,
  tags TEXT, -- JSON array stored as text
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_work_log_session ON work_log(session_id);
CREATE INDEX IF NOT EXISTS idx_work_log_timestamp ON work_log(timestamp DESC);

-- SQLite version (alternative for development)
-- Note: SQLite doesn't support IF NOT EXISTS for indexes in older versions
-- Uncomment if using SQLite:
/*
CREATE TABLE IF NOT EXISTS work_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT NOT NULL,
  summary TEXT NOT NULL CHECK(length(summary) <= 280),
  chat_file_link TEXT,
  issue_number INTEGER,
  workflow_id TEXT,
  tags TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_work_log_session ON work_log(session_id);
CREATE INDEX IF NOT EXISTS idx_work_log_timestamp ON work_log(timestamp DESC);
*/
