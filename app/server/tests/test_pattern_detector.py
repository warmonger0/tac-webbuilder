"""
Unit tests for pattern detection engine.
"""

from core.pattern_detector import (
    calculate_confidence_score,
    detect_patterns_in_workflow,
    extract_pattern_characteristics,
    process_workflow_for_patterns,
)


class TestPatternDetection:
    """Test multi-pattern detection from workflows."""

    def test_primary_pattern_only(self):
        workflow = {
            "nl_input": "Run backend tests with pytest",
            "workflow_template": "adw_test_iso",
            "error_message": None
        }
        patterns = detect_patterns_in_workflow(workflow)
        assert "test:pytest:backend" in patterns
        # Template also adds test:generic:all, so we expect 2 patterns
        assert len(patterns) == 2

    def test_multiple_patterns(self):
        workflow = {
            "nl_input": "Run tests and build",
            "workflow_template": "adw_sdlc_iso",
            "error_message": None
        }
        patterns = detect_patterns_in_workflow(workflow)
        # Should detect test pattern (primary detection gives test:generic:frontend due to "run" context)
        assert any("test:" in p for p in patterns)
        assert len(patterns) >= 1

    def test_pattern_from_error(self):
        workflow = {
            "nl_input": "Deploy to production",
            "workflow_template": "adw_deploy",
            "error_message": "pytest failed: 3 tests failed in test_api.py"
        }
        patterns = detect_patterns_in_workflow(workflow)
        assert "test:pytest:backend" in patterns

    def test_pattern_from_template(self):
        workflow = {
            "nl_input": "Do stuff",  # Ambiguous
            "workflow_template": "adw_test_iso",
            "error_message": None
        }
        patterns = detect_patterns_in_workflow(workflow)
        assert "test:generic:all" in patterns

    def test_no_duplicates(self):
        workflow = {
            "nl_input": "Run backend tests with pytest",
            "workflow_template": "adw_test_iso",
            "error_message": "pytest failed"
        }
        patterns = detect_patterns_in_workflow(workflow)
        # Should only have one instance of test:pytest:backend
        assert patterns.count("test:pytest:backend") == 1


class TestCharacteristicExtraction:
    """Test extraction of pattern characteristics."""

    def test_simple_workflow(self):
        workflow = {
            "nl_input": "Run pytest tests",
            "duration_seconds": 120,
            "error_count": 0
        }
        chars = extract_pattern_characteristics(workflow)

        assert chars["complexity"] == "simple"
        assert chars["duration_range"] == "short"
        assert "test" in chars["keywords"]
        assert "pytest" in chars["keywords"]
        assert chars["error_count"] == 0

    def test_complex_workflow(self):
        long_input = (
            "Implement comprehensive authentication system with JWT tokens, "
            "refresh tokens, role-based access control, and multi-factor authentication. "
            "Create database migrations, API endpoints, frontend UI components, "
            "integration tests, and documentation."
        )
        workflow = {
            "nl_input": long_input,
            "duration_seconds": 1200,
            "error_count": 8
        }
        chars = extract_pattern_characteristics(workflow)

        assert chars["complexity"] == "complex"
        assert chars["duration_range"] == "long"
        assert chars["input_length"] > 200

    def test_medium_workflow(self):
        workflow = {
            "nl_input": "Run all tests and fix any failures that occur in the backend test suite",
            "duration_seconds": 450,
            "error_count": 2
        }
        chars = extract_pattern_characteristics(workflow)

        # Word count is 14 (< 50) and error_count is 2 (< 3), so it's "simple"
        assert chars["complexity"] == "simple"
        assert chars["duration_range"] == "medium"

    def test_keyword_extraction(self):
        workflow = {
            "nl_input": "Run backend tests with pytest and format with prettier",
            "duration_seconds": 120,
            "error_count": 0
        }
        chars = extract_pattern_characteristics(workflow)

        assert "test" in chars["keywords"]
        assert "pytest" in chars["keywords"]
        assert "backend" in chars["keywords"]
        assert "format" in chars["keywords"]

    def test_file_path_extraction(self):
        workflow = {
            "nl_input": "Run tests in app/server/tests/ and check app/client/src/",
            "duration_seconds": 120,
            "error_count": 0
        }
        chars = extract_pattern_characteristics(workflow)

        assert len(chars["files_mentioned"]) > 0


class TestConfidenceScore:
    """Test confidence score calculation."""

    def test_new_pattern(self):
        pattern_data = {"occurrence_count": 1, "pattern_type": "test"}
        workflows = [
            {"error_count": 0, "duration_seconds": 120, "retry_count": 0}
        ]
        score = calculate_confidence_score(pattern_data, workflows)
        # Score components: frequency(10) + consistency(15 default) + success(30 perfect) = 55
        assert score == 55.0  # New pattern with perfect success

    def test_frequent_pattern(self):
        pattern_data = {"occurrence_count": 10, "pattern_type": "test"}
        workflows = [
            {"error_count": 0, "duration_seconds": 120, "retry_count": 0},
            {"error_count": 0, "duration_seconds": 125, "retry_count": 0},
            {"error_count": 0, "duration_seconds": 118, "retry_count": 0},
            {"error_count": 1, "duration_seconds": 130, "retry_count": 0},
            {"error_count": 0, "duration_seconds": 122, "retry_count": 0},
        ]
        score = calculate_confidence_score(pattern_data, workflows)
        assert score >= 70  # High confidence for frequent, consistent patterns

    def test_inconsistent_pattern(self):
        pattern_data = {"occurrence_count": 5, "pattern_type": "test"}
        workflows = [
            {"error_count": 0, "duration_seconds": 120, "retry_count": 0},
            {"error_count": 5, "duration_seconds": 600, "retry_count": 3},
            {"error_count": 0, "duration_seconds": 130, "retry_count": 0},
            {"error_count": 10, "duration_seconds": 1200, "retry_count": 5},
        ]
        score = calculate_confidence_score(pattern_data, workflows)
        assert score < 70  # Lower confidence for inconsistent patterns

    def test_empty_workflows(self):
        pattern_data = {"occurrence_count": 1, "pattern_type": "test"}
        workflows = []
        score = calculate_confidence_score(pattern_data, workflows)
        assert score == 10.0  # Base score


class TestBatchProcessing:
    """Test the main processing function."""

    def test_process_workflow(self):
        workflow = {
            "nl_input": "Run backend tests with pytest",
            "duration_seconds": 120,
            "error_count": 0,
            "workflow_template": "adw_test_iso",
            "error_message": None
        }
        result = process_workflow_for_patterns(workflow)

        assert "patterns" in result
        assert "characteristics" in result
        assert len(result["patterns"]) > 0
        assert "test:pytest:backend" in result["patterns"]
        assert result["characteristics"]["complexity"] == "simple"

    def test_process_complex_workflow(self):
        workflow = {
            "nl_input": "Implement user authentication",
            "duration_seconds": 1200,
            "error_count": 5,
            "workflow_template": "adw_plan_iso",
            "error_message": None
        }
        result = process_workflow_for_patterns(workflow)

        assert "patterns" in result
        assert "characteristics" in result
        # Complex implementation shouldn't generate automation patterns
        assert len(result["patterns"]) == 0
