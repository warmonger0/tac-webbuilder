## Workflow 3B.6: Extract recommendations.py and temporal/complexity helpers

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 29-122, 770-904)

**Output Files:**
- `app/server/core/workflow_analytics/temporal.py` (new)
- `app/server/core/workflow_analytics/complexity.py` (new)
- `app/server/core/workflow_analytics/recommendations.py` (new)

**Tasks:**

1. **Extract extract_hour(), extract_day_of_week()** → temporal.py
2. **Extract detect_complexity()** → complexity.py
3. **Extract generate_optimization_recommendations()** → recommendations.py
4. **Update imports**

**Acceptance Criteria:**
- [ ] All helper modules created
- [ ] Recommendations generated correctly
- [ ] Tests pass

**Status:** Not Started

---
