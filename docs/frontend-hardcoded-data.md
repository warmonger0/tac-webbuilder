# Frontend Hard-Coded Data Documentation

**Generated:** 2025-11-28
**Scope:** Complete audit of `app/client/src/` directory
**Total Items:** 200+

## Executive Summary

This document catalogs all hard-coded data in the tac-webbuilder frontend. Hard-coded values include UI text, URLs, configuration values, default data, and visual constants that are embedded directly in component code rather than externalized to configuration files.

### Key Findings

- **200+ hard-coded items** identified across 15+ component files
- **Critical infrastructure values** (GitHub URLs, API endpoints, ports) require immediate extraction
- **Extensive UI text strings** present opportunities for future internationalization (i18n)
- **Multiple polling intervals and timeouts** scattered across components
- **Status color mappings and visual themes** need centralization

---

## 1. UI Text & Strings (120+ items)

### Application-Level Text

**File:** `app/client/src/App.tsx`
- Line 35: `"tac-webbuilder"` - Application title
- Line 38: `"Build web apps with natural language"` - Subtitle/tagline

**File:** `app/client/src/components/TabBar.tsx`
- Line 8: `"New Request"` - Tab label
- Line 9: `"Workflows"` - Tab label
- Line 10: `"History"` - Tab label
- Line 11: `"API Routes"` - Tab label

### Request Form Strings

**File:** `app/client/src/components/RequestFormCore.tsx`
- Line 71: `"Create New Request"` - Section header
- Line 80: `"Describe what you want to build"` - Label
- Line 85: `"Example: Build a REST API for user management with CRUD operations..."` - Placeholder
- Line 109: `"Project path (optional)"` - Label
- Line 114: `"/Users/username/projects/my-app"` - Placeholder
- Line 130: `"Auto-post to GitHub (skip confirmation)"` - Checkbox label
- Line 163: `"Processing..."` - Button loading state
- Line 163: `"Generate Issue"` - Button text

### Workflow Dashboard Strings

**File:** `app/client/src/components/WorkflowDashboard.tsx`
- Line 20: `"Loading workflow catalog..."` - Loading message
- Line 28: `"Error loading workflow catalog"` - Error message
- Line 44: `"ADW Workflow Catalog"` - Section header
- Line 47: `"Available automated development workflows for your projects"` - Description
- Line 78: `"Workflow Steps:"` - Label
- Line 97: `"Purpose:"` - Label
- Line 105: `"Best for:"` - Label

### Pre-Flight Check Strings

**File:** `app/client/src/components/PreflightCheckPanel.tsx`
- Line 65: `"Pre-Flight Health Checks"` - Title
- Line 67: `"System readiness before launching ADW workflows"` - Description
- Line 78: `"Skip test checks (faster)"` - Checkbox label
- Line 85: `"Checking..."` - Button loading text
- Line 85: `"Run Checks"` - Button text
- Line 93: `"Running pre-flight checks..."` - Loading message
- Line 100: `"Error running pre-flight checks"` - Error header
- Line 121: `"All Checks Passed"` - Success message
- Line 121: `"Checks Failed"` - Failure message
- Line 125: `"System ready for ADW workflows"` - Success detail
- Line 126: `"Fix blocking issues before launching workflows"` - Failure detail
- Line 131: `"Completed in {ms}ms"` - Completion time text
- Line 140: `"🚫 Blocking Failures ({count})"` - Section header
- Line 148: `"Fix:"` - Label
- Line 153: `"View failing tests ({count})"` - Details toggle
- Line 174: `"⚠️ Warnings ({count})"` - Section header
- Line 182: `"Impact:"` - Label
- Line 192: `"Check Details"` - Section header

### System Status Strings

**File:** `app/client/src/components/SystemStatusPanel.tsx`
- Line 250: `"System Status"` - Title
- Line 265: `"Refresh"` - Button text
- Line 296: `"Overall Status:"` - Label
- Line 298: `"{count} of {total} services healthy ({percent}%)"` - Summary text
- Line 193: `"Starting..."` - Button loading text
- Line 193: `"Start Service"` - Button text
- Line 202: `"Restarting..."` - Button loading text
- Line 202: `"Restart Tunnel"` - Button text
- Line 212: `"Redelivering..."` - Button loading text
- Line 214: `"Test Webhook"` - Button text (healthy state)
- Line 215: `"Redeliver Failed"` - Button text (error state)

