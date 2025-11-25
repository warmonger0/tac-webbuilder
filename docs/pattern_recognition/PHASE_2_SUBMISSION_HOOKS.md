# Phase 2: Submission-Time Pattern Detection

## Overview

Phase 2 implements **submission-time pattern detection**, enabling the system to predict operation patterns (test, build, deploy, fix) from natural language input BEFORE workflow execution begins. This differs from Phase 1's post-workflow pattern detection by providing immediate pattern insights at request submission time.

## Architecture

### Before Phase 2
```
RequestForm → submitRequest() → GitHubIssueService → Create Issue
```

### After Phase 2
```
RequestForm → submitRequest() → GitHubIssueService → Pattern Predictor → Create Issue (with pattern metadata)
                                                              ↓
                                                      Store predicted patterns
                                                              ↓
                                                      Display to user
```

## Components

### 1. Pattern Predictor Module
**File:** `app/server/core/pattern_predictor.py`

The pattern predictor analyzes natural language input using keyword matching to identify operation patterns.

#### Key Functions

**`predict_patterns_from_input(nl_input, project_path) -> List[Dict]`**

Predicts patterns from user input using keyword-based detection.

```python
from core.pattern_predictor import predict_patterns_from_input

predictions = predict_patterns_from_input("Run backend tests with pytest")
# Returns: [{'pattern': 'test:pytest:backend', 'confidence': 0.85, 'reasoning': '...'}]
```

**Supported Patterns:**
- **Test patterns:**
  - `test:pytest:backend` - Backend tests with pytest
  - `test:vitest:frontend` - Frontend tests with vitest
- **Build patterns:**
  - `build:typecheck:backend` - Build and typecheck operations
- **Deploy patterns:**
  - `deploy:production` - Production deployments
- **Fix patterns:**
  - `fix:bug` - Bug fixes and patches

**Confidence Scoring:**
- **0.85**: Explicit framework mention (pytest, vitest)
- **0.75**: Build keywords detected
- **0.70**: Deployment keywords detected
- **0.65**: Implicit pattern detection (backend, frontend)
- **0.60**: Fix/bug keywords detected

**`store_predicted_patterns(request_id, predictions, db_connection)`**

Stores predicted patterns in the database for later validation.

```python
from utils.db_connection import get_connection
from core.pattern_predictor import store_predicted_patterns

predictions = [{'pattern': 'test:pytest:backend', 'confidence': 0.85, 'reasoning': '...'}]

with get_connection() as conn:
    store_predicted_patterns("REQ-123", predictions, conn)
```

### 2. Database Schema

#### pattern_predictions Table
```sql
CREATE TABLE pattern_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    pattern_id INTEGER NOT NULL,

    -- Prediction details
    confidence_score REAL NOT NULL,
    reasoning TEXT,
    predicted_at TEXT DEFAULT (datetime('now')),

    -- Validation (filled after workflow completes)
    was_correct INTEGER,  -- NULL = not validated, 1 = correct, 0 = incorrect
    validated_at TEXT,

    FOREIGN KEY (pattern_id) REFERENCES operation_patterns(id)
);
```

#### operation_patterns Enhancements
```sql
ALTER TABLE operation_patterns ADD COLUMN prediction_count INTEGER DEFAULT 0;
ALTER TABLE operation_patterns ADD COLUMN prediction_accuracy REAL DEFAULT 0.0;
ALTER TABLE operation_patterns ADD COLUMN last_predicted TEXT;
```

### 3. Service Integration

**File:** `app/server/services/github_issue_service.py`

Pattern prediction is integrated into the `_handle_single_phase_request` method:

```python
# Predict patterns from input (Phase 2 feature)
predicted_patterns = []
try:
    predicted_patterns = predict_patterns_from_input(
        nl_input=request.nl_input,
        project_path=request.project_path
    )

    # Store predictions in database if any were detected
    if predicted_patterns:
        with get_connection() as conn:
            store_predicted_patterns(request_id, predicted_patterns, conn)

        logger.info(
            f"[Request {request_id}] Predicted {len(predicted_patterns)} patterns: "
            f"{[p['pattern'] for p in predicted_patterns]}"
        )
except Exception as e:
    # Don't fail request if pattern prediction fails
    logger.error(f"[Request {request_id}] Pattern prediction failed: {e}")
```

**Error Handling:**
- Pattern prediction errors are caught and logged
- Request submission succeeds even if prediction fails
- Ensures graceful degradation

### 4. Frontend Display

**File:** `app/client/src/components/RequestForm.tsx`

The frontend displays predicted patterns in the success message:

```typescript
// Display predicted patterns if any were detected (Phase 2 feature)
if (response.predicted_patterns && response.predicted_patterns.length > 0) {
  const patternNames = response.predicted_patterns.map(p => p.pattern).join(', ');
  setSuccessMessage(
    `Request submitted! Detected patterns: ${patternNames}`
  );
}
```

**Type Definition:**
```typescript
export interface SubmitRequestResponse {
  request_id: string;
  predicted_patterns?: Array<{
    pattern: string;
    confidence: number;
    reasoning: string;
  }>;
}
```

## Algorithm Details

### Keyword Matching Logic

The pattern predictor uses case-insensitive keyword matching:

1. **Normalize input:** Convert to lowercase
2. **Scan for keywords:** Check for operation-specific keywords
3. **Determine target:** Identify backend/frontend/both from context
4. **Calculate confidence:** Based on explicitness of keywords
5. **Generate reasoning:** Explain why pattern was detected

