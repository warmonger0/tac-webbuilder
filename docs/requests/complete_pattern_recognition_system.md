# Complete Pattern Recognition System (Phases 1-4)

**Project:** End-to-End Pattern Detection & Learning System
**Type:** Multi-Phase Feature Implementation
**Priority:** Normal (50)
**Estimated Total Effort:** 8-12 hours across 4 phases
**Source Plan:** `docs/pattern_recognition/PATTERN_RECOGNITION_IMPLEMENTATION_PLAN.md`

**Note:** These phases are numbered 1-4 for the multi-phase submission system. They correspond to original Phases 2-5 from the implementation plan (original Phase 1 is already complete).

---

## Context

**What's Already Done (Original Phase 1):**
- ✅ **Pattern detection infrastructure** verified and working
  - Migration 004 applied (observability + pattern learning tables)
  - Pattern detection from completed workflows functional
  - Test scripts created and documented
  - Verification doc: `docs/pattern_recognition/PHASE_1_VERIFICATION.md`

**What's Partially Done (This Phase 1 = Original Phase 2):**
- ⚠️ **Submission-time pattern detection:** Code written but migration not applied
  - `app/server/core/pattern_predictor.py` exists ✅
  - Integration in `github_issue_service.py` complete ✅
  - Migration 010 file created but NOT applied ❌
  - `pattern_predictions` table doesn't exist in DB ❌
  - Frontend UI updates missing ❌

**What Needs Implementation:**
- ❌ **Phase 1:** Complete Submission-Time Pattern Detection (was Phase 2)
- ❌ **Phase 2:** Integrate with Queue System (was Phase 3)
- ❌ **Phase 3:** Close the Loop - Validate Predictions (was Phase 4)
- ❌ **Phase 4:** Observability & Dashboard (was Phase 5)

---

## Phase 1: Complete Submission-Time Pattern Detection

**Effort:** 1-2 hours
**Status:** 80% complete, needs migration + verification

### Objectives
- Apply migration 010 to create `pattern_predictions` table
- Verify pattern prediction works at submission time
- Add frontend UI to display predicted patterns
- **Add comprehensive logging for pattern detection pipeline**
- Create verification documentation

### Logging Requirements (All Phases)

**Note:** Logging infrastructure applies across ALL phases (1-4). Set up once in Phase 1, use throughout.

**Logging Standard:** Structured logging with consistent format across all pattern recognition components

#### Log Format
```python
import logging
import json
from datetime import datetime

# Configure structured logger
logger = logging.getLogger('pattern_recognition')

# Log entry format
def log_pattern_event(event_type: str, data: dict, level=logging.INFO):
    """
    Structured logging for pattern recognition events.

    Args:
        event_type: Type of event (prediction, validation, detection, etc.)
        data: Event-specific data dictionary
        level: Log level (INFO, WARNING, ERROR)
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'component': 'pattern_recognition',
        'event_type': event_type,
        **data
    }
    logger.log(level, json.dumps(log_entry))
```

#### Phase 1 Logging Points

**1A. Pattern Prediction Start**
```python
log_pattern_event('prediction_start', {
    'request_id': request_id,
    'nl_input_length': len(nl_input),
    'nl_input_preview': nl_input[:100]
})
```

**1B. Pattern Prediction Results**
```python
log_pattern_event('prediction_complete', {
    'request_id': request_id,
    'patterns_predicted': len(predictions),
    'patterns': [p['pattern'] for p in predictions],
    'confidence_scores': [p['confidence'] for p in predictions],
    'prediction_time_ms': (end_time - start_time) * 1000
})
```

**1C. Pattern Storage**
```python
log_pattern_event('patterns_stored', {
    'request_id': request_id,
    'patterns_count': len(predictions),
    'db_write_time_ms': write_duration,
    'new_patterns_created': new_count,
    'existing_patterns_updated': existing_count
})
```

**1D. Prediction Errors**
```python
log_pattern_event('prediction_error', {
    'request_id': request_id,
    'error_type': type(e).__name__,
    'error_message': str(e),
    'nl_input': nl_input,
    'stack_trace': traceback.format_exc()
}, level=logging.ERROR)
```

#### Phase 2 Logging Points

**2A. Queue Pattern Attachment**
```python
log_pattern_event('queue_pattern_attach', {
    'queue_id': queue_id,
    'parent_issue': parent_issue,
    'phase_number': phase_number,
    'patterns_attached': patterns
})
```

