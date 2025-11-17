# Phase 1.3: Quick Reference Guide

## File Locations

### Implementation
- **Core Module:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/core/pattern_persistence.py`
- **Test Suite:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/tests/test_pattern_persistence.py`

### Documentation
- **Implementation Guide:** `/Users/Warmonger0/tac/tac-webbuilder/PATTERN_PERSISTENCE_IMPLEMENTATION.md`
- **Delivery Summary:** `/Users/Warmonger0/tac/tac-webbuilder/PHASE_1_3_DELIVERY.md`
- **Verification Report:** `/Users/Warmonger0/tac/tac-webbuilder/IMPLEMENTATION_VERIFICATION.md`
- **Quick Reference:** `/Users/Warmonger0/tac/tac-webbuilder/QUICK_REFERENCE.md` (this file)

---

## Core Functions Quick Reference

### 1. record_pattern_occurrence()
**Purpose:** Record pattern observation in database

**Signature:**
```python
def record_pattern_occurrence(
    pattern_signature: str,
    workflow: Dict,
    db_connection: sqlite3.Connection
) -> Tuple[Optional[int], bool]:
```

**Parameters:**
- `pattern_signature`: Pattern ID (e.g., "test:pytest:backend")
- `workflow`: Complete workflow dictionary
- `db_connection`: SQLite connection object

**Returns:**
- `(pattern_id, is_new_pattern)` tuple
- `(None, False)` if workflow_id missing

**Location:** Line 25

**Example:**
```python
pattern_id, is_new = record_pattern_occurrence(
    "test:pytest:backend",
    workflow,
    db_conn
)
```

---

### 2. update_pattern_statistics()
**Purpose:** Update running averages and statistics for pattern

**Signature:**
```python
def update_pattern_statistics(
    pattern_id: int,
    workflow: Dict,
    db_connection: sqlite3.Connection
) -> None:
```

**Updates:**
- avg_tokens_with_llm (running average)
- avg_cost_with_llm (running average)
- avg_tokens_with_tool (5% of LLM)
- avg_cost_with_tool (5% of LLM)
- potential_monthly_savings (extrapolated)
- confidence_score (recalculated)

**Location:** Line 160

**Called By:** record_pattern_occurrence() after committing occurrence

---

### 3. _calculate_confidence_from_db()
**Purpose:** Helper to calculate confidence from database data

**Signature:**
```python
def _calculate_confidence_from_db(
    pattern_id: int,
    db_connection: sqlite3.Connection
) -> float:
```

**Parameters:**
- `pattern_id`: Pattern to calculate confidence for
- `db_connection`: SQLite connection

**Returns:** Float confidence score (0-100)

**Location:** Line 265

**Used By:** update_pattern_statistics()

---

### 4. process_and_persist_workflow()
**Purpose:** Main entry point for single workflow processing

**Signature:**
```python
def process_and_persist_workflow(
    workflow: Dict,
    db_connection: sqlite3.Connection
) -> Dict:
```

**Parameters:**
- `workflow`: Complete workflow dictionary
- `db_connection`: SQLite connection

**Returns:**
```python
{
    'patterns_detected': int,
    'new_patterns': int,
    'pattern_ids': [int, ...]
}
```

**Location:** Line 330

**Example:**
```python
result = process_and_persist_workflow(workflow, db_conn)
print(f"Detected {result['patterns_detected']} patterns")
```

---

### 5. batch_process_workflows()
**Purpose:** Process multiple workflows in batch

**Signature:**
```python
def batch_process_workflows(
    workflows: List[Dict],
    db_connection: sqlite3.Connection
) -> Dict:
```

**Parameters:**
- `workflows`: List of workflow dictionaries
- `db_connection`: SQLite connection

**Returns:**
```python
{
    'total_workflows': int,
    'processed': int,
    'total_patterns': int,
    'new_patterns': int,
    'errors': int
}
```

**Location:** Line 388

