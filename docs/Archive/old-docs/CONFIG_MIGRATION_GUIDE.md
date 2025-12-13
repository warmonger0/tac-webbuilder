# Configuration Management Migration Guide

## Overview

The tac-webbuilder project now has a centralized, type-safe configuration system using Pydantic. This replaces the scattered `os.getenv()` calls throughout the codebase with a unified configuration API.

## Benefits

- **Type Safety**: Pydantic validates all configuration values at startup
- **Centralized**: All configuration in one place (`core/config.py`)
- **YAML Support**: Load configuration from YAML files with environment variable overrides
- **Documentation**: Configuration schema is self-documenting
- **Defaults**: Sensible defaults for all settings
- **Validation**: Automatic validation of values (e.g., port numbers, repo format)

## Configuration Structure

```python
from core.config import get_config

config = get_config()

# Access nested configuration
port = config.server.backend_port          # 8000
repo = config.github.repo                  # "warmonger0/tac-webbuilder"
db_type = config.database.type             # "sqlite"
openai_key = config.llm.openai_api_key     # None or set value
```

### Configuration Sections

1. **ServerConfig** - Server-related settings
   - `backend_port` (default: 8000)
   - `frontend_port` (default: 5173)
   - `frontend_url` (auto-computed)
   - `webhook_trigger_url` (default: "http://localhost:8001")

2. **GitHubConfig** - GitHub integration
   - `pat` (Personal Access Token)
   - `repo` (format: "owner/repo", default: "warmonger0/tac-webbuilder")
   - `webhook_id` (default: "580534779")

3. **DatabaseConfig** - Database settings
   - `type` (default: "sqlite", options: "sqlite" | "postgresql")
   - `postgres_host`, `postgres_port`, `postgres_db`, `postgres_user`, `postgres_password`
   - `postgres_pool_min`, `postgres_pool_max`

4. **LLMConfig** - LLM API keys
   - `openai_api_key`
   - `anthropic_api_key`

5. **CloudflareConfig** - Cloudflare settings
   - `tunnel_token`

## Using the Config System

### Option 1: Environment Variables Only (Recommended for Development)

```bash
# Nested config (double underscores)
export TWB_SERVER__BACKEND_PORT=9000
export TWB_GITHUB__PAT="ghp_xxxxxxxxxxxx"
export TWB_DB__TYPE=postgresql
export TWB_LLM__OPENAI_API_KEY="sk-xxxx"
```

```python
from core.config import get_config

config = get_config()
# Config loaded from environment variables
```

### Option 2: YAML Configuration File

Create `config.yaml` in project root:

```yaml
server:
  backend_port: 8000
  frontend_port: 5173

github:
  repo: "myorg/myrepo"

database:
  type: postgresql
  postgres_host: "db.example.com"
  postgres_password: "secret"

llm:
  openai_api_key: "sk-xxxx"
```

```python
from core.config import get_config

# Auto-loads from config.yaml if present
config = get_config()

# Or specify path explicitly
config = get_config("path/to/config.yaml")
```

### Option 3: YAML + Environment Variables (Best for Production)

Environment variables always override YAML values:

```yaml
# config.yaml
database:
  type: postgresql
  postgres_host: "localhost"
```

```bash
# Override in production
export TWB_DB__POSTGRES_HOST="prod-db.example.com"
export TWB_DB__POSTGRES_PASSWORD="prod-secret"
```

## Migration Examples

### Before (Old Way)

```python
import os

# Scattered throughout codebase
backend_port = int(os.environ.get("BACKEND_PORT", "8000"))
github_repo = os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder")
db_type = os.getenv("DB_TYPE", "sqlite").lower()
openai_key = os.environ.get("OPENAI_API_KEY")
```

### After (New Way)

```python
from core.config import get_config

config = get_config()

# Type-safe, validated access
backend_port = config.server.backend_port
github_repo = config.github.repo
db_type = config.database.type
openai_key = config.llm.openai_api_key
```

