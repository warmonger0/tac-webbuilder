#!/usr/bin/env python3
"""
Latency Analytics Service

Business logic for workflow performance analysis and bottleneck identification.

Responsibilities:
- Analyze execution times by phase (p50, p95, p99)
- Identify performance bottlenecks
- Track latency trends over time
- Detect slow workflows (outliers)
- Generate optimization recommendations
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from database import get_database_adapter

logger = logging.getLogger(__name__)


@dataclass
class PhaseStats:
    """Statistics for a single phase."""
    p50: float  # Median latency
    p95: float  # 95th percentile latency
    p99: float  # 99th percentile latency
    average: float  # Average latency
    min: float  # Minimum latency
    max: float  # Maximum latency
    std_dev: float  # Standard deviation
    sample_count: int  # Number of samples

    def to_dict(self):
        return asdict(self)


@dataclass
class PhaseLatencyBreakdown:
    """Latency breakdown by workflow phase."""
    phase_latencies: Dict[str, PhaseStats]  # {phase: stats}
    total_duration_avg: float

    def to_dict(self):
        result = {
            'phase_latencies': {
                phase: stats.to_dict()
                for phase, stats in self.phase_latencies.items()
            },
            'total_duration_avg': self.total_duration_avg
        }
        return result


@dataclass
class LatencySummary:
    """Overall latency summary statistics."""
    total_workflows: int
    average_duration_seconds: float
    p50_duration: float
    p95_duration: float
    p99_duration: float
    slowest_phase: str
    slowest_phase_avg: float

    def to_dict(self):
        return asdict(self)


@dataclass
class Bottleneck:
    """Identified performance bottleneck."""
    phase: str
    p95_latency: float
    threshold: float
    percentage_over_threshold: float
    affected_workflows: int
    recommendation: str
    estimated_speedup: str

    def to_dict(self):
        return asdict(self)


@dataclass
class TimeSeriesDataPoint:
    """Single data point in time series."""
    date: str  # ISO format date
    duration: float
    workflow_count: int


@dataclass
class TrendData:
    """Latency trend analysis over time."""
    daily_latencies: List[TimeSeriesDataPoint]
    moving_average: List[float]  # 7-day moving average
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    percentage_change: float  # Overall percentage change
    average_daily_duration: float

    def to_dict(self):
        result = asdict(self)
        # Convert TimeSeriesDataPoint objects to dicts
        result['daily_latencies'] = [asdict(dp) for dp in self.daily_latencies]
        return result


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation for improving latency."""
    target: str  # Phase or workflow type
    current_latency: float
    target_latency: float
    improvement_percentage: float
    actions: List[str]

    def to_dict(self):
        return asdict(self)


