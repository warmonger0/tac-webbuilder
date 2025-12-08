#!/usr/bin/env python3
"""
Error Analytics Service

Business logic for error pattern analysis and debugging recommendations.

Responsibilities:
- Analyze error rates and patterns
- Classify errors by type and phase
- Detect recurring error patterns
- Generate debugging recommendations
- Track failure trends over time
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from database import get_database_adapter

logger = logging.getLogger(__name__)


# Error classification patterns
ERROR_PATTERNS = {
    'import_error': {
        'keywords': ['ModuleNotFoundError', 'ImportError', 'No module named', 'cannot import'],
        'category': 'Dependency Issue',
        'recommendation': 'Add missing package to requirements.txt and ensure dependencies are installed',
        'severity': 'high'
    },
    'connection_error': {
        'keywords': ['ECONNREFUSED', 'Connection refused', 'Failed to connect', 'connection reset'],
        'category': 'Network Issue',
        'recommendation': 'Check service availability and port allocation. Verify backend/frontend are running',
        'severity': 'high'
    },
    'timeout_error': {
        'keywords': ['timeout', 'timed out', 'TimeoutError', 'deadline exceeded'],
        'category': 'Performance Issue',
        'recommendation': 'Increase timeout threshold or optimize long-running operations',
        'severity': 'medium'
    },
    'syntax_error': {
        'keywords': ['SyntaxError', 'invalid syntax', 'unexpected token'],
        'category': 'Code Quality',
        'recommendation': 'Run linter before committing. Check for Python/JS syntax errors',
        'severity': 'high'
    },
    'type_error': {
        'keywords': ['TypeError', 'type object', 'is not a function', 'is not callable'],
        'category': 'Type Issue',
        'recommendation': 'Add type hints and use mypy/TypeScript checking',
        'severity': 'medium'
    },
    'file_not_found': {
        'keywords': ['FileNotFoundError', 'ENOENT', 'no such file', 'file does not exist'],
        'category': 'File System Issue',
        'recommendation': 'Verify file paths and ensure required files exist before accessing',
        'severity': 'medium'
    },
    'permission_error': {
        'keywords': ['PermissionError', 'EACCES', 'permission denied', 'access denied'],
        'category': 'Permission Issue',
        'recommendation': 'Check file/directory permissions. May need sudo or ownership changes',
        'severity': 'medium'
    },
    'api_error': {
        'keywords': ['API error', '404', '500', '503', 'status code', 'HTTP error'],
        'category': 'API Issue',
        'recommendation': 'Check API endpoint availability and request format. Verify API keys',
        'severity': 'high'
    },
    'database_error': {
        'keywords': ['DatabaseError', 'SQL error', 'constraint violation', 'foreign key'],
        'category': 'Database Issue',
        'recommendation': 'Check database schema and query syntax. Verify foreign key relationships',
        'severity': 'high'
    },
    'git_error': {
        'keywords': ['git error', 'merge conflict', 'divergent branches', 'fatal: not a git'],
        'category': 'Git Issue',
        'recommendation': 'Resolve merge conflicts and ensure git repository is properly initialized',
        'severity': 'medium'
    }
}


class ErrorAnalyticsService:
    """Service for error analytics operations."""

    def __init__(self):
        """Initialize the error analytics service."""
        self.db = get_database_adapter()

    def get_error_summary(self, days: int = 30) -> Dict:
        """
        Get summary statistics for workflow errors.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with error summary statistics
        """
        logger.info(f"Generating error summary for last {days} days")

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get all workflows in the time period
        query = """
            SELECT status, error_message, current_phase
            FROM workflow_history
            WHERE started_at >= ?
        """

        rows = self.db.execute_query(query, (cutoff_date,))

        total_workflows = len(rows)
        failed_workflows = [r for r in rows if r[0] == 'failed']
        failed_count = len(failed_workflows)

        if total_workflows == 0:
            return {
                'total_workflows': 0,
                'failed_workflows': 0,
                'failure_rate': 0.0,
                'top_errors': [],
                'most_problematic_phase': None,
                'error_categories': {}
            }

        failure_rate = (failed_count / total_workflows) * 100

        # Classify errors and count patterns
        error_patterns = defaultdict(int)
        error_categories = defaultdict(int)
        phase_errors = defaultdict(int)

        for workflow in failed_workflows:
            error_message = workflow[1] or "Unknown error"
            current_phase = workflow[2] or "Unknown"

            # Classify error
            pattern_name = self.classify_error(error_message)
            error_patterns[pattern_name] += 1

            # Get category
            if pattern_name in ERROR_PATTERNS:
                category = ERROR_PATTERNS[pattern_name]['category']
                error_categories[category] += 1

            # Track phase
            phase_errors[current_phase] += 1

        # Get top errors
        top_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get most problematic phase
        most_problematic_phase = max(phase_errors.items(), key=lambda x: x[1])[0] if phase_errors else None

        return {
            'total_workflows': total_workflows,
            'failed_workflows': failed_count,
            'failure_rate': round(failure_rate, 2),
            'top_errors': top_errors,
            'most_problematic_phase': most_problematic_phase,
            'error_categories': dict(error_categories)
        }

    def analyze_by_phase(self, days: int = 30) -> Dict:
        """
        Analyze error rates by workflow phase.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with phase error breakdown
        """
        logger.info(f"Analyzing errors by phase for last {days} days")

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get all workflows with their phases
        query = """
            SELECT current_phase, status
            FROM workflow_history
            WHERE started_at >= ?
        """

        rows = self.db.execute_query(query, (cutoff_date,))

        phase_totals = defaultdict(int)
        phase_errors = defaultdict(int)

        for row in rows:
            phase = row[0] or "Unknown"
            status = row[1]

            phase_totals[phase] += 1
            if status == 'failed':
                phase_errors[phase] += 1

        # Calculate failure rates
        phase_failure_rates = {}
        for phase in phase_totals:
            if phase_totals[phase] > 0:
                rate = (phase_errors[phase] / phase_totals[phase]) * 100
                phase_failure_rates[phase] = round(rate, 2)

        total_errors = sum(phase_errors.values())

        # Find most error-prone phase
        most_error_prone = None
        if phase_failure_rates:
            most_error_prone = max(phase_failure_rates.items(), key=lambda x: x[1])[0]

        return {
            'phase_error_counts': dict(phase_errors),
            'phase_failure_rates': phase_failure_rates,
            'total_errors': total_errors,
            'most_error_prone_phase': most_error_prone
        }

    def find_error_patterns(self, days: int = 30) -> List[Dict]:
        """
        Detect recurring error patterns.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            List of error pattern dictionaries
        """
        logger.info(f"Finding error patterns for last {days} days")

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get all failed workflows with error messages
        query = """
            SELECT adw_id, error_message
            FROM workflow_history
            WHERE status = 'failed' AND started_at >= ?
        """

        rows = self.db.execute_query(query, (cutoff_date,))

        # Group by pattern
        pattern_data = defaultdict(lambda: {
            'count': 0,
            'example': '',
            'workflows': []
        })

        for row in rows:
            adw_id = row[0]
            error_message = row[1] or "Unknown error"

            pattern_name = self.classify_error(error_message)
            pattern_data[pattern_name]['count'] += 1
            pattern_data[pattern_name]['workflows'].append(adw_id)

            # Store first example
            if not pattern_data[pattern_name]['example']:
                # Truncate long error messages
                pattern_data[pattern_name]['example'] = error_message[:200]

        # Build pattern list
        patterns = []
        for pattern_name, data in sorted(pattern_data.items(), key=lambda x: x[1]['count'], reverse=True):
            pattern_info = ERROR_PATTERNS.get(pattern_name, {
                'category': 'Unknown',
                'recommendation': 'Review error message and stack trace for root cause',
                'severity': 'medium'
            })

            patterns.append({
                'pattern_name': pattern_name.replace('_', ' ').title(),
                'pattern_category': pattern_info['category'],
                'occurrences': data['count'],
                'example_message': data['example'],
                'affected_workflows': data['workflows'][:10],  # Limit to first 10
                'recommendation': pattern_info['recommendation'],
                'severity': pattern_info['severity']
            })

        return patterns

    def get_failure_trends(self, days: int = 30) -> Dict:
        """
        Analyze error trends over time.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with trend data
        """
        logger.info(f"Analyzing error trends for last {days} days")

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get daily error counts
        query = """
            SELECT DATE(started_at) as date, status
            FROM workflow_history
            WHERE started_at >= ?
            ORDER BY date
        """

        rows = self.db.execute_query(query, (cutoff_date,))

        # Group by date
        daily_data = defaultdict(lambda: {'total': 0, 'failed': 0})

        for row in rows:
            date = row[0]
            status = row[1]

            daily_data[date]['total'] += 1
            if status == 'failed':
                daily_data[date]['failed'] += 1

        # Build daily error list
        daily_errors = []
        for date in sorted(daily_data.keys()):
            data = daily_data[date]
            error_count = data['failed']
            total = data['total']
            failure_rate = (error_count / total * 100) if total > 0 else 0.0

            daily_errors.append({
                'date': date,
                'error_count': error_count,
                'failure_rate': round(failure_rate, 2),
                'workflow_count': total
            })

        # Calculate trend
        if len(daily_errors) >= 2:
            first_week = [d['failure_rate'] for d in daily_errors[:7]]
            last_week = [d['failure_rate'] for d in daily_errors[-7:]]

            avg_first = sum(first_week) / len(first_week) if first_week else 0
            avg_last = sum(last_week) / len(last_week) if last_week else 0

            percentage_change = ((avg_last - avg_first) / avg_first * 100) if avg_first > 0 else 0

            if percentage_change > 10:
                trend_direction = 'increasing'
            elif percentage_change < -10:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            percentage_change = 0
            trend_direction = 'stable'

        total_failures = sum(d['error_count'] for d in daily_errors)
        avg_daily = total_failures / len(daily_errors) if daily_errors else 0

        return {
            'daily_errors': daily_errors,
            'trend_direction': trend_direction,
            'percentage_change': round(percentage_change, 2),
            'average_daily_failures': round(avg_daily, 2)
        }

    def get_debugging_recommendations(self, days: int = 30) -> List[Dict]:
        """
        Generate debugging recommendations based on error analysis.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            List of debugging recommendation dictionaries
        """
        logger.info(f"Generating debugging recommendations for last {days} days")

        # Get error patterns
        patterns = self.find_error_patterns(days)

        recommendations = []

        for pattern in patterns:
            # Only recommend for patterns with 2+ occurrences
            if pattern['occurrences'] >= 2:
                severity = pattern['severity']

                # Estimate fix time based on severity and occurrences
                if pattern['occurrences'] >= 10:
                    fix_time = "1-2 hours (high priority - recurring issue)"
                elif pattern['occurrences'] >= 5:
                    fix_time = "30-60 minutes (medium priority)"
                else:
                    fix_time = "15-30 minutes (low priority)"

                recommendations.append({
                    'issue': f"{pattern['pattern_name']} occurring {pattern['occurrences']} times",
                    'severity': severity,
                    'root_cause': pattern['pattern_category'],
                    'solution': pattern['recommendation'],
                    'estimated_fix_time': fix_time,
                    'affected_count': pattern['occurrences']
                })

        # Sort by severity (high -> medium -> low) and then by count
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: (severity_order[x['severity']], -x['affected_count']))

        return recommendations

    def classify_error(self, error_message: str) -> str:
        """
        Classify error message into pattern category.

        Args:
            error_message: Error message to classify

        Returns:
            Pattern name (e.g., 'import_error', 'connection_error')
        """
        if not error_message:
            return 'unknown'

        error_lower = error_message.lower()

        for pattern_name, pattern_info in ERROR_PATTERNS.items():
            keywords = pattern_info['keywords']
            if any(kw.lower() in error_lower for kw in keywords):
                return pattern_name

        return 'unknown'
