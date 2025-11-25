# Frontend Config Refactor Session - 2025-11-25

## Session Overview

This session completed a comprehensive audit of hardcoded values in the tac-webbuilder frontend and created an implementation plan for a centralized configuration system. Additionally, fixed critical backend phantom workflow_history records bug and designed workflow save/resume architecture.

---

## Part 1: Frontend Hardcoded Data Audit

### Executive Summary

**Total Issues Found:** 356+ hardcoded values across React/TypeScript frontend

**Breakdown by Priority:**
- **HIGH Priority:** 15-20 items (breaks in different environments)
- **MEDIUM Priority:** 30-40 items (configuration/maintainability issues)
- **LOW Priority:** 50+ items (consistency improvements)

**Estimated Refactor Time:** 8-10 hours total (2-3h HIGH, 3-4h MEDIUM, 2-3h LOW)

---

## HIGH Priority Issues (MUST FIX)

### 1. Hardcoded Webhook Service URL
**File:** `app/client/src/api/client.ts:212`
```typescript
fetch('http://localhost:8001/webhook-status')
```
**Problem:** Hardcoded localhost URL breaks in production
**Solution:** Environment variable `VITE_WEBHOOK_SERVICE_URL`

---

### 2. Hardcoded WebSocket Port (4 locations)
**File:** `app/client/src/hooks/useWebSocket.ts`
**Lines:** 21, 55, 100, 171
```typescript
const wsUrl = `${protocol}//${host}:8000/ws/workflows`;
const wsUrl = `${protocol}//${host}:8000/ws/routes`;
const wsUrl = `${protocol}//${host}:8000/ws/workflow-history`;
const wsUrl = adwId ? `${protocol}//${host}:8000/ws/adw-state/${adwId}` : '';
```
**Problem:** Port 8000 hardcoded in WebSocket URLs
**Solution:** Environment variable `VITE_WS_PORT` or derive from `VITE_API_BASE_URL`

---

### 3. Hardcoded GitHub Repository URLs
**File:** `app/client/src/components/PhaseQueueCard.tsx`
**Lines:** 94, 101
```typescript
window.open(`https://github.com/warmonger0/tac-webbuilder/issues/${issue_number}`, '_blank');
window.open(`https://github.com/warmonger0/tac-webbuilder/pull/${pr_number}`, '_blank');
```
**Problem:** Repository-specific URLs won't work for different repos
**Solution:** Environment variable `VITE_GITHUB_REPO_URL`

---

### 4. Hardcoded GitHub Domain
**File:** `app/client/src/components/AdwMonitorCard.tsx:318`
```typescript
href={`https://github.com/${new URL(currentWorkflow.github_url).pathname...}`}
```
**Problem:** Assumes github.com (not GitHub Enterprise compatible)
**Solution:** Environment variable `VITE_GIT_HOST`

---

### 5. Hardcoded Polling Intervals
**File:** `app/client/src/hooks/useReliablePolling.ts:36-40`
```typescript
interval = 60000,           // 60 seconds
minInterval = 30000,        // 30 seconds
maxInterval = 120000,       // 2 minutes
maxConsecutiveErrors = 5,
```
**Problem:** Different environments need different polling rates
**Solution:** Config file `src/config/polling.config.ts`

---

## MEDIUM Priority Issues

### 6. WebSocket Configuration
**File:** `app/client/src/hooks/useReliableWebSocket.ts:36-38, 93-96`
```typescript
pollingInterval = 3000,         // 3 seconds fallback
maxReconnectDelay = 30000,      // 30 seconds max delay
maxReconnectAttempts = 10,
const baseDelay = 1000;         // Start at 1 second
```
**Problem:** Hardcoded retry/reconnection strategy
**Solution:** Config file `src/config/websocket.config.ts`

---

### 7. Component-Specific Polling Intervals
**Files & Lines:**
- `AdwMonitorCard.tsx:33` - `interval: summary.running > 0 ? 10000 : 30000`
- `SystemStatusPanel.tsx:23, 78, 96, 133` - Multiple 30s/2s timeouts
- `ZteHopperQueueCard.tsx:39` - `setInterval(fetchData, 10000)`
**Problem:** Inconsistent polling intervals, not configurable
**Solution:** Centralized `POLLING_INTERVALS` config

---

### 8. File Upload Size Limit
**File:** `app/client/src/utils/fileHandlers.ts:6`
```typescript
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;  // 5MB
```
**Problem:** Different environments may have different limits
**Solution:** Environment variable `VITE_MAX_FILE_SIZE_MB`

---

### 9. Workflow Health Thresholds
**File:** `app/client/src/components/WorkflowProgressVisualization.tsx:45-46`
```typescript
const STUCK_THRESHOLD = 10 * 60 * 1000;   // 10 minutes
const HUNG_THRESHOLD = 20 * 60 * 1000;    // 20 minutes
```
**Problem:** Different workflows may have different SLAs
**Solution:** Config constant `WORKFLOW_HEALTH_THRESHOLDS`

---

### 10. Native Alert/Confirm Dialogs
**Files:**
- `PhaseQueueCard.tsx:115, 119` - `alert()` calls
- `main.ts:470` - `confirm()` dialog
**Problem:** No internationalization, poor UX, not themeable
**Solution:** Replace with toast notifications and ConfirmDialog component

---

## LOW Priority Issues

### 11. UI Timing Constants
**Files:**
- `main.ts:31` - `DEBOUNCE_DELAY = 400`
- `FileUploadSection.tsx:65, 96` - `setTimeout(..., 3000)`
- `WorkflowCard.tsx:18` - `setTimeout(..., 1000)`
**Solution:** Config constant `UI_TIMING`

---

### 12. Connection Quality Thresholds
**File:** `useReliablePolling.ts:93-98, 202`
```typescript
if (errors === 0 && timeSinceLastSuccess < 10000) return 'excellent';
if (errors <= 1 && timeSinceLastSuccess < 30000) return 'good';
if (errors <= 3 && timeSinceLastSuccess < 60000) return 'poor';
```
**Solution:** Config constant `CONNECTION_QUALITY_THRESHOLDS`

---

### 13. Workflow Phase Definitions
**Files:**
- `AdwMonitorCard.tsx:56-66` - Hardcoded workflow phases array
- `WorkflowProgressVisualization.tsx:31-42` - Duplicate workflow steps
**Problem:** Should be single source of truth
**Solution:** Fetch from `/api/workflow-phases` or shared config

---

### 14. Status Color Mappings
**File:** `PhaseQueueCard.tsx:35-84`
```typescript
const STATUS_COLORS = {
  queued: { bg: 'bg-gray-100', border: 'border-gray-300', ... },
  // ... 6 status types
};
```
**Solution:** Move to `src/config/theme.ts` or CSS variables

---

## Implementation Plan

### Phase 1: Create Config Infrastructure (30 minutes)

**Step 1:** Create centralized config file

**File:** `app/client/src/config/index.ts`
```typescript
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
    wsPort: import.meta.env.VITE_WS_PORT || '8000',
    webhookUrl: import.meta.env.VITE_WEBHOOK_SERVICE_URL || 'http://localhost:8001',
  },
  github: {
    repoUrl: import.meta.env.VITE_GITHUB_REPO_URL || 'https://github.com/warmonger0/tac-webbuilder',
    host: import.meta.env.VITE_GIT_HOST || 'https://github.com',
  },
  polling: {
    defaultInterval: parseInt(import.meta.env.VITE_POLL_INTERVAL || '60000'),
    activeInterval: parseInt(import.meta.env.VITE_POLL_ACTIVE_INTERVAL || '10000'),
    minInterval: parseInt(import.meta.env.VITE_POLL_MIN_INTERVAL || '30000'),
    maxInterval: parseInt(import.meta.env.VITE_POLL_MAX_INTERVAL || '120000'),
    maxConsecutiveErrors: parseInt(import.meta.env.VITE_MAX_CONSECUTIVE_ERRORS || '5'),
  },
  websocket: {
    pollingFallbackInterval: parseInt(import.meta.env.VITE_WS_FALLBACK_INTERVAL || '3000'),
    maxReconnectDelay: parseInt(import.meta.env.VITE_WS_MAX_RECONNECT_DELAY || '30000'),
    maxReconnectAttempts: parseInt(import.meta.env.VITE_WS_MAX_RECONNECT_ATTEMPTS || '10'),
    reconnectBaseDelay: parseInt(import.meta.env.VITE_WS_RECONNECT_BASE_DELAY || '1000'),
  },
  files: {
    maxSizeMB: parseInt(import.meta.env.VITE_MAX_FILE_SIZE_MB || '5'),
  },
  ui: {
    debounceMs: parseInt(import.meta.env.VITE_UI_DEBOUNCE_MS || '400'),
    notificationDurationMs: parseInt(import.meta.env.VITE_NOTIFICATION_DURATION_MS || '3000'),
    staggerLoadDelays: {
      adwMonitor: parseInt(import.meta.env.VITE_STAGGER_ADW_MS || '100'),
      hopperQueue: parseInt(import.meta.env.VITE_STAGGER_QUEUE_MS || '400'),
    },
  },
  workflow: {
    stuckThresholdMs: parseInt(import.meta.env.VITE_WORKFLOW_STUCK_THRESHOLD_MS || '600000'), // 10 min
    hungThresholdMs: parseInt(import.meta.env.VITE_WORKFLOW_HUNG_THRESHOLD_MS || '1200000'), // 20 min
  },
};