**2B. Queue State Transitions with Patterns**
```python
log_pattern_event('queue_state_transition', {
    'queue_id': queue_id,
    'from_state': old_status,
    'to_state': new_status,
    'patterns': phase_data.get('predicted_patterns', [])
})
```

#### Phase 3 Logging Points

**3A. Validation Start**
```python
log_pattern_event('validation_start', {
    'request_id': request_id,
    'workflow_id': workflow_id,
    'actual_patterns_detected': len(actual_patterns)
})
```

**3B. Validation Results**
```python
log_pattern_event('validation_complete', {
    'request_id': request_id,
    'workflow_id': workflow_id,
    'accuracy': results['accuracy'],
    'correct_predictions': results['correct'],
    'false_positives': results['false_positives'],
    'false_negatives': results['false_negatives'],
    'validation_details': results['details']
})
```

**3C. Accuracy Updates**
```python
log_pattern_event('accuracy_updated', {
    'pattern_signature': pattern_sig,
    'old_accuracy': old_accuracy,
    'new_accuracy': new_accuracy,
    'total_validations': validation_count
})
```

**3D. Validation Errors**
```python
log_pattern_event('validation_error', {
    'request_id': request_id,
    'workflow_id': workflow_id,
    'error_type': type(e).__name__,
    'error_message': str(e)
}, level=logging.ERROR)
```

#### Phase 4 Logging Points

**4A. Analytics Query**
```python
log_pattern_event('analytics_query', {
    'endpoint': '/api/patterns/analytics',
    'query_time_ms': query_duration,
    'total_patterns': stats.total_patterns,
    'total_predictions': stats.total_predictions
})
```

**4B. Dashboard Access**
```python
log_pattern_event('dashboard_access', {
    'user_agent': request.headers.get('User-Agent'),
    'patterns_displayed': len(high_value_candidates)
})
```

### Diagnostic Logging Helpers

Create: `app/server/core/pattern_logging.py`

```python
"""
Pattern Recognition Logging Utilities

Provides consistent, structured logging for pattern detection pipeline.
"""
import logging
import json
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger('pattern_recognition')

def log_pattern_event(event_type: str, data: dict, level=logging.INFO):
    """Log structured pattern recognition event."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'component': 'pattern_recognition',
        'event_type': event_type,
        **data
    }
    logger.log(level, json.dumps(log_entry))


def log_pattern_performance(func: Callable) -> Callable:
    """
    Decorator to log performance metrics for pattern operations.

    Usage:
        @log_pattern_performance
        def predict_patterns_from_input(nl_input: str) -> list:
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__

        log_pattern_event('function_start', {
            'function': function_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        })

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            log_pattern_event('function_complete', {
                'function': function_name,
                'duration_ms': duration_ms,
                'result_type': type(result).__name__,
                'result_length': len(result) if hasattr(result, '__len__') else None
            })

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            log_pattern_event('function_error', {
                'function': function_name,
                'duration_ms': duration_ms,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }, level=logging.ERROR)

            raise

    return wrapper


class PatternOperationContext:
    """
    Context manager for pattern operations with automatic logging.

    Usage:
        with PatternOperationContext('prediction', request_id='req-123') as ctx:
            predictions = predict_patterns(nl_input)
            ctx.set_result(predictions)
    """
    def __init__(self, operation_type: str, **metadata):
        self.operation_type = operation_type
        self.metadata = metadata
        self.start_time = None
        self.result_data = {}

    def __enter__(self):
        self.start_time = time.time()
        log_pattern_event(f'{self.operation_type}_start', self.metadata)
        return self

    def set_result(self, **result_data):
        """Set result data to be logged on exit."""
        self.result_data.update(result_data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type is None:
            log_pattern_event(f'{self.operation_type}_complete', {
                **self.metadata,
                **self.result_data,
                'duration_ms': duration_ms
            })
        else:
            log_pattern_event(f'{self.operation_type}_error', {
                **self.metadata,
                'duration_ms': duration_ms,
                'error_type': exc_type.__name__,
                'error_message': str(exc_val)
            }, level=logging.ERROR)

        return False  # Don't suppress exceptions


# Example usage in pattern_predictor.py
@log_pattern_performance
def predict_patterns_from_input(nl_input: str, project_path: str | None = None) -> list[dict[str, Any]]:
    """Predict patterns with automatic performance logging."""
    with PatternOperationContext('pattern_keyword_analysis',
                                   nl_input_length=len(nl_input)) as ctx:
        predictions = []
        nl_lower = nl_input.lower()

        # Test patterns
        if any(kw in nl_lower for kw in ['test', 'pytest', 'vitest']):
            # ... prediction logic ...

        ctx.set_result(patterns_found=len(predictions))

    return predictions
```

