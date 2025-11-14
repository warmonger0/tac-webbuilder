# Configuration Guide

## Overview

tac-webbuilder uses environment variables for configuration. This guide explains each setting and how to configure them.

## Quick Setup

### 1. Run Interactive Setup
```bash
./scripts/setup_env.sh
```

This will guide you through all configuration options.

### 2. Verify Configuration
```bash
./scripts/test_config.sh
```

### 3. Manual Setup
```bash
cp .env.sample .env
# Edit .env with your values
```

## Required Configuration

### ANTHROPIC_API_KEY (REQUIRED)

**Description**: Your Anthropic API key for Claude Code

**Get it from**: https://console.anthropic.com/settings/keys

**Example**: `ANTHROPIC_API_KEY=sk-ant-api03-xxx...`

**How to get**:
1. Go to https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-`)
4. Add to `.env`

## Claude Code Configuration

### CLAUDE_CODE_PATH

**Description**: Path to Claude Code binary

**Default**: `claude`

**Example**: `CLAUDE_CODE_PATH=/usr/local/bin/claude`

**How to find**:
```bash
which claude
```

### CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR

**Description**: Keep Claude in project root after commands

**Default**: `true`

**Options**: `true`, `false`

**Recommended**: `true`

## GitHub Configuration

### gh CLI Authentication

**Required for posting issues**

```bash
gh auth login
```

Follow the prompts to authenticate.

### GITHUB_PAT

**Description**: GitHub Personal Access Token (optional)

**When needed**: To use different account than `gh auth`

**Get it from**: https://github.com/settings/tokens

**How to create**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Copy token (starts with `ghp_`)
5. Add to `.env`

### GITHUB_REPO_URL

**Description**: Default repository for webbuilder issues

**Format**: `owner/repo-name`

**Example**: `GITHUB_REPO_URL=myorg/my-webbuilder-repo`

### AUTO_POST_ISSUES

**Description**: Skip confirmation when posting issues

**Default**: `false`

**Options**: `true`, `false`

## ADW Workflow Configuration

### DEFAULT_WORKFLOW

**Description**: Which ADW workflow to use by default

**Default**: `adw_sdlc_iso`

**Options**:
- `adw_sdlc_iso` - Full SDLC (plan, build, test, review, document, ship)
- `adw_plan_build_test_iso` - Streamlined (plan, build, test)
- `adw_build_iso` - Build only (fast iteration)

### DEFAULT_MODEL_SET

**Description**: Which Claude model set to use

**Default**: `base`

**Options**:
- `base` - Faster, more cost-effective (Sonnet)
- `heavy` - More powerful (Opus/Sonnet mix)

## Web UI Configuration

### WEB_UI_PORT

**Description**: Port for web frontend

**Default**: `5174`

**Example**: `WEB_UI_PORT=3000`

### WEB_API_PORT

**Description**: Port for backend API

**Default**: `8002`

**Example**: `WEB_API_PORT=8000`

## Cloud Services (Optional)

### E2B Cloud Sandbox

**Description**: Isolated code execution environment

**Get key from**: https://e2b.dev/docs

**Setup**:
1. Sign up at https://e2b.dev
2. Get API key from dashboard
3. Add to `.env`: `E2B_API_KEY=sk_e2b_xxx...`

**Benefits**:
- Isolated execution of generated code
- No risk to your local environment
- Consistent build environment

### Cloudflare Tunnel

**Description**: Expose webhook to GitHub

**When needed**: For automatic ADW trigger on issue creation

**Get token from**: https://dash.cloudflare.com/

**Setup**:
1. Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Create tunnel in Cloudflare dashboard
3. Copy tunnel token
4. Add to `.env`: `CLOUDFLARED_TUNNEL_TOKEN=xxx...`

### Cloudflare R2 (Screenshot Upload)

**Description**: Upload review screenshots to cloud

**Get credentials from**: https://dash.cloudflare.com/

**Setup**:
1. Create R2 bucket in Cloudflare
2. Generate R2 API tokens
3. Configure public domain (optional)
4. Add all credentials to `.env`

**Configuration**:
```bash
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_R2_ACCESS_KEY_ID=your-access-key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret-key
CLOUDFLARE_R2_BUCKET_NAME=your-bucket-name
CLOUDFLARE_R2_PUBLIC_DOMAIN=https://your-bucket.r2.dev
```

**Benefits**:
- Screenshots appear as images in GitHub comments
- Easier visual code review
- No local file path dependencies

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Run `./scripts/setup_env.sh`
- Or manually add to `.env`

### "Claude Code not found"
- Install Claude Code: https://claude.com/code
- Update `CLAUDE_CODE_PATH` in `.env`
- Verify with: `which claude`

### "GitHub not authenticated"
```bash
gh auth login
```

### "Configuration test failed"
```bash
./scripts/test_config.sh
```

Check the output for specific errors.

### Port Already in Use

If ports 5174 or 8002 are already in use:
1. Update `WEB_UI_PORT` and/or `WEB_API_PORT` in `.env`
2. Or stop the conflicting process:
```bash
# Find process using port
lsof -ti:5174
# Kill process
kill -9 <pid>
```

### MCP Server Won't Start
- Ensure Node.js is installed: `node --version`
- Run `npx @playwright/mcp@latest --version` to verify
- Check `.mcp.json` syntax is valid
- See [Playwright MCP Integration](playwright-mcp.md) for details

## Best Practices

### Security
- Never commit `.env` to git
- Use `.env.sample` for team sharing
- Rotate API keys regularly
- Use minimum required token scopes
- Store sensitive values in secure credential managers

### Performance
- Use `base` model set for most tasks
- Use `heavy` only for complex features
- Enable E2B for safer execution
- Monitor token usage with monitoring tools

### Development
- Set `AUTO_POST_ISSUES=false` during testing
- Use separate GitHub repo for experiments
- Keep `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true`
- Test configuration after changes: `./scripts/test_config.sh`

### Team Collaboration
- Keep `.env.sample` up to date
- Document any custom variables in comments
- Share setup instructions in team wiki
- Use consistent port numbers across team

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key |
| `CLAUDE_CODE_PATH` | No | `claude` | Path to Claude binary |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | No | `true` | Keep in project root |
| `GITHUB_PAT` | No | - | GitHub token (optional) |
| `GITHUB_REPO_URL` | No | - | Default repo |
| `AUTO_POST_ISSUES` | No | `false` | Skip confirmation |
| `DEFAULT_WORKFLOW` | No | `adw_sdlc_iso` | ADW workflow |
| `DEFAULT_MODEL_SET` | No | `base` | Model set |
| `WEB_UI_PORT` | No | `5174` | Frontend port |
| `WEB_API_PORT` | No | `8002` | Backend port |
| `E2B_API_KEY` | No | - | Cloud sandbox |
| `CLOUDFLARED_TUNNEL_TOKEN` | No | - | Webhook tunnel |
| `CLOUDFLARE_ACCOUNT_ID` | No | - | R2 account |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` | No | - | R2 access key |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | No | - | R2 secret |
| `CLOUDFLARE_R2_BUCKET_NAME` | No | - | R2 bucket |
| `CLOUDFLARE_R2_PUBLIC_DOMAIN` | No | - | R2 public URL |

## Advanced Configuration

### Custom Workflows

To add custom ADW workflows:
1. Create workflow script in `adws/`
2. Add workflow to `DEFAULT_WORKFLOW` options
3. Update documentation

### Multiple Environments

For different environments (dev, staging, prod):
```bash
# Development
cp .env .env.dev
# Edit .env.dev with dev settings

# Load specific environment
set -a && source .env.dev && set +a
```

### CI/CD Integration

For automated deployments:
1. Store secrets in CI/CD system (GitHub Actions, GitLab CI)
2. Pass as environment variables to build process
3. Never commit actual `.env` files

Example GitHub Actions:
```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  DEFAULT_MODEL_SET: base
```

## Related Documentation

- [Setup Scripts](../scripts/setup_env.sh) - Interactive setup tool
- [Validation Script](../scripts/test_config.sh) - Configuration testing
- [Troubleshooting Guide](troubleshooting.md) - Common issues
- [Quick Start](../README.md#configuration) - Basic setup steps

## Quick Reference Commands

```bash
# Interactive setup
./scripts/setup_env.sh

# Validate configuration
./scripts/test_config.sh

# Check Claude path
which claude

# Check GitHub auth
gh auth status

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```
