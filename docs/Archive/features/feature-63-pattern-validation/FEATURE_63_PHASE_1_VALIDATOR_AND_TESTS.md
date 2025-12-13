# Feature #63 Phase 1: Core Validator + Tests

## Task Summary
**Issue**: Create pattern validator module with comprehensive test coverage
**Priority**: High
**Type**: Feature
**Estimated Time**: 1.5 hours
**Status**: Planned → In Progress
**Dependencies**: Migration 010 applied (verify first)

## Context
Load: `/prime`

Feature #63 implements the "Close the Loop" validation system that measures prediction accuracy by comparing patterns predicted at submission (via `pattern_predictor.py`) against actual patterns detected after workflow completion (via `pattern_detector.py`).

**What exists:**
- ✅ `app/server/core/pattern_predictor.py` - Predicts patterns from NL input
- ✅ `app/server/core/pattern_detector.py` - Detects patterns from completed workflows
- ✅ Migration 010 files - Database schema for predictions
- ✅ `operation_patterns` table
- ✅ `pattern_predictions` table (if Migration 010 applied)

**What we're building (Phase 1):**
- ❌ `app/server/core/pattern_validator.py` - Compare predicted vs actual patterns
- ❌ `app/server/tests/core/test_pattern_validator.py` - Comprehensive test suite

## Problem Statement

### Current Behavior
- Pattern predictions are stored but never validated
- `pattern_predictions.was_correct` field remains NULL
- `operation_patterns.prediction_accuracy` field never updated
- No feedback loop to measure prediction quality

### Expected Behavior
- Validator compares predicted patterns against actual patterns
- Calculates accuracy metrics (TP, FP, FN)
- Updates database with validation results
- Provides structured ValidationResult data

### Impact
- Cannot measure prediction system effectiveness
- Missing data for ML feedback loop
- No visibility into which patterns predict well

## Root Cause
Pattern validator module was never implemented - only predictor and detector exist.

## Solution

### Overview
Create `pattern_validator.py` module using TDD approach. Write tests first to define expected behavior, then implement validator to pass tests. Module will fetch predictions, compare with actual patterns, calculate metrics, and update database.

### Technical Details

**Core Function Signature:**
```python
def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: List[str],
    db_connection
) -> ValidationResult
```

**Algorithm:**
1. Fetch predictions from DB for request_id
2. Convert to sets: predicted_set vs actual_set
3. Calculate: TP (intersection), FP (predicted - actual), FN (actual - predicted)
4. Update pattern_predictions.was_correct (1 or 0)
5. Recalculate operation_patterns.prediction_accuracy
6. Return ValidationResult with metrics

## Implementation Steps

### Step 1: Verify Migration 010 Applied (10 min)

**CRITICAL**: Validator requires pattern_predictions table.

```bash
cd app/server

# Check if table exists
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user \
POSTGRES_PASSWORD=changeme \
DB_TYPE=postgresql \
.venv/bin/python3 << 'EOF'
from database import get_database_adapter

adapter = get_database_adapter()
with adapter.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'pattern_predictions'
    """)
    if cursor.fetchone():
        print("✅ Migration 010 applied - pattern_predictions exists")
    else:
        print("❌ ERROR: Migration 010 NOT applied")
        print("   Run Feature #62 (Migration verification) first")
        exit(1)
EOF
```

**If migration not applied**: Stop and run Feature #62 first.

### Step 2: Write Test File (TDD) (40 min)

Create `app/server/tests/core/test_pattern_validator.py`:

```python
"""Tests for pattern validation system."""
import pytest
from datetime import datetime
from core.pattern_validator import validate_predictions, ValidationResult


@pytest.fixture
def db_connection():
    """Get test database connection."""
    from database import get_database_adapter
    adapter = get_database_adapter()
    with adapter.get_connection() as conn:
        yield conn
        conn.rollback()  # Rollback test data


@pytest.fixture
def sample_patterns(db_connection):
    """Create sample patterns and predictions in DB."""
    cursor = db_connection.cursor()

    # Insert test patterns
    cursor.execute("""
        INSERT INTO operation_patterns (
            pattern_signature, pattern_type, automation_status
        ) VALUES
            ('test:pytest:backend', 'test', 'detected'),
            ('build:typecheck:backend', 'build', 'detected'),
            ('fix:bug', 'fix', 'detected')
        RETURNING id
    """)
    pattern_ids = [row[0] for row in cursor.fetchall()]

    # Insert predictions
    cursor.execute("""
        INSERT INTO pattern_predictions (
            request_id, pattern_id, confidence_score, reasoning
        ) VALUES
            ('test-req-001', %s, 0.85, 'Test prediction 1'),
            ('test-req-001', %s, 0.75, 'Test prediction 2'),
            ('test-req-001', %s, 0.60, 'Test prediction 3')
    """, tuple(pattern_ids))

    db_connection.commit()

    return {
        'request_id': 'test-req-001',
        'pattern_ids': pattern_ids,
        'predicted_signatures': [
            'test:pytest:backend',
            'build:typecheck:backend',
            'fix:bug'
        ]
    }


def test_validate_predictions_perfect_accuracy(db_connection, sample_patterns):
    """All predictions match actual patterns - 100% accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    actual_patterns = sample_patterns['predicted_signatures']  # All match

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-001',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 3
    assert result.total_actual == 3
    assert result.correct == 3
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.accuracy == 1.0

    # Verify database updated
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 1
    """, (request_id,))
    assert cursor.fetchone()[0] == 3


def test_validate_predictions_partial_accuracy(db_connection, sample_patterns):
    """Some predictions correct, some not - partial accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    actual_patterns = [
        'test:pytest:backend',  # Correct (TP)
        'build:typecheck:backend',  # Correct (TP)
        'deploy:production'  # Not predicted (FN)
    ]
    # 'fix:bug' was predicted but not actual (FP)

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-002',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 3
    assert result.total_actual == 3
    assert result.correct == 2  # test:pytest, build:typecheck
    assert result.false_positives == 1  # fix:bug
    assert result.false_negatives == 1  # deploy:production
    assert result.accuracy == pytest.approx(2/3, 0.01)  # 66.7%

    # Verify database
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 1
    """, (request_id,))
    assert cursor.fetchone()[0] == 2

    cursor.execute("""
        SELECT COUNT(*) FROM pattern_predictions
        WHERE request_id = %s AND was_correct = 0
    """, (request_id,))
    assert cursor.fetchone()[0] == 1


def test_validate_predictions_no_predictions(db_connection):
    """No predictions were made - graceful handling."""
    # Act
    result = validate_predictions(
        request_id='nonexistent-req',
        workflow_id='wf-003',
        actual_patterns=['test:pytest:backend'],
        db_connection=db_connection
    )

    # Assert
    assert result.total_predicted == 0
    assert result.total_actual == 1
    assert result.correct == 0
    assert result.false_positives == 0
    assert result.false_negatives == 1
    assert result.accuracy == 0.0


def test_validate_predictions_updates_pattern_accuracy(db_connection, sample_patterns):
    """Validation updates operation_patterns.prediction_accuracy."""
    # Arrange
    request_id = sample_patterns['request_id']
    actual_patterns = ['test:pytest:backend']  # Only one correct

    # Act
    validate_predictions(
        request_id=request_id,
        workflow_id='wf-004',
        actual_patterns=actual_patterns,
        db_connection=db_connection
    )

    # Assert - Check pattern accuracy was updated
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = 'test:pytest:backend'
    """)
    accuracy = cursor.fetchone()[0]
    assert accuracy == 1.0  # This pattern was predicted correctly

    cursor.execute("""
        SELECT prediction_accuracy
        FROM operation_patterns
        WHERE pattern_signature = 'build:typecheck:backend'
    """)
    accuracy = cursor.fetchone()[0]
    assert accuracy == 0.0  # This pattern was predicted incorrectly


def test_validate_predictions_empty_actual(db_connection, sample_patterns):
    """Workflow completed with no detected patterns."""
    # Arrange
    request_id = sample_patterns['request_id']

    # Act
    result = validate_predictions(
        request_id=request_id,
        workflow_id='wf-005',
        actual_patterns=[],  # No patterns detected
        db_connection=db_connection
    )

    # Assert - All predictions are false positives
    assert result.total_predicted == 3
    assert result.total_actual == 0
    assert result.correct == 0
    assert result.false_positives == 3
    assert result.false_negatives == 0
    assert result.accuracy == 0.0


def test_validation_result_dataclass():
    """ValidationResult dataclass has correct structure."""
    result = ValidationResult(
        total_predicted=5,
        total_actual=4,
        correct=3,
        false_positives=2,
        false_negatives=1,
        accuracy=0.6,
        details={'pattern1': True, 'pattern2': False}
    )

    assert result.total_predicted == 5
    assert result.total_actual == 4
    assert result.correct == 3
    assert result.false_positives == 2
    assert result.false_negatives == 1
    assert result.accuracy == 0.6
    assert 'pattern1' in result.details
```

