-- Webhook Analytics View
-- Provides aggregated webhook event statistics for pattern analysis and monitoring

CREATE OR REPLACE VIEW webhook_analytics AS
SELECT
    DATE(created_at) as date,
    CASE
        WHEN phase_name = 'webhook_received' THEN 'github_webhook'
        WHEN phase_name LIKE 'phase_%_complete' THEN 'workflow_complete'
        ELSE 'other'
    END as webhook_type,
    phase_status,
    COUNT(*) as event_count,
    AVG(duration_seconds) as avg_duration_seconds,
    MIN(duration_seconds) as min_duration_seconds,
    MAX(duration_seconds) as max_duration_seconds,
    COUNT(CASE WHEN phase_status = 'completed' THEN 1 END) as success_count,
    COUNT(CASE WHEN phase_status = 'failed' THEN 1 END) as failure_count,
    ROUND(
        COUNT(CASE WHEN phase_status = 'completed' THEN 1 END)::numeric /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate_percent
FROM task_logs
WHERE phase_name = 'webhook_received' OR phase_name LIKE 'phase_%_complete'
GROUP BY DATE(created_at), webhook_type, phase_status
ORDER BY date DESC, event_count DESC;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_task_logs_webhook_analytics
ON task_logs(created_at, phase_name, phase_status)
WHERE phase_name = 'webhook_received' OR phase_name LIKE 'phase_%_complete';