### Log Aggregation & Analysis

Create: `app/server/tests/manual/analyze_pattern_logs.py`

```python
"""
Analyze pattern recognition logs for diagnostics and insights.

Run: cd app/server && uv run python tests/manual/analyze_pattern_logs.py
"""
import json
import sys
from collections import defaultdict, Counter
from datetime import datetime

def analyze_pattern_logs(log_file: str = 'logs/pattern_recognition.log'):
    """Analyze pattern recognition logs."""

    events = []

    # Read log file
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Extract JSON from log line (skip timestamp prefix)
                    json_start = line.find('{')
                    if json_start >= 0:
                        event = json.loads(line[json_start:])
                        events.append(event)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file}")
        return

    print(f"\n📊 Pattern Recognition Log Analysis")
    print(f"   Log file: {log_file}")
    print(f"   Total events: {len(events)}\n")

    # Event type distribution
    event_types = Counter(e['event_type'] for e in events)
    print("🔍 Event Distribution:")
    for event_type, count in event_types.most_common():
        print(f"   {event_type:30} {count:5} events")

    # Prediction accuracy over time
    validations = [e for e in events if e['event_type'] == 'validation_complete']
    if validations:
        print(f"\n✅ Validation Summary:")
        print(f"   Total validations: {len(validations)}")
        avg_accuracy = sum(v['accuracy'] for v in validations) / len(validations)
        print(f"   Average accuracy: {avg_accuracy:.1%}")

        correct = sum(v['correct_predictions'] for v in validations)
        total = sum(v['correct_predictions'] + v['false_positives'] for v in validations)
        print(f"   Overall: {correct}/{total} predictions correct")

    # Performance metrics
    timed_events = [e for e in events if 'duration_ms' in e]
    if timed_events:
        print(f"\n⚡ Performance Metrics:")
        by_operation = defaultdict(list)
        for e in timed_events:
            by_operation[e['event_type']].append(e['duration_ms'])

        for operation, durations in sorted(by_operation.items()):
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            print(f"   {operation:30} avg: {avg_duration:6.1f}ms, max: {max_duration:6.1f}ms")

    # Error analysis
    errors = [e for e in events if 'error' in e['event_type']]
    if errors:
        print(f"\n❌ Errors ({len(errors)} total):")
        error_types = Counter(e.get('error_type', 'Unknown') for e in errors)
        for error_type, count in error_types.most_common():
            print(f"   {error_type:30} {count:3} occurrences")

            # Show sample error message
            sample = next(e for e in errors if e.get('error_type') == error_type)
            if 'error_message' in sample:
                msg = sample['error_message'][:100]
                print(f"      Sample: {msg}...")

    # Pattern prediction insights
    predictions = [e for e in events if e['event_type'] == 'prediction_complete']
    if predictions:
        print(f"\n🎯 Prediction Insights:")
        print(f"   Total prediction operations: {len(predictions)}")

        total_patterns = sum(e['patterns_predicted'] for e in predictions)
        print(f"   Total patterns predicted: {total_patterns}")

        if total_patterns > 0:
            avg_patterns = total_patterns / len(predictions)
            print(f"   Avg patterns per request: {avg_patterns:.1f}")

        # Most common patterns
        all_patterns = []
        for e in predictions:
            all_patterns.extend(e.get('patterns', []))

        if all_patterns:
            pattern_counts = Counter(all_patterns)
            print(f"\n   Most Common Patterns:")
            for pattern, count in pattern_counts.most_common(10):
                print(f"      {pattern:30} {count:3} times")

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'logs/pattern_recognition.log'
    analyze_pattern_logs(log_file)
```

### Tasks

#### 1.0 Set Up Pattern Recognition Logging (NEW)
**Before any other Phase 1 tasks**

1. Create `app/server/core/pattern_logging.py` with utilities above
2. Create `app/server/logs/` directory if it doesn't exist
3. Configure logger in `app/server/core/pattern_predictor.py`:

```python
# At top of pattern_predictor.py
import logging
from core.pattern_logging import log_pattern_event, log_pattern_performance, PatternOperationContext

# Configure file handler for pattern logs
pattern_logger = logging.getLogger('pattern_recognition')
pattern_logger.setLevel(logging.INFO)

# Add file handler
fh = logging.FileHandler('logs/pattern_recognition.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
pattern_logger.addHandler(fh)

# Add console handler for errors
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
ch.setFormatter(formatter)
pattern_logger.addHandler(ch)
```

