# Webhook Observability Strategy Decision

**Date**: 2025-12-13
**Feature**: #69 - Integrate webhooks with observability system
**Phase**: 1 - Strategy & Setup
**Decision**: Option B - Remote Logging Endpoint

## Context

The tac-webbuilder project has two webhook implementations:
1. **Internal webhook** (`app/server/routes/queue_routes.py`) - Already fully integrated with StructuredLogger ✅
2. **External webhook** (`adws/adw_triggers/trigger_webhook.py`) - Uses in-memory stats only ❌

The external webhook was intentionally designed to be lightweight (line 76: "Observability logging moved to backend to avoid heavy dependencies").

## Problem

The external webhook needs persistent observability logging for:
- Pattern analysis (frequency, types, timing)
- Cost attribution (track workflow triggers)
- Failure monitoring (error analytics)
- Complete audit trail (regulatory/debugging)

Currently, all stats are stored in memory and lost on restart.

## Options Evaluated

### Option A: Accept Dependencies ❌

**Approach**: Add pydantic, psycopg2, sqlalchemy, rich, etc. to webhook server dependencies

**Pros**:
- Consistent with internal webhook pattern
- Direct database access
- No network overhead

**Cons**:
- Requires 20+ additional packages (tested: StructuredLogger import pulls in rich, sqlalchemy, fastapi dependencies)
- Defeats lightweight design goal
- Increases webhook server startup time and memory footprint
- Goes against explicit design decision (line 76)

**Verdict**: ❌ **Rejected** - Violates design principles

### Option B: Remote Logging Endpoint ✅

**Approach**: Webhook POSTs events to backend API endpoint `/api/v1/observability/log-webhook-event`

**Pros**:
- ✅ Keeps webhook server lightweight
- ✅ Leverages existing backend infrastructure
- ✅ Backend already has StructuredLogger integrated
- ✅ Minimal overhead (async HTTP POST, non-blocking)
- ✅ Webhook already has HTTP client (uses it for GitHub API)
- ✅ No additional dependencies needed
- ✅ Aligns with original design philosophy

**Cons**:
- Minor network call overhead (~5-10ms per event)
- Requires new backend endpoint (simple to implement)

**Verdict**: ✅ **SELECTED** - Best balance of lightweight + persistent observability

### Option C: Hybrid Periodic Persistence ⚠️

**Approach**: Keep in-memory stats, periodically POST summary to backend

**Pros**:
- Minimal changes to webhook server
- Very low overhead

**Cons**:
- Risk of data loss between flushes
- Incomplete audit trail (only summaries, not individual events)
- More complex state management

**Verdict**: ⚠️ **Acceptable fallback** - But not ideal for audit trail requirements

## Selected Approach: Option B

### Architecture

```
┌─────────────────────────────────┐
│  External Webhook               │
│  (adws/adw_triggers/            │
│   trigger_webhook.py)           │
│                                 │
│  1. Receive GitHub webhook      │
│  2. Log to file (existing)      │
│  3. POST to observability API ──┼─┐
│  4. Process workflow            │ │
└─────────────────────────────────┘ │
                                    │ HTTP POST
                                    │ /api/v1/observability/log-webhook-event
                                    │
┌─────────────────────────────────┐ │
│  Backend API                    │◄┘
│  (app/server/routes/            │
│   observability_routes.py)      │
│                                 │
│  1. Receive log request         │
│  2. Validate payload            │
│  3. Use StructuredLogger ───────┼──┐
│  4. Return 200 OK               │  │
└─────────────────────────────────┘  │
                                     │
┌─────────────────────────────────┐  │
│  StructuredLogger               │◄─┘
│  (services/structured_logger.py)│
│                                 │
│  - Write to task_logs table     │
│  - Write to structured.jsonl    │
│  - Enable pattern analysis      │
└─────────────────────────────────┘
```

### Implementation Plan

**Phase 1 (This Phase)**: Basic Structure
- [x] Decision documented
- [ ] Add logging helper function to webhook server
- [ ] Define API contract for observability endpoint
- [ ] Document integration points

**Phase 2 (Next)**: Full Implementation
- [ ] Create backend endpoint `/api/v1/observability/log-webhook-event`
- [ ] Integrate logging calls in webhook processing
- [ ] Add error handling for observability failures (non-blocking)
- [ ] Test end-to-end
- [ ] Verify analytics queries

## API Contract

### Endpoint
```
POST /api/v1/observability/log-webhook-event
```

### Request Body
```json
{
  "adw_id": "adw-12345678",           // Optional - null for initial webhook
  "issue_number": 123,
  "message": "Webhook received from New issue",
  "webhook_type": "github_issue",     // or "workflow_complete"
  "phase_status": "received",         // or "processed", "failed"
  "duration_seconds": 0.045,          // Optional
  "event_data": {                     // Optional metadata
    "event_type": "issues",
    "workflow": "adw_plan_iso",
    "trigger_source": "New issue",
    "error": "..."                    // Only if failed
  }
}
```

### Response
```json
{
  "success": true,
  "message": "Webhook event logged",
  "task_log_id": 12345
}
```

### Error Handling
- Webhook server should NOT fail if observability logging fails
- Use try/except around logging calls
- Log to stderr if observability API unavailable
- Continue processing workflow regardless

## Rationale

1. **Lightweight Priority**: Original design explicitly avoided heavy dependencies
2. **Existing Infrastructure**: Backend already has StructuredLogger fully integrated
3. **Minimal Overhead**: ~5-10ms async POST is acceptable for observability
4. **Separation of Concerns**: Webhook focuses on triggering, backend handles persistence
5. **No Data Loss**: Every event logged immediately (unlike Option C)
6. **Audit Compliance**: Complete trail of individual events (unlike Option C summaries)

## Performance Impact

- **Network overhead**: ~5-10ms per webhook event (async, non-blocking)
- **Webhook processing**: No change (POST happens in background)
- **Backend load**: Negligible (simple database insert, existing code)
- **Total impact**: <1% increase in webhook response time

## Success Criteria

- ✅ Decision documented with rationale
- ✅ API contract defined
- ✅ Implementation plan outlined
- [ ] Basic logging structure added (Phase 1)
- [ ] Full implementation complete (Phase 2)
- [ ] Pattern analysis working with webhook data (Phase 2)

## Next Steps

1. Add logging helper function to `trigger_webhook.py`
2. Create backend endpoint stub (Phase 2)
3. Implement full integration (Phase 2)

---

**Status**: ✅ Decision Complete
**Next Phase**: Implementation (Phase 2)
