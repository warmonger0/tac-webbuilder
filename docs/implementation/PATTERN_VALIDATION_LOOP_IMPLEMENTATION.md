# Pattern Validation Loop Implementation Plan
## Phase 3: Close the Loop - Validate Predictions

**Related Plan Item:** ID #63 (Session 18)
**Priority:** High
**Estimated Effort:** 3.0 hours
**Status:** Planned

---

## Executive Summary

Implement the missing "Close the Loop" validation system for pattern predictions. This creates a feedback loop that measures prediction accuracy by comparing patterns predicted at submission time (via `pattern_predictor.py`) against actual patterns detected after workflow completion (via `pattern_detector.py`).

**Current State:**
- ✅ Pattern Predictor exists (`pattern_predictor.py`) - predicts patterns from NL input
- ✅ Pattern Detector exists (`pattern_detector.py`) - detects patterns from completed workflows
- ✅ Migration 010 schema ready - `pattern_predictions` table with `was_correct` field
- ❌ Pattern Validator missing - no code to compare predicted vs actual
- ❌ Validation integration missing - no workflow completion hook
- ❌ Accuracy metrics missing - `prediction_accuracy` field never updated

**What This Enables:**
- Measure how well we predict patterns (accuracy tracking)
- Improve predictions over time (machine learning feedback loop)
- Identify high-confidence patterns for automation
- Close the observability gap between prediction and reality

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATTERN VALIDATION LOOP                       │
└─────────────────────────────────────────────────────────────────┘

1. SUBMISSION (existing)
   User Input → pattern_predictor.py → Predictions stored in DB
                                        └─> pattern_predictions table
                                            (was_correct = NULL)

2. EXECUTION (existing)
   Workflow runs → Phases execute → Work gets done

3. COMPLETION (existing)
   Workflow completes → pattern_detector.py → Actual patterns detected
                                               └─> operation_patterns table

4. VALIDATION (NEW - this implementation)
   ┌─────────────────────────────────────────────────────┐
   │  pattern_validator.py (NEW)                         │
   │  ├─ Compare predicted vs actual patterns            │
   │  ├─ Calculate accuracy (TP, FP, FN)                 │
   │  ├─ Update pattern_predictions.was_correct          │
   │  └─ Update operation_patterns.prediction_accuracy   │
   └─────────────────────────────────────────────────────┘
           ↓
   Accuracy metrics stored → Future predictions improved
```

---

## Implementation Steps

### Step 1: Create Pattern Validator Module (45 min)

**File:** `app/server/core/pattern_validator.py`

**Responsibilities:**
1. Fetch predicted patterns for a given request_id
2. Compare against actual patterns detected
3. Calculate accuracy metrics (true positives, false positives, false negatives)
4. Update database with validation results

**Key Functions:**

```python
def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: List[str],
    db_connection
) -> ValidationResult:
    """
    Compare predicted patterns against actual patterns.

    Returns:
        ValidationResult with:
        - total_predicted: int
        - total_actual: int
        - correct: int (true positives)
        - false_positives: int (predicted but not actual)
        - false_negatives: int (actual but not predicted)
        - accuracy: float (0.0 to 1.0)
        - details: dict with pattern-level results
    """
```

**Algorithm:**

```python
# 1. Fetch predictions from DB
predictions = fetch_predictions_for_request(request_id)
predicted_set = {p.pattern_signature for p in predictions}

# 2. Convert actual to set
actual_set = set(actual_patterns)

# 3. Calculate metrics
true_positives = predicted_set & actual_set  # Intersection
false_positives = predicted_set - actual_set  # Predicted but not actual
false_negatives = actual_set - predicted_set  # Actual but not predicted

accuracy = len(true_positives) / len(predicted_set) if predicted_set else 0.0

# 4. Update pattern_predictions table
for prediction in predictions:
    was_correct = 1 if prediction.pattern_signature in actual_set else 0
    update_prediction_validation(prediction.id, was_correct)

# 5. Update operation_patterns.prediction_accuracy
# Recalculate accuracy as: (sum of was_correct) / (total validations)
for pattern_id in affected_pattern_ids:
    update_pattern_accuracy(pattern_id)
```

**Database Queries:**

```sql
-- Update individual prediction
UPDATE pattern_predictions
SET was_correct = ?, validated_at = NOW()
WHERE id = ?;

