# Webhook Architecture Overview

## Two Separate Webhook Systems

This project has **TWO DISTINCT** webhook systems that serve different purposes:

### 1. ADW Trigger Webhook (Port 8001)
**Purpose**: Triggers AI Developer Workflows (ADW) from GitHub issues

```
┌──────────────┐
│   GitHub     │
│   Issues     │
└──────┬───────┘
       │ Webhook: issues.opened, issues.labeled
       │ Command: /workflow <type>
       ↓
┌────────────────────────────────────────┐
│ ADW Webhook Service (Port 8001)        │
│ File: adws/adw_triggers/trigger_webhook.py │
│                                        │
│ • Validates webhook signature          │
│ • Runs pre-flight checks               │
│ • Launches ADW in isolated worktree    │
│ • Posts observability events to backend│
└────────────────────────────────────────┘
```

**Key Details:**
- **Port**: 8001
- **File**: `adws/adw_triggers/trigger_webhook.py`
- **Cloudflare Domain**: `webhook.directmyagent.com`
- **Endpoints**:
  - `POST /gh-webhook` - Receives GitHub webhook events
  - `GET /webhook-status` - Status endpoint (stats, uptime, failures)
  - `GET /ping` - Health check
- **CORS**: **NOT CONFIGURED** (intentional - not accessed from browser)
- **Access Pattern**:
  - GitHub → Direct POST
  - Backend → Direct HTTP GET (internal)
  - Frontend → **NEVER DIRECTLY**

**Event Flow**:
1. User comments `/workflow sdlc_planner` on GitHub issue
2. GitHub sends `issues.labeled` webhook to `webhook.directmyagent.com/gh-webhook`
3. Webhook service validates signature, runs checks
4. Webhook service launches ADW in isolated worktree
5. Webhook service POSTs event to backend `/api/v1/observability/log-webhook-event`

---

### 2. Planned Features Sync Webhook (Port 8002)
**Purpose**: Syncs GitHub issue state changes to planned_features database

```
┌──────────────┐
│   GitHub     │
│   Issues     │
└──────┬───────┘
       │ Webhook: issues.closed, issues.reopened
       │
       ↓
┌────────────────────────────────────────┐
│ Backend API (Port 8002)                │
│ File: app/server/routes/github_webhook_routes.py │
│                                        │
│ • Validates webhook signature          │
│ • Finds planned_feature by issue number│
│ • Updates status (completed/in-progress)│
│ • Syncs labels to tags                 │
│ • Broadcasts to WebSocket clients      │
└────────────────────────────────────────┘
       │
       ↓ WebSocket broadcast
┌────────────────────────────────────────┐
│ Frontend (Port 5173)                   │
│ Component: PlansPanel                  │
│                                        │
│ • Receives real-time status update     │
│ • UI refreshes without manual refresh  │
└────────────────────────────────────────┘
```

**Key Details:**
- **Port**: 8002 (main backend)
- **File**: `app/server/routes/github_webhook_routes.py`
- **Cloudflare Domain**: `api.directmyagent.com`
- **Endpoint**: `POST /api/v1/webhooks/github`
- **CORS**: **CONFIGURED** (allows frontend on port 5173)
- **Access Pattern**:
  - GitHub → Direct POST
  - Frontend → WebSocket updates (not HTTP)

**Event Flow**:
1. User closes GitHub issue #123
2. GitHub sends `issues.closed` webhook to `api.directmyagent.com/api/v1/webhooks/github`
3. Backend finds `planned_feature` with `github_issue_number=123`
4. Backend updates `status='completed'`, `completed_at=now()`
5. Backend broadcasts update via `/api/v1/ws/planned-features` WebSocket
6. PlansPanel receives update and refreshes UI

---

## Webhook Status Monitoring

### Frontend Access Pattern

**WRONG** ❌:
```typescript
// DO NOT DO THIS - causes CORS errors
const status = await fetch('http://localhost:8001/webhook-status');
```

**CORRECT** ✅:
```typescript
// Use WebSocket context
const { webhookStatusData } = useGlobalWebSocket();
// webhookStatusData contains: { status, uptime, stats, recent_failures }
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│ Webhook Service (Port 8001)                     │
│ • NO CORS (security by design)                  │
│ • Only accepts requests from GitHub & backend   │
└──────────────────────┬──────────────────────────┘
                       │
                       │ HTTP GET /webhook-status
                       │ (Backend internal request)
                       ↓
┌─────────────────────────────────────────────────┐
│ Backend API (Port 8002)                         │
│ server.py: get_webhook_status_data()            │
│ • Fetches from port 8001 every 30s              │
│ • Broadcasts to WebSocket clients               │
└──────────────────────┬──────────────────────────┘
                       │
                       │ WebSocket: /api/v1/ws/webhook-status
                       │ (Real-time broadcast)
                       ↓
┌─────────────────────────────────────────────────┐
│ Frontend (Port 5173)                            │
│ GlobalWebSocketContext                          │
│ • Connects to WebSocket                         │
│ • Receives real-time status updates             │
│ • NO HTTP fallback (WebSocket only)             │
└─────────────────────────────────────────────────┘
```

