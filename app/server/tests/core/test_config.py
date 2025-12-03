"""Tests for configuration management system."""

import os
import tempfile
from pathlib import Path

import pytest

from core.config import (
    AppConfig,
    CloudflareConfig,
    DatabaseConfig,
    GitHubConfig,
    LLMConfig,
    ServerConfig,
    get_config,
)


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self):
        """Test default server configuration values."""
        config = ServerConfig()
        assert config.backend_port == 8000
        assert config.frontend_port == 5173
        assert config.frontend_url is None
        assert config.webhook_trigger_url == "http://localhost:8001"

    def test_port_validation(self):
        """Test port number validation."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerConfig(backend_port=0)
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerConfig(frontend_port=70000)

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("TWB_SERVER_BACKEND_PORT", "9000")
        monkeypatch.setenv("TWB_SERVER_FRONTEND_PORT", "3000")
        config = ServerConfig()
        assert config.backend_port == 9000
        assert config.frontend_port == 3000


class TestGitHubConfig:
    """Tests for GitHubConfig."""

    def test_default_values(self):
        """Test default GitHub configuration values."""
        config = GitHubConfig()
        assert config.pat is None
        assert config.repo == "warmonger0/tac-webbuilder"
        assert config.webhook_id == "580534779"

    def test_repo_format_validation(self):
        """Test repository format validation."""
        with pytest.raises(ValueError, match="Repository must be in format 'owner/repo'"):
            GitHubConfig(repo="invalid-format")

        # Valid format should work
        config = GitHubConfig(repo="owner/repo")
        assert config.repo == "owner/repo"

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("TWB_GITHUB_PAT", "ghp_test123")
        monkeypatch.setenv("TWB_GITHUB_REPO", "test/repo")
        config = GitHubConfig()
        assert config.pat == "ghp_test123"
        assert config.repo == "test/repo"


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_values(self):
        """Test default database configuration values."""
        config = DatabaseConfig()
        assert config.type == "sqlite"
        assert config.postgres_host == "localhost"
        assert config.postgres_port == 5432
        assert config.postgres_db == "tac_webbuilder"
        assert config.postgres_user == "tac_user"
        assert config.postgres_password is None
        assert config.postgres_pool_min == 1
        assert config.postgres_pool_max == 10

    def test_db_type_validation(self):
        """Test database type validation."""
        with pytest.raises(ValueError, match="Database type must be 'sqlite' or 'postgresql'"):
            DatabaseConfig(type="mysql")

        # Valid types should work
        config_sqlite = DatabaseConfig(type="sqlite")
        assert config_sqlite.type == "sqlite"

        config_pg = DatabaseConfig(type="postgresql")
        assert config_pg.type == "postgresql"

    def test_port_validation(self):
        """Test port number validation."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            DatabaseConfig(postgres_port=0)
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            DatabaseConfig(postgres_port=70000)

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("TWB_DB_TYPE", "postgresql")
        monkeypatch.setenv("TWB_DB_POSTGRES_HOST", "db.example.com")
        monkeypatch.setenv("TWB_DB_POSTGRES_PASSWORD", "secret123")
        config = DatabaseConfig()
        assert config.type == "postgresql"
        assert config.postgres_host == "db.example.com"
        assert config.postgres_password == "secret123"


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self):
        """Test default LLM configuration values."""
        config = LLMConfig()
        assert config.openai_api_key is None
        assert config.anthropic_api_key is None

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("TWB_LLM_OPENAI_API_KEY", "sk-test123")
        monkeypatch.setenv("TWB_LLM_ANTHROPIC_API_KEY", "sk-ant-test123")
        config = LLMConfig()
        assert config.openai_api_key == "sk-test123"
        assert config.anthropic_api_key == "sk-ant-test123"


class TestCloudflareConfig:
    """Tests for CloudflareConfig."""

    def test_default_values(self):
        """Test default Cloudflare configuration values."""
        config = CloudflareConfig()
        assert config.tunnel_token is None

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("TWB_CLOUDFLARE_TUNNEL_TOKEN", "token123")
        config = CloudflareConfig()
        assert config.tunnel_token == "token123"


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_initialization(self):
        """Test default app configuration initialization."""
        config = AppConfig()
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.github, GitHubConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.cloudflare, CloudflareConfig)

    def test_frontend_url_auto_computation(self):
        """Test that frontend_url is auto-computed if not provided."""
        config = AppConfig()
        assert config.server.frontend_url == "http://localhost:5173"

        # Test with custom port
        config_custom = AppConfig(server={"frontend_port": 3000})
        assert config_custom.server.frontend_url == "http://localhost:3000"

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
server:
  backend_port: 9000
  frontend_port: 3000
github:
  repo: "test/repo"
database:
  type: postgresql
  postgres_password: secret
llm:
  openai_api_key: sk-test
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = AppConfig.from_yaml(yaml_path)
            assert config.server.backend_port == 9000
            assert config.server.frontend_port == 3000
            assert config.github.repo == "test/repo"
            assert config.database.type == "postgresql"
            assert config.database.postgres_password == "secret"
            assert config.llm.openai_api_key == "sk-test"
        finally:
            os.unlink(yaml_path)

    def test_env_vars_override_yaml(self, monkeypatch):
        """Test that environment variables override YAML values."""
        yaml_content = """
server:
  backend_port: 9000
github:
  repo: "yaml/repo"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Set env var that should override YAML (use nested delimiter for AppConfig)
            monkeypatch.setenv("TWB_SERVER__BACKEND_PORT", "7000")
            monkeypatch.setenv("TWB_GITHUB__REPO", "env/repo")

            config = AppConfig.from_yaml(yaml_path)
            # Env vars should win
            assert config.server.backend_port == 7000
            assert config.github.repo == "env/repo"
        finally:
            os.unlink(yaml_path)

    def test_load_with_missing_file(self):
        """Test loading with non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            AppConfig.from_yaml("/nonexistent/config.yaml")

    def test_load_fallback_behavior(self, monkeypatch, tmp_path):
        """Test automatic fallback behavior of load()."""
        # Test 1: No config file, should use env vars only (use nested delimiter)
        monkeypatch.setenv("TWB_SERVER__BACKEND_PORT", "6000")
        config = AppConfig.load()
        assert config.server.backend_port == 6000

    def test_env_cleanup_after_yaml_load(self):
        """Test that temporary env vars are cleaned up after YAML load."""
        yaml_content = """
server:
  backend_port: 9000
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Ensure nested env vars don't persist
            nested_keys = ["TWB_SERVER__BACKEND_PORT"]
            for key in nested_keys:
                if key in os.environ:
                    del os.environ[key]

            config = AppConfig.from_yaml(yaml_path)
            assert config.server.backend_port == 9000

            # Nested env vars should not persist after load
            for key in nested_keys:
                assert key not in os.environ
        finally:
            os.unlink(yaml_path)


class TestGetConfig:
    """Tests for get_config singleton function."""

    def test_singleton_behavior(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_force_reload(self, monkeypatch):
        """Test force_reload parameter."""
        # First call
        config1 = get_config()
        port1 = config1.server.backend_port

        # Change env var (use nested delimiter for AppConfig)
        monkeypatch.setenv("TWB_SERVER__BACKEND_PORT", "9999")

        # Without force_reload, should return cached config
        config2 = get_config()
        assert config2.server.backend_port == port1

        # With force_reload, should load new config
        config3 = get_config(force_reload=True)
        assert config3.server.backend_port == 9999
