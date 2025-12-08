#!/usr/bin/env python3
"""
Daily Pattern Analysis CLI

Automatically discovers automation patterns from hook events, calculates metrics,
and populates the pattern review system for approval.

Usage:
    python scripts/analyze_daily_patterns.py
    python scripts/analyze_daily_patterns.py --hours 48
    python scripts/analyze_daily_patterns.py --dry-run --verbose
    python scripts/analyze_daily_patterns.py --report
    python scripts/analyze_daily_patterns.py --help
"""

import argparse
import hashlib
import json
import logging
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app" / "server"))

from database import get_database_adapter
from services.pattern_review_service import PatternReviewService

logger = logging.getLogger(__name__)


@dataclass
class ToolSequence:
    """Represents a sequence of tools used in a session."""
    session_id: str
    tool_sequence: str  # e.g., "Read→Edit→Write"
    tool_names: List[str]
    event_count: int
    first_seen: str
    last_seen: str


@dataclass
class PatternMetrics:
    """Metrics for a discovered pattern."""
    pattern_id: str
    tool_sequence: str
    confidence_score: float
    occurrence_count: int
    estimated_savings_usd: float
    pattern_context: str
    example_sessions: List[str]
    status: str  # 'auto-approved', 'pending', 'auto-rejected'


class DailyPatternAnalyzer:
    """Analyzes hook events to discover automation patterns."""

    def __init__(self, window_hours: int = 24, min_occurrences: int = 2):
        """
        Initialize analyzer.

        Args:
            window_hours: Analysis window in hours (default: 24)
            min_occurrences: Minimum pattern occurrences to consider (default: 2)
        """
        self.window_hours = window_hours
        self.min_occurrences = min_occurrences
        self.adapter = get_database_adapter()
        self.service = PatternReviewService()

        # Destructive operations that should be auto-rejected
        self.destructive_tools = [
            'Delete', 'Remove', 'Drop', 'Truncate', 'ForceDelete',
            'DeleteFile', 'RemoveFile', 'DropTable', 'TruncateTable'
        ]

        logger.info(f"[INIT] DailyPatternAnalyzer initialized (window={window_hours}h, min_occurrences={min_occurrences})")

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Main analysis entry point.

        Returns:
            Dictionary with analysis results and statistics
        """
        logger.info(f"[ANALYZE] Starting pattern analysis for last {self.window_hours} hours")

        # 1. Extract tool sequences from hook_events
        sequences = self.extract_tool_sequences()
        logger.info(f"[ANALYZE] Extracted {len(sequences)} tool sequences from hook events")

        # 2. Find repeated patterns
        patterns = self.find_repeated_patterns(sequences)
        logger.info(f"[ANALYZE] Found {len(patterns)} repeated patterns")

        # 3. Calculate metrics and classify
        analyzed_patterns = []
        for pattern_seq, occurrences in patterns.items():
            metrics = self.calculate_metrics(pattern_seq, occurrences, sequences)
            analyzed_patterns.append(metrics)

        # 4. Deduplicate and save
        results = {
            'total_sessions': len(sequences),
            'patterns_found': len(analyzed_patterns),
            'new_patterns': 0,
            'updated_patterns': 0,
            'auto_approved': 0,
            'pending': 0,
            'auto_rejected': 0,
            'total_savings': 0.0
        }

        for pattern in analyzed_patterns:
            is_new = self.save_pattern(pattern)

            if is_new:
                results['new_patterns'] += 1
            else:
                results['updated_patterns'] += 1

            # Count by status
            if pattern.status == 'auto-approved':
                results['auto_approved'] += 1
            elif pattern.status == 'pending':
                results['pending'] += 1
            elif pattern.status == 'auto-rejected':
                results['auto_rejected'] += 1

            results['total_savings'] += pattern.estimated_savings_usd

        logger.info(f"[ANALYZE] Analysis complete: {results}")
        return results

    def extract_tool_sequences(self) -> List[ToolSequence]:
        """
        Extract tool sequences from hook_events grouped by session_id.

        Returns:
            List of ToolSequence objects
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # PostgreSQL version - using string_agg instead of GROUP_CONCAT
            placeholder = self.adapter.placeholder()

            # First, get all tool events in the time window
            cursor.execute(f"""
                SELECT
                    session_id,
                    tool_name,
                    timestamp
                FROM hook_events
                WHERE timestamp >= NOW() - INTERVAL '{self.window_hours} hours'
                AND event_type = 'PreToolUse'
                AND tool_name IS NOT NULL
                AND session_id IS NOT NULL
                ORDER BY session_id, timestamp
            """)

            rows = cursor.fetchall()

            # Group by session_id and build sequences
            sessions = defaultdict(list)
            session_times = {}

            for row in rows:
                session_id = row['session_id']
                tool_name = row['tool_name']
                timestamp = row['timestamp']

                sessions[session_id].append(tool_name)

                if session_id not in session_times:
                    session_times[session_id] = {'first': timestamp, 'last': timestamp}
                else:
                    session_times[session_id]['last'] = timestamp

            # Convert to ToolSequence objects
            sequences = []
            for session_id, tools in sessions.items():
                if len(tools) >= 2:  # Only sequences with 2+ tools
                    tool_sequence = '→'.join(tools)
                    sequences.append(ToolSequence(
                        session_id=session_id,
                        tool_sequence=tool_sequence,
                        tool_names=tools,
                        event_count=len(tools),
                        first_seen=str(session_times[session_id]['first']),
                        last_seen=str(session_times[session_id]['last'])
                    ))

            logger.info(f"[EXTRACT] Found {len(sequences)} tool sequences from {len(sessions)} sessions")
            return sequences

    def find_repeated_patterns(self, sequences: List[ToolSequence]) -> Dict[str, List[ToolSequence]]:
        """
        Group identical tool sequences and count occurrences.

        Args:
            sequences: List of ToolSequence objects

        Returns:
            Dictionary mapping tool_sequence to list of matching ToolSequence objects
        """
        # Group by tool_sequence
        pattern_groups = defaultdict(list)
        for seq in sequences:
            pattern_groups[seq.tool_sequence].append(seq)

        # Filter patterns that appear min_occurrences+ times
        repeated = {
            seq: occurrences
            for seq, occurrences in pattern_groups.items()
            if len(occurrences) >= self.min_occurrences
        }

        logger.info(f"[PATTERNS] Found {len(repeated)} patterns with {self.min_occurrences}+ occurrences")
        return repeated

    def calculate_metrics(
        self,
        pattern_seq: str,
        occurrences: List[ToolSequence],
        all_sequences: List[ToolSequence]
    ) -> PatternMetrics:
        """
        Calculate confidence score, savings, and classify pattern.

        Args:
            pattern_seq: The tool sequence pattern
            occurrences: List of matching ToolSequence objects
            all_sequences: All sequences for context

        Returns:
            PatternMetrics object
        """
        occurrence_count = len(occurrences)
        total_sessions = len(all_sequences)

        # Calculate confidence score
        confidence = self.calculate_confidence(occurrence_count, total_sessions)

        # Estimate savings
        savings = self.estimate_savings(pattern_seq, occurrence_count)

        # Auto-classify
        status = self.auto_classify(pattern_seq, confidence, occurrence_count, savings)

        # Generate pattern ID
        pattern_id = hashlib.sha256(pattern_seq.encode()).hexdigest()[:16]

        # Build context
        tools = pattern_seq.split('→')
        pattern_context = f"Sequence of {len(tools)} tools: {', '.join(tools)}"

        # Get example sessions
        example_sessions = [occ.session_id for occ in occurrences[:10]]  # Max 10 examples

        return PatternMetrics(
            pattern_id=pattern_id,
            tool_sequence=pattern_seq,
            confidence_score=confidence,
            occurrence_count=occurrence_count,
            estimated_savings_usd=savings,
            pattern_context=pattern_context,
            example_sessions=example_sessions,
            status=status
        )

    def calculate_confidence(self, occurrences: int, total_sessions: int) -> float:
        """
        Statistical confidence score (0.0 to 1.0).

        Args:
            occurrences: Number of times pattern appeared
            total_sessions: Total sessions analyzed

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if total_sessions == 0:
            return 0.0

        # Base frequency
        frequency = occurrences / total_sessions

        # Boost confidence for high occurrence counts
        if occurrences >= 100:
            confidence = min(0.99, frequency * 1.2)
        elif occurrences >= 50:
            confidence = min(0.97, frequency * 1.15)
        elif occurrences >= 10:
            confidence = min(0.95, frequency * 1.1)
        else:
            confidence = frequency

        return round(confidence, 4)

    def estimate_savings(self, pattern: str, occurrences: int) -> float:
        """
        Estimate cost savings if pattern is automated.

        Args:
            pattern: Tool sequence pattern
            occurrences: Number of times pattern appeared

        Returns:
            Estimated savings in USD
        """
        # Average time per tool execution (seconds)
        avg_time_per_tool = 30

        # Parse tool sequence
        tools = pattern.split('→')
        pattern_time_seconds = len(tools) * avg_time_per_tool

        # Assume $100/hour AI cost (conservative)
        cost_per_second = 100.0 / 3600.0

        # Savings if automated
        savings_per_occurrence = pattern_time_seconds * cost_per_second
        total_savings = savings_per_occurrence * occurrences

        return round(total_savings, 2)

    def auto_classify(
        self,
        pattern: str,
        confidence: float,
        occurrences: int,
        savings: float
    ) -> str:
        """
        Determine pattern status based on thresholds.

        Args:
            pattern: Tool sequence pattern
            confidence: Confidence score (0.0 to 1.0)
            occurrences: Number of occurrences
            savings: Estimated savings in USD

        Returns:
            Status: 'auto-approved', 'pending', or 'auto-rejected'
        """
        # Check for destructive operations
        if any(tool in pattern for tool in self.destructive_tools):
            logger.info(f"[CLASSIFY] Auto-rejecting pattern with destructive operation: {pattern}")
            return 'auto-rejected'

        # Auto-approve high-confidence, high-value patterns
        if confidence > 0.99 and occurrences > 200 and savings > 5000:
            logger.info(f"[CLASSIFY] Auto-approving high-value pattern: {pattern}")
            return 'auto-approved'

        # Auto-reject low-confidence patterns
        if confidence < 0.95:
            logger.info(f"[CLASSIFY] Auto-rejecting low-confidence pattern: {pattern} (confidence={confidence:.2%})")
            return 'auto-rejected'

        # Everything else requires manual review
        logger.info(f"[CLASSIFY] Pattern requires manual review: {pattern}")
        return 'pending'

    def save_pattern(self, pattern: PatternMetrics) -> bool:
        """
        Save pattern to database or update if exists.

        Args:
            pattern: PatternMetrics object

        Returns:
            True if new pattern, False if updated existing
        """
        # Check if pattern already exists
        existing = self.service.get_pattern_details(pattern.pattern_id)

        if existing:
            # Update occurrence count
            new_count = existing.occurrence_count + pattern.occurrence_count
            logger.info(f"[SAVE] Updating existing pattern {pattern.pattern_id}: {existing.occurrence_count} -> {new_count}")

            self.service.update_occurrence_count(pattern.pattern_id, new_count)
            return False  # Updated existing

        else:
            # Insert new pattern
            logger.info(f"[SAVE] Creating new pattern {pattern.pattern_id}: {pattern.tool_sequence}")

            pattern_data = {
                'pattern_id': pattern.pattern_id,
                'status': pattern.status,
                'tool_sequence': pattern.tool_sequence,
                'confidence_score': pattern.confidence_score,
                'occurrence_count': pattern.occurrence_count,
                'estimated_savings_usd': pattern.estimated_savings_usd,
                'pattern_context': pattern.pattern_context,
                'example_sessions': pattern.example_sessions
            }

            self.service.create_pattern(pattern_data)
            return True  # New pattern

    def get_new_pending_patterns(self) -> List[PatternMetrics]:
        """
        Get patterns that are pending and were created in this analysis window.

        Returns:
            List of PatternMetrics for new pending patterns
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT * FROM pattern_approvals
                WHERE status = 'pending'
                AND created_at >= NOW() - INTERVAL '{self.window_hours} hours'
                ORDER BY (confidence_score * occurrence_count * estimated_savings_usd) DESC
            """)

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                patterns.append(PatternMetrics(
                    pattern_id=row['pattern_id'],
                    tool_sequence=row['tool_sequence'],
                    confidence_score=row['confidence_score'],
                    occurrence_count=row['occurrence_count'],
                    estimated_savings_usd=row['estimated_savings_usd'],
                    pattern_context=row['pattern_context'],
                    example_sessions=json.loads(row['example_sessions']) if row['example_sessions'] else [],
                    status=row['status']
                ))

            return patterns


class DailyPatternAnalysisCLI:
    """CLI interface for daily pattern analysis."""

    def __init__(self, args):
        """
        Initialize CLI.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.analyzer = DailyPatternAnalyzer(
            window_hours=args.hours,
            min_occurrences=args.min_occurrences
        )

    def run_analysis(self):
        """Execute pattern analysis."""
        if self.args.dry_run:
            print("\n🔍 DRY RUN MODE - No database changes will be made\n")

        # Run analysis
        results = self.analyzer.analyze_patterns()

        # Print summary
        self.print_analysis_summary(results)

        # Generate report if requested
        if self.args.report:
            self.generate_report(results)

        # Send notifications if requested
        if self.args.notify:
            self.send_notifications()

        return results

    def print_analysis_summary(self, results: Dict[str, Any]):
        """Print summary of analysis."""
        print("\n" + "=" * 80)
        print("DAILY PATTERN ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Analysis Window:     {self.args.hours} hours")
        print(f"Total Sessions:      {results['total_sessions']}")
        print(f"Patterns Discovered: {results['patterns_found']}")
        print(f"  - New Patterns:    {results['new_patterns']}")
        print(f"  - Updated:         {results['updated_patterns']}")
        print(f"\nClassification:")
        print(f"  - Auto-Approved:   {results['auto_approved']}")
        print(f"  - Pending Review:  {results['pending']}")
        print(f"  - Auto-Rejected:   {results['auto_rejected']}")
        print(f"\nEstimated Total Savings: ${results['total_savings']:,.2f}")
        print("=" * 80 + "\n")

    def generate_report(self, results: Dict[str, Any]):
        """Generate markdown analysis report."""
        report_dir = Path("logs")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"pattern_analysis_{timestamp}.md"

        with open(report_file, 'w') as f:
            f.write(f"# Daily Pattern Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Analysis Window:** {self.args.hours} hours\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Total Sessions: {results['total_sessions']}\n")
            f.write(f"- Patterns Discovered: {results['patterns_found']}\n")
            f.write(f"- New Patterns: {results['new_patterns']}\n")
            f.write(f"- Updated Patterns: {results['updated_patterns']}\n\n")
            f.write(f"## Classification\n\n")
            f.write(f"- Auto-Approved: {results['auto_approved']}\n")
            f.write(f"- Pending Review: {results['pending']}\n")
            f.write(f"- Auto-Rejected: {results['auto_rejected']}\n\n")
            f.write(f"## Impact\n\n")
            f.write(f"- Estimated Total Savings: ${results['total_savings']:,.2f}\n\n")

        print(f"📝 Report generated: {report_file}")

    def send_notifications(self):
        """Send notifications for new pending patterns."""
        new_pending = self.analyzer.get_new_pending_patterns()

        if not new_pending:
            print("📭 No new pending patterns requiring notification")
            return

        # Format notification message
        message = self._format_notification(new_pending)

        # Log notification
        self._log_notification(message)

        print(f"📬 Notification logged for {len(new_pending)} new pending pattern(s)")

    def _format_notification(self, patterns: List[PatternMetrics]) -> str:
        """Format notification message."""
        msg = f"""
New Patterns Requiring Review
==============================
Date: {datetime.now().isoformat()}

{len(patterns)} new patterns discovered that require manual approval.

"""
        for pattern in patterns[:5]:  # Show top 5
            msg += f"""
Pattern: {pattern.tool_sequence}
Confidence: {pattern.confidence_score:.1%}
Occurrences: {pattern.occurrence_count}
Estimated Savings: ${pattern.estimated_savings_usd:,.2f}
---
"""

        if len(patterns) > 5:
            msg += f"\n... and {len(patterns) - 5} more patterns\n"

        msg += f"\nReview via CLI: python scripts/review_patterns.py"
        msg += f"\nReview via Web UI: http://localhost:5173 (Panel 8)"

        return msg

    def _log_notification(self, message: str):
        """Log notification to file."""
        log_file = Path("logs/pattern_notifications.log")
        log_file.parent.mkdir(exist_ok=True)

        with open(log_file, 'a') as f:
            f.write(f"\n[{datetime.now().isoformat()}]\n")
            f.write(message)
            f.write("\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated daily pattern analysis from hook events',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last 24 hours
  python scripts/analyze_daily_patterns.py

  # Analyze last 48 hours
  python scripts/analyze_daily_patterns.py --hours 48

  # Dry run (no database changes)
  python scripts/analyze_daily_patterns.py --dry-run --verbose

  # Generate report
  python scripts/analyze_daily_patterns.py --report

  # With notifications
  python scripts/analyze_daily_patterns.py --notify
        """
    )

    # Analysis configuration
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Analysis window in hours (default: 24)'
    )
    parser.add_argument(
        '--min-occurrences',
        type=int,
        default=2,
        help='Minimum pattern occurrences to consider (default: 2)'
    )

    # Operation modes
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze but do not save to database'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate analysis report (markdown)'
    )
    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send notifications for new pending patterns'
    )

    # Output options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(name)s: %(message)s'
    )

    # Initialize CLI
    cli = DailyPatternAnalysisCLI(args)

    # Execute analysis
    try:
        results = cli.run_analysis()

        # Exit with appropriate code
        if results['patterns_found'] == 0:
            print("ℹ️  No patterns discovered in analysis window")
            sys.exit(0)
        else:
            print(f"✅ Analysis complete - {results['patterns_found']} patterns processed")
            sys.exit(0)

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
