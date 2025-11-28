#!/usr/bin/env python3
"""
Fix phantom workflow_history records (completed/failed without end_time).

This script updates existing phantom records by setting end_time to:
- For completed workflows: updated_at timestamp (last known activity)
- For failed workflows: updated_at timestamp (last known activity)

Run with: uv run python scripts/fix_phantom_records.py [--dry-run]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.workflow_history_utils.database import DB_PATH, _db_adapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_phantom_records(dry_run: bool = False) -> dict:
    """
    Fix phantom workflow_history records by setting end_time.

    Args:
        dry_run: If True, only report what would be fixed without making changes

    Returns:
        dict with statistics: total_found, fixed_count, skipped_count
    """
    stats = {
        'total_found': 0,
        'fixed_count': 0,
        'skipped_count': 0,
        'details': []
    }

    with _db_adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Find all phantom records
        cursor.execute("""
            SELECT
                id,
                adw_id,
                status,
                start_time,
                end_time,
                updated_at,
                created_at
            FROM workflow_history
            WHERE status IN ('completed', 'failed') AND end_time IS NULL
            ORDER BY created_at DESC
        """)

        phantom_records = cursor.fetchall()
        stats['total_found'] = len(phantom_records)

        logger.info(f"Found {stats['total_found']} phantom records")

        if stats['total_found'] == 0:
            logger.info("No phantom records to fix!")
            return stats

        for record in phantom_records:
            adw_id = record['adw_id']
            status = record['status']
            start_time = record['start_time']
            updated_at = record['updated_at']
            created_at = record['created_at']

            # Determine best end_time value
            # Priority: updated_at > start_time > created_at
            end_time = updated_at or start_time or created_at

            if not end_time:
                logger.warning(
                    f"Cannot fix {adw_id}: no timestamp available "
                    f"(start_time={start_time}, updated_at={updated_at}, created_at={created_at})"
                )
                stats['skipped_count'] += 1
                stats['details'].append({
                    'adw_id': adw_id,
                    'status': status,
                    'action': 'skipped',
                    'reason': 'no_timestamp'
                })
                continue

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would fix {adw_id} (status={status}): "
                    f"end_time={end_time}"
                )
            else:
                cursor.execute("""
                    UPDATE workflow_history
                    SET end_time = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE adw_id = ?
                """, (end_time, adw_id))

                logger.info(
                    f"Fixed {adw_id} (status={status}): "
                    f"end_time={end_time}"
                )

            stats['fixed_count'] += 1
            stats['details'].append({
                'adw_id': adw_id,
                'status': status,
                'action': 'fixed' if not dry_run else 'would_fix',
                'end_time': end_time
            })

        if not dry_run and stats['fixed_count'] > 0:
            conn.commit()
            logger.info(f"✅ Committed {stats['fixed_count']} fixes to database")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Fix phantom workflow_history records without end_time'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information for each record'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Phantom Record Fix Script")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info("=" * 60)

    if not args.dry_run:
        confirm = input("\n⚠️  This will modify the database. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("Cancelled by user")
            return 1

    stats = fix_phantom_records(dry_run=args.dry_run)

    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info(f"  Total phantom records found: {stats['total_found']}")
    logger.info(f"  Records fixed: {stats['fixed_count']}")
    logger.info(f"  Records skipped: {stats['skipped_count']}")
    logger.info("=" * 60)

    if args.verbose and stats['details']:
        logger.info("\nDetails:")
        for detail in stats['details']:
            logger.info(f"  {detail['adw_id']}: {detail['action']} ({detail['status']})")

    if args.dry_run and stats['fixed_count'] > 0:
        logger.info("\nRun without --dry-run to apply these fixes")

    return 0


if __name__ == '__main__':
    sys.exit(main())
