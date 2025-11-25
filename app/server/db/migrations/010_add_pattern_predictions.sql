-- Migration 010: Add Pattern Predictions Table
-- Implements the validation loop for pattern recognition by tracking predictions
-- and measuring accuracy against actual workflow outcomes.

-- ============================================================================
-- PATTERN PREDICTIONS TABLE - Tracks predictions and validation results
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Workflow Context
    workflow_id TEXT NOT NULL,
    request_id TEXT,  -- Optional: links to request that triggered prediction

    -- Pattern Information
    pattern_id INTEGER NOT NULL,
    pattern_signature TEXT NOT NULL,

    -- Prediction Data
    predicted_at TEXT DEFAULT (datetime('now')),
    predicted_confidence REAL DEFAULT 0.0,  -- 0.0 to 100.0
    prediction_reason TEXT,  -- Why this pattern was predicted

    -- Validation Results
    was_correct INTEGER,  -- NULL until validated, 1 for correct, 0 for incorrect
    validated_at TEXT,
    validation_notes TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id),
    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id),

    -- Ensure unique prediction per workflow-pattern combination
    UNIQUE(workflow_id, pattern_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_workflow ON pattern_predictions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_validated ON pattern_predictions(validated_at);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_was_correct ON pattern_predictions(was_correct);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_request ON pattern_predictions(request_id);

-- ============================================================================
-- ADD prediction_accuracy TO operation_patterns
-- ============================================================================
-- Track running average of prediction accuracy for each pattern
ALTER TABLE operation_patterns ADD COLUMN prediction_accuracy REAL DEFAULT NULL;

-- Index for filtering by accuracy
CREATE INDEX IF NOT EXISTS idx_operation_patterns_prediction_accuracy
    ON operation_patterns(prediction_accuracy);

-- ============================================================================
-- VIEWS for easier querying
-- ============================================================================

-- Patterns with high prediction accuracy (reliable automation candidates)
CREATE VIEW IF NOT EXISTS v_reliable_patterns AS
SELECT
    p.*,
    p.prediction_accuracy * 100 as accuracy_percent,
    (SELECT COUNT(*) FROM pattern_predictions pp WHERE pp.pattern_id = p.id AND pp.was_correct = 1) as correct_predictions,
    (SELECT COUNT(*) FROM pattern_predictions pp WHERE pp.pattern_id = p.id AND pp.was_correct = 0) as incorrect_predictions,
    (SELECT COUNT(*) FROM pattern_predictions pp WHERE pp.pattern_id = p.id AND pp.was_correct IS NOT NULL) as total_validated
FROM operation_patterns p
WHERE p.prediction_accuracy >= 0.70  -- 70% accuracy threshold
AND p.occurrence_count >= 5  -- Minimum sample size
ORDER BY p.prediction_accuracy DESC, p.occurrence_count DESC;

-- Recent validation results
CREATE VIEW IF NOT EXISTS v_recent_validations AS
SELECT
    pp.id,
    pp.workflow_id,
    pp.pattern_signature,
    pp.predicted_confidence,
    pp.was_correct,
    pp.predicted_at,
    pp.validated_at,
    p.pattern_type,
    p.automation_status,
    p.prediction_accuracy
FROM pattern_predictions pp
JOIN operation_patterns p ON pp.pattern_id = p.id
WHERE pp.validated_at IS NOT NULL
ORDER BY pp.validated_at DESC
LIMIT 100;

-- Validation metrics by pattern type
CREATE VIEW IF NOT EXISTS v_validation_metrics_by_type AS
SELECT
    p.pattern_type,
    COUNT(DISTINCT p.id) as pattern_count,
    COUNT(pp.id) as total_predictions,
    SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
    SUM(CASE WHEN pp.was_correct = 0 THEN 1 ELSE 0 END) as incorrect_predictions,
    CAST(SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) AS REAL) /
        NULLIF(COUNT(CASE WHEN pp.was_correct IS NOT NULL THEN 1 END), 0) as accuracy_rate,
    AVG(p.prediction_accuracy) as avg_pattern_accuracy,
    AVG(pp.predicted_confidence) as avg_predicted_confidence
FROM operation_patterns p
LEFT JOIN pattern_predictions pp ON pp.pattern_id = p.id
GROUP BY p.pattern_type
ORDER BY accuracy_rate DESC;

-- ============================================================================
-- TRIGGERS for automated maintenance
-- ============================================================================

-- Update operation_patterns.prediction_accuracy when validation result is recorded
CREATE TRIGGER IF NOT EXISTS trigger_update_pattern_accuracy
AFTER UPDATE OF was_correct ON pattern_predictions
FOR EACH ROW
WHEN NEW.was_correct IS NOT NULL
BEGIN
    UPDATE operation_patterns
    SET prediction_accuracy = (
        SELECT AVG(CAST(was_correct AS REAL))
        FROM pattern_predictions
        WHERE pattern_id = NEW.pattern_id
        AND was_correct IS NOT NULL
    )
    WHERE id = NEW.pattern_id;
END;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Migration 010 adds pattern prediction tracking and validation infrastructure.
-- This enables the system to:
-- 1. Track pattern predictions at workflow start
-- 2. Validate predictions against actual outcomes at workflow completion
-- 3. Calculate prediction accuracy metrics per pattern
-- 4. Identify reliable patterns for safe automation
-- 5. Continuously improve confidence scores based on validation feedback
