# Scripts

## create_issue_safe.sh

Safe issue creation with automatic webhook health check and server management.

### Features

- ✅ Checks webhook server health before creating issue
- ✅ Offers to start webhook server if not running
- ✅ Handles port conflicts automatically
- ✅ Provides clear status messages
- ✅ Falls back gracefully if webhook unavailable

### Usage

```bash
# Same syntax as gh issue create
./scripts/create_issue_safe.sh --title "My Issue" --body-file issue.md

# With labels
./scripts/create_issue_safe.sh --title "Bug fix" --body "Description" --label bug

# Interactive mode
./scripts/create_issue_safe.sh
```

### What it does

1. **Health Check**: Verifies webhook server at `http://localhost:8001/health`
2. **Auto-start**: Offers to start webhook server if not running
3. **Port Management**: Detects and handles port conflicts
4. **Issue Creation**: Creates GitHub issue with your parameters
5. **Status Report**: Shows whether ADW workflow will auto-trigger

### Examples

```bash
# Create issue with webhook check
./scripts/create_issue_safe.sh \
  --title "Add dark mode" \
  --body-file specs/dark-mode.md \
  --label feature

# Output:
# 🔍 Safe Issue Creation with Webhook Health Check
# ================================================
# 
# 🔍 Checking webhook server health...
#    Endpoint: http://localhost:8001/health
# 
# ✅ Webhook server is healthy
# 
# 📝 Creating GitHub issue...
# 
# https://github.com/user/repo/issues/42
# 
# ✅ Issue created successfully!
# 🤖 Webhook server will automatically trigger ADW workflow
```

### Troubleshooting

If webhook server won't start:
```bash
# Check what's using port 8001
lsof -i :8001

# Kill existing process
lsof -ti :8001 | xargs kill -9

# Check server logs
tail -f /tmp/webhook_server.log
```

## Other Scripts

- `clear_issue_comments.sh` - Remove comments from GitHub issues