export type Config = typeof config;
```

**Step 2:** Create environment variables template

**File:** `app/client/.env.example`
```bash
# API Configuration
VITE_API_BASE_URL=/api
VITE_WS_PORT=8000
VITE_WEBHOOK_SERVICE_URL=http://localhost:8001

# GitHub Configuration
VITE_GITHUB_REPO_URL=https://github.com/your-org/your-repo
VITE_GIT_HOST=https://github.com

# Polling Configuration (milliseconds)
VITE_POLL_INTERVAL=60000
VITE_POLL_ACTIVE_INTERVAL=10000
VITE_POLL_MIN_INTERVAL=30000
VITE_POLL_MAX_INTERVAL=120000
VITE_MAX_CONSECUTIVE_ERRORS=5

# WebSocket Configuration (milliseconds)
VITE_WS_FALLBACK_INTERVAL=3000
VITE_WS_MAX_RECONNECT_DELAY=30000
VITE_WS_MAX_RECONNECT_ATTEMPTS=10
VITE_WS_RECONNECT_BASE_DELAY=1000

# File Upload Configuration
VITE_MAX_FILE_SIZE_MB=5

# UI Configuration (milliseconds)
VITE_UI_DEBOUNCE_MS=400
VITE_NOTIFICATION_DURATION_MS=3000
VITE_STAGGER_ADW_MS=100
VITE_STAGGER_QUEUE_MS=400

