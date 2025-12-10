#!/usr/bin/env python3
"""
Confidence Update Service

Business logic for automatic confidence score updates based on ROI performance.

Responsibilities:
- Calculate confidence adjustments from ROI data
- Update pattern confidence scores dynamically
- Track confidence change history
- Recommend status changes based on performance
- Enable self-improving pattern system
"""

import json
import logging
from datetime import datetime

from core.models.workflow import (
    ConfidenceUpdate,
    PatternROISummary,
    StatusChangeRecommendation,
)
from database import get_database_adapter

logger = logging.getLogger(__name__)


class ConfidenceUpdateService:
    """Service for automatic confidence score updates."""

    def __init__(self):
        """Initialize ConfidenceUpdateService with database adapter."""
        self.adapter = get_database_adapter()
        logger.info("[INIT] ConfidenceUpdateService initialized")

    def calculate_confidence_adjustment(self, roi_summary: PatternROISummary) -> float:
        """
        Calculate new confidence score based on performance metrics.

        Algorithm:
        - Base confidence = success rate (0.0-1.0)
        - Bonus for high ROI: up to +0.1 for ROI >= 1000%
        - Bonus for high execution count: up to +0.05 for 1000+ executions
        - Penalty for negative ROI: -abs(roi_percentage) / 100
        - Clamped to [0.0, 1.0] range

        Args:
            roi_summary: PatternROISummary with performance metrics

        Returns:
            New confidence score (0.0 to 1.0)
        """
        # Base confidence on success rate
        base_confidence = roi_summary.success_rate

        # Bonus for high ROI (up to +0.1)
        roi_bonus = min(0.1, roi_summary.roi_percentage / 1000)

        # Bonus for high execution count (up to +0.05)
        execution_bonus = min(0.05, roi_summary.total_executions / 1000)

        # Penalty for negative ROI
        roi_penalty = 0
        if roi_summary.roi_percentage < 0:
            roi_penalty = abs(roi_summary.roi_percentage) / 100

        # Calculate new confidence
        new_confidence = base_confidence + roi_bonus + execution_bonus - roi_penalty

        # Clamp to [0.0, 1.0]
        clamped_confidence = max(0.0, min(1.0, new_confidence))

        logger.debug(
            f"[ConfidenceUpdateService] Calculated confidence for pattern: "
            f"base={base_confidence:.3f}, roi_bonus={roi_bonus:.3f}, "
            f"exec_bonus={execution_bonus:.3f}, penalty={roi_penalty:.3f}, "
            f"final={clamped_confidence:.3f}"
        )

        return clamped_confidence

    def update_pattern_confidence(
        self,
        pattern_id: str,
        dry_run: bool = False
    ) -> ConfidenceUpdate | None:
        """
        Update confidence score for a single pattern based on ROI data.

        Args:
            pattern_id: Pattern identifier to update
            dry_run: If True, calculate but don't persist changes

        Returns:
            ConfidenceUpdate object with change details, or None if no ROI data
        """
        # Get ROI data
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_roi_summary
                WHERE pattern_id = %s
                """,
                (pattern_id,)
            )

            roi_row = cursor.fetchone()
            if not roi_row:
                logger.warning(
                    f"[ConfidenceUpdateService] No ROI data for pattern {pattern_id}, "
                    f"cannot update confidence"
                )
                return None

            # Convert to model
            roi_summary = PatternROISummary(
                pattern_id=roi_row['pattern_id'],
                total_executions=roi_row['total_executions'],
                successful_executions=roi_row['successful_executions'],
                success_rate=roi_row['success_rate'],
                total_time_saved_seconds=roi_row['total_time_saved_seconds'],
                total_cost_saved_usd=roi_row['total_cost_saved_usd'],
                average_time_saved_seconds=roi_row['average_time_saved_seconds'],
                average_cost_saved_usd=roi_row['average_cost_saved_usd'],
                roi_percentage=roi_row['roi_percentage'],
                last_updated=roi_row['last_updated'].isoformat() if roi_row['last_updated'] else None
            )

            # Get current confidence
            cursor.execute(
                """
                SELECT confidence_score FROM pattern_approvals
                WHERE pattern_id = %s
                """,
                (pattern_id,)
            )

            pattern_row = cursor.fetchone()
            if not pattern_row:
                logger.warning(
                    f"[ConfidenceUpdateService] Pattern {pattern_id} not found in approvals"
                )
                return None

            old_confidence = pattern_row['confidence_score']

            # Calculate new confidence
            new_confidence = self.calculate_confidence_adjustment(roi_summary)

            # Generate adjustment reason
            adjustment_reason = self._generate_adjustment_reason(roi_summary, old_confidence, new_confidence)

            # Store ROI snapshot
            roi_data = {
                'total_executions': roi_summary.total_executions,
                'success_rate': roi_summary.success_rate,
                'roi_percentage': roi_summary.roi_percentage,
                'total_cost_saved_usd': roi_summary.total_cost_saved_usd
            }

            if not dry_run:
                # Update pattern_approvals
                cursor.execute(
                    """
                    UPDATE pattern_approvals
                    SET confidence_score = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE pattern_id = %s
                    """,
                    (new_confidence, pattern_id)
                )

                # Log to confidence history
                cursor.execute(
                    """
                    INSERT INTO pattern_confidence_history (
                        pattern_id, old_confidence, new_confidence,
                        adjustment_reason, roi_data, updated_by
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        pattern_id,
                        old_confidence,
                        new_confidence,
                        adjustment_reason,
                        json.dumps(roi_data),
                        'system'
                    )
                )

                update_id = cursor.fetchone()['id']
                conn.commit()

                logger.info(
                    f"[ConfidenceUpdateService] Updated confidence for pattern {pattern_id}: "
                    f"{old_confidence:.3f} -> {new_confidence:.3f} (change: {new_confidence - old_confidence:+.3f})"
                )
            else:
                update_id = None
                logger.info(
                    f"[ConfidenceUpdateService] [DRY RUN] Would update pattern {pattern_id}: "
                    f"{old_confidence:.3f} -> {new_confidence:.3f} (change: {new_confidence - old_confidence:+.3f})"
                )

            return ConfidenceUpdate(
                id=update_id,
                pattern_id=pattern_id,
                old_confidence=old_confidence,
                new_confidence=new_confidence,
                adjustment_reason=adjustment_reason,
                roi_data=roi_data,
                updated_by='system',
                updated_at=datetime.utcnow().isoformat() if not dry_run else None
            )

    def update_all_patterns(self, dry_run: bool = False) -> dict[str, float]:
        """
        Update confidence scores for all patterns with ROI data.

        Args:
            dry_run: If True, calculate but don't persist changes

        Returns:
            Dictionary mapping pattern_id to confidence change
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all patterns with ROI data
            cursor.execute(
                """
                SELECT DISTINCT pattern_id FROM pattern_roi_summary
                """
            )

            pattern_ids = [row['pattern_id'] for row in cursor.fetchall()]

            logger.info(
                f"[ConfidenceUpdateService] Updating confidence for {len(pattern_ids)} patterns "
                f"(dry_run={dry_run})"
            )

        # Update each pattern
        changes = {}
        for pattern_id in pattern_ids:
            update = self.update_pattern_confidence(pattern_id, dry_run=dry_run)
            if update:
                change = update.new_confidence - update.old_confidence
                changes[pattern_id] = change

        logger.info(
            f"[ConfidenceUpdateService] Completed batch update: "
            f"{len(changes)} patterns updated, "
            f"average change: {sum(changes.values()) / len(changes):+.3f}" if changes else "0"
        )

        return changes

    def get_confidence_history(
        self,
        pattern_id: str,
        limit: int = 50
    ) -> list[ConfidenceUpdate]:
        """
        Get confidence change history for a pattern.

        Args:
            pattern_id: Pattern identifier
            limit: Maximum number of records to return

        Returns:
            List of ConfidenceUpdate objects ordered by date (newest first)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_confidence_history
                WHERE pattern_id = %s
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (pattern_id, limit)
            )

            rows = cursor.fetchall()
            history = []

            for row in rows:
                # Parse ROI data JSON
                roi_data = json.loads(row['roi_data']) if row['roi_data'] else {}

                history.append(ConfidenceUpdate(
                    id=row['id'],
                    pattern_id=row['pattern_id'],
                    old_confidence=row['old_confidence'],
                    new_confidence=row['new_confidence'],
                    adjustment_reason=row['adjustment_reason'],
                    roi_data=roi_data,
                    updated_by=row['updated_by'],
                    updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                ))

            logger.info(
                f"[ConfidenceUpdateService] Retrieved {len(history)} confidence history records "
                f"for pattern {pattern_id}"
            )

            return history

    def recommend_status_changes(self) -> list[StatusChangeRecommendation]:
        """
        Recommend status changes based on performance data.

        Recommendations:
        - Reject approved patterns with poor performance (< 70% success or negative ROI)
        - Auto-approve pending patterns with excellent performance (> 95% success and > 200% ROI)
        - Flag patterns for manual review based on trends

        Returns:
            List of StatusChangeRecommendation objects
        """
        recommendations = []

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all patterns with status and ROI data
            cursor.execute(
                """
                SELECT
                    pa.pattern_id,
                    pa.status,
                    pa.confidence_score,
                    rs.success_rate,
                    rs.roi_percentage,
                    rs.total_executions
                FROM pattern_approvals pa
                INNER JOIN pattern_roi_summary rs ON pa.pattern_id = rs.pattern_id
                WHERE rs.total_executions >= 3
                """
            )

            rows = cursor.fetchall()

            for row in rows:
                pattern_id = row['pattern_id']
                status = row['status']
                confidence = row['confidence_score']
                success_rate = row['success_rate']
                roi_percentage = row['roi_percentage']
                total_executions = row['total_executions']

                # Recommend rejection for poor performers (if currently approved)
                if status == 'approved' and (success_rate < 0.7 or roi_percentage < 0):
                    recommendations.append(StatusChangeRecommendation(
                        pattern_id=pattern_id,
                        current_status='approved',
                        recommended_status='rejected',
                        reason=(
                            f'Low performance: {success_rate*100:.1f}% success rate, '
                            f'{roi_percentage:.1f}% ROI over {total_executions} executions. '
                            f'Consider revocation or pattern refinement.'
                        ),
                        severity='high',
                        confidence_score=confidence,
                        roi_percentage=roi_percentage
                    ))

                # Recommend auto-approval for excellent performers (if pending)
                elif status == 'pending' and success_rate > 0.95 and roi_percentage > 200:
                    recommendations.append(StatusChangeRecommendation(
                        pattern_id=pattern_id,
                        current_status='pending',
                        recommended_status='auto-approved',
                        reason=(
                            f'Excellent performance: {success_rate*100:.1f}% success rate, '
                            f'{roi_percentage:.1f}% ROI over {total_executions} executions. '
                            f'Strong candidate for auto-approval.'
                        ),
                        severity='medium',
                        confidence_score=confidence,
                        roi_percentage=roi_percentage
                    ))

                # Flag borderline performers for manual review
                elif status == 'approved' and (0.7 <= success_rate < 0.8 or 0 <= roi_percentage < 50):
                    recommendations.append(StatusChangeRecommendation(
                        pattern_id=pattern_id,
                        current_status='approved',
                        recommended_status='manual-review',
                        reason=(
                            f'Borderline performance: {success_rate*100:.1f}% success rate, '
                            f'{roi_percentage:.1f}% ROI over {total_executions} executions. '
                            f'Recommend manual review to assess continued approval.'
                        ),
                        severity='low',
                        confidence_score=confidence,
                        roi_percentage=roi_percentage
                    ))

        logger.info(
            f"[ConfidenceUpdateService] Generated {len(recommendations)} status change recommendations"
        )

        return recommendations

    def _generate_adjustment_reason(
        self,
        roi_summary: PatternROISummary,
        old_confidence: float,
        new_confidence: float
    ) -> str:
        """Generate human-readable reason for confidence adjustment."""
        change = new_confidence - old_confidence
        direction = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"

        return (
            f"Confidence {direction} by {abs(change):.3f} based on performance: "
            f"{roi_summary.total_executions} executions, "
            f"{roi_summary.success_rate*100:.1f}% success rate, "
            f"{roi_summary.roi_percentage:.1f}% ROI"
        )
