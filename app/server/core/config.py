"""
Configuration management for tac-webbuilder.

This module provides Pydantic-based configuration management that supports
loading settings from both YAML files and environment variables, with
environment variables taking precedence.
"""

import os
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server-related configuration."""

    model_config = SettingsConfigDict(env_prefix="TWB_SERVER_")

    backend_port: int = Field(
        default=8000,
        description="Backend server port",
    )
    frontend_port: int = Field(
        default=5173,
        description="Frontend development server port",
    )
    frontend_url: str | None = Field(
        default=None,
        description="Frontend URL (auto-computed if not provided)",
    )
    webhook_trigger_url: str = Field(
        default="http://localhost:8001",
        description="Webhook trigger URL",
    )

    @field_validator("backend_port", "frontend_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class GitHubConfig(BaseSettings):
    """GitHub-related configuration."""

    model_config = SettingsConfigDict(env_prefix="TWB_GITHUB_")

    pat: str | None = Field(
        default=None,
        description="GitHub Personal Access Token",
    )
    repo: str = Field(
        default="warmonger0/tac-webbuilder",
        description="GitHub repository in format 'owner/repo'",
    )
    webhook_id: str = Field(
        default="580534779",
        description="GitHub webhook ID",
    )

    @field_validator("repo")
    @classmethod
    def validate_repo_format(cls, v: str) -> str:
        """Validate repository format."""
        if v and "/" not in v:
            raise ValueError("Repository must be in format 'owner/repo'")
        return v


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="TWB_DB_")

    type: str = Field(
        default="sqlite",
        description="Database type (sqlite or postgresql)",
    )

    # PostgreSQL-specific settings
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host",
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
    )
    postgres_db: str = Field(
        default="tac_webbuilder",
        description="PostgreSQL database name",
    )
    postgres_user: str = Field(
        default="tac_user",
        description="PostgreSQL user",
    )
    postgres_password: str | None = Field(
        default=None,
        description="PostgreSQL password",
    )
    postgres_pool_min: int = Field(
        default=1,
        description="PostgreSQL connection pool minimum connections",
    )
    postgres_pool_max: int = Field(
        default=10,
        description="PostgreSQL connection pool maximum connections",
    )

    @field_validator("type")
    @classmethod
    def validate_db_type(cls, v: str) -> str:
        """Validate database type."""
        v = v.lower()
        if v not in ("sqlite", "postgresql"):
            raise ValueError("Database type must be 'sqlite' or 'postgresql'")
        return v

    @field_validator("postgres_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class LLMConfig(BaseSettings):
    """LLM API configuration."""

    model_config = SettingsConfigDict(env_prefix="TWB_LLM_")

    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )


class CloudflareConfig(BaseSettings):
    """Cloudflare configuration."""

    model_config = SettingsConfigDict(env_prefix="TWB_CLOUDFLARE_")

    tunnel_token: str | None = Field(
        default=None,
        description="Cloudflare tunnel token",
    )


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TWB_",
        env_nested_delimiter="__",
        # Don't auto-load .env - let python-dotenv handle it
        # This avoids conflicts with legacy env var names
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)

    def __init__(self, **data):
        """Initialize config and compute derived values."""
        super().__init__(**data)
        # Compute frontend_url if not provided
        if not self.server.frontend_url:
            self.server.frontend_url = f"http://localhost:{self.server.frontend_port}"

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> "AppConfig":
        """
        Load configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            AppConfig instance with settings loaded from YAML and environment

        Note:
            Environment variables will override YAML settings.
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(yaml_path) as f:
            yaml_data = yaml.safe_load(f) or {}

        # Convert nested YAML data into environment variables temporarily
        # This allows Pydantic to properly merge YAML and env vars with env taking precedence
        env_backup = {}

        # Flatten YAML data to environment variable format
        def set_env_from_yaml(prefix: str, data: dict):
            """Set environment variables from YAML data if not already set."""
            for key, value in data.items():
                if isinstance(value, dict):
                    # Nested dict - recurse
                    set_env_from_yaml(f"{prefix}{key.upper()}__", value)
                else:
                    # Leaf value - set env var only if not already set (preserving existing env vars)
                    env_key = f"{prefix}{key.upper()}"
                    if env_key not in os.environ:
                        # Save for cleanup (None means it didn't exist before)
                        if env_key not in env_backup:
                            env_backup[env_key] = None
                        os.environ[env_key] = str(value)

        try:
            set_env_from_yaml("TWB_", yaml_data)
            # Now create config - Pydantic will load from env vars, with real env vars taking precedence
            return cls()
        finally:
            # Restore original environment - remove env vars we added
            for key, original_value in env_backup.items():
                if original_value is None:
                    # We added this, remove it
                    os.environ.pop(key, None)

    @classmethod
    def load(cls, yaml_path: Path | str | None = None) -> "AppConfig":
        """
        Load configuration with automatic fallback.

        Tries to load from:
        1. Provided yaml_path
        2. config.yaml in project root
        3. Environment variables only

        Args:
            yaml_path: Optional path to YAML config file

        Returns:
            AppConfig instance
        """
        # Try provided path
        if yaml_path:
            return cls.from_yaml(yaml_path)

        # Try default config.yaml in project root
        # Navigate from app/server/core to project root
        project_root = Path(__file__).parent.parent.parent.parent
        default_config = project_root / "config.yaml"
        if default_config.exists():
            return cls.from_yaml(default_config)

        # Fall back to environment variables only
        return cls()


# Singleton config instance
_config: AppConfig | None = None


def get_config(yaml_path: Path | str | None = None, force_reload: bool = False) -> AppConfig:
    """
    Get the application configuration singleton.

    Args:
        yaml_path: Optional path to YAML configuration file
        force_reload: Force reload the configuration

    Returns:
        AppConfig instance with all settings loaded
    """
    global _config
    if _config is None or force_reload:
        _config = AppConfig.load(yaml_path)
    return _config


# Convenience function for backward compatibility
def load_config(yaml_path: Path | str | None = None) -> AppConfig:
    """
    Load application configuration.

    Args:
        yaml_path: Optional path to YAML configuration file

    Returns:
        AppConfig instance with all settings loaded
    """
    return get_config(yaml_path)
