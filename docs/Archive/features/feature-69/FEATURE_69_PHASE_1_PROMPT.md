# Feature #69 Phase 1: Webhook Observability Strategy & Setup

## Context
Load: `/prime`

**Depends on**: Investigation complete (92.5% done - external webhook remaining)

## Task
Decide on dependency strategy for external webhook observability and add basic logging structure.

**Scope**: Decision + basic setup only. Full implementation in Phase 2.

## Background

### Current State
- ✅ **Internal webhook** (`queue_routes.py`): Fully integrated with StructuredLogger
- ❌ **External webhook** (`trigger_webhook.py`): NO observability, uses in-memory stats

### The Problem
Line 76 of `trigger_webhook.py` states:
> "Observability logging moved to backend to avoid heavy dependencies"

The webhook server was designed to be lightweight, but we need observability.

### Implementation Guide Available
- **File**: `docs/Archive/sessions/session-19/prompts/session19_phase1_part4_observability.md`
- Lines 104-119: Exact code to add
- Lines 130-233: Full integration pattern

## Workflow

### 1. Investigate (15 min)

```bash
# Read current webhook implementation
cd /Users/Warmonger0/tac/tac-webbuilder
cat adws/adw_triggers/trigger_webhook.py | head -100
grep -n "webhook_stats\|StructuredLogger\|TaskLog" adws/adw_triggers/trigger_webhook.py

# Check dependencies
cat adws/requirements.txt 2>/dev/null || echo "No requirements.txt"
grep "pydantic\|psycopg2\|sqlalchemy" adws/adw_triggers/trigger_webhook.py

# Read implementation guide
cat docs/Archive/sessions/session-19/prompts/session19_phase1_part4_observability.md | grep -A50 "trigger_webhook.py"

# Compare with working internal webhook
grep -A20 "StructuredLogger\|log_webhook_event" app/server/routes/queue_routes.py | head -40
```

### 2. Make Decision (10 min)

**Evaluate 3 options:**

**Option A: Accept Dependencies**
- Add pydantic, psycopg2, etc. to webhook server
- Consistent with internal webhook pattern
- Simple implementation (copy from queue_routes.py)
- **Downside**: Heavier webhook server

**Option B: Remote Logging Endpoint**
- Webhook POSTs to backend `/api/v1/observability/log-webhook-event`
- Backend handles database writes
- Webhook stays lightweight
- **Downside**: Network call overhead, more complex

**Option C: Hybrid - Periodic Persistence**
- Keep in-memory stats (lines 80-87)
- Add periodic POST to backend to persist stats
- Minimal changes needed
- **Downside**: May lose data between flushes

**Make the decision** and document in `docs/features/webhook-observability-decision.md`

### 3. Implement Basic Structure (15 min)

**If Option A (Recommended):**

```bash
# Add imports to trigger_webhook.py (around line 42)
```

Edit `adws/adw_triggers/trigger_webhook.py`:
```python
# Add after existing imports
from services.structured_logger import StructuredLogger
from repositories.task_log_repository import TaskLogRepository
from core.models.observability import TaskLogCreate
```

Initialize in webhook handler (around line 200):
```python
# Initialize observability
structured_logger = StructuredLogger()
task_log_repo = TaskLogRepository()
```

**If Option B:**
- Document API endpoint spec
- Defer implementation to Phase 2

**If Option C:**
- Add periodic flush function
- Document persistence interval

### 4. Test (10 min)

```bash
# Test webhook server still starts
cd adws/adw_triggers
python3 trigger_webhook.py &
WEBHOOK_PID=$!

# Check it's running
sleep 2
curl http://localhost:8001/webhook/status

# Kill test server
kill $WEBHOOK_PID

# If using Option A, verify imports work
python3 -c "
from services.structured_logger import StructuredLogger
print('✅ StructuredLogger imports successfully')
"
```

### 5. Quality (10 min)

```bash
# Linting
ruff check adws/adw_triggers/trigger_webhook.py --fix

# Type check
mypy adws/adw_triggers/trigger_webhook.py --ignore-missing-imports

# Commit decision + basic structure
git add adws/adw_triggers/trigger_webhook.py docs/features/webhook-observability-decision.md
git commit -m "feat: Add webhook observability strategy and basic structure (Phase 1/2)

Decision: [Option A/B/C] for external webhook observability

Problem:
- External webhook has no persistent observability logging
- In-memory stats lost on restart
- No pattern analysis for GitHub webhook events

Solution (Phase 1):
- Decided on [strategy]
- Added basic structure [if Option A: imports and initialization]
- [If Option A: Ready for full implementation]
- [If Option B/C: Defined integration approach]

Next: Phase 2 will implement full observability integration

Location: adws/adw_triggers/trigger_webhook.py"

# Update Plans Panel (partial progress)
curl -X PATCH http://localhost:8002/api/v1/planned-features/69 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "#69: Integrate webhooks with observability system",
    "status": "in_progress"
  }'
```

## Success Criteria
- ✅ Decision documented with rationale
- ✅ Basic structure added (if Option A)
- ✅ Webhook server still starts without errors
- ✅ 0 linting errors
- ✅ Clear path forward for Phase 2

## Time: 0.5-0.75h (50-45 min)

## Next Phase
Phase 2: Implement full observability integration based on chosen strategy
