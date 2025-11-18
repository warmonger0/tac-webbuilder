## Workflow 3B.7: Integration Tests and Cleanup

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflows 3B.2-3B.6

**Input Files:**
- All refactored modules

**Output Files:**
- `app/server/tests/test_workflow_analytics_integration.py` (new)
- Updated `app/server/core/workflow_analytics/__init__.py` (final)

**Tasks:**

1. **Create integration tests**
2. **Update final __init__.py with all imports**
3. **Remove backup file**
4. **Verify all imports across codebase**
5. **Run full test suite**

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Backwards compatibility verified
- [ ] No breaking changes
- [ ] Performance unchanged
- [ ] Backup file removed

**Verification Commands:**
```bash
# Test all scoring functions
python -c "
from app.server.core.workflow_analytics import (
    calculate_nl_input_clarity_score,
    calculate_cost_efficiency_score,
    calculate_performance_score,
    calculate_quality_score,
    find_similar_workflows,
    detect_anomalies,
    generate_optimization_recommendations,
)
print('All imports successful')
"

# Run full test suite
cd app/server && pytest tests/test_workflow_analytics.py -v
cd app/server && pytest tests/test_workflow_analytics_integration.py -v
```

**Status:** Not Started

---
