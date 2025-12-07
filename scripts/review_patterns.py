#!/usr/bin/env python3
"""
Pattern Review CLI

Interactive command-line interface for reviewing and approving automation patterns.

Usage:
    python scripts/review_patterns.py --stats
    python scripts/review_patterns.py --pattern-id test-pattern-1
    python scripts/review_patterns.py --limit 10
    python scripts/review_patterns.py --help
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from services.pattern_review_service import (
    PatternReviewItem,
    PatternReviewService,
)


class PatternReviewCLI:
    """CLI interface for pattern review."""

    def __init__(self, reviewer_name: str = "cli-reviewer"):
        """
        Initialize CLI.

        Args:
            reviewer_name: Name of the reviewer (default: cli-reviewer)
        """
        self.service = PatternReviewService()
        self.reviewer_name = reviewer_name

    def show_statistics(self):
        """Display review statistics."""
        stats = self.service.get_review_statistics()

        print("\n" + "=" * 80)
        print("PATTERN REVIEW STATISTICS")
        print("=" * 80)

        # Calculate totals
        total = sum(stats.values())
        print(f"Total Patterns: {total}\n")

        # Display by status
        for status in ["pending", "approved", "rejected", "auto-approved", "auto-rejected"]:
            count = stats.get(status, 0)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {status.upper():15s}: {count:4d} ({percentage:5.1f}%)")

        print("=" * 80 + "\n")

    def display_pattern(self, pattern: PatternReviewItem, detailed: bool = False):
        """
        Display pattern details.

        Args:
            pattern: Pattern to display
            detailed: Show full detailed view
        """
        print("\n" + "─" * 80)
        print(f"Pattern ID: {pattern.pattern_id}")
        print("─" * 80)
        print(f"Status:          {pattern.status}")
        print(f"Tool Sequence:   {pattern.tool_sequence}")
        print(f"Confidence:      {pattern.confidence_score:.1%}")
        print(f"Occurrences:     {pattern.occurrence_count}")
        print(f"Est. Savings:    ${pattern.estimated_savings_usd:,.2f}")
        print(f"Impact Score:    {pattern.impact_score:,.2f}")

        if pattern.pattern_context:
            print(f"\nContext:")
            print(f"  {pattern.pattern_context}")

        if pattern.example_sessions:
            print(f"\nExample Sessions ({len(pattern.example_sessions)}):")
            for session in pattern.example_sessions[:5]:  # Show first 5
                print(f"  - {session}")
            if len(pattern.example_sessions) > 5:
                print(f"  ... and {len(pattern.example_sessions) - 5} more")

        if pattern.reviewed_by:
            print(f"\nReviewed By:     {pattern.reviewed_by}")
            print(f"Reviewed At:     {pattern.reviewed_at}")
            if pattern.approval_notes:
                print(f"Notes:           {pattern.approval_notes}")

        if detailed:
            print(f"\nFull JSON:")
            print(json.dumps(pattern.to_dict(), indent=2))

        print("─" * 80)

    def review_pattern_interactive(self, pattern: PatternReviewItem) -> str:
        """
        Review pattern interactively.

        Args:
            pattern: Pattern to review

        Returns:
            Action taken: 'approved', 'rejected', 'skip', 'quit'
        """
        self.display_pattern(pattern)

        print("\nActions:")
        print("  [a] Approve pattern")
        print("  [r] Reject pattern")
        print("  [s] Skip to next")
        print("  [d] Show full details")
        print("  [q] Quit review session")

        while True:
            choice = input("\nYour choice: ").lower().strip()

            if choice == "a":
                # Approve pattern
                notes = input("Approval notes (optional): ").strip()
                notes = notes if notes else None

                result = self.service.approve_pattern(
                    pattern.pattern_id, self.reviewer_name, notes
                )
                if result:
                    print(f"✅ Pattern {pattern.pattern_id} APPROVED")
                    return "approved"
                else:
                    print(f"❌ Failed to approve pattern")
                    return "skip"

            elif choice == "r":
                # Reject pattern (reason required)
                reason = input("Rejection reason (required): ").strip()
                while not reason:
                    print("⚠️  Reason is required for rejection")
                    reason = input("Rejection reason: ").strip()

                result = self.service.reject_pattern(
                    pattern.pattern_id, self.reviewer_name, reason
                )
                if result:
                    print(f"❌ Pattern {pattern.pattern_id} REJECTED")
                    return "rejected"
                else:
                    print(f"❌ Failed to reject pattern")
                    return "skip"

            elif choice == "s":
                # Skip
                print("⏭️  Skipping to next pattern")
                return "skip"

            elif choice == "d":
                # Show full details
                self.display_pattern(pattern, detailed=True)
                print("\nActions: [a]pprove, [r]eject, [s]kip, [q]uit")

            elif choice == "q":
                # Quit
                print("👋 Exiting review session")
                return "quit"

            else:
                print("❓ Invalid choice. Please choose: a, r, s, d, or q")

    def review_all_pending(self, limit: int = 20):
        """
        Review all pending patterns interactively.

        Args:
            limit: Maximum number of patterns to review
        """
        patterns = self.service.get_pending_patterns(limit=limit)

        if not patterns:
            print("\n✨ No pending patterns to review!")
            return

        print(f"\n📋 Found {len(patterns)} pending pattern(s) to review")
        print(f"👤 Reviewer: {self.reviewer_name}\n")

        approved_count = 0
        rejected_count = 0
        skipped_count = 0

        for i, pattern in enumerate(patterns, 1):
            print(f"\n{'=' * 80}")
            print(f"Pattern {i} of {len(patterns)}")
            print(f"{'=' * 80}")

            action = self.review_pattern_interactive(pattern)

            if action == "approved":
                approved_count += 1
            elif action == "rejected":
                rejected_count += 1
            elif action == "skip":
                skipped_count += 1
            elif action == "quit":
                break

        # Summary
        print("\n" + "=" * 80)
        print("REVIEW SESSION SUMMARY")
        print("=" * 80)
        print(f"Reviewed:  {i} of {len(patterns)} patterns")
        print(f"Approved:  {approved_count}")
        print(f"Rejected:  {rejected_count}")
        print(f"Skipped:   {skipped_count}")
        print("=" * 80 + "\n")

    def review_single_pattern(self, pattern_id: str):
        """
        Review a specific pattern by ID.

        Args:
            pattern_id: Pattern identifier
        """
        pattern = self.service.get_pattern_details(pattern_id)

        if not pattern:
            print(f"\n❌ Pattern not found: {pattern_id}")
            return

        print(f"\n👤 Reviewer: {self.reviewer_name}")
        action = self.review_pattern_interactive(pattern)

        if action == "quit":
            print("\n👋 Review session ended")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI for reviewing automation patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show statistics only
  python scripts/review_patterns.py --stats

  # Review specific pattern
  python scripts/review_patterns.py --pattern-id test-retry-pattern

  # Review up to 10 pending patterns
  python scripts/review_patterns.py --limit 10

  # Review with custom reviewer name
  python scripts/review_patterns.py --reviewer "Jane Smith"
        """,
    )

    # Mode arguments
    parser.add_argument(
        "--stats", action="store_true", help="Show statistics only (no review)"
    )
    parser.add_argument(
        "--pattern-id", type=str, help="Review specific pattern by ID"
    )

    # Configuration arguments
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of patterns to review (default: 20)",
    )
    parser.add_argument(
        "--reviewer",
        type=str,
        default="cli-reviewer",
        help='Reviewer name for attribution (default: "cli-reviewer")',
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Set up logging
    import logging

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level, format="[%(levelname)s] %(name)s: %(message)s"
    )

    # Initialize CLI
    cli = PatternReviewCLI(reviewer_name=args.reviewer)

    # Execute based on arguments
    try:
        if args.stats:
            cli.show_statistics()
        elif args.pattern_id:
            cli.review_single_pattern(args.pattern_id)
        else:
            cli.review_all_pending(limit=args.limit)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