### Step 3: Create Validator Module (30 min)

Create `app/server/core/pattern_validator.py`:

```python
"""Pattern prediction validation system.

Compares predicted patterns against actual detected patterns
to measure prediction accuracy and close the feedback loop.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of pattern prediction validation.

    Attributes:
        total_predicted: Number of patterns predicted
        total_actual: Number of patterns actually detected
        correct: Number of correct predictions (true positives)
        false_positives: Predicted but not actual
        false_negatives: Actual but not predicted
        accuracy: Percentage correct (0.0 to 1.0)
        details: Pattern-level results {signature: was_correct}
    """
    total_predicted: int
    total_actual: int
    correct: int
    false_positives: int
    false_negatives: int
    accuracy: float
    details: Dict[str, bool]


def validate_predictions(
    request_id: str,
    workflow_id: str,
    actual_patterns: List[str],
    db_connection
) -> ValidationResult:
    """Compare predicted patterns against actual patterns.

    Args:
        request_id: Request ID that triggered workflow
        workflow_id: Workflow that completed
        actual_patterns: List of pattern signatures actually detected
        db_connection: Database connection

    Returns:
        ValidationResult with accuracy metrics
    """
    cursor = db_connection.cursor()

    # 1. Fetch predictions for this request
    cursor.execute("""
        SELECT pp.id, op.pattern_signature, pp.confidence_score
        FROM pattern_predictions pp
        JOIN operation_patterns op ON pp.pattern_id = op.id
        WHERE pp.request_id = %s
    """, (request_id,))

    predictions = cursor.fetchall()

    # Handle no predictions case
    if not predictions:
        return ValidationResult(
            total_predicted=0,
            total_actual=len(actual_patterns),
            correct=0,
            false_positives=0,
            false_negatives=len(actual_patterns),
            accuracy=0.0,
            details={}
        )

    # 2. Build sets for comparison
    predicted_map = {row[1]: row[0] for row in predictions}  # {signature: pred_id}
    predicted_set: Set[str] = set(predicted_map.keys())
    actual_set: Set[str] = set(actual_patterns)

    # 3. Calculate metrics
    true_positives = predicted_set & actual_set
    false_positives = predicted_set - actual_set
    false_negatives = actual_set - predicted_set

    correct_count = len(true_positives)
    accuracy = correct_count / len(predicted_set) if predicted_set else 0.0

    # 4. Update pattern_predictions.was_correct
    details = {}
    for signature, pred_id in predicted_map.items():
        was_correct = 1 if signature in actual_set else 0
        details[signature] = bool(was_correct)

        cursor.execute("""
            UPDATE pattern_predictions
            SET was_correct = %s, validated_at = NOW()
            WHERE id = %s
        """, (was_correct, pred_id))

    # 5. Update operation_patterns.prediction_accuracy
    # Recalculate accuracy for each pattern based on all validations
    affected_patterns = predicted_set | actual_set
    for pattern_sig in affected_patterns:
        cursor.execute("""
            UPDATE operation_patterns
            SET prediction_accuracy = (
                SELECT CAST(SUM(was_correct) AS REAL) / COUNT(*)
                FROM pattern_predictions
                WHERE pattern_id = operation_patterns.id
                  AND was_correct IS NOT NULL
            )
            WHERE pattern_signature = %s
        """, (pattern_sig,))

    db_connection.commit()

    # 6. Return results
    return ValidationResult(
        total_predicted=len(predicted_set),
        total_actual=len(actual_set),
        correct=correct_count,
        false_positives=len(false_positives),
        false_negatives=len(false_negatives),
        accuracy=accuracy,
        details=details
    )
```

### Step 4: Run Tests (10 min)

```bash
cd app/server

# Run validator tests
env POSTGRES_HOST=localhost \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=tac_webbuilder \
    POSTGRES_USER=tac_user \
    POSTGRES_PASSWORD=changeme \
    DB_TYPE=postgresql \
    .venv/bin/pytest tests/core/test_pattern_validator.py -v

# Expected: All 7 tests passing
```

**If tests fail**: Debug and fix until all pass.

### Step 5: Quality Checks (10 min)

```bash
cd app/server

# Linting
.venv/bin/ruff check core/pattern_validator.py --fix
.venv/bin/ruff check tests/core/test_pattern_validator.py --fix

# Type checking
.venv/bin/mypy core/pattern_validator.py --ignore-missing-imports
.venv/bin/mypy tests/core/test_pattern_validator.py --ignore-missing-imports

# Full test suite (ensure no regressions)
env POSTGRES_HOST=localhost \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=tac_webbuilder \
    POSTGRES_USER=tac_user \
    POSTGRES_PASSWORD=changeme \
    DB_TYPE=postgresql \
    .venv/bin/pytest tests/ -v --tb=short
```

