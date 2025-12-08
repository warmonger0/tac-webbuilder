#!/usr/bin/env python3
"""
Latency Analysis CLI

Analyze workflow execution times by phase, identify bottlenecks, track trends,
and generate optimization recommendations.

Usage:
    python scripts/analyze_latency.py --summary --days 30
    python scripts/analyze_latency.py --phase --days 30
    python scripts/analyze_latency.py --bottlenecks --threshold 300
    python scripts/analyze_latency.py --trends --days 30
    python scripts/analyze_latency.py --recommendations
    python scripts/analyze_latency.py --report --output latency_report.md
    python scripts/analyze_latency.py --help
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.latency_analytics_service import LatencyAnalyticsService


class LatencyAnalysisCLI:
    """CLI interface for latency analysis and reporting."""

    def __init__(self):
        self.service = LatencyAnalyticsService()

    def show_summary(self, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Show overall latency summary statistics."""
        print("\n" + "="*80)
        print(f"LATENCY ANALYSIS SUMMARY - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.get_latency_summary(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        if result.total_workflows == 0:
            print("No completed workflow data found in the specified date range.")
            return

        # Display summary statistics
        print(f"Total workflows analyzed: {result.total_workflows}")
        print()
        print(f"Average duration:    {self._format_duration(result.average_duration_seconds)}")
        print(f"p50 (median):        {self._format_duration(result.p50_duration)}")
        print(f"p95:                 {self._format_duration(result.p95_duration)}")
        print(f"p99:                 {self._format_duration(result.p99_duration)}")
        print()

        if result.slowest_phase:
            print(f"Slowest phase:       {result.slowest_phase} (avg: {self._format_duration(result.slowest_phase_avg)})")

        print("="*80 + "\n")

    def show_phase_breakdown(self, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Show latency breakdown by phase."""
        print("\n" + "="*80)
        print(f"PHASE LATENCY BREAKDOWN - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.analyze_by_phase(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        if not result.phase_latencies:
            print("No phase latency data found in the specified date range.")
            return

        # Sort phases by p95 latency (descending)
        sorted_phases = sorted(
            result.phase_latencies.items(),
            key=lambda x: x[1].p95,
            reverse=True
        )

        # Display phase latencies
        print(f"{'Phase':<15} {'p50':>8} {'p95':>8} {'p99':>8} {'Avg':>8} {'Sample':>8}")
        print("-" * 80)

        for phase, stats in sorted_phases:
            print(
                f"{phase:<15} "
                f"{self._format_duration(stats.p50):>8} "
                f"{self._format_duration(stats.p95):>8} "
                f"{self._format_duration(stats.p99):>8} "
                f"{self._format_duration(stats.average):>8} "
                f"{stats.sample_count:>8}"
            )

        print("-" * 80)
        print(f"Total workflow avg: {self._format_duration(result.total_duration_avg)}")
        print("="*80 + "\n")

    def show_bottlenecks(self, threshold: int = 300, days: int = 30):
        """Show performance bottlenecks."""
        print("\n" + "="*80)
        print(f"PERFORMANCE BOTTLENECKS - Last {days} Days (Threshold: {threshold}s)")
        print("="*80 + "\n")

        bottlenecks = self.service.find_bottlenecks(
            threshold_seconds=threshold,
            days=days
        )

        if not bottlenecks:
            print(f"No bottlenecks detected (all phases p95 < {threshold}s)")
            print("="*80 + "\n")
            return

        print(f"Found {len(bottlenecks)} bottleneck(s):\n")

        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"{i}. {bottleneck.phase} Phase")
            print(f"   p95 Latency:        {self._format_duration(bottleneck.p95_latency)}")
            print(f"   Threshold:          {self._format_duration(bottleneck.threshold)}")
            print(f"   % Over Threshold:   {bottleneck.percentage_over_threshold:.1f}%")
            print(f"   Affected Workflows: {bottleneck.affected_workflows}")
            print(f"   Estimated Speedup:  {bottleneck.estimated_speedup}")
            print(f"   Recommendation:     {bottleneck.recommendation}")
            print()

        print("="*80 + "\n")

    def show_trends(self, days: int = 30):
        """Show latency trends over time."""
        print("\n" + "="*80)
        print(f"LATENCY TRENDS - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.get_latency_trends(days=days)

        if not result.daily_latencies:
            print("No trend data found in the specified date range.")
            return

        # Display trend summary
        print(f"Trend Direction:      {result.trend_direction.upper()}")
        print(f"Percentage Change:    {result.percentage_change:+.1f}%")
        print(f"Average Daily:        {self._format_duration(result.average_daily_duration)}")
        print()

        # Display recent data points (last 10 days)
        print("Recent Daily Latencies:")
        print(f"{'Date':<12} {'Avg Duration':>14} {'Workflows':>12}")
        print("-" * 80)

        recent_days = result.daily_latencies[-10:] if len(result.daily_latencies) > 10 else result.daily_latencies
        for dp in recent_days:
            print(f"{dp.date:<12} {self._format_duration(dp.duration):>14} {dp.workflow_count:>12}")

        print("="*80 + "\n")

    def show_recommendations(self, days: int = 30):
        """Show optimization recommendations."""
        print("\n" + "="*80)
        print(f"OPTIMIZATION RECOMMENDATIONS - Last {days} Days")
        print("="*80 + "\n")

        recommendations = self.service.get_optimization_recommendations(days=days)

        if not recommendations:
            print("No optimization opportunities identified.")
            print("="*80 + "\n")
            return

        print(f"Found {len(recommendations)} optimization opportunity(ies):\n")

        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.target}")
            print(f"   Current Latency:  {self._format_duration(rec.current_latency)}")
            print(f"   Target Latency:   {self._format_duration(rec.target_latency)}")
            print(f"   Improvement:      {rec.improvement_percentage:.0f}% faster")
            print(f"   Actions:")
            for action in rec.actions:
                print(f"   - {action}")
            print()

        print("="*80 + "\n")

    def generate_report(self, output_file: str, days: int = 30):
        """Generate comprehensive latency analysis report."""
        print(f"\nGenerating latency analysis report for last {days} days...")

        # Collect all data
        summary = self.service.get_latency_summary(days=days)
        phase_breakdown = self.service.analyze_by_phase(days=days)
        bottlenecks = self.service.find_bottlenecks(threshold_seconds=300, days=days)
        trends = self.service.get_latency_trends(days=days)
        recommendations = self.service.get_optimization_recommendations(days=days)

        # Generate markdown report
        report = []
        report.append("# Workflow Latency Analysis Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Period:** Last {days} days\n")
        report.append("\n---\n")

        # Summary Section
        report.append("\n## Executive Summary\n")
        report.append(f"- **Total Workflows:** {summary.total_workflows}\n")
        report.append(f"- **Average Duration:** {self._format_duration(summary.average_duration_seconds)}\n")
        report.append(f"- **p50 (Median):** {self._format_duration(summary.p50_duration)}\n")
        report.append(f"- **p95:** {self._format_duration(summary.p95_duration)}\n")
        report.append(f"- **p99:** {self._format_duration(summary.p99_duration)}\n")
        if summary.slowest_phase:
            report.append(f"- **Slowest Phase:** {summary.slowest_phase} (avg: {self._format_duration(summary.slowest_phase_avg)})\n")

        # Phase Breakdown Section
        report.append("\n## Phase Latency Breakdown\n")
        report.append("\n| Phase | p50 | p95 | p99 | Average | Sample Count |\n")
        report.append("|-------|-----|-----|-----|---------|-------------|\n")

        sorted_phases = sorted(
            phase_breakdown.phase_latencies.items(),
            key=lambda x: x[1].p95,
            reverse=True
        )

        for phase, stats in sorted_phases:
            report.append(
                f"| {phase} | {self._format_duration(stats.p50)} | "
                f"{self._format_duration(stats.p95)} | {self._format_duration(stats.p99)} | "
                f"{self._format_duration(stats.average)} | {stats.sample_count} |\n"
            )

        # Bottlenecks Section
        report.append("\n## Performance Bottlenecks\n")
        if bottlenecks:
            report.append(f"\nIdentified **{len(bottlenecks)}** bottleneck(s):\n")
            for i, bottleneck in enumerate(bottlenecks, 1):
                report.append(f"\n### {i}. {bottleneck.phase} Phase\n")
                report.append(f"- **p95 Latency:** {self._format_duration(bottleneck.p95_latency)}\n")
                report.append(f"- **Threshold:** {self._format_duration(bottleneck.threshold)}\n")
                report.append(f"- **% Over Threshold:** {bottleneck.percentage_over_threshold:.1f}%\n")
                report.append(f"- **Affected Workflows:** {bottleneck.affected_workflows}\n")
                report.append(f"- **Estimated Speedup:** {bottleneck.estimated_speedup}\n")
                report.append(f"- **Recommendation:** {bottleneck.recommendation}\n")
        else:
            report.append("\n✅ No bottlenecks detected (all phases performing well)\n")

        # Trends Section
        report.append("\n## Latency Trends\n")
        report.append(f"- **Trend Direction:** {trends.trend_direction.upper()}\n")
        report.append(f"- **Percentage Change:** {trends.percentage_change:+.1f}%\n")
        report.append(f"- **Average Daily Duration:** {self._format_duration(trends.average_daily_duration)}\n")

        # Recommendations Section
        report.append("\n## Optimization Recommendations\n")
        if recommendations:
            report.append(f"\nTop **{len(recommendations)}** optimization opportunity(ies):\n")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"\n### {i}. {rec.target}\n")
                report.append(f"- **Current Latency:** {self._format_duration(rec.current_latency)}\n")
                report.append(f"- **Target Latency:** {self._format_duration(rec.target_latency)}\n")
                report.append(f"- **Expected Improvement:** {rec.improvement_percentage:.0f}% faster\n")
                report.append(f"- **Actions:**\n")
                for action in rec.actions:
                    report.append(f"  - {action}\n")
        else:
            report.append("\n✅ No immediate optimization opportunities identified\n")

        # Write report to file
        report_content = "".join(report)
        with open(output_file, 'w') as f:
            f.write(report_content)

        print(f"✅ Report generated: {output_file}")
        print(f"   Total workflows: {summary.total_workflows}")
        print(f"   Bottlenecks: {len(bottlenecks)}")
        print(f"   Recommendations: {len(recommendations)}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze workflow latency patterns and generate optimization recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show overall latency summary
  python scripts/analyze_latency.py --summary --days 30

  # Show phase-by-phase breakdown
  python scripts/analyze_latency.py --phase --days 30

  # Detect bottlenecks (phases exceeding 300s)
  python scripts/analyze_latency.py --bottlenecks --threshold 300

  # Show latency trends over time
  python scripts/analyze_latency.py --trends --days 30

  # Show optimization recommendations
  python scripts/analyze_latency.py --recommendations

  # Generate comprehensive markdown report
  python scripts/analyze_latency.py --report --output latency_report.md
        """
    )

    # Analysis options
    parser.add_argument('--summary', action='store_true', help='Show overall latency summary')
    parser.add_argument('--phase', action='store_true', help='Show latency breakdown by phase')
    parser.add_argument('--bottlenecks', action='store_true', help='Detect performance bottlenecks')
    parser.add_argument('--trends', action='store_true', help='Show latency trends over time')
    parser.add_argument('--recommendations', action='store_true', help='Show optimization recommendations')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive markdown report')

    # Configuration options
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument('--threshold', type=int, default=300, help='Bottleneck threshold in seconds (default: 300)')
    parser.add_argument('--output', type=str, default='latency_analysis_report.md', help='Output file for report (default: latency_analysis_report.md)')
    parser.add_argument('--start-date', type=str, help='Start date (ISO format: YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (ISO format: YYYY-MM-DD)')

    args = parser.parse_args()

    # If no analysis option specified, show help
    if not (args.summary or args.phase or args.bottlenecks or args.trends or args.recommendations or args.report):
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = LatencyAnalysisCLI()

    try:
        # Execute requested analysis
        if args.summary:
            cli.show_summary(days=args.days, start_date=args.start_date, end_date=args.end_date)

        if args.phase:
            cli.show_phase_breakdown(days=args.days, start_date=args.start_date, end_date=args.end_date)

        if args.bottlenecks:
            cli.show_bottlenecks(threshold=args.threshold, days=args.days)

        if args.trends:
            cli.show_trends(days=args.days)

        if args.recommendations:
            cli.show_recommendations(days=args.days)

        if args.report:
            cli.generate_report(output_file=args.output, days=args.days)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
