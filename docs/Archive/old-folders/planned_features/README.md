# Planned Features: Efficiency Score Improvements

This directory contains detailed implementation plans for fixing the three efficiency scores in the Workflow History feature.

## Overview

The Workflow History dashboard displays three efficiency scores to evaluate workflow quality:
1. **Quality Score** - Based on errors, retries, PR/CI status
2. **Cost Efficiency Score** - Based on budget adherence, cache usage
3. **Performance Score** - Based on duration and phase metrics

**Current State:**
- Quality Score: **95.0** for all workflows (uniform, lacks differentiation)
- Cost Efficiency Score: **0.0** for 92% of workflows (missing estimates)
- Performance Score: **0.0** for 100% of workflows (no duration data)

## Implementation Plans

### 1. Quality Score Improvements
**File:** [quality_score_improvements.md](./quality_score_improvements.md)

**Problem:** All workflows show 95.0 because error tracking, PR/CI integration, and review metrics are not implemented.

**Solution Phases:**
- **Phase 1:** Add error tracking (parse errors from `raw_output.jsonl`)
- **Phase 2:** Integrate GitHub PR/CI status
- **Phase 3:** Track review cycles and feedback iterations

**Timeline:** 14-20 hours

**Impact:** Scores will differentiate workflows based on actual quality metrics (errors, test results, review feedback)

---

### 2. Cost Efficiency Score Improvements
**File:** [cost_efficiency_score_improvements.md](./cost_efficiency_score_improvements.md)

**Problem:** 92% of workflows show 0.0 because only 2 issues have cost estimates in `cost_estimates_by_issue.json`.

**Solution Phases:**
- **Phase 1:** Backfill estimates for all historical issues
- **Phase 2:** Auto-generate estimates for new issues (webhook + fallback)
- **Phase 3:** Improve estimate accuracy with ML/historical data

**Timeline:** 18-26 hours

**Impact:** All workflows will have meaningful cost efficiency scores showing budget adherence

---

### 3. Performance Score Improvements
**File:** [performance_score_improvements.md](./performance_score_improvements.md)

**Problem:** All workflows show 0.0 because `duration_seconds` is never populated.

**Solution Phases:**
- **Phase 1:** Extract duration from `raw_output.jsonl` timestamps
- **Phase 2:** Continuously update duration for running workflows
- **Phase 3:** Add advanced phase-level performance metrics

**Timeline:** 14-20 hours

**Impact:** All workflows will show performance scores based on duration, bottlenecks, and phase efficiency

---

## Priority Recommendation

### High Priority (Implement First)
1. **Performance Score - Phase 1** (6-8 hours)
   - Most impactful: fixes 100% of workflows showing 0.0
   - Relatively straightforward: parse existing data
   - No external dependencies

2. **Cost Efficiency Score - Phase 1** (6-8 hours)
   - High impact: fixes 92% of workflows showing 0.0
   - Uses heuristic estimation (no ML required)
   - Requires GitHub API access

### Medium Priority
3. **Performance Score - Phase 2** (4-6 hours)
   - Enables real-time tracking for running workflows
   - Improves user experience with live updates

4. **Quality Score - Phase 1** (4-6 hours)
   - Adds error differentiation
   - Relatively simple parsing logic

### Low Priority (Nice to Have)
5. **Cost Efficiency Score - Phase 2 & 3** (12-18 hours)
   - Automation and accuracy improvements
   - Can be done incrementally

6. **Quality Score - Phase 2 & 3** (10-14 hours)
   - PR/CI integration and advanced metrics
   - Requires more complex GitHub integration

7. **Performance Score - Phase 3** (4-6 hours)
   - Advanced metrics (nice to have)
   - Can be added later

---

## Quick Start Guide

### 1. Performance Score Fix (Recommended First)

```bash
cd app/server

# Step 1: Add database columns
uv run python -c "
from core.workflow_history import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN end_time TEXT DEFAULT NULL')
    conn.commit()
    print('✓ Added end_time column')
"

# Step 2: Implement extract_workflow_timestamps() in workflow_history.py
# (See performance_score_improvements.md Section 1.1)

# Step 3: Update sync_workflow_history() to use new function
# (See performance_score_improvements.md Section 1.2)

# Step 4: Run sync to backfill duration data
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'✓ Synced {synced} workflows with duration data')
"

# Step 5: Verify results
sqlite3 db/workflow_history.db "
    SELECT COUNT(*) as with_duration
    FROM workflow_history
    WHERE duration_seconds IS NOT NULL AND duration_seconds > 0
"
```

### 2. Cost Efficiency Score Fix

