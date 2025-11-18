## Workflow 3B.5: Extract similarity.py and anomalies.py

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 437-767)

**Output Files:**
- `app/server/core/workflow_analytics/similarity.py` (new)
- `app/server/core/workflow_analytics/anomalies.py` (new)

**Tasks:**

1. **Extract find_similar_workflows()** → similarity.py
2. **Extract detect_anomalies()** → anomalies.py
3. **Update imports**

**Acceptance Criteria:**
- [ ] Similarity detection works
- [ ] Anomaly detection works
- [ ] Tests pass

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