-- Recalculate pattern accuracy
UPDATE operation_patterns
SET prediction_accuracy = (
    SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
    FROM pattern_predictions
    WHERE pattern_id = operation_patterns.id
      AND was_correct IS NOT NULL
)
WHERE id = ?;
```

**Error Handling:**
- Handle missing request_id gracefully (some workflows predate predictions)
- Log validation failures but don't block workflow completion
- Return empty ValidationResult if no predictions found

---

### Step 2: Integrate into Workflow Completion (30 min)

**Where to Hook:**

Option A: Modify `pattern_detector.py` (Recommended)
- Already has access to completed workflow data
- Already detects actual patterns
- Natural place to add validation step

Option B: Create separate completion hook
- More separation of concerns
- Easier to test independently
- May duplicate workflow data fetching

**Recommended Approach:** Modify `pattern_detector.py`

**Integration Point:**

```python
# In pattern_detector.py

def detect_patterns_from_workflow(workflow_data: dict) -> List[Pattern]:
    """Detect patterns from completed workflow."""

    # Existing pattern detection logic
    detected_patterns = []
    # ... detection logic ...

    # NEW: Validate predictions if request_id exists
    if workflow_data.get('request_id'):
        from core.pattern_validator import validate_predictions

        pattern_signatures = [p['signature'] for p in detected_patterns]
        validation_result = validate_predictions(
            request_id=workflow_data['request_id'],
            workflow_id=workflow_data['workflow_id'],
            actual_patterns=pattern_signatures,
            db_connection=conn
        )

        logger.info(
            f"[Validator] Request {workflow_data['request_id']}: "
            f"{validation_result.accuracy:.1%} accuracy "
            f"({validation_result.correct}/{validation_result.total_predicted} correct)"
        )

    return detected_patterns
```

**Fallback Handling:**
- If `request_id` not in workflow_data, skip validation (no error)
- If validation fails, log error but continue pattern detection
- Ensure validation doesn't block main workflow completion

---

### Step 3: Add Analytics Queries (30 min)

**File:** `app/server/tests/manual/query_prediction_accuracy.py`

**Purpose:** Query and report on prediction accuracy metrics

**Queries to Implement:**

1. **Overall Accuracy**
```sql
SELECT
    COUNT(*) as total_predictions,
    SUM(was_correct) as correct_predictions,
    CAST(SUM(was_correct) AS REAL) / COUNT(*) as accuracy
FROM pattern_predictions
WHERE was_correct IS NOT NULL;
```

2. **Accuracy by Pattern Type**
```sql
SELECT
    op.pattern_signature,
    op.pattern_type,
    op.prediction_count,
    op.prediction_accuracy,
    COUNT(pp.id) as validated_count
FROM operation_patterns op
LEFT JOIN pattern_predictions pp ON op.id = pp.pattern_id
WHERE op.prediction_count > 0
GROUP BY op.id
ORDER BY op.prediction_accuracy DESC;
```

3. **Recent Prediction Performance**
```sql
SELECT
    pp.request_id,
    pp.predicted_at,
    op.pattern_signature,
    pp.confidence_score,
    pp.was_correct
FROM pattern_predictions pp
JOIN operation_patterns op ON pp.pattern_id = op.id
WHERE pp.was_correct IS NOT NULL
ORDER BY pp.predicted_at DESC
LIMIT 20;
```

4. **Low-Confidence Patterns (need improvement)**
```sql
SELECT
    pattern_signature,
    prediction_count,
    prediction_accuracy
FROM operation_patterns
WHERE prediction_count >= 5
  AND prediction_accuracy < 0.60
ORDER BY prediction_count DESC;
```

**CLI Output Format:**

```
📊 Pattern Prediction Accuracy Report
================================================================================

Overall Accuracy: 73.5% (147/200 predictions correct)

Top Performing Patterns:
  1. test:pytest:backend          92.3%  (12/13 correct, 13 predictions)
  2. build:typecheck:backend      87.5%  (7/8 correct, 8 predictions)
  3. fix:bug                      75.0%  (15/20 correct, 20 predictions)

Underperforming Patterns (need improvement):
  1. deploy:production            45.0%  (9/20 correct, 20 predictions)
  2. refactor:architecture        50.0%  (5/10 correct, 10 predictions)