4. Update existing `predict_patterns_from_input()` to use logging:

```python
@log_pattern_performance
def predict_patterns_from_input(
    nl_input: str,
    project_path: str | None = None
) -> list[dict[str, Any]]:
    """Predict patterns from natural language input before workflow starts."""

    with PatternOperationContext('keyword_pattern_matching',
                                   nl_input_length=len(nl_input),
                                   nl_input_preview=nl_input[:100]) as ctx:

        predictions = []
        nl_lower = nl_input.lower()

        # Test patterns
        if any(kw in nl_lower for kw in ['test', 'pytest', 'vitest']):
            log_pattern_event('pattern_keyword_match', {
                'keywords': ['test', 'pytest', 'vitest'],
                'nl_input_preview': nl_input[:50]
            })

            # ... rest of prediction logic ...

        ctx.set_result(
            patterns_predicted=len(predictions),
            patterns=[p['pattern'] for p in predictions]
        )

    return predictions
```

#### 1.1 Apply Migration 010
```bash
cd app/server
uv run python -c "
import sqlite3
conn = sqlite3.connect('../workflow_history.db')
with open('db/migrations/010_add_pattern_predictions.sql', 'r') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print('✅ Migration 010 applied')
"
```

**Verify:**
```bash
sqlite3 workflow_history.db "SELECT name FROM sqlite_master WHERE type='table' AND name='pattern_predictions';"
# Expected: pattern_predictions
```

#### 1.2 Test Pattern Prediction End-to-End
Create test script: `app/server/tests/manual/test_pattern_prediction.py`

```python
"""
Test pattern prediction at submission time.
Run: cd app/server && uv run python tests/manual/test_pattern_prediction.py
"""
import requests
import json

# Submit test request with pattern keywords
test_cases = [
    {
        "nl_input": "Run backend pytest tests and ensure coverage >80%",
        "expected_patterns": ["test:pytest:backend"]
    },
    {
        "nl_input": "Build and typecheck the backend TypeScript code",
        "expected_patterns": ["build:typecheck:backend"]
    },
    {
        "nl_input": "Fix the authentication bug in login flow",
        "expected_patterns": ["fix:bug"]
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n🧪 Test {i}: {test['nl_input']}")

    response = requests.post(
        "http://localhost:8000/api/submit-request",
        json={"nl_input": test["nl_input"]}
    )

    if response.status_code == 200:
        data = response.json()
        predicted = data.get("predicted_patterns", [])
        print(f"✅ Predicted: {[p['pattern'] for p in predicted]}")
        print(f"📊 Expected: {test['expected_patterns']}")

        # Check prediction stored in DB
        # ... verification code ...
    else:
        print(f"❌ Failed: {response.status_code}")
```

#### 1.3 Update Frontend to Display Patterns (Optional)
Modify: `app/client/src/components/CreateNewRequestCard.tsx`

After successful submission, display predicted patterns:
```typescript
{response.predicted_patterns && response.predicted_patterns.length > 0 && (
  <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
    <h4 className="text-sm font-medium text-emerald-300 mb-2">
      🎯 Detected Patterns
    </h4>
    <div className="flex flex-wrap gap-2">
      {response.predicted_patterns.map((pred, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <span className="px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-md border border-emerald-500/30">
            {pred.pattern}
          </span>
          <span className="text-xs text-gray-400">
            {(pred.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      ))}
    </div>
  </div>
)}
```

#### 1.4 Create Verification Documentation
Create: `docs/pattern_recognition/PHASE_1_IMPLEMENTATION_VERIFICATION.md`

Document:
- Migration 010 applied successfully
- Pattern prediction test results (accuracy for each test case)
- Database verification (pattern_predictions table populated)
- Frontend UI screenshots (if implemented)
- Known issues or limitations

### Acceptance Criteria
- [ ] Migration 010 applied to `workflow_history.db`
- [ ] `pattern_predictions` table exists with correct schema
- [ ] Pattern prediction works on test cases (≥80% accuracy)
- [ ] Predictions stored in database with request_id linkage
- [ ] Frontend shows predicted patterns (optional)
- [ ] Verification doc created

---

## Phase 2: Integrate with Queue System

**Effort:** 2-3 hours
**Status:** Not started

### Objectives
- Pass pattern predictions to phase queue
- Display patterns in ZteHopperQueueCard
- Enable pattern metadata in queue items

### Tasks

#### 2.1 Modify Phase Queue Service
Update: `app/server/services/phase_queue_service.py`

