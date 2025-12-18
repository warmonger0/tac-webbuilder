# GitHub Webhook Setup Guide - Planned Features Sync

> **Note**: This project has TWO separate webhook systems. This guide covers **Planned Features Sync** (port 8002).
> For **ADW Trigger Webhooks** (port 8001), see [`adws/README.md`](../adws/README.md).
> For architecture overview, see [`docs/webhook-architecture.md`](webhook-architecture.md).

## Overview

This webhook system synchronizes GitHub issue state changes to the `planned_features` database. When a GitHub issue is closed, reopened, or labeled, the corresponding planned feature is automatically updated and the UI is refreshed via WebSocket.

**This is NOT the ADW trigger webhook** - that runs on port 8001 and launches workflows.

## Features

- **Real-time UI updates**: No manual refresh needed when GitHub issues change
- **Automatic status sync**: Issue closed → Feature completed, Issue reopened → Feature in-progress
- **Label sync**: GitHub labels automatically sync to feature tags
- **Secure**: HMAC-SHA256 signature verification prevents unauthorized requests
- **Idempotent**: Safe to replay webhooks, only updates when changes detected

## Quick Start

### 1. Set Webhook Secret

Set the `GITHUB_WEBHOOK_SECRET` environment variable:

```bash
# In .env or shell
export GITHUB_WEBHOOK_SECRET="your_secret_here_use_random_string"

# Generate a secure secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Expose Port 8002 via Cloudflare Tunnel

Update your Cloudflare Tunnel configuration to expose the backend API:

```bash
# Run the automated update script
cd /Users/Warmonger0/tac/tac-webbuilder
./scripts/update_tunnel_config.sh
```

This will:
- Add `api.directmyagent.com → localhost:8002` route
- Restart the Cloudflare Tunnel service
- Verify the configuration

**Or manually update:**
1. Edit `/Users/Warmonger0/tac/tac-webbuilder/config/cloudflare-tunnel.yml`
2. Add the new ingress rule for api.directmyagent.com
3. Restart tunnel: `sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist && sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist`

### 3. Configure GitHub Webhook

Go to your GitHub repository settings:

1. Navigate to: **Settings** → **Webhooks** → **Add webhook**

2. Configure webhook:
   - **Payload URL**: `https://api.directmyagent.com/api/v1/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Use the same secret from step 1
   - **SSL verification**: Enable (recommended)

3. Select events:
   - ☑️ **Issues** (required)
   - ☐ Issue comments (optional, for future expansion)
   - ☐ Pull requests (optional, for future expansion)

4. Click **Add webhook**

### 4. Verify Webhook

GitHub will send a `ping` event. Check:
- Webhook shows green checkmark ✅
- Recent deliveries show 200 OK responses
- Server logs show: `[WEBHOOK] Received GitHub webhook: ping`

### 5. Link Planned Features to GitHub Issues

For automatic sync to work, planned features must have a `github_issue_number`:

```bash
# Via API
curl -X POST http://localhost:8002/api/v1/planned-features \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add dark mode",
    "item_type": "feature",
    "status": "planned",
    "github_issue_number": 123,
    "priority": "high"
  }'

# Or via UI
# Panel 5 (Plans) → Create Feature → Enter GitHub issue number
```

## How It Works

### Workflow

```
GitHub Issue #123 closed
    ↓
GitHub sends webhook POST to /api/v1/webhooks/github
    ↓
Webhook handler validates signature (security)
    ↓
Find planned_feature with github_issue_number=123
    ↓
Update status to "completed", set completed_at
    ↓
Broadcast WebSocket message to all connected clients
    ↓
PlansPanel (Panel 5) receives update
    ↓
UI refreshes immediately (no manual refresh needed)
```

### Supported Event Actions

| GitHub Action | Planned Feature Update |
|---------------|------------------------|
| `issues.closed` | `status = "completed"`, `completed_at = now` |
| `issues.reopened` | `status = "in_progress"`, `completed_at = null` |
| `issues.labeled` | `tags = [label names]` |
| `issues.unlabeled` | `tags = [label names]` |

### What Gets Synced

- ✅ Issue closed → Feature completed
- ✅ Issue reopened → Feature in-progress
- ✅ Labels added/removed → Tags updated
- ❌ Issue title (manual update only)
- ❌ Issue description (manual update only)
- ❌ Issue assignees (not synced)

## Testing

### Test with Mock Payloads

```bash
# Run test script (server must be running)
cd app/server
python test_github_webhook.py
```

### Test with Real GitHub Events

1. Create a planned feature with `github_issue_number`
2. Close the corresponding GitHub issue
3. Watch PlansPanel update in real-time (no refresh!)
4. Check server logs for webhook processing:

```bash
tail -f logs/app.log | grep WEBHOOK
```

Expected logs:
```
[WEBHOOK] Received GitHub webhook: issues
[WEBHOOK] Processing issue #123 action: closed
[WEBHOOK] Marking feature 45 as completed (issue #123 closed)
[WEBHOOK] Updated planned feature 45 from issue #123
[WEBHOOK] Broadcasted planned features update to WebSocket clients
```

### Test Signature Verification

```bash
# Test with invalid signature (should fail with 401)
curl -X POST http://localhost:8002/api/v1/webhooks/github \
  -H "X-GitHub-Event: issues" \
  -H "X-Hub-Signature-256: sha256=invalid" \
  -H "Content-Type: application/json" \
  -d '{"action":"closed","issue":{"number":123}}'

# Expected: 401 Unauthorized
```

