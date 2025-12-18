#!/usr/bin/env python3
"""
Pattern Sync Service

Automated service for synchronizing patterns from operation_patterns to pattern_approvals.

Responsibilities:
- Sync new detected patterns for review
- Apply intelligent filtering (high confidence, high savings, high occurrence)
- Track sync history and prevent duplicates
- Support manual and automated sync operations
- Provide sync statistics and reporting

Architecture:
    operation_patterns (source of truth)
            ↓
    PatternSyncService (sync logic)
            ↓
    pattern_approvals (review queue)
            ↓
    Panel 8 Review UI
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from database import get_database_adapter

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a pattern sync operation."""

    total_candidates: int
    synced_count: int
    skipped_count: int
    error_count: int
    synced_pattern_ids: list[str]
    errors: list[str]
    sync_duration_ms: float

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "total_candidates": self.total_candidates,
            "synced_count": self.synced_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "synced_pattern_ids": self.synced_pattern_ids,
            "errors": self.errors,
            "sync_duration_ms": self.sync_duration_ms,
        }


@dataclass
class SyncFilter:
    """Filter criteria for pattern sync."""

    min_confidence: float = 0.0  # 0-100 scale
    min_occurrences: int = 1
    min_savings: float = 0.0  # USD/month
    max_patterns: int = 50  # Limit per sync
    exclude_types: list[str] | None = None  # Pattern types to exclude
    only_types: list[str] | None = None  # Only these pattern types


