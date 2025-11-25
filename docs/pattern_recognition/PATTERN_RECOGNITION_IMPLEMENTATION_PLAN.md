# Pattern Recognition Implementation Plan
**Project:** End-to-End Pattern Detection & Learning System
**Goal:** Enable real-time pattern tracking from request submission → workflow completion
**Approach:** Phased rollout with verification at each step
**Created:** 2025-11-24
**Status:** Phase 1 Ready to Begin

---

## Architecture Overview

```
Request Form → Pattern Detection (Phase 2) → GitHub Issue → Queue (Phase 3) → Workflow Execution → Pattern Collection (Phase 1) → Database
     ↓                                                                                                           ↓
  nl_input                                                                                              operation_patterns
                                                                                                        pattern_occurrences
```

---

## Phase 1: Verify Existing Post-Workflow Pattern Collection
**Status:** ✅ Already Implemented, Needs Testing
**Effort:** 1-2 hours
**Risk:** Low

### Objectives
- Verify pattern detection works on completed workflows
- Confirm database schema is functional
- Establish baseline for pattern quality

### Tasks

#### 1.1 Database Verification
```sql
-- Check tables exist
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('operation_patterns', 'pattern_occurrences', 'tool_calls');

-- Check for existing patterns
SELECT * FROM operation_patterns LIMIT 10;

-- Check pattern-workflow linkage
SELECT * FROM pattern_occurrences LIMIT 10;
```

**Acceptance Criteria:**
- All 3 tables exist
- Can query without errors

#### 1.2 Manual Pattern Detection Test
Create test script: `app/server/tests/manual/test_existing_pattern_detection.py`

```python
"""
Manual test to verify pattern detection on existing workflows.
Run: cd app/server && uv run python tests/manual/test_existing_pattern_detection.py
"""
import sqlite3
from core.pattern_detector import detect_patterns_in_workflow
from core.pattern_persistence import record_pattern_occurrence

# Connect to database
conn = sqlite3.connect('data/workflow_history.db')

# Get a completed workflow
cursor = conn.cursor()
cursor.execute("""
    SELECT * FROM workflow_history
    WHERE status = 'completed'
    AND nl_input IS NOT NULL
    LIMIT 1
""")

workflow = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))

# Detect patterns
patterns = detect_patterns_in_workflow(workflow)
print(f"✅ Detected {len(patterns)} patterns:")
for p in patterns:
    print(f"  - {p}")

# Record patterns
for pattern in patterns:
    pattern_id, is_new = record_pattern_occurrence(pattern, workflow, conn)
    status = "NEW" if is_new else "EXISTING"
    print(f"  [{status}] Pattern ID: {pattern_id}")

conn.commit()
conn.close()
```

**Acceptance Criteria:**
- Script detects at least 1 pattern from completed workflow
- Patterns are saved to database
- Re-running script shows patterns as "EXISTING"

#### 1.3 Query Pattern Statistics
Create query script: `app/server/tests/manual/query_pattern_stats.py`

```python
"""
Query and display pattern statistics.
"""
import sqlite3
import json

conn = sqlite3.connect('data/workflow_history.db')
cursor = conn.cursor()

# Get top 10 patterns by occurrence
cursor.execute("""
    SELECT
        pattern_signature,
        pattern_type,
        occurrence_count,
        automation_status,
        confidence_score
    FROM operation_patterns
    ORDER BY occurrence_count DESC
    LIMIT 10
""")

print("\n📊 Top 10 Patterns:\n")
for row in cursor.fetchall():
    sig, type_, count, status, confidence = row
    print(f"{sig:40} | Count: {count:3} | Status: {status:15} | Confidence: {confidence:.2f}")

# Get pattern characteristics
cursor.execute("""
    SELECT pattern_signature, characteristics
    FROM operation_patterns
    WHERE characteristics IS NOT NULL
    LIMIT 3
""")

print("\n🔍 Sample Pattern Characteristics:\n")
for sig, chars in cursor.fetchall():
    print(f"Pattern: {sig}")
    print(f"  {json.loads(chars)}\n")

conn.close()
```