### Workflow History Strings

**File:** `app/client/src/components/WorkflowHistoryView.tsx`
- Line 53: `"Workflow History"` - Header
- Line 66: `"Search"` - Label
- Line 73: `"Search by ADW ID or request..."` - Placeholder
- Line 80: `"Status"` - Filter label
- Line 87: `"All Statuses"` - Dropdown option
- Line 99: `"Model"` - Filter label
- Line 106: `"All Models"` - Dropdown option
- Line 119: `"Active filters:"` - Label
- Line 122: `"Search: {term}"` - Filter chip
- Line 127: `"Status: {status}"` - Filter chip
- Line 132: `"Model: {model}"` - Filter chip
- Line 143: `"Clear all"` - Button text
- Line 151: `"Showing {count} of {total} workflows"` - Results count
- Line 157: `"No workflow history found"` - Empty state
- Line 160: `"Workflow executions will appear here once they are run"` - Empty state detail
- Line 161: `"Try adjusting your filters"` - Empty state detail

### Routes View Strings

**File:** `app/client/src/components/RoutesView.tsx`
- Line 34: `"Just now"` - Timestamp text
- Line 35: `"{n}s ago"` - Timestamp format
- Line 36: `"{n}m ago"` - Timestamp format
- Line 37: `"{n}h ago"` - Timestamp format
- Line 78: `"Live updates"` - Connection status
- Line 78: `"Reconnecting..."` - Connection status
- Line 89: `"No routes found"` - Empty message
- Line 91: `"Routes will appear here once the server is analyzed"` - Empty detail
- Line 104: `"API Routes"` - Header
- Line 112: `"Live updates"` - Connection status
- Line 112: `"Polling fallback"` - Connection status
- Line 128: `"Search routes by path, handler, or description..."` - Placeholder
- Line 144: `"All Methods"` - Dropdown option
- Line 153: `"Showing {count} of {total} routes"` - Results count
- Line 163: `"Method"` - Table header
- Line 166: `"Path"` - Table header
- Line 169: `"Handler"` - Table header
- Line 172: `"Description"` - Table header
- Line 180: `"No routes match your filters"` - Empty state
- Line 199: `"N/A"` - Default handler
- Line 204: `"No description"` - Default description

### Connection Status Strings

**File:** `app/client/src/components/ConnectionStatusIndicator.tsx`
- Line 25: `"Live"` - Status label
- Line 33: `"Connected"` - Status label
- Line 41: `"Slow"` - Status label
- Line 49: `"Offline"` - Status label
- Line 59: `"Never"` - Last updated text
- Line 64: `"Just now"` - Timestamp
- Line 65: `"{n}s ago"` - Timestamp format
- Line 66: `"{n}m ago"` - Timestamp format
- Line 77: `"Connection: {label}"` - Tooltip
- Line 104: `"Retry"` - Button text
- Line 111: `"Last update:"` - Label
- Line 114: `"Reconnect attempts: {n}"` - Status text
- Line 114: `"Errors: {n}"` - Status text
- Line 121: `"Connection lost. Retrying automatically..."` - Warning
- Line 127: `"Connection is slow. Updates may be delayed."` - Warning

### Dialog & Preview Strings

**File:** `app/client/src/components/ConfirmDialog.tsx`
- Line 22: `"Confirm GitHub Issue"` - Dialog title
- Line 38: `"Post to GitHub (Est. ${min}-${max})"` - Button text with cost
- Line 39: `"Post to GitHub"` - Button text (no cost)
- Line 45: `"Cancel"` - Button text

**File:** `app/client/src/components/IssuePreview.tsx`
- Line 30: `"Classification:"` - Label
- Line 34: `"Workflow:"` - Label
- Line 37: `"Model Set:"` - Label