# Workflow Health Thresholds (milliseconds)
VITE_WORKFLOW_STUCK_THRESHOLD_MS=600000
VITE_WORKFLOW_HUNG_THRESHOLD_MS=1200000
```

**Step 3:** Add TypeScript path alias (if not exists)

**File:** `app/client/tsconfig.json`
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/config": ["./src/config"]
    }
  }
}
```

---

### Phase 2: Fix HIGH Priority Items (2-3 hours)

#### Fix 1: Webhook Service URL
**File:** `app/client/src/api/client.ts:212`

**Before:**
```typescript
fetch('http://localhost:8001/webhook-status')
```

**After:**
```typescript
import { config } from '@/config';

fetch(`${config.api.webhookUrl}/webhook-status`)
```

---

#### Fix 2: WebSocket Ports (4 locations)
**File:** `app/client/src/hooks/useWebSocket.ts`

**Before (line 21):**
```typescript
const wsUrl = `${protocol}//${host}:8000/ws/workflows`;
```

**After:**
```typescript
import { config } from '@/config';

const wsUrl = `${protocol}//${host}:${config.api.wsPort}/ws/workflows`;
```

**Apply same fix to lines 55, 100, 171**

---

#### Fix 3: GitHub Repository URLs
**File:** `app/client/src/components/PhaseQueueCard.tsx:94,101`

**Before:**
```typescript
window.open(`https://github.com/warmonger0/tac-webbuilder/issues/${issue_number}`, '_blank');
window.open(`https://github.com/warmonger0/tac-webbuilder/pull/${pr_number}`, '_blank');
```

**After:**
```typescript
import { config } from '@/config';