### Example Predictions

**Input:** "Run backend tests with pytest"
```json
[
  {
    "pattern": "test:pytest:backend",
    "confidence": 0.85,
    "reasoning": "Backend test keywords detected"
  }
]
```

**Input:** "Run tests and deploy"
```json
[
  {
    "pattern": "test:pytest:backend",
    "confidence": 0.65,
    "reasoning": "Backend test keywords detected"
  },
  {
    "pattern": "deploy:production",
    "confidence": 0.70,
    "reasoning": "Deployment keywords detected"
  }
]
```

**Input:** "Fix authentication bug"
```json
[
  {
    "pattern": "fix:bug",
    "confidence": 0.60,
    "reasoning": "Bug fix keywords detected"
  }
]
```

## Future Validation Strategy

Phase 2 stores predictions for future validation against actual patterns:

1. **Phase 3:** Compare predicted patterns vs actual patterns from workflow execution
2. **Update validation:**
   ```sql
   UPDATE pattern_predictions
   SET was_correct = 1, validated_at = datetime('now')
   WHERE request_id = ? AND pattern_id = ?
   ```
3. **Calculate accuracy:**
   ```sql
   UPDATE operation_patterns
   SET prediction_accuracy = (
       SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
       FROM pattern_predictions
       WHERE pattern_id = operation_patterns.id
   )
   WHERE id = ?
   ```

## Performance Characteristics

- **Prediction time:** < 100ms (keyword matching is fast)
- **Database storage:** < 50ms (single transaction with batched inserts)
- **Total overhead:** < 150ms added to request submission
- **No external dependencies:** All processing happens locally

## Troubleshooting

### Pattern Not Detected

**Symptom:** Input contains pattern keywords but no pattern predicted

**Solution:**
1. Check keyword spelling in input
2. Verify keywords match those in `pattern_predictor.py`
3. Add new keywords to detection logic if needed

### Database Storage Fails

**Symptom:** Patterns predicted but not stored in database

**Solution:**
1. Check database connection: `sqlite3 db/database.db ".tables"`
2. Verify migration 010 applied: `sqlite3 db/database.db ".schema pattern_predictions"`
3. Check logs for database errors

### Frontend Not Displaying Patterns

**Symptom:** Patterns stored but not shown in UI

**Solution:**
1. Verify response includes `predicted_patterns` field
2. Check browser console for TypeScript errors
3. Verify `SubmitRequestResponse` type is up to date

## Testing

### Unit Tests
**File:** `app/server/tests/test_pattern_predictor.py`

Run unit tests:
```bash
cd app/server
uv run pytest tests/test_pattern_predictor.py -v
```

**Test Coverage:**
- Pattern prediction for all pattern types
- Confidence score calculation
- Empty/ambiguous input handling
- Multiple pattern detection
- Database storage and updates
- Transaction rollback on errors

### E2E Test
**File:** `.claude/commands/e2e/test_pattern_prediction.md`

Run E2E test:
```bash
# Follow instructions in test file
```

**Validates:**
- End-to-end pattern prediction workflow
- UI display of predicted patterns
- Multiple patterns from single input
- No console errors

## Monitoring

### Key Metrics

1. **Prediction Rate:**
   ```sql
   SELECT COUNT(*) FROM pattern_predictions
   WHERE predicted_at > datetime('now', '-1 day')
   ```

2. **Pattern Popularity:**
   ```sql
   SELECT pattern_signature, prediction_count
   FROM operation_patterns
   ORDER BY prediction_count DESC
   LIMIT 10
   ```

3. **Recent Predictions:**
   ```sql
   SELECT pp.request_id, op.pattern_signature, pp.confidence_score, pp.predicted_at
   FROM pattern_predictions pp
   JOIN operation_patterns op ON pp.pattern_id = op.id
   ORDER BY pp.predicted_at DESC
   LIMIT 20
   ```

### Logging

Pattern prediction logs include:
- Request ID for tracing
- Number of patterns predicted
- Pattern names for debugging
- Errors with full context

Example:
```
[Request abc-123] Predicted 2 patterns: ['test:pytest:backend', 'test:vitest:frontend']
```

## Security Considerations

- **SQL Injection Prevention:** All queries use parameterized statements
- **Input Validation:** No user input directly interpolated into SQL
- **Transaction Safety:** Automatic rollback on errors prevents partial state
- **Logging Privacy:** No sensitive user data exposed in logs

## Future Enhancements (Out of Scope)

1. **ML-based Prediction:** Train model on `pattern_predictions` data
2. **Workflow Routing:** Use predictions to select optimal workflow templates
3. **Pattern-based Cost Estimation:** Estimate costs from predicted patterns
4. **User Feedback Loop:** Allow users to correct mispredictions
5. **Prediction Accuracy Dashboard:** Display prediction_accuracy metrics
6. **Pattern Validation:** Automated comparison of predicted vs actual patterns

## References

- **Phase 1 Documentation:** `docs/pattern_recognition/PHASE_1_POST_WORKFLOW_DETECTION.md` (if exists)
- **Pattern Signatures:** `app/server/core/pattern_signatures.py`
- **Database Schema:** `app/server/db/migrations/010_add_pattern_predictions.sql`
- **API Types:** `app/client/src/types/api.types.ts`