Add `predicted_patterns` parameter to enqueue:
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

#### 2.2 Update GitHub Issue Service Integration
Modify: `app/server/services/github_issue_service.py`

Pass predictions to queue when creating phases:
```python
# After predicting patterns, store pattern strings for queue
pattern_strings = [p['pattern'] for p in predicted_patterns]

# When enqueueing phases
queue_service.enqueue(
    parent_issue=parent_issue,
    phase_number=phase_num,
    phase_data=phase_data,
    depends_on_phase=depends_on,
    predicted_patterns=pattern_strings  # NEW
)
```

#### 2.3 Display Patterns in Queue UI
Modify: `app/client/src/components/ZteHopperQueueCard.tsx`

Add pattern badges to queued phases:
```typescript
{/* Show predicted patterns if available */}
{phase.phase_data?.predicted_patterns && (
  <div className="mt-2 flex flex-wrap gap-1">
    <span className="text-xs text-gray-400 mr-1">Patterns:</span>
    {phase.phase_data.predicted_patterns.map((pattern, idx) => (
      <span
        key={idx}
        className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-xs rounded-md border border-emerald-500/30"
        title="Predicted pattern"
      >
        {pattern}
      </span>
    ))}
  </div>
)}
```

#### 2.4 Test Queue Integration
1. Submit multi-phase request with pattern keywords
2. Verify patterns appear in queue items
3. Check pattern persistence through queue transitions (ready → running → completed)

### Acceptance Criteria
- [ ] Queue service stores predicted patterns in phase_data
- [ ] Patterns passed from submission → queue correctly
- [ ] ZteHopperQueueCard displays pattern badges
- [ ] Patterns persist through queue state transitions
- [ ] No visual clutter for phases without patterns

---

## Phase 3: Close the Loop - Validate Predictions

**Effort:** 2-3 hours
**Status:** Not started

### Objectives
- Compare predicted vs actual patterns after workflow completes
- Calculate prediction accuracy metrics
- Update pattern statistics based on validation

### Tasks

#### 3.1 Create Pattern Validator Service
New file: `app/server/core/pattern_validator.py`

```python
"""
Pattern Validator - Compares predicted vs actual patterns after workflow completion.
"""
import logging
import sqlite3
from typing import Dict, List

logger = logging.getLogger(__name__)

def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: List[str],
    db_connection: sqlite3.Connection
) -> Dict:
    """
    Compare predicted patterns against actual patterns from completed workflow.

    Returns validation results with accuracy metrics:
    {
        'total_predicted': 3,
        'total_actual': 2,
        'correct': 2,
        'false_positives': 1,
        'false_negatives': 0,
        'accuracy': 0.67,
        'details': [...]
    }
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
    predicted_patterns = {row[2] for row in predictions}  # Set of pattern signatures
    actual_patterns_set = set(actual_patterns)

    # Calculate metrics
    correct = predicted_patterns & actual_patterns_set
    false_positives = predicted_patterns - actual_patterns_set
    false_negatives = actual_patterns_set - predicted_patterns

    results = {
        'total_predicted': len(predicted_patterns),
        'total_actual': len(actual_patterns),
        'correct': len(correct),
        'false_positives': len(false_positives),
        'false_negatives': len(false_negatives),
        'accuracy': len(correct) / len(predicted_patterns) if predictions else 0.0,
        'details': {
            'correct_predictions': list(correct),
            'false_positives': list(false_positives),
            'false_negatives': list(false_negatives)
        }
    }

    # Update pattern_predictions table with validation results
    for pred_id, pattern_id, pattern_sig, confidence in predictions:
        was_correct = 1 if pattern_sig in actual_patterns_set else 0
        cursor.execute("""
            UPDATE pattern_predictions
            SET was_correct = ?, validated_at = datetime('now')
            WHERE id = ?
        """, (was_correct, pred_id))

    # Update operation_patterns accuracy statistics
    cursor.execute("""
        UPDATE operation_patterns
        SET prediction_accuracy = (
            SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
            FROM pattern_predictions
            WHERE pattern_id = operation_patterns.id
              AND was_correct IS NOT NULL
        )
        WHERE id IN (
            SELECT DISTINCT pattern_id FROM pattern_predictions WHERE request_id = ?
        )
    """, (request_id,))

    db_connection.commit()
    logger.info(f"[Validator] Request {request_id}: {results['accuracy']:.1%} accuracy")

    return results
```

#### 3.2 Integrate Validation into Workflow Completion
Modify: `app/server/core/pattern_detector.py` or workflow completion handler

