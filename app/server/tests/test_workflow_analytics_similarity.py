"""
Unit tests for Phase 3E similarity detection algorithms.

Tests cover:
- Text similarity (Jaccard index)
- Complexity detection
- Multi-factor workflow similarity scoring
"""
from core.workflow_analytics import (
    calculate_text_similarity,
    detect_complexity,
    find_similar_workflows,
)


class TestTextSimilarity:
    """Test suite for calculate_text_similarity() function."""

    def test_identical_text(self):
        """Identical text should return 1.0."""
        result = calculate_text_similarity("hello world", "hello world")
        assert result == 1.0

    def test_no_overlap(self):
        """Completely different text should return 0.0."""
        result = calculate_text_similarity("foo bar", "baz qux")
        assert result == 0.0

    def test_partial_overlap(self):
        """Partial overlap should return value between 0 and 1."""
        result = calculate_text_similarity("foo bar baz", "bar baz qux")
        # 2 words in common (bar, baz) out of 4 total unique words
        # Jaccard = 2/4 = 0.5
        assert 0.4 < result < 0.7

    def test_case_insensitive(self):
        """Text comparison should be case-insensitive."""
        result = calculate_text_similarity("Hello World", "hello world")
        assert result == 1.0

    def test_empty_strings(self):
        """Empty strings should return 0.0."""
        assert calculate_text_similarity("", "test") == 0.0
        assert calculate_text_similarity("test", "") == 0.0
        assert calculate_text_similarity("", "") == 0.0

    def test_none_values(self):
        """None values should return 0.0."""
        assert calculate_text_similarity(None, "test") == 0.0
        assert calculate_text_similarity("test", None) == 0.0
        assert calculate_text_similarity(None, None) == 0.0

    def test_multi_word_similarity(self):
        """Test similarity with multi-word phrases."""
        text1 = "implement user authentication system"
        text2 = "add user login authentication"
        result = calculate_text_similarity(text1, text2)
        # Common: user, authentication (2 words)
        # Total unique: implement, user, authentication, system, add, login (6 words)
        # Jaccard = 2/6 = 0.333...
        assert 0.25 < result < 0.45


class TestComplexityDetection:
    """Test suite for detect_complexity() function."""

    def test_simple_workflow(self):
        """Low values across all metrics should return 'simple'."""
        workflow = {
            'nl_input_word_count': 30,
            'total_duration_seconds': 200,
            'errors': []
        }
        assert detect_complexity(workflow) == "simple"

    def test_complex_workflow_by_word_count(self):
        """High word count should return 'complex'."""
        workflow = {
            'nl_input_word_count': 250,
            'total_duration_seconds': 200,
            'errors': []
        }
        assert detect_complexity(workflow) == "complex"

    def test_complex_workflow_by_duration(self):
        """Long duration should return 'complex'."""
        workflow = {
            'nl_input_word_count': 30,
            'total_duration_seconds': 2000,
            'errors': []
        }
        assert detect_complexity(workflow) == "complex"

    def test_complex_workflow_by_errors(self):
        """Many errors should return 'complex'."""
        workflow = {
            'nl_input_word_count': 30,
            'total_duration_seconds': 200,
            'errors': list(range(10))  # 10 errors
        }
        assert detect_complexity(workflow) == "complex"

    def test_medium_workflow(self):
        """Mid-range values should return 'medium'."""
        workflow = {
            'nl_input_word_count': 100,
            'total_duration_seconds': 600,
            'errors': ['error1', 'error2']
        }
        assert detect_complexity(workflow) == "medium"

    def test_edge_case_simple_boundary(self):
        """Values at simple boundary should be consistent."""
        # Exactly at boundary: 50 words, 300s, 3 errors
        workflow = {
            'nl_input_word_count': 49,
            'total_duration_seconds': 299,
            'errors': ['e1', 'e2']
        }
        assert detect_complexity(workflow) == "simple"

    def test_edge_case_complex_boundary(self):
        """Values at complex boundary should be consistent."""
        workflow = {
            'nl_input_word_count': 201,
            'total_duration_seconds': 500,
            'errors': []
        }
        assert detect_complexity(workflow) == "complex"

    def test_missing_fields(self):
        """Missing fields should default to medium."""
        workflow = {}
        # Should handle missing fields gracefully
        result = detect_complexity(workflow)
        assert result in ["simple", "medium", "complex"]


