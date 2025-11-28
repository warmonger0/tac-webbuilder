# How to Populate and Visualize ADW Workflows

This guide explains how to trigger ADW workflows from GitHub issues and watch them execute with animated phase progression in the frontend.

## Two Ways to Trigger Workflows

### Method 1: GitHub Webhook (Automatic)

**Setup the webhook listener:**
```bash
cd adws/
uv run adw_triggers/trigger_webhook.py
# Server starts on http://localhost:8001
```

**Create a GitHub issue with workflow command:**
1. Go to your GitHub repository
2. Create a new issue with an ADW workflow command in the body:
   ```
   Add a new feature to handle user authentication

   adw_sdlc_complete_iso
   ```

3. The webhook will automatically:
   - Detect the workflow command
   - Generate an ADW ID
   - Launch the workflow in the background
   - Post updates to the GitHub issue

**Supported workflow commands in issues/comments:**
- `adw_plan_iso` - Planning only
- `adw_lightweight_iso` - Quick fixes ($0.20-0.50)
- `adw_patch_iso` - Specific changes
- `adw_sdlc_complete_iso` - Full 9-phase SDLC
- `adw_sdlc_complete_zte_iso` - Full SDLC + auto-merge
- `adw_stepwise_iso` - Complexity-based routing

**How it works:**
- Webhook listens on port 8001
- Detects issue creation/comments with `adw_*_iso` patterns
- Runs pre-flight checks (git state, disk space, API quota)
- Acquires concurrency lock to prevent conflicts
- Launches workflow in background
- Creates `adw_state.json` in `agents/{adw_id}/`

### Method 2: Manual CLI (Direct)

**Run a workflow directly:**
```bash
cd adws/

# Full 9-phase SDLC workflow
uv run adw_sdlc_complete_iso.py <issue-number>

# Example: Process issue #123
uv run adw_sdlc_complete_iso.py 123

# Stepwise (complexity-based routing)
uv run adw_stepwise_iso.py 123

# Planning only
uv run adw_plan_iso.py 123

# Lightweight (simple changes)
uv run adw_lightweight_iso.py 123
```

**What happens:**
1. Creates isolated worktree in `trees/adw-{id}/`
2. Generates ADW ID (e.g., `adw-12345678`)
3. Creates state file: `agents/{adw_id}/adw_state.json`
4. Executes workflow phases sequentially
5. Updates state file after each phase
6. Creates workflow history in database

## Workflow Visualization (Frontend)

### Start the Full Stack

**Terminal 1 - Backend:**
```bash
cd app/server
uv run python server.py
# Runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd app/client
bun run dev
# Runs on http://localhost:5173
```

**Terminal 3 - Webhook (Optional):**
```bash
cd adws/
uv run adw_triggers/trigger_webhook.py
# Runs on http://localhost:8001
```

### View Workflow Animation

1. **Open browser:** http://localhost:5173
2. **Navigate to:** Workflow Dashboard or Current Workflow card
3. **Watch the animation:**
   - Each phase appears as a circular icon
   - **Green pulsing** = Currently active phase
   - **Green solid** = Completed phase
   - **Purple pulsing** = Stuck (>10 minutes)
   - **Red pulsing** = Error/Hung (>20 minutes)
   - **Gray** = Pending phase
   - Connecting lines animate between phases

### Workflow Phases Visualized

The frontend shows 10 sequential phases:

```
Ingestion → Preflight → Plan → Validate → Build → Lint → Test → Review → Doc → Ship
```

**Phase progression:**
- **Ingestion**: Issue data extracted
- **Preflight**: Pre-flight checks
- **Plan**: Implementation plan created
- **Validate**: Baseline errors detected (new in Complete workflows)
- **Build**: Code implementation
- **Lint**: TypeScript/ESLint validation
- **Test**: Unit/integration tests
- **Review**: Code review & analysis
- **Doc**: Documentation generation
- **Ship**: PR creation/merge

### Real-Time Updates

The frontend polls the backend every 2-5 seconds to:
- Fetch latest workflow state from `adw_state.json`
- Update current phase indicator
- Show elapsed time
- Display error messages
- Update progress animations

## How Workflow Data Flows

### 1. Workflow Execution Creates State
```bash
# When you run: uv run adw_sdlc_complete_iso.py 123
# Creates: agents/adw-12345678/adw_state.json
```

**State file structure:**
```json
{
  "adw_id": "adw-12345678",
  "issue_number": "123",
  "status": "running",
  "current_phase": "build",
  "workflow_template": "adw_sdlc_complete_iso",
  "start_time": "2025-11-28T10:30:00",
  "github_url": "https://github.com/user/repo/issues/123",
  "model_used": "sonnet",
  "phases": {
    "plan": {"status": "completed", "start_time": "...", "end_time": "..."},
    "validate": {"status": "completed", "start_time": "...", "end_time": "..."},
    "build": {"status": "running", "start_time": "..."}
  }
}
```