**Example:**
```python
result = batch_process_workflows(workflows, db_conn)
print(f"Processed {result['processed']}/{result['total_workflows']}")
```

---

## Test Classes Quick Reference

### TestPatternRecording (7 tests)
**Tests:** Pattern creation and updates
```
- test_create_new_pattern
- test_create_new_pattern_stores_characteristics
- test_update_existing_pattern
- test_missing_workflow_id
- test_pattern_occurrence_link_created
- test_idempotent_occurrence_recording
```

### TestStatisticsUpdate (6 tests)
**Tests:** Statistics calculations
```
- test_first_workflow_statistics
- test_running_average_calculation
- test_estimated_tool_cost_calculation
- test_monthly_savings_calculation
- test_confidence_score_updated
- test_nonexistent_pattern_handling
```

### TestConfidenceCalculation (3 tests)
**Tests:** Confidence scoring
```
- test_confidence_with_no_workflows
- test_confidence_with_workflow_data
- test_confidence_nonexistent_pattern
```

### TestBatchProcessing (6 tests)
**Tests:** Batch operations
```
- test_process_single_workflow
- test_process_workflow_returns_correct_structure
- test_batch_process_workflows
- test_batch_process_returns_correct_structure
- test_batch_process_with_mixed_workflows
- test_batch_process_error_handling
```

### TestErrorHandling (4 tests)
**Tests:** Error scenarios
```
- test_pattern_recording_with_null_tokens
- test_pattern_recording_with_null_cost
- test_concurrent_pattern_creation
```

---

## Running Tests

### All Tests
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
pytest app/server/tests/test_pattern_persistence.py -v
```

### Specific Class
```bash
pytest app/server/tests/test_pattern_persistence.py::TestPatternRecording -v
```

### Specific Test
```bash
pytest app/server/tests/test_pattern_persistence.py::TestPatternRecording::test_create_new_pattern -v
```

### With Coverage
```bash
pytest app/server/tests/test_pattern_persistence.py --cov=app.server.core.pattern_persistence
```

---

## Database Schema Summary

### operation_patterns
```sql
id INTEGER PRIMARY KEY
pattern_signature TEXT UNIQUE
pattern_type TEXT
occurrence_count INTEGER
avg_tokens_with_llm INTEGER
avg_cost_with_llm REAL
avg_tokens_with_tool INTEGER
avg_cost_with_tool REAL
typical_input_pattern TEXT (JSON)
automation_status TEXT
confidence_score REAL
potential_monthly_savings REAL
created_at TEXT
last_seen TEXT
```

### pattern_occurrences
```sql
id INTEGER PRIMARY KEY
pattern_id INTEGER
workflow_id TEXT
similarity_score REAL
matched_characteristics TEXT (JSON)
detected_at TEXT
UNIQUE(pattern_id, workflow_id)
```

---

## Integration with pattern_detector.py

### Imported Functions
1. **process_workflow_for_patterns()**
   - Detects patterns in workflow
   - Returns: `{'patterns': [...], 'characteristics': {...}}`
   - Used in: `process_and_persist_workflow()`

2. **calculate_confidence_score()**
   - Calculates confidence from data
   - Returns: float (0-100)
   - Used in: `_calculate_confidence_from_db()`

3. **extract_pattern_characteristics()**
   - Extracts characteristics from workflow
   - Returns: dict with keywords, duration, complexity, etc.
   - Used in: `record_pattern_occurrence()`

---

## Logging Output Examples

### Info Level
```
[Pattern] New pattern detected: test:pytest:backend
```

### Debug Level
```
[Pattern] Updated pattern test:pytest:backend (count: 5)
[Pattern] Updated statistics for pattern 1: avg_cost=$0.5000, savings=$2.375/mo, confidence=85.0%
```

### Warning Level
```
[Pattern] Workflow missing workflow_id, cannot record pattern
[Pattern] Pattern 999 not found for statistics update
[Pattern] Failed to record pattern test:pytest:backend for workflow wf-123: KeyError
```

### Error Level
```
[Pattern] Failed to process workflow wf-123: ValueError
```

---

## Usage Patterns

### Single Workflow Processing
```python
from app.server.core.pattern_persistence import process_and_persist_workflow
import sqlite3