**File:** `app/client/src/components/RequestFormPreview.tsx`
- Line 27: `"Preview"` - Section header

### Cost Estimate Strings

**File:** `app/client/src/components/CostEstimateCard.tsx`
- Line 21: `"💡"` - Icon (lightweight)
- Line 28: `"💰"` - Icon (standard)
- Line 35: `"⚠️"` - Icon (complex)
- Line 48: `"Estimated Cost"` - Title
- Line 58: `"Cost Range"` - Label
- Line 63: `"Confidence: {percent}%"` - Text
- Line 69: `"Recommended Workflow"` - Label
- Line 76: `"Analysis"` - Label
- Line 79: `"Standard complexity assessment"` - Default reasoning
- Line 90: `"High Cost Warning"` - Warning title
- Line 93: `"This workflow may be expensive. Consider:"` - Warning text
- Line 96: `"Breaking into smaller issues (2-3 separate workflows)"` - Suggestion
- Line 97: `"Narrowing the scope to essential features only"` - Suggestion
- Line 98: `"Implementing manually for complex parts"` - Suggestion
- Line 99: `"Using the lightweight workflow if applicable"` - Suggestion
- Line 109: `"💡 Tip: Lightweight workflows ($0.20-$0.50) are ideal for simple UI changes, docs, and single-file modifications."` - Tip text

### Phase Queue Strings

**File:** `app/client/src/components/PhaseQueueCard.tsx`
- Line 42: `"Queued"` - Status label
- Line 50: `"Ready"` - Status label
- Line 58: `"Running"` - Status label
- Line 66: `"Completed"` - Status label
- Line 74: `"Blocked"` - Status label
- Line 82: `"Failed"` - Status label
- Line 115: `"✅ {message}\n\nADW ID: {id}\nIssue: #{number}"` - Alert success
- Line 119: `"❌ Failed to execute phase:\n\n{error}"` - Alert error
- Line 161: `"Collapse details"` - Tooltip
- Line 161: `"Expand details"` - Tooltip
- Line 171: `"Start phase execution"` - Tooltip
- Line 176: `"Starting..."` - Button text
- Line 181: `"Processing"` - Button text
- Line 204: `"View Issue #{number}"` - Tooltip
- Line 207: `"Open"` - Button text
- Line 214: `"View PR #{number}"` - Tooltip

### Hopper Queue Strings

**File:** `app/client/src/components/ZteHopperQueueCard.tsx`
- Line 84: `"Hopper Queue"` - Title
- Line 89: `"{n} in progress • {n} completed"` - Status summary
- Line 109: `"In Progress ({count})"` - Tab label
- Line 121: `"Completed ({count})"` - Tab label
- Line 130: `"⚠️ {error}"` - Error prefix
- Line 146: `"Loading queue..."` - Loading message
- Line 161: `"Queue Empty"` - Empty state
- Line 180: `"Completed items will be displayed here"` - Empty state

### ADW Monitor Strings

**File:** `app/client/src/components/AdwMonitorCard.tsx`
- Line 169: `"Loading workflows..."` - Loading message
- Line 185: `"Unable to load workflows"` - Error message
- Line 263: `"Current Workflow"` - Title
- Line 265: `"Real-time progress"` - Subtitle
- Line 289: `"No Active Workflow"` - Empty state
- Line 290: `"Queue is empty"` - Empty detail
- Line 339: `"Planning Phase"` - Workflow type label
- Line 340: `"Full SDLC"` - Workflow type label
- Line 341: `"Standard SDLC"` - Workflow type label
- Line 342: `"Workflow {id}"` - Default workflow label
- Line 365: `"HEALTH"` - Badge text
- Line 789: `"{n} / {total} phases completed"` - Progress text

### File Upload Strings

