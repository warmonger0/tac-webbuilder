"""
Tests for Error Analytics Service

Tests error pattern detection, phase analysis, trend analysis, and debugging recommendations.

Run with:
    cd app/server
    pytest tests/services/test_error_analytics_service.py -v
    pytest tests/services/test_error_analytics_service.py -v -k "test_get_error_summary"
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from services.error_analytics_service import ErrorAnalyticsService


@pytest.fixture
def mock_db_adapter():
    """Create a mock database adapter."""
    adapter = MagicMock()
    return adapter


@pytest.fixture
def service(mock_db_adapter):
    """Create ErrorAnalyticsService with mocked database."""
    with patch(
        "services.error_analytics_service.get_database_adapter",
        return_value=mock_db_adapter,
    ):
        return ErrorAnalyticsService()


@pytest.fixture
def sample_failed_workflows():
    """Sample failed workflow data."""
    return [
        ('completed', None, 'Plan'),
        ('completed', None, 'Build'),
        ('failed', 'ModuleNotFoundError: No module named "requests"', 'Build'),
        ('completed', None, 'Test'),
        ('failed', 'ECONNREFUSED localhost:9100', 'Test'),
        ('completed', None, 'Review'),
        ('failed', 'ModuleNotFoundError: No module named "pytest"', 'Build'),
        ('completed', None, 'Ship'),
        ('failed', 'TimeoutError: Command timed out after 120s', 'Test'),
        ('completed', None, 'Document'),
    ]


@pytest.fixture
def sample_error_workflows_only():
    """Sample data with only failed workflows."""
    return [
        ('failed', 'ModuleNotFoundError: No module named "requests"', 'Build'),
        ('failed', 'ECONNREFUSED localhost:9100', 'Test'),
        ('failed', 'ModuleNotFoundError: No module named "pytest"', 'Build'),
        ('failed', 'TimeoutError: Command timed out after 120s', 'Test'),
        ('failed', 'SyntaxError: invalid syntax in test.py', 'Lint'),
    ]


class TestGetErrorSummary:
    """Test error summary generation."""

    def test_get_error_summary_success(self, service, sample_failed_workflows):
        """Test successful error summary generation."""
        service.db.execute_query = MagicMock(return_value=sample_failed_workflows)

        result = service.get_error_summary(days=30)

        assert result['total_workflows'] == 10
        assert result['failed_workflows'] == 4
        assert result['failure_rate'] == 40.0
        assert len(result['top_errors']) > 0
        assert result['most_problematic_phase'] in ['Build', 'Test']
        assert 'Dependency Issue' in result['error_categories']

    def test_get_error_summary_no_data(self, service):
        """Test error summary with no data."""
        service.db.execute_query = MagicMock(return_value=[])

        result = service.get_error_summary(days=30)

        assert result['total_workflows'] == 0
        assert result['failed_workflows'] == 0
        assert result['failure_rate'] == 0.0
        assert result['top_errors'] == []
        assert result['most_problematic_phase'] is None

    def test_get_error_summary_no_failures(self, service):
        """Test error summary with no failures."""
        all_successful = [
            ('completed', None, 'Plan'),
            ('completed', None, 'Build'),
            ('completed', None, 'Test'),
        ]
        service.db.execute_query = MagicMock(return_value=all_successful)

        result = service.get_error_summary(days=30)

        assert result['total_workflows'] == 3
        assert result['failed_workflows'] == 0
        assert result['failure_rate'] == 0.0


class TestAnalyzeByPhase:
    """Test phase error analysis."""

    def test_analyze_by_phase_success(self, service):
        """Test successful phase error analysis."""
        # Format: (current_phase, status) - matching the service's query
        phase_data = [
            ('Plan', 'completed'),
            ('Build', 'completed'),
            ('Build', 'failed'),
            ('Build', 'failed'),
            ('Test', 'completed'),
            ('Test', 'failed'),
            ('Test', 'failed'),
            ('Review', 'completed'),
            ('Ship', 'completed'),
            ('Document', 'completed'),
        ]
        service.db.execute_query = MagicMock(return_value=phase_data)

        result = service.analyze_by_phase(days=30)

        assert result['total_errors'] == 4
        assert 'Build' in result['phase_error_counts']
        assert 'Test' in result['phase_error_counts']
        assert result['phase_error_counts']['Build'] == 2
        assert result['phase_error_counts']['Test'] == 2
        assert result['most_error_prone_phase'] is not None

    def test_analyze_by_phase_calculates_rates(self, service):
        """Test phase failure rate calculation."""
        # Build phase: 2 errors out of 3 total = 66.67%
        phase_data = [
            ('Build', 'completed'),
            ('Build', 'failed'),
            ('Build', 'failed'),
        ]
        service.db.execute_query = MagicMock(return_value=phase_data)

        result = service.analyze_by_phase(days=30)

        assert 'Build' in result['phase_failure_rates']
        build_rate = result['phase_failure_rates']['Build']
        assert 60 <= build_rate <= 70  # Allow some rounding

    def test_analyze_by_phase_no_errors(self, service):
        """Test phase analysis with no errors."""
        all_successful = [
            ('Plan', 'completed'),
            ('Build', 'completed'),
            ('Test', 'completed'),
        ]
        service.db.execute_query = MagicMock(return_value=all_successful)

        result = service.analyze_by_phase(days=30)

        assert result['total_errors'] == 0


class TestFindErrorPatterns:
    """Test error pattern detection."""

    def test_find_error_patterns_success(self, service, sample_error_workflows_only):
        """Test successful error pattern detection."""
        # Convert to format expected by find_error_patterns (adw_id, error_message)
        pattern_data = [
            ('adw-001', 'ModuleNotFoundError: No module named "requests"'),
            ('adw-002', 'ECONNREFUSED localhost:9100'),
            ('adw-003', 'ModuleNotFoundError: No module named "pytest"'),
            ('adw-004', 'TimeoutError: Command timed out after 120s'),
            ('adw-005', 'SyntaxError: invalid syntax in test.py'),
        ]
        service.db.execute_query = MagicMock(return_value=pattern_data)

        patterns = service.find_error_patterns(days=30)

        assert len(patterns) > 0

        # Check import error pattern
        import_pattern = next((p for p in patterns if 'Import' in p['pattern_name']), None)
        assert import_pattern is not None
        assert import_pattern['occurrences'] == 2
        assert 'recommendation' in import_pattern

    def test_find_error_patterns_groups_similar_errors(self, service):
        """Test that similar errors are grouped into patterns."""
        pattern_data = [
            ('adw-001', 'ModuleNotFoundError: No module named "pandas"'),
            ('adw-002', 'ModuleNotFoundError: No module named "numpy"'),
            ('adw-003', 'ImportError: cannot import name "something"'),
        ]
        service.db.execute_query = MagicMock(return_value=pattern_data)

        patterns = service.find_error_patterns(days=30)

        # All three should be grouped as import_error pattern
        import_pattern = next((p for p in patterns if 'Import' in p['pattern_name']), None)
        assert import_pattern is not None
        assert import_pattern['occurrences'] == 3

    def test_find_error_patterns_no_errors(self, service):
        """Test pattern detection with no errors."""
        service.db.execute_query = MagicMock(return_value=[])

        patterns = service.find_error_patterns(days=30)

        assert len(patterns) == 0


class TestGetFailureTrends:
    """Test failure trend analysis."""

    def test_get_failure_trends_success(self, service):
        """Test successful trend analysis."""
        # Simulate 7 days of data
        base_date = datetime.now().date()
        trend_data = []

        for i in range(7):
            date = (base_date - timedelta(days=6-i)).isoformat()
            # Simulate increasing failures
            for j in range(3):  # 3 workflows per day
                status = 'failed' if j < (i // 2) else 'completed'
                trend_data.append((date, status))

        service.db.execute_query = MagicMock(return_value=trend_data)

        result = service.get_failure_trends(days=7)

        assert 'daily_errors' in result
        assert len(result['daily_errors']) > 0
        assert 'trend_direction' in result
        assert result['trend_direction'] in ['increasing', 'decreasing', 'stable']

    def test_get_failure_trends_calculates_percentage_change(self, service):
        """Test percentage change calculation."""
        base_date = datetime.now().date()
        trend_data = []

        # First 7 days: 10% failure rate (1 out of 10)
        for i in range(7):
            date = (base_date - timedelta(days=13-i)).isoformat()
            trend_data.append((date, 'failed'))
            for j in range(9):
                trend_data.append((date, 'completed'))

        # Last 7 days: 50% failure rate (5 out of 10)
        for i in range(7, 14):
            date = (base_date - timedelta(days=13-i)).isoformat()
            for j in range(5):
                trend_data.append((date, 'failed'))
            for j in range(5):
                trend_data.append((date, 'completed'))

        service.db.execute_query = MagicMock(return_value=trend_data)

        result = service.get_failure_trends(days=14)

        # Should show increasing trend (10% -> 50% = +300% change)
        assert result['trend_direction'] == 'increasing'
        assert result['percentage_change'] > 0


class TestGetDebuggingRecommendations:
    """Test debugging recommendation generation."""

    def test_get_debugging_recommendations_success(self, service):
        """Test successful recommendation generation."""
        pattern_data = [
            ('adw-001', 'ModuleNotFoundError: No module named "requests"'),
            ('adw-002', 'ModuleNotFoundError: No module named "pytest"'),
            ('adw-003', 'ECONNREFUSED localhost:9100'),
        ]
        service.db.execute_query = MagicMock(return_value=pattern_data)

        recommendations = service.get_debugging_recommendations(days=30)

        assert len(recommendations) > 0

        # Check recommendation structure
        rec = recommendations[0]
        assert 'issue' in rec
        assert 'severity' in rec
        assert 'root_cause' in rec
        assert 'solution' in rec
        assert 'estimated_fix_time' in rec

    def test_get_debugging_recommendations_prioritizes_by_severity(self, service):
        """Test that high severity errors are prioritized."""
        pattern_data = [
            ('adw-001', 'ModuleNotFoundError: No module named "requests"'),  # High severity
            ('adw-002', 'ModuleNotFoundError: No module named "pytest"'),    # High severity
            ('adw-003', 'TimeoutError: Command timed out after 120s'),       # Medium severity
        ]
        service.db.execute_query = MagicMock(return_value=pattern_data)

        recommendations = service.get_debugging_recommendations(days=30)

        # High severity should come first
        assert recommendations[0]['severity'] == 'high'

    def test_get_debugging_recommendations_no_errors(self, service):
        """Test recommendations with no errors."""
        service.db.execute_query = MagicMock(return_value=[])

        recommendations = service.get_debugging_recommendations(days=30)

        assert len(recommendations) == 0


class TestClassifyError:
    """Test error classification."""

    def test_classify_import_error(self, service):
        """Test import error classification."""
        error_msg = "ModuleNotFoundError: No module named 'requests'"

        pattern = service.classify_error(error_msg)

        assert pattern == 'import_error'

    def test_classify_connection_error(self, service):
        """Test connection error classification."""
        error_msg = "ECONNREFUSED localhost:9100"

        pattern = service.classify_error(error_msg)

        assert pattern == 'connection_error'

    def test_classify_timeout_error(self, service):
        """Test timeout error classification."""
        error_msg = "TimeoutError: Command timed out after 120 seconds"

        pattern = service.classify_error(error_msg)

        assert pattern == 'timeout_error'

    def test_classify_syntax_error(self, service):
        """Test syntax error classification."""
        error_msg = "SyntaxError: invalid syntax in test.py line 42"

        pattern = service.classify_error(error_msg)

        assert pattern == 'syntax_error'

    def test_classify_unknown_error(self, service):
        """Test unknown error classification."""
        error_msg = "Some random error that doesn't match any pattern"

        pattern = service.classify_error(error_msg)

        assert pattern == 'unknown'

    def test_classify_empty_error(self, service):
        """Test empty error message."""
        pattern = service.classify_error("")

        assert pattern == 'unknown'

    def test_classify_none_error(self, service):
        """Test None error message."""
        pattern = service.classify_error(None)

        assert pattern == 'unknown'
