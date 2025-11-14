"""
ADW Concurrency Lock Management

Prevents multiple ADW workflows from working on the same GitHub issue simultaneously.
This module provides mutex-like locking functionality to ensure only one ADW instance
processes a given issue at any time.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "database.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_adw_locks_table() -> None:
    """
    Initialize the adw_locks table if it doesn't exist.

    This table tracks active ADW instances per issue to prevent
    concurrent workflows from competing for the same work.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adw_locks (
                issue_number INTEGER PRIMARY KEY,
                adw_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('planning', 'building', 'testing', 'reviewing', 'documenting')),
                github_url TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster status queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_adw_locks_status
            ON adw_locks(status)
        """)

        logger.info("[ADW Lock] Lock table initialized")


def acquire_lock(issue_number: int, adw_id: str, github_url: Optional[str] = None) -> bool:
    """
    Attempt to acquire a lock for a GitHub issue.

    Args:
        issue_number: The GitHub issue number
        adw_id: The ADW workflow identifier
        github_url: Optional GitHub issue URL

    Returns:
        True if lock acquired successfully, False if issue is already locked
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if there's an existing lock for this issue
        cursor.execute("""
            SELECT adw_id, status, created_at
            FROM adw_locks
            WHERE issue_number = ?
            AND status IN ('planning', 'building', 'testing', 'reviewing', 'documenting')
        """, (issue_number,))

        existing_lock = cursor.fetchone()

        if existing_lock:
            logger.warning(
                f"[ADW Lock] Issue #{issue_number} already locked by ADW {existing_lock['adw_id']} "
                f"(status: {existing_lock['status']}, since: {existing_lock['created_at']})"
            )
            return False

        # Acquire the lock
        try:
            cursor.execute("""
                INSERT INTO adw_locks (issue_number, adw_id, status, github_url)
                VALUES (?, ?, ?, ?)
            """, (issue_number, adw_id, 'planning', github_url))

            logger.info(f"[ADW Lock] Lock acquired for issue #{issue_number} by ADW {adw_id}")
            return True

        except sqlite3.IntegrityError:
            # Race condition: another ADW acquired the lock between our check and insert
            logger.warning(f"[ADW Lock] Race condition detected for issue #{issue_number}")
            return False


def update_lock_status(issue_number: int, adw_id: str, new_status: str) -> bool:
    """
    Update the status of an existing lock.

    Args:
        issue_number: The GitHub issue number
        adw_id: The ADW workflow identifier (must match existing lock)
        new_status: New status ('planning', 'building', 'testing', 'reviewing', 'documenting')

    Returns:
        True if update successful, False if no matching lock found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE adw_locks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE issue_number = ? AND adw_id = ?
        """, (new_status, issue_number, adw_id))

        if cursor.rowcount > 0:
            logger.info(f"[ADW Lock] Updated issue #{issue_number} status to '{new_status}'")
            return True
        else:
            logger.warning(
                f"[ADW Lock] Failed to update lock for issue #{issue_number} "
                f"(ADW {adw_id} may not own this lock)"
            )
            return False


def release_lock(issue_number: int, adw_id: str) -> bool:
    """
    Release a lock when ADW workflow completes or fails.

    Args:
        issue_number: The GitHub issue number
        adw_id: The ADW workflow identifier (must match existing lock)

    Returns:
        True if lock released successfully, False if no matching lock found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM adw_locks
            WHERE issue_number = ? AND adw_id = ?
        """, (issue_number, adw_id))

        if cursor.rowcount > 0:
            logger.info(f"[ADW Lock] Released lock for issue #{issue_number} (ADW {adw_id})")
            return True
        else:
            logger.warning(
                f"[ADW Lock] No lock found to release for issue #{issue_number} "
                f"(ADW {adw_id})"
            )
            return False


def force_release_lock(issue_number: int) -> bool:
    """
    Forcefully release a lock (admin/cleanup operation).

    Use this for stuck locks or manual cleanup. Should not be used
    during normal ADW workflow execution.

    Args:
        issue_number: The GitHub issue number

    Returns:
        True if lock released, False if no lock existed
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM adw_locks
            WHERE issue_number = ?
        """, (issue_number,))

        if cursor.rowcount > 0:
            logger.warning(f"[ADW Lock] Force-released lock for issue #{issue_number}")
            return True
        else:
            logger.info(f"[ADW Lock] No lock to force-release for issue #{issue_number}")
            return False


def get_active_locks() -> list[dict]:
    """
    Get all currently active ADW locks.

    Returns:
        List of dictionaries containing lock information
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                issue_number,
                adw_id,
                status,
                github_url,
                created_at,
                updated_at
            FROM adw_locks
            ORDER BY created_at DESC
        """)

        locks = []
        for row in cursor.fetchall():
            locks.append({
                'issue_number': row['issue_number'],
                'adw_id': row['adw_id'],
                'status': row['status'],
                'github_url': row['github_url'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })

        return locks


def cleanup_stale_locks(max_age_hours: int = 24) -> int:
    """
    Clean up locks that have been active for too long (likely stuck/abandoned).

    Args:
        max_age_hours: Maximum age in hours before a lock is considered stale

    Returns:
        Number of stale locks cleaned up
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM adw_locks
            WHERE created_at < datetime('now', '-' || ? || ' hours')
        """, (max_age_hours,))

        count = cursor.rowcount
        if count > 0:
            logger.warning(f"[ADW Lock] Cleaned up {count} stale locks (older than {max_age_hours}h)")

        return count


# Initialize table on module import
try:
    init_adw_locks_table()
except Exception as e:
    logger.error(f"[ADW Lock] Failed to initialize locks table: {e}")