**Acceptance Criteria:**
- Can see patterns ranked by occurrence
- Characteristics JSON is valid and meaningful

### Deliverables
- ✅ Verified database schema functional
- ✅ Manual test script demonstrates pattern detection works
- ✅ Query script shows pattern statistics
- 📄 Document findings in `docs/pattern_recognition/PHASE_1_VERIFICATION.md`

### Success Metrics
- At least 1 pattern detected from test workflow
- Pattern persists across multiple runs
- Characteristics include duration, cost, tool usage

---

## Phase 2: Add Submission-Time Pattern Detection
**Status:** 🔨 To Be Implemented
**Effort:** 3-4 hours
**Risk:** Medium (requires service modification)

### Objectives
- Detect patterns during request submission (before workflow starts)
- Store "predicted patterns" for later validation
- Enable pattern-based workflow routing

### Architecture Change

**Before:**
```
RequestForm → submitRequest() → GitHubIssueService → Create Issue
```

**After:**
```
RequestForm → submitRequest() → GitHubIssueService → Pattern Detector → Create Issue (with pattern metadata)
                                                              ↓
                                                      Store predicted patterns
```

### Tasks

#### 2.1 Create Lightweight Pattern Predictor
New file: `app/server/core/pattern_predictor.py`

```python
"""
Pattern Predictor - Predicts patterns from nl_input before workflow execution.

Differs from pattern_detector.py which analyzes completed workflows.
This module predicts patterns from user input alone.
"""
import logging
from typing import List, Dict
from .pattern_signatures import extract_operation_signature

logger = logging.getLogger(__name__)

def predict_patterns_from_input(
    nl_input: str,
    project_path: str | None = None
) -> List[Dict[str, any]]:
    """
    Predict patterns from natural language input before workflow starts.

    Args:
        nl_input: User's natural language request
        project_path: Optional project context

    Returns:
        List of predicted patterns with confidence scores

    Example:
        >>> predict_patterns_from_input("Run backend tests with pytest")
        [{'pattern': 'test:pytest:backend', 'confidence': 0.85, 'reasoning': 'explicit pytest mention'}]
    """
    predictions = []
    nl_lower = nl_input.lower()

    # Test patterns
    if any(kw in nl_lower for kw in ['test', 'pytest', 'vitest']):
        if 'pytest' in nl_lower or 'backend' in nl_lower or 'api' in nl_lower:
            predictions.append({
                'pattern': 'test:pytest:backend',
                'confidence': 0.85 if 'pytest' in nl_lower else 0.65,
                'reasoning': 'Backend test keywords detected'
            })
        if 'vitest' in nl_lower or 'frontend' in nl_lower or 'ui' in nl_lower or 'component' in nl_lower:
            predictions.append({
                'pattern': 'test:vitest:frontend',
                'confidence': 0.85 if 'vitest' in nl_lower else 0.65,
                'reasoning': 'Frontend test keywords detected'
            })

    # Build patterns
    if any(kw in nl_lower for kw in ['build', 'compile', 'typecheck', 'tsc']):
        predictions.append({
            'pattern': 'build:typecheck:backend',
            'confidence': 0.75,
            'reasoning': 'Build operation keywords detected'
        })

    # Deploy patterns
    if any(kw in nl_lower for kw in ['deploy', 'ship', 'release', 'publish']):
        predictions.append({
            'pattern': 'deploy:production',
            'confidence': 0.70,
            'reasoning': 'Deployment keywords detected'
        })

    # Fix/patch patterns
    if any(kw in nl_lower for kw in ['fix', 'bug', 'patch', 'hotfix']):
        predictions.append({
            'pattern': 'fix:bug',
            'confidence': 0.60,
            'reasoning': 'Bug fix keywords detected'
        })

    logger.info(f"[Predictor] Predicted {len(predictions)} patterns from input")
    for pred in predictions:
        logger.debug(f"  - {pred['pattern']} (confidence: {pred['confidence']:.2f})")

    return predictions


def store_predicted_patterns(
    request_id: str,
    predictions: List[Dict],
    db_connection
) -> None:
    """
    Store predicted patterns for later validation.

    Creates entries in operation_patterns with 'predicted' status.
    After workflow completes, we can compare predicted vs actual.
    """
    cursor = db_connection.cursor()

    for pred in predictions:
        # Check if pattern exists
        cursor.execute(
            "SELECT id FROM operation_patterns WHERE pattern_signature = ?",
            (pred['pattern'],)
        )
        result = cursor.fetchone()

        if result:
            pattern_id = result[0]
            # Update prediction count
            cursor.execute(
                """
                UPDATE operation_patterns
                SET prediction_count = prediction_count + 1,
                    last_predicted = datetime('now')
                WHERE id = ?
                """,
                (pattern_id,)
            )
        else:
            # Create new predicted pattern
            cursor.execute(
                """
                INSERT INTO operation_patterns (
                    pattern_signature,
                    pattern_type,
                    automation_status,
                    prediction_count,
                    last_predicted
                ) VALUES (?, ?, 'predicted', 1, datetime('now'))
                """,
                (pred['pattern'], pred['pattern'].split(':')[0])
            )
            pattern_id = cursor.lastrowid

        # Store prediction metadata
        cursor.execute(
            """
            INSERT INTO pattern_predictions (
                request_id,
                pattern_id,
                confidence_score,
                reasoning
            ) VALUES (?, ?, ?, ?)
            """,
            (request_id, pattern_id, pred['confidence'], pred['reasoning'])
        )

    db_connection.commit()
    logger.info(f"[Predictor] Stored {len(predictions)} predicted patterns for request {request_id}")
```

