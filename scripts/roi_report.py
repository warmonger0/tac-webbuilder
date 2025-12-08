#!/usr/bin/env python3
"""
ROI Report CLI

Generate comprehensive ROI reports for automated pattern execution.
Track actual savings vs estimates and validate pattern effectiveness.

Usage:
    python scripts/roi_report.py --summary
    python scripts/roi_report.py --pattern-id test-retry-automation
    python scripts/roi_report.py --top-performers --limit 10
    python scripts/roi_report.py --underperformers --limit 10
    python scripts/roi_report.py --report --output roi_report.md
    python scripts/roi_report.py --help
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.roi_tracking_service import ROITrackingService
from core.models.workflow import PatternROISummary, ROIReport


class ROIReportCLI:
    """CLI interface for ROI tracking and reporting."""

    def __init__(self):
        self.service = ROITrackingService()

    def show_summary(self):
        """Show overall ROI summary for all patterns."""
        print("\n" + "=" * 100)
        print("PATTERN ROI SUMMARY")
        print("=" * 100 + "\n")

        summaries = self.service.get_all_roi_summaries()

        if not summaries:
            print("No ROI data available. No patterns have been executed yet.")
            return

        # Calculate overall metrics
        total_executions = sum(s.total_executions for s in summaries)
        total_successful = sum(s.successful_executions for s in summaries)
        total_time_saved = sum(s.total_time_saved_seconds for s in summaries)
        total_cost_saved = sum(s.total_cost_saved_usd for s in summaries)
        avg_success_rate = (
            sum(s.success_rate for s in summaries) / len(summaries) if summaries else 0
        )

        # Top performers
        print("TOP PERFORMERS (by ROI)")
        print("-" * 100)
        top_performers = sorted(summaries, key=lambda s: s.roi_percentage, reverse=True)[:5]

        for idx, summary in enumerate(top_performers, 1):
            rating = self._get_rating_symbol(self.service.calculate_effectiveness(summary.pattern_id))
            print(f"\n{idx}. Pattern: {summary.pattern_id}")
            print(f"   Executions: {summary.total_executions} ({summary.successful_executions} successful, "
                  f"{summary.success_rate*100:.1f}% success rate)")
            print(f"   Time saved: {summary.total_time_saved_seconds:.0f} seconds "
                  f"({summary.total_time_saved_seconds/60:.1f} minutes)")
            print(f"   Cost saved: ${summary.total_cost_saved_usd:.2f}")
            print(f"   ROI: {summary.roi_percentage:.1f}%")
            print(f"   Rating: {rating}")

        # Underperformers
        print("\n" + "=" * 100)
        print("\nUNDERPERFORMERS (needs attention)")
        print("-" * 100)

        underperformers = sorted(
            [s for s in summaries if s.total_executions >= 3],
            key=lambda s: (s.success_rate, s.roi_percentage)
        )[:5]

        if not underperformers:
            print("\nNo underperforming patterns found (all patterns performing well).")
        else:
            for idx, summary in enumerate(underperformers, 1):
                rating = self._get_rating_symbol(self.service.calculate_effectiveness(summary.pattern_id))
                effectiveness = self.service.calculate_effectiveness(summary.pattern_id)

                print(f"\n{idx}. Pattern: {summary.pattern_id}")
                print(f"   Executions: {summary.total_executions} ({summary.successful_executions} successful, "
                      f"{summary.success_rate*100:.1f}% success rate)")
                print(f"   Time saved: {summary.total_time_saved_seconds:.0f} seconds "
                      f"({summary.total_time_saved_seconds/60:.1f} minutes)")
                print(f"   Cost saved: ${summary.total_cost_saved_usd:.2f}")
                print(f"   ROI: {summary.roi_percentage:.1f}%")
                print(f"   Rating: {rating}")

                if effectiveness in ['poor', 'failed']:
                    print(f"   ⚠️  RECOMMENDATION: Review pattern logic or consider revocation")

        # Overall metrics
        print("\n" + "=" * 100)
        print("\nOVERALL METRICS")
        print("-" * 100)
        print(f"Total patterns tracked: {len(summaries)}")
        print(f"Total executions: {total_executions}")
        print(f"Total successful executions: {total_successful}")
        print(f"Total time saved: {total_time_saved:.0f} seconds ({total_time_saved/3600:.2f} hours)")
        print(f"Total cost saved: ${total_cost_saved:.2f}")
        print(f"Average success rate: {avg_success_rate*100:.1f}%")
        print("=" * 100 + "\n")

    def show_pattern_report(self, pattern_id: str):
        """Show detailed report for a specific pattern."""
        print("\n" + "=" * 100)
        print(f"ROI REPORT: {pattern_id}")
        print("=" * 100 + "\n")

        report = self.service.get_roi_report(pattern_id)

        if not report:
            print(f"No ROI data found for pattern: {pattern_id}")
            print("This pattern may not have been executed yet or doesn't exist.")
            return

        # Pattern metadata
        print("PATTERN DETAILS")
        print("-" * 100)
        print(f"Pattern ID: {report.pattern_id}")
        print(f"Pattern Name: {report.pattern_name}")
        print(f"Approval Date: {report.approval_date}")
        print(f"Effectiveness Rating: {report.effectiveness_rating.upper()} {self._get_rating_symbol(report.effectiveness_rating)}")
        print()

        # ROI Summary
        summary = report.summary
        print("ROI METRICS")
        print("-" * 100)
        print(f"Total Executions: {summary.total_executions}")
        print(f"Successful Executions: {summary.successful_executions}")
        print(f"Success Rate: {summary.success_rate*100:.1f}%")
        print(f"Total Time Saved: {summary.total_time_saved_seconds:.0f} seconds "
              f"({summary.total_time_saved_seconds/60:.1f} minutes)")
        print(f"Average Time Saved: {summary.average_time_saved_seconds:.1f} seconds per execution")
        print(f"Total Cost Saved: ${summary.total_cost_saved_usd:.2f}")
        print(f"Average Cost Saved: ${summary.average_cost_saved_usd:.2f} per execution")
        print(f"ROI Percentage: {summary.roi_percentage:.1f}%")
        print()

        # Recent executions
        print("RECENT EXECUTIONS (last 10)")
        print("-" * 100)
        print(f"{'Date':<20} {'Success':<10} {'Time (s)':<12} {'Cost ($)':<12} {'Savings ($)':<12}")
        print("-" * 100)

        recent_executions = report.executions[:10]
        for execution in recent_executions:
            success_str = "✓ Success" if execution.success else "✗ Failed"
            time_saved = execution.estimated_time_seconds - execution.execution_time_seconds
            cost_saved = execution.estimated_cost - execution.actual_cost

            exec_date = execution.executed_at[:19] if execution.executed_at else "N/A"

            print(f"{exec_date:<20} {success_str:<10} {execution.execution_time_seconds:<12.1f} "
                  f"${execution.actual_cost:<11.2f} ${cost_saved:<11.2f}")

        if len(report.executions) > 10:
            print(f"\n... and {len(report.executions) - 10} more executions")

        print()

        # Recommendation
        print("RECOMMENDATION")
        print("-" * 100)
        print(report.recommendation)
        print()
        print("=" * 100 + "\n")

    def show_top_performers(self, limit: int = 10):
        """Show top performing patterns."""
        print("\n" + "=" * 100)
        print(f"TOP {limit} PERFORMING PATTERNS (by ROI)")
        print("=" * 100 + "\n")

        performers = self.service.get_top_performers(limit=limit)

        if not performers:
            print("No patterns with sufficient executions found.")
            print("Patterns need at least 5 executions to be included in top performers.")
            return

        print(f"{'Rank':<6} {'Pattern ID':<35} {'Executions':<12} {'Success %':<12} "
              f"{'ROI %':<12} {'Cost Saved':<12} {'Rating':<10}")
        print("-" * 100)

        for idx, summary in enumerate(performers, 1):
            effectiveness = self.service.calculate_effectiveness(summary.pattern_id)
            rating_symbol = self._get_rating_symbol(effectiveness)

            print(f"{idx:<6} {summary.pattern_id[:33]:<35} {summary.total_executions:<12} "
                  f"{summary.success_rate*100:<11.1f}% {summary.roi_percentage:<11.1f}% "
                  f"${summary.total_cost_saved_usd:<11.2f} {rating_symbol:<10}")

        print("=" * 100 + "\n")

    def show_underperformers(self, limit: int = 10):
        """Show underperforming patterns."""
        print("\n" + "=" * 100)
        print(f"UNDERPERFORMING PATTERNS (bottom {limit})")
        print("=" * 100 + "\n")

        underperformers = self.service.get_underperformers(limit=limit)

        if not underperformers:
            print("No underperforming patterns found.")
            print("All patterns are performing well!")
            return

        print(f"{'Rank':<6} {'Pattern ID':<35} {'Executions':<12} {'Success %':<12} "
              f"{'ROI %':<12} {'Cost Impact':<12} {'Rating':<10}")
        print("-" * 100)

        for idx, summary in enumerate(underperformers, 1):
            effectiveness = self.service.calculate_effectiveness(summary.pattern_id)
            rating_symbol = self._get_rating_symbol(effectiveness)

            # For underperformers, cost could be negative
            cost_str = f"${summary.total_cost_saved_usd:.2f}"
            if summary.total_cost_saved_usd < 0:
                cost_str = f"-${abs(summary.total_cost_saved_usd):.2f}"

            print(f"{idx:<6} {summary.pattern_id[:33]:<35} {summary.total_executions:<12} "
                  f"{summary.success_rate*100:<11.1f}% {summary.roi_percentage:<11.1f}% "
                  f"{cost_str:<12} {rating_symbol:<10}")

        print("\n⚠️  ATTENTION: Review patterns with low success rates or negative ROI")
        print("=" * 100 + "\n")

    def generate_full_report(self, output_file: str):
        """Generate comprehensive markdown report."""
        print(f"\nGenerating comprehensive ROI report...")

        summaries = self.service.get_all_roi_summaries()

        if not summaries:
            print("No ROI data available. Cannot generate report.")
            return

        # Calculate overall metrics
        total_executions = sum(s.total_executions for s in summaries)
        total_successful = sum(s.successful_executions for s in summaries)
        total_time_saved = sum(s.total_time_saved_seconds for s in summaries)
        total_cost_saved = sum(s.total_cost_saved_usd for s in summaries)
        avg_success_rate = sum(s.success_rate for s in summaries) / len(summaries)

        # Build markdown report
        lines = []
        lines.append("# Pattern ROI Report")
        lines.append(f"\n**Generated:** {datetime.utcnow().isoformat()}Z\n")

        # Executive Summary
        lines.append("## Executive Summary\n")
        lines.append(f"- **Total Patterns Tracked:** {len(summaries)}")
        lines.append(f"- **Total Executions:** {total_executions}")
        lines.append(f"- **Total Successful Executions:** {total_successful}")
        lines.append(f"- **Average Success Rate:** {avg_success_rate*100:.1f}%")
        lines.append(f"- **Total Time Saved:** {total_time_saved:.0f} seconds ({total_time_saved/3600:.2f} hours)")
        lines.append(f"- **Total Cost Saved:** ${total_cost_saved:.2f}")
        lines.append("")

        # Top Performers
        lines.append("## Top Performers\n")
        lines.append("| Rank | Pattern ID | Executions | Success Rate | ROI % | Cost Saved | Rating |")
        lines.append("|------|------------|------------|--------------|-------|------------|--------|")

        top_performers = sorted(summaries, key=lambda s: s.roi_percentage, reverse=True)[:10]
        for idx, summary in enumerate(top_performers, 1):
            effectiveness = self.service.calculate_effectiveness(summary.pattern_id)
            rating_symbol = self._get_rating_symbol(effectiveness)
            lines.append(
                f"| {idx} | {summary.pattern_id} | {summary.total_executions} | "
                f"{summary.success_rate*100:.1f}% | {summary.roi_percentage:.1f}% | "
                f"${summary.total_cost_saved_usd:.2f} | {rating_symbol} |"
            )

        lines.append("")

        # Underperformers
        lines.append("## Underperformers\n")
        lines.append("| Rank | Pattern ID | Executions | Success Rate | ROI % | Cost Impact | Rating |")
        lines.append("|------|------------|------------|--------------|-------|-------------|--------|")

        underperformers = sorted(
            [s for s in summaries if s.total_executions >= 3],
            key=lambda s: (s.success_rate, s.roi_percentage)
        )[:10]

        if not underperformers:
            lines.append("| - | No underperforming patterns | - | - | - | - | - |")
        else:
            for idx, summary in enumerate(underperformers, 1):
                effectiveness = self.service.calculate_effectiveness(summary.pattern_id)
                rating_symbol = self._get_rating_symbol(effectiveness)
                cost_str = f"${summary.total_cost_saved_usd:.2f}"
                lines.append(
                    f"| {idx} | {summary.pattern_id} | {summary.total_executions} | "
                    f"{summary.success_rate*100:.1f}% | {summary.roi_percentage:.1f}% | "
                    f"{cost_str} | {rating_symbol} |"
                )

        lines.append("")

        # Detailed Pattern Reports
        lines.append("## Detailed Pattern Reports\n")

        for summary in sorted(summaries, key=lambda s: s.roi_percentage, reverse=True):
            report = self.service.get_roi_report(summary.pattern_id)
            if not report:
                continue

            lines.append(f"### {summary.pattern_id}\n")
            lines.append(f"**Effectiveness:** {report.effectiveness_rating.upper()} {self._get_rating_symbol(report.effectiveness_rating)}\n")
            lines.append("**Metrics:**")
            lines.append(f"- Executions: {summary.total_executions} (Success Rate: {summary.success_rate*100:.1f}%)")
            lines.append(f"- Time Saved: {summary.total_time_saved_seconds:.0f}s ({summary.total_time_saved_seconds/60:.1f} minutes)")
            lines.append(f"- Cost Saved: ${summary.total_cost_saved_usd:.2f}")
            lines.append(f"- ROI: {summary.roi_percentage:.1f}%")
            lines.append("")
            lines.append(f"**Recommendation:** {report.recommendation}")
            lines.append("")

        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))

        print(f"✓ Report generated: {output_file}")
        print(f"  - {len(summaries)} patterns analyzed")
        print(f"  - {total_executions} executions tracked")
        print(f"  - ${total_cost_saved:.2f} total savings")
        print()

    def _get_rating_symbol(self, effectiveness: str) -> str:
        """Get visual symbol for effectiveness rating."""
        if effectiveness == "excellent":
            return "⭐⭐⭐"
        elif effectiveness == "good":
            return "⭐⭐"
        elif effectiveness == "acceptable":
            return "⭐"
        elif effectiveness == "poor":
            return "⚠️"
        else:
            return "❌"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ROI Report CLI - Track and analyze pattern execution ROI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show overall summary
  python scripts/roi_report.py --summary

  # Show specific pattern report
  python scripts/roi_report.py --pattern-id test-retry-automation

  # Show top 10 performers
  python scripts/roi_report.py --top-performers --limit 10

  # Show underperformers
  python scripts/roi_report.py --underperformers --limit 5

  # Generate full markdown report
  python scripts/roi_report.py --report --output roi_report.md
        """
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show overall ROI summary for all patterns'
    )

    parser.add_argument(
        '--pattern-id',
        type=str,
        help='Show detailed report for specific pattern'
    )

    parser.add_argument(
        '--top-performers',
        action='store_true',
        help='Show top performing patterns by ROI'
    )

    parser.add_argument(
        '--underperformers',
        action='store_true',
        help='Show underperforming patterns'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive markdown report'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='roi_report.md',
        help='Output file for markdown report (default: roi_report.md)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of patterns to show (default: 10)'
    )

    args = parser.parse_args()

    # Create CLI instance
    cli = ROIReportCLI()

    # Execute requested action
    if args.summary:
        cli.show_summary()
    elif args.pattern_id:
        cli.show_pattern_report(args.pattern_id)
    elif args.top_performers:
        cli.show_top_performers(limit=args.limit)
    elif args.underperformers:
        cli.show_underperformers(limit=args.limit)
    elif args.report:
        cli.generate_full_report(output_file=args.output)
    else:
        # Default: show summary
        cli.show_summary()


if __name__ == "__main__":
    main()