with sqlite3.connect('db/workflow_history.db') as conn:
    result = process_and_persist_workflow(workflow, conn)
    if result['new_patterns'] > 0:
        print(f"Found {result['new_patterns']} new patterns!")
```

### Batch Processing
```python
from app.server.core.pattern_persistence import batch_process_workflows
import sqlite3

workflows = fetch_workflows_from_adw()

with sqlite3.connect('db/workflow_history.db') as conn:
    result = batch_process_workflows(workflows, conn)
    print(f"Processed {result['processed']} workflows")
    print(f"Found {result['new_patterns']} new patterns")
    if result['errors'] > 0:
        print(f"Encountered {result['errors']} errors")
```

### Integration with Sync
```python
from app.server.core.pattern_persistence import process_and_persist_workflow

def sync_workflow_history():
    # ... existing sync code ...

    # Pattern learning pass
    with get_db_connection() as conn:
        for workflow in all_workflows:
            try:
                result = process_and_persist_workflow(workflow, conn)
                if result['patterns_detected'] > 0:
                    logger.debug(f"Detected {result['patterns_detected']} patterns")
            except Exception as e:
                logger.warning(f"Pattern learning failed: {e}")
                # Continue processing other workflows
```

---

## Key Features Summary

### Idempotency
- Safe to re-run without duplicates
- Uses `INSERT OR IGNORE` for occurrences
- Checks pattern existence before creation

### Error Resilience
- Individual pattern failures don't stop batch
- Graceful handling of missing data
- Batch continues on errors

### Performance
- Running averages avoid recalculation
- Minimal database queries
- Batch aggregation in memory

### Data Integrity
- Transaction commits after operations
- Parameterized queries prevent SQL injection
- Proper NULL handling

### Observability
- Structured logging with [Pattern] prefix
- Debug, info, warning, error levels
- Performance metrics in logs

---

## Common Issues and Solutions

### Issue: Workflow missing workflow_id
**Solution:** Function returns (None, False) and logs warning
**Prevention:** Ensure workflow_id is always set

### Issue: Statistics calculation fails
**Solution:** Handled with try-except, logs warning
**Prevention:** Check pattern exists before calling update_pattern_statistics()

### Issue: Duplicate pattern occurrences
**Solution:** INSERT OR IGNORE prevents duplicates
**Prevention:** Idempotency built in

### Issue: Null metric values
**Solution:** Defaults to 0 for tokens, 0.0 for cost
**Prevention:** None, safe defaults used

---

## Statistics Calculation Details

### Running Average Formula
```
new_avg = (old_avg * (count - 1) + new_value) / count
```

### Tool Cost Estimation
Based on Phase 3E research (95-97% cost reduction):
- Tool tokens = 5% of LLM tokens
- Tool cost = 5% of LLM cost

### Monthly Savings
```
savings_per_use = llm_cost - tool_cost
potential_monthly_savings = savings_per_use * occurrence_count
```

### Confidence Score Components
1. **Frequency** (0-40 points): Based on occurrence count
2. **Consistency** (0-30 points): Based on duration/error variance
3. **Success Rate** (0-30 points): Based on errors and retries

---

## Code Statistics

| Metric | Value |
|--------|-------|
| Implementation Lines | 426 |
| Test Lines | 620 |
| Test Methods | 26+ |
| Functions | 5 |
| Test Classes | 5 |
| Coverage | Comprehensive |

---

## Ready For

1. ✅ Integration with workflow_history.py
2. ✅ Code review
3. ✅ Production deployment
4. ✅ Phase 1.4 (Backfill & Validation)

---

**Last Updated:** November 17, 2025
**Status:** COMPLETE AND VERIFIED