**Acceptance Criteria:**
- `predict_patterns_from_input()` returns patterns with confidence scores
- Common patterns (test, build, deploy) are detected
- Patterns stored with 'predicted' status

#### 2.2 Add Pattern Predictions Table
New migration: `app/server/db/migrations/006_add_pattern_predictions.sql`

```sql
-- Migration 006: Add pattern predictions tracking
-- Stores predicted patterns before workflow execution for validation

CREATE TABLE IF NOT EXISTS pattern_predictions (
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

CREATE INDEX IF NOT EXISTS idx_pattern_predictions_request ON pattern_predictions(request_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_pattern ON pattern_predictions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_predictions_validated ON pattern_predictions(was_correct);

-- Add prediction tracking to operation_patterns
ALTER TABLE operation_patterns ADD COLUMN prediction_count INTEGER DEFAULT 0;
ALTER TABLE operation_patterns ADD COLUMN prediction_accuracy REAL DEFAULT 0.0;
ALTER TABLE operation_patterns ADD COLUMN last_predicted TEXT;
```

#### 2.3 Integrate into GitHubIssueService
Modify: `app/server/services/github_issue_service.py`

```python
# Add imports
from core.pattern_predictor import predict_patterns_from_input, store_predicted_patterns

class GitHubIssueService:
    async def submit_nl_request(self, request: SubmitRequestData) -> SubmitRequestResponse:
        """Process natural language request and generate GitHub issue preview WITH cost estimate"""

        # ... existing validation ...

        # NEW: Predict patterns from input
        try:
            predicted_patterns = predict_patterns_from_input(
                nl_input=request.nl_input,
                project_path=request.project_path
            )

            # Store predictions linked to request_id
            if predicted_patterns:
                store_predicted_patterns(
                    request_id=request_id,
                    predictions=predicted_patterns,
                    db_connection=self.db_connection
                )

                logger.info(
                    f"[Request {request_id}] Predicted {len(predicted_patterns)} patterns: "
                    f"{[p['pattern'] for p in predicted_patterns]}"
                )
        except Exception as e:
            # Don't fail request if pattern prediction fails
            logger.error(f"[Request {request_id}] Pattern prediction failed: {e}")

        # ... rest of existing code ...

        return SubmitRequestResponse(
            request_id=request_id,
            message=f"Request processed. Predicted patterns: {[p['pattern'] for p in predicted_patterns]}" if predicted_patterns else "Request processed",
            issue_preview=preview,
            cost_estimate=cost_estimate
        )
```

