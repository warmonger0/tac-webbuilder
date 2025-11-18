## Workflow 3B.4: Extract performance_score.py and quality_score.py

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 289-430)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/performance_score.py` (new)
- `app/server/core/workflow_analytics/scoring/quality_score.py` (new)

**Tasks:**

1. **Create performance_score.py** (similar pattern to clarity and cost)
2. **Create quality_score.py** (similar pattern)
3. **Update imports**

**Acceptance Criteria:**
- [ ] Both scorer modules created
- [ ] Use BaseScorer pattern
- [ ] Backwards compatible API
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import (
    calculate_performance_score,
    calculate_quality_score
)
workflow = {'duration_seconds': 120, 'error_count': 0, 'status': 'completed'}
perf = calculate_performance_score(workflow)
qual = calculate_quality_score(workflow)
print(f'Performance: {perf}, Quality: {qual}')
"
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