**Why NO CORS on Port 8001?**
- Webhook service is intentionally lightweight
- Only needs to accept GitHub webhooks and backend requests
- Adding CORS would allow any website to probe the webhook service
- Security: Minimize attack surface
- Frontend gets data via backend WebSocket (proper separation of concerns)

---

## Configuration

### Environment Variables

**ADW Webhook Service (Port 8001)**:
```bash
PORT=8001                           # Webhook service port
GITHUB_PAT=ghp_...                  # GitHub Personal Access Token
GITHUB_WEBHOOK_SECRET=...           # Signature validation
BACKEND_API_URL=http://localhost:8002  # For observability logging
```

**Backend API (Port 8002)**:
```bash
BACKEND_PORT=8002                   # Main backend port
GITHUB_WEBHOOK_SECRET=...           # Must match webhook config
WEBHOOK_PORT=8001                   # For internal status fetching
```

**Frontend (Port 5173)**:
```bash
VITE_BACKEND_URL=http://localhost:8002   # Backend API base URL
# NO VITE_WEBHOOK_SERVICE_URL - frontend never contacts port 8001
```

### Cloudflare Tunnel Configuration

```yaml
# /Users/Warmonger0/tac/tac-webbuilder/config/cloudflare-tunnel.yml

ingress:
  # ADW Webhook Trigger (Port 8001)
  - hostname: webhook.directmyagent.com
    service: http://localhost:8001
    # Receives: GitHub webhooks for ADW triggering

  # Backend API (Port 8002)
  - hostname: api.directmyagent.com
    service: http://localhost:8002
    # Receives: GitHub webhooks for planned features sync
    # Provides: WebSocket connections for frontend

  # Frontend (Port 5173 or 3000)
  - hostname: tac-webbuilder.directmyagent.com
    service: http://localhost:3000

  - service: http_status:404
```

---

## GitHub Webhook Configuration

You need to configure **TWO** separate webhooks in GitHub:

### Webhook 1: ADW Trigger

**Settings → Webhooks → Add webhook**:
- **Payload URL**: `https://webhook.directmyagent.com/gh-webhook`
- **Content type**: `application/json`
- **Secret**: Your `GITHUB_WEBHOOK_SECRET`
- **Events**:
  - ☑️ Issues (for `/workflow` commands)
  - ☑️ Issue comments (for commands in comments)
- **Active**: ☑️

### Webhook 2: Planned Features Sync

**Settings → Webhooks → Add webhook**:
- **Payload URL**: `https://api.directmyagent.com/api/v1/webhooks/github`
- **Content type**: `application/json`
- **Secret**: Your `GITHUB_WEBHOOK_SECRET`
- **Events**:
  - ☑️ Issues (for close/reopen/label events)
- **Active**: ☑️

---

## Common Mistakes

### ❌ MISTAKE 1: Frontend tries to access port 8001
```typescript
// DON'T DO THIS
fetch('http://localhost:8001/webhook-status'); // CORS error!
```
**Fix**: Use `useGlobalWebSocket()` hook

### ❌ MISTAKE 2: Backend doesn't have CORS for port 8001
**This is intentional!** Port 8001 should NOT have CORS. It's not a public API.

### ❌ MISTAKE 3: Confusing the two webhook systems
- Port 8001 = ADW triggering (launches workflows)
- Port 8002 = Planned features sync (updates database)
- They are SEPARATE systems with different purposes

### ❌ MISTAKE 4: Expecting HTTP fallback for webhook status
```typescript
// This doesn't exist
GET /api/v1/webhook-status  // 404 Not Found
```
**Fix**: Webhook status is WebSocket-only, no HTTP endpoint on backend

---

## Testing

### Test ADW Webhook (Port 8001)
```bash
# Check webhook service is running
curl http://localhost:8001/ping

# Get webhook status
curl http://localhost:8001/webhook-status

# Test GitHub webhook signature validation
curl -X POST http://localhost:8001/gh-webhook \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{}'
```

### Test Planned Features Webhook (Port 8002)
```bash
# Check backend is running
curl http://localhost:8002/api/v1/health

# Test webhook endpoint
curl -X POST http://localhost:8002/api/v1/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{}'
```

### Test WebSocket Status Updates
```bash
# Connect to WebSocket and watch updates
# (Use browser console or WebSocket client)
ws://localhost:8002/api/v1/ws/webhook-status
```

---

## Documentation Files

- **This file**: `docs/webhook-architecture.md` - Architecture overview
- **Setup guide**: `docs/github-webhook-setup.md` - Planned features sync setup
- **ADW README**: `adws/README.md` - ADW system overview
- **Observability**: `docs/features/webhook-observability-decision.md` - Observability design

---

**Last Updated**: 2025-12-18
**Version**: 2.0.0