**File:** `app/client/src/components/request-form/FileUploadSection.tsx`
- Line 64: `"Multi-phase document detected with {n} phases"` - Success message
- Line 85: `"File uploaded successfully"` - Success message
- Line 87: `"{n} files uploaded successfully"` - Success message
- Line 92: `". Rejected files: {names}"` - Rejection suffix
- Line 98: `"Failed to read file(s)"` - Error message
- Line 128: `"Upload .md file"` - Button text
- Line 130: `"or drag and drop anywhere"` - Helper text
- Line 154: `"Drop .md file anywhere on this card"` - Drop zone text
- Line 155: `"Supports multiple files"` - Drop zone detail
- Line 165: `"Reading file(s)..."` - Loading text

---

## 2. URLs & API Endpoints (10 items)

### API Configuration

**File:** `app/client/src/api/baseClient.ts`
- Line 8: `"/api/v1"` - **API base URL prefix**

### WebSocket Endpoints

**File:** `app/client/src/hooks/useWebSocket.ts`
- Line 21: `"{protocol}//{host}:8000/ws/workflows"` - WebSocket URL (workflows)
- Line 55: `"{protocol}//{host}:8000/ws/routes"` - WebSocket URL (routes)
- Line 100: `"{protocol}//{host}:8000/ws/workflow-history"` - WebSocket URL (history)
- Line 171: `"{protocol}//{host}:8000/ws/adw-state/{id}"` - WebSocket URL (ADW state)

**Note:** Port 8000 is hard-coded in all WebSocket URLs

### REST Endpoints

**File:** `app/client/src/components/WorkflowDashboard.tsx`
- Line 9: `"/api/workflow-catalog"` - Workflow catalog endpoint

**File:** `app/client/src/components/PreflightCheckPanel.tsx`
- Line 38: `"/api/preflight-checks?skip_tests={bool}"` - Preflight checks endpoint

### External URLs

**File:** `app/client/src/components/PhaseQueueCard.tsx`
- Line 94: `"https://github.com/warmonger0/tac-webbuilder/issues/{number}"` - **GitHub issue URL (hard-coded repository)**
- Line 101: `"https://github.com/warmonger0/tac-webbuilder/pull/{number}"` - **GitHub PR URL (hard-coded repository)**

**CRITICAL:** GitHub repository owner and name are hard-coded

### Direct Service URLs

**File:** `app/client/src/api/systemClient.ts`
- Line 35: `"http://localhost:8001/webhook-status"` - **Webhook service direct URL (bypasses API gateway)**

**Note:** Port 8001 is hard-coded and assumes localhost

---

## 3. Configuration Values (25+ items)

### LocalStorage Keys

**File:** `app/client/src/App.tsx`
- Line 10: `"tac-webbuilder-active-tab"` - LocalStorage key for active tab persistence

### Tab Configuration

**File:** `app/client/src/App.tsx`
- Line 18: `['request', 'workflows', 'history', 'routes']` - Valid tab values
- Line 21: `"request"` - Default active tab

### WebSocket Configuration

**File:** `app/client/src/hooks/useReliableWebSocket.ts`
- Line 36: `3000` ms - Default polling interval
- Line 37: `30000` ms - Default max reconnect delay
- Line 38: `10` - Default max reconnect attempts
- Line 110: `5000` ms - Excellent quality threshold
- Line 115: `15000` ms - Good quality threshold
- Line 119: `30000` ms - Poor quality threshold
- Line 286: `5000` ms - Quality update interval

### Polling Configuration

**File:** `app/client/src/hooks/useReliablePolling.ts`
- Line 36: `60000` ms - Default polling interval (1 minute)
- Line 38: `30000` ms - Default min interval
- Line 39: `120000` ms - Default max interval (2 minutes)
- Line 40: `5` - Default max consecutive errors
- Line 80: `1.5` - Exponential backoff multiplier
- Line 93: `10000` ms - Excellent quality time threshold
- Line 97: `30000` ms - Good quality time threshold
- Line 101: `60000` ms - Poor quality time threshold
- Line 202: `2000` ms - Random stagger delay max

### Component-Specific Intervals

**File:** `app/client/src/components/PreflightCheckPanel.tsx`
- Line 44: `30000` ms - Auto-refresh interval