class PatternSyncService:
    """Service for syncing patterns from operation_patterns to pattern_approvals."""

    def __init__(self):
        """Initialize PatternSyncService with database adapter."""
        self.adapter = get_database_adapter()
        logger.info("[INIT] PatternSyncService initialized")

    def sync_patterns(
        self,
        sync_filter: SyncFilter | None = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Sync patterns from operation_patterns to pattern_approvals.

        Args:
            sync_filter: Filter criteria (uses smart defaults if None)
            dry_run: If True, report what would be synced without syncing

        Returns:
            SyncResult with statistics and list of synced patterns

        Example:
            >>> service = PatternSyncService()
            >>> # Sync high-value patterns only
            >>> filter = SyncFilter(min_confidence=70, min_savings=1000)
            >>> result = service.sync_patterns(sync_filter=filter)
            >>> print(f"Synced {result.synced_count} patterns")
        """
        start_time = datetime.now()

        # Use smart defaults if no filter provided
        if sync_filter is None:
            sync_filter = self._get_smart_defaults()

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()

                # Get candidates from operation_patterns
                candidates = self._get_sync_candidates(cursor, sync_filter)

                logger.info(
                    f"[{self.__class__.__name__}] Found {len(candidates)} candidates for sync"
                )

                synced_pattern_ids = []
                errors = []
                skipped_count = 0

                for candidate in candidates:
                    try:
                        # Check if already exists in pattern_approvals
                        if self._pattern_exists(cursor, candidate["pattern_signature"]):
                            logger.debug(
                                f"[{self.__class__.__name__}] Skipping existing pattern: "
                                f"{candidate['pattern_signature']}"
                            )
                            skipped_count += 1
                            continue

                        # Sync to pattern_approvals
                        if not dry_run:
                            self._sync_single_pattern(cursor, candidate)
                            conn.commit()

                        synced_pattern_ids.append(candidate["pattern_signature"])

                    except Exception as e:
                        logger.error(
                            f"[{self.__class__.__name__}] Error syncing pattern "
                            f"{candidate.get('pattern_signature', 'unknown')}: {e}"
                        )
                        errors.append(
                            f"Pattern {candidate.get('pattern_signature', 'unknown')}: {str(e)}"
                        )

                # Calculate duration
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000

                result = SyncResult(
                    total_candidates=len(candidates),
                    synced_count=len(synced_pattern_ids),
                    skipped_count=skipped_count,
                    error_count=len(errors),
                    synced_pattern_ids=synced_pattern_ids,
                    errors=errors,
                    sync_duration_ms=duration_ms,
                )

                logger.info(
                    f"[{self.__class__.__name__}] Sync completed: "
                    f"{result.synced_count} synced, {result.skipped_count} skipped, "
                    f"{result.error_count} errors in {duration_ms:.0f}ms "
                    f"(dry_run={dry_run})"
                )

                return result

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Sync failed: {e}")
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return SyncResult(
                total_candidates=0,
                synced_count=0,
                skipped_count=0,
                error_count=1,
                synced_pattern_ids=[],
                errors=[f"Sync failed: {str(e)}"],
                sync_duration_ms=duration_ms,
            )

    def _get_sync_candidates(self, cursor, sync_filter: SyncFilter) -> list[dict]:
        """Get patterns from operation_patterns that match filter criteria."""
        # Build WHERE clause based on filter
        where_clauses = ["automation_status = 'detected'"]

        if sync_filter.min_confidence > 0:
            where_clauses.append(f"confidence_score >= {sync_filter.min_confidence}")

        if sync_filter.min_occurrences > 1:
            where_clauses.append(f"occurrence_count >= {sync_filter.min_occurrences}")

        if sync_filter.min_savings > 0:
            where_clauses.append(
                f"potential_monthly_savings >= {sync_filter.min_savings}"
            )

        if sync_filter.only_types:
            types_str = ",".join(f"'{t}'" for t in sync_filter.only_types)
            where_clauses.append(f"pattern_type IN ({types_str})")

        if sync_filter.exclude_types:
            types_str = ",".join(f"'{t}'" for t in sync_filter.exclude_types)
            where_clauses.append(f"pattern_type NOT IN ({types_str})")

        where_clause = " AND ".join(where_clauses)

        # Query with ordering by impact (confidence * occurrences * savings)
        query = f"""
            SELECT
                pattern_signature,
                pattern_type,
                confidence_score,
                occurrence_count,
                potential_monthly_savings,
                typical_operations,
                typical_input_pattern,
                first_detected,
                last_seen
            FROM operation_patterns
            WHERE {where_clause}
            ORDER BY (confidence_score * occurrence_count * potential_monthly_savings) DESC
            LIMIT {sync_filter.max_patterns}
        """

        cursor.execute(query)
        return cursor.fetchall()

    def _pattern_exists(self, cursor, pattern_id: str) -> bool:
        """Check if pattern already exists in pattern_approvals."""
        placeholder = self.adapter.placeholder()
        cursor.execute(
            f"SELECT 1 FROM pattern_approvals WHERE pattern_id = {placeholder}",
            (pattern_id,),
        )
        return cursor.fetchone() is not None

    def _sync_single_pattern(self, cursor, candidate: dict) -> None:
        """Sync a single pattern to pattern_approvals."""
        placeholder = self.adapter.placeholder()

        # Extract tool sequence from typical_operations (JSONB field)
        # For now, use pattern_type as tool_sequence
        # TODO: Parse typical_operations JSONB to extract actual tool sequence
        tool_sequence = candidate.get("pattern_type") or "Unknown"

        # Build pattern context from typical_input_pattern
        typical_input = candidate.get("typical_input_pattern") or ""
        pattern_context = typical_input[:500] if typical_input else ""  # Limit length

        # Handle NULL values gracefully
        confidence_score = candidate.get("confidence_score") or 0.0
        occurrence_count = candidate.get("occurrence_count") or 0
        potential_savings = candidate.get("potential_monthly_savings") or 0.0

        # Insert into pattern_approvals
        cursor.execute(
            f"""
            INSERT INTO pattern_approvals (
                pattern_id,
                tool_sequence,
                status,
                confidence_score,
                occurrence_count,
                estimated_savings_usd,
                pattern_context,
                created_at,
                updated_at
            ) VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder},
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """,
            (
                candidate["pattern_signature"],
                tool_sequence,
                "pending",  # All synced patterns start as pending
                confidence_score / 100.0,  # Convert to 0-1 scale
                occurrence_count,
                potential_savings,
                pattern_context,
            ),
        )

        logger.debug(
            f"[{self.__class__.__name__}] Synced pattern: {candidate['pattern_signature']}"
        )

    def _get_smart_defaults(self) -> SyncFilter:
        """
        Get smart default filter that prioritizes high-value patterns.

        Strategy:
        - High confidence (70%+) OR high savings ($1000+/mo) OR high occurrences (100+)
        - Limit to top 50 patterns per sync
        - Exclude low-value noise patterns
        """
        return SyncFilter(
            min_confidence=60.0,  # Reasonable confidence threshold
            min_occurrences=2,  # At least 2 occurrences to avoid noise
            min_savings=0.0,  # Include all savings levels initially
            max_patterns=50,  # Prevent overwhelming reviewers
            exclude_types=None,  # Include all types
            only_types=None,
        )

    def get_sync_statistics(self) -> dict:
        """
        Get statistics about sync status.

        Returns:
            Dictionary with:
            - patterns_in_source: Count in operation_patterns
            - patterns_in_review: Count in pattern_approvals
            - pending_sync: Patterns that could be synced
            - last_sync_time: Timestamp of last sync (if tracked)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Count patterns in operation_patterns
            cursor.execute(
                "SELECT COUNT(*) as count FROM operation_patterns WHERE automation_status = 'detected'"
            )
            patterns_in_source = cursor.fetchone()["count"]

            # Count patterns in pattern_approvals
            cursor.execute("SELECT COUNT(*) as count FROM pattern_approvals")
            patterns_in_review = cursor.fetchone()["count"]

            # Count pending sync (in source but not in review)
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM operation_patterns op
                WHERE op.automation_status = 'detected'
                  AND NOT EXISTS (
                      SELECT 1 FROM pattern_approvals pa
                      WHERE pa.pattern_id = op.pattern_signature
                  )
            """
            )
            pending_sync = cursor.fetchone()["count"]

            stats = {
                "patterns_in_source": patterns_in_source,
                "patterns_in_review": patterns_in_review,
                "pending_sync": pending_sync,
                "sync_percentage": (
                    (patterns_in_review / patterns_in_source * 100)
                    if patterns_in_source > 0
                    else 0
                ),
            }

            logger.info(f"[{self.__class__.__name__}] Sync statistics: {stats}")
            return stats

    def sync_high_priority_patterns(self) -> SyncResult:
        """
        Convenience method to sync only high-priority patterns.

        This is the recommended sync strategy for automated background jobs.

        Returns:
            SyncResult with sync details
        """
        high_priority_filter = SyncFilter(
            min_confidence=70.0,  # High confidence
            min_savings=1000.0,  # At least $1000/month value
            min_occurrences=5,  # Proven patterns
            max_patterns=20,  # Don't overwhelm reviewers
        )

        logger.info(
            f"[{self.__class__.__name__}] Starting high-priority pattern sync"
        )
        return self.sync_patterns(sync_filter=high_priority_filter)

    def sync_all_patterns(self) -> SyncResult:
        """
        Sync all detected patterns regardless of confidence/savings.

        Use with caution - may create many low-value review items.

        Returns:
            SyncResult with sync details
        """
        all_patterns_filter = SyncFilter(
            min_confidence=0.0,
            min_savings=0.0,
            min_occurrences=1,
            max_patterns=200,  # Higher limit for bulk sync
        )

        logger.info(f"[{self.__class__.__name__}] Starting full pattern sync")
        return self.sync_patterns(sync_filter=all_patterns_filter)
