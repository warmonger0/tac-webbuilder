-- Migration 010: Add pattern predictions tracking
-- Stores predicted patterns before workflow execution for validation
-- This enables submission-time pattern detection (Phase 2)

-- ============================================================================
-- OPERATION_PATTERNS TABLE (Create if not exists - for Phase 1)
-- ============================================================================
-- Create simplified operation_patterns table for Phase 2 if it doesn't exist
-- Full table with all Phase 1 features will be created by migration 004
CREATE TABLE IF NOT EXISTS operation_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_signature TEXT UNIQUE NOT NULL,
    pattern_type TEXT NOT NULL,

    -- Detection
    first_detected TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now')),
    occurrence_count INTEGER DEFAULT 1,

    -- Automation Status
    automation_status TEXT DEFAULT 'detected' CHECK(
        automation_status IN ('detected', 'candidate', 'approved', 'implemented', 'active', 'deprecated', 'predicted')
    ),
    confidence_score REAL DEFAULT 0.0,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Phase 2 prediction tracking columns
    prediction_count INTEGER DEFAULT 0,
    prediction_accuracy REAL DEFAULT 0.0,
    last_predicted TEXT
);

CREATE INDEX IF NOT EXISTS idx_operation_patterns_type ON operation_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_status ON operation_patterns(automation_status);

-- ============================================================================
-- PATTERN PREDICTIONS TABLE - Tracks predicted patterns from user input
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    pattern_id INTEGER NOT NULL,

    -- Prediction details
    confidence_score REAL NOT NULL,
    reasoning TEXT,
    predicted_at TEXT DEFAULT (datetime('now')),

    -- Validation (filled after workflow completes)
    was_correct INTEGER,  -- NULL = not validated, 1 = correct, 0 = incorrect
    validated_at TEXT,

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);

CREATE INDEX IF NOT EXISTS idx_pattern_predictions_request ON pattern_predictions(request_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_validated ON pattern_predictions(was_correct);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Migration 010 adds pattern prediction infrastructure for Phase 2
-- This enables:
-- 1. Predict patterns from user input at submission time
-- 2. Store predictions for later validation
-- 3. Track prediction accuracy over time
-- 4. Improve prediction algorithm based on validation results
