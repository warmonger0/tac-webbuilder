-- Migration 010: Add pattern predictions tracking
-- Stores predicted patterns before workflow execution for validation

-- Create operation_patterns table if it doesn't exist
CREATE TABLE IF NOT EXISTS operation_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_signature TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL,
    automation_status TEXT DEFAULT 'detected',
    detection_count INTEGER DEFAULT 0,
    last_detected TEXT,
    prediction_count INTEGER DEFAULT 0,
    prediction_accuracy REAL DEFAULT 0.0,
    last_predicted TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_operation_patterns_signature ON operation_patterns(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_operation_patterns_type ON operation_patterns(pattern_type);

-- Drop and recreate pattern_predictions table with proper foreign key
DROP TABLE IF EXISTS pattern_predictions;

CREATE TABLE pattern_predictions (
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