## Troubleshooting

### Webhook Returns 401 Unauthorized

**Cause**: Signature verification failed

**Solutions**:
1. Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook secret
2. Check environment variable is set: `echo $GITHUB_WEBHOOK_SECRET`
3. Restart server after changing environment variable
4. Check GitHub webhook "Recent Deliveries" for exact error

### Webhook Returns 200 but UI Doesn't Update

**Possible causes**:

1. **Planned feature not linked to issue**
   - Check server logs for: `No planned feature found for issue #123`
   - Solution: Add `github_issue_number` to planned feature

2. **WebSocket not connected**
   - Check PlansPanel connection indicator (top-right)
   - Should show green dot + "Live"
   - Solution: Click "Reconnect" button or refresh page

3. **Status already matches**
   - Check logs for: `No updates needed for feature X`
   - This is normal if GitHub state already matches planned feature

### GitHub Webhook Shows Red X

**Cause**: Server not reachable or returning errors

**Solutions**:
1. Check server is running: `curl http://localhost:8002/api/v1/health`
2. For production: Verify domain/SSL certificate
3. For local testing: Use ngrok or similar tunnel
4. Check firewall rules allow incoming webhooks

### WebSocket Disconnects Frequently

**Cause**: Network issues or server restarts

**Solutions**:
- WebSocket has automatic reconnection (exponential backoff)
- Connection quality indicator shows: excellent / good / poor
- Check server logs for: `[WS] Client connected/disconnected`

## Cloudflare Tunnel Setup

This project uses Cloudflare Tunnel to expose local services to the internet securely.

### Current Tunnel Routes

```yaml
# Tunnel ID: 5e482074-4677-4f78-9a5b-301a27d9463f
ingress:
  - hostname: webhook.directmyagent.com
    service: http://localhost:8001  # ADW Webhook Trigger

  - hostname: api.directmyagent.com
    service: http://localhost:8002  # Backend API (NEW)

  - hostname: tac-webbuilder.directmyagent.com
    service: http://localhost:3000  # Frontend

  - hostname: www.directmyagent.com
    service: http://localhost:3000  # Frontend
```

### Benefits of Cloudflare Tunnel

- ✅ No port forwarding required
- ✅ Works on dynamic IPs
- ✅ Free SSL/TLS certificates
- ✅ DDoS protection
- ✅ Automatic DNS management

### Managing the Tunnel

```bash
# Check tunnel status
launchctl list | grep cloudflare

# View tunnel logs
tail -f /Library/Logs/com.cloudflare.cloudflared.out.log

# Restart tunnel
sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# Update tunnel configuration
./scripts/update_tunnel_config.sh
```

## Security Considerations

### Signature Verification

- **REQUIRED**: Always set `GITHUB_WEBHOOK_SECRET`
- **NEVER**: Disable signature verification in production
- Webhook handler uses constant-time comparison to prevent timing attacks
- Uses HMAC-SHA256 (GitHub's standard)

### Secret Management

```bash
# ✅ Good: Use environment variable
export GITHUB_WEBHOOK_SECRET="random_secure_string"

# ✅ Better: Use secrets manager
export GITHUB_WEBHOOK_SECRET=$(aws secretsmanager get-secret-value ...)

# ❌ Bad: Hardcode in code
WEBHOOK_SECRET = "my_secret"  # NEVER DO THIS
```

### Rate Limiting

- Webhook handler returns 200 even on errors to prevent retries
- GitHub retries failed webhooks (5xx errors)
- Logging tracks all webhook attempts
- Consider rate limiting if receiving spam webhooks

## Monitoring

### Health Check

```bash
# Check webhook is accessible
curl -X POST http://localhost:8002/api/v1/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{}'

# Should return 200 (may show signature error, that's OK)
```

### Metrics to Track

- Webhook success rate (check GitHub "Recent Deliveries")
- WebSocket broadcast success rate (check logs)
- Planned feature sync accuracy (manual spot checks)
- Webhook processing latency (check logs for timestamps)

## Future Enhancements

Potential additions (not yet implemented):

- [ ] Sync issue title changes
- [ ] Sync issue description changes
- [ ] Track issue comments as activity
- [ ] Support pull request events
- [ ] Support project board events
- [ ] Webhook delivery retries with exponential backoff
- [ ] Webhook event analytics dashboard

## API Reference

### Webhook Endpoint

```
POST /api/v1/webhooks/github
```

**Headers:**
- `X-GitHub-Event`: Event type (e.g., "issues", "pull_request")
- `X-Hub-Signature-256`: HMAC-SHA256 signature
- `Content-Type`: application/json

**Request Body:** GitHub webhook payload (varies by event type)

**Response:**
- `200 OK`: Webhook processed (even if error occurred, to prevent retries)
- `401 Unauthorized`: Invalid signature

**Example Issue Closed Event:**
```json
{
  "action": "closed",
  "issue": {
    "number": 123,
    "title": "Add dark mode",
    "state": "closed",
    "labels": [
      {"name": "enhancement"},
      {"name": "priority:high"}
    ]
  }
}
```

## Support

For issues or questions:
- Check server logs: `tail -f logs/app.log | grep WEBHOOK`
- Check GitHub webhook deliveries: Repo Settings → Webhooks → Recent Deliveries
- File an issue: [GitHub Issues](https://github.com/your-org/tac-webbuilder/issues)

---

**Last Updated:** 2025-12-17
**Version:** 1.0.0
**Author:** TAC Webbuilder Team
