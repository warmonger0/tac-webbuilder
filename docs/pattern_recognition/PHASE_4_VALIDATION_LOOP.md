# Phase 4: Pattern Validation Loop

## Overview

Phase 4 implements the validation loop that "closes the loop" on pattern learning by comparing predicted patterns against actual workflow outcomes. This feedback mechanism enables the system to continuously improve prediction accuracy and build confidence in automation candidates.

## Architecture

### Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        VALIDATION LOOP                           │
└─────────────────────────────────────────────────────────────────┘

1. Workflow Execution Starts
   └─> [Future Phase 5: Make pattern predictions]
       └─> Store predictions in pattern_predictions table

2. Workflow Execution Completes
   └─> Status changes to 'completed'
       └─> Trigger: _trigger_pattern_validation()

3. Pattern Detection
   └─> detect_patterns_in_workflow(workflow)
       └─> Returns list of actual patterns found

4. Validation
   └─> validate_predictions(workflow_id, actual_patterns)
       ├─> Compare predicted vs actual
       ├─> Calculate accuracy metrics
       └─> Update pattern_predictions.was_correct

5. Accuracy Update
   └─> Update operation_patterns.prediction_accuracy
       └─> Running average of validation results

6. Continuous Improvement
   └─> Higher accuracy patterns = stronger automation candidates
```

## Database Schema

### pattern_predictions Table

Tracks pattern predictions and validation results.

```sql
CREATE TABLE pattern_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Workflow Context
    workflow_id TEXT NOT NULL,
    request_id TEXT,  -- Optional: links to triggering request

    -- Pattern Information
    pattern_id INTEGER NOT NULL,
    pattern_signature TEXT NOT NULL,

    -- Prediction Data
    predicted_at TEXT DEFAULT (datetime('now')),
    predicted_confidence REAL DEFAULT 0.0,  -- 0.0 to 100.0
    prediction_reason TEXT,

    -- Validation Results
    was_correct INTEGER,  -- NULL until validated, 1=correct, 0=incorrect
    validated_at TEXT,
    validation_notes TEXT,

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id),
    FOREIGN KEY (workflow_id) REFERENCES workflow_history(workflow_id),
    UNIQUE(workflow_id, pattern_id)
);
```

### operation_patterns Enhancement

Added `prediction_accuracy` column to track validation performance.

```sql
ALTER TABLE operation_patterns
ADD COLUMN prediction_accuracy REAL DEFAULT NULL;
```

- **NULL**: No validated predictions yet
- **0.0 to 1.0**: Running average of validation correctness

## Validation Metrics

### Accuracy

```
Accuracy = Correct Predictions / Total Predictions
```

**Example:** 8 correct out of 10 predictions = 80% accuracy

### Precision

```
Precision = True Positives / (True Positives + False Positives)
```

**Meaning:** "When we predict a pattern, how often are we correct?"

**Example:** Predicted 10 patterns, 8 were actually present = 80% precision

### Recall

```
Recall = True Positives / (True Positives + False Negatives)
```

**Meaning:** "Of all actual patterns, how many did we predict?"

**Example:** 8 patterns detected, we predicted 6 of them = 75% recall

### F1 Score

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Meaning:** Harmonic mean of precision and recall (balanced metric)

## Code Structure

### core/pattern_validator.py

Main validation service with three core functions:

1. **validate_predictions(workflow_id, actual_patterns, db_connection)**
   - Compares predictions vs actuals
   - Calculates all accuracy metrics
   - Updates pattern_predictions table
   - Returns ValidationResult with details

2. **update_pattern_accuracy(pattern_id, db_connection)**
   - Recalculates running average accuracy
   - Updates operation_patterns.prediction_accuracy
   - Called automatically by database trigger

3. **get_validation_metrics(pattern_id, db_connection)**
   - Fetches validation statistics for a pattern
   - Returns precision, recall, F1, accuracy
   - Used for analysis and reporting

### Integration Points

#### Workflow Completion Hook

In `core/workflow_history_utils/database/mutations.py`:

```python
def update_workflow_history(adw_id: str, **kwargs) -> bool:
    # ... update logic ...

    # Check if status changed to 'completed'
    if 'status' in kwargs and kwargs['status'] == 'completed':
        _trigger_pattern_validation(adw_id, conn)