**File:** `app/client/src/components/SystemStatusPanel.tsx`
- Line 24: `30000` ms - Polling interval
- Line 78: `2000` ms - Status refresh delay after action
- Line 96: `2000` ms - Status refresh delay after action
- Line 133: `2000` ms - Status refresh delay after action

**File:** `app/client/src/components/ZteHopperQueueCard.tsx`
- Line 39: `10000` ms - Queue polling interval

**File:** `app/client/src/components/AdwMonitorCard.tsx`
- Line 33: `10000` ms - Active workflow polling interval
- Line 33: `30000` ms - Idle workflow polling interval
- Line 190: `5` - Max reconnect attempts for ADW state

### Data Limits

**File:** `app/client/src/components/WorkflowHistoryView.tsx`
- Line 112: `50` - Default workflow history limit

### UI Configuration

**File:** `app/client/src/components/CostEstimateCard.tsx`
- Line 40: `2.0` - High cost warning threshold (in dollars)

**File:** `app/client/src/components/request-form/FileUploadSection.tsx`
- Line 65: `3000` ms - Success message auto-hide delay
- Line 96: `3000` ms - Success message auto-hide delay
- Line 114: `".md,.markdown"` - Accepted file types

### Service Display Order

**File:** `app/client/src/components/SystemStatusPanel.tsx`
- Line 243: `['backend_api', 'database', 'webhook', 'frontend', 'cloudflare_tunnel', 'github_webhook']` - Service display order array

---

## 4. Default/Mock Data & Enums (20+ items)

### Status Color Mappings

**File:** `app/client/src/components/StatusBadge.tsx`
- Lines 9-22: Status to color mapping object:
  - `plan` → blue
  - `build` → yellow
  - `test` → purple
  - `review` → indigo
  - `document` → cyan
  - `ship` → green
  - `completed` / `success` → green
  - `error` / `failed` → red
  - `pending` → gray

### Phase Queue Status Configuration

**File:** `app/client/src/components/PhaseQueueCard.tsx`
- Lines 35-84: Complete `STATUS_COLORS` configuration object:
  ```typescript
  {
    queued: { bg, text, border, icon: "⏸️", label: "Queued" },
    ready: { bg, text, border, icon: "▶️", label: "Ready" },
    running: { bg, text, border, icon: "⚙️", label: "Running" },
    completed: { bg, text, border, icon: "✅", label: "Completed" },
    blocked: { bg, text, border, icon: "🚫", label: "Blocked" },
    failed: { bg, text, border, icon: "❌", label: "Failed" }
  }
  ```

### HTTP Method Colors

**File:** `app/client/src/components/RoutesView.tsx`
- Lines 18-24: HTTP method color mapping:
  - `GET` → blue
  - `POST` → green
  - `PUT` → yellow
  - `DELETE` → red
  - `PATCH` → purple

### Workflow Phase Definitions

**File:** `app/client/src/components/AdwMonitorCard.tsx`
- Lines 56-66: Workflow phases array (9 phases):
  ```typescript
  [
    { phase: 'plan', name: 'Plan', icon: '📋' },
    { phase: 'validate', name: 'Validate', icon: '✅' },
    { phase: 'build', name: 'Build', icon: '🔨' },
    { phase: 'lint', name: 'Lint', icon: '🧹' },
    { phase: 'test', name: 'Test', icon: '🧪' },
    { phase: 'review', name: 'Review', icon: '👀' },
    { phase: 'doc', name: 'Doc', icon: '📝' },
    { phase: 'ship', name: 'Ship', icon: '🚀' },
    { phase: 'cleanup', name: 'Cleanup', icon: '🧹' }
  ]
  ```

### ADW Status Colors

