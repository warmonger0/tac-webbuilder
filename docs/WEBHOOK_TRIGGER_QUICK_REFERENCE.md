# Webhook Trigger Quick Reference

**Last Updated:** 2025-11-14

## 🚀 Quick Start

### Start All Services
```bash
# 1. Start webhook trigger
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run adw_triggers/trigger_webhook.py &

# 2. Verify Cloudflare tunnel
ps aux | grep cloudflared | grep -v grep

# 3. Check health
curl http://localhost:8001/health
curl https://webhook.directmyagent.com/health
```

---

## 🔍 Health Checks

### Local Webhook Trigger
```bash
# Process check
ps aux | grep trigger_webhook | grep -v grep

# Port check
lsof -i :8001

# Health endpoint
curl -s http://localhost:8001/health | jq '.status'
```

### Public Webhook (via Cloudflare)
```bash
# Test public URL
curl -s https://webhook.directmyagent.com/health | jq '.status'

# Check Cloudflare tunnel
ps aux | grep cloudflared | grep -v grep
sudo tail -20 /Library/Logs/com.cloudflare.cloudflared.out.log
```

### GitHub Webhooks
```bash
# Check webhook deliveries
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries \
  --jq '.[] | {event: .event, status: .status_code, delivered_at: .delivered_at}' \
  | head -5

# Send test ping
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/pings -X POST
```

---

## 🐛 Common Issues

### ❌ Webhook Trigger Offline

**Symptom:** Backend returns "ADW webhook trigger is offline"

**Fix:**
```bash
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run adw_triggers/trigger_webhook.py &
```

### ❌ Cloudflare Tunnel Down

**Symptom:** Public URL returns error, GitHub webhooks fail with HTTP 530

**Fix:**
```bash
# Restart tunnel
sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# Verify
sleep 5
curl https://webhook.directmyagent.com/health
```

### ❌ Workflow Not Starting

**Symptom:** Webhook succeeds but no ADW process

**Check:**
```bash
# 1. Verify issue body contains workflow command
gh issue view <ISSUE_NUMBER> --json body --jq '.body' | grep "adw_"

# 2. Check webhook trigger logs
tail -50 /tmp/webhook_trigger.log | grep -E "(Detected|Launching|error)"

# 3. Check if workflow process is running
ps aux | grep "adw_.*_iso.py" | grep -v grep
```

**Fix:**
```bash
# Manually trigger workflow for testing
cd adws
uv run adw_lightweight_iso.py <ISSUE_NUMBER>
```

---

## 📋 System Architecture

```
┌─────────────────┐
│   Frontend UI   │
└────────┬────────┘
         │ POST /api/request
         ▼
┌─────────────────┐
│  Backend API    │ ← Health check before posting
│  (port 8000)    │
└────────┬────────┘
         │ gh issue create
         ▼
┌─────────────────┐
│  GitHub Issue   │
│   #5 created    │
└────────┬────────┘
         │ Webhook POST
         ▼
┌─────────────────┐
│ Cloudflare Tunnel│ webhook.directmyagent.com
│   (port 443)    │ ───► http://localhost:8001
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Webhook Trigger │ Receives & parses event
│  (port 8001)    │ Extracts workflow command
└────────┬────────┘
         │ Launch process
         ▼
┌─────────────────┐
│  ADW Workflow   │ uv run adw_lightweight_iso.py 5
│   Process       │
└─────────────────┘
```

---

## 📁 Key Files

### Configuration
- `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` - Cloudflare tunnel config
- `app/server/.env` - Backend environment variables
- `app/server/pyproject.toml` - Backend dependencies (includes httpx)

### Code
- `adws/adw_triggers/trigger_webhook.py` - Webhook trigger service
- `app/server/server.py:796-848` - Health check function
- `app/server/server.py:850-876` - Issue posting with pre-flight check

### Logs
- `/tmp/webhook_trigger.log` - Webhook trigger logs (if running in background)
- `/Library/Logs/com.cloudflare.cloudflared.out.log` - Tunnel stdout
- `/Library/Logs/com.cloudflare.cloudflared.err.log` - Tunnel stderr

### State
- `agents/<adw-id>/adw_state.json` - Workflow state
- `agents/<adw-id>/<workflow>/` - Workflow logs and output

---

## 🔧 Maintenance Commands

### Daily Health Check
```bash
# One-liner to check all services
echo "Webhook Trigger:" && curl -s http://localhost:8001/health | jq -r '.status' && \
echo "Cloudflare Tunnel:" && curl -s https://webhook.directmyagent.com/health | jq -r '.status' && \
echo "GitHub Webhooks:" && gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries --jq '.[0].status_code'
```

### Restart All Services
```bash
# Stop
pkill -f trigger_webhook
sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# Start
sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run adw_triggers/trigger_webhook.py &
```

### View Logs
```bash
# Webhook trigger
tail -f /tmp/webhook_trigger.log

# Cloudflare tunnel (requires sudo)
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.out.log
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.err.log

# Active workflows
ls -la agents/
```

---

## 🧪 Test Commands

### Test Local Webhook
```bash
curl -X POST http://localhost:8001/gh-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -d '{
    "action": "created",
    "issue": {
      "number": 999,
      "body": "Test\n\n## Workflow\nadw_lightweight_iso with base model"
    },
    "comment": {
      "body": "adw_lightweight_iso"
    }
  }' | jq
```

### Test End-to-End via GitHub
```bash
# Post comment to trigger workflow
gh issue comment <ISSUE_NUMBER> --body "adw_lightweight_iso"

# Check webhook delivery
sleep 2
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries \
  --jq '.[0] | {event: .event, status: .status_code}'

# Verify workflow started
ps aux | grep "adw_.*_iso.py <ISSUE_NUMBER>" | grep -v grep
```

---

## 📞 Support

**Full Documentation:** [WEBHOOK_TRIGGER_SETUP.md](./WEBHOOK_TRIGGER_SETUP.md)

**Troubleshooting Steps:**
1. Check this quick reference
2. Review full documentation
3. Check logs (webhook trigger + Cloudflare tunnel)
4. Test each component individually
5. Create GitHub issue with logs

**Key Endpoints:**
- Local health: http://localhost:8001/health
- Public health: https://webhook.directmyagent.com/health
- Backend API: http://localhost:8000
- Webhook endpoint: https://webhook.directmyagent.com/gh-webhook

**GitHub Webhook ID:** 580534779
**Cloudflare Tunnel ID:** 5e482074-4677-4f78-9a5b-301a27d9463f