Recent Predictions:
  ✅ test:pytest:backend (req-123) - 0.85 confidence - CORRECT
  ❌ deploy:production (req-122) - 0.70 confidence - INCORRECT
  ✅ build:typecheck:backend (req-121) - 0.75 confidence - CORRECT
```

---

### Step 4: Add Logging (30 min)

**Log Events to Add:**

1. **Validation Start**
```python
logger.info(f"[Validator] Starting validation for request {request_id}")
```

2. **Validation Results**
```python
logger.info(
    f"[Validator] Request {request_id}: {accuracy:.1%} accuracy - "
    f"{correct} correct, {false_positives} FP, {false_negatives} FN"
)
```

3. **Database Updates**
```python
logger.debug(f"[Validator] Updated {count} prediction records")
logger.debug(f"[Validator] Updated accuracy for {pattern_count} patterns")
```

4. **Errors**
```python
logger.error(
    f"[Validator] Validation failed for request {request_id}: {error}",
    exc_info=True
)
```

**Structured Logging (Optional Enhancement):**

If implementing structured logging (from Phase 1 of pattern recognition plan):

```python
from core.pattern_logging import log_pattern_event

log_pattern_event('validation_start', {
    'request_id': request_id,
    'workflow_id': workflow_id,
    'actual_patterns_count': len(actual_patterns)
})

log_pattern_event('validation_complete', {
    'request_id': request_id,
    'accuracy': validation_result.accuracy,
    'correct_predictions': validation_result.correct,
    'false_positives': validation_result.false_positives,
    'false_negatives': validation_result.false_negatives
})
```

---

### Step 5: Write Tests (45 min)

**File:** `app/server/tests/core/test_pattern_validator.py`

**Test Cases:**

1. **Test Perfect Prediction**
```python
def test_validate_predictions_perfect_accuracy():
    """All predictions match actual patterns."""
    # Predicted: [A, B, C]
    # Actual: [A, B, C]
    # Expected: 100% accuracy, 0 FP, 0 FN
```

2. **Test Partial Match**
```python
def test_validate_predictions_partial_accuracy():
    """Some predictions correct, some not."""
    # Predicted: [A, B, C]
    # Actual: [A, B, D]
    # Expected: 66.7% accuracy, 1 FP (C), 1 FN (D)
```

3. **Test No Predictions**
```python
def test_validate_predictions_empty_predictions():
    """No predictions were made."""
    # Predicted: []
    # Actual: [A, B]
    # Expected: 0% accuracy, 0 FP, 2 FN
```

4. **Test Database Updates**
```python
def test_validate_predictions_updates_database():
    """Validation results stored in DB correctly."""
    # Verify pattern_predictions.was_correct set
    # Verify operation_patterns.prediction_accuracy updated
```

5. **Test Missing Request ID**
```python
def test_validate_predictions_no_request_id():
    """Gracefully handle workflows without request_id."""
    # Should not raise error
    # Should return empty ValidationResult
```

**Test Fixtures:**

```python
@pytest.fixture
def sample_predictions(db_connection):
    """Create sample predictions in DB."""
    # Insert test data into pattern_predictions
    # Return request_id for testing

@pytest.fixture
def sample_actual_patterns():
    """Return list of actual pattern signatures."""
    return ['test:pytest:backend', 'build:typecheck:backend']
