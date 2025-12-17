# Add api.directmyagent.com Route to Cloudflare Tunnel

## Current Status

✅ Code committed and pushed to origin
✅ Backend webhook endpoint ready at `/api/v1/webhooks/github`

## Issue Found

Your Cloudflare Tunnel is using **token-based setup** (not config file), so routes must be added via the **Cloudflare Dashboard**.

Current LaunchDaemon uses:
```bash
cloudflared tunnel run --token <token>
```

Routes are managed in the Cloudflare Zero Trust dashboard, not via config file.

---

## Steps to Add the New Route

### 1. Open Cloudflare Dashboard

Go to: https://one.dash.cloudflare.com/

### 2. Navigate to Tunnels

1. Click **Networks** → **Tunnels**
2. Find your tunnel (should be named something related to directmyagent)
3. Click **Edit** (or **Configure**)

### 3. Add Public Hostname

1. Go to **Public Hostname** tab
2. Click **Add a public hostname**
3. Configure:
   - **Subdomain**: `api`
   - **Domain**: `directmyagent.com`
   - **Type**: `HTTP`
   - **URL**: `localhost:8002`

4. Click **Save hostname**

### 4. Verify Configuration

After saving, you should see:

| Public Hostname | Service |
|----------------|---------|
| webhook.directmyagent.com | http://localhost:8001 |
| **api.directmyagent.com** | **http://localhost:8002** ← NEW |
| tac-webbuilder.directmyagent.com | http://localhost:3000 |
| www.directmyagent.com | http://localhost:3000 |

### 5. Wait for DNS Propagation

- DNS changes typically take 1-2 minutes
- No tunnel restart needed (token-based tunnels update automatically)

---

## Test the New Route

After 1-2 minutes, test:

```bash
# Test health endpoint
curl https://api.directmyagent.com/api/v1/health

# Expected response:
# {"status":"healthy"} or similar
```

If this works, the route is live! ✅

---

## Next Steps After Route is Live

### 1. Set GitHub Webhook Secret

```bash
# Generate secure secret
export GITHUB_WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Add to shell profile
echo "export GITHUB_WEBHOOK_SECRET='$GITHUB_WEBHOOK_SECRET'" >> ~/.zshrc

# Verify
echo $GITHUB_WEBHOOK_SECRET
```

### 2. Restart Backend

```bash
# Restart backend to pick up the new env var
cd app/server
python server.py
```

### 3. Configure GitHub Webhook

Go to your GitHub repository:

**Settings** → **Webhooks** → **Add webhook**

Configure:
- **Payload URL**: `https://api.directmyagent.com/api/v1/webhooks/github`
- **Content type**: `application/json`
- **Secret**: Your `$GITHUB_WEBHOOK_SECRET`
- **SSL verification**: ✅ Enable
- **Events**: Select "Issues"

Save and verify green checkmark appears.

### 4. Test End-to-End

```bash
# Create test planned feature
curl -X POST http://localhost:8002/api/v1/planned-features \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Webhook Sync",
    "item_type": "feature",
    "status": "in_progress",
    "github_issue_number": 999,
    "priority": "high"
  }'

# Then close GitHub issue #999
# Watch PlansPanel update immediately!
```

---

## Troubleshooting

### Can't find tunnel in dashboard?

Check tunnel ID:
```bash
cat /Library/LaunchDaemons/com.cloudflare.cloudflared.plist | grep token
```

The token contains your tunnel ID. You can decode it at:
https://www.base64decode.org/

### Route doesn't appear?

Make sure you're logged into the correct Cloudflare account that owns `directmyagent.com`.

### DNS not resolving?

```bash
# Check DNS
dig api.directmyagent.com

# Should show Cloudflare nameservers
```

Wait 5 minutes and try again if not resolving yet.

---

## Alternative: Convert to Config File (Advanced)

If you prefer config-file based setup:

1. Create config file at `/Users/Warmonger0/tac/tac-webbuilder/config/cloudflare-tunnel.yml` (already created)
2. Update LaunchDaemon to use `--config` instead of `--token`
3. Restart tunnel service

**Benefits**: Version controlled routes, easier to manage
**Drawbacks**: More complex setup, need credentials file

For now, **using the dashboard is simpler and faster**.

---

## Summary

**What you need to do:**

1. ✅ Open Cloudflare Dashboard → Networks → Tunnels
2. ✅ Edit your tunnel
3. ✅ Add public hostname: `api.directmyagent.com` → `localhost:8002`
4. ⏳ Wait 1-2 minutes for DNS
5. ✅ Test: `curl https://api.directmyagent.com/api/v1/health`
6. ✅ Configure GitHub webhook with the URL

Then real-time sync will be live! 🚀
