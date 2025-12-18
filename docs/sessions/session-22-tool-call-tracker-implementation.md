# Session 22: ToolCallTracker Implementation

**Date:** 2025-12-18
**Duration:** ~2 hours
**Status:** ✅ Complete - Ready for pilot testing

## Summary

Implemented ToolCallTracker helper class for ADW workflow tool usage tracking. Created comprehensive test suite (20 tests, 100% passing) and integrated tracking into BuildChecker module. System is now ready for pilot workflow execution to validate data flows to PostgreSQL.

## Key Accomplishments

### 1. ToolCallTracker Helper Class ✅

**File:** `adws/adw_modules/tool_call_tracker.py` (265 lines)

**Features:**
- Context manager for automatic tool usage tracking
- Captures: tool_name, timestamps, duration, success/failure, errors, parameters, results
- Zero-overhead guarantee - logging failures don't block workflows
- Two tracking methods:
  - `track(tool_name, callable_fn)` - Generic tool tracking
  - `track_bash(tool_name, command, cwd)` - Convenience method for subprocess commands
- Auto-logs to observability system on context exit
- Phase number inference from phase name (Plan=1, Build=3, Test=5, etc.)

**API Example:**
```python
with ToolCallTracker(adw_id="adw-123", issue_number=42, phase_name="Build") as tracker:
    tracker.track_bash("npm_install", ["npm", "install"], cwd="/path/to/repo")
    tracker.track_bash("npm_build", ["npm", "run", "build"], cwd="/path/to/repo")
# Auto-calls log_task_completion() with tool_calls=[...] on exit
```

### 2. Comprehensive Unit Tests ✅

**File:** `adws/tests/test_tool_call_tracker.py` (447 lines, 20 tests)

**Test Coverage:**
- ✅ Tracker initialization and phase number inference
- ✅ Successful tool call tracking with metadata capture
- ✅ Failed tool call error message capture
- ✅ Multiple tool tracking in sequence
- ✅ Subprocess result capture (returncode, stderr)
- ✅ track_bash() convenience method (list and string commands)
- ✅ Summary generation (total calls, success/failure counts, duration)
- ✅ Context manager success case (logs to observability)
- ✅ Context manager exception handling (logs failure)
- ✅ Context manager logging failure non-blocking (zero-overhead)
- ✅ Tool failures vs phase failures (failed tools ≠ failed phase)
- ✅ Error message truncation (500 chars)
- ✅ Result summary truncation (200 chars)
- ✅ Duration calculation accuracy

**Test Results:**
```
============================= test session starts ==============================
collected 20 items

tests/test_tool_call_tracker.py::TestToolCallTrackerBasics::test_tracker_initialization PASSED [  5%]
tests/test_tool_call_tracker.py::TestToolCallTrackerBasics::test_phase_number_inference PASSED [ 10%]
tests/test_tool_call_tracker.py::TestToolCallTrackerBasics::test_unknown_phase_defaults_to_zero PASSED [ 15%]
tests/test_tool_call_tracker.py::TestToolTracking::test_track_successful_tool_call PASSED [ 20%]
tests/test_tool_call_tracker.py::TestToolTracking::test_track_failed_tool_call PASSED [ 25%]
tests/test_tool_call_tracker.py::TestToolTracking::test_track_multiple_tools PASSED [ 30%]
tests/test_tool_call_tracker.py::TestToolTracking::test_track_with_result_capture PASSED [ 35%]
tests/test_tool_call_tracker.py::TestToolTracking::test_track_subprocess_failure PASSED [ 40%]
tests/test_tool_call_tracker.py::TestBashTracking::test_track_bash_with_list_command PASSED [ 45%]
tests/test_tool_call_tracker.py::TestBashTracking::test_track_bash_with_string_command PASSED [ 50%]
tests/test_tool_call_tracker.py::TestSummaryGeneration::test_get_summary_empty PASSED [ 55%]
tests/test_tool_call_tracker.py::TestSummaryGeneration::test_get_summary_with_calls PASSED [ 60%]
tests/test_tool_call_tracker.py::TestContextManager::test_context_manager_success PASSED [ 65%]
tests/test_tool_call_tracker.py::TestContextManager::test_context_manager_with_exception PASSED [ 70%]
tests/test_tool_call_tracker.py::TestContextManager::test_context_manager_logging_failure_non_blocking PASSED [ 75%]
tests/test_tool_call_tracker.py::TestContextManager::test_context_manager_with_failed_tools PASSED [ 80%]
tests/test_tool_call_tracker.py::TestEdgeCases::test_tool_with_empty_parameters PASSED [ 85%]
tests/test_tool_call_tracker.py::TestEdgeCases::test_error_message_truncation PASSED [ 90%]
tests/test_tool_call_tracker.py::TestEdgeCases::test_result_summary_truncation PASSED [ 95%]
tests/test_tool_call_tracker.py::TestEdgeCases::test_duration_calculation PASSED [100%]

============================== 20 passed in 0.04s ==============================
```

