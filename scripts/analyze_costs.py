#!/usr/bin/env python3
"""
Cost Analysis CLI

Analyze workflow costs by phase, workflow type, and time period.
Identify optimization opportunities and generate detailed reports.

Usage:
    python scripts/analyze_costs.py --phase --days 30
    python scripts/analyze_costs.py --workflow --days 30
    python scripts/analyze_costs.py --trends --days 30
    python scripts/analyze_costs.py --optimize
    python scripts/analyze_costs.py --report --output cost_report.md
    python scripts/analyze_costs.py --help
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.cost_analytics_service import CostAnalyticsService


class CostAnalysisCLI:
    """CLI interface for cost analysis and reporting."""

    def __init__(self):
        self.service = CostAnalyticsService()

    def show_phase_breakdown(self, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Show cost breakdown by phase."""
        print("\n" + "="*80)
        print(f"COST BREAKDOWN BY PHASE - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.analyze_by_phase(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        if result.workflow_count == 0:
            print("No workflow data found in the specified date range.")
            return

        # Sort phases by cost (descending)
        sorted_phases = sorted(
            result.phase_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Display phase costs
        print(f"{'Phase':<15} {'Cost':>12} {'Percentage':>12} {'Count':>8}")
        print("-" * 80)

        for phase, cost in sorted_phases:
            percentage = result.phase_percentages.get(phase, 0)
            count = result.phase_counts.get(phase, 0)
            print(f"{phase:<15} ${cost:>11.2f} {percentage:>11.1f}% {count:>8}")

        print("-" * 80)
        print(f"{'TOTAL':<15} ${result.total:>11.2f} {'100.0%':>12} {result.workflow_count:>8}")
        print()
        print(f"Average cost per workflow: ${result.average_per_workflow:.2f}")
        print("="*80 + "\n")

    def show_workflow_breakdown(self, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Show cost breakdown by workflow type."""
        print("\n" + "="*80)
        print(f"COST BREAKDOWN BY WORKFLOW TYPE - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.analyze_by_workflow_type(
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        if not result.by_type:
            print("No workflow data found in the specified date range.")
            return

        # Sort by total cost (descending)
        sorted_types = sorted(
            result.by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Calculate total for percentages
        total_cost = sum(result.by_type.values())

        # Display workflow type costs
        print(f"{'Workflow Type':<30} {'Total Cost':>12} {'Count':>8} {'Avg Cost':>12} {'%':>8}")
        print("-" * 80)

        for workflow_type, cost in sorted_types:
            count = result.count_by_type[workflow_type]
            avg_cost = result.average_by_type[workflow_type]
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"{workflow_type:<30} ${cost:>11.2f} {count:>8} ${avg_cost:>11.2f} {percentage:>7.1f}%")

        print("-" * 80)
        print(f"{'TOTAL':<30} ${total_cost:>11.2f} {sum(result.count_by_type.values()):>8}")
        print("="*80 + "\n")

    def show_trends(self, days: int = 30):
        """Show cost trends over time."""
        print("\n" + "="*80)
        print(f"COST TRENDS - Last {days} Days")
        print("="*80 + "\n")

        result = self.service.analyze_by_time_period(period='day', days=days)

        if not result.daily_costs:
            print("No workflow data found in the specified date range.")
            return

        # Show summary
        print(f"Total Cost:         ${result.total_cost:.2f}")
        print(f"Average Daily Cost: ${result.average_daily_cost:.2f}")
        print(f"Trend Direction:    {result.trend_direction.upper()}")
        print(f"Percentage Change:  {result.percentage_change:+.1f}%")
        print()

        # Show recent daily costs (last 10 days)
        print(f"{'Date':<12} {'Cost':>12} {'Workflows':>12} {'7-Day MA':>12}")
        print("-" * 80)

        recent_days = result.daily_costs[-10:] if len(result.daily_costs) > 10 else result.daily_costs
        recent_ma = result.moving_average[-10:] if len(result.moving_average) > 10 else result.moving_average

        for i, day_data in enumerate(recent_days):
            ma_value = recent_ma[i] if i < len(recent_ma) else 0
            print(
                f"{day_data.date:<12} ${day_data.cost:>11.2f} "
                f"{day_data.workflow_count:>12} ${ma_value:>11.2f}"
            )

        print("="*80 + "\n")

    def show_optimizations(self, days: int = 30):
        """Show optimization opportunities."""
        print("\n" + "="*80)
        print(f"OPTIMIZATION OPPORTUNITIES - Last {days} Days")
        print("="*80 + "\n")

        opportunities = self.service.get_optimization_opportunities(days=days)

        if not opportunities:
            print("No optimization opportunities identified.")
            print("Your workflow costs appear to be well-optimized!")
            return

        total_potential_savings = sum(opp.estimated_savings for opp in opportunities)

        print(f"Found {len(opportunities)} optimization opportunities")
        print(f"Total potential monthly savings: ${total_potential_savings:.2f}")
        print()

        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. [{opp.priority.upper()}] {opp.category.upper()}")
            print(f"   {opp.description}")
            print(f"   Current: ${opp.current_cost:.2f} → Target: ${opp.target_cost:.2f}")
            print(f"   Estimated monthly savings: ${opp.estimated_savings:.2f}")
            print(f"   Recommendation: {opp.recommendation}")
            print()

        print("="*80 + "\n")

    def generate_report(self, output_file: str, days: int = 30):
        """Generate a comprehensive markdown report."""
        print(f"\nGenerating cost analysis report for last {days} days...")

        # Gather all data
        phase_data = self.service.analyze_by_phase(days=days)
        workflow_data = self.service.analyze_by_workflow_type(days=days)
        trend_data = self.service.analyze_by_time_period(days=days)
        opportunities = self.service.get_optimization_opportunities(days=days)

        # Generate markdown report
        report_lines = []
        report_lines.append(f"# Cost Analysis Report")
        report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Period:** Last {days} days\n")

        # Executive Summary
        report_lines.append("## Executive Summary\n")
        report_lines.append(f"- **Total Cost:** ${trend_data.total_cost:.2f}")
        report_lines.append(f"- **Average Daily Cost:** ${trend_data.average_daily_cost:.2f}")
        report_lines.append(f"- **Workflows Analyzed:** {phase_data.workflow_count}")
        report_lines.append(f"- **Cost Trend:** {trend_data.trend_direction} ({trend_data.percentage_change:+.1f}%)")
        if opportunities:
            total_savings = sum(opp.estimated_savings for opp in opportunities)
            report_lines.append(f"- **Potential Monthly Savings:** ${total_savings:.2f}\n")
        else:
            report_lines.append(f"- **Optimization Status:** Well-optimized\n")

        # Phase Breakdown
        report_lines.append("## Cost Breakdown by Phase\n")
        if phase_data.phase_costs:
            report_lines.append("| Phase | Cost | Percentage | Count |")
            report_lines.append("|-------|------|------------|-------|")
            sorted_phases = sorted(
                phase_data.phase_costs.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for phase, cost in sorted_phases:
                percentage = phase_data.phase_percentages.get(phase, 0)
                count = phase_data.phase_counts.get(phase, 0)
                report_lines.append(f"| {phase} | ${cost:.2f} | {percentage:.1f}% | {count} |")
            report_lines.append(f"| **TOTAL** | **${phase_data.total:.2f}** | **100.0%** | **{phase_data.workflow_count}** |\n")
        else:
            report_lines.append("No phase cost data available.\n")

        # Workflow Type Breakdown
        report_lines.append("## Cost Breakdown by Workflow Type\n")
        if workflow_data.by_type:
            report_lines.append("| Workflow Type | Total Cost | Count | Avg Cost |")
            report_lines.append("|---------------|------------|-------|----------|")
            sorted_types = sorted(
                workflow_data.by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for workflow_type, cost in sorted_types:
                count = workflow_data.count_by_type[workflow_type]
                avg_cost = workflow_data.average_by_type[workflow_type]
                report_lines.append(f"| {workflow_type} | ${cost:.2f} | {count} | ${avg_cost:.2f} |")
            report_lines.append("")
        else:
            report_lines.append("No workflow type data available.\n")

        # Trends
        report_lines.append("## Cost Trends\n")
        report_lines.append(f"- **Trend Direction:** {trend_data.trend_direction}")
        report_lines.append(f"- **Percentage Change:** {trend_data.percentage_change:+.1f}%")
        report_lines.append(f"- **Total Period Cost:** ${trend_data.total_cost:.2f}")
        report_lines.append(f"- **Average Daily Cost:** ${trend_data.average_daily_cost:.2f}\n")

        # Recent daily costs
        if trend_data.daily_costs:
            report_lines.append("### Recent Daily Costs (Last 10 Days)\n")
            report_lines.append("| Date | Cost | Workflows | 7-Day MA |")
            report_lines.append("|------|------|-----------|----------|")
            recent = trend_data.daily_costs[-10:]
            recent_ma = trend_data.moving_average[-10:] if len(trend_data.moving_average) >= len(recent) else [0] * len(recent)
            for i, day_data in enumerate(recent):
                ma = recent_ma[i] if i < len(recent_ma) else 0
                report_lines.append(f"| {day_data.date} | ${day_data.cost:.2f} | {day_data.workflow_count} | ${ma:.2f} |")
            report_lines.append("")

        # Optimization Opportunities
        report_lines.append("## Optimization Opportunities\n")
        if opportunities:
            total_savings = sum(opp.estimated_savings for opp in opportunities)
            report_lines.append(f"**Total Potential Monthly Savings:** ${total_savings:.2f}\n")

            for i, opp in enumerate(opportunities, 1):
                report_lines.append(f"### {i}. [{opp.priority.upper()}] {opp.category.upper()}\n")
                report_lines.append(f"**Description:** {opp.description}\n")
                report_lines.append(f"- **Current Cost:** ${opp.current_cost:.2f}")
                report_lines.append(f"- **Target Cost:** ${opp.target_cost:.2f}")
                report_lines.append(f"- **Estimated Monthly Savings:** ${opp.estimated_savings:.2f}")
                report_lines.append(f"- **Recommendation:** {opp.recommendation}\n")
        else:
            report_lines.append("No optimization opportunities identified. Your workflow costs are well-optimized!\n")

        # Write report
        report_content = "\n".join(report_lines)
        output_path = Path(output_file)
        output_path.write_text(report_content)

        print(f"Report generated: {output_file}")
        print(f"Report size: {len(report_content)} characters\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze workflow costs and identify optimization opportunities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show phase breakdown for last 30 days
  python scripts/analyze_costs.py --phase --days 30

  # Show workflow type breakdown
  python scripts/analyze_costs.py --workflow --days 30

  # Show cost trends
  python scripts/analyze_costs.py --trends --days 30

  # Show optimization opportunities
  python scripts/analyze_costs.py --optimize

  # Generate full markdown report
  python scripts/analyze_costs.py --report --output cost_report.md

  # Show all analysis
  python scripts/analyze_costs.py --all --days 30
        """
    )

    # Analysis type
    parser.add_argument(
        '--phase',
        action='store_true',
        help='Show cost breakdown by phase'
    )
    parser.add_argument(
        '--workflow',
        action='store_true',
        help='Show cost breakdown by workflow type'
    )
    parser.add_argument(
        '--trends',
        action='store_true',
        help='Show cost trends over time'
    )
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='Show optimization opportunities'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate markdown report'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all analyses'
    )

    # Date range
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (ISO format: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (ISO format: YYYY-MM-DD)'
    )

    # Output
    parser.add_argument(
        '--output',
        type=str,
        default='cost_analysis_report.md',
        help='Output file for report (default: cost_analysis_report.md)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON (for API integration)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Set up logging
    import logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level)

    # Initialize CLI
    cli = CostAnalysisCLI()

    # Execute based on arguments
    try:
        # If no specific analysis requested, show help
        if not any([args.phase, args.workflow, args.trends, args.optimize, args.report, args.all]):
            parser.print_help()
            return

        # Show all if requested
        if args.all:
            cli.show_phase_breakdown(args.days, args.start_date, args.end_date)
            cli.show_workflow_breakdown(args.days, args.start_date, args.end_date)
            cli.show_trends(args.days)
            cli.show_optimizations(args.days)
            return

        # Show individual analyses
        if args.phase:
            cli.show_phase_breakdown(args.days, args.start_date, args.end_date)

        if args.workflow:
            cli.show_workflow_breakdown(args.days, args.start_date, args.end_date)

        if args.trends:
            cli.show_trends(args.days)

        if args.optimize:
            cli.show_optimizations(args.days)

        if args.report:
            cli.generate_report(args.output, args.days)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
