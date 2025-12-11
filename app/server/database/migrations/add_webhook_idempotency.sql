-- Add webhook idempotency tracking
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_id VARCHAR(255) NOT NULL,
    webhook_type VARCHAR(50) NOT NULL,
    adw_id VARCHAR(100),
    issue_number INTEGER,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(webhook_id)
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_webhook_events_lookup
    ON webhook_events(webhook_id, received_at);

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_webhook_events_cleanup
    ON webhook_events(received_at);
