# Feature #69: Integrate Webhooks with Observability System

## Current Status
- **92.5% Complete** - Internal webhook fully integrated
- **Remaining**: External webhook observability integration
- **Time**: 1.0-1.5h estimated (down from 4h since internal done)

## What's Done ✅
- Internal webhook (`queue_routes.py`) fully integrated with StructuredLogger
- TaskLogRepository logging workflow completion events
- Pattern analysis for internal webhook events

## What Remains ❌
- External webhook (`adws/adw_triggers/trigger_webhook.py`) has NO observability
- Uses in-memory stats that reset on restart
- No persistent logging of GitHub webhook events

## Key Decision Required

**Dependency Strategy** for external webhook server:

**Option A**: Accept heavy dependencies (pydantic, psycopg2, etc.)
- Pro: Consistent with internal webhook
- Con: Adds dependencies to lightweight webhook server

**Option B**: Create lightweight observability endpoint in backend
- Pro: Keeps webhook server lightweight
- Con: Adds network call overhead

**Option C**: Use webhook status endpoint + periodic persistence
- Pro: Minimal changes
- Con: May lose data between persistence intervals

---

## Phase Breakdown (2 Phases)

### Phase 1: Decide Strategy & Add Basic Logging (0.5-0.75h)
**Deliverable**: Decision documented, basic observability structure added

**Tasks**:
1. Review implementation guide (session19_phase1_part4_observability.md)
2. Decide on dependency strategy (A, B, or C)
3. Add imports and basic StructuredLogger initialization
4. Test that webhook server still starts without errors

**Files**:
- `adws/adw_triggers/trigger_webhook.py`
- `docs/features/webhook-observability.md` (decision doc)

---

### Phase 2: Implement Full Observability (0.5-0.75h)
**Deliverable**: External webhook fully integrated with observability system

**Tasks**:
1. Add `log_webhook_event()` calls at key points:
   - Webhook received
   - Processing start/end
   - Success/failure outcomes
2. Create TaskLog entries for pattern analysis
3. Test webhook processing with observability
4. Verify logs appear in database
5. Mark #69 as completed

**Files**:
- `adws/adw_triggers/trigger_webhook.py`
- Tests to verify logging

---

## Implementation Reference

**Guide**: `docs/Archive/sessions/session-19/prompts/session19_phase1_part4_observability.md`
- Lines 104-119: Exact code for `trigger_webhook.py`
- Lines 130-233: Full integration pattern

**Example** (from internal webhook):
```python
# queue_routes.py:630-647
structured_logger = StructuredLogger()
task_log_repo = TaskLogRepository()

structured_logger.log_webhook_event(
    adw_id=request.adw_id,
    issue_number=request.parent_issue,
    message=f"Workflow complete webhook received (status={request.status})",
    webhook_type="workflow_complete",
    event_data={...}
)
```

---

## Total Time: 1.0-1.5h (2 phases)
- Phase 1: 0.5-0.75h (decision + basic structure)
- Phase 2: 0.5-0.75h (full implementation)
