#!/usr/bin/env python3
"""
Error Analysis CLI

Analyze workflow errors, detect patterns, and generate debugging recommendations.
Provides insights into failure rates, error trends, and systematic debugging strategies.

Usage:
    python scripts/analyze_errors.py --summary --days 30
    python scripts/analyze_errors.py --phase --days 30
    python scripts/analyze_errors.py --patterns --days 30
    python scripts/analyze_errors.py --trends --days 30
    python scripts/analyze_errors.py --recommendations --days 30
    python scripts/analyze_errors.py --report --output error_analysis_report.md
    python scripts/analyze_errors.py --help
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.error_analytics_service import ErrorAnalyticsService


class ErrorAnalysisCLI:
    """CLI interface for error analysis and reporting."""

    def __init__(self):
        self.service = ErrorAnalyticsService()

    def show_summary(self, days: int = 30):
        """Display error summary statistics."""
        print("\n" + "="*80)
        print(f"ERROR ANALYSIS SUMMARY - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.get_error_summary(days=days)

        if result['total_workflows'] == 0:
            print("No workflow data found in the specified date range.")
            return

        print(f"Total workflows:     {result['total_workflows']}")
        print(f"Failed workflows:    {result['failed_workflows']}")
        print(f"Failure rate:        {result['failure_rate']:.1f}%")

        if result['most_problematic_phase']:
            print(f"Most problematic phase: {result['most_problematic_phase']}")

        if result['top_errors']:
            print("\nTOP ERROR PATTERNS:")
            print("-" * 80)
            for i, (pattern, count) in enumerate(result['top_errors'], 1):
                pattern_display = pattern.replace('_', ' ').title()
                print(f"{i}. {pattern_display:<30} {count:>3} occurrences")

        if result['error_categories']:
            print("\nERROR CATEGORIES:")
            print("-" * 80)
            for category, count in sorted(result['error_categories'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {category:<30} {count:>3} occurrences")

        print("\n" + "="*80 + "\n")

    def show_phase_breakdown(self, days: int = 30):
        """Display error breakdown by workflow phase."""
        print("\n" + "="*80)
        print(f"ERROR BREAKDOWN BY PHASE - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.analyze_by_phase(days=days)

        if result['total_errors'] == 0:
            print("No errors found in the specified date range.")
            return

        print(f"Total errors: {result['total_errors']}")
        if result['most_error_prone_phase']:
            print(f"Most error-prone phase: {result['most_error_prone_phase']}")

        print("\nPHASE ERROR RATES:")
        print(f"{'Phase':<20} {'Errors':>10} {'Failure Rate':>15}")
        print("-" * 80)

        # Sort by failure rate (descending)
        sorted_phases = sorted(
            result['phase_failure_rates'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for phase, rate in sorted_phases:
            error_count = result['phase_error_counts'].get(phase, 0)
            # Determine status indicator
            if rate >= 20:
                indicator = "🔴 CRITICAL"
            elif rate >= 10:
                indicator = "🟡 WARNING"
            else:
                indicator = "🟢 OK"

            print(f"{phase:<20} {error_count:>10} {rate:>13.1f}%  {indicator}")

        print("="*80 + "\n")

    def show_patterns(self, days: int = 30):
        """Display detected error patterns with recommendations."""
        print("\n" + "="*80)
        print(f"ERROR PATTERNS - Last {days} Days")
        print("="*80 + "\n")

        patterns = self.service.find_error_patterns(days=days)

        if not patterns:
            print("No error patterns detected in the specified date range.")
            return

        for i, pattern in enumerate(patterns, 1):
            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }
            emoji = severity_emoji.get(pattern['severity'], '⚪')

            print(f"{i}. {emoji} {pattern['pattern_name']} ({pattern['occurrences']} occurrences)")
            print(f"   Category: {pattern['pattern_category']}")
            print(f"   Severity: {pattern['severity'].upper()}")
            print(f"   Example: {pattern['example_message'][:80]}...")
            print(f"   Recommendation: {pattern['recommendation']}")
            print(f"   Affected workflows: {len(pattern['affected_workflows'])}")
            print()

        print("="*80 + "\n")

    def show_trends(self, days: int = 30):
        """Display error trends over time."""
        print("\n" + "="*80)
        print(f"ERROR TRENDS - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.get_failure_trends(days=days)

        if not result['daily_errors']:
            print("No error trend data available.")
            return

        print(f"Trend direction: {result['trend_direction'].upper()}")
        print(f"Percentage change: {result['percentage_change']:+.1f}%")
        print(f"Average daily failures: {result['average_daily_failures']:.1f}")

        print("\nDAILY ERROR TRENDS:")
        print(f"{'Date':<12} {'Errors':>8} {'Failure Rate':>15} {'Total':>8}")
        print("-" * 80)

        for entry in result['daily_errors'][-14:]:  # Show last 14 days
            date = entry['date']
            error_count = entry['error_count']
            failure_rate = entry['failure_rate']
            workflow_count = entry['workflow_count']

            # Add visual indicator
            if failure_rate >= 20:
                bar = '█' * int(failure_rate / 5)
            elif failure_rate >= 10:
                bar = '▓' * int(failure_rate / 5)
            else:
                bar = '░' * int(failure_rate / 5)

            print(f"{date:<12} {error_count:>8} {failure_rate:>13.1f}% {workflow_count:>8}  {bar}")

        print("="*80 + "\n")

    def show_recommendations(self, days: int = 30):
        """Display debugging recommendations."""
        print("\n" + "="*80)
        print(f"DEBUGGING RECOMMENDATIONS - Last {days} Days")
        print("="*80 + "\n")

        recommendations = self.service.get_debugging_recommendations(days=days)

        if not recommendations:
            print("No debugging recommendations available. Great work - no recurring errors!")
            return

        severity_order = {'high': 1, 'medium': 2, 'low': 3}
        sorted_recs = sorted(recommendations, key=lambda x: (severity_order[x['severity']], -x['affected_count']))

        for i, rec in enumerate(sorted_recs, 1):
            severity_emoji = {
                'high': '🔴 HIGH',
                'medium': '🟡 MEDIUM',
                'low': '🟢 LOW'
            }
            severity_display = severity_emoji.get(rec['severity'], '⚪ UNKNOWN')

            print(f"{i}. [{severity_display}] {rec['issue']}")
            print(f"   Root Cause: {rec['root_cause']}")
            print(f"   Solution: {rec['solution']}")
            print(f"   Estimated Fix Time: {rec['estimated_fix_time']}")
            print(f"   Affected Workflows: {rec['affected_count']}")
            print()

        print("="*80 + "\n")

    def generate_report(self, output_file: str = "error_analysis_report.md", days: int = 30):
        """Generate comprehensive markdown report."""
        print(f"\nGenerating error analysis report for last {days} days...")

        # Gather all data
        summary = self.service.get_error_summary(days=days)
        phase_breakdown = self.service.analyze_by_phase(days=days)
        patterns = self.service.find_error_patterns(days=days)
        trends = self.service.get_failure_trends(days=days)
        recommendations = self.service.get_debugging_recommendations(days=days)

        # Generate markdown
        report_lines = [
            f"# Error Analysis Report",
            f"",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Period:** Last {days} days",
            f"",
            f"---",
            f"",
            f"## Summary",
            f"",
            f"- **Total Workflows:** {summary['total_workflows']}",
            f"- **Failed Workflows:** {summary['failed_workflows']}",
            f"- **Failure Rate:** {summary['failure_rate']:.1f}%",
            f"- **Most Problematic Phase:** {summary['most_problematic_phase'] or 'N/A'}",
            f"",
            f"### Top Error Patterns",
            f"",
        ]

        if summary['top_errors']:
            for i, (pattern, count) in enumerate(summary['top_errors'], 1):
                pattern_display = pattern.replace('_', ' ').title()
                report_lines.append(f"{i}. **{pattern_display}** - {count} occurrences")
        else:
            report_lines.append("No errors detected.")

        report_lines.extend([
            f"",
            f"---",
            f"",
            f"## Phase Breakdown",
            f"",
            f"| Phase | Error Count | Failure Rate | Status |",
            f"|-------|-------------|--------------|--------|",
        ])

        sorted_phases = sorted(
            phase_breakdown['phase_failure_rates'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for phase, rate in sorted_phases:
            error_count = phase_breakdown['phase_error_counts'].get(phase, 0)
            if rate >= 20:
                status = "🔴 CRITICAL"
            elif rate >= 10:
                status = "🟡 WARNING"
            else:
                status = "🟢 OK"
            report_lines.append(f"| {phase} | {error_count} | {rate:.1f}% | {status} |")

        report_lines.extend([
            f"",
            f"---",
            f"",
            f"## Error Patterns",
            f"",
        ])

        for i, pattern in enumerate(patterns, 1):
            report_lines.extend([
                f"### {i}. {pattern['pattern_name']} ({pattern['occurrences']} occurrences)",
                f"",
                f"- **Category:** {pattern['pattern_category']}",
                f"- **Severity:** {pattern['severity'].upper()}",
                f"- **Example:** `{pattern['example_message'][:100]}...`",
                f"- **Recommendation:** {pattern['recommendation']}",
                f"",
            ])

        report_lines.extend([
            f"---",
            f"",
            f"## Trends",
            f"",
            f"- **Trend Direction:** {trends['trend_direction'].upper()}",
            f"- **Percentage Change:** {trends['percentage_change']:+.1f}%",
            f"- **Average Daily Failures:** {trends['average_daily_failures']:.1f}",
            f"",
            f"---",
            f"",
            f"## Debugging Recommendations",
            f"",
        ])

        for i, rec in enumerate(recommendations, 1):
            report_lines.extend([
                f"### {i}. [{rec['severity'].upper()}] {rec['issue']}",
                f"",
                f"- **Root Cause:** {rec['root_cause']}",
                f"- **Solution:** {rec['solution']}",
                f"- **Estimated Fix Time:** {rec['estimated_fix_time']}",
                f"- **Affected Workflows:** {rec['affected_count']}",
                f"",
            ])

        # Write to file
        output_path = Path(output_file)
        output_path.write_text("\n".join(report_lines))

        print(f"✅ Report generated: {output_path.absolute()}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze workflow errors and generate debugging recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_errors.py --summary --days 30
  python scripts/analyze_errors.py --phase
  python scripts/analyze_errors.py --patterns
  python scripts/analyze_errors.py --recommendations
  python scripts/analyze_errors.py --report --output error_report.md
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show error summary statistics'
    )

    parser.add_argument(
        '--phase',
        action='store_true',
        help='Show error breakdown by phase'
    )

    parser.add_argument(
        '--patterns',
        action='store_true',
        help='Show detected error patterns'
    )

    parser.add_argument(
        '--trends',
        action='store_true',
        help='Show error trends over time'
    )

    parser.add_argument(
        '--recommendations',
        action='store_true',
        help='Show debugging recommendations'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive markdown report'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='error_analysis_report.md',
        help='Output file for report (default: error_analysis_report.md)'
    )

    args = parser.parse_args()

    # If no specific action specified, show summary
    if not any([args.summary, args.phase, args.patterns, args.trends, args.recommendations, args.report]):
        args.summary = True

    cli = ErrorAnalysisCLI()

    try:
        if args.summary:
            cli.show_summary(days=args.days)

        if args.phase:
            cli.show_phase_breakdown(days=args.days)

        if args.patterns:
            cli.show_patterns(days=args.days)

        if args.trends:
            cli.show_trends(days=args.days)

        if args.recommendations:
            cli.show_recommendations(days=args.days)

        if args.report:
            cli.generate_report(output_file=args.output, days=args.days)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
