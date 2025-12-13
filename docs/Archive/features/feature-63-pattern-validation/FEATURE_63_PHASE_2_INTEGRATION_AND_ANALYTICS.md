# Feature #63 Phase 2: Integration + Analytics

## Context
Load: `/prime`
Depends on: Phase 1 complete (validator module + tests passing)

## Task
Integrate validator into `pattern_detector.py` and create analytics CLI for accuracy reporting.

## Workflow

### 1. Investigate (5 min)
```bash
# Verify Phase 1 complete
ls -la app/server/core/pattern_validator.py
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
  POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
  app/server/.venv/bin/pytest app/server/tests/core/test_pattern_validator.py -v
```

### 2. Implement (35 min)

**A. Integrate into pattern_detector.py** (15 min)

In `app/server/core/pattern_detector.py`, add after pattern detection:

```python
from core.pattern_validator import validate_predictions

# After detecting patterns
request_id = workflow_data.get('request_id')
if request_id:
    try:
        pattern_signatures = [p['signature'] for p in detected_patterns]
        result = validate_predictions(request_id, workflow_data['workflow_id'],
                                      pattern_signatures, db_connection)
        logger.info(f"[Validator] {request_id}: {result.accuracy:.1%} accuracy")
    except Exception as e:
        logger.error(f"[Validator] Failed: {e}", exc_info=True)
```

**B. Create analytics script** (20 min)

Create `scripts/analytics/query_prediction_accuracy.py`:
- Query overall accuracy from `pattern_predictions` table
- Query accuracy by pattern from `operation_patterns`
- Support `--report` flag for detailed breakdown
- Use existing `get_database_adapter()` pattern

### 3. Test (15 min)

Create `app/server/tests/integration/test_pattern_validation_flow.py`:
- Test end-to-end: create prediction → run validation → verify DB updated
- Test missing request_id handling

```bash
cd app/server
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
  POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
  .venv/bin/pytest tests/integration/test_pattern_validation_flow.py -v

# Test analytics
cd /Users/Warmonger0/tac/tac-webbuilder
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
  POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
  python3 scripts/analytics/query_prediction_accuracy.py --report
```

### 4. Quality (5 min)
```bash
cd app/server
.venv/bin/ruff check core/pattern_detector.py tests/integration/ --fix
.venv/bin/mypy core/pattern_detector.py --ignore-missing-imports

cd /Users/Warmonger0/tac/tac-webbuilder
app/server/.venv/bin/ruff check scripts/analytics/query_prediction_accuracy.py --fix

# Full test suite
cd app/server
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
  POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
  .venv/bin/pytest tests/ -v --tb=short

# Commit
cd /Users/Warmonger0/tac/tac-webbuilder
git add app/server/core/pattern_detector.py \
        app/server/tests/integration/test_pattern_validation_flow.py \
        scripts/analytics/query_prediction_accuracy.py

git commit -m "feat: Integrate validator and add analytics (Phase 2/3)

Problem:
- Validator existed but never called
- No accuracy reporting

Solution:
- Integrated into pattern_detector.py
- Analytics script queries accuracy metrics
- Integration test verifies e2e flow

Result:
- Validation runs on workflow completion
- Can query overall/pattern accuracy

Files:
- app/server/core/pattern_detector.py (+15 lines)
- scripts/analytics/query_prediction_accuracy.py (new)
- tests/integration/test_pattern_validation_flow.py (new)

Location: app/server/core/pattern_detector.py"
```

## Success Criteria
- ✅ Integration tests pass
- ✅ Analytics script generates report
- ✅ 0 linting/type errors
- ✅ Full test suite passes

## Time: 1.0h

## Next
Phase 3: Add logging + verification (0.5h)