### 3. BuildChecker Integration ✅

**File:** `adws/adw_modules/build_checker.py` (modified)

**Changes:**
- Added `from adw_modules.tool_call_tracker import ToolCallTracker` import
- Updated `__init__(project_root, tracker=None)` - Optional tracker parameter (backward compatible)
- Integrated tracking in 3 build methods:
  1. **check_frontend_types()** - Tracks `tsc_typecheck` (TypeScript compiler)
  2. **check_frontend_build()** - Tracks `bun_build` (Vite build)
  3. **check_backend_types()** - Tracks `mypy_typecheck` (Python type checker)

**Integration Pattern:**
```python
# Track tool call if tracker available
if self.tracker:
    result = self.tracker.track_bash(
        tool_name="tsc_typecheck",
        command=cmd,
        cwd=str(frontend_path)
    )
else:
    result = subprocess.run(cmd, cwd=frontend_path, capture_output=True, text=True)
```

**Backward Compatibility:**
- ✅ All existing code works unchanged (tracker is optional)
- ✅ No breaking changes to BuildChecker API
- ✅ Tracking is opt-in via passing tracker instance

### 4. Example Implementation ✅

**File:** `adws/examples/build_with_tracking_example.py` (77 lines)

Demonstrates complete usage pattern:
1. Create ToolCallTracker context manager
2. Pass tracker to BuildChecker
3. Run build checks (automatically tracked)
4. Get summary of tracked tools
5. Auto-log on context exit

**Usage:**
```bash
cd adws
python examples/build_with_tracking_example.py 123 adw-test-abc
```

## Architecture Integration

### Two-Layer Tracking System

**Layer 1: hook_events table** (existing, already working)
- Captures: Claude Code native tool usage (Read, Edit, Bash, Grep, etc.)
- Source: Claude Code CLI hooks
- Volume: 29,268 events captured so far
- Purpose: Track LLM tool usage patterns

**Layer 2: task_logs.tool_calls** (NEW, implemented this session)
- Captures: ADW workflow-specific tools (git, npm, pytest, tsc, mypy, etc.)
- Source: ToolCallTracker in ADW phases
- Volume: 0 events (needs pilot workflows)
- Purpose: Track build/test/deploy tool usage patterns

**Unified Analysis:**
Both layers feed into `scripts/analyze_daily_patterns.py` for pattern detection and automation pipeline.

### Data Flow

```
ADW Phase (Build/Test/etc)
    ↓
ToolCallTracker context manager
    ↓
Tracks tools: tsc, npm, pytest, mypy
    ↓
Observability.log_task_completion(tool_calls=[...])
    ↓
POST /api/v1/task-logs (backend API)
    ↓
TaskLogRepository.create()
    ↓
PostgreSQL: task_logs.tool_calls JSONB column
    ↓
Pattern Detection: scripts/analyze_daily_patterns.py
    ↓
Pattern Automation: Script generation pipeline (future)
```

## Database Schema

**Table:** `task_logs`
**Column:** `tool_calls JSONB DEFAULT '[]'::jsonb`
**Index:** `idx_task_logs_tool_calls` (GIN index for efficient JSONB queries)

**Tool Call Record Structure:**
```json
{
  "tool_name": "tsc_typecheck",
  "started_at": "2025-12-18T13:45:23.123456",
  "completed_at": "2025-12-18T13:45:25.456789",
  "duration_ms": 2333,
  "success": true,
  "error_message": null,
  "parameters": {
    "command": "npx tsc --noEmit",
    "cwd": "/path/to/worktree/app/client"
  },
  "result_summary": "returncode=0"
}
```

## Next Steps

### Immediate (Week 1)

**1. Run Pilot Workflow (4 hours)**
- Execute 5-10 real ADW workflows with tool tracking enabled
- Validate tool_calls data appears in PostgreSQL
- Check data quality (timestamps, durations, error messages)
- Verify observability logging doesn't block workflows