**File:** `app/client/src/components/AdwMonitorCard.tsx**
- Lines 196-239: Status color configurations:
  - `failed` state colors (red theme)
  - `running` state colors (blue theme)
  - `paused` state colors (yellow theme)
  - Default state colors (gray theme)

---

## 5. Visual/Icon Constants (15+ items)

### Connection Status Icons

**File:** `app/client/src/components/ConnectionStatusIndicator.tsx`
- Line 26: `"●"` - Live icon (filled circle)
- Line 34: `"●"` - Connected icon (filled circle)
- Line 42: `"●"` - Slow icon (filled circle)
- Line 50: `"○"` - Offline icon (empty circle)

### Phase Queue Icons

**File:** `app/client/src/components/PhaseQueueCard.tsx`
- Line 41: `"⏸️"` - Queued icon (pause)
- Line 49: `"▶️"` - Ready icon (play)
- Line 57: `"⚙️"` - Running icon (gear)
- Line 65: `"✅"` - Completed icon (checkmark)
- Line 73: `"🚫"` - Blocked icon (prohibited)
- Line 81: `"❌"` - Failed icon (X)
- Line 163: `"▼"` - Collapse icon (down arrow)
- Line 163: `"▶"` - Expand icon (right arrow)
- Line 206: `"⭕"` - Issue icon (hollow circle)
- Line 216: `"🔀"` - PR icon (merge)

### Preflight Check Icons

**File:** `app/client/src/components/PreflightCheckPanel.tsx`
- Line 50: `"✅"` - Pass icon
- Line 52: `"⚠️"` - Warning icon
- Line 54: `"❌"` - Fail icon
- Line 56: `"❓"` - Unknown icon

### Health Status Icons

**File:** `app/client/src/components/AdwMonitorCard.tsx`
- Line 379: `"🟢"` - Healthy icon (green circle)
- Line 379: `"🟡"` - Warning icon (yellow circle)
- Line 379: `"🔴"` - Error icon (red circle)

---

## 6. Error Messages & Notifications (10+ items)

### Generic Errors

**File:** `app/client/src/api/baseClient.ts`
- Line 33: `"API Error: {status} {error}"` - Generic API error format

### Component-Specific Errors

**File:** `app/client/src/components/WorkflowDashboard.tsx`
- Line 11: `"Failed to fetch workflow catalog"` - Error message

**File:** `app/client/src/components/PreflightCheckPanel.tsx`
- Line 40: `"Failed to fetch pre-flight checks"` - Error message

### System API Errors

**File:** `app/client/src/api/systemClient.ts`
- Line 68: `"Failed to start webhook service: {statusText}"` - Error message
- Line 85: `"Failed to restart Cloudflare: {statusText}"` - Error message
- Line 114: `"Failed to redeliver webhook: {statusText}"` - Error message

### Validation Errors

**File:** `app/client/src/components/request-form/FileUploadSection.tsx`
- Line 50: `"No valid files to process"` - Error message

---

## 7. ARIA Labels & Accessibility (8+ items)

**File:** `app/client/src/components/request-form/FileUploadSection.tsx`
- Line 119: `"Upload markdown files"` - ARIA label for file input

**File:** `app/client/src/components/ZteHopperQueueCard.tsx`
- Line 97: `"tablist"` - Role for tab container
- Line 99: `"tab"` - Role for tab button (in-progress)
- Line 101: `"in-progress-panel"` - ARIA controls reference
- Line 112: `"tab"` - Role for tab button (completed)
- Line 114: `"completed-panel"` - ARIA controls reference
- Line 153: `"tabpanel"` - Role for in-progress panel
- Line 171: `"tabpanel"` - Role for completed panel

**File:** `app/client/src/components/PhaseQueueCard.tsx`
- Line 133: `"article"` - Role for queue card container

---

## Priority Recommendations

### 🔴 CRITICAL (Immediate Action Required)

1. **GitHub Repository URL** (`PhaseQueueCard.tsx:94,101`)
   - Currently: `"https://github.com/warmonger0/tac-webbuilder"`
   - Action: Extract to environment variable `VITE_GITHUB_REPO_URL`
   - Impact: Breaks functionality if repository is renamed/moved

2. **Backend Port Number** (`useWebSocket.ts:21,55,100,171`)
   - Currently: Hard-coded `:8000` in all WebSocket URLs
   - Action: Extract to environment variable `VITE_BACKEND_PORT`
   - Impact: Breaks all real-time features if backend port changes

3. **Webhook Service Port** (`systemClient.ts:35`)
   - Currently: `"http://localhost:8001"`
   - Action: Extract to environment variable `VITE_WEBHOOK_SERVICE_URL`
   - Impact: Direct localhost reference breaks in production

4. **API Base URL** (`baseClient.ts:8`)
   - Currently: `"/api/v1"`
   - Action: Extract to environment variable `VITE_API_BASE_PATH`
   - Impact: API versioning changes require code changes

### 🟡 HIGH (Near-Term Extraction)

1. **Polling Intervals** (Multiple files)
   - Action: Create `src/config/intervals.ts` with all timing constants
   - Benefit: Single source of truth, easier performance tuning

2. **Status Color Mappings** (`StatusBadge.tsx`, `PhaseQueueCard.tsx`, `RoutesView.tsx`)
   - Action: Create `src/config/theme.ts` with all color schemes
   - Benefit: Consistent theming, easier dark mode implementation

3. **Workflow Phase Definitions** (`AdwMonitorCard.tsx:56-66`)
   - Action: Create `src/config/workflows.ts` with phase definitions
   - Benefit: Single source of truth for workflow configuration

4. **Service Display Order** (`SystemStatusPanel.tsx:243`)
   - Action: Extract to `src/config/services.ts`
   - Benefit: Configurable service priority/ordering

### 🟢 MEDIUM (Future Enhancement)

1. **UI Text Strings** (120+ items across all components)
   - Action: Create `src/locales/en-US.json` for all UI strings
   - Benefit: Enables future internationalization (i18n)
   - Framework: Consider `react-i18next` or similar

2. **Configuration Thresholds** (Quality thresholds, cost warnings, etc.)
   - Action: Create `src/config/thresholds.ts`
   - Benefit: Tunable application behavior without code changes

3. **File Upload Configuration** (`FileUploadSection.tsx:114`)
   - Action: Extract to `src/config/uploads.ts`
   - Benefit: Centralized file handling configuration

### ⚪ LOW (Optional)

1. **Icons and Emojis** (15+ items)
   - Current: Fine as-is for visual consistency
   - Future: Consider icon component library for scalability

2. **ARIA Labels** (8+ items)
   - Current: Should remain in components for accessibility
   - Note: Accessibility labels are often best kept co-located with components

---

## Suggested File Structure

```
app/client/src/
├── config/
│   ├── api.ts              # API URLs, endpoints, ports
│   ├── intervals.ts        # All polling/timeout values
│   ├── theme.ts            # Colors, status mappings
│   ├── workflows.ts        # Workflow definitions
│   ├── services.ts         # Service configurations
│   ├── thresholds.ts       # Quality/cost/performance thresholds
│   └── uploads.ts          # File upload configuration
├── locales/
│   ├── en-US.json          # English UI strings
│   └── i18n.ts             # i18n configuration
└── .env.example            # Environment variable template
```

### Example `.env.example`

```bash
# API Configuration
VITE_API_BASE_PATH=/api/v1
VITE_BACKEND_PORT=8000
VITE_WEBHOOK_SERVICE_URL=http://localhost:8001

# GitHub Integration
VITE_GITHUB_REPO_OWNER=warmonger0
VITE_GITHUB_REPO_NAME=tac-webbuilder

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_FILE_UPLOAD=true
```

---

## Next Steps

1. **Create configuration files** for critical values (API URLs, ports)
2. **Set up environment variables** for deployment-specific values
3. **Extract status/theme mappings** to centralized theme configuration
4. **Document migration plan** for moving UI strings to i18n structure
5. **Create type definitions** for all configuration objects
6. **Add runtime validation** for environment variables (using Zod or similar)

---

## Maintenance Notes

- **Last Updated:** 2025-11-28
- **Files Analyzed:** 15+ component files in `app/client/src/`
- **Total Hard-Coded Items:** 200+
- **Critical Items:** 4 (GitHub URLs, ports, API paths)
- **Recommended Actions:** 3 critical extractions, 4 high-priority refactors

This documentation should be updated whenever:
- New components are added with hard-coded values
- Configuration values change or move
- New API endpoints are added
- Theming or status definitions change
