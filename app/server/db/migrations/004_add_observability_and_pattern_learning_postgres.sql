-- Migration 004: Add Observability and Pattern Learning Tables (PostgreSQL)
-- Created: 2025-12-17
-- Purpose: Create missing tables from migration 004 for PostgreSQL
--
-- Note: Most tables from migration 004 were created programmatically.
-- This migration adds only the 2 missing tables:
-- 1. pattern_occurrences - Links workflows to detected patterns
-- 2. cost_savings_log - Tracks actual cost savings from optimizations

-- ============================================================================
-- PATTERN OCCURRENCES TABLE - Links executions to patterns
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_occurrences (
    id SERIAL PRIMARY KEY,
    pattern_id INTEGER NOT NULL,
    workflow_id TEXT NOT NULL,

    -- Similarity Metrics
    similarity_score REAL DEFAULT 0.0,
    matched_characteristics TEXT,  -- JSON

    detected_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
    -- Note: workflow_id references workflow_history(adw_id) but we can't create FK
    -- because adw_id is VARCHAR(255) and workflow_id is TEXT
);

CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_workflow ON pattern_occurrences(workflow_id);
CREATE INDEX IF NOT EXISTS idx_pattern_occurrences_detected ON pattern_occurrences(detected_at);

-- ============================================================================
-- COST SAVINGS LOG TABLE - Measure actual impact
-- ============================================================================
CREATE TABLE IF NOT EXISTS cost_savings_log (
    id SERIAL PRIMARY KEY,

    -- What saved cost
    optimization_type TEXT NOT NULL CHECK(
        optimization_type IN ('tool_call', 'input_split', 'pattern_offload', 'inverted_flow')
    ),
    workflow_id TEXT NOT NULL,
    tool_call_id TEXT,
    pattern_id INTEGER,

    -- Savings
    baseline_tokens INTEGER DEFAULT 0,
    actual_tokens INTEGER DEFAULT 0,
    tokens_saved INTEGER DEFAULT 0,
    cost_saved_usd REAL DEFAULT 0.0,

    -- Context
    saved_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,

    -- Note: Foreign keys removed to avoid constraint issues
    -- workflow_id should reference workflow_history(adw_id)
    -- tool_call_id should reference tool_calls(tool_call_id)
    -- pattern_id references operation_patterns(id)
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);

CREATE INDEX IF NOT EXISTS idx_cost_savings_type ON cost_savings_log(optimization_type);
CREATE INDEX IF NOT EXISTS idx_cost_savings_workflow ON cost_savings_log(workflow_id);
CREATE INDEX IF NOT EXISTS idx_cost_savings_saved_at ON cost_savings_log(saved_at);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Migration 004 (PostgreSQL) adds the 2 missing tables for pattern learning:
-- 1. pattern_occurrences - Enables tracking which workflows matched which patterns
-- 2. cost_savings_log - Enables ROI measurement and validation
--
-- Key conversions from SQLite:
-- - INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
-- - TEXT DEFAULT (datetime('now')) → TIMESTAMP DEFAULT NOW()
-- - REAL → REAL (compatible)
-- - TEXT → TEXT (compatible)