When workflow completes:
```python
from core.pattern_validator import validate_predictions

# After detecting patterns from completed workflow
detected_patterns = detect_patterns_in_workflow(workflow)
pattern_signatures = [p['signature'] for p in detected_patterns]

# Validate predictions (if request_id is available)
if workflow.get('request_id'):
    validation_results = validate_predictions(
        request_id=workflow['request_id'],
        workflow_id=workflow['workflow_id'],
        actual_patterns=pattern_signatures,
        db_connection=conn
    )

    logger.info(f"Pattern prediction accuracy: {validation_results['accuracy']:.1%}")
```

#### 3.3 Create Validation Analytics Query
New file: `app/server/tests/manual/query_prediction_accuracy.py`

```python
"""
Query pattern prediction accuracy statistics.
"""
import sqlite3

conn = sqlite3.connect('workflow_history.db')
cursor = conn.cursor()

# Overall accuracy
cursor.execute("""
    SELECT
        COUNT(*) as total_predictions,
        SUM(was_correct) as correct_predictions,
        CAST(SUM(was_correct) AS REAL) / COUNT(*) as accuracy
    FROM pattern_predictions
    WHERE was_correct IS NOT NULL
""")

total, correct, accuracy = cursor.fetchone()
print(f"\n📊 Overall Prediction Accuracy: {accuracy:.1%}")
print(f"   {correct}/{total} predictions correct\n")

# Accuracy by pattern type
cursor.execute("""
    SELECT
        op.pattern_signature,
        op.prediction_count,
        op.prediction_accuracy,
        COUNT(pp.id) as validated_count
    FROM operation_patterns op
    LEFT JOIN pattern_predictions pp ON op.id = pp.pattern_id
    WHERE op.prediction_count > 0
    GROUP BY op.id
    ORDER BY op.prediction_accuracy DESC
""")

print("🎯 Accuracy by Pattern:\n")
for sig, pred_count, accuracy, validated in cursor.fetchall():
    acc_str = f"{accuracy:.1%}" if accuracy else "N/A"
    print(f"  {sig:30} | Predicted: {pred_count:3} | Accuracy: {acc_str:6} | Validated: {validated}")

conn.close()
```

### Acceptance Criteria
- [ ] Pattern validator compares predicted vs actual
- [ ] Validation results stored in `pattern_predictions.was_correct`
- [ ] `operation_patterns.prediction_accuracy` updated
- [ ] Analytics query shows accuracy by pattern type
- [ ] Accuracy ≥60% for common patterns (test, build, fix)

---

## Phase 4: Observability & Dashboard

**Effort:** 3-4 hours
**Status:** Not started

### Objectives
- Create pattern analytics dashboard endpoint
- Display real-time pattern detection stats
- Show automation recommendations

### Tasks

#### 4.1 Create Pattern Analytics Endpoint
New file: `app/server/routes/pattern_routes.py`

```python
"""
Pattern Recognition Analytics Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3

router = APIRouter(prefix="/api/patterns", tags=["patterns"])

class PatternStats(BaseModel):
    total_patterns: int
    total_predictions: int
    overall_accuracy: float
    high_value_candidates: list[dict]
    recent_predictions: list[dict]

@router.get("/analytics", response_model=PatternStats)
async def get_pattern_analytics():
    """Get comprehensive pattern recognition analytics."""
    conn = sqlite3.connect('workflow_history.db')
    cursor = conn.cursor()

    # Total patterns
    cursor.execute("SELECT COUNT(*) FROM operation_patterns")
    total_patterns = cursor.fetchone()[0]

    # Total predictions
    cursor.execute("SELECT COUNT(*) FROM pattern_predictions")
    total_predictions = cursor.fetchone()[0]

    # Overall accuracy
    cursor.execute("""
        SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
        FROM pattern_predictions
        WHERE was_correct IS NOT NULL
    """)
    accuracy_row = cursor.fetchone()
    overall_accuracy = accuracy_row[0] if accuracy_row and accuracy_row[0] else 0.0

    # High-value automation candidates (≥70% accuracy, ≥5 occurrences)
    cursor.execute("""
        SELECT
            pattern_signature,
            prediction_count,
            prediction_accuracy,
            detection_count
        FROM operation_patterns
        WHERE prediction_accuracy >= 0.70
          AND prediction_count >= 5
        ORDER BY prediction_accuracy DESC, prediction_count DESC
        LIMIT 10
    """)

    high_value = [
        {
            "pattern": row[0],
            "predictions": row[1],
            "accuracy": row[2],
            "occurrences": row[3]
        }
        for row in cursor.fetchall()
    ]

    # Recent predictions (last 10)
    cursor.execute("""
        SELECT
            pp.request_id,
            op.pattern_signature,
            pp.confidence_score,
            pp.was_correct,
            pp.predicted_at
        FROM pattern_predictions pp
        JOIN operation_patterns op ON pp.pattern_id = op.id
        ORDER BY pp.predicted_at DESC
        LIMIT 10
    """)

    recent = [
        {
            "request_id": row[0],
            "pattern": row[1],
            "confidence": row[2],
            "was_correct": row[3],
            "predicted_at": row[4]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return PatternStats(
        total_patterns=total_patterns,
        total_predictions=total_predictions,
        overall_accuracy=overall_accuracy,
        high_value_candidates=high_value,
        recent_predictions=recent
    )
```

