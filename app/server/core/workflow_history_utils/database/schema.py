"""
Database schema initialization and migrations.

This module handles schema creation, index management, and database migrations
for the workflow history system.
"""

import logging
import sqlite3
from pathlib import Path

from utils.db_connection import get_connection as get_db_connection

logger = logging.getLogger(__name__)

# Database path - relative to package: core/workflow_history_utils/database/
DB_PATH = Path(__file__).parent.parent.parent.parent / "db" / "workflow_history.db"


def init_db():
    """
    Initialize the workflow history database with schema.

    Creates the workflow_history table with all required fields and indexes.
    Safe to call multiple times - creates tables only if they don't exist.
    """
    # Ensure db directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Create workflow_history table with comprehensive fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adw_id TEXT NOT NULL UNIQUE,
                issue_number INTEGER,
                nl_input TEXT,
                github_url TEXT,
                gh_issue_state TEXT,  -- GitHub issue state: 'open', 'closed', or NULL
                workflow_template TEXT,
                model_used TEXT,
                status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                error_message TEXT,
                phase_count INTEGER,
                current_phase TEXT,
                success_rate REAL,
                retry_count INTEGER DEFAULT 0,
                worktree_path TEXT,
                backend_port INTEGER,
                frontend_port INTEGER,
                concurrent_workflows INTEGER DEFAULT 0,

                -- Token usage fields
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cached_tokens INTEGER DEFAULT 0,
                cache_hit_tokens INTEGER DEFAULT 0,
                cache_miss_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cache_efficiency_percent REAL DEFAULT 0.0,

                -- Cost tracking fields
                estimated_cost_total REAL DEFAULT 0.0,
                actual_cost_total REAL DEFAULT 0.0,
                estimated_cost_per_step REAL DEFAULT 0.0,
                actual_cost_per_step REAL DEFAULT 0.0,
                cost_per_token REAL DEFAULT 0.0,

                -- Structured data fields (JSON)
                structured_input TEXT,  -- JSON object
                cost_breakdown TEXT,    -- JSON object
                token_breakdown TEXT,   -- JSON object

                -- Resource usage
                worktree_reused INTEGER DEFAULT 0,  -- Boolean (0 or 1)
                steps_completed INTEGER DEFAULT 0,
                steps_total INTEGER DEFAULT 0,

                -- Phase 3A: Analytics fields (temporal and scoring)
                hour_of_day INTEGER DEFAULT -1,
                day_of_week INTEGER DEFAULT -1,
                nl_input_clarity_score REAL DEFAULT 0.0,
                cost_efficiency_score REAL DEFAULT 0.0,
                performance_score REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,

                -- Phase 3B: Scoring version tracking
                scoring_version TEXT DEFAULT '1.0',

                -- Phase 3D: Insights & Recommendations
                anomaly_flags TEXT,  -- JSON array of anomaly objects
                optimization_recommendations TEXT,  -- JSON array of recommendation strings

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_adw_id ON workflow_history(adw_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON workflow_history(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON workflow_history(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_issue_number ON workflow_history(issue_number)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_used ON workflow_history(model_used)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workflow_template ON workflow_history(workflow_template)
        """)

        # Migration: Add gh_issue_state column if it doesn't exist
        try:
            cursor.execute("SELECT gh_issue_state FROM workflow_history LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            logger.info("[DB] Adding gh_issue_state column to workflow_history table")
            cursor.execute("ALTER TABLE workflow_history ADD COLUMN gh_issue_state TEXT")
            conn.commit()

        # Migration: Fix phantom records (completed/failed without end_time)
        # Note: We can't add CHECK constraint to existing table in SQLite,
        # but we can fix existing data and rely on application-level validation
        cursor.execute("""
            SELECT adw_id, status, end_time
            FROM workflow_history
            WHERE status IN ('completed', 'failed') AND end_time IS NULL
        """)
        phantom_records = cursor.fetchall()

        if phantom_records:
            logger.warning(
                f"[DB] Found {len(phantom_records)} phantom records with completed/failed "
                f"status but no end_time. These should be investigated."
            )
            for record in phantom_records:
                logger.warning(
                    f"[DB] Phantom record: adw_id={record['adw_id']}, "
                    f"status={record['status']}, end_time={record['end_time']}"
                )

        logger.info(f"[DB] Workflow history database initialized at {DB_PATH}")
