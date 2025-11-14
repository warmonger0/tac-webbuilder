# Troubleshooting Guide

Solutions to common issues when using tac-webbuilder.

## Table of Contents

- [Configuration Issues](#configuration-issues)
- [Environment Setup](#environment-setup)
- [Playwright MCP](#playwright-mcp)
- [API and Backend](#api-and-backend)
- [Frontend Issues](#frontend-issues)
- [GitHub Integration](#github-integration)
- [ADW Workflow](#adw-workflow)
- [Templates and Integration](#templates-and-integration)
- [Performance](#performance)

## Configuration Issues

### Environment Setup

**Problem**: `.env file not found`

**Solution**:
```bash
# Run interactive setup
./scripts/setup_env.sh

# Or manual setup
cp .env.sample .env
```

---

**Problem**: `ANTHROPIC_API_KEY not set`

**Solution**:
1. Get key from https://console.anthropic.com/settings/keys
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-xxx...`
3. Verify with: `./scripts/test_config.sh`

---

**Problem**: `Claude Code not found`

**Solution**:
1. Check installation: `which claude`
2. Update path in `.env`: `CLAUDE_CODE_PATH=/path/to/claude`
3. Verify with: `./scripts/test_config.sh`

See [Configuration Guide](configuration.md) for detailed setup instructions.

---

### GitHub Authentication

**Problem**: `GitHub not authenticated`

**Solution**:
```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

---

**Problem**: `Cannot create issues`

**Solution**:
1. Verify auth: `gh auth status`
2. Check token scopes if using `GITHUB_PAT` (needs `repo`, `workflow`)
3. Test issue creation: `gh issue create --title "Test" --body "Test"`

See [Configuration Guide](configuration.md#github-configuration) for details.

---

### Cloud Services

**Problem**: `E2B API key invalid`

**Solution**:
1. Verify key at https://e2b.dev/dashboard
2. Check key format: `sk_e2b_...`
3. Update in `.env`

---

**Problem**: `Cloudflare tunnel not working`

**Solution**:
1. Verify tunnel token
2. Check cloudflared is installed: `cloudflared --version`
3. Test tunnel: `cloudflared tunnel run`

---

**Problem**: `R2 screenshot upload fails`

**Solution**:
1. Verify all R2 variables are set in `.env`:
   - `CLOUDFLARE_ACCOUNT_ID`
   - `CLOUDFLARE_R2_ACCESS_KEY_ID`
   - `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
   - `CLOUDFLARE_R2_BUCKET_NAME`
   - `CLOUDFLARE_R2_PUBLIC_DOMAIN`
2. Check bucket exists and is public
3. Test credentials with AWS CLI (R2 is S3-compatible)

See [Configuration Guide](configuration.md#cloudflare-r2-screenshot-upload) for setup details.

---

### Port Conflicts

**Problem**: `Port 5174 already in use`

**Solution**:
```bash
# Find process using port
lsof -ti:5174

# Kill process
kill -9 <pid>

# Or change port in .env
echo "WEB_UI_PORT=3000" >> .env
```

---

**Problem**: `Port 8002 already in use`

**Solution**:
```bash
# Find process using port
lsof -ti:8002

# Kill process
kill -9 <pid>

# Or change port in .env
echo "WEB_API_PORT=8000" >> .env
```

See [Configuration Guide](configuration.md#web-ui-configuration) for port configuration.

---

## Environment Setup

### Issue: Cannot start backend - Python version error

**Symptoms:**
```
Error: Python 3.10 or higher is required
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.10+ using pyenv
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# Or use uv's Python management
uv python install 3.11

# Verify
python --version
```

---

### Issue: uv command not found

**Symptoms:**
```
bash: uv: command not found
```

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Verify
uv --version
```

---

### Issue: Missing environment variables

**Symptoms:**
```
Error: ANTHROPIC_API_KEY not found
Error: GITHUB_TOKEN not found
```

**Solution:**
```bash
# Copy sample env file
cp .env.sample .env

# Edit .env and add your keys
# Get Anthropic key: https://console.anthropic.com/
# Get GitHub token: gh auth token

# Verify environment file
cat .env | grep -E "ANTHROPIC_API_KEY|GITHUB_TOKEN"

# Restart backend
./scripts/start_web_backend.sh
```

---

### Issue: Permission denied on scripts

**Symptoms:**
```
bash: ./scripts/start_cli.sh: Permission denied
```

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Or run with bash
bash scripts/start_cli.sh
```

## Playwright MCP

### Issue: MCP Server Won't Start

**Symptoms:**
```
Error: Cannot start Playwright MCP server
```

**Solution:**
```bash
# Verify Node.js is installed
node --version  # Should be 18+

# Test MCP server directly
npx @playwright/mcp@latest --version

# Check .mcp.json syntax
python3 -m json.tool .mcp.json

# Verify config path
grep "playwright-mcp-config.json" .mcp.json
```

---

### Issue: Browser Launch Fails

**Symptoms:**
```
Error: Executable doesn't exist at /path/to/chromium
```

**Solution:**
```bash
# Install Playwright browsers
npx playwright install chromium

# Or install all browsers
npx playwright install

# Install system dependencies (Linux)
npx playwright install-deps

# Verify installation
npx playwright --version
```

---

### Issue: Videos Not Recording

**Symptoms:**
- No videos appear in videos/ directory
- MCP runs but no recordings

**Solution:**
```bash
# Check videos directory exists
mkdir -p videos

# Verify video config
grep -A 5 "recordVideo" playwright-mcp-config.json

# Check disk space
df -h .

# Try with absolute path temporarily
# Edit playwright-mcp-config.json:
# "dir": "/full/path/to/project/videos"
```

---

### Issue: Screenshots Not Saving

**Symptoms:**
- Screenshot commands execute but no files appear
- Permission denied errors

**Solution:**
```bash
# Create screenshots directory
mkdir -p logs/screenshots

# Check permissions
ls -la logs/

# Fix permissions if needed
chmod 755 logs/
chmod 755 logs/screenshots/

# Verify MCP can write
touch logs/screenshots/test.txt && rm logs/screenshots/test.txt
```

**See [docs/playwright-mcp.md](playwright-mcp.md) for detailed configuration.**

---

## API and Backend

### Issue: Backend fails to start - Port already in use

**Symptoms:**
```
Error: Address already in use (port 8002)
```

**Solution:**
```bash
# Find process using port 8002
lsof -i :8002

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8003 ./scripts/start_web_backend.sh
```

---

### Issue: API returns 500 Internal Server Error

**Symptoms:**
```
{"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
```

**Solution:**
```bash
# Check backend logs
tail -f logs/backend.log

# Check for errors
grep ERROR logs/backend.log

# Restart backend with verbose logging
LOG_LEVEL=DEBUG ./scripts/start_web_backend.sh

# Check database file
ls -lh ~/.local/share/tac-webbuilder/history.db
```

---

### Issue: Cannot connect to backend from frontend

**Symptoms:**
- Frontend shows "API Unavailable"
- Network errors in browser console

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8002/health

# Check API_URL in frontend
# app/client/.env should have:
VITE_API_URL=http://localhost:8002

# Restart frontend
cd app/client
bun run dev

# Check CORS configuration in backend
# app/server/main.py should allow frontend origin
```

---

### Issue: Database locked error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Close all connections to database
pkill -f uvicorn

# Remove lock file
rm ~/.local/share/tac-webbuilder/history.db-wal
rm ~/.local/share/tac-webbuilder/history.db-shm

# Restart backend
./scripts/start_web_backend.sh
```

## Frontend Issues

### Issue: Frontend fails to build

**Symptoms:**
```
Error: Cannot find module 'react'
Build failed with errors
```

**Solution:**
```bash
cd app/client

# Remove node_modules and lockfile
rm -rf node_modules bun.lockb

# Reinstall dependencies
bun install

# Verify dependencies
bun list

# Try building again
bun run build
```

---

### Issue: HMR (Hot Module Replacement) not working

**Symptoms:**
- Changes not reflecting in browser
- Need to manually refresh

**Solution:**
```bash
# Stop frontend
# Clear Vite cache
rm -rf app/client/.vite

# Restart frontend
cd app/client
bun run dev

# If still not working, check file watchers
# macOS: increase file watcher limit
sudo sysctl -w kern.maxfiles=65536
sudo sysctl -w kern.maxfilesperproc=32768
```

---

### Issue: WebSocket connection failed

**Symptoms:**
- "WebSocket disconnected" indicator
- No real-time updates
- Console error: WebSocket connection failed

**Solution:**
```bash
# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8002/ws

# Verify backend is running
curl http://localhost:8002/health

# Check firewall isn't blocking WebSocket
# Restart backend
./scripts/start_web_backend.sh

# Check browser console for details
# Open DevTools → Network → WS tab
```

---

### Issue: TypeScript errors

**Symptoms:**
```
TS2307: Cannot find module 'X'
TS2339: Property 'Y' does not exist
```

**Solution:**
```bash
cd app/client

# Run type checking
bun run type-check

# Update TypeScript
bun add -D typescript@latest

# Regenerate types if using API
# Check tsconfig.json includes all source files

# Clear TypeScript cache
rm -rf node_modules/.cache
```

## GitHub Integration

### Issue: GitHub CLI not authenticated

**Symptoms:**
```
Error: gh: To use GitHub CLI, you must first authenticate
```

**Solution:**
```bash
# Authenticate with GitHub CLI
gh auth login

# Follow prompts:
# - Select GitHub.com
# - Choose HTTPS
# - Authenticate with browser
# - Select repo and workflow permissions

# Verify authentication
gh auth status

# Get token for .env
gh auth token
```

---

### Issue: Cannot create GitHub issue - 401 Unauthorized

**Symptoms:**
```
Error: GitHub API returned 401: Bad credentials
```

**Solution:**
```bash
# Check GitHub token
echo $GITHUB_TOKEN

# Verify token in .env
grep GITHUB_TOKEN .env

# Generate new token if needed
gh auth refresh -s repo,workflow

# Update .env with new token
GITHUB_TOKEN=$(gh auth token)
echo "GITHUB_TOKEN=$GITHUB_TOKEN" >> .env

# Restart backend
./scripts/start_web_backend.sh
```

---

### Issue: Cannot create issue - 404 Not Found

**Symptoms:**
```
Error: Repository not found: owner/repo
```

**Solution:**
```bash
# Verify repository exists
gh repo view owner/repo

# Check repository access
gh repo list owner

# Ensure correct spelling
# Check if repo is private (token needs access)

# Try with full URL
./scripts/start_cli.sh request "..." --repo owner/repo
```

---

### Issue: Rate limit exceeded

**Symptoms:**
```
Error: API rate limit exceeded for user
```

**Solution:**
```bash
# Check rate limit status
gh api rate_limit

# Wait for reset time shown in output

# For higher limits, use authenticated requests
# Ensure GITHUB_TOKEN is set correctly

# Consider caching responses if making many API calls
```

## ADW Workflow

### Issue: ADW workflow not triggering

**Symptoms:**
- Issue created but no ADW activity
- No PR created
- No workflow logs

**Solution:**
```bash
# Check issue has correct labels
gh issue view <issue-number> --json labels

# Verify webhook is configured
# Go to: https://github.com/owner/repo/settings/hooks
# Check webhook is active and has correct payload URL

# Check worktree state
ls -la ~/.local/share/tac-worktrees/

# Manually trigger ADW (if configured)
cd /path/to/project
# Run ADW script manually to debug
```

---

### Issue: ADW workflow stuck or hanging

**Symptoms:**
- Workflow status shows "in progress" for long time
- No recent log updates
- No PR created

**Solution:**
```bash
# Check ADW logs
ls ~/.local/share/tac-worktrees/*/adw.log

# View latest logs
tail -f ~/.local/share/tac-worktrees/*/adw.log

# Check for errors
grep ERROR ~/.local/share/tac-worktrees/*/adw.log

# Check worktree health
cd ~/.local/share/tac-worktrees/<worktree-id>
git status

# Cancel workflow if stuck
# Comment on issue with: /cancel
```

---

### Issue: ADW tests failing

**Symptoms:**
- Workflow fails at testing stage
- PR shows failed CI checks

**Solution:**
```bash
# Check test output in PR
gh pr view <pr-number> --json statusCheckRollup

# Run tests locally
cd /path/to/project
npm test  # or bun test, pytest, etc.

# Fix failing tests
# Comment on PR with feedback
# ADW will update based on comments

# Or manually fix and push to PR branch
git fetch origin
git checkout <pr-branch>
# Fix tests
git commit -am "Fix tests"
git push
```

---

### Issue: Git worktree errors

**Symptoms:**
```
Error: worktree already exists
Error: cannot create worktree
```

**Solution:**
```bash
# List worktrees
git worktree list

# Remove stale worktree
git worktree remove <path-to-worktree>

# Prune invalid worktrees
git worktree prune

# Clean up worktree directory
rm -rf ~/.local/share/tac-worktrees/<stale-worktree>

# Try creating worktree again
```

## Templates and Integration

### Issue: Template scaffolding fails

**Symptoms:**
```
Error: Template 'react-vite' not found
Error: Cannot copy template files
```

**Solution:**
```bash
# Verify templates exist
ls -la templates/new_webapp/

# Check template structure
cat templates/template_structure.json | python -m json.tool

# Verify permissions
chmod -R 755 templates/

# Try scaffolding again with full path
./scripts/setup_new_project.sh myapp react-vite /full/path
```

---

### Issue: Integration script cannot detect framework

**Symptoms:**
```
📊 Detected framework: Unknown
```

**Solution:**
```bash
# Check project has identifying files
ls package.json   # For JavaScript projects
ls requirements.txt  # For Python projects

# Verify file contents
cat package.json | grep react

# Manually specify framework (if supported)
# Or use manual integration steps from guide

# Update project_detector.py if new framework
```

---

### Issue: Template dependencies fail to install

**Symptoms:**
```
Error: Package installation failed
npm ERR! code ENOENT
```

**Solution:**
```bash
# Check package manager is installed
which npm
which bun

# Try different package manager
bun install  # Instead of npm install

# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Check node version
node --version  # Should be 18+
```

## Performance

### Issue: Slow API responses

**Symptoms:**
- Requests take >5 seconds
- Timeouts
- UI feels sluggish

**Solution:**
```bash
# Check backend CPU/memory
top -p $(pgrep -f uvicorn)

# Enable caching in backend
# Check database performance
sqlite3 ~/.local/share/tac-webbuilder/history.db "ANALYZE;"

# Reduce history limit
./scripts/start_cli.sh config set history_limit 50

# Consider upgrading to PostgreSQL for production
```

---

### Issue: High memory usage

**Symptoms:**
- Backend using >1GB RAM
- System slow
- OOM errors

**Solution:**
```bash
# Check memory usage
ps aux | grep uvicorn

# Limit worker processes
# Edit scripts/start_web_backend.sh
# Add: --workers 2

# Clear old worktrees
rm -rf ~/.local/share/tac-worktrees/*

# Restart backend
pkill -f uvicorn
./scripts/start_web_backend.sh
```

---

### Issue: Large log files

**Symptoms:**
- Disk space low
- Log files >1GB

**Solution:**
```bash
# Check log sizes
du -h logs/

# Rotate logs
mv logs/backend.log logs/backend.log.old
touch logs/backend.log

# Add log rotation (logrotate)
# Or limit log size in backend config

# Clean old logs
find logs/ -name "*.log.*" -mtime +30 -delete
```

## Getting More Help

If your issue isn't covered here:

1. **Check Documentation**
   - [CLI Reference](cli.md)
   - [Web UI Guide](web-ui.md)
   - [API Reference](api.md)
   - [Architecture](architecture.md)

2. **Enable Debug Logging**
   ```bash
   LOG_LEVEL=DEBUG ./scripts/start_web_backend.sh
   ```

3. **Check GitHub Issues**
   - Search existing issues
   - Create new issue with:
     - Operating system
     - Python/Node versions
     - Error messages
     - Steps to reproduce

4. **Community Support**
   - Join Discord/Slack (if available)
   - Ask on GitHub Discussions

5. **Collect Debug Information**
   ```bash
   # System info
   uname -a
   python --version
   node --version

   # Backend status
   curl http://localhost:8002/health

   # Recent logs
   tail -100 logs/backend.log

   # Configuration
   cat .env | grep -v "KEY\|TOKEN"
   ```