**Validation Queries:**
```sql
-- Check tool_calls are being logged
SELECT adw_id, issue_number, phase_name, tool_calls::text
FROM task_logs
WHERE tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) > 0
ORDER BY completed_at DESC
LIMIT 10;

-- Count tool usage by type
SELECT
    t.tool->>'tool_name' AS tool_name,
    COUNT(*) AS usage_count,
    AVG((t.tool->>'duration_ms')::int) AS avg_duration_ms
FROM task_logs,
     jsonb_array_elements(tool_calls) AS t(tool)
WHERE tool_calls IS NOT NULL
GROUP BY t.tool->>'tool_name'
ORDER BY usage_count DESC;

-- Find failed tools
SELECT
    adw_id,
    issue_number,
    phase_name,
    t.tool->>'tool_name' AS tool_name,
    t.tool->>'error_message' AS error_message
FROM task_logs,
     jsonb_array_elements(tool_calls) AS t(tool)
WHERE (t.tool->>'success')::boolean = false;
```

**2. Expand to Additional Phases (6 hours)**
- Integrate ToolCallTracker in **Test phase** (adws/adw_test_iso.py)
  - Track: pytest, vitest, coverage, linting
- Integrate ToolCallTracker in **Plan phase** (adws/adw_plan_iso.py)
  - Track: git clone, git checkout, file reads
- Integrate ToolCallTracker in **Ship phase** (adws/adw_ship_iso.py)
  - Track: git push, PR creation, merge operations

**3. Create Analytics Dashboard (8 hours)**
- Panel 7 extension: Tool usage heatmaps
- Most expensive tools by time and cost
- Tool failure rate trends
- Build vs Test tool usage comparison

### Phase 2 (Weeks 2-4)

**4. Pattern Detection Enhancement (2 weeks)**
- Implement semantic pattern detector
  - Groups similar tool sequences: `[Read, Edit, Test]` ≈ `[Edit, Read, Test]`
  - Extracts intent: "test-driven fix", "type-error resolution", "dependency update"
- Build pattern confidence scoring
  - Factors: frequency, success rate, consistency, cost savings
- Auto-approval thresholds: >99% confidence + 200+ occurrences + $5K+ savings

**5. Script Generation Pipeline (2 weeks)**
- Template system for converting patterns → Python scripts
- Safety validation framework
  - Rejects destructive operations (delete, drop, truncate)
  - Dry-run mode for human review
  - Rollback capability
- Auto-registration system for validated scripts

### Future (Weeks 5-10)

**6. Deploy 5 Automated Patterns (2 weeks)**
- Target patterns identified from existing 11 patterns:
  1. Import fix pattern (180 occurrences, $1.8K savings)
  2. Type annotation pattern (145 occurrences, $1.5K savings)
  3. Lint auto-fix pattern (estimated 200+ occurrences)
  4. Test retry pattern (estimated 150+ occurrences)
  5. Database migration generator (95 occurrences, $1.1K savings)

**7. ROI Measurement (1 week)**
- Measure token reduction from automated patterns
- Track cost savings (before/after automation)
- Calculate time savings per workflow
- Update pattern_approvals table with actual ROI data

## Files Modified

### Created
- ✅ `adws/adw_modules/tool_call_tracker.py` (265 lines)
- ✅ `adws/tests/test_tool_call_tracker.py` (447 lines, 20 tests)
- ✅ `adws/examples/build_with_tracking_example.py` (77 lines)
- ✅ `docs/sessions/session-22-tool-call-tracker-implementation.md` (this file)

### Modified
- ✅ `adws/adw_modules/build_checker.py` (+8 lines)
  - Added ToolCallTracker import
  - Added optional tracker parameter to __init__
  - Integrated tracking in 3 build methods

### Database
- ✅ Migration already applied (Session 21): `task_logs.tool_calls JSONB` column exists
- ✅ GIN index exists: `idx_task_logs_tool_calls`
- ✅ Models updated (Session 21): `ToolCallRecord`, `TaskLog`, `TaskLogCreate`
- ✅ Repository updated (Session 21): JSON serialization/deserialization

## Technical Decisions

### Why Optional Tracker Parameter?
**Decision:** Made tracker optional in BuildChecker.__init__()
**Rationale:**
- ✅ Backward compatibility - all existing code works unchanged
- ✅ Gradual rollout - enable tracking phase by phase
- ✅ Testing flexibility - can test with/without tracking
- ✅ Zero risk - won't break production workflows

### Why Context Manager Pattern?
**Decision:** ToolCallTracker is a context manager with auto-logging on exit
**Rationale:**
- ✅ Guaranteed cleanup - tool_calls always logged (even on exception)
- ✅ Clean API - no manual log_task_completion() calls
- ✅ Error handling - context manager captures phase-level exceptions
- ✅ Pythonic - follows standard Python patterns

### Why track_bash() Convenience Method?
**Decision:** Added track_bash() alongside generic track()
**Rationale:**
- ✅ 90% of ADW tools are subprocess commands (npm, git, pytest)
- ✅ Reduces boilerplate - no lambda wrappers needed
- ✅ Consistent parameter logging - auto-captures command and cwd
- ✅ Type safety - CompletedProcess result handling built-in

