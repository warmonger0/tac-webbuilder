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
            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                SELECT * FROM pattern_approvals
                WHERE status = 'pending'
                ORDER BY (confidence_score * occurrence_count * estimated_savings_usd) DESC
                LIMIT {placeholder}
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

            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"SELECT * FROM pattern_approvals WHERE pattern_id = {placeholder}", (pattern_id,)
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
            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                UPDATE pattern_approvals
                SET status = 'approved',
                    reviewed_by = {placeholder},
                    reviewed_at = CURRENT_TIMESTAMP,
                    approval_notes = {placeholder}
                WHERE pattern_id = {placeholder}
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
                f"""
                INSERT INTO pattern_review_history (pattern_id, action, reviewer, notes)
                VALUES ({placeholder}, 'approved', {placeholder}, {placeholder})
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
            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                UPDATE pattern_approvals
                SET status = 'rejected',
                    reviewed_by = {placeholder},
                    reviewed_at = CURRENT_TIMESTAMP,
                    approval_notes = {placeholder}
                WHERE pattern_id = {placeholder}
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
                f"""
                INSERT INTO pattern_review_history (pattern_id, action, reviewer, notes)
                VALUES ({placeholder}, 'rejected', {placeholder}, {placeholder})
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

            # PostgreSQL RealDictCursor returns dict rows
            rows = cursor.fetchall()
            stats = {row['status']: row['count'] for row in rows}

            logger.info(f"[{self.__class__.__name__}] Review statistics: {stats}")
            return stats

    def create_pattern(self, pattern_data: Dict[str, any]) -> str:
        """
        Insert new pattern into pattern_approvals.

        Args:
            pattern_data: Dictionary with pattern fields:
                - pattern_id: Unique pattern identifier
                - status: Pattern status (pending, auto-approved, auto-rejected)
                - tool_sequence: Sequence of tools (e.g., "Read→Edit→Write")
                - confidence_score: Confidence score (0.0 to 1.0)
                - occurrence_count: Number of times pattern appeared
                - estimated_savings_usd: Estimated cost savings
                - pattern_context: Description of the pattern
                - example_sessions: List of session IDs

        Returns:
            pattern_id of created pattern
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self.adapter.placeholder()

            cursor.execute(
                f"""
                INSERT INTO pattern_approvals
                    (pattern_id, status, tool_sequence, confidence_score,
                     occurrence_count, estimated_savings_usd, pattern_context,
                     example_sessions)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
                (
                    pattern_data['pattern_id'],
                    pattern_data['status'],
                    pattern_data['tool_sequence'],
                    pattern_data['confidence_score'],
                    pattern_data['occurrence_count'],
                    pattern_data['estimated_savings_usd'],
                    pattern_data['pattern_context'],
                    json.dumps(pattern_data['example_sessions'])
                ),
            )

            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Created pattern {pattern_data['pattern_id']}"
            )
            return pattern_data['pattern_id']

    def update_occurrence_count(self, pattern_id: str, new_count: int) -> bool:
        """
        Update occurrence count for existing pattern.

        Args:
            pattern_id: Pattern identifier
            new_count: New occurrence count

        Returns:
            True if updated successfully, False if pattern not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = self.adapter.placeholder()

            cursor.execute(
                f"""
                UPDATE pattern_approvals
                SET occurrence_count = {placeholder}
                WHERE pattern_id = {placeholder}
            """,
                (new_count, pattern_id),
            )

            if cursor.rowcount == 0:
                logger.warning(
                    f"[{self.__class__.__name__}] Pattern not found: {pattern_id}"
                )
                return False

            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Updated occurrence count for pattern {pattern_id}: {new_count}"
            )
            return True

    def update_confidence_score(
        self,
        pattern_id: str,
        new_confidence: float,
        reason: str,
        roi_data: Optional[Dict] = None
    ) -> bool:
        """
        Update pattern confidence score and log to history (Session 13).

        Args:
            pattern_id: Pattern identifier
            new_confidence: New confidence score (0.0-1.0)
            reason: Explanation for the adjustment
            roi_data: Optional ROI performance snapshot (JSON)

        Returns:
            True if updated successfully, False otherwise
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get current confidence
            placeholder = self.adapter.placeholder()
            cursor.execute(
                f"""
                SELECT confidence_score FROM pattern_approvals
                WHERE pattern_id = {placeholder}
            """,
                (pattern_id,),
            )

            row = cursor.fetchone()
            if not row:
                logger.warning(
                    f"[{self.__class__.__name__}] Pattern not found: {pattern_id}"
                )
                return False

            old_confidence = row['confidence_score']

            # Update pattern_approvals
            cursor.execute(
                f"""
                UPDATE pattern_approvals
                SET confidence_score = {placeholder},
                    updated_at = CURRENT_TIMESTAMP
                WHERE pattern_id = {placeholder}
            """,
                (new_confidence, pattern_id),
            )

            # Log to confidence history
            roi_data_json = json.dumps(roi_data) if roi_data else json.dumps({})
            cursor.execute(
                f"""
                INSERT INTO pattern_confidence_history (
                    pattern_id, old_confidence, new_confidence,
                    adjustment_reason, roi_data, updated_by
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
                (
                    pattern_id,
                    old_confidence,
                    new_confidence,
                    reason,
                    roi_data_json,
                    'system',
                ),
            )

            conn.commit()

            logger.info(
                f"[{self.__class__.__name__}] Updated confidence for pattern {pattern_id}: "
                f"{old_confidence:.3f} -> {new_confidence:.3f} ({new_confidence - old_confidence:+.3f})"
            )
            return True

    def _row_to_model(self, row) -> PatternReviewItem:
        """
        Convert PostgreSQL database row to PatternReviewItem model.

        Args:
            row: PostgreSQL RealDictCursor dict row

        Returns:
            PatternReviewItem object
        """
        if not row:
            return None

        # PostgreSQL with RealDictCursor returns dict rows
        example_sessions_raw = row.get('example_sessions')

        # Parse example_sessions JSON if present and if it's a string
        example_sessions = None
        if example_sessions_raw:
            if isinstance(example_sessions_raw, str):
                try:
                    example_sessions = json.loads(example_sessions_raw)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        f"[{self.__class__.__name__}] Failed to parse example_sessions for pattern {row.get('pattern_id')}"
                    )
                    example_sessions = []
            else:
                # Already parsed by PostgreSQL (JSON/JSONB column)
                example_sessions = example_sessions_raw

        return PatternReviewItem(
            id=row.get('id'),
            pattern_id=row.get('pattern_id'),
            status=row.get('status'),
            reviewed_by=row.get('reviewed_by'),
            reviewed_at=str(row.get('reviewed_at')) if row.get('reviewed_at') else None,
            approval_notes=row.get('approval_notes'),
            confidence_score=row.get('confidence_score'),
            occurrence_count=row.get('occurrence_count'),
            estimated_savings_usd=row.get('estimated_savings_usd'),
            tool_sequence=row.get('tool_sequence'),
            pattern_context=row.get('pattern_context'),
            example_sessions=example_sessions,
            created_at=str(row.get('created_at')) if row.get('created_at') else None,
            updated_at=str(row.get('updated_at')) if row.get('updated_at') else None,
        )