class TestSimilarWorkflows:
    """Test suite for find_similar_workflows() function."""

    def test_finds_exact_match(self):
        """Should find workflows with very high similarity."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'implement user authentication',
            'nl_input_word_count': 30,
            'total_duration_seconds': 200,
            'errors': []
        }

        all_workflows = [
            workflow,
            {
                'adw_id': '2',
                'classification_type': 'feature',
                'workflow_template': 'adw_plan_build_test',
                'nl_input': 'implement authentication system',
                'nl_input_word_count': 28,
                'total_duration_seconds': 220,
                'errors': []
            }
        ]

        similar = find_similar_workflows(workflow, all_workflows)
        assert '2' in similar
        assert len(similar) >= 1

    def test_excludes_self(self):
        """Should not include the workflow itself in results."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        similar = find_similar_workflows(workflow, [workflow])
        assert len(similar) == 0

    def test_similarity_threshold(self):
        """Should exclude workflows below 70-point threshold."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        # Create dissimilar workflow (different on all factors)
        dissimilar = {
            'adw_id': '2',
            'classification_type': 'bug',  # Different (0 points)
            'workflow_template': 'adw_patch',  # Different (0 points)
            'nl_input': 'completely different text',  # Low similarity (~0 points)
            'nl_input_word_count': 500,
            'total_duration_seconds': 3000,
            'errors': list(range(10))  # Different complexity (0 points)
        }

        similar = find_similar_workflows(workflow, [workflow, dissimilar])
        # Dissimilar workflow scores ~0 points, should not be included
        assert '2' not in similar

    def test_max_10_results(self):
        """Should return at most 10 results even if more match."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'implement feature',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        # Create 15 very similar workflows
        all_workflows = [workflow]
        for i in range(15):
            all_workflows.append({
                'adw_id': str(i + 2),
                'classification_type': 'feature',  # 30 points
                'workflow_template': 'adw_plan_build_test',  # 30 points
                'nl_input': 'implement new feature',  # High similarity (~15 points)
                'nl_input_word_count': 22,
                'total_duration_seconds': 110,
                'errors': []  # Same complexity (20 points)
                # Total: ~95 points - well above threshold
            })

        similar = find_similar_workflows(workflow, all_workflows)
        assert len(similar) <= 10

    def test_sorted_by_score(self):
        """Results should be sorted by similarity score (highest first)."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'implement auth',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        all_workflows = [
            workflow,
            {
                'adw_id': '2',
                'classification_type': 'feature',  # 30
                'workflow_template': 'adw_plan_build_test',  # 30
                'nl_input': 'implement auth',  # 20 (identical)
                'nl_input_word_count': 20,
                'total_duration_seconds': 100,
                'errors': []  # 20
                # Total: 100 points
            },
            {
                'adw_id': '3',
                'classification_type': 'feature',  # 30
                'workflow_template': 'adw_plan_build_test',  # 30
                'nl_input': 'add feature',  # ~0 (different)
                'nl_input_word_count': 20,
                'total_duration_seconds': 100,
                'errors': []  # 20
                # Total: 80 points
            }
        ]

        similar = find_similar_workflows(workflow, all_workflows)
        # Should return ['2', '3'] in that order (highest score first)
        assert similar[0] == '2'  # 100 points comes first
        assert similar[1] == '3'  # 80 points comes second

    def test_multi_factor_scoring(self):
        """Verify multi-factor scoring works correctly."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'implement feature',
            'nl_input_word_count': 50,
            'total_duration_seconds': 400,
            'errors': []
        }

        # Perfect match on all factors
        perfect_match = {
            'adw_id': '2',
            'classification_type': 'feature',  # +30
            'workflow_template': 'adw_plan_build_test',  # +30
            'nl_input': 'implement feature',  # +20 (identical text)
            'nl_input_word_count': 50,  # Same complexity
            'total_duration_seconds': 400,
            'errors': []  # +20
            # Total: 100 points
        }

        all_workflows = [workflow, perfect_match]
        similar = find_similar_workflows(workflow, all_workflows)

        assert '2' in similar
        assert len(similar) == 1

    def test_no_matches(self):
        """Should return empty list when no similar workflows exist."""
        workflow = {
            'adw_id': '1',
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        # Only dissimilar workflows
        all_workflows = [
            workflow,
            {
                'adw_id': '2',
                'classification_type': 'bug',
                'workflow_template': 'adw_patch',
                'nl_input': 'different',
                'nl_input_word_count': 200,
                'total_duration_seconds': 2000,
                'errors': list(range(10))
            }
        ]

        similar = find_similar_workflows(workflow, all_workflows)
        assert len(similar) == 0

    def test_missing_adw_id(self):
        """Should handle workflow without adw_id gracefully."""
        workflow = {
            # No adw_id field
            'classification_type': 'feature',
            'workflow_template': 'adw_plan_build_test',
            'nl_input': 'test',
            'nl_input_word_count': 20,
            'total_duration_seconds': 100,
            'errors': []
        }

        all_workflows = [workflow]
        similar = find_similar_workflows(workflow, all_workflows)
        # Should return empty list due to missing adw_id
        assert similar == []
