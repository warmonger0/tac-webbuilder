# CLI Reference

Complete reference for the tac-webbuilder command-line interface.

## Table of Contents

- [Installation](#installation)
- [Commands](#commands)
- [Configuration](#configuration)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

## Installation

### Prerequisites

- Python 3.10+
- uv (Python package manager)
- GitHub CLI (`gh`)

### Setup

```bash
cd /path/to/tac-webbuilder
uv sync
cp .env.sample .env
# Edit .env with your API keys
```

## Commands

### `request` - Create a feature request

Submit a natural language request to create a GitHub issue and trigger ADW workflow.

**Usage:**
```bash
./scripts/start_cli.sh request "Your feature request"
./scripts/start_cli.sh request --file request.txt
./scripts/start_cli.sh request --stdin < request.txt
```

**Options:**
- `--project PATH` - Target project directory (default: current directory)
- `--repo REPO` - GitHub repository (format: owner/repo)
- `--label LABEL` - Additional label(s) to add to the issue
- `--file FILE` - Read request from file
- `--stdin` - Read request from stdin
- `--preview` - Preview the issue without posting

**Examples:**
```bash
# Simple request
./scripts/start_cli.sh request "Add dark mode toggle"

# Specify target repo
./scripts/start_cli.sh request "Add user auth" --repo myorg/myapp

# From file
./scripts/start_cli.sh request --file feature-request.txt

# Preview before posting
./scripts/start_cli.sh request "Add feature" --preview
```

**Output:**
```
Processing your request...
✓ Detected project: React + Vite
✓ Created GitHub issue #42
✓ Issue URL: https://github.com/owner/repo/issues/42
✓ ADW workflow triggered
```

### `interactive` - Interactive mode

Start an interactive session for creating requests with prompts.

**Usage:**
```bash
./scripts/start_cli.sh interactive
```

**Features:**
- Guided prompts for request details
- Project detection and confirmation
- Preview before posting
- History of recent requests
- Multi-line input support

**Interactive Flow:**
```
Welcome to tac-webbuilder interactive mode!

Project: /Users/you/myapp
Repository: myorg/myapp
Framework: React + Vite

Describe your feature request (Ctrl+D when done):
> Add a user authentication system with:
> - Email/password login
> - OAuth providers (Google, GitHub)
> - Session management with JWT
>
✓ Request created as issue #43
```

### `history` - View request history

View previously created requests and their status.

**Usage:**
```bash
./scripts/start_cli.sh history
./scripts/start_cli.sh history --limit 10
./scripts/start_cli.sh history --filter react
```

**Options:**
- `--limit N` - Show last N requests (default: 20)
- `--filter TEXT` - Filter by text in request or issue title
- `--repo REPO` - Filter by repository
- `--status STATUS` - Filter by status (open, closed, all)
- `--json` - Output as JSON

**Output:**
```
Recent Requests:

#43 - Add user authentication (open)
   Created: 2024-01-15 10:30
   Repo: myorg/myapp
   URL: https://github.com/myorg/myapp/issues/43

#42 - Add dark mode toggle (closed - merged)
   Created: 2024-01-14 15:20
   Repo: myorg/myapp
   URL: https://github.com/myorg/myapp/issues/42
   PR: https://github.com/myorg/myapp/pull/45

Showing 2 of 15 requests. Use --limit to see more.
```

### `config` - View and update configuration

Manage CLI configuration settings.

**Usage:**
```bash
./scripts/start_cli.sh config
./scripts/start_cli.sh config get <key>
./scripts/start_cli.sh config set <key> <value>
./scripts/start_cli.sh config list
```

**Options:**
- `get KEY` - Get a configuration value
- `set KEY VALUE` - Set a configuration value
- `list` - List all configuration
- `reset` - Reset to defaults

**Configurable Settings:**
- `default_repo` - Default GitHub repository
- `default_labels` - Default labels for issues
- `auto_trigger_adw` - Auto-trigger ADW workflow (true/false)
- `preview_before_post` - Always preview before posting (true/false)
- `history_limit` - Default history limit

**Examples:**
```bash
# Set default repo
./scripts/start_cli.sh config set default_repo myorg/myapp

# Get setting
./scripts/start_cli.sh config get default_repo

# List all settings
./scripts/start_cli.sh config list
```

### `new` - Create new project from template

Scaffold a new project using a template.

**Usage:**
```bash
./scripts/start_cli.sh new <project-name> --framework <template>
./scripts/start_cli.sh new <project-name> --framework <template> --path /custom/path
```

**Options:**
- `--framework NAME` - Template to use (react-vite, nextjs, vanilla)
- `--path PATH` - Custom project location
- `--no-install` - Skip dependency installation
- `--no-git` - Skip git initialization
- `--no-github` - Skip GitHub repository creation

**Available Templates:**
- `react-vite` - React + Vite + TypeScript
- `nextjs` - Next.js with App Router
- `vanilla` - Plain HTML/CSS/JS

**Examples:**
```bash
# Create React app
./scripts/start_cli.sh new my-app --framework react-vite

# Create Next.js app in custom location
./scripts/start_cli.sh new my-nextapp --framework nextjs --path ~/projects

# Create without installing dependencies
./scripts/start_cli.sh new my-app --framework react-vite --no-install
```

### `integrate` - Integrate ADW into existing project

Add ADW workflow to an existing codebase.

**Usage:**
```bash
./scripts/start_cli.sh integrate /path/to/existing/app
./scripts/start_cli.sh integrate /path/to/existing/app --preview
```

**Options:**
- `--preview` - Preview integration plan without creating issue
- `--framework NAME` - Manually specify framework (auto-detected by default)

**Process:**
1. Analyzes project structure and framework
2. Creates GitHub issue with integration plan
3. ADW automatically implements integration
4. Review and merge PR

**Examples:**
```bash
# Integrate into existing React app
./scripts/start_cli.sh integrate ~/projects/my-react-app

# Preview integration plan
./scripts/start_cli.sh integrate ~/projects/my-app --preview
```

## Configuration

### Configuration File

CLI configuration is stored in `~/.config/tac-webbuilder/config.json`:

```json
{
  "default_repo": "myorg/myapp",
  "default_labels": ["enhancement"],
  "auto_trigger_adw": true,
  "preview_before_post": false,
  "history_limit": 20,
  "api_url": "http://localhost:8002"
}
```

### Environment Variables

Set in `.env` file in the tac-webbuilder root:

```env
# Required
ANTHROPIC_API_KEY=your-anthropic-key
GITHUB_TOKEN=your-github-token

# Optional
DEFAULT_REPO=owner/repo
API_URL=http://localhost:8002
LOG_LEVEL=INFO
```

## History Storage

Request history is stored locally in:
- **Location:** `~/.local/share/tac-webbuilder/history.json`
- **Format:** JSON array of request objects
- **Size limit:** Last 1000 requests
- **Cleanup:** Automatic, keeps last 1000

History includes:
- Request text
- GitHub issue URL and number
- Repository
- Timestamp
- Status (open, closed, merged)
- Associated PR (if merged)

## Advanced Usage

### Piping Requests

Use pipes to compose requests:

```bash
# From file
cat feature.txt | ./scripts/start_cli.sh request --stdin

# From command output
echo "Add feature X" | ./scripts/start_cli.sh request --stdin

# From clipboard (macOS)
pbpaste | ./scripts/start_cli.sh request --stdin
```

### Batch Requests

Process multiple requests:

```bash
# Create script
cat > requests.txt << EOF
Add user authentication
Add dark mode toggle
Create admin dashboard
EOF

# Process each line
while IFS= read -r line; do
  ./scripts/start_cli.sh request "$line"
  sleep 5  # Rate limiting
done < requests.txt
```

### JSON Output

Get machine-readable output:

```bash
# History as JSON
./scripts/start_cli.sh history --json | jq '.[] | select(.status == "open")'

# Config as JSON
./scripts/start_cli.sh config list --json
```

## Troubleshooting

### Issue: Command not found

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/start_cli.sh

# Or run with bash
bash scripts/start_cli.sh request "..."
```

### Issue: Authentication failed

**Solution:**
```bash
# Check GitHub CLI auth
gh auth status

# Re-authenticate
gh auth login

# Verify token in .env
cat .env | grep GITHUB_TOKEN
```

### Issue: Cannot detect project

**Solution:**
- Ensure you're in a git repository
- Check repository has GitHub remote
- Specify repo explicitly: `--repo owner/repo`

### Issue: API connection failed

**Solution:**
- Check if backend is running: `curl http://localhost:8002/health`
- Start backend: `./scripts/start_web_backend.sh`
- Verify API_URL in .env

## See Also

- [Example Requests](examples.md) - Example natural language requests
- [Web UI Guide](web-ui.md) - Using the web interface
- [API Reference](api.md) - Backend API documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