Register in `app/server/server.py`:
```python
from routes.pattern_routes import router as pattern_router
app.include_router(pattern_router)
```

#### 4.2 Create Pattern Analytics Card (Frontend)
New file: `app/client/src/components/PatternAnalyticsCard.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';

interface PatternAnalytics {
  total_patterns: number;
  total_predictions: number;
  overall_accuracy: number;
  high_value_candidates: Array<{
    pattern: string;
    predictions: number;
    accuracy: number;
    occurrences: number;
  }>;
  recent_predictions: Array<{
    request_id: string;
    pattern: string;
    confidence: number;
    was_correct: boolean | null;
    predicted_at: string;
  }>;
}

export function PatternAnalyticsCard() {
  const { data, isLoading } = useQuery<PatternAnalytics>({
    queryKey: ['pattern-analytics'],
    queryFn: async () => {
      const res = await fetch('/api/patterns/analytics');
      if (!res.ok) throw new Error('Failed to fetch pattern analytics');
      return res.json();
    },
    refetchInterval: 10000  // Refresh every 10s
  });

  if (isLoading) return <div>Loading pattern analytics...</div>;

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">
        🎯 Pattern Recognition Analytics
      </h2>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Total Patterns</div>
          <div className="text-2xl font-bold text-white">
            {data?.total_patterns || 0}
          </div>
        </div>
        <div className="bg-gray-900 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Predictions Made</div>
          <div className="text-2xl font-bold text-white">
            {data?.total_predictions || 0}
          </div>
        </div>
        <div className="bg-gray-900 p-4 rounded-lg">
          <div className="text-gray-400 text-sm">Accuracy</div>
          <div className={`text-2xl font-bold ${
            (data?.overall_accuracy || 0) >= 0.7 ? 'text-emerald-400' : 'text-yellow-400'
          }`}>
            {((data?.overall_accuracy || 0) * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* High-Value Candidates */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">
          🚀 Automation Candidates (≥70% accuracy)
        </h3>
        {data?.high_value_candidates && data.high_value_candidates.length > 0 ? (
          <div className="space-y-2">
            {data.high_value_candidates.map((candidate, idx) => (
              <div key={idx} className="bg-gray-900 p-3 rounded-lg flex justify-between items-center">
                <div>
                  <span className="font-mono text-emerald-300">{candidate.pattern}</span>
                  <div className="text-xs text-gray-400 mt-1">
                    {candidate.predictions} predictions, {candidate.occurrences} occurrences
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-emerald-400 font-semibold">
                    {(candidate.accuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-400">accuracy</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400 text-sm">
            No automation candidates yet. Need ≥5 predictions with ≥70% accuracy.
          </div>
        )}
      </div>

      {/* Recent Predictions */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">
          📊 Recent Predictions
        </h3>
        {data?.recent_predictions && data.recent_predictions.length > 0 ? (
          <div className="space-y-2">
            {data.recent_predictions.slice(0, 5).map((pred, idx) => (
              <div key={idx} className="bg-gray-900 p-2 rounded text-sm flex justify-between">
                <span className="font-mono text-gray-300">{pred.pattern}</span>
                <span className={
                  pred.was_correct === null ? 'text-gray-500' :
                  pred.was_correct ? 'text-emerald-400' : 'text-red-400'
                }>
                  {pred.was_correct === null ? '⏳ pending' :
                   pred.was_correct ? '✓ correct' : '✗ wrong'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400 text-sm">No predictions yet</div>
        )}
      </div>
    </div>
  );
}
```

#### 4.3 Add to Main Dashboard
Update: `app/client/src/pages/Dashboard.tsx`