### Step 6: Commit (10 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

git add app/server/core/pattern_validator.py
git add app/server/tests/core/test_pattern_validator.py

git commit -m "feat: Add pattern validator module (Phase 1/3)

Create core validation system to compare predicted vs actual patterns.

Problem:
- Pattern predictions stored but never validated
- No feedback loop to measure prediction accuracy
- Missing data for ML training pipeline

Solution:
- Created pattern_validator.py with validate_predictions()
- Compares predicted patterns against actual (TP, FP, FN)
- Updates pattern_predictions.was_correct field
- Recalculates operation_patterns.prediction_accuracy
- Comprehensive test suite (7 tests, 100% coverage)

Result:
- ValidationResult dataclass with accuracy metrics
- Database properly updated with validation results
- TDD approach ensures correctness
- Ready for Phase 2 integration

Files Changed:
- app/server/core/pattern_validator.py (new, ~150 lines)
- app/server/tests/core/test_pattern_validator.py (new, ~250 lines)

Testing:
- 7 test cases covering all scenarios
- Perfect accuracy, partial accuracy, edge cases
- Database update verification

Location: app/server/core/pattern_validator.py:1-150"
```

## Success Criteria

### Code Quality
- ✅ **Linting**: 0 errors, 0 warnings
- ✅ **Type Safety**: 0 mypy errors
- ✅ **Tests**: 7+ tests passing, 100% coverage of validator module
- ✅ **Regression**: All existing tests still pass

### Functionality
- ✅ **Validator Works**: Correctly calculates TP, FP, FN, accuracy
- ✅ **Database Updates**: pattern_predictions.was_correct set correctly
- ✅ **Pattern Accuracy**: operation_patterns.prediction_accuracy recalculated
- ✅ **Edge Cases**: Handles no predictions, no actuals, perfect/zero accuracy

### Module Design
- ✅ **Clean API**: Simple function signature, clear return type
- ✅ **Dataclass**: ValidationResult well-structured
- ✅ **No Side Effects**: Only database writes, no external calls
- ✅ **Testable**: Dependency injection (db_connection parameter)

## Expected Time Breakdown
- **Investigation**: 10 minutes (verify migration)
- **Test Writing**: 40 minutes (TDD approach)
- **Implementation**: 30 minutes (validator module)
- **Testing**: 10 minutes (run tests, verify)
- **Quality**: 10 minutes (linting, type checking)
- **Commit**: 10 minutes (git operations)

**Total**: 1.5 hours (90 minutes) ✅

## Files Modified

### New Files
- `app/server/core/pattern_validator.py` - Core validation module
- `app/server/tests/core/test_pattern_validator.py` - Comprehensive test suite

### No Modifications
Phase 1 is isolated - no integration yet (that's Phase 2)

## Testing Strategy

### Unit Tests (TDD Approach)
```bash
# Write tests first, then implement to pass them
pytest tests/core/test_pattern_validator.py -v
```

**Test Coverage:**
1. Perfect accuracy (100%)
2. Partial accuracy (66.7%)
3. No predictions (graceful handling)
4. Updates pattern accuracy correctly
5. Empty actual patterns (all FP)
6. ValidationResult dataclass structure

### Database Verification
```bash
# After tests pass, verify database state
psql -h localhost -U tac_user -d tac_webbuilder -c "
  SELECT COUNT(*) FROM pattern_predictions WHERE was_correct IS NOT NULL;
"
```

## Dependencies

**Required:**
- ✅ Migration 010 applied (`pattern_predictions` table exists)
- ✅ PostgreSQL database running
- ✅ `operation_patterns` table exists
- ✅ pytest installed

**Optional:**
- Pattern predictions already in database (not required for tests)

## Next Steps

After Phase 1 completion:
- **Phase 2**: Integrate validator into `pattern_detector.py` + analytics queries (1.0h)
- **Phase 3**: Add logging + verification + documentation (0.5h)

**Do NOT proceed to Phase 2 until:**
- ✅ All 7 tests passing
- ✅ 0 linting/type errors
- ✅ Validator committed to git
- ✅ Code reviewed and approved

---

**Status**: Ready to implement
**Depends on**: Migration 010 applied (verify first)
**Delivers**: Tested pattern validation core module