**Acceptance Criteria:**
- Request submission predicts patterns
- Patterns stored with request_id linkage
- Submission doesn't fail if pattern prediction errors

#### 2.4 Add Pattern Info to Response
Update: `app/client/src/types.ts`

```typescript
export interface SubmitRequestResponse {
  request_id: string;
  message: string;
  issue_preview?: GitHubIssue;
  cost_estimate?: CostEstimate;
  predicted_patterns?: Array<{  // NEW
    pattern: string;
    confidence: number;
    reasoning: string;
  }>;
}
```

Update: `app/client/src/components/RequestForm.tsx`

```typescript
// After successful submission, show predicted patterns
if (response.predicted_patterns && response.predicted_patterns.length > 0) {
  setSuccessMessage(
    `✅ Request submitted! Detected patterns: ${response.predicted_patterns.map(p => p.pattern).join(', ')}`
  );
}
```

**Acceptance Criteria:**
- UI shows predicted patterns after submission
- User gets feedback on what system detected

### Deliverables
- ✅ `pattern_predictor.py` with prediction logic
- ✅ Migration 006 with predictions table
- ✅ GitHubIssueService integration
- ✅ Frontend displays predicted patterns
- 📄 Document in `docs/pattern_recognition/PHASE_2_SUBMISSION_HOOKS.md`

### Success Metrics
- 80%+ of test/build requests predict correct pattern
- Predictions stored in <100ms
- No request failures due to pattern system

---

## Phase 3: Integrate with Queue System
**Status:** 🔜 After Phase 2
**Effort:** 2-3 hours
**Risk:** Low (additive only)

### Objectives
- Pass pattern predictions to queue
- Display patterns in ZteHopperQueueCard
- Enable pattern-based prioritization (future)

### Tasks

#### 3.1 Add Patterns to Phase Queue Data
Modify: `app/server/services/phase_queue_service.py`

```python
def enqueue(
    self,
    parent_issue: int,
    phase_number: int,
    phase_data: dict,
    depends_on_phase: int | None = None,
    predicted_patterns: list[str] | None = None  # NEW
) -> str:
    """Enqueue a new phase with optional predicted patterns."""

    queue_id = f"{parent_issue}-{phase_number}-{uuid.uuid4().hex[:8]}"

    # Add patterns to phase_data
    if predicted_patterns:
        phase_data['predicted_patterns'] = predicted_patterns

    # ... rest of existing code ...
```

#### 3.2 Display Patterns in Queue UI
Modify: `app/client/src/components/ZteHopperQueueCard.tsx`

```typescript
// Add pattern badges to each queued phase
{phase.phase_data?.predicted_patterns && (
  <div className="flex gap-1 mt-2 flex-wrap">
    {phase.phase_data.predicted_patterns.map((pattern, idx) => (
      <span
        key={idx}
        className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-xs rounded-md border border-emerald-500/30"
      >
        {pattern}
      </span>
    ))}
  </div>
)}
```

**Acceptance Criteria:**
- Queue items show predicted patterns
- Patterns display as badges/chips
- No visual clutter for items without patterns

### Deliverables
- ✅ Queue service stores patterns
- ✅ UI displays patterns in queue
- 📄 Document in `docs/pattern_recognition/PHASE_3_QUEUE_INTEGRATION.md`

---