```

---

## Database Schema Verification

**Required Tables:**

1. **operation_patterns** (should exist)
```sql
CREATE TABLE operation_patterns (
    id SERIAL PRIMARY KEY,
    pattern_signature TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL,
    automation_status TEXT DEFAULT 'detected',
    detection_count INTEGER DEFAULT 0,
    prediction_count INTEGER DEFAULT 0,
    prediction_accuracy REAL DEFAULT 0.0,  -- Updated by validator
    last_detected TIMESTAMP,
    last_predicted TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

2. **pattern_predictions** (Migration 010)
```sql
CREATE TABLE pattern_predictions (
    id SERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    pattern_id INTEGER REFERENCES operation_patterns(id),
    confidence_score REAL NOT NULL,
    reasoning TEXT,
    predicted_at TIMESTAMP DEFAULT NOW(),
    was_correct INTEGER,  -- NULL, 1 (correct), 0 (incorrect)
    validated_at TIMESTAMP,  -- Set by validator
    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);
```

**Indexes:**
```sql
CREATE INDEX idx_pattern_predictions_request ON pattern_predictions(request_id);
CREATE INDEX idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX idx_pattern_predictions_validated ON pattern_predictions(was_correct);
```

---

## Success Criteria

**Phase Complete When:**

- [ ] `pattern_validator.py` created with `validate_predictions()` function
- [ ] Validation integrated into workflow completion (pattern_detector.py)
- [ ] `pattern_predictions.was_correct` field populated after validation
- [ ] `operation_patterns.prediction_accuracy` field updated
- [ ] Analytics query script created and working
- [ ] Comprehensive test coverage (≥5 test cases)
- [ ] Logging added for all validation events
- [ ] Manual test shows ≥60% overall accuracy for common patterns
- [ ] Documentation updated with validation flow

**Validation Metrics:**

After implementation, run validation on past workflows:
- Overall accuracy should be ≥60% (keyword-based predictions)
- High-confidence patterns (>0.8) should have ≥80% accuracy
- Low-confidence patterns (<0.6) expected to be <50% accurate

---

## Implementation Order

1. ✅ **Step 1:** Create `pattern_validator.py` (45 min)
2. ✅ **Step 5:** Write tests first (TDD approach) (45 min)
3. ✅ **Step 2:** Integrate into workflow completion (30 min)
4. ✅ **Step 3:** Add analytics queries (30 min)
5. ✅ **Step 4:** Add logging (30 min)
6. ✅ **Verify:** Run manual tests and check accuracy metrics

**Total Estimated Time:** 3.0 hours

---

## Risks & Mitigation

**Risk 1: Validation Slows Down Workflow Completion**
- Mitigation: Validation runs after pattern detection (async-safe)
- Mitigation: Add try/catch so validation errors don't block workflow
- Mitigation: Keep queries efficient with proper indexing

**Risk 2: Low Initial Accuracy (<50%)**
- Mitigation: Expected for keyword-based predictor (Phase 1)
- Mitigation: Accuracy will improve in future phases (ML-based prediction)
- Mitigation: Document accuracy expectations in validation report

**Risk 3: Missing request_id in Older Workflows**
- Mitigation: Check for request_id before validation
- Mitigation: Skip validation gracefully if not present
- Mitigation: Only validate workflows created after prediction system deployed

---

## Future Enhancements (Out of Scope)

1. **Real-time Accuracy Dashboard** (Phase 4)
   - Web UI to view prediction accuracy
   - Charts showing accuracy trends over time
   - Pattern-specific accuracy breakdowns

2. **ML-Based Predictor** (Future Phase)
   - Use validation data to train ML model
   - Replace keyword-based predictions with learned predictions
   - Expected accuracy improvement to 85%+

3. **Auto-Correction**
   - Automatically adjust confidence scores based on validation
   - Suppress low-accuracy patterns from future predictions
   - Boost high-accuracy patterns

4. **A/B Testing**
   - Test multiple prediction algorithms
   - Use validation data to compare accuracy
   - Choose best-performing algorithm

---

## Dependencies

**Code Dependencies:**
- `pattern_predictor.py` (already exists)
- `pattern_detector.py` (already exists)
- Database migration 010 applied (verify in Step 0)

**Database Dependencies:**
- PostgreSQL with `pattern_predictions` table
- `operation_patterns` table
- Proper indexes on request_id and pattern_id

**Testing Dependencies:**
- pytest
- Database test fixtures
- Sample workflow data

---

## Related Documentation

- Main Plan: `docs/requests/complete_pattern_recognition_system.md`
- Phase 1: Submission-Time Prediction (partially complete)
- Phase 2: Queue Integration (not started)
- **Phase 3: This Document** - Validation Loop
- Phase 4: Dashboard & Observability (not started)

---

## Contact & Questions

**Implementation Session:** Session 18
**Planned Feature ID:** #63
**Related Feature ID:** #62 (Migration 010 verification)

**Questions to Answer Before Starting:**
1. Has Migration 010 been applied to PostgreSQL? (See related feature #62)
2. Do we have workflows with request_id in the database?
3. Should validation run synchronously or async?

---

**Status:** Ready for implementation
**Next Action:** Verify Migration 010 applied (Feature #62), then begin Step 1
