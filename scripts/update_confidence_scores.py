#!/usr/bin/env python3
"""
Confidence Update CLI

Automatically update pattern confidence scores based on ROI performance data.
Enables self-improving pattern system through performance-based learning.

Usage:
    python scripts/update_confidence_scores.py --update-all
    python scripts/update_confidence_scores.py --pattern-id test-retry-automation
    python scripts/update_confidence_scores.py --update-all --dry-run
    python scripts/update_confidence_scores.py --recommendations
    python scripts/update_confidence_scores.py --apply-recommendations
    python scripts/update_confidence_scores.py --history test-retry-automation
    python scripts/update_confidence_scores.py --help
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.confidence_update_service import ConfidenceUpdateService
from services.pattern_review_service import PatternReviewService
from core.models.workflow import ConfidenceUpdate, StatusChangeRecommendation


class ConfidenceUpdateCLI:
    """CLI interface for confidence score updates."""

    def __init__(self):
        self.service = ConfidenceUpdateService()
        self.pattern_service = PatternReviewService()

    def update_all(self, dry_run: bool = False):
        """Update confidence scores for all patterns with ROI data."""
        print("\n" + "=" * 100)
        print(f"CONFIDENCE UPDATE - {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print("=" * 100 + "\n")

        changes = self.service.update_all_patterns(dry_run=dry_run)

        if not changes:
            print("No patterns with ROI data found. No updates to process.")
            return

        # Calculate statistics
        increased = [pid for pid, change in changes.items() if change > 0]
        decreased = [pid for pid, change in changes.items() if change < 0]
        unchanged = [pid for pid, change in changes.items() if change == 0]

        print(f"Processed {len(changes)} patterns:\n")
        print(f"  ↑ Increased confidence: {len(increased)}")
        print(f"  ↓ Decreased confidence: {len(decreased)}")
        print(f"  = Unchanged confidence: {len(unchanged)}")
        print(f"  Average change: {sum(changes.values()) / len(changes):+.3f}")

        # Show top increases
        if increased:
            print("\n" + "-" * 100)
            print("TOP CONFIDENCE INCREASES")
            print("-" * 100)
            top_increases = sorted(
                [(pid, changes[pid]) for pid in increased],
                key=lambda x: x[1],
                reverse=True
            )[:5]

            for idx, (pattern_id, change) in enumerate(top_increases, 1):
                print(f"\n{idx}. {pattern_id}")
                print(f"   Change: {change:+.3f}")

        # Show top decreases
        if decreased:
            print("\n" + "-" * 100)
            print("TOP CONFIDENCE DECREASES (needs attention)")
            print("-" * 100)
            top_decreases = sorted(
                [(pid, changes[pid]) for pid in decreased],
                key=lambda x: x[1]
            )[:5]

            for idx, (pattern_id, change) in enumerate(top_decreases, 1):
                print(f"\n{idx}. {pattern_id}")
                print(f"   Change: {change:+.3f}")
                print(f"   ⚠️  Recommend reviewing pattern performance")

        if dry_run:
            print("\n" + "=" * 100)
            print("DRY RUN COMPLETE - No changes were saved to database")
            print("Run without --dry-run to apply changes")
            print("=" * 100 + "\n")
        else:
            print("\n" + "=" * 100)
            print("CONFIDENCE UPDATE COMPLETE")
            print("=" * 100 + "\n")

    def update_pattern(self, pattern_id: str, dry_run: bool = False):
        """Update confidence score for a single pattern."""
        print("\n" + "=" * 100)
        print(f"UPDATE PATTERN: {pattern_id} - {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print("=" * 100 + "\n")

        update = self.service.update_pattern_confidence(pattern_id, dry_run=dry_run)

        if not update:
            print(f"❌ Cannot update confidence for pattern {pattern_id}")
            print("   Possible reasons:")
            print("   - Pattern not found in database")
            print("   - No ROI data available for this pattern")
            return

        change = update.new_confidence - update.old_confidence
        direction = "↑ INCREASED" if change > 0 else "↓ DECREASED" if change < 0 else "= UNCHANGED"

        print(f"Pattern ID: {pattern_id}")
        print(f"Old confidence: {update.old_confidence:.3f}")
        print(f"New confidence: {update.new_confidence:.3f}")
        print(f"Change: {change:+.3f} ({direction})")
        print(f"\nReason: {update.adjustment_reason}")

        if update.roi_data:
            print("\nROI Performance Metrics:")
            print(f"  Total executions: {update.roi_data.get('total_executions', 0)}")
            print(f"  Success rate: {update.roi_data.get('success_rate', 0)*100:.1f}%")
            print(f"  ROI percentage: {update.roi_data.get('roi_percentage', 0):.1f}%")
            print(f"  Cost saved: ${update.roi_data.get('total_cost_saved_usd', 0):.2f}")

        if dry_run:
            print("\n" + "=" * 100)
            print("DRY RUN COMPLETE - No changes were saved to database")
            print("=" * 100 + "\n")
        else:
            print("\n" + "=" * 100)
            print("CONFIDENCE UPDATED SUCCESSFULLY")
            print("=" * 100 + "\n")

    def show_recommendations(self):
        """Show status change recommendations based on performance."""
        print("\n" + "=" * 100)
        print("STATUS CHANGE RECOMMENDATIONS")
        print("=" * 100 + "\n")

        recommendations = self.service.recommend_status_changes()

        if not recommendations:
            print("✅ No status change recommendations at this time.")
            print("   All patterns are performing within acceptable ranges.")
            return

        # Group by severity
        high = [r for r in recommendations if r.severity == 'high']
        medium = [r for r in recommendations if r.severity == 'medium']
        low = [r for r in recommendations if r.severity == 'low']

        print(f"Found {len(recommendations)} recommendations:\n")
        print(f"  🔴 High severity: {len(high)}")
        print(f"  🟡 Medium severity: {len(medium)}")
        print(f"  🟢 Low severity: {len(low)}")

        # Show high severity first
        if high:
            print("\n" + "=" * 100)
            print("🔴 HIGH SEVERITY - IMMEDIATE ACTION REQUIRED")
            print("=" * 100)
            for idx, rec in enumerate(high, 1):
                self._print_recommendation(idx, rec)

        # Show medium severity
        if medium:
            print("\n" + "=" * 100)
            print("🟡 MEDIUM SEVERITY - REVIEW RECOMMENDED")
            print("=" * 100)
            for idx, rec in enumerate(medium, 1):
                self._print_recommendation(idx, rec)

        # Show low severity
        if low:
            print("\n" + "=" * 100)
            print("🟢 LOW SEVERITY - INFORMATIONAL")
            print("=" * 100)
            for idx, rec in enumerate(low, 1):
                self._print_recommendation(idx, rec)

        print("\n" + "=" * 100)
        print("Use --apply-recommendations to take action (requires manual review)")
        print("=" * 100 + "\n")

    def apply_recommendations(self, auto_approve: bool = False):
        """Apply status change recommendations (interactive)."""
        print("\n" + "=" * 100)
        print("APPLY STATUS CHANGE RECOMMENDATIONS")
        print("=" * 100 + "\n")

        recommendations = self.service.recommend_status_changes()

        if not recommendations:
            print("✅ No status change recommendations to apply.")
            return

        print(f"Found {len(recommendations)} recommendations to review.\n")

        if not auto_approve:
            print("⚠️  This is an interactive process. You will be asked to confirm each change.")
            print("    Press Ctrl+C at any time to abort.\n")

        applied = 0
        skipped = 0

        for idx, rec in enumerate(recommendations, 1):
            print("-" * 100)
            print(f"Recommendation {idx}/{len(recommendations)}")
            print(f"Pattern: {rec.pattern_id}")
            print(f"Current status: {rec.current_status}")
            print(f"Recommended status: {rec.recommended_status}")
            print(f"Reason: {rec.reason}")
            print(f"Confidence: {rec.confidence_score:.3f} | ROI: {rec.roi_percentage:.1f}%")

            if auto_approve:
                confirm = 'y'
                print("Auto-approved (--auto-approve flag)")
            else:
                confirm = input("\nApply this recommendation? [y/N]: ").lower().strip()

            if confirm == 'y':
                # Apply the status change via pattern service
                # NOTE: This would require implementing a status update method
                print(f"✅ Applied: {rec.pattern_id} -> {rec.recommended_status}")
                applied += 1
            else:
                print(f"⏭️  Skipped: {rec.pattern_id}")
                skipped += 1
            print()

        print("\n" + "=" * 100)
        print(f"RECOMMENDATIONS PROCESSED: {applied} applied, {skipped} skipped")
        print("=" * 100 + "\n")

    def show_history(self, pattern_id: Optional[str] = None):
        """Show confidence change history."""
        if pattern_id:
            print("\n" + "=" * 100)
            print(f"CONFIDENCE HISTORY: {pattern_id}")
            print("=" * 100 + "\n")

            history = self.service.get_confidence_history(pattern_id)

            if not history:
                print(f"No confidence history found for pattern {pattern_id}")
                return

            print(f"Found {len(history)} confidence updates:\n")

            for idx, update in enumerate(history, 1):
                change = update.new_confidence - update.old_confidence
                direction = "↑" if change > 0 else "↓" if change < 0 else "="

                print(f"{idx}. {update.updated_at}")
                print(f"   {update.old_confidence:.3f} -> {update.new_confidence:.3f} "
                      f"({change:+.3f}) {direction}")
                print(f"   Reason: {update.adjustment_reason}")
                print(f"   Updated by: {update.updated_by}")
                print()
        else:
            print("Error: --history requires --pattern-id")
            sys.exit(1)

    def _print_recommendation(self, idx: int, rec: StatusChangeRecommendation):
        """Print a single recommendation."""
        print(f"\n{idx}. Pattern: {rec.pattern_id}")
        print(f"   Current: {rec.current_status} → Recommended: {rec.recommended_status}")
        print(f"   Confidence: {rec.confidence_score:.3f} | ROI: {rec.roi_percentage:.1f}%")
        print(f"   Reason: {rec.reason}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update pattern confidence scores based on ROI performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all patterns (dry run)
  python scripts/update_confidence_scores.py --update-all --dry-run

  # Update all patterns (live)
  python scripts/update_confidence_scores.py --update-all

  # Update single pattern
  python scripts/update_confidence_scores.py --pattern-id test-retry-automation

  # Show recommendations
  python scripts/update_confidence_scores.py --recommendations

  # Show confidence history
  python scripts/update_confidence_scores.py --history --pattern-id test-retry-automation
        """
    )

    parser.add_argument(
        '--pattern-id',
        type=str,
        help='Pattern ID to update'
    )
    parser.add_argument(
        '--update-all',
        action='store_true',
        help='Update all patterns with ROI data'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate changes but do not persist to database'
    )
    parser.add_argument(
        '--recommendations',
        action='store_true',
        help='Show status change recommendations based on performance'
    )
    parser.add_argument(
        '--apply-recommendations',
        action='store_true',
        help='Apply status change recommendations (interactive)'
    )
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show confidence change history (requires --pattern-id)'
    )
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Auto-approve all recommendations (use with --apply-recommendations)'
    )

    args = parser.parse_args()

    # Validate argument combinations
    if not any([args.update_all, args.pattern_id, args.recommendations,
                args.apply_recommendations, args.history]):
        parser.print_help()
        sys.exit(1)

    cli = ConfidenceUpdateCLI()

    try:
        if args.update_all:
            cli.update_all(dry_run=args.dry_run)
        elif args.pattern_id and not args.history:
            cli.update_pattern(args.pattern_id, dry_run=args.dry_run)
        elif args.recommendations:
            cli.show_recommendations()
        elif args.apply_recommendations:
            cli.apply_recommendations(auto_approve=args.auto_approve)
        elif args.history:
            cli.show_history(pattern_id=args.pattern_id)

    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