## Phase 4: Close the Loop - Validate Predictions
**Status:** 🔜 After Phase 3
**Effort:** 2-3 hours
**Risk:** Low

### Objectives
- Compare predicted vs actual patterns after workflow completes
- Calculate prediction accuracy
- Improve prediction model based on errors

### Tasks

#### 4.1 Create Validation Service
New file: `app/server/core/pattern_validator.py`

```python
"""
Pattern Validator - Compares predicted vs actual patterns after workflow completion.
"""
import logging
import sqlite3

logger = logging.getLogger(__name__)

def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: list[str],
    db_connection: sqlite3.Connection
) -> dict:
    """
    Compare predicted patterns against actual patterns from completed workflow.

    Args:
        request_id: Original request ID with predictions
        workflow_id: Completed workflow ID
        actual_patterns: Patterns detected from completed workflow
        db_connection: Database connection

    Returns:
        Validation results with accuracy metrics
    """
    cursor = db_connection.cursor()

    # Get predictions for this request
    cursor.execute("""
        SELECT pp.id, pp.pattern_id, op.pattern_signature, pp.confidence_score
        FROM pattern_predictions pp
        JOIN operation_patterns op ON pp.pattern_id = op.id
        WHERE pp.request_id = ?
    """, (request_id,))

    predictions = cursor.fetchall()

    results = {
        'total_predicted': len(predictions),
        'total_actual': len(actual_patterns),
        'correct': 0,
        'false_positives': 0,
        'false_negatives': 0,
        'details': []
    }

    predicted_patterns = [p[2] for p in predictions]

    # Check each prediction
    for pred_id, pattern_id, pattern_sig, confidence in predictions:
        was_correct = pattern_sig in actual_patterns

        # Update prediction record
        cursor.execute("""
            UPDATE pattern_predictions
            SET was_correct = ?, validated_at = datetime('now')
            WHERE id = ?
        """, (1 if was_correct else 0, pred_id))

        results['details'].append({
            'pattern': pattern_sig,
            'predicted_confidence': confidence,
            'was_correct': was_correct
        })

        if was_correct:
            results['correct'] += 1
        else:
            results['false_positives'] += 1

    # Check for false negatives (actual patterns we didn't predict)
    for actual in actual_patterns:
        if actual not in predicted_patterns:
            results['false_negatives'] += 1
            results['details'].append({
                'pattern': actual,
                'predicted_confidence': 0.0,
                'was_correct': False
            })

    # Calculate accuracy
    if results['total_predicted'] > 0:
        accuracy = results['correct'] / results['total_predicted']

        # Update pattern accuracy metrics
        for pred_id, pattern_id, _, _ in predictions:
            cursor.execute("""
                UPDATE operation_patterns
                SET prediction_accuracy = (
                    SELECT AVG(CAST(was_correct AS REAL))
                    FROM pattern_predictions
                    WHERE pattern_id = ? AND was_correct IS NOT NULL
                )
                WHERE id = ?
            """, (pattern_id, pattern_id))

    db_connection.commit()

    logger.info(
        f"[Validator] Request {request_id}: "
        f"Predicted {results['total_predicted']}, "
        f"Actual {results['total_actual']}, "
        f"Correct {results['correct']}"
    )

    return results
```

#### 4.2 Trigger Validation After Workflow Completion
Modify: `app/server/core/workflow_history_utils/database/mutations.py`

```python
# Add import
from core.pattern_validator import validate_predictions

def record_workflow_completion(...):
    # ... existing completion logic ...

    # NEW: Validate pattern predictions if this workflow was triggered by a request
    if workflow.get('request_id'):
        try:
            actual_patterns = detect_patterns_in_workflow(workflow)
            validation_results = validate_predictions(
                request_id=workflow['request_id'],
                workflow_id=workflow['workflow_id'],
                actual_patterns=actual_patterns,
                db_connection=db_connection
            )

            logger.info(
                f"[Workflow {workflow['workflow_id']}] Pattern validation: "
                f"{validation_results['correct']}/{validation_results['total_predicted']} correct"
            )
        except Exception as e:
            logger.error(f"Pattern validation failed: {e}")
```