```bash
cd app/server

# Step 1: Implement cost estimator
# (See cost_efficiency_score_improvements.md Section 1.3)

# Step 2: Create backfill script
# (See cost_efficiency_score_improvements.md Section 1.1)

# Step 3: Run backfill
uv run python scripts/backfill_cost_estimates.py

# Step 4: Re-sync workflows
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'✓ Updated {synced} workflows with cost estimates')
"
```

### 3. Quality Score Fix

```bash
cd app/server

# Step 1: Add database columns
uv run python -c "
from core.workflow_history import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN error_count INTEGER DEFAULT 0')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN error_types TEXT DEFAULT \"[]\"')
    conn.commit()
    print('✓ Added error tracking columns')
"

# Step 2: Implement extract_errors_from_raw_output()
# (See quality_score_improvements.md Section 1.2)

# Step 3: Update sync_workflow_history()
# (See quality_score_improvements.md Section 1.3)

# Step 4: Run sync to backfill error data
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'✓ Synced {synced} workflows with error data')
"
```

---

## Expected Outcomes

### Before Implementation
```
Workflow History Dashboard:
┌──────────────────────────────────────┐
│ Efficiency Scores                    │
├──────────────────────────────────────┤
│ Cost Efficiency:    0.0              │  ← Not useful
│ Performance:        0.0              │  ← Not useful
│ Quality:           95.0              │  ← Not useful (uniform)
└──────────────────────────────────────┘

Status: All scores either 0 or uniform 95
Usefulness: Low (cannot differentiate workflows)
```

### After Implementation
```
Workflow History Dashboard:
┌──────────────────────────────────────┐
│ Efficiency Scores                    │
├──────────────────────────────────────┤
│ Cost Efficiency:   72.5              │  ← Meaningful (under budget)
│ Performance:       81.0              │  ← Meaningful (fast execution)
│ Quality:           88.0              │  ← Meaningful (minor errors fixed)
└──────────────────────────────────────┘

Status: Scores show realistic differentiation
Usefulness: High (actionable insights)
```

---

## Testing Strategy

### Unit Tests
Each implementation plan includes specific unit tests in the "Testing Plan" section.

**General approach:**
1. Test calculation functions with mock data
2. Test edge cases (missing data, invalid values)
3. Test score boundaries (0-100 range)

### Integration Tests
1. Test data extraction from actual files
2. Test database operations
3. Test sync workflow end-to-end

### Manual Testing Checklist
- [ ] All workflows have non-zero scores (where data available)
- [ ] Score distribution looks realistic (not all same value)
- [ ] Scores update when underlying data changes
- [ ] UI displays scores correctly
- [ ] Performance acceptable (<10s sync for 50 workflows)

---

## Dependencies

### Required
- **Python 3.11+**
- **SQLite3**
- **GitHub CLI** (`gh`) or GitHub API token

### Optional
- **apscheduler** (for background sync)
- **scikit-learn** (for ML-based cost estimation)
- **pandas/numpy** (for analysis scripts)

---

## Risks & Common Issues

### Database Schema Changes
**Risk:** Schema changes could break existing queries

**Mitigation:**
1. Test migrations on copy of database first
2. Use `ALTER TABLE ADD COLUMN` with `DEFAULT` values
3. Add columns incrementally, not all at once

### GitHub API Rate Limits
**Risk:** Backfilling 100+ issues could hit rate limits

**Mitigation:**
1. Use GitHub CLI (higher limits for authenticated users)
2. Add delays between requests
3. Use GraphQL API for batch requests
4. Cache results to avoid re-fetching

### Performance Impact
**Risk:** Periodic sync could slow down server

**Mitigation:**
1. Limit sync frequency (5-10 minutes)
2. Use background threads/workers
3. Add circuit breaker to skip sync if overloaded
4. Optimize file parsing (only read first/last lines)

---

## Success Metrics

### Quantitative
- **Coverage**: % of workflows with non-zero scores
  - Target: >90% for all three scores
- **Distribution**: Coefficient of variation
  - Target: CV > 0.15 (shows differentiation)
- **Sync Performance**: Time to sync 50 workflows
  - Target: <10 seconds

### Qualitative
- Scores reflect actual workflow quality/efficiency
- Users can identify best/worst performing workflows
- Scores help prioritize optimization efforts
- Dashboard provides actionable insights

---

## Questions?

For detailed implementation steps, refer to the individual plan documents:
- [quality_score_improvements.md](./quality_score_improvements.md)
- [cost_efficiency_score_improvements.md](./cost_efficiency_score_improvements.md)
- [performance_score_improvements.md](./performance_score_improvements.md)

For questions or clarifications, please open an issue or contact the development team.