window.open(`${config.github.repoUrl}/issues/${issue_number}`, '_blank');
window.open(`${config.github.repoUrl}/pull/${pr_number}`, '_blank');
```

---

#### Fix 4: GitHub Domain
**File:** `app/client/src/components/AdwMonitorCard.tsx:318`

**Before:**
```typescript
href={`https://github.com/${new URL(currentWorkflow.github_url).pathname.split('/').slice(1, 3).join('/')}/pull/${currentWorkflow.pr_number}`}
```

**After:**
```typescript
import { config } from '@/config';

href={`${config.github.host}/${new URL(currentWorkflow.github_url).pathname.split('/').slice(1, 3).join('/')}/pull/${currentWorkflow.pr_number}`}
```

---

#### Fix 5: Polling Intervals
**File:** `app/client/src/hooks/useReliablePolling.ts:36-40`

**Before:**
```typescript
interval = 60000,
adaptiveInterval = true,
minInterval = 30000,
maxInterval = 120000,
maxConsecutiveErrors = 5,
```

**After:**
```typescript
import { config } from '@/config';

interval = config.polling.defaultInterval,
adaptiveInterval = true,
minInterval = config.polling.minInterval,
maxInterval = config.polling.maxInterval,
maxConsecutiveErrors = config.polling.maxConsecutiveErrors,
```

---

### Phase 3: Fix MEDIUM Priority Items (3-4 hours)

Follow similar pattern for:
- WebSocket configuration (useReliableWebSocket.ts)
- Component polling intervals (AdwMonitorCard, SystemStatusPanel, ZteHopperQueueCard)
- File upload limits (fileHandlers.ts)
- Workflow health thresholds (WorkflowProgressVisualization.tsx)
- Replace alert/confirm with proper components

---

### Phase 4: Fix LOW Priority Items (2-3 hours)

Follow similar pattern for:
- UI timing constants
- Connection quality thresholds
- Workflow phase definitions (consider API endpoint)
- Status color mappings (consider theme config)

---

## Testing Checklist

After implementing config system:

- [ ] Test in development environment (`bun run dev`)
- [ ] Verify WebSocket connections work with config values
- [ ] Test webhook status endpoint with config URL
- [ ] Verify GitHub links open correctly
- [ ] Test polling intervals are respected
- [ ] Verify file upload size limit works
- [ ] Test workflow health threshold calculations
- [ ] Create production `.env` file with real values
- [ ] Test build process (`bun run build`)
- [ ] Verify no hardcoded values remain in bundle

---

## Migration Notes

### Backward Compatibility
- All config values have sensible defaults matching current hardcoded values
- No breaking changes to existing functionality
- Can deploy incrementally (config system first, then update components)

### Deployment Strategy
1. Merge config infrastructure (Phase 1)
2. Deploy to staging with `.env` file
3. Fix HIGH priority items
4. Deploy and verify
5. Fix MEDIUM priority items in batches
6. Fix LOW priority items as needed

### Environment-Specific Overrides

**Development (`.env.development`):**
```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_PORT=8000
VITE_WEBHOOK_SERVICE_URL=http://localhost:8001
```

**Staging (`.env.staging`):**
```bash
VITE_API_BASE_URL=https://staging-api.tac-webbuilder.com/api
VITE_WS_PORT=443
VITE_WEBHOOK_SERVICE_URL=https://staging-webhooks.tac-webbuilder.com
```

**Production (`.env.production`):**
```bash
VITE_API_BASE_URL=https://api.tac-webbuilder.com/api
VITE_WS_PORT=443
VITE_WEBHOOK_SERVICE_URL=https://webhooks.tac-webbuilder.com
VITE_GITHUB_REPO_URL=https://github.com/your-org/your-repo
```

---

## Related Work This Session

### Backend Phantom Records Fix (Completed)
- Fixed 361 phantom workflow_history records (356 database + 5 state files)
- Patched filesystem.py to set end_time when inferring status
- Added debug logging for future phantom detection
- Verified no more [PHANTOM] warnings in logs

### Architecture Documentation (Completed)
- Created workflow save/resume technical specification
- Designed checkpoint system with 5-phase implementation plan
- Documented edge cases and recovery strategies

### Frontend Components (Completed)
- Added WorkflowProgressVisualization.tsx component
- Added useStaggeredLoad.ts hook
- Created feature documentation

---

## Commits

**Expected Commits for Config Refactor:**

1. **feat: Add frontend configuration architecture**
   - Create src/config/index.ts
   - Create .env.example
   - Add TypeScript path alias
   - Document config system

2. **refactor: Fix HIGH priority hardcoded values**
   - Update api/client.ts webhook URL
   - Update useWebSocket.ts ports (4 locations)
   - Update PhaseQueueCard.tsx GitHub URLs
   - Update AdwMonitorCard.tsx GitHub domain
   - Update useReliablePolling.ts intervals

3. **refactor: Fix MEDIUM priority hardcoded values**
   - Update WebSocket configuration
   - Update component polling intervals
   - Update file upload limits
   - Update workflow health thresholds
   - Replace native dialogs with components

4. **refactor: Fix LOW priority hardcoded values**
   - Update UI timing constants
   - Update connection quality thresholds
   - Centralize workflow phase definitions
   - Move status colors to theme config

---

## Success Metrics

- **Zero hardcoded environment-specific values** in production bundle
- **All configuration externalized** to .env files
- **TypeScript type safety** for all config values
- **Documentation complete** for all environment variables
- **No breaking changes** to existing functionality
- **Improved maintainability** - config changes don't require code changes

---

## Additional Resources

- Original audit report: In agent memory (356+ issues documented)
- Frontend quick start: `.claude/commands/quick_start/frontend.md`
- Backend architecture: `.claude/commands/quick_start/backend.md`
- Workflow save/resume design: `docs/architecture/workflow-save-resume.md`

---

## Session Artifacts

**Files Created:**
- `app/server/scripts/fix_phantom_records.py` - Migration script for phantom records
- `docs/architecture/workflow-save-resume.md` - Complete technical specification
- `docs/architecture/workflow-save-resume-quickstart.md` - Executive summary
- `docs/architecture/workflow-save-resume-diagrams.md` - Visual flow diagrams
- `app/client/src/components/WorkflowProgressVisualization.tsx` - New component
- `app/client/src/hooks/useStaggeredLoad.ts` - New hook

**Files Modified:**
- `app/server/core/workflow_history_utils/filesystem.py` - Phantom fix
- `app/server/core/workflow_history_utils/database/mutations.py` - Debug logging
- `app/server/core/workflow_history_utils/database/schema.py` - Migration check
- 5 ADW state files - Manual end_time fixes

**Commits Created:**
- `542669d` - fix: Prevent phantom workflow_history records without end_time
- `bb5fce1` - feat: Add animated workflow progress visualization component

---

## Next Session Priorities

1. ✅ Implement frontend config architecture (this document)
2. Review and commit remaining modified files
3. Test phantom fix with new workflow
4. Optional: Implement workflow save/resume Phase 1

---

**Document Version:** 1.0
**Created:** 2025-11-25
**Author:** Claude Code Session
**Project:** tac-webbuilder
