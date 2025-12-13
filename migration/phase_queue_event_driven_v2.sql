-- Migration: phase_queue v1.0 (polling) → v2.0 (event-driven)
-- Date: 2025-12-13
-- Purpose: Support multi-dependencies and feature-based tracking

BEGIN;

-- 1. Add new column for multi-dependencies
ALTER TABLE phase_queue ADD COLUMN depends_on_phases JSONB;

-- 2. Migrate existing single dependency to array format
UPDATE phase_queue
SET depends_on_phases = CASE
    WHEN depends_on_phase IS NULL THEN '[]'::jsonb
    ELSE json_build_array(depends_on_phase)::jsonb
END;

-- 3. Verify migration (should be 0 NULL values)
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count
    FROM phase_queue
    WHERE depends_on_phases IS NULL;

    IF null_count > 0 THEN
        RAISE EXCEPTION 'Migration failed: % rows have NULL depends_on_phases', null_count;
    END IF;

    RAISE NOTICE 'Migration verified: All rows have depends_on_phases populated';
END $$;

-- 4. Drop old single-dependency column
ALTER TABLE phase_queue DROP COLUMN IF EXISTS depends_on_phase;

-- 5. Rename parent_issue → feature_id
-- (Skip if parent_issue already references planned_features.id)
ALTER TABLE phase_queue RENAME COLUMN parent_issue TO feature_id;

-- 6. Update indexes
DROP INDEX IF EXISTS idx_phase_queue_parent;
CREATE INDEX IF NOT EXISTS idx_phase_queue_feature ON phase_queue(feature_id);
CREATE INDEX IF NOT EXISTS idx_phase_queue_status_feature ON phase_queue(status, feature_id);

-- 7. Add comments
COMMENT ON COLUMN phase_queue.feature_id IS 'References planned_features.id (NOT GitHub parent issue)';
COMMENT ON COLUMN phase_queue.depends_on_phases IS 'JSON array of phase numbers that must complete first (e.g., [1, 3])';
COMMENT ON TABLE phase_queue IS 'Event-driven phase queue with multi-dependency support';

COMMIT;

-- Verification queries
SELECT
    'Total rows' as metric,
    COUNT(*) as value
FROM phase_queue
UNION ALL
SELECT
    'Rows with dependencies',
    COUNT(*)
FROM phase_queue
WHERE jsonb_array_length(depends_on_phases) > 0
UNION ALL
SELECT
    'Max dependencies per phase',
    MAX(jsonb_array_length(depends_on_phases))
FROM phase_queue;