class LatencyAnalyticsService:
    """Service for latency analytics operations."""

    def get_latency_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> LatencySummary:
        """
        Get summary statistics for workflow latencies.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            days: Number of days to look back (default: 30)

        Returns:
            LatencySummary with overall latency statistics
        """
        start_date, end_date = self._resolve_date_range(start_date, end_date, days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all completed workflows with durations
            cursor.execute("""
                SELECT
                    duration_seconds,
                    phase_durations
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND duration_seconds IS NOT NULL
                  AND duration_seconds > 0
                  AND status = 'completed'
            """, (start_date, end_date))

            rows = cursor.fetchall()

            if not rows:
                logger.info("[LatencyAnalyticsService] No completed workflows found in date range")
                return LatencySummary(
                    total_workflows=0,
                    average_duration_seconds=0.0,
                    p50_duration=0.0,
                    p95_duration=0.0,
                    p99_duration=0.0,
                    slowest_phase="",
                    slowest_phase_avg=0.0
                )

            # Extract durations
            durations = [float(row['duration_seconds']) for row in rows]

            # Calculate percentiles
            percentiles = self.calculate_percentiles(durations)

            # Find slowest phase across all workflows
            phase_durations_all = defaultdict(list)
            for row in rows:
                phase_durations = row['phase_durations']

                # Parse phase_durations if it's a string (PostgreSQL may return dict or string)
                if isinstance(phase_durations, str):
                    try:
                        phase_durations = json.loads(phase_durations)
                    except json.JSONDecodeError:
                        logger.warning("[LatencyAnalyticsService] Failed to parse phase_durations")
                        continue

                if phase_durations:
                    for phase, duration in phase_durations.items():
                        if duration and duration > 0:
                            phase_durations_all[phase].append(float(duration))

            # Find slowest phase by average
            slowest_phase = ""
            slowest_phase_avg = 0.0
            if phase_durations_all:
                for phase, phase_durs in phase_durations_all.items():
                    avg = statistics.mean(phase_durs)
                    if avg > slowest_phase_avg:
                        slowest_phase_avg = avg
                        slowest_phase = phase

            logger.info(
                f"[LatencyAnalyticsService] Analyzed {len(durations)} workflows, "
                f"avg duration: {percentiles['average']:.1f}s, slowest phase: {slowest_phase}"
            )

            return LatencySummary(
                total_workflows=len(durations),
                average_duration_seconds=percentiles['average'],
                p50_duration=percentiles['p50'],
                p95_duration=percentiles['p95'],
                p99_duration=percentiles['p99'],
                slowest_phase=slowest_phase,
                slowest_phase_avg=slowest_phase_avg
            )

    def analyze_by_phase(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> PhaseLatencyBreakdown:
        """
        Analyze latencies broken down by workflow phase.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            days: Number of days to look back (default: 30)

        Returns:
            PhaseLatencyBreakdown with percentile analysis per phase
        """
        start_date, end_date = self._resolve_date_range(start_date, end_date, days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all workflows with phase_durations
            cursor.execute("""
                SELECT
                    phase_durations,
                    duration_seconds
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND phase_durations IS NOT NULL
                  AND status = 'completed'
            """, (start_date, end_date))

            rows = cursor.fetchall()

            if not rows:
                logger.info("[LatencyAnalyticsService] No workflows found with phase_durations")
                return PhaseLatencyBreakdown(
                    phase_latencies={},
                    total_duration_avg=0.0
                )

            # Aggregate phase durations
            phase_durations_all = defaultdict(list)
            total_durations = []

            for row in rows:
                phase_durations = row['phase_durations']

                # Parse phase_durations if it's a string
                if isinstance(phase_durations, str):
                    try:
                        phase_durations = json.loads(phase_durations)
                    except json.JSONDecodeError:
                        logger.warning("[LatencyAnalyticsService] Failed to parse phase_durations")
                        continue

                if phase_durations:
                    for phase, duration in phase_durations.items():
                        if duration and duration > 0:
                            phase_durations_all[phase].append(float(duration))

                # Track total durations
                if row['duration_seconds'] and row['duration_seconds'] > 0:
                    total_durations.append(float(row['duration_seconds']))

            # Calculate percentiles for each phase
            phase_latencies = {}
            for phase, durations in phase_durations_all.items():
                percentiles = self.calculate_percentiles(durations)
                phase_latencies[phase] = PhaseStats(
                    p50=percentiles['p50'],
                    p95=percentiles['p95'],
                    p99=percentiles['p99'],
                    average=percentiles['average'],
                    min=percentiles['min'],
                    max=percentiles['max'],
                    std_dev=percentiles['std_dev'],
                    sample_count=len(durations)
                )

            total_duration_avg = statistics.mean(total_durations) if total_durations else 0.0

            logger.info(
                f"[LatencyAnalyticsService] Analyzed {len(phase_latencies)} phases "
                f"across {len(rows)} workflows"
            )

            return PhaseLatencyBreakdown(
                phase_latencies=phase_latencies,
                total_duration_avg=total_duration_avg
            )

    def find_bottlenecks(
        self,
        threshold_seconds: int = 300,
        days: int = 30
    ) -> List[Bottleneck]:
        """
        Identify performance bottlenecks (phases consistently exceeding threshold).

        Args:
            threshold_seconds: Threshold in seconds for bottleneck detection (default: 300s = 5min)
            days: Number of days to analyze (default: 30)

        Returns:
            List of Bottleneck objects
        """
        phase_breakdown = self.analyze_by_phase(days=days)

        if not phase_breakdown.phase_latencies:
            return []

        bottlenecks = []

        for phase, stats in phase_breakdown.phase_latencies.items():
            # Flag phases where p95 > threshold
            if stats.p95 > threshold_seconds:
                # Calculate how many workflows exceed threshold
                # Approximate: if p95 > threshold, then ~5% of workflows exceed it
                # But we'll be conservative and estimate based on p95
                percentage_over = 5.0 if stats.p95 > threshold_seconds else 0.0

                # If average is also high, more workflows are affected
                if stats.average > threshold_seconds:
                    percentage_over = 50.0  # Estimate ~50% if average exceeds

                affected_workflows = int((percentage_over / 100.0) * stats.sample_count)

                # Generate recommendation
                recommendation = self._get_phase_optimization_recommendation(phase, stats.p95)

                # Estimate speedup potential
                if stats.p95 > threshold_seconds * 2:
                    estimated_speedup = "50-60% faster with optimization"
                elif stats.p95 > threshold_seconds * 1.5:
                    estimated_speedup = "30-40% faster with optimization"
                else:
                    estimated_speedup = "20-30% faster with optimization"

                bottlenecks.append(Bottleneck(
                    phase=phase,
                    p95_latency=stats.p95,
                    threshold=float(threshold_seconds),
                    percentage_over_threshold=percentage_over,
                    affected_workflows=affected_workflows,
                    recommendation=recommendation,
                    estimated_speedup=estimated_speedup
                ))

        # Sort by p95 latency (highest first)
        bottlenecks.sort(key=lambda x: x.p95_latency, reverse=True)

        logger.info(f"[LatencyAnalyticsService] Found {len(bottlenecks)} bottlenecks")

        return bottlenecks

    def get_latency_trends(
        self,
        period: str = 'day',
        days: int = 30
    ) -> TrendData:
        """
        Analyze latency trends over time.

        Args:
            period: Time period ('day', 'week') - currently only 'day' supported
            days: Number of days to look back (default: 30)

        Returns:
            TrendData with time series latency data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(*) as workflow_count
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND duration_seconds IS NOT NULL
                  AND duration_seconds > 0
                  AND status = 'completed'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()

            # Build time series
            daily_latencies = []
            for row in rows:
                daily_latencies.append(TimeSeriesDataPoint(
                    date=str(row['date']),
                    duration=float(row['avg_duration']),
                    workflow_count=row['workflow_count']
                ))

            # Calculate moving average (7-day)
            moving_average = self._calculate_moving_average(
                [dp.duration for dp in daily_latencies],
                window=7
            )

            # Calculate trend
            trend_direction, percentage_change = self._calculate_trend(daily_latencies)

            # Calculate average
            average_daily_duration = (
                statistics.mean([dp.duration for dp in daily_latencies])
                if daily_latencies else 0.0
            )

            logger.info(
                f"[LatencyAnalyticsService] Analyzed {days} days, "
                f"trend: {trend_direction}, change: {percentage_change:.1f}%"
            )

            return TrendData(
                daily_latencies=daily_latencies,
                moving_average=moving_average,
                trend_direction=trend_direction,
                percentage_change=percentage_change,
                average_daily_duration=average_daily_duration
            )

    def get_optimization_recommendations(
        self,
        days: int = 30
    ) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on latency analysis.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            List of OptimizationRecommendation objects
        """
        recommendations = []

        # Analyze phase latencies
        phase_breakdown = self.analyze_by_phase(days=days)

        if not phase_breakdown.phase_latencies:
            return recommendations

        # Sort phases by average latency (highest first)
        sorted_phases = sorted(
            phase_breakdown.phase_latencies.items(),
            key=lambda x: x[1].average,
            reverse=True
        )

        # Generate recommendations for top 3 slowest phases
        for phase, stats in sorted_phases[:3]:
            # Calculate percentage of total duration
            if phase_breakdown.total_duration_avg > 0:
                phase_percentage = (stats.average / phase_breakdown.total_duration_avg) * 100
            else:
                phase_percentage = 0.0

            # Only recommend if phase is >15% of total duration
            if phase_percentage > 15.0:
                # Estimate target latency (aim for 40% reduction)
                target_latency = stats.average * 0.6
                improvement_percentage = 40.0

                # Get phase-specific actions
                actions = self._get_optimization_actions(phase, stats.average)

                recommendations.append(OptimizationRecommendation(
                    target=f"{phase} Phase",
                    current_latency=stats.average,
                    target_latency=target_latency,
                    improvement_percentage=improvement_percentage,
                    actions=actions
                ))

        logger.info(
            f"[LatencyAnalyticsService] Generated {len(recommendations)} optimization recommendations"
        )

        return recommendations

    def calculate_percentiles(self, durations: List[float]) -> Dict[str, float]:
        """
        Calculate latency percentiles.

        Args:
            durations: List of duration values

        Returns:
            Dictionary with p50, p95, p99, average, min, max, std_dev
        """
        if not durations:
            return {
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'average': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std_dev': 0.0
            }

        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        # Calculate percentiles manually (simple implementation)
        def percentile(data, p):
            k = (n - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < n:
                return data[f] + c * (data[f + 1] - data[f])
            else:
                return data[f]

        return {
            'p50': percentile(sorted_durations, 50),
            'p95': percentile(sorted_durations, 95),
            'p99': percentile(sorted_durations, 99),
            'average': statistics.mean(durations),
            'min': min(durations),
            'max': max(durations),
            'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0.0
        }

    def detect_outliers(
        self,
        durations: List[float],
        threshold_std: float = 2.0
    ) -> List[int]:
        """
        Detect outlier workflows (>N standard deviations from mean).

        Args:
            durations: List of duration values
            threshold_std: Number of standard deviations for outlier detection (default: 2.0)

        Returns:
            List of indices of outlier durations
        """
        if len(durations) < 3:
            return []

        mean = statistics.mean(durations)
        std_dev = statistics.stdev(durations)

        outliers = []
        for i, duration in enumerate(durations):
            if abs(duration - mean) > threshold_std * std_dev:
                outliers.append(i)

        return outliers

    def _get_phase_optimization_recommendation(self, phase: str, latency: float) -> str:
        """Get optimization recommendation for a specific phase."""
        phase_lower = phase.lower()

        recommendations = {
            'plan': "Enable prompt caching for planning phase, use structured inputs to reduce LLM latency",
            'validate': "Implement validation result caching, parallelize validation checks where possible",
            'build': "Use incremental builds, enable dependency caching, parallelize build steps",
            'lint': "Run linters in parallel, cache linting results for unchanged files",
            'test': "Enable test result caching, run tests in parallel, skip redundant test suites",
            'review': "Cache code review results for similar changes, use parallel review processes",
            'document': "Use template-based documentation generation, cache documentation for unchanged code",
            'ship': "Optimize git operations, use shallow clones, parallelize PR creation steps",
            'cleanup': "Defer non-critical cleanup, run cleanup asynchronously"
        }

        return recommendations.get(
            phase_lower,
            f"Review {phase} phase for parallelization opportunities and caching"
        )

    def _get_optimization_actions(self, phase: str, latency: float) -> List[str]:
        """Get specific optimization actions for a phase."""
        phase_lower = phase.lower()

        actions_map = {
            'plan': [
                "Enable prompt caching for repeated planning patterns",
                "Use structured inputs to reduce LLM processing time",
                "Implement plan templates for common workflows"
            ],
            'build': [
                "Enable dependency caching (pip, npm)",
                "Use incremental builds where possible",
                "Parallelize independent build steps"
            ],
            'test': [
                "Enable test result caching",
                "Run test suites in parallel",
                "Skip redundant tests for unchanged code",
                "Use test sharding for large test suites"
            ],
            'lint': [
                "Run linters in parallel",
                "Cache linting results for unchanged files",
                "Use incremental linting where supported"
            ],
            'review': [
                "Cache review results for similar code patterns",
                "Parallelize independent review checks",
                "Use automated review tools where appropriate"
            ]
        }

        default_actions = [
            f"Profile {phase} phase to identify specific bottlenecks",
            "Look for parallelization opportunities",
            "Implement caching for repeated operations"
        ]

        return actions_map.get(phase_lower, default_actions)

    def _calculate_moving_average(self, values: List[float], window: int = 7) -> List[float]:
        """Calculate moving average for a list of values."""
        if len(values) < window:
            return values.copy()

        moving_avg = []
        for i in range(len(values)):
            if i < window - 1:
                # Not enough data points yet, use available data
                moving_avg.append(sum(values[:i+1]) / (i+1))
            else:
                # Calculate window average
                window_values = values[i-window+1:i+1]
                moving_avg.append(sum(window_values) / window)

        return moving_avg

    def _calculate_trend(
        self,
        daily_latencies: List[TimeSeriesDataPoint]
    ) -> Tuple[str, float]:
        """Calculate overall trend direction and percentage change."""
        if len(daily_latencies) < 2:
            return 'stable', 0.0

        # Compare first week vs last week averages
        first_week = daily_latencies[:7] if len(daily_latencies) >= 7 else daily_latencies[:len(daily_latencies)//2]
        last_week = daily_latencies[-7:] if len(daily_latencies) >= 7 else daily_latencies[len(daily_latencies)//2:]

        first_avg = sum(dp.duration for dp in first_week) / len(first_week)
        last_avg = sum(dp.duration for dp in last_week) / len(last_week)

        if first_avg == 0:
            return 'stable', 0.0

        percentage_change = ((last_avg - first_avg) / first_avg) * 100

        # Determine trend direction
        if abs(percentage_change) < 5:
            trend = 'stable'
        elif percentage_change > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        return trend, percentage_change

    def _resolve_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        days: int
    ) -> Tuple[str, str]:
        """Resolve start and end dates from inputs."""
        if end_date is None:
            end_date = datetime.now().isoformat()

        if start_date is None:
            # Calculate start_date from days
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            start_dt = end_dt - timedelta(days=days)
            start_date = start_dt.isoformat()

        return start_date, end_date
