# ADW Webhook Trigger System - Setup & Troubleshooting

**Date:** 2025-11-14
**Status:** ✅ Operational

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Investigation Summary](#investigation-summary)
- [Solution Implemented](#solution-implemented)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Overview

The ADW (Automated Development Workflow) system requires a trigger mechanism to automatically start workflows when GitHub issues are created or updated. This document describes the webhook trigger system, the issues encountered during setup, and the complete solution.

### System Components

```
User → Frontend → Backend API → GitHub Issues
                                      ↓
                          GitHub Webhook (HTTP POST)
                                      ↓
                      Cloudflare Tunnel (webhook.directmyagent.com)
                                      ↓
                      Webhook Trigger (localhost:8001)
                                      ↓
                      ADW Workflow Launch (adw_*_iso.py)
```

---

## Architecture

### 1. Webhook Trigger Service

**Location:** `adws/adw_triggers/trigger_webhook.py`
**Port:** 8001
**Endpoints:**
- `POST /gh-webhook` - Receives GitHub webhook events
- `GET /health` - Health check endpoint (comprehensive system check)

**Responsibilities:**
- Listen for GitHub webhook events (issues, issue_comment)
- Parse issue body and comments for workflow commands (e.g., `adw_lightweight_iso`)
- Extract workflow parameters (workflow type, model set, ADW ID)
- Launch ADW workflows in background processes
- Post status updates to GitHub issues

**Key Features:**
- Responds within GitHub's 10-second timeout
- Prevents infinite loops (ignores bot-generated issues/comments)
- Supports both new workflow creation and dependent workflow phases
- Validates workflow requirements (e.g., dependent workflows need ADW IDs)

### 2. Backend Pre-flight Health Check

**Location:** `app/server/server.py:796-848`
**Function:** `check_webhook_trigger_health()`

**Purpose:**
Before posting issues to GitHub, the backend verifies the webhook trigger is online and healthy. This prevents issues from being created when no automation is available to process them.

**Behavior:**
```python
# Before posting issue to GitHub:
await check_webhook_trigger_health()  # Throws HTTP 503 if webhook is down

# If webhook is healthy:
github_poster.post_issue(issue, confirm=False)
```

**Error Response:**
```json
{
  "detail": "ADW webhook trigger is offline. Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
}
```

### 3. Cloudflare Tunnel

**Purpose:** Expose local webhook trigger to the internet so GitHub can reach it

**Configuration:**
- **Tunnel ID:** `5e482074-4677-4f78-9a5b-301a27d9463f`
- **Public URL:** `https://webhook.directmyagent.com`
- **Origin:** `http://localhost:8001`
- **Config File:** `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`

**Routes:**
```yaml
ingress:
  - hostname: webhook.directmyagent.com
    service: http://localhost:8001
  - hostname: tac-webbuilder.directmyagent.com
    service: http://localhost:3000
  - hostname: www.directmyagent.com
    service: http://localhost:3000
  - service: http_status:404
```

### 4. GitHub Webhook

**Repository:** `warmonger0/tac-webbuilder`
**Webhook URL:** `https://webhook.directmyagent.com/gh-webhook`
**Content Type:** `application/json`
**Events:**
- Issues (opened, edited, labeled, etc.)
- Issue comments (created, edited, deleted)

**Webhook ID:** 580534779

---

## Investigation Summary

### The Problem

**Symptom:** ADW workflows were not starting automatically after GitHub issues were created via the tac-webbuilder frontend.

**User Flow:**
1. ✅ User submits NL request through frontend
2. ✅ POST /api/request processes it and generates GitHub issue
3. ✅ POST /api/confirm/{request_id} posts issue to GitHub successfully
4. ✅ Issue appears on GitHub with correct workflow command
5. ❌ **No corresponding ADW workflow starts**

### Root Cause Analysis

**Primary Issue:** Cloudflare tunnel token mismatch

The system had two Cloudflare tunnels:
1. **Old Tunnel (RUNNING):** `7642840a-7379-4fc3-a8c0-06d9f73d626c`
   - This was the tunnel the cloudflared daemon was using
   - **NO ROUTES CONFIGURED** ❌

2. **New Tunnel (CONFIGURED):** `5e482074-4677-4f78-9a5b-301a27d9463f`
   - This tunnel had all the routes configured (webhook.directmyagent.com → localhost:8001)
   - **BUT NOT RUNNING** ❌

**Result:**
- GitHub webhooks → `webhook.directmyagent.com` → Cloudflare Tunnel (wrong tunnel with no routes) → HTTP 530 error
- Webhook trigger running on localhost:8001 was never reached

**Secondary Discoveries:**
- No pre-flight health check existed to warn when webhook trigger was offline
- Issue body format was correct (contained `adw_lightweight_iso with base model`)
- Webhook trigger code was correct and working locally

### Verification Process

```bash
# 1. Decoded tunnel tokens to find tunnel IDs
echo "<TOKEN>" | base64 -d | python3 -m json.tool

# 2. Tested local webhook trigger
curl -X POST http://localhost:8001/gh-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -d '{"action":"opened","issue":{"number":6,"body":"adw_lightweight_iso"}}'
# Result: ✅ Workflow triggered successfully

# 3. Tested public webhook URL
curl https://webhook.directmyagent.com/health
# Result: ❌ HTTP 530 (tunnel error)

# 4. Checked GitHub webhook deliveries
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries
# Result: ❌ All deliveries returning HTTP 530
```

---

## Solution Implemented

### 1. Updated Backend Health Check

**File:** `app/server/server.py`

**Added:**
- `httpx` dependency to `pyproject.toml`
- `check_webhook_trigger_health()` async function (lines 796-848)
- Pre-flight check in `confirm_and_post_issue()` endpoint (line 855)

**Code:**
```python
async def check_webhook_trigger_health() -> dict:
    """
    Check if the ADW webhook trigger service is online and healthy.

    Returns:
        dict: Health status from webhook trigger service

    Raises:
        HTTPException: If webhook trigger is offline or unhealthy
    """
    webhook_url = os.environ.get("WEBHOOK_TRIGGER_URL", "http://localhost:8001")
    health_endpoint = f"{webhook_url}/health"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(health_endpoint)
            response.raise_for_status()
            health_data = response.json()

            # Check if service reports healthy status
            if health_data.get("status") != "healthy":
                errors = health_data.get("health_check", {}).get("errors", [])
                error_msg = ", ".join(errors) if errors else "Service reported unhealthy status"
                raise HTTPException(
                    503,
                    f"ADW webhook trigger is unhealthy: {error_msg}. "
                    f"Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
                )

            return health_data

    except httpx.TimeoutException:
        raise HTTPException(
            503,
            "ADW webhook trigger is not responding (timeout). "
            "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
        )
    except httpx.ConnectError:
        raise HTTPException(
            503,
            "ADW webhook trigger is offline. "
            "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
        )
```

**Configuration:**
```bash
# Optional: Set custom webhook URL
export WEBHOOK_TRIGGER_URL="http://localhost:8001"
```

### 2. Fixed Cloudflare Tunnel

**Problem:** Launch daemon was using wrong tunnel token

**Solution:**

1. **Obtained Correct Token:**
   - Navigated to Cloudflare Zero Trust Dashboard → Networks → Tunnels
   - Clicked "tac-webbuilder" tunnel
   - Clicked "Refresh token" button
   - Copied new token: `eyJhIjoiZGRlM2JkZTVjNjdlZjExNjFlYTU5YWFkYzk1ZDUyOWIiLCJ0IjoiNWU0ODIwN2EtNDY3Ny00Zjc4LTlhNWItMzAxYTI3ZDk0NjNmIiwicyI6IlpEWXdPRFl5WVRZdE5EWXpNQzAwWkRsa0xUbGlZbVl0T1RFd09UTmpNamN3TVRreSJ9`

2. **Updated Launch Daemon:**
   ```bash
   # Created new plist file with correct token
   cat > /tmp/com.cloudflare.cloudflared.plist <<'EOF'
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   	<dict>
   		<key>Label</key>
   		<string>com.cloudflare.cloudflared</string>
   		<key>ProgramArguments</key>
   		<array>
   			<string>/opt/homebrew/bin/cloudflared</string>
   			<string>tunnel</string>
   			<string>run</string>
   			<string>--token</string>
   			<string>eyJhIjoiZGRlM2JkZTVjNjdlZjExNjFlYTU5YWFkYzk1ZDUyOWIiLCJ0IjoiNWU0ODIwN2EtNDY3Ny00Zjc4LTlhNWItMzAxYTI3ZDk0NjNmIiwicyI6IlpEWXdPRFl5WVRZdE5EWXpNQzAwWkRsa0xUbGlZbVl0T1RFd09UTmpNamN3TVRreSJ9</string>
   		</array>
   		<key>RunAtLoad</key>
   		<true/>
   		<key>StandardOutPath</key>
   		<string>/Library/Logs/com.cloudflare.cloudflared.out.log</string>
   		<key>StandardErrorPath</key>
   		<string>/Library/Logs/com.cloudflare.cloudflared.err.log</string>
   		<key>KeepAlive</key>
   		<dict>
   			<key>SuccessfulExit</key>
   			<false/>
   		</dict>
   		<key>ThrottleInterval</key>
   		<integer>5</integer>
   	</dict>
   </plist>
   EOF
   ```

3. **Restarted Tunnel:**
   ```bash
   # Unload old service
   sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

   # Kill running processes
   sudo pkill -9 cloudflared

   # Install new configuration
   sudo cp /tmp/com.cloudflare.cloudflared.plist /Library/LaunchDaemons/
   sudo chown root:wheel /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   sudo chmod 644 /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

   # Load new service
   sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   ```

**Result:** ✅ Tunnel connected successfully, webhook accessible from internet

---

## Verification

### System Health Checks

**1. Verify Webhook Trigger is Running**
```bash
# Check process
ps aux | grep trigger_webhook | grep -v grep

# Check port
lsof -i :8001 | grep LISTEN

# Test health endpoint (local)
curl http://localhost:8001/health | python3 -m json.tool

# Test health endpoint (public)
curl https://webhook.directmyagent.com/health | python3 -m json.tool
```

**Expected Output:**
```json
{
    "status": "healthy",
    "service": "adw-webhook-trigger",
    "health_check": {
        "success": true,
        "warnings": [],
        "errors": [],
        "details": "Run health_check.py directly for full report"
    }
}
```

**2. Verify Cloudflare Tunnel**
```bash
# Check tunnel process
ps aux | grep cloudflared | grep -v grep

# Check tunnel logs
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.out.log
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.err.log

# Test public accessibility
curl -v https://webhook.directmyagent.com/health
```

**3. Verify GitHub Webhook**
```bash
# Check webhook configuration
gh api repos/warmonger0/tac-webbuilder/hooks

# Check recent deliveries
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries --jq '.[] | {id: .id, event: .event, status: .status_code, delivered_at: .delivered_at}' | head -5

# Send test ping
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/pings -X POST
```

**Expected:** All deliveries should return `status_code: 200`

**4. Test End-to-End Flow**
```bash
# Test local webhook with mock payload
curl -X POST http://localhost:8001/gh-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -d '{
    "action": "created",
    "issue": {
      "number": 5,
      "body": "Test issue\n\n## Workflow\nadw_lightweight_iso with base model"
    },
    "comment": {
      "body": "adw_lightweight_iso"
    }
  }'
```

**Expected Output:**
```json
{
    "status": "accepted",
    "issue": 5,
    "adw_id": "<generated-id>",
    "workflow": "adw_lightweight_iso",
    "message": "ADW adw_lightweight_iso triggered for issue #5",
    "reason": "Comment with adw_lightweight_iso workflow",
    "logs": "agents/<adw-id>/adw_lightweight_iso/"
}
```

### Verification Checklist

- [ ] Webhook trigger running on port 8001
- [ ] Health endpoint returns HTTP 200
- [ ] Cloudflare tunnel process running
- [ ] Public webhook URL accessible (HTTP 200)
- [ ] GitHub webhook deliveries returning HTTP 200
- [ ] Test issue comment triggers workflow
- [ ] ADW process starts (check `ps aux | grep adw`)
- [ ] Agent directory created in `agents/<adw-id>/`
- [ ] GitHub issue receives bot comment with status

---

## Troubleshooting

### Issue: Webhook Trigger Not Running

**Symptoms:**
- Backend returns HTTP 503 when confirming issues
- Error message: "ADW webhook trigger is offline"

**Diagnosis:**
```bash
# Check if process is running
ps aux | grep trigger_webhook

# Check port availability
lsof -i :8001
```

**Solution:**
```bash
# Start webhook trigger
cd /Users/Warmonger0/tac/tac-webbuilder/adws
uv run adw_triggers/trigger_webhook.py

# Or run in background
nohup uv run adw_triggers/trigger_webhook.py > /tmp/webhook_trigger.log 2>&1 &
```

---

### Issue: Cloudflare Tunnel Not Working

**Symptoms:**
- `curl https://webhook.directmyagent.com/health` returns error
- GitHub webhook deliveries show HTTP 530
- Cloudflare dashboard shows tunnel as "DOWN"

**Diagnosis:**
```bash
# Check if cloudflared is running
ps aux | grep cloudflared

# Check tunnel logs
sudo tail -50 /Library/Logs/com.cloudflare.cloudflared.err.log

# Decode current token to verify tunnel ID
sudo cat /Library/LaunchDaemons/com.cloudflare.cloudflared.plist | grep -A1 "token" | tail -1 | sed 's/<string>//;s/<\/string>//' | base64 -d | python3 -m json.tool
```

**Common Issues:**

1. **Wrong Tunnel Token**
   - Symptom: Log shows "Failed to connect" or "control stream error"
   - Solution: Refresh token in Cloudflare dashboard and update plist file

2. **Tunnel Not Running**
   ```bash
   # Restart tunnel
   sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   ```

3. **Wrong Routes Configured**
   - Check Cloudflare Zero Trust Dashboard → Networks → Tunnels → tac-webbuilder → Public Hostname
   - Verify: `webhook.directmyagent.com` → `http://localhost:8001`

---

### Issue: GitHub Webhooks Failing

**Symptoms:**
- GitHub webhook deliveries show HTTP 4xx or 5xx
- No ADW workflows starting

**Diagnosis:**
```bash
# Check recent webhook deliveries
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries --jq '.[] | select(.status_code != 200) | {id: .id, event: .event, status: .status_code, delivered_at: .delivered_at}'

# Check specific delivery details
gh api repos/warmonger0/tac-webbuilder/hooks/580534779/deliveries/<DELIVERY_ID>
```

**Solutions:**

1. **HTTP 530 (Cloudflare Error)**
   - Issue: Tunnel not working
   - Solution: See "Cloudflare Tunnel Not Working" section

2. **HTTP 503 (Service Unavailable)**
   - Issue: Webhook trigger not running or not responding
   - Solution: Restart webhook trigger

3. **HTTP 404 (Not Found)**
   - Issue: Wrong webhook URL
   - Solution: Update GitHub webhook URL to `https://webhook.directmyagent.com/gh-webhook`

4. **HTTP 500 (Internal Server Error)**
   - Issue: Bug in webhook trigger code
   - Solution: Check webhook trigger logs: `tail -f /tmp/webhook_trigger.log`

---

### Issue: Workflow Not Starting Despite Webhook Success

**Symptoms:**
- Webhook delivery shows HTTP 200
- Webhook trigger logs show "accepted"
- But no ADW process running

**Diagnosis:**
```bash
# Check webhook trigger logs
# (Look for "Launching" and "Background process started" messages)

# Check if workflow process is running
ps aux | grep "adw_.*_iso.py" | grep -v grep

# Check agent directory
ls -la agents/

# Check issue body format
gh issue view <ISSUE_NUMBER> --json body --jq '.body'
```

**Common Issues:**

1. **Issue Body Missing Workflow Command**
   - Issue body must contain line like: `adw_lightweight_iso with base model`
   - Check `app/server/core/nl_processor.py` for issue body format

2. **Workflow Script Not Found**
   - Check if workflow script exists: `ls adws/adw_lightweight_iso.py`

3. **Permission Issues**
   - Check file permissions: `ls -la adws/*.py`
   - Ensure scripts are executable

4. **Python Environment Issues**
   ```bash
   # Test workflow manually
   cd adws
   uv run adw_lightweight_iso.py <ISSUE_NUMBER>
   ```

---

### Issue: Backend Health Check Timing Out

**Symptoms:**
- POST /api/confirm returns HTTP 503
- Error: "ADW webhook trigger is not responding (timeout)"
- Webhook trigger is running and healthy

**Diagnosis:**
```bash
# Test health check manually
time curl http://localhost:8001/health

# Check if health check takes > 15 seconds
```

**Solution:**

If health check consistently takes > 15 seconds:

1. **Increase Timeout** (app/server/server.py:810)
   ```python
   async with httpx.AsyncClient(timeout=30.0) as client:  # Increase from 15.0
   ```

2. **Optimize Health Check** (adws/adw_triggers/trigger_webhook.py:248-325)
   - Consider caching health check results
   - Run health check script async
   - Return simplified health status

---

## Maintenance

### Daily Operations

**Check System Status:**
```bash
# Quick health check
curl -s http://localhost:8001/health | jq '.status'

# Check all services
ps aux | grep -E "(trigger_webhook|cloudflared)" | grep -v grep
```

**Monitor Logs:**
```bash
# Webhook trigger logs
tail -f /tmp/webhook_trigger.log

# Cloudflare tunnel logs
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.out.log

# Backend logs
# (Check wherever your backend logs are written)
```

### Startup Script

Create a startup script to ensure all services are running:

```bash
#!/bin/bash
# startup_adw_services.sh

echo "Starting ADW services..."

# 1. Start webhook trigger
echo "1. Starting webhook trigger..."
cd /Users/Warmonger0/tac/tac-webbuilder/adws
nohup uv run adw_triggers/trigger_webhook.py > /tmp/webhook_trigger.log 2>&1 &
sleep 2

# 2. Verify Cloudflare tunnel
echo "2. Checking Cloudflare tunnel..."
if ! ps aux | grep -v grep | grep cloudflared > /dev/null; then
    echo "   Cloudflare tunnel not running. Starting..."
    sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
fi

# 3. Wait and verify
sleep 5
echo ""
echo "Verification:"
echo "-------------"

# Check webhook trigger
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Webhook trigger: ONLINE"
else
    echo "❌ Webhook trigger: OFFLINE"
fi

# Check Cloudflare tunnel
if curl -s https://webhook.directmyagent.com/health > /dev/null 2>&1; then
    echo "✅ Cloudflare tunnel: ONLINE"
else
    echo "❌ Cloudflare tunnel: OFFLINE"
fi

echo ""
echo "Services started. Logs:"
echo "  Webhook: /tmp/webhook_trigger.log"
echo "  Tunnel: /Library/Logs/com.cloudflare.cloudflared.out.log"
```

### Backup Configuration

Important files to backup:

```bash
# Cloudflare tunnel configuration
/Library/LaunchDaemons/com.cloudflare.cloudflared.plist
~/.cloudflared/cert.pem

# Backend configuration
app/server/.env
app/server/pyproject.toml

# Webhook trigger
adws/adw_triggers/trigger_webhook.py
```

### Recovery Procedure

If system goes down completely:

1. **Verify Network Connectivity**
   ```bash
   ping github.com
   curl https://www.cloudflare.com
   ```

2. **Restart All Services**
   ```bash
   # Stop everything
   sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   pkill -f trigger_webhook

   # Wait
   sleep 5

   # Start everything
   sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
   cd /Users/Warmonger0/tac/tac-webbuilder/adws
   uv run adw_triggers/trigger_webhook.py &
   ```

3. **Verify Each Component**
   ```bash
   # Test local webhook
   curl http://localhost:8001/health

   # Test public webhook
   curl https://webhook.directmyagent.com/health

   # Test GitHub webhook
   gh api repos/warmonger0/tac-webbuilder/hooks/580534779/pings -X POST
   ```

4. **Check Logs for Errors**
   ```bash
   # Webhook trigger
   tail -100 /tmp/webhook_trigger.log

   # Cloudflare tunnel
   sudo tail -100 /Library/Logs/com.cloudflare.cloudflared.err.log
   ```

---

## Additional Resources

### Related Documentation

- [ADW Technical Overview](./ADW_TECHNICAL_OVERVIEW.md)
- [API Documentation](./api.md)
- [Architecture Overview](./architecture.md)
- [General Troubleshooting](./troubleshooting.md)

### External Links

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [GitHub Webhooks Guide](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Support

For issues or questions:
1. Check this troubleshooting guide
2. Review logs in `/tmp/webhook_trigger.log` and `/Library/Logs/com.cloudflare.cloudflared.err.log`
3. Create a GitHub issue with logs and error messages

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-14 | Initial implementation and documentation | Claude Code |
| 2025-11-14 | Fixed Cloudflare tunnel token mismatch | Claude Code |
| 2025-11-14 | Added backend pre-flight health check | Claude Code |
| 2025-11-14 | Verified end-to-end workflow trigger | Claude Code |
