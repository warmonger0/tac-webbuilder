# Phase 3B Completion: Tests + Missing Components

**Status:** 85% Complete - Core functionality working, needs tests + minor gaps
**Handoff Type:** ADW Workflow
**Priority:** HIGH (user wants production-ready before Phase 3C)

## What's Already Done ✅

**Core Scoring Functions** (all functional in `app/server/core/workflow_analytics.py`):
- ✅ `calculate_nl_input_clarity_score()` - lines 14-76
- ⚠️ `calculate_cost_efficiency_score()` - lines 78-123 (missing model appropriateness)
- ✅ `calculate_performance_score()` - lines 125-188
- ✅ `calculate_quality_score()` - lines 190-234
- ⭐ Bonus: `find_similar_workflows()`, `detect_anomalies()`, `generate_optimization_recommendations()`

**Integration:**
- ✅ Database schema with all Phase 3A columns
- ✅ Sync process calculates scores (workflow_history.py:875-913)
- ✅ TypeScript/Python types in sync
- ✅ No compilation errors

## What's Missing ❌

### 1. Unit Tests (CRITICAL - No Tests Exist)

**Create:** `app/server/tests/test_workflow_analytics.py`

**Required Test Classes:**
```python
class TestClarityScoring:
    # Test short input (10 words) → low score
    # Test optimal input (150 words, criteria) → high score (80-90)
    # Test verbose input (600 words) → medium score
    # Test empty input → 0 score
    # Test edge cases

class TestCostEfficiencyScoring:
    # Test under budget + high cache → high score (90-100)
    # Test over budget + low cache + retries → low score (<40)
    # Test missing estimate data → handle gracefully
    # Test model appropriateness (after implementing)

class TestPerformanceScoring:
    # Test faster than average → high score
    # Test slower than average → low score
    # Test no similar workflows → fallback to absolute duration
    # Test bottleneck detection

class TestQualityScoring:
    # Test perfect execution (no errors) → high score (90-100)
    # Test errors + retries → lower score
    # Test missing PR/CI data → handle gracefully

class TestHelperFunctions:
    # Test extract_hour() with various ISO formats
    # Test extract_day_of_week()
    # Test detect_complexity()

class TestIntegration:
    # Test sync_workflow_history() populates all score fields
    # Test scores are 0-100 range
    # Test missing data doesn't crash
```

**Framework:** pytest (already in project)

### 2. Helper Functions Refactor

**Extract to standalone functions in `workflow_analytics.py`:**

```python
def extract_hour(timestamp: str) -> int:
    """Extract hour (0-23) from ISO timestamp."""
    # Current logic at workflow_history.py:886
    # Move here for reusability

def extract_day_of_week(timestamp: str) -> int:
    """Extract day of week (0=Monday, 6=Sunday) from ISO timestamp."""
    # Current logic at workflow_history.py:887
    # Move here for reusability

def detect_complexity(workflow: Dict) -> str:
    """
    Detect workflow complexity for model appropriateness scoring.

    Returns: "simple", "medium", "complex"

    Criteria:
    - Simple: word_count < 50 AND duration < 300s AND errors < 3
    - Complex: word_count > 200 OR duration > 1800s OR errors > 5
    - Medium: everything else
    """
    pass  # Implement
```

### 3. Model Appropriateness Scoring

**Add to `calculate_cost_efficiency_score()` (lines 78-123):**

```python
# After retry penalty calculation, add:

# Model appropriateness scoring (10 points)
complexity = detect_complexity(workflow)
model = workflow.get("model_used", "").lower()

model_score = 0
if complexity == "simple" and "haiku" in model:
    model_score = 10  # Perfect match
elif complexity == "complex" and "sonnet" in model:
    model_score = 10  # Perfect match
elif complexity == "medium":
    model_score = 8   # Either model is fine
elif "sonnet" in model and complexity == "simple":
    model_score = 5   # Overkill but works
elif "haiku" in model and complexity == "complex":
    model_score = 3   # Underpowered

score = score * 0.9 + model_score  # Reweight to include model component
```