### Deliverables
- ✅ Validation service compares predictions vs actuals
- ✅ Accuracy metrics stored per pattern
- ✅ Validation triggered automatically on completion
- 📄 Document in `docs/pattern_recognition/PHASE_4_VALIDATION_LOOP.md`

---

## Phase 5: Observability & Dashboard
**Status:** 🔜 Final Phase
**Effort:** 2-3 hours
**Risk:** Low (UI only)

### Objectives
- Visualize pattern learning progress
- Show prediction accuracy over time
- Enable pattern-based insights

### Tasks

#### 5.1 Pattern Statistics Endpoint
New route: `app/server/routes/pattern_routes.py`

```python
@router.get("/api/patterns/stats")
async def get_pattern_stats():
    """Get pattern learning statistics."""
    cursor = db_connection.cursor()

    stats = {
        'total_patterns': 0,
        'automated_patterns': 0,
        'avg_accuracy': 0.0,
        'top_patterns': [],
        'recent_discoveries': []
    }

    # Total patterns
    cursor.execute("SELECT COUNT(*) FROM operation_patterns")
    stats['total_patterns'] = cursor.fetchone()[0]

    # Automated patterns
    cursor.execute("SELECT COUNT(*) FROM operation_patterns WHERE automation_status = 'automated'")
    stats['automated_patterns'] = cursor.fetchone()[0]

    # Average accuracy
    cursor.execute("SELECT AVG(prediction_accuracy) FROM operation_patterns WHERE prediction_count > 0")
    result = cursor.fetchone()
    stats['avg_accuracy'] = result[0] if result[0] else 0.0

    # Top patterns
    cursor.execute("""
        SELECT pattern_signature, occurrence_count, prediction_accuracy
        FROM operation_patterns
        ORDER BY occurrence_count DESC
        LIMIT 10
    """)
    stats['top_patterns'] = [
        {'pattern': row[0], 'count': row[1], 'accuracy': row[2]}
        for row in cursor.fetchall()
    ]

    # Recent discoveries
    cursor.execute("""
        SELECT pattern_signature, first_detected
        FROM operation_patterns
        ORDER BY first_detected DESC
        LIMIT 5
    """)
    stats['recent_discoveries'] = [
        {'pattern': row[0], 'discovered': row[1]}
        for row in cursor.fetchall()
    ]

    return stats
```

#### 5.2 Pattern Learning Panel
New component: `app/client/src/components/PatternLearningPanel.tsx`

```typescript
export function PatternLearningPanel() {
  const { data: stats } = useQuery({
    queryKey: ['pattern-stats'],
    queryFn: () => fetch('/api/patterns/stats').then(r => r.json()),
    refetchInterval: 30000
  });

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg border border-slate-700 p-4">
      <h2 className="text-lg font-bold text-white mb-4">📊 Pattern Learning</h2>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <StatCard label="Total Patterns" value={stats?.total_patterns || 0} />
        <StatCard label="Automated" value={stats?.automated_patterns || 0} />
        <StatCard label="Avg Accuracy" value={`${((stats?.avg_accuracy || 0) * 100).toFixed(1)}%`} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Top Patterns</h3>
        {stats?.top_patterns?.map(p => (
          <div key={p.pattern} className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{p.pattern}</span>
            <span>{p.count} uses · {(p.accuracy * 100).toFixed(0)}% accuracy</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Deliverables
- ✅ Pattern statistics API endpoint
- ✅ Pattern learning dashboard panel
- ✅ Real-time accuracy metrics
- 📄 Document in `docs/pattern_recognition/PHASE_5_OBSERVABILITY.md`

---

## Testing Strategy

### Unit Tests
```bash
# Phase 1
pytest tests/test_pattern_detector.py
pytest tests/test_pattern_persistence.py

