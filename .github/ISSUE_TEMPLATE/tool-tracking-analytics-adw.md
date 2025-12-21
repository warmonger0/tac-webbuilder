## Overview
Expand tool call tracking infrastructure to all ADW phases and build analytics dashboard for pattern analysis.

**Context:** Session 22 completed ToolCallTracker infrastructure with 20/20 tests passing. BuildChecker integration is live. Next phase: expand coverage and add analytics visibility.

**Related:** #236 (Tool Call Tracking and Analytics)

adw_sdlc_complete_iso

## Phase 1: Expand Tracking Coverage

### 1. Test Phase Integration (adw_test_iso.py)
- [ ] Integrate ToolCallTracker in Test phase
- [ ] Track: pytest, vitest, coverage commands
- [ ] Track: linting tools (eslint, ruff, mypy)
- [ ] Validate tool_calls data in PostgreSQL

### 2. Plan Phase Integration (adw_plan_iso.py)
- [ ] Integrate ToolCallTracker in Plan phase
- [ ] Track: git operations (clone, checkout, fetch)
- [ ] Track: file exploration commands
- [ ] Validate metadata capture

### 3. Ship Phase Integration (adw_ship_iso.py)
- [ ] Integrate ToolCallTracker in Ship phase
- [ ] Track: git push, PR creation, merge operations
- [ ] Track: deployment commands
- [ ] Validate end-to-end flow

## Phase 2: Analytics Dashboard (Panel 7 Extension)

### 4. Tool Usage Analytics
- [ ] Add tool usage heatmap visualization
- [ ] Show most expensive tools by time and cost
- [ ] Display tool failure rate trends
- [ ] Compare Build vs Test vs Ship tool usage

### 5. Pattern Analysis Queries
- [ ] Query tool call sequences from task_logs
- [ ] Group similar patterns (semantic clustering)
- [ ] Calculate pattern frequency and success rates
- [ ] Identify automation candidates (>50 occurrences)

### 6. Cost Attribution
- [ ] Link tool usage to workflow costs
- [ ] Calculate ROI for potential automations
- [ ] Show cost trends over time
- [ ] Highlight high-impact optimization opportunities

## Phase 3: Validation

### 7. Run Pilot Workflows
- [ ] Execute 5-10 workflows with full tracking enabled
- [ ] Verify tool_calls data quality in PostgreSQL
- [ ] Validate observability API integration
- [ ] Confirm zero-overhead guarantee (no workflow blocking)

### 8. Data Quality Checks
```sql
-- Verify tool calls are being logged
SELECT adw_id, issue_number, phase_name, jsonb_array_length(tool_calls) as tool_count
FROM task_logs
WHERE tool_calls IS NOT NULL AND jsonb_array_length(tool_calls) > 0
ORDER BY completed_at DESC
LIMIT 20;

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
```

## Success Metrics

**Immediate (Week 1):**
- ✅ All ADW phases instrumented (Plan, Build, Test, Ship)
- ✅ 20+ workflows executed with tracking
- ✅ Analytics dashboard showing tool usage trends

**Phase 2 (Weeks 2-4):**
- ✅ First automated pattern detected and validated
- ✅ 5+ automation candidates identified
- ✅ Cost savings projections documented

## Technical Notes

**Database:** `task_logs.tool_calls JSONB` column (already exists, GIN indexed)
**Tracker:** `adws/adw_modules/tool_call_tracker.py` (tested, ready)
**Pattern:** Context manager with auto-logging on exit

**Example Integration:**
```python
from adw_modules.tool_call_tracker import ToolCallTracker

with ToolCallTracker(adw_id=adw_id, issue_number=issue_num, phase_name="Test") as tracker:
    tracker.track_bash("pytest", ["pytest", "tests/", "-v"], cwd=repo_path)
    tracker.track_bash("vitest", ["bun", "run", "test"], cwd=frontend_path)
# Auto-logs to task_logs.tool_calls on exit
```

## References
- Session 22: `docs/sessions/session-22-tool-call-tracker-implementation.md`
- Architecture: `docs/architecture/adw-tracking-architecture.md`
- Design: `docs/design/tool-call-tracking-design.md`
