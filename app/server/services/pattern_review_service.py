#!/usr/bin/env python3
"""
Pattern Review Service

Business logic for pattern approval and review operations.

Responsibilities:
- Fetch pending patterns for review
- Approve/reject patterns with audit trail
- Track review statistics
- Calculate impact scores for prioritization
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from database import get_database_adapter

logger = logging.getLogger(__name__)


@dataclass
class PatternReviewItem:
    """Data model for pattern review."""

    pattern_id: str
    tool_sequence: str
    status: str
    confidence_score: float
    occurrence_count: int
    estimated_savings_usd: float
    pattern_context: Optional[str] = None
    example_sessions: Optional[List[str]] = None  # Parsed from JSON
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    approval_notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    @property
    def impact_score(self) -> float:
        """Calculate impact score for prioritization."""
        return self.confidence_score * self.occurrence_count * self.estimated_savings_usd


class PatternReviewService:
    """Service for pattern review operations."""

    def __init__(self):
        """Initialize PatternReviewService with database adapter."""
        self.adapter = get_database_adapter()
        logger.info("[INIT] PatternReviewService initialized")

    def get_pending_patterns(self, limit: int = 20) -> List[PatternReviewItem]:
        """
        Get patterns pending review, ordered by impact score.

        Args:
            limit: Maximum number of patterns to return (default: 20)

        Returns:
            List of PatternReviewItem objects ordered by impact score (highest first)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Order by impact score: confidence * occurrences * savings
            cursor.execute(
                """
                SELECT * FROM pattern_approvals
                WHERE status = 'pending'
                ORDER BY (confidence_score * occurrence_count * estimated_savings_usd) DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            patterns = [self._row_to_model(row) for row in rows]

            logger.info(
                f"[{self.__class__.__name__}] Found {len(patterns)} pending patterns"
            )
            return patterns

    def get_pattern_details(self, pattern_id: str) -> Optional[PatternReviewItem]:
        """
        Get single pattern by pattern_id.

        Args:
            pattern_id: Pattern identifier

        Returns:
            PatternReviewItem or None if not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM pattern_approvals WHERE pattern_id = ?", (pattern_id,)
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(
                    f"[{self.__class__.__name__}] Pattern not found: {pattern_id}"
                )
                return None

            return self._row_to_model(row)

    def approve_pattern(
        self, pattern_id: str, reviewer: str, notes: Optional[str] = None
    ) -> Optional[PatternReviewItem]:
        """
        Approve a pattern.

        Args:
            pattern_id: Pattern identifier
            reviewer: Name of reviewer
            notes: Optional approval notes

        Returns:
            Updated PatternReviewItem or None if not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Update pattern status
            cursor.execute(
                """
                UPDATE pattern_approvals
                SET status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP,
                    approval_notes = ?
                WHERE pattern_id = ?
            """,
                (reviewer, notes, pattern_id),
            )

            if cursor.rowcount == 0:
                logger.warning(
                    f"[{self.__class__.__name__}] Pattern not found: {pattern_id}"
                )
                return None

            # Add to review history
            cursor.execute(
                """
                INSERT INTO pattern_review_history (pattern_id, action, reviewer, notes)
                VALUES (?, 'approved', ?, ?)
            """,
                (pattern_id, reviewer, notes),
            )

            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Approved pattern {pattern_id} by {reviewer}"
            )
            return self.get_pattern_details(pattern_id)

    def reject_pattern(
        self, pattern_id: str, reviewer: str, reason: str
    ) -> Optional[PatternReviewItem]:
        """
        Reject a pattern.

        Args:
            pattern_id: Pattern identifier
            reviewer: Name of reviewer
            reason: Reason for rejection (required)

        Returns:
            Updated PatternReviewItem or None if not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Update pattern status
            cursor.execute(
                """
                UPDATE pattern_approvals
                SET status = 'rejected',
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP,
                    approval_notes = ?
                WHERE pattern_id = ?
            """,
                (reviewer, f"REJECTED: {reason}", pattern_id),
            )

            if cursor.rowcount == 0:
                logger.warning(
                    f"[{self.__class__.__name__}] Pattern not found: {pattern_id}"
                )
                return None

            # Add to review history
            cursor.execute(
                """
                INSERT INTO pattern_review_history (pattern_id, action, reviewer, notes)
                VALUES (?, 'rejected', ?, ?)
            """,
                (pattern_id, reviewer, reason),
            )

            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Rejected pattern {pattern_id} by {reviewer}"
            )
            return self.get_pattern_details(pattern_id)

    def get_review_statistics(self) -> Dict[str, int]:
        """
        Get review statistics by status.

        Returns:
            Dictionary mapping status to count
            Example: {'pending': 15, 'approved': 42, 'rejected': 8}
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM pattern_approvals
                GROUP BY status
            """
            )

            stats = {row[0]: row[1] for row in cursor.fetchall()}

            logger.info(f"[{self.__class__.__name__}] Review statistics: {stats}")
            return stats

    def _row_to_model(self, row) -> PatternReviewItem:
        """
        Convert database row to PatternReviewItem model.

        Args:
            row: Database row tuple

        Returns:
            PatternReviewItem object
        """
        if not row:
            return None

        # Parse example_sessions JSON if present
        example_sessions = None
        if row[11]:  # example_sessions column
            try:
                example_sessions = json.loads(row[11])
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    f"[{self.__class__.__name__}] Failed to parse example_sessions for pattern {row[1]}"
                )
                example_sessions = []

        return PatternReviewItem(
            id=row[0],
            pattern_id=row[1],
            status=row[2],
            reviewed_by=row[3],
            reviewed_at=row[4],
            approval_notes=row[5],
            confidence_score=row[6],
            occurrence_count=row[7],
            estimated_savings_usd=row[8],
            tool_sequence=row[9],
            pattern_context=row[10],
            example_sessions=example_sessions,
            created_at=row[12],
            updated_at=row[13],
        )