### 4. Tighten Anomaly Thresholds (User Feedback)

**Update `detect_anomalies()` in workflow_analytics.py:310-381:**

Current thresholds are TOO LENIENT per user. Change:
- Cost anomaly: `>2x` → `>1.5x` (line ~346)
- Duration anomaly: `>2x` → `>1.5x` (line ~357)
- Retry anomaly: `>=3` → `>=2` (line ~365)

### 5. Add Scoring Version Tracking (User Request)

**Update database schema:**
```sql
-- Add to migration or new migration file
ALTER TABLE workflow_history ADD COLUMN scoring_version TEXT DEFAULT '1.0';
```

**Update types:**
- Add to `WorkflowHistoryItem` in data_models.py
- Add to `WorkflowHistoryItem` in api.types.ts

**Set version during sync:**
```python
# In sync_workflow_history()
workflow_data["scoring_version"] = "1.0"
```

## User Requirements (Answered Questions)

1. **Missing cost estimate data:** Should NEVER happen - kick back if missing (user requirement)
2. **Anomaly thresholds:** Current >2x is TOO LENIENT - tighten to >1.5x
3. **Score versioning:** YES - track version (starting at "1.0")
4. **Priority:** Complete Phase 3B fully BEFORE moving to Phase 3C UI

## Acceptance Criteria for Completion

- [ ] All 5 test classes created with 3+ test cases each
- [ ] All tests pass with no failures
- [ ] Test coverage >90% for workflow_analytics.py functions
- [ ] Helper functions extracted and reusable
- [ ] Model appropriateness added to cost_efficiency_score
- [ ] Anomaly thresholds tightened to 1.5x
- [ ] Scoring version tracking added (database + types + sync)
- [ ] Integration test confirms all scores populate during sync
- [ ] No regressions - existing functionality still works

## Files to Modify

1. **Create:** `app/server/tests/test_workflow_analytics.py` (new test file)
2. **Modify:** `app/server/core/workflow_analytics.py`
   - Add `extract_hour()`, `extract_day_of_week()`, `detect_complexity()`
   - Update `calculate_cost_efficiency_score()` with model appropriateness
   - Update `detect_anomalies()` thresholds
3. **Modify:** `app/server/core/workflow_history.py`
   - Replace inline temporal logic with helper function calls
   - Add scoring_version to sync
4. **Modify:** `app/server/core/data_models.py`
   - Add `scoring_version: Optional[str]` to WorkflowHistoryItem
5. **Modify:** `app/client/src/types/api.types.ts`
   - Add `scoring_version?: string` to WorkflowHistoryItem
6. **Create:** Database migration for scoring_version column (if needed)

## Testing Instructions

```bash
# Run tests
cd app/server
uv run pytest tests/test_workflow_analytics.py -v

# Check coverage
uv run pytest tests/test_workflow_analytics.py --cov=core.workflow_analytics --cov-report=term-missing

# Run integration test
uv run pytest tests/test_workflow_analytics.py::TestIntegration -v
```

## Success Metrics

- ✅ All tests pass
- ✅ Coverage >90%
- ✅ Scoring version tracked
- ✅ Anomaly detection more sensitive (1.5x threshold)
- ✅ Model appropriateness scoring complete
- ✅ Helper functions reusable
- ✅ Ready for Phase 3C UI implementation

## Reference

- Full spec: `docs/PHASE_3B_SCORING_ENGINE.md`
- Gap analysis: `docs/PHASE_3B_SCORING_ENGINE.md` lines 52-71
- Current implementation: `app/server/core/workflow_analytics.py`

## Time Estimate

- Unit tests: 2-3 hours
- Helper functions: 30 min
- Model appropriateness: 30 min
- Anomaly threshold updates: 15 min
- Scoring version: 30 min
- **Total: 3.5-4.5 hours**

## ADW Workflow Parameters

**Classification:** lightweight (mostly tests, small refactor)
**Model:** Haiku (straightforward test writing + small logic additions)
**Estimated Cost:** $0.30-0.50