```

#### Validation Trigger

```python
def _trigger_pattern_validation(adw_id: str, db_connection) -> None:
    # 1. Get workflow data
    # 2. Check for predictions
    # 3. Detect actual patterns
    # 4. Validate predictions
    # 5. Log results
```

## Usage Examples

### Example 1: Perfect Accuracy

**Scenario:** Testing workflow - prediction matches actual

```python
# Prediction made at workflow start (Phase 5)
pattern_id = 42  # test:pytest:backend
workflow_id = "wf-123"
predicted_confidence = 85.0

# Workflow completes
actual_patterns = ["test:pytest:backend"]

# Validation
result = validate_predictions("wf-123", actual_patterns, conn)
# result['accuracy'] = 1.0 (100%)
# result['correct'] = 1
# result['false_positives'] = 0
# result['false_negatives'] = 0
```

### Example 2: Partial Accuracy

**Scenario:** Multiple predictions, some correct, some incorrect

```python
# Predictions
# - test:pytest:backend (confidence: 90)
# - build:typecheck:backend (confidence: 75)
# - format:eslint:all (confidence: 50)

# Actual patterns detected
actual_patterns = ["test:pytest:backend", "build:typecheck:backend"]

# Validation
result = validate_predictions("wf-456", actual_patterns, conn)
# result['accuracy'] = 0.67 (67%)
# result['correct'] = 2
# result['false_positives'] = 1 (format:eslint:all)
# result['false_negatives'] = 0
```

### Example 3: False Negatives

**Scenario:** Missed predictions

```python
# Predictions
# - test:pytest:backend (confidence: 80)

# Actual patterns detected (more than predicted)
actual_patterns = [
    "test:pytest:backend",
    "build:typecheck:backend",  # Not predicted
    "format:eslint:all"          # Not predicted
]

# Validation
result = validate_predictions("wf-789", actual_patterns, conn)
# result['accuracy'] = 1.0 (prediction was correct)
# result['correct'] = 1
# result['false_positives'] = 0
# result['false_negatives'] = 2 (missed patterns)
# result['recall'] = 0.33 (predicted 1 of 3 actual patterns)
```

## Query Functions

### Get Pattern Predictions

```python
from core.workflow_history_utils.database.queries import get_pattern_predictions

predictions = get_pattern_predictions("wf-123")
# Returns: List of all predictions for workflow
```

### Get Pattern Accuracy History

```python
from core.workflow_history_utils.database.queries import get_pattern_accuracy_history

history = get_pattern_accuracy_history(pattern_id=42, limit=50)
# Returns: Recent validation results for pattern
```

### Get Reliable Patterns

```python
from core.workflow_history_utils.database.queries import get_reliable_patterns

reliable = get_reliable_patterns(
    min_accuracy=0.70,  # 70% accuracy threshold
    min_occurrences=5,  # At least 5 occurrences
    limit=20
)
# Returns: Top 20 most reliable patterns for automation
```

### Get Validation Summary

```python
from core.pattern_validator import get_validation_summary

summary = get_validation_summary(conn)
# {
#     'total_patterns': 15,
#     'patterns_with_predictions': 10,
#     'total_predictions': 100,
#     'total_validations': 85,
#     'overall_accuracy': 0.75,
#     'patterns_above_70_percent': 8,
#     'patterns_above_90_percent': 3
# }
```

## SQL Query Examples

### Find High-Accuracy Patterns

```sql
SELECT
    pattern_signature,
    pattern_type,
    occurrence_count,
    prediction_accuracy * 100 as accuracy_percent,
    confidence_score
FROM operation_patterns
WHERE prediction_accuracy >= 0.70
AND occurrence_count >= 5
ORDER BY prediction_accuracy DESC, occurrence_count DESC;
```

### Validation Trend Over Time

```sql
SELECT
    DATE(validated_at) as date,
    COUNT(*) as validations,
    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
    AVG(CAST(was_correct AS REAL)) as accuracy