## Service Migration Pattern

For services that need configuration, use dependency injection:

```python
from core.config import AppConfig, get_config

class MyService:
    def __init__(self, config: AppConfig = None):
        self.config = config or get_config()

    def do_something(self):
        # Access config
        api_key = self.config.llm.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        # Use the key...
```

## Testing with Config

In tests, you can override configuration:

```python
from core.config import AppConfig, ServerConfig

def test_my_service():
    # Create test config
    test_config = AppConfig(
        server=ServerConfig(backend_port=9999)
    )

    service = MyService(config=test_config)
    assert service.config.server.backend_port == 9999
```

Or use environment variables with monkeypatch:

```python
def test_with_env(monkeypatch):
    monkeypatch.setenv("TWB_SERVER__BACKEND_PORT", "7000")
    config = AppConfig.load()
    assert config.server.backend_port == 7000
```

## Legacy Environment Variables

The existing environment variables (without `TWB_` prefix) will continue to work for now, but should be migrated:

| Old Variable | New Variable |
|--------------|--------------|
| `BACKEND_PORT` | `TWB_SERVER__BACKEND_PORT` |
| `FRONTEND_PORT` | `TWB_SERVER__FRONTEND_PORT` |
| `GITHUB_PAT` | `TWB_GITHUB__PAT` |
| `GITHUB_REPO` | `TWB_GITHUB__REPO` |
| `DB_TYPE` | `TWB_DB__TYPE` |
| `POSTGRES_HOST` | `TWB_DB__POSTGRES_HOST` |
| `POSTGRES_PASSWORD` | `TWB_DB__POSTGRES_PASSWORD` |
| `OPENAI_API_KEY` | `TWB_LLM__OPENAI_API_KEY` |
| `ANTHROPIC_API_KEY` | `TWB_LLM__ANTHROPIC_API_KEY` |

**Note**: Services should be migrated to use the new config system rather than reading environment variables directly.

## Best Practices

1. **Centralize Config Access**: Import and call `get_config()` once at service/module initialization
2. **Use Dependency Injection**: Pass config to services rather than having them import it directly
3. **Validate Early**: The config system validates all values at startup, catching errors early
4. **Document Defaults**: All defaults are defined in `core/config.py`
5. **Use YAML for Deployment**: Store non-sensitive config in YAML, sensitive values in env vars
6. **Type Hints**: Use `AppConfig` type hints for better IDE support

## Troubleshooting

### Config value not loading from environment

Check the env var format:
- Use `TWB_` prefix
- Use double underscores (`__`) for nested sections
- Example: `TWB_SERVER__BACKEND_PORT` not `TWB_SERVER_BACKEND_PORT`

### Validation errors on startup

The config system validates all values. Check error messages:
```python
pydantic.ValidationError: Port must be between 1 and 65535
```

Fix the invalid value in your config or environment variable.

### Force reload config

If you need to reload configuration (e.g., in tests):

```python
from core.config import get_config

# Force reload from environment
config = get_config(force_reload=True)
```

## Example: Complete Migration

### Before

```python
# server.py
import os

backend_port = int(os.environ.get("BACKEND_PORT", "8000"))
github_pat = os.environ.get("GITHUB_PAT")
db_type = os.getenv("DB_TYPE", "sqlite")
```

### After

```python
# server.py
from core.config import get_config

config = get_config()

backend_port = config.server.backend_port
github_pat = config.github.pat
db_type = config.database.type
```

## Next Steps

1. Services can be migrated incrementally to use the new config system
2. Old `os.getenv()` calls can coexist with new config system during transition
3. Eventually, all environment variable access should go through the config system

## Support

For questions or issues with the configuration system:
- See `core/config.py` for implementation details
- See `tests/core/test_config.py` for usage examples
- See `config.yaml.example` for YAML configuration template