# Phase 2
pytest tests/test_pattern_predictor.py

# Phase 4
pytest tests/test_pattern_validator.py
```

### Integration Tests
```bash
# End-to-end pattern flow
pytest tests/integration/test_pattern_flow_e2e.py
```

### Manual Testing Checklist
```
Phase 1:
□ Run manual test scripts
□ Verify patterns in database
□ Check pattern characteristics

Phase 2:
□ Submit request through UI
□ Verify patterns shown in success message
□ Check patterns stored with request_id

Phase 3:
□ Submit multi-phase request
□ Verify patterns show in queue
□ Check pattern badges render correctly

Phase 4:
□ Complete a workflow
□ Verify predictions validated
□ Check accuracy metrics updated

Phase 5:
□ View pattern dashboard
□ Verify stats accurate
□ Check real-time updates work
```

---

## Rollback Plan

Each phase is independent and additive:

- **Phase 1:** No changes, only verification
- **Phase 2:** Remove pattern prediction from `GitHubIssueService.submit_nl_request()`
- **Phase 3:** Remove pattern display from queue UI
- **Phase 4:** Disable validation hook
- **Phase 5:** Hide dashboard panel

No data loss - all pattern tables preserve historical data.

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Can detect patterns from existing workflows
- ✅ Patterns persist in database
- ✅ Query scripts show meaningful data

### Phase 2 Complete When:
- ✅ New requests predict patterns
- ✅ Predictions stored with >90% success rate
- ✅ UI shows predicted patterns

### Phase 3 Complete When:
- ✅ Queue items display patterns
- ✅ Patterns visible without clutter

### Phase 4 Complete When:
- ✅ Predictions validated on completion
- ✅ Accuracy >70% for common patterns
- ✅ Metrics update correctly

### Phase 5 Complete When:
- ✅ Dashboard displays all stats
- ✅ Real-time updates work
- ✅ User can see learning progress

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 1-2 hours | None |
| Phase 2 | 3-4 hours | Phase 1 complete |
| Phase 3 | 2-3 hours | Phase 2 complete |
| Phase 4 | 2-3 hours | Phase 3 complete |
| Phase 5 | 2-3 hours | Phase 4 complete |
| **Total** | **10-15 hours** | Sequential |

Can be completed over 2-3 work sessions.

---

## Current Infrastructure (Already Implemented)

### Database Schema ✅
- `operation_patterns` - Pattern definitions and statistics
- `pattern_occurrences` - Links patterns to workflows
- `tool_calls` - Tracks tool usage for optimization

### Core Modules ✅
- `pattern_detector.py` - Analyzes completed workflows
- `pattern_persistence.py` - Stores patterns to database
- `pattern_signatures.py` - Extracts operation signatures
- Tests: `test_pattern_detector.py`, `test_pattern_persistence.py`

### What It Detects ✅
- Test operations (pytest, vitest)
- Build operations (typecheck, tsc)
- Duration, cost, success rate metrics
- Multi-level extraction from nl_input, errors, templates

---

## Next Steps

**To begin Phase 1 NOW:**

1. Navigate to project root
2. Run database verification:
   ```bash
   sqlite3 app/server/data/workflow_history.db "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('operation_patterns', 'pattern_occurrences');"
   ```
3. Create manual test directory:
   ```bash
   mkdir -p app/server/tests/manual
   ```
4. Create and run test scripts (provided in Phase 1 tasks)
5. Document findings in `docs/pattern_recognition/PHASE_1_VERIFICATION.md`

---

## Contact & Questions

For questions or clarifications about this implementation plan:
- Review existing pattern detection code in `app/server/core/pattern_*.py`
- Check test files for usage examples
- Refer to migration `004_add_observability_and_pattern_learning.sql` for schema details

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-11-24
**Next Review:** After Phase 1 completion