## Testing Strategy

### Unit Tests (20 tests, 100% passing)
- ✅ Core functionality (initialization, phase inference, tracking)
- ✅ Error handling (failed tools, exceptions, truncation)
- ✅ Context manager behavior (success, failure, non-blocking)
- ✅ Convenience methods (track_bash with list/string commands)
- ✅ Edge cases (empty params, long errors, duration calculation)

### Integration Tests (Next Step)
- ⏳ Run pilot workflows with real BuildChecker
- ⏳ Validate data in PostgreSQL
- ⏳ Verify observability API integration
- ⏳ Test zero-overhead guarantee (logging failures don't block)

### End-to-End Tests (Future)
- ⏳ Full ADW workflow with tracking enabled
- ⏳ Pattern detection on tracked data
- ⏳ Script generation from detected patterns
- ⏳ ROI measurement accuracy

## Risk Assessment

### Low Risk ✅
- ✅ 100% backward compatible (tracker is optional)
- ✅ Zero-overhead guarantee (logging failures are caught)
- ✅ No changes to existing workflows
- ✅ Well-tested (20 unit tests passing)

### Medium Risk ⚠️
- ⚠️ Database performance - JSONB queries on large datasets
  - **Mitigation:** GIN index already created
  - **Monitoring:** Track query performance in Panel 7
- ⚠️ Observability API availability during workflow
  - **Mitigation:** Zero-overhead - failures are non-blocking
  - **Monitoring:** Log warnings when API calls fail

### Future Risk (Pattern Automation) 🔮
- 🔮 Automated script safety - destructive operations
  - **Mitigation:** Whitelist-based validation, dry-run mode
- 🔮 Pattern false positives - incorrect automation
  - **Mitigation:** 99%+ confidence threshold, human review

## Success Metrics

### Immediate (Week 1)
- ✅ ToolCallTracker created and tested (20/20 tests passing)
- ✅ BuildChecker integration complete (3 methods instrumented)
- ✅ Example implementation created
- ⏳ 5-10 pilot workflows executed with tracking
- ⏳ Tool call data validated in PostgreSQL

### Phase 1 (Weeks 1-4)
- ⏳ 20-30 workflows with tool tracking enabled
- ⏳ Test and Plan phases instrumented
- ⏳ Analytics dashboard shows tool usage trends
- ⏳ First pattern detected from tool_calls data

### Phase 2 (Weeks 5-10)
- ⏳ 5 automated patterns deployed
- ⏳ 50% token reduction on automated patterns
- ⏳ $10K+ cost savings measured
- ⏳ 95%+ automation accuracy

## Lessons Learned

### What Went Well ✅
1. **Clear separation of concerns** - Tracker is independent of BuildChecker
2. **Comprehensive testing** - 20 tests caught all edge cases
3. **Backward compatibility** - Zero breaking changes
4. **Clean API design** - Context manager pattern is intuitive

### What Could Be Improved 🔧
1. **Documentation** - Could add more inline examples
2. **Type hints** - Could strengthen Optional types
3. **Error messages** - Could add more context to warnings

### What's Next 🚀
1. **Pilot workflows** - Validate real-world usage
2. **Pattern detection** - Analyze tracked tool data
3. **Automation pipeline** - Build script generation system
4. **ROI measurement** - Prove cost savings

## References

### Related Documents
- `docs/architecture/adw-tracking-architecture.md` - Complete tracking system overview
- `docs/design/tool-call-tracking-design.md` - Implementation specification
- `docs/analysis/tool-tracking-comprehensive-review.md` - Multi-agent review findings
- `app/server/core/models/observability.py` - ToolCallRecord model (lines 88-97)
- `adws/adw_modules/observability.py` - log_task_completion() API (lines 33-48)

### Database Environment
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tac_webbuilder
POSTGRES_USER=tac_user
POSTGRES_PASSWORD=changeme
DB_TYPE=postgresql
```

### Key Commands
```bash
# Run unit tests
cd adws && .venv/bin/pytest tests/test_tool_call_tracker.py -v

# Run example
cd adws && python examples/build_with_tracking_example.py 123 adw-test

# Query tracked tools
psql -U tac_user -d tac_webbuilder -c "SELECT adw_id, phase_name, tool_calls::text FROM task_logs WHERE jsonb_array_length(tool_calls) > 0 LIMIT 5"
```

---

**Session Status:** ✅ Complete
**Ready for:** Pilot workflow execution and data validation
**Next Session:** Run 5-10 pilot workflows with tool tracking enabled