Add PatternAnalyticsCard to the dashboard grid.

### Acceptance Criteria
- [ ] `/api/patterns/analytics` endpoint returns stats
- [ ] PatternAnalyticsCard displays live data
- [ ] Accuracy displayed with color coding (green ≥70%, yellow <70%)
- [ ] High-value automation candidates shown
- [ ] Recent predictions visible with validation status

---

## Success Criteria (All Phases)

### Phase 1 Complete
- [x] **Logging infrastructure** set up (pattern_logging.py created)
- [x] **Log file** created (`logs/pattern_recognition.log`)
- [x] Migration 010 applied
- [x] Pattern prediction at submission time working
- [x] Predictions stored in database
- [x] **Structured logging** capturing all prediction events
- [x] Test accuracy ≥80% for keyword-based patterns
- [x] **Log analysis tool** working (analyze_pattern_logs.py)
- [x] Documentation created

### Phase 2 Complete
- [x] Patterns stored in queue phase_data
- [x] Queue UI displays pattern badges
- [x] Patterns persist through queue transitions
- [x] **Queue logging** capturing pattern attachments and state transitions
- [x] **Log analysis** shows queue pattern flow

### Phase 3 Complete
- [x] Validation runs on workflow completion
- [x] Accuracy metrics tracked per pattern
- [x] Overall accuracy ≥60%
- [x] False positive/negative tracking
- [x] **Validation logging** capturing all accuracy calculations
- [x] **Log analysis** shows accuracy trends over time
- [x] **Error patterns** identified from logs

### Phase 4 Complete
- [x] Analytics endpoint functional
- [x] Dashboard displays real-time stats
- [x] Automation candidates identified (≥70% accuracy, ≥5 predictions)
- [x] Recent predictions visible
- [x] **Analytics logging** tracking dashboard usage
- [x] **Performance metrics** logged and analyzable
- [x] **Log analysis tool** can generate insights report

---

## Testing Strategy

### End-to-End Test Flow
1. **Submit:** Create request with pattern keywords ("run pytest tests")
2. **Predict:** System predicts `test:pytest:backend` (Phase 1)
3. **Queue:** Pattern appears in ZteHopperQueueCard (Phase 2)
4. **Execute:** Workflow runs, actual patterns detected
5. **Validate:** Compare predicted vs actual (Phase 3)
6. **Display:** Accuracy shows in dashboard (Phase 4)

### Test Cases
```
Test 1: "Run backend pytest tests" → Expect: test:pytest:backend
Test 2: "Build TypeScript backend" → Expect: build:typecheck:backend
Test 3: "Fix authentication bug" → Expect: fix:bug
Test 4: "Deploy to production" → Expect: deploy:production
Test 5: "Run frontend vitest tests" → Expect: test:vitest:frontend
```

---

## Rollback Plan

If issues arise, can safely rollback:

1. **Phase 1:** Migration 010 adds tables, doesn't modify existing
   - Safe to leave tables even if unused
   - Pattern prediction code has try/catch, won't break submissions

2. **Phase 2:** Purely additive to queue system
   - `predicted_patterns` is optional field
   - Queue works without patterns

3. **Phase 3:** Validation is post-execution
   - Doesn't affect workflow execution
   - Can disable validation hook without impact

4. **Phase 4:** Read-only dashboard
   - Can remove analytics card from UI
   - Endpoint can be disabled

---

## Dependencies

- **Code:** Python 3.12+, FastAPI, React, TypeScript
- **Database:** SQLite (workflow_history.db)
- **Existing Migrations:** 004 (pattern learning), 010 (predictions - file exists)
- **Existing Code:** pattern_detector.py, pattern_predictor.py, github_issue_service.py
- **Documentation:** PATTERN_RECOGNITION_IMPLEMENTATION_PLAN.md, PHASE_1_VERIFICATION.md (original Phase 1, already complete)

---

## Notes for ADW Execution

- Each phase should create verification doc (`PHASE_X_IMPLEMENTATION_VERIFICATION.md`)
- Run tests after each phase before proceeding
- Monitor pattern prediction accuracy - if <50%, pause and investigate
- Phase 2 requires frontend changes (React/TypeScript)
- Phase 4 creates new API endpoint + UI component
- Full test coverage recommended for pattern_validator.py (Phase 3)

---

**Workflow Template:** `adw_sdlc_complete_iso` (standard full SDLC)
**Model Preference:** Standard (not lightweight - this is complex multi-phase work)
**Estimated Cost:** $4-8 (4 phases, ~2-3 hours each)
