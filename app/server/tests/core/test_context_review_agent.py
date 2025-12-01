"""Tests for context review agent."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context_review_agent import ContextReviewAgent, ContextReviewResult


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    with patch('core.context_review_agent.anthropic') as mock:
        yield mock


@pytest.fixture
def agent(mock_anthropic_client):
    """Create agent with mocked Anthropic client."""
    # Set fake API key for testing
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-123'
    return ContextReviewAgent()


class TestContextReviewAgent:
    """Test suite for ContextReviewAgent."""

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        # Remove env var if present
        old_key = os.environ.pop('ANTHROPIC_API_KEY', None)

        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
                ContextReviewAgent()
        finally:
            # Restore env var
            if old_key:
                os.environ['ANTHROPIC_API_KEY'] = old_key

    def test_init_with_api_key(self, agent):
        """Test initialization with API key."""
        assert agent.api_key == 'test-key-123'
        assert agent.client is not None

    def test_extract_keywords(self, agent):
        """Test keyword extraction from description."""
        description = "Add user authentication with JWT tokens and login system"
        keywords = agent._extract_keywords(description)

        assert 'user' in keywords
        assert 'authentication' in keywords
        assert 'jwt' in keywords
        assert 'tokens' in keywords
        assert 'login' in keywords
        assert 'system' in keywords

        # Stopwords should be removed
        assert 'add' not in keywords
        assert 'with' not in keywords
        assert 'and' not in keywords

    def test_extract_keywords_removes_short_words(self, agent):
        """Test that short words are filtered out."""
        description = "Add a new API to the system"
        keywords = agent._extract_keywords(description)

        # Short words (2 chars or less) should be removed
        assert 'to' not in keywords
        assert 'a' not in keywords

        # Longer words should remain
        assert 'api' in keywords
        assert 'new' in keywords

    def test_score_file_relevance(self, agent):
        """Test file relevance scoring."""
        keywords = ['auth', 'user', 'login']

        # Exact match in filename (highest score)
        score1 = agent._score_file_relevance("app/auth.py", keywords)
        assert score1 > 10

        # Match in directory path
        score2 = agent._score_file_relevance("app/user/models.py", keywords)
        assert score2 > 3

        # No match
        score3 = agent._score_file_relevance("app/database.py", keywords)
        assert score3 <= 1  # Only extension bonus

    def test_score_file_relevance_prefers_code_files(self, agent):
        """Test that code files get bonus points."""
        keywords = ['test']

        py_score = agent._score_file_relevance("test.py", keywords)
        ts_score = agent._score_file_relevance("test.ts", keywords)
        txt_score = agent._score_file_relevance("test.txt", keywords)

        assert py_score > txt_score
        assert ts_score > txt_score

    def test_identify_relevant_files_with_existing_list(self, agent):
        """Test file identification with pre-provided file list."""
        description = "Add user authentication module"
        files = [
            "app/models/user.py",
            "app/auth/handler.py",
            "app/database/connection.py",
            "app/utils/logger.py",
            "app/auth/jwt.py"
        ]

        relevant = agent.identify_relevant_files(
            description,
            "/fake/path",
            existing_files=files
        )

        # Should identify auth and user related files
        assert "app/models/user.py" in relevant
        assert "app/auth/handler.py" in relevant
        assert "app/auth/jwt.py" in relevant

    def test_identify_relevant_files_limits_results(self, agent):
        """Test that file identification limits results to 50."""
        description = "Add feature"
        # Create 100 files
        files = [f"app/module{i}/feature{i}.py" for i in range(100)]

        relevant = agent.identify_relevant_files(
            description,
            "/fake/path",
            existing_files=files
        )

        # Should limit to top 50
        assert len(relevant) <= 50

    def test_generate_cache_key(self, agent):
        """Test cache key generation."""
        desc1 = "Add user auth"
        path1 = "/project/path"

        key1 = agent.generate_cache_key(desc1, path1)
        key2 = agent.generate_cache_key(desc1, path1)

        # Same inputs should produce same key
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    def test_generate_cache_key_different_inputs(self, agent):
        """Test that different inputs produce different keys."""
        key1 = agent.generate_cache_key("desc1", "/path1")
        key2 = agent.generate_cache_key("desc2", "/path1")
        key3 = agent.generate_cache_key("desc1", "/path2")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_extract_json_from_plain_json(self, agent):
        """Test JSON extraction from plain JSON response."""
        response = '{"key": "value", "number": 42}'
        result = agent._extract_json(response)

        assert result == {"key": "value", "number": 42}

    def test_extract_json_from_markdown(self, agent):
        """Test JSON extraction from markdown code block."""
        response = """Here is the result:
```json
{"key": "value", "number": 42}
```
That's it!"""

        result = agent._extract_json(response)
        assert result == {"key": "value", "number": 42}

    def test_extract_json_from_code_block(self, agent):
        """Test JSON extraction from code block without language."""
        response = """Result:
```
{"key": "value"}
```"""

        result = agent._extract_json(response)
        assert result == {"key": "value"}

    def test_extract_json_invalid_raises_error(self, agent):
        """Test that invalid JSON raises error."""
        with pytest.raises(json.JSONDecodeError):
            agent._extract_json("This is not JSON at all")

    def test_parse_result(self, agent):
        """Test parsing API response into ContextReviewResult."""
        result_json = {
            "integration_strategy": "Create new auth module",
            "files_to_modify": ["app.py", "config.py"],
            "files_to_create": ["auth.py", "jwt_handler.py"],
            "reference_files": ["example.py"],
            "risks": ["Breaking change", "Security concern"],
            "optimized_context": {
                "must_read": ["app.py"],
                "optional": ["config.py"],
                "skip": ["test.py"]
            },
            "estimated_tokens": 2000
        }

        result = agent._parse_result(result_json)

        assert isinstance(result, ContextReviewResult)
        assert result.integration_strategy == "Create new auth module"
        assert len(result.files_to_modify) == 2
        assert len(result.files_to_create) == 2
        assert len(result.risks) == 2
        assert result.estimated_tokens == 2000

    def test_parse_result_with_missing_optional_fields(self, agent):
        """Test parsing result with minimal required fields."""
        result_json = {
            "integration_strategy": "Simple approach"
        }

        result = agent._parse_result(result_json)

        assert result.integration_strategy == "Simple approach"
        assert result.files_to_modify == []
        assert result.files_to_create == []
        assert result.risks == []
        assert result.estimated_tokens == 0

    def test_format_samples(self, agent):
        """Test formatting file samples for prompt."""
        samples = {
            "file1.py": "def hello():\n    print('hello')\n" * 50,
            "file2.py": "def world():\n    print('world')\n" * 50
        }

        formatted = agent._format_samples(samples)

        assert "file1.py" in formatted
        assert "file2.py" in formatted
        assert "```" in formatted

    def test_format_samples_empty(self, agent):
        """Test formatting empty samples."""
        formatted = agent._format_samples({})
        assert "No sample files available" in formatted

    @pytest.mark.asyncio
    async def test_analyze_with_claude_success(self, agent, mock_anthropic_client):
        """Test successful Claude API call."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "integration_strategy": "Test strategy",
            "files_to_modify": ["test.py"],
            "files_to_create": ["new.py"],
            "reference_files": [],
            "risks": ["Test risk"],
            "optimized_context": {
                "must_read": ["test.py"],
                "optional": [],
                "skip": []
            },
            "estimated_tokens": 1500
        })

        agent.client.messages.create = MagicMock(return_value=mock_response)

        result = await agent._analyze_with_claude(
            "Test description",
            ["test.py", "new.py"],
            {"test.py": "print('test')"}
        )

        assert isinstance(result, ContextReviewResult)
        assert result.integration_strategy == "Test strategy"
        assert "test.py" in result.files_to_modify

    @pytest.mark.asyncio
    async def test_analyze_with_claude_api_error(self, agent):
        """Test handling of Claude API error."""
        agent.client.messages.create = MagicMock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(Exception, match="API Error"):
            await agent._analyze_with_claude(
                "Test description",
                ["test.py"],
                {}
            )

    @pytest.mark.asyncio
    async def test_analyze_context_full_workflow(self, agent, mock_anthropic_client):
        """Test complete analyze_context workflow."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "integration_strategy": "Full test",
            "files_to_modify": [],
            "files_to_create": [],
            "reference_files": [],
            "risks": [],
            "optimized_context": {"must_read": [], "optional": [], "skip": []},
            "estimated_tokens": 1000
        })

        agent.client.messages.create = MagicMock(return_value=mock_response)

        # Provide existing files to avoid filesystem access
        result = await agent.analyze_context(
            "Add new feature",
            "/fake/project",
            existing_files=["app.py", "test.py"]
        )

        assert isinstance(result, ContextReviewResult)
        assert result.integration_strategy == "Full test"

    def test_scan_project_files_excludes_common_dirs(self, agent, tmp_path):
        """Test that common directories are excluded from scan."""
        # Create test structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("test")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.js").write_text("test")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("test")

        files = agent._scan_project_files(str(tmp_path))

        # Should include src files
        assert any("app.py" in f for f in files)

        # Should exclude node_modules and .git
        assert not any("node_modules" in f for f in files)
        assert not any(".git" in f for f in files)

    def test_build_analysis_prompt_structure(self, agent):
        """Test that analysis prompt has expected structure."""
        prompt = agent._build_analysis_prompt(
            "Add user auth",
            ["app.py", "auth.py"],
            {"app.py": "print('test')"}
        )

        assert "Proposed Change" in prompt
        assert "Add user auth" in prompt
        assert "Relevant Files" in prompt
        assert "app.py" in prompt
        assert "Sample Files" in prompt
        assert "integration_strategy" in prompt
        assert "files_to_modify" in prompt