### 2. Backend Service Reads State
```python
# app/server/services/workflow_service.py
# Scans agents/ directory for adw_state.json files
# Returns list of active workflows to frontend
```

### 3. Frontend Displays Animation
```typescript
// app/client/src/components/WorkflowProgressVisualization.tsx
// Receives workflow data via WebSocket or polling
// Renders animated phase progression
```

### 4. Workflow History Database
```python
# After workflow completes, synced to database
# app/server/core/workflow_history.py
# SQLite table with full workflow metadata
```

## Testing the Complete Flow

### Quick Test (5 minutes)

1. **Create a test issue:**
   ```bash
   gh issue create --title "Test workflow animation" --body "Add a simple console.log statement to server.py

   adw_lightweight_iso"
   ```

2. **Start the stack:**
   ```bash
   # Terminal 1
   cd app/server && uv run python server.py

   # Terminal 2
   cd app/client && bun run dev

   # Terminal 3
   cd adws && uv run adw_triggers/trigger_webhook.py
   ```

3. **Watch in browser:**
   - Open http://localhost:5173
   - Navigate to "Current Workflow" card
   - See animated phase progression in real-time

4. **Monitor progress:**
   ```bash
   # Watch state file updates
   watch -n 1 "cat agents/adw-*/adw_state.json | jq '.current_phase, .status'"

   # Tail workflow logs
   tail -f agents/adw-*/*/execution.log
   ```

### Expected Behavior

**Lightweight workflow (~2-5 minutes):**
```
Ingestion   ✓ (5s)
Preflight   ✓ (10s)
Plan        ✓ (30s)
Validate    ✓ (15s)
Build       ⟳ (60s) ← Currently active, pulsing green
Lint        ○ (pending)
Test        ○ (pending)
Review      ○ (pending)
Doc         ○ (pending)
Ship        ○ (pending)
```

**Complete SDLC workflow (~10-20 minutes):**
- All 10 phases execute sequentially
- Each phase updates state file
- Frontend shows real-time progression
- Final phase creates PR

## Troubleshooting

### Workflow not showing in UI?

**Check backend is reading state:**
```bash
curl http://localhost:8000/api/workflows
# Should return array of active workflows
```

**Check state file exists:**
```bash
ls -la agents/adw-*/adw_state.json
# Should show recent state files
```

**Check workflow service:**
```bash
# In app/server/services/workflow_service.py
# Ensure get_workflows() is scanning agents/ directory
```

### Animation not updating?

**Check WebSocket connection:**
```bash
# Browser DevTools → Network → WS
# Should see active WebSocket connection
```

**Check polling interval:**
```typescript
// app/client/src/hooks/useWorkflows.ts
// Should poll every 2-5 seconds
```

**Force refresh:**
```bash
# Clear browser cache and reload
# Or restart frontend dev server
```

### Webhook not triggering?

**Check webhook is running:**
```bash
curl http://localhost:8001/ping
# Should return: {"status": "healthy"}
```

**Check GitHub webhook configuration:**
1. Go to GitHub repo → Settings → Webhooks
2. Ensure webhook URL is set to your server
3. Check recent deliveries for errors

**Check logs:**
```bash
tail -f agents/webhook_error/webhook_trigger/execution.log
```

## Advanced: Custom Workflow Visualization

To customize the animation in `WorkflowProgressVisualization.tsx`:

```typescript
// Change phase colors
const PHASE_COLORS = {
  completed: 'bg-green-500',
  active: 'bg-blue-500',
  stuck: 'bg-yellow-500',
  error: 'bg-red-500'
};

// Adjust time thresholds
const STUCK_THRESHOLD = 15 * 60 * 1000;  // 15 minutes
const HUNG_THRESHOLD = 30 * 60 * 1000;   // 30 minutes

// Add custom phases
const WORKFLOW_STEPS = [
  { id: 'custom1', label: 'My Phase', phase: 'custom1' },
  // ... existing phases
];
```

## Summary

**To populate workflows:**
1. Create GitHub issues with `adw_*_iso` commands (automatic via webhook)
2. OR run CLI: `uv run adw_sdlc_complete_iso.py <issue-number>` (manual)

**To view animation:**
1. Start backend: `cd app/server && uv run python server.py`
2. Start frontend: `cd app/client && bun run dev`
3. Open browser: http://localhost:5173
4. Watch real-time phase progression with animated icons

**Workflow data flow:**
```
GitHub Issue → Webhook/CLI → ADW Workflow → State File → Backend API → Frontend Animation
                                              ↓
                                      Workflow History DB
```
