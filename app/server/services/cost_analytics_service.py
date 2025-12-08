#!/usr/bin/env python3
"""
Cost Analytics Service

Business logic for cost attribution analytics and optimization recommendations.

Responsibilities:
- Analyze costs by phase (Plan, Build, Test, etc.)
- Analyze costs by workflow type
- Analyze cost trends over time
- Identify optimization opportunities
- Generate cost breakdown reports
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
class PhaseBreakdown:
    """Cost breakdown by workflow phase."""
    phase_costs: Dict[str, float]  # {phase: total_cost}
    phase_percentages: Dict[str, float]  # {phase: percentage}
    phase_counts: Dict[str, int]  # {phase: occurrence_count}
    total: float
    average_per_workflow: float
    workflow_count: int

    def to_dict(self):
        return asdict(self)


@dataclass
class WorkflowBreakdown:
    """Cost breakdown by workflow type."""
    by_type: Dict[str, float]  # {workflow_type: total_cost}
    count_by_type: Dict[str, int]  # {workflow_type: count}
    average_by_type: Dict[str, float]  # {workflow_type: avg_cost}

    def to_dict(self):
        return asdict(self)


@dataclass
class TimeSeriesDataPoint:
    """Single data point in time series."""
    date: str  # ISO format date
    cost: float
    workflow_count: int


@dataclass
class TrendAnalysis:
    """Cost trend analysis over time."""
    daily_costs: List[TimeSeriesDataPoint]  # [(date, cost, count)]
    moving_average: List[float]  # 7-day moving average
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    percentage_change: float  # Overall percentage change
    total_cost: float
    average_daily_cost: float

    def to_dict(self):
        result = asdict(self)
        # Convert TimeSeriesDataPoint objects to dicts
        result['daily_costs'] = [asdict(dp) for dp in self.daily_costs]
        return result


@dataclass
class OptimizationOpportunity:
    """Cost optimization opportunity."""
    category: str  # 'phase', 'workflow_type', 'outlier'
    description: str
    current_cost: float
    target_cost: float
    estimated_savings: float
    recommendation: str
    priority: str  # 'high', 'medium', 'low'

    def to_dict(self):
        return asdict(self)


class CostAnalyticsService:
    """Service for cost analytics operations."""

    def analyze_by_phase(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> PhaseBreakdown:
        """
        Aggregate costs by ADW phase.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            days: Number of days to look back (default: 30)

        Returns:
            PhaseBreakdown with cost analysis by phase
        """
        start_date, end_date = self._resolve_date_range(start_date, end_date, days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get all workflows with cost_breakdown in the date range
            cursor.execute("""
                SELECT
                    cost_breakdown,
                    actual_cost_total
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND actual_cost_total > 0
                  AND cost_breakdown IS NOT NULL
            """, (start_date, end_date))

            rows = cursor.fetchall()

            if not rows:
                logger.info("[CostAnalyticsService] No workflows found in date range")
                return PhaseBreakdown(
                    phase_costs={},
                    phase_percentages={},
                    phase_counts={},
                    total=0.0,
                    average_per_workflow=0.0,
                    workflow_count=0
                )

            # Aggregate costs by phase
            phase_costs = defaultdict(float)
            phase_counts = defaultdict(int)
            total_cost = 0.0

            for row in rows:
                cost_breakdown = row['cost_breakdown']

                # Parse cost_breakdown if it's a string (PostgreSQL may return dict or string)
                if isinstance(cost_breakdown, str):
                    try:
                        cost_breakdown = json.loads(cost_breakdown)
                    except json.JSONDecodeError:
                        logger.warning(f"[CostAnalyticsService] Failed to parse cost_breakdown")
                        continue

                # Extract by_phase costs
                by_phase = cost_breakdown.get('by_phase', {})
                if not by_phase:
                    # Fallback: use actual_cost_total if no phase breakdown
                    continue

                for phase, cost in by_phase.items():
                    if cost and cost > 0:
                        phase_costs[phase] += cost
                        phase_counts[phase] += 1
                        total_cost += cost

            # Calculate percentages
            phase_percentages = {}
            if total_cost > 0:
                for phase, cost in phase_costs.items():
                    phase_percentages[phase] = (cost / total_cost) * 100

            workflow_count = len(rows)
            average_per_workflow = total_cost / workflow_count if workflow_count > 0 else 0.0

            logger.info(
                f"[CostAnalyticsService] Analyzed {workflow_count} workflows, "
                f"total cost: ${total_cost:.2f}"
            )

            return PhaseBreakdown(
                phase_costs=dict(phase_costs),
                phase_percentages=phase_percentages,
                phase_counts=dict(phase_counts),
                total=total_cost,
                average_per_workflow=average_per_workflow,
                workflow_count=workflow_count
            )

    def analyze_by_workflow_type(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> WorkflowBreakdown:
        """
        Aggregate costs by workflow type.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            days: Number of days to look back (default: 30)

        Returns:
            WorkflowBreakdown with cost analysis by workflow type
        """
        start_date, end_date = self._resolve_date_range(start_date, end_date, days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COALESCE(workflow_template, workflow_type, 'unknown') as type,
                    SUM(actual_cost_total) as total_cost,
                    COUNT(*) as count,
                    AVG(actual_cost_total) as avg_cost
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND actual_cost_total > 0
                GROUP BY COALESCE(workflow_template, workflow_type, 'unknown')
                ORDER BY total_cost DESC
            """, (start_date, end_date))

            rows = cursor.fetchall()

            by_type = {}
            count_by_type = {}
            average_by_type = {}

            for row in rows:
                workflow_type = row['type']
                by_type[workflow_type] = float(row['total_cost'])
                count_by_type[workflow_type] = row['count']
                average_by_type[workflow_type] = float(row['avg_cost'])

            logger.info(
                f"[CostAnalyticsService] Analyzed {len(by_type)} workflow types"
            )

            return WorkflowBreakdown(
                by_type=by_type,
                count_by_type=count_by_type,
                average_by_type=average_by_type
            )

    def analyze_by_time_period(
        self,
        period: str = 'day',
        days: int = 30
    ) -> TrendAnalysis:
        """
        Analyze costs over time with trend analysis.

        Args:
            period: Time period ('day', 'week') - currently only 'day' supported
            days: Number of days to look back (default: 30)

        Returns:
            TrendAnalysis with time series data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    SUM(actual_cost_total) as daily_cost,
                    COUNT(*) as workflow_count
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND actual_cost_total > 0
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()

            # Build time series
            daily_costs = []
            for row in rows:
                daily_costs.append(TimeSeriesDataPoint(
                    date=str(row['date']),
                    cost=float(row['daily_cost']),
                    workflow_count=row['workflow_count']
                ))

            # Calculate moving average (7-day)
            moving_average = self._calculate_moving_average([dp.cost for dp in daily_costs], window=7)

            # Calculate trend
            trend_direction, percentage_change = self._calculate_trend(daily_costs)

            # Calculate totals
            total_cost = sum(dp.cost for dp in daily_costs)
            average_daily_cost = total_cost / len(daily_costs) if daily_costs else 0.0

            logger.info(
                f"[CostAnalyticsService] Analyzed {days} days, "
                f"trend: {trend_direction}, change: {percentage_change:.1f}%"
            )

            return TrendAnalysis(
                daily_costs=daily_costs,
                moving_average=moving_average,
                trend_direction=trend_direction,
                percentage_change=percentage_change,
                total_cost=total_cost,
                average_daily_cost=average_daily_cost
            )

    def get_optimization_opportunities(
        self,
        days: int = 30
    ) -> List[OptimizationOpportunity]:
        """
        Identify cost optimization opportunities.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            List of OptimizationOpportunity objects
        """
        opportunities = []

        # Analyze phase costs for anomalies
        phase_breakdown = self.analyze_by_phase(days=days)
        phase_opportunities = self._detect_phase_anomalies(phase_breakdown)
        opportunities.extend(phase_opportunities)

        # Analyze workflow types for inefficiencies
        workflow_breakdown = self.analyze_by_workflow_type(days=days)
        workflow_opportunities = self._detect_workflow_inefficiencies(workflow_breakdown)
        opportunities.extend(workflow_opportunities)

        # Detect high-cost outliers
        outlier_opportunities = self._detect_outliers(days=days)
        opportunities.extend(outlier_opportunities)

        # Sort by estimated savings (highest first)
        opportunities.sort(key=lambda x: x.estimated_savings, reverse=True)

        logger.info(
            f"[CostAnalyticsService] Found {len(opportunities)} optimization opportunities"
        )

        return opportunities

    def _detect_phase_anomalies(self, phase_breakdown: PhaseBreakdown) -> List[OptimizationOpportunity]:
        """Detect phases with abnormally high costs."""
        opportunities = []

        if not phase_breakdown.phase_costs:
            return opportunities

        # Expected phase cost percentages (based on typical ADW workflows)
        expected_percentages = {
            'plan': 15.0,
            'validate': 10.0,
            'build': 25.0,
            'lint': 5.0,
            'test': 20.0,
            'review': 10.0,
            'document': 8.0,
            'ship': 5.0,
            'cleanup': 2.0
        }

        for phase, actual_pct in phase_breakdown.phase_percentages.items():
            phase_lower = phase.lower()
            expected_pct = expected_percentages.get(phase_lower, 15.0)

            # Flag if phase is >20% above expected
            if actual_pct > expected_pct * 1.2:
                current_cost = phase_breakdown.phase_costs[phase]
                target_cost = (expected_pct / 100) * phase_breakdown.total
                estimated_savings = (current_cost - target_cost) * 4  # Monthly estimate

                opportunities.append(OptimizationOpportunity(
                    category='phase',
                    description=f"{phase} phase: {actual_pct:.1f}% of costs (expected: {expected_pct:.1f}%)",
                    current_cost=current_cost,
                    target_cost=target_cost,
                    estimated_savings=estimated_savings,
                    recommendation=self._get_phase_recommendation(phase_lower),
                    priority='high' if actual_pct > expected_pct * 1.5 else 'medium'
                ))

        return opportunities

    def _detect_workflow_inefficiencies(
        self,
        workflow_breakdown: WorkflowBreakdown
    ) -> List[OptimizationOpportunity]:
        """Detect workflow types with high average costs."""
        opportunities = []

        if not workflow_breakdown.average_by_type:
            return opportunities

        # Calculate overall average
        overall_avg = sum(workflow_breakdown.by_type.values()) / sum(workflow_breakdown.count_by_type.values())

        for workflow_type, avg_cost in workflow_breakdown.average_by_type.items():
            # Flag if workflow type is >50% above average
            if avg_cost > overall_avg * 1.5:
                count = workflow_breakdown.count_by_type[workflow_type]
                current_total = workflow_breakdown.by_type[workflow_type]
                target_total = overall_avg * count
                estimated_savings = (current_total - target_total) * 4  # Monthly estimate

                opportunities.append(OptimizationOpportunity(
                    category='workflow_type',
                    description=f"{workflow_type}: ${avg_cost:.2f}/workflow (avg: ${overall_avg:.2f})",
                    current_cost=current_total,
                    target_cost=target_total,
                    estimated_savings=estimated_savings,
                    recommendation=f"Review {workflow_type} workflow configuration for optimization opportunities",
                    priority='medium'
                ))

        return opportunities

    def _detect_outliers(self, days: int = 30) -> List[OptimizationOpportunity]:
        """Detect individual workflows with abnormally high costs."""
        opportunities = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get cost statistics
            cursor.execute("""
                SELECT
                    AVG(actual_cost_total) as avg_cost,
                    STDDEV(actual_cost_total) as stddev_cost
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND actual_cost_total > 0
            """, (start_date.isoformat(), end_date.isoformat()))

            stats = cursor.fetchone()
            if not stats or not stats['avg_cost']:
                return opportunities

            avg_cost = float(stats['avg_cost'])
            stddev_cost = float(stats['stddev_cost']) if stats['stddev_cost'] else 0

            # Find outliers (>2 standard deviations above mean)
            threshold = avg_cost + (2 * stddev_cost)

            cursor.execute("""
                SELECT COUNT(*) as outlier_count,
                       SUM(actual_cost_total) as outlier_total_cost
                FROM workflow_history
                WHERE created_at >= %s
                  AND created_at <= %s
                  AND actual_cost_total > %s
            """, (start_date.isoformat(), end_date.isoformat(), threshold))

            result = cursor.fetchone()

            if result and result['outlier_count'] > 0:
                outlier_count = result['outlier_count']
                outlier_total = float(result['outlier_total_cost'])
                target_cost = avg_cost * outlier_count
                estimated_savings = (outlier_total - target_cost) * 4  # Monthly estimate

                opportunities.append(OptimizationOpportunity(
                    category='outlier',
                    description=f"{outlier_count} high-cost workflows (>${threshold:.2f} each)",
                    current_cost=outlier_total,
                    target_cost=target_cost,
                    estimated_savings=estimated_savings,
                    recommendation="Review high-cost workflows for retry loops, inefficient prompts, or excessive tool usage",
                    priority='high' if outlier_count > 5 else 'medium'
                ))

        return opportunities

    def _get_phase_recommendation(self, phase: str) -> str:
        """Get optimization recommendation for a specific phase."""
        recommendations = {
            'plan': "Enable prompt caching for planning phase, use structured inputs",
            'validate': "Implement validation result caching",
            'build': "Enable external tool usage (ruff, mypy) to reduce LLM costs in build phase",
            'lint': "Use external linting tools (ruff) instead of LLM-based linting",
            'test': "Implement test result caching, use external test runners (pytest)",
            'review': "Cache code review results for similar changes",
            'document': "Use template-based documentation generation",
            'ship': "Optimize git operations and PR creation",
            'cleanup': "Review cleanup process for unnecessary operations"
        }
        return recommendations.get(phase, "Review phase configuration for optimization opportunities")

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
        daily_costs: List[TimeSeriesDataPoint]
    ) -> Tuple[str, float]:
        """Calculate overall trend direction and percentage change."""
        if len(daily_costs) < 2:
            return 'stable', 0.0

        # Compare first week vs last week averages
        first_week = daily_costs[:7] if len(daily_costs) >= 7 else daily_costs[:len(daily_costs)//2]
        last_week = daily_costs[-7:] if len(daily_costs) >= 7 else daily_costs[len(daily_costs)//2:]

        first_avg = sum(dp.cost for dp in first_week) / len(first_week)
        last_avg = sum(dp.cost for dp in last_week) / len(last_week)

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
