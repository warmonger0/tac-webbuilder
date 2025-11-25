-- Migration 009: Add queue configuration table for global queue settings
-- Enables pause/resume functionality for automatic phase execution

CREATE TABLE IF NOT EXISTS queue_config (
  config_key TEXT PRIMARY KEY,
  config_value TEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with queue paused by default (false = not paused, queue runs automatically)
INSERT INTO queue_config (config_key, config_value)
VALUES ('queue_paused', 'false')
ON CONFLICT (config_key) DO NOTHING;