FROM pattern_predictions
WHERE validated_at IS NOT NULL
GROUP BY DATE(validated_at)
ORDER BY date DESC
LIMIT 30;
```

### Pattern Accuracy by Type

```sql
SELECT
    p.pattern_type,
    COUNT(DISTINCT p.id) as pattern_count,
    AVG(p.prediction_accuracy) as avg_accuracy,
    COUNT(pp.id) as total_predictions,
    SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) as correct
FROM operation_patterns p
LEFT JOIN pattern_predictions pp ON pp.pattern_id = p.id
WHERE p.prediction_accuracy IS NOT NULL
GROUP BY p.pattern_type
ORDER BY avg_accuracy DESC;
```

## Benefits of Validation Loop

### 1. Continuous Improvement

- System learns from mistakes
- Accuracy improves over time
- Confidence scores reflect reality

### 2. Safe Automation

- Only automate patterns with high accuracy
- Set threshold (e.g., 90% accuracy) for automation approval
- Reduce risk of incorrect automated actions

### 3. Performance Tracking

- Measure prediction system effectiveness
- Identify patterns that are hard to predict
- Guide future improvements to detection logic

### 4. Transparency

- Clear metrics for pattern reliability
- Audit trail of predictions and validations
- Explainable automation decisions

## Future Enhancements (Not in Phase 4)

### Phase 5: Pattern Prediction
- Actually make predictions at workflow start
- Use historical patterns to predict future operations
- Store predictions in pattern_predictions table

### Phase 6: Automation Candidates
- Confidence threshold for automation
- A/B testing of automated workflows
- Fallback to manual on low confidence

### Phase 7: Advanced Analytics
- Prediction explanations (feature importance)
- Time-based accuracy trends
- Pattern evolution tracking

## Error Handling

### Graceful Degradation

Validation errors never block workflow completion:

```python
try:
    validation_result = validate_predictions(...)
    logger.info(f"Validation succeeded: {validation_result['accuracy']:.2%}")
except Exception as e:
    logger.error(f"Validation failed: {e}", exc_info=True)
    # Workflow completion continues normally
```

### Edge Cases Handled

1. **No predictions exist**: Validation skips gracefully
2. **No actual patterns**: All predictions marked as false positives
3. **Workflow failed**: Validation not triggered (incomplete data)
4. **Database errors**: Logged but don't crash workflow updates

## Testing

### Test Coverage

See `app/server/tests/test_pattern_validator.py`:

- ✅ 100% accuracy scenarios
- ✅ 0% accuracy scenarios
- ✅ Mixed accuracy scenarios
- ✅ No predictions edge case
- ✅ No actual patterns edge case
- ✅ False negatives detection
- ✅ Accuracy metric calculations
- ✅ Database operations

### Running Tests

```bash
cd app/server
uv run pytest tests/test_pattern_validator.py -v
uv run pytest tests/test_pattern_validator.py --cov=core.pattern_validator
```

## Monitoring

### Log Messages

Validation produces structured log messages:

```
[Validator] Workflow wf-123: Predicted 3, Actual 2, Correct 2, Accuracy 66.67%
[Validator] Updated pattern 42 accuracy: 75.00%
[DB] Pattern validation for adw-123: 2/3 correct, accuracy 66.67%
```

### Metrics to Monitor

- Overall validation accuracy trend
- Per-pattern accuracy convergence
- False positive/negative rates
- Validation coverage (% of workflows with predictions)

## Conclusion

Phase 4 establishes the foundation for intelligent pattern-based automation by validating predictions against reality. This feedback loop enables the system to:

1. **Learn continuously** from workflow outcomes
2. **Build confidence** in pattern reliability
3. **Identify safe automation** candidates
4. **Measure effectiveness** of prediction system

The validation loop is the key to moving from pattern detection (Phases 1-3) to pattern prediction and automation (Phases 5+).
